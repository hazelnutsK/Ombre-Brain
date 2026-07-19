# OmbreBrain v2.4.0 Remaining Systems Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the remaining v2.4.0 local architecture layers after Foundation: collaboration graph, Raft-style cluster simulator, snapshot/catch-up primitives, capability catalog, manifest-driven hot update policy, v2 bucket migration, and non-commercial release docs.

**Architecture:** Keep v2.3.22 runtime untouched. Add v2.4.0 modules under `src/ombrebrain/` and focused tests under `tests/test_v3_*.py`. Implement deterministic local primitives first so later production networking and UI integration can build on tested contracts.

**Tech Stack:** Python standard library, dataclasses, enum, pathlib, json, hashlib, shutil, pytest, existing `python-frontmatter`.

---

## Scope

This plan completes the remaining local v2.4.0 architecture surface without pushing, releasing, or replacing the existing v2 runtime.

In scope:

- Collaboration Graph and merge policy.
- Raft-style in-memory cluster primitives for election, quorum commit, follower catch-up, and snapshot install.
- Manifest-driven hot update policy with protected paths and hash verification.
- Capability catalog for MCP/tools/web/oauth/deployment/hot_update.
- v2 bucket directory migration into Memory Fabric with report.
- Non-commercial v2.4.0 license notice and README/release wording.
- Final artifact rebuild.

Out of scope:

- Real network RPC transport.
- Production daemon orchestration.
- Browser/UI wiring.
- Automatic GitHub push or Release publication.
- Cloud server changes.

## Tasks

### Task 1: Collaboration Graph

**Files:**
- Create: `src/ombrebrain/collab/__init__.py`
- Create: `src/ombrebrain/collab/graph.py`
- Create: `src/ombrebrain/collab/merge_policy.py`
- Test: `tests/test_v3_collab_graph.py`

**Requirements:**
- Add `CollaborationGraph` that indexes `MemoryEvent` by id.
- Support parent/child lookup through `parent_event_ids`.
- Support `events_for_actor(actor_name)`.
- Support `source_chain(event_id)`.
- Add `MergeDecision` and `MergePolicy` with decisions: keep_both, prefer_new, prefer_existing, mark_conflict.
- Tests must prove parent/child traversal, actor filtering, provenance/source chain, and conflict detection.

**Verification:**
- `py -3.10 -m pytest tests/test_v3_collab_graph.py -v`

### Task 2: Raft-Style Local Cluster Simulator

**Files:**
- Create: `src/ombrebrain/cluster/raft/__init__.py`
- Create: `src/ombrebrain/cluster/raft/log.py`
- Create: `src/ombrebrain/cluster/raft/quorum.py`
- Create: `src/ombrebrain/cluster/raft/leader.py`
- Create: `src/ombrebrain/cluster/replication/__init__.py`
- Create: `src/ombrebrain/cluster/replication/apply.py`
- Test: `tests/test_v3_raft_cluster.py`

**Requirements:**
- Add immutable `RaftLogEntry(term, index, event, checksum)`.
- Add `Quorum` helper for majority decisions.
- Add `InMemoryRaftCluster` for three-node local simulation.
- Election chooses a leader only with majority.
- Leader commit replicates a `MemoryEvent` to majority followers and applies committed event to leader `MemoryFabric`.
- Minority partition rejects commits.
- Tests must prove leader election, majority commit, follower log replication, and minority rejection.

**Verification:**
- `py -3.10 -m pytest tests/test_v3_raft_cluster.py -v`

### Task 3: Snapshot And Catch-Up

**Files:**
- Create: `src/ombrebrain/fabric/log/snapshot.py`
- Create: `src/ombrebrain/cluster/replication/catchup.py`
- Create: `src/ombrebrain/cluster/safety/__init__.py`
- Create: `src/ombrebrain/cluster/safety/integrity.py`
- Test: `tests/test_v3_snapshot_catchup.py`

**Requirements:**
- Add `MemorySnapshot` with last_index, last_term, events, checksum.
- Add snapshot save/load to JSON using strict `allow_nan=False`.
- Add catch-up helper that installs snapshot when follower is behind snapshot boundary.
- Add integrity helper that verifies snapshot checksum and event ids.
- Tests must prove save/load, checksum rejection, follower catch-up from log entries, and follower catch-up from snapshot.

**Verification:**
- `py -3.10 -m pytest tests/test_v3_snapshot_catchup.py -v`

### Task 4: Capability Catalog

**Files:**
- Create: `src/ombrebrain/capabilities/__init__.py`
- Create: `src/ombrebrain/capabilities/catalog.py`
- Test: `tests/test_v3_capability_catalog.py`

