# Formal Invariants Shadow Checker Phase 8A Implementation Plan

**Goal:** Turn the vNext §18/§19 philosophical invariants into a read-only, JSON-safe checker that can be attached to diagnostics without changing runtime behavior.

**Architecture:** Add `ombrebrain.policy.formal_invariants.FormalInvariantChecker`. It consumes already-produced ledger events, surfacing decisions, context serialization metadata, and tool request metadata. It never writes buckets, never mutates projections, and never blocks requests in Phase 8A.

**Tech Stack:** Python dataclasses, existing `SurfacePolicyVM`, existing ledger diagnostics, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_formal_invariants_phase8a.py`
- Modify: `src/bucket_manager.py`

- [x] **Step 1: Write failing invariant checker tests**

Cover:
- physical erasure without tombstone is a violation;
- suppressed memory cannot be allowed through spontaneous surfacing;
- memory context with imperative text and instructional force is a violation;
- ordinary `breath` cannot request unrestricted total recall.

- [x] **Step 2: Write failing diagnostics test**

Assert `BucketManager.ledger_integrity_report()` exposes `formal_invariants` with shadow role and non-canonical status.

- [x] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_formal_invariants_phase8a.py -q`
Expected: FAIL because `FormalInvariantChecker` does not exist yet.

### Task 2: Implement Checker

**Files:**
- Add: `src/ombrebrain/policy/formal_invariants.py`
- Modify: `src/ombrebrain/policy/__init__.py`
- Modify: `src/bucket_manager.py`

- [x] **Step 1: Add report contracts**

Create `InvariantViolation`, `InvariantReport`, and JSON-safe `to_dict()` methods.

- [x] **Step 2: Add invariant checks**

Implement read-only checks for selected §18 invariants:
- I1 no silent erasure;
- I3 similarity cannot bypass policy;
- I4/I13 memory context cannot carry instructional force;
- I6/I9 ordinary tools cannot request total recall.

- [x] **Step 3: Wire ledger diagnostics**

Attach `formal_invariants` to `BucketManager.ledger_integrity_report()`.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_formal_invariants_phase8a.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-formal-invariants-phase8a.md`

- [x] **Step 1: Document Phase 8A**

Explain that the checker is shadow-only and not an enforcement gate yet.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_formal_invariants_phase8a.py tests/test_ledger_replay_phase5a.py tests/test_surface_policy_phase3.py tests/test_system_diagnostics.py -q`
Expected: selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 1: Ledger Mirror
- [x] Phase 2A: In-memory Trace Catalog Projection
- [x] Phase 2B: SQLite/FTS Shadow Projection
- [x] Phase 2C: Vector Projection Manifest
- [x] Phase 3A: Surface Policy VM
- [x] Phase 3B: Dashboard Search Surface Policy
- [x] Phase 3C: MCP Breath Search Surface Policy
- [x] Phase 4: Tombstone-only Erasure Shadow
- [x] Phase 5A: Replay Validator
- [x] Phase 5B: Deterministic Replay Property Runner
- [x] Phase 6A: Rust Replay Kernel Scaffold
- [x] Phase 7A: Policy Effective/Audit Verdicts
- [x] Phase 7B: Executable Policy Enforcement Boundary
- [x] Phase 7C: Plugin Capability Enforcement
- [x] Phase 8A: Formal Invariants Shadow Checker
