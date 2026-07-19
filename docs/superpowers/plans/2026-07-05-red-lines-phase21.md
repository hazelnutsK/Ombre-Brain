# Red Lines Contract Phase 21 Implementation Plan

**Goal:** Implement vNext §31 Red Lines as a policy contract: forbidden product/architecture capabilities are represented by stable codes and produce blocking violations when claimed by a feature.

**Architecture:** Add `ombrebrain.policy.red_lines` with feature specs, violation/report dataclasses, and a `RedLineContract`. This is diagnostic-only and does not scan PRs or block merges automatically in this phase.

**Tech Stack:** Python dataclasses, policy package lazy exports, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_red_lines_phase21.py`

- [x] **Step 1: Write failing red-line tests**

Cover:
- default contract lists all 17 vNext red lines.
- phrase-shaped claims are rejected.
- code-shaped claims are rejected.
- safe diagnostic features pass.
- manifest report is JSON-safe.
- policy package exports red-line symbols.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_red_lines_phase21.py -q`
Result: FAIL, 11 failed because red-line symbols did not exist yet.

### Task 2: Implement Red Line Contract

**Files:**
- Add: `src/ombrebrain/policy/red_lines.py`
- Modify: `src/ombrebrain/policy/__init__.py`

- [x] **Step 1: Add feature/violation/report dataclasses**

Create `RedLineFeatureSpec`, `RedLineViolation`, `RedLineReport`, and `RedLineContract`.

- [x] **Step 2: Encode 17 red lines**

Add stable codes plus phrase aliases for all §31 red lines.

- [x] **Step 3: Add manifest evaluation**

Evaluate multiple feature specs and return JSON-safe aggregate results.

- [x] **Step 4: Export policy symbols**

Export the new contract through `ombrebrain.policy`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_red_lines_phase21.py -q`
Result: PASS, 11 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-red-lines-phase21.md`

- [x] **Step 1: Document Phase 21**

Explain that red-line validation is diagnostic and not yet wired into PR/release automation.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_red_lines_phase21.py tests/test_formal_invariants_phase10.py tests/test_adr_requirements_phase20.py -q`
Result: PASS, 26 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 699 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 20: ADR Requirements Contract
- [x] Phase 21: Red Lines Contract
