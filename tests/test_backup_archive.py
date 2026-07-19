import hashlib
import io
import json
import os
import sqlite3
import stat
import tracemalloc
import zipfile
from pathlib import Path

import frontmatter
import pytest

from backup_archive import (
    BackupArchiveError,
    build_export_archive,
    build_export_archive_file,
    extract_backup_archive_file,
    read_backup_archive,
)
from bucket_manager import BucketManager
from embedding_engine import EmbeddingEngine
from migrate_engine import MigrateEngine
import migrate_engine as migrate_mod
import backup_archive as archive_mod


class _Backend:
    def vector_dim(self):
        return 2


def _config(root):
    return {
        "buckets_dir": str(root),
        "embedding": {"enabled": False},
        "storage": {"external_change_poll_seconds": 0},
    }


def _engine(config, model="test-embedding"):
    engine = EmbeddingEngine(config)
    engine.model = model
    engine._backend = _Backend()
    return engine


def _write_bucket(root, bucket_id="memory-1", content="important memory"):
    path = root / "dynamic" / "general" / f"memory_{bucket_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(
        content,
        id=bucket_id,
        name="Memory",
        type="dynamic",
        domain=["general"],
        created="2026-07-11T12:00:00",
    )
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return path


def _rewrite_zip(payload, updates):
    source = zipfile.ZipFile(io.BytesIO(payload), "r")
    output = io.BytesIO()
    with source, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            target.writestr(info.filename, updates.get(info.filename, source.read(info)))
    return output.getvalue()


def test_export_archive_has_verified_manifest_and_sqlite_snapshot(tmp_path):
    vault = tmp_path / "vault"
    bucket = _write_bucket(vault)
    engine = _engine(_config(vault))
    engine._store_embedding("memory-1", [0.1, 0.2], "digest")

    payload, manifest = build_export_archive(
        str(vault), engine.db_path, {"exported_at": "now", "version": "test"}
    )
    package = read_backup_archive(payload)

    assert package["integrity_verified"] is True
    assert package["integrity_warning"] == ""
    assert package["manifest"] == manifest
    assert package["files"]["buckets/dynamic/general/memory_memory-1.md"] == bucket.read_bytes()
    assert "embeddings.db" in package["files"]
    assert manifest["file_count"] == 3

    db_file = tmp_path / "snapshot.db"
    db_file.write_bytes(package["files"]["embeddings.db"])
    with sqlite3.connect(db_file) as connection:
        row = connection.execute(
            "SELECT bucket_id, content_hash FROM embeddings WHERE bucket_id = ?",
            ("memory-1",),
        ).fetchone()
    assert row == ("memory-1", "digest")


