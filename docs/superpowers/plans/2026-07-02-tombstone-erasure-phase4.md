# Tombstone Erasure Phase 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Represent user-facing deletion as tombstone-only erasure in the shadow ledger/projection path while preserving the existing Markdown archive behavior.

**Architecture:** Keep Markdown buckets canonical and keep `delete()` moving files to `archive/` with `deleted_at`. Add tombstone metadata to the archived Markdown frontmatter and ledger payload. Teach the rebuildable projection to surface a `tombstone` state and count tombstoned traces for diagnostics.

**Tech Stack:** Python dataclasses, python-frontmatter, pytest, existing `LedgerMirror` and `TraceCatalogProjection`.

---

### Task 1: Capture Tombstone Delete Contract

**Files:**
- Create: `tests/test_tombstone_erasure_phase4.py`
- Modify: `tests/test_projection_mirror_phase2.py`

- [x] **Step 1: Write failing BucketManager tombstone test**

Add a test that creates a bucket, calls `delete()`, reads the archived Markdown frontmatter, and asserts `deleted_at`, `tombstone=True`, `tombstoned_at`, and `erasure_mode="tombstone_only"`.

- [x] **Step 2: Write failing ledger/projection test**

Add a test that verifies the delete ledger payload carries tombstone metadata and the trace catalog projection reports `tombstone_count=1`.

- [x] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_tombstone_erasure_phase4.py tests/test_projection_mirror_phase2.py -q`

Expected: FAIL because delete does not write tombstone metadata and projection does not count tombstones yet.

### Task 2: Implement Tombstone Metadata

**Files:**
- Modify: `src/bucket_manager.py`

- [x] **Step 1: Add tombstone frontmatter during soft delete**

In `BucketManager.delete()`, reuse the same timestamp for `deleted_at` and `tombstoned_at`, set `tombstone=True`, and set `erasure_mode="tombstone_only"` before writing the archived Markdown file.

- [x] **Step 2: Run BucketManager tombstone test**

Run: `pytest tests/test_tombstone_erasure_phase4.py::test_bucket_manager_delete_writes_tombstone_metadata_and_ledger_payload -q`

Expected: PASS.

### Task 3: Implement Tombstone Projection

**Files:**
- Modify: `src/projection_mirror.py`

- [x] **Step 1: Recognize tombstone payloads**

Treat `TraceDeletedToArchive` with `payload.tombstone=True` or `payload.erasure_mode=="tombstone_only"` as projection state `tombstone`, while keeping older `TraceDeletedToArchive` events as `deleted_to_archive`.

- [x] **Step 2: Report tombstone count**

Add `tombstone_count` to `TraceCatalogProjection.to_report()`.

- [x] **Step 3: Run projection tests**

Run: `pytest tests/test_projection_mirror_phase2.py tests/test_tombstone_erasure_phase4.py -q`

Expected: PASS.

### Task 4: Document And Verify

**Files:**
- Modify: `docs/INTERNALS.md`

- [x] **Step 1: Document Phase 4 shadow tombstone semantics**

Add a short vNext section explaining that delete is now represented as tombstone-only erasure in ledger/projection, while Markdown archive remains canonical.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_tombstone_erasure_phase4.py tests/test_projection_mirror_phase2.py tests/test_ledger_mirror_phase1.py tests/test_surface_policy_phase3.py -q`

Expected: PASS.

- [x] **Step 3: Run full regression**

Run: `pytest -q`

Expected: PASS.

- [x] **Step 4: Run whitespace diff check**

Run: `git diff --check`

Expected: no whitespace errors.

- [x] **Step 5: Stop locally**

Do not commit or push unless the user asks.
