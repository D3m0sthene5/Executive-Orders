# Remaining-work dashboard: page source

`index.html` is the page of the dashboard artifact https://claude.ai/artifact/531KGTebdrgdeUitKhp8du
(Dashboard type; it reads its data from datasets in the artifact's database). Saved here so changes can be
reviewed. Tabs and hashes: Steps left `#steps`, AI effort `#effort`, Tool map `#toolmap`, Mission `#apollo`,
Workflow `#workflow`.

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

The Workflow tab added on 2026-10-31 changed only the page (styles, one tab button, one section, one script
block) and added the `workflow_nodes` dataset; the seven existing datasets were left as Codex published them.
