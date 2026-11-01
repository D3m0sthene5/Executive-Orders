# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 6 (parse errors: 0)
- Orders with a claim (latest claim per order): 6
- All checks passed: 4
- Mechanical checks passed: 4; with unverifiable items: 2; failed: 0
- Structural gate passed: 6

## Source references

- custody_record_only: 5
- gpo_published_hash_match: 25
- held_bytes_verified: 6

## Quotations

- exact: 43

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-apollo-2026-10-31/g10/packet/complete-v1/CLAIMS.selected.jsonl:5` | EO:12921 | unverifiable items |
| `research/excavator/claude-apollo-2026-10-31/g10/packet/complete-v1/CLAIMS.selected.jsonl:6` | EO:12987 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 13

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
