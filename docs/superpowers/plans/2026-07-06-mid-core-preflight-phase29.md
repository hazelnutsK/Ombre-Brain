# Mid Core Preflight Phase 29 Implementation Plan

**Goal:** Add vNext preflight sample coverage for the next coverage gaps after Phase 28: deterministic ledger property replay, Rust replay kernel scaffold, policy verdict semantics, plugin capability enforcement, and the preflight report itself.

**Architecture:** Keep checks deterministic and local. They must not read real user buckets, mutate the vault, require live network access, or make Rust toolchain availability a startup condition.

**Tech Stack:** `LedgerReplayPropertyRunner`, Rust kernel scaffold files, `PolicyEngine`, `PluginRuntime`, `VNextPreflightReportBuilder`, `VNextCoverageMatrix`, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_vnext_preflight_report_phase22.py`

- [x] **Step 1: Require mid-core checks**

Require these checks in vNext preflight:
- `ledger_property`
- `rust_kernel_scaffold`
- `policy_verdicts`
- `plugin_capability_enforcement`
- `preflight_report_self`

- [x] **Step 2: Require gap progress**

Assert Phase 5B, Phase 6A, Phase 7A, Phase 7C, and Phase 22 are no longer listed in `preflight_gaps`, and the first `next_preflight_targets` entry becomes `phase_23`.

- [x] **Step 3: Run focused red/green test**

Run: `pytest tests/test_vnext_preflight_report_phase22.py::test_vnext_preflight_report_summarizes_new_contracts -q`
Result: PASS after implementation, 1 passed.

### Task 2: Implement Mid-Core Checks

**Files:**
- Modify: `src/ombrebrain/maintenance/report.py`
- Modify: `src/ombrebrain/maintenance/vnext_coverage.py`

- [x] **Step 1: Add deterministic property preflight**

Run `LedgerReplayPropertyRunner.default().run(seed=20260706, cases=5, max_events=20)`.

- [x] **Step 2: Add Rust scaffold preflight**

Verify `kernel/rust/ombre-kernel/Cargo.toml` and `src/lib.rs` export the replay contract types without requiring cargo.

- [x] **Step 3: Add policy verdict preflight**

Verify audit mode is non-blocking, enforce mode blocks missing required permission, and read verdicts remain JSON-safe.

- [x] **Step 4: Add plugin capability enforcement preflight**

Verify sandbox rejection, audit-mode missing capability recording, enforce-mode block, and permission-granted execution.

- [x] **Step 5: Add preflight self-check and coverage mapping**

Add `preflight_report_self`, then map Phase 5B, 6A, 7A, 7C, and 22 to their check names.

- [x] **Step 6: Fix coverage matrix self-coverage**

Treat `vnext_coverage` as an available check while the matrix evaluates itself, so Phase 26 is not incorrectly listed as a remaining preflight gap.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-mid-core-preflight-phase29.md`

- [x] **Step 1: Document Phase 29**

Explain that the new checks are deterministic, local, and sample-only.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_vnext_preflight_report_phase22.py tests/test_v3_maintenance_report.py tests/test_system_diagnostics.py tests/test_ledger_property_phase5b.py tests/test_rust_kernel_phase6a.py tests/test_v3_policy_engine.py tests/test_v3_plugin_runtime.py -q`
Result: PASS, 32 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 28: Early Core Preflight Samples
- [x] Phase 29: Mid Core Preflight Samples
