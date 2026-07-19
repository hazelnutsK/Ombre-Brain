# Public Tool Manifest Diagnostics Phase 32 Implementation Plan

**Goal:** Connect the Phase 16 public MCP tool design contract to Dashboard system diagnostics so live public tool names stay inside organ-language boundaries.

**Architecture:** Use read-only AST inspection of `src/server.py` to collect functions decorated with `@mcp.tool()` and `@mcp_extra.tool()`. Evaluate those names through `PublicToolDesignContract`. Do not import `server.py`, start FastMCP, change tool registration, or remove legacy compatibility names.

**Tech Stack:** `web.system.build_system_diagnostics`, `PublicToolDesignContract`, Python `ast`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Require public tool manifest check**

Assert diagnostics includes `public_tool_manifest` with an OK contract report.

- [x] **Step 2: Require current public tool names**

Assert the diagnostics details include current organ tools and the compatibility `release` tool.

### Task 2: Implement Source Registration Audit

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Add source parser**

Add `_read_public_tool_specs_from_server_source()` to parse `src/server.py` without importing it.

- [x] **Step 2: Evaluate through public tool contract**

Append `public_tool_manifest` diagnostics check using `PublicToolDesignContract.default().evaluate_manifest(...)`.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-public-tool-manifest-diagnostics-phase32.md`

- [x] **Step 1: Document Phase 32**

Explain that the diagnostics audit is read-only and source based.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_system_diagnostics.py tests/test_public_tool_design_phase16.py -q`
Result: PASS, 38 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 31: Diagnostics Observability Boundary
- [x] Phase 32: Public Tool Manifest Diagnostics
