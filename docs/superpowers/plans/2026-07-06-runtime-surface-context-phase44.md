# Runtime Surface Context Phase 44 Implementation Plan

**Goal:** Move surface-context compilation from contract/preflight-only usage into a reusable `LegacyRuntime` API.

**Architecture:** Add `LegacyRuntime.compile_surface_context()` that compiles allowed surface decisions and memory payloads through `SurfaceContextCompiler`, then validates the resulting context items with `FormalInvariantChecker`. Have vNext preflight reuse this runtime API. Do not change visible `breath()` or `/api/search` output yet.

**Tech Stack:** `LegacyRuntime`, `SurfaceContextCompiler`, `FormalInvariantChecker`, `VNextPreflightReportBuilder`, pytest.

---

### Task 1: Runtime Tests

**Files:**
- Modify: `tests/test_v3_legacy_runtime.py`

- [x] **Step 1: Require runtime surface context API**

Assert runtime compiles allowed decisions into `surface-context.v1` while filtering denied decisions.

- [x] **Step 2: Require invariant validation**

Assert compiled items remain non-instructional and imperative wording is redacted.

### Task 2: Runtime Implementation

**Files:**
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Modify: `src/ombrebrain/maintenance/report.py`

- [x] **Step 1: Add runtime compiler API**

Add `LegacyRuntime.compile_surface_context()`.

- [x] **Step 2: Reuse API in preflight**

Make `_surface_context_check()` call the runtime API.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-runtime-surface-context-phase44.md`

- [x] **Step 1: Document Phase 44**

Explain that this is runtime API exposure, not a live output format change.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_v3_legacy_runtime.py tests/test_vnext_preflight_report_phase22.py -q`
Result: PASS, 28 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 715 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 43: Runtime Command Boundary Health
- [x] Phase 44: Runtime Surface Context
