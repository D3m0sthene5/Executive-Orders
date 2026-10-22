# Historical remaining-work and tool-map snapshot

The `TOOLMAP_WORKLOAD.csv`, `REMAINING_WORK*`, and `EFFORT*` files were
regenerated on 2026-10-22 from main at `582a64a0652b5ba4545805546d5d3d815273909e`
(the tracker output there, committed in `a6a005c41f`, still counts 3,359
provisional statuses; the 15 statuses adopted in PR #51 are not in it until the
GitHub run after that merge publishes its results). The counts came out identical
to the PR #48 snapshot at `78d1b67cb5157fb70be912b167f266718d10d483`. A local
preview run of the tracker with the 3,374 statuses gives 76,875 open steps
(prerequisite 50,319, agent claim 17,509) and the same 278 ready; that preview is
not committed. These files are not a measurement of the results of PR #50. The PR description originally named
`09310ada` as its source baseline; these files do not themselves pin every
input file's version. Restoring generated job outputs to main during PR cleanup
does not refresh these planning snapshots or establish that they describe the
restored outputs.

At this snapshot, 278 of 14,972 tracked orders were ready for human review.
`TOOLMAP_WORKLOAD.csv` partitions 76,905 open steps for those existing orders.
`REMAINING_WORK*` also includes 9,198 estimated steps for 1,314 APP-counted
orders not yet in the project (seven steps each), giving 86,103 total steps.
`EFFORT*` estimates roughly 15,698 agent-hours under its effort model; this is
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
