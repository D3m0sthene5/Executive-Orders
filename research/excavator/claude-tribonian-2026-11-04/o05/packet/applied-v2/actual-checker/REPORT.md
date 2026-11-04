# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 30 (parse errors: 0)
- Orders with a claim (latest claim per order): 30
- All checks passed: 3
- Mechanical checks passed: 3; with unverifiable items: 26; failed: 1
- Structural gate passed: 30

## Source references

- custody_record_only: 143
- gpo_published_hash_match: 16

## Quotations

- exact: 189

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:1` | EO:8413 | date_after_signing:before_signing_date@operative_clauses[0].first_end.date; date_after_signing:before_signing_date@whole_order_end.date |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:2` | EO:8414 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:3` | EO:8421 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:4` | EO:8422 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:6` | EO:8448 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:7` | EO:8452 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:8` | EO:8453 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:9` | EO:8477 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:10` | EO:8481 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:11` | EO:8483 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:12` | EO:8489 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:13` | EO:8491 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:14` | EO:8503 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:15` | EO:8504 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:16` | EO:8520 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:17` | EO:8524 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:18` | EO:8525 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:21` | EO:8539 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:22` | EO:8543 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:23` | EO:8552 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:24` | EO:8554 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:25` | EO:8555 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:26` | EO:8562 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:27` | EO:8581 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:28` | EO:8582 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:29` | EO:8584 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o05/packet/applied-v2/CLAIMS.proposed.jsonl:30` | EO:8603 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 60

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
