#!/bin/bash
# usage: prepare.sh BATCH  (run from repo root; coordinator tool, no legal judgment). Packet in research/herschel/H2/packets/BATCH/packet
S=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H2
B=$1; R=research/herschel/H2/packets/$B
IDS=$(python3 -c "import json;print(' '.join(json.load(open('$S/batches.json'))['$B']))")
mkdir -p $R
echo "prepare $B start $(date -u +%FT%TZ)" >> $S/prep-times.log
python3 jobs/claim-kit/kit.py prepare $IDS --agent claude --write $R/packet > $S/prep-$B.log 2>&1 || echo "PREPARE_EXIT $? (source blocks retained; see DISPATCH_CHECK.json)" >> $S/prep-$B.log
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/packet >> $S/prep-$B.log 2>&1
mkdir -p $R/packet/views
for i in $IDS; do n=${i#EO:}; python3 -I jobs/geddes/geddes.py view $R/packet/PACKET.json $i --write $R/packet/views/EO_$n.json >> $S/prep-$B.log 2>&1 || echo "VIEWFAIL $i" >> $S/prep-$B.log; done
echo "prepare $B end $(date -u +%FT%TZ)" >> $S/prep-times.log
echo "DONE $B"
