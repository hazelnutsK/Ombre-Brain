# Ledger Replay Phase 5A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only replay validator that checks ledger events can rebuild the shadow projection while satisfying basic memory-state invariants.

**Architecture:** Keep Markdown buckets canonical. Keep `LedgerMirror` append-only and `TraceCatalogProjection` rebuildable. Add a small `LedgerReplayValidator` that consumes event dictionaries, rebuilds a projection, and returns a diagnostic report with violations instead of raising on recoverable replay issues.

**Tech Stack:** Python dataclasses, pytest, existing `LedgerMirror` and `TraceCatalogProjection`.

---

### Task 1: Capture Replay Contract

**Files:**
- Create: `tests/test_ledger_replay_phase5a.py`

- [x] **Step 1: Write failing replay success test**

Create a ledger lifecycle with create/update/touch/tombstone delete and assert `LedgerReplayValidator.validate(events)` returns `ok=True`, `event_count`, `latest_seq`, `projection_trace_count`, `tombstone_count`, and no violations.

- [x] **Step 2: Write failing replay violation test**

Create manual events with duplicated/non-increasing seq values and an invalid body hash, then assert the validator reports `non_increasing_seq` and `invalid_body_hash` violations without crashing.

- [x] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_ledger_replay_phase5a.py -q`

Expected: FAIL because `ledger_replay.py` does not exist yet.

### Task 2: Implement Replay Validator

**Files:**
- Create: `src/ledger_replay.py`

- [x] **Step 1: Implement `LedgerReplayValidator.validate()`**

Return a report dict with:
- `ok`
- `event_count`
- `latest_seq`
- `projection_name`
- `projection_trace_count`
- `tombstone_count`
- `unknown_event_count`
- `violations`

- [x] **Step 2: Validate simple invariants**

Detect non-increasing seq, missing trace id, invalid/missing body hash, tombstone traces that are not marked deleted, and projection lag.

- [x] **Step 3: Run replay tests**

Run: `pytest tests/test_ledger_replay_phase5a.py -q`

Expected: PASS.

### Task 3: Attach Replay Diagnostics

**Files:**
- Modify: `src/bucket_manager.py`
- Modify: `tests/test_ledger_mirror_phase1.py`
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Add replay report to `ledger_integrity_report()`**

Attach `report["replay"] = LedgerReplayValidator.default().validate(events)`.

- [x] **Step 2: Update diagnostics tests**

Assert fake and real reports include `replay.ok` and replay counters.

- [x] **Step 3: Run targeted tests**

Run: `pytest tests/test_ledger_replay_phase5a.py tests/test_ledger_mirror_phase1.py tests/test_projection_mirror_phase2.py tests/test_system_diagnostics.py -q`

Expected: PASS.

### Task 4: Document And Verify

**Files:**
- Modify: `docs/INTERNALS.md`

- [x] **Step 1: Document Phase 5A replay validator**

Add a vNext section explaining that replay validation is still shadow/read-only and defines the contract a future Rust kernel must preserve.

- [x] **Step 2: Run full regression**

Run: `pytest -q`

Expected: PASS.

- [x] **Step 3: Run whitespace diff check**

Run: `git diff --check`

Expected: no whitespace errors.

- [x] **Step 4: Stop locally**

Do not commit or push unless the user asks.
