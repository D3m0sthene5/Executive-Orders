# Readiness tracker

**Ready for human review: 399 of 14,972 orders (2.7%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,403. The other 11,569 have not been researched yet.

Ready by text evidence: {'original_supported': 298, 'transcription_dependent': 101}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 107; quotation rechecks: 107. These remain work after readiness.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,403 | 3,403 | 100.0% |
| Original or explicitly reviewed provisional working text saved | 2,456 | 3,403 | 72.2% |
| Complete inventory of the order's operative clauses | 464 | 3,403 | 13.6% |
| When and how it ended (NO), or what keeps it operating now (YES) | 418 | 3,403 | 12.3% |
| Savings clauses and surviving effects closed | 451 | 3,403 | 13.3% |
| Search for later contrary sources recorded, no open conflicts | 2,640 | 3,403 | 77.6% |
| Every shared legal source it cites has been retrieved | 209 | 236 | 88.6% |
| Opus evidence images matched to this order (Opus cases only) | 125 | 839 | 14.9% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 5,247 | machine job | Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy |
| 2,750 | agent check | Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held |
| 431 | machine job | Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl |
| 285 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
| 10 | one source | Retrieve shared source EO::4314 |
| 6 | one source | Retrieve shared source EO::6868 |
| 3 | one source | Retrieve shared source USC::48 U.S.C. 863) |
| 3 | one source | Retrieve shared source EO::6964 |
| 3 | one source | Retrieve shared source EO::6910 |
| 2 | one source | Retrieve shared source CFR::26 CFR 458.324 |
| 1 | agent check | Settle ambiguous Opus media matches (MATCHES.csv rows graded ambiguous) |

## What blocks orders

| Blocker | Orders with a status | All orders |
|---|---:|---:|
| `NO_PROVISIONAL_STATUS` | 0 | 11,569 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 860 | 7,715 |
| `ONLY_COMPILED_TRANSCRIPTION_FOUND` | 844 | 5,247 |
| `NO_CLAUSE_INVENTORY` | 2,890 | 2,890 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 2,890 | 2,890 |
| `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK` | 77 | 2,750 |
| `FIRST_END_UNPROVED` | 2,497 | 2,497 |
| `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` | 580 | 580 |
| `OPUS_MEDIA_REFETCH_NEEDED` | 431 | 431 |
| `CURRENT_BASIS_UNPROVED` | 393 | 393 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 87 | 285 |
| `OPUS_MEDIA_NONE_CITED` | 212 | 212 |
| `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` | 139 | 139 |
| `CLAIM_INCOMPLETE` | 88 | 88 |
| `OPUS_MEDIA_PARTLY_RESOLVED` | 52 | 52 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 36 | 36 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 27 | 27 |
| `OPUS_MEDIA_ORIGINAL_NOT_KEPT` | 18 | 18 |
| `CLAIM_CHECK_FAILED` | 10 | 10 |
| `OPEN_SOURCE_AUDIT` | 6 | 6 |
| `WORKING_TEXT_REVIEW_OR_DISCLOSURE_REQUIRED` | 2 | 2 |
| `OPUS_MEDIA_MATCH_AMBIGUOUS` | 1 | 1 |

## How to move an order forward

- Add or extend its claim in `research/readiness/claims/*.jsonl` (format: `research/stage19/CLAIM_SCHEMA.md`).
  Partial claims count: each step lights up once its part passes the gate and claim-checker.
- Start from the order's draft in `jobs/claim-drafts/output/` (see `jobs/claim-drafts/AGENT_GUIDE.md`).
- Need a source? Add it to `research/readiness/FETCH_QUEUE.jsonl`; source-ladder fetches it.
- If a step cannot be finished by machine, add a line to `research/readiness/EXHAUSTED.jsonl` with
  `instrument_id`, `step`, `searched` (list of repositories and queries), `recorded_by`, `recorded_on`.
- Step names: `provisional_status`, `original_text`, `clause_inventory`, `ending_or_current_basis`, `savings_residuals`, `counterevidence`, `shared_sources`, `opus_media`.
- Per-order detail is in `READINESS_BY_ORDER.csv`.
