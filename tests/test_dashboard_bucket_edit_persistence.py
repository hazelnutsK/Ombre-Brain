import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import _common as common
from tools import _runtime as rt
from web import import_api


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
    def __init__(self, bucket_id, body):
        self.path_params = {"bucket_id": bucket_id}
        self._body = body
        self.headers = {}
        self.query_params = {}

    async def json(self):
        return self._body


class MutableBucketManager:
    def __init__(self, row, *, on_update=None, apply_updates=True):
        self.row = row
        self.on_update = on_update
        self.apply_updates = apply_updates
        self.updates = []

    async def get(self, bucket_id):
        return self.row if bucket_id == self.row["id"] else None

    async def update(self, bucket_id, **updates):
        assert bucket_id == self.row["id"]
        if self.on_update is not None:
            self.on_update(updates)
        self.updates.append(dict(updates))
        if not self.apply_updates:
            return True

        metadata = self.row["metadata"]
        was_pinned = bool(metadata.get("pinned", False))
        was_protected = bool(metadata.get("protected", False))
        for field, value in updates.items():
            if field == "content":
                self.row["content"] = value
            else:
                metadata[field] = value

        if updates.get("pinned") is True:
            metadata["importance"] = 10
            metadata["type"] = "permanent"
        elif (
            updates.get("pinned") is False
            and was_pinned
            and not was_protected
            and metadata.get("type") == "permanent"
        ):
            metadata["type"] = "dynamic"
        return True


def _row(
    bucket_id="bucket-1",
    *,
    bucket_type="dynamic",
    pinned=False,
    protected=False,
    importance=None,
):
    return {
        "id": bucket_id,
        "content": "original content",
        "metadata": {
            "id": bucket_id,
            "name": "Original memory",
            "type": bucket_type,
            "tags": ["old"],
            "domain": ["work"],
            "importance": importance if importance is not None else (10 if pinned else 5),
            "resolved": False,
            "pinned": pinned,
            "protected": protected,
            "digested": False,
        },
    }


def _json(response):
    return json.loads(response.body.decode("utf-8"))


