# Breath Search Surface Policy Phase 3C Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route MCP `breath(query=...)` search results through `SurfacePolicyVM(mode="search")` so terminal memory states cannot surface through the tool layer while `dont_surface=True` remains explicitly searchable.

**Architecture:** Keep `BucketManager.search()` untouched for internal maintenance callers. Add a local `_can_surface_search()` helper in `tools/breath/search.py`, apply it to ranked keyword results and semantic vector expansion before dehydration/touch. Random drift remains passive and uses stricter spontaneous policy in a later pass; this phase focuses on explicit query hits.

**Tech Stack:** Python async tool path, existing `SurfacePolicyVM`, pytest.

---

### Task 1: MCP Search Policy Test

**Files:**
- Modify: `tests/test_permanent_breath_regression.py`
- Modify: `src/tools/breath/search.py`

- [x] **Step 1: Write the failing test**

Add a `surface_search()` test with fake runtime dependencies. The fake bucket manager returns visible, `dont_surface`, deleted, tombstone, and archived buckets. Assert the rendered result includes visible and `dont_surface`, but excludes terminal states.

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_permanent_breath_regression.py::test_search_breath_filters_terminal_states_but_keeps_dont_surface -q`
Expected: FAIL because `surface_search()` currently only excludes feel/plan/letter and archived vector fallback, not deleted/tombstone search matches.

- [x] **Step 3: Implement minimal filter**

Import `SurfacePolicyVM`, create `_can_surface_search(bucket)`, and use it on both `bucket_mgr.search()` matches and vector fallback candidates.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_permanent_breath_regression.py::test_search_breath_filters_terminal_states_but_keeps_dont_surface -q`
Expected: PASS.

### Task 2: Documentation and Regression Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-03-breath-search-surface-policy-phase3c.md`

- [x] **Step 1: Document Phase 3C**

Add an `INTERNALS.md` note that MCP `breath(query=...)` now applies search-mode surface policy to explicit query hits while preserving `dont_surface` reachability.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_permanent_breath_regression.py tests/test_surface_policy_phase3.py -q`
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
- [x] Phase 3C: MCP Breath Search Surface Policy
- [x] Phase 4: Tombstone-only Erasure Shadow
- [x] Phase 5A: Replay Validator
- [x] Phase 5B: Deterministic Replay Property Runner
- [x] Phase 6A: Rust Replay Kernel Scaffold
- [x] Phase 7A: Policy Effective/Audit Verdicts
- [x] Phase 7B: Executable Policy Enforcement Boundary
- [x] Phase 7C: Plugin Capability Enforcement
