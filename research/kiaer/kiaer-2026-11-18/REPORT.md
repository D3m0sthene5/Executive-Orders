# Kiaer probe: tier census and transition costs

Every launched order is scored; failed orders count as no move. Starting tiers are the census tiers fixed before the run. Probe tiers are research tiers: T5 here means no listed gap and every proposition upheld by the second-family reviewer, not the tracker's ready count. Budget is in project usage units (0.1 x cache reads + 1 x other input + 4 x output). Nothing here changes a status, count or certification.

Orders launched: 80; scored with a review: 80; failed: none. Usage: 8,082,009 units (16,275,221 raw tokens; 0 turns had no usage report and were charged an estimate). Units count each provider's main model. Claude Code's side model (web-fetch summaries) used a further 8,999,546 raw tokens, not in the units; Claude Code reported 64.59 dollars at list price for all its turns, side model included. Blind-audit orders: 1 tool calls refused by the read rules, 0 denied paths cited in results.

Planted controls: 9 planted, 6 informative, 5 caught, 1 missed (catch rate 95% 0.44-0.97). Share of genuine reviews that flagged something: 0.562. Stop codes the reviewer marked wrong: 22/59.

## Per cell

| Cell | Pool | Orders | Failed | Advanced at first pass | Census start overstated | Worker agreed with census start | Median units | Leading stops |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| C01 T0, all eras | 70 | 4 | 0 | 0/4 (0.00-0.49) | 0 | 4/4 | 104,774 | OFFLINE 2, WEB 1, NOT_FOUND 1 |
| C02 T1, 1937 on | 103 | 6 | 0 | 3/6 (0.19-0.81) | 0 | 6/6 | 125,874 | TOOL_DEFECT 2, WEB 1, HELD_UNROUTED 1 |
| C03 T1, before 1937 | 2,142 | 10 | 0 | 2/10 (0.06-0.51) | 0 | 10/10 | 109,538 | WEB 3, NOT_FOUND 3, OFFLINE 2 |
| C04 T2, 1937 on, no rule lead | 1,700 | 10 | 0 | 8/10 (0.49-0.94) | 0 | 6/10 | 82,968 | NEEDS_RULING 2, WEB 2, NOT_FOUND 2 |
| C05 T2, before 1937 | 5,011 | 10 | 0 | 8/10 (0.49-0.94) | 0 | 4/10 | 90,588 | WEB 4, NOT_FOUND 2, OFFLINE 1 |
| C06 T3, 1937 on (blind status audit) | 1,436 | 3 | 0 | 1/3 (0.06-0.79) | 2 | 0/3 | 127,480 | NEEDS_RULING 2, WEB 1 |
| C07 T2, 1937 on, with a finding-aid rule lead | 2,433 | 7 | 0 | 3/7 (0.16-0.75) | 0 | 6/7 | 111,783 | WEB 3, NEEDS_RULING 1, OFFLINE 1 |
| C08 T3, before 1937 | 504 | 10 | 0 | 3/10 (0.11-0.60) | 5 | 0/10 | 95,598 | WEB 4, NEEDS_RULING 4 |
| C09 T4 | 348 | 10 | 0 | 5/10 (0.24-0.76) | 0 | 0/10 | 61,493 | WEB 2, NEEDS_RULING 1 |
| C10 T5, ready (blind status audit) | 1,255 | 3 | 0 | 0/3 (0.00-0.56) | 3 | 0/3 | 74,481 | NEEDS_RULING 1 |
| C11 Unnumbered identities | 1,816 | 7 | 0 | 3/7 (0.16-0.75) | 0 | 7/7 | 116,391 | NOT_FOUND 5, WEB 2 |

## Moves (first pass, census start tier)

