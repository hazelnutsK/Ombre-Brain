# OmbreBrain v2.4.0 Projection Runtime Design

## Purpose

Add an internal v2.4.0 projection layer that turns an existing `CommandPlan` into a durable, inspectable shadow journal and a consistency report. This layer deepens the v2.4.0 architecture without changing OmbreBrain's public behavior.

The projection layer must not write buckets, embeddings, dashboard state, deployment files, or network targets directly. Legacy code remains the source of actual side effects for this phase. v2.4.0 records what should have happened, audits whether the expected projection path was represented, and reports mismatches as metadata.

## Non-Goals

- Do not change MCP tool names, arguments, or return text.
- Do not change bucket markdown format.
- Do not change vector database behavior.
- Do not change dashboard routes or API responses.
- Do not block legacy execution because the projection layer fails.
- Do not commit, push, publish, or touch cloud infrastructure.

## Architecture

The new flow is:

`ExecutionEnvelope -> MemoryCommand -> CommandPlan -> ProjectionJournal -> ConsistencyReport`

Existing pieces:

- `ExecutionEnvelope` captures legacy module, operation, payload, actor, source, permissions, and write intent.
- `MemoryCommand` normalizes old tool/web/core intent.
- `CommandPlan` lists expected `ProjectionStep` values for fabric, buckets, vector index, dashboard, deployment, or external network.

New pieces:

- `ProjectionJournalEntry`: immutable record of one projected step.
- `ProjectionJournal`: immutable collection of projection entries for a command.
- `ProjectionRuntime`: maps each `ProjectionStep` to a journal entry with deterministic checksums and structured metadata.
- `ConsistencyReport`: immutable report describing missing, duplicate, unexpected, or mismatched projection steps.
- `ConsistencyAuditor`: compares a `CommandPlan`, `ProjectionJournal`, and optional legacy result metadata.

## Data Model

### ProjectionJournalEntry

Fields:

- `command_id`: stable command id from `CommandPlan`.
- `command_kind`: command kind value.
- `projection_kind`: fabric, bucket markdown, vector index, dashboard, deployment, external network.
- `surface`: target logical surface, such as `buckets` or `embeddings`.
- `action`: expected action, such as `upsert`, `patch`, `sync`, or `refresh`.
- `status`: one of `planned`, `observed`, `skipped`, or `failed`.
- `checksum`: deterministic checksum of the logical projection entry.
- `metadata`: sanitized structured metadata.

### ProjectionJournal

Fields:

- `command_id`
- `entries`
- `created_at`

The journal is append-style from the caller's perspective, but represented immutably in memory for this phase.

### ConsistencyReport

Fields:

- `command_id`
- `ok`
- `expected_count`
- `observed_count`
- `issues`
- `metadata`

`ok` is false only when the journal does not match the plan shape. A false report does not block legacy behavior.

## Projection Semantics

Each `CommandPlan.projections` item creates exactly one planned journal entry.

The runtime does not infer real filesystem or vector state yet. Instead, it records the planned projection shape so later stages can connect real observers. The first auditor checks shape-level consistency:

- all planned steps are present;
- no unexpected projection keys are present;
- duplicate projection keys are reported;
- failed or skipped entries are reported;
- command ids match.

Projection key:

`(projection_kind, surface, action)`

This key is stable and independent of entry ordering.

## Legacy Runtime Integration

`LegacyRuntime.record_execution_event()` should:

1. create or reuse the existing `CommandPlan`;
2. pass the plan to `ProjectionRuntime.project(plan)`;
3. pass the plan and journal to `ConsistencyAuditor.audit(plan, journal, legacy_metadata)`;
4. include both `projection_journal` and `consistency_report` in v2.4.0 trace metadata;
5. keep existing return values and exception behavior unchanged.

`LegacyRuntime.record_tool_event()` should do the same when payload already contains a `command_plan`, or reconstruct a plan through the existing command bridge if possible.

All projection work is best effort. If projection or audit fails, legacy execution continues and only a warning is logged.

## Error Handling

- Projection runtime errors are captured as best-effort failures by the caller.
- Invalid or unknown projection kinds are represented as failed report issues when possible.
- Metadata is sanitized through existing command payload rules where possible.
- Auditor errors must not block legacy handlers or tool responses.

## Testing

Add focused tests:

- `tests/test_v3_projection_runtime.py`
  - creates one journal entry per planned projection step;
  - produces deterministic checksums;
  - serializes journal entries as JSON-safe dictionaries;
  - does not mutate the input `CommandPlan`.

- `tests/test_v3_consistency_auditor.py`
  - reports ok for a complete matching journal;
  - reports missing projection steps;
  - reports duplicate projection steps;
  - reports unexpected projection steps;
  - reports command id mismatch.

Extend existing runtime tests:

- verify `LegacyRuntime.record_execution_event()` metadata includes `projection_journal` and `consistency_report`;
- verify tool event recording remains best effort and external payload return behavior is unchanged.

Required verification:

- new projection tests;
- affected legacy runtime/tool tests;
- all `test_v3_*.py`;
- full test suite.

## Acceptance Criteria

- v2.4.0 has a projection package with journal, runtime, and auditor.
- command plans can be converted to shadow projection journals.
- consistency reports are attached to v2.4.0 metadata.
- projection/audit failures do not change legacy behavior.
- full test suite passes.
