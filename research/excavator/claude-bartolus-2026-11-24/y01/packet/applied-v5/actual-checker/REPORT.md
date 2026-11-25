# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 9 (parse errors: 0)
- Orders with a claim (latest claim per order): 9
- All checks passed: 5
- Mechanical checks passed: 5; with unverifiable items: 0; failed: 4
- Structural gate passed: 9

## Source references

- custody_record_only: 34
- gpo_published_hash_match: 133
- held_bytes_verified: 118

## Quotations

- exact: 310
- not_found: 35

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-bartolus-2026-11-24/y01/packet/applied-v5/CLAIMS.proposed.jsonl:3` | EO:11145 | quote_verbatim:not_found@operative_clauses[0].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[1].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[2].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[2].later_events[6].source.quote; quote_verbatim:not_found@operative_clauses[3].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[3].later_events[5].source.quote ... |
| `research/excavator/claude-bartolus-2026-11-24/y01/packet/applied-v5/CLAIMS.proposed.jsonl:4` | EO:10485 | quote_verbatim:not_found@operative_clauses[0].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[1].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[2].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[3].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[4].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[5].current_predicate.source.quote ... |
| `research/excavator/claude-bartolus-2026-11-24/y01/packet/applied-v5/CLAIMS.proposed.jsonl:5` | EO:10982 | quote_verbatim:not_found@operative_clauses[0].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[1].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[2].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[3].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[4].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[5].current_predicate.source.quote ... |
| `research/excavator/claude-bartolus-2026-11-24/y01/packet/applied-v5/CLAIMS.proposed.jsonl:6` | EO:12318 | quote_verbatim:not_found@operative_clauses[0].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[7].current_predicate.source.quote; quote_verbatim:not_found@operative_clauses[8].current_predicate.source.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 69

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
