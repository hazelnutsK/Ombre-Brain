# OmbreBrain v2.4.0 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working v2.4.0 foundation: a new `ombrebrain` package with typed memory events, Kernel capability registry, append-only WAL, single-node consensus adapter, and compatibility adapters for existing bucket data.

**Architecture:** This plan introduces the v2.4.0 architecture without breaking the v2.3.22 runtime. Existing top-level modules stay in place while the new `src/ombrebrain/` package is added beside them. The first slice stores AI-native memory events through a WAL-backed Memory Fabric and exposes a consensus interface that later Raft work can replace.

**Tech Stack:** Python standard library, dataclasses, pathlib, hashlib, json, pytest. No new runtime dependency is required in this foundation slice.

---

## Scope Check

The v2.4.0 spec covers several independent subsystems. This plan implements only the foundation slice:

- package skeleton
- product constitution metadata
- typed memory event schema
- Kernel context and capability registry
- append-only WAL with checksum chain
- Memory Fabric replay/query API
- single-node consensus adapter
- compatibility adapter for existing bucket Markdown files

Separate follow-up plans should cover:

- three-node Raft transport and election
- hot update manifest rollout
- capability migration for MCP/web/OAuth/deployment
- license and README release changes
- full v2.3.22-to-v2.4.0 data migration tool

## File Structure

Create:

- `src/ombrebrain/__init__.py` - public package exports.
- `src/ombrebrain/version.py` - version reader compatible with root `VERSION`.
- `src/ombrebrain/protocol/__init__.py` - protocol package marker.
- `src/ombrebrain/protocol/schemas.py` - MemoryEvent and shared schema types.
- `src/ombrebrain/kernel/__init__.py` - kernel package marker.
- `src/ombrebrain/kernel/context.py` - request/runtime context object.
- `src/ombrebrain/kernel/errors.py` - typed v2.4.0 error hierarchy.
- `src/ombrebrain/kernel/registry.py` - capability manifest and registry.
- `src/ombrebrain/fabric/__init__.py` - fabric package marker.
- `src/ombrebrain/fabric/log/__init__.py` - log package marker.
- `src/ombrebrain/fabric/log/wal.py` - WAL entry and JSONL store.
- `src/ombrebrain/fabric/storage/__init__.py` - storage package marker.
- `src/ombrebrain/fabric/storage/engine.py` - Memory Fabric API.
- `src/ombrebrain/cluster/__init__.py` - cluster package marker.
- `src/ombrebrain/cluster/node.py` - node identity model.
- `src/ombrebrain/cluster/consensus.py` - consensus interface and single-node adapter.
- `src/ombrebrain/adapters/__init__.py` - compatibility adapter package marker.
- `src/ombrebrain/adapters/bucket_adapter.py` - bucket Markdown to MemoryEvent converter.

Create tests:

- `tests/test_v3_package.py`
- `tests/test_v3_memory_event.py`
- `tests/test_v3_kernel_registry.py`
- `tests/test_v3_wal.py`
- `tests/test_v3_memory_fabric.py`
- `tests/test_v3_consensus.py`
- `tests/test_v3_bucket_adapter.py`

Modify:

- None in this foundation slice unless an import path issue is discovered during execution.

## Execution Precondition

This desktop folder was created from a GitHub zip and is not a git repository. Before implementation, execute this plan in a git-backed clone or worktree. If implementation must happen inside the zip folder, keep the same commit checkpoints as file groups and record them in an execution note.

Recommended setup:

```powershell
git clone https://github.com/P0lar1zZ/Ombre-Brain.git OmbreBrain-v2.4.0-work
cd OmbreBrain-v2.4.0-work
```

If the remote owner/name differs, use the actual GitHub repository URL shown in the browser.

---

### Task 1: Add v2.4.0 Package Skeleton And Version Reader

**Files:**
- Create: `src/ombrebrain/__init__.py`
- Create: `src/ombrebrain/version.py`
- Test: `tests/test_v3_package.py`

- [ ] **Step 1: Write the failing package import test**

Create `tests/test_v3_package.py`:

