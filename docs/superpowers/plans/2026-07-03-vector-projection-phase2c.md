# Vector Projection Manifest Phase 2C Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the Phase 2 shadow projection family by adding a read-only vector projection manifest for `embeddings.db`.

**Architecture:** Keep `EmbeddingEngine`, semantic search, and bucket write paths unchanged. The new manifest reads ledger events and the existing SQLite vector store, then reports whether the vector projection is aligned with active traces. It is diagnostic-only and never generates, rewrites, deletes, or ranks embeddings.

**Tech Stack:** Python, SQLite, existing `TraceCatalogProjection`, pytest.

---

### Task 1: Vector Projection Tests

**Files:**
- Add: `tests/test_vector_projection_phase2c.py`
- Modify: `src/bucket_manager.py`

- [x] **Step 1: Write failing manifest test**

Create a ledger with one active trace, one tombstone trace, and an `embeddings.db` with one valid vector, one orphan vector, and one malformed vector. Assert the manifest reports counts, meta, missing vectors, orphan vectors, malformed vectors, shadow role, and non-canonical status.

- [x] **Step 2: Write failing BucketManager diagnostics test**

Assert `BucketManager.ledger_integrity_report()` includes a `vector_projection` field with projection name, shadow role, non-canonical status, and source/applied seq alignment.

- [x] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_vector_projection_phase2c.py -q`
Expected: FAIL because `projection_vector.py` and `vector_projection` diagnostics do not exist yet.

### Task 2: Implement Shadow Manifest

**Files:**
- Add: `src/projection_vector.py`
- Modify: `src/bucket_manager.py`

- [x] **Step 1: Add `TraceVectorProjectionManifest`**

Use `TraceCatalogProjection` to derive expected active trace ids. Read only `embeddings.db` tables and metadata. Never call `generate_and_store()` or mutate SQLite.

- [x] **Step 2: Report drift safely**

Expose `expected_trace_count`, `vector_count`, `missing_vector_count`, `orphan_vector_count`, `malformed_vector_count`, small id samples, `model_name`, `vector_dim`, `db_exists`, `path`, `applied_seq`, `source_latest_seq`, and `lag`.

- [x] **Step 3: Wire diagnostics**

Attach `vector_projection` to `BucketManager.ledger_integrity_report()` using `embedding_engine.db_path` when present, otherwise `<buckets_dir>/embeddings.db`.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_vector_projection_phase2c.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-03-vector-projection-phase2c.md`

- [x] **Step 1: Document Phase 2C**

Add an `INTERNALS.md` note that vector projection diagnostics are shadow-only, do not replace embedding search, and only report drift.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_vector_projection_phase2c.py tests/test_sqlite_projection_phase2b.py tests/test_projection_mirror_phase2.py tests/test_system_diagnostics.py -q`
Expected: all selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 1: Ledger Mirror
- [x] Phase 2A: In-memory Trace Catalog Projection
- [x] Phase 2B: SQLite/FTS Shadow Projection
- [x] Phase 2C: Vector Projection Manifest
- [x] Phase 3A: Surface Policy VM
- [x] Phase 3B: Dashboard Search Surface Policy
- [x] Phase 3C: MCP Breath Search Surface Policy
- [x] Phase 4: Tombstone-only Erasure Shadow
- [x] Phase 5A: Replay Validator
- [x] Phase 5B: Deterministic Replay Property Runner
- [x] Phase 6A: Rust Replay Kernel Scaffold
- [x] Phase 7A: Policy Effective/Audit Verdicts
- [x] Phase 7B: Executable Policy Enforcement Boundary
- [x] Phase 7C: Plugin Capability Enforcement