**Requirements:**
- Provide `foundation_capabilities()` returning `CapabilityManifest` entries for:
  - `mcp.aggregate`
  - `tools.search`
  - `tools.breath`
  - `web.dashboard`
  - `oauth.control`
  - `hot_update.apply`
  - `deployment.local`
- Each capability must declare permissions, memory write behavior, cluster safety, hot update safety, and dependencies where useful.
- Add `register_foundation_capabilities(registry)` that registers no-op handlers returning manifest metadata.
- Tests must prove catalog contents, dependency order, hot update safety flags, and registry dispatch.

**Verification:**
- `py -3.10 -m pytest tests/test_v3_capability_catalog.py -v`

### Task 5: Manifest-Driven Hot Update Policy

**Files:**
- Create: `src/ombrebrain/protocol/manifests.py`
- Create: `src/ombrebrain/policy/__init__.py`
- Create: `src/ombrebrain/policy/update_policy.py`
- Test: `tests/test_v3_update_policy.py`

**Requirements:**
- Add `FileManifest`, `UpdateManifest`, and `UpdatePlan`.
- Protected path rules must reject `.env`, `config.yaml`, `buckets/`, vector db paths, OAuth secrets, and deployment user overrides.
- Hash verification must use sha256.
- Path validation must reject traversal and absolute paths.
- Cluster rollout strategy is represented in manifest metadata, not executed yet.
- Tests must prove protected paths are rejected, traversal is rejected, valid files pass hash verification, bad hash fails, and update plan separates allowed/rejected files.

**Verification:**
- `py -3.10 -m pytest tests/test_v3_update_policy.py -v`

### Task 6: v2 Bucket Migration Report

**Files:**
- Create: `src/ombrebrain/adapters/migration.py`
- Test: `tests/test_v3_migration.py`

**Requirements:**
- Add `MigrationReport(converted, skipped, errors, vector_rebuild_required)`.
- Add `migrate_bucket_tree(bucket_root, fabric)` that scans known v2 bucket dirs: dynamic, permanent, archive, feel, plans, letters.
- Convert markdown files through `bucket_markdown_to_event`.
- Append events to `MemoryFabric`.
- Skip non-markdown files with a reason.
- Continue after per-file errors and record error path/message.
- Tests must prove dynamic/permanent conversion, skipped files, error reporting, and replay from fabric after migration.

**Verification:**
- `py -3.10 -m pytest tests/test_v3_migration.py -v`

### Task 7: Non-Commercial Release Docs

**Files:**
- Create: `LICENSE.v2.4.0-NONCOMMERCIAL-NOTICE.md`
- Create: `docs/V2.4.0_RELEASE_NOTES_DRAFT.md`
- Modify: `README.md`
- Test: `tests/test_v3_release_docs.py`

**Requirements:**
- Do not replace existing `LICENSE` in this local slice.
- Add a v2.4.0 notice that says v2.4.0 source is public source for personal, learning, research, and non-commercial self-hosting.
- State that commercial hosting, paid resale, renamed resale, SaaS resale, and selling modified builds require permission.
- README must include a short v2.4.0 notice that points to `LICENSE.v2.4.0-NONCOMMERCIAL-NOTICE.md`.
- Release notes draft must summarize v2.4.0 Foundation and list that full multi-node production transport is still future work.
- Tests must prove the notice files exist and include the required phrases.

**Verification:**
- `py -3.10 -m pytest tests/test_v3_release_docs.py -v`

### Task 8: Final Verification And Artifacts

**Files:**
- Update artifact folder on Desktop:
  - `C:\Users\孙立人\Desktop\OmbreBrain-v2.4.0-complete-artifacts`
  - `C:\Users\孙立人\Desktop\OmbreBrain-v2.4.0-complete-artifacts.zip`

**Requirements:**
- Run all v2.4.0 tests.
- Run key legacy regression tests.
- Run full test suite.
- Generate changed file list, patch, changed-files tree, and Chinese summary.
- Do not commit, push, or publish.

**Verification:**
- `py -3.10 -m pytest tests/test_v3_*.py -v`
- `py -3.10 -m pytest tests/test_permanent_breath_regression.py tests/test_letter_read_regression.py tests/test_letter_author_regression.py tests/test_security_regression.py tests/test_trace_importance_regression.py -v`
- `py -3.10 -m pytest -q`

## Self-Review

- Spec coverage: The tasks cover remaining local architecture layers from the approved v2.4.0 design: collaboration graph, cluster/consensus, snapshot/catch-up, capability catalog, hot update policy, migration, and non-commercial docs.
- Deferred: Real network RPC, UI wiring, cloud deployment, and actual release publication stay out of scope to preserve user control and avoid accidental publishing.
- Placeholder scan: No unresolved placeholder markers.
- Type consistency: All tasks build on existing `MemoryEvent`, `MemoryFabric`, `CapabilityManifest`, and `WalStore` interfaces from Foundation.
