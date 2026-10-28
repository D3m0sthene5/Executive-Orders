# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 2 (parse errors: 0)
- Orders with a claim (latest claim per order): 2
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 1; failed: 1
- Structural gate passed: 2

## Source references

- custody_record_only: 2
- held_bytes_verified: 31

## Quotations

- exact: 44
- not_found: 1
- source_text_not_available: 3

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/production-cost-trace-2026-10-26/recovery/production-claims-v5/CLAIMS.recovered-v5.jsonl:1` | EO:8179 | unverifiable items |
| `research/excavator/production-cost-trace-2026-10-26/recovery/production-claims-v5/CLAIMS.recovered-v5.jsonl:2` | EO:8300 | quote_verbatim:not_found@original_representation.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 6

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
