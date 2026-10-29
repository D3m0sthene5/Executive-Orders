# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 34 (parse errors: 0)
- Orders with a claim (latest claim per order): 34
- All checks passed: 33
- Mechanical checks passed: 33; with unverifiable items: 1; failed: 0
- Structural gate passed: 34

## Source references

- custody_record_only: 3
- held_bytes_in_release_or_repo: 10
- held_bytes_verified: 172

## Quotations

- exact: 219

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-production-2026-10-28/b1b/packet/supp/complete-v1/CLAIMS.selected.jsonl:4` | EO:6088 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 68

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
