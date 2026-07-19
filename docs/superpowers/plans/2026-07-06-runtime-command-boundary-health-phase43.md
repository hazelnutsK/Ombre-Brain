# Runtime Command Boundary Health Phase 43 Implementation Plan

**Goal:** Move command-boundary evidence from preflight-only scanning into a reusable `LegacyRuntime` health API.

**Architecture:** Add an app-level command-boundary health helper and expose it through `LegacyRuntime.debug_command_boundary_health(limit=50)`. Have vNext preflight reuse this runtime API. Do not turn command-boundary reports into an enforcement gate or rewrite fabric events.

**Tech Stack:** `LegacyRuntime`, `build_runtime_command_boundary_health`, `VNextPreflightReportBuilder`, pytest.

---

### Task 1: Runtime Tests

**Files:**
- Modify: `tests/test_v3_legacy_runtime.py`

- [x] **Step 1: Require runtime command-boundary health**

Assert runtime reports receipt counts, missing receipts, invalid receipts, and issues after real tool/execution events.

- [x] **Step 2: Require limit behavior**

Assert `debug_command_boundary_health(limit=1)` scans only the most recent event while preserving total event count.

### Task 2: Runtime Implementation

**Files:**
- Add: `src/ombrebrain/app/command_boundary_health.py`
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Modify: `src/ombrebrain/maintenance/report.py`

- [x] **Step 1: Extract reusable health builder**

Add `build_runtime_command_boundary_health()` for event scanning and receipt validation.

- [x] **Step 2: Expose runtime API**

Add `LegacyRuntime.debug_command_boundary_health()`.

- [x] **Step 3: Reuse API in preflight**

Make `_runtime_command_boundary_check()` call the runtime API when available.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-runtime-command-boundary-health-phase43.md`

- [x] **Step 1: Document Phase 43**

Explain that this is runtime health observability, not enforcement.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_v3_legacy_runtime.py tests/test_vnext_preflight_report_phase22.py -q`
Result: PASS, 27 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 714 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 42: vNext Coverage Diagnostics
- [x] Phase 43: Runtime Command Boundary Health
