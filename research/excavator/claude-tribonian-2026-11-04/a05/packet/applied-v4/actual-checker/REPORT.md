# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 19 (parse errors: 0)
- Orders with a claim (latest claim per order): 19
- All checks passed: 16
- Mechanical checks passed: 16; with unverifiable items: 2; failed: 1
- Structural gate passed: 19

## Source references

- custody_record_only: 2
- gpo_published_hash_match: 187
- held_bytes_verified: 250

## Quotations

- exact: 614
- not_found: 1
- too_short_to_verify: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/a05/packet/applied-v4/CLAIMS.proposed.jsonl:2` | EO:12296 | quote_verbatim:not_found@operative_clauses[9].later_events[1].source.quote |
| `research/excavator/claude-tribonian-2026-11-04/a05/packet/applied-v4/CLAIMS.proposed.jsonl:9` | EO:12864 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/a05/packet/applied-v4/CLAIMS.proposed.jsonl:16` | EO:13038 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 197

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
