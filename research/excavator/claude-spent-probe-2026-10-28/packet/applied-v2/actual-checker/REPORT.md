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

- held_bytes_verified: 10

## Quotations

- exact: 12

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-spent-probe-2026-10-28/packet/applied-v2/CLAIMS.proposed.jsonl:1` | EO:1547 | date_valid:not_exact_iso_date@operative_clauses[0].first_end.source.signing_date; date_valid:not_exact_iso_date@operative_clauses[0].original_source.signing_date; date_valid:not_exact_iso_date@original_representation.signing_date; date_valid:not_exact_iso_date@savings_residuals.source.signing_date; date_valid:not_exact_iso_date@whole_order_end.source.signing_date |
| `research/excavator/claude-spent-probe-2026-10-28/packet/applied-v2/CLAIMS.proposed.jsonl:2` | EO:4782 | date_valid:not_exact_iso_date@operative_clauses[0].first_end.source.signing_date; date_valid:not_exact_iso_date@operative_clauses[0].original_source.signing_date; date_valid:not_exact_iso_date@original_representation.signing_date; date_valid:not_exact_iso_date@savings_residuals.source.signing_date; date_valid:not_exact_iso_date@whole_order_end.source.signing_date |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 4

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
