# vNext Preflight Phase 22 Implementation Plan

**Goal:** Aggregate the vNext shadow/contract layer into one local preflight report, so the architecture work can be checked as a coherent release/readiness signal.

**Architecture:** Add `VNextPreflightReportBuilder` in `ombrebrain.maintenance.report`. It evaluates representative safe specs for the contracts added in Phase 16-21 and returns a JSON-safe summary. Include the report inside `V3MaintenanceReportBuilder` without changing live Dashboard routes in this phase.

**Tech Stack:** Existing maintenance report builder, vNext contracts, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_vnext_preflight_report_phase22.py`

- [x] **Step 1: Write failing preflight tests**

Cover:
- default preflight summarizes public tool, code standards, command boundary, surface context, ADR, and red-line checks.
- red-line overrides make the report fail.
- V3 maintenance report includes `vnext_preflight`.
- maintenance package exports `VNextPreflightReportBuilder`.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_vnext_preflight_report_phase22.py -q`
Result: FAIL, 4 failed because the preflight builder did not exist yet.

### Task 2: Implement Preflight Builder

**Files:**
- Modify: `src/ombrebrain/maintenance/report.py`
- Modify: `src/ombrebrain/maintenance/__init__.py`

- [x] **Step 1: Add `VNextPreflightReportBuilder`**

Build JSON-safe checks from Phase 16-21 contracts.

- [x] **Step 2: Support red-line feature overrides**

Allow callers/tests to pass candidate feature specs into red-line evaluation.

- [x] **Step 3: Include preflight in V3 maintenance report**

Add `vnext_preflight` and fold it into top-level `ok`.

- [x] **Step 4: Export maintenance symbol**

Export `VNextPreflightReportBuilder` from `ombrebrain.maintenance`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_vnext_preflight_report_phase22.py -q`
Result: PASS, 4 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-vnext-preflight-phase22.md`

- [x] **Step 1: Document Phase 22**

Explain that preflight is a local aggregate report and not yet a GitHub/PR gate.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_vnext_preflight_report_phase22.py tests/test_v3_maintenance_report.py tests/test_red_lines_phase21.py -q`
Result: PASS, 18 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 703 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 21: Red Lines Contract
- [x] Phase 22: vNext Preflight Report
