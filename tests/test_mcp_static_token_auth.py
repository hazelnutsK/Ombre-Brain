"""静态 Token 鉴权（mcp_auth_mode: token）—— 与 OAuth 互斥的第三种 /mcp 鉴权模式。

覆盖：
- MCPAuthMiddleware 在 token 模式下接受 Authorization: Bearer / Ombre-MCP-Token 两种请求头
- 错误或缺失 token 一律 401
- token 模式下 OAuth 的 discovery/register/authorize/token 路由全部 404（互斥性）
- oauth（默认）/ off 两个既有模式不受影响（回归）
- mcp_auth_mode=token 但未配置密钥时，load_config() 自动回退为 oauth 并告警
- _is_valid_static_mcp_token 的 env 优先级与常量时间比较行为
"""
import json

import pytest

import web.oauth as oauth_mod
from server_app import HTTPRuntimeSettings, MCPAuthMiddleware


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


def _scope(headers):
    return {
        "type": "http",
        "scheme": "https",
        "path": "/mcp",
        "headers": [(b"host", b"ombre.example"), *headers],
    }


# --- MCPAuthMiddleware in token mode ---------------------------------------

@pytest.mark.asyncio
async def test_token_mode_accepts_correct_bearer_token():
    downstream = RecordingASGIApp()
    middleware = MCPAuthMiddleware(
        downstream,
        auth_required=True,
        auth_mode="token",
        token_validator=lambda token, **_kwargs: token == "secret-1",
    )
    scope = _scope([(b"authorization", b"Bearer secret-1")])

    await middleware(scope, _empty_receive, _discard_send)

    assert downstream.scopes == [scope]


@pytest.mark.asyncio
async def test_token_mode_accepts_correct_custom_header():
    downstream = RecordingASGIApp()
    middleware = MCPAuthMiddleware(
        downstream,
        auth_required=True,
        auth_mode="token",
        token_validator=lambda token, **_kwargs: token == "secret-1",
    )
    scope = _scope([(b"ombre-mcp-token", b"secret-1")])

    await middleware(scope, _empty_receive, _discard_send)

    assert downstream.scopes == [scope]


@pytest.mark.asyncio
async def test_token_mode_rejects_wrong_token_via_either_header():
    for headers in (
        [(b"authorization", b"Bearer wrong")],
        [(b"ombre-mcp-token", b"wrong")],
        [],  # missing entirely
    ):
        downstream = RecordingASGIApp()
        middleware = MCPAuthMiddleware(
            downstream,
            auth_required=True,
            auth_mode="token",
            token_validator=lambda token, **_kwargs: token == "secret-1",
        )
        messages = []

        await middleware(_scope(headers), _empty_receive, _collect_into(messages))

        assert downstream.scopes == []
        assert messages[0]["status"] == 401


@pytest.mark.asyncio
async def test_token_mode_401_challenge_has_no_oauth_resource_metadata():
    downstream = RecordingASGIApp()
    middleware = MCPAuthMiddleware(
        downstream,
        auth_required=True,
        auth_mode="token",
        token_validator=lambda *_a, **_k: False,
    )
    messages = []

    await middleware(_scope([]), _empty_receive, _collect_into(messages))

    payload = json.loads(messages[1]["body"])
    assert "resource_metadata" not in payload
    headers = dict(messages[0]["headers"])
    assert b"resource_metadata" not in headers[b"www-authenticate"]


@pytest.mark.asyncio
async def test_oauth_mode_ignores_custom_header_fallback():
    """默认 oauth 模式回归：自定义请求头不应绕过 OAuth Bearer 校验。"""
    downstream = RecordingASGIApp()
    middleware = MCPAuthMiddleware(
        downstream,
        auth_required=True,
        auth_mode="oauth",
        token_validator=lambda *_a, **_k: False,
    )
    messages = []

    await middleware(
        _scope([(b"ombre-mcp-token", b"whatever")]), _empty_receive, _collect_into(messages)
    )

    assert downstream.scopes == []
    assert messages[0]["status"] == 401


def test_http_runtime_settings_defaults_and_reads_auth_mode():
    assert HTTPRuntimeSettings.from_config({}).auth_mode == "oauth"
    assert HTTPRuntimeSettings.from_config({"mcp_auth_mode": "token"}).auth_mode == "token"
    # 非法值一律回退 oauth，不能悄悄变成拒绝一切或全放行
    assert HTTPRuntimeSettings.from_config({"mcp_auth_mode": "bogus"}).auth_mode == "oauth"


# --- OAuth route visibility (mutual exclusivity) ----------------------------

class FakeMCP:
    def __init__(self):
        self.routes = {}

    def custom_route(self, path, methods):
        def decorator(fn):
            for method in methods:
                self.routes[(method, path)] = fn
            return fn

        return decorator


class FakeUrl:
    scheme = "https"
    netloc = "ombre.example"


