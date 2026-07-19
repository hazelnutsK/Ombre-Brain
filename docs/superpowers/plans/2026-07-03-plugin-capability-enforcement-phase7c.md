# Plugin Capability Enforcement Phase 7C Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add execution-time capability-scope policy to `PluginRuntime` so plugins cannot bypass declared permissions when enforcement is explicitly enabled.

**Architecture:** Keep plugin registration sandbox behavior unchanged. At execution time, map declared plugin capabilities into the existing `CapabilityMicrokernel` when the capability is known to the foundation registry. Default `audit` mode records missing permissions but still runs legacy-compatible handlers; explicit `enforce` mode raises `PolicyViolation` before calling the handler.

**Tech Stack:** Python dataclasses, existing `CapabilityMicrokernel`, pytest.

---

### Task 1: Execution Decision Contract

**Files:**
- Modify: `src/ombrebrain/plugins/contracts.py`
- Modify: `src/ombrebrain/plugins/__init__.py`
- Test: `tests/test_v3_plugin_runtime.py`

- [x] **Step 1: Write the failing tests**

Add tests that expect `PluginRuntime.last_execution_decision()` to expose `allowed`, `effective_allowed`, `audit_only`, `missing_permissions`, and `protected_surfaces`.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_v3_plugin_runtime.py::test_plugin_runtime_audit_mode_records_missing_capability_permissions_without_blocking -q`
Expected: FAIL because no execution decision object exists yet.

- [x] **Step 3: Implement minimal contract**

Create `PluginExecutionDecision` with a JSON-safe `to_dict()` method and export it from the plugin package.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_v3_plugin_runtime.py::test_plugin_runtime_audit_mode_records_missing_capability_permissions_without_blocking -q`
Expected: PASS after runtime wiring in Task 2.

### Task 2: Plugin Runtime Enforcement

**Files:**
- Modify: `src/ombrebrain/plugins/runtime.py`
- Test: `tests/test_v3_plugin_runtime.py`

- [x] **Step 1: Write the failing tests**

Add tests for:
- audit mode records missing `tools.breath` permissions and still calls the handler;
- enforce mode blocks missing permissions and does not call the handler;
- enforce mode allows execution when scope has required permissions.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_v3_plugin_runtime.py::test_plugin_runtime_audit_mode_records_missing_capability_permissions_without_blocking tests/test_v3_plugin_runtime.py::test_plugin_runtime_enforce_mode_blocks_missing_capability_permission tests/test_v3_plugin_runtime.py::test_plugin_runtime_enforce_mode_allows_when_scope_has_required_permissions -q`
Expected: FAIL because `PluginRuntime.execute()` has no permission scope or enforcement mode.

- [x] **Step 3: Implement minimal runtime policy**

Add `enforcement_mode`, a foundation `CapabilityMicrokernel`, optional `permissions`/`actor_name`/`source` execution scope, and pre-handler policy check. Unknown plugin-local capabilities remain declaration-scoped for compatibility.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_v3_plugin_runtime.py -q`
Expected: all plugin runtime tests pass.

### Task 3: Documentation and Regression Verification

**Files:**
- Modify: `docs/INTERNALS.md`

- [x] **Step 1: Document Phase 7C**

Add a short section after Phase 7B explaining plugin audit/enforce behavior and permission scope parameters.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_v3_plugin_runtime.py tests/test_v3_capability_microkernel.py tests/test_v3_legacy_execution_pipeline.py -q`
Expected: targeted tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 1: Ledger Mirror
- [x] Phase 2: Rebuildable Projection
- [x] Phase 3: Surface Policy VM
- [x] Phase 4: Tombstone-only Erasure Shadow
- [x] Phase 5A: Replay Validator
- [x] Phase 5B: Deterministic Replay Property Runner
- [x] Phase 6A: Rust Replay Kernel Scaffold
- [x] Phase 7A: Policy Effective/Audit Verdicts
- [x] Phase 7B: Executable Policy Enforcement Boundary
- [x] Phase 7C: Plugin Capability Enforcement
