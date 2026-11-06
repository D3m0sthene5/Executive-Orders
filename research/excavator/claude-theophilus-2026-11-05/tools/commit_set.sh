#!/bin/bash
# usage: commit_set.sh -> stages only the small Theophilus receipts that belong on the work branch (claims, tools, orders,
# reports, per-batch REAPPLY/review/completion manifests and tallies). Bulky packet files stay for the state snapshot.
cd /home/claude/executive-orders
R=research/excavator/claude-theophilus-2026-11-05
git add research/readiness/claims/claude-2026-11-05-theophilus-*.jsonl 2>/dev/null
git add $R/orders $R/tools $R/BATCHES.json $R/COORDINATOR_LOG.txt $R/REPORT.md $R/telemetry 2>/dev/null
for P in $R/*/packet; do
  for f in REAPPLY.json DISPATCH_CHECK.json PREPARE.json decisions.csv clauses.csv RATIONALES.json PRODUCER_REPORT.md APPLIED_FOR_REVIEW \
           reviews completion complete-v*-dryrun; do [ -e $P/$f ] && git add $P/$f; done
  for c in $P/complete-v*; do [ -d $c ] || continue
    for f in TALLY.json EXCEPTIONS.json PUBLICATION.json INPUTS.json PACKETS.json TRACKER_REPLAY.json checker/SUMMARY.json checker/PER_CLAIM.json; do [ -e $c/$f ] && git add $c/$f; done
  done
  for a in $P/applied-v*; do [ -d $a ] || continue
    for f in CHECK_SUMMARY.json GEDDES_LINT.json GEDDES_RESOLUTIONS.json SELECTED_SOURCE_CHECK.json actual-checker/SUMMARY.json; do [ -e $a/$f ] && git add $a/$f; done
  done
done
git status --short | grep '^A' | wc -l
