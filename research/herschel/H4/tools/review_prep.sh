#!/bin/bash
# usage: review_prep.sh BATCH APPLIED_VERSION -> plants controls once, writes a seeded shuffle per arm (A, B), renders
# both blind reviewer prompts for workers WA and WB. Coordinator tool; no legal judgment.
set -e
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4
cd /home/claude/executive-orders; T=research/herschel/H4/tools
B=$1; V=$2; WA=$3; WB=$4; P=research/herschel/H4/packets/$B/packet
python3 -I $T/plant.py $B $P/$V && mkdir -p $P/reviews $E/prompts
echo "$V" > $P/APPLIED_FOR_REVIEW
for arm in A B; do
python3 - $E/moon-review/$B/REVIEW_SET.jsonl $E/moon-review/$B/REVIEW_SET_$arm.jsonl "herschel-H4-$B-$arm" <<'PY'
import random, sys
rows=[l for l in open(sys.argv[1]) if l.strip()]
random.Random(sys.argv[3]).shuffle(rows)
open(sys.argv[2],'w').writelines(rows)
PY
W=$WA; [ $arm = B ] && W=$WB
sed -e "s#SETPATH#$E/moon-review/$B/REVIEW_SET_$arm.jsonl#" -e "s#PACKETDIR#/home/claude/executive-orders/$P#g" -e "s#BATCH#$B#g" -e "s#ARM#$arm#g" $T/prompts/reviewer.txt > $E/prompts/$W.txt
done
echo "REVIEW-PREP $B: $(wc -l < $E/moon-review/$B/REVIEW_SET_A.jsonl) claims"
