# Historical remaining-work and tool-map snapshot

The `TOOLMAP_WORKLOAD.csv`, `REMAINING_WORK*`, and `EFFORT*` files were
regenerated on 2026-10-22 from main at `20d4f4d4b6c4284fecd46e6671411a05388d9d9a`
(PR #48, the narrowed PR #51 and PR #50 merged). The tracker output committed
there is PR #50's bot snapshot: 280 ready on 3,359 provisional statuses. The 15
statuses adopted in PR #51 (3,374 in the decided file) are not counted until the
GitHub run after the merge publishes its results. Against the PR #48 snapshot at
`78d1b67cb5157fb70be912b167f266718d10d483` (278 ready, 76,905 open steps on held
orders, 15,698 model agent-hours) this snapshot has 280 ready, 76,876 open steps
on held orders, 86,074 in all, and 15,439 model agent-hours; the no-route lane
fell from 803 to 100 because PR #50's ProQuest replica records give those old
orders a text lead. The PR description originally named
`09310ada` as its source baseline; these files do not themselves pin every
input file's version. Restoring generated job outputs to main during PR cleanup
does not refresh these planning snapshots or establish that they describe the
restored outputs.

At this snapshot, 280 of 14,972 tracked orders were ready for human review.
`TOOLMAP_WORKLOAD.csv` partitions 76,876 open steps for those existing orders.
`REMAINING_WORK*` also includes 9,198 estimated steps for 1,314 APP-counted
orders not yet in the project (seven steps each), giving 86,074 total steps.
`EFFORT*` estimates roughly 15,439 agent-hours under its effort model; this is
a planning estimate, not measured runtime, token use, or verified savings.

`TOOLS.csv` is a hand-maintained inventory, updated 2026-10-22 from the merge
audit (`research/diagnostics/pr-merge-20261022/`), the Sinclair lean review, the
Justinian run report on branch `claude/justinian-1` and the PR #50 description.
Rows that describe branch work say so; the CSC row's `unwired` label and the
Junto candidate count are as recorded in those sources, not re-measured. Use the dated owner-ruling records
for the owner's decisions and freshly generated, version-pinned job outputs
for current counts and readiness.

Workload lanes are planning classifications inferred from tracker blockers and
held job outputs. A `machine_queued` label is not evidence of a successful
fetch, a reviewed legal claim, or a completed readiness step. Regenerating this
map does not implement owner rulings, change tracker gates, or review claims.
