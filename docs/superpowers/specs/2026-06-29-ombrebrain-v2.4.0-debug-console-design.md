# OmbreBrain v2.4.0 Debug Console Design

## Goal

Add E1/E2/E3 as a read-only v2.4.0 debugging layer over Decision Ledger and Replay Debugger. The layer should make internal v2.4.0 audit data easier to inspect from code, HTTP, CLI, and Dashboard, while preserving all existing Ombre Brain behavior.

## Approved Scope

The user approved all three steps:

- E1: read-only CLI/API debug entry
- E2: Dashboard internal debug view
- E3: drift, malformed data, and legacy behavior regression tests

## Architecture

The debug layer sits above the existing v2.4.0 side channel:

`MemoryFabric events -> decision_record metadata -> DecisionDebugService -> ReplayDebugger -> API/CLI/Dashboard`

No legacy handler is re-executed. No bucket, vector database, config file, deploy file, OAuth file, or remote network resource is modified.

## Components

### DecisionDebugService

`DecisionDebugService` reads v2.4.0 memory fabric events and extracts `decision_record` metadata. It provides:

- `list_records(limit, module, operation)` for recent records
- `get_record(command_id or decision_id)` for a single record
- `explain(...)` for replay/explanation
- `health()` for operator-facing status

The service tolerates bad historical metadata and returns structured problems instead of crashing.

### Web API

Add `src/web/v3_debug.py` with authenticated GET endpoints:

- `GET /api/v3/debug/decisions`
- `GET /api/v3/debug/decision/{identifier}`
- `GET /api/v3/debug/replay/{identifier}`

All endpoints are read-only and use existing dashboard auth.

### CLI

Add a small local CLI under `tools/debug_decision.py` for offline inspection:

- `list`
- `show <id>`
- `replay <id>`

The CLI reads the same fabric directory from a `--buckets-dir` argument.

### Dashboard View

Add a `2.4.0 Debug` tab to `frontend/dashboard.html`. It shows recent decisions, policy/consistency status, projection surfaces, and replay issues. The view fetches only the new read-only debug endpoints.

## Behavior Guarantees

- No route changes for existing APIs.
- No changes to MCP tool names, parameters, return strings, or errors.
- No changes to bucket markdown or embedding side effects.
- No changes to deployment behavior.
- Debug endpoints require the same dashboard authentication as operational APIs.
- If the v2.4.0 runtime is unavailable, endpoints return an empty/disabled debug payload rather than affecting normal dashboard usage.

## Testing

Tests cover:

- service list/get/replay
- bad decision metadata does not crash the service
- web route registration includes the new debug routes
- debug API delegates to runtime/service read-only methods
- dashboard contains the v2.4.0 debug tab, view, endpoint calls, and render functions
- legacy operations still return handler results and trace metadata remains append-only

## Non-Goals

- No production multi-node transport.
- No writable admin action in the debug UI.
- No generated release/publish step.
- No commit, push, or cloud operation.
