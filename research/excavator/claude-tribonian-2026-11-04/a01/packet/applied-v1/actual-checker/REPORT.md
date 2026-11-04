# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 3 (parse errors: 0)
- Orders with a claim (latest claim per order): 3
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 1; failed: 2
- Structural gate passed: 3

## Source references

- gpo_published_hash_match: 9
- held_bytes_verified: 12

## Quotations

- exact: 20
- normalised: 4
- not_found: 1
- too_short_to_verify: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v1/CLAIMS.proposed.jsonl:1` | EO:9027 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v1/CLAIMS.proposed.jsonl:2` | EO:9052 | order_exists:not_in_universe@original_representation.quote |
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v1/CLAIMS.proposed.jsonl:3` | EO:9405 | quote_verbatim:not_found@original_representation.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 9

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
