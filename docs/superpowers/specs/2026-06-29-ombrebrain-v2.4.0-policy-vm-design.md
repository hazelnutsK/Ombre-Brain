# OmbreBrain v2.4.0 Policy VM Design

## Purpose

Add an internal policy virtual machine that evaluates memory commands, capability contracts, module profiles, static surfaces, and projection plans before they are recorded into v2.4.0 metadata. This deepens the v2.4.0 architecture without changing OmbreBrain's public behavior.

The Policy VM is an audit and contract layer in this phase. It produces structured verdicts that are attached to v2.4.0 events. It does not block legacy tools, web routes, bucket writes, vector writes, hot-update planning, or deployment behavior.

## Non-Goals

- Do not change MCP tool names, arguments, return text, or error behavior.
- Do not change dashboard/API routes or responses.
- Do not change bucket markdown format.
- Do not apply or reject real hot updates differently from existing `update_policy.py`.
- Do not mutate config, buckets, vector DB, secrets, deploy files, or cloud resources.
- Do not commit, push, publish, or touch cloud infrastructure.

## Current Foundation

Current v2.4.0 flow:

`ExecutionEnvelope -> MemoryCommand -> CommandPlan -> ProjectionJournal -> ProjectionObservations -> ConsistencyReport`

Existing inputs:

- `LegacyModuleProfile`: module responsibilities, side effects, protected surfaces, permissions, and safety tier.
- `CapabilityManifest`: capability permissions, dependencies, write behavior, cluster safety, and hot-update safety.
- `StaticSurfaceDecision`: path risk and protected surface classification.
- `CommandPlan`: expected projection side effects for a command.

New C flow:

`MemoryCommand -> CapabilityContract -> PolicyProgram -> PolicyVM -> SurfaceAccessVerdict -> CommandPlan -> ProjectionRuntime`

## Architecture

Add a focused policy VM package under `src/ombrebrain/policy/`:

- `contracts.py`
  - `CapabilityContract`
  - `SurfaceAccess`
  - `SurfaceAccessVerdict`

- `vm.py`
  - `PolicyOpcode`
  - `PolicyInstruction`
  - `PolicyProgram`
  - `PolicyVM`

- `engine.py`
  - `PolicyEngine`
  - builds a contract from a command plan, module profile, capability manifests, and optional static surface decisions
  - compiles policy instructions
  - returns a verdict dictionary for v2.4.0 metadata

Existing files to extend:

- `legacy_runtime.py`
  - hold a `PolicyEngine`
  - include `policy_verdict` in execution/tool event metadata
  - keep legacy behavior unchanged when policy verdict is denied or warning-only

- `__init__.py` under `src/ombrebrain/policy/`
  - export new policy VM types

## Data Model

### CapabilityContract

Fields:

- `command_id`
- `command_kind`
- `module`
- `operation`
- `permissions`
- `required_permissions`
- `capabilities`
- `side_effects`
- `protected_surfaces`
- `writes_memory`
- `projection_surfaces`
- `hot_update_safe`
- `cluster_safe`
- `metadata`

The contract is JSON-safe and immutable.

### SurfaceAccessVerdict

Fields:

- `allowed`: bool
- `severity`: `allow`, `warn`, or `deny`
- `reasons`
- `required_permissions`
- `missing_permissions`
- `protected_surfaces`
- `projection_surfaces`
- `metadata`

In this phase, `allowed=False` means policy would deny the operation if enforcement were enabled, but legacy execution remains unchanged.

### PolicyInstruction

Supported opcodes:

- `REQUIRE_PERMISSION`
- `WARN_PROTECTED_SURFACE`
- `DENY_PROTECTED_WRITE`
- `WARN_HOT_UPDATE_UNSAFE`
- `WARN_CLUSTER_UNSAFE`
- `ALLOW`

The instruction set is intentionally small. It can express the current OB safety rules without becoming a second implementation of all business logic.

## Policy Semantics

Policy VM evaluates a compiled program:

1. Missing required permissions create a deny issue.
2. Protected surfaces create warning issues.
3. Writes to protected surfaces create deny issues.
4. Hot-update unsafe capabilities create warning issues.
5. Cluster-unsafe capabilities create warning issues.
6. If there are no deny issues, the verdict is allowed.

The VM does not mutate inputs and does not call legacy handlers.

## Runtime Integration

`LegacyRuntime.record_execution_event()` should:

1. create the existing `CommandPlan`;
2. evaluate policy using envelope + command plan + module profile;
3. attach `policy_verdict` to metadata;
4. continue projection/audit metadata as before.

`LegacyRuntime.record_tool_event()` should:

1. create or reconstruct an `ExecutionEnvelope`;
2. create the existing `CommandPlan`;
3. evaluate policy;
4. attach `policy_verdict`;
5. preserve existing `legacy_payload`, `command_plan`, `projection_journal`, `projection_observations`, and `consistency_report`.

Policy failures are best effort. Errors become `policy_error` metadata and do not change legacy behavior.

## Testing

Add focused tests:

- `tests/test_v3_policy_contracts.py`
  - contract is immutable and JSON-safe;
  - contract can be built from a command plan and envelope-like data;
  - verdict serializes missing permissions and protected surfaces.

- `tests/test_v3_policy_vm.py`
  - VM allows matching permissions;
  - VM denies missing required permission;
  - VM warns protected surface read/observe;
  - VM denies protected surface write;
  - VM warns hot-update unsafe and cluster-unsafe capabilities.

- `tests/test_v3_policy_engine.py`
  - engine maps command projections into surface access;
  - engine incorporates module profile permissions and protected surfaces;
  - engine output is JSON-safe.

Extend existing tests:

- `tests/test_v3_legacy_runtime.py`
  - execution event metadata includes `policy_verdict`;
  - tool event metadata includes `policy_verdict`;
  - policy deny does not prevent fabric append.

Required verification:

- new policy tests;
- affected legacy runtime tests;
- all `test_v3_*.py`;
- full test suite.

## Acceptance Criteria

- v2.4.0 has a policy VM with contracts, instructions, programs, and verdicts.
- policy engine can evaluate legacy execution/tool events from existing v2.4.0 command plans.
- policy verdict metadata is attached to v2.4.0 events.
- denied verdicts remain audit-only and do not change OB external behavior.
- full test suite passes.
