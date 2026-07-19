# Policy-Gated Retrieval Scoring Phase 9 Implementation Plan

**Goal:** Implement vNext §17 advanced retrieval scoring as a shadow contract: richer candidate scoring is allowed, but every score must remain subordinate to surface policy and philosophy gates.

**Architecture:** Add `ombrebrain.retrieval.scoring` with explicit feature weights, candidate score, gate values, and final surface score. The module does not change live `breath()` or Dashboard search ordering yet.

**Tech Stack:** Python dataclasses, existing `SurfacePolicyVM`, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_retrieval_scoring_phase9.py`

- [x] **Step 1: Write failing scoring tests**

Cover:
- candidate score is the weighted sum of semantic, lexical, temporal, affective, unresolved, promise, and graph-neighbor signals.
- surface score multiplies candidate score by accessibility/dignity/scarcity/intent/non-cognition gates.
- a high candidate score cannot bypass a zero policy gate.
- `dont_surface` buckets are denied in spontaneous mode but allowed in explicit search mode.
- ranking sorts by final surface score rather than raw candidate score.
- retrieval package exports the scorer symbols.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_retrieval_scoring_phase9.py -q`
Expected: FAIL because `ombrebrain.retrieval.scoring` does not exist yet.

### Task 2: Implement Shadow Scorer

**Files:**
- Add: `src/ombrebrain/retrieval/scoring.py`
- Modify: `src/ombrebrain/retrieval/__init__.py`

- [x] **Step 1: Add feature/gate/score dataclasses**

Create `RetrievalFeatures`, `RetrievalGates`, `RetrievalWeights`, `RetrievalScore`, and `RetrievalCandidate`.

- [x] **Step 2: Apply policy-gated formula**

Compute:

```text
candidate_score =
    semantic_similarity      * w_semantic
  + lexical_similarity       * w_lexical
  + temporal_proximity       * w_time
  + affective_proximity      * w_affect
  + unresolved_relevance     * w_unresolved
  + promise_relevance        * w_promise
  + graph_neighbor_relevance * w_graph

surface_score =
    candidate_score
  * accessibility
  * dignity_gate
  * scarcity_gate
  * intent_gate
  * non_cognition_gate
```

`SurfacePolicyVM` denial forces accessibility to zero.

- [x] **Step 3: Add deterministic ranking**

Sort by final `surface_score`, then raw `candidate_score`, then bucket id for deterministic output.

- [x] **Step 4: Export retrieval symbols**

Export scorer symbols from `ombrebrain.retrieval`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_retrieval_scoring_phase9.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-retrieval-scoring-phase9.md`

- [x] **Step 1: Document Phase 9**

Explain that this is a shadow scoring contract and does not yet alter live retrieval ordering.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_retrieval_scoring_phase9.py tests/test_surface_policy_phase3.py tests/test_formal_invariants_phase8a.py -q`
Expected: selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 8D: Tool Output Humility Contract
- [x] Phase 9: Policy-Gated Retrieval Scoring
