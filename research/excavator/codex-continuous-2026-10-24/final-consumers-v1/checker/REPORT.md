# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 9 (parse errors: 0)
- Orders with a claim (latest claim per order): 9
- All checks passed: 8
- Mechanical checks passed: 9; with unverifiable items: 0; failed: 0
- Structural gate passed: 8

## Source references

- held_bytes_verified: 163

## Quotations

- exact: 196
- normalised: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/codex-continuous-2026-10-24/final-consumers-v1/CLAIMS.exact-selected.jsonl:4` | EO:10030 | structural_gate:clause_0_first_end@-; structural_gate:unresolved_material_gaps@- |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 44

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
