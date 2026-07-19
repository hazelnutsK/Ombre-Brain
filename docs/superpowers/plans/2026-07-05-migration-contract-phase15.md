# Migration Preservation Contract Phase 15 Implementation Plan

**Goal:** Implement vNext §24 Migration Strategy as a shadow contract: migration must not flatten philosophical distinctions between trace kinds, states, lineage, decay, tombstones, anchors, and surfacing rules.

**Architecture:** Add `ombrebrain.maintenance.migration_contract` with source/target migration record comparison and phase-plan validation. This contract does not change existing migration engines or adapters.

**Tech Stack:** Python dataclasses, existing maintenance package, pytest.

---

### Task 1: Red Tests

**Files:**
- Add: `tests/test_migration_contract_phase15.py`

- [x] **Step 1: Write failing migration-contract tests**

Cover:
- good migration preserves trace kind, state, lineage, decay, tombstone, anchor, and surfacing rules.
- flattening dynamic/permanent/archive/anchor into generic memories is rejected.
- missing target trace is rejected.
- tombstone, lineage, decay, and surfacing rules cannot be dropped.
- Rust extraction cannot be a startup prerequisite before Python-first phases.
- report is JSON-safe and maintenance package exports contract symbols.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_migration_contract_phase15.py -q`
Expected: FAIL because migration contract symbols do not exist yet.

### Task 2: Implement Migration Contract

**Files:**
- Add: `src/ombrebrain/maintenance/migration_contract.py`
- Modify: `src/ombrebrain/maintenance/__init__.py`

- [x] **Step 1: Add migration record/report dataclasses**

Create `MigrationTraceRecord`, `MigrationPhasePlan`, `MigrationContractDecision`, and `MigrationPreservationContract`.

- [x] **Step 2: Add record preservation validation**

Compare source and target records by trace id and reject flattened or missing philosophical fields.

- [x] **Step 3: Add phase-plan validation**

Require Python-first phases before Rust extraction and reject Rust as a startup prerequisite.

- [x] **Step 4: Export maintenance symbols**

Export the new contract symbols from `ombrebrain.maintenance`.

- [x] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_migration_contract_phase15.py -q`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Modify: `docs/superpowers/plans/2026-07-05-migration-contract-phase15.md`

- [x] **Step 1: Document Phase 15**

Explain that migration preservation is diagnostic-only and does not alter existing migration engines.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_migration_contract_phase15.py tests/test_v3_migration.py tests/test_tombstone_erasure_phase4.py -q`
Expected: selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 14: Replication Contract
- [x] Phase 15: Migration Preservation Contract
