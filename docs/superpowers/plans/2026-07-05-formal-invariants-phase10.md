# Formal Invariants Coverage Phase 10 Implementation Plan

**Goal:** Extend the vNext §18/§19 formal invariant checker beyond the initial Phase 8A subset, while keeping it read-only and diagnostic.

**Architecture:** Add small executable checks to `ombrebrain.policy.formal_invariants.FormalInvariantChecker`. These checks inspect caller-provided ledgers, projection snapshots, compression receipts, context items, and tool receipts. They do not write canonical state and do not enforce live runtime behavior yet.

**Tech Stack:** Python dataclasses, existing `InvariantReport`, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_formal_invariants_phase10.py`

- [x] **Step 1: Write failing invariant tests**

Cover:
- Invariant 2: projection rebuild cannot create or lose canonical truth.
- Invariant 5: past affect cannot be emitted as current feeling.
- Invariant 7: lossy compression must declare loss and preserve lineage.
- Invariant 8: admin erasure must be logged as external storage action, not internal forgetting.
- Invariant 10: reconstruction must append and cannot overwrite original trace body.
- Invariant 11: dream must not create autonomous goals/current emotions/behavior commands.
- Invariant 12: pulse must not report or set current emotional state.
- report metadata lists all 13 formal invariants.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_formal_invariants_phase10.py -q`
Expected: FAIL because the new checker methods/invariants do not exist yet.

### Task 2: Extend FormalInvariantChecker

**Files:**
- Modify: `src/ombrebrain/policy/formal_invariants.py`

- [x] **Step 1: Expand supported invariant metadata**

List all 13 invariants from vNext §18 in `_SUPPORTED_INVARIANTS`.

- [x] **Step 2: Add projection rebuild checks**

Add `evaluate_projection_rebuild()` for missing/extra trace ids after rebuild.

- [x] **Step 3: Add compression checks**

Add `evaluate_compression_records()` for lossy dehydration receipts.

- [x] **Step 4: Extend ledger checks**

Detect admin erasure logged as internal forgetting and reconstruction overwriting the original trace.

- [x] **Step 5: Add tool receipt checks**

Add `evaluate_tool_receipt()` for `dream` and `pulse` boundary violations.

- [x] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_formal_invariants_phase10.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-formal-invariants-phase10.md`

- [x] **Step 1: Document Phase 10**

Explain the expanded invariant coverage and that it remains shadow diagnostics.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_formal_invariants_phase10.py tests/test_formal_invariants_phase8a.py tests/test_retrieval_scoring_phase9.py tests/test_tool_output_contract_phase8d.py -q`
Expected: selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 8A: Formal Invariants Shadow Checker
- [x] Phase 9: Policy-Gated Retrieval Scoring
- [x] Phase 10: Formal Invariants Coverage Extension
