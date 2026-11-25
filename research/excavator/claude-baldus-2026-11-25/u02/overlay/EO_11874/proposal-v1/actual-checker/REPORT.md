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

- custody_record_only: 1
- gpo_published_hash_match: 3

## Quotations

- exact: 4
- not_found: 1

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-baldus-2026-11-25/u02/overlay/EO_11874/proposal-v1/CLAIMS.working.jsonl:1` | EO:11874 | quote_verbatim:not_found@operative_clauses[0].current_predicate.source.quote |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 2

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
