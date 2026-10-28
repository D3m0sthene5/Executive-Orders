# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 5 (parse errors: 0)
- Orders with a claim (latest claim per order): 5
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 1; failed: 4
- Structural gate passed: 5

## Source references

- held_bytes_verified: 83

## Quotations

- exact: 49
- normalised: 13
- not_found: 39

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/counterexample-first-2026-10-26/packet/PROPOSED_SELECTION.v1.jsonl:1` | EO:7975A | quote_verbatim:not_found@original_representation.quote |
| `research/excavator/counterexample-first-2026-10-26/packet/PROPOSED_SELECTION.v1.jsonl:2` | EO:8083 | unverifiable items |
| `research/excavator/counterexample-first-2026-10-26/packet/PROPOSED_SELECTION.v1.jsonl:3` | EO:8123 | quote_verbatim:not_found@counterevidence_checked[1].source.quote; quote_verbatim:not_found@operative_clauses[0].first_end.source.quote; quote_verbatim:not_found@operative_clauses[1].first_end.source.quote; quote_verbatim:not_found@operative_clauses[2].first_end.source.quote; quote_verbatim:not_found@savings_residuals.source.quote; quote_verbatim:not_found@whole_order_end.source.quote |
| `research/excavator/counterexample-first-2026-10-26/packet/PROPOSED_SELECTION.v1.jsonl:4` | EO:8126 | quote_verbatim:not_found@operative_clauses[0].original_operative_text; quote_verbatim:not_found@operative_clauses[0].original_source.quote; quote_verbatim:not_found@original_representation.quote; quote_verbatim:not_found@supporting_sources[0].quote; quote_verbatim:not_found@supporting_sources[1].quote; quote_verbatim:not_found@supporting_sources[2].quote |
| `research/excavator/counterexample-first-2026-10-26/packet/PROPOSED_SELECTION.v1.jsonl:5` | EO:8992 | quote_verbatim:not_found@operative_clauses[0].first_end.source.quote; quote_verbatim:not_found@operative_clauses[0].later_events[0].source.quote; quote_verbatim:not_found@operative_clauses[0].later_events[1].source.quote; quote_verbatim:not_found@operative_clauses[0].later_events[1].sources[0].quote; quote_verbatim:not_found@operative_clauses[0].later_events[1].sources[1].quote; quote_verbatim:not_found@operative_clauses[1].first_end.source.quote ... |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 12
- text_does_not_name_this_order: 4
- text_names_this_order: 2

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
