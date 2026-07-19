# Code Standards Diagnostics Phase 34 Implementation Plan

**Goal:** Connect the Phase 17 code standards contract to Dashboard system diagnostics for a small set of high-risk boundary artifacts.

**Architecture:** Build a fixed local artifact manifest for source files that sit on important runtime, dashboard, search, and policy boundaries. Evaluate it with `HighestDifficultyCodeStandards`. Do not run external linters, scan the full repository, mutate files, or gate release.

**Tech Stack:** `web.system.build_system_diagnostics`, `HighestDifficultyCodeStandards`, `CodeArtifactSpec`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Require code standards diagnostics check**

Assert diagnostics includes `code_standards` with an OK report.

- [x] **Step 2: Require boundary artifacts**

Assert the report covers `src/server.py`, `src/web/system.py`, `src/web/search.py`, and `src/ombrebrain/policy/surfacing.py` when those files exist under the repo root.

### Task 2: Implement Code Standards Diagnostics

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Add artifact manifest helper**

Add `_build_code_standard_artifacts()` to create `CodeArtifactSpec` entries for existing known boundary files.

- [x] **Step 2: Evaluate through code standards contract**

Append `code_standards` diagnostics check using `HighestDifficultyCodeStandards.default().evaluate_manifest(...)`.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-code-standards-diagnostics-phase34.md`

- [x] **Step 1: Document Phase 34**

Explain that this is a fixed boundary-artifact contract check, not a full repo lint.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_system_diagnostics.py tests/test_code_standards_phase17.py -q`
Result: PASS, 17 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 33: ADR Requirements Diagnostics
- [x] Phase 34: Code Standards Diagnostics
