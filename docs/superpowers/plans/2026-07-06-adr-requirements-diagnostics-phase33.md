# ADR Requirements Diagnostics Phase 33 Implementation Plan

**Goal:** Connect the Phase 20 ADR requirements contract to Dashboard system diagnostics so ADR documents can be checked locally for vNext boundary sections.

**Architecture:** Read `docs/adr/ADR-*.md` files as local documents and evaluate them with `ADRRequirementsContract`. Missing ADR directory or no ADR documents should warn rather than fail runtime diagnostics. Existing ADR documents with missing required sections should fail the check.

**Tech Stack:** `web.system.build_system_diagnostics`, `ADRRequirementsContract`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Require ADR diagnostics check**

Add a valid sample ADR under the test repo root and assert diagnostics includes `adr_requirements`.

- [x] **Step 2: Require ADR contract report**

Assert `adr_requirements.details.report.ok` is true and the sampled ADR path is listed.

### Task 2: Implement ADR Diagnostics

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Add ADR reader**

Add `_read_adr_documents_from_repo()` to scan `docs/adr/ADR-*.md` without modifying files.

- [x] **Step 2: Evaluate through contract**

Append `adr_requirements` diagnostics check using `ADRRequirementsContract.default().evaluate_documents(...)`.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-adr-requirements-diagnostics-phase33.md`

- [x] **Step 1: Document Phase 33**

Explain that ADR diagnostics are local, read-only, and warning-only when no ADRs exist.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_system_diagnostics.py tests/test_adr_requirements_phase20.py -q`
Result: PASS, 9 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 32: Public Tool Manifest Diagnostics
- [x] Phase 33: ADR Requirements Diagnostics
