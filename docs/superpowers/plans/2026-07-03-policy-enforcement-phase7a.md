# Policy Enforcement Phase 7A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing v3 capability policy engine expose configurable audit/enforce semantics without changing runtime behavior by default.

**Architecture:** Keep `PolicyVM` verdict semantics unchanged: `allowed` remains the raw policy decision. Add `enforcement_mode` and `effective_allowed` in `PolicyEngine.evaluate()`. Default mode is `audit`, where policy denies are recorded but effectively allowed. Explicit `enforce` mode turns raw deny into effective deny for future callers.

**Tech Stack:** Python dataclasses/enums, existing v3 policy tests, pytest.

---

### Task 1: Capture Enforcement Mode Contract

**Files:**
- Modify: `tests/test_v3_policy_engine.py`
- Modify: `tests/test_v3_legacy_runtime.py`
- Modify: `tests/test_v3_decision_record.py`

- [x] **Step 1: Write failing audit-mode tests**

Assert default `PolicyEngine.default()` returns `metadata.audit_only=True`, `metadata.enforcement_mode="audit"`, and `effective_allowed=True` even when raw `allowed=False`.

- [x] **Step 2: Write failing enforce-mode tests**

Assert `PolicyEngine.default(enforcement_mode="enforce")` returns `metadata.audit_only=False`, `metadata.enforcement_mode="enforce"`, and `effective_allowed=False` when raw `allowed=False`.

- [x] **Step 3: Write failing decision-summary test**

Assert decision records preserve old `summary.policy_allowed` and also add `summary.policy_effective_allowed`.

- [x] **Step 4: Run tests to verify they fail**

Run: `pytest tests/test_v3_policy_engine.py tests/test_v3_legacy_runtime.py tests/test_v3_decision_record.py -q`

Expected: FAIL because `effective_allowed` and `enforcement_mode` do not exist yet.

### Task 2: Implement Configurable Policy Engine

**Files:**
- Modify: `src/ombrebrain/policy/engine.py`

- [x] **Step 1: Add enforcement mode field**

Add `enforcement_mode: str = "audit"` to `PolicyEngine`, accept it in `default()`, and normalize unknown values to `audit`.

- [x] **Step 2: Add effective verdict fields**

Return top-level `effective_allowed` and metadata fields `audit_only`, `enforcement_mode`, and `effective_allowed`.

- [x] **Step 3: Run policy engine tests**

Run: `pytest tests/test_v3_policy_engine.py -q`

Expected: PASS.

### Task 3: Preserve Runtime Compatibility

**Files:**
- Modify: `src/ombrebrain/decision/records.py`

- [x] **Step 1: Add decision summary field**

Add `policy_effective_allowed`, defaulting to `allowed` for old records that do not include `effective_allowed`.

- [x] **Step 2: Run runtime/decision tests**

Run: `pytest tests/test_v3_legacy_runtime.py tests/test_v3_decision_record.py -q`

Expected: PASS.

### Task 4: Document And Verify

**Files:**
- Modify: `docs/INTERNALS.md`

- [x] **Step 1: Document Phase 7A**

Explain audit vs enforce semantics and that runtime still constructs audit mode by default.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_v3_policy_engine.py tests/test_v3_legacy_runtime.py tests/test_v3_decision_record.py tests/test_v3_policy_vm.py -q`

Expected: PASS.

- [x] **Step 3: Run full regression**

Run: `pytest -q`

Expected: PASS.

- [x] **Step 4: Run whitespace diff check**

Run: `git diff --check`

Expected: no whitespace errors.

- [x] **Step 5: Stop locally**

Do not commit or push unless the user asks.
