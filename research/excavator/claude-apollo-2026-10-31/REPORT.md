# Apollo claim swarm, 2026-10-31

Named for the Apollo program, whose 1969 landing came from thousands of separately checked parts assembled under one
flight plan. This run sent 444 orders through the claim-kit route in 19 parallel batches and filed **254 lifecycle
claims** in `research/readiness/claims/claude-2026-10-31-apollo-*.jsonl`. Every filed claim passed the actual
claim-checker, a blind separate-context review and `kit.py complete`. None is a human certification; the certified
whole-lifecycle count stays at 0.

## What was run

- **Orders.** Nine NRA batches (n01–n09, 193 orders) used the reviewed shared analysis of
  `research/excavator/claude-nira-sweep-2026-10-29/` (approvals end 1935-06-14 under S.J. Res. 113 section 2). Ten
  general batches (g01–g10, 241 post-1937 orders statused before today) were judged order by order. One-person
  civil-service waivers were left out, because their ends are intervals and the claim schema needs an exact date.
- **Producers.** One Sonnet agent per batch filled `decisions.csv` and `clauses.csv`, ran `kit.py apply` and
  `batch-check`, and wrote `PRODUCER_REPORT.md`. Producers submitted 300 claims and blocked 144 orders with named gaps.
- **Blind review.** One Opus agent per batch, in a separate context, reviewed every submitted claim with the planted
  controls in place (`tools/prompts/reviewer_*.txt`). It was told that some claims might be planted but not which.
- **Controls.** `tools/moon_plant.py` picked max(1, round(n/15)) claims per batch, seeded by the batch name, and
  moved every first-end and whole-order-end date back three years. That gave 20 controls in total. A control
  counted as caught only if the blind verdict was "rejected" and it named a date defect, a rule fixed before any
  review ran. **All 20 were caught.** Each genuine control version then got an after-reveal review from the same reviewer;
  15 were upheld and 5 were rejected on other grounds (EO 6876, 8163, 10103, 10915 and 12095), which blocks
  them.
- **Completion.** `tools/moon_finish.py` wrote the seed receipts and ran `make_completion.py` and
  `kit.py complete --publish`, one batch at a time under a lock (`tools/moon_fin.sh`). The private control keys
  stayed outside the repository; only their hashes are copied.

## Results

| Track | Orders | Submitted | Rejected by review | Dropped at completion | Filed |
|---|---|---|---|---|---|
| NRA (n01–n09) | 193 | 133 | 6 | 0 | 127 |
| General (g01–g10) | 251 | 167 | 34 | 6 | 127 |
| Total | 444 | 300 | 40 | 6 | **254** |

Completion dropped six reviewed claims for mechanical reasons. EO 12921, 12987 and 8937 rest on mirror or PDF bytes
whose custody the repository does not hold. EO 8168, 10570 and 10346 quote OCR text that does not match the
checker's copy.

The 40 review rejections fall into these groups:

- **Template carry-over.** Text from a sibling order describes something this order lacks: a standstill (EO 11013,
  12095), an "Approval recommended" line or hearing recitals (6875), a non-derogation sentence (10314, 10319) or a
  status-quo sentence (10285, 10303). 7 rejections.
- **Wrong citation detail.** Lettered EO numbers lost their suffix (6275, 6312, 6578), or the Federal Register page
  or issue date was wrong (9538, 10138, 10139). Other misdescriptions: a statute subsection (11436), a catalog note
  (10989, 11036), the dossier (10843), the end in the search text (10222), the number of disputes (10283) and
  three clauses (12891). 13 rejections.
- **Incomplete search of later or earlier instruments.** EO 6204A, 6876, 8129, 8163, 9949, 10103, 10634, 10693,
  10915, 11026, 11138, 11343 and 12121. 13 rejections.
- **Sourcing rules.** Later events were named in the reasoning but not recorded (12398, 12429), quotation marks
  were put around reworded text (11314, 11329, 11431), or a search was claimed that EO 12553 does not support
  (11195, 11355). 7 rejections.

## Cost and time (`TELEMETRY.csv`, `tools/moon_telemetry.py`)

Token counts are summed per API message from the agent transcripts. Active time excludes gaps over ten minutes, which
removes the usage-limit pause of 2026-10-31 19:30–23:24 EDT.

| Track and role | Model | Output tokens per filed claim | Cache-read tokens per filed claim | Active seconds per filed claim |
|---|---|---|---|---|
| NRA producer | Sonnet | 5,202 | 816,905 | 79 |
| NRA reviewer | Opus | 1,621 | 312,930 | 36 |
| General producer | Sonnet | 9,274 | 2,171,291 | 147 |
| General reviewer | Opus | 2,857 | 607,146 | 45 |

The coordinator (Opus, this session) is not included. Its work was planting controls, sending reveal messages and
running completion.

## Observations for future runs

- **Shared analysis halves the cost.** A filed NRA claim cost about 2.7 times fewer producer cache-read tokens than a
  general one, and its review cost about half as much. One reviewed analysis across a lot does most of the work.
- **Cache reads dominate.** They are 95% or more of input. Producers re-read large packet files (`READ.md`,
  `LOOKUPS.details.json`, 7.6 MB each) on every turn. A slimmer per-order view would cut cost more than any prompt change.
- **Many rejections are machine-detectable.** Most template carry-over and wrong-citation rejections (about 15 of
  40) could be caught by a deterministic lint run before review. Such a lint would check sentences quoted or
  described in the reasons against the order's own text, check that suffixed EO numbers match the APP file, and
  check FR page and issue dates against the citation. Each would save a blind-review slot and a resubmission.
- **Check the blocks before re-attempting.** Most of the 144 producer blocks need source bytes the proxy refuses
  (current CFR and U.S. Code text, FR page images, public land orders). They are not judgment failures, so retrying
  them without the sources would waste tokens.
- **Blinding held, with one disclosed slip.** The n01 reviewer's mis-scoped search printed two lines of another
  batch's claim file (EO 6903 and 7016). Its review records for EO 6471A and 7016 disclose this. Both claims were
  filed, and whether to keep them is an open owner question in Kean.

## Files

- `<batch>/packet[/supp]/`: the frozen packet, producer CSVs and report, `applied-v*`, `reviews/BLIND_REVIEW.jsonl`
  and `AFTER_REVEAL.jsonl`, `completion/` (manifest and seed receipts) and `complete-v1/`. In each `complete-v1`,
  `TRACKER_CLAIMS.jsonl` is stored gzipped (`gzip -n -9`), following the Astra production precedent. It is the
  deterministic union copy of all canonical claims.
- `tools/`: the coordinator scripts and prompt templates.
- `COORDINATOR_LOG.txt`: agent IDs, per-batch counts and adjudication notes.
- `TELEMETRY.csv` and `.json`: per-agent tokens, tool calls and active time.
