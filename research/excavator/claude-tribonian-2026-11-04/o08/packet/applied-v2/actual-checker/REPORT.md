# Claim checker report

Mechanical checks of every claim in `research/readiness/claims/`. A pass means the
sources are held, the quotations are word for word, the dates and order numbers are
possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**

- Claims checked: 28 (parse errors: 0)
- Orders with a claim (latest claim per order): 28
- All checks passed: 0
- Mechanical checks passed: 0; with unverifiable items: 26; failed: 2
- Structural gate passed: 28

## Source references

- custody_record_only: 130
- gpo_published_hash_match: 13

## Quotations

- exact: 165
- not_found: 7

## Claims with problems (first 100)

| claim | order | problems |
|---|---|---|
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:1` | EO:8907 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:2` | EO:8913 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:3` | EO:8917 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:4` | EO:8918 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:5` | EO:8919 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:6` | EO:8925 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:7` | EO:8933 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:8` | EO:8934 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:9` | EO:8935 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:10` | EO:8936 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:11` | EO:8945 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:12` | EO:8948 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:13` | EO:8949 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:14` | EO:8953 | quote_verbatim:not_found@operative_clauses[0].original_operative_text; quote_verbatim:not_found@operative_clauses[0].original_source.quote; quote_verbatim:not_found@operative_clauses[1].first_end.source.quote; quote_verbatim:not_found@operative_clauses[1].original_operative_text; quote_verbatim:not_found@operative_clauses[1].original_source.quote; quote_verbatim:not_found@original_representation.quote ... |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:15` | EO:8958 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:16` | EO:8961 | order_exists:not_in_universe@operative_clauses[0].first_end.source.quote |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:17` | EO:8966 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:18` | EO:8967 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:19` | EO:8968 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:20` | EO:8993 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:21` | EO:8994 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:22` | EO:8995 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:23` | EO:8996 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:24` | EO:8997 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:25` | EO:9002 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:26` | EO:9003 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:27` | EO:9009 | unverifiable items |
| `research/excavator/claude-tribonian-2026-11-04/o08/packet/applied-v2/CLAIMS.proposed.jsonl:28` | EO:9010 | unverifiable items |

## Source identity (is the cited original this order's?)

- recorded_for_this_order: 57

Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode `non_pass_rows`). Per claim: `PER_CLAIM.json`.
