# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 2 (parse errors: 0)
- Orders with a claim (latest claim per order): 2
- All checks passed: 0
- Mechanical checks passed: 2; with unverifiable items: 0; failed: 0
- Structural gate passed: 0

## Source references

- held_bytes_verified: 58

## Quotations

- exact: 66

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/astra-production-2026-10-24/b02/review/complete-v2/CLAIMS.selected.jsonl:1` | EO:11829 | structural_gate:clause_5_first_end@-; structural_gate:clause_6_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@-; structural_gate:bounded_later_search@-; structural_gate:unresolved_material_gaps@- |
| `research/excavator/astra-production-2026-10-24/b02/review/complete-v2/CLAIMS.selected.jsonl:2` | EO:11853 | structural_gate:savings_residuals_evidence@-; structural_gate:bounded_later_search@-; structural_gate:unresolved_material_gaps@- |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 10

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
