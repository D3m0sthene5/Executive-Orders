# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 9 (parse errors: 0)
- Orders with a claim (latest claim per order): 9
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 6; failed: 3
- Structural gate passed: 9

## Source references

- custody_record_only: 47
- held_but_different_hash: 2
- held_bytes_in_release_or_repo: 5

## Quotations

- exact: 42
- normalised: 16
- not_found: 3
- other_copy_exact: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/namier-serial-exemptions-2026-10-28/packet/applied-v1/CLAIMS.proposed.jsonl:1` | EO:6088 | source_held:held_but_different_hash@operative_clauses[0].first_end.source; source_held:held_but_different_hash@whole_order_end.source |
| `research/excavator/namier-serial-exemptions-2026-10-28/packet/applied-v1/CLAIMS.proposed.jsonl:2` | EO:6998 | unverifiable items |
| `research/excavator/namier-serial-exemptions-2026-10-28/packet/applied-v1/CLAIMS.proposed.jsonl:3` | EO:7597 | unverifiable items |
| `research/excavator/namier-serial-exemptions-2026-10-28/packet/applied-v1/CLAIMS.proposed.jsonl:4` | EO:6013 | unverifiable items |
| `research/excavator/namier-serial-exemptions-2026-10-28/packet/applied-v1/CLAIMS.proposed.jsonl:5` | EO:6615 | unverifiable items |
| `research/excavator/namier-serial-exemptions-2026-10-28/packet/applied-v1/CLAIMS.proposed.jsonl:6` | EO:6974 | unverifiable items |
| `research/excavator/namier-serial-exemptions-2026-10-28/packet/applied-v1/CLAIMS.proposed.jsonl:7` | EO:6577 | quote_verbatim:not_found@operative_clauses[0].later_events[0].source.quote |
| `research/excavator/namier-serial-exemptions-2026-10-28/packet/applied-v1/CLAIMS.proposed.jsonl:8` | EO:6773 | quote_verbatim:not_found@original_representation.quote; quote_verbatim:not_found@savings_residuals.source.quote |
| `research/excavator/namier-serial-exemptions-2026-10-28/packet/applied-v1/CLAIMS.proposed.jsonl:9` | EO:7217 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 18

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
