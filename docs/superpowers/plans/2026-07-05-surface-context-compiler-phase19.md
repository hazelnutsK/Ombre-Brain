# Surface Context Compiler Phase 19 Implementation Plan

**Goal:** Implement vNext §29 Example Surfacing Compiler as a retrieval contract: allowed surface decisions enter context within budget, and every serialized memory remains non-instructional.

**Architecture:** Extend `ombrebrain.retrieval.context` with `SurfaceContextCompiler`. It consumes already-produced surface decisions plus memory payloads, filters denied decisions, applies a surface budget, and reuses `MemoryContextCompiler` for humble serialization. This is contract-only and does not change live search/breath routing.

**Tech Stack:** Python dataclasses, existing `SurfaceDecision`, retrieval package exports, formal invariant checker regression tests.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_surface_context_compiler_phase19.py`

- [x] **Step 1: Write failing surface-context compiler tests**

Cover:
- allowed surface decisions are selected, denied decisions are filtered, and budget truncates output.
- surface reasons become `why_surfaced`.
- compiled items keep `instructional_force="none"` and pass formal invariants.
- missing memories are skipped.
- mapping-shaped decisions are accepted.
- retrieval package exports `SurfaceContextCompiler`.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_surface_context_compiler_phase19.py -q`
Result: FAIL, 6 failed because `SurfaceContextCompiler` did not exist yet.

### Task 2: Implement Compiler

**Files:**
- Modify: `src/ombrebrain/retrieval/context.py`
- Modify: `src/ombrebrain/retrieval/__init__.py`

- [x] **Step 1: Add `SurfaceContextCompiler`**

Filter decisions by `allowed`, map decision IDs to memory payloads, apply `max_items`, and preserve surface reasons.

- [x] **Step 2: Reuse humble context serialization**

Call `MemoryContextCompiler` so all output items preserve the no-instruction boundary.

- [x] **Step 3: Export retrieval symbol**

Export `SurfaceContextCompiler` from `ombrebrain.retrieval`.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_surface_context_compiler_phase19.py -q`
Result: PASS, 6 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-surface-context-compiler-phase19.md`

- [x] **Step 1: Document Phase 19**

Explain that surface context compilation is a contract/compiler and not yet wired into live retrieval output.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_surface_context_compiler_phase19.py tests/test_context_serialization_phase8b.py tests/test_formal_invariants_phase8a.py -q`
Result: PASS, 18 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 681 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 18: Advanced Command Boundary Contract
- [x] Phase 19: Surface Context Compiler
