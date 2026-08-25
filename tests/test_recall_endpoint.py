"""Regressions for /api/recall — the per-turn automatic surfacing endpoint.

Recall 与 breath_search 共享同一条可见性边界，但走的是 HTTP：换了入口不能多露
东西，也不能在调用方还没决定浮现哪几条之前就把桶 touch 掉。
"""

import asyncio
import json
import threading

import pytest

from web import hooks


class _MCP:
    def __init__(self):
        self.routes = {}

    def custom_route(self, path, methods):
        def decorator(handler):
            for method in methods:
                self.routes[(method, path)] = handler
            return handler

        return decorator


class _Request:
    def __init__(self, body=None, *, token="secret", source="client"):
        self.source = source
        self.headers = {}
        if token:
            self.headers["x-ombre-hook-token"] = token
        self._body = {} if body is None else body

    async def json(self):
        if isinstance(self._body, str):
            return json.loads(self._body)
        return self._body


class _Manager:
    def __init__(self, buckets):
        self.buckets = buckets
        self.searched = []
        self.touched = []

    async def search(self, query, limit=20, **kwargs):
        self.searched.append((query, limit, kwargs))
        return list(self.buckets)

    async def list_all(self, include_archive=False):
        return list(self.buckets)

    async def touch_many(self, ids, ripple=True):
        self.touched.append((list(ids), ripple))


class _Decay:
    @staticmethod
    def calculate_score(metadata):
        return float(metadata.get("importance", 0))


class _Engine:
    enabled = True

    def __init__(self, pairs=None, fail=False):
        self.pairs = pairs or []
        self.fail = fail

    async def search_similar(self, query, top_k=50):
        if self.fail:
            raise RuntimeError("vector backend down")
        return list(self.pairs)


def _bucket(bucket_id, content, **metadata):
    base = {
        "id": bucket_id,
        "name": bucket_id,
        "type": "dynamic",
        "importance": 5,
        "created": "2026-08-25T00:00:00",
        "domain": ["她"],
        "tags": [],
    }
    base.update(metadata)
    return {"id": bucket_id, "content": content, "metadata": base}


@pytest.fixture(autouse=True)
def _recall_runtime(monkeypatch):
    monkeypatch.setenv("OMBRE_HOOK_TOKEN", "secret")
    monkeypatch.delenv("OMBRE_HOOK_ALLOW_PUBLIC", raising=False)
    monkeypatch.setattr(hooks, "_recall_slots", threading.BoundedSemaphore(4))
    with hooks._hook_rate_lock:
        hooks._hook_source_events.clear()
        hooks._hook_global_events.clear()
    monkeypatch.setattr(hooks.sh, "_client_key", lambda request: request.source)
    monkeypatch.setattr(hooks.sh, "decay_engine", _Decay(), raising=False)
    monkeypatch.setattr(hooks.sh, "embedding_engine", _Engine(), raising=False)


def _routes(monkeypatch, buckets):
    manager = _Manager(buckets)
    monkeypatch.setattr(hooks.sh, "config", {"hooks": {"token": "secret"}})
    monkeypatch.setattr(hooks.sh, "bucket_mgr", manager, raising=False)
    mcp = _MCP()
    hooks.register(mcp)
    return mcp.routes, manager


def _recall(monkeypatch, buckets):
    routes, manager = _routes(monkeypatch, buckets)
    return routes[("POST", "/api/recall")], manager


def _payload(response):
    return json.loads(response.body.decode("utf-8"))


@pytest.mark.asyncio
async def test_recall_rejects_requests_without_hook_token(monkeypatch):
    handler, manager = _recall(monkeypatch, [_bucket("a", "记忆")])
    response = await handler(_Request({"query": "猫"}, token=""))

    assert response.status_code == 401
    assert manager.searched == []


