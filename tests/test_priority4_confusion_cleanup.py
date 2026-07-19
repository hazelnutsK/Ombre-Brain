import json
from pathlib import Path

import pytest
import yaml

import web.buckets as buckets_web
import web.config_api as config_api
import web.import_api as import_api
import utils


ROOT = Path(__file__).resolve().parents[1]


class FakeMCP:
    def __init__(self):
        self.routes = {}

    def custom_route(self, path, methods):
        def decorator(handler):
            for method in methods:
                self.routes[(method, path)] = handler
            return handler

        return decorator


class JsonRequest:
    def __init__(self, body=None, *, path_params=None):
        self._body = body or {}
        self.path_params = path_params or {}
        self.headers = {}
        self.query_params = {}

    async def json(self):
        return self._body


def _json(response):
    return json.loads(response.body.decode("utf-8"))


@pytest.mark.asyncio
async def test_pulse_shows_special_bucket_counts_separately(monkeypatch):
    from tools.anchor import core as anchor_core

    class FakeDecay:
        is_running = True

        async def ensure_started(self):
            return None

    class FakeBucketManager:
        async def get_stats(self):
            return {
                "permanent_count": 1,
                "dynamic_count": 2,
                "archive_count": 3,
                "feel_count": 4,
                "plan_count": 5,
                "letter_count": 6,
                "total_size_kb": 7.0,
            }

        async def list_all(self, include_archive=False):
            return []

    monkeypatch.setattr(anchor_core.rt, "decay_engine", FakeDecay(), raising=False)
    monkeypatch.setattr(anchor_core.rt, "bucket_mgr", FakeBucketManager(), raising=False)
    monkeypatch.setattr(anchor_core.rt, "embedding_engine", None, raising=False)

    result = await anchor_core.pulse()

    assert "feel 桶: 4 条" in result
    assert "plan 桶: 5 条" in result
    assert "letter 桶: 6 封" in result


@pytest.mark.asyncio
async def test_grow_shortpath_explains_hold_style_single_memory(monkeypatch):
    from tools.grow import shortpath

    class FakeLogger:
        def info(self, *_args, **_kwargs):
            pass

    class FakeDehydrator:
        async def analyze(self, _content):
            return {
                "importance": 5,
                "tags": ["短句"],
                "domain": ["测试"],
                "valence": 0.5,
                "arousal": 0.3,
                "suggested_name": "短内容",
            }

    async def fake_merge_or_create(**_kwargs):
        return "bucket-1", False, ""

    async def fake_background(*_args, **_kwargs):
        return None

    def fake_create_task(coro):
        coro.close()
        return None

    monkeypatch.setattr(shortpath.rt, "logger", FakeLogger(), raising=False)
    monkeypatch.setattr(shortpath.rt, "dehydrator", FakeDehydrator(), raising=False)
    monkeypatch.setattr(shortpath, "merge_or_create", fake_merge_or_create)
    monkeypatch.setattr(shortpath, "check_plan_resolution", fake_background)
    monkeypatch.setattr(shortpath, "check_duplicate_for", fake_background)
    monkeypatch.setattr(shortpath.asyncio, "create_task", fake_create_task)

    result = await shortpath.grow_shortpath("短句")

    assert "短内容已按 hold 路径保存为单条记忆" in result


