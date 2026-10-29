# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 32 (parse errors: 0)
- Orders with a claim (latest claim per order): 32
- All checks passed: 2
- Mechanical checks passed: 2; with unverifiable items: 28; failed: 2
- Structural gate passed: 32

## Source references

- custody_record_only: 157
- held_but_different_hash: 2
- held_bytes_in_release_or_repo: 5
- held_bytes_verified: 11

## Quotations

- exact: 147
- normalised: 56
- not_found: 2
- other_copy_exact: 2

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:2` | EO:6030 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:3` | EO:6168 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:4` | EO:6263 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:5` | EO:6302 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:6` | EO:6610 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:7` | EO:6687 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:8` | EO:6703 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:9` | EO:6753 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:10` | EO:6864 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:11` | EO:6931 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:12` | EO:6933 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:13` | EO:6975 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:14` | EO:7030 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:15` | EO:7042 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:16` | EO:7072 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:17` | EO:7094 | source_held:held_but_different_hash@operative_clauses[0].first_end.source; source_held:held_but_different_hash@whole_order_end.source |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:18` | EO:7184 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:19` | EO:7230 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:20` | EO:7238 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:21` | EO:7286 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:22` | EO:7314 | quote_verbatim:not_found@original_representation.quote; quote_verbatim:not_found@savings_residuals.source.quote |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:23` | EO:7336 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:24` | EO:7385 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:25` | EO:7413 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:26` | EO:7444 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:27` | EO:7457 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:28` | EO:7478 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:29` | EO:7494 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:31` | EO:7519 | unverifiable items |
| `research/excavator/claude-production-2026-10-28/b1c/packet/supp/applied-v2/CLAIMS.proposed.jsonl:32` | EO:7531 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 64

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
