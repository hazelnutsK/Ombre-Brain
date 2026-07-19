# OmbreBrain v2.4.0 Total Hardening Implementation Plan

## Goal

Finish the v2.4.0 advanced architecture pass for all remaining legacy modules while
preserving the original Ombre Brain behavior.

## Tasks

### 1. Legacy Execution Pipeline

- Test: `tests/test_v3_legacy_execution_pipeline.py`
- Create `src/ombrebrain/app/execution.py`.
- Add immutable operation envelopes, sanitized payloads, permission checks,
  result metadata, phase transitions, and failure passthrough.

### 2. Module Profile Registry

- Test: `tests/test_v3_legacy_module_profiles.py`
- Create `src/ombrebrain/app/profiles.py`.
- Register core, tools, web, frontend, deploy, Docker, and config profiles.
- Expose the profiles through `LegacyRuntime`.

### 3. Runtime Recording

- Extend `LegacyRuntime` with `record_execution_event()` and pipeline ownership.
- Ensure successful and failed operations write internal v2.4.0 trace events.

### 4. Core Engine Attachment

- Add no-op-safe `attach_v3_runtime()` support to decay, dehydrator, embedding,
  import, migrate, migration, and GitHub sync surfaces.
- Wire all created components from `server.py` via `legacy_wiring`.

### 5. Tools/Web Gateway Integration

- Extend `tools/_runtime.py` with `run_v3_operation()`.
- Extend `web/_shared.py` with `run_v3_web_operation()`.
- Keep existing `record_v3_tool_event()` and hot-update policy behavior.

### 6. Verification and Artifacts

- Run targeted v2.4.0 tests.
- Run legacy regression tests.
- Run full pytest suite if targeted verification passes.
- Refresh v2.4.0 complete artifacts folder and zip inside the total folder.