def test_disk_export_streams_sources_without_path_read_bytes(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    bucket = _write_bucket(vault, content="streamed memory " * 10_000)
    with bucket.open("rb") as handle:
        expected_bucket = handle.read()

    def forbid_materializing(_path):
        raise AssertionError("disk export must stream files instead of Path.read_bytes")

    monkeypatch.setattr(Path, "read_bytes", forbid_materializing)
    archive_path, manifest = build_export_archive_file(
        str(vault),
        "",
        {"exported_at": "now", "version": "test"},
    )
    try:
        with open(archive_path, "rb") as handle:
            package = read_backup_archive(handle.read())
        member = f"buckets/dynamic/general/{bucket.name}"
        assert package["files"][member] == expected_bucket
        assert package["manifest"] == manifest
    finally:
        os.unlink(archive_path)


def test_disk_export_aborts_and_cleans_temp_files_at_compressed_cap(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    path = vault / "dynamic" / "general" / "large.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(os.urandom(4096))
    created = []
    original_mkstemp = archive_mod.tempfile.mkstemp

    def tracked_mkstemp(*args, **kwargs):
        kwargs["dir"] = tmp_path
        fd, temp_path = original_mkstemp(*args, **kwargs)
        created.append(temp_path)
        return fd, temp_path

    monkeypatch.setattr(archive_mod.tempfile, "mkstemp", tracked_mkstemp)
    monkeypatch.setattr(archive_mod, "MAX_ARCHIVE_BYTES", 512)

    with pytest.raises(BackupArchiveError, match="压缩后"):
        build_export_archive_file(str(vault), "", {"version": "test"})

    assert created
    assert all(not os.path.exists(temp_path) for temp_path in created)


def test_manifest_rejects_tampered_member(tmp_path):
    vault = tmp_path / "vault"
    path = _write_bucket(vault)
    engine = _engine(_config(vault))
    payload, _ = build_export_archive(
        str(vault), engine.db_path, {"exported_at": "now", "version": "test"}
    )
    member = f"buckets/dynamic/general/{path.name}"
    tampered = _rewrite_zip(payload, {member: b"changed after manifest"})

    with pytest.raises(BackupArchiveError, match="不一致|校验失败"):
        read_backup_archive(tampered)


def test_reader_rejects_traversal_and_normalizes_legacy_windows_paths():
    malicious = io.BytesIO()
    with zipfile.ZipFile(malicious, "w") as archive:
        archive.writestr("buckets/../../outside.md", b"bad")
    with pytest.raises(BackupArchiveError, match="不安全路径"):
        read_backup_archive(malicious.getvalue())

    legacy = io.BytesIO()
    with zipfile.ZipFile(legacy, "w") as archive:
        archive.writestr("buckets\\dynamic\\general\\old.md", b"legacy")
    package = read_backup_archive(legacy.getvalue())
    assert package["integrity_verified"] is False
    assert package["files"] == {"buckets/dynamic/general/old.md": b"legacy"}
    assert "旧版备份" in package["integrity_warning"]


def test_reader_rejects_symbolic_link_member():
    malicious = io.BytesIO()
    with zipfile.ZipFile(malicious, "w") as archive:
        info = zipfile.ZipInfo("buckets/dynamic/link.md")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, b"../../outside.md")

    with pytest.raises(BackupArchiveError, match="符号链接"):
        read_backup_archive(malicious.getvalue())


def test_disk_extractor_does_not_materialize_large_member_in_memory(tmp_path):
    archive_path = tmp_path / "large.zip"
    chunk = b"z" * (1024 * 1024)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_STORED) as archive:
        with archive.open("embeddings.db", "w") as member:
            for _ in range(32):
                member.write(chunk)

    destination = tmp_path / "extracted"
    tracemalloc.start()
    package = extract_backup_archive_file(str(archive_path), str(destination))
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    extracted = package["files"]["embeddings.db"]
    assert os.path.getsize(extracted) == 32 * 1024 * 1024
    assert peak < 8 * 1024 * 1024


