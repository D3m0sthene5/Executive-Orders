# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 1 (parse errors: 0)
- Orders with a claim (latest claim per order): 1
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 0; failed: 1
- Structural gate passed: 0

## Source references

- custody_record_only: 6
- held_bytes_in_release_or_repo: 2
- held_bytes_verified: 21

## Quotations

- exact: 33
- not_found: 3

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/astra-production-2026-10-24/b01/CLAIMS.partial.proposed-v1.jsonl:1` | EO:11022 | quote_verbatim:not_found@operative_clauses[0].later_events[0].before_text_source.quoted_parts[0]; quote_verbatim:not_found@operative_clauses[0].later_events[2].before_text_source.quoted_parts[0]; quote_verbatim:not_found@operative_clauses[0].later_events[3].supporting_sources[0].source.quoted_parts[0]; structural_gate:clause_0_first_end@-; structural_gate:clause_1_first_end@-; structural_gate:clause_2_first_end@- ... |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 5

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
