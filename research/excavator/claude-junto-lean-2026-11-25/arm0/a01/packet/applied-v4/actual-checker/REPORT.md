# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 5 (parse errors: 0)
- Orders with a claim (latest claim per order): 5
- All checks passed: 4
- Mechanical checks passed: 4; with unverifiable items: 1; failed: 0
- Structural gate passed: 5

## Source references

- custody_record_only: 9
- gpo_published_hash_match: 82
- held_bytes_verified: 6

## Quotations

- exact: 123
- source_text_not_available: 1

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-junto-lean-2026-11-25/arm0/a01/packet/applied-v4/CLAIMS.proposed.jsonl:4` | EO:12170 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 32

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
