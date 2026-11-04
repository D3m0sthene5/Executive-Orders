#!/bin/bash
# usage: fin.sh BATCH APPLIED_VERSION -> serialised finish and publish
E=/tmp/claude-0/-home-claude/113ce3b2-4ba3-50df-9241-eb6576e0f367/scratchpad/tribonian
cd /home/claude/executive-orders
B=$1; V=$2; P=research/excavator/claude-tribonian-2026-11-04/$B/packet
exec 9>$E/finish.lock; flock 9
python3 -I research/excavator/claude-tribonian-2026-11-04/tools/finish.py $B $P $P/$V --publish > $E/finish-$B.log 2>&1
echo "$B: $(grep -o '"plants_caught": [0-9]*' $E/finish-$B.log) $(grep -o '"claims_published": [0-9]*' $E/finish-$B.log | tail -1) $(grep -o 'missed_controls[^]]*' $E/finish-$B.log)"
