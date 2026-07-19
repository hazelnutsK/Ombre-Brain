# OmbreBrain v2.4.0 Architecture Design

Date: 2026-06-28
Base version: v2.3.22
Target version: v2.4.0
Status: Design approved for spec review

## 1. Product Constitution

OmbreBrain v2.4.0 must remain memory-first, AI-native, and user-owned.

The goal is not to turn OmbreBrain into a generic distributed database or a commercial cloud platform. The goal is to give AI a durable, inspectable, user-controlled long-term memory system with breath-style maintenance, tool collaboration, safe hot updates, and a warm personal experience.

The architecture may become significantly more advanced, but the product experience must stay simple:

- A normal user can still run one local node without understanding consensus, WAL, snapshots, quorum, or cluster terms.
- Advanced users can enable a multi-node cluster when they need synchronization, redundancy, or collaborative AI memory.
- Dynamic memory, permanent memory, trace, letter, plan, bucket, vector search, MCP, OAuth, and web dashboard remain OmbreBrain's main functional surface.
- User data ownership has priority over update convenience. Config files, secrets, bucket data, vector database files, OAuth secrets, and local port settings must not be overwritten by hot updates.
- Complexity belongs behind clear interfaces. v2.4.0 may use advanced architecture, but it must not rely on intentionally unreadable or unmaintainable code.

## 2. License And Distribution Boundary

OmbreBrain v2.4.0 should move from permissive open-source positioning to public source with a non-commercial boundary.

Intended permission model:

- Allowed: personal use, learning, research, private experimentation, non-commercial self-hosting.
- Prohibited: commercial hosting, paid resale, renamed resale, SaaS resale, selling modified builds, and using OmbreBrain as the core of a paid service without permission.
- Required: attribution and preservation of license notices.

The implementation should update `LICENSE`, `README.md`, release notes, and project metadata so that users do not mistake v2.4.0 for MIT-style commercial-permissive software.

PolyForm Noncommercial can be used as a reference model, but the final license text should be reviewed separately. This design is not legal advice.

## 3. Top-Level Architecture

v2.4.0 reorganizes the project around five core systems:

```text
Ombre Kernel
Memory Fabric
Cluster Fabric
Collaboration Graph
Capability System
```

The expected package layout is:

```text
src/ombrebrain/
  kernel/
    runtime.py
    registry.py
    events.py
    context.py
    errors.py

  protocol/
    schemas.py
    manifests.py
    contracts.py

  fabric/
    log/
      wal.py
      segment.py
      snapshot.py
      compaction.py
    storage/
      engine.py
      bucket_store.py
      vector_store.py
      manifest_store.py

  cluster/
    node.py
    membership.py
    consensus.py
    raft/
      leader.py
      log.py
      quorum.py
      snapshot.py
      transport.py
    replication/
      planner.py
      apply.py
      catchup.py
    safety/
      term.py
      fence.py
      integrity.py

  collab/
    actor.py
    event.py
    graph.py
    merge_policy.py
    provenance.py
    visibility.py
    indexing.py

  capabilities/
    mcp/
    tools/
    web/
    oauth/
    hot_update/
    deployment/

  policy/
    license_policy.py
    update_policy.py
    security_policy.py

  app/
    server.py
    cli.py
```

Existing modules can be migrated incrementally, but the public direction is clear: application entry points call the Kernel, the Kernel calls registered capabilities, and durable memory changes flow through the Collaboration Graph and Memory Fabric.

## 4. Ombre Kernel

The Kernel is the runtime coordinator. It owns startup, dependency wiring, lifecycle, configuration snapshots, capability registration, and error normalization.

Primary responsibilities:

- Load and validate configuration without leaking secrets into logs or cluster state.
- Create an `OmbreContext` for each request, including identity, source, request id, config snapshot, and capability scope.
- Register tools, MCP routes, dashboard APIs, OAuth controls, deployment controls, hot update operations, and memory operations as capabilities.
- Convert user/tool/API actions into typed protocol commands.
- Emit internal events for observability and testing.
- Enforce policy before writes, updates, and sensitive operations.

The Kernel must not directly embed memory storage details, vector indexing details, or cluster transport details. It should use protocol interfaces.

## 5. Memory Fabric

Memory Fabric is the durable storage engine for OmbreBrain memory.

It is not a general SQL database. It is an append-oriented memory engine optimized for AI memory events, provenance, snapshots, bucket views, and vector index rebuilds.

