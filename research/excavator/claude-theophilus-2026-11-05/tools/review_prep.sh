#!/bin/bash
# usage: review_prep.sh BATCH APPLIED_VERSION -> plants controls once, writes a separately shuffled review set for each of
# two independent arms (A, B; same planted controls), renders both blind reviewer prompts. Coordinator tool; no judgment.
set -e
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/theophilus
cd /home/claude/executive-orders; T=research/excavator/claude-theophilus-2026-11-05/tools
B=$1; V=$2; P=research/excavator/claude-theophilus-2026-11-05/$B/${PK:-packet}
python3 -I $T/plant.py $B $P/$V && mkdir -p $P/reviews $E/prompts
for arm in A B; do
python3 - $E/moon-review/$B/REVIEW_SET.jsonl $E/moon-review/$B/REVIEW_SET_$arm.jsonl "theophilus-$B-$arm" <<'PY'
import random, sys
rows=[l for l in open(sys.argv[1]) if l.strip()]
random.Random(sys.argv[3]).shuffle(rows)
open(sys.argv[2],'w').writelines(rows)
PY
sed -e "s#SETPATH#$E/moon-review/$B/REVIEW_SET_$arm.jsonl#" -e "s#PACKETDIR#/home/claude/executive-orders/$P#g" -e "s#BATCH#$B#g" -e "s#ARM#$arm#g" $T/prompts/reviewer.txt > $E/prompts/reviewer-$B-$arm.txt
done
echo "REVIEW-PREP $B: $(wc -l < $E/moon-review/$B/REVIEW_SET_A.jsonl) claims"
