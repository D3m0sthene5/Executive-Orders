#!/bin/bash
# Lind trial (paired A/B blind review). usage: lind_prep.sh BATCH APPLIED_VERSION
# Plants controls once (same REVIEW_SET for both arms), writes a seeded shuffle of the set per arm,
# runs the maintained verifier adapter on arm B's set only (planted versions, so no genuine counterpart
# reaches any receipt), and renders both reviewer prompts. Coordinator tool; no legal judgment.
set -e
E=/tmp/claude-0/-home-claude/113ce3b2-4ba3-50df-9241-eb6576e0f367/scratchpad/tribonian
cd /home/claude/executive-orders; T=research/excavator/claude-tribonian-2026-11-04/tools
B=$1; V=$2; P=research/excavator/claude-tribonian-2026-11-04/$B/packet
L=$E/lind/$B; mkdir -p $L $P/reviews
python3 -I $T/plant.py $B $P/$V
for arm in A B; do
python3 - $E/moon-review/$B/REVIEW_SET.jsonl $L/REVIEW_SET_$arm.jsonl "lind-$B-$arm" <<'PY'
import random, sys
rows=[l for l in open(sys.argv[1]) if l.strip()]
random.Random(sys.argv[3]).shuffle(rows)
open(sys.argv[2],'w').writelines(rows)
PY
done
python3 -I /home/claude/executive-orders/research/excavator/claude-tribonian-2026-11-04/tools/lind/cards_from_review_set.py --review-set $L/REVIEW_SET_B.jsonl --repo-root /home/claude/executive-orders --out-dir $L/receipts > $L/adapter.log 2>&1
rm -rf $L/receipts/cards   # reviewer needs only the receipts; cards are the same claims
sed -e "s#SETPATH#$L/REVIEW_SET_A.jsonl#" -e "s#PACKETDIR#/home/claude/executive-orders/$P#g" -e "s#BATCH#$B#g" $T/prompts/reviewer.txt > $E/prompts/reviewer-$B-A.txt
{ sed -e "s#SETPATH#$L/REVIEW_SET_B.jsonl#" -e "s#PACKETDIR#/home/claude/executive-orders/$P#g" -e "s#BATCH#$B-armB#g" -e "s#reviews/BLIND_REVIEW.jsonl#reviews/BLIND_REVIEW_ARM_B.jsonl#" $T/prompts/reviewer.txt
  sed -e "s#RECEIPTDIR#$L/receipts#" $T/prompts/reviewer_armB_addendum.txt; } > $E/prompts/reviewer-$B-B.txt
echo "LIND-PREP $B: $(wc -l < $L/REVIEW_SET_A.jsonl) claims; receipts $(ls $L/receipts | grep -c MECHANICAL)"
