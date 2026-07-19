# Migration Preservation Diagnostics Phase 38 Implementation Plan

**Goal:** Connect the Phase 15 migration preservation contract to Dashboard system diagnostics so local diagnostics can expose trace-field preservation and Python-first migration ordering.

**Architecture:** Evaluate representative records and phase-plan samples through `MigrationPreservationContract`. Do not run migration adapters, migrate embeddings, mutate buckets, or change Rust/kernel startup behavior.

**Tech Stack:** `web.system.build_system_diagnostics`, `MigrationPreservationContract`, `MigrationTraceRecord`, `MigrationPhasePlan`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Require migration diagnostics check**

Assert diagnostics includes `migration_preservation` with OK status.

- [x] **Step 2: Require records and phase-plan decisions**

Assert the check includes records and phase-plan decisions.

### Task 2: Implement Migration Diagnostics

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Add diagnostics decision builder**

Add `_build_migration_preservation_diagnostics()` using safe preserved-records and Python-first phase-plan samples.

- [x] **Step 2: Append diagnostics check**

Append `migration_preservation` check to `build_system_diagnostics()`.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-migration-preservation-diagnostics-phase38.md`

- [x] **Step 1: Document Phase 38**

Explain that this is read-only contract validation, not live migration.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_system_diagnostics.py tests/test_migration_contract_phase15.py -q`
Result: PASS, 9 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 37: Replication Contract Diagnostics
- [x] Phase 38: Migration Preservation Diagnostics
