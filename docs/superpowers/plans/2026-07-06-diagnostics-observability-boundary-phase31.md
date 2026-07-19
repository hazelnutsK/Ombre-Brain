# Diagnostics Observability Boundary Phase 31 Implementation Plan

**Goal:** Connect the Phase 12 observability boundary to Dashboard system diagnostics so live diagnostics metrics remain constrained to memory-health signals.

**Architecture:** Build a small metrics manifest from already-read buckets and ledger diagnostics. Validate it through `ObservabilityMetricBoundary` before exposing it as a Dashboard diagnostics check. Do not add network calls, scan bucket content, write vault state, or introduce release gating.

**Tech Stack:** `web.system.build_system_diagnostics`, `ObservabilityMetricBoundary`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Require diagnostics observability check**

Assert `/api/system/diagnostics` payload includes `observability_boundary` with an OK boundary report.

- [x] **Step 2: Require memory-health metric names**

Assert the live manifest includes only memory-health metrics such as `trace_count_by_state`, `archive_growth`, `projection_lag`, and `tombstone_count`.

### Task 2: Implement Live Diagnostic Boundary

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Build diagnostics metrics manifest**

Add `_build_diagnostics_observability_metrics()` that converts existing bucket and ledger diagnostics into a small allowed metric list.

- [x] **Step 2: Evaluate metrics through boundary**

Append an `observability_boundary` diagnostics check using `ObservabilityMetricBoundary.default().evaluate_manifest(...)`.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-diagnostics-observability-boundary-phase31.md`

- [x] **Step 1: Document Phase 31**

Explain that diagnostics observability is live but read-only and memory-health constrained.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_system_diagnostics.py tests/test_observability_boundary_phase12.py -q`
Result: PASS, 21 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 30: Preflight Gap Closure
- [x] Phase 31: Diagnostics Observability Boundary
