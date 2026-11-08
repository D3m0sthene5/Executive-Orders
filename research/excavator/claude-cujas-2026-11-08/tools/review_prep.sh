#!/bin/bash
# usage: review_prep.sh BATCH APPLIED_VERSION -> plants controls once, writes a separately shuffled review set for each of
# two independent arms (A, B; same planted controls), renders both blind reviewer prompts. Coordinator tool; no judgment.
set -e
E=/tmp/claude-0/-home-user-Executive-Orders/e6387873-0c33-504f-9955-73a6cf06733e/scratchpad/necker
cd /home/user/Executive-Orders; T=research/excavator/claude-cujas-2026-11-08/tools
B=$1; V=$2; P=research/excavator/claude-cujas-2026-11-08/$B/${PK:-packet}
python3 -I $T/plant.py $B $P/$V && mkdir -p $P/reviews $E/prompts
for arm in A B; do
python3 - $E/moon-review/$B/REVIEW_SET.jsonl $E/moon-review/$B/REVIEW_SET_$arm.jsonl "cujas-$B-$arm" <<'PY'
import random, sys
rows=[l for l in open(sys.argv[1]) if l.strip()]
random.Random(sys.argv[3]).shuffle(rows)
open(sys.argv[2],'w').writelines(rows)
PY
sed -e "s#SETPATH#$E/moon-review/$B/REVIEW_SET_$arm.jsonl#" -e "s#PACKETDIR#/home/user/Executive-Orders/$P#g" -e "s#BATCH#$B#g" -e "s#ARM#$arm#g" $T/prompts/reviewer.txt > $E/prompts/reviewer-$B-$arm.txt
done
echo "REVIEW-PREP $B: $(wc -l < $E/moon-review/$B/REVIEW_SET_A.jsonl) claims"
