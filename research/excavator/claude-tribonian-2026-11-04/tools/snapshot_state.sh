#!/bin/bash
# Durable snapshot of the Tribonian run folder (packets, applied versions, reviews, completions, reports) to branch
# claude/tribonian-state, one batch per commit and push (a single large push was refused by the server). Uses a separate
# index so the working index, which Valla reads as the tracked package set, is untouched. Control keys never included.
cd /home/claude/executive-orders
S=/tmp/claude-0/-home-claude/113ce3b2-4ba3-50df-9241-eb6576e0f367/scratchpad/tribonian
R=research/excavator/claude-tribonian-2026-11-04
cp $S/COORDINATOR_LOG.txt $R/COORDINATOR_LOG.txt
export GIT_INDEX_FILE=$S/state.idx
P=$(git ls-remote origin refs/heads/claude/tribonian-state | cut -f1)
if [ -n "$P" ]; then git fetch -q origin claude/tribonian-state && git read-tree $P; else git read-tree HEAD; P=$(git rev-parse HEAD); fi
for d in tools COORDINATOR_LOG.txt $(ls $R | grep -E '^[a-z][0-9]{2}$|^rereview'); do
  git add -f $R/$d research/readiness/claims 2>/dev/null
  T=$(git write-tree); [ "$T" = "$(git rev-parse $P^{tree})" ] && continue
  C=$(git commit-tree $T -p $P -m "Tribonian state snapshot $(date -u +%FT%TZ): $d")
  for try in 1 2 3; do git push -q origin $C:refs/heads/claude/tribonian-state 2>/dev/null && break; sleep 20; done || { echo "FAILED at $d"; exit 1; }
  P=$C; echo "pushed $d"
done
echo "snapshot complete $P"
