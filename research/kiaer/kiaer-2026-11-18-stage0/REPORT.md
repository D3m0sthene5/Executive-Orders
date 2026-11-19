# Kiaer probe: tier census and transition costs

Every launched order is scored; failed orders count as no move. Starting tiers are the census tiers fixed before the run. Probe tiers are research tiers: T5 here means no listed gap and every proposition upheld by the second-family reviewer, not the tracker's ready count. Budget is in project usage units (0.1 x cache reads + 1 x other input + 4 x output). Nothing here changes a status, count or certification.

Orders launched: 29; scored with a review: 29; failed: none. Usage: 3,025,975 units (6,124,129 raw tokens; 0 turns had no usage report and were charged an estimate). Units count each provider's main model. Claude Code's side model (web-fetch summaries) used a further 4,040,068 raw tokens, not in the units; Claude Code reported 23.34 dollars at list price for all its turns, side model included. Blind-audit orders: 1 tool calls refused by the read rules, 0 denied paths cited in results.

Planted controls: 3 planted, 2 informative, 2 caught, 0 missed (catch rate 95% 0.34-1.0). Share of genuine reviews that flagged something: 0.552. Stop codes the reviewer marked wrong: 10/23.

## Per cell

| Cell | Pool | Orders | Failed | Advanced at first pass | Census start overstated | Worker agreed with census start | Median units | Leading stops |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| C01 T0, all eras | 70 | 3 | 0 | 0/3 (0.00-0.56) | 0 | 3/3 | 119,640 | OFFLINE 2, NOT_FOUND 1 |
| C02 T1, 1937 on | 103 | 3 | 0 | 1/3 (0.06-0.79) | 0 | 3/3 | 130,139 | TOOL_DEFECT 1, WEB 1, HELD_UNROUTED 1 |
| C03 T1, before 1937 | 2,142 | 3 | 0 | 0/3 (0.00-0.56) | 0 | 3/3 | 103,744 | WEB 1, NOT_FOUND 1, OFFLINE 1 |
| C04 T2, 1937 on, no rule lead | 1,700 | 3 | 0 | 2/3 (0.21-0.94) | 0 | 2/3 | 90,688 | NEEDS_RULING 1, WEB 1, NOT_FOUND 1 |
| C05 T2, before 1937 | 5,011 | 3 | 0 | 3/3 (0.44-1.00) | 0 | 2/3 | 79,296 | WEB 1, NOT_FOUND 1, OFFLINE 1 |
| C06 T3, 1937 on (blind status audit) | 1,436 | 1 | 0 | 0/1 (0.00-0.79) | 1 | 0/1 | 148,413 | NEEDS_RULING 1 |
| C07 T2, 1937 on, with a finding-aid rule lead | 2,433 | 3 | 0 | 2/3 (0.21-0.94) | 0 | 3/3 | 111,783 | NEEDS_RULING 1 |
| C08 T3, before 1937 | 504 | 3 | 0 | 1/3 (0.06-0.79) | 1 | 0/3 | 59,704 | WEB 1, NEEDS_RULING 1 |
| C09 T4 | 348 | 3 | 0 | 2/3 (0.21-0.94) | 0 | 0/3 | 78,394 |  |
| C10 T5, ready (blind status audit) | 1,255 | 1 | 0 | 0/1 (0.00-0.79) | 1 | 0/1 | 61,253 | NEEDS_RULING 1 |
| C11 Unnumbered identities | 1,816 | 3 | 0 | 1/3 (0.06-0.79) | 0 | 3/3 | 100,657 | NOT_FOUND 2, WEB 1 |

## Moves (first pass, census start tier)

| Group | Move | Attempts | Upheld | Weighted rate | 95% (unweighted) | After repair, not re-reviewed | Where it stopped |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| all numbered | T0->T1 | 3 | 0 | 0.0 | 0.00-0.56 | 0 | REVIEW_REJECTED 1, OFFLINE 1, NOT_FOUND 1 |
| all numbered | T1->T2 | 6 | 1 | 0.015 | 0.03-0.56 | 1 | WEB 2, TOOL_DEFECT 1, NOT_FOUND 1 |
| all numbered | T2->T3 | 10 | 7 | 0.846 | 0.40-0.89 | 8 | REVIEW_REJECTED 3 |
| all numbered | T3->T4 | 10 | 8 | 0.959 | 0.49-0.94 | 8 | WEB 1, NEEDS_RULING 1 |
| all numbered | T4->T5 | 11 | 4 | 0.146 | 0.15-0.65 | 6 | REVIEW_REJECTED 2, NOT_FOUND 2, NEEDS_RULING 1 |
| modern | T0->T1 | 1 | 0 | 0.0 | 0.00-0.79 | 0 | OFFLINE 1 |
| modern | T1->T2 | 3 | 1 | 0.333 | 0.06-0.79 | 1 | TOOL_DEFECT 1, WEB 1 |
| modern | T2->T3 | 7 | 4 | 0.661 | 0.25-0.84 | 5 | REVIEW_REJECTED 3 |
| modern | T3->T4 | 4 | 4 | 1.0 | 0.51-1.00 | 4 |  |
| modern | T4->T5 | 7 | 3 | 0.336 | 0.16-0.75 | 5 | REVIEW_REJECTED 2, NEEDS_RULING 1, NOT_FOUND 1 |
| pre1937 | T0->T1 | 2 | 0 | 0.0 | 0.00-0.66 | 0 | REVIEW_REJECTED 1, NOT_FOUND 1 |
| pre1937 | T1->T2 | 3 | 0 | 0.0 | 0.00-0.56 | 0 | WEB 1, NOT_FOUND 1, OFFLINE 1 |
| pre1937 | T2->T3 | 3 | 3 | 1.0 | 0.44-1.00 | 3 |  |
| pre1937 | T3->T4 | 6 | 4 | 0.939 | 0.30-0.90 | 4 | WEB 1, NEEDS_RULING 1 |
| pre1937 | T4->T5 | 4 | 1 | 0.032 | 0.05-0.70 | 1 | WEB 1, NOT_FOUND 1, OFFLINE 1 |
| unnumbered | T0->T1 | 3 | 1 | 0.333 | 0.06-0.79 | 1 | NOT_FOUND 2 |
| unnumbered | T1->T2 | 1 | 0 | 0.0 | 0.00-0.79 | 0 | WEB 1 |

