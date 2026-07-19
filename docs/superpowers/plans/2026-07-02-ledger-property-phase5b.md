# Ledger Property Phase 5B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic randomized replay/property checks for the shadow ledger contract before any Rust kernel work.

**Architecture:** Keep runtime paths unchanged. Add a small `LedgerReplayPropertyRunner` that generates valid random ledger event streams from a seed, feeds them through `LedgerReplayValidator`, and reports any replay invariant failures. This runner is for tests/manual diagnostics, not Dashboard hot paths.

**Tech Stack:** Python standard library `random` and `hashlib`, existing `LedgerReplayValidator`, pytest.

---

### Task 1: Capture Property Runner Contract

**Files:**
- Create: `tests/test_ledger_property_phase5b.py`

- [x] **Step 1: Write failing deterministic generation test**

Assert two runners with the same seed produce identical event streams and strictly increasing seq values.

- [x] **Step 2: Write failing randomized replay test**

Assert `LedgerReplayPropertyRunner.default().run(seed=20260702, cases=25, max_events=80)` returns `ok=True`, reports all cases, and has no failures.

- [x] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_ledger_property_phase5b.py -q`

Expected: FAIL because `ledger_property.py` does not exist yet.

### Task 2: Implement Property Runner

**Files:**
- Create: `src/ledger_property.py`

- [x] **Step 1: Implement deterministic event generation**

Generate valid event streams with create/update/touch/archive/tombstone-delete events over a small trace pool. Every generated event must have a valid `sha256:<64hex>` body hash, non-empty trace id, and strictly increasing seq.

- [x] **Step 2: Implement `run()`**

Run `LedgerReplayValidator` over each generated case and return:
- `ok`
- `seed`
- `cases`
- `max_events`
- `failures`
- `checked_events`

- [x] **Step 3: Run property tests**

Run: `pytest tests/test_ledger_property_phase5b.py -q`

Expected: PASS.

### Task 3: Document And Verify

**Files:**
- Modify: `docs/INTERNALS.md`

- [x] **Step 1: Document Phase 5B**

Explain that property runner is deterministic, local/manual/test-only, and is the acceptance harness for a future Rust kernel.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_ledger_property_phase5b.py tests/test_ledger_replay_phase5a.py tests/test_projection_mirror_phase2.py -q`

Expected: PASS.

- [x] **Step 3: Run full regression**

Run: `pytest -q`

Expected: PASS.

- [x] **Step 4: Run whitespace diff check**

Run: `git diff --check`

Expected: no whitespace errors.

- [x] **Step 5: Stop locally**

Do not commit or push unless the user asks.
