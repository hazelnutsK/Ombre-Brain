# OmbreBrain v2.4.0 Projection Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a v2.4.0 shadow projection runtime and consistency auditor that attach projection journal metadata to legacy execution/tool events without changing legacy behavior.

**Architecture:** Add a focused `ombrebrain.projection` package with immutable journal data structures, a deterministic projection runtime, and a shape-level consistency auditor. Wire `LegacyRuntime` to record projection metadata best-effort after command planning.

**Tech Stack:** Python dataclasses, existing `CommandPlan` / `ProjectionStep` domain model, pytest.

---

### Task 1: Projection Journal Model

**Files:**
- Create: `src/ombrebrain/projection/__init__.py`
- Create: `src/ombrebrain/projection/journal.py`
- Test: `tests/test_v3_projection_runtime.py`

- [ ] **Step 1: Write the failing test**

```python
from ombrebrain.domain.commands import CommandKind, MemoryCommand, MemoryCommandRouter
from ombrebrain.projection.runtime import ProjectionRuntime


def test_projection_runtime_creates_one_journal_entry_per_plan_step() -> None:
    command = MemoryCommand.new(kind=CommandKind.HOLD, payload={"bucket_id": "b1"})
    plan = MemoryCommandRouter.default().plan(command)

    journal = ProjectionRuntime.default().project(plan)

    assert journal.command_id == plan.command_id
    assert len(journal.entries) == len(plan.projections)
    assert journal.entries[0].projection_kind == plan.projections[0].kind
    assert journal.entries[0].status.value == "planned"
    assert journal.to_dict()["entries"][0]["checksum"].startswith("proj_")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.10 -m pytest tests\test_v3_projection_runtime.py -q`
Expected: FAIL because `ombrebrain.projection` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create immutable `ProjectionStatus`, `ProjectionJournalEntry`, and `ProjectionJournal` with JSON-safe `to_dict()` methods and stable sha256 checksums.

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.10 -m pytest tests\test_v3_projection_runtime.py -q`
Expected: PASS.

### Task 2: Projection Runtime Determinism

**Files:**
- Modify: `src/ombrebrain/projection/runtime.py`
- Test: `tests/test_v3_projection_runtime.py`

- [ ] **Step 1: Write failing tests**

```python
def test_projection_runtime_checksums_are_deterministic() -> None:
    command = MemoryCommand.new(kind=CommandKind.TRACE, payload={"bucket_id": "b1", "delete": True})
    plan = MemoryCommandRouter.default().plan(command)

    first = ProjectionRuntime.default().project(plan)
    second = ProjectionRuntime.default().project(plan)

    assert [entry.checksum for entry in first.entries] == [entry.checksum for entry in second.entries]


def test_projection_runtime_does_not_mutate_command_plan() -> None:
    command = MemoryCommand.new(kind=CommandKind.BREATH, payload={"query": "x"})
    plan = MemoryCommandRouter.default().plan(command)
    before = plan.to_dict()

    ProjectionRuntime.default().project(plan)

    assert plan.to_dict() == before
```

- [ ] **Step 2: Run tests to verify they fail if runtime is incomplete**

Run: `py -3.10 -m pytest tests\test_v3_projection_runtime.py -q`

- [ ] **Step 3: Implement deterministic `ProjectionRuntime.project()`**

Use plan data only, default created time `1970-01-01T00:00:00+00:00`, metadata with `step_index` and `policy_tags`, and immutable tuples.

- [ ] **Step 4: Run projection runtime tests**

Run: `py -3.10 -m pytest tests\test_v3_projection_runtime.py -q`
Expected: PASS.

### Task 3: Consistency Auditor

**Files:**
- Create: `src/ombrebrain/projection/auditor.py`
- Test: `tests/test_v3_consistency_auditor.py`

- [ ] **Step 1: Write failing tests**

```python
from dataclasses import replace

from ombrebrain.domain.commands import CommandKind, MemoryCommand, MemoryCommandRouter
from ombrebrain.projection.auditor import ConsistencyAuditor
from ombrebrain.projection.journal import ProjectionJournal
from ombrebrain.projection.runtime import ProjectionRuntime


