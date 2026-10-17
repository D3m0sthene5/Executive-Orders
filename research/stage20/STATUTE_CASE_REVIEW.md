# Stage 20 — GovInfo sources now linked to clause-specific audit queues

The companion source acquisition stage successfully downloaded and SHA-256-logged **seven out of ten** repeatedly cited *Statutes at Large* PDF candidates and recorded **three** failed or invalid retrieval attempts. See [GovInfo acquisition index](output/STATUTE_FETCH_INDEX.csv), [archive folder](sources/statutes_at_large/) and [acquisition summary](output/STATUTE_FETCH_SUMMARY.json).

This deterministic merger links the downloaded PDF candidate's exact URL, byte count, SHA-256, repository path and printed-page hint to each original candidate EO citation. The [per-case review CSV](output/STATUTE_CASE_REVIEW_QUEUE.csv) has **18 source-linked candidate cases** for the seven downloaded sources; [full machine packets](output/STATUTE_SOURCE_CASE_PACKETS.jsonl) include the three unresolved source acquisition families. [Open the interactive research workbench](output/STATUTE_SOURCE_READY_WORKBENCH.html) to read the PDFs and export separately proposed clause impacts.

Research scope remains fixed: source download proves a candidate PDF was retained. It does not prove it is the exact statute or page referred to in the record, much less that it alters an EO, establishes the first cessation, or preserves residual effects. The workbench never records human approvals or increases the strict lifecycle count.

Run `node research/stage20/code/merge_statute_custody.mjs --check` from the repository root with Node 18+. Omit `--check` to regenerate. [Metrics](output/STATUTE_CUSTODY_METRICS.json) bind the exact Git blob SHA-1 of the upstream 98-family task ledger and ten-row official PDF acquisition index. Changed inputs halt the build rather than silently alter the research cohort.

[Stage 19 independent lifecycle claim gate](../stage19/CLAIM_SCHEMA.md) still requires full operative-clause reconstruction, event dates and mechanisms, savings, contrary-source search, an independently checked original representation, and separate human approval.
