#!/bin/bash
# usage: review_prep.sh BATCH APPLIED_VERSION  -> plants controls, renders reviewer prompt
E=/tmp/claude-0/-home-claude/79a6cc5c-022c-506a-a289-86cc7ef89ecd/scratchpad/erasmus
cd /home/claude/executive-orders
B=$1; V=$2
if [[ $B == c1 || $B == r1 || $B == e1 ]]; then P=research/excavator/claude-erasmus-2026-11-02/$B/packet/supp; T=reviewer_nra.txt; else P=research/excavator/claude-erasmus-2026-11-02/$B/packet; T=reviewer_general.txt; fi
python3 -I $E/erasmus_plant.py $B $P/$V && mkdir -p $P/reviews
sed -e "s#SETPATH#$E/moon-review/$B/REVIEW_SET.jsonl#" -e "s#PACKETDIR#/home/claude/executive-orders/$P#g" -e "s#BATCH#$B#g" -e "s#claude-apollo-2026-10-31#claude-erasmus-2026-11-02#g" -e "s#2026-10-31\"#2026-11-02\"#g" research/excavator/claude-apollo-2026-10-31/tools/prompts/$T > $E/prompts/reviewer-$B.txt
