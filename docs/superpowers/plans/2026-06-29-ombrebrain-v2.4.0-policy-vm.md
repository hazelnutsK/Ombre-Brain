# OmbreBrain v2.4.0 Policy VM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an audit-only Policy VM and Capability Contract Engine that attach policy verdict metadata to v2.4.0 events without changing legacy behavior.

**Architecture:** Add policy contract, VM, and engine modules under `src/ombrebrain/policy/`. The engine compiles existing module profiles, execution envelopes, and command plans into a small instruction program, then returns a JSON-safe verdict for v2.4.0 metadata.

**Tech Stack:** Python dataclasses, Enum, existing `ExecutionEnvelope`, `CommandPlan`, `LegacyModuleProfile`, pytest.

---

### Task 1: Policy Contracts

**Files:**
- Create: `src/ombrebrain/policy/contracts.py`
- Test: `tests/test_v3_policy_contracts.py`

- [ ] **Step 1: Write failing tests**

```python
from ombrebrain.domain.commands import CommandKind
from ombrebrain.policy.contracts import CapabilityContract, SurfaceAccess, SurfaceAccessVerdict, VerdictSeverity


def test_capability_contract_is_json_safe() -> None:
    contract = CapabilityContract(
        command_id="cmd_1",
        command_kind=CommandKind.HOLD,
        module="tools.hold",
        operation="hold",
        permissions=("mcp:call",),
        required_permissions=("mcp:call",),
        capabilities=("tools.hold",),
        side_effects=("bucket-create",),
        protected_surfaces=("tool-payload-privacy",),
        writes_memory=True,
        projection_surfaces=("buckets",),
    )

    assert contract.to_dict()["command_kind"] == "hold"
    assert contract.to_dict()["permissions"] == ["mcp:call"]


def test_surface_access_verdict_serializes_missing_permissions() -> None:
    verdict = SurfaceAccessVerdict(
        allowed=False,
        severity=VerdictSeverity.DENY,
        reasons=("missing permission",),
        required_permissions=("memory:write",),
        missing_permissions=("memory:write",),
    )

    assert verdict.to_dict()["allowed"] is False
    assert verdict.to_dict()["severity"] == "deny"
```

- [ ] **Step 2: Run test**

Run: `py -3.10 -m pytest tests\test_v3_policy_contracts.py -q`
Expected: FAIL because `contracts.py` does not exist.

- [ ] **Step 3: Implement contracts**

Create immutable `SurfaceAccess`, `CapabilityContract`, `VerdictSeverity`, and `SurfaceAccessVerdict` with JSON-safe `to_dict()` methods.

- [ ] **Step 4: Run test**

Run: `py -3.10 -m pytest tests\test_v3_policy_contracts.py -q`
Expected: PASS.

### Task 2: Policy VM

**Files:**
- Create: `src/ombrebrain/policy/vm.py`
- Test: `tests/test_v3_policy_vm.py`

- [ ] **Step 1: Write failing tests**

```python
from ombrebrain.domain.commands import CommandKind
from ombrebrain.policy.contracts import CapabilityContract
from ombrebrain.policy.vm import PolicyInstruction, PolicyOpcode, PolicyProgram, PolicyVM


def _contract(**overrides):
    data = dict(
        command_id="cmd_1",
        command_kind=CommandKind.HOLD,
        module="tools.hold",
        operation="hold",
        permissions=("mcp:call",),
        required_permissions=("mcp:call",),
        capabilities=("tools.hold",),
        side_effects=(),
        protected_surfaces=(),
        writes_memory=False,
        projection_surfaces=("dashboard",),
    )
    data.update(overrides)
    return CapabilityContract(**data)


def test_policy_vm_allows_matching_permissions() -> None:
    program = PolicyProgram((PolicyInstruction(PolicyOpcode.REQUIRE_PERMISSION, "mcp:call"),))

    verdict = PolicyVM.default().evaluate(program, _contract())

    assert verdict.allowed is True


def test_policy_vm_denies_missing_permission() -> None:
    program = PolicyProgram((PolicyInstruction(PolicyOpcode.REQUIRE_PERMISSION, "memory:write"),))

    verdict = PolicyVM.default().evaluate(program, _contract())

    assert verdict.allowed is False
    assert "memory:write" in verdict.missing_permissions
```

- [ ] **Step 2: Run test**

Run: `py -3.10 -m pytest tests\test_v3_policy_vm.py -q`
Expected: FAIL because `vm.py` does not exist.

- [ ] **Step 3: Implement VM**

