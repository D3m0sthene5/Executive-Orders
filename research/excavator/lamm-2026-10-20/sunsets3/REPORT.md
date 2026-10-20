# Lamm III: sunsets and PEB queue (2026-10-20)

## Queue lines
- FETCH_QUEUE.jsonl holds 98 Lamm III lines, uncommitted and unpushed, none with URLs.
  - 84 are `claude-lamm3-queue`, report-date leads, from the earlier queue step.
  - 9 are `claude-lamm-t01-producer` lines, refined report-date windows.
  - 5 are `claude-lamm3-02-producer` lines.
  - batch_03 added none.

## Plants
Three plants went in and the reviewer caught three. Nothing is void.

| Batch | Plant | Genuine | Result |
|---|---|---|---|
| batch_01 | EO 13037 claim, sec1 first_end.date 1998-09-30 | 1999-09-30 | caught, code DATE |
| batch_02 | OTE:EO:11301@lamm source.signing_date 1966-09-12 | 1966-09-02 | caught |
| batch_03 | EO 13369 claim, whole_order_end.date 2005-11-01 | 2005-11-15 | caught |

- The planted values are labelled in `research/excavator/lamm-2026-10-20/sunsets3/PLANTED_CONTROLS_NOTE.md`.
- Only genuine work files were copied.

## Per batch

| Batch | Attempted | Upheld ends | Negatives confirmed | Refuted | Claims | Plant |
|---|---|---|---|---|---|---|
| 01 (probe) | 13 | 2 (EO 13037 whole; EO 6734-A partial, record only) | 11 | 0 genuine (1 plant) | 1 | caught |
| 02 | 13 | 2 (EO 13933 partial; EO 13111 partial) | 11 | 0 | 0 | caught |
| 03 | 12 | 1 (EO 13369 whole) | 11 | 0 | 1 | caught |
| All | 38 | 5 | 33 | 0 | 2 | 3 of 3 |

- The 33 negatives break down as 22 `end_date_needs_source`, 8 `not_an_end` and 3 `extended_or_renewed`.
- batch_01 passed the scale gate: 0.154 upheld per attempt against the 0.15 bar, one upheld claim, and the plant caught.

## Claims and checker
- Copied `research/readiness/claims/claude-lamm-t01-2026-10-20.jsonl` (EO 13037) and `claude-lamm-t02-2026-10-20.jsonl` (EO 13369).
- I ran the claim checker over the whole repo. It checked 273 claims with 0 parse errors, and both new lines passed mechanically and passed the gate.
- In the producer's scratch run, the EO 13037 line was only "mechanical unverified", because the EO 13108 bytes are custody-only on that machine. Nothing failed.
- The reviewers' AI reviews are not `eo-lifecycle-review/v1`. The certified count stays 0.

## Forecast vs outcome

| Id | Quantity | p10 / p50 / p90 | Measured | Result |
|---|---|---|---|---|
| L-20261020-45 | Upheld ends per attempt, probe | 0 / 0.15 / 0.38 | 0.154 | on p50; Llull warned the measure exceeds the census ceiling |
| L-20261020-47 | Upheld ends per attempt, all batches | 0.015 / 0.15 / 0.32 | 0.132 | inside the interval, just below p50 |
| L-20261020-46 | Upheld genuine claim lines | 0 / 1 / 3 | 2 | inside the interval |
| L-20261020-48 | Plants caught share | 0.1 / 1.0 / 1.0 | 1.0 | on p50 |

- Llull outcomes recorded: O-20261020-31, -32, -33 and -34.
- The ledger outcomes and the new `sunsets3/` files are uncommitted. I committed nothing, since the task did not ask for it.

## Expected new ready orders
- Expect 1 to 2: EO 13369 is clean and EO 13037 is likely.
- Both claims are NO orders with a whole end.
- The EO 13037 claim is unverified only in the producer's scratch run, where the EO 13108 bytes are not held.
- The remaining 33 negatives and 3 partials produce no claims. The main blocker is that report dates are not held.

SUMMARY: Lamm III ran all 3 batches (38 orders). 5 own-term ends were upheld, 0.132 per attempt, and the probe cleared the gate at 0.154. All 3 plants were caught. Two claims were filed (EO 13037 and EO 13369) and both pass the checker. Llull outcomes were recorded for all four forecasts (O-20261020-31 to -34). Expect 1 to 2 new ready orders. Nothing is committed, and the certified count stays 0.