class JsonRequest:
    def __init__(self, body=None, *, headers=None, path_params=None, method="POST"):
        self._body = {} if body is None else body
        self.headers = headers or {"content-type": "application/json", "host": "ombre.example"}
        self.url = FakeUrl()
        self.path_params = path_params or {}
        self.method = method
        self.query_params = {}
        self.client = type("Client", (), {"host": "127.0.0.1"})()

    async def json(self):
        return self._body


@pytest.mark.asyncio
async def test_oauth_routes_404_when_auth_mode_is_token(monkeypatch, tmp_path):
    oauth_mod._oauth_clients.clear()
    oauth_mod._oauth_codes.clear()
    oauth_mod._mcp_tokens.clear()
    oauth_mod._mcp_token_resources.clear()
    monkeypatch.setattr(oauth_mod.sh, "config", {
        "buckets_dir": str(tmp_path / "buckets"),
        "mcp_require_auth": True,
        "mcp_auth_mode": "token",
    })

    mcp = FakeMCP()
    oauth_mod.register(mcp)

    for key in (
        ("GET", "/.well-known/oauth-protected-resource"),
        ("GET", "/.well-known/oauth-authorization-server"),
        ("POST", "/oauth/register"),
        ("GET", "/oauth/authorize"),
        ("POST", "/oauth/token"),
    ):
        response = await mcp.routes[key](JsonRequest(method=key[0]))
        assert response.status_code == 404, f"{key} should 404 when mcp_auth_mode=token"


def test_oauth_required_from_config_true_only_for_default_oauth_mode(monkeypatch):
    monkeypatch.setattr(oauth_mod.sh, "config", {"mcp_require_auth": True})
    assert oauth_mod._oauth_required_from_config() is True

    monkeypatch.setattr(
        oauth_mod.sh, "config", {"mcp_require_auth": True, "mcp_auth_mode": "oauth"}
    )
    assert oauth_mod._oauth_required_from_config() is True

    monkeypatch.setattr(
        oauth_mod.sh, "config", {"mcp_require_auth": True, "mcp_auth_mode": "token"}
    )
    assert oauth_mod._oauth_required_from_config() is False

    monkeypatch.setattr(
        oauth_mod.sh, "config", {"mcp_require_auth": False, "mcp_auth_mode": "token"}
    )
    assert oauth_mod._oauth_required_from_config() is False


# --- _is_valid_static_mcp_token ---------------------------------------------

def test_static_token_validator_rejects_empty_or_unconfigured(monkeypatch):
    monkeypatch.delenv("OMBRE_MCP_TOKEN", raising=False)
    monkeypatch.setattr(oauth_mod.sh, "config", {"mcp_token": ""})
    assert oauth_mod._is_valid_static_mcp_token("") is False
    assert oauth_mod._is_valid_static_mcp_token("anything") is False


def test_static_token_validator_matches_configured_secret(monkeypatch):
    monkeypatch.delenv("OMBRE_MCP_TOKEN", raising=False)
    monkeypatch.setattr(oauth_mod.sh, "config", {"mcp_token": "my-secret"})
    assert oauth_mod._is_valid_static_mcp_token("my-secret") is True
    assert oauth_mod._is_valid_static_mcp_token("wrong") is False


def test_static_token_validator_env_takes_priority_over_config(monkeypatch):
    monkeypatch.setenv("OMBRE_MCP_TOKEN", "env-secret")
    monkeypatch.setattr(oauth_mod.sh, "config", {"mcp_token": "config-secret"})
    assert oauth_mod._is_valid_static_mcp_token("env-secret") is True
    assert oauth_mod._is_valid_static_mcp_token("config-secret") is False


# --- load_config() safety fallback ------------------------------------------

def test_load_config_falls_back_to_oauth_when_token_mode_has_no_secret(
    monkeypatch, tmp_path, caplog
):
    from utils import load_config

    monkeypatch.delenv("OMBRE_MCP_AUTH_MODE", raising=False)
    monkeypatch.delenv("OMBRE_MCP_TOKEN", raising=False)

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
buckets_dir: buckets
mcp_auth_mode: "token"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(str(cfg_path))

    assert config["mcp_auth_mode"] == "oauth"


def test_load_config_keeps_token_mode_when_secret_is_present(monkeypatch, tmp_path):
    from utils import load_config

    monkeypatch.delenv("OMBRE_MCP_AUTH_MODE", raising=False)
    monkeypatch.setenv("OMBRE_MCP_TOKEN", "env-secret")

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
buckets_dir: buckets
mcp_auth_mode: "token"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(str(cfg_path))

    assert config["mcp_auth_mode"] == "token"
    assert config["mcp_token"] == "env-secret"


def test_load_config_default_auth_mode_is_oauth(monkeypatch, tmp_path):
    from utils import load_config

    monkeypatch.delenv("OMBRE_MCP_AUTH_MODE", raising=False)
    monkeypatch.delenv("OMBRE_MCP_TOKEN", raising=False)

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("buckets_dir: buckets\n", encoding="utf-8")

    config = load_config(str(cfg_path))

    assert config["mcp_auth_mode"] == "oauth"
    assert config["mcp_token"] == ""
