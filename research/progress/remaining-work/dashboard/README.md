# Remaining-work dashboard: page source

`index.html` is the page of the dashboard artifact https://claude.ai/artifact/531KGTebdrgdeUitKhp8du
(Dashboard type; it reads its data from datasets in the artifact's database). Saved here so changes can be
reviewed. Tabs and hashes: Steps left `#steps`, AI effort `#effort`, Tool map `#toolmap`, Mission `#apollo`,
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
- `tools` and `workflow_nodes`: see `snapshots/2026-11-07/` once added.
