# Preflight Report Self Diagnostics Phase 41 Implementation Plan

**Goal:** Expose the Phase 22 vNext preflight self-check as a standalone Dashboard system diagnostics check.

**Architecture:** Reuse the already generated `vnext_preflight` report and extract `checks.preflight_report_self`. Do not rebuild preflight, execute the CLI, write output files, or make the self-check a release gate.

**Tech Stack:** `web.system.build_system_diagnostics`, `VNextPreflightReportBuilder`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Require preflight report self diagnostics check**

Assert diagnostics includes `preflight_report_self` with OK status.

- [x] **Step 2: Require complete required-check report**

Assert no required checks are missing and no malformed checks are present.

### Task 2: Implement Preflight Report Self Diagnostics

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Add extraction helper**

Add `_build_preflight_report_self_diagnostics()` that extracts the nested self-check from `vnext_preflight`.

- [x] **Step 2: Append diagnostics check**

Append `preflight_report_self` after `vnext_preflight` is generated, and emit a warning when preflight is skipped or fails.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-preflight-report-self-diagnostics-phase41.md`

- [x] **Step 1: Document Phase 41**

Explain that this is report extraction, not a second preflight run.

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

- [x] Phase 40: Preflight CLI Diagnostics
- [x] Phase 41: Preflight Report Self Diagnostics
