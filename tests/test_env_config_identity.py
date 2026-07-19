import json
import os
from types import SimpleNamespace

import pytest

import web.config_api as config_api
from utils import get_ai_name, load_config


class FakeMCP:
    def __init__(self):
        self.routes = {}

    def custom_route(self, path, methods):
        def decorator(fn):
            for method in methods:
                self.routes[(method, path)] = fn
            return fn

        return decorator


class JsonRequest:
    def __init__(self, body):
        self._body = body

    async def json(self):
        return self._body


@pytest.mark.asyncio
async def test_env_config_can_clear_ai_display_name(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_NAME", "trainsprout")
    monkeypatch.setattr(config_api.sh, "_require_auth", lambda request: None)
    monkeypatch.setattr(config_api.sh, "_project_env_path", lambda: str(tmp_path / ".env"))
    monkeypatch.setattr(config_api.sh, "config", {})

    mcp = FakeMCP()
    config_api.register(mcp)

    response = await mcp.routes[("POST", "/api/env-config")](
        JsonRequest({"updates": {"AI_NAME": ""}})
    )
    payload = json.loads(response.body)

    assert payload["ok"] is True
    assert "AI_NAME" in payload["updated"]
    assert os.environ.get("AI_NAME") is None
    assert get_ai_name() == "AI"


@pytest.mark.asyncio
async def test_compress_runtime_reload_survives_config_persistence_failure(
    monkeypatch, tmp_path
):
    import openai

    created_clients = []

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            created_clients.append(self)

    old_client = object()
    dehydrator = SimpleNamespace(
        api_key="old-key",
        base_url="https://old.example/v1",
        model="old-model",
        timeout_seconds=60.0,
        api_format="openai_compat",
        api_available=True,
        client=old_client,
    )
    runtime_config = {
        "dehydration": {
            "api_key": "old-key",
            "base_url": "https://old.example/v1",
            "model": "old-model",
            "timeout_seconds": 60,
            "api_format": "openai_compat",
        }
    }
    persistence_calls = []

    def fail_config_persistence(mutate):
        persisted = {}
        mutate(persisted)
        persistence_calls.append(persisted)
        raise OSError("Device or resource busy")

    monkeypatch.setattr(config_api.sh, "_require_auth", lambda request: None)
    monkeypatch.setattr(
        config_api.sh, "_project_env_path", lambda: str(tmp_path / ".env")
    )
    monkeypatch.setattr(config_api.sh, "config", runtime_config)
    monkeypatch.setattr(config_api.sh, "dehydrator", dehydrator)
    monkeypatch.setattr(config_api, "atomic_update_config_yaml", fail_config_persistence)
    monkeypatch.setattr(openai, "AsyncOpenAI", FakeAsyncOpenAI)
    monkeypatch.setenv("OMBRE_COMPRESS_API_KEY", "old-key")
    monkeypatch.setenv("OMBRE_COMPRESS_BASE_URL", "https://old.example/v1")
    monkeypatch.setenv("OMBRE_COMPRESS_MODEL", "old-model")
    monkeypatch.setenv("OMBRE_COMPRESS_TIMEOUT_SECONDS", "60")

    updates = {
        # Deliberately not client-construction order: the route must stage the
        # complete batch and build exactly one client from the final values.
        "OMBRE_COMPRESS_MODEL": "new-model",
        "OMBRE_COMPRESS_API_KEY": "new-key",
        "OMBRE_COMPRESS_TIMEOUT_SECONDS": "45",
        "OMBRE_COMPRESS_BASE_URL": "https://new.example/v1",
    }
    mcp = FakeMCP()
    config_api.register(mcp)

    response = await mcp.routes[("POST", "/api/env-config")](
        JsonRequest({"updates": updates})
    )
    payload = json.loads(response.body)

    assert payload["ok"] is True
    assert payload["partial"] is True
    assert payload["updated"] == list(updates)
    assert payload["persisted"] == []
    assert any(
        "config.yaml 持久化失败" in warning
        and "运行时已生效" in warning
        and "重启后可能恢复旧值" in warning
        for warning in payload["warnings"]
    )
    assert len(persistence_calls) == 1
    assert persistence_calls[0]["dehydration"] == {
        "model": "new-model",
        "api_key": "new-key",
        "timeout_seconds": "45",
        "base_url": "https://new.example/v1",
    }

    assert runtime_config["dehydration"]["api_key"] == "new-key"
    assert runtime_config["dehydration"]["base_url"] == "https://new.example/v1"
    assert runtime_config["dehydration"]["model"] == "new-model"
    assert dehydrator.api_key == "new-key"
    assert dehydrator.base_url == "https://new.example/v1"
    assert dehydrator.model == "new-model"
    assert dehydrator.timeout_seconds == 45.0
    assert dehydrator.api_available is True
    assert len(created_clients) == 1
    assert dehydrator.client is created_clients[0]
    assert created_clients[0].kwargs == {
        "api_key": "new-key",
        "base_url": "https://new.example/v1",
        "timeout": 45.0,
    }
    assert os.environ["OMBRE_COMPRESS_API_KEY"] == "new-key"
    assert os.environ["OMBRE_COMPRESS_BASE_URL"] == "https://new.example/v1"


@pytest.mark.asyncio
async def test_compress_client_rebuild_failure_is_not_reported_as_success(
    monkeypatch, tmp_path
):
    import openai

    def fail_client_rebuild(**kwargs):
        raise ValueError("invalid base URL")

    persistence_called = False

    def persist_unexpectedly(_mutate):
        nonlocal persistence_called
        persistence_called = True

    old_client = object()
    dehydrator = SimpleNamespace(
        api_key="old-key",
        base_url="https://old.example/v1",
        model="old-model",
        timeout_seconds=60.0,
        api_format="openai_compat",
        api_available=True,
        client=old_client,
    )
    runtime_config = {
        "dehydration": {
            "api_key": "old-key",
            "base_url": "https://old.example/v1",
            "model": "old-model",
            "timeout_seconds": 60,
            "api_format": "openai_compat",
        }
    }

    monkeypatch.setattr(config_api.sh, "_require_auth", lambda request: None)
    monkeypatch.setattr(
        config_api.sh, "_project_env_path", lambda: str(tmp_path / ".env")
    )
    monkeypatch.setattr(config_api.sh, "config", runtime_config)
    monkeypatch.setattr(config_api.sh, "dehydrator", dehydrator)
    monkeypatch.setattr(config_api, "atomic_update_config_yaml", persist_unexpectedly)
    monkeypatch.setattr(openai, "AsyncOpenAI", fail_client_rebuild)
    monkeypatch.setenv("OMBRE_COMPRESS_API_KEY", "old-key")
    monkeypatch.setenv("OMBRE_COMPRESS_BASE_URL", "https://old.example/v1")

    mcp = FakeMCP()
    config_api.register(mcp)
    response = await mcp.routes[("POST", "/api/env-config")](
        JsonRequest(
            {
                "updates": {
                    "OMBRE_COMPRESS_API_KEY": "new-key",
                    "OMBRE_COMPRESS_BASE_URL": "not-a-valid-base-url",
                }
            }
        )
    )
    payload = json.loads(response.body)

    assert payload["ok"] is False
    assert payload["partial"] is False
    assert payload["updated"] == []
    assert payload["persisted"] == []
    assert "压缩配置热更新失败" in payload["error"]
    assert "ValueError: invalid base URL" in payload["error"]
    assert persistence_called is False
    assert runtime_config["dehydration"]["api_key"] == "old-key"
    assert runtime_config["dehydration"]["base_url"] == "https://old.example/v1"
    assert dehydrator.api_key == "old-key"
    assert dehydrator.base_url == "https://old.example/v1"
    assert dehydrator.client is old_client
    assert os.environ["OMBRE_COMPRESS_API_KEY"] == "old-key"
    assert os.environ["OMBRE_COMPRESS_BASE_URL"] == "https://old.example/v1"


def test_v1_environment_names_remain_compatible(monkeypatch, tmp_path):
    monkeypatch.delenv("OMBRE_COMPRESS_API_KEY", raising=False)
    monkeypatch.delenv("OMBRE_COMPRESS_BASE_URL", raising=False)
    monkeypatch.delenv("OMBRE_DASHBOARD_PASSWORD", raising=False)
    monkeypatch.setenv("OMBRE_API_KEY", "legacy-key")
    monkeypatch.setenv("OMBRE_BASE_URL", "https://legacy.example/v1")
    monkeypatch.setenv("PASSWORD", "legacy-password")
    monkeypatch.setenv("OMBRE_VAULT_DIR", str(tmp_path / "vault"))
    monkeypatch.delenv("OMBRE_BUCKETS_DIR", raising=False)

    config = load_config(str(tmp_path / "missing-config.yaml"))

    assert config["dehydration"]["api_key"] == "legacy-key"
    assert config["dehydration"]["base_url"] == "https://legacy.example/v1"
    assert os.environ["OMBRE_DASHBOARD_PASSWORD"] == "legacy-password"
    assert config["media_dir"] == str(tmp_path / "vault" / "_media")


@pytest.mark.asyncio
async def test_embedding_provider_tuple_rebuilds_and_persists_once(
    monkeypatch, tmp_path
):
    runtime_config = {
        "embedding": {
            "enabled": True,
            "api_key": "old-key",
            "api_format": "ollama",
            "base_url": "",
            "model": "bge-m3",
        }
    }
    rebuild_snapshots = []
    persisted_configs = []

    def rebuild_once():
        rebuild_snapshots.append(dict(runtime_config["embedding"]))
        return SimpleNamespace(enabled=True)

    def persist_once(mutate):
        saved = {}
        mutate(saved)
        persisted_configs.append(saved)

    monkeypatch.setattr(config_api.sh, "_require_auth", lambda request: None)
    monkeypatch.setattr(
        config_api.sh, "_project_env_path", lambda: str(tmp_path / ".env")
    )
    monkeypatch.setattr(config_api.sh, "config", runtime_config)
    monkeypatch.setattr(
        config_api.sh, "embedding_engine", SimpleNamespace(enabled=True)
    )
    monkeypatch.setattr(config_api, "_rebuild_embedding_runtime", rebuild_once)
    monkeypatch.setattr(config_api, "atomic_update_config_yaml", persist_once)

    updates = {
        "OMBRE_EMBED_API_KEY": "new-key",
        "OMBRE_EMBED_BASE_URL": "https://api.siliconflow.cn/v1",
        "OMBRE_EMBED_MODEL": "BAAI/bge-m3",
        "OMBRE_EMBED_FORMAT": "openai_compat",
    }
    mcp = FakeMCP()
    config_api.register(mcp)
    response = await mcp.routes[("POST", "/api/env-config")](
        JsonRequest({"updates": updates})
    )
    payload = json.loads(response.body)

    assert payload["ok"] is True
    assert payload["partial"] is False
    assert payload["updated"] == list(updates)
    assert len(rebuild_snapshots) == 1
    assert rebuild_snapshots[0] == {
        "enabled": True,
        "api_key": "new-key",
        "api_format": "openai_compat",
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "BAAI/bge-m3",
    }
    assert len(persisted_configs) == 1
    assert persisted_configs[0]["embedding"]["api_key"] == "new-key"
    assert persisted_configs[0]["embedding"]["base_url"] == updates[
        "OMBRE_EMBED_BASE_URL"
    ]
    assert persisted_configs[0]["embedding"]["model"] == "BAAI/bge-m3"
    assert persisted_configs[0]["embedding"]["api_format"] == "openai_compat"
