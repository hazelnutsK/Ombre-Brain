# Dashboard Diagnostics Design

## Goal

Add a fast, read-only system diagnostics surface in Dashboard so users can see why Ombre Brain is not fully healthy without digging through logs.

## Scope

This first slice covers local/runtime checks only. It does not call external LLM, embedding, GitHub, or Cloudflare APIs; those slower network probes stay behind the existing explicit test/validate buttons.

## Design

Add `GET /api/system/diagnostics` in `src/web/system.py`. The endpoint returns:

- `ok`: true when no check has `error`
- `summary`: counts of `ok`, `warning`, and `error`
- `checks`: ordered check entries with `id`, `label`, `status`, `message`, `details`, and optional `action`

Checks:

- `storage`: `buckets_dir` exists and is writable
- `buckets`: bucket counts via the current `bucket_mgr`
- `llm`: dehydration model/base URL/key/timeout are present enough to write memories
- `embedding`: embedding enabled/runtime/backend/db path
- `github`: GitHub sync configured/validated/last status
- `auth`: Dashboard password and MCP OAuth mode
- `runtime`: version, decay engine, environment type, repo root

Dashboard adds a compact "系统体检" panel under Settings -> Service. It calls the endpoint on refresh/settings load and renders status rows with stable colors and short action hints.

## Testing

Add `tests/test_system_diagnostics.py` with a failing-first helper test for missing critical configuration and a route test that verifies authentication and response shape.

