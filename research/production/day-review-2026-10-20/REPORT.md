### Day review (2026-10-20)

I ranked from Llull rank on a scratch copy of the ledger and Polya rerun at ab88f6d138. The committed Polya output is stale: it was built at 46f91fd, when 135 orders were ready. 176 are ready now. Nothing is committed and the certified count stays 0.

**Calibration**
- 44 forecasts registered today, 25 resolved, 23 scored. L-1 and L-2 are excluded as not preregistered; 19 are still open (L-3..12, Lambertini III L-32..35, Sinclair L-40..44).
- Intervals: 17 of 19 fell inside p10–p90 (0.89 against the 80% target). Both misses were above p90: MW-C2 (0.8 against p90 0.6) and Lambertini II (20 against p90 14). 12 of 19 measured values were above p50, so planners forecast too low.
- Events: Brier 0.36 on 4 events, worse than the 0.25 of always saying 50%. 3 of 4 gates passed against a mean forecast of 0.39.
- 6 of 8 planners forecast too low. Craigellachie II forecast 20× too high and Rastell 1.28× too high. Every planner is still "unproven" (under 5 resolved forecasts).
- Selfscore: 1 of 2 misses was flagged in advance; flag precision 0.17.
- New measurement: of 45 orders claimed today, 41 are now ready. That is the whole 135 → 176 rise.
  - Lambertini 25 of 26, Rastell 6 of 6, Bowditch Y2 3 of 3.
  - Lamm 7 of 10; the other 3 are blocked on Opus media.

**Base rates by method**

| Method | Rate | Population |
|---|---|---|
| Opus re-review with sources and D6, of accepted Y1 NO statuses | 15/15 (12/15 on the strict reading) | BOWY1NO |
| Random Y1 status sweep | 15/50 (0.30) | Y1 |
| ACT provision records | 57/69 (0.83); EO 12553 batches 108/120, not in ledger | RASTELL |
| Claims on claims-enabled EO 12553 targets | 6/10 (0.60), or 6/8 without the plants | R12553C |
| Shared ending-instrument reading (S0) | P1 6/20 (0.30), II 20/24 (0.83) | LAMBS, LAMBS2 |
| Own fixed-term ends | 23/40 (0.575); sunsets 19/54, not in ledger | LAMM |
| Random Y2 modern claims | 3/50 (0.06) | Y2 |
| Last-step claims after fetch (Craigellachie) | 0/23 and 0/5 | CRAIG, CRAIG2 |
| Plant catch: scratch planter / sealed MW-C2 with Opus and sources | 2/2 (20/20 overall, diffable) / 8/10 | R12553C, NR |
| S0 prefill agreement | 4/6, 12/20 | LAMBS, LAMBS2 |

**Cost per upheld claim, by line** (estimate: agent count × $2.82)

| Line | $ per upheld claim | $ per ready order |
|---|---|---|
| Lambertini II | 1.55 | 1.55 |
| Lambertini P1 | 1.90 | 2.26 |
| Lamm II | 3.10 per checked claim line | 4.43 |
| EO 12553 claims | 3.75 | 3.75 |
| Bowditch Y2 | 3.77 | 3.77 |
| Craigellachie I + II | about $34 for 0 upheld | — |

Rastell ACT records (about $0.25–0.50 each) and Y1 statuses (about $0.75 each) are not claims.

**Ranked next workflows** (unblocked first; $10 per ready order is a planning parameter I chose, not a measurement)

| # | Workflow | Census (pool / strict / leads) | Llull E_ready (cost) | Note |
|---|---|---|---|---|
| 1 | Source-ladder queue (no agents): about 89 PEB report-date lines for EO 12553 emergency boards, plus routes for the 20 report-date lines with no route | 89 + 36 targets | 0 directly ($0–3) | None of the 89 are queued yet. The NMB route found 14 of 14 lines today. |
| 2 | Near-ready fix-ups: Lambertini P1 claim-check fail 1, Lamm Opus media 3, quarantined 2, source audit 1 | NEAR 31/31/31; 23 are dead Craigellachie orders | unranked, at most about 7 (about $3–6) | |
| 3 | Lamm III: sunset remainder, about 45 not yet attempted | LAMMSUN 92/7/79 | 9.6, capped at strict 7 ($26, 0.37 per $) | Best ratio |
| 4 | Y2LEAD probe of 50, excluding EO 12553 targets | Y2LEAD 474/149/474; 116 of the 149 strict are EO 12553 targets | 3 per 50 ($11.5); run 21.5 ($82), overlap inflates it | Llull says EVPI is below the probe cost; the protocol still requires the probe |
| 5 | Lambertini III (preregistered) | LAMB3 82/3/82 | 4.2 ($106; probe $26) | Census undercounts this line: Lambertini II upheld 20 of 24 from a pool with strict 0. Planner p50 is 40 enabled. |
| 6 | Finish Sinclair (running) | SINCLAIRS 150/3/96 | 0 ($34) | Statuses are not adopted; it only informs the Y1 adoption ruling |
| 7 | EO 12553 emergency-board claims (89) | R12553ACT 122/118/118 | **51.6** ($200, 0.26 per $); about 64 at the 0.75 rate without plants | Blocked: report-deadline ruling, and PEB dates if the ruling is "the board ends on its report" |
| 8 | Report-relative claims once dates land (Lamm 26 + Lambertini 10) | 36 | unranked (no measured rate) | A ruling is still needed where the order gives only a deadline |

Dropped:
- Craigellachie III: E 0.05, and two probes have failed.
- Rastell EO 12553 ACT remainder: E 9.3 for $94, and its claims hit the same emergency-board block.
- Lamm retirement-exemption batches: need the transcription ruling.

**Owner decisions, ranked by orders unblocked** (Polya reach at the current commit)

| # | Decision | Orders reached | Ready orders soon | Gates |
|---|---|---|---|---|
| 1 | Y1 batch adoption | 11,613 | 0 directly | Sinclair, BOWY1NO 15 |
| 2 | ProQuest/NYU request | 6,839 | about 0 (X1S strict 2 of 693) | X1 text route |
| 3 | Transcription-as-copy | 3,216 | Lamm 20–23 ends; 276 retirement exemptions reached | Lamm batches 10–12 |
| 4 | Report deadline | 575 plus 89 emergency boards | **about 52 + up to 36, the most of any ruling** | Workflows 7 and 8 |
| 5 | Lamm extension / "until" | 6 | 6 or fewer | EO 8554, 8392, 8828, 8058, 7300, 6933 |

Files:
- Ranking input (scratch): /tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/llull_rank/actions.json
- Scratch pool ids for the emergency-board census: /home/user/Executive-Orders/research/production/day-review-2026-10-20/R12553ACT_ids.txt
- Current Polya outputs (scratch): /tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/polya_now/

SUMMARY: Forecasts ran low: intervals 17 of 19 inside, both misses high; events Brier 0.36. 41 of 45 claimed orders are now ready (135 → 176), so claims convert. Cheapest per upheld claim is Lambertini II at $1.55. Next: queue 89 PEB date lines, near-ready fix-ups, Lamm III sunsets (0.37 ready per $), a Y2LEAD probe without EO 12553 targets, Lambertini III, and finishing Sinclair. Then the 89 emergency-board claims (about 52 ready orders) and 36 report-relative orders. The report-deadline ruling unblocks the most ready orders soon; Y1 batch adoption reaches the most orders (11,613) but makes none ready directly. Certified stays 0.