def _trace_plan():
    command = MemoryCommand.new(kind=CommandKind.TRACE, payload={"bucket_id": "b1", "delete": True})
    return MemoryCommandRouter.default().plan(command)


def test_consistency_auditor_accepts_matching_journal() -> None:
    plan = _trace_plan()
    journal = ProjectionRuntime.default().project(plan)

    report = ConsistencyAuditor.default().audit(plan, journal)

    assert report.ok is True
    assert report.expected_count == len(plan.projections)
    assert report.observed_count == len(journal.entries)
    assert report.issues == ()


def test_consistency_auditor_reports_missing_projection() -> None:
    plan = _trace_plan()
    journal = ProjectionRuntime.default().project(plan)
    journal = ProjectionJournal(command_id=journal.command_id, entries=journal.entries[:-1], created_at=journal.created_at)

    report = ConsistencyAuditor.default().audit(plan, journal)

    assert report.ok is False
    assert any(issue.code == "missing_projection" for issue in report.issues)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.10 -m pytest tests\test_v3_consistency_auditor.py -q`
Expected: FAIL because `ConsistencyAuditor` does not exist.

- [ ] **Step 3: Implement auditor**

Compare projection keys `(kind, surface, action)`, report missing, duplicate, unexpected, command id mismatch, and non-planned status issues.

- [ ] **Step 4: Run auditor tests**

Run: `py -3.10 -m pytest tests\test_v3_consistency_auditor.py -q`
Expected: PASS.

### Task 4: Legacy Runtime Integration

**Files:**
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Test: `tests/test_v3_legacy_runtime.py`

- [ ] **Step 1: Write failing tests**

```python
from ombrebrain.app.execution import ExecutionEnvelope, ExecutionOutcome


def test_legacy_runtime_execution_event_includes_projection_metadata(tmp_path) -> None:
    runtime = LegacyRuntime.from_config({"buckets_dir": str(tmp_path / "buckets")})
    envelope = ExecutionEnvelope(module="tools.hold", operation="hold", payload={"bucket_id": "b1"})
    outcome = ExecutionOutcome(ok=True, phase_history=("completed",), result_type="str")

    runtime.record_execution_event(envelope, outcome)

    metadata = runtime.fabric.replay_events()[0].metadata
    assert metadata["projection_journal"]["command_id"] == metadata["command_plan"]["command_id"]
    assert metadata["consistency_report"]["ok"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.10 -m pytest tests\test_v3_legacy_runtime.py -q`
Expected: FAIL because projection metadata is absent.

- [ ] **Step 3: Wire projection runtime into `LegacyRuntime`**

Add `projection_runtime` and `consistency_auditor` fields, instantiate defaults in `from_config()`, and attach projection metadata inside `record_execution_event()` and `record_tool_event()` best-effort.

- [ ] **Step 4: Run affected tests**

Run: `py -3.10 -m pytest tests\test_v3_legacy_runtime.py tests\test_v3_legacy_tools_runtime.py -q`
Expected: PASS.

### Task 5: Final Verification And Artifacts

**Files:**
- Update: `docs/superpowers/plans/2026-06-29-ombrebrain-v2.4.0-projection-runtime.md`
- Update artifacts folder and zip after tests pass.

- [ ] **Step 1: Run projection and affected tests**

Run: `py -3.10 -m pytest tests\test_v3_projection_runtime.py tests\test_v3_consistency_auditor.py tests\test_v3_legacy_runtime.py tests\test_v3_legacy_tools_runtime.py -q`

- [ ] **Step 2: Run all v2.4.0 tests**

Run: `$files = Get-ChildItem tests -Filter 'test_v3_*.py' | ForEach-Object { $_.FullName }; py -3.10 -m pytest $files -q`

- [ ] **Step 3: Run full suite**

Run: `py -3.10 -m pytest -q`

- [ ] **Step 4: Refresh artifacts**

Regenerate `OmbreBrain-v2.4.0-complete-artifacts`, `v2.4.0-complete.diff`, `v2.4.0-complete-summary-cn.md`, `verification.txt`, and `OmbreBrain-v2.4.0-complete-artifacts.zip`.

- [ ] **Step 5: No commit**

Do not run `git commit`, `git push`, or release commands because the user explicitly requested no direct submission.