```python
from pathlib import Path


def test_ombrebrain_package_exports_version():
    import ombrebrain

    assert isinstance(ombrebrain.__version__, str)
    assert ombrebrain.__version__


def test_version_reader_uses_root_version_file():
    from ombrebrain.version import read_version

    root_version = Path(__file__).resolve().parent.parent / "VERSION"
    assert read_version() == root_version.read_text(encoding="utf-8").strip()
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```powershell
pytest tests/test_v3_package.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'ombrebrain'`.

- [ ] **Step 3: Create package files**

Create `src/ombrebrain/__init__.py`:

```python
from .version import __version__, read_version

__all__ = ["__version__", "read_version"]
```

Create `src/ombrebrain/version.py`:

```python
from pathlib import Path


def read_version() -> str:
    root = Path(__file__).resolve().parents[2]
    version_file = root / "VERSION"
    return version_file.read_text(encoding="utf-8").strip()


__version__ = read_version()
```

- [ ] **Step 4: Run the test and verify it passes**

Run:

```powershell
pytest tests/test_v3_package.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add src/ombrebrain/__init__.py src/ombrebrain/version.py tests/test_v3_package.py
git commit -m "chore(v2.4.0): add ombrebrain package skeleton"
```

---

### Task 2: Add AI-Native MemoryEvent Schema

**Files:**
- Create: `src/ombrebrain/protocol/__init__.py`
- Create: `src/ombrebrain/protocol/schemas.py`
- Test: `tests/test_v3_memory_event.py`

- [ ] **Step 1: Write failing schema tests**

Create `tests/test_v3_memory_event.py`:

```python
from ombrebrain.protocol.schemas import ActorKind, MemoryEvent, MemoryType, Visibility


def test_memory_event_has_deterministic_id_for_same_payload():
    first = MemoryEvent.new(
        actor=ActorKind.USER,
        actor_name="rin",
        memory_type=MemoryType.PERMANENT,
        content="OB remembers permanent memories.",
        visibility=Visibility.PRIVATE,
        session_id="s1",
        task_id="t1",
    )
    second = MemoryEvent.new(
        actor=ActorKind.USER,
        actor_name="rin",
        memory_type=MemoryType.PERMANENT,
        content="OB remembers permanent memories.",
        visibility=Visibility.PRIVATE,
        session_id="s1",
        task_id="t1",
    )

    assert first.id == second.id
    assert first.vector_state == "pending"


def test_memory_event_serializes_without_enum_objects():
    event = MemoryEvent.new(
        actor=ActorKind.CODEX,
        actor_name="Codex",
        memory_type=MemoryType.TRACE,
        content="Trace source is preserved.",
        visibility=Visibility.INTERNAL,
        source_chain=["mcp", "trace"],
    )

    payload = event.to_dict()

    assert payload["actor"] == "codex"
    assert payload["memory_type"] == "trace"
    assert payload["visibility"] == "internal"
    assert payload["source_chain"] == ["mcp", "trace"]
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```powershell
pytest tests/test_v3_memory_event.py -v
```

Expected: FAIL with `ModuleNotFoundError` or missing `MemoryEvent`.

- [ ] **Step 3: Add protocol package and schema code**

Create `src/ombrebrain/protocol/__init__.py`:

```python
from .schemas import ActorKind, MemoryEvent, MemoryType, Visibility

__all__ = ["ActorKind", "MemoryEvent", "MemoryType", "Visibility"]
```

