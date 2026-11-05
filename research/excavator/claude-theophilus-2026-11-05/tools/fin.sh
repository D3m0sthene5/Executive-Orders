#!/bin/bash
# usage: fin.sh BATCH APPLIED_VERSION -> serialised finish and publish
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/theophilus
cd /home/claude/executive-orders
B=$1; V=$2; P=research/excavator/claude-theophilus-2026-11-05/$B/packet
exec 9>$E/finish.lock; flock 9
python3 -I research/excavator/claude-theophilus-2026-11-05/tools/finish.py $B $P $P/$V --publish > $E/finish-$B.log 2>&1
echo "$B: $(grep -o '"plants_caught": [0-9]*' $E/finish-$B.log) $(grep -o '"claims_published": [0-9]*' $E/finish-$B.log | tail -1) $(grep -o 'missed_controls[^]]*' $E/finish-$B.log)"
