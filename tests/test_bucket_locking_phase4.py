"""Phase 4 regressions for storage turns and create/ripple races."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
import os
from pathlib import Path
import re
import threading

import frontmatter
import pytest

from bucket_manager import _filesystem_turn
from utils import parse_iso_datetime


@pytest.mark.asyncio
async def test_filesystem_turn_hashes_key_and_does_not_steal_aged_live_lease(
    tmp_path,
):
    base = str(tmp_path / "vault")
    malicious_key = "../../outside\\nested/lock"
    digest = hashlib.sha256(malicious_key.encode("utf-8")).hexdigest()
    lock_path = Path(base) / ".locks" / f"{digest}.lock"

    async with _filesystem_turn(base, malicious_key):
        assert lock_path.is_file()
        assert re.fullmatch(r"[0-9a-f]{64}\.lock", lock_path.name)
        os.utime(lock_path, (0, 0))
        with pytest.raises(TimeoutError):
            async with _filesystem_turn(base, malicious_key, timeout_seconds=0.05):
                pytest.fail("a live kernel lease must not be stolen by file age")

    assert not (tmp_path / "outside").exists()


def test_filesystem_turn_serializes_independent_event_loops(tmp_path):
    base = str(tmp_path / "vault")
    state_lock = threading.Lock()
    state = {"active": 0, "maximum": 0}

    async def enter_once():
        async with _filesystem_turn(base, "same-bucket"):
            with state_lock:
                state["active"] += 1
                state["maximum"] = max(state["maximum"], state["active"])
            await asyncio.sleep(0.02)
            with state_lock:
                state["active"] -= 1

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda _index: asyncio.run(enter_once()), range(6)))

    assert state["maximum"] == 1


def test_active_cache_lock_serializes_independent_event_loops(bucket_mgr, monkeypatch):
    asyncio.run(bucket_mgr.create("cross-loop cache body", domain=["race"]))
    bucket_mgr.external_change_poll_seconds = 0
    entered = threading.Event()
    release = threading.Event()
    original_scan = bucket_mgr._scan_active_file_state
    calls = 0
    calls_guard = threading.Lock()

    def coordinated_scan():
        nonlocal calls
        with calls_guard:
            calls += 1
            call_number = calls
        if call_number == 1:
            entered.set()
            release.wait(timeout=2)
        return original_scan()

    monkeypatch.setattr(bucket_mgr, "_scan_active_file_state", coordinated_scan)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(lambda: asyncio.run(bucket_mgr.list_all()))
        assert entered.wait(timeout=2)
        second = pool.submit(lambda: asyncio.run(bucket_mgr.list_all()))
        release.set()
        assert len(first.result(timeout=2)) == 1
        assert len(second.result(timeout=2)) == 1

    # Re-entering from the original caller after another loop owned the mutex
    # used to raise "Lock ... is bound to a different event loop".
    assert len(asyncio.run(bucket_mgr.list_all())) == 1


def test_bulk_bucket_id_index_avoids_n_by_n_frontmatter_scans(
    bucket_mgr,
    monkeypatch,
):
    for index in range(24):
        asyncio.run(
            bucket_mgr.create(
                f"indexed body {index}",
                name=f"indexed-{index}",
                domain=["race"],
            )
        )

    original_load = frontmatter.load
    loads = 0

    def counted_load(*args, **kwargs):
        nonlocal loads
        loads += 1
        return original_load(*args, **kwargs)

    monkeypatch.setattr(frontmatter, "load", counted_load)
    bucket_mgr._ensure_bucket_path_index()
    build_loads = loads
    assert build_loads == 24

    for index in range(200):
        assert bucket_mgr._find_bucket_file(f"missing-import-{index}") is None
    assert loads == build_loads


@pytest.mark.asyncio
async def test_concurrent_create_override_never_overwrites_same_id(bucket_mgr):
    first, second = await asyncio.gather(
        bucket_mgr.create("first body", bucket_id_override="shared-id"),
        bucket_mgr.create("second body", bucket_id_override="shared-id"),
    )

    assert first != second
    assert {first, second} >= {"shared-id"}
    assert {
        (await bucket_mgr.get(first))["content"],
        (await bucket_mgr.get(second))["content"],
    } == {"first body", "second body"}


@pytest.mark.asyncio
async def test_create_rechecks_id_after_waiting_for_migration_turn(bucket_mgr):
    imported_id = "migration-race-id"
    imported_path = Path(bucket_mgr.dynamic_dir) / "race" / "imported.md"

    async with bucket_mgr._bucket_turn(imported_id):
        create_task = asyncio.create_task(
            bucket_mgr.create(
                "new local body",
                domain=["race"],
                bucket_id_override=imported_id,
            )
        )
        await asyncio.sleep(0.05)
        imported_path.parent.mkdir(parents=True, exist_ok=True)
        imported_path.write_text(
            frontmatter.dumps(
                frontmatter.Post(
                    "imported body",
                    id=imported_id,
                    name="imported",
                    type="dynamic",
                    domain=["race"],
                    created=datetime.now().isoformat(),
                    last_active=datetime.now().isoformat(),
                    activation_count=0,
                    importance=5,
                )
            ),
            encoding="utf-8",
        )

    created_id = await create_task
    assert created_id != imported_id
    assert (await bucket_mgr.get(imported_id))["content"] == "imported body"
    assert (await bucket_mgr.get(created_id))["content"] == "new local body"


@pytest.mark.asyncio
async def test_ripple_reloads_target_under_its_turn_without_lost_touch(bucket_mgr):
    source_id = await bucket_mgr.create("source", domain=["race"])
    target_id = await bucket_mgr.create("target", domain=["race"])
    source = await bucket_mgr.get(source_id)
    reference = parse_iso_datetime(source["metadata"]["created"])

    async with bucket_mgr._bucket_turn(target_id):
        ripple_task = asyncio.create_task(
            bucket_mgr._time_ripple(source_id, reference)
        )
        await asyncio.sleep(0.05)
        assert await bucket_mgr._touch_locked(target_id) is not None

    await ripple_task
    target = await bucket_mgr.get(target_id)
    assert target["metadata"]["activation_count"] == 1.3


@pytest.mark.asyncio
async def test_ripple_does_not_update_target_archived_after_snapshot(bucket_mgr):
    source_id = await bucket_mgr.create("source", domain=["race"])
    target_id = await bucket_mgr.create("target", domain=["race"])
    source = await bucket_mgr.get(source_id)
    reference = parse_iso_datetime(source["metadata"]["created"])

    async with bucket_mgr._bucket_turn(target_id):
        ripple_task = asyncio.create_task(
            bucket_mgr._time_ripple(source_id, reference)
        )
        await asyncio.sleep(0.05)
        assert await bucket_mgr._archive_locked(target_id) is True

    await ripple_task
    target = await bucket_mgr.get(target_id)
    assert target["metadata"]["type"] == "archived"
    assert target["metadata"]["activation_count"] == 0


@pytest.mark.asyncio
async def test_hard_delete_rechecks_provenance_inside_bucket_turn(bucket_mgr):
    bucket_id = await bucket_mgr.create("test body", test_data=True)
    bucket = await bucket_mgr.get(bucket_id)
    path = Path(bucket["path"])

    async with bucket_mgr._bucket_turn(bucket_id):
        delete_task = asyncio.create_task(
            bucket_mgr.hard_delete_test_bucket(bucket_id, reason="race")
        )
        await asyncio.sleep(0.05)
        if path.exists():
            post = frontmatter.load(path)
            post["provenance"] = {
                "kind": "test",
                "created_by": "developer",
                "erasable": False,
            }
            path.write_text(frontmatter.dumps(post), encoding="utf-8")

    assert await delete_task == {"ok": False, "error": "not_erasable_test_data"}
    assert path.is_file()
