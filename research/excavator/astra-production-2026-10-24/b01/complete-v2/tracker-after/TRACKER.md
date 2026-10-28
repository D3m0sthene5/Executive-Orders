# Readiness tracker

**Ready for human review: 277 of 14,972 orders (1.9%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,403. The other 11,569 have not been researched yet.

Ready by text evidence: {'original_supported': 277}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 0; quotation rechecks: 0. These remain work after readiness.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,403 | 3,403 | 100.0% |
| Original or explicitly reviewed provisional working text saved | 2,328 | 3,403 | 68.4% |
| Complete inventory of the order's operative clauses | 345 | 3,403 | 10.1% |
| When and how it ended (NO), or what keeps it operating now (YES) | 303 | 3,403 | 8.9% |
| Savings clauses and surviving effects closed | 336 | 3,403 | 9.9% |
| Search for later contrary sources recorded, no open conflicts | 326 | 3,403 | 9.6% |
| Every shared legal source it cites has been retrieved | 209 | 236 | 88.6% |
| Opus evidence images matched to this order (Opus cases only) | 0 | 844 | 0.0% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 2,750 | agent check | Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and decide the custody grade; a replica scan counts only after that decision is written into the codebook |
| 844 | machine job | Match the 496 Opus evidence images to orders by their contents (opus-media-match) |
| 267 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
| 10 | one source | Retrieve shared source EO::4314 |
| 6 | machine job | Run claim-checker on the newest claims (it reruns on every claims change and daily) |
| 6 | one source | Retrieve shared source EO::6868 |
| 3 | one source | Retrieve shared source USC::48 U.S.C. 863) |
| 3 | one source | Retrieve shared source EO::6964 |
| 3 | one source | Retrieve shared source EO::6910 |
| 2 | one source | Retrieve shared source CFR::26 CFR 458.324 |

## What blocks orders

| Blocker | Orders with a status | All orders |
|---|---:|---:|
| `NO_PROVISIONAL_STATUS` | 0 | 11,569 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 985 | 8,469 |
| `NO_CLAUSE_INVENTORY` | 3,008 | 3,008 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 3,008 | 3,008 |
| `LATER_SOURCE_SEARCH_NOT_RECORDED` | 3,008 | 3,008 |
| `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK` | 77 | 2,750 |
| `FIRST_END_UNPROVED` | 2,615 | 2,615 |
| `OPUS_MEDIA_NOT_MATCHED_TO_ORDER` | 844 | 844 |
| `CURRENT_BASIS_UNPROVED` | 393 | 393 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 90 | 267 |
| `CLAIM_INCOMPLETE` | 88 | 88 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 36 | 36 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 27 | 27 |
| `CLAIM_NOT_YET_CHECKED` | 6 | 6 |
| `OPEN_SOURCE_AUDIT` | 6 | 6 |
| `CLAIM_CHECK_FAILED` | 5 | 5 |

## How to move an order forward

- Add or extend its claim in `research/readiness/claims/*.jsonl` (format: `research/stage19/CLAIM_SCHEMA.md`).
  Partial claims count: each step lights up once its part passes the gate and claim-checker.
- Start from the order's draft in `jobs/claim-drafts/output/` (see `jobs/claim-drafts/AGENT_GUIDE.md`).
- Need a source? Add it to `research/readiness/FETCH_QUEUE.jsonl`; source-ladder fetches it.
- If a step cannot be finished by machine, add a line to `research/readiness/EXHAUSTED.jsonl` with
  `instrument_id`, `step`, `searched` (list of repositories and queries), `recorded_by`, `recorded_on`.
- Step names: `provisional_status`, `original_text`, `clause_inventory`, `ending_or_current_basis`, `savings_residuals`, `counterevidence`, `shared_sources`, `opus_media`.
- Per-order detail is in `READINESS_BY_ORDER.csv`.
