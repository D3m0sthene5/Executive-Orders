### Evening re-rank (2026-10-20)

This repeats the morning method (Llull census and rank, $10 per ready order as a planning parameter, cost = agents × $2.82) on the current state. It ran on a scratch copy of the ledger, so the repo ledger is unchanged. Nothing is committed. Certified stays 0, and no owner decision is assumed.

**What changed since the morning**
- Tracker at 66de5dae: 182 ready, up from 176. It has not yet counted Lambertini III (52 upheld, 49 pass the checker) or the 7 Y2LEAD claims.
- New measured rates, added to the scratch ledger only:
  - Lambertini III: 0.634 (O-35).
  - Y2LEAD probe: 0.14 (O-39). Its gate failed and the line is stopped.
  - Lamm III sunsets: 0.15 (O-31). The line is exhausted.
- PEB report dates: 32 usable dates landed. The scout found 0 orders that become ready without the report-deadline ruling and 47 that depend on it. 43 Lamm III queue lines (370-412) have not been worked, and 7 are retry_later.
- Running now, not ranked: Lambertini III coda (LAMB3C, 12 orders) and Sinclair mend (SINCM, 9 orders, statuses only).
- New pool screen (zero-agent `lambertini build` at HEAD):
  - LAMB4X: 65 unclaimed, never-attempted decided-NO orders, each with a single held acting EO other than EO 12553 and with original text done.
  - 16 of them have a located whole-scope ACT record (LAMB4W).
  - 30 are EO 9830 targets with no ACT record (R9830).
  - 17 have partial-scope records only.
- Checked and dropped: the Claude codification claims that are not ready (47 orders) have only 1 order meeting the strict ending gate. They have the same shape as Craigellachie (0 of 28), so the line is not proposed.

**Llull rank** (scratch output `RANK.json`)

| Line | Cost | E_ready | Ready per $ | Note |
|---|---|---|---|---|
| Push, then the tracker counts Lambertini III and Y2LEAD | $0 | about 45-51 (claims already exist) | — | zero-agent; runs first |
| Source-ladder run for the Lamm III tail | $0 | 0 now | — | zero-agent; every order it serves needs the ruling |
| Lambertini IV whole-scope (LAMB4W, 16) | $23 | 9.2 | 0.41 | best unblocked line |
| EO 9830: Rastell ACT records, then claims (R9830, 30) | $40 | 13 | 0.33 | optimistic: only 2 of 40 non-12553 Rastell orders enabled claims |
| EO 12553 emergency boards (89) | $200 | 47 | 0.24 | **ruling-dependent** |
| Y2LEADX remainder (281) | $169 | 36 | 0.21 | stopped: the quality gate failed (3 of 10 genuine rejected) |
| Lamm III report-relative sunsets (25) | $25 | 3.5 | 0.14 | **ruling-dependent** |
| Rastell non-12553 remainder (about 300) | $120 | 7.9 | 0.07 | poor |
| Lambertini III remnants (EO 10324, 10467, 12977) | about $5 | 3 or fewer | — | unranked: no base rate |

**Top 5 to launch**
1. **Push and Actions (zero-agent).** Push once while no run is in progress. Then read the tracker and source-ladder STATUS. Expect about 45-51 newly ready orders from claims already filed, and dates for the 43 remaining PEB lines. $0.
2. **Lambertini IV.** Run 16 LAMB4W orders as 2 batches of 8. Batch 1 is the probe, with a gate enforced in code: at least 5 of 8 upheld and at most 1 savings state overturned. Use a planter step and an Opus reviewer with sources and a D6 step. E 9.2 ready, $23.
3. **EO 9830 probe, Rastell then Lambertini.** Make 10 EO 9830 ACT records under the D6 earlier-end test, then claims on those that enable claims. Scale to 30 only if at least 4 of 10 orders enable claims. E 13 ready (likely lower), $40; the probe costs about $14.
4. **Lambertini III remnants.**
   - Add a FETCH_QUEUE line for the EO 10480 FR text, or an act_overrides record, for EO 10324 and 10467.
   - Request the later-event sources for EO 12977.
   - Re-check the 3 claims.
   - Record EO 10169 and 10390 as blocked.
   - Result: up to 3 ready orders for about $5.
5. **Emergency-board packets, prepared but not decided (zero-agent).** Pre-stage the 89 EO 12553 board packets with the 32 held report dates and the EO 10286 page check, so the line can run the day the owner rules. It produces 0 ready orders now and E 47 ($200) after the ruling. I did not decide the ruling.

Not proposed: Craigellachie, Y2LEAD/Y2LEADX, Lamm sunsets (none of their inputs changed), and the codification claim repair.

Files: the pool ids are `LAMB4X_ids.txt`, `LAMB4W_ids.txt` and `R9830_ids.txt` in this folder. The scratch rank is at `/tmp/claude-0/-home-user-Executive-Orders/357394c8-997b-5c91-82db-c4517632e70c/scratchpad/rerank/` (`actions.json`, `llull/output/RANK.json`, `llull/ledger/`).
