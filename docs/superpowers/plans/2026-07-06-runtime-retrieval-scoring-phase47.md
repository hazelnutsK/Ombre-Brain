# Runtime Retrieval Scoring Phase 47 Implementation Plan

**Goal:** Move policy-gated retrieval scoring from standalone preflight construction into a reusable `LegacyRuntime` API.

**Architecture:** Keep live search ordering unchanged. Add runtime APIs for scoring one bucket and ranking candidate mappings. The vNext preflight retrieval check should use those runtime APIs so future breath/search migration can share the same policy-gated scorer.

**Tech Stack:** `LegacyRuntime`, `PolicyGatedRetrievalScorer`, `RetrievalFeatures`, `RetrievalCandidate`, pytest.

---

## Implementation Steps

1. Add `PolicyGatedRetrievalScorer` to `LegacyRuntime`.
2. Add `score_retrieval_bucket(...)` and `rank_retrieval_candidates(...)`.
3. Update the `retrieval_scoring` preflight check to use runtime scorer.
4. Add runtime regression coverage for hidden spontaneous candidates losing to visible candidates.
5. Document the runtime boundary.

---

## Validation

Targeted command:

```powershell
pytest tests/test_v3_legacy_runtime.py tests/test_vnext_preflight_report_phase22.py tests/test_retrieval_scoring_phase9.py -q
```

Status: passed, 39 tests.

Full command:

```powershell
pytest -q
```

Status: passed, 719 passed and 7 skipped.

Diff check:

```powershell
git diff --check
```

Status: passed, with Windows LF-to-CRLF warnings only.
