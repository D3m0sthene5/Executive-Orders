# Historical remaining-work and tool-map snapshot

The `TOOLMAP_WORKLOAD.csv`, `REMAINING_WORK*`, and `EFFORT*` files were
regenerated on 2026-10-22 (22:20 UTC) from main at
`46a29e15d6ed4c252416b28e0ccc0590fcf6abc2`, whose tracker output (GitHub run 254)
counts 3,403 provisional statuses (3,359 + 15 Bowditch adopted in PR #51 + 29
Sinclair adopted after Codex's cross-family review in PR #52) and 280 orders ready
for human review. Lewis re-ran at 20:34 UTC with the Pinakes ProQuest ingest as an
input, so its scope fell from 7,340 to 5,426 orders; the 2,750 orders with the
owner's ProQuest replica scans now carry ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK and
the tool map puts them in the "ruled or drafted, not wired" lane (they count under
the Oct 21 transcription ruling once the tracker rule on branch claude/justinian-1
merges). Against the PR #48 snapshot at
`78d1b67cb5157fb70be912b167f266718d10d483` (278 ready, 76,905 open steps on held
orders, 15,698 model agent-hours) this snapshot has 280 ready, 76,785 open steps
on held orders, 85,983 in all, and 15,427 model agent-hours; the owner's hand-work
lane fell from 2,655 steps to 10 because the scans are in. The PR description originally named
`09310ada` as its source baseline; these files do not themselves pin every
input file's version. Restoring generated job outputs to main during PR cleanup
does not refresh these planning snapshots or establish that they describe the
restored outputs.

At this snapshot, 280 of 14,972 tracked orders were ready for human review.
`TOOLMAP_WORKLOAD.csv` partitions 76,785 open steps for those existing orders.
`REMAINING_WORK*` also includes 9,198 estimated steps for 1,314 APP-counted
orders not yet in the project (seven steps each), giving 85,983 total steps.
`EFFORT*` estimates roughly 15,427 agent-hours under its effort model; this is
a planning estimate, not measured runtime, token use, or verified savings.

`TOOLS.csv` is a hand-maintained inventory, updated 2026-10-22 from the merge
audit (`research/diagnostics/pr-merge-20261022/`), the Sinclair lean review, the
Justinian run report on branch `claude/justinian-1`, the PR #50, #52 and #54 descriptions and the Mansfield report.
Rows that describe branch work say so; the CSC row's `unwired` label and the
Junto candidate count are as recorded in those sources, not re-measured. Use the dated owner-ruling records
for the owner's decisions and freshly generated, version-pinned job outputs
for current counts and readiness.

Workload lanes are planning classifications inferred from tracker blockers and
held job outputs. A `machine_queued` label is not evidence of a successful
fetch, a reviewed legal claim, or a completed readiness step. Regenerating this
map does not implement owner rulings, change tracker gates, or review claims.
