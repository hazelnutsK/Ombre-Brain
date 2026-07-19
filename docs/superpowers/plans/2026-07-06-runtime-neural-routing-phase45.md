# Runtime Neural Routing Phase 45 Implementation Plan

**Goal:** Move neural tool routing from shadow contract-only usage into a reusable `LegacyRuntime` API.

**Architecture:** Add `LegacyRuntime.neural_route()` and `route_neural_tool()` backed by `NeuralToolRouter`. Have the tool-output humility preflight reuse the runtime route. Do not call handlers or change MCP public tool names.

**Tech Stack:** `LegacyRuntime`, `NeuralToolRouter`, `ToolOutputContract`, pytest.

---

## Implementation Steps

1. Add a `NeuralToolRouter` field to `LegacyRuntime.from_config()`.
2. Add runtime APIs returning either a `NeuralToolRoute` object or JSON-safe dict.
3. Update `VNextPreflightReportBuilder.tool_output_humility` to route through `LegacyRuntime`.
4. Add regression tests for scoped route generation and forbidden route denial.
5. Document the live runtime boundary in `docs/INTERNALS.md`.

---

## Validation

Targeted command:

```powershell
pytest tests/test_v3_legacy_runtime.py tests/test_vnext_preflight_report_phase22.py -q
```

Status: passed, 30 tests.

Full command:

```powershell
pytest -q
```

Status: passed, 717 passed and 7 skipped.

Diff check:

```powershell
git diff --check
```

Status: passed, with Windows LF-to-CRLF warnings only.
