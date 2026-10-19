# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 3 (parse errors: 0)
- Orders with a claim (latest claim per order): 3
- All checks passed: 2
- Mechanical checks passed: 2; with unverifiable items: 0; failed: 1
- Structural gate passed: 3

## Source references

- held_bytes_in_release_or_repo: 15

## Quotations

- exact: 18

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/x1-pilot-2026-10-19/P1/applied-v2/CLAIMS.proposed.jsonl:1` | EO:5881 | order_exists:not_in_universe@operative_clauses[0].judgment_reason |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 6

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
