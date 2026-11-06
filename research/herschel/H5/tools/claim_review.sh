#!/bin/bash
# usage: claim_review.sh BATCH WA WB CLAIMS_FILE_OR_APPLIED_DIR -> plants controls (plant.py), seeded shuffle per arm,
# renders and launches two fresh blind Opus reviewers. Coordinator tool; no legal judgment.
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5
R=/home/claude/executive-orders; T=$R/research/herschel/H5/tools; L=$R/research/herschel/H5/COORDINATOR_LOG.txt
B=$1; WA=$2; WB=$3; C=$4; P=$R/research/herschel/H5/packets/$B/packet
cd $R; echo "claim-plant $B $(python3 -I $T/plant.py $B $C 2>&1 | tail -1)" >> $L; mkdir -p $P/reviews
for arm in A B; do W=$WA; [ $arm = B ] && W=$WB; mkdir -p /tmp/claude-0/herschel-H5/$W
python3 - $E/moon-review/$B/REVIEW_SET.jsonl $E/moon-review/$B/REVIEW_SET_$arm.jsonl "herschel-H5-$B-$arm" <<'PY'
import random, sys
rows=[l for l in open(sys.argv[1]) if l.strip()]
random.Random(sys.argv[3]).shuffle(rows)
open(sys.argv[2],'w').writelines(rows)
PY
sed -e "s#SETPATH#$E/moon-review/$B/REVIEW_SET_$arm.jsonl#" -e "s#PACKETDIR#$P#g" -e "s#WORKER#$W#g" -e "s#BATCH#$B#g" -e "s#ARM#$arm#g" $T/prompt_claim_review.txt > $E/prompts/$W.txt
printf "$W\treview\topus\t-\t$B\t$(python3 -c "import json;print(' '.join(json.loads(l)['instrument_id'] for l in open('$E/moon-review/$B/REVIEW_SET.jsonl') if l.strip()))")\n" >> $E/WORKERS.tsv
(nohup bash $T/launch.sh $W opus $E/prompts/$W.txt > /dev/null 2>&1 &)
done
