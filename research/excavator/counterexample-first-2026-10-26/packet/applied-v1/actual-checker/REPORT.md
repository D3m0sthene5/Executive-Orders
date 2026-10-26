# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 2 (parse errors: 0)
- Orders with a claim (latest claim per order): 2
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 0; failed: 2
- Structural gate passed: 2

## Source references

- held_bytes_verified: 14

## Quotations

- exact: 13
- normalised: 2
- not_found: 3

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/counterexample-first-2026-10-26/packet/applied-v1/CLAIMS.proposed.jsonl:1` | EO:7975A | quote_verbatim:not_found@original_representation.quote |
| `research/excavator/counterexample-first-2026-10-26/packet/applied-v1/CLAIMS.proposed.jsonl:2` | EO:8083 | quote_verbatim:not_found@original_representation.quote; quote_verbatim:not_found@savings_residuals.source.quote |

## Source identity (is the cited original this order's?)

- text_does_not_name_this_order: 4
- text_names_this_order: 2

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