## Measured units per order, by group, start tier and tiers gained

| Group | Start | Tiers gained | Orders | Median units | 80% range |
| --- | --- | ---: | ---: | ---: | --- |
| modern | T0 | 0 | 1 | 80,118 | 80,118-80,118 |
| modern | T1 | 0 | 2 | 128,092 | 126,454-129,730 |
| modern | T1 | 1 | 1 | 156,553 | 156,553-156,553 |
| modern | T2 | 0 | 2 | 126,792 | 114,785-138,800 |
| modern | T2 | 2 | 3 | 90,688 | 78,336-140,034 |
| modern | T2 | 3 | 1 | 68,707 | 68,707-68,707 |
| modern | T4 | 0 | 1 | 93,666 | 93,666-93,666 |
| modern | T4 | 1 | 2 | 65,710 | 55,562-75,857 |
| pre1937 | T0 | 0 | 2 | 164,610 | 128,634-200,585 |
| pre1937 | T1 | 0 | 3 | 103,744 | 55,554-115,601 |
| pre1937 | T2 | 2 | 3 | 79,296 | 54,293-102,878 |
| pre1937 | T3 | 0 | 2 | 87,002 | 65,164-108,841 |
| pre1937 | T3 | 2 | 1 | 41,798 | 41,798-41,798 |
| unnumbered | T0 | 0 | 2 | 111,530 | 93,854-129,205 |
| unnumbered | T0 | 1 | 1 | 100,657 | 100,657-100,657 |

## Cost per move (estimate, with 80% bootstrap bands)

Decomposed from first-pass units per order over the moves each order attempted. Use the measured table above where they disagree.

| Component | Units | 80% band |
| --- | ---: | --- |
| fixed_per_order | 52,288 | 29,522-61,988 |
| T0->T1 | 31,660 | 11,618-56,306 |
| T1->T2 | 33,558 | 16,343-56,084 |
| T2->T3 | 20,524 | 0-28,432 |
| T3->T4 | 5,361 | 0-26,923 |
| T4->T5 | 318 | 0-15,435 |

## Remaining work (estimate: one pass of the probe's route over each tier)

| Group and census tier | Orders | Median units per pass | Units for one pass | Expected to reach T5 per pass | Expected stalls by move |
| --- | ---: | ---: | ---: | ---: | --- |
| modern|T0 | 8 | 80,118 | 640,944 | n/a | too few attempts |
| modern|T1 | 103 | 130,139 | 13,404,317 | 8 | T1->T2 69, T2->T3 12, T3->T4 0, T4->T5 15 |
| modern|T2 | 4,133 | 101,236 | 418,406,322 | 918 | T2->T3 1,400, T3->T4 0, T4->T5 1,814 |
| modern|T3 | 1,436 | 0 | 0 | 483 | T3->T4 0, T4->T5 953 |
| modern|T4 | 341 | 78,394 | 26,732,354 | 115 | T4->T5 226 |
| pre1937|T0 | 62 | 164,610 | 10,205,789 | n/a | too few attempts |
| pre1937|T1 | 2,142 | 103,744 | 222,219,648 | 0 | T1->T2 2,142, T2->T3 0, T3->T4 0, T4->T5 0 |
| pre1937|T2 | 5,011 | 79,296 | 397,352,256 | 153 | T2->T3 0, T3->T4 305, T4->T5 4,553 |
| pre1937|T3 | 504 | 59,704 | 30,090,816 | 15 | T3->T4 31, T4->T5 458 |
| pre1937|T4 | 7 | 0 | 0 | 0 | T4->T5 7 |

## Blind audit of existing statuses (C06, C10)

The reviewed blind conclusion matched the ledger status on 0 of 2 orders (95% 0.00-0.66). OPEN, an unreviewed conclusion and a failed order all count as disagreement. Each disagreement needs adjudication against the held text; agreement is not proof of correctness, because the worker and the ledger can rest on the same finding aid.

- EO:10886: ledger no, probe NO (reviewer: rejected, stop: NEEDS_RULING)
- EO:6313: ledger no, probe OPEN (reviewer: upheld, stop: NEEDS_RULING)

## Decision rules (fixed in the plan)

- A move upheld 70% of the time or more, cheaply: run it at scale first.
- Stops mostly HELD_UNROUTED or TOOL_DEFECT: fix code before spending tokens.
- Stops mostly WEB: raise the search cap and build a fetch job for those sources.
- Stops mostly OFFLINE: buy or scan film and archive records first.
- Stops mostly NEEDS_RULING: put the listed rulings to the owner.
- Census start overstated for more than 15% of a cell: fix the census before relying on its counts.
- Audit agreement below 95%: audit the ready set before any human review.
- Stop codes the reviewer marked wrong in more than 20% of checked cases: treat stop-code shares as soft.
