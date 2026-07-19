# Public MCP Tool Design Phase 16 Implementation Plan

**Goal:** Implement vNext §25 Public MCP Tool Design as a protocol contract: public MCP tool names are philosophical organ-language assets, while engineering names must remain internal.

**Architecture:** Add `ombrebrain.protocol.public_tools` with tool specs, decisions, and manifest evaluation. The contract is diagnostic-only and does not change existing FastMCP registrations.

**Tech Stack:** Python dataclasses/enums, existing protocol package, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_public_tool_design_phase16.py`

- [x] **Step 1: Write failing public-tool contract tests**

Cover:
- vNext normal organ tools are accepted as public normal tools.
- current compatibility public names (`release`, `letter_write`, `letter_read`) are accepted but mapped to organ-language replacements.
- engineering aliases (`remember`, `touch`, `resolve`, `suppress`, `surface`, etc.) are rejected as public MCP tools.
- engineering aliases are allowed only in internal exposure.
- restricted tools require restricted/admin exposure.
- forbidden normal tools (`delete`, `dump_all`, `set_emotion`, etc.) are rejected.
- report is JSON-safe and protocol package exports contract symbols.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_public_tool_design_phase16.py -q`
Result: FAIL, 36 failed because public tool design symbols did not exist yet.

### Task 2: Implement Public Tool Contract

**Files:**
- Add: `src/ombrebrain/protocol/public_tools.py`
- Modify: `src/ombrebrain/protocol/__init__.py`

- [x] **Step 1: Add tool spec/decision dataclasses**

Create `ToolExposure`, `PublicToolSpec`, `PublicToolDecision`, `PublicToolReport`, and `PublicToolDesignContract`.

- [x] **Step 2: Add normal/restricted/forbidden classification**

Encode vNext §25 normal, restricted, and forbidden public tool names.

- [x] **Step 3: Add manifest evaluation**

Evaluate multiple tool specs and return JSON-safe details.

- [x] **Step 4: Export protocol symbols**

Export the new contract from `ombrebrain.protocol`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_public_tool_design_phase16.py -q`
Result: PASS, 36 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-public-tool-design-phase16.md`

- [x] **Step 1: Document Phase 16**

Explain that public tool design validation is contract-only and does not alter live MCP tool names.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_public_tool_design_phase16.py tests/test_neural_tool_router_phase8c.py tests/test_v3_release_acceptance.py -q`
Result: PASS, 46 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 651 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 15: Migration Preservation Contract
- [x] Phase 16: Public MCP Tool Design Contract
