# Junto's first run: finders scored, savers to test (2026-10-20)

Named for Benjamin Franklin's Junto (1727), the club that kept only the ideas that worked in practice.
Code and rules: `jobs/junto/README.md`. Design: `research/plans/JUNTO_DESIGN.md`. Outputs here:
`scoreboard.json`, `candidates.json` (aggregate evidence only), `allocation.json`.
Ledger: `jobs/junto/ledger/` (`junto.py check`: ledger ok).

**Headline: every finder scores 0. No saving has been verified yet.** Every dollar figure below other
than measured session costs is an unverified estimate and counts for nothing until a before-and-after
test measures it.

## What Junto does

| Level | What | Examples |
|---|---|---|
| Saver | A change that cuts tokens | Revere (phase handoff to a fresh session), Watchman (monitoring outside the big session), Spare setup, Quiet protocol |
| Finder | A script that reads audit data and proposes savers ("candidates", always `unverified`) | `F-hamilton`, `F-friction` (Clausewitz), `F-wasted_work` (Gallatin) |
| Junto | Runs finders, scores them, splits the next budget, proposes new finders | `jobs/junto/junto.py` |

- **Score** = verified USD saved / (USD spent running the finder + $2 prior). Only lines in
  `verified_savings.jsonl` tied to a measured test count. Estimates never do.
- **Verified** means `add-test` received measured `get_session` costs for a before arm and an after
  arm. The after arm must be at least 10% cheaper per unit of work, with a reject rate no worse. An
  after-arm session can back only one test.
- **Allocation:** 80% of each round's budget goes to finders by score and 20% to exploration. With no
  positive score, the whole budget goes to exploration.
- **Propose:** waste measured in a test that no finder targeted becomes a new finder proposal.

Why the hard rule exists: an earlier plan claimed 4,134 hours that measured at 463.

## Data coverage

Raw pages and `get_session` totals stay in the scratchpad, outside the repo. Only aggregates are committed.

| Session | Label | Pages | Events read | Billed cost | Complete | Cache-read coverage |
|---|---|---:|---:|---:|---|---:|
| `session_01JjQVjYb1QFf8uogYLQK2S8` | X1 build and pilot | 26 | 2,514 | $53.94 | yes | 100% |
| `session_018rjJnzg7QqYRKGzsDQySDT` | remaining-work treemap | 18 | 1,697 | $28.00 | yes | 94% |
| `session_015vd3urDCdnou5mGUvtvFWf` | PR 31/33 merge | 7 | 640 | $4.97 | yes | 100% |
| `session_01LUoGyyTUtLBnjhVa9VgHXP` | ProQuest survey | 3 | 255 | $1.93 | yes | 100% |
| `session_017gGLB1QjDADWtJrgtW2aD7` | Stage 9/11 research and upload | 51 | 5,080 | $815.90 | **no** | **9%** |

All three finders read 10,186 events. The page files hold 10,264 lines; the finders did not parse 78
of them as events.

**Blocked-copy gap.** For `session_017gGLB1QjDADWtJrgtW2aD7`, the auto-mode classifier denied copying
page 52 as a possible sensitive-source export. It was not worked around. Pages 1-51 (5,100 events,
newest first) were saved. Older events are missing, and the session's total event count is unknown.
The saved window covers about 9% of the billed cache reads, so the finders priced the session at
$73.12 of its $815.90. Hamilton's per-session means exclude it. The friction and wasted-work upper
bounds count only the saved part.

Other gaps:
- The treemap session's cache-read coverage is 94%, but all three finders price it at its full cost.
  That inflates its per-cause dollars by about 6%. Only estimates are affected.
- Two account sessions (`session_01DfyRpay7hxj5h3w8gzhgcC`, `session_013LuYBD9GEt5QNDtmNZmU1R`)
  report no cost (local/bridge) and were not read.
- Item sizes are estimated as characters / 4, and transcripts understate output tokens.
- This Junto build session is not in the sample.

## First scoreboard

| Finder | Run cost | Candidates | Est. USD/session (unverified) | Verified USD | Score |
|---|---:|---:|---:|---:|---:|
| F-hamilton | $0.00 | 6 | 14.47 | **0** | **0** |
| F-friction | $0.00 | 4 | 1.09 | **0** | **0** |
| F-wasted_work | $0.00 | 3 | 2.31 | **0** | **0** |

All finders score 0 because no before-and-after test has run. Run cost is $0.00 because the finders
are pure scripts (`local_script`). The estimates overlap, so they must not be summed.
**Allocation, round 1:** $10, all to exploration, $3.33 per finder. **Propose:** no test has waste
data, so there are no new proposals.

## Savers to test next (ranked)

Ranking rule: candidates priced from billed tokens (Hamilton) come first. Within each group, they are
ranked by estimated USD per session divided by marginal test cost (spend that would not happen anyway).

Test costs are unverified estimates built from measured session costs. The price is about $3.01 per
million input-price units ($53.94 / 17.92 M units in X1). Cache writes cost 1.25x (5-minute) or 2x
(1-hour). A fresh session's roughly 70k tokens of setup costs about $0.26.

