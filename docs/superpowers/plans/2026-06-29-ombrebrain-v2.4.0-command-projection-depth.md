# OmbreBrain v2.4.0 Command Projection Depth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a command/policy/projection domain layer under v2.4.0 while preserving existing OB behavior.

**Architecture:** Legacy execution envelopes continue to wrap old runtime calls. A new domain router maps those envelopes into deterministic memory commands and projection plans, then records the plan in internal v2.4.0 trace metadata. The old handler result and exceptions remain unchanged.

**Tech Stack:** Python 3.10 dataclasses/enums, pytest, existing `src/ombrebrain/` v2.4.0 package.

---

### Task 1: Domain Command Router

**Files:**
- Create: `src/ombrebrain/domain/commands.py`
- Create: `src/ombrebrain/domain/__init__.py`
- Test: `tests/test_v3_memory_command_router.py`

- [ ] **Step 1: Write failing tests**

Create tests for deterministic command ids, hold/breath/trace projection plans,
and no visible legacy output dependency.

- [ ] **Step 2: Run failing tests**

Run: `py -3.10 -m pytest tests/test_v3_memory_command_router.py -q`
Expected: import failure for `ombrebrain.domain.commands`.

- [ ] **Step 3: Implement command router**

Define `CommandKind`, `ProjectionKind`, `MemoryCommand`, `ProjectionPlan`,
`CommandPlan`, and `MemoryCommandRouter`.

- [ ] **Step 4: Run tests**

Run: `py -3.10 -m pytest tests/test_v3_memory_command_router.py -q`
Expected: all tests pass.

### Task 2: Memory Invariants

**Files:**
- Create: `src/ombrebrain/domain/invariants.py`
- Test: `tests/test_v3_memory_invariants.py`

- [ ] **Step 1: Write failing tests**

Cover permanent, feel, plan, letter, and trace-delete invariants.

- [ ] **Step 2: Run failing tests**

Run: `py -3.10 -m pytest tests/test_v3_memory_invariants.py -q`
Expected: import failure for `ombrebrain.domain.invariants`.

- [ ] **Step 3: Implement invariant checker**

Define immutable `InvariantVerdict` and `MemoryInvariantSet`.

- [ ] **Step 4: Run tests**

Run: `py -3.10 -m pytest tests/test_v3_memory_invariants.py -q`
Expected: all tests pass.

### Task 3: Legacy Command Bridge

**Files:**
- Create: `src/ombrebrain/app/command_bridge.py`
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Test: `tests/test_v3_legacy_command_bridge.py`

- [ ] **Step 1: Write failing tests**

Cover mapping `tools.hold`, `tools.breath`, `tools.trace`, `web.*`, and
`github_sync` execution envelopes to command plans.

- [ ] **Step 2: Run failing tests**

Run: `py -3.10 -m pytest tests/test_v3_legacy_command_bridge.py -q`
Expected: import failure for `ombrebrain.app.command_bridge`.

- [ ] **Step 3: Implement bridge and runtime metadata**

Add `LegacyCommandBridge.plan_from_envelope()` and include `command_plan` in
`LegacyRuntime.record_execution_event()` metadata.

- [ ] **Step 4: Run tests**

Run: `py -3.10 -m pytest tests/test_v3_legacy_command_bridge.py -q`
Expected: all tests pass.

### Task 4: Verification and Artifacts

**Files:**
- Update: `C:/Users/孙立人/Desktop/OmbreBrain-v2.4.0-总文件夹/OmbreBrain-v2.4.0-complete-artifacts`
- Update: `C:/Users/孙立人/Desktop/OmbreBrain-v2.4.0-总文件夹/OmbreBrain-v2.4.0-complete-artifacts.zip`

- [ ] **Step 1: Run target tests**

Run command/projection tests plus affected legacy runtime tests.

- [ ] **Step 2: Run all v2.4.0 tests**

Run: `$files = Get-ChildItem tests -Filter 'test_v3_*.py' | ForEach-Object { $_.FullName }; py -3.10 -m pytest $files -q`

- [ ] **Step 3: Run full suite**

Run: `py -3.10 -m pytest -q`

- [ ] **Step 4: Refresh artifacts**

Regenerate changed-files, full diff, Chinese summary, verification record, and zip.
