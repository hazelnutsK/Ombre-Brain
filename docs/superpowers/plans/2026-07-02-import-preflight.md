# Import Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Dashboard import preflight step before the existing background import job starts.

**Architecture:** Put parse/chunk preview in `import_memory.py` as a pure function. Register `/api/import/preflight` in `web/import_api.py`. Dashboard stores the selected file in memory, renders preflight output, then calls the existing upload endpoint only after confirmation.

**Tech Stack:** Python pure helpers, Starlette custom routes, Dashboard HTML/JS, pytest static checks.

---

### Task 1: Pure Import Preview

**Files:**
- Modify: `src/import_memory.py`
- Test: `tests/test_import_preflight.py`

- [ ] **Step 1: Write failing tests** requiring `preview_import()` to report markdown turn/chunk counts and warn when invalid `.json` falls back to text.
- [ ] **Step 2: Run tests** with `py -3.10 -m pytest tests\test_import_preflight.py -q`; expect missing function failure.
- [ ] **Step 3: Implement `preview_import()`** using `detect_and_parse()` and `chunk_turns()`.
- [ ] **Step 4: Run tests**; expect pass.

### Task 2: Preflight API

**Files:**
- Modify: `src/web/import_api.py`
- Test: `tests/test_import_preflight.py`

- [ ] **Step 1: Add failing route test** for `POST /api/import/preflight`.
- [ ] **Step 2: Implement route** reusing upload body parsing and adding runtime readiness.
- [ ] **Step 3: Run route test**; expect pass.

### Task 3: Dashboard Confirmation UI

**Files:**
- Modify: `dashboard.html`
- Modify: `frontend/dashboard.html`
- Test: `tests/test_dashboard_import_preflight.py`

- [ ] **Step 1: Add failing static test** requiring `import-preflight-panel`, `runImportPreflight`, and `/api/import/preflight`.
- [ ] **Step 2: Patch Dashboard upload flow** so selected files are previewed before upload.
- [ ] **Step 3: Run static test**; expect pass.

### Task 4: Version and Verification

**Files:**
- Modify: `VERSION`
- Modify: `src/VERSION`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Bump version to 2.4.9 and add changelog entry**.
- [ ] **Step 2: Run focused tests** for import preflight, import JSON tolerance, dashboard static checks, and comprehensive regression.
- [ ] **Step 3: Commit and push** with `feat: add import preflight`.

