# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 20 (parse errors: 0)
- Orders with a claim (latest claim per order): 20
- All checks passed: 19
- Mechanical checks passed: 19; with unverifiable items: 0; failed: 1
- Structural gate passed: 20

## Source references

- gpo_published_hash_match: 92
- held_bytes_verified: 16

## Quotations

- exact: 128
- not_found: 3

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-apollo-2026-10-31/g05/packet/complete-v1/CLAIMS.selected.jsonl:9` | EO:10570 | quote_verbatim:not_found@operative_clauses[0].original_operative_text; quote_verbatim:not_found@operative_clauses[0].original_source.quote; quote_verbatim:not_found@original_representation.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 43

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