Create `src/ombrebrain/protocol/schemas.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any


class ActorKind(str, Enum):
    USER = "user"
    CODEX = "codex"
    CLAUDE = "claude"
    GPT = "gpt"
    GEMINI = "gemini"
    MCP_TOOL = "mcp_tool"
    WEB_DASHBOARD = "web_dashboard"
    SYSTEM = "system"


class MemoryType(str, Enum):
    DYNAMIC = "dynamic"
    PERMANENT = "permanent"
    TRACE = "trace"
    LETTER = "letter"
    PLAN = "plan"
    FEEL = "feel"


class Visibility(str, Enum):
    PRIVATE = "private"
    INTERNAL = "internal"
    SHARED = "shared"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _enum_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_enum_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _enum_value(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class MemoryEvent:
    id: str
    actor: ActorKind
    actor_name: str
    memory_type: MemoryType
    content: str
    visibility: Visibility
    session_id: str = ""
    task_id: str = ""
    parent_event_ids: tuple[str, ...] = ()
    confidence: float = 1.0
    importance: int = 5
    source_chain: tuple[str, ...] = ()
    vector_state: str = "pending"
    cluster_term: int = 0
    cluster_index: int = 0
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        *,
        actor: ActorKind,
        actor_name: str,
        memory_type: MemoryType,
        content: str,
        visibility: Visibility,
        session_id: str = "",
        task_id: str = "",
        parent_event_ids: list[str] | tuple[str, ...] | None = None,
        confidence: float = 1.0,
        importance: int = 5,
        source_chain: list[str] | tuple[str, ...] | None = None,
        created_at: str = "1970-01-01T00:00:00+00:00",
        metadata: dict[str, Any] | None = None,
    ) -> "MemoryEvent":
        parent_ids = tuple(parent_event_ids or ())
        sources = tuple(source_chain or ())
        clean_metadata = dict(metadata or {})
        event_id = cls.derive_id(
            actor=actor,
            actor_name=actor_name,
            memory_type=memory_type,
            content=content,
            visibility=visibility,
            session_id=session_id,
            task_id=task_id,
            parent_event_ids=parent_ids,
            source_chain=sources,
            created_at=created_at,
            metadata=clean_metadata,
        )
        return cls(
            id=event_id,
            actor=actor,
            actor_name=actor_name,
            memory_type=memory_type,
            content=content,
            visibility=visibility,
            session_id=session_id,
            task_id=task_id,
            parent_event_ids=parent_ids,
            confidence=max(0.0, min(1.0, float(confidence))),
            importance=max(1, min(10, int(importance))),
            source_chain=sources,
            created_at=created_at,
            metadata=clean_metadata,
        )

    @staticmethod
    def derive_id(**payload: Any) -> str:
        canonical = json.dumps(_enum_value(payload), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]

    def to_dict(self) -> dict[str, Any]:
        return _enum_value(asdict(self))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MemoryEvent":
        data = dict(payload)
        data["actor"] = ActorKind(data["actor"])
        data["memory_type"] = MemoryType(data["memory_type"])
        data["visibility"] = Visibility(data["visibility"])
        data["parent_event_ids"] = tuple(data.get("parent_event_ids", ()))
        data["source_chain"] = tuple(data.get("source_chain", ()))
        data["metadata"] = dict(data.get("metadata", {}))
        return cls(**data)
```

- [ ] **Step 4: Run schema tests**

Run:

```powershell
pytest tests/test_v3_memory_event.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add src/ombrebrain/protocol/__init__.py src/ombrebrain/protocol/schemas.py tests/test_v3_memory_event.py
git commit -m "feat(v2.4.0): add memory event schema"
```

---

### Task 3: Add Kernel Context, Errors, And Capability Registry

**Files:**
- Create: `src/ombrebrain/kernel/__init__.py`
- Create: `src/ombrebrain/kernel/context.py`
- Create: `src/ombrebrain/kernel/errors.py`
- Create: `src/ombrebrain/kernel/registry.py`
- Test: `tests/test_v3_kernel_registry.py`

- [ ] **Step 1: Write failing registry tests**

Create `tests/test_v3_kernel_registry.py`:

```python
import pytest

from ombrebrain.kernel.context import OmbreContext
from ombrebrain.kernel.errors import CapabilityLoadError, PolicyViolation
from ombrebrain.kernel.registry import CapabilityManifest, CapabilityRegistry


def test_registry_registers_and_returns_manifest():
    registry = CapabilityRegistry()
    manifest = CapabilityManifest(
        name="memory.write",
        version="3.0.0",
        permissions=("memory:write",),
        writes_memory=True,
        cluster_safe=True,
    )

    registry.register(manifest, handler=lambda context, payload: {"ok": True})

    assert registry.get("memory.write").manifest == manifest


def test_registry_rejects_duplicate_capability():
    registry = CapabilityRegistry()
    manifest = CapabilityManifest(name="mcp.search", version="3.0.0")
    registry.register(manifest, handler=lambda context, payload: payload)

    with pytest.raises(CapabilityLoadError):
        registry.register(manifest, handler=lambda context, payload: payload)


def test_dispatch_requires_permission():
    registry = CapabilityRegistry()
    manifest = CapabilityManifest(name="memory.write", version="3.0.0", permissions=("memory:write",))
    registry.register(manifest, handler=lambda context, payload: payload)
    context = OmbreContext(request_id="r1", actor_name="tester", permissions=())

    with pytest.raises(PolicyViolation):
        registry.dispatch("memory.write", context, {"content": "blocked"})
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```powershell
pytest tests/test_v3_kernel_registry.py -v
```

Expected: FAIL with missing kernel modules.

- [ ] **Step 3: Add kernel modules**

Create `src/ombrebrain/kernel/__init__.py`:

```python
from .context import OmbreContext
from .registry import CapabilityManifest, CapabilityRegistry

