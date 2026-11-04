# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 20 (parse errors: 0)
- Orders with a claim (latest claim per order): 20
- All checks passed: 16
- Mechanical checks passed: 16; with unverifiable items: 2; failed: 2
- Structural gate passed: 20

## Source references

- custody_record_only: 2
- gpo_published_hash_match: 193
- held_bytes_verified: 250

## Quotations

- exact: 618
- not_found: 4
- too_short_to_verify: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/a05/packet/applied-v3/CLAIMS.proposed.jsonl:2` | EO:12296 | quote_verbatim:not_found@operative_clauses[9].later_events[1].source.quote |
| `research/excavator/claude-tribonian-2026-11-04/a05/packet/applied-v3/CLAIMS.proposed.jsonl:9` | EO:12521 | quote_verbatim:not_found@operative_clauses[0].original_operative_text; quote_verbatim:not_found@operative_clauses[0].original_source.quote; quote_verbatim:not_found@original_representation.quote |
| `research/excavator/claude-tribonian-2026-11-04/a05/packet/applied-v3/CLAIMS.proposed.jsonl:10` | EO:12864 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/a05/packet/applied-v3/CLAIMS.proposed.jsonl:17` | EO:13038 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 199

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
