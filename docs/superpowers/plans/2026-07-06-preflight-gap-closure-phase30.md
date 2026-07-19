# Preflight Gap Closure Phase 30 Implementation Plan

**Goal:** Close the remaining local vNext preflight coverage gaps for Phase 23 and Phase 25 so `vnext_coverage.preflight_gaps` reaches zero.

**Architecture:** Keep the new checks read-only and non-recursive. The aggregate preflight should confirm CLI/diagnostics entry points and coverage-expansion semantics without running the CLI from inside itself, scanning real buckets, or mutating runtime state.

**Tech Stack:** `VNextPreflightReportBuilder`, `VNextCoverageMatrix`, `tools/vnext_preflight.py`, Dashboard diagnostics source, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_vnext_preflight_report_phase22.py`

- [x] **Step 1: Require final gap checks**

Require:
- `preflight_cli_diagnostics`
- `preflight_coverage_expansion`

- [x] **Step 2: Require gap closure**

Assert `preflight_gap_count == 0`, `preflight_coverage_percent == 100.0`, and `next_preflight_targets == []`.

- [x] **Step 3: Run focused red/green test**

Run: `pytest tests/test_vnext_preflight_report_phase22.py::test_vnext_preflight_report_summarizes_new_contracts -q`
Result: PASS after implementation, 1 passed.

### Task 2: Implement Final Checks

**Files:**
- Modify: `src/ombrebrain/maintenance/report.py`
- Modify: `src/ombrebrain/maintenance/vnext_coverage.py`

- [x] **Step 1: Add CLI/diagnostics check**

Add `preflight_cli_diagnostics`, which statically verifies the local CLI options and Dashboard diagnostics hook.

- [x] **Step 2: Add coverage-expansion check**

Add `preflight_coverage_expansion`, which verifies Phase 8-15 aggregate checks are present and currently passing.

- [x] **Step 3: Update coverage matrix**

Map Phase 23 to `preflight_cli_diagnostics` and Phase 25 to `preflight_coverage_expansion`.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-preflight-gap-closure-phase30.md`

- [x] **Step 1: Document Phase 30**

Explain that gap closure remains a local signal, not a release gate.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_vnext_preflight_report_phase22.py tests/test_v3_maintenance_report.py tests/test_system_diagnostics.py -q`
Result: PASS, 16 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

- [x] **Step 5: Confirm coverage-only gap closure**

Run: `python tools/vnext_preflight.py --buckets-dir buckets --coverage-only`
Result: PASS; `preflight_covered_count=36`, `phase_count=36`, `preflight_gap_count=0`, `preflight_coverage_percent=100.0`, `next_preflight_targets=[]`.

### Status

- [x] Phase 29: Mid Core Preflight Samples
- [x] Phase 30: Preflight Gap Closure
