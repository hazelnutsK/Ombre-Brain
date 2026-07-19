import asyncio
import json

import pytest

from tools import _common as common
from tools import _runtime as rt
from web import _shared as sh
from web import buckets as buckets_web
from web import import_api


class FakeMcp:
    def __init__(self):
        self.routes = {}

    def custom_route(self, path, methods):
        def decorator(handler):
            self.routes[path] = handler
            return handler

        return decorator


class FakeRequest:
    def __init__(self, *, path_params=None, body=None):
        self.path_params = path_params or {}
        self._body = body or {}
        self.headers = {}
        self.query_params = {}

    async def json(self):
        return self._body


class FakeBucketManager:
    def __init__(self):
        self.rows = {
            "already-pinned": self._row("already-pinned", pinned=True, bucket_type="permanent"),
            "plain": self._row("plain", pinned=False, bucket_type="dynamic"),
        }
        self.updates = []

    @staticmethod
    def _row(bucket_id, *, pinned, bucket_type):
        return {
            "id": bucket_id,
            "content": f"content for {bucket_id}",
            "metadata": {
                "id": bucket_id,
                "name": bucket_id,
                "pinned": pinned,
                "type": bucket_type,
                "importance": 10 if pinned else 5,
            },
        }

    async def list_all(self, include_archive=False):
        return list(self.rows.values())

    async def get(self, bucket_id):
        return self.rows.get(bucket_id)

    async def update(self, bucket_id, **updates):
        self.updates.append((bucket_id, updates))
        self.rows[bucket_id]["metadata"].update(updates)
        return True


class DummyLogger:
    def warning(self, *_args, **_kwargs):
        pass

    def info(self, *_args, **_kwargs):
        pass


