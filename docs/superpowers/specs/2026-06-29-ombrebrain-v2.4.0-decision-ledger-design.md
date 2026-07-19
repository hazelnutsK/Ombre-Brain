# OmbreBrain v2.4.0 Decision Ledger Design

## Goal

Add a Decision Ledger and Replay Debugger to the v2.4.0 side channel so every legacy operation can carry an explainable internal decision record. The feature must not change MCP tool behavior, web routes, bucket files, embedding updates, deployment behavior, or any user-visible output.

## Scope

This phase adds audit-only decision records for the existing v2.4.0 execution chain:

`ExecutionEnvelope -> MemoryCommand -> CommandPlan -> PolicyEngine -> ProjectionAuditRuntime -> DecisionLedger -> MemoryEvent metadata`

The ledger does not become a database, scheduler, queue, authorization gate, or replacement for existing memory storage. It is a structured trace artifact attached to the v2.4.0 memory fabric event metadata.

## Components

### DecisionRecord

`DecisionRecord` is an immutable JSON-safe value object. It captures:

- Stable decision id derived from the command id, module, operation, command plan, policy verdict, projection journal, consistency report, and outcome.
- Legacy module and operation.
- Command plan snapshot.
- Policy verdict snapshot.
- Projection journal and observer snapshots.
- Consistency report snapshot.
- Outcome snapshot.
- Human-readable summary fields for explanation.

### DecisionLedger

`DecisionLedger` is a small append-oriented factory for decision records. It has no external side effects. `LegacyRuntime` uses it to build a decision record after policy and projection metadata are created, then embeds that record into the trace event metadata under `decision_record`.

### ReplayDebugger

`ReplayDebugger` performs deterministic replay checks against a serialized decision record. It does not re-execute legacy handlers. It validates internal consistency:

- command ids match across command plan, policy contract, projection journal, projection observations, and consistency report
- decision id matches the record contents
- expected projection surfaces align with journal and observation surfaces
- policy and consistency outcomes are explained in a stable structured report

## Behavior Guarantees

- Audit-only: policy denials remain informational unless existing legacy code already denied something.
- Read-only replay: the debugger does not write buckets, vectors, config, deploy files, or network resources.
- Best-effort integration: if decision recording fails, `LegacyRuntime` records `decision_error` and still appends the legacy trace event.
- JSON-safe: no unserializable Python objects enter memory fabric metadata.
- Backward compatible: existing metadata keys remain present.

## Error Handling

Decision creation sanitizes all input through strict JSON serialization. Replay reports inconsistencies as data in `issues`; it does not raise for normal mismatch cases. The only expected raised errors are invalid construction inputs for direct developer misuse.

## Testing

Tests cover:

- stable, JSON-safe `DecisionRecord` serialization
- replay success for a coherent record
- replay mismatch detection for command id drift
- explanation fields for policy/projection/consistency
- `LegacyRuntime.record_execution_event` includes `decision_record`
- `LegacyRuntime.record_tool_event` includes `decision_record`
- decision failures remain audit-only

## Non-Goals

- No commit, push, release, or cloud operation.
- No obfuscation or intentionally unreadable code.
- No change to legacy return strings, API response shapes, file formats, or deployment defaults.