__all__ = ["CapabilityManifest", "CapabilityRegistry", "OmbreContext"]
```

Create `src/ombrebrain/kernel/errors.py`:

```python
class OmbreError(Exception):
    code = "OMBRE_ERROR"


class ConfigError(OmbreError):
    code = "CONFIG_ERROR"


class CapabilityLoadError(OmbreError):
    code = "CAPABILITY_LOAD_ERROR"


class PolicyViolation(OmbreError):
    code = "POLICY_VIOLATION"


class ClusterUnavailable(OmbreError):
    code = "CLUSTER_UNAVAILABLE"


class NotLeader(OmbreError):
    code = "NOT_LEADER"


class QuorumTimeout(OmbreError):
    code = "QUORUM_TIMEOUT"


class LogIntegrityError(OmbreError):
    code = "LOG_INTEGRITY_ERROR"


class SnapshotRestoreError(OmbreError):
    code = "SNAPSHOT_RESTORE_ERROR"


class VectorRebuildError(OmbreError):
    code = "VECTOR_REBUILD_ERROR"


class HotUpdateRejected(OmbreError):
    code = "HOT_UPDATE_REJECTED"


class MigrationFailed(OmbreError):
    code = "MIGRATION_FAILED"
```

Create `src/ombrebrain/kernel/context.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class OmbreContext:
    request_id: str
    actor_name: str
    permissions: tuple[str, ...] = ()
    source: str = "local"
    session_id: str = ""
    task_id: str = ""
    config_snapshot: Mapping[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def safe_config(self) -> Mapping[str, Any]:
        redacted = {}
        for key, value in dict(self.config_snapshot).items():
            lowered = key.lower()
            if "key" in lowered or "secret" in lowered or "token" in lowered:
                redacted[key] = "***"
            else:
                redacted[key] = value
        return MappingProxyType(redacted)
```

Create `src/ombrebrain/kernel/registry.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .context import OmbreContext
from .errors import CapabilityLoadError, PolicyViolation

CapabilityHandler = Callable[[OmbreContext, dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class CapabilityManifest:
    name: str
    version: str
    permissions: tuple[str, ...] = ()
    writes_memory: bool = False
    cluster_safe: bool = False
    hot_update_safe: bool = False
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegisteredCapability:
    manifest: CapabilityManifest
    handler: CapabilityHandler


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, RegisteredCapability] = {}

    def register(self, manifest: CapabilityManifest, handler: CapabilityHandler) -> None:
        if manifest.name in self._capabilities:
            raise CapabilityLoadError(f"Capability already registered: {manifest.name}")
        missing = [name for name in manifest.dependencies if name not in self._capabilities]
        if missing:
            raise CapabilityLoadError(f"Missing dependencies for {manifest.name}: {', '.join(missing)}")
        self._capabilities[manifest.name] = RegisteredCapability(manifest=manifest, handler=handler)

    def get(self, name: str) -> RegisteredCapability:
        try:
            return self._capabilities[name]
        except KeyError as exc:
            raise CapabilityLoadError(f"Unknown capability: {name}") from exc

    def dispatch(self, name: str, context: OmbreContext, payload: dict[str, Any]) -> dict[str, Any]:
        capability = self.get(name)
        for permission in capability.manifest.permissions:
            if not context.has_permission(permission):
                raise PolicyViolation(f"Missing permission: {permission}")
        return capability.handler(context, payload)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._capabilities))
```

- [ ] **Step 4: Run kernel tests**

Run:

```powershell
pytest tests/test_v3_kernel_registry.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```powershell
git add src/ombrebrain/kernel tests/test_v3_kernel_registry.py
git commit -m "feat(v2.4.0): add kernel capability registry"
```

---

### Task 4: Add Append-Only WAL With Checksum Chain

**Files:**
- Create: `src/ombrebrain/fabric/__init__.py`
- Create: `src/ombrebrain/fabric/log/__init__.py`
- Create: `src/ombrebrain/fabric/log/wal.py`
- Test: `tests/test_v3_wal.py`

- [ ] **Step 1: Write failing WAL tests**

Create `tests/test_v3_wal.py`:

