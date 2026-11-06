#!/bin/bash
# usage: prepare.sh BATCH EO:1 EO:2 ...  (repo root; coordinator tool, no legal judgment)
# 1. ordinary production prepare (source-blocked orders are refused and recorded), 2. Selden supplement + brief,
# 3. source_supplement prepare into packet-s1 (or a copy note when nothing to add), 4. Cruden lookups and Geddes views.
set -e
cd /home/claude/executive-orders
B=$1; shift; R=research/selden/proof/packets/$B; L=/home/claude/selden-scratch/prep-$B.log
mkdir -p $R
python3 jobs/claim-kit/kit.py prepare "$@" --agent claude --research-only --write $R/screen > $L 2>&1
OK=$(python3 -c "import json;print(' '.join(json.load(open('$R/screen/DISPATCH_CHECK.json'))['dispatchable_ids']))")
python3 -c "import json;d=json.load(open('$R/screen/DISPATCH_CHECK.json'));json.dump({'source_blocked_ids':d['source_blocked_ids'],'dispatchable_ids':d['dispatchable_ids']},open('$R/SCREEN.json','w'),indent=1)"
python3 jobs/claim-kit/kit.py prepare $OK --agent claude --write $R/packet >> $L 2>&1
python3 -I research/selden/proof/tools/supplement.py $B $OK >> $L 2>&1
P=packet
if python3 -c "import json,sys;sys.exit(0 if json.load(open('$R/SUPPLEMENT_SOURCES.json'))['sources'] else 1)"; then
  (cd jobs/claim-kit && python3 source_supplement.py --repo ../.. prepare --parent ../../$R/packet --sources ../../$R/SUPPLEMENT_SOURCES.json --agent claude --write ../../$R/packet-s1) >> $L 2>&1 && P=packet-s1
fi
echo $P > $R/PRODUCTION_PACKET
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/$P >> $L 2>&1 || true
mkdir -p $R/$P/views
for i in $(python3 -c "import json;print(' '.join(json.load(open('$R/$P/PACKET.json'))['dossiers']))" 2>/dev/null); do n=${i#EO:}; python3 -I jobs/geddes/geddes.py view $R/$P/PACKET.json $i --write $R/$P/views/EO_$n.json >> $L 2>&1 || echo "VIEWFAIL $i" >> $L; done
python3 jobs/claim-kit/kit.py dispatch-check $R/$P --write $R/$P/DISPATCH_CHECK.final.json >> $L 2>&1 || true
echo "DONE $B packet=$P"
