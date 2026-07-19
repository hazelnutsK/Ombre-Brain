# OmbreBrain v2.4.0 Final Hardening Design

## Goal

Complete the remaining F -> G -> H -> I -> J sequence for the local v2.4.0 architecture work:

- F: architecture audit and boundary tightening
- G: stability hardening
- H: maintainer tools
- I: architecture documentation and boundary diagrams
- J: pre-release acceptance package

The work remains local-only. It must not commit, push, publish, release, or touch any cloud server.

## Design Principles

- Preserve existing Ombre Brain external behavior.
- Add internal audit/reporting/maintenance layers instead of rewriting legacy paths.
- Keep all new tooling read-only unless a test explicitly proves it only writes generated report files.
- Prefer structured reports over free-form logs.
- Make future Codex maintenance easier by encoding architecture boundaries as data and tests.

## F: Architecture Audit

Add `ombrebrain.architecture` with static component descriptors and an auditor. It records component layer, ownership, dependencies, side-effect mode, and protected surfaces.

The auditor reports:

- unknown dependencies
- dependency cycles
- read-only components claiming write surfaces
- multiple write owners for protected surfaces
- missing critical v2.4.0 components

The default graph should pass, creating a living architecture contract.

## G: Stability Hardening

Add `ombrebrain.resilience` with read-only health scanners for:

- WAL presence and replay integrity
- decision record health
- policy/projection metadata shape
- v2.4.0 runtime availability

Scanners must catch integrity and parsing failures as structured findings. They must not mutate WAL files or bucket files.

## H: Maintainer Tools

Add `ombrebrain.maintenance` and a local CLI:

- `tools/v3_health_report.py`

The tool generates JSON health/debug reports from a buckets directory. It reuses architecture and resilience scanners plus DecisionDebugService. It is safe for Codex maintenance sessions and works offline.

## I: Architecture Documentation

Add formal docs:

- `docs/V2.4.0_ARCHITECTURE.md`
- `docs/V2.4.0_BOUNDARY_MAP.md`

They document execution flow, command/projection/policy/decision/replay layers, protected surfaces, read-only versus write paths, and the Dashboard debug view.

## J: Pre-Release Acceptance Package

Add final release-prep docs:

- `docs/V2.4.0_ACCEPTANCE_CHECKLIST.md`
- `docs/V2.4.0_ROLLBACK.md`
- update `docs/V2.4.0_RELEASE_NOTES_DRAFT.md`

The acceptance package states exactly what changed, what stayed unchanged, how to verify locally, and how to roll back by removing v2.4.0 side-channel files or reverting code before publication.

## Testing

Add focused tests for:

- architecture auditor
- resilience scanner
- maintenance report CLI
- architecture docs
- acceptance package

Then run all v2.4.0 tests and the full suite.

## Non-Goals

- No production multi-node networking.
- No writable Dashboard maintenance action.
- No direct GitHub upload or release.
- No cloud server operation.
- No intentional obfuscation.
