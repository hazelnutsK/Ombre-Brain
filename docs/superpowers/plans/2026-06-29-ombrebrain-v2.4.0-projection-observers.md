# OmbreBrain v2.4.0 Projection Observers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add read-only projection observers and real-state consistency audit metadata without changing OmbreBrain legacy behavior.

**Architecture:** Add immutable observation models, read-only observer classes, and an audit runtime under `ombrebrain.projection`. Extend the existing auditor and legacy runtime so event metadata can include observations while all observer failures remain best effort.

**Tech Stack:** Python dataclasses, existing `CommandPlan`, `ProjectionJournal`, pytest.

---

### Task 1: Observation Model

**Files:**
- Create: `src/ombrebrain/projection/observation.py`
- Test: `tests/test_v3_projection_observers.py`

- [ ] **Step 1: Write failing tests**

```python
from ombrebrain.domain.commands import ProjectionKind
from ombrebrain.projection.observation import ObservationStatus, ProjectionObservation, ProjectionObservationSet


def test_projection_observation_is_json_safe_and_keyed() -> None:
    obs = ProjectionObservation(
        projection_kind=ProjectionKind.BUCKET_MARKDOWN,
        surface="buckets",
        action="patch",
        status=ObservationStatus.OBSERVED,
        subject="bucket-1",
        metadata={"exists": True},
    )

    assert obs.key == ("bucket_markdown", "buckets", "patch")
    assert obs.to_dict()["status"] == "observed"


def test_projection_observation_set_serializes_entries() -> None:
    obs = ProjectionObservation(
        projection_kind=ProjectionKind.DASHBOARD_STATE,
        surface="dashboard",
        action="refresh",
        status=ObservationStatus.UNKNOWN,
    )
    obs_set = ProjectionObservationSet(command_id="cmd_1", observations=(obs,))

    assert obs_set.to_dict()["command_id"] == "cmd_1"
    assert obs_set.to_dict()["observations"][0]["projection_kind"] == "dashboard_state"
```

- [ ] **Step 2: Run test**

Run: `py -3.10 -m pytest tests\test_v3_projection_observers.py -q`
Expected: FAIL because `observation.py` does not exist.

- [ ] **Step 3: Implement model**

Add `ObservationStatus`, `ProjectionObservation`, and `ProjectionObservationSet`.

- [ ] **Step 4: Run test**

Run: `py -3.10 -m pytest tests\test_v3_projection_observers.py -q`
Expected: PASS for model tests.

### Task 2: Read-Only Observers And Registry

**Files:**
- Create: `src/ombrebrain/projection/observers.py`
- Test: `tests/test_v3_projection_observers.py`

- [ ] **Step 1: Write failing tests**

```python
import pytest

from ombrebrain.domain.commands import CommandKind, MemoryCommand, MemoryCommandRouter
from ombrebrain.projection.observation import ObservationStatus
from ombrebrain.projection.observers import ProjectionObserverRegistry
from ombrebrain.projection.runtime import ProjectionRuntime


class FakeBucketManager:
    def __init__(self, bucket):
        self.bucket = bucket
        self.calls = []

    async def get(self, bucket_id):
        self.calls.append(("get", bucket_id))
        return self.bucket


@pytest.mark.asyncio
async def test_observer_registry_reads_bucket_without_writing() -> None:
    command = MemoryCommand.new(kind=CommandKind.TRACE, payload={"bucket_id": "bucket-1"})
    plan = MemoryCommandRouter.default().plan(command)
    journal = ProjectionRuntime.default().project(plan)
    bucket_mgr = FakeBucketManager({"id": "bucket-1", "metadata": {"type": "dynamic"}})

    obs_set = await ProjectionObserverRegistry.default(bucket_manager=bucket_mgr).observe(plan, journal)

    assert any(obs.status == ObservationStatus.OBSERVED for obs in obs_set.observations)
    assert bucket_mgr.calls == [("get", "bucket-1")]
```

- [ ] **Step 2: Run observer tests**

Run: `py -3.10 -m pytest tests\test_v3_projection_observers.py -q`
Expected: FAIL because `observers.py` does not exist.

- [ ] **Step 3: Implement observers**

Add bucket, vector, dashboard, deployment observers and a registry. Observers only call read methods.

- [ ] **Step 4: Run observer tests**

