# Tool Output Humility Contract Phase 8D Implementation Plan

**Goal:** Implement the vNext §16.12 tool output contract: every public tool result must remain memory-humble, descriptive, and unable to become an instruction, current feeling, belief engine, or autonomous action driver.

**Architecture:** Add a shadow-only contract in `ombrebrain.app.tool_output_contract`. It wraps `NeuralToolRoute` metadata into a JSON-safe receipt and evaluates receipts for humility violations. It does not replace MCP handlers or change live responses yet.

**Tech Stack:** Python dataclasses/enums, existing `NeuralToolRouter`, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_tool_output_contract_phase8d.py`

- [x] **Step 1: Write failing contract tests**

Cover:
- `breath` output renders surfaced memory, not instruction.
- `pulse` output renders homeostatic signal, not emotion.
- `dream` output renders sediment, not belief engine.
- `trace` output renders reconstruction/trace, not original or command.
- receipts are JSON-safe and preserve public tool/subsystem metadata.
- contract rejects outputs that can drive action, claim current emotion, or carry instructional force.
- app package exports the contract symbols.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tool_output_contract_phase8d.py -q`
Expected: FAIL because `ombrebrain.app.tool_output_contract` does not exist yet.

### Task 2: Implement Shadow Contract

**Files:**
- Add: `src/ombrebrain/app/tool_output_contract.py`
- Modify: `src/ombrebrain/app/__init__.py`

- [x] **Step 1: Add receipt and boundary dataclasses**

Create `ToolOutputStatus`, `ToolOutputBoundary`, `ToolOutputReceipt`, and `ToolOutputContract`.

- [x] **Step 2: Add subsystem-specific humility text**

Render vNext §16.12 English/Chinese boundaries for surfaced memory, past affect, trace, reconstruction, sediment, and homeostatic signal.

- [x] **Step 3: Add executable contract checks**

Reject `may_drive_action=True`, instructional force, current-emotion claims, belief-engine claims, or original-memory claims.

- [x] **Step 4: Export app symbols**

Export the new contract types from `ombrebrain.app`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_tool_output_contract_phase8d.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-tool-output-contract-phase8d.md`

- [x] **Step 1: Document Phase 8D**

Explain that this is a shadow tool-output contract and does not yet alter live MCP output formatting.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_tool_output_contract_phase8d.py tests/test_neural_tool_router_phase8c.py tests/test_context_serialization_phase8b.py tests/test_formal_invariants_phase8a.py -q`
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
- [x] Phase 8D: Tool Output Humility Contract
