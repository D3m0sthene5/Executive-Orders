# Phase 2 worker ledger (harness totals; cache read/write split and cash cost not exposed)
| worker | model | subagent_tokens | tool_uses | wall_s | deliverable |
|---|---|---|---|---|---|
| batch screen | sonnet | 123374 | 32 | 944 | SCREEN_CANDIDATES.json, screen.py |
| real-tree cache check | sonnet | 107888 | 14 | 951 | CACHE_CHECK.json, cachecheck.py |
| input-closure inventory | sonnet | 441330 | 95 | 1062 | INPUT_CLOSURE.md/.json |
| producer, rehearsal r1 (7 orders) | sonnet | 111493 | 16 | 207 | sheets, applied-v1, PRODUCER_REPORT.md |
| blind reviewer, rehearsal r1 (5 lines incl. 1 plant) | opus | 130996 | 27 | 218 | reviews/BLIND_REVIEW.jsonl |
| after-reveal, control adjudication, block check (same reviewer, continued) | opus | 54881 increment (185877 cumulative) | 20 | 187 | AFTER_REVEAL.jsonl, CONTROL_ADJUDICATION_NOTE.json, BLOCK_CHECK.jsonl |
| coordinator | opus | not exposed in this session | - | - | integration, fixes, receipts |
| final engineering review (fresh context, read-only) | opus | 146791 | 29 | 255 | findings 1-9; all fixed except the flagged adjudication policy question |
