# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 2 (parse errors: 0)
- Orders with a claim (latest claim per order): 2
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 0; failed: 2
- Structural gate passed: 2

## Source references

- held_bytes_verified: 15

## Quotations

- not_found: 17

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/mommsen3-2026-11-10-decided02/mommsen3-decided02-review-v2/complete-v2/CLAIMS.selected.jsonl:1` | EO:7420 | quote_verbatim:not_found@operative_clauses[0].first_end.source.quote; quote_verbatim:not_found@operative_clauses[0].original_operative_text; quote_verbatim:not_found@operative_clauses[0].original_source.quote; quote_verbatim:not_found@original_representation.quote; quote_verbatim:not_found@savings_residuals.source.quote; quote_verbatim:not_found@source_notes[0].source.quote ... |
| `research/excavator/mommsen3-2026-11-10-decided02/mommsen3-decided02-review-v2/complete-v2/CLAIMS.selected.jsonl:2` | EO:7431 | quote_verbatim:not_found@operative_clauses[0].first_end.source.quote; quote_verbatim:not_found@operative_clauses[0].original_operative_text; quote_verbatim:not_found@operative_clauses[0].original_source.quote; quote_verbatim:not_found@original_representation.quote; quote_verbatim:not_found@savings_residuals.source.quote; quote_verbatim:not_found@source_notes[0].source.quote ... |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 4

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
