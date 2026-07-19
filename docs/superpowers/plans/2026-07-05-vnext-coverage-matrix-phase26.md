# vNext Coverage Matrix Phase 26 Implementation Plan

**Goal:** Add a machine-readable vNext phase coverage matrix to the local preflight report, so local progress can be inspected without manually reading every implementation plan.

**Architecture:** Keep the matrix separate from `maintenance/report.py` in `ombrebrain.maintenance.vnext_coverage`. The preflight check reports phase plans, test files, and preflight check mappings. It is read-only and does not scan user memory.

**Tech Stack:** `VNextCoverageMatrix`, `VNextPreflightReportBuilder`, pytest.

---

### Task 1: Coverage Tests

**Files:**
- Modify: `tests/test_vnext_preflight_report_phase22.py`

- [x] **Step 1: Require coverage matrix in preflight**

Assert `checks.vnext_coverage` exists, uses schema `vnext-coverage.v1`, lists at least 30 phases, reports 100% local completion for the current local plan set, and maps at least 20 phases to preflight checks.

- [x] **Step 2: Require maintenance export**

Assert `VNextCoverageMatrix` is exported and includes both early and recent phases.

### Task 2: Implement Matrix

**Files:**
- Add: `src/ombrebrain/maintenance/vnext_coverage.py`
- Modify: `src/ombrebrain/maintenance/report.py`
- Modify: `src/ombrebrain/maintenance/__init__.py`

- [x] **Step 1: Add coverage dataclasses**

Create `VNextCoverageItem` and `VNextCoverageMatrix`.

- [x] **Step 2: Add default local phase mapping**

Map Phase 1 through Phase 25 to plan files, test files, and available preflight checks.

- [x] **Step 3: Attach matrix to preflight**

Add `checks.vnext_coverage` after the regular check map is built, so it can evaluate which preflight checks are actually present.

- [x] **Step 4: Run focused preflight tests**

Run: `pytest tests/test_vnext_preflight_report_phase22.py -q`
Result: PASS, 7 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-05-vnext-coverage-matrix-phase26.md`

- [x] **Step 1: Document Phase 26**

Explain that `vnext_coverage` is a progress/index matrix, not a release gate.

- [x] **Step 2: Add CLI coverage-only mode**

Add `tools/vnext_preflight.py --coverage-only` so maintainers can print only the `vnext-coverage.v1` matrix. Add CLI tests for stdout and `--output`.

- [x] **Step 3: Run targeted regression**

Run: `pytest tests/test_vnext_preflight_report_phase22.py tests/test_v3_maintenance_report.py tests/test_system_diagnostics.py -q`
Result: PASS, 16 passed.

- [x] **Step 4: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 5: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 25: vNext Preflight Coverage Expansion
- [x] Phase 26: vNext Coverage Matrix
