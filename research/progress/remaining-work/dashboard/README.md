# Remaining-work dashboard: page source

`index.html` is the page of the dashboard artifact https://claude.ai/artifact/531KGTebdrgdeUitKhp8du
(Dashboard type; it reads its data from datasets in the artifact's database). Saved here so changes can be
reviewed. **This is the project's only dashboard** (owner, 2026-11-08): every view, Tsiolkovsky's trajectory included, is a tab here; the standalone Tsiolkovsky page (https://claude.ai/artifact/BZJxATqRtwrtBbuBy2UZpc) is retired and is not refreshed. Tabs and hashes: Steps left `#steps`, AI effort `#effort`, Tool map `#toolmap`, Mission `#apollo`,
Workflow `#workflow`, Job tiers `#tiers`, Trajectory `#trajectory`.

| Dataset | File |
|---|---|
| open_work | REMAINING_WORK_LONG.csv |
| by_president | REMAINING_WORK_BY_PRESIDENT.csv |
| effort_work | EFFORT_LONG.csv |
| effort_tiers | EFFORT_BY_TIER.csv |
| workload | TOOLMAP_WORKLOAD.csv |
| tools | TOOLS.csv |
| mission_log | MISSION_LOG.csv |
| workflow_nodes | workflow/WORKFLOW_NODES.csv |
| traj_readings | jobs/tsiolkovsky-trajectory/output/GENERATION_POINTS.csv |
| traj_daily | jobs/tsiolkovsky-trajectory/output/TRAJECTORY.csv |
| traj_campaigns | jobs/tsiolkovsky-trajectory/output/CAMPAIGNS.csv |
| traj_events | jobs/tsiolkovsky-trajectory/output/EVENTS.csv |

The Workflow tab added on 2026-10-31 changed only the page (styles, one tab button, one section, one script
block) and added the `workflow_nodes` dataset; the seven existing datasets were left as Codex published them.


## November 2 refresh

Job tiers (`#tiers`) adds 85 dated editorial assessments, with search, kind/tier filters and source-backed details. `../tiers/JOB_TIERS.json` is embedded by `../tiers/build_job_tiers.py`. The Workflow feed now has 82 nodes including Apollo, Erasmus and Geddes. Replace only `tools` with `snapshots/2026-11-02/TOOLS.csv` and `workflow_nodes` with `workflow/WORKFLOW_NODES.csv`, then publish this page into the same private artifact. The six other feeds and the mission clock remain unchanged: current main confirms the identical readiness CSV blob, so later filings are not added to readiness. The visible main-check strip names its source commit and tracker date.

## November 7 refresh (Encyclopedie campaign)

- Rebuilt on main `178203a83a` with this folder's builders: `open_work`, `by_president` (`build_remaining_work.py`:
  78,828 open steps, 20,677 done), `effort_work`, `effort_tiers` (`build_effort.py`), `workload` (`build_toolmap.py`:
  14,998 tracker rows, 1,185 ready). `mission_log` is the official `jobs/daily-digest/output/MISSION_LOG.csv` (frozen
  weights), not a local rebuild.
- New Trajectory tab (`#trajectory`): Tsiolkovsky's readings, daily series, campaign credit and landings, drawn in this
  page's own style (the standalone Tsiolkovsky dashboard, https://claude.ai/artifact/BZJxATqRtwrtBbuBy2UZpc, uses the
  one-writer page form, which this page cannot host). Data from `tsiolkovsky-trajectory` rebuilt locally on the same
  commit: 42 readings, newest 2026-11-06 22:18 UTC, 6,630.8 of 18,191 work-hours (36.5%).
- `tools` is `snapshots/2026-11-07/TOOLS.csv` (79 tools: the 46 of 2026-11-02 unchanged plus 33 added Nov 3-7); `workflow_nodes`
  is `workflow/WORKFLOW_NODES.csv` (115 nodes, 33 added); `tiers/JOB_TIERS.json` has 118 assessments (33 added, dated
  2026-11-07), embedded by `tiers/build_job_tiers.py`. Published as files/index.html version 17. Numbers the worker could
  not source are written "not yet measured"; inferred namesakes are marked "inferred".

## November 8 refresh (7:40 PM EST; consolidation)

- Owner asked for one dashboard with Tsiolkovsky as a tab, refreshed to 2026-11-08 7:40 PM EST (00:40 UTC Nov 9). Main at that time: `17c7f2f91` (00:28 UTC). The page (version 17, identical to `index.html` here) already had the Trajectory tab, so only data changed.
- Rebuilt on `17c7f2f91` with this folder's builders: `open_work` and `by_president` (76,212 open steps, 23,598 done), `effort_work` and `effort_tiers`, `workload` (14,998 tracker rows, **1,091 ready**, after the Cujas wave's 68 claims).
- `traj_*`: Tsiolkovsky rebuilt locally on the same commit (its committed output was from 08:10 UTC). That gives 71 readings over 23 days, newest 2026-11-08 23:19 UTC: 6,812.1 of 18,191 work-hours (37.4%), ready 1,091.
- Files are in `../snapshots/2026-11-08/` (`TRAJ_*` are the Tsiolkovsky files).
- **`mission_log` is unchanged:** the official `jobs/daily-digest/output/MISSION_LOG.csv` at `17c7f2f91` still ends 2026-11-06. A local `build_mission_log.py` rebuild does not reproduce the official rows (different step totals), so it was not used. The daily digest should advance it.
- **`tools` and `workflow_nodes` are unchanged** (editorial feeds, last set 2026-11-07).
- **Open PRs at refresh:** #236, #235 (Sol, Montfaucon page checks) and #185 (held). All are drafts, and none is merged, so none is counted.
