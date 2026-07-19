# Rust Kernel Phase 6A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal Rust replay kernel scaffold that mirrors the Python shadow replay contract without replacing the runtime.

**Architecture:** Create an isolated Cargo crate under `kernel/rust/ombre-kernel`. The crate has no external dependencies and exposes typed ledger events, replay reports, violations, and a `ReplayKernel` that checks the same baseline invariants as the Python `LedgerReplayValidator`. Python remains canonical for runtime diagnostics.

**Tech Stack:** Rust std only, Cargo when available, pytest contract tests.

---

### Task 1: Capture Rust Kernel Contract

**Files:**
- Create: `tests/test_rust_kernel_phase6a.py`

- [x] **Step 1: Write failing scaffold contract test**

Assert `kernel/rust/ombre-kernel/Cargo.toml` and `src/lib.rs` exist, expose `ReplayKernel`, `LedgerEvent`, `ReplayReport`, and `ViolationCode`, and avoid runtime dependencies.

- [x] **Step 2: Write optional cargo test bridge**

If `cargo` is available, run `cargo test --manifest-path kernel/rust/ombre-kernel/Cargo.toml`. If not, verify the scaffold files and skip compilation.

- [x] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_rust_kernel_phase6a.py -q`

Expected: FAIL because the Rust crate does not exist yet.

### Task 2: Implement Minimal Rust Replay Kernel

**Files:**
- Create: `kernel/rust/ombre-kernel/Cargo.toml`
- Create: `kernel/rust/ombre-kernel/src/lib.rs`
- Create: `kernel/rust/ombre-kernel/README.md`

- [x] **Step 1: Add crate manifest**

Use `edition = "2021"` and no dependencies.

- [x] **Step 2: Add core replay types**

Define `LedgerEvent`, `ReplayReport`, `ReplayFailure`, `ViolationCode`, and `ReplayKernel`.

- [x] **Step 3: Add invariant checks**

Check strictly increasing seq, non-empty trace id, `sha256:<64hex>` body hash, projection summary counts, and tombstone-is-deleted.

- [x] **Step 4: Add Rust unit tests**

Cover valid lifecycle and structural violations in `src/lib.rs`.

- [x] **Step 5: Run scaffold tests**

Run: `pytest tests/test_rust_kernel_phase6a.py -q`

Expected: PASS. If Cargo is unavailable locally, pytest should still validate scaffold files and report that cargo execution was skipped.

### Task 3: Document And Verify

**Files:**
- Modify: `docs/INTERNALS.md`

- [x] **Step 1: Document Phase 6A**

Explain that Rust kernel is scaffold-only and shadow, with Python runtime unchanged.

- [x] **Step 2: Run targeted regression**

Run: `pytest tests/test_rust_kernel_phase6a.py tests/test_ledger_property_phase5b.py tests/test_ledger_replay_phase5a.py -q`

Expected: PASS.

- [x] **Step 3: Run full regression**

Run: `pytest -q`

Expected: PASS.

- [x] **Step 4: Run whitespace diff check**

Run: `git diff --check`

Expected: no whitespace errors.

- [x] **Step 5: Stop locally**

Do not commit or push unless the user asks.
