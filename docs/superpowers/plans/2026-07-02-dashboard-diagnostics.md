# Dashboard Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only Dashboard system diagnostics endpoint and settings panel.

**Architecture:** Keep diagnostics logic in `src/web/system.py` beside heartbeat/log/error routes. The endpoint reads shared runtime objects from `web._shared` and returns JSON-safe checks. Dashboard renders those checks in the existing Settings -> Service section.

**Tech Stack:** Starlette custom routes, Python helper functions, existing Dashboard HTML/JS, pytest.

---

### Task 1: Backend Diagnostics

**Files:**
- Modify: `src/web/system.py`
- Test: `tests/test_system_diagnostics.py`

- [ ] **Step 1: Write failing tests** for `build_system_diagnostics()` reporting missing LLM key/embedding backend and for `GET /api/system/diagnostics` returning authenticated JSON.
- [ ] **Step 2: Run tests** with `py -3.10 -m pytest tests\test_system_diagnostics.py -q`; expect import or missing attribute failure.
- [ ] **Step 3: Implement diagnostics helper and route** returning `ok`, `summary`, and ordered `checks`.
- [ ] **Step 4: Run tests** with `py -3.10 -m pytest tests\test_system_diagnostics.py -q`; expect pass.

### Task 2: Dashboard Panel

**Files:**
- Modify: `dashboard.html`
- Modify: `frontend/dashboard.html`
- Test: `tests/test_dashboard_diagnostics_panel.py`

- [ ] **Step 1: Write failing static HTML tests** requiring `/api/system/diagnostics`, `system-diagnostics-list`, and `loadSystemDiagnostics`.
- [ ] **Step 2: Run tests** with `py -3.10 -m pytest tests\test_dashboard_diagnostics_panel.py -q`; expect failure.
- [ ] **Step 3: Add Settings -> Service diagnostics markup and JS renderer**.
- [ ] **Step 4: Run static HTML tests**; expect pass.

### Task 3: Version and Verification

**Files:**
- Modify: `VERSION`
- Modify: `src/VERSION`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Bump version to 2.4.8 and add changelog entry**.
- [ ] **Step 2: Run focused tests**: `py -3.10 -m pytest tests\test_system_diagnostics.py tests\test_dashboard_diagnostics_panel.py tests\test_comprehensive.py -q`.
- [ ] **Step 3: Review diff, commit, and push** with `feat: add dashboard diagnostics`.

