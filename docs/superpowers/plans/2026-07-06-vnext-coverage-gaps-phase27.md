# vNext Coverage Gaps Phase 27 Implementation Plan

**Goal:** Make the vNext coverage matrix directly list which implemented phases still lack preflight sample coverage.

**Architecture:** Keep `vnext_coverage` read-only. Add `preflight_gaps` and `next_preflight_targets` to the matrix output. These are planning signals, not failing checks.

**Tech Stack:** `VNextCoverageMatrix`, `VNextPreflightReportBuilder`, `tools/vnext_preflight.py --coverage-only`, pytest.

---

### Task 1: Gap Tests

**Files:**
- Modify: `tests/test_vnext_preflight_report_phase22.py`

- [x] **Step 1: Require gap fields**

Assert coverage output includes `preflight_gap_count`, `preflight_gaps`, and `next_preflight_targets`.

- [x] **Step 2: Verify first recommended target**

Assert the first recommended target is `phase_1`, because ledger mirror is implemented and tested but not yet sampled by vNext preflight.

- [x] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_vnext_preflight_report_phase22.py -k "summarizes or exports" -q`
Result: FAIL, because the gap fields did not exist yet.

### Task 2: Implement Gaps

**Files:**
- Modify: `src/ombrebrain/maintenance/vnext_coverage.py`

- [x] **Step 1: Add gap calculation**

Implemented phases with no available preflight checks are listed in `preflight_gaps`.

- [x] **Step 2: Add next targets**

Expose the first five gaps as `next_preflight_targets`.

- [x] **Step 3: Run focused tests**

Run: `pytest tests/test_vnext_preflight_report_phase22.py -q`
Result: PASS, 7 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-vnext-coverage-gaps-phase27.md`

- [x] **Step 1: Document gap semantics**

Clarify that gaps are planning signals, not failed checks.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_vnext_preflight_report_phase22.py tests/test_v3_maintenance_report.py tests/test_system_diagnostics.py -q`
Result: PASS, 16 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 26: vNext Coverage Matrix
- [x] Phase 27: vNext Coverage Gaps
