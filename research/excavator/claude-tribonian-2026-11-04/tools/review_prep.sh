#!/bin/bash
# usage: review_prep.sh BATCH APPLIED_VERSION -> plants controls, renders the blind reviewer prompt
E=/tmp/claude-0/-home-claude/113ce3b2-4ba3-50df-9241-eb6576e0f367/scratchpad/tribonian
cd /home/claude/executive-orders; T=research/excavator/claude-tribonian-2026-11-04/tools
B=$1; V=$2; P=research/excavator/claude-tribonian-2026-11-04/$B/packet
python3 -I $T/plant.py $B $P/$V && mkdir -p $P/reviews
sed -e "s#SETPATH#$E/moon-review/$B/REVIEW_SET.jsonl#" -e "s#PACKETDIR#/home/claude/executive-orders/$P#g" -e "s#BATCH#$B#g" $T/prompts/reviewer.txt > $E/prompts/reviewer-$B.txt