Run: `py -3.10 -m pytest tests\test_v3_projection_observers.py -q`
Expected: PASS.

### Task 3: Auditor Observation Support

**Files:**
- Modify: `src/ombrebrain/projection/auditor.py`
- Test: `tests/test_v3_consistency_auditor.py`

- [ ] **Step 1: Write failing tests**

```python
from ombrebrain.projection.observation import ObservationStatus, ProjectionObservation, ProjectionObservationSet


def test_consistency_auditor_accepts_matching_observations() -> None:
    plan = _trace_plan()
    journal = ProjectionRuntime.default().project(plan)
    observations = ProjectionObservationSet(
        command_id=plan.command_id,
        observations=tuple(
            ProjectionObservation(
                projection_kind=entry.projection_kind,
                surface=entry.surface,
                action=entry.action,
                status=ObservationStatus.OBSERVED,
            )
            for entry in journal.entries
        ),
    )

    report = ConsistencyAuditor.default().audit_with_observations(plan, journal, observations)

    assert report.ok is True


def test_consistency_auditor_reports_missing_observation() -> None:
    plan = _trace_plan()
    journal = ProjectionRuntime.default().project(plan)
    observations = ProjectionObservationSet(command_id=plan.command_id, observations=())

    report = ConsistencyAuditor.default().audit_with_observations(plan, journal, observations)

    assert report.ok is False
    assert any(issue.code == "missing_observation" for issue in report.issues)
```

- [ ] **Step 2: Run auditor tests**

Run: `py -3.10 -m pytest tests\test_v3_consistency_auditor.py -q`
Expected: FAIL because `audit_with_observations` does not exist.

- [ ] **Step 3: Implement audit support**

Add observation comparison rules while preserving existing `audit()` behavior.

- [ ] **Step 4: Run auditor tests**

Run: `py -3.10 -m pytest tests\test_v3_consistency_auditor.py -q`
Expected: PASS.

### Task 4: Legacy Runtime Integration

**Files:**
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Test: `tests/test_v3_legacy_runtime.py`

- [ ] **Step 1: Write failing tests**

```python
def test_legacy_runtime_execution_event_includes_projection_observations(tmp_path) -> None:
    runtime = LegacyRuntime.from_config({"buckets_dir": str(tmp_path / "buckets")})
    envelope = ExecutionEnvelope(module="tools.breath", operation="breath", payload={"query": "x"})
    outcome = ExecutionOutcome(ok=True, phase_history=("completed",), result_type="str")

    runtime.record_execution_event(envelope, outcome)

    metadata = runtime.fabric.replay_events()[0].metadata
    assert "projection_observations" in metadata
    assert "observations" in metadata["projection_observations"]
```

- [ ] **Step 2: Run runtime tests**

Run: `py -3.10 -m pytest tests\test_v3_legacy_runtime.py -q`
Expected: FAIL because observations are absent.

- [ ] **Step 3: Wire audit runtime**

Add `ProjectionAuditRuntime` and observer registry to `LegacyRuntime`; include observations in metadata best-effort.

- [ ] **Step 4: Run affected tests**

Run: `py -3.10 -m pytest tests\test_v3_projection_observers.py tests\test_v3_consistency_auditor.py tests\test_v3_legacy_runtime.py -q`
Expected: PASS.

### Task 5: Verification And Artifacts

**Files:**
- Update artifacts folder and zip after tests pass.

- [ ] **Step 1: Run local B tests**

Run: `py -3.10 -m pytest tests\test_v3_projection_observers.py tests\test_v3_consistency_auditor.py tests\test_v3_legacy_runtime.py tests\test_v3_legacy_tools_runtime.py -q`

- [ ] **Step 2: Run all v2.4.0 tests**

Run: `$files = Get-ChildItem tests -Filter 'test_v3_*.py' | ForEach-Object { $_.FullName }; py -3.10 -m pytest $files -q`

- [ ] **Step 3: Run full suite**

Run: `py -3.10 -m pytest -q`

- [ ] **Step 4: Refresh artifacts**

Regenerate `OmbreBrain-v2.4.0-complete-artifacts`, `v2.4.0-complete.diff`, `v2.4.0-complete-summary-cn.md`, `verification.txt`, and `OmbreBrain-v2.4.0-complete-artifacts.zip`.

- [ ] **Step 5: Do not commit**

Do not run `git commit`, `git push`, or release commands.
