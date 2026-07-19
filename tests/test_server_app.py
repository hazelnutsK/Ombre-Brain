import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from starlette.applications import Starlette

from server_app import (
    DEFAULT_MAX_MANAGEMENT_REQUEST_BYTES,
    DEFAULT_MAX_MCP_REQUEST_BYTES,
    HTTPRuntimeSettings,
    MCPAcceptShim,
    MCPAuthMiddleware,
    NgrokHeaderMiddleware,
    OriginCSRFGuardMiddleware,
    RuntimeLifecycle,
    build_http_app,
    install_runtime_lifespan,
    merge_mcp_tool_registries,
)


class RecordingLogger:
    def __init__(self):
        self.messages = []

    def _record(self, level, message, *args):
        self.messages.append((level, message % args if args else message))

    def debug(self, message, *args):
        self._record("debug", message, *args)

    def info(self, message, *args):
        self._record("info", message, *args)

    def warning(self, message, *args):
        self._record("warning", message, *args)


class RecordingASGIApp:
    def __init__(self):
        self.scopes = []

    async def __call__(self, scope, receive, send):
        self.scopes.append(scope)
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})


async def _empty_receive():
    return {"type": "http.request", "body": b"", "more_body": False}


def _collect_into(messages):
    async def send(message):
        messages.append(message)

    return send


async def _discard_send(_message):
    return None


@pytest.mark.parametrize(
    ("config", "auth_required", "limit"),
    [
        ({}, True, DEFAULT_MAX_MCP_REQUEST_BYTES),
        ({"mcp_require_auth": "false", "limits": {"max_mcp_request_bytes": 0}}, False, 0),
        ({"limits": {"max_mcp_request_bytes": "1024"}}, True, 1024),
        ({"limits": {"max_mcp_request_bytes": -1}}, True, DEFAULT_MAX_MCP_REQUEST_BYTES),
        ({"limits": {"max_mcp_request_bytes": "bad"}}, True, DEFAULT_MAX_MCP_REQUEST_BYTES),
    ],
)
def test_http_runtime_settings_are_normalized(config, auth_required, limit):
    settings = HTTPRuntimeSettings.from_config(config)

    assert settings.auth_required is auth_required
    assert settings.max_request_bytes == limit


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, DEFAULT_MAX_MANAGEMENT_REQUEST_BYTES),
        (0, 0),
        ("2048", 2048),
        (-1, DEFAULT_MAX_MANAGEMENT_REQUEST_BYTES),
        ("bad", DEFAULT_MAX_MANAGEMENT_REQUEST_BYTES),
    ],
)
def test_management_request_limit_is_normalized(raw, expected):
    limits = {} if raw is None else {"max_management_request_bytes": raw}

    settings = HTTPRuntimeSettings.from_config({"limits": limits})

    assert settings.max_management_request_bytes == expected


def test_merge_mcp_tool_registries_keeps_one_public_manifest():
    primary = SimpleNamespace(
        _tool_manager=SimpleNamespace(_tools={"breath": object()})
    )
    extra = SimpleNamespace(
        _tool_manager=SimpleNamespace(_tools={"dream": object(), "pulse": object()})
    )

    count = merge_mcp_tool_registries(primary, extra)

    assert count == 2
    assert set(primary._tool_manager._tools) == {"breath", "dream", "pulse"}