Core components:

- WAL: append-only write-ahead log for memory events and metadata events.
- Segment files: bounded log files with checksums and version headers.
- Snapshots: compacted state for fast startup and follower catch-up.
- Compaction: safe cleanup of old segments once snapshots cover them.
- Bucket store: materialized bucket view derived from committed events.
- Vector store adapter: local vector index derived from committed events.
- Manifest store: version, migration, hot update, and cluster metadata.

The source of truth is the committed event log plus snapshots. Vector indexes are derived views and must be rebuildable.

## 6. Cluster Fabric

v2.4.0 supports multi-node synchronization and consensus.

The first supported cluster target is a three-node deployment:

```text
1 leader + 2 followers
```

Cluster responsibilities:

- Node identity, membership, heartbeat, and health state.
- Leader election.
- Replicated log.
- Majority quorum commit.
- Term/index safety.
- Leader fencing.
- Snapshot install and restore.
- Follower catch-up.
- Hash-chain integrity checks.
- Cluster-aware hot update manifest replication.

Strongly consistent objects:

- Memory events.
- Bucket metadata.
- Dynamic and permanent memory writes.
- Trace, letter, plan, and tool-derived memory events.
- Capability manifests.
- Hot update manifests.
- Migration state.
- Cluster membership state.

Local-only objects:

- `config.yaml`.
- `.env`.
- OAuth secrets.
- API keys.
- Local dashboard port mapping.
- Local filesystem paths.
- User-private runtime overrides.

Derived objects:

- Vector index files.
- Search caches.
- Dashboard summaries.
- Diagnostic reports.

Derived objects are rebuilt from committed events and snapshots. They are not directly replicated through consensus.

## 7. Consensus Model

The design should use a Raft-style consensus model.

Required behaviors:

- Every write goes through the leader.
- The leader appends a log entry and replicates it to followers.
- An entry is committed only after majority acknowledgement.
- Committed entries are applied to Memory Fabric in log order.
- Followers reject entries from stale terms.
- A leader cannot serve writes after losing leadership.
- A lagging node catches up through missing log entries or snapshot install.
- Startup validates term, last index, snapshot metadata, and hash chain.

Read policy:

- Default reads go to the leader for freshest behavior.
- Follower stale reads may be added later as an explicit optimization.
- Local diagnostic reads may inspect local state but must label themselves as local.

Failure model:

- Single follower failure should not stop writes in a three-node cluster.
- Leader failure should trigger election.
- Network partition should only allow the majority side to commit writes.
- Rejoining nodes must catch up before serving cluster reads.

## 8. Collaboration Graph

Collaboration Graph turns memory from plain text records into AI-native collaborative events.

Every write becomes a structured event:

```text
MemoryEvent
  id
  actor
  actor_name
  session_id
  task_id
  parent_event_ids
  memory_type
  content
  confidence
  importance
  visibility
  created_at
  source_chain
  vector_state
  cluster_term
  cluster_index
```

Actor examples:

- user
- codex
- claude
- gpt
- gemini
- mcp_tool
- web_dashboard
- system

Collaboration rules:

- Conflicting memories are not blindly overwritten.
- A conflict record is created when two events disagree on the same durable claim.
- Merge policy can keep both, merge them, downgrade one, mark one stale, or request human review.
- Tool output keeps provenance: tool name, source route, input summary, model actor, and task id.
- Letters, plans, trace records, breath results, and permanent memories share one event model.

This preserves OmbreBrain's original memory purpose while allowing multiple AI agents and tools to work in the same memory space.

## 9. Capability System

Capabilities are registered modules with typed manifests and contracts.

Examples:

- MCP aggregation.
- Tool search.
- Breath tools.
- Trace tools.
- Letter tools.
- OAuth controls.
- Dashboard controls.
- Hot update.
- Deployment helpers.
- Local Ollama/Gemini/OpenAI-compatible providers.

A capability must declare:

- Name and version.
- Required permissions.
- Input and output schemas.
- Whether it can write memory.
- Whether it is cluster-safe.
- Whether it can run during hot update.
- Dependencies on other capabilities.

The Kernel registry loads capabilities and rejects incompatible versions before runtime.

## 10. Hot Update Policy

Hot update becomes manifest-driven.

Update manifest fields:

- Version.
- Source commit or release id.
- File list.
- Hashes.
- Protected path rules.
- Migration plan.
- Rollback plan.
- Minimum compatible current version.
- Cluster rollout strategy.

