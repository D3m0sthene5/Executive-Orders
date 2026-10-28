# Readiness tracker

**Ready for human review: 0 of 6 orders (0.0%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 5. The other 1 have not been researched yet.

Ready by text evidence: {}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 0; quotation rechecks: 0. These remain work after readiness.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 5 | 5 | 100.0% |
| Original or explicitly reviewed provisional working text saved | 2 | 5 | 40.0% |
| Complete inventory of the order's operative clauses | 1 | 5 | 20.0% |
| When and how it ended (NO), or what keeps it operating now (YES) | 1 | 5 | 20.0% |
| Savings clauses and surviving effects closed | 1 | 5 | 20.0% |
| Search for later contrary sources recorded, no open conflicts | 1 | 5 | 20.0% |
| Every shared legal source it cites has been retrieved | 0 | 2 | 0.0% |
| Opus evidence images matched to this order (Opus cases only) | 0 | 0 | n/a |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 2 | one source | Retrieve shared source STAT::1 Stat. 1 |

## What blocks orders

| Blocker | Orders with a status | All orders |
|---|---:|---:|
| `NO_CLAUSE_INVENTORY` | 4 | 4 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 4 | 4 |
| `LATER_SOURCE_SEARCH_NOT_RECORDED` | 4 | 4 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 3 | 4 |
| `FIRST_END_UNPROVED` | 3 | 3 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 2 | 2 |
| `CURRENT_BASIS_UNPROVED` | 1 | 1 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 1 | 1 |
| `NO_PROVISIONAL_STATUS` | 0 | 1 |

## How to move an order forward

- Add or extend its claim in `research/readiness/claims/*.jsonl` (format: `research/stage19/CLAIM_SCHEMA.md`).
  Partial claims count: each step lights up once its part passes the gate and claim-checker.
- Start from the order's draft in `jobs/claim-drafts/output/` (see `jobs/claim-drafts/AGENT_GUIDE.md`).
- Need a source? Add it to `research/readiness/FETCH_QUEUE.jsonl`; source-ladder fetches it.
- If a step cannot be finished by machine, add a line to `research/readiness/EXHAUSTED.jsonl` with
  `instrument_id`, `step`, `searched` (list of repositories and queries), `recorded_by`, `recorded_on`.
- Step names: `provisional_status`, `original_text`, `clause_inventory`, `ending_or_current_basis`, `savings_residuals`, `counterevidence`, `shared_sources`, `opus_media`.
- Per-order detail is in `READINESS_BY_ORDER.csv`.
