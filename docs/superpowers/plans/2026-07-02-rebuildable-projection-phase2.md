# Rebuildable Projection Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. User instruction for this session: do not commit and do not push.

**Goal:** Add the first rebuildable projection derived from the Phase 1 ledger mirror without changing current Markdown/search behavior.

**Architecture:** Keep Markdown and existing indexes as the runtime read path. Add a lightweight trace catalog projection that can rebuild from `LedgerMirror.iter_events()` and report projection lag. This projection is disposable and explicitly non-canonical.

**Tech Stack:** Python 3, dataclasses, existing `LedgerMirror`, pytest.

---

### Task 1: Define A Minimal Projection Contract

**Files:**
- Create: `src/projection_mirror.py`
- Test: `tests/test_projection_mirror_phase2.py`

- [x] **Step 1: Write failing tests**

Assert the projection reports `projection_role="shadow"`, `canonical=False`, and can rebuild from an empty ledger.

- [x] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_projection_mirror_phase2.py -q`

Expected: FAIL because `projection_mirror` does not exist.

- [x] **Step 3: Implement minimal contract**

Create `TraceCatalogProjection` with `rebuild(events)` and `to_report(source_latest_seq=0)`.

- [x] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_projection_mirror_phase2.py -q`

Expected: PASS.

### Task 2: Rebuild Trace State From Ledger Events

**Files:**
- Modify: `src/projection_mirror.py`
- Test: `tests/test_projection_mirror_phase2.py`

- [x] **Step 1: Write failing lifecycle tests**

Append `TraceCreated`, `TraceUpdated`, `TraceTouched`, `TraceArchived`, and `TraceDeletedToArchive` events to a ledger. Rebuild projection and assert latest state, kind, touched count, and deleted/archived markers.

- [x] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_projection_mirror_phase2.py -q`

Expected: FAIL because lifecycle handling is missing.

- [x] **Step 3: Implement lifecycle rebuild**

Store one trace entry per `trace_id`. Events are applied in ledger order. Unknown event types are counted but do not fail rebuild.

- [x] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_projection_mirror_phase2.py -q`

Expected: PASS.

### Task 3: Report Projection Lag In Diagnostics

**Files:**
- Modify: `src/bucket_manager.py`
- Modify: `src/web/system.py`
- Test: `tests/test_projection_mirror_phase2.py`
- Test: `tests/test_system_diagnostics.py`

- [x] **Step 1: Write failing diagnostics tests**

Assert `BucketManager.ledger_integrity_report()` includes `trace_catalog_projection` with `applied_seq`, `source_latest_seq`, and `lag`.

- [x] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_projection_mirror_phase2.py tests/test_system_diagnostics.py -q`

Expected: FAIL because diagnostics do not yet include projection report.

- [x] **Step 3: Implement report wiring**

Rebuild the in-memory projection on demand inside `ledger_integrity_report()`. This is read-only and does not write projection files.

- [x] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_projection_mirror_phase2.py tests/test_system_diagnostics.py -q`

Expected: PASS.

### Task 4: Verify Scope

- [ ] **Step 1: Run focused tests**

Run: `pytest tests/test_projection_mirror_phase2.py tests/test_ledger_mirror_phase1.py tests/test_system_diagnostics.py -q`

- [ ] **Step 2: Run full suite**

Run: `pytest -q`

- [ ] **Step 3: Stop without commit or push**

Run: `git status --short`

Expected: local modifications only.
