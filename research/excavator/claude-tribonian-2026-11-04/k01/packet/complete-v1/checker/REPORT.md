# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 11 (parse errors: 0)
- Orders with a claim (latest claim per order): 11
- All checks passed: 7
- Mechanical checks passed: 7; with unverifiable items: 4; failed: 0
- Structural gate passed: 11

## Source references

- held_bytes_verified: 782

## Quotations

- exact: 1130
- too_short_to_verify: 18

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/k01/packet/complete-v1/CLAIMS.selected.jsonl:4` | EO:14012 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/k01/packet/complete-v1/CLAIMS.selected.jsonl:5` | EO:14013 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/k01/packet/complete-v1/CLAIMS.selected.jsonl:9` | EO:14052 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/k01/packet/complete-v1/CLAIMS.selected.jsonl:10` | EO:14082 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 377

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
