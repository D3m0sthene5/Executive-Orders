# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 5 (parse errors: 0)
- Orders with a claim (latest claim per order): 5
- All checks passed: 3
- Mechanical checks passed: 3; with unverifiable items: 2; failed: 0
- Structural gate passed: 5

## Source references

- gpo_published_hash_match: 30
- held_bytes_verified: 70

## Quotations

- exact: 133
- too_short_to_verify: 9

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-bartolus-2026-11-24/y04/packet/applied-v2/CLAIMS.proposed.jsonl:2` | EO:10860 | unverifiable items |
| `research/excavator/claude-bartolus-2026-11-24/y04/packet/applied-v2/CLAIMS.proposed.jsonl:4` | EO:13257 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 47

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
