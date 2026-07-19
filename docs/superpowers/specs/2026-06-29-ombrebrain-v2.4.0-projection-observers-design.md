# OmbreBrain v2.4.0 Projection Observers Design

## Purpose

Extend the v2.4.0 projection system from a shadow journal into a read-only real-state audit layer. Projection observers inspect existing legacy state after legacy code has already done its work, then the consistency auditor compares the observed state with the expected projection plan.

The layer must remain observational in this phase. It may read bucket markdown, embedding metadata, dashboard/config snapshots, and deployment/config paths, but it must not write files, mutate vectors, call network services, rebuild indexes, or change public API output.

## Non-Goals

- Do not change MCP tool names, arguments, return text, or error behavior.
- Do not change bucket markdown format.
- Do not generate, delete, rebuild, or migrate embeddings.
- Do not refresh, rewrite, or serve dashboard state differently.
- Do not mutate deploy files, config files, secrets, or cloud resources.
- Do not block legacy execution because an observer cannot read a surface.
- Do not commit, push, publish, or touch cloud infrastructure.

## Current Foundation

Existing v2.4.0 flow:

`ExecutionEnvelope -> MemoryCommand -> CommandPlan -> ProjectionJournal -> ConsistencyReport`

The current `ProjectionRuntime` creates planned journal entries from `CommandPlan`. The current `ConsistencyAuditor` checks the shape of the journal against the plan.

New B flow:

`ExecutionEnvelope -> MemoryCommand -> CommandPlan -> ProjectionJournal -> ProjectionObservations -> Real ConsistencyReport`

## Architecture

Add a focused observer layer under `src/ombrebrain/projection/`:

- `observation.py`
  - `ObservationStatus`
  - `ProjectionObservation`
  - `ProjectionObservationSet`

- `observers.py`
  - `BucketProjectionObserver`
  - `VectorProjectionObserver`
  - `DashboardProjectionObserver`
  - `DeploymentProjectionObserver`
  - `ProjectionObserverRegistry`

- `audit_runtime.py`
  - `ProjectionAuditRuntime`

Existing files to extend:

- `auditor.py`
  - Add `audit_with_observations(plan, journal, observations, legacy_metadata=None)`.
  - Keep existing `audit(plan, journal, legacy_metadata=None)` behavior.

- `legacy_runtime.py`
  - Add optional observer registry/audit runtime fields.
  - Include `projection_observations` and a real-state `consistency_report` in v2.4.0 metadata when observers are available.
  - Continue best-effort behavior.

## Data Model

### ProjectionObservation

Fields:

- `projection_kind`
- `surface`
- `action`
- `status`: `observed`, `missing`, `unknown`, or `failed`
- `subject`: specific bucket id, vector id, dashboard route, deployment path, or empty string
- `metadata`: JSON-safe read-only details

Projection key remains:

`(projection_kind, surface, action)`

### ProjectionObservationSet

Fields:

- `command_id`
- `observations`
- `created_at`

The observation set is immutable and JSON-safe.

## Observer Semantics

### BucketProjectionObserver

Inputs:

- optional `bucket_manager`
- optional command payload metadata

Rules:

- For `bucket_markdown` actions `upsert` or `patch`, try to read `bucket_id` using `bucket_manager.get(bucket_id)` if a bucket id is present.
- For `archive`, treat a missing `bucket_manager.get(bucket_id)` result as `unknown` unless archive path metadata is explicitly available. This avoids mistaking hidden archived buckets for missing active buckets.
- If no bucket id is present, return `unknown`.
- Never call create/update/delete/search.

### VectorProjectionObserver

Inputs:

- optional `embedding_engine`
- optional command payload metadata

Rules:

- For `vector_index` actions, only inspect available read methods.
- Prefer `get_embedding(bucket_id)` when available.
- Fall back to `list_all_ids()` when available.
- If embedding engine is absent or disabled, return `unknown`.
- Never call `generate_and_store`, `delete_embedding`, migration, or search methods.

### DashboardProjectionObserver

Inputs:

- optional config snapshot

Rules:

- For `dashboard_state` projections, report `observed` when a config snapshot exists and contains known dashboard-relevant keys.
- Otherwise report `unknown`.
- Do not make HTTP requests or call route handlers.

### DeploymentProjectionObserver

Inputs:

- optional config snapshot

Rules:

- For `deployment_state` projections, inspect configured static metadata only.
- Return `unknown` if no deployment snapshot is available.
- Do not read secrets, deploy to cloud, run shell scripts, or edit files.

## Audit Semantics

`ConsistencyAuditor.audit_with_observations()` should:

1. Run the existing journal-vs-plan audit.
2. Compare observation keys with planned projection keys.
3. Add issues for:
   - `missing_observation` when a planned key has no observation.
   - `observer_missing_projection` when observer reports missing.
   - `observer_failed` when observer reports failed.
   - `unexpected_observation` when observer reports a key not planned.
4. Treat `unknown` as non-blocking metadata, not a hard failure.

This is intentionally conservative: unknown means "not observable yet", not "broken".

## Legacy Runtime Integration

`LegacyRuntime` should pass read-only runtime surfaces into the observer registry when available:

- `bucket_manager`
- `embedding_engine`
- `config_snapshot`

For this phase, existing callers that do not inject those surfaces still work. Observations may be unknown, and old behavior remains unchanged.

Event metadata should include:

- `projection_journal`
- `projection_observations`
- `consistency_report`

If observation fails, metadata should include a sanitized observer error and legacy execution should continue.

## Testing

Add focused tests:

- `tests/test_v3_projection_observers.py`
  - bucket observer reads via fake `get()` and reports observed/missing/unknown.
  - vector observer reads via fake `get_embedding()` or `list_all_ids()`.
  - dashboard observer returns observed from config snapshot.
  - registry dispatches one observation per observable projection.

- Extend `tests/test_v3_consistency_auditor.py`
  - `audit_with_observations()` accepts matching observations.
  - reports missing observations.
  - reports failed/missing observer results.
  - ignores unknown observations as non-blocking.

- Extend `tests/test_v3_legacy_runtime.py`
  - event metadata includes `projection_observations`.
  - observer failures do not prevent legacy event append.

Required verification:

- new observer tests;
- affected auditor/runtime tests;
- all `test_v3_*.py`;
- full test suite.

## Acceptance Criteria

- v2.4.0 has read-only projection observers and an observation set model.
- observer registry can produce observations from a `CommandPlan` and `ProjectionJournal`.
- auditor can combine planned journal checks with real observation checks.
- legacy metadata contains observations when available.
- no observer writes to bucket/vector/dashboard/deploy surfaces.
- full test suite passes.
