# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 15 (parse errors: 0)
- Orders with a claim (latest claim per order): 15
- All checks passed: 13
- Mechanical checks passed: 13; with unverifiable items: 2; failed: 0
- Structural gate passed: 15

## Source references

- custody_record_only: 15
- gpo_published_hash_match: 90

## Quotations

- exact: 131

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/o10/packet/applied-v3/CLAIMS.proposed.jsonl:2` | EO:9271 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o10/packet/applied-v3/CLAIMS.proposed.jsonl:8` | EO:9492 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 41

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
