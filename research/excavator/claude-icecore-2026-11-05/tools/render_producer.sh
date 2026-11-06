#!/bin/bash
# usage: render_producer.sh BATCH -> scratch prompts/producer-BATCH.txt
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/icecore
cd /home/claude/executive-orders; T=research/excavator/claude-icecore-2026-11-05/tools/prompts
B=$1; P=/home/claude/executive-orders/research/excavator/claude-icecore-2026-11-05/$B/packet
case $B in f*) F=$T/family_12553.txt;; k*) F=$T/family_14148.txt;; *) F=/dev/null;; esac
PT=$T/producer.txt; [[ $B == c* ]] && PT=$T/producer_correction.txt
python3 - "$PT" "$F" "$P" "$B" > $E/prompts/producer-$B.txt <<'PY'
import sys
t=open(sys.argv[1]).read(); f=open(sys.argv[2]).read()
print(t.replace('PACKETPATH',sys.argv[3]).replace('<PACKET>',sys.argv[3]).replace('FAMILYBRIEF',f).replace('BRIEFPATH',sys.argv[3].rsplit('/packet',1)[0]+'/CORRECTION_BRIEF.json').replace('/icecore-work/BATCH/','/icecore-work/'+sys.argv[4]+'/'))
PY