@pytest.mark.parametrize("with_manifest", [False, True], ids=["legacy", "manifest"])
def test_production_extractor_rejects_every_unused_member(tmp_path, with_manifest):
    archive_path = tmp_path / "junk.zip"
    files = {
        "buckets/dynamic/valid.md": b"---\nid: valid\n---\nbody\n",
        "junk.bin": b"0" * (2 * 1024 * 1024),
    }
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        if with_manifest:
            manifest = {
                "schema_version": 1,
                "kind": "ombre-brain-backup",
                "created_at": "now",
                "version": "test",
                "file_count": len(files),
                "total_bytes": sum(len(data) for data in files.values()),
                "files": [
                    {
                        "path": name,
                        "size": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                    for name, data in files.items()
                ],
            }
            archive.writestr("backup_manifest.json", json.dumps(manifest))

    destination = tmp_path / "extracted"
    with pytest.raises(BackupArchiveError, match="不支持的成员"):
        extract_backup_archive_file(str(archive_path), str(destination))

    assert not list(destination.glob("*"))


def test_production_extractor_enforces_path_specific_member_caps(
    tmp_path,
    monkeypatch,
):
    archive_path = tmp_path / "oversized-bucket.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("buckets/dynamic/too-large.md", b"x" * 65)

    monkeypatch.setattr(archive_mod, "MIGRATE_MAX_BUCKET_BYTES", 64)
    with pytest.raises(BackupArchiveError, match="成员过大"):
        extract_backup_archive_file(str(archive_path), str(tmp_path / "extracted"))


def test_production_extractor_does_not_fsync_each_temporary_member(
    tmp_path,
    monkeypatch,
):
    archive_path = tmp_path / "valid.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("buckets/dynamic/valid.md", b"---\nid: valid\n---\nbody\n")

    monkeypatch.setattr(
        archive_mod.os,
        "fsync",
        lambda _fd: pytest.fail("temporary extraction must not fsync per member"),
    )
    package = extract_backup_archive_file(
        str(archive_path),
        str(tmp_path / "extracted"),
    )

    assert set(package["files"]) == {"buckets/dynamic/valid.md"}


def test_embedding_merge_fetches_large_vectors_in_bounded_batches(tmp_path):
    source_db = tmp_path / "source.db"
    payload = "[0.1,0.2]" + (" " * (512 * 1024 - len("[0.1,0.2]")))
    row_count = 128
    with sqlite3.connect(source_db) as connection:
        connection.execute(
            """CREATE TABLE embeddings (
                bucket_id TEXT PRIMARY KEY,
                embedding TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                content_hash TEXT NOT NULL
            )"""
        )
        connection.executemany(
            "INSERT INTO embeddings VALUES (?, ?, ?, ?)",
            (
                (f"memory-{index}", payload, "now", f"hash-{index}")
                for index in range(row_count)
            ),
        )

    config = _config(tmp_path / "target")
    target_engine = _engine(config)
    migrate = MigrateEngine(
        config,
        BucketManager(config, embedding_engine=target_engine),
        target_engine,
    )
    migrate._import_model_dim = 2
    id_map = {f"memory-{index}": f"memory-{index}" for index in range(row_count)}

    tracemalloc.start()
    merged = migrate._merge_embeddings_path(str(source_db), id_map)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert len(merged) == row_count
    assert peak < 32 * 1024 * 1024
    with sqlite3.connect(target_engine.db_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    assert count == row_count


def test_embedding_merge_rejects_untrusted_cells_and_reindexes_them(tmp_path):
    source_db = tmp_path / "source.db"
    oversized = "[0.1,0.2]" + (" " * (1024 * 1024))
    rows = [
        ("good", "[0.1, 0.2]", "now", "digest"),
        ("oversized", oversized, "now", "digest"),
        ("wrong-element", '["not-a-number", 0.2]', "now", "digest"),
        ("nonfinite", "[NaN, 0.2]", "now", "digest"),
        ("wrong-dimension", "[0.1]", "now", "digest"),
        ("wrong-type", 42, "now", "digest"),
    ]
    with sqlite3.connect(source_db) as connection:
        connection.execute(
            """CREATE TABLE embeddings (
                bucket_id TEXT PRIMARY KEY,
                embedding,
                updated_at,
                content_hash
            )"""
        )
        connection.executemany("INSERT INTO embeddings VALUES (?, ?, ?, ?)", rows)

    config = _config(tmp_path / "target")
    target_engine = _engine(config)
    migrate = MigrateEngine(
        config,
        BucketManager(config, embedding_engine=target_engine),
        target_engine,
    )
    migrate._import_model_dim = 2
    id_map = {source_id: source_id for source_id, *_rest in rows}

    merged = migrate._merge_embeddings_path(str(source_db), id_map)

    assert merged == {"good"}
    with sqlite3.connect(target_engine.db_path) as connection:
        stored = connection.execute(
            "SELECT bucket_id, embedding FROM embeddings"
        ).fetchall()
    assert stored == [("good", "[0.1,0.2]")]


@pytest.mark.asyncio
async def test_export_to_empty_vault_restores_markdown_and_current_embedding_schema(tmp_path):
    source_vault = tmp_path / "source"
    _write_bucket(source_vault, content="restore this exact text")
    source_engine = _engine(_config(source_vault))
    source_engine._store_embedding("memory-1", [0.3, 0.4], "source-hash")
    payload, _ = build_export_archive(
        str(source_vault),
        source_engine.db_path,
        {
            "exported_at": "2026-07-11T12:00:00",
            "version": "test",
            "embedding": {"model": "test-embedding", "dim": 2, "backend": "api"},
        },
    )

    target_vault = tmp_path / "target"
    target_config = _config(target_vault)
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)
    migrate = MigrateEngine(target_config, manager, target_engine)

    parsed = await migrate.parse_zip(payload)
    assert parsed["ok"] is True
    assert parsed["integrity_verified"] is True
    await migrate.apply({})

    restored = await manager.get("memory-1")
    assert restored is not None
    assert restored["content"] == "restore this exact text"
    assert await target_engine.get_embedding("memory-1") == [0.3, 0.4]
    assert target_engine.get_content_hash("memory-1") == "source-hash"
    assert migrate.get_status()["result"] == {"imported": 1, "skipped": 0}


@pytest.mark.asyncio
async def test_keep_both_maps_imported_vector_to_new_id(tmp_path):
    source_vault = tmp_path / "source"
    _write_bucket(source_vault, content="imported version")
    source_engine = _engine(_config(source_vault))
    source_engine._store_embedding("memory-1", [0.7, 0.8], "imported-hash")
    payload, _ = build_export_archive(
        str(source_vault),
        source_engine.db_path,
        {
            "exported_at": "now",
            "version": "test",
            "embedding": {"model": "test-embedding", "dim": 2, "backend": "api"},
        },
    )

    target_vault = tmp_path / "target"
    _write_bucket(target_vault, content="local version")
    target_config = _config(target_vault)
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)
    migrate = MigrateEngine(target_config, manager, target_engine)

    parsed = await migrate.parse_zip(payload)
    assert parsed["conflicts_count"] == 1
    await migrate.apply({"memory-1": "keep_both"})

    buckets = await manager.list_all()
    assert {bucket["content"] for bucket in buckets} == {"local version", "imported version"}
    imported = next(bucket for bucket in buckets if bucket["content"] == "imported version")
    assert imported["id"] != "memory-1"
    assert await target_engine.get_embedding(imported["id"]) == [0.7, 0.8]