```python
import json

import pytest

from ombrebrain.fabric.log.wal import WalStore
from ombrebrain.kernel.errors import LogIntegrityError
from ombrebrain.protocol.schemas import ActorKind, MemoryEvent, MemoryType, Visibility


def make_event(content: str) -> MemoryEvent:
    return MemoryEvent.new(
        actor=ActorKind.USER,
        actor_name="tester",
        memory_type=MemoryType.DYNAMIC,
        content=content,
        visibility=Visibility.PRIVATE,
    )


def test_wal_appends_and_replays_events(tmp_path):
    wal = WalStore(tmp_path / "memory.wal")
    first = wal.append(make_event("first").to_dict())
    second = wal.append(make_event("second").to_dict())

    replayed = list(wal.replay())

    assert first.index == 1
    assert second.index == 2
    assert [entry.payload["content"] for entry in replayed] == ["first", "second"]


def test_wal_detects_payload_corruption(tmp_path):
    wal_path = tmp_path / "memory.wal"
    wal = WalStore(wal_path)
    wal.append(make_event("clean").to_dict())

    line = wal_path.read_text(encoding="utf-8").splitlines()[0]
    record = json.loads(line)
    record["payload"]["content"] = "tampered"
    wal_path.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(LogIntegrityError):
        list(WalStore(wal_path).replay())
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```powershell
pytest tests/test_v3_wal.py -v
```

Expected: FAIL with missing `WalStore`.

- [ ] **Step 3: Add WAL implementation**

Create `src/ombrebrain/fabric/__init__.py`:

```python
__all__: list[str] = []
```

Create `src/ombrebrain/fabric/log/__init__.py`:

```python
from .wal import WalEntry, WalStore

__all__ = ["WalEntry", "WalStore"]
```

Create `src/ombrebrain/fabric/log/wal.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

from ombrebrain.kernel.errors import LogIntegrityError


@dataclass(frozen=True)
class WalEntry:
    index: int
    previous_checksum: str
    checksum: str
    payload: dict[str, Any]

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _checksum(index: int, previous_checksum: str, payload: dict[str, Any]) -> str:
    body = f"{index}|{previous_checksum}|{_canonical_payload(payload)}"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


class WalStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, payload: dict[str, Any]) -> WalEntry:
        last = self._last_entry()
        index = 1 if last is None else last.index + 1
        previous_checksum = "" if last is None else last.checksum
        checksum = _checksum(index, previous_checksum, payload)
        entry = WalEntry(
            index=index,
            previous_checksum=previous_checksum,
            checksum=checksum,
            payload=dict(payload),
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_record(), ensure_ascii=False, sort_keys=True) + "\n")
        return entry

    def replay(self) -> Iterator[WalEntry]:
        if not self.path.exists():
            return
        previous_checksum = ""
        expected_index = 1
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    entry = WalEntry(
                        index=int(record["index"]),
                        previous_checksum=str(record["previous_checksum"]),
                        checksum=str(record["checksum"]),
                        payload=dict(record["payload"]),
                    )
                except Exception as exc:
                    raise LogIntegrityError(f"Invalid WAL record at line {line_number}") from exc
                if entry.index != expected_index:
                    raise LogIntegrityError(f"Unexpected WAL index {entry.index}, expected {expected_index}")
                if entry.previous_checksum != previous_checksum:
                    raise LogIntegrityError(f"Broken WAL checksum chain at index {entry.index}")
                actual = _checksum(entry.index, entry.previous_checksum, entry.payload)
                if actual != entry.checksum:
                    raise LogIntegrityError(f"Corrupt WAL payload at index {entry.index}")
                yield entry
                previous_checksum = entry.checksum
                expected_index += 1

    def _last_entry(self) -> WalEntry | None:
        last = None
        for entry in self.replay():
            last = entry
        return last
```

- [ ] **Step 4: Run WAL tests**

Run:

```powershell
pytest tests/test_v3_wal.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add src/ombrebrain/fabric tests/test_v3_wal.py
git commit -m "feat(v2.4.0): add wal-backed memory log"
```

---

### Task 5: Add Memory Fabric Replay And Query API

**Files:**
- Create: `src/ombrebrain/fabric/storage/__init__.py`
- Create: `src/ombrebrain/fabric/storage/engine.py`
- Test: `tests/test_v3_memory_fabric.py`

- [ ] **Step 1: Write failing Memory Fabric tests**

Create `tests/test_v3_memory_fabric.py`:

```python
from ombrebrain.fabric.storage.engine import MemoryFabric
from ombrebrain.protocol.schemas import ActorKind, MemoryEvent, MemoryType, Visibility


