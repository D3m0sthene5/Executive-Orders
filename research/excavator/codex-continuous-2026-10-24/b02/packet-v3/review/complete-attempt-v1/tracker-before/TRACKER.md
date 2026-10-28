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
| Original or explicitly reviewed provisional working text saved | 2,351 | 3,403 | 69.1% |
| Complete inventory of the order's operative clauses | 344 | 3,403 | 10.1% |
| When and how it ended (NO), or what keeps it operating now (YES) | 303 | 3,403 | 8.9% |
| Savings clauses and surviving effects closed | 336 | 3,403 | 9.9% |
| Search for later contrary sources recorded, no open conflicts | 2,534 | 3,403 | 74.5% |
| Every shared legal source it cites has been retrieved | 209 | 236 | 88.6% |
| Opus evidence images matched to this order (Opus cases only) | 0 | 844 | 0.0% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 844 | machine job | Match the 496 Opus evidence images to orders by their contents (opus-media-match) |
| 798 | machine job | Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy |
| 268 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
| 10 | one source | Retrieve shared source EO::4314 |
| 8 | machine job | Run claim-checker on the newest claims (it reruns on every claims change and daily) |
| 6 | one source | Retrieve shared source EO::6868 |
| 3 | one source | Retrieve shared source USC::48 U.S.C. 863) |
| 3 | one source | Retrieve shared source EO::6964 |
| 3 | one source | Retrieve shared source EO::6910 |
| 2 | one source | Retrieve shared source CFR::26 CFR 458.324 |

## What blocks orders

| Blocker | Orders with a status | All orders |
|---|---:|---:|
| `NO_PROVISIONAL_STATUS` | 0 | 11,569 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 962 | 7,975 |
| `NO_CLAUSE_INVENTORY` | 3,007 | 3,007 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 3,007 | 3,007 |
| `FIRST_END_UNPROVED` | 2,614 | 2,614 |
| `OPUS_MEDIA_NOT_MATCHED_TO_ORDER` | 844 | 844 |
| `ONLY_COMPILED_TRANSCRIPTION_FOUND` | 46 | 798 |
| `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` | 687 | 687 |
| `CURRENT_BASIS_UNPROVED` | 393 | 393 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 90 | 268 |
| `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` | 139 | 139 |
| `CLAIM_INCOMPLETE` | 88 | 88 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 36 | 36 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 27 | 27 |
| `CLAIM_NOT_YET_CHECKED` | 8 | 8 |
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
