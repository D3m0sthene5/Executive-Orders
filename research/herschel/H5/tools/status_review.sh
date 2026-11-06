#!/bin/bash
# usage: status_review.sh BATCH WA WB "EO:a EO:b ..."  -> plants one control, renders and launches two blind Opus status reviewers
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5
R=/home/claude/executive-orders; T=$R/research/herschel/H5/tools; L=$R/research/herschel/H5/COORDINATOR_LOG.txt
B=$1; WA=$2; WB=$3; ORDERS=$4; P=$R/research/herschel/H5/packets/$B/packet
cd $R; echo "status-plant $B $(python3 -I $T/status_plant.py $B $ORDERS 2>&1 | tail -1)" >> $L
for arm in A B; do W=$WA; [ $arm = B ] && W=$WB; mkdir -p /tmp/claude-0/herschel-H5/$W
 sed -e "s#WORKER#$W#g" -e "s#ORDERLIST#$(echo $ORDERS | sed 's/ /, /g')#" -e "s#REVIEWDIR#$E/review/status-$B#g" -e "s#PACKETPATH#$P#g" -e "s#BATCH#$B#g" -e "s#ARM#$arm#g" $T/prompt_status_review.txt > $E/prompts/$W.txt
 printf "$W\treview_status\topus\t-\t$B\t$ORDERS\n" >> $E/WORKERS.tsv
 (nohup bash $T/launch.sh $W opus $E/prompts/$W.txt > /dev/null 2>&1 &)
done