def make_event(memory_type: MemoryType, content: str) -> MemoryEvent:
    return MemoryEvent.new(
        actor=ActorKind.CODEX,
        actor_name="Codex",
        memory_type=memory_type,
        content=content,
        visibility=Visibility.INTERNAL,
    )


def test_memory_fabric_persists_and_replays_events(tmp_path):
    fabric = MemoryFabric.open(tmp_path)
    fabric.append_event(make_event(MemoryType.DYNAMIC, "short thought"))
    fabric.append_event(make_event(MemoryType.PERMANENT, "durable thought"))

    reopened = MemoryFabric.open(tmp_path)
    events = reopened.replay_events()

    assert [event.content for event in events] == ["short thought", "durable thought"]


def test_memory_fabric_queries_by_type(tmp_path):
    fabric = MemoryFabric.open(tmp_path)
    fabric.append_event(make_event(MemoryType.DYNAMIC, "dynamic"))
    fabric.append_event(make_event(MemoryType.PERMANENT, "permanent"))

    permanent = fabric.events_by_type(MemoryType.PERMANENT)

    assert len(permanent) == 1
    assert permanent[0].content == "permanent"
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```powershell
pytest tests/test_v3_memory_fabric.py -v
```

Expected: FAIL with missing `MemoryFabric`.

- [ ] **Step 3: Add Memory Fabric implementation**

Create `src/ombrebrain/fabric/storage/__init__.py`:

```python
from .engine import MemoryFabric

__all__ = ["MemoryFabric"]
```

Create `src/ombrebrain/fabric/storage/engine.py`:

```python
from __future__ import annotations

from pathlib import Path

from ombrebrain.fabric.log.wal import WalStore
from ombrebrain.protocol.schemas import MemoryEvent, MemoryType


class MemoryFabric:
    def __init__(self, wal: WalStore) -> None:
        self._wal = wal

    @classmethod
    def open(cls, root: str | Path) -> "MemoryFabric":
        root_path = Path(root)
        return cls(WalStore(root_path / "fabric" / "memory.wal"))

    def append_event(self, event: MemoryEvent) -> int:
        entry = self._wal.append(event.to_dict())
        return entry.index

    def replay_events(self) -> list[MemoryEvent]:
        return [MemoryEvent.from_dict(entry.payload) for entry in self._wal.replay()]

    def events_by_type(self, memory_type: MemoryType) -> list[MemoryEvent]:
        return [event for event in self.replay_events() if event.memory_type == memory_type]
```

- [ ] **Step 4: Run Memory Fabric tests**

Run:

```powershell
pytest tests/test_v3_memory_fabric.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add src/ombrebrain/fabric/storage tests/test_v3_memory_fabric.py
git commit -m "feat(v2.4.0): add memory fabric replay api"
```

---

### Task 6: Add Consensus Interface And Single-Node Adapter

**Files:**
- Create: `src/ombrebrain/cluster/__init__.py`
- Create: `src/ombrebrain/cluster/node.py`
- Create: `src/ombrebrain/cluster/consensus.py`
- Test: `tests/test_v3_consensus.py`

- [ ] **Step 1: Write failing consensus tests**

Create `tests/test_v3_consensus.py`:

```python
import pytest

from ombrebrain.cluster.consensus import SingleNodeConsensus
from ombrebrain.cluster.node import NodeIdentity, NodeRole
from ombrebrain.fabric.storage.engine import MemoryFabric
from ombrebrain.kernel.errors import NotLeader
from ombrebrain.protocol.schemas import ActorKind, MemoryEvent, MemoryType, Visibility


def make_event() -> MemoryEvent:
    return MemoryEvent.new(
        actor=ActorKind.SYSTEM,
        actor_name="cluster-test",
        memory_type=MemoryType.TRACE,
        content="single node commit",
        visibility=Visibility.INTERNAL,
    )


def test_single_node_consensus_commits_to_fabric(tmp_path):
    node = NodeIdentity(node_id="n1", address="127.0.0.1:8001", role=NodeRole.LEADER)
    consensus = SingleNodeConsensus(node=node, fabric=MemoryFabric.open(tmp_path))

    result = consensus.commit(make_event())

    assert result.committed is True
    assert result.index == 1


def test_single_node_consensus_rejects_non_leader(tmp_path):
    node = NodeIdentity(node_id="n1", address="127.0.0.1:8001", role=NodeRole.FOLLOWER)
    consensus = SingleNodeConsensus(node=node, fabric=MemoryFabric.open(tmp_path))

    with pytest.raises(NotLeader):
        consensus.commit(make_event())
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
pytest tests/test_v3_consensus.py -v
```

