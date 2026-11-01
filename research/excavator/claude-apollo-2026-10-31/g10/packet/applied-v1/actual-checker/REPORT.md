# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 10 (parse errors: 0)
- Orders with a claim (latest claim per order): 10
- All checks passed: 6
- Mechanical checks passed: 6; with unverifiable items: 3; failed: 1
- Structural gate passed: 10

## Source references

- custody_record_only: 24
- gpo_published_hash_match: 65
- held_bytes_verified: 6

## Quotations

- exact: 121
- not_found: 4

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-apollo-2026-10-31/g10/packet/applied-v1/CLAIMS.proposed.jsonl:5` | EO:12521 | quote_verbatim:not_found@operative_clauses[0].original_operative_text; quote_verbatim:not_found@operative_clauses[0].original_source.quote; quote_verbatim:not_found@original_representation.quote; quote_verbatim:not_found@savings_residuals.source.quote |
| `research/excavator/claude-apollo-2026-10-31/g10/packet/applied-v1/CLAIMS.proposed.jsonl:8` | EO:12891 | unverifiable items |
| `research/excavator/claude-apollo-2026-10-31/g10/packet/applied-v1/CLAIMS.proposed.jsonl:9` | EO:12921 | unverifiable items |
| `research/excavator/claude-apollo-2026-10-31/g10/packet/applied-v1/CLAIMS.proposed.jsonl:10` | EO:12987 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 40

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
