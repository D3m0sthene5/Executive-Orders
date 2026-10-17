# Stage 20 · Shared-source acquisition and case-specific legal review

This extension turns [98 repeated legal citations](output/SHARED_SOURCE_REFERENCE_QUEUE.csv) into deterministic **source-once, verify-per-case** research tasks. [Open the offline workbench](output/SHARED_SOURCE_WORKBENCH.html) to select an authority, follow its official-portal and constrained search routes, record actual source URLs/pages/hash once, and make a separate *proposed* effect, affected clause, date, contrary search, and savings assessment for each associated EO.

[Machine-readable source tasks](output/SHARED_SOURCE_TASKS.jsonl) include one custody record per citation and distinct empty legal-review records for every linked order; [flat per-case review queue](output/SHARED_SOURCE_CASE_REVIEW_QUEUE.csv) is suitable for audit assignment. [Metrics](output/SHARED_SOURCE_METRICS.json) count research tasks and record hashes of input versioned files. Neither the official portal nor a Google discovery route asserts that the particular law has been found there.

Run from the repository root (Node 18+, no dependencies):

```sh
node research/stage20/code/test_shared_source_workbench.mjs
node research/stage20/code/build_shared_source_workbench.mjs --check
```

To regenerate rather than merely check, omit `--check`. The builder fails if the SHA-1 of a frozen input Git blob differs from the pinned source. This protects the old Stage 20 case labels and reference families from silent mutation; future data refresh requires a reconciled revision.

**Do not conflate source retrieval with legal proof.** Citation co-occurrence may reflect amendments, formal revocations, independent statutory authority, historical context, saved consequences, or a completely irrelevant mention. Only verified original clauses, legally effective events and dates, earlier-displacement counterchecks, and genuine independent review under the [Stage 19 lifecycle claim gate](../stage19/CLAIM_SCHEMA.md) produce a completed dossier. The workbench exports `eo-shared-source-review-proposal/v1` **only**, always labeled uncertified and with unresolved gaps. It makes no new countable legal findings.