@pytest.mark.asyncio
async def test_overwrite_preserves_old_memory_under_unique_archived_id(tmp_path):
    source_vault = tmp_path / "source"
    _write_bucket(source_vault, content="imported version")
    source_engine = _engine(_config(source_vault))
    payload, _ = build_export_archive(
        str(source_vault),
        source_engine.db_path,
        {
            "exported_at": "now",
            "version": "test",
            "embedding": {"model": "test-embedding", "dim": 2, "backend": "api"},
        },
    )

    target_vault = tmp_path / "target"
    _write_bucket(target_vault, content="local version")
    target_config = _config(target_vault)
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)
    migrate = MigrateEngine(target_config, manager, target_engine)

    await migrate.parse_zip(payload)
    await migrate.apply({"memory-1": "overwrite"})

    buckets = await manager.list_all(include_archive=True)
    assert {bucket["content"] for bucket in buckets} == {"local version", "imported version"}
    assert len({bucket["id"] for bucket in buckets}) == 2
    archived = next(bucket for bucket in buckets if bucket["content"] == "local version")
    assert archived["id"].startswith("memory-1-superseded-")
    assert archived["metadata"]["superseded_by"] == "memory-1"


@pytest.mark.asyncio
async def test_overwrite_leaves_old_memory_untouched_when_new_content_write_fails(tmp_path, monkeypatch):
    """回归锁死找茬会话发现的 bug：overwrite 冲突原来是「先删旧、再写新」，

    写新内容失败时旧桶已经被移进 archive/ 改名，两边都没有=数据丢失。
    修复后顺序反过来：新内容先完整落盘到暂存文件，写失败旧桶必须完全不受影响。
    """
    source_vault = tmp_path / "source"
    _write_bucket(source_vault, content="imported version")
    source_engine = _engine(_config(source_vault))
    payload, _ = build_export_archive(
        str(source_vault),
        source_engine.db_path,
        {
            "exported_at": "now",
            "version": "test",
            "embedding": {"model": "test-embedding", "dim": 2, "backend": "api"},
        },
    )

    target_vault = tmp_path / "target"
    _write_bucket(target_vault, content="local version")
    target_config = _config(target_vault)
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)
    migrate = MigrateEngine(target_config, manager, target_engine)

    def _boom(self, pb, target_id, buckets_dir):
        raise OSError("simulated disk failure while staging new content")

    monkeypatch.setattr(MigrateEngine, "_write_bucket_file_staged", _boom)

    await migrate.parse_zip(payload)
    await migrate.apply({"memory-1": "overwrite"})

    # 新内容落盘先炸：旧桶必须还在原地、原样、原 ID，完全没被删/被改名。
    buckets = await manager.list_all(include_archive=True)
    assert len(buckets) == 1
    survivor = buckets[0]
    assert survivor["id"] == "memory-1"
    assert survivor["content"] == "local version"
    assert survivor["metadata"].get("type") != "archived"
    assert migrate._apply_errors, "写入失败应该被记录成一条 apply error"


