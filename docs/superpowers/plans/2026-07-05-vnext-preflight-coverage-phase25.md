# vNext Preflight Coverage Phase 25 Implementation Plan

**Goal:** Expand `VNextPreflightReportBuilder` beyond Phase 16-24 so the local preflight also summarizes the earlier heavy vNext contracts from Phase 8-15.

**Architecture:** Keep every check read-only and sample-driven. Do not scan real user bucket content, do not mutate runtime state, and do not turn this into an automatic release gate. The preflight remains a local aggregate signal.

**Tech Stack:** `VNextPreflightReportBuilder`, formal invariant checker, context compiler, tool output contract, retrieval scoring contract, observability boundary, crash recovery contract, replication contract, migration preservation contract, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_vnext_preflight_report_phase22.py`

- [x] **Step 1: Require Phase 8-15 checks in preflight**

Cover these check names:
- `formal_invariants`
- `context_serialization`
- `tool_output_humility`
- `retrieval_scoring`
- `observability_boundary`
- `crash_recovery`
- `replication_contract`
- `migration_preservation`

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_vnext_preflight_report_phase22.py::test_vnext_preflight_report_summarizes_new_contracts -q`
Result: FAIL, because the new checks did not exist yet.

### Task 2: Implement Coverage Expansion

**Files:**
- Modify: `src/ombrebrain/maintenance/report.py`

- [x] **Step 1: Add sample-driven check functions**

Each new check evaluates a known-safe representative sample through the real contract object.

- [x] **Step 2: Keep runtime behavior unchanged**

The new checks only build local report data. They do not write memory, mutate WAL, scan user bucket content, or change Dashboard routes.

- [x] **Step 3: Run focused preflight tests**

Run: `pytest tests/test_vnext_preflight_report_phase22.py -q`
Result: PASS, 7 passed.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-05-vnext-preflight-coverage-phase25.md`

- [x] **Step 1: Document Phase 25**

Explain the new preflight coverage and the safety boundary: sample-driven, read-only, not a release gate.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_vnext_preflight_report_phase22.py tests/test_v3_maintenance_report.py tests/test_system_diagnostics.py tests/test_formal_invariants_phase8a.py tests/test_context_serialization_phase8b.py tests/test_tool_output_contract_phase8d.py tests/test_retrieval_scoring_phase9.py tests/test_observability_boundary_phase12.py tests/test_crash_recovery_phase13.py tests/test_replication_contract_phase14.py tests/test_migration_contract_phase15.py -q`
Result: PASS, 83 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 710 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 24: Runtime Command Boundary Preflight
- [x] Phase 25: vNext Preflight Coverage Expansion
