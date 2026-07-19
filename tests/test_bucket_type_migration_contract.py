"""Regression contract for editing a bucket's storage-backed type.

The bucket type is not merely presentation metadata: it selects the tree in
which the Markdown source of truth lives.  Editing ``metadata.type`` without
relocating that file makes later scans disagree about what the bucket is.
"""

from pathlib import Path

import frontmatter
import pytest


def _bucket_files(bucket_mgr, bucket_id: str) -> list[Path]:
    """Return every Markdown source whose frontmatter owns ``bucket_id``."""
    matches: list[Path] = []
    for path in Path(bucket_mgr.base_dir).rglob("*.md"):
        try:
            if frontmatter.load(path).get("id") == bucket_id:
                matches.append(path)
        except Exception:
            continue
    return matches


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("target_type", "source_type", "expected_tree"),
    [
        ("dynamic", "permanent", ("dynamic", "migration-domain")),
        ("permanent", "dynamic", ("permanent", "migration-domain")),
        ("feel", "dynamic", ("feel", "沉淀物")),
        ("plan", "dynamic", ("plans", "active")),
        ("letter", "dynamic", ("letters", "history")),
        ("i", "permanent", ("dynamic", "migration-domain")),
        ("self", "permanent", ("dynamic", "migration-domain")),
    ],
)
async def test_type_update_relocates_source_to_the_canonical_tree(
    bucket_mgr,
    target_type,
    source_type,
    expected_tree,
):
    bucket_id = await bucket_mgr.create(
        content=f"move to {target_type}",
        domain=["migration-domain"],
        bucket_type=source_type,
    )
    before = Path((await bucket_mgr.get(bucket_id))["path"])

    assert await bucket_mgr.update(bucket_id, type=target_type) is True

    updated = await bucket_mgr.get(bucket_id)
    assert updated is not None
    assert updated["metadata"]["type"] == target_type
    after = Path(updated["path"])
    assert after.parent == Path(bucket_mgr.base_dir).joinpath(*expected_tree)
    assert after.exists()
    assert not before.exists() or before == after
    assert _bucket_files(bucket_mgr, bucket_id) == [after]


@pytest.mark.asyncio
async def test_type_update_rejects_archived_and_keeps_source_unchanged(bucket_mgr):
    bucket_id = await bucket_mgr.create(
        content="archive is a lifecycle action",
        domain=["migration-domain"],
        bucket_type="dynamic",
    )
    before = await bucket_mgr.get(bucket_id)
    before_path = Path(before["path"])
    before_bytes = before_path.read_bytes()

    assert await bucket_mgr.update(bucket_id, type="archived") is False

    unchanged = await bucket_mgr.get(bucket_id)
    assert unchanged is not None
    assert unchanged["metadata"]["type"] == "dynamic"
    assert Path(unchanged["path"]) == before_path
    assert before_path.read_bytes() == before_bytes
    assert _bucket_files(bucket_mgr, bucket_id) == [before_path]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "updates",
    [
        {"name": "must not edit archived"},
        {"pinned": True},
        {"type": "dynamic"},
    ],
)
async def test_archived_bucket_is_terminal_for_all_regular_updates(
    bucket_mgr,
    updates,
):
    bucket_id = await bucket_mgr.create(
        content="terminal archived memory",
        domain=["migration-domain"],
        bucket_type="dynamic",
    )
    assert await bucket_mgr.archive(bucket_id) is True
    archived = await bucket_mgr.get(bucket_id)
    archived_path = Path(archived["path"])
    archived_bytes = archived_path.read_bytes()

    assert await bucket_mgr.update(bucket_id, **updates) is False

    unchanged = await bucket_mgr.get(bucket_id)
    assert unchanged is not None
    assert unchanged["metadata"]["type"] == "archived"
    assert Path(unchanged["path"]) == archived_path
    assert archived_path.read_bytes() == archived_bytes
    assert _bucket_files(bucket_mgr, bucket_id) == [archived_path]


