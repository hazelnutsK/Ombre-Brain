# Import Preflight Design

## Goal

Make Dashboard imports less opaque by previewing the uploaded conversation before starting the background import job.

## Scope

Add a lightweight preflight step that parses and chunks the file locally. It does not call the LLM, does not write buckets, and does not mutate import state.

## Design

Add `preview_import(raw_content, filename, human_label)` in `src/import_memory.py`. It returns whether the file is parseable, detected format, turn count, chunk count, estimated API calls, rough token count, first chunk preview, and warnings such as invalid JSON falling back to text.

Add `POST /api/import/preflight` in `src/web/import_api.py`. It reads the same upload shapes as `/api/import/upload`, calls `preview_import`, and adds runtime readiness fields:

- `can_start`
- `import_running`
- `llm_ready`
- `filename`
- `size_bytes`

Dashboard changes file selection flow to:

1. User selects or drops file.
2. Browser calls `/api/import/preflight`.
3. Panel shows format, turns, chunks, estimated API calls, warnings, and a first chunk preview.
4. User clicks "开始导入" to run the existing `/api/import/upload` path.

## Testing

Add pure parser tests, route tests, and a static Dashboard test so the preflight path cannot regress silently.

