# OmbreBrain v2.4.0 Final Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete F -> G -> H -> I -> J as local-only v2.4.0 architecture hardening, maintainer tooling, documentation, and release-prep artifacts.

**Architecture:** F adds a data-backed architecture contract, G adds read-only resilience scanners, H packages those scanners into an offline maintainer report tool, I writes formal architecture docs, and J writes pre-release acceptance materials. None of these stages changes legacy MCP tools, bucket markdown, embedding behavior, Dashboard existing routes, or deployment behavior.

**Tech Stack:** Python dataclasses, JSON-safe structured reports, existing MemoryFabric and DecisionDebugService, standalone Python CLI tools, Markdown docs, pytest.

---

### Task F: Architecture Audit

**Files:**
- Create: `src/ombrebrain/architecture/__init__.py`
- Create: `src/ombrebrain/architecture/contracts.py`
- Create: `src/ombrebrain/architecture/defaults.py`
- Create: `src/ombrebrain/architecture/auditor.py`
- Test: `tests/test_v3_architecture_audit.py`

- [ ] **Step 1: Write failing tests** for default architecture passing, duplicate write ownership detection, read-only write-surface detection, and missing critical component detection.
- [ ] **Step 2: Run tests** with `py -3.10 -m pytest tests\test_v3_architecture_audit.py -q`; expect import failure.
- [ ] **Step 3: Implement the architecture package** with immutable descriptors and structured audit reports.
- [ ] **Step 4: Run F tests** and proceed only if passing.

### Task G: Stability Hardening

**Files:**
- Create: `src/ombrebrain/resilience/__init__.py`
- Create: `src/ombrebrain/resilience/scanner.py`
- Test: `tests/test_v3_resilience_scanner.py`

- [ ] **Step 1: Write failing tests** for clean runtime health, corrupt WAL reporting, decision problems being surfaced, and side-effect-free scanning.
- [ ] **Step 2: Run tests** with `py -3.10 -m pytest tests\test_v3_resilience_scanner.py -q`; expect import failure.
- [ ] **Step 3: Implement scanner** catching integrity errors as findings.
- [ ] **Step 4: Run G tests** and proceed only if passing.

### Task H: Maintainer Tools

**Files:**
- Create: `src/ombrebrain/maintenance/__init__.py`
- Create: `src/ombrebrain/maintenance/report.py`
- Create: `tools/v3_health_report.py`
- Test: `tests/test_v3_maintenance_report.py`

- [ ] **Step 1: Write failing tests** for report shape and CLI help/output.
- [ ] **Step 2: Run tests** with `py -3.10 -m pytest tests\test_v3_maintenance_report.py -q`; expect import failure.
- [ ] **Step 3: Implement report builder and CLI** using architecture audit, resilience scanner, and debug decision listing.
- [ ] **Step 4: Run H tests** and proceed only if passing.

### Task I: Architecture Docs

**Files:**
- Create: `docs/V2.4.0_ARCHITECTURE.md`
- Create: `docs/V2.4.0_BOUNDARY_MAP.md`
- Test: `tests/test_v3_architecture_docs.py`

- [ ] **Step 1: Write failing doc tests** requiring execution flow, command/projection/policy/decision/replay, protected surfaces, read-only paths, and maintenance commands.
- [ ] **Step 2: Run tests** with `py -3.10 -m pytest tests\test_v3_architecture_docs.py -q`; expect missing docs failure.
- [ ] **Step 3: Write docs** with diagrams and boundary tables.
- [ ] **Step 4: Run I tests** and proceed only if passing.

### Task J: Pre-Release Acceptance Package

**Files:**
- Create: `docs/V2.4.0_ACCEPTANCE_CHECKLIST.md`
- Create: `docs/V2.4.0_ROLLBACK.md`
- Modify: `docs/V2.4.0_RELEASE_NOTES_DRAFT.md`
- Test: `tests/test_v3_release_acceptance.py`

- [ ] **Step 1: Write failing tests** requiring acceptance checklist, rollback instructions, full test commands, no-cloud/no-push note, and release note coverage through E/F/G/H/I/J.
- [ ] **Step 2: Run tests** with `py -3.10 -m pytest tests\test_v3_release_acceptance.py -q`; expect missing docs failure.
- [ ] **Step 3: Write acceptance package and update release draft**.
- [ ] **Step 4: Run J tests** and proceed only if passing.

### Task Final Verification and Artifacts

**Files:**
- Update complete artifacts summary and verification files
- Regenerate complete diff and zip

- [ ] **Step 1: Run focused final tests**

`py -3.10 -m pytest tests\test_v3_architecture_audit.py tests\test_v3_resilience_scanner.py tests\test_v3_maintenance_report.py tests\test_v3_architecture_docs.py tests\test_v3_release_acceptance.py -q`

- [ ] **Step 2: Run all v2.4.0 tests**

`$files = @(Get-ChildItem -Path tests -Filter 'test_v3_*.py' | ForEach-Object { $_.FullName }); py -3.10 -m pytest @files -q`

- [ ] **Step 3: Run full suite**

`py -3.10 -m pytest -q`

- [ ] **Step 4: Refresh artifacts and zip**

Regenerate changed files, `v2.4.0-complete.diff`, Chinese summary, verification record, and `OmbreBrain-v2.4.0-complete-artifacts.zip`.

- [ ] **Step 5: Stop without commit**

The user explicitly requested no direct commit, push, release, or cloud changes.
