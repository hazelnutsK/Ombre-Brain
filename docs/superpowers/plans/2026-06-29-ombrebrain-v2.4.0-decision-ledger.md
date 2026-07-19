# OmbreBrain v2.4.0 Decision Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add audit-only decision records and replay/explain tooling to the v2.4.0 side channel without changing legacy behavior.

**Architecture:** Create a focused `ombrebrain.decision` package for immutable decision records, an append-style ledger factory, and a read-only replay debugger. Wire the ledger into `LegacyRuntime` after policy and projection metadata are available, storing the result under `decision_record`.

**Tech Stack:** Python dataclasses, JSON-safe dictionaries, existing `ExecutionEnvelope`, `CommandPlan`, `PolicyEngine`, `ProjectionAuditRuntime`, and pytest.

---

### Task 1: Decision Record Model

**Files:**
- Create: `src/ombrebrain/decision/records.py`
- Create: `tests/test_v3_decision_record.py`

- [ ] **Step 1: Write the failing test**

```python
import json

from ombrebrain.decision.records import DecisionRecord


def test_decision_record_is_stable_and_json_safe() -> None:
    record = DecisionRecord.new(
        module="tools.breath",
        operation="breath",
        command_plan={"command_id": "cmd_1", "command_kind": "breath", "projections": []},
        policy_verdict={"allowed": True, "contract": {"command_id": "cmd_1"}},
        projection_journal={"command_id": "cmd_1", "entries": []},
        projection_observations={"command_id": "cmd_1", "observations": []},
        consistency_report={"command_id": "cmd_1", "ok": True, "issues": []},
        outcome={"ok": True, "result_type": "str"},
    )

    assert record.id.startswith("dec_")
    assert record.command_id == "cmd_1"
    assert record.summary["module"] == "tools.breath"
    assert DecisionRecord.from_dict(record.to_dict()).id == record.id
    json.dumps(record.to_dict(), ensure_ascii=False, allow_nan=False)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.10 -m pytest tests\test_v3_decision_record.py -q`
Expected: FAIL because `ombrebrain.decision` does not exist.

- [ ] **Step 3: Implement minimal model**

Create `DecisionRecord` with `new`, `to_dict`, `from_dict`, stable sha256 id generation, and JSON-safe sanitation.

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.10 -m pytest tests\test_v3_decision_record.py -q`
Expected: PASS.

### Task 2: Decision Ledger Factory

**Files:**
- Create: `src/ombrebrain/decision/ledger.py`
- Modify: `tests/test_v3_decision_record.py`

- [ ] **Step 1: Write the failing test**

```python
from ombrebrain.decision.ledger import DecisionLedger


