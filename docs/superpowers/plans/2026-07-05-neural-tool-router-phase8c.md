# Neural Tool Router Shadow Contract Phase 8C Implementation Plan

**Goal:** Implement the vNext §16.11 internal Neural Tool Router contract: public organ tool names stay unchanged, while internal routes declare the neural subsystem, policy boundary, command kind, and capability tags.

**Architecture:** Add a shadow-only router in `ombrebrain.app.neural_router`. It does not replace `LegacyCommandBridge`, does not execute handlers, and does not call the kernel. It only produces a JSON-safe `NeuralToolRoute` that can be inspected, tested, and later wired into runtime/policy enforcement.

**Tech Stack:** Python enums/dataclasses, existing `CommandKind`, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_neural_tool_router_phase8c.py`

- [x] **Step 1: Write failing router tests**

Cover:
- `hold`/`grow` route to `engram_encoding`;
- `breath` routes to `cue_driven_surfacing` with normal surface budget;
- `pulse` routes to `homeostatic_monitoring` and is read-only;
- `dream` routes to `offline_replay`;
- `trace` routes to `reconsolidation`;
- `anchor`/`I`/`letter` include non-cognition boundary;
- `plan` includes no-agency boundary and cannot drive action;
- forbidden/unknown tool names are rejected.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_neural_tool_router_phase8c.py -q`
Expected: FAIL because `ombrebrain.app.neural_router` does not exist yet.

### Task 2: Implement Shadow Router

**Files:**
- Add: `src/ombrebrain/app/neural_router.py`
- Modify: `src/ombrebrain/app/__init__.py`

- [x] **Step 1: Add route contracts**

Create `OrganTool`, `NeuralSubsystem`, `ToolScope`, `NeuralToolRoute`, and `NeuralToolRouter`.

- [x] **Step 2: Add deterministic routing table**

Map all current public tools to internal neural subsystems and command kinds without changing public names.

- [x] **Step 3: Add policy boundary metadata**

Expose `policy_boundaries`, `capability_tags`, `surface_budget`, `writes_memory`, and `may_drive_action=False`.

- [x] **Step 4: Export app symbols**

Export router symbols from `ombrebrain.app`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_neural_tool_router_phase8c.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-neural-tool-router-phase8c.md`

- [x] **Step 1: Document Phase 8C**

Explain that this is a shadow routing contract, not live handler execution.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_neural_tool_router_phase8c.py tests/test_v3_legacy_command_bridge.py tests/test_v3_policy_engine.py -q`
Expected: selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 8A: Formal Invariants Shadow Checker
- [x] Phase 8B: Context Serialization Contract
- [x] Phase 8C: Neural Tool Router Shadow Contract
