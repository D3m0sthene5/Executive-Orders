# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 21 (parse errors: 0)
- Orders with a claim (latest claim per order): 21
- All checks passed: 19
- Mechanical checks passed: 19; with unverifiable items: 2; failed: 0
- Structural gate passed: 21

## Source references

- gpo_published_hash_match: 436
- held_bytes_verified: 55

## Quotations

- exact: 672
- too_short_to_verify: 6

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/a04/packet/complete-v1/CLAIMS.selected.jsonl:14` | EO:12323 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/a04/packet/complete-v1/CLAIMS.selected.jsonl:20` | EO:12546 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 208

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
