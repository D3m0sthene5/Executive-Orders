# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 8 (parse errors: 0)
- Orders with a claim (latest claim per order): 8
- All checks passed: 7
- Mechanical checks passed: 7; with unverifiable items: 0; failed: 1
- Structural gate passed: 8

## Source references

- gpo_published_hash_match: 82
- held_bytes_verified: 16

## Quotations

- exact: 139

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-papinian-2026-11-10/y11/packet/applied-v8/CLAIMS.proposed.jsonl:4` | EO:10860 | order_exists:not_in_universe@original_representation.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 49

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
