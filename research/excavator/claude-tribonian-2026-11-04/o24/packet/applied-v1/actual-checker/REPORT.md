# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 8 (parse errors: 0)
- Orders with a claim (latest claim per order): 8
- All checks passed: 4
- Mechanical checks passed: 4; with unverifiable items: 4; failed: 0
- Structural gate passed: 8

## Source references

- custody_record_only: 76
- held_bytes_verified: 88

## Quotations

- exact: 234

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/o24/packet/applied-v1/CLAIMS.proposed.jsonl:1` | EO:13900 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o24/packet/applied-v1/CLAIMS.proposed.jsonl:2` | EO:13965 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o24/packet/applied-v1/CLAIMS.proposed.jsonl:3` | EO:13983 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o24/packet/applied-v1/CLAIMS.proposed.jsonl:7` | EO:14337 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 78

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