@pytest.mark.asyncio
async def test_overwrite_cleans_up_staged_file_when_old_bucket_handling_fails(tmp_path, monkeypatch):
    """写新内容成功，但处理旧桶（delete+rekey）失败：暂存文件必须被清理掉，

    不能留下一个既不是新桶也不是旧桶、谁都不认的孤儿 .staging 文件。
    """
    source_vault = tmp_path / "source"
    _write_bucket(source_vault, content="imported version")
    source_engine = _engine(_config(source_vault))
    payload, _ = build_export_archive(
        str(source_vault),
        source_engine.db_path,
        {
            "exported_at": "now",
            "version": "test",
            "embedding": {"model": "test-embedding", "dim": 2, "backend": "api"},
        },
    )

    target_vault = tmp_path / "target"
    _write_bucket(target_vault, content="local version")
    target_config = _config(target_vault)
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)
    migrate = MigrateEngine(target_config, manager, target_engine)

    def _boom(self, existing_path, bucket_id, buckets_dir):
        raise OSError("simulated failure while archiving the old bucket")

    monkeypatch.setattr(MigrateEngine, "_write_historical_copy", _boom)

    await migrate.parse_zip(payload)
    await migrate.apply({"memory-1": "overwrite"})

    staged_leftovers = list((target_vault / "dynamic").rglob("*.staging-*"))
    assert staged_leftovers == [], f"暂存文件没被清理: {staged_leftovers}"
    assert migrate._apply_errors, "旧桶处理失败应该被记录成一条 apply error"
    buckets = await manager.list_all(include_archive=True)
    assert [(bucket["id"], bucket["content"]) for bucket in buckets] == [
        ("memory-1", "local version")
    ]


@pytest.mark.asyncio
async def test_missing_snapshot_vector_is_durably_queued(tmp_path):
    source_vault = tmp_path / "source"
    _write_bucket(source_vault)
    source_engine = _engine(_config(source_vault))
    payload, _ = build_export_archive(
        str(source_vault),
        source_engine.db_path,
        {
            "exported_at": "now",
            "version": "test",
            "embedding": {"model": "test-embedding", "dim": 2, "backend": "api"},
        },
    )

    class Outbox:
        def __init__(self):
            self.queued = []

        def enqueue(self, bucket_id, content):
            self.queued.append((bucket_id, content))
            return True

    target_vault = tmp_path / "target"
    target_config = _config(target_vault)
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)
    outbox = Outbox()
    manager.attach_embedding_outbox(outbox)
    migrate = MigrateEngine(target_config, manager, target_engine)

    assert (await migrate.parse_zip(payload))["ok"] is True
    await migrate.apply({})
    assert outbox.queued == [("memory-1", "important memory")]
    assert migrate.get_status()["reindex_progress"] == {"done": 1, "total": 1, "errors": 0}


@pytest.mark.asyncio
async def test_disk_backed_parse_releases_extracted_payload_after_apply(tmp_path):
    source_vault = tmp_path / "source"
    _write_bucket(source_vault)
    source_engine = _engine(_config(source_vault))
    archive_path, _manifest = build_export_archive_file(
        str(source_vault),
        source_engine.db_path,
        {
            "exported_at": "now",
            "version": "test",
            "embedding": {"model": "test-embedding", "dim": 2, "backend": "api"},
        },
    )

    target_vault = tmp_path / "target"
    target_config = _config(target_vault)
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)
    migrate = MigrateEngine(target_config, manager, target_engine)
    reservation = migrate.reserve_parse()
    try:
        parsed = await migrate.parse_zip_file(
            archive_path,
            reservation_id=reservation,
        )
    finally:
        os.unlink(archive_path)

    assert parsed["ok"] is True
    workspace = migrate._parse_temp_dir
    assert os.path.isdir(workspace)
    assert migrate._parsed_buckets[0].md_bytes is None
    assert os.path.isfile(migrate._parsed_buckets[0].md_path)
    assert migrate._zip_db_bytes is None

    await migrate.apply({})

    assert not os.path.exists(workspace)
    assert migrate._parsed_buckets == []
    assert migrate._zip_db_path == ""
    assert (await manager.get("memory-1"))["content"] == "important memory"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "decision",
    [
        {},
        {"memory-1": "overwrite"},
        {"memory-1": "keep_both"},
    ],
    ids=["default-skip", "forged-overwrite", "forged-keep-both"],
)
async def test_apply_rechecks_conflict_created_after_parse(tmp_path, decision):
    source_vault = tmp_path / "source"
    _write_bucket(source_vault, content="imported version")
    source_engine = _engine(_config(source_vault))
    payload, _ = build_export_archive(
        str(source_vault),
        source_engine.db_path,
        {"embedding": {"model": "test-embedding", "dim": 2}},
    )

    target_vault = tmp_path / "target"
    target_config = _config(target_vault)
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)
    migrate = MigrateEngine(target_config, manager, target_engine)
    parsed = await migrate.parse_zip(payload)
    assert parsed["conflicts_count"] == 0

    _write_bucket(target_vault, content="created after parse")
    await migrate.apply(decision)

    buckets = await manager.list_all(include_archive=True)
    assert [(bucket["id"], bucket["content"]) for bucket in buckets] == [
        ("memory-1", "created after parse")
    ]
    assert migrate.get_status()["result"] == {"imported": 0, "skipped": 1}
    assert "新冲突" in " ".join(migrate._apply_errors)