@pytest.mark.asyncio
async def test_recall_rejects_empty_query(monkeypatch):
    handler, manager = _recall(monkeypatch, [_bucket("a", "记忆")])
    response = await handler(_Request({"query": "   "}))

    assert response.status_code == 400
    assert _payload(response)["error"] == "empty_query"
    assert manager.searched == []


@pytest.mark.asyncio
async def test_recall_returns_structured_cards_without_touching(monkeypatch):
    buckets = [
        _bucket("cat", "她养的猫叫 onion", importance=8),
        _bucket("autumn", "她喜欢秋天，凉爽的天气", pinned=True),
    ]
    handler, manager = _recall(monkeypatch, buckets)
    response = await handler(_Request({"query": "猫 秋天"}))
    body = _payload(response)

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert [card["id"] for card in body["cards"]] == ["cat", "autumn"]
    assert body["cards"][0]["content"] == "她养的猫叫 onion"
    assert body["cards"][0]["rank"] == 0
    assert body["cards"][1]["pinned"] is True
    assert body["degraded"] == ""
    # 关键：候选还没经过调用方的冷却过滤，此刻加固就是虚假激活。
    assert manager.touched == []


@pytest.mark.asyncio
async def test_recall_never_returns_dedicated_channel_buckets(monkeypatch):
    buckets = [
        _bucket("feel", "一闪的感受", type="feel"),
        _bucket("plan", "待办", type="plan"),
        _bucket("letter", "一封信", type="letter"),
        _bucket("ok", "普通记忆"),
    ]
    handler, _ = _recall(monkeypatch, buckets)
    body = _payload(await handler(_Request({"query": "任何"})))

    assert [card["id"] for card in body["cards"]] == ["ok"]


@pytest.mark.asyncio
async def test_recall_drops_whole_bucket_instead_of_truncating(monkeypatch):
    buckets = [
        _bucket("short", "十个字的记忆内容啊"),
        _bucket("long", "超" * 500),
    ]
    handler, _ = _recall(monkeypatch, buckets)
    body = _payload(await handler(_Request({"query": "记忆", "max_chars": 200})))

    assert [card["id"] for card in body["cards"]] == ["short"]
    assert all(len(card["content"]) < 200 for card in body["cards"])


@pytest.mark.asyncio
async def test_recall_clamps_max_results(monkeypatch):
    buckets = [_bucket(f"b{i}", f"记忆 {i}") for i in range(30)]
    handler, _ = _recall(monkeypatch, buckets)
    body = _payload(await handler(_Request({"query": "记忆", "max_results": 999})))

    assert len(body["cards"]) == 20


@pytest.mark.asyncio
async def test_recall_degrades_when_vector_backend_fails(monkeypatch):
    monkeypatch.setattr(hooks.sh, "embedding_engine", _Engine(fail=True), raising=False)
    handler, manager = _recall(monkeypatch, [_bucket("a", "关键词也能命中")])
    body = _payload(await handler(_Request({"query": "关键词"})))

    assert body["degraded"] == "semantic_unavailable"
    assert [card["id"] for card in body["cards"]] == ["a"]
    # 降级不等于放弃：关键词/BM25 通道照常查。
    assert manager.searched and manager.searched[0][2]["vector_scores"] == {}


@pytest.mark.asyncio
async def test_confirm_touches_only_reported_ids(monkeypatch):
    routes, manager = _routes(monkeypatch, [_bucket("a", "记忆")])
    handler = routes[("POST", "/api/recall/confirm")]
    response = await handler(_Request({"ids": ["cat", "autumn", ""]}))
    await asyncio.sleep(0)

    assert response.status_code == 202
    assert _payload(response)["touched"] == 2
    assert manager.touched == [(["cat", "autumn"], False)]


@pytest.mark.asyncio
async def test_confirm_rejects_non_list_ids(monkeypatch):
    routes, manager = _routes(monkeypatch, [_bucket("a", "记忆")])
    response = await routes[("POST", "/api/recall/confirm")](_Request({"ids": "cat"}))

    assert response.status_code == 400
    assert manager.touched == []