| Group | Move | Attempts | Upheld | Weighted rate | 95% (unweighted) | After repair, not re-reviewed | Where it stopped |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| all numbered | T0->T1 | 4 | 0 | 0.0 | 0.00-0.49 | 1 | REVIEW_REJECTED 2, OFFLINE 1, NOT_FOUND 1 |
| all numbered | T1->T2 | 16 | 5 | 0.214 | 0.14-0.56 | 6 | REVIEW_REJECTED 6, WEB 2, TOOL_DEFECT 1 |
| all numbered | T2->T3 | 32 | 23 | 0.714 | 0.55-0.84 | 30 | REVIEW_REJECTED 9 |
| all numbered | T3->T4 | 33 | 24 | 0.861 | 0.56-0.85 | 29 | REVIEW_REJECTED 6, NEEDS_RULING 2, WEB 1 |
| all numbered | T4->T5 | 34 | 12 | 0.244 | 0.21-0.52 | 17 | REVIEW_REJECTED 6, WEB 4, NEEDS_RULING 4 |
| modern | T0->T1 | 1 | 0 | 0.0 | 0.00-0.79 | 0 | OFFLINE 1 |
| modern | T1->T2 | 6 | 3 | 0.5 | 0.19-0.81 | 4 | TOOL_DEFECT 1, WEB 1, REVIEW_REJECTED 1 |
| modern | T2->T3 | 20 | 13 | 0.582 | 0.43-0.82 | 18 | REVIEW_REJECTED 7 |
| modern | T3->T4 | 13 | 12 | 0.93 | 0.67-0.99 | 13 | REVIEW_REJECTED 1 |
| modern | T4->T5 | 21 | 9 | 0.4 | 0.24-0.64 | 13 | REVIEW_REJECTED 5, WEB 2, NOT_FOUND 2 |
| pre1937 | T0->T1 | 3 | 0 | 0.0 | 0.00-0.56 | 1 | REVIEW_REJECTED 2, NOT_FOUND 1 |
| pre1937 | T1->T2 | 10 | 2 | 0.2 | 0.06-0.51 | 2 | REVIEW_REJECTED 5, WEB 1, NOT_FOUND 1 |
| pre1937 | T2->T3 | 12 | 10 | 0.816 | 0.55-0.95 | 12 | REVIEW_REJECTED 2 |
| pre1937 | T3->T4 | 20 | 12 | 0.827 | 0.39-0.78 | 16 | REVIEW_REJECTED 5, NEEDS_RULING 2, WEB 1 |
| pre1937 | T4->T5 | 13 | 3 | 0.146 | 0.08-0.50 | 4 | NEEDS_RULING 3, WEB 2, NOT_FOUND 2 |
| unnumbered | T0->T1 | 7 | 3 | 0.429 | 0.16-0.75 | 3 | NOT_FOUND 4 |
| unnumbered | T1->T2 | 3 | 0 | 0.0 | 0.00-0.56 | 0 | WEB 2, REVIEW_REJECTED 1 |

## Measured units per order, by group, start tier and tiers gained

| Group | Start | Tiers gained | Orders | Median units | 80% range |
| --- | --- | ---: | ---: | ---: | --- |
| modern | T0 | 0 | 1 | 80,118 | 80,118-80,118 |
| modern | T1 | 0 | 3 | 126,044 | 86,365-129,320 |
| modern | T1 | 1 | 1 | 156,553 | 156,553-156,553 |
| modern | T1 | 3 | 2 | 108,242 | 94,273-122,211 |
| modern | T2 | 0 | 6 | 119,404 | 105,901-144,554 |
| modern | T2 | 1 | 1 | 146,382 | 146,382-146,382 |
| modern | T2 | 2 | 6 | 82,968 | 59,827-124,556 |
| modern | T2 | 3 | 4 | 53,246 | 35,640-71,108 |
| modern | T4 | 0 | 4 | 74,346 | 51,156-102,397 |
| modern | T4 | 1 | 5 | 61,646 | 54,185-73,781 |
| pre1937 | T0 | 0 | 3 | 119,640 | 95,854-191,591 |
| pre1937 | T1 | 0 | 8 | 109,538 | 54,791-121,217 |
| pre1937 | T1 | 3 | 2 | 117,368 | 90,620-144,117 |
| pre1937 | T2 | 0 | 2 | 106,976 | 85,446-128,506 |
| pre1937 | T2 | 1 | 1 | 103,656 | 103,656-103,656 |
| pre1937 | T2 | 2 | 6 | 90,588 | 63,669-133,602 |
| pre1937 | T2 | 3 | 1 | 43,571 | 43,571-43,571 |
| pre1937 | T3 | 0 | 7 | 102,110 | 77,156-141,161 |
| pre1937 | T3 | 1 | 1 | 115,916 | 115,916-115,916 |
| pre1937 | T3 | 2 | 2 | 48,505 | 43,139-53,871 |
| pre1937 | T4 | 0 | 1 | 61,340 | 61,340-61,340 |
| unnumbered | T0 | 0 | 4 | 108,536 | 92,809-128,454 |
| unnumbered | T0 | 1 | 3 | 151,518 | 110,829-173,046 |

## Cost per move (estimate, with 80% bootstrap bands)

Decomposed from first-pass units per order over the moves each order attempted. Use the measured table above where they disagree.

