# Ledger Mirror Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. User instruction for this session: do not commit and do not push.

**Goal:** Add a Python-first append-only ledger mirror beside existing Markdown bucket storage without changing current public MCP tool names or read behavior.

**Architecture:** Keep Markdown buckets as the active source for current reads and UI. Add a small JSONL ledger module that records successful bucket mutations after they are already durable on disk. The ledger is a mirror for auditability and future replay work, not yet canonical truth.

**Tech Stack:** Python 3, JSONL, existing `BucketManager`, pytest.

---

### Task 1: Add A Focused Ledger Module

**Files:**
- Create: `src/ledger_mirror.py`
- Test: `tests/test_ledger_mirror_phase1.py`

- [x] **Step 1: Write failing tests**

```python
def test_append_event_writes_jsonl_with_hash_and_sequence(tmp_path):
    from ledger_mirror import LedgerMirror

    ledger = LedgerMirror(tmp_path / "ledger.jsonl")
    event = ledger.append_event(
        event_type="TraceCreated",
        trace_id="b1",
        trace_kind="dynamic",
        payload={"name": "hello"},
        body="memory body",
    )

    rows = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
    data = json.loads(rows[0])
    assert event["seq"] == 1
    assert data["event_type"] == "TraceCreated"
    assert data["trace_id"] == "b1"
    assert data["body_hash"].startswith("sha256:")
    assert data["payload"] == {"name": "hello"}
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ledger_mirror_phase1.py::test_append_event_writes_jsonl_with_hash_and_sequence -q`

Expected: FAIL because `ledger_mirror` does not exist.

- [x] **Step 3: Implement minimal ledger module**

Create `LedgerMirror` with `append_event()`, sequence detection from existing JSONL, JSON-safe payload serialization, content hashing, and append-only writes.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ledger_mirror_phase1.py::test_append_event_writes_jsonl_with_hash_and_sequence -q`

Expected: PASS.

### Task 2: Wire Ledger Mirror Into BucketManager Without Changing Behavior

**Files:**
- Modify: `src/bucket_manager.py`
- Test: `tests/test_ledger_mirror_phase1.py`

- [x] **Step 1: Write failing integration tests**

Test that `BucketManager.create()` appends `TraceCreated` after successful markdown write, and `update()/delete()/archive()` append corresponding events. Use a fake embedding engine so tests exercise real bucket files without external API.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ledger_mirror_phase1.py -q`

Expected: FAIL because `BucketManager` does not yet create or call a ledger mirror.

- [x] **Step 3: Implement minimal wiring**

Instantiate `LedgerMirror` in `BucketManager.__init__` at `<buckets_dir>/_ledger/events.jsonl` by default. Add a private `_record_ledger_event()` helper that catches and logs ledger failures so the mirror cannot break current bucket operations in Phase 1.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ledger_mirror_phase1.py -q`

Expected: PASS.

### Task 3: Add Read/Replay Helpers For Future Projection Work

**Files:**
- Modify: `src/ledger_mirror.py`
- Test: `tests/test_ledger_mirror_phase1.py`

- [x] **Step 1: Write failing tests**

Test `iter_events()` returns events in append order and ignores blank lines.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ledger_mirror_phase1.py::test_iter_events_reads_append_order -q`

Expected: FAIL because `iter_events()` does not exist.

- [x] **Step 3: Implement minimal read helper**

Add `iter_events()` and `latest_seq()` methods.

- [x] **Step 4: Run tests to verify they pass**

### Task 3.5: Harden Event Schema And Diagnostics

**Files:**
- Modify: `src/ledger_mirror.py`
- Modify: `src/bucket_manager.py`
- Modify: `src/web/system.py`
- Modify: `docs/INTERNALS.md`
- Test: `tests/test_ledger_mirror_phase1.py`
- Test: `tests/test_system_diagnostics.py`

- [x] **Step 1: Add failing schema/version tests**

Assert each event has `schema_version=1`, `ledger_role="mirror"`, and `canonical=false`.

- [x] **Step 2: Add failing corrupt-line recovery tests**

Assert corrupt/partial JSONL lines are reported by `verify_integrity()` and skipped by `iter_events()`.

- [x] **Step 3: Implement schema/version and corrupt-line recovery**

Add constants, skip invalid JSONL rows during iteration, and insert a newline before appending after a partial final line.

- [x] **Step 4: Add read-only diagnostics**

Expose `BucketManager.ledger_integrity_report()` and surface it through `/api/system/diagnostics`.

- [x] **Step 5: Document mirror boundary**

Document that Phase 1 ledger is an audit mirror, not canonical truth.

Run: `pytest tests/test_ledger_mirror_phase1.py -q`

Expected: PASS.

### Task 4: Verify Scope

**Files:**
- No new production files beyond `src/ledger_mirror.py`
- No public MCP tool renames
- No Rust kernel
- No projection replacement

- [ ] **Step 1: Run focused tests**

Run: `pytest tests/test_ledger_mirror_phase1.py tests/test_comprehensive.py::TestBucketManager -q`

- [ ] **Step 2: Run full suite**

Run: `pytest -q`

- [ ] **Step 3: Stop without commit or push**

Run: `git status --short`

Expected: local modifications only.
