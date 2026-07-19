# Observability Metric Boundary Phase 12 Implementation Plan

**Goal:** Implement vNext §21 observability boundaries: advanced observability may measure memory health, but must not measure user value, dependency, persuasion, manipulation, or personality compliance.

**Architecture:** Add a small `ombrebrain.observability` package with metric specs, boundary decisions, and manifest evaluation. This remains a contract layer and does not change Dashboard diagnostics yet.

**Tech Stack:** Python dataclasses, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_observability_boundary_phase12.py`

- [x] **Step 1: Write failing observability-boundary tests**

Cover:
- all vNext allowed memory-health metrics pass.
- forbidden user-value/manipulation metrics are rejected.
- unknown metrics are rejected by default.
- allowed metrics cannot carry forbidden user-value labels.
- manifest/report evaluation returns JSON-safe decisions.
- observability package exports the boundary symbols.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_observability_boundary_phase12.py -q`
Expected: FAIL because `ombrebrain.observability` does not exist yet.

### Task 2: Implement Metric Boundary

**Files:**
- Add: `src/ombrebrain/observability/__init__.py`
- Add: `src/ombrebrain/observability/metrics.py`

- [x] **Step 1: Add metric spec and decision contracts**

Create `ObservabilityMetricSpec`, `ObservabilityDecision`, and `ObservabilityReport`.

- [x] **Step 2: Add boundary evaluator**

Create `ObservabilityMetricBoundary` with vNext §21 allowed and forbidden metric names.

- [x] **Step 3: Add manifest evaluation**

Evaluate a list of metric specs and return JSON-safe report details.

- [x] **Step 4: Export observability symbols**

Export the new contracts from `ombrebrain.observability`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_observability_boundary_phase12.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-observability-boundary-phase12.md`

- [x] **Step 1: Document Phase 12**

Explain that metric boundaries are contract-only and not yet wired into Dashboard diagnostics.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_observability_boundary_phase12.py tests/test_system_diagnostics.py tests/test_formal_invariants_phase10.py -q`
Expected: selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 11: Plugin Agency Boundary
- [x] Phase 12: Observability Metric Boundary
