#!/bin/bash
# usage: review_prep.sh BATCH APPLIED_VERSION WA WB -> plants controls once, writes a seeded shuffle per arm (A, B),
# renders both blind reviewer prompts. Coordinator tool; no legal judgment.
set -e
E=/home/claude/selden-scratch
cd /home/claude/executive-orders; T=research/selden/proof/tools
B=$1; V=$2; WA=$3; WB=$4; P=research/selden/proof/packets/$B/${PK:-packet-s1}
python3 -I $T/plant.py $B $P/$V && mkdir -p $P/reviews $E/prompts
echo "$V" > $P/APPLIED_FOR_REVIEW
for arm in A B; do
python3 - $E/review/$B/REVIEW_SET.jsonl $E/review/$B/REVIEW_SET_$arm.jsonl "selden-proof-$B-$arm" <<'PY'
import random, sys
rows=[l for l in open(sys.argv[1]) if l.strip()]
random.Random(sys.argv[3]).shuffle(rows)
open(sys.argv[2],'w').writelines(rows)
PY
W=$WA; [ $arm = B ] && W=$WB
sed -e "s#SETPATH#$E/review/$B/REVIEW_SET_$arm.jsonl#" -e "s#PACKETDIR#/home/claude/executive-orders/$P#g" -e "s#BATCH#$B#g" -e "s#ARM#$arm#g" $T/prompts/reviewer.txt > $E/prompts/$W.txt
done
echo "REVIEW-PREP $B: $(wc -l < $E/review/$B/REVIEW_SET_A.jsonl) claims"