def _edit_handler(monkeypatch, manager):
    monkeypatch.setattr(import_api.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(import_api.sh, "bucket_mgr", manager, raising=False)
    monkeypatch.setattr(
        import_api.sh,
        "dehydrator",
        SimpleNamespace(invalidate_cache=lambda _content: None),
        raising=False,
    )
    mcp = FakeMCP()
    import_api.register(mcp)
    return mcp.routes[("PATCH", "/api/bucket/{bucket_id}/edit")]


@pytest.mark.asyncio
async def test_dashboard_edit_persists_surface_reason_and_plan_weight(
    monkeypatch,
    bucket_mgr,
):
    bucket_id = await bucket_mgr.create(
        "plan body",
        bucket_type="plan",
        name="Plan memory",
        tags=["old"],
        domain=["work"],
        importance=6,
        why_remembered="old reason",
        weight=0.25,
    )
    before = await bucket_mgr.get(bucket_id)
    metadata = before["metadata"]
    handler = _edit_handler(monkeypatch, bucket_mgr)

    # Mirrors the Dashboard form: it submits all visible fields, including
    # unchanged values, while these three fields are the actual edit.
    body = {
        "name": metadata["name"],
        "type": metadata["type"],
        "tags": metadata["tags"],
        "domain": metadata["domain"],
        "importance": metadata["importance"],
        "resolved": metadata.get("resolved", False),
        "pinned": metadata.get("pinned", False),
        "digested": metadata.get("digested", False),
        "dont_surface": True,
        "why_remembered": "needed for the next review",
        "weight": 0.8,
        "content": before["content"],
    }
    response = await handler(JsonRequest(bucket_id, body))

    assert response.status_code == 200
    assert _json(response)["updated"] == [
        "dont_surface",
        "why_remembered",
        "weight",
    ]
    persisted = await bucket_mgr.get(bucket_id)
    assert persisted["metadata"]["dont_surface"] is True
    assert persisted["metadata"]["why_remembered"] == "needed for the next review"
    assert persisted["metadata"]["weight"] == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_dashboard_edit_rejects_unknown_fields_without_partial_write(monkeypatch):
    manager = MutableBucketManager(_row())
    handler = _edit_handler(monkeypatch, manager)

    response = await handler(
        JsonRequest("bucket-1", {"name": "Changed", "future_field": "ignored before"})
    )

    payload = _json(response)
    assert response.status_code == 400
    assert payload["ok"] is False
    assert payload["updated"] == []
    assert payload["unknown_fields"] == ["future_field"]
    assert manager.updates == []
    assert manager.row["metadata"]["name"] == "Original memory"


@pytest.mark.asyncio
async def test_dashboard_edit_rejects_archived_bucket_without_resurrecting_it(
    monkeypatch,
):
    manager = MutableBucketManager(_row(bucket_type="archived"))
    handler = _edit_handler(monkeypatch, manager)

    response = await handler(
        JsonRequest("bucket-1", {"name": "must stay archived", "pinned": True})
    )

    payload = _json(response)
    assert response.status_code == 409
    assert payload["conflict"] == "archived"
    assert payload["updated"] == []
    assert manager.updates == []
    assert manager.row["metadata"]["type"] == "archived"


@pytest.mark.asyncio
async def test_dashboard_edit_reports_manager_ignored_field_as_not_applied(monkeypatch):
    manager = MutableBucketManager(_row(), apply_updates=False)
    handler = _edit_handler(monkeypatch, manager)

    response = await handler(JsonRequest("bucket-1", {"dont_surface": True}))

    payload = _json(response)
    assert response.status_code == 409
    assert payload["ok"] is False
    assert payload["updated"] == []
    assert payload["not_applied"] == ["dont_surface"]
    assert manager.updates == [{"dont_surface": True}]


@pytest.mark.asyncio
async def test_dashboard_edit_does_not_claim_pinned_importance_was_changed(monkeypatch):
    manager = MutableBucketManager(_row(bucket_type="permanent", pinned=True))
    handler = _edit_handler(monkeypatch, manager)

    response = await handler(JsonRequest("bucket-1", {"importance": 4}))

    payload = _json(response)
    assert response.status_code == 409
    assert payload["ok"] is False
    assert payload["field"] == "importance"
    assert payload["updated"] == []
    assert manager.updates == []
    assert manager.row["metadata"]["importance"] == 10


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("raw_type", "expected_type", "expected_top_dir"),
    [
        (" PLAN ", "plan", "plans"),
        (" SELF ", "self", "dynamic"),
    ],
)
async def test_dashboard_edit_normalizes_and_persists_safe_type_migration(
    monkeypatch,
    bucket_mgr,
    raw_type,
    expected_type,
    expected_top_dir,
):
    bucket_id = await bucket_mgr.create(
        "type migration body",
        bucket_type="dynamic",
        name="Migrating memory",
        domain=["work"],
    )
    handler = _edit_handler(monkeypatch, bucket_mgr)

    response = await handler(JsonRequest(bucket_id, {"type": raw_type}))

    assert response.status_code == 200
    assert _json(response)["updated"] == ["type"]
    persisted = await bucket_mgr.get(bucket_id)
    assert persisted["metadata"]["type"] == expected_type
    persisted_path = Path(bucket_mgr._find_bucket_file(bucket_id))
    assert expected_top_dir in persisted_path.parts


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_type", ["archived", "system", ""])
async def test_dashboard_edit_rejects_non_editable_types(monkeypatch, invalid_type):
    manager = MutableBucketManager(_row())
    handler = _edit_handler(monkeypatch, manager)

    response = await handler(JsonRequest("bucket-1", {"type": invalid_type}))

    assert response.status_code == 400
    assert _json(response)["updated"] == []
    assert manager.updates == []


@pytest.mark.asyncio
@pytest.mark.parametrize("protected", [False, True])
async def test_dashboard_edit_rejects_pinned_or_protected_non_permanent_type(
    monkeypatch,
    protected,
):
    manager = MutableBucketManager(
        _row(bucket_type="permanent", pinned=not protected, protected=protected)
    )
    handler = _edit_handler(monkeypatch, manager)

    response = await handler(JsonRequest("bucket-1", {"type": "feel"}))

    payload = _json(response)
    assert response.status_code == 409
    assert payload["field"] == "type"
    assert payload["updated"] == []
    assert manager.updates == []


