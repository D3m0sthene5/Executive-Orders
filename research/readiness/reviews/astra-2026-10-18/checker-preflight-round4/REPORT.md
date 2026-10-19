# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 6 (parse errors: 0)
- Orders with a claim (latest claim per order): 6
- All checks passed: 0
- Mechanical checks passed: 4; with unverifiable items: 2; failed: 0
- Structural gate passed: 0

## Source references

- custody_record_only: 1
- gpo_published_hash_match: 247
- held_bytes_verified: 50

## Quotations

- exact: 356
- too_short_to_verify: 18

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round4/EO_10152.jsonl:1` | EO:10152 | structural_gate:clause_0_state@-; structural_gate:clause_1_state@-; structural_gate:clause_2_state@-; structural_gate:clause_3_state@-; structural_gate:clause_4_state@-; structural_gate:clause_5_state@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round4/EO_10168.jsonl:1` | EO:10168 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_first_end@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round4/EO_10249.jsonl:1` | EO:10249 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@-; structural_gate:bounded_later_search@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round4/EO_10605.jsonl:1` | EO:10605 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@-; structural_gate:bounded_later_search@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round4/EO_10897.jsonl:1` | EO:10897 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_state@-; structural_gate:clause_4_first_end@-; structural_gate:whole_order_end_evidence@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round4/EO_9932.jsonl:1` | EO:9932 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_first_end@- ... |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 78

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
