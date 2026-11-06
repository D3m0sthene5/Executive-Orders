#!/bin/bash
# usage: prepare.sh BATCH   (run from repo root; coordinator tool, no legal judgment)
# Herschel H5: prepares one claim-kit packet (research-only export kept if source-blocked), lookups and slim views.
S=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5
H=research/herschel/H5
B=$1; R=$H/packets/$B
IDS=$(python3 -c "import json;print(' '.join(json.load(open('$H/tools/batches.json'))['$B']))")
mkdir -p $R
echo "prepare $B start $(date -u +%FT%TZ)" > $S/prep-$B.log
python3 jobs/claim-kit/kit.py prepare $IDS --agent claude --write $R/packet >> $S/prep-$B.log 2>&1
RC=$?
if [ $RC -ne 0 ]; then
  echo "PREPARE_EXIT $RC; retrying --research-only into packet" >> $S/prep-$B.log
  if [ ! -f $R/packet/PACKET.json ]; then
    python3 jobs/claim-kit/kit.py prepare $IDS --agent claude --research-only --write $R/packet >> $S/prep-$B.log 2>&1
  fi
fi
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/packet >> $S/prep-$B.log 2>&1
mkdir -p $R/packet/views
for i in $IDS; do n=${i#EO:}; python3 -I jobs/geddes/geddes.py view $R/packet/PACKET.json $i --write $R/packet/views/EO_$n.json >> $S/prep-$B.log 2>&1 || echo "VIEWFAIL $i" >> $S/prep-$B.log; done
echo "prepare $B end $(date -u +%FT%TZ)" >> $S/prep-$B.log
echo "DONE $B"
