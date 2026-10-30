# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 5 (parse errors: 0)
- Orders with a claim (latest claim per order): 5
- All checks passed: 3
- Mechanical checks passed: 3; with unverifiable items: 1; failed: 1
- Structural gate passed: 5

## Source references

- custody_record_only: 10
- held_bytes_verified: 15

## Quotations

- exact: 28
- normalised: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/readiness/claims/claude-2026-10-28-spent-probe.jsonl:1` | EO:1547 | working_text_policy:invalid_working_text@operative_clauses[0].first_end.source; working_text_policy:invalid_working_text@operative_clauses[0].original_source; working_text_policy:invalid_working_text@original_representation; working_text_policy:invalid_working_text@savings_residuals.source; working_text_policy:invalid_working_text@whole_order_end.source |
| `research/readiness/claims/claude-2026-10-28-spent-probe.jsonl:2` | EO:4782 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 10

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `all_rows`). Per claim: `PER_CLAIM.json`.
