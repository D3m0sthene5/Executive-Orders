# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 4 (parse errors: 0)
- Orders with a claim (latest claim per order): 4
- All checks passed: 3
- Mechanical checks passed: 3; with unverifiable items: 1; failed: 0
- Structural gate passed: 4

## Source references

- custody_text_only: 37
- custody_text_only_disclosed: 4
- held_bytes_verified: 327

## Quotations

- exact: 509
- too_short_to_verify: 3

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-baldus-2026-11-25/y18/packet-v3-held/complete-v1/CLAIMS.selected.jsonl:3` | EO:14033 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 152

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
