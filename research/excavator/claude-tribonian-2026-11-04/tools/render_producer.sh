#!/bin/bash
# usage: render_producer.sh BATCH -> scratch prompts/producer-BATCH.txt
E=/tmp/claude-0/-home-claude/113ce3b2-4ba3-50df-9241-eb6576e0f367/scratchpad/tribonian
cd /home/claude/executive-orders; T=research/excavator/claude-tribonian-2026-11-04/tools/prompts
B=$1; P=/home/claude/executive-orders/research/excavator/claude-tribonian-2026-11-04/$B/packet
case $B in f*) F=$T/family_12553.txt;; k*) F=$T/family_14148.txt;; *) F=/dev/null;; esac
python3 - "$T/producer.txt" "$F" "$P" > $E/prompts/producer-$B.txt <<'PY'
import sys
t=open(sys.argv[1]).read(); f=open(sys.argv[2]).read()
print(t.replace('PACKETPATH',sys.argv[3]).replace('<PACKET>',sys.argv[3]).replace('FAMILYBRIEF',f))
PY