| Component | Units | 80% band |
| --- | ---: | --- |
| fixed_per_order | 63,320 | 58,370-66,711 |
| T0->T1 | 22,728 | 12,551-34,681 |
| T1->T2 | 11,711 | 2,702-19,352 |
| T2->T3 | 3,406 | 0-11,585 |
| T3->T4 | 3,044 | 0-9,917 |
| T4->T5 | 0 | 0-0 |

## Remaining work (estimate: one pass of the probe's route over each tier)

| Group and census tier | Orders | Median units per pass | Units for one pass | Expected to reach T5 per pass | Expected stalls by move |
| --- | ---: | ---: | ---: | ---: | --- |
| modern|T0 | 8 | 80,118 | 640,944 | n/a | too few attempts |
| modern|T1 | 103 | 125,874 | 12,964,970 | 11 | T1->T2 52, T2->T3 22, T3->T4 2, T4->T5 17 |
| modern|T2 | 4,133 | 96,742 | 399,834,686 | 895 | T2->T3 1,726, T3->T4 168, T4->T5 1,344 |
| modern|T3 | 1,436 | 0 | 0 | 534 | T3->T4 100, T4->T5 802 |
| modern|T4 | 341 | 61,646 | 21,021,286 | 136 | T4->T5 205 |
| pre1937|T0 | 62 | 119,640 | 7,417,680 | 0 | T0->T1 62, T1->T2 0, T2->T3 0, T3->T4 0, T4->T5 0 |
| pre1937|T1 | 2,142 | 109,538 | 234,629,325 | 42 | T1->T2 1,714, T2->T3 79, T3->T4 60, T4->T5 247 |
| pre1937|T2 | 5,011 | 90,588 | 453,938,974 | 494 | T2->T3 923, T3->T4 706, T4->T5 2,888 |
| pre1937|T3 | 504 | 95,598 | 48,181,644 | 61 | T3->T4 87, T4->T5 356 |
| pre1937|T4 | 7 | 61,340 | 429,380 | 1 | T4->T5 6 |

## Blind audit of existing statuses (C06, C10)

The reviewed blind conclusion matched the ledger status on 2 of 6 orders (95% 0.10-0.70). OPEN, an unreviewed conclusion and a failed order all count as disagreement. Each disagreement needs adjudication against the held text; agreement is not proof of correctness, because the worker and the ledger can rest on the same finding aid.

- EO:10886: ledger no, probe NO (reviewer: rejected, stop: NEEDS_RULING)
- EO:11666: ledger no, probe OPEN (reviewer: upheld, stop: NEEDS_RULING)
- EO:6313: ledger no, probe OPEN (reviewer: upheld, stop: NEEDS_RULING)
- EO:8163: ledger no, probe NO (reviewer: rejected, stop: WEB)

## Decision rules (fixed in the plan)

- A move upheld 70% of the time or more, cheaply: run it at scale first.
- Stops mostly HELD_UNROUTED or TOOL_DEFECT: fix code before spending tokens.
- Stops mostly WEB: raise the search cap and build a fetch job for those sources.
- Stops mostly OFFLINE: buy or scan film and archive records first.
- Stops mostly NEEDS_RULING: put the listed rulings to the owner.
- Census start overstated for more than 15% of a cell: fix the census before relying on its counts.
- Audit agreement below 95%: audit the ready set before any human review.
- Stop codes the reviewer marked wrong in more than 20% of checked cases: treat stop-code shares as soft.

## Other files in this folder

- `OWNER_TABLES.json`: sample arithmetic added after the run. Tier shares of the 15,002 numbered orders, in
  percent, T0 to T5: machine census 0.5, 15.0, 61.0, 12.9, 2.3, 8.4;
  reviewer-supported tier after one probe pass, weighted by cell
  0.5, 12.4, 25.7, 7.9, 42.6, 10.9. The second line is
  what one pass of this route can support from the evidence, not a count of anything adopted.
- `REVIEW_HISTORY.md`: how the launch plans were reviewed (four Codex rejections, then the owner's review).
- `CHANGES.md`, `CHANGES.diff`, `SOURCE.txt`: the code that ran and every change made to it.
- `WAVE_stage0.json`, `WAVE_stage1.json`: the plans with the owner's review; `review/`: Augur receipts, the four
  Codex reviews and the superseded plans.
- `SMOKE.json`: the two one-order smoke tests. `../kiaer-2026-11-18-stage0/`: the stage-0 report.

Spend outside this report's totals: two smoke tests and four plan reviews, 783,269 units and 1,659,693 raw tokens.
With them the probe cost 8,865,278 units and 17,934,914 raw tokens.
