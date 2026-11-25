# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 1 (parse errors: 0)
- Orders with a claim (latest claim per order): 1
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 0; failed: 1
- Structural gate passed: 1

## Source references

- custody_record_only: 8
- gpo_published_hash_match: 11

## Quotations

- exact: 19
- not_found: 5
- source_text_not_available: 3

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-baldus-2026-11-25/y08/packet/applied-v4/CLAIMS.proposed.jsonl:1` | EO:12322 | quote_verbatim:not_found@operative_clauses[0].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[4].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[5].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[6].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[7].current_predicate.source.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 9

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
