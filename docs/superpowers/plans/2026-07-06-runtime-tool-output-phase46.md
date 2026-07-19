# Runtime Tool Output Phase 46 Implementation Plan

**Goal:** Move tool-output humility receipts from standalone preflight construction into a reusable `LegacyRuntime` API.

**Architecture:** Keep public MCP output unchanged. `LegacyRuntime.tool_output_receipt()` builds a receipt from runtime neural routing, and `evaluate_tool_output()` evaluates the same receipt with `ToolOutputContract`. Preflight calls the runtime API.

**Tech Stack:** `LegacyRuntime`, `NeuralToolRouter`, `ToolOutputContract`, `VNextPreflightReportBuilder`, pytest.

---

## Implementation Steps

1. Add `ToolOutputContract` to `LegacyRuntime`.
2. Add `tool_output_receipt(...)` and `evaluate_tool_output(...)`.
3. Update the `tool_output_humility` preflight check to call runtime.
4. Add runtime regression coverage for scoped receipt evaluation.
5. Document the runtime boundary.

---

## Validation

Targeted command:

```powershell
pytest tests/test_v3_legacy_runtime.py tests/test_vnext_preflight_report_phase22.py tests/test_tool_output_contract_phase8d.py -q
```

Status: passed, 39 tests.

Full command:

```powershell
pytest -q
```

Status: passed, 719 passed and 7 skipped.

Diff check:

```powershell
git diff --check
```

Status: passed, with Windows LF-to-CRLF warnings only.
