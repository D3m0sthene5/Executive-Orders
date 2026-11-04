# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 15 (parse errors: 0)
- Orders with a claim (latest claim per order): 15
- All checks passed: 14
- Mechanical checks passed: 14; with unverifiable items: 1; failed: 0
- Structural gate passed: 15

## Source references

- gpo_published_hash_match: 152
- held_bytes_verified: 203

## Quotations

- exact: 498
- too_short_to_verify: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/a05/packet/complete-v1/CLAIMS.selected.jsonl:7` | EO:12864 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 160

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