@pytest.mark.asyncio
async def test_soft_deleted_tombstone_cannot_be_resurrected_by_pin_update(
    bucket_mgr,
):
    bucket_id = await bucket_mgr.create(
        content="terminal tombstone memory",
        domain=["migration-domain"],
        bucket_type="dynamic",
    )
    assert await bucket_mgr.delete(bucket_id) is True
    tombstone_files = _bucket_files(bucket_mgr, bucket_id)
    assert len(tombstone_files) == 1
    tombstone_path = tombstone_files[0]
    tombstone_bytes = tombstone_path.read_bytes()

    assert await bucket_mgr.update(bucket_id, pinned=True) is False

    unchanged = frontmatter.load(tombstone_path)
    assert unchanged.get("deleted_at")
    assert unchanged.get("tombstone") is True
    assert unchanged.get("pinned") is not True
    assert tombstone_path.read_bytes() == tombstone_bytes
    assert _bucket_files(bucket_mgr, bucket_id) == [tombstone_path]


@pytest.mark.asyncio
@pytest.mark.parametrize("guard_field", ["pinned", "protected"])
async def test_guarded_permanent_bucket_cannot_be_retyped_out_of_permanent(
    bucket_mgr,
    guard_field,
):
    create_kwargs = {guard_field: True}
    bucket_id = await bucket_mgr.create(
        content=f"guarded by {guard_field}",
        domain=["migration-domain"],
        bucket_type="permanent",
        **create_kwargs,
    )
    before = await bucket_mgr.get(bucket_id)
    before_path = Path(before["path"])
    before_bytes = before_path.read_bytes()

    assert await bucket_mgr.update(bucket_id, type="dynamic") is False

    unchanged = await bucket_mgr.get(bucket_id)
    assert unchanged is not None
    assert unchanged["metadata"]["type"] == "permanent"
    assert unchanged["metadata"][guard_field] is True
    assert Path(unchanged["path"]) == before_path
    assert before_path.read_bytes() == before_bytes
    assert _bucket_files(bucket_mgr, bucket_id) == [before_path]


@pytest.mark.asyncio
async def test_type_move_collision_never_overwrites_existing_target(bucket_mgr):
    bucket_id = await bucket_mgr.create(
        content="source must survive a collision",
        domain=["collision-domain"],
        bucket_type="permanent",
    )
    before = await bucket_mgr.get(bucket_id)
    source_path = Path(before["path"])
    source_bytes = source_path.read_bytes()

    collision_path = (
        Path(bucket_mgr.dynamic_dir) / "collision-domain" / source_path.name
    )
    collision_path.parent.mkdir(parents=True, exist_ok=True)
    collision_bytes = b"pre-existing target must not be replaced\n"
    collision_path.write_bytes(collision_bytes)

    moved = await bucket_mgr.update(bucket_id, type="dynamic")

    assert collision_path.read_bytes() == collision_bytes
    current = await bucket_mgr.get(bucket_id)
    assert current is not None
    if moved:
        # A collision-safe suffix is a valid successful implementation.
        assert current["metadata"]["type"] == "dynamic"
        assert Path(current["path"]).parent == collision_path.parent
        assert Path(current["path"]) != collision_path
        assert not source_path.exists()
    else:
        # Rejecting the move is also valid, provided the source rolls back.
        assert current["metadata"]["type"] == "permanent"
        assert Path(current["path"]) == source_path
        assert source_path.read_bytes() == source_bytes
    assert _bucket_files(bucket_mgr, bucket_id) == [Path(current["path"])]


@pytest.mark.asyncio
async def test_type_move_failure_rolls_back_metadata_and_path(bucket_mgr, monkeypatch):
    import bucket_manager as bucket_manager_module

    bucket_id = await bucket_mgr.create(
        content="move failure must be atomic",
        domain=["migration-domain"],
        bucket_type="dynamic",
    )
    before = await bucket_mgr.get(bucket_id)
    source_path = Path(before["path"])
    source_bytes = source_path.read_bytes()

    real_remove = bucket_manager_module.os.remove

    def fail_source_removal(path, *_args, **_kwargs):
        if Path(path) == source_path:
            raise OSError("simulated source removal failure")
        return real_remove(path, *_args, **_kwargs)

    # The migration has already written its destination when source removal
    # runs.  Failing this exact step exercises the hard rollback boundary:
    # the new copy must be removed and the untouched source kept canonical.
    monkeypatch.setattr(bucket_manager_module.os, "remove", fail_source_removal)

    assert await bucket_mgr.update(bucket_id, type="permanent") is False

    unchanged = await bucket_mgr.get(bucket_id)
    assert unchanged is not None
    assert unchanged["metadata"]["type"] == "dynamic"
    assert Path(unchanged["path"]) == source_path
    assert source_path.read_bytes() == source_bytes
    assert _bucket_files(bucket_mgr, bucket_id) == [source_path]


