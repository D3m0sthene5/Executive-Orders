# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 23 (parse errors: 0)
- Orders with a claim (latest claim per order): 23
- All checks passed: 22
- Mechanical checks passed: 22; with unverifiable items: 0; failed: 1
- Structural gate passed: 23

## Source references

- gpo_published_hash_match: 146

## Quotations

- exact: 179

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/o15/packet/applied-v1/CLAIMS.proposed.jsonl:13` | EO:10859 | order_exists:not_in_universe@operative_clauses[0].first_end.source.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 56

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
