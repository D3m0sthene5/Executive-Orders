#!/bin/bash
# usage: prepare.sh BATCH  (repo root; coordinator tool, no legal judgment). Packet in research/herschel/H6/packets/BATCH.
S=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H6
cd /home/claude/executive-orders
B=$1; R=research/herschel/H6/packets/$B
IDS=$(python3 -c "import json;print(' '.join(json.load(open('research/herschel/H6/tools/batches.json'))['$B']))")
mkdir -p research/herschel/H6/packets
t0=$(date -u +%FT%TZ)
python3 jobs/claim-kit/kit.py prepare $IDS --agent claude --write $R > $S/prep-$B.log 2>&1 || echo "PREPARE_EXIT $? (source blocks retained; see DISPATCH_CHECK.json)" >> $S/prep-$B.log
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R >> $S/prep-$B.log 2>&1
mkdir -p $R/views
for i in $IDS; do n=${i#EO:}; python3 -I jobs/geddes/geddes.py view $R/PACKET.json $i --write $R/views/EO_$n.json >> $S/prep-$B.log 2>&1 || echo "VIEWFAIL $i" >> $S/prep-$B.log; done
echo "PREPARE $B $t0 -> $(date -u +%FT%TZ)" >> /home/claude/executive-orders/research/herschel/H6/COORDINATOR_LOG.txt
echo "DONE $B"