@pytest.mark.asyncio
async def test_type_metadata_write_failure_does_not_move_source(
    bucket_mgr,
    monkeypatch,
):
    import bucket_manager as bucket_manager_module

    bucket_id = await bucket_mgr.create(
        content="write failure must be atomic",
        domain=["migration-domain"],
        bucket_type="dynamic",
    )
    before = await bucket_mgr.get(bucket_id)
    source_path = Path(before["path"])
    source_bytes = source_path.read_bytes()

    def fail_write(*_args, **_kwargs):
        raise OSError("simulated metadata write failure")

    monkeypatch.setattr(bucket_manager_module, "_atomic_write_text", fail_write)

    assert await bucket_mgr.update(bucket_id, type="permanent") is False

    unchanged = await bucket_mgr.get(bucket_id)
    assert unchanged is not None
    assert unchanged["metadata"]["type"] == "dynamic"
    assert Path(unchanged["path"]) == source_path
    assert source_path.read_bytes() == source_bytes
    assert _bucket_files(bucket_mgr, bucket_id) == [source_path]


@pytest.mark.asyncio
async def test_archive_move_failure_keeps_active_type_and_source(
    bucket_mgr,
    monkeypatch,
):
    """Archive uses the same copy-on-commit boundary as an explicit type move."""
    import bucket_manager as bucket_manager_module

    bucket_id = await bucket_mgr.create(
        content="archive failure must not split metadata from storage",
        domain=["migration-domain"],
        bucket_type="dynamic",
    )
    before = await bucket_mgr.get(bucket_id)
    source_path = Path(before["path"])
    source_bytes = source_path.read_bytes()
    real_remove = bucket_manager_module.os.remove

    def fail_source_removal(path, *_args, **_kwargs):
        if Path(path) == source_path:
            raise OSError("simulated archive source removal failure")
        return real_remove(path, *_args, **_kwargs)

    monkeypatch.setattr(bucket_manager_module.os, "remove", fail_source_removal)

    assert await bucket_mgr.archive(bucket_id) is False

    unchanged = await bucket_mgr.get(bucket_id)
    assert unchanged is not None
    assert unchanged["metadata"]["type"] == "dynamic"
    assert Path(unchanged["path"]) == source_path
    assert source_path.read_bytes() == source_bytes
    assert _bucket_files(bucket_mgr, bucket_id) == [source_path]


@pytest.mark.asyncio
async def test_soft_delete_move_failure_rolls_back_tombstone_and_copy(
    bucket_mgr,
    monkeypatch,
):
    import bucket_manager as bucket_manager_module

    bucket_id = await bucket_mgr.create(
        content="soft delete failure must keep one live source",
        domain=["migration-domain"],
    )
    before = await bucket_mgr.get(bucket_id)
    source_path = Path(before["path"])
    source_bytes = source_path.read_bytes()
    real_remove = bucket_manager_module.os.remove

    def fail_source_removal(path, *_args, **_kwargs):
        if Path(path) == source_path:
            raise OSError("simulated soft-delete source removal failure")
        return real_remove(path, *_args, **_kwargs)

    monkeypatch.setattr(bucket_manager_module.os, "remove", fail_source_removal)

    assert await bucket_mgr.delete(bucket_id) is False

    unchanged = await bucket_mgr.get(bucket_id)
    assert unchanged is not None
    assert "deleted_at" not in unchanged["metadata"]
    assert "tombstone" not in unchanged["metadata"]
    assert Path(unchanged["path"]) == source_path
    assert source_path.read_bytes() == source_bytes
    assert _bucket_files(bucket_mgr, bucket_id) == [source_path]


@pytest.mark.asyncio
async def test_legacy_scalar_domain_uses_the_whole_value_for_migration(bucket_mgr):
    bucket_id = await bucket_mgr.create(
        content="legacy scalar domain",
        domain=["temporary-domain"],
    )
    source_path = Path((await bucket_mgr.get(bucket_id))["path"])
    post = frontmatter.load(source_path)
    post["domain"] = "legacy-work"
    source_path.write_text(frontmatter.dumps(post), encoding="utf-8")

    assert await bucket_mgr.update(bucket_id, name="edited legacy bucket") is True

    updated = await bucket_mgr.get(bucket_id)
    updated_path = Path(updated["path"])
    assert updated_path.parent == Path(bucket_mgr.dynamic_dir) / "legacy-work"
    assert updated_path.parent.name != "l"
    assert _bucket_files(bucket_mgr, bucket_id) == [updated_path]
