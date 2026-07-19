# OmbreBrain v2.4.0 Total Hardening Design

## Goal

Raise the remaining legacy code to the v2.4.0 architecture level without changing
Ombre Brain's external behavior, file formats, MCP tool names, dashboard routes,
or deployment defaults.

## Boundary

- Keep the existing memory purpose: durable first-person emotional memory,
  surfacing, decay, import, migration, dashboard, and self-host deployment.
- Do not add artificial obfuscation or hidden behavior.
- Do not touch any cloud server, remote GitHub state, commits, tags, or releases.
- Keep legacy APIs stable so existing tests and current users keep working.

## Architecture

This phase adds an advanced legacy execution layer around the remaining modules:

- `ExecutionEnvelope` describes an operation with actor, module, capability,
  permissions, payload, protected paths, and feature flags.
- `LegacyExecutionPipeline` validates, authorizes, executes, records, and
  returns the original result unchanged.
- `LegacyModuleProfile` declares each legacy module's v2.4.0 contract, side effects,
  safety tier, and protected surfaces.
- `LegacyRuntime` owns this profile registry and records execution outcomes into
  the v2.4.0 fabric as internal trace events.

The legacy modules opt into this layer through a small `attach_v3_runtime`
surface. Their public constructors and methods remain compatible.

## Modules Covered

- Core engines: `decay_engine.py`, `dehydrator.py`, `embedding_engine.py`,
  `import_memory.py`, `migrate_engine.py`, `migration_engine.py`,
  `github_sync.py`.
- Runtime gateways: `tools/_runtime.py`, `web/_shared.py`.
- App wiring: `server.py`, `ombrebrain/app/legacy_wiring.py`.
- Static surfaces tracked by profile: `src/tools/*`, `src/web/*`,
  `frontend/dashboard.html`, `deploy/*`, `Dockerfile`, config templates.

## Behavioral Contract

- A missing v2.4.0 runtime must behave as a no-op.
- A v2.4.0 recording failure must never break legacy behavior.
- Handler return values must pass through unchanged.
- Handler exceptions must be re-raised unchanged after best-effort recording.
- Sensitive payload fields must be redacted before fabric recording.
- Hot-update protected surfaces remain protected: config, buckets, vector DB,
  OAuth/session secrets, deployment user overrides, unsafe paths.
