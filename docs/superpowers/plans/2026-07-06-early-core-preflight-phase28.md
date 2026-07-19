# Early Core Preflight Phase 28 Implementation Plan

**Goal:** Add vNext preflight sample coverage for the earliest core phases listed by `next_preflight_targets`: ledger mirror, rebuildable projections, vector projection manifest, and ledger replay.

**Architecture:** Keep checks sample-driven and temporary-directory based. They must not read real user buckets, mutate the vault, or change runtime behavior.

**Tech Stack:** `LedgerMirror`, `TraceCatalogProjection`, `TraceSQLiteProjection`, `TraceVectorProjectionManifest`, `LedgerReplayValidator`, `VNextPreflightReportBuilder`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_vnext_preflight_report_phase22.py`

- [x] **Step 1: Require early core checks**

Require these checks in vNext preflight:
- `ledger_mirror`
- `trace_catalog_projection`
- `sqlite_projection`
- `vector_projection`
- `ledger_replay`

- [x] **Step 2: Require gap progress**

Assert `phase_1` is no longer in `preflight_gaps` and the first `next_preflight_targets` entry becomes `phase_5b`.

- [x] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_vnext_preflight_report_phase22.py::test_vnext_preflight_report_summarizes_new_contracts -q`
Result: FAIL, because `ledger_mirror` and sibling checks did not exist yet.

### Task 2: Implement Early Core Checks

**Files:**
- Modify: `src/ombrebrain/maintenance/report.py`
- Modify: `src/ombrebrain/maintenance/vnext_coverage.py`

- [x] **Step 1: Add sample ledger helper**

Create a temporary ledger with active and tombstone traces.

- [x] **Step 2: Add check functions**

Evaluate ledger mirror integrity, trace catalog rebuild, SQLite/FTS rebuild/search, vector manifest consistency, and replay validator health.

- [x] **Step 3: Update coverage matrix**

Map Phase 1, Phase 2A, Phase 2B, Phase 2C, and Phase 5A to the new preflight checks.

- [x] **Step 4: Verify focused preflight**

Run: `pytest tests/test_vnext_preflight_report_phase22.py -q`
Result: PASS, 7 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-early-core-preflight-phase28.md`

- [x] **Step 1: Document Phase 28**

Explain that the new early-core checks use temporary sample data only.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_vnext_preflight_report_phase22.py tests/test_v3_maintenance_report.py tests/test_system_diagnostics.py tests/test_ledger_mirror_phase1.py tests/test_projection_mirror_phase2.py tests/test_sqlite_projection_phase2b.py tests/test_vector_projection_phase2c.py tests/test_ledger_replay_phase5a.py -q`
Result: PASS, 32 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 27: vNext Coverage Gaps
- [x] Phase 28: Early Core Preflight Samples
