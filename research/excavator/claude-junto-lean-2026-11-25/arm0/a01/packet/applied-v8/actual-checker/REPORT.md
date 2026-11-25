# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 7 (parse errors: 0)
- Orders with a claim (latest claim per order): 7
- All checks passed: 5
- Mechanical checks passed: 5; with unverifiable items: 2; failed: 0
- Structural gate passed: 7

## Source references

- gpo_published_hash_match: 239
- held_bytes_verified: 47

## Quotations

- exact: 382
- too_short_to_verify: 10

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-junto-lean-2026-11-25/arm0/a01/packet/applied-v8/CLAIMS.proposed.jsonl:3` | EO:11858 | unverifiable items |
| `research/excavator/claude-junto-lean-2026-11-25/arm0/a01/packet/applied-v8/CLAIMS.proposed.jsonl:6` | EO:12146 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 113

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
