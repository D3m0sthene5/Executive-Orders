# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 18 (parse errors: 0)
- Orders with a claim (latest claim per order): 18
- All checks passed: 16
- Mechanical checks passed: 16; with unverifiable items: 2; failed: 0
- Structural gate passed: 18

## Source references

- custody_record_only: 2
- gpo_published_hash_match: 159
- held_bytes_verified: 250

## Quotations

- exact: 577
- too_short_to_verify: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/a05/packet/applied-v5/CLAIMS.proposed.jsonl:8` | EO:12864 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/a05/packet/applied-v5/CLAIMS.proposed.jsonl:15` | EO:13038 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 186

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
