# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 1 (parse errors: 0)
- Orders with a claim (latest claim per order): 1
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 0; failed: 1
- Structural gate passed: 1

## Source references

- held_bytes_verified: 22

## Quotations

- exact: 28
- normalised: 4
- not_found: 7

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/astra-cumulative-2026-10-24/EO_9452/PROPOSED_CLAIMS.jsonl:1` | EO:9452 | quote_verbatim:not_found@operative_clauses[0].later_events[0].after_amendment.source.quoted_parts[0]; quote_verbatim:not_found@operative_clauses[0].later_events[0].source.quoted_parts[0]; quote_verbatim:not_found@operative_clauses[1].later_events[0].after_amendment.source.quoted_parts[0]; quote_verbatim:not_found@operative_clauses[1].later_events[0].source.quoted_parts[0]; quote_verbatim:not_found@savings_residuals.supporting_sources[1].source.quoted_parts[0]; quote_verbatim:not_found@savings_residuals.supporting_sources[2].source.quoted_parts[0] ... |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 4

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
