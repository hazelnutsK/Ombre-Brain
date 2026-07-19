# Advanced Command Boundary Phase 18 Implementation Plan

**Goal:** Implement vNext §28 Advanced Command Boundary as a diagnostic domain contract: memory mutations must be representable as `command -> policy -> event -> ledger -> receipt`, and adapters must not directly mutate memory.

**Architecture:** Add `ombrebrain.domain.boundary` with boundary stage enums, command receipts, issue/report dataclasses, and a contract evaluator. This is shadow/contract first and does not replace existing legacy execution handlers.

**Tech Stack:** Python dataclasses/enums, existing domain package exports, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_command_boundary_phase18.py`

- [x] **Step 1: Write failing command-boundary tests**

Cover:
- valid mutation receipt follows command -> policy -> event derivation -> event policy validation -> ledger append -> receipt.
- missing policy preflight is rejected.
- wrong stage ordering is rejected.
- ledger append after policy denial is rejected.
- mutating commands require events and ledger append.
- read-only commands may omit events/ledger append.
- adapter direct write markers are rejected.
- manifest report is JSON-safe and domain package exports symbols.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_command_boundary_phase18.py -q`
Result: FAIL, 9 failed because command boundary symbols did not exist yet.

### Task 2: Implement Boundary Contract

**Files:**
- Add: `src/ombrebrain/domain/boundary.py`
- Modify: `src/ombrebrain/domain/__init__.py`

- [x] **Step 1: Add boundary dataclasses**

Create `BoundaryStage`, `CommandBoundaryReceipt`, `CommandBoundaryIssue`, `CommandBoundaryReport`, and `AdvancedCommandBoundaryContract`.

- [x] **Step 2: Add sequence and policy checks**

Validate required stage presence, stage order, preflight denial, event validation, mutation events, ledger append, and adapter-direct-write markers.

- [x] **Step 3: Add manifest evaluation**

Evaluate multiple receipts and return JSON-safe aggregate results.

- [x] **Step 4: Export domain symbols**

Export the new contract from `ombrebrain.domain`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_command_boundary_phase18.py -q`
Result: PASS, 9 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-command-boundary-phase18.md`

- [x] **Step 1: Document Phase 18**

Explain that command boundary validation is diagnostic and not yet wired into live handler execution.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_command_boundary_phase18.py tests/test_v3_legacy_execution_pipeline.py tests/test_v3_policy_engine.py -q`
Result: PASS, 21 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 675 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 17: Code Standards Contract
- [x] Phase 18: Advanced Command Boundary Contract
