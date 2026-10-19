# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 5 (parse errors: 0)
- Orders with a claim (latest claim per order): 5
- All checks passed: 0
- Mechanical checks passed: 4; with unverifiable items: 0; failed: 1
- Structural gate passed: 0

## Source references

- gpo_published_hash_match: 148

## Quotations

- exact: 227
- not_found: 6

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round3/EO_12182.jsonl:1` | EO:12182 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_first_end@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round3/EO_12262.jsonl:1` | EO:12262 | quote_verbatim:not_found@operative_clauses[2].dependency_sources[0].quoted_parts[0]; quote_verbatim:not_found@operative_clauses[2].dependency_sources[0].quoted_parts[1]; quote_verbatim:not_found@operative_clauses[2].dependency_sources[1].quoted_parts[0]; quote_verbatim:not_found@savings_residuals.supporting_sources[0].quoted_parts[0]; quote_verbatim:not_found@savings_residuals.supporting_sources[0].quoted_parts[1]; quote_verbatim:not_found@savings_residuals.supporting_sources[0].quoted_parts[2] ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round3/EO_12285.jsonl:1` | EO:12285 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_first_end@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round3/EO_9799.jsonl:1` | EO:9799 | structural_gate:clause_0_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@-; structural_gate:bounded_later_search@-; structural_gate:unresolved_material_gaps@- |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round3/EO_9837.jsonl:1` | EO:9837 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@-; structural_gate:bounded_later_search@- ... |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 48

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