@pytest.mark.asyncio
async def test_overwrite_preserves_latest_version_changed_after_parse(tmp_path):
    source_vault = tmp_path / "source"
    _write_bucket(source_vault, content="imported version")
    source_engine = _engine(_config(source_vault))
    payload, _ = build_export_archive(
        str(source_vault),
        source_engine.db_path,
        {"embedding": {"model": "test-embedding", "dim": 2}},
    )

    target_vault = tmp_path / "target"
    _write_bucket(target_vault, content="local at parse")
    target_config = _config(target_vault)
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)
    migrate = MigrateEngine(target_config, manager, target_engine)
    await migrate.parse_zip(payload)
    assert await manager.update("memory-1", content="latest concurrent edit") is True

    await migrate.apply({"memory-1": "overwrite"})

    buckets = await manager.list_all(include_archive=True)
    assert {bucket["content"] for bucket in buckets} == {
        "imported version",
        "latest concurrent edit",
    }
    historical = next(bucket for bucket in buckets if bucket["content"] == "latest concurrent edit")
    assert historical["metadata"]["superseded_by"] == "memory-1"


@pytest.mark.asyncio
async def test_migrate_rejects_bucket_over_runtime_content_limit(tmp_path):
    source_vault = tmp_path / "source"
    _write_bucket(source_vault, content="x" * (51 * 1024))
    source_engine = _engine(_config(source_vault))
    payload, _ = build_export_archive(
        str(source_vault),
        source_engine.db_path,
        {"embedding": {}},
    )
    target_config = _config(tmp_path / "target")
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)

    result = await MigrateEngine(target_config, manager, target_engine).parse_zip(payload)

    assert result["ok"] is False
    assert "正文过大" in result["error"]


@pytest.mark.asyncio
async def test_migrate_rejects_non_json_safe_yaml_metadata(tmp_path):
    source_vault = tmp_path / "source"
    path = source_vault / "dynamic" / "general" / "unsafe.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\nid: unsafe-metadata\npayload: !!set\n  ? value\n---\nbody\n",
        encoding="utf-8",
    )
    payload, _ = build_export_archive(
        str(source_vault),
        "",
        {"embedding": {}},
    )
    target_config = _config(tmp_path / "target")
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)

    result = await MigrateEngine(target_config, manager, target_engine).parse_zip(payload)

    assert result["ok"] is False
    assert "JSON-safe" in result["error"]


@pytest.mark.asyncio
async def test_overwrite_rolls_back_when_old_source_cannot_be_removed(tmp_path, monkeypatch):
    source_vault = tmp_path / "source"
    source_path = _write_bucket(source_vault, content="imported permanent")
    source_post = frontmatter.load(source_path)
    source_post["type"] = "permanent"
    source_path.write_text(frontmatter.dumps(source_post), encoding="utf-8")
    source_engine = _engine(_config(source_vault))
    payload, _ = build_export_archive(
        str(source_vault),
        source_engine.db_path,
        {"embedding": {"model": "test-embedding", "dim": 2}},
    )

    target_vault = tmp_path / "target"
    old_path = _write_bucket(target_vault, content="local survivor")
    target_config = _config(target_vault)
    target_engine = _engine(target_config)
    manager = BucketManager(target_config, embedding_engine=target_engine)
    migrate = MigrateEngine(target_config, manager, target_engine)
    await migrate.parse_zip(payload)

    original_unlink = os.unlink
    expected = os.path.normcase(os.path.abspath(str(old_path)))

    def fail_old_source(path, *args, **kwargs):
        normalized = str(path)
        if normalized.startswith("\\\\?\\"):
            normalized = normalized[4:]
        if os.path.normcase(os.path.abspath(normalized)) == expected:
            raise OSError("simulated old source unlink failure")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(migrate_mod.os, "unlink", fail_old_source)
    await migrate.apply({"memory-1": "overwrite"})

    buckets = await manager.list_all(include_archive=True)
    assert [(bucket["id"], bucket["content"]) for bucket in buckets] == [
        ("memory-1", "local survivor")
    ]
    assert migrate._apply_errors
    assert not list(target_vault.rglob("*.staging-*"))
