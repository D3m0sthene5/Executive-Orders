# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 18 (parse errors: 0)
- Orders with a claim (latest claim per order): 18
- All checks passed: 14
- Mechanical checks passed: 14; with unverifiable items: 4; failed: 0
- Structural gate passed: 18

## Source references

- custody_record_only: 20
- gpo_published_hash_match: 373
- held_bytes_verified: 91

## Quotations

- exact: 681
- too_short_to_verify: 8

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/o21/packet/applied-v1/CLAIMS.proposed.jsonl:2` | EO:12771 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o21/packet/applied-v1/CLAIMS.proposed.jsonl:12` | EO:12914 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o21/packet/applied-v1/CLAIMS.proposed.jsonl:15` | EO:12922 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o21/packet/applied-v1/CLAIMS.proposed.jsonl:16` | EO:12944 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 223

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
