#!/bin/bash
# usage: moon_review_prep.sh BATCH APPLIED_VERSION   -> plants controls, renders reviewer prompt
S=/tmp/claude-0/-home-claude/79a6cc5c-022c-506a-a289-86cc7ef89ecd/scratchpad
cd /home/claude/executive-orders
B=$1; V=${2:-applied-v1}
if [[ $B == n* ]]; then P=research/excavator/claude-apollo-2026-10-31/$B/packet/supp; T=reviewer_nra.txt; else P=research/excavator/claude-apollo-2026-10-31/$B/packet; T=reviewer_general.txt; fi
python3 -I $S/moon_plant.py $B $P/$V && mkdir -p $P/reviews
sed -e "s#SETPATH#$S/moon-review/$B/REVIEW_SET.jsonl#" -e "s#PACKETDIR#/home/claude/executive-orders/$P#g" -e "s#BATCH#$B#g" $S/moon-prompts/$T > $S/moon-prompts/reviewer-$B.txt