Expected: FAIL with missing cluster modules.

- [ ] **Step 3: Add cluster identity and single-node consensus**

Create `src/ombrebrain/cluster/__init__.py`:

```python
from .consensus import CommitResult, SingleNodeConsensus
from .node import NodeIdentity, NodeRole

__all__ = ["CommitResult", "NodeIdentity", "NodeRole", "SingleNodeConsensus"]
```

Create `src/ombrebrain/cluster/node.py`:

```python
from dataclasses import dataclass
from enum import Enum


class NodeRole(str, Enum):
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"


@dataclass(frozen=True)
class NodeIdentity:
    node_id: str
    address: str
    role: NodeRole = NodeRole.FOLLOWER
    term: int = 1
```

Create `src/ombrebrain/cluster/consensus.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ombrebrain.cluster.node import NodeIdentity, NodeRole
from ombrebrain.fabric.storage.engine import MemoryFabric
from ombrebrain.kernel.errors import NotLeader
from ombrebrain.protocol.schemas import MemoryEvent


@dataclass(frozen=True)
class CommitResult:
    committed: bool
    index: int
    term: int
    leader_id: str


class ConsensusEngine(Protocol):
    def commit(self, event: MemoryEvent) -> CommitResult:
        raise NotImplementedError


class SingleNodeConsensus:
    def __init__(self, *, node: NodeIdentity, fabric: MemoryFabric) -> None:
        self.node = node
        self.fabric = fabric

    def commit(self, event: MemoryEvent) -> CommitResult:
        if self.node.role != NodeRole.LEADER:
            raise NotLeader(f"Node {self.node.node_id} is not leader")
        index = self.fabric.append_event(event)
        return CommitResult(
            committed=True,
            index=index,
            term=self.node.term,
            leader_id=self.node.node_id,
        )
```

- [ ] **Step 4: Run consensus tests**

Run:

```powershell
pytest tests/test_v3_consensus.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add src/ombrebrain/cluster tests/test_v3_consensus.py
git commit -m "feat(v2.4.0): add consensus interface"
```

---

### Task 7: Add Bucket Markdown Compatibility Adapter

**Files:**
- Create: `src/ombrebrain/adapters/__init__.py`
- Create: `src/ombrebrain/adapters/bucket_adapter.py`
- Test: `tests/test_v3_bucket_adapter.py`

- [ ] **Step 1: Write failing adapter tests**

Create `tests/test_v3_bucket_adapter.py`:

```python
from pathlib import Path

from ombrebrain.adapters.bucket_adapter import bucket_markdown_to_event
from ombrebrain.protocol.schemas import MemoryType


def test_bucket_markdown_to_event_maps_type_and_content(tmp_path):
    bucket = tmp_path / "memory.md"
    bucket.write_text(
        """---
id: abc123
name: Test Memory
type: permanent
importance: 9
tags:
- ob
---

OB should keep old bucket data readable.
""",
        encoding="utf-8",
    )

    event = bucket_markdown_to_event(Path(bucket))

    assert event.memory_type == MemoryType.PERMANENT
    assert event.content == "OB should keep old bucket data readable."
    assert event.importance == 9
    assert event.metadata["legacy_bucket_id"] == "abc123"
    assert event.metadata["legacy_name"] == "Test Memory"
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```powershell
pytest tests/test_v3_bucket_adapter.py -v
```

Expected: FAIL with missing adapter.

- [ ] **Step 3: Add adapter implementation**

Create `src/ombrebrain/adapters/__init__.py`:

```python
from .bucket_adapter import bucket_markdown_to_event

__all__ = ["bucket_markdown_to_event"]
```

Create `src/ombrebrain/adapters/bucket_adapter.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import frontmatter

from ombrebrain.protocol.schemas import ActorKind, MemoryEvent, MemoryType, Visibility