The pass rule for all tests (computed by `add-test`): after-arm USD per unit ≤ 0.9 x before-arm USD
per unit, and the reject rate is no worse. A gain under 10% is inconclusive, and a second
inconclusive result refutes the saver. Record accepted and rejected counts; without them the ledger
flags `quality_measured: false`. Each test needs its own after-arm session(s).

| # | Saver (candidate) | Est. USD/session | Measure | Baseline | Sample | Test cost: gross / marginal |
|---|---|---:|---|---|---|---:|
| 1 | **Watchman** `watchman_outside_monitoring` (C-3) | 2.04 | `get_session` cost per PR babysat to merge; a scripted watcher wakes the main session only on change | PR 31/33, $4.97 per merged PR (n=1) | 2 PR babysits | $8 / $1 |
| 2 | **Revere** `revere_phase_handoff` (C-1) | 6.07 | cost per completed phase summed over handoff sessions; checker pass and reject counts | X1 $53.94 / its completed phases (fix the phase count from X1 handoff notes first) | 1 Y1 phase, 200k cap, 20k handoff | $20 / $3 |
| 3 | **Idle cache avoidance** `idle_cache_avoidance` (C-2) | 2.45 | cache-write tokens and cost of the first call after a >5-minute idle, resumed fresh from a handoff | X1's 1-hour rebuild: 629k tokens, about $3.8 | 3 natural idles | $2 / $2 |
| 4 | Quiet protocol: tool output `tool_output_cap` (C-4) | 1.61 | USD per accepted claim; tool-output share in a re-audit | X1 helper batch (about $1.4 per agent) | 5-agent batch, ≤20-line prints | $7 / $0.50 |
| 5 | Quiet protocol: narration `narration_cap` (C-5) | 1.40 | USD per accepted claim; narration share | X1 helper batch | separate 5-agent batch | $7 / $0.50 |
| 6 | Spare setup `spare_setup_trim` (C-6) | 0.90 | first-call context tokens of an empty session; one fixed short task succeeds | 69-73k tokens | 3 configs x 2 sessions | $2 / $2 |
| 7 | Early triage gate (C-11, low confidence) | 0.95 | rows blocked after full work; USD per accepted unit | batch with $4.75 blocked | 1 batch | $5 / $1 |
| 8 | Intent echo first (C-12, low confidence) | 0.73 | user corrections; USD per accepted unit | 2 sessions | 5 prompts | $2 / $0.50 |
| 9 | Producer pre-check (C-13, low confidence) | 0.63 | rejected share; USD per accepted unit | 2 sessions, 28 hand-backs | 1 batch | $5 / $1 |
| 10 | Pre-flight checks (C-7) | 0.62 | failed calls; USD per unit | 58 failures in 5 sessions | 2 jobs | $2 / $0.50 |
| 11 | Quiet protocol, oversize (C-8) | 0.34 | oversize errors | 1 session, 72 events | fold into #4 under one `saver_key` | $0 with #4 |
| 12 | Letter of Marque `permission_preapproval` (C-9) | 0.07 | denials; USD per accepted unit | 9 denials | 2 runs | $1 / $1 |
| 13 | Mason-Dixon branch rule `conflict_guard` (C-10) | 0.06 | conflicts; USD per merged PR | 5 conflicts | 2 parallel runs | $10 / $4 |

Notes on the top three:
- **Watchman** has only one baseline session, so add a third babysit before treating it as settled.
- **Revere** exceeds the $10 round on gross cost. It is affordable only because the Y1 phase is
  planned work, and its baseline unit must be defined first.
- **Idle cache avoidance** waits for natural idles. Price each rebuild at its own cache rate.

## Finder catalog (not built; `jobs/junto/catalog/`, all costs unverified estimates)

| Name | Kind | What | Build / run (est.) | First test |
|---|---|---|---:|---|
| Tocqueville Comparison | finder | compare sessions of one task class | $1.50 / $0.05 | X1 vs Y1 coordinator per accepted unit |
| Washington Farewell | finder | one exit question per agent | $1.00 / $0.01 | next 20 agent briefs |
| Thornton Patent Scan | finder | scan public platform docs for unused cost features | $2.00 / $1.50 | a caching/compaction feature on one PR babysit |
| Mason-Dixon Resurvey | finder | replay a finished task more cheaply | $4.00 / $12.00 | replay the ~$5 PR-merge task |
| Wolcott Pre-flight | saver | price a task before launch; stop at 1.5x | $2.50 / $0.10 | price the next Y1 phase, compare with measured cost |

## What could not be verified

- **Any saving:** verified USD is 0 everywhere and every finder scores 0.
- **Every estimate:** they are simulated or assumed cuts, or upper bounds that assume the saver
  removes all attributed cost. They overlap, and the wasted-work signals are heuristic and low
  confidence.
- **The $816 session,** about 91% unread (blocked-copy gap). Its causes may differ from the four
  small sessions.
- **Treemap pricing,** about 6% too high.
- **Test costs:** estimates only. The real cost comes from `get_session` and is logged with
  `add-test --test-cost-usd`.
- **Dollar meaning:** `cost_usd` is list-price value, not necessarily what was paid.
- **Quality:** a test without accepted and rejected counts can still pass. It is flagged
  `quality_measured: false` and should not be trusted.
