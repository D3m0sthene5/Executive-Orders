# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 25 (parse errors: 0)
- Orders with a claim (latest claim per order): 25
- All checks passed: 20
- Mechanical checks passed: 20; with unverifiable items: 5; failed: 0
- Structural gate passed: 25

## Source references

- custody_record_only: 25
- held_bytes_verified: 100

## Quotations

- exact: 150

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/complete-v1/CLAIMS.selected.jsonl:1` | EO:8907 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/complete-v1/CLAIMS.selected.jsonl:11` | EO:8945 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/complete-v1/CLAIMS.selected.jsonl:12` | EO:8948 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/complete-v1/CLAIMS.selected.jsonl:19` | EO:8994 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/complete-v1/CLAIMS.selected.jsonl:25` | EO:9010 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 50

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
