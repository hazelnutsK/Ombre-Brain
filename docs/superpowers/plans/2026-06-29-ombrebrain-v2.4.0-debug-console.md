# OmbreBrain v2.4.0 Debug Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build read-only v2.4.0 debug API, CLI, Dashboard view, and regression tests over Decision Ledger and Replay Debugger.

**Architecture:** Add `DecisionDebugService` in the `ombrebrain.decision` package, expose it through `LegacyRuntime`, register authenticated `web.v3_debug` routes, add a compact Dashboard tab, and verify malformed records plus old behavior invariants. The whole layer reads v2.4.0 MemoryFabric metadata and never re-executes legacy handlers.

**Tech Stack:** Python dataclasses, Starlette custom routes, existing MemoryFabric and DecisionRecord/Replayer, standalone Python CLI, static Dashboard HTML/JS, pytest.

---

### Task 1: E1 Service and CLI

**Files:**
- Create: `src/ombrebrain/decision/debug.py`
- Create: `tools/debug_decision.py`
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Test: `tests/test_v3_decision_debug_service.py`

- [ ] **Step 1: Write failing tests**

Tests should create a `LegacyRuntime`, record a tool or execution event, then assert `runtime.debug_decisions(limit=5)` returns the decision record and `runtime.replay_decision(identifier)` returns an ok replay result.

- [ ] **Step 2: Run tests to verify failure**

Run: `py -3.10 -m pytest tests\test_v3_decision_debug_service.py -q`
Expected: FAIL because `DecisionDebugService` does not exist.

- [ ] **Step 3: Implement service and runtime wrappers**

Create `DecisionDebugService` with `list_records`, `get_record`, `replay`, `health`, and add `debug_decisions`, `debug_decision`, `replay_decision` methods to `LegacyRuntime`.

- [ ] **Step 4: Implement CLI**

Add `tools/debug_decision.py` that opens `LegacyRuntime.from_config({"buckets_dir": args.buckets_dir})` and prints JSON for list/show/replay commands.

- [ ] **Step 5: Run tests**

Run: `py -3.10 -m pytest tests\test_v3_decision_debug_service.py -q`
Expected: PASS.

### Task 2: E1 Web API

**Files:**
- Create: `src/web/v3_debug.py`
- Modify: `src/web/__init__.py`
- Test: `tests/test_v3_debug_web_api.py`

- [ ] **Step 1: Write failing tests**

Tests should verify `web.register_all` includes `web.v3_debug` and that route handlers delegate to a fake runtime's read-only debug methods.

- [ ] **Step 2: Run tests to verify failure**

Run: `py -3.10 -m pytest tests\test_v3_debug_web_api.py -q`
Expected: FAIL because `web.v3_debug` is not registered.

- [ ] **Step 3: Implement authenticated GET routes**

Add `/api/v3/debug/decisions`, `/api/v3/debug/decision/{identifier}`, and `/api/v3/debug/replay/{identifier}`. Use `sh._require_auth(request)`.

- [ ] **Step 4: Run tests**

Run: `py -3.10 -m pytest tests\test_v3_debug_web_api.py -q`
Expected: PASS.

### Task 3: E2 Dashboard View

**Files:**
- Modify: `frontend/dashboard.html`
- Test: `tests/test_v3_dashboard_debug_view.py`

- [ ] **Step 1: Write failing tests**

Tests should assert the HTML contains a `data-tab="v3-debug"` tab, `id="v3-debug-view"`, fetch calls to `/api/v3/debug/decisions` and `/api/v3/debug/replay/`, plus `loadV3Debug`.

- [ ] **Step 2: Run tests to verify failure**

Run: `py -3.10 -m pytest tests\test_v3_dashboard_debug_view.py -q`
Expected: FAIL because the dashboard lacks the new view.

- [ ] **Step 3: Implement compact read-only view**

Add a tab, a content section, and JS functions `loadV3Debug`, `renderV3DebugDecision`, and `replayV3Decision`. Use stable container dimensions and avoid nested cards.

- [ ] **Step 4: Run tests**

Run: `py -3.10 -m pytest tests\test_v3_dashboard_debug_view.py -q`
Expected: PASS.

### Task 4: E3 Drift and Behavior Regression Tests

**Files:**
- Modify: `tests/test_v3_decision_debug_service.py`
- Modify: `tests/test_v3_decision_replay.py`
- Modify: `tests/test_v3_legacy_execution_pipeline.py`

- [ ] **Step 1: Write failing tests**

Add tests for malformed decision metadata, id drift, command id drift, and legacy handler result passthrough.

- [ ] **Step 2: Run tests to verify failure**

Run: `py -3.10 -m pytest tests\test_v3_decision_debug_service.py tests\test_v3_decision_replay.py tests\test_v3_legacy_execution_pipeline.py -q`
Expected: at least one FAIL until malformed data handling is complete.

- [ ] **Step 3: Implement fixes**

Harden debug service and replay explanation around malformed data. Do not alter legacy execution behavior.

- [ ] **Step 4: Run tests**

Run: `py -3.10 -m pytest tests\test_v3_decision_debug_service.py tests\test_v3_decision_replay.py tests\test_v3_legacy_execution_pipeline.py -q`
Expected: PASS.

### Task 5: Verification and Artifacts

**Files:**
- Update complete artifacts summary and verification files
- Regenerate complete diff and zip

- [ ] **Step 1: Run E focused tests**

Run: `py -3.10 -m pytest tests\test_v3_decision_debug_service.py tests\test_v3_debug_web_api.py tests\test_v3_dashboard_debug_view.py tests\test_v3_decision_replay.py tests\test_v3_legacy_execution_pipeline.py -q`

- [ ] **Step 2: Run all v2.4.0 tests**

Run: `$files = @(Get-ChildItem -Path tests -Filter 'test_v3_*.py' | ForEach-Object { $_.FullName }); py -3.10 -m pytest @files -q`

- [ ] **Step 3: Run full suite**

Run: `py -3.10 -m pytest -q`

- [ ] **Step 4: Refresh artifacts and zip**

Regenerate changed files, `v2.4.0-complete.diff`, Chinese summary, verification record, and `OmbreBrain-v2.4.0-complete-artifacts.zip`.

- [ ] **Step 5: Stop without commit**

The user explicitly requested no commit, push, release, or cloud changes.
