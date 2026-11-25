#!/bin/bash
# usage: prep.sh BATCH AGENT RP ACTION EO:N ...   (coordinator tool, no legal judgment)
# RP=1 adds --replacement-proposal (members that already have a filed claim). Prepares one claim-kit packet,
# then builds cruden lookups and Geddes slim views. Log: $SCR/logs/prep-BATCH.log
REPO=/home/claude/d3m0sthene5/executive-orders; SCR=/home/claude/bartolus-scr
W=research/excavator/claude-bartolus-2026-11-24
B=$1; A=$2; RP=$3; ACT=$4; shift 4; IDS="$@"; export LARREY_LEVEL=hard
cd $REPO; R=$W/$B; L=$SCR/logs/prep-$B.log; mkdir -p $R $SCR/logs
echo "PREPARE $B agent=$A rp=$RP start $(date -u +%FT%TZ) $IDS" > $L
FLAG=""; [ "$RP" = "1" ] && FLAG="--replacement-proposal"
python3 -X utf8 jobs/claim-kit/kit.py prepare $IDS --agent $A --action $ACT $FLAG --write $R/packet >> $L 2>&1 || echo "PREPARE_EXIT $?" >> $L
python3 -X utf8 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/packet >> $L 2>&1 || echo "LOOKUPS_FAIL" >> $L
mkdir -p $R/packet/views
for i in $IDS; do n=$(echo ${i#EO:} | tr ':' '_'); python3 -X utf8 -I jobs/geddes/geddes.py view $R/packet/PACKET.json $i --write $R/packet/views/EO_$n.json >> $L 2>&1 || echo "VIEWFAIL $i" >> $L; done
echo "DONE $B $(date -u +%FT%TZ)" >> $L; grep -E 'PREPARE_EXIT|LOOKUPS_FAIL|VIEWFAIL|DONE|"state"|source_blocked' $L | tail -6