@pytest.fixture
def pinned_quota_runtime(monkeypatch):
    bucket_mgr = FakeBucketManager()
    monkeypatch.setattr(sh, "bucket_mgr", bucket_mgr, raising=False)
    monkeypatch.setattr(sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(rt, "bucket_mgr", bucket_mgr, raising=False)
    monkeypatch.setattr(rt, "config", {"limits": {"max_pinned": 1}}, raising=False)
    monkeypatch.setattr(rt, "logger", DummyLogger(), raising=False)
    return bucket_mgr


def _json(response):
    return json.loads(response.body.decode("utf-8"))


@pytest.mark.asyncio
async def test_bucket_pin_route_rejects_new_pin_when_quota_is_full(pinned_quota_runtime):
    mcp = FakeMcp()
    buckets_web.register(mcp)

    response = await mcp.routes["/api/bucket/{bucket_id}/pin"](
        FakeRequest(path_params={"bucket_id": "plain"})
    )

    assert response.status_code == 400
    assert "error" in _json(response)
    assert pinned_quota_runtime.rows["plain"]["metadata"]["pinned"] is False
    assert pinned_quota_runtime.updates == []


@pytest.mark.asyncio
async def test_bucket_pin_route_rejects_archived_bucket(pinned_quota_runtime):
    metadata = pinned_quota_runtime.rows["plain"]["metadata"]
    metadata["type"] = "archived"
    mcp = FakeMcp()
    buckets_web.register(mcp)

    response = await mcp.routes["/api/bucket/{bucket_id}/pin"](
        FakeRequest(path_params={"bucket_id": "plain"})
    )

    assert response.status_code == 409
    assert metadata["type"] == "archived"
    assert metadata["pinned"] is False
    assert pinned_quota_runtime.updates == []


@pytest.mark.asyncio
async def test_import_review_pin_action_respects_pinned_quota(pinned_quota_runtime):
    mcp = FakeMcp()
    import_api.register(mcp)

    response = await mcp.routes["/api/import/review"](
        FakeRequest(body={"decisions": [{"bucket_id": "plain", "action": "pin"}]})
    )

    assert response.status_code == 200
    assert _json(response)["applied"] == 0
    assert _json(response)["errors"] == 1
    assert pinned_quota_runtime.rows["plain"]["metadata"]["pinned"] is False
    assert pinned_quota_runtime.updates == []


@pytest.mark.asyncio
async def test_import_review_pin_rejects_archived_bucket(pinned_quota_runtime):
    metadata = pinned_quota_runtime.rows["plain"]["metadata"]
    metadata["type"] = "archived"
    mcp = FakeMcp()
    import_api.register(mcp)

    response = await mcp.routes["/api/import/review"](
        FakeRequest(body={"decisions": [{"bucket_id": "plain", "action": "pin"}]})
    )

    assert response.status_code == 200
    assert _json(response) == {"applied": 0, "errors": 1}
    assert metadata["type"] == "archived"
    assert metadata["pinned"] is False
    assert pinned_quota_runtime.updates == []


@pytest.mark.asyncio
async def test_import_review_important_action_rejects_when_high_quota_is_full(
    pinned_quota_runtime,
    monkeypatch,
):
    high = pinned_quota_runtime.rows["already-pinned"]["metadata"]
    high.update({"pinned": False, "type": "dynamic", "importance": 9})
    monkeypatch.setattr(common, "_HIGH_IMP_HARD_CAP", 1)
    mcp = FakeMcp()
    import_api.register(mcp)

    response = await mcp.routes["/api/import/review"](
        FakeRequest(body={"decisions": [{"bucket_id": "plain", "action": "important"}]})
    )

    assert response.status_code == 200
    assert _json(response) == {"applied": 0, "errors": 1}
    assert pinned_quota_runtime.rows["plain"]["metadata"]["importance"] == 5


@pytest.mark.asyncio
async def test_import_review_special_bucket_does_not_consume_ordinary_high_slot(
    pinned_quota_runtime,
    monkeypatch,
):
    high = pinned_quota_runtime.rows["already-pinned"]["metadata"]
    high.update({"pinned": False, "type": "dynamic", "importance": 9})
    special = pinned_quota_runtime.rows["plain"]["metadata"]
    special.update({"type": "feel", "importance": 5})
    monkeypatch.setattr(common, "_HIGH_IMP_HARD_CAP", 1)
    mcp = FakeMcp()
    import_api.register(mcp)

    response = await mcp.routes["/api/import/review"](
        FakeRequest(body={"decisions": [{"bucket_id": "plain", "action": "important"}]})
    )

    assert response.status_code == 200
    assert _json(response) == {"applied": 1, "errors": 0}
    assert special["importance"] == 9


@pytest.mark.asyncio
async def test_bucket_unpin_ignores_hidden_and_special_high_rows(
    pinned_quota_runtime,
    monkeypatch,
):
    for index in range(30):
        row = FakeBucketManager._row(
            f"hidden-{index}", pinned=False, bucket_type="dynamic"
        )
        row["metadata"].update({"importance": 9, "dont_surface": True})
        pinned_quota_runtime.rows[row["id"]] = row
    for index in range(30):
        row = FakeBucketManager._row(
            f"feel-{index}", pinned=False, bucket_type="feel"
        )
        row["metadata"]["importance"] = 9
        pinned_quota_runtime.rows[row["id"]] = row
    monkeypatch.setattr(common, "_HIGH_IMP_HARD_CAP", 1)
    mcp = FakeMcp()
    buckets_web.register(mcp)

    response = await mcp.routes["/api/bucket/{bucket_id}/pin"](
        FakeRequest(path_params={"bucket_id": "already-pinned"})
    )

    assert response.status_code == 200
    payload = _json(response)
    assert payload["pinned"] is False
    assert payload["importance"] == 10
    assert pinned_quota_runtime.updates[-1] == (
        "already-pinned",
        {"pinned": False},
    )


@pytest.mark.asyncio
async def test_single_unforget_reserves_high_importance_slot(
    pinned_quota_runtime,
    monkeypatch,
):
    existing = pinned_quota_runtime.rows["already-pinned"]["metadata"]
    existing.update({"pinned": False, "type": "dynamic", "importance": 9})
    hidden = pinned_quota_runtime.rows["plain"]["metadata"]
    hidden.update({"importance": 10, "dont_surface": True})
    monkeypatch.setattr(common, "_HIGH_IMP_HARD_CAP", 1)
    monkeypatch.setattr(common, "_HIGH_IMP_SOFT_WARN", 1)
    mcp = FakeMcp()
    buckets_web.register(mcp)

    response = await mcp.routes["/api/bucket/{bucket_id}/forget"](
        FakeRequest(path_params={"bucket_id": "plain"})
    )

    assert response.status_code == 200
    assert _json(response)["quota_adjustment"] == {
        "requested": 10,
        "applied": 8,
    }
    assert hidden["dont_surface"] is False
    assert hidden["importance"] == 8


@pytest.mark.asyncio
async def test_batch_unforget_serializes_each_new_high_slot(
    pinned_quota_runtime,
    monkeypatch,
):
    first = pinned_quota_runtime.rows["already-pinned"]["metadata"]
    first.update({
        "pinned": False,
        "type": "dynamic",
        "importance": 9,
        "dont_surface": True,
    })
    second = pinned_quota_runtime.rows["plain"]["metadata"]
    second.update({"importance": 10, "dont_surface": True})
    monkeypatch.setattr(common, "_HIGH_IMP_HARD_CAP", 1)
    monkeypatch.setattr(common, "_HIGH_IMP_SOFT_WARN", 1)
    mcp = FakeMcp()
    buckets_web.register(mcp)

    response = await mcp.routes["/api/buckets/forget"](
        FakeRequest(
            body={
                "ids": ["already-pinned", "plain"],
                "dont_surface": False,
            }
        )
    )

    payload = _json(response)
    assert response.status_code == 200
    assert payload["updated"] == ["already-pinned", "plain"]
    assert payload["quota_adjustments"] == [
        {"id": "plain", "requested": 10, "applied": 8}
    ]
    assert first["dont_surface"] is False
    assert first["importance"] == 9
    assert second["dont_surface"] is False
    assert second["importance"] == 8


@pytest.mark.asyncio
async def test_concurrent_unpin_and_unforget_cannot_create_unchecked_high_slot(
    pinned_quota_runtime,
    monkeypatch,
):
    existing = pinned_quota_runtime.rows["plain"]["metadata"]
    existing.update({"type": "dynamic", "importance": 9})
    target = pinned_quota_runtime.rows["already-pinned"]["metadata"]
    target["dont_surface"] = True
    monkeypatch.setattr(common, "_HIGH_IMP_HARD_CAP", 1)
    monkeypatch.setattr(common, "_HIGH_IMP_SOFT_WARN", 1)
    mcp = FakeMcp()
    buckets_web.register(mcp)

    responses = await asyncio.gather(
        mcp.routes["/api/bucket/{bucket_id}/pin"](
            FakeRequest(path_params={"bucket_id": "already-pinned"})
        ),
        mcp.routes["/api/bucket/{bucket_id}/forget"](
            FakeRequest(path_params={"bucket_id": "already-pinned"})
        ),
    )

    assert [response.status_code for response in responses] == [200, 200]
    assert target["pinned"] is False
    assert target["dont_surface"] is False
    assert target["importance"] == 8


@pytest.mark.asyncio
async def test_concurrent_import_review_pins_share_check_and_write_lock(
    pinned_quota_runtime,
    monkeypatch,
):
    first = pinned_quota_runtime.rows["already-pinned"]["metadata"]
    first.update({"pinned": False, "type": "dynamic", "importance": 5})
    monkeypatch.setattr(rt, "config", {"limits": {"max_pinned": 1}})
    mcp = FakeMcp()
    import_api.register(mcp)

    responses = await asyncio.gather(
        mcp.routes["/api/import/review"](
            FakeRequest(
                body={
                    "decisions": [
                        {"bucket_id": "already-pinned", "action": "pin"}
                    ]
                }
            )
        ),
        mcp.routes["/api/import/review"](
            FakeRequest(
                body={"decisions": [{"bucket_id": "plain", "action": "pin"}]}
            )
        ),
    )

    payloads = [_json(response) for response in responses]
    assert sum(payload["applied"] for payload in payloads) == 1
    assert sum(payload["errors"] for payload in payloads) == 1
    assert sum(
        bool(row["metadata"].get("pinned"))
        for row in pinned_quota_runtime.rows.values()
    ) == 1


@pytest.mark.asyncio
async def test_import_review_does_not_count_failed_update_as_applied(
    pinned_quota_runtime,
    monkeypatch,
):
    monkeypatch.setattr(rt, "config", {"limits": {"max_pinned": 2}})

    async def failed_update(bucket_id, **updates):
        pinned_quota_runtime.updates.append((bucket_id, updates))
        return False

    monkeypatch.setattr(pinned_quota_runtime, "update", failed_update)
    mcp = FakeMcp()
    import_api.register(mcp)

    response = await mcp.routes["/api/import/review"](
        FakeRequest(body={"decisions": [{"bucket_id": "plain", "action": "pin"}]})
    )

    assert response.status_code == 200
    assert _json(response) == {"applied": 0, "errors": 1}
    assert pinned_quota_runtime.rows["plain"]["metadata"]["pinned"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["unknown", "archive-now"])
async def test_import_review_unknown_action_is_an_error(
    pinned_quota_runtime,
    action,
):
    mcp = FakeMcp()
    import_api.register(mcp)

    response = await mcp.routes["/api/import/review"](
        FakeRequest(body={"decisions": [{"bucket_id": "plain", "action": action}]})
    )

    assert response.status_code == 200
    assert _json(response) == {"applied": 0, "errors": 1}
    assert pinned_quota_runtime.updates == []


@pytest.mark.asyncio
async def test_import_review_delete_false_is_not_counted_as_applied(
    pinned_quota_runtime,
    monkeypatch,
):
    async def failed_delete(_bucket_id):
        return False

    monkeypatch.setattr(
        pinned_quota_runtime,
        "delete",
        failed_delete,
        raising=False,
    )
    mcp = FakeMcp()
    import_api.register(mcp)

    response = await mcp.routes["/api/import/review"](
        FakeRequest(body={"decisions": [{"bucket_id": "plain", "action": "delete"}]})
    )

    assert response.status_code == 200
    assert _json(response) == {"applied": 0, "errors": 1}


@pytest.mark.asyncio
async def test_import_review_noise_rejects_locked_bucket_without_partial_write(
    pinned_quota_runtime,
):
    mcp = FakeMcp()
    import_api.register(mcp)

    response = await mcp.routes["/api/import/review"](
        FakeRequest(
            body={
                "decisions": [
                    {"bucket_id": "already-pinned", "action": "noise"}
                ]
            }
        )
    )

    assert response.status_code == 200
    assert _json(response) == {"applied": 0, "errors": 1}
    metadata = pinned_quota_runtime.rows["already-pinned"]["metadata"]
    assert metadata["importance"] == 10
    assert metadata.get("resolved") is not True
    assert pinned_quota_runtime.updates == []
