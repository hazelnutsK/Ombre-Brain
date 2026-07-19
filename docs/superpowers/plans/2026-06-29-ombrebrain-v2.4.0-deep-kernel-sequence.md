# OmbreBrain v2.4.0 Deep Kernel Sequence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved F -> B -> C -> D -> E -> A deep architecture sequence while preserving current v2.4.0 version and original OB external behavior.

**Architecture:** The sequence first freezes legacy compatibility with a formal acceptance harness, then adds event-sourced command/event/projection internals, a query planner, a capability microkernel, a constrained plugin runtime, and production-grade distributed Memory Fabric abstractions. All layers are additive or side-channel integrations; legacy MCP tools, bucket markdown, dashboard routes, config semantics, and deployment behavior remain unchanged.

**Tech Stack:** Python dataclasses, existing `MemoryCommand`, `MemoryEvent`, `MemoryFabric`, policy/projection/decision layers, JSON-safe reports, pytest.

---

### Task F: Formal Acceptance Harness

**Files:**
- Create: `src/ombrebrain/acceptance/__init__.py`
- Create: `src/ombrebrain/acceptance/contracts.py`
- Create: `src/ombrebrain/acceptance/harness.py`
- Test: `tests/test_v3_formal_acceptance_harness.py`

- [ ] **Step 1: Write failing tests** for default compatibility contracts, snapshot verification, route/tool/bucket checks, and no side effects.
- [ ] **Step 2: Run F tests** with `py -3.10 -m pytest tests\test_v3_formal_acceptance_harness.py -q`; expect import failure.
- [ ] **Step 3: Implement immutable contract and report objects** with `LegacyCompatibilityContract`, `CompatibilitySnapshot`, `CompatibilityIssue`, and `AcceptanceReport`.
- [ ] **Step 4: Implement `FormalAcceptanceHarness.default().evaluate(snapshot)`** as a read-only compatibility gate.
- [ ] **Step 5: Run F tests** and continue only if passing.

### Task B: Event-Sourced Memory Kernel

**Files:**
- Create: `src/ombrebrain/eventsourcing/__init__.py`
- Create: `src/ombrebrain/eventsourcing/contracts.py`
- Create: `src/ombrebrain/eventsourcing/kernel.py`
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Test: `tests/test_v3_event_sourced_kernel.py`

- [ ] **Step 1: Write failing tests** for command -> event -> projection, JSON-safe metadata, deterministic projection summaries, and runtime metadata integration.
- [ ] **Step 2: Run B tests** and expect missing import/metadata failure.
- [ ] **Step 3: Implement `EventSourcedMemoryKernel`** that converts a `MemoryCommand` and `CommandPlan` into an event-sourced envelope and projection batch without changing legacy state.
- [ ] **Step 4: Add a `event_sourced_kernel` field to `LegacyRuntime`** and include `event_sourced_kernel` metadata in tool/execution trace events.
- [ ] **Step 5: Run B tests** and continue only if passing.

### Task C: Query Planner + Retrieval Engine

**Files:**
- Create: `src/ombrebrain/retrieval/__init__.py`
- Create: `src/ombrebrain/retrieval/planner.py`
- Create: `src/ombrebrain/retrieval/engine.py`
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Test: `tests/test_v3_query_planner.py`

- [ ] **Step 1: Write failing tests** for query intent, channel selection, stage ordering, stable trace output, and runtime metadata integration for breath/search.
- [ ] **Step 2: Run C tests** and expect missing import/metadata failure.
- [ ] **Step 3: Implement planner and read-only retrieval engine** with lexical, semantic, recency, importance, and rerank stages.
- [ ] **Step 4: Add retrieval metadata to read-oriented tool trace events** without changing tool return values.
- [ ] **Step 5: Run C tests** and continue only if passing.

### Task D: Capability Microkernel

**Files:**
- Create: `src/ombrebrain/microkernel/__init__.py`
- Create: `src/ombrebrain/microkernel/contracts.py`
- Create: `src/ombrebrain/microkernel/runtime.py`
- Modify: `src/ombrebrain/app/legacy_runtime.py`
- Test: `tests/test_v3_capability_microkernel.py`

- [ ] **Step 1: Write failing tests** for allowed dispatch, denied dispatch, side-effect classification, and runtime dispatch preserving successful payload behavior.
- [ ] **Step 2: Run D tests** and expect missing import/runtime failure.
- [ ] **Step 3: Implement `CapabilityMicrokernel`** that checks registry manifests, permissions, declared side effects, and protected surfaces before dispatch.
- [ ] **Step 4: Route `LegacyRuntime.dispatch_capability` through the microkernel** while preserving allowed handler return payloads.
- [ ] **Step 5: Run D tests** and continue only if passing.

### Task E: Plugin / Extension Runtime

**Files:**
- Create: `src/ombrebrain/plugins/__init__.py`
- Create: `src/ombrebrain/plugins/contracts.py`
- Create: `src/ombrebrain/plugins/runtime.py`
- Test: `tests/test_v3_plugin_runtime.py`

- [ ] **Step 1: Write failing tests** for plugin manifest validation, sandbox policy, allowed plugin execution, and protected surface rejection.
- [ ] **Step 2: Run E tests** and expect missing import failure.
- [ ] **Step 3: Implement `PluginRuntime`** with manifest parsing, capability declarations, sandbox decisions, and in-memory handler registration.
- [ ] **Step 4: Run E tests** and continue only if passing.

### Task A: Production-Grade Distributed Memory Fabric

**Files:**
- Create: `src/ombrebrain/distributed/__init__.py`
- Create: `src/ombrebrain/distributed/membership.py`
- Create: `src/ombrebrain/distributed/transport.py`
- Create: `src/ombrebrain/distributed/coordinator.py`
- Test: `tests/test_v3_distributed_fabric.py`

- [ ] **Step 1: Write failing tests** for membership changes, leader lease, quorum commit, follower catch-up, read-only follower queries, and minority rejection.
- [ ] **Step 2: Run A tests** and expect missing import failure.
- [ ] **Step 3: Implement production-grade abstractions** using in-memory transport and existing `MemoryFabric`, `RaftLogEntry`, and catch-up primitives.
- [ ] **Step 4: Run A tests** and continue only if passing.

### Final Verification And Artifacts

**Files:**
- Modify: `docs/V2.4.0_ARCHITECTURE.md`
- Modify: `docs/V2.4.0_BOUNDARY_MAP.md`
- Modify: `docs/V2.4.0_RELEASE_NOTES_DRAFT.md`
- Update: `C:\Users\孙立人\Desktop\OmbreBrain-v2.4.0-总文件夹\OmbreBrain-v2.4.0-complete-artifacts`

- [ ] **Step 1: Update docs** with F -> B -> C -> D -> E -> A layers.
- [ ] **Step 2: Run focused tests** for all new test files.
- [ ] **Step 3: Run all v2.4.0 tests** with `py -3.10 -m pytest @files -q`.
- [ ] **Step 4: Run full suite** with `py -3.10 -m pytest -q`.
- [ ] **Step 5: Refresh complete artifacts and zip**.
- [ ] **Step 6: Stop without commit, push, release, version bump, or cloud changes.**
