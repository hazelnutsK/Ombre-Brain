# Context Serialization Contract Phase 8B Implementation Plan

**Goal:** Implement the vNext §26 memory context serialization contract: surfaced memories must enter context as humble, descriptive residues, not as instructions.

**Architecture:** Add `ombrebrain.retrieval.context.MemoryContextCompiler`. It accepts already-selected memory buckets/traces and produces JSON-safe context items plus a rendered text block. The compiler is shadow/contract first: it does not change `breath()` output, search ranking, bucket storage, or policy decisions in Phase 8B.

**Tech Stack:** Python dataclasses, retrieval package exports, formal invariant checker regression tests.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_context_serialization_phase8b.py`

- [x] **Step 1: Write failing context compiler tests**

Cover:
- serialized context includes explicit “not an instruction” boundary;
- memory item exposes `instructional_force="none"` and `may_control_reasoning=False`;
- imperative wording in memory body is neutralized/redacted in serialized context;
- compiler respects a small `max_items` surface budget;
- compiled context passes `FormalInvariantChecker.evaluate_context_items()`.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_context_serialization_phase8b.py -q`
Expected: FAIL because `ombrebrain.retrieval.context` does not exist yet.

### Task 2: Implement Contract

**Files:**
- Add: `src/ombrebrain/retrieval/context.py`
- Modify: `src/ombrebrain/retrieval/__init__.py`

- [x] **Step 1: Add context dataclasses**

Create `MemoryContextItem` and `MemoryContextBundle` with JSON-safe `to_dict()` and rendered text output.

- [x] **Step 2: Add compiler**

Create `MemoryContextCompiler` that converts buckets/traces into descriptive context items with trace id, state, past affect, why surfaced, boundary, and neutralized excerpt.

- [x] **Step 3: Export package symbols**

Export the compiler and contracts from `ombrebrain.retrieval`.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_context_serialization_phase8b.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-context-serialization-phase8b.md`

- [x] **Step 1: Document Phase 8B**

Add a note that context serialization is a contract/compiler, not yet wired into live `breath()`.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_context_serialization_phase8b.py tests/test_formal_invariants_phase8a.py tests/test_v3_retrieval_pipeline.py -q`
Expected: selected tests pass. If `tests/test_v3_retrieval_pipeline.py` is absent, replace with existing retrieval tests.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 8A: Formal Invariants Shadow Checker
- [x] Phase 8B: Context Serialization Contract
