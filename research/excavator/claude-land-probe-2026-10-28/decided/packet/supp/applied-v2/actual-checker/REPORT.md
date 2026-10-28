# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 2 (parse errors: 0)
- Orders with a claim (latest claim per order): 2
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 2; failed: 0
- Structural gate passed: 2

## Source references

- custody_record_only: 6
- gpo_published_hash_match: 1
- held_bytes_verified: 7

## Quotations

- exact: 16

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-land-probe-2026-10-28/decided/packet/supp/applied-v2/CLAIMS.proposed.jsonl:1` | EO:4109 | unverifiable items |
| `research/excavator/claude-land-probe-2026-10-28/decided/packet/supp/applied-v2/CLAIMS.proposed.jsonl:2` | EO:4430 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 4

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
