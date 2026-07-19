# ADR Requirements Phase 20 Implementation Plan

**Goal:** Implement vNext §30 ADR Requirements as an architecture contract: philosophy-touching changes must have an ADR, and ADR documents must answer the required boundary questions.

**Architecture:** Add `ombrebrain.architecture.adr` with change specs, ADR document specs, issue/report dataclasses, and an `ADRRequirementsContract`. This is diagnostic-only and does not scan the repo automatically in this phase.

**Tech Stack:** Python dataclasses, simple Markdown heading parsing, architecture package exports, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_adr_requirements_phase20.py`

- [x] **Step 1: Write failing ADR requirements tests**

Cover:
- complete ADR template passes.
- missing required section is rejected.
- invalid ADR title is rejected.
- philosophy-touching topics require ADR.
- non-philosophy topics may omit ADR.
- multi-document report is JSON-safe.
- architecture package exports ADR contract symbols.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adr_requirements_phase20.py -q`
Result: FAIL, 7 failed because ADR requirements symbols did not exist yet.

### Task 2: Implement ADR Contract

**Files:**
- Add: `src/ombrebrain/architecture/adr.py`
- Modify: `src/ombrebrain/architecture/__init__.py`

- [x] **Step 1: Add ADR dataclasses**

Create `ADRChangeSpec`, `ADRDocument`, `ADRRequirementIssue`, `ADRRequirementReport`, and `ADRRequirementsContract`.

- [x] **Step 2: Add topic and template checks**

Encode §30 required topics and template sections.

- [x] **Step 3: Add manifest evaluation**

Evaluate multiple ADR documents and return JSON-safe aggregate results.

- [x] **Step 4: Export architecture symbols**

Export the new contract from `ombrebrain.architecture`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_adr_requirements_phase20.py -q`
Result: PASS, 7 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-adr-requirements-phase20.md`

- [x] **Step 1: Document Phase 20**

Explain that ADR validation is diagnostic and not yet wired into a repo scanner or release gate.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_adr_requirements_phase20.py tests/test_code_standards_phase17.py tests/test_v3_architecture_audit.py -q`
Result: PASS, 27 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 688 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 19: Surface Context Compiler
- [x] Phase 20: ADR Requirements Contract
