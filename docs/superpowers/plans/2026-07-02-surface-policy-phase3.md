# Surface Policy Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal policy VM in front of active surfacing so hidden, archived, deleted, and tombstone memories cannot reappear through ranking shortcuts.

**Architecture:** Keep Markdown buckets canonical. Add a small deterministic surfacing policy under `src/ombrebrain/policy/` and wire it into active `breath()` surfacing first; explicit keyword search remains intentionally reachable for `dont_surface=True` memories.

**Tech Stack:** Python dataclasses/enums, pytest, existing `tools.breath` runtime.

---

### Task 1: Capture Surfacing Boundary Regression

**Files:**
- Modify: `tests/test_permanent_breath_regression.py`

- [x] **Step 1: Write the failing test**

Add an async regression test proving that a pinned/permanent bucket with `dont_surface=True` must not appear in no-query `breath()`.

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_permanent_breath_regression.py::test_default_breath_respects_dont_surface_even_for_core_bucket -q`

Expected: FAIL because current pinned/permanent surfacing does not consult a unified policy.

### Task 2: Add Minimal Surface Policy VM

**Files:**
- Create: `src/ombrebrain/policy/surfacing.py`
- Modify: `src/ombrebrain/policy/__init__.py`
- Test: `tests/test_surface_policy_phase3.py`

- [x] **Step 1: Write pure policy tests**

Cover spontaneous denial for `dont_surface`, `anchor`, `feel/plan/letter/self/i`, `archived`, `deleted_at`, and `tombstone`; cover explicit search preserving `dont_surface` reachability.

- [x] **Step 2: Run pure policy tests to verify they fail**

Run: `pytest tests/test_surface_policy_phase3.py -q`

Expected: FAIL because `ombrebrain.policy.surfacing` does not exist yet.

- [x] **Step 3: Implement minimal policy VM**

Create `SurfacePolicyVM.evaluate_bucket()` and `filter_buckets()` with mode-specific rules.

- [x] **Step 4: Run pure policy tests to verify they pass**

Run: `pytest tests/test_surface_policy_phase3.py -q`

Expected: PASS.

### Task 3: Wire Policy Into Active Surfacing

**Files:**
- Modify: `src/tools/breath/surface.py`
- Modify: `src/web/search.py`

- [x] **Step 1: Apply policy before no-query breath ranking**

Use `SurfacePolicyVM.default().filter_buckets(..., mode="spontaneous")` for pinned, unresolved, passive, and occasional resolved pools.

- [x] **Step 2: Apply policy to dashboard breath endpoint**

Filter `/api/breath` results with the same spontaneous policy.

- [x] **Step 3: Run regression test to verify it passes**

Run: `pytest tests/test_permanent_breath_regression.py::test_default_breath_respects_dont_surface_even_for_core_bucket -q`

Expected: PASS.

### Task 4: Document And Verify

**Files:**
- Modify: `docs/INTERNALS.md`

- [x] **Step 1: Document Phase 3 policy boundary**

Add a short vNext section explaining shadow policy VM scope and explicit search exception.

- [x] **Step 2: Run targeted tests**

Run: `pytest tests/test_surface_policy_phase3.py tests/test_permanent_breath_regression.py tests/test_system_diagnostics.py -q`

Expected: PASS.

- [x] **Step 3: Run full regression**

Run: `pytest -q`

Expected: PASS.

- [x] **Step 4: Run whitespace diff check**

Run: `git diff --check`

Expected: no output and exit 0.

- [x] **Step 5: Stop locally**

Do not commit or push unless the user asks.
