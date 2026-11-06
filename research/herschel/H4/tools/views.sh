#!/bin/bash
# usage: views.sh BATCH -> cruden lookups + geddes slim views for a prepared packet (coordinator tool)
S=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4
cd /home/claude/executive-orders; B=$1; R=research/herschel/H4/packets/$B/packet
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R >> $S/views-$B.log 2>&1 || echo LOOKUPFAIL >> $S/views-$B.log
mkdir -p $R/views
for i in $(python3 -c "import json;print(' '.join(json.load(open('$R/PACKET.json'))['members'] if isinstance(json.load(open('$R/PACKET.json')).get('members'),list) else []))" 2>/dev/null); do :; done
for i in $(python3 -c "import json;print(' '.join(json.load(open('research/herschel/H4/tools/batches.json'))['$B']))"); do n=${i#EO:}; python3 -I jobs/geddes/geddes.py view $R/PACKET.json "$i" --write "$R/views/EO_$n.json" >> $S/views-$B.log 2>&1 || echo "VIEWFAIL $i" >> $S/views-$B.log; done
echo "VIEWS $B $(ls $R/views | wc -l)"
