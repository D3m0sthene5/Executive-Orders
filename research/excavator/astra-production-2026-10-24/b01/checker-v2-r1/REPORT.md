# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 1 (parse errors: 0)
- Orders with a claim (latest claim per order): 1
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 1; failed: 0
- Structural gate passed: 0

## Source references

- custody_record_only: 2
- held_bytes_verified: 29

## Quotations

- exact: 36

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/astra-production-2026-10-24/b01/CLAIMS.partial.proposed-v2.jsonl:1` | EO:11022 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@- ... |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 5

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
