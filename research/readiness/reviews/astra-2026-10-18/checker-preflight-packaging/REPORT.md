# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 3 (parse errors: 0)
- Orders with a claim (latest claim per order): 3
- All checks passed: 1
- Mechanical checks passed: 1; with unverifiable items: 0; failed: 2
- Structural gate passed: 2

## Source references

- custody_record_only: 8
- gpo_published_hash_match: 115
- held_bytes_in_release_or_repo: 7
- no_hash_in_reference: 3
- not_held: 7

## Quotations

- exact: 227
- source_text_not_available: 15

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-packaging/EO_11782.jsonl:1` | EO:11782 | source_held:not_held@operative_clauses[0].first_end.supporting_sources[2].source; source_held:not_held@operative_clauses[1].first_end.supporting_sources[2].source; source_held:not_held@operative_clauses[2].first_end.supporting_sources[2].source; source_held:not_held@operative_clauses[3].first_end.supporting_sources[2].source; source_held:not_held@operative_clauses[4].first_end.supporting_sources[2].source; source_held:not_held@savings_residuals.supporting_sources[0].source ... |
| `research/readiness/reviews/astra-2026-10-18/checker-inputs-packaging/EO_12075.jsonl:1` | EO:12075 | source_held:no_hash_in_reference@supplemental_duties_analysis.sources[0]; source_held:no_hash_in_reference@supplemental_duties_analysis.sources[1]; source_held:no_hash_in_reference@supplemental_duties_analysis.sources[2]; structural_gate:clause_2_first_end@-; structural_gate:clause_4_first_end@-; structural_gate:savings_residuals_evidence@- ... |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 27

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
