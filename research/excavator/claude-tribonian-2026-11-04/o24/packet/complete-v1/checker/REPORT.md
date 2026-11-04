# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 7 (parse errors: 0)
- Orders with a claim (latest claim per order): 7
- All checks passed: 3
- Mechanical checks passed: 3; with unverifiable items: 4; failed: 0
- Structural gate passed: 7

## Source references

- custody_record_only: 76
- held_bytes_verified: 67

## Quotations

- exact: 204

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/o24/packet/complete-v1/CLAIMS.selected.jsonl:1` | EO:13900 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o24/packet/complete-v1/CLAIMS.selected.jsonl:2` | EO:13965 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o24/packet/complete-v1/CLAIMS.selected.jsonl:3` | EO:13983 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o24/packet/complete-v1/CLAIMS.selected.jsonl:6` | EO:14337 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 68

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
