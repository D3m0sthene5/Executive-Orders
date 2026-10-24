# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 2 (parse errors: 0)
- Orders with a claim (latest claim per order): 2
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 0; failed: 2
- Structural gate passed: 0

## Source references

- held_bytes_verified: 28

## Quotations

- exact: 35
- not_found: 27

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/astra-production-2026-10-24/b02/review/complete-v1/CLAIMS.selected.jsonl:1` | EO:11829 | quote_verbatim:not_found@operative_clauses[0].first_end.legal_sources[0].quote; quote_verbatim:not_found@operative_clauses[0].first_end.legal_sources[1].quote; quote_verbatim:not_found@operative_clauses[1].first_end.legal_sources[0].quote; quote_verbatim:not_found@operative_clauses[1].first_end.legal_sources[1].quote; quote_verbatim:not_found@operative_clauses[2].first_end.legal_sources[0].quote; quote_verbatim:not_found@operative_clauses[2].first_end.legal_sources[1].quote ... |
| `research/excavator/astra-production-2026-10-24/b02/review/complete-v1/CLAIMS.selected.jsonl:2` | EO:11853 | quote_verbatim:not_found@operative_clauses[0].first_end.legal_sources[0].quote; quote_verbatim:not_found@operative_clauses[0].first_end.legal_sources[1].quote; quote_verbatim:not_found@original_representation.quote; quote_verbatim:not_found@research_sources[0].quote; quote_verbatim:not_found@research_sources[1].quote; quote_verbatim:not_found@research_sources[2].quote ... |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 10

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
