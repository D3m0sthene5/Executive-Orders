# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 9 (parse errors: 0)
- Orders with a claim (latest claim per order): 9
- All checks passed: 3
- Mechanical checks passed: 3; with unverifiable items: 3; failed: 3
- Structural gate passed: 9

## Source references

- custody_record_only: 12
- gpo_published_hash_match: 38
- held_bytes_verified: 19

## Quotations

- exact: 72
- normalised: 4
- not_found: 10
- too_short_to_verify: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v5/CLAIMS.proposed.jsonl:2` | EO:8078 | quote_verbatim:not_found@operative_clauses[0].original_operative_text; quote_verbatim:not_found@operative_clauses[0].original_source.quote; quote_verbatim:not_found@operative_clauses[1].original_operative_text; quote_verbatim:not_found@operative_clauses[1].original_source.quote; quote_verbatim:not_found@operative_clauses[2].original_operative_text; quote_verbatim:not_found@operative_clauses[2].original_source.quote ... |
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v5/CLAIMS.proposed.jsonl:3` | EO:8402 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v5/CLAIMS.proposed.jsonl:5` | EO:8538 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v5/CLAIMS.proposed.jsonl:7` | EO:9027 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v5/CLAIMS.proposed.jsonl:8` | EO:9052 | order_exists:not_in_universe@original_representation.quote |
| `research/excavator/claude-tribonian-2026-11-04/a01/packet/applied-v5/CLAIMS.proposed.jsonl:9` | EO:9405 | quote_verbatim:not_found@original_representation.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 28

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
