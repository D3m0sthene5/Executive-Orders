# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 7 (parse errors: 0)
- Orders with a claim (latest claim per order): 7
- All checks passed: 4
- Mechanical checks passed: 4; with unverifiable items: 1; failed: 2
- Structural gate passed: 7

## Source references

- custody_record_only: 1
- gpo_published_hash_match: 25
- held_bytes_verified: 22

## Quotations

- exact: 53
- normalised: 4
- not_found: 1

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-apollo-2026-10-31/g02/packet/supp/applied-v2/CLAIMS.proposed.jsonl:2` | EO:8937 | unverifiable items |
| `research/excavator/claude-apollo-2026-10-31/g02/packet/supp/applied-v2/CLAIMS.proposed.jsonl:3` | EO:9052 | order_exists:not_in_universe@original_representation.quote |
| `research/excavator/claude-apollo-2026-10-31/g02/packet/supp/applied-v2/CLAIMS.proposed.jsonl:5` | EO:9405 | quote_verbatim:not_found@original_representation.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 17

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
