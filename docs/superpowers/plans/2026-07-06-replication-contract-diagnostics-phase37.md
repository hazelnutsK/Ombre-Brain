# Replication Contract Diagnostics Phase 37 Implementation Plan

**Goal:** Connect the Phase 14 replication contract to Dashboard system diagnostics so local diagnostics can expose single-writer and trace/tombstone replication boundaries.

**Architecture:** Evaluate representative topology and segment samples through `ReplicationContract`. Do not start a cluster, perform network replication, mutate buckets, or change runtime/GitHub sync behavior.

**Tech Stack:** `web.system.build_system_diagnostics`, `ReplicationContract`, `ReplicationTopology`, `ReplicationSegment`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Require replication diagnostics check**

Assert diagnostics includes `replication_contract` with OK status.

- [x] **Step 2: Require topology and segment decisions**

Assert the check includes topology and segment decisions.

### Task 2: Implement Replication Diagnostics

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Add diagnostics decision builder**

Add `_build_replication_contract_diagnostics()` using safe single-writer topology and tombstone-preserving segment samples.

- [x] **Step 2: Append diagnostics check**

Append `replication_contract` check to `build_system_diagnostics()`.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-replication-contract-diagnostics-phase37.md`

- [x] **Step 1: Document Phase 37**

Explain that this is read-only contract validation, not live cluster replication.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_system_diagnostics.py tests/test_replication_contract_phase14.py -q`
Result: PASS, 10 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 36: Crash Recovery Diagnostics
- [x] Phase 37: Replication Contract Diagnostics
