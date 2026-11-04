# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 30 (parse errors: 0)
- Orders with a claim (latest claim per order): 30
- All checks passed: 27
- Mechanical checks passed: 27; with unverifiable items: 3; failed: 0
- Structural gate passed: 30

## Source references

- custody_record_only: 23
- gpo_published_hash_match: 120
- held_bytes_verified: 652

## Quotations

- exact: 1131
- too_short_to_verify: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/c03/packet/applied-v1/CLAIMS.proposed.jsonl:4` | EO:13018 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/c03/packet/applied-v1/CLAIMS.proposed.jsonl:5` | EO:13137 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/c03/packet/applied-v1/CLAIMS.proposed.jsonl:17` | EO:14075 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 368

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
