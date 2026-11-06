#!/bin/bash
# usage: prepare.sh PACKET   (coordinator tool, no legal judgment; never run two at once)
# Prepares one claim-kit packet for the Dorotheus wave, runs the dispatch check, builds lookups and Geddes slim views.
E=/tmp/claude-0/dorotheus-wave; cd /home/user/Executive-Orders
B=$1; case $B in y*) W=research/excavator/dorotheus-yesprobe-2026-11-06;; *) W=research/excavator/dorotheus-sample-2026-11-06;; esac
R=$W/$B; L=$E/prep-$B.log
IDS=$(python3 -c "import json;print(' '.join(json.load(open('$E/batches.json'))['packets']['$B']))")
mkdir -p $R; echo "PREPARE $B start $(date -u +%FT%TZ) $IDS" > $L
python3 jobs/claim-kit/kit.py prepare $IDS --agent dorotheus --write $R/packet >> $L 2>&1 || echo "PREPARE_EXIT $? (source blocks retained; see DISPATCH_CHECK.json)" >> $L
python3 jobs/claim-kit/kit.py dispatch-check $R/packet --write $R/packet/dispatch-v2.json >> $L 2>&1; echo "DISPATCH_EXIT $?" >> $L
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/packet >> $L 2>&1
mkdir -p $R/packet/views
for i in $IDS; do n=$(echo ${i#EO:} | tr ':' '_'); python3 -I jobs/geddes/geddes.py view $R/packet/PACKET.json $i --write $R/packet/views/EO_$n.json >> $L 2>&1 || echo "VIEWFAIL $i" >> $L; done
echo "DONE $B $(date -u +%FT%TZ)" >> $L; tail -3 $L
