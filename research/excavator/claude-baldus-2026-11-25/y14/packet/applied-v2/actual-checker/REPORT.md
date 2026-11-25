# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 9 (parse errors: 0)
- Orders with a claim (latest claim per order): 9
- All checks passed: 5
- Mechanical checks passed: 5; with unverifiable items: 4; failed: 0
- Structural gate passed: 9

## Source references

- held_bytes_verified: 668

## Quotations

- exact: 870
- too_short_to_verify: 12

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-baldus-2026-11-25/y14/packet/applied-v2/CLAIMS.proposed.jsonl:2` | EO:13551 | unverifiable items |
| `research/excavator/claude-baldus-2026-11-25/y14/packet/applied-v2/CLAIMS.proposed.jsonl:3` | EO:13553 | unverifiable items |
| `research/excavator/claude-baldus-2026-11-25/y14/packet/applied-v2/CLAIMS.proposed.jsonl:6` | EO:13581 | unverifiable items |
| `research/excavator/claude-baldus-2026-11-25/y14/packet/applied-v2/CLAIMS.proposed.jsonl:8` | EO:13606 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 223

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
