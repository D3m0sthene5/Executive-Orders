# Independent review of variable LOC response plans — 2026-10-22

Reviewer: incremental_drafts swarm agent, reviewing the separate
independent_review agent's implementation. Scope: `job.py` and `test_job.py`
in early-ranger-reparse, early-ranger-triage, early-ranger-original-items and
early-ranger-full-pages. Implementation and canonical outputs were not edited
by this reviewer.

**No remaining blocking findings in the reviewed patch.** One reporting issue
was identified and corrected by the implementer: deferred metadata items were
included in the prose's requested count. The report now distinguishes planned,
attempted and retrieved counts; the 29-plan/22-attempt regression passes.

- Independently reran all 11 tests successfully, and reran the two originals
  tests after that reporting correction. Path-scoped diff whitespace checks
  pass.
- Independently replayed the current held Scout inputs with URL access
  forbidden: 24 LOC responses, 77 result rows and 65 unique canonical links.
  Triage produced six directive-title and 14 correspondence leads. The plan
  retains 21 unique item IDs, with `mjm017456`, `maj012871` and `mtjbib012509`
  first. No new acquisitions were made in this review.
- Reparse rejects no successful LOC responses, duplicate/missing request IDs,
  malformed response arrays, over-budget inputs and custody hash mismatches.
  Successful empty results emit a valid empty schema; they do not authenticate
  an identity or establish historical absence. Both compressed and decompressed
  sizes remain bounded. The 65-request bound matches Scout's existing budget.
- Metadata retrieval is capped at 22 item attempts. Deferred candidates remain
  explicit packets. An additional all-failure probe attempted four requests,
  recorded four failures, 18 provider-skipped packets and seven budget-deferred
  packets; every inclusion field remained unknown. Historical full-page targets
  remain explicit even when refreshed search results omit them.
- Full-page retrieval still selects exactly the three explicit target IDs.
  It validates their success state, metadata hash shape, nonempty deduplicated
  manifests of at most 24 master JPEGs per item, and approved URLs before
  prefetch. Changed page counts require review in both metrics and prose.
  Missing/failed metadata is rejected rather than becoming an empty success.
  Another failure probe retained six failed page records, zero acquired bytes,
  zero identity admissions and `original_clause_authentication_done: false`.
- Rehashed all 21 retained successful original-item metadata blobs from their
  gzip custody files; every SHA-256 matched and none was missing locally.
  Acquired image bytes continue to receive their own hashes; catalog attribution
  and page acquisition remain separate from authentication or legal findings.

Evidence: [RANGER_FOLLOWUP_REVIEW_EVIDENCE.json](RANGER_FOLLOWUP_REVIEW_EVIDENCE.json).
This is an offline software review and held-data replay. It does not establish
that a fresh GitHub acquisition run succeeded, that all historical pages are
complete, or that any executive-order identity or lifecycle is authenticated.
