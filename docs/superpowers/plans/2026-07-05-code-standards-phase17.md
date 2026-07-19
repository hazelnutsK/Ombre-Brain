# Code Standards Contract Phase 17 Implementation Plan

**Goal:** Implement vNext §27 Highest-Difficulty Code Standards as a diagnostic architecture contract. The contract should catch boundary-breaking code shapes without requiring local ruff/mypy/pyright installation in this phase.

**Architecture:** Add `ombrebrain.architecture.code_standards` with artifact specs, issue/report dataclasses, and a standards auditor. This is contract-only: it does not reformat files, run external linters, or block live runtime.

**Tech Stack:** Python dataclasses/enums, existing architecture package exports, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_code_standards_phase17.py`

- [x] **Step 1: Write failing code-standards tests**

Cover:
- Python adapters are accepted when typed and command-boundary aware.
- Python direct canonical memory mutation is rejected.
- Rust kernel specs must be append-only, policy checked, and free of normal hard-delete APIs.
- async tasks, projections, and dashboard actions must satisfy role-specific standards.
- philosophy-touching changes require ADR evidence.
- reports are JSON-safe and architecture package exports the contract.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_code_standards_phase17.py -q`
Result: FAIL, 15 failed because code standards symbols did not exist yet.

### Task 2: Implement Code Standards Contract

**Files:**
- Add: `src/ombrebrain/architecture/code_standards.py`
- Modify: `src/ombrebrain/architecture/__init__.py`

- [x] **Step 1: Add artifact spec and report dataclasses**

Create `ArtifactLanguage`, `ArtifactRole`, `CodeArtifactSpec`, `CodeStandardIssue`, `CodeStandardReport`, and `HighestDifficultyCodeStandards`.

- [x] **Step 2: Add §27 checks**

Encode Python adapter, Rust kernel, async idempotency, projection lag, dashboard capability, hard-delete, and ADR requirements.

- [x] **Step 3: Add manifest evaluation**

Evaluate multiple artifacts and return JSON-safe aggregate results.

- [x] **Step 4: Export architecture symbols**

Export the new contract from `ombrebrain.architecture`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_code_standards_phase17.py -q`
Result: PASS, 15 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-code-standards-phase17.md`

- [x] **Step 1: Document Phase 17**

Explain that code standards validation is diagnostic and does not run external lint tools yet.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_code_standards_phase17.py tests/test_v3_architecture_audit.py tests/test_public_tool_design_phase16.py -q`
Result: PASS, 56 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 666 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 16: Public MCP Tool Design Contract
- [x] Phase 17: Code Standards Contract
