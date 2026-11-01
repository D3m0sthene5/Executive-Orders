#!/bin/bash
# usage: moon_fin.sh BATCH [APPLIED]  -> serialised finish+publish (flock), log to scratch/moon-finish-BATCH.log
S=/tmp/claude-0/-home-claude/79a6cc5c-022c-506a-a289-86cc7ef89ecd/scratchpad
cd /home/claude/executive-orders
B=$1; V=${2:-applied-v1}
if [[ $B == n* || $B == g01 || $B == g02 ]]; then P=research/excavator/claude-apollo-2026-10-31/$B/packet/supp; else P=research/excavator/claude-apollo-2026-10-31/$B/packet; fi
exec 9>$S/moon-finish.lock; flock 9
python3 -I $S/moon_finish.py $B $P $P/$V --publish > $S/moon-finish-$B.log 2>&1
echo "$B: $(grep -o '"plants_caught": [0-9]*' $S/moon-finish-$B.log) $(grep -o '"claims_published": [0-9]*' $S/moon-finish-$B.log | tail -1) $(grep -o 'missed_controls[^]]*' $S/moon-finish-$B.log)"
