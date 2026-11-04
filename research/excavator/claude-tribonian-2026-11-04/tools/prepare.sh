#!/bin/bash
# usage: prepare.sh BATCH   (run from repo root; coordinator tool, no legal judgment)
set -e
S=/tmp/claude-0/-home-claude/113ce3b2-4ba3-50df-9241-eb6576e0f367/scratchpad/tribonian
B=$1; R=research/excavator/claude-tribonian-2026-11-04/$B
IDS=$(python3 -c "import json;print(' '.join(json.load(open('$S/batches.json'))['$B']))")
mkdir -p $R
python3 jobs/claim-kit/kit.py prepare $IDS --agent claude --write $R/packet > $S/prep-$B.log 2>&1
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/packet >> $S/prep-$B.log 2>&1
mkdir -p $R/packet/views
for i in $IDS; do n=${i#EO:}; python3 -I jobs/geddes/geddes.py view $R/packet/PACKET.json $i --write $R/packet/views/EO_$n.json >> $S/prep-$B.log 2>&1 || echo "VIEWFAIL $i" >> $S/prep-$B.log; done
echo "DONE $B"