Add `PolicyOpcode`, `PolicyInstruction`, `PolicyProgram`, and `PolicyVM.evaluate()`.

- [ ] **Step 4: Run test**

Run: `py -3.10 -m pytest tests\test_v3_policy_vm.py -q`
Expected: PASS.

### Task 3: Policy Engine

**Files:**
- Create: `src/ombrebrain/policy/engine.py`
- Modify: `src/ombrebrain/policy/__init__.py`
- Test: `tests/test_v3_policy_engine.py`

- [ ] **Step 1: Write failing tests**

```python
from ombrebrain.app.execution import ExecutionEnvelope
from ombrebrain.app.profiles import build_default_legacy_profiles
from ombrebrain.domain.commands import CommandKind, MemoryCommand, MemoryCommandRouter
from ombrebrain.policy.engine import PolicyEngine


def test_policy_engine_evaluates_command_plan_from_envelope() -> None:
    command = MemoryCommand.new(kind=CommandKind.HOLD, payload={"content_length": 5})
    plan = MemoryCommandRouter.default().plan(command)
    envelope = ExecutionEnvelope(module="tools.hold", operation="hold", permissions=("mcp:call",))

    verdict = PolicyEngine.default(build_default_legacy_profiles()).evaluate(envelope, plan)

    assert verdict["contract"]["command_kind"] == "hold"
    assert verdict["allowed"] in (True, False)
    assert "tool-payload-privacy" in verdict["contract"]["protected_surfaces"]
```

- [ ] **Step 2: Run test**

Run: `py -3.10 -m pytest tests\test_v3_policy_engine.py -q`
Expected: FAIL because `engine.py` does not exist.

- [ ] **Step 3: Implement engine**

Build contracts from envelope, command plan, profile registry, projection surfaces, and compile program instructions.

- [ ] **Step 4: Run test**

Run: `py -3.10 -m pytest tests\test_v3_policy_engine.py -q`
Expected: PASS.

### Task 4: Legacy Runtime Integration

**Files:**
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Test: `tests/test_v3_legacy_runtime.py`

- [ ] **Step 1: Write failing tests**

```python
def test_legacy_runtime_execution_event_includes_policy_verdict(tmp_path) -> None:
    runtime = LegacyRuntime.from_config({"buckets_dir": str(tmp_path / "buckets")})
    envelope = ExecutionEnvelope(module="tools.hold", operation="hold", payload={"content_length": 5})
    outcome = ExecutionOutcome(ok=True, phase_history=("completed",), result_type="str")

    runtime.record_execution_event(envelope, outcome)

    metadata = runtime.fabric.replay_events()[0].metadata
    assert metadata["policy_verdict"]["contract"]["command_kind"] == "hold"
```

- [ ] **Step 2: Run test**

Run: `py -3.10 -m pytest tests\test_v3_legacy_runtime.py -q`
Expected: FAIL because `policy_verdict` is absent.

- [ ] **Step 3: Wire PolicyEngine into runtime**

Add `policy_engine` field and include `policy_verdict` metadata for execution and tool events. Policy errors become `policy_error` metadata.

- [ ] **Step 4: Run affected tests**

Run: `py -3.10 -m pytest tests\test_v3_policy_contracts.py tests\test_v3_policy_vm.py tests\test_v3_policy_engine.py tests\test_v3_legacy_runtime.py -q`
Expected: PASS.

### Task 5: Verification And Artifacts

**Files:**
- Update artifacts folder and zip after tests pass.

- [ ] **Step 1: Run C local tests**

Run: `py -3.10 -m pytest tests\test_v3_policy_contracts.py tests\test_v3_policy_vm.py tests\test_v3_policy_engine.py tests\test_v3_legacy_runtime.py tests\test_v3_legacy_tools_runtime.py -q`

- [ ] **Step 2: Run all v2.4.0 tests**

Run: `$files = Get-ChildItem tests -Filter 'test_v3_*.py' | ForEach-Object { $_.FullName }; py -3.10 -m pytest $files -q`

- [ ] **Step 3: Run full suite**

Run: `py -3.10 -m pytest -q`

- [ ] **Step 4: Refresh artifacts**

Regenerate `OmbreBrain-v2.4.0-complete-artifacts`, `v2.4.0-complete.diff`, `v2.4.0-complete-summary-cn.md`, `verification.txt`, and `OmbreBrain-v2.4.0-complete-artifacts.zip`.

- [ ] **Step 5: Do not commit**

Do not run `git commit`, `git push`, or release commands.
