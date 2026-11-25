# Bartolus wave, 2026-11-24 (first part, agent route)

Named for Bartolus de Saxoferrato, the fourteenth-century jurist whose commentaries and opinions became the working
law of Europe. Plan: `research/bartolus/WAVE.json`, signed by the owner (Augur PASS, sha256 d3ee295b...;
D-20261124-bartolus). The owner then paused new batches until a stateless-call gauge decides the route
(instruction of 2026-11-24 20:14 ET); every batch already produced was finished on the agent route.

**Result: 42 lifecycle claims filed canonically and 4 undecided-route statuses adopted and filed (46 in all).** No
census or codebook change. Decided orders 3,788 -> 3,792. Human-certified stays 0.

| Batch | Pool (Bentham action) | Attempted | Submitted | Filed | Controls (caught by both arms) |
|---|---|---:|---:|---:|---|
| r01 | recovery.custody_stranded | 5 | 3 | 1 | EO 8613 |
| r02 | recovery.custody_stranded | 1 | 0 | 0 | none |
| s01 | recovery.working_text_stale | 26 | 26 | 24 | EO 7996, 8002 |
| y01 | production.claim_ready.yes.fr | 25 | 9 | 6 | EO 12318 |
| y02 | production.claim_ready.yes.fr | 8 | 7 | 4 | EO 12580 |
| y03 | production.claim_ready.yes.fr | 8 (7 assigned) | 6 | 4 | EO 11295 |
| y04 | production.claim_ready.yes.fr | 9 | 6 | 3 | EO 11701 |
| u01 | status_assignment.undecided (Lind stage-0 draw) | 30 (21 dispatchable) | 5 | 4 adopted | EO 9155 |

Controls: 8 planted, 8 caught by both arms. Rejections by either arm demoted 15 submitted claims (both-uphold rule).

## Lind stage-0 reading (research/lind/DECISION_2026-11-12.md section 7.3)

Ready among the all-gates group a = 3 (EO 9155, 11943, 12701); among the hard-only group h = 1 (EO 12437). All four
are NO statuses of small amending or revoking orders. Dollar cost per ready is estimated, not measured (below), and
falls well under the 9.30 USD threshold on any reasonable reading, so the result reads as "success, soft gates hold
for now" (stage 1 would keep 1 in 5 orders from the hard-only pool). Continuation waits for the owner's stateless
gauge.

## What the YES re-run showed

All 200 all-gates YES orders had been worked by Papinian on 2026-11-10, blocked mostly by missing NEA continuation
notices and an official EO 13286; both are now held (theophilus-sources, fr-originals). In the 50 re-run, producers
submitted 28 and 17 filed (34%), against Papinian's 16%. Producers repeatedly stopped early with "clause
reconciliation not done"; a resumed pass on the same producer converted most of those to submissions.

## Defects and lessons

- **A new owner-ruling file invalidates every open packet** (`changed prior research`: prior research includes
  `current_rulings`). Write ruling files only after every open packet has completed, or hold them outside the tree.
- **Completion is stricter than batch-check**: a claim with any `unverified` checker entry (typically a quote that
  includes a neighbouring order's number from a whole-page original) fails completion. EO 8613 and EO 8639 (r01) failed
  this way; refiling needs a fresh prepare.
- **Planted-control date shifts are caught reliably**, but most real rejections are date or citation slips the
  producer could have caught with a self-check of every structured date against the signing date.
- Subagent transcripts are not exposed in this environment, so per-call usage could not be priced.

## Cost

Measured: tokens at hand-back and tool calls per worker (`WORKERS.csv`). Estimated workers' list price about 66 USD
(each call re-reads about half the final context at cache-read price, the final context written once, about 800
output tokens per call): producers about 22, arms about 39, status reviewer about 2, the stateless-mode engineer about
3. Coordinator not measured. This is an estimate, not a measurement, so it is not added to Bentham's measured rates.

## Stateless gauge (built, not run)

`jobs/maudslay-conveyor/stateless.py`, `gauge_stateless.py` (`--dry-run` forecast 24.24 USD for 232 requests),
`research/stateless-calls-2026-11-24/README.md`. The owner runs it on his PC once `claude -p` is installed and logged
in. The gauge's agent-arm baseline should be checked: the recorded Papinian arms disagreed on 16 of 83, not 7 of 85.
