#!/bin/bash
# usage: render_review.sh KIND BATCH ARM WORKER [PACKETDIR] [PACKETMAP] -> scratch prompts/WORKER.txt (coordinator tool)
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H2
T=/home/claude/executive-orders/research/herschel/H2/tools/prompts
K=$1; B=$2; A=$3; W=$4; PD=$5; PM=$6
O=/home/claude/executive-orders/research/herschel/H2/reviews/$B; mkdir -p $O
cat $T/review_common.txt $T/review_$K.txt $T/review_tail.txt | python3 -c "
import sys
s=sys.stdin.read()
for k,v in (('SETPATH','$E/review/$B/REVIEW_SET_$A.jsonl'),('OUTPATH','$O/BLIND_REVIEW_$A.jsonl'),('REVIEWER','claude-blind-reviewer-herschel-H2-$B-$A-2026-11-05'),('PACKETDIR','$PD'),('PACKETMAP','$PM'),('WORKER','$W')):
    s=s.replace(k,v)
print(s)" > $E/prompts/$W.txt
echo $E/prompts/$W.txt
