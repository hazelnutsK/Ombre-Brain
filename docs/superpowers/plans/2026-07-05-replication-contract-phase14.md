# Replication Contract Phase 14 Implementation Plan

**Goal:** Implement vNext §23 Cluster and Replication as a shadow contract: cluster support is allowed only when memory philosophy is preserved.

**Architecture:** Add `ombrebrain.cluster.replication.contract` with topology and segment checks. The contract verifies single-writer canonical ledger shape, multi-reader projection shape, snapshot + append-only segment replication, and the tombstone replication invariant. It does not change the existing Raft-style local cluster simulator.

**Tech Stack:** Python dataclasses, existing cluster package, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_replication_contract_phase14.py`

- [x] **Step 1: Write failing replication-contract tests**

Cover:
- topology with one canonical writer, projection readers, optional encrypted replicas, and append-only segments is accepted.
- multiple canonical writers are rejected.
- full distributed consensus without an explicit necessity reason is rejected.
- replication segments may replicate traces and tombstones, not database-style user records.
- erased content removal must be replicated with a tombstone for the same trace.
- report is JSON-safe and package exports contract symbols.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_replication_contract_phase14.py -q`
Expected: FAIL because replication contract symbols do not exist yet.

### Task 2: Implement Replication Contract

**Files:**
- Add: `src/ombrebrain/cluster/replication/contract.py`
- Modify: `src/ombrebrain/cluster/replication/__init__.py`

- [x] **Step 1: Add topology/segment dataclasses**

Create `ReplicationTopology`, `ReplicationSegment`, `ReplicationDecision`, and `ReplicationContract`.

- [x] **Step 2: Add topology validation**

Validate single-writer canonical ledger, projection readers, optional encrypted replicas, and append-only segment mode.

- [x] **Step 3: Add segment validation**

Reject user-record replication and enforce removal+tombstone pairing.

- [x] **Step 4: Export replication symbols**

Export the new contract types from `ombrebrain.cluster.replication`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_replication_contract_phase14.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-replication-contract-phase14.md`

- [x] **Step 1: Document Phase 14**

Explain that replication contract is diagnostic-only and does not implement distributed consensus.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_replication_contract_phase14.py tests/test_v3_raft_cluster.py tests/test_v3_snapshot_catchup.py -q`
Expected: selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 13: Crash Recovery Contract
- [x] Phase 14: Replication Contract
