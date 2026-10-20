# Llull: first use (2026-10-20)

**Recurring failure modes.** Across the 12 plans that fell short, plans delivered a median of 0.036 of what they forecast (about 1/28). The causes, with how many of the 12 misses each explains:

| Failure mode | Misses |
|---|---|
| Unmeasured prerequisite | 8 (9 with Craigellachie) |
| Selection bias | 5 |
| Cost shift | 3 |
| Invented rate | 2 |
| Proxy unit | 2 |
| Access assumption | 2 |
| Assumed independence | 1 |
| Counting an unapproved policy | 1 |

Today's run confirms the pattern. The block is missing source documents (ending instruments, report dates, statutes, regulations), not agent effort. Nobody had measured how often an accepted status or an upheld claim becomes a ready order.
- I measured that conversion now at no agent cost: the 3 upheld Bowditch claims all became ready (3 of 3, 135 → 138 in the tracker at commit 0430303d7).
- An accepted status alone gives 0 ready orders, because the tracker requires every step to be done.

**Backtest.**
- On past plans (in-sample, since the rules were written after the postmortems): 5 of the 12 misses caught, 7 missed, 1 false alarm.
- Its widened forecast ranges held the result 8 of 17 times, against 80% intended.
- `premortem` gives every plan the same warnings, so it cannot tell plans apart.
- **First out-of-sample case (counterfactual, n = 1): Craigellachie.** Its forecast was 0.015 / 0.15 / 0.35 upheld per attempt and was registered with no census cap, because no Llull pool covered its 23 orders. Llull's gate code (rev 2) and data were frozen at the registration commit. Run on those 23 orders, the gate gives 1 of 23 (4.3%), counting leads or not. That would have flagged the forecast as above the ceiling even with leads. Measured: 0 of 23.
- The forecast ledger now holds 2 resolved forecasts (craigellachie-scout): Brier 0.30, 0 of 1 range held the result, forecasts were about 30x too high.
- Limit: the gate is not a true ceiling. Bowditch's 3 upheld orders all fell outside it.

**Ranked next actions.** Rank uses 1.534 agent-minutes per attempt (30.6 producer + 46.1 reviewer minutes over 50 Bowditch attempts) and a limit of 60 agent-minutes per ready order. That 60 is the example file's planning number, not one the owner has set.

| # | Action | Census ceiling | Rank result | Forecasts | Cost | Owner? |
|---|---|---|---|---|---|---|
| 1 | **A: drain the 159 ending/current-basis fetch requests through source-ladder in bulk** (no agents) | Y2 NO orders: 38 of 1,680 strict, 1,220 with leads | Runs first | L-5: share found 0.02 / 0.20 / 0.45. L-6: P = 0.12 that the Y2 strict count rises by 20 or more | 0 agent-minutes, Actions time only | No |
| 2 | **B: Y2 claims on 500 orders drawn from the 995 lead-selected NO orders**, in batches of 50; stop if upheld is below 2.6% after 150 | Y2 strict 38 (1.8%), leads 363 (17.6%); measured 6% | 30 expected ready; probe not worth it. Break-even rate 0.026; P(below it) = 0.13 (3/50), 0.28 adding Craigellachie's 0/23 | L-3: upheld 0.004 / 0.045 / 0.11. L-4: ready 1 / 18 / 40 (Llull's history-based fallback says 0.65) | 767 agent-minutes, about $100 (estimate) | Only to set the limit |
| 3 | W1: EO 9789 (source-audit hold) and EO 14139 (unresolved gaps), with every step done | 2 | Unranked: no cost or base rate | L-10: P = 0.25 | Small | Yes, the 9789 audit |
| 4 | D: repair the 87 orders that have a claim but are not ready, after fetches arrive (own-terms ends, provisions) | 1 strict, 78 with leads; 0 of 23 measured | Unranked: Craigellachie's 0/23 is not a base rate yet | L-9: P = 0.15 that 3 or more become ready | About 1.1 minutes per attempt | No (depends on A) |
| 5 | C: Y1 status sweep of 1,000 | 3,952 hold their prerequisites, but only 111 would hold an ending instrument if NO | 0 expected ready | L-7: P = 0.03 that it adds 1 or more ready. L-8: P = 0.35 that the owner adopts 15 or more statuses | 450 agent-minutes | **Yes**, adoption |
| 6 | E/F/G: pre-1937 routes | E ProQuest (661 with status, no text): 1 strict / 294 leads after text arrives. F type-rule statuses (608 with text, no status): 0 / 280. G PLO: 18 with status, 1 with status and text | Unranked | L-11: P = 0.08 that any adds a ready order | Unmeasured | **Yes**: NYU written approval (E), status adoption (F) |
| 7 | H/I: CSC dating, census gap admission | 0 ready (no readiness step closes; admitted orders arrive with 6 open steps) | 0 expected ready | L-12: P = 0.01 | Unmeasured | No; worth doing for correctness, not for this count |

The premortem wheel added three candidates:
- W1 above.
- Drawing B from orders with ending leads. This is a post-hoc split, so treat it with care: 3 of 19 upheld with leads against 0 of 31 without in Bowditch, and 3 of 34 against 0 of 39 with Craigellachie added.
- An independent review of the Y1 statuses before adoption, because their reviewer was the same model family.

The wheel never asks whether "ready for review" is the binding constraint. 138 orders are ready and 0 are certified, so the owner may want to weigh human review.

**Defects found while using Llull** (not fixed; `llull.py` unchanged):
1. **`rank` undercounts expected ready orders about 55x.** It multiplies the measured rate by the strict census share. That rate was measured on random draws, and none of the 3 upheld orders passed the gate. I worked around it by giving each action a share of 1.0.
2. **Llull's own outcomes cannot become base rates.** A base-rate row needs an id from the old postmortems file, so `rank` ignores the 0 of 23.
3. **Censuses on custom pools cannot be recorded.** The test requires exactly Y1, Y2 and X1, so the near-ready and pre-1937 sub-pool censuses exist only in the scratch files.
4. **`check` and 1 of the 26 tests now fail, from an earlier commit and not my entries.** The Craigellachie forecast and its run were committed together (439e274ab), so git cannot prove the forecast came first.
5. **My forecasts L-3 to L-12 are not committed.** They must be committed before any run starts.

Files:
- `/home/user/Executive-Orders/jobs/llull/ledger/forecasts.jsonl`
- `/home/user/Executive-Orders/jobs/llull/output/RANK.json`
- `/home/user/Executive-Orders/jobs/llull/output/CALIBRATION.json`
- `/tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/llull/use/` (`censuses.py`, `censuses.json`, `actions.json`, `plan_next_actions.json`)

SUMMARY: Plans keep missing because they assume inputs nobody measured; on median they deliver 0.036 of the forecast. Llull caught Craigellachie counterfactually: its gate caps that pool at 1 of 23, against a forecast of 15% to 35%, and the result was 0. That is its first out-of-sample catch, n = 1. A measured fact now in hand: 3 of 3 upheld claims became ready orders. Rank: first drain the 159 ending fetch requests through source-ladder, at no agent cost. Then run Y2 claims on 500 lead-selected orders, in batches with a stop rule: about 18 ready orders (1 to 40), 767 agent-minutes. Y1, ProQuest and type-rule statuses need the owner; CSC dating and gap admission add 0. Five Llull defects are listed, including a 55x undercount in rank. My 10 forecasts are not committed yet.
