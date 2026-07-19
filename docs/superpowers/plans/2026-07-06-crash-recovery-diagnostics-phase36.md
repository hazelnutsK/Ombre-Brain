# Crash Recovery Diagnostics Phase 36 Implementation Plan

**Goal:** Connect the Phase 13 crash recovery contract to Dashboard system diagnostics so local diagnostics can expose ledger-wins write/read/recovery ordering.

**Architecture:** Evaluate representative write path, read path, and recovery plan samples through `CrashRecoveryContract`. Do not perform real fsync, repair WAL, rebuild projections, mutate buckets, or change runtime recovery behavior.

**Tech Stack:** `web.system.build_system_diagnostics`, `CrashRecoveryContract`, `PathStep`, `CrashRecoveryPlan`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Require crash recovery diagnostics check**

Assert diagnostics includes `crash_recovery` with OK status.

- [x] **Step 2: Require three decision paths**

Assert the check includes write, read, and recovery-plan decisions.

### Task 2: Implement Crash Recovery Diagnostics

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Add diagnostics decision builder**

Add `_build_crash_recovery_diagnostics()` using vNext write path, read path, and ledger-wins recovery plan samples.

- [x] **Step 2: Append diagnostics check**

Append `crash_recovery` check to `build_system_diagnostics()`.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-crash-recovery-diagnostics-phase36.md`

- [x] **Step 1: Document Phase 36**

Explain that this is read-only contract validation, not live recovery.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_system_diagnostics.py tests/test_crash_recovery_phase13.py -q`
Result: PASS, 10 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 35: Red Lines Diagnostics
- [x] Phase 36: Crash Recovery Diagnostics