Protected paths:

- `config.yaml`.
- `.env`.
- `buckets/`.
- vector database files.
- OAuth secrets.
- deployment user overrides.
- local runtime data.

Cluster rollout:

- Leader commits the update manifest first.
- Followers verify hashes and compatibility.
- Nodes apply the update only after policy approval.
- If a node fails update verification, it must stay out of service until repaired or rolled back.

## 11. Security And Integrity

Required safeguards:

- Cluster token or node certificate for node admission.
- Signed or hash-verified manifests.
- Hash chain across replicated log segments.
- Path traversal protection for update extraction and file operations.
- Redaction for secrets in logs and diagnostics.
- Policy checks before memory writes, tool execution, OAuth changes, and deployment changes.

Security should protect users from accidental data loss and unauthorized cluster mutation. It is not intended to provide enterprise multi-tenant isolation in the first v2.4.0 release.

## 12. Error Handling

Errors should be typed and user-actionable.

Error categories:

- ConfigError.
- CapabilityLoadError.
- PolicyViolation.
- ClusterUnavailable.
- NotLeader.
- QuorumTimeout.
- LogIntegrityError.
- SnapshotRestoreError.
- VectorRebuildError.
- HotUpdateRejected.
- MigrationFailed.

Dashboard and CLI messages should explain what happened and what the user can safely do next. Internal stack traces may be preserved in diagnostics but should not expose secrets.

## 13. Migration From v2.3.22

Migration should be staged:

1. Introduce new package skeleton and compatibility adapters.
2. Wrap existing memory operations behind Memory Fabric interfaces.
3. Convert existing writes into `MemoryEvent`.
4. Add single-node log and snapshot mode.
5. Add cluster transport and three-node Raft-style replication.
6. Move MCP, web, OAuth, deployment, and hot update into capabilities.
7. Add manifest-driven release and update flow.
8. Update license, README, changelog, and release docs.
9. Retain compatibility entry points where practical.

Existing user data must be backed up before migration. Migration should create a report that lists converted buckets, vector rebuild status, skipped local-only files, and any manual actions.

## 14. Testing Strategy

v2.4.0 requires tests at several levels.

Unit tests:

- Kernel registry.
- Capability manifest validation.
- MemoryEvent schema.
- WAL append/read.
- Segment checksum.
- Snapshot metadata.
- Merge policy.
- Update policy.

Integration tests:

- Dynamic memory write and read.
- Permanent memory write and read.
- Trace importance behavior.
- Letter author behavior.
- MCP tool aggregation.
- OAuth enable/disable.
- Dashboard port configuration.
- Hot update protected path behavior.

Cluster simulation tests:

- Leader election.
- Follower catch-up.
- Leader crash and re-election.
- Log replication.
- Majority partition.
- Minority partition rejection.
- Snapshot install.
- Corrupt log detection.
- Duplicate write idempotency.

Migration tests:

- v2.3.22 data converts to v2.4.0 event model.
- Vector index can be rebuilt.
- Config and secrets are not copied into cluster log.
- Rollback report is generated when migration fails.

## 15. Non-Goals For First v2.4.0

The first v2.4.0 release should not attempt:

- SQL compatibility.
- Full OLTP database behavior.
- Global multi-region consensus.
- Hosted commercial cloud control plane.
- Enterprise multi-tenant billing.
- Arbitrary plugin marketplace execution.
- Secret synchronization through cluster logs.
- Follower stale reads as default behavior.

These are outside the first architecture pass because they do not serve OmbreBrain's core memory-first purpose.

## 16. Success Criteria

The v2.4.0 architecture is successful when:

- A single-node user can still run OmbreBrain without cluster knowledge.
- A three-node cluster can replicate committed memory events.
- Dynamic and permanent reads still match expected behavior.
- Vector indexes can be rebuilt from committed memory events.
- Hot updates protect config, buckets, vector data, secrets, and local overrides.
- Multiple AI/tool actors can write traceable memory events.
- The codebase has clearer module boundaries than v2.3.22.
- The public license boundary clearly forbids commercial resale and hosted resale.
- Tests cover the main regression, migration, cluster, and update paths.

## 17. Review Gate

This document is the design spec for OmbreBrain v2.4.0 architecture work. Implementation should not begin until the spec has been reviewed and approved.

After approval, the next step is to produce a detailed implementation plan with milestones, file-level changes, tests, and rollback checkpoints.
