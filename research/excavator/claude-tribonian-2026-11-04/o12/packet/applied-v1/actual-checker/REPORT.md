# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 18 (parse errors: 0)
- Orders with a claim (latest claim per order): 18
- All checks passed: 16
- Mechanical checks passed: 16; with unverifiable items: 0; failed: 2
- Structural gate passed: 18

## Source references

- gpo_published_hash_match: 143

## Quotations

- exact: 178

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/o12/packet/applied-v1/CLAIMS.proposed.jsonl:5` | EO:10061 | order_exists:not_in_universe@operative_clauses[0].first_end.source.quote |
| `research/excavator/claude-tribonian-2026-11-04/o12/packet/applied-v1/CLAIMS.proposed.jsonl:15` | EO:10156 | order_exists:not_in_universe@operative_clauses[2].first_end.source.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 53

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