@pytest.mark.asyncio
async def test_dashboard_edit_atomically_unpins_demotes_and_persists_fields(
    monkeypatch,
    bucket_mgr,
):
    bucket_id = await bucket_mgr.create(
        "atomic unpin body",
        bucket_type="permanent",
        pinned=True,
        name="Pinned memory",
        domain=["old-domain"],
    )
    old_path = Path(bucket_mgr._find_bucket_file(bucket_id))
    assert "permanent" in old_path.parts
    handler = _edit_handler(monkeypatch, bucket_mgr)

    response = await handler(
        JsonRequest(
            bucket_id,
            {
                "type": "dynamic",
                "domain": ["new-domain"],
                "importance": 8,
                "pinned": False,
            },
        )
    )

    payload = _json(response)
    assert response.status_code == 200
    assert payload["updated"] == ["type", "domain", "importance", "pinned"]
    persisted = await bucket_mgr.get(bucket_id)
    assert persisted["metadata"]["type"] == "dynamic"
    assert persisted["metadata"]["domain"] == ["new-domain"]
    assert persisted["metadata"]["importance"] == 8
    assert persisted["metadata"]["pinned"] is False
    new_path = Path(bucket_mgr._find_bucket_file(bucket_id))
    assert "dynamic" in new_path.parts
    assert new_path != old_path
    assert not old_path.exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("protected", "requested_type", "pin_field"),
    [
        (False, "dynamic", None),
        (False, "dynamic", True),
        (False, "feel", False),
        (True, "dynamic", False),
    ],
)
async def test_dashboard_edit_requires_explicit_compatible_unpin_transition(
    monkeypatch,
    protected,
    requested_type,
    pin_field,
):
    manager = MutableBucketManager(
        _row(
            bucket_type="permanent",
            pinned=not protected,
            protected=protected,
            importance=10,
        )
    )
    handler = _edit_handler(monkeypatch, manager)
    body = {"type": requested_type, "importance": 8}
    if pin_field is not None:
        body["pinned"] = pin_field

    response = await handler(JsonRequest("bucket-1", body))

    payload = _json(response)
    assert response.status_code == 409
    assert payload["field"] == "type"
    assert payload["updated"] == []
    assert manager.updates == []
    assert manager.row["metadata"]["type"] == "permanent"
    assert manager.row["metadata"]["importance"] == 10


@pytest.mark.asyncio
async def test_dashboard_pin_holds_shared_quota_lock_through_check_and_write(
    monkeypatch,
):
    state = {"held": [], "events": []}

    @asynccontextmanager
    async def quota_turn(name):
        if name == "pinned":
            assert state["held"] == []
        else:
            assert name == "high_importance"
            assert state["held"] == ["pinned"]
        state["held"].append(name)
        state["events"].append(f"enter:{name}")
        try:
            yield
        finally:
            assert state["held"][-1] == name
            state["events"].append(f"exit:{name}")
            state["held"].pop()

    async def check_quota():
        assert state["held"] == ["pinned", "high_importance"]
        state["events"].append("check")
        return None

    def on_update(_updates):
        assert state["held"] == ["pinned", "high_importance"]
        state["events"].append("write")

    manager = MutableBucketManager(_row(), on_update=on_update)
    handler = _edit_handler(monkeypatch, manager)
    monkeypatch.setattr(import_api, "_quota_turn", quota_turn)
    monkeypatch.setattr(import_api, "_check_pinned_quota", check_quota)

    response = await handler(
        JsonRequest(
            "bucket-1",
            {"type": "dynamic", "importance": 5, "pinned": True},
        )
    )

    assert response.status_code == 200
    assert _json(response)["updated"] == ["type", "importance", "pinned"]
    assert state["events"] == [
        "enter:pinned",
        "enter:high_importance",
        "check",
        "write",
        "exit:high_importance",
        "exit:pinned",
    ]
    assert manager.updates == [{"pinned": True}]


@pytest.mark.asyncio
async def test_dashboard_unpin_uses_pinned_then_high_importance_lock_and_demotes(
    monkeypatch,
):
    state = {"held": [], "events": []}

    @asynccontextmanager
    async def quota_turn(name):
        state["held"].append(name)
        state["events"].append(f"enter:{name}")
        try:
            yield
        finally:
            assert state["held"][-1] == name
            state["events"].append(f"exit:{name}")
            state["held"].pop()

    async def enforce_high_importance(importance):
        assert importance == 10
        assert state["held"] == ["pinned", "high_importance"]
        state["events"].append("enforce")
        return 8

    def on_update(updates):
        assert state["held"] == ["pinned", "high_importance"]
        assert updates == {"pinned": False, "importance": 8}
        state["events"].append("write")

    manager = MutableBucketManager(
        _row(bucket_type="permanent", pinned=True),
        on_update=on_update,
    )
    handler = _edit_handler(monkeypatch, manager)
    monkeypatch.setattr(import_api, "_quota_turn", quota_turn)
    monkeypatch.setattr(
        import_api,
        "_enforce_high_importance_quota",
        enforce_high_importance,
    )

    response = await handler(
        JsonRequest(
            "bucket-1",
            {"type": "permanent", "importance": 10, "pinned": False},
        )
    )

    payload = _json(response)
    assert response.status_code == 200
    assert payload["updated"] == ["type", "importance", "pinned"]
    assert payload["quota_adjustment"] == {
        "field": "importance",
        "requested": 10,
        "applied": 8,
    }
    assert state["events"] == [
        "enter:pinned",
        "enter:high_importance",
        "enforce",
        "write",
        "exit:high_importance",
        "exit:pinned",
    ]


