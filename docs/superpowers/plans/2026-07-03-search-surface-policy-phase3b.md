# Search Surface Policy Phase 3B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route user-facing `/api/search` results through `SurfacePolicyVM(mode="search")` so terminal memory states cannot surface through Dashboard search while `dont_surface=True` remains explicitly searchable.

**Architecture:** Keep `BucketManager.search()` untouched because internal callers use it for merge/import/de-dup behavior. Add a small policy filter in `web.search.api_search` after ranking and before JSON serialization. This preserves scoring and result shape while making the read boundary consistent with the Phase 3 surfacing VM.

**Tech Stack:** Python, Starlette route handlers, existing `SurfacePolicyVM`, pytest.

---

### Task 1: User-facing Search Policy Test

**Files:**
- Modify: `tests/test_surface_policy_phase3.py`
- Modify: `src/web/search.py`

- [x] **Step 1: Write the failing test**

Add a Dashboard `/api/search` route test where bucket manager returns visible, `dont_surface`, deleted, tombstone, and archived buckets. Assert the response contains visible and `dont_surface`, but excludes terminal states.

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_surface_policy_phase3.py::test_dashboard_search_filters_terminal_states_but_keeps_dont_surface -q`
Expected: FAIL because `/api/search` currently serializes all matches returned by `bucket_mgr.search()`.

- [x] **Step 3: Implement minimal filter**

In `web.search.api_search`, skip buckets whose `_SURFACE_POLICY.evaluate_bucket(bucket, mode="search").allowed` is false.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_surface_policy_phase3.py::test_dashboard_search_filters_terminal_states_but_keeps_dont_surface -q`
Expected: PASS.

### Task 2: Regression Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-03-search-surface-policy-phase3b.md`

- [x] **Step 1: Document Phase 3B**

Add a short `INTERNALS.md` note that `/api/search` now uses search-mode surface policy, while internal `BucketManager.search()` remains unfiltered.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_surface_policy_phase3.py tests/test_permanent_breath_regression.py -q`
Expected: all selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 1: Ledger Mirror
- [x] Phase 2A: In-memory Trace Catalog Projection
- [x] Phase 2B: SQLite/FTS Shadow Projection
- [x] Phase 3A: Surface Policy VM
- [x] Phase 3B: Dashboard Search Surface Policy
- [x] Phase 4: Tombstone-only Erasure Shadow
- [x] Phase 5A: Replay Validator
- [x] Phase 5B: Deterministic Replay Property Runner
- [x] Phase 6A: Rust Replay Kernel Scaffold
- [x] Phase 7A: Policy Effective/Audit Verdicts
- [x] Phase 7B: Executable Policy Enforcement Boundary
- [x] Phase 7C: Plugin Capability Enforcement
