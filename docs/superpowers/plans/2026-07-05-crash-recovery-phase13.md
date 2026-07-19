# Crash Recovery Contract Phase 13 Implementation Plan

**Goal:** Implement vNext §22 Concurrency and Crash Recovery as a shadow contract: write/read paths must be ordered correctly, and after crash recovery the ledger wins while projections/indexes rebuild.

**Architecture:** Add `ombrebrain.resilience.recovery` with immutable path-step contracts and recovery-plan evaluation. The module is diagnostic-only and does not change `LedgerMirror`, Markdown writes, or projection rebuild execution.

**Tech Stack:** Python dataclasses/enums, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_crash_recovery_phase13.py`

- [x] **Step 1: Write failing recovery-contract tests**

Cover:
- write path order must be policy preflight → append WAL → fsync → projection update → Markdown repair/update → return trace id.
- returning a trace id before fsync is rejected.
- read path order must be candidate generation → canonical trace verification → policy gate → surface budget → context compiler.
- crash recovery plan must declare ledger wins, projections rebuild, Markdown repaired, indexes disposable.
- recovery report is JSON-safe.
- resilience package exports recovery contract symbols.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_crash_recovery_phase13.py -q`
Expected: FAIL because `ombrebrain.resilience.recovery` does not exist yet.

### Task 2: Implement Recovery Contract

**Files:**
- Add: `src/ombrebrain/resilience/recovery.py`
- Modify: `src/ombrebrain/resilience/__init__.py`

- [x] **Step 1: Add path and recovery dataclasses**

Create `PathStep`, `PathContractDecision`, `CrashRecoveryPlan`, `CrashRecoveryDecision`, and `CrashRecoveryContract`.

- [x] **Step 2: Add write/read path validation**

Validate strict ordering and missing required steps.

- [x] **Step 3: Add recovery rule validation**

Validate the four vNext recovery principles: ledger wins, projections rebuild, Markdown is repaired, indexes are disposable.

- [x] **Step 4: Export resilience symbols**

Export recovery symbols from `ombrebrain.resilience`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_crash_recovery_phase13.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-crash-recovery-phase13.md`

- [x] **Step 1: Document Phase 13**

Explain that recovery contract is diagnostic-only and not yet a live WAL/fsync implementation.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_crash_recovery_phase13.py tests/test_ledger_replay_phase5a.py tests/test_projection_mirror_phase2.py -q`
Expected: selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 12: Observability Metric Boundary
- [x] Phase 13: Crash Recovery Contract
