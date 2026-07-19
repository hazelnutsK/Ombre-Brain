# SQLite Projection Phase 2B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a rebuildable SQLite/FTS shadow projection derived from the Phase 1 ledger mirror without replacing Markdown buckets, BM25, embeddings, or Dashboard reads.

**Architecture:** Keep `TraceCatalogProjection` as the in-memory replay model. Add `TraceSQLiteProjection` as a persistence adapter that rebuilds a local SQLite database from ledger events, stores trace catalog rows plus metadata JSON, and optionally maintains an FTS5 table when SQLite supports it. Diagnostics report this projection as shadow/non-canonical with applied sequence, lag, trace count, and tombstone count.

**Tech Stack:** Python stdlib `sqlite3`, JSONL ledger mirror, pytest.

---

### Task 1: SQLite Projection Contract

**Files:**
- Create: `src/projection_sqlite.py`
- Test: `tests/test_sqlite_projection_phase2b.py`

- [x] **Step 1: Write the failing test**

Add a test that creates ledger events, rebuilds a SQLite projection, verifies the database file exists, verifies report fields, and verifies rows can be read back by trace id.

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sqlite_projection_phase2b.py::test_sqlite_projection_rebuilds_trace_catalog_database -q`
Expected: FAIL because `projection_sqlite` does not exist.

- [x] **Step 3: Implement minimal SQLite projection**

Create `TraceSQLiteProjection` with `rebuild(events)`, `to_report(source_latest_seq=0)`, and `get_trace(trace_id)` methods. Use `TraceCatalogProjection` internally so lifecycle semantics stay centralized.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_sqlite_projection_phase2b.py::test_sqlite_projection_rebuilds_trace_catalog_database -q`
Expected: PASS.

### Task 2: Optional FTS Search

**Files:**
- Modify: `src/projection_sqlite.py`
- Test: `tests/test_sqlite_projection_phase2b.py`

- [x] **Step 1: Write the failing test**

Add a test that indexes payload text such as name/tags/domain/why_remembered and searches it through `TraceSQLiteProjection.search()`.

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sqlite_projection_phase2b.py::test_sqlite_projection_searches_metadata_text -q`
Expected: FAIL because search is not implemented.

- [x] **Step 3: Implement search**

Try to create an FTS5 table. If unavailable, keep a fallback text table and search with `LIKE`. Reports must expose `fts_enabled`.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_sqlite_projection_phase2b.py::test_sqlite_projection_searches_metadata_text -q`
Expected: PASS.

### Task 3: Diagnostics Wiring

**Files:**
- Modify: `src/bucket_manager.py`
- Modify: `docs/INTERNALS.md`
- Test: `tests/test_projection_mirror_phase2.py`
- Test: `tests/test_system_diagnostics.py`

- [x] **Step 1: Write/update failing tests**

Assert `BucketManager.ledger_integrity_report()` includes `sqlite_projection` with shadow role and lag information.

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_projection_mirror_phase2.py::test_bucket_manager_ledger_report_includes_sqlite_projection -q`
Expected: FAIL because diagnostics do not expose SQLite projection yet.

- [x] **Step 3: Wire diagnostics**

Instantiate `TraceSQLiteProjection` at `<buckets_dir>/_ledger/projections/trace_catalog.sqlite3` inside `ledger_integrity_report()` and rebuild it from the same event list. Catch/report projection errors without blocking bucket operations.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_sqlite_projection_phase2b.py tests/test_projection_mirror_phase2.py tests/test_system_diagnostics.py -q`
Expected: PASS.

### Task 4: Regression Verification

**Files:**
- Modify: `docs/superpowers/plans/2026-07-03-sqlite-projection-phase2b.md`

- [x] **Step 1: Run targeted regression**

Run: `pytest tests/test_sqlite_projection_phase2b.py tests/test_projection_mirror_phase2.py tests/test_ledger_replay_phase5a.py tests/test_system_diagnostics.py -q`
Expected: targeted tests pass.

- [x] **Step 2: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 3: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 1: Ledger Mirror
- [x] Phase 2A: In-memory Trace Catalog Projection
- [x] Phase 2B: SQLite/FTS Shadow Projection
- [x] Phase 3: Surface Policy VM
- [x] Phase 4: Tombstone-only Erasure Shadow
- [x] Phase 5A: Replay Validator
- [x] Phase 5B: Deterministic Replay Property Runner
- [x] Phase 6A: Rust Replay Kernel Scaffold
- [x] Phase 7A: Policy Effective/Audit Verdicts
- [x] Phase 7B: Executable Policy Enforcement Boundary
- [x] Phase 7C: Plugin Capability Enforcement