@pytest.mark.asyncio
async def test_host_vault_set_returns_restart_required_message(monkeypatch, tmp_path):
    monkeypatch.setattr(import_api.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(import_api.sh, "in_docker", lambda: False)
    monkeypatch.setattr(import_api.sh, "_project_env_path", lambda: str(tmp_path / ".env"))
    monkeypatch.setattr(import_api.sh, "_write_env_var", lambda _key, _value: None)

    mcp = FakeMCP()
    import_api.register(mcp)

    response = await mcp.routes[("POST", "/api/host-vault")](
        JsonRequest({"value": "D:/Vault/Ombre"})
    )
    payload = _json(response)

    assert payload["ok"] is True
    assert payload["restart_required"] is True
    assert "重启" in payload["message"]


@pytest.mark.asyncio
async def test_host_vault_set_rejects_container_local_fake_save(monkeypatch):
    writes = []
    monkeypatch.setattr(import_api.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(import_api.sh, "in_docker", lambda: True)
    monkeypatch.setattr(import_api.sh, "_write_env_var", lambda key, value: writes.append((key, value)))

    mcp = FakeMCP()
    import_api.register(mcp)

    response = await mcp.routes[("POST", "/api/host-vault")](
        JsonRequest({"value": "D:/Vault/Ombre"})
    )
    payload = _json(response)

    assert response.status_code == 409
    assert payload["compose_managed"] is True
    assert payload["restart_required"] is True
    assert "compose" in payload["error"].lower()
    assert writes == []


@pytest.mark.asyncio
async def test_host_vault_get_reports_compose_injected_value_in_container(monkeypatch):
    monkeypatch.setattr(import_api.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(import_api.sh, "in_docker", lambda: True)
    monkeypatch.setenv("OMBRE_HOST_VAULT_DIR", "D:/Vault/Ombre")
    monkeypatch.setattr(
        import_api.sh,
        "_read_env_var",
        lambda _name: pytest.fail("container must not read its local .env for a host mount"),
    )

    mcp = FakeMCP()
    import_api.register(mcp)

    response = await mcp.routes[("GET", "/api/host-vault")](JsonRequest())
    payload = _json(response)

    assert response.status_code == 200
    assert payload["value"] == "D:/Vault/Ombre"
    assert payload["source"] == "env"
    assert payload["env_file"] is None
    assert payload["compose_managed"] is True


@pytest.mark.asyncio
async def test_bucket_resolve_route_returns_trace_aligned_message(monkeypatch):
    class FakeBucketManager:
        def __init__(self):
            self.row = {"id": "b1", "metadata": {"id": "b1", "resolved": False}}
            self.updates = []

        async def get(self, bucket_id):
            return self.row if bucket_id == "b1" else None

        async def update(self, bucket_id, **updates):
            self.updates.append((bucket_id, updates))
            self.row["metadata"].update(updates)
            return True

    bucket_mgr = FakeBucketManager()
    monkeypatch.setattr(buckets_web.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(buckets_web.sh, "bucket_mgr", bucket_mgr, raising=False)

    mcp = FakeMCP()
    buckets_web.register(mcp)

    response = await mcp.routes[("POST", "/api/bucket/{bucket_id}/resolve")](
        JsonRequest(path_params={"bucket_id": "b1"})
    )
    payload = _json(response)

    assert payload["resolved"] is True
    assert payload["message"] == "已沉底，只在关键词触发时重新浮现"


def test_config_example_marks_wikilink_deprecated_without_active_stanza():
    text = (ROOT / "config.example.yaml").read_text(encoding="utf-8")

    assert "\nwikilink:" not in text
    assert "wikilink" in text
    assert "deprecated" in text.lower() or "已废弃" in text


def test_dashboard_single_bucket_delete_is_not_labeled_as_hard_delete():
    for rel in ("frontend/dashboard.html",):
        text = (ROOT / rel).read_text(encoding="utf-8")

        assert "删除到档案" in text
        assert "这将彻底删除此记忆桶" not in text
        assert "你真的要永久删除吗" not in text
        assert "彻底删除这封信" not in text
        assert "你真的要永久删除这封信吗" not in text
        assert 'title="彻底删除"' not in text
        assert "/api/buckets/purge" not in text
        assert "进入清理模式" not in text
        assert "批量永久删除" not in text


def test_dashboard_exposes_oauth_authentication_switch():
    for rel in ("frontend/dashboard.html",):
        text = (ROOT / rel).read_text(encoding="utf-8")

        assert 'id="cfg-mcp-auth"' in text
        assert "开启 OAuth（Claude.ai 网页版 / Claude Code 远程需要）" in text
        assert "saveMcpAuth()" in text
        assert "mcp_require_auth: false, persist: true" in text
        assert 'id="btn-restart"' in text
        assert "restartService()" in text
        assert "setRestartRequired(!!result.restart_required" in text


def test_dashboard_exposes_mcp_static_token_mode():
    for rel in ("frontend/dashboard.html",):
        text = (ROOT / rel).read_text(encoding="utf-8")

        # 三态互斥：选 OAuth 就不认 Token，选 Token 就不认 OAuth。
        assert '<option value="oauth">' in text
        assert '<option value="token">' in text
        assert '<option value="off">' in text
        assert 'id="mcp-token-panel"' in text
        assert "regenerateMcpToken()" in text
        assert "/api/mcp-token/regenerate" in text
        assert "Ombre-MCP-Token" in text


@pytest.mark.asyncio
async def test_dashboard_oauth_switch_persists_to_config(monkeypatch, tmp_path):
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr(config_api.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(config_api.sh, "config", {"mcp_require_auth": True})
    monkeypatch.setattr(utils, "config_file_path", lambda: str(config_path))
    mcp = FakeMCP()
    config_api.register(mcp)

    response = await mcp.routes[("POST", "/api/config")](
        JsonRequest({"mcp_require_auth": False, "persist": True})
    )
    payload = _json(response)
    persisted = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["restart_required"] is True
    assert payload["mcp_require_auth_effective"] is True
    # Startup-bound settings remain the effective runtime snapshot until restart.
    assert config_api.sh.config["mcp_require_auth"] is True
    assert persisted["mcp_require_auth"] is False


@pytest.mark.asyncio
async def test_dashboard_mcp_startup_settings_require_persistence_and_do_not_publish_on_failure(
    monkeypatch,
):
    runtime = {"mcp_require_auth": True, "mcp_auth_mode": "oauth"}
    monkeypatch.setattr(config_api.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(config_api.sh, "config", runtime)
    mcp = FakeMCP()
    config_api.register(mcp)

    not_persisted = await mcp.routes[("POST", "/api/config")](
        JsonRequest({"mcp_require_auth": False})
    )
    assert not_persisted.status_code == 400
    assert runtime == {"mcp_require_auth": True, "mcp_auth_mode": "oauth"}

    monkeypatch.setattr(
        config_api,
        "atomic_update_config_yaml",
        lambda _mutate: (_ for _ in ()).throw(OSError("read-only mount")),
    )
    failed = await mcp.routes[("POST", "/api/config")](
        JsonRequest(
            {
                "mcp_require_auth": False,
                "mcp_auth_mode": "token",
                "persist": True,
            }
        )
    )
    assert failed.status_code == 500
    assert runtime == {"mcp_require_auth": True, "mcp_auth_mode": "oauth"}


@pytest.mark.asyncio
async def test_dashboard_public_mcp_address_persists_round_trips_and_clears(
    monkeypatch, tmp_path
):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump({"deployment": {"profile": "advanced"}}), encoding="utf-8"
    )
    monkeypatch.setattr(config_api.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(
        config_api.sh,
        "config",
        {"mcp_require_auth": True, "deployment": {"profile": "advanced"}},
    )
    monkeypatch.setattr(config_api.sh, "in_docker", lambda: False)
    monkeypatch.setattr(utils, "config_file_path", lambda: str(config_path))
    mcp = FakeMCP()
    config_api.register(mcp)

    saved = await mcp.routes[("POST", "/api/config")](
        JsonRequest(
            {
                "deployment": {"public_url": "https://OB.Example:443/mcp"},
                "persist": True,
            }
        )
    )
    saved_payload = _json(saved)
    reloaded = await mcp.routes[("GET", "/api/config")](JsonRequest())

    assert saved.status_code == 200
    assert saved_payload["restart_required"] is True
    assert saved_payload["deployment"]["public_url"] == "https://ob.example"
    assert saved_payload["deployment"]["public_url_effective"] == ""
    reloaded_payload = _json(reloaded)
    assert reloaded_payload["deployment"]["public_url"] == "https://ob.example"
    assert reloaded_payload["deployment"]["public_url_effective"] == ""
    assert reloaded_payload["restart_required"] is True
    assert config_api.sh.config["deployment"] == {"profile": "advanced"}
    persisted = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert persisted["deployment"] == {
        "profile": "advanced",
        "public_url": "https://ob.example",
    }

    cleared = await mcp.routes[("POST", "/api/config")](
        JsonRequest({"deployment": {"public_url": ""}, "persist": True})
    )
    cleared_payload = _json(cleared)
    persisted = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert cleared_payload["deployment"]["public_url"] == ""
    assert persisted["deployment"] == {"profile": "advanced"}


@pytest.mark.asyncio
async def test_dashboard_public_mcp_address_rejects_non_origin_without_mutation(
    monkeypatch, tmp_path
):
    config_path = tmp_path / "config.yaml"
    original = {"deployment": {"public_url": "https://safe.example"}}
    config_path.write_text(yaml.safe_dump(original), encoding="utf-8")
    monkeypatch.setattr(config_api.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(config_api.sh, "config", dict(original))
    monkeypatch.setattr(utils, "config_file_path", lambda: str(config_path))
    mcp = FakeMCP()
    config_api.register(mcp)

    response = await mcp.routes[("POST", "/api/config")](
        JsonRequest(
            {
                "deployment": {"public_url": "https://safe.example/other?x=1"},
                "persist": True,
            }
        )
    )

    assert response.status_code == 400
    assert yaml.safe_load(config_path.read_text(encoding="utf-8")) == original
    assert config_api.sh.config == original


@pytest.mark.asyncio
async def test_dashboard_public_mcp_address_write_failure_is_not_published_to_runtime(
    monkeypatch
):
    runtime = {"deployment": {"public_url": "https://old.example"}}
    monkeypatch.setattr(config_api.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(config_api.sh, "config", runtime)
    monkeypatch.setattr(
        config_api,
        "atomic_update_config_yaml",
        lambda _mutate: (_ for _ in ()).throw(OSError("read-only mount")),
    )
    mcp = FakeMCP()
    config_api.register(mcp)

    response = await mcp.routes[("POST", "/api/config")](
        JsonRequest(
            {
                "deployment": {"public_url": "https://new.example/mcp"},
                "persist": True,
            }
        )
    )

    assert response.status_code == 500
    assert "persist failed" in _json(response)["error"]
    assert runtime == {"deployment": {"public_url": "https://old.example"}}


@pytest.mark.asyncio
async def test_retired_purge_endpoint_never_deletes_memory(monkeypatch):
    class ExplodingBucketManager:
        def __getattr__(self, name):
            raise AssertionError(f"retired purge endpoint touched bucket manager: {name}")

    monkeypatch.setattr(buckets_web.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(
        buckets_web.sh, "bucket_mgr", ExplodingBucketManager(), raising=False
    )
    mcp = FakeMCP()
    buckets_web.register(mcp)

    response = await mcp.routes[("POST", "/api/buckets/purge")](
        JsonRequest({"ids": ["memory-1"]})
    )
    payload = _json(response)

    assert response.status_code == 410
    assert payload["error"] == "physical_deletion_forbidden"
    assert "Markdown 文件会继续保留" in payload["message"]
