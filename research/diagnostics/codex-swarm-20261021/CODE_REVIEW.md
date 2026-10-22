# Independent code review — 2026-10-21

Reviewer: Codex independent_review swarm agent. Implementation and claims were not edited by this reviewer. Scope: working integration diff, particularly draft receipt verification, dependency scheduling, Pinakes lead grades and search backoff. This report describes the initial reviewed version; parent integration may subsequently resolve findings.

## Findings requiring disposition

1. **P2 — Connect the standalone checker receipt store to offline drafting.** In `jobs/claim-drafts/drafts.py`, `CheckerRunner` supplies `<claim-drafts-cache>/checker-text` to its checker context and `OfflineVerification` reads only that directory's `verified/` subtree. The runner puts standalone checker receipts under `.job-cache/claim-checker/verified/`. Thus even a successful predecessor acquisition is invisible to a fresh draft cache. Missing custody remains correctly unverified, so this is a missed connection rather than false promotion. Read the predecessor store explicitly, without writing or downloading, and rehash any reused bytes. Add a test with only the standalone store populated.

2. **P2 — Reject a receipt changed during hashing.** `OfflineVerification.__call__` checks the post-hash stat tuple but, if it changed, only suppresses memoization; it still returns the digest result. An atomic replacement after hashing correct bytes returned `True` while the current file hashed differently (`verification_returned=True`, `current_bytes_match=False`, `memoized_entries=0`). Return unverified or perform a bounded retry when the pre/post version differs, and handle removal during that interval. This narrows a race rather than relying on persistent verdicts. The caller's preexisting truthy check maps a false download-verification result to `custody_record_only`; the new comment saying corruption “fails” should not be read as a guarantee of a mechanical-fail row.

3. **P2 — Do not count deferred searches as attempted engines.** The new `deferred_this_run:*` response in `jobs/_lib/eo_websearch.py::Searcher.search` bypasses the request, but `advance` increments each target's persisted `engines_tried` for every response except `budget_exhausted`. As a result, blocked-engine suppression inflates per-target attempted-search counts. Distinguish deferrals in target state and do not increment actual attempts for them. The aggregate `ENGINES.json` deferral count is useful; no legal-exhaustion promotion was observed.

## Validation and boundaries

- Scheduler regression/integration suite: **12 tests passed**, including the full runnable dependency graph, uploaded-ProQuest selection, consumer ordering and shared-library trigger coverage.
- Claim-drafts suite: **66 tests passed**, including no-network embedded checking, missing receipts, changed/replaced/deleted receipts and Windows no-reuse behavior.
- Independent race reproduction used a temporary receipt and atomically replaced its path at digest completion; no repository artifact was changed.
- The scheduler refactor preserves downstream-only expansion; source-ladder is not scheduled by a Pinakes/CSC refresh. Cycle detection fails explicitly. Removed `wpa-lists` predecessors refer to a nonexistent runner and are replaced with explanatory comments.
- Inspected Pinakes fragment emission and tracker consumption: `acceptable_as_original:false`, `needs_page_check:true`, and the replica blocker remain; transcription/replica leads are not promoted into accepted originals, claims or human certification.
- The receipt change still rebuilds draft claims and reruns gates/quotation checks. It is not per-order incremental computation; no savings magnitude is established by these tests.
- Full git status encountered a missing promisor blob and unavailable network DNS in this reviewer environment. Path-scoped diffs were available; current GitHub/main verification and import completeness remain the parent integration agent's responsibility.
- Existing repository claims, status/codebook records, human reviews and handoff files were untouched by this reviewer. The parent owns the required Codex handoff entry.

## Final follow-up disposition

All three initial findings are resolved in the final inspected implementation:

- Offline verification reads standalone checker sibling/explicit receipt roots read-only and rehashes them; the embedded test populates only the standalone store and checks corruption remains unverified.
- Changed-during-hash receipts return unverified. Replacement/removal regressions pass; no stale verdict is memoized.
- Deferred search responses no longer increment actual engine attempts; target notes retain the deferral.

Independent reruns: **68 claim-drafts tests, 13 web-search tests, 12 scheduler tests, and 3 early-ranger-transcription tests passed**. The additional transcription fix removes the brittle exact-nine requirement, validates/deduplicates a finite maximum-50 metadata plan before fetch, retains distinct item+URL outputs, and preserves the unreviewed/authentication-false classification. Its producer ordering is present and the full runnable graph passes. No additional actionable blocker was found in this focused code review. These tests do not constitute a full online production refresh or measured cost-saving result.

## Authorized final metadata repair

After the independent review, the coordinator assigned this reviewer a narrow implementation task. I added the missing direct `after.txt` edges for scout → reparse → triage → original-items → full-pages and all six actual ranger-output producers read by census-candidates. The existing original-items → transcriptions edge was retained. Exact research-input and producer-output trigger declarations accompany the edges; output-only commits remain excluded by the selector, with consumer expansion supplying execution ordering. Existing needs declarations already cover the consumed research inputs, so no sparse-checkout additions were required. Scout's unused CURATED constant was not mistaken for a read dependency.

Two scheduler regressions now derive the census reader's job inputs from its literal INPUTS map, exercise the real chain, ensure transcript-only refresh does not refetch its predecessors, and check consumed research triggers. **All 14 scheduler tests pass**, including full-graph cycle validation. The existing frozen input-count checks in older ranger jobs remain fail-closed; no research classification or source-quality logic was edited. This metadata patch is authored by the reviewer and is therefore not claimed as independently reviewed by this same agent.
