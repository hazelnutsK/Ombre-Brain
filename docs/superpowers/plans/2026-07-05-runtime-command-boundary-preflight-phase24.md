# Runtime Command Boundary Preflight Phase 24 Implementation Plan

**Goal:** Connect real runtime `command_boundary` receipts to the vNext preflight report, so Phase 18 boundary rules are checked against recent fabric events as evidence, not only sample contracts.

**Architecture:** Keep the existing synthetic `command_boundary` contract check, add a separate `runtime_command_boundary` check in `VNextPreflightReportBuilder`, and make old receipt-less events a warning instead of a hard failure.

**Tech Stack:** `LegacyRuntime`, `MemoryFabric`, `AdvancedCommandBoundaryContract`, `VNextPreflightReportBuilder`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_vnext_preflight_report_phase22.py`

- [x] **Step 1: Add failing runtime evidence tests**

Cover:
- empty runtime passes with `runtime_command_boundary.receipt_count == 0`.
- runtime `hold` execution receipt is discovered and evaluated.
- old legacy events with `command_plan` but no `command_boundary` become warnings.
- invalid runtime receipts make preflight fail.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_vnext_preflight_report_phase22.py -k "runtime_command_boundary or summarizes" -q`
Result: FAIL, because `runtime_command_boundary` did not exist yet.

### Task 2: Implement Runtime Receipt Scan

**Files:**
- Modify: `src/ombrebrain/maintenance/report.py`

- [x] **Step 1: Add `runtime_command_boundary` check**

Scan recent fabric events, find events with `command_boundary`, `command_boundary_error`, `command_plan`, or legacy execution/tool source chains.

- [x] **Step 2: Re-evaluate receipts**

Use `AdvancedCommandBoundaryContract` to evaluate each real receipt and report invalid receipts as errors.

- [x] **Step 3: Treat legacy missing receipts as warnings**

Missing receipt events are counted in `missing_receipts` and set check `status="warning"` while leaving top-level preflight `ok=True`.

- [x] **Step 4: Run focused tests**

Run: `pytest tests/test_vnext_preflight_report_phase22.py -q`
Result: PASS, 7 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-05-runtime-command-boundary-preflight-phase24.md`

- [x] **Step 1: Document Phase 24**

Explain the `runtime_command_boundary` check, warning behavior for old events, and error behavior for invalid receipts.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_vnext_preflight_report_phase22.py tests/test_v3_maintenance_report.py tests/test_system_diagnostics.py tests/test_v3_legacy_runtime.py -q`
Result: PASS, 32 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 710 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 22: vNext Preflight Report
- [x] Phase 23: vNext Preflight CLI and Diagnostics
- [x] Phase 24: Runtime Command Boundary Preflight