@pytest.mark.asyncio
async def test_dashboard_high_importance_edit_enforces_quota_inside_write_lock(
    monkeypatch,
):
    state = {"inside": False, "events": []}

    @asynccontextmanager
    async def quota_turn(name):
        assert name == "high_importance"
        state["inside"] = True
        state["events"].append("enter")
        try:
            yield
        finally:
            state["events"].append("exit")
            state["inside"] = False

    async def enforce_high_importance(importance):
        assert state["inside"] is True
        assert importance == 9
        state["events"].append("enforce")
        return 9

    def on_update(updates):
        assert state["inside"] is True
        assert updates == {"importance": 9}
        state["events"].append("write")

    manager = MutableBucketManager(_row(importance=5), on_update=on_update)
    handler = _edit_handler(monkeypatch, manager)
    monkeypatch.setattr(import_api, "_quota_turn", quota_turn)
    monkeypatch.setattr(
        import_api,
        "_enforce_high_importance_quota",
        enforce_high_importance,
    )

    response = await handler(JsonRequest("bucket-1", {"importance": 9}))

    assert response.status_code == 200
    assert _json(response)["updated"] == ["importance"]
    assert state["events"] == ["enter", "enforce", "write", "exit"]


@pytest.mark.asyncio
async def test_dashboard_unforget_reserves_high_importance_slot(monkeypatch):
    state = {"inside": False}

    @asynccontextmanager
    async def quota_turn(name):
        assert name == "high_importance"
        state["inside"] = True
        try:
            yield
        finally:
            state["inside"] = False

    async def enforce_high_importance(importance):
        assert state["inside"] is True
        assert importance == 10
        return 8

    def on_update(updates):
        assert state["inside"] is True
        assert updates == {"dont_surface": False, "importance": 8}

    row = _row(importance=10)
    row["metadata"]["dont_surface"] = True
    manager = MutableBucketManager(row, on_update=on_update)
    handler = _edit_handler(monkeypatch, manager)
    monkeypatch.setattr(import_api, "_quota_turn", quota_turn)
    monkeypatch.setattr(
        import_api,
        "_enforce_high_importance_quota",
        enforce_high_importance,
    )

    response = await handler(JsonRequest("bucket-1", {"dont_surface": False}))

    payload = _json(response)
    assert response.status_code == 200
    assert payload["updated"] == ["importance", "dont_surface"]
    assert payload["quota_adjustment"] == {
        "field": "importance",
        "requested": 10,
        "applied": 8,
    }


@pytest.mark.asyncio
async def test_dashboard_special_to_dynamic_transition_reserves_high_slot(
    monkeypatch,
):
    state = {"inside": False}

    @asynccontextmanager
    async def quota_turn(name):
        assert name == "high_importance"
        state["inside"] = True
        try:
            yield
        finally:
            state["inside"] = False

    async def enforce_high_importance(importance):
        assert state["inside"] is True
        assert importance == 9
        return 8

    def on_update(updates):
        assert state["inside"] is True
        assert updates == {"type": "dynamic", "importance": 8}

    manager = MutableBucketManager(
        _row(bucket_type="feel", importance=9),
        on_update=on_update,
    )
    handler = _edit_handler(monkeypatch, manager)
    monkeypatch.setattr(import_api, "_quota_turn", quota_turn)
    monkeypatch.setattr(
        import_api,
        "_enforce_high_importance_quota",
        enforce_high_importance,
    )

    response = await handler(JsonRequest("bucket-1", {"type": "dynamic"}))

    payload = _json(response)
    assert response.status_code == 200
    assert payload["updated"] == ["type", "importance"]
    assert payload["quota_adjustment"] == {
        "field": "importance",
        "requested": 9,
        "applied": 8,
    }


