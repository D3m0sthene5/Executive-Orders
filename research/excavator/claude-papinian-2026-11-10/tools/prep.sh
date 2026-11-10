#!/bin/bash
# usage: prep.sh BATCH AGENT RP EO:N ...   (coordinator tool, no legal judgment)
# RP=1 adds --replacement-proposal (members that already have a filed claim). Prepares one claim-kit packet,
# then builds cruden lookups and Geddes slim views. Log: $SCR/logs/prep-BATCH.log
REPO=/c/Users/danie/eo-wt/papinian; SCR=/c/Users/danie/AppData/Local/Temp/papinian
W=research/excavator/claude-papinian-2026-11-10
B=$1; A=$2; RP=$3; shift 3; IDS="$@"
cd $REPO; R=$W/$B; L=$SCR/logs/prep-$B.log; mkdir -p $R $SCR/logs
echo "PREPARE $B agent=$A rp=$RP start $(date -u +%FT%TZ) $IDS" > $L
FLAG=""; [ "$RP" = "1" ] && FLAG="--replacement-proposal"
python -X utf8 jobs/claim-kit/kit.py prepare $IDS --agent $A $FLAG --write $R/packet >> $L 2>&1 || echo "PREPARE_EXIT $?" >> $L
python -X utf8 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/packet >> $L 2>&1 || echo "LOOKUPS_FAIL" >> $L
mkdir -p $R/packet/views
for i in $IDS; do n=$(echo ${i#EO:} | tr ':' '_'); python -X utf8 -I jobs/geddes/geddes.py view $R/packet/PACKET.json $i --write $R/packet/views/EO_$n.json >> $L 2>&1 || echo "VIEWFAIL $i" >> $L; done
echo "DONE $B $(date -u +%FT%TZ)" >> $L; grep -E 'PREPARE_EXIT|LOOKUPS_FAIL|VIEWFAIL|DONE|"state"|source_blocked' $L | tail -6
