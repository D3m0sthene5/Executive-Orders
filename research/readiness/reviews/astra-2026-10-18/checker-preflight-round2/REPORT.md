# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 8 (parse errors: 0)
- Orders with a claim (latest claim per order): 8
- All checks passed: 0
- Mechanical checks passed: 6; with unverifiable items: 0; failed: 2
- Structural gate passed: 1

## Source references

- custody_record_only: 1
- gpo_published_hash_match: 189
- held_bytes_in_release_or_repo: 1

## Quotations

- exact: 321
- not_found: 22
- source_text_not_available: 1

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round2/EO_11022.jsonl:1` | EO:11022 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_first_end@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round2/EO_11256.jsonl:1` | EO:11256 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_first_end@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round2/EO_11782.jsonl:1` | EO:11782 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:whole_order_end_evidence@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round2/EO_11829.jsonl:1` | EO:11829 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:clause_3_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:clause_5_state@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round2/EO_12075.jsonl:1` | EO:12075 | quote_verbatim:not_found@pending_event_leads[0].effective_date_instrument.quoted_parts[0]; quote_verbatim:not_found@pending_event_leads[0].effective_date_instrument.quoted_parts[1]; quote_verbatim:not_found@savings_residuals_analysis.supporting_sources[0].quoted_parts[0]; quote_verbatim:not_found@savings_residuals_analysis.supporting_sources[0].quoted_parts[1]; quote_verbatim:not_found@savings_residuals_analysis.supporting_sources[2].quoted_parts[0]; quote_verbatim:not_found@savings_residuals_analysis.supporting_sources[2].quoted_parts[1] ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round2/EO_12095.jsonl:1` | EO:12095 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@-; structural_gate:unresolved_material_gaps@- |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round2/EO_12159.jsonl:1` | EO:12159 | structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@-; structural_gate:whole_order_end_evidence@-; structural_gate:savings_residuals_evidence@-; structural_gate:bounded_later_search@- ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-round2/EO_9452.jsonl:1` | EO:9452 | quote_verbatim:not_found@savings_residuals.supporting_sources[0].quoted_parts[0]; quote_verbatim:not_found@savings_residuals.supporting_sources[1].quoted_parts[0]; quote_verbatim:not_found@savings_residuals.supporting_sources[2].quoted_parts[0]; quote_verbatim:not_found@savings_residuals.supporting_sources[3].quoted_parts[0] |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 75

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
