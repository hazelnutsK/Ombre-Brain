# Preflight CLI Diagnostics Phase 40 Implementation Plan

**Goal:** Expose the Phase 23 vNext preflight CLI/source hook contract as a standalone Dashboard system diagnostics check.

**Architecture:** Inspect `tools/vnext_preflight.py` and `src/web/system.py` for required files and snippets. Do not execute the CLI, write output files, read user buckets, or make preflight a release gate.

**Tech Stack:** `web.system.build_system_diagnostics`, source snippet checks, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_system_diagnostics.py`

- [x] **Step 1: Add fake preflight CLI source**

Create a fake `tools/vnext_preflight.py` in the diagnostics temp repo.

- [x] **Step 2: Require preflight CLI diagnostics check**

Assert diagnostics includes `preflight_cli_diagnostics` with OK status and no missing snippets.

### Task 2: Implement Preflight CLI Diagnostics

**Files:**
- Modify: `src/web/system.py`

- [x] **Step 1: Add source-level diagnostics helper**

Add `_build_preflight_cli_diagnostics()` that checks required files and snippets.

- [x] **Step 2: Append diagnostics check**

Append `preflight_cli_diagnostics` check to `build_system_diagnostics()`.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/INTERNALS.md`
- Add: `docs/superpowers/plans/2026-07-06-preflight-cli-diagnostics-phase40.md`

- [x] **Step 1: Document Phase 40**

Explain that this is read-only source validation, not CLI execution.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_system_diagnostics.py tests/test_vnext_preflight_report_phase22.py -q`
Result: PASS, 9 passed.

- [x] **Step 3: Run full verification**

Run: `pytest -q`
Result: PASS, 712 passed, 7 skipped.

- [x] **Step 4: Check whitespace**

Run: `git diff --check`
Result: PASS; exit 0 with Windows line-ending warnings only.

### Status

- [x] Phase 39: Surface Context Diagnostics
- [x] Phase 40: Preflight CLI Diagnostics
