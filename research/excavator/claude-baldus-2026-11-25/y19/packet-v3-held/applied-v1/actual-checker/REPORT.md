# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 8 (parse errors: 0)
- Orders with a claim (latest claim per order): 8
- All checks passed: 6
- Mechanical checks passed: 6; with unverifiable items: 2; failed: 0
- Structural gate passed: 8

## Source references

- custody_text_only: 14
- custody_text_only_disclosed: 2
- held_bytes_verified: 379

## Quotations

- exact: 539
- too_short_to_verify: 6

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-baldus-2026-11-25/y19/packet-v3-held/applied-v1/CLAIMS.proposed.jsonl:2` | EO:14065 | unverifiable items |
| `research/excavator/claude-baldus-2026-11-25/y19/packet-v3-held/applied-v1/CLAIMS.proposed.jsonl:3` | EO:14066 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 160

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
