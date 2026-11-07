# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 5 (parse errors: 0)
- Orders with a claim (latest claim per order): 5
- All checks passed: 3
- Mechanical checks passed: 3; with unverifiable items: 1; failed: 1
- Structural gate passed: 5

## Source references

- custody_record_only: 4
- gpo_published_hash_match: 40

## Quotations

- exact: 57

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-haloander-2026-11-07/ux/completion/complete-v1/CLAIMS.selected.jsonl:2` | EO:10955 | unverifiable items |
| `research/excavator/claude-haloander-2026-11-07/ux/completion/complete-v1/CLAIMS.selected.jsonl:5` | EO:9446 | order_exists:not_in_universe@operative_clauses[4].original_operative_text; order_exists:not_in_universe@original_representation.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 18

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
