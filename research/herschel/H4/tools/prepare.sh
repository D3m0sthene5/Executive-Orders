#!/bin/bash
# usage: prepare.sh BATCH   (run from repo root; coordinator tool, no legal judgment)
S=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4
B=$1; R=research/herschel/H4/packets/$B
cd /home/claude/executive-orders
IDS=$(python3 -c "import json;print(' '.join(json.load(open('research/herschel/H4/tools/batches.json'))['$B']))")
echo "prepare $B start $(date -u +%FT%TZ)" >> $S/prep-$B.log
python3 jobs/claim-kit/kit.py prepare $IDS --agent claude --write $R/packet >> $S/prep-$B.log 2>&1 || echo "PREPARE_EXIT $? (source blocks retained; see DISPATCH_CHECK.json)" >> $S/prep-$B.log
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/packet >> $S/prep-$B.log 2>&1
mkdir -p $R/packet/views
for i in $IDS; do n=${i#EO:}; python3 -I jobs/geddes/geddes.py view $R/packet/PACKET.json $i --write "$R/packet/views/EO_$n.json" >> $S/prep-$B.log 2>&1 || echo "VIEWFAIL $i" >> $S/prep-$B.log; done
echo "prepare $B done $(date -u +%FT%TZ)" >> $S/prep-$B.log
echo "DONE $B"
