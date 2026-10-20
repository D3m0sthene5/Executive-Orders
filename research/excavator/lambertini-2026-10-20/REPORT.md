# Lambertini: savings residuals and counterevidence (2026-10-20)

Checkers all pass (`jobs/lambertini` 9 of 9 tests, `llull check` ok, `kit.py check` clean on all 6 claims). Nothing is committed or pushed.

**What closes each step**
- **savings_residuals:** a claim field `{state, reason, source}` that passes the gate and the claim-checker.
  - The state is `none_after_bounded_search`, `continuing_independent` or `transferred_or_accrued`.
  - The source needs https, sha256 and a page.
  - There is no machine route, and `research/readiness/EXHAUSTED.jsonl` has 0 lines.
- **counterevidence:** a claim `later_source_search` entry, or the machine search covering an order that has an OFR catalog entry and no flags.
- **Neither step is ever the last one open:** among the 3,221 decided not-ready orders, savings is the only open step on 0 and counterevidence on 2.

**The unit**
- **Savings** rides on the claim that also closes ending and has no stand-alone unit. One reading per ending instrument covers every order it ends: 84 instruments cover 807 orders, and EO 12553 alone covers 332.
- The `S0_none_candidate` class (156 orders) prefills "no savings", and a reader must still confirm it.
- **Counterevidence** gets a draft search record for each of the 688 orders with no catalog entry. 18 have no lead and their original text, 112 have a lead, and 558 lack the original text. It closes nothing until the owner rules the record adequate.

**Probe result against forecast**

| Forecast | Quantity | p10 / p50 / p90 | Measured | Llull outcome |
|---|---|---|---|---|
| L-20261020-17 | upheld per attempt | 0 / 0.15 / 0.45 | 0.30 (6 of 20) | O-20261020-10 |
| L-20261020-18 | S0 prefill agreement | 0.05 / 0.8 / 1.0 | 0.667 (4 of 6) | O-20261020-11 |
| L-20261020-19 | scale gate passed | prob 0.2 | 1 | O-20261020-12 |

- **Forecast 17:** this is above p50. Llull warned that 0.30 exceeds the census ceiling of 0.026, meaning the census gate missed a route (the held acting EO text). That was already flagged on the forecast.
- **Forecast 18:** the prefill was overruled on EO 10897 and EO 11800, so the reader confirmation step does real work.
- **Forecast 19:** the gate passes on 6 upheld with 0 savings states overturned. It fails (4 of 20) if only the claims that can close a step today count.
- **Probe outcome:** 6 claims were upheld and 0 rejected. 10 orders were blocked at ending, and 4 were skipped as overlap with Astra's claims. Only 4 claims can close a step now (EO 10249, 10897, 12089, 12262).
- **Waiting on source bytes:** EO 11800 and EO 12852 wait until the claim-checker can confirm the held source files.
- **D6 (no later event removed or ignored):** it found no wrong ending or savings state. Four amending orders are described in prose but not attached as later events: 12608 and 13286 (for 11800), 12855 (for 12852) and 12107 (for 12089). Attach them before any commit.

**Needs the owner**
- A ruling on the report-deadline question. It blocks 10 probe orders at ending, because report dates are not held.
- A ruling on whether the pre-1937 draft search records are adequate for counterevidence.
- Permission to commit the claims, the excavator records and the job, and a go-ahead to coordinate with Rastell on the 10 probe orders that overlap EO 12553.
- Fetching the original texts for the 558 orders that lack them.

**Scale recommendation**
- Scale in a limited way, not to all 807 orders. Scale only the instrument-level savings reading, riding on the ending claim, and keep reader confirmation.
- Hold until the four amending orders are attached and the report-deadline ruling lands. That ruling unblocks the 10 ending-blocked orders.
- A second probe on fresh instruments should show whether the 0.30 rate holds when the eligible-now rate is 0.20.
- Counterevidence should wait for the owner's ruling.
- Certified count stays 0.

**Git status**
- My paths are `jobs/lambertini/`, `research/excavator/lambertini-2026-10-20/` (now including `OUTCOME.json`), `research/readiness/claims/claude-lambertini-p1-2026-10-20.jsonl`, and the Llull ledger appends (`outcomes.jsonl`, `pools.json`, `censuses.jsonl`).
- The other changes belong to other workflows and I left them alone: `jobs/claim-kit/*`, `research/readiness/FETCH_QUEUE.jsonl`, `research/readiness/act_overrides/`, and `jobs/llull/ledger/pool_ids/CRAIG2.txt`.

SUMMARY: Lambertini probe: 6 of 20 upheld (0.30, above the 0.15 forecast), 0 rejected, 0 savings states overturned. Only 4 can close a step now. The S0 prefill matched 4 of 6. Outcomes O-20261020-10 to -12 are recorded and checkers pass; nothing is committed. The owner needs to rule on report deadlines and the pre-1937 search records. Scale only the instrument-level savings reading after a second probe.
