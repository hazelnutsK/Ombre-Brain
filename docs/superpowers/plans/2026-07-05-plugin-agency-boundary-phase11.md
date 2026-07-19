# Plugin Agency Boundary Phase 11 Implementation Plan

**Goal:** Implement vNext §20 plugin-system boundaries: plugins may extend infrastructure, but must not extend agency or cognitive control.

**Architecture:** Extend `PluginManifest` with a plugin type and vNext-style capability flags. Add a registration-time `PluginAgencyBoundary` used by `PluginSandbox.evaluate()` before the existing protected-surface sandbox check.

**Tech Stack:** Python dataclasses, existing `PluginRuntime` / `PluginSandbox`, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_plugin_agency_boundary_phase11.py`

- [x] **Step 1: Write failing plugin agency-boundary tests**

Cover:
- manifest parses `type` / `plugin_type`.
- manifest parses boolean capability tables and keeps only enabled capabilities.
- allowed infrastructure plugin types pass the agency boundary.
- forbidden plugin types are rejected.
- forbidden cognitive capabilities are rejected.
- `PluginRuntime.register()` refuses rejected manifests before handlers are installed.
- package exports the agency boundary symbols.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_plugin_agency_boundary_phase11.py -q`
Expected: FAIL because agency boundary symbols do not exist yet.

### Task 2: Implement Agency Boundary

**Files:**
- Modify: `src/ombrebrain/plugins/contracts.py`
- Modify: `src/ombrebrain/plugins/runtime.py`
- Modify: `src/ombrebrain/plugins/__init__.py`

- [x] **Step 1: Extend manifest contract**

Add `plugin_type` to `PluginManifest`, defaulting legacy manifests to `projection`, and support dict-style capability flags.

- [x] **Step 2: Add agency decision contract**

Create `PluginAgencyDecision` with `allowed`, `reason`, `plugin_type`, `forbidden_capabilities`, and `forbidden_plugin_type`.

- [x] **Step 3: Add boundary evaluator**

Create `PluginAgencyBoundary` with allowed infrastructure plugin types and forbidden cognitive capabilities from vNext §20.

- [x] **Step 4: Wire sandbox/runtime**

Run agency boundary inside `PluginSandbox.evaluate()` before protected-surface checks.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_plugin_agency_boundary_phase11.py tests/test_v3_plugin_runtime.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-plugin-agency-boundary-phase11.md`

- [x] **Step 1: Document Phase 11**

Explain that plugin agency rejection is registration-time and separate from execution-time capability enforcement.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_plugin_agency_boundary_phase11.py tests/test_v3_plugin_runtime.py tests/test_v3_policy_engine.py -q`
Expected: selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 7C: Plugin Capability Enforcement
- [x] Phase 10: Formal Invariants Coverage Extension
- [x] Phase 11: Plugin Agency Boundary