def test_decision_ledger_builds_records_from_runtime_metadata() -> None:
    record = DecisionLedger.default().record(
        module="tools.hold",
        operation="hold",
        command_plan={"command_id": "cmd_hold", "command_kind": "hold", "projections": []},
        policy_metadata={"policy_verdict": {"allowed": False, "missing_permissions": ["memory:write"], "contract": {"command_id": "cmd_hold"}}},
        projection_metadata={
            "projection_journal": {"command_id": "cmd_hold", "entries": []},
            "projection_observations": {"command_id": "cmd_hold", "observations": []},
            "consistency_report": {"command_id": "cmd_hold", "ok": True, "issues": []},
        },
        outcome={"ok": True},
    )

    assert record.policy_verdict["allowed"] is False
    assert record.summary["consistency_ok"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.10 -m pytest tests\test_v3_decision_record.py -q`
Expected: FAIL because `DecisionLedger` does not exist.

- [ ] **Step 3: Implement ledger**

Create `DecisionLedger.default()` and `record(...)` that extracts existing metadata into `DecisionRecord`.

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.10 -m pytest tests\test_v3_decision_record.py -q`
Expected: PASS.

### Task 3: Replay Debugger

**Files:**
- Create: `src/ombrebrain/decision/replay.py`
- Create: `tests/test_v3_decision_replay.py`

- [ ] **Step 1: Write failing tests**

```python
from ombrebrain.decision.records import DecisionRecord
from ombrebrain.decision.replay import ReplayDebugger


def _record(command_id: str = "cmd_1") -> DecisionRecord:
    return DecisionRecord.new(
        module="tools.breath",
        operation="breath",
        command_plan={"command_id": command_id, "command_kind": "breath", "projections": [{"surface": "dashboard"}]},
        policy_verdict={"allowed": True, "contract": {"command_id": command_id}},
        projection_journal={"command_id": command_id, "entries": [{"surface": "dashboard"}]},
        projection_observations={"command_id": command_id, "observations": [{"surface": "dashboard", "status": "ok"}]},
        consistency_report={"command_id": command_id, "ok": True, "issues": []},
        outcome={"ok": True},
    )


def test_replay_debugger_accepts_coherent_record() -> None:
    result = ReplayDebugger.default().replay(_record())

    assert result.ok is True
    assert result.issues == ()
    assert result.explanation["policy_allowed"] is True


def test_replay_debugger_detects_command_id_mismatch() -> None:
    data = _record().to_dict()
    data["policy_verdict"]["contract"]["command_id"] = "cmd_other"

    result = ReplayDebugger.default().replay(DecisionRecord.from_dict(data))

    assert result.ok is False
    assert any("policy" in issue for issue in result.issues)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.10 -m pytest tests\test_v3_decision_replay.py -q`
Expected: FAIL because `ReplayDebugger` does not exist.

- [ ] **Step 3: Implement replay debugger**

Create `ReplayResult` and `ReplayDebugger` with `replay(record)` and structured explanation.

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.10 -m pytest tests\test_v3_decision_replay.py -q`
Expected: PASS.

### Task 4: Legacy Runtime Integration

**Files:**
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Modify: `tests/test_v3_legacy_runtime.py`

- [ ] **Step 1: Write failing integration tests**

Add tests asserting execution and tool trace metadata include `decision_record`, and that the record command id matches `command_plan`.

- [ ] **Step 2: Run tests to verify failure**

Run: `py -3.10 -m pytest tests\test_v3_legacy_runtime.py -q`
Expected: FAIL because runtime metadata does not include `decision_record`.

- [ ] **Step 3: Wire `DecisionLedger` into runtime**

Add a `decision_ledger` field, instantiate it in `from_config`, and call a best-effort `_decision_metadata(...)` helper from both event recording paths.

- [ ] **Step 4: Run integration tests**

Run: `py -3.10 -m pytest tests\test_v3_legacy_runtime.py -q`
Expected: PASS.

### Task 5: Verification and Artifacts

**Files:**
- Modify: complete artifacts summary file `v2.4.0-complete-summary-cn.md`
- Modify: complete artifacts verification file `verification.txt`
- Modify zip: complete artifacts zip archive

- [ ] **Step 1: Run focused D tests**

Run: `py -3.10 -m pytest tests\test_v3_decision_record.py tests\test_v3_decision_replay.py tests\test_v3_legacy_runtime.py tests\test_v3_legacy_tools_runtime.py -q`

- [ ] **Step 2: Run all v2.4.0 tests**

Run: `$files = Get-ChildItem tests -Filter 'test_v3_*.py' | ForEach-Object { $_.FullName }; py -3.10 -m pytest $files -q`

- [ ] **Step 3: Run full test suite**

Run: `py -3.10 -m pytest -q`

- [ ] **Step 4: Refresh artifacts**

Copy changed files into the complete artifacts folder, regenerate `v2.4.0-complete.diff`, update the Chinese summary and verification file, and compress the complete artifacts folder.

- [ ] **Step 5: Do not commit**

Stop with a status report. The user explicitly requested no direct commit, push, or release.
