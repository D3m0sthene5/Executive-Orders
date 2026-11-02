#!/bin/bash
# usage: fin.sh BATCH APPLIED_VERSION -> serialised finish+publish
E=/tmp/claude-0/-home-claude/79a6cc5c-022c-506a-a289-86cc7ef89ecd/scratchpad/erasmus
cd /home/claude/executive-orders
B=$1; V=$2
if [[ $B == c1 || $B == r1 || $B == e1 ]]; then P=research/excavator/claude-erasmus-2026-11-02/$B/packet/supp; else P=research/excavator/claude-erasmus-2026-11-02/$B/packet; fi
exec 9>$E/finish.lock; flock 9
python3 -I $E/erasmus_finish.py $B $P $P/$V --publish > $E/finish-$B.log 2>&1
echo "$B: $(grep -o '"plants_caught": [0-9]*' $E/finish-$B.log) $(grep -o '"claims_published": [0-9]*' $E/finish-$B.log | tail -1) $(grep -o 'missed_controls[^]]*' $E/finish-$B.log)"
