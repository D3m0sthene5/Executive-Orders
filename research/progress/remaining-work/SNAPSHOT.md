# Historical remaining-work and tool-map snapshot

The `TOOLS.csv`, `TOOLMAP_WORKLOAD.csv`, `REMAINING_WORK*`, and `EFFORT*` files
preserve the planning snapshot authored in PR #48 at commit
`78d1b67cb5157fb70be912b167f266718d10d483`. They are not a current inventory or
a measurement of the results of PR #50. The PR description originally named
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

`TOOLS.csv` is a hand-maintained historical inventory. Its counts and wiring
labels were not all reconciled with one baseline. In particular, the Sinclair
row says 32 proposals / 47 in the adoption batch, while the owner-ruling record
in the same PR describes 41 Sinclair proposals plus 15 Bowditch proposals.
The Junto row's 13 candidates and the CSC row's `unwired` label likewise must
not be read as current counts or current wiring. These original rows are
preserved rather than silently rewritten. Use the dated owner-ruling records
for the owner's decisions and freshly generated, version-pinned job outputs
for current counts and readiness.

Workload lanes are planning classifications inferred from tracker blockers and
held job outputs. A `machine_queued` label is not evidence of a successful
fetch, a reviewed legal claim, or a completed readiness step. Regenerating this
map does not implement owner rulings, change tracker gates, or review claims.
