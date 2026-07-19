# Red Lines Diagnostics Phase 35 Implementation Plan

**Goal:** Connect the Phase 21 red lines contract to Dashboard system diagnostics so diagnostic feature claims are checked against vNext no-go boundaries.

**Architecture:** Build a small local feature-claim manifest from diagnostics checks that already exist in the payload. Evaluate it with `RedLineContract`. Do not scan PRs, block release, mutate runtime state, or introduce a GitHub Action.

**Tech Stack:** `web.system.build_system_diagnostics`, `RedLineContract`, `RedLineFeatureSpec`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Require red lines diagnostics check**

Assert diagnostics includes `red_lines` with an OK report and zero violations.

- [x] **Step 2: Require current diagnostic features**

Assert the report covers `system_diagnostics`, `public_tool_manifest`, and `code_standards`.

### Task 2: Implement Red Lines Diagnostics

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Build diagnostics feature claims**

Add `_build_diagnostics_red_line_features()` to create safe feature claims from existing diagnostics checks.

- [x] **Step 2: Evaluate through red line contract**

Append `red_lines` diagnostics check using `RedLineContract.default().evaluate_manifest(...)`.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-red-lines-diagnostics-phase35.md`

- [x] **Step 1: Document Phase 35**

Explain that this is diagnostics feature-claim validation, not PR scanning or a release gate.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_system_diagnostics.py tests/test_red_lines_phase21.py -q`
Result: PASS, 13 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 34: Code Standards Diagnostics
- [x] Phase 35: Red Lines Diagnostics
