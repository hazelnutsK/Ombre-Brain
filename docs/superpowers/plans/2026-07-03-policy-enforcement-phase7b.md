# Policy Enforcement Phase 7B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route v3 `policy_verdict.effective_allowed` into the legacy execution boundary so explicit enforce mode can block execution while default audit mode stays behavior-compatible.

**Architecture:** `PolicyEngine` already computes raw `allowed` and effective `effective_allowed`. This phase keeps legacy `required_permissions` as the old hard guard, adds a v3 policy guard in `LegacyExecutionPipeline`, and reads enforcement mode from runtime config. Denied enforce-mode calls are recorded as failed execution events before raising `PolicyViolation`.

**Tech Stack:** Python dataclasses, pytest, existing v3 legacy runtime and decision ledger.

---

### Task 1: Configurable Runtime Enforcement Mode

**Files:**
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Test: `tests/test_v3_legacy_runtime.py`

- [x] **Step 1: Write the failing test**

Add assertions that `LegacyRuntime.from_config({"policy": {"enforcement_mode": "enforce"}})` creates a policy engine whose metadata reports `enforce`.

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_v3_legacy_runtime.py::test_legacy_runtime_reads_policy_enforcement_mode_from_config -q`
Expected before implementation: FAIL because runtime still constructs `PolicyEngine.default()` in audit mode.

- [x] **Step 3: Write minimal implementation**

Parse `policy.enforcement_mode`, falling back to top-level `policy_enforcement_mode`, then pass it to `PolicyEngine.default(..., enforcement_mode=mode)`.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_v3_legacy_runtime.py::test_legacy_runtime_reads_policy_enforcement_mode_from_config -q`
Expected after implementation: PASS.

### Task 2: Enforce-Mode Pipeline Guard

**Files:**
- Modify: `src/ombrebrain/app/execution.py`
- Test: `tests/test_v3_legacy_execution_pipeline.py`

- [x] **Step 1: Write the failing tests**

Add one test proving default audit mode still executes a raw policy deny, and one test proving enforce mode raises `PolicyViolation`, does not call the handler, and records a failed trace event.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_v3_legacy_execution_pipeline.py::test_execution_pipeline_audit_mode_keeps_policy_deny_non_blocking tests/test_v3_legacy_execution_pipeline.py::test_execution_pipeline_enforce_mode_blocks_effective_policy_deny_and_records_trace -q`
Expected before implementation: enforce test FAILS because the handler still runs.

- [x] **Step 3: Write minimal implementation**

In `LegacyExecutionPipeline`, evaluate v3 policy after old preflight validation. If a verdict exists and `effective_allowed` is `False`, record a failed `ExecutionOutcome` and raise `PolicyViolation` before entering the handler.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_v3_legacy_execution_pipeline.py::test_execution_pipeline_audit_mode_keeps_policy_deny_non_blocking tests/test_v3_legacy_execution_pipeline.py::test_execution_pipeline_enforce_mode_blocks_effective_policy_deny_and_records_trace -q`
Expected after implementation: PASS.

### Task 3: Documentation and Regression Verification

**Files:**
- Modify: `docs/INTERNALS.md`

- [x] **Step 1: Document the executable policy boundary**

Add a Phase 7B note explaining audit default, enforce config keys, and failure recording.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_v3_policy_engine.py tests/test_v3_legacy_runtime.py tests/test_v3_legacy_execution_pipeline.py tests/test_v3_decision_record.py -q`
Expected: all selected tests pass.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Expected: full suite passes.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Expected: exit 0; Windows line-ending warnings may appear but no whitespace errors.

### Status

- [x] Phase 1: Ledger Mirror
- [x] Phase 2: Rebuildable Projection
- [x] Phase 3: Surface Policy VM
- [x] Phase 4: Tombstone-only Erasure Shadow
- [x] Phase 5A: Replay Validator
- [x] Phase 5B: Deterministic Replay Property Runner
- [x] Phase 6A: Rust Replay Kernel Scaffold
- [x] Phase 7A: Policy Effective/Audit Verdicts
- [x] Phase 7B: Executable Policy Enforcement Boundary
