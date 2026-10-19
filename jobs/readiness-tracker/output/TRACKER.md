# Readiness tracker

**Ready for human review: 130 of 14,972 orders (0.9%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 2,312 | 3,359 | 68.8% |
| Complete inventory of the order's operative clauses | 178 | 3,359 | 5.3% |
| When and how it ended (NO), or what keeps it operating now (YES) | 134 | 3,359 | 4.0% |
| Savings clauses and surviving effects closed | 166 | 3,359 | 4.9% |
| Search for later contrary sources recorded, no open conflicts | 2,470 | 3,359 | 73.5% |
| Every shared legal source it cites has been retrieved | 7 | 236 | 3.0% |
| Opus evidence images matched to this order (Opus cases only) | 82 | 844 | 9.7% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 472 | machine job | Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl |
| 286 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
| 19 | one source | Retrieve shared source STAT::66 Stat. 259 |
| 11 | one source | Retrieve shared source EO::9337 |
| 10 | one source | Retrieve shared source EO::4314 |
| 9 | one source | Retrieve shared source EO::8417 |
| 9 | one source | Retrieve shared source EO::9515 |
| 8 | one source | Retrieve shared source USC::31 U.S.C. 1552 |
| 7 | one source | Retrieve shared source EO::10153 |
| 7 | one source | Retrieve shared source EO::9492 |
| 7 | one source | Retrieve shared source EO::9792 |
| 7 | one source | Retrieve shared source EO::9886 |
| 7 | one source | Retrieve shared source EO::10608 |
| 6 | one source | Retrieve shared source EO::11401 |
| 6 | one source | Retrieve shared source EO::6868 |
| 6 | one source | Retrieve shared source EO::13286 |
| 6 | one source | Retrieve shared source EO::10713 |
| 6 | one source | Retrieve shared source EO::11211 |
| 6 | one source | Retrieve shared source EO::14173 |
| 6 | one source | Retrieve shared source EO::12282 |
| 6 | one source | Retrieve shared source EO::9526 |
| 6 | one source | Retrieve shared source EO::9714 |
| 5 | one source | Retrieve shared source EO::10084 |
| 5 | one source | Retrieve shared source EO::11766 |
| 5 | one source | Retrieve shared source EO::10152 |
| | | ...and 69 more in `SHARED_UNLOCKS.csv` |

## What blocks orders

| Blocker | Orders with a status | All orders |
|---|---:|---:|
| `NO_PROVISIONAL_STATUS` | 0 | 11,613 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 959 | 7,814 |
| `NO_CLAUSE_INVENTORY` | 3,142 | 3,142 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 3,142 | 3,142 |
| `FIRST_END_UNPROVED` | 2,742 | 2,742 |
| `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` | 693 | 693 |
| `OPUS_MEDIA_REFETCH_NEEDED` | 472 | 472 |
| `CURRENT_BASIS_UNPROVED` | 400 | 400 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 88 | 286 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 229 | 229 |
| `OPUS_MEDIA_NONE_CITED` | 217 | 217 |
| `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` | 159 | 159 |
| `CLAIM_INCOMPLETE` | 83 | 83 |
| `ONLY_COMPILED_TRANSCRIPTION_FOUND` | 2 | 68 |
| `OPUS_MEDIA_PARTLY_RESOLVED` | 52 | 52 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 36 | 36 |
| `OPUS_MEDIA_ORIGINAL_NOT_KEPT` | 20 | 20 |
| `OPUS_MEDIA_MATCH_AMBIGUOUS` | 1 | 1 |
| `OPEN_SOURCE_AUDIT` | 1 | 1 |

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
- ofr-compilations: 500
- isthmian-canal-1911: 105
- indian-reservations-1912: 55
- richardson-volumes (lead only, never counted as the original): 68
- opus-media-match status: 1,155
- source-ladder: not run yet
- claim-checker: 217
- machine later-source search: 6,938

## Historical census candidates — separate from the 14,972 working identities

- Distinct LOC catalog item candidates: 67 (not yet admitted).
- LOC item transcripts obtained: 9.
- LOC items with retained original-page images: 3.
- Lord indexed date-row appearances awaiting identity authentication: 1,023, including 812 nineteenth-century gap leads.
**Newly admitted EOs: 0.** Catalog data and manuscripts need independent signer, authority, duplicate and legal inclusion review.
See jobs/census-candidates/output/CENSUS_READINESS.md and ITEM_CANDIDATES.csv.
