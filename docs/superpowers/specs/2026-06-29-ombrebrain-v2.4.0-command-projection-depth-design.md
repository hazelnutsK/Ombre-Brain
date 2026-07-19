# OmbreBrain v2.4.0 Command Projection Depth Design

## Goal

Deepen v2.4.0 internals without changing existing Ombre Brain behavior. Legacy MCP
tools, dashboard routes, markdown bucket files, config, deploy entrypoints, and
visible return text remain unchanged.

## Design

Add a domain layer between legacy execution envelopes and v2.4.0 fabric events:

- `MemoryCommand` represents user-visible intent such as hold, breath, trace,
  import, migrate, decay, or sync.
- `CommandPolicy` evaluates invariant rules before a command is projected.
- `ProjectionPlan` describes which surfaces the command affects: fabric event,
  markdown bucket, vector index, dashboard state, deployment state, or external
  network.
- `MemoryCommandRouter` converts commands into a deterministic `CommandPlan`.
- `LegacyCommandBridge` maps legacy `ExecutionEnvelope` instances into domain
  commands and embeds the plan in v2.4.0 trace metadata.

## Invariants

- Permanent memory is non-decaying.
- Feel memory does not appear in ordinary breath.
- Plan memory is lifecycle-driven by status, not by decay.
- Letter memory preserves raw text.
- Trace delete affects bucket and vector projection.
- Hot update and deployment surfaces remain policy-controlled.

## Non-Goals

- Do not change legacy runtime outputs.
- Do not replace markdown buckets with fabric as the visible data layer yet.
- Do not add networked multi-node production transport in this phase.
- Do not add code obfuscation.

## Success Criteria

- New command/projection tests prove deterministic command ids, projection plans,
  and invariant rules.
- Legacy execution trace events include command plan metadata.
- Full v2.4.0 and legacy regression tests still pass.
