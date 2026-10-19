# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 14 (parse errors: 0)
- Orders with a claim (latest claim per order): 14
- All checks passed: 2
- Mechanical checks passed: 13; with unverifiable items: 0; failed: 1
- Structural gate passed: 2

## Source references

- gpo_published_hash_match: 260
- held_bytes_verified: 230

## Quotations

- exact: 709
- too_short_to_verify: 7

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_10152.jsonl:1` | EO:10152 | order_exists:not_in_universe@reviewed_later_events[5].page_image_verification.path; structural_gate:clause_0_state@-; structural_gate:clause_1_state@-; structural_gate:clause_2_state@-; structural_gate:clause_3_state@-; structural_gate:clause_4_state@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_11022.jsonl:1` | EO:11022 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_first_end@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_11256.jsonl:1` | EO:11256 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_first_end@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_11829.jsonl:1` | EO:11829 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_state@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_12075.jsonl:1` | EO:12075 | structural_gate:clause_2_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:savings_residuals_evidence@-; structural_gate:bounded_later_search@-; structural_gate:unresolved_material_gaps@- |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_12095.jsonl:1` | EO:12095 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@-; structural_gate:unresolved_material_gaps@- |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_12159.jsonl:1` | EO:12159 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@-; structural_gate:bounded_later_search@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_12182.jsonl:1` | EO:12182 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_first_end@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_12262.jsonl:1` | EO:12262 | structural_gate:clause_2_first_end@-; structural_gate:bounded_later_search@-; structural_gate:unresolved_material_gaps@- |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_12285.jsonl:1` | EO:12285 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_first_end@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_9799.jsonl:1` | EO:9799 | structural_gate:clause_0_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@-; structural_gate:bounded_later_search@-; structural_gate:unresolved_material_gaps@- |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-acquired/EO_9837.jsonl:1` | EO:9837 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@-; structural_gate:bounded_later_search@- ... |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 157

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
