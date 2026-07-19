# GitHub Backup Manifest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-sync GitHub backup manifest without changing existing bucket restore behavior.

**Architecture:** Extend `GitHubSync` with a pure manifest builder and include `_ombre_backup_manifest.json` as an extra tree entry in `_batch_commit()`. During import, read the manifest blob if it exists and return a small summary.

**Tech Stack:** Python stdlib `hashlib`/`json`, existing GitHub Git Trees API flow, pytest with fake API responses.

---

### Task 1: Manifest Builder

**Files:**
- Modify: `src/github_sync.py`
- Test: `tests/test_github_backup_manifest.py`

- [ ] **Step 1: Write failing tests** for manifest file count, byte totals, and sha256 values.
- [ ] **Step 2: Run tests** with `py -3.10 -m pytest tests\test_github_backup_manifest.py -q`; expect missing helper failure.
- [ ] **Step 3: Implement `_build_backup_manifest()`**.
- [ ] **Step 4: Run tests**; expect pass.

### Task 2: Commit Manifest

**Files:**
- Modify: `src/github_sync.py`
- Test: `tests/test_github_backup_manifest.py`

- [ ] **Step 1: Add failing `_batch_commit()` test** requiring `_ombre_backup_manifest.json` in tree entries.
- [ ] **Step 2: Add manifest tree entry without changing uploaded markdown count**.
- [ ] **Step 3: Run tests**; expect pass.

### Task 3: Import Readback

**Files:**
- Modify: `src/github_sync.py`
- Test: `tests/test_github_backup_manifest.py`

- [ ] **Step 1: Add failing `import_from_github()` test** requiring `backup_manifest.present == True` when the manifest blob exists.
- [ ] **Step 2: Implement optional manifest readback and compact summary**.
- [ ] **Step 3: Run focused GitHub tests**.

### Task 4: Version and Verification

**Files:**
- Modify: `VERSION`
- Modify: `src/VERSION`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Bump version to 2.4.10 and add changelog entry**.
- [ ] **Step 2: Run focused tests** for GitHub sync/import, import preflight, diagnostics, and comprehensive regression.
- [ ] **Step 3: Commit and push** with `feat: add github backup manifest`.