def _memory_type(value: Any) -> MemoryType:
    text = str(value or "dynamic").strip().lower()
    try:
        return MemoryType(text)
    except ValueError:
        return MemoryType.DYNAMIC


def bucket_markdown_to_event(path: str | Path) -> MemoryEvent:
    bucket_path = Path(path)
    post = frontmatter.load(bucket_path)
    metadata = {
        "legacy_bucket_id": str(post.metadata.get("id", "")),
        "legacy_name": str(post.metadata.get("name", bucket_path.stem)),
        "legacy_path": str(bucket_path),
        "legacy_tags": list(post.metadata.get("tags", []) or []),
    }
    return MemoryEvent.new(
        actor=ActorKind.SYSTEM,
        actor_name="v2.3.22-migration",
        memory_type=_memory_type(post.metadata.get("type")),
        content=post.content.strip(),
        visibility=Visibility.PRIVATE,
        importance=int(post.metadata.get("importance", 5) or 5),
        source_chain=("legacy_bucket",),
        metadata=metadata,
    )
```

- [ ] **Step 4: Run adapter tests**

Run:

```powershell
pytest tests/test_v3_bucket_adapter.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```powershell
git add src/ombrebrain/adapters tests/test_v3_bucket_adapter.py
git commit -m "feat(v2.4.0): add bucket compatibility adapter"
```

---

### Task 8: Run Foundation Regression Suite

**Files:**
- No source changes expected.
- Test: all v2.4.0 foundation tests plus current regression tests.

- [ ] **Step 1: Run v2.4.0 foundation tests**

Run:

```powershell
pytest tests/test_v3_package.py tests/test_v3_memory_event.py tests/test_v3_kernel_registry.py tests/test_v3_wal.py tests/test_v3_memory_fabric.py tests/test_v3_consensus.py tests/test_v3_bucket_adapter.py -v
```

Expected: all selected tests pass.

- [ ] **Step 2: Run current regression tests**

Run:

```powershell
pytest tests/test_permanent_breath_regression.py tests/test_letter_read_regression.py tests/test_letter_author_regression.py tests/test_security_regression.py tests/test_trace_importance_regression.py -v
```

Expected: all selected tests pass. If a failure appears, stop and investigate before proceeding; do not change unrelated existing behavior.

- [ ] **Step 3: Run full test suite**

Run:

```powershell
pytest -q
```

Expected: test suite passes or reports only pre-existing failures documented before this plan started.

- [ ] **Step 4: Commit final foundation verification notes**

If all tests pass:

```powershell
git status --short
git commit --allow-empty -m "test(v2.4.0): verify foundation regression suite"
```

If there are pre-existing failures, create `docs/superpowers/plans/2026-06-28-v2.4.0-foundation-test-notes.md` with the command, failure names, and evidence, then commit that note with:

```powershell
git add docs/superpowers/plans/2026-06-28-v2.4.0-foundation-test-notes.md
git commit -m "test(v2.4.0): document foundation test status"
```

---

## Follow-Up Plan Order

After this foundation plan passes, implement these plans in order:

1. `ombrebrain-v2.4.0-raft-cluster` - multi-node Raft-style election, replication, snapshot install, catch-up, and partition tests.
2. `ombrebrain-v2.4.0-capabilities` - migrate MCP, web, OAuth, tools, deployment, and hot update into capability manifests.
3. `ombrebrain-v2.4.0-hot-update-policy` - signed/hash manifest, protected paths, rollback plan, cluster rollout.
4. `ombrebrain-v2.4.0-migration` - convert existing bucket directories into Memory Fabric events with report and rollback.
5. `ombrebrain-v2.4.0-license-release` - non-commercial license boundary, README, changelog, release notes, and public warnings.

## Self-Review Checklist

- Spec coverage: This plan covers package skeleton, event schema, Kernel registry, WAL, Memory Fabric, single-node consensus adapter, and v2 bucket compatibility. It intentionally defers full Raft, hot update, capability migration, license docs, and full migration tooling into follow-up plans.
- Placeholder scan: No task uses unresolved placeholder markers or unspecified tests.
- Type consistency: `MemoryEvent`, `ActorKind`, `MemoryType`, `Visibility`, `WalStore`, `MemoryFabric`, `NodeIdentity`, `NodeRole`, `SingleNodeConsensus`, `CapabilityManifest`, and `CapabilityRegistry` are introduced before later tasks reference them.
