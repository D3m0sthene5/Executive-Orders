# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 4 (parse errors: 0)
- Orders with a claim (latest claim per order): 4
- All checks passed: 3
- Mechanical checks passed: 3; with unverifiable items: 0; failed: 1
- Structural gate passed: 4

## Source references

- gpo_published_hash_match: 12
- held_bytes_verified: 12

## Quotations

- exact: 28

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-apollo-2026-10-31/g01/packet/supp/applied-v3/CLAIMS.proposed.jsonl:4` | EO:8168 | order_exists:not_in_universe@operative_clauses[0].first_end.source.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 8

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
