# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 31 (parse errors: 0)
- Orders with a claim (latest claim per order): 31
- All checks passed: 25
- Mechanical checks passed: 25; with unverifiable items: 6; failed: 0
- Structural gate passed: 31

## Source references

- custody_record_only: 12
- held_bytes_in_release_or_repo: 5
- held_bytes_verified: 153

## Quotations

- exact: 201

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v3/CLAIMS.proposed.jsonl:17` | EO:7094 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v3/CLAIMS.proposed.jsonl:22` | EO:7336 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v3/CLAIMS.proposed.jsonl:24` | EO:7413 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v3/CLAIMS.proposed.jsonl:25` | EO:7444 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v3/CLAIMS.proposed.jsonl:27` | EO:7478 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v3/CLAIMS.proposed.jsonl:31` | EO:7531 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 62

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