@pytest.mark.asyncio
async def test_concurrent_dashboard_high_importance_edits_cannot_exceed_hard_cap(
    monkeypatch,
    bucket_mgr,
):
    first_id = await bucket_mgr.create(
        "first low importance memory",
        importance=5,
        name="First",
    )
    second_id = await bucket_mgr.create(
        "second low importance memory",
        importance=5,
        name="Second",
    )
    handler = _edit_handler(monkeypatch, bucket_mgr)
    monkeypatch.setattr(rt, "bucket_mgr", bucket_mgr, raising=False)
    monkeypatch.setattr(rt, "config", bucket_mgr.config, raising=False)
    monkeypatch.setattr(
        rt,
        "logger",
        SimpleNamespace(info=lambda *_a, **_k: None, warning=lambda *_a, **_k: None),
        raising=False,
    )
    monkeypatch.setattr(common, "_HIGH_IMP_HARD_CAP", 1)

    responses = await asyncio.gather(
        handler(JsonRequest(first_id, {"importance": 9})),
        handler(JsonRequest(second_id, {"importance": 9})),
    )

    assert [response.status_code for response in responses] == [200, 200], [
        _json(response) for response in responses
    ]
    persisted = [
        await bucket_mgr.get(first_id),
        await bucket_mgr.get(second_id),
    ]
    importances = sorted(row["metadata"]["importance"] for row in persisted)
    assert importances == [8, 9]
    assert await common.count_high_importance() == 1
    adjustments = [
        _json(response).get("quota_adjustment") for response in responses
    ]
    assert sum(adjustment is not None for adjustment in adjustments) == 1


@pytest.mark.asyncio
async def test_concurrent_same_bucket_promotion_rejects_stale_snapshot(
    monkeypatch,
    bucket_mgr,
):
    bucket_id = await bucket_mgr.create(
        "same bucket promotion race",
        importance=5,
    )

    class InitialReadBarrier:
        def __init__(self, inner):
            self.inner = inner
            self.initial_reads = 0
            self.both_read = asyncio.Event()

        def __getattr__(self, name):
            return getattr(self.inner, name)

        async def get(self, requested_id):
            row = await self.inner.get(requested_id)
            if self.initial_reads < 2:
                self.initial_reads += 1
                if self.initial_reads == 2:
                    self.both_read.set()
                else:
                    await self.both_read.wait()
            return row

    manager = InitialReadBarrier(bucket_mgr)
    handler = _edit_handler(monkeypatch, manager)
    monkeypatch.setattr(rt, "bucket_mgr", manager, raising=False)
    monkeypatch.setattr(rt, "config", bucket_mgr.config, raising=False)

    responses = await asyncio.gather(
        handler(JsonRequest(bucket_id, {"importance": 9})),
        handler(JsonRequest(bucket_id, {"importance": 9})),
    )

    assert sorted(response.status_code for response in responses) == [200, 409]
    conflict = next(response for response in responses if response.status_code == 409)
    assert _json(conflict)["conflict"] == "concurrent_change"
    persisted = await bucket_mgr.get(bucket_id)
    assert persisted["metadata"]["importance"] == 9
    assert await common.count_high_importance() == 1


@pytest.mark.asyncio
async def test_concurrent_dashboard_pins_cannot_exceed_configured_cap(
    monkeypatch,
    bucket_mgr,
):
    first_id = await bucket_mgr.create("first pin candidate", name="First pin")
    second_id = await bucket_mgr.create("second pin candidate", name="Second pin")
    handler = _edit_handler(monkeypatch, bucket_mgr)
    runtime_config = dict(bucket_mgr.config)
    runtime_config["limits"] = {
        **(bucket_mgr.config.get("limits") or {}),
        "max_pinned": 1,
    }
    monkeypatch.setattr(rt, "bucket_mgr", bucket_mgr, raising=False)
    monkeypatch.setattr(rt, "config", runtime_config, raising=False)

    responses = await asyncio.gather(
        handler(JsonRequest(first_id, {"pinned": True})),
        handler(JsonRequest(second_id, {"pinned": True})),
    )

    assert sorted(response.status_code for response in responses) == [200, 400]
    persisted = [
        await bucket_mgr.get(first_id),
        await bucket_mgr.get(second_id),
    ]
    assert sum(bool(row["metadata"].get("pinned")) for row in persisted) == 1
