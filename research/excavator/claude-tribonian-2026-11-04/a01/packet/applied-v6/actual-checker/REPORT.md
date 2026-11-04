# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 6 (parse errors: 0)
- Orders with a claim (latest claim per order): 6
- All checks passed: 3
- Mechanical checks passed: 3; with unverifiable items: 3; failed: 0
- Structural gate passed: 6

## Source references

- custody_record_only: 12
- gpo_published_hash_match: 21
- held_bytes_verified: 11

## Quotations

- exact: 53
- too_short_to_verify: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v6/CLAIMS.proposed.jsonl:2` | EO:8402 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v6/CLAIMS.proposed.jsonl:4` | EO:8538 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v6/CLAIMS.proposed.jsonl:6` | EO:9027 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 17

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
