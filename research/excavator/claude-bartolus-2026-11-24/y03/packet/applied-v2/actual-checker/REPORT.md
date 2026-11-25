# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 6 (parse errors: 0)
- Orders with a claim (latest claim per order): 6
- All checks passed: 5
- Mechanical checks passed: 5; with unverifiable items: 1; failed: 0
- Structural gate passed: 6

## Source references

- gpo_published_hash_match: 82
- held_bytes_verified: 37

## Quotations

- exact: 165
- too_short_to_verify: 3

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-bartolus-2026-11-24/y03/packet/applied-v2/CLAIMS.proposed.jsonl:2` | EO:13276 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 55

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
