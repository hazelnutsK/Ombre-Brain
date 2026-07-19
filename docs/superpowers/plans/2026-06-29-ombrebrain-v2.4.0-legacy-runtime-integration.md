# OmbreBrain v2.4.0 Legacy Runtime Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the existing server, bucket, tools, and web runtime surfaces to the v2.4.0 engine without changing their public behavior.

**Architecture:** Add a `LegacyRuntime` facade under `src/ombrebrain/app/` that owns v2.4.0 `MemoryFabric`, `CapabilityRegistry`, contexts, and policy helpers. Existing legacy modules keep their external APIs but optionally call the facade for event recording, capability dispatch, and hot-update policy checks.

**Tech Stack:** Python 3.10, pytest, existing OmbreBrain modules, v2.4.0 `src/ombrebrain/` architecture.

---

### Task 1: v2.4.0 Legacy Runtime Facade

**Files:**
- Create: `src/ombrebrain/app/__init__.py`
- Create: `src/ombrebrain/app/legacy_runtime.py`
- Test: `tests/test_v3_legacy_runtime.py`

- [ ] Write failing tests for runtime initialization, context creation, capability dispatch, and bucket event recording.
- [ ] Implement `LegacyRuntime.from_config(config)`.
- [ ] Store v2.4.0 data under `<buckets_dir>/.ombrebrain-v3`.
- [ ] Register foundation capabilities.
- [ ] Provide `record_bucket_event(action, bucket_id, bucket_type, content, metadata)`.
- [ ] Run `py -3.10 -m pytest tests/test_v3_legacy_runtime.py -q`.

### Task 2: BucketManager v2.4.0 Event Hook

**Files:**
- Modify: `src/bucket_manager.py`
- Test: `tests/test_v3_legacy_bucket_integration.py`

- [ ] Write failing tests proving `BucketManager.create()` still writes markdown and also records a v2.4.0 event when a runtime is attached.
- [ ] Add optional `v3_runtime` parameter to `BucketManager.__init__`.
- [ ] Add `attach_v3_runtime(runtime)` method.
- [ ] Call runtime after successful create/update/delete/archive writes.
- [ ] Never fail legacy bucket operations if v2.4.0 recording fails; log warning.
- [ ] Run bucket integration tests and existing bucket tests.

### Task 3: Tools Runtime Capability Wrapper

**Files:**
- Modify: `src/tools/_runtime.py`
- Modify: `src/server.py`
- Test: `tests/test_v3_legacy_tools_runtime.py`

- [ ] Write failing tests for injecting and dispatching v2.4.0 runtime through `tools._runtime`.
- [ ] Add `v3_runtime` global to `tools._runtime.init`.
- [ ] Add `run_capability(name, payload, permissions, actor_name, source)` helper.
- [ ] Keep helper best-effort: if v2.4.0 runtime is absent, return `None`.
- [ ] Update `server.py` runtime injection to pass v2.4.0 runtime.

### Task 4: Web Shared Runtime And Hot Update Policy

**Files:**
- Modify: `src/web/_shared.py`
- Modify: `src/web/meta.py`
- Test: `tests/test_v3_legacy_web_integration.py`

- [ ] Write failing tests that `web._shared` stores v2.4.0 runtime and exposes policy evaluation.
- [ ] Add `v3_runtime` to `web._shared.init`.
- [ ] Add `evaluate_v3_update_manifest(manifest, content_by_path)` wrapper.
- [ ] Add lightweight `/api/meta` exposure if existing meta route can include `v3_runtime`.
- [ ] Keep routes and response compatibility.

### Task 5: Server Startup Wiring

**Files:**
- Modify: `src/server.py`
- Test: `tests/test_v3_legacy_server_wiring.py`

- [ ] Write failing import-light tests for a pure `build_v3_runtime(config, bucket_mgr)` helper.
- [ ] Add helper near component initialization.
- [ ] Attach runtime to `bucket_mgr`.
- [ ] Inject runtime into `tools._runtime` and `web._shared`.
- [ ] Avoid changing MCP tool signatures.

### Task 6: Verification And Artifacts

**Files:**
- Update: `C:\Users\孙立人\Desktop\OmbreBrain-v2.4.0-总文件夹\OmbreBrain-v2.4.0-complete-artifacts`
- Update zip after verification if present.

- [ ] Run all new legacy integration tests.
- [ ] Run all v2.4.0 tests.
- [ ] Run key legacy regressions.
- [ ] Run full pytest.
- [ ] Regenerate diff, changed-files tree, Chinese summary, verification record, and zip inside the v2.4.0 total folder.