@pytest.mark.asyncio
async def test_accept_shim_adds_both_mcp_media_types():
    downstream = RecordingASGIApp()
    middleware = MCPAcceptShim(downstream)
    messages = []
    scope = {
        "type": "http",
        "path": "/mcp",
        "headers": [(b"accept", b"application/json")],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    forwarded = dict(downstream.scopes[0]["headers"])[b"accept"]
    assert b"application/json" in forwarded
    assert b"text/event-stream" in forwarded


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/health", "/mcp-extra", "/mcp-retired"])
async def test_accept_shim_leaves_non_mcp_routes_unchanged(path):
    downstream = RecordingASGIApp()
    middleware = MCPAcceptShim(downstream)
    scope = {
        "type": "http",
        "path": path,
        "headers": [(b"accept", b"application/json")],
    }

    await middleware(scope, _empty_receive, _discard_send)

    assert downstream.scopes[0] is scope


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scheme", "host", "origin"),
    [
        ("https", "Ombre.Example:443", "HTTPS://ombre.example/"),
        ("http", "ombre.example:80", "http://OMBRE.EXAMPLE///"),
        ("https", "ombre.example:8443", "https://OMBRE.example:8443/"),
        ("https", "[2001:DB8::1]:443", "https://[2001:db8::1]/"),
    ],
)
async def test_csrf_guard_allows_normalized_same_origin_direct_request(
    scheme, host, origin
):
    downstream = RecordingASGIApp()
    middleware = OriginCSRFGuardMiddleware(downstream)
    messages = []
    scope = {
        "type": "http",
        "method": "PATCH",
        "scheme": scheme,
        "path": "/api/bucket/b1",
        "client": ("198.51.100.4", 50123),
        "headers": [
            (b"host", host.encode("ascii")),
            (b"origin", origin.encode("ascii")),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == [scope]
    assert messages[0]["status"] == 204


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("PATCH", "/api/bucket/b1"),
        ("POST", "/api/restart"),
        ("POST", "/api/do-update"),
    ],
)
async def test_csrf_guard_allows_public_origin_from_trusted_proxy(
    monkeypatch, method, path
):
    monkeypatch.setenv("OMBRE_TRUSTED_PROXY_CIDRS", "10.0.0.0/8")
    downstream = RecordingASGIApp()
    middleware = OriginCSRFGuardMiddleware(downstream)
    messages = []
    scope = {
        "type": "http",
        "method": method,
        "scheme": "http",
        "path": path,
        "client": ("10.20.30.40", 49152),
        "headers": [
            (b"host", b"127.0.0.1:8000"),
            (b"origin", b"https://PUBLIC.example/"),
            (b"x-forwarded-proto", b"https, http"),
            (b"x-forwarded-host", b"public.example:443, proxy.internal"),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == [scope]
    assert messages[0]["status"] == 204


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("PATCH", "/api/bucket/b1/edit"),
        ("POST", "/api/env-config"),
        ("POST", "/api/config"),
        ("POST", "/api/restart"),
        ("POST", "/api/do-update"),
    ],
)
async def test_csrf_guard_uses_same_origin_fetch_signal_when_proxy_omits_headers(
    monkeypatch,
    method,
    path,
):
    monkeypatch.setenv("OMBRE_TRUSTED_PROXY_CIDRS", "10.0.0.0/8")
    downstream = RecordingASGIApp()
    middleware = OriginCSRFGuardMiddleware(downstream)
    messages = []
    scope = {
        "type": "http",
        "method": method,
        "scheme": "http",
        "path": path,
        "client": ("10.20.30.40", 49152),
        "headers": [
            (b"host", b"127.0.0.1:8000"),
            (b"origin", b"https://public.example"),
            (b"sec-fetch-site", b"same-origin"),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == [scope]
    assert messages[0]["status"] == 204


@pytest.mark.asyncio
async def test_csrf_guard_accepts_configured_public_origin_without_fetch_metadata():
    downstream = RecordingASGIApp()
    middleware = OriginCSRFGuardMiddleware(
        downstream,
        public_origin="HTTPS://Public.Example:443/mcp/",
    )
    messages = []
    scope = {
        "type": "http",
        "method": "POST",
        "scheme": "http",
        "path": "/api/env-config",
        "client": ("198.51.100.4", 50123),
        "headers": [
            (b"host", b"internal.service:8000"),
            (b"origin", b"https://public.example"),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == [scope]
    assert messages[0]["status"] == 204


@pytest.mark.asyncio
async def test_csrf_guard_cross_site_signal_overrides_configured_public_origin():
    downstream = RecordingASGIApp()
    middleware = OriginCSRFGuardMiddleware(
        downstream,
        public_origin="https://public.example",
    )
    messages = []
    scope = {
        "type": "http",
        "method": "PATCH",
        "scheme": "http",
        "path": "/api/bucket/b1",
        "client": ("198.51.100.4", 50123),
        "headers": [
            (b"host", b"internal.service:8000"),
            (b"origin", b"https://public.example"),
            (b"sec-fetch-site", b"cross-site"),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == []
    assert messages[0]["status"] == 403


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "origin",
    ["null", "file://", "https://public.example/path", "not a URL"],
)
async def test_csrf_guard_rejects_invalid_origin_despite_same_origin_signal(origin):
    downstream = RecordingASGIApp()
    middleware = OriginCSRFGuardMiddleware(
        downstream,
        public_origin="https://public.example",
    )
    messages = []
    scope = {
        "type": "http",
        "method": "POST",
        "scheme": "http",
        "path": "/api/env-config",
        "client": ("198.51.100.4", 50123),
        "headers": [
            (b"host", b"internal.service:8000"),
            (b"origin", origin.encode("ascii")),
            (b"sec-fetch-site", b"same-origin"),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == []
    assert messages[0]["status"] == 403


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "duplicate_name",
    [
        b"origin",
        b"host",
        b"sec-fetch-site",
        b"forwarded",
        b"x-forwarded-for",
        b"x-forwarded-host",
        b"x-forwarded-proto",
    ],
)
async def test_csrf_guard_rejects_duplicate_security_headers(duplicate_name):
    downstream = RecordingASGIApp()
    middleware = OriginCSRFGuardMiddleware(
        downstream,
        public_origin="https://public.example",
    )
    messages = []
    headers = [
        (b"host", b"internal.service:8000"),
        (b"origin", b"https://public.example"),
        (b"sec-fetch-site", b"same-origin"),
    ]
    existing = next(
        (value for name, value in headers if name == duplicate_name),
        None,
    )
    if existing is None:
        headers.extend(
            [
                (duplicate_name, b"synthetic"),
                (duplicate_name, b"synthetic"),
            ]
        )
    else:
        headers.append((duplicate_name, existing))
    scope = {
        "type": "http",
        "method": "PATCH",
        "scheme": "http",
        "path": "/api/bucket/b1/edit",
        "client": ("198.51.100.4", 50123),
        "headers": headers,
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == []
    assert messages[0]["status"] == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("fetch_site", ["same-site", "cross-site"])
async def test_csrf_guard_rejects_non_same_origin_fetch_signal_without_origin(
    fetch_site,
):
    downstream = RecordingASGIApp()
    middleware = OriginCSRFGuardMiddleware(downstream)
    messages = []
    scope = {
        "type": "http",
        "method": "POST",
        "scheme": "https",
        "path": "/auth/login",
        "client": ("198.51.100.4", 50123),
        "headers": [
            (b"host", b"ombre.example"),
            (b"sec-fetch-site", fetch_site.encode("ascii")),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == []
    assert messages[0]["status"] == 403


@pytest.mark.asyncio
async def test_csrf_guard_ignores_spoofed_forwarding_headers(monkeypatch):
    monkeypatch.setenv("OMBRE_TRUSTED_PROXY_CIDRS", "127.0.0.0/8,::1/128")
    downstream = RecordingASGIApp()
    middleware = OriginCSRFGuardMiddleware(downstream)
    messages = []
    scope = {
        "type": "http",
        "method": "PATCH",
        "scheme": "https",
        "path": "/api/bucket/b1",
        "client": ("198.51.100.4", 50123),
        "headers": [
            (b"host", b"ombre.example"),
            (b"origin", b"https://evil.example"),
            (b"x-forwarded-proto", b"https"),
            (b"x-forwarded-host", b"evil.example"),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == []
    assert messages[0]["status"] == 403


@pytest.mark.asyncio
async def test_csrf_guard_rejects_cross_origin_through_trusted_proxy(monkeypatch):
    monkeypatch.setenv("OMBRE_TRUSTED_PROXY_CIDRS", "10.0.0.0/8")
    downstream = RecordingASGIApp()
    middleware = OriginCSRFGuardMiddleware(downstream)
    messages = []
    scope = {
        "type": "http",
        "method": "POST",
        "scheme": "http",
        "path": "/auth/login",
        "client": ("10.20.30.40", 49152),
        "headers": [
            (b"host", b"127.0.0.1:8000"),
            (b"origin", b"https://evil.example"),
            (b"x-forwarded-proto", b"https"),
            (b"x-forwarded-host", b"ombre.example"),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == []
    assert messages[0]["status"] == 403
    assert json.loads(messages[1]["body"]) == {
        "error": "Cross-origin request rejected"
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/mcp",
        "/mcp/",
        "/oauth/token",
        "/.well-known/oauth-protected-resource/mcp",
    ],
)
async def test_csrf_guard_keeps_bearer_and_oauth_routes_exempt(path):
    downstream = RecordingASGIApp()
    middleware = OriginCSRFGuardMiddleware(downstream)
    messages = []
    scope = {
        "type": "http",
        "method": "POST",
        "scheme": "https",
        "path": path,
        "client": ("198.51.100.4", 50123),
        "headers": [
            (b"host", b"ombre.example"),
            (b"origin", b"https://cross-origin.example"),
            (b"sec-fetch-site", b"cross-site"),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == [scope]
    assert messages[0]["status"] == 204


@pytest.mark.asyncio
async def test_ngrok_header_middleware_adds_skip_warning_header():
    downstream = RecordingASGIApp()
    middleware = NgrokHeaderMiddleware(downstream)
    messages = []
    scope = {"type": "http", "path": "/mcp", "headers": []}

    await middleware(scope, _empty_receive, _collect_into(messages))

    start = next(m for m in messages if m["type"] == "http.response.start")
    assert (b"ngrok-skip-browser-warning", b"true") in start["headers"]


@pytest.mark.asyncio
async def test_ngrok_header_middleware_applies_regardless_of_status():
    class RejectingApp:
        async def __call__(self, scope, receive, send):
            await send({"type": "http.response.start", "status": 401, "headers": []})
            await send({"type": "http.response.body", "body": b""})

    middleware = NgrokHeaderMiddleware(RejectingApp())
    messages = []
    scope = {"type": "http", "path": "/mcp", "headers": []}

    await middleware(scope, _empty_receive, _collect_into(messages))

    start = next(m for m in messages if m["type"] == "http.response.start")
    assert start["status"] == 401
    assert (b"ngrok-skip-browser-warning", b"true") in start["headers"]


@pytest.mark.asyncio
async def test_ngrok_header_middleware_does_not_duplicate_existing_header():
    class PreHeaderedApp:
        async def __call__(self, scope, receive, send):
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"ngrok-skip-browser-warning", b"true")],
                }
            )
            await send({"type": "http.response.body", "body": b""})

    middleware = NgrokHeaderMiddleware(PreHeaderedApp())
    messages = []
    scope = {"type": "http", "path": "/mcp", "headers": []}

    await middleware(scope, _empty_receive, _collect_into(messages))

    start = next(m for m in messages if m["type"] == "http.response.start")
    assert start["headers"].count((b"ngrok-skip-browser-warning", b"true")) == 1


@pytest.mark.asyncio
async def test_ngrok_header_middleware_ignores_non_http_scopes():
    downstream = RecordingASGIApp()
    middleware = NgrokHeaderMiddleware(downstream)
    scope = {"type": "lifespan"}

    await middleware(scope, _empty_receive, _discard_send)

    assert downstream.scopes == [scope]


@pytest.mark.asyncio
async def test_auth_middleware_rejects_missing_token_with_canonical_metadata_url():
    downstream = RecordingASGIApp()
    middleware = MCPAuthMiddleware(
        downstream,
        auth_required=True,
        token_validator=lambda *_args, **_kwargs: False,
    )
    messages = []
    scope = {
        "type": "http",
        "scheme": "http",
        "path": "/mcp",
        "client": ("127.0.0.1", 49152),
        "headers": [
            (b"host", b"internal:8000"),
            (b"x-forwarded-proto", b"https, http"),
            (b"x-forwarded-host", b"ombre.example, proxy.local"),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == []
    assert messages[0]["status"] == 401
    payload = json.loads(messages[1]["body"])
    assert payload["resource_metadata"] == (
        "https://ombre.example/.well-known/oauth-protected-resource/mcp"
    )


@pytest.mark.asyncio
async def test_auth_middleware_ignores_forwarded_resource_from_untrusted_peer(
    monkeypatch,
):
    monkeypatch.setenv("OMBRE_TRUSTED_PROXY_CIDRS", "127.0.0.0/8,::1/128")
    downstream = RecordingASGIApp()
    middleware = MCPAuthMiddleware(
        downstream,
        auth_required=True,
        token_validator=lambda *_args, **_kwargs: False,
    )
    messages = []
    scope = {
        "type": "http",
        "scheme": "https",
        "path": "/mcp",
        "client": ("198.51.100.4", 50123),
        "headers": [
            (b"host", b"ombre.example:443"),
            (b"x-forwarded-proto", b"http"),
            (b"x-forwarded-host", b"evil.example"),
        ],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    payload = json.loads(messages[1]["body"])
    assert payload["resource_metadata"] == (
        "https://ombre.example/.well-known/oauth-protected-resource/mcp"
    )


@pytest.mark.asyncio
async def test_auth_middleware_does_not_challenge_retired_mcp_extra_path():
    downstream = RecordingASGIApp()
    middleware = MCPAuthMiddleware(
        downstream,
        auth_required=True,
        token_validator=lambda *_args, **_kwargs: pytest.fail(
            "retired routes must reach the router without OAuth validation"
        ),
    )
    messages = []
    scope = {
        "type": "http",
        "scheme": "https",
        "path": "/mcp-extra",
        "headers": [(b"host", b"ombre.example")],
    }

    await middleware(scope, _empty_receive, _collect_into(messages))

    assert downstream.scopes == [scope]
    assert messages[0]["status"] == 204


@pytest.mark.asyncio
async def test_auth_middleware_validates_token_against_exact_resource():
    downstream = RecordingASGIApp()
    seen = {}

    def validator(token, *, resource):
        seen.update(token=token, resource=resource)
        return True

    middleware = MCPAuthMiddleware(
        downstream,
        auth_required=True,
        token_validator=validator,
    )
    scope = {
        "type": "http",
        "scheme": "https",
        "path": "/mcp/",
        "headers": [
            (b"host", b"ombre.example"),
            (b"authorization", b"Bearer token-1"),
        ],
    }

    await middleware(scope, _empty_receive, _discard_send)

    assert seen == {"token": "token-1", "resource": "https://ombre.example/mcp"}
    assert downstream.scopes == [scope]


@pytest.mark.asyncio
async def test_auth_middleware_can_be_explicitly_disabled():
    downstream = RecordingASGIApp()
    middleware = MCPAuthMiddleware(
        downstream,
        auth_required=False,
        token_validator=lambda *_args, **_kwargs: False,
    )
    scope = {"type": "http", "path": "/mcp", "headers": []}

    await middleware(scope, _empty_receive, _discard_send)

    assert downstream.scopes == [scope]


class RecordingService:
    def __init__(self, name, events):
        self.name = name
        self.events = events

    async def start(self):
        self.events.append(f"{self.name}:start")

    async def stop(self):
        self.events.append(f"{self.name}:stop")


@pytest.mark.asyncio
async def test_runtime_lifecycle_starts_and_stops_every_owned_service(tmp_path):
    events = []
    logger = RecordingLogger()
    marker = tmp_path / ".boot_fails"
    marker.write_text("2", encoding="utf-8")

    async def ollama_start():
        events.append("ollama:start")

    async def ollama_stop():
        events.append("ollama:stop")

    lifecycle = RuntimeLifecycle(
        logger=logger,
        decay_engine=RecordingService("decay", events),
        embedding_outbox=RecordingService("outbox", events),
        ensure_ollama_child=ollama_start,
        stop_ollama_child=ollama_stop,
        load_tunnel_config=lambda: {"auto_start": True, "token": "tunnel-token"},
        start_tunnel=lambda token: (events.append(f"tunnel:start:{token}") or True, "ok"),
        stop_tunnel=lambda: events.append("tunnel:stop"),
        restart_github_auto_task=lambda interval: events.append(f"github:{interval}"),
        github_auto_interval=9,
        boot_marker_path=str(marker),
    )

    await lifecycle.start()
    await lifecycle.start()
    await lifecycle.stop()
    await lifecycle.stop()

    assert events == [
        "tunnel:start:tunnel-token",
        "github:9",
        "decay:start",
        "ollama:start",
        "outbox:start",
        "github:0",
        "outbox:stop",
        "decay:stop",
        "ollama:stop",
        "tunnel:stop",
    ]
    assert marker.read_text(encoding="utf-8") == "0"


@pytest.mark.asyncio
async def test_runtime_lifecycle_cancels_keepalive_on_shutdown():
    lifecycle = RuntimeLifecycle(
        logger=RecordingLogger(),
        keepalive_url="http://127.0.0.1:1/health",
        keepalive_initial_delay=3600,
    )

    await lifecycle.start()
    task = lifecycle._keepalive_task
    await asyncio.sleep(0)
    await lifecycle.stop()

    assert task is not None
    assert task.done()
    assert lifecycle._keepalive_task is None


@pytest.mark.asyncio
async def test_runtime_lifecycle_logs_optional_service_failures_without_leaking():
    logger = RecordingLogger()

    class FailingService:
        async def start(self):
            raise RuntimeError("start failed")

        async def stop(self):
            raise RuntimeError("stop failed")

    lifecycle = RuntimeLifecycle(
        logger=logger,
        decay_engine=FailingService(),
        embedding_outbox=FailingService(),
        load_tunnel_config=lambda: (_ for _ in ()).throw(RuntimeError("tunnel failed")),
        start_tunnel=lambda _token: (True, "unused"),
        stop_tunnel=lambda: (_ for _ in ()).throw(RuntimeError("stop tunnel failed")),
    )

    await lifecycle.start()
    await lifecycle.stop()

    warnings = "\n".join(message for level, message in logger.messages if level == "warning")
    assert "tunnel auto-start failed" in warnings
    assert "decay engine start failed" in warnings
    assert "embedding outbox stop failed" in warnings
    assert "tunnel stop failed" in warnings


@pytest.mark.asyncio
async def test_runtime_lifespan_composes_with_parent_lifespan():
    events = []

    @asynccontextmanager
    async def parent(_app):
        events.append("parent:start")
        try:
            yield
        finally:
            events.append("parent:stop")

    class FakeLifecycle:
        async def start(self):
            events.append("runtime:start")

        async def stop(self):
            events.append("runtime:stop")

    app = SimpleNamespace(router=SimpleNamespace(lifespan_context=parent))
    install_runtime_lifespan(app, FakeLifecycle())

    async with app.router.lifespan_context(app):
        events.append("body")

    assert events == [
        "parent:start",
        "runtime:start",
        "body",
        "runtime:stop",
        "parent:stop",
    ]


@pytest.mark.parametrize("transport", ["streamable-http", "sse"])
def test_build_http_app_uses_same_managed_stack_for_both_http_transports(transport):
    class FakeMCP:
        def streamable_http_app(self):
            return Starlette()

        def sse_app(self):
            return Starlette()

    lifecycle = RuntimeLifecycle(logger=RecordingLogger())
    settings = HTTPRuntimeSettings(
        auth_required=False,
        max_request_bytes=2048,
        public_origin="https://public.example",
    )

    app = build_http_app(
        FakeMCP(),
        transport,
        settings=settings,
        token_validator=lambda *_args, **_kwargs: False,
        lifecycle=lifecycle,
    )

    middleware_names = {item.cls.__name__ for item in app.user_middleware}
    assert middleware_names >= {
        "CORSMiddleware",
        "OriginCSRFGuardMiddleware",
        "MCPRequestBodyLimitMiddleware",
        "ManagementRequestBodyLimitMiddleware",
        "MCPAcceptShim",
        "MCPAuthMiddleware",
        "NgrokHeaderMiddleware",
    }
    csrf_middleware = next(
        item
        for item in app.user_middleware
        if item.cls is OriginCSRFGuardMiddleware
    )
    assert csrf_middleware.kwargs["public_origin"] == "https://public.example"
    assert app.state.ombre_http_settings is settings
    assert app.state.ombre_runtime_lifecycle is lifecycle


def test_build_http_app_rejects_stdio_transport():
    with pytest.raises(ValueError, match="stdio"):
        build_http_app(
            SimpleNamespace(),
            "stdio",
            settings=HTTPRuntimeSettings(True, 1024),
            token_validator=lambda *_args, **_kwargs: False,
            lifecycle=RuntimeLifecycle(logger=RecordingLogger()),
        )
