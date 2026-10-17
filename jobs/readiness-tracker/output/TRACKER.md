# Readiness tracker

**Ready for human review: 0 of 14,972 orders (0.0%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 307 | 3,359 | 9.1% |
| Complete inventory of the order's operative clauses | 0 | 3,359 | 0.0% |
| When and how it ended (NO), or what keeps it operating now (YES) | 0 | 3,359 | 0.0% |
| Savings clauses and surviving effects closed | 0 | 3,359 | 0.0% |
| Search for later contrary sources recorded, no open conflicts | 0 | 3,359 | 0.0% |
| Every shared legal source it cites has been retrieved | 209 | 236 | 88.6% |
| Opus evidence images matched to this order (Opus cases only) | 82 | 844 | 9.7% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 472 | machine job | Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl |
| 242 | machine job | Run one bulk download of the official links already found (Stage 21 crosswalk) |
| 10 | one source | Retrieve shared source EO::4314 |
| 8 | agent check | Check the page location of fr-originals finds marked medium/low confidence |
| 6 | one source | Retrieve shared source EO::6868 |
| 3 | one source | Retrieve shared source USC::48 U.S.C. 863) |
| 3 | one source | Retrieve shared source EO::6964 |
| 3 | one source | Retrieve shared source EO::6910 |
| 2 | one source | Retrieve shared source CFR::26 CFR 458.324 |
| 1 | agent check | Settle ambiguous Opus media matches (MATCHES.csv rows graded ambiguous) |

## What blocks orders

| Blocker | Orders with a status | All orders |
|---|---:|---:|
| `NO_OFFICIAL_SOURCE_LOCATED` | 2,802 | 14,400 |
| `NO_PROVISIONAL_STATUS` | 0 | 11,613 |
| `NO_CLAUSE_INVENTORY` | 3,359 | 3,359 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 3,359 | 3,359 |
| `LATER_SOURCE_SEARCH_NOT_RECORDED` | 3,359 | 3,359 |
| `FIRST_END_UNPROVED` | 2,954 | 2,954 |
| `OPUS_MEDIA_REFETCH_NEEDED` | 472 | 472 |
| `CURRENT_BASIS_UNPROVED` | 405 | 405 |
| `OFFICIAL_URL_KNOWN_NOT_DOWNLOADED` | 242 | 242 |
| `OPUS_MEDIA_NONE_CITED` | 217 | 217 |
| `OPUS_MEDIA_PARTLY_RESOLVED` | 52 | 52 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 36 | 36 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 27 | 27 |
| `OPUS_MEDIA_ORIGINAL_NOT_KEPT` | 20 | 20 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 8 | 8 |
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

- fr-originals: 40
- opus-media-match fragments: 122
- opus-media-match status: 1,155
- source-ladder: 85
- claim-checker: 0

## Historical census candidates — separate from the 14,972 working identities

- Distinct LOC catalog item candidates: 67 (not yet admitted).
- LOC item transcripts obtained: 9.
- LOC items with retained original-page images: 3.
- Lord indexed date-row appearances awaiting identity authentication: 1,023, including 812 nineteenth-century gap leads.
**Newly admitted EOs: 0.** Catalog data and manuscripts need independent signer, authority, duplicate and legal inclusion review.
See jobs/census-candidates/output/CENSUS_READINESS.md and ITEM_CANDIDATES.csv.
