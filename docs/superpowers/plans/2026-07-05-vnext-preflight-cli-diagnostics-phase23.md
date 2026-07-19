# vNext Preflight CLI and Diagnostics Phase 23 Implementation Plan

**Goal:** Make the vNext preflight report directly runnable from the command line and visible in system diagnostics.

**Architecture:** Add `tools/vnext_preflight.py` beside `tools/v3_health_report.py`, and add a `vnext_preflight` check to `web.system.build_system_diagnostics()`. This surfaces the Phase 22 aggregate without changing live memory behavior or adding a release gate.

**Tech Stack:** Existing `LegacyRuntime`, `VNextPreflightReportBuilder`, Dashboard system diagnostics, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_v3_maintenance_report.py`
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Add failing CLI and diagnostics tests**

Cover:
- `tools/vnext_preflight.py` prints JSON.
- `tools/vnext_preflight.py --output` writes JSON.
- `/api/system/diagnostics` payload includes a `vnext_preflight` check.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_v3_maintenance_report.py tests/test_system_diagnostics.py -q`
Result: FAIL, 3 failed because CLI and diagnostics hook did not exist yet.

### Task 2: Implement CLI and Diagnostics

**Files:**
- Add: `tools/vnext_preflight.py`
- Modify: `src/web/system.py`

- [x] **Step 1: Add CLI**

Create a read-only JSON CLI with `--buckets-dir` and optional `--output`.

- [x] **Step 2: Add diagnostics check**

Add a `vnext_preflight` system diagnostics check that runs `VNextPreflightReportBuilder`.

- [x] **Step 3: Run tests to verify they pass**

Run: `pytest tests/test_v3_maintenance_report.py tests/test_system_diagnostics.py -q`
Result: PASS, 7 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-vnext-preflight-cli-diagnostics-phase23.md`

- [x] **Step 1: Document Phase 23**

Explain the CLI and diagnostics entry points.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_vnext_preflight_report_phase22.py tests/test_v3_maintenance_report.py tests/test_system_diagnostics.py -q`
Result: PASS, 11 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 705 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 22: vNext Preflight Report
- [x] Phase 23: vNext Preflight CLI and Diagnostics
