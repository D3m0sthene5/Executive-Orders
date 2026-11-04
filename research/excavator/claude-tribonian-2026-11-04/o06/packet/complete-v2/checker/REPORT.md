# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 27 (parse errors: 0)
- Orders with a claim (latest claim per order): 27
- All checks passed: 25
- Mechanical checks passed: 25; with unverifiable items: 0; failed: 2
- Structural gate passed: 27

## Source references

- gpo_published_hash_match: 35
- held_bytes_verified: 119

## Quotations

- exact: 186

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/o06/packet/complete-v2/CLAIMS.selected.jsonl:3` | EO:8613 | order_exists:not_in_universe@operative_clauses[0].first_end.source.quote |
| `research/excavator/claude-tribonian-2026-11-04/o06/packet/complete-v2/CLAIMS.selected.jsonl:9` | EO:8639 | order_exists:not_in_universe@operative_clauses[0].first_end.source.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 59

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
