#!/bin/bash
# usage: reprep_correction.sh BATCH  -- a correction packet went stale (prior research changed by later
# completions). Preserve the stale packet as packet-stale-vN, re-prepare from the same ids, and carry the
# producer's filled sheets and report into the new packet. Coordinator tool; no legal judgment.
set -e
cd /home/claude/executive-orders
B=$1; R=research/excavator/claude-tribonian-2026-11-04/$B
n=1; while [ -e $R/packet-stale-v$n ]; do n=$((n+1)); done
mv $R/packet $R/packet-stale-v$n
bash research/excavator/claude-tribonian-2026-11-04/tools/prepare.sh $B
for f in decisions.csv clauses.csv PRODUCER_REPORT.md; do
  [ -e $R/packet-stale-v$n/$f ] && cp $R/packet-stale-v$n/$f $R/packet/$f
done
cp $R/packet-stale-v$n/RATIONALES.json $R/packet/RATIONALES.stale-v$n.json 2>/dev/null || true
python3 research/excavator/claude-tribonian-2026-11-04/tools/freshness.py $B
echo "REPREP $B from packet-stale-v$n"
