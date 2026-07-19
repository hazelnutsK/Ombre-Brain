# Surface Context Diagnostics Phase 39 Implementation Plan

**Goal:** Connect the Phase 19 surface context compiler to Dashboard system diagnostics so local diagnostics can expose non-instructional context compilation after surfacing policy allows a memory.

**Architecture:** Evaluate a representative allowed `SurfaceDecision` and memory payload through `SurfaceContextCompiler`. Do not run live retrieval, read user buckets, mutate search output, or turn the compiler into a runtime gate.

**Tech Stack:** `web.system.build_system_diagnostics`, `SurfaceContextCompiler`, `SurfaceDecision`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Require surface context diagnostics check**

Assert diagnostics includes `surface_context` with OK status.

- [x] **Step 2: Require non-instructional compiled context**

Assert the check emits one `surface-context.v1` item with `instructional_force="none"` and `may_control_reasoning=False`.

### Task 2: Implement Surface Context Diagnostics

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Add diagnostics compiler helper**

Add `_build_surface_context_diagnostics()` using a safe allowed decision and diagnostic memory payload.

- [x] **Step 2: Append diagnostics check**

Append `surface_context` check to `build_system_diagnostics()`.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-surface-context-diagnostics-phase39.md`

- [x] **Step 1: Document Phase 39**

Explain that this is read-only contract validation, not live retrieval integration.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_system_diagnostics.py tests/test_surface_context_compiler_phase19.py -q`
Result: PASS, 8 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 38: Migration Preservation Diagnostics
- [x] Phase 39: Surface Context Diagnostics
