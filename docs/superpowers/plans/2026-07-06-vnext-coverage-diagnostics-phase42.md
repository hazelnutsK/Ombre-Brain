# vNext Coverage Diagnostics Phase 42 Implementation Plan

**Goal:** Expose the Phase 26 vNext coverage matrix as a standalone Dashboard system diagnostics check.

**Architecture:** Reuse the already generated `vnext_preflight` report and extract `checks.vnext_coverage`. Do not rebuild the matrix, execute the CLI, scan real buckets, or treat coverage percent as a release gate.

**Tech Stack:** `web.system.build_system_diagnostics`, `VNextPreflightReportBuilder`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Require vNext coverage diagnostics check**

Assert diagnostics includes `vnext_coverage` with OK status.

- [x] **Step 2: Require coverage matrix fields**

Assert the standalone check exposes `vnext-coverage.v1`, phase count, zero preflight gaps, and empty next targets.

### Task 2: Implement vNext Coverage Diagnostics

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Add extraction helper**

Add `_build_vnext_coverage_diagnostics()` that extracts the nested coverage check from `vnext_preflight`.

- [x] **Step 2: Append diagnostics check**

Append `vnext_coverage` after `vnext_preflight` is generated, and emit a warning when preflight is skipped or fails.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-vnext-coverage-diagnostics-phase42.md`

- [x] **Step 1: Document Phase 42**

Explain that this is report extraction, not a second coverage calculation.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_system_diagnostics.py tests/test_vnext_preflight_report_phase22.py -q`
Result: PASS, 9 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 41: Preflight Report Self Diagnostics
- [x] Phase 42: vNext Coverage Diagnostics
