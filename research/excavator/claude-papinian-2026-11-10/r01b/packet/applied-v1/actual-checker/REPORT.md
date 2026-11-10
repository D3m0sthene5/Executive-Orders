# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 5 (parse errors: 0)
- Orders with a claim (latest claim per order): 5
- All checks passed: 2
- Mechanical checks passed: 2; with unverifiable items: 0; failed: 3
- Structural gate passed: 5

## Source references

- gpo_published_hash_match: 17
- held_bytes_verified: 42

## Quotations

- exact: 81

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-papinian-2026-11-10/r01b/packet/applied-v1/CLAIMS.proposed.jsonl:3` | EO:8341 | order_exists:not_in_universe@operative_clauses[0].first_end.source.quote |
| `research/excavator/claude-papinian-2026-11-10/r01b/packet/applied-v1/CLAIMS.proposed.jsonl:4` | EO:8613 | order_exists:not_in_universe@operative_clauses[0].first_end.source.quote |
| `research/excavator/claude-papinian-2026-11-10/r01b/packet/applied-v1/CLAIMS.proposed.jsonl:5` | EO:8639 | order_exists:not_in_universe@operative_clauses[0].first_end.source.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 27

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
