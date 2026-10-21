# Readiness tracker

**Ready for human review: 225 of 14,972 orders (1.5%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 2,312 | 3,359 | 68.8% |
| Complete inventory of the order's operative clauses | 290 | 3,359 | 8.6% |
| When and how it ended (NO), or what keeps it operating now (YES) | 245 | 3,359 | 7.3% |
| Savings clauses and surviving effects closed | 278 | 3,359 | 8.3% |
| Search for later contrary sources recorded, no open conflicts | 2,484 | 3,359 | 74.0% |
| Every shared legal source it cites has been retrieved | 190 | 236 | 80.5% |
| Opus evidence images matched to this order (Opus cases only) | 121 | 844 | 14.3% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 3,216 | machine job | Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy |
| 435 | machine job | Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl |
| 286 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
| 19 | one source | Retrieve shared source STAT::66 Stat. 259 |
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
| `NO_PROVISIONAL_STATUS` | 0 | 11,613 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 959 | 7,814 |
| `ONLY_COMPILED_TRANSCRIPTION_FOUND` | 898 | 3,216 |
| `NO_CLAUSE_INVENTORY` | 3,028 | 3,028 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 3,028 | 3,028 |
| `FIRST_END_UNPROVED` | 2,635 | 2,635 |
| `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` | 688 | 688 |
| `OPUS_MEDIA_REFETCH_NEEDED` | 435 | 435 |
| `CURRENT_BASIS_UNPROVED` | 393 | 393 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 88 | 286 |
| `OPUS_MEDIA_NONE_CITED` | 217 | 217 |
| `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` | 144 | 144 |
| `CLAIM_INCOMPLETE` | 83 | 83 |
| `OPUS_MEDIA_PARTLY_RESOLVED` | 52 | 52 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 46 | 46 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 36 | 36 |
| `OPUS_MEDIA_ORIGINAL_NOT_KEPT` | 18 | 18 |
| `OPEN_SOURCE_AUDIT` | 6 | 6 |
| `CLAIM_CHECK_FAILED` | 4 | 4 |
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
