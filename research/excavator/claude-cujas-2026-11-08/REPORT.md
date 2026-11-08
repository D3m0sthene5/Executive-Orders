# Cujas wave, 2026-11-08: Photius-stale recheck, batch c01

Named for Jacques Cujas, who restored corrupted legal texts by collating manuscripts. The owner approved the recheck (D-20261108-photius-recheck).

**Result: 21 claims filed** (`research/readiness/claims/claude-2026-11-08-cujas-c01.jsonl`). In the completion's tracker replay, ready goes from 1,023 to 1,044. No status, census or codebook changed. Certified: **0**.

## Route (Haloander h01)
- 160 of the 193 Photius-stale orders still need recheck: 38 at 99% or more, 116 at 95-99% and 6 at 80-95%. Of the rest, 25 were already ready, 25 were refiled by Haloander and 8 have no claim.
- **c01** holds the first 25 orders in the 99%-or-more band. They were prepared with `--replacement-proposal`, agent `claude`. Their claims belong to `claude-2026-11-04-tribonian-*`, Claude's own earlier wave, and the completion's own-claims rule lets agent `claude` file under a later-sorting name.
- Tribonian's reviewed sheets came from `origin/claude/tribonian-state` (2bc32c6d4) via `tools/carry.py`. Clause end dates match the canonical claims for 25 of 25.
- A Sonnet producer compared each transcription word by word with its GPO printing. All 25 agree apart from OCR noise and three variants: "sec." vs "section" (EO 8452), the typo "see." (EO 8525), and "Latte" vs "Latta" (EO 9238). batch-check passed 25 of 25, and Geddes raised 0 flags.
- Two blind Opus arms reviewed the batch. Both caught both planted controls (EO 8452 and EO 8562, end dates moved back three years) and upheld the genuine versions after reveal.
  - Arm A rejected EO 8256, 8402, 8497 and 8525. Two of these leave an FR "Revoked by" note unaddressed (8402: EO 8896; 8497: EO 8904).
  - Arm B rejected EO 8525.
  - Under the both-uphold rule, 21 claims file. `kit.py complete --publish` ran with 0 exceptions.
- **Gate:** `recovery.photius_stale` is not a ranked Bentham action, so the gate refuses it. The nearest measured action, `recovery.custody_stranded` (same route), gives **PILOT** (25 of 30 attempts; probability of beating the next action 1.00).

## Stopped
At 17:46Z the coordinating session lowered the cap from $35 to $22. Batch c02 (13 orders at 99% or more and 12 at 95-99%) was prepared and carried. Its producer was stopped before review, and its partial `applied-v1` was removed. Its packet is kept for the next wave, but it is stale once claim-kit rebuilds.

## Free work
The 58 board-report requests had not been fetched: source-ladder last published 2026-11-07 20:10, before they were queued at 21:56. I dispatched source-ladder alone (`requeue_depth=1`) on main at about 17:2xZ. Its result was not checked before close-out.

## Cost (list prices, `telemetry/AGENT_USAGE.csv`): about $20.9 at close-out, before the final PR turns
| Role | Model | $ |
|---|---|---:|
| Coordinator | Opus | 11.5 |
| Producer c01 | Sonnet | 1.3 |
| Arm A / Arm B | Opus | 4.8 / 2.5 |
| Producer c02 (stopped) | Sonnet | 0.9 |

The coordinator's cost went mostly to checking out about 900 large files under `jobs/` and the research inputs (the partial checkout hides fragment providers and the census, which prepare and the checker need). The worker cost of the filed batch was about $8.5, or about $0.41 per filed claim.
Completion receipts over 100 MB are stored as lossless `.gz` files with a `TRACKER_CLAIMS.COMPRESSED.json` SHA-256 record.
