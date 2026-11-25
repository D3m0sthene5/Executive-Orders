# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 9 (parse errors: 0)
- Orders with a claim (latest claim per order): 9
- All checks passed: 6
- Mechanical checks passed: 6; with unverifiable items: 3; failed: 0
- Structural gate passed: 9

## Source references

- gpo_published_hash_match: 92
- held_bytes_verified: 561

## Quotations

- exact: 845
- too_short_to_verify: 6

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-baldus-2026-11-25/y11/packet/applied-v3/CLAIMS.proposed.jsonl:3` | EO:12938 | unverifiable items |
| `research/excavator/claude-baldus-2026-11-25/y11/packet/applied-v3/CLAIMS.proposed.jsonl:4` | EO:12957 | unverifiable items |
| `research/excavator/claude-baldus-2026-11-25/y11/packet/applied-v3/CLAIMS.proposed.jsonl:8` | EO:13106 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 207

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
