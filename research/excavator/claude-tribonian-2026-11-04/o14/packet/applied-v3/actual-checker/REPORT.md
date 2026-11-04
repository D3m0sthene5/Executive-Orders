# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 10 (parse errors: 0)
- Orders with a claim (latest claim per order): 10
- All checks passed: 8
- Mechanical checks passed: 8; with unverifiable items: 0; failed: 2
- Structural gate passed: 10

## Source references

- gpo_published_hash_match: 52

## Quotations

- exact: 57
- not_found: 6

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/o14/packet/applied-v3/CLAIMS.proposed.jsonl:2` | EO:10508 | quote_verbatim:not_found@operative_clauses[0].first_end.source.quote; quote_verbatim:not_found@operative_clauses[0].original_operative_text; quote_verbatim:not_found@operative_clauses[0].original_source.quote; quote_verbatim:not_found@original_representation.quote; quote_verbatim:not_found@savings_residuals.source.quote; quote_verbatim:not_found@whole_order_end.source.quote |
| `research/excavator/claude-tribonian-2026-11-04/o14/packet/applied-v3/CLAIMS.proposed.jsonl:10` | EO:10687 | order_exists:not_in_universe@operative_clauses[0].first_end.source.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 21

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
