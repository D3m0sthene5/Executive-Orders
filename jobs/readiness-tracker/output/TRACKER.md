# Readiness tracker

**Ready for human review: 1 of 14,972 orders (0.0%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 2,281 | 3,359 | 67.9% |
| Complete inventory of the order's operative clauses | 7 | 3,359 | 0.2% |
| When and how it ended (NO), or what keeps it operating now (YES) | 2 | 3,359 | 0.1% |
| Savings clauses and surviving effects closed | 7 | 3,359 | 0.2% |
| Search for later contrary sources recorded, no open conflicts | 2,461 | 3,359 | 73.3% |
| Every shared legal source it cites has been retrieved | 209 | 236 | 88.6% |
| Opus evidence images matched to this order (Opus cases only) | 82 | 844 | 9.7% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 472 | machine job | Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl |
| 265 | agent check | Check the page location of fr-originals finds marked medium/low confidence |
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
| `NO_OFFICIAL_SOURCE_LOCATED` | 990 | 8,474 |
| `NO_CLAUSE_INVENTORY` | 3,318 | 3,318 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 3,318 | 3,318 |
| `FIRST_END_UNPROVED` | 2,918 | 2,918 |
| `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` | 693 | 693 |
| `OPUS_MEDIA_REFETCH_NEEDED` | 472 | 472 |
| `CURRENT_BASIS_UNPROVED` | 400 | 400 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 88 | 265 |
| `OPUS_MEDIA_NONE_CITED` | 217 | 217 |
| `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` | 172 | 172 |
| `OPUS_MEDIA_PARTLY_RESOLVED` | 52 | 52 |
| `CLAIM_INCOMPLETE` | 39 | 39 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 36 | 36 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 27 | 27 |
| `OPUS_MEDIA_ORIGINAL_NOT_KEPT` | 20 | 20 |
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

## Job outputs read

- fr-originals: 6,497
- opus-media-match fragments: 122
- opus-media-match status: 1,155
- source-ladder: 122
- claim-checker: 41
- machine later-source search: 6,938

## Historical census candidates — separate from the 14,972 working identities

- Distinct LOC catalog item candidates: 67 (not yet admitted).
- LOC item transcripts obtained: 9.
- LOC items with retained original-page images: 3.
- Lord indexed date-row appearances awaiting identity authentication: 1,023, including 812 nineteenth-century gap leads.
**Newly admitted EOs: 0.** Catalog data and manuscripts need independent signer, authority, duplicate and legal inclusion review.
See jobs/census-candidates/output/CENSUS_READINESS.md and ITEM_CANDIDATES.csv.
