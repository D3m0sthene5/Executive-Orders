#!/bin/bash
# usage: launch.sh NAME MODEL PROMPTFILE [SESSION_ID] -> one fresh headless Claude Code worker (separate context), run from
# the H3 scratch run folder so jobs/bentham/sessions.py can find its transcript; result JSON in run/NAME.json.
# With SESSION_ID: sends one follow-up message (PROMPTFILE) into that worker's context (after-reveal step).
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H3
L=/home/claude/executive-orders/research/herschel/H3/COORDINATOR_LOG.txt
N=$1; M=$2; P=$3; SID=$4
mkdir -p $E/run $E/running; cd $E/run
C=$(ls $E/running | wc -l); touch $E/running/$N
echo "{\"worker\":\"$N\",\"model\":\"$M\",\"started_utc\":\"$(date -u +%FT%TZ)\",\"concurrent_workers_at_start\":$((C+1)),\"resume\":\"${SID}\"}" >> $E/starts.jsonl
echo "$N $M ${SID:+resume $SID }launched $(date -u +%FT%TZ) concurrent=$((C+1))" >> $L
if [ -n "$SID" ]; then
  claude -p --resume $SID --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
else
  claude -p --model $M --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
fi
rm -f $E/running/$N
python3 -c "import json;d=json.load(open('$E/run/$N.json'));print('$N', d.get('session_id'), 'cost', d.get('total_cost_usd'), 'turns', d.get('num_turns'), 'is_error', d.get('is_error'))" >> $L 2>&1 || echo "$N RESULT_UNREADABLE $(head -c 300 $E/run/$N.err)" >> $L
echo "$N done $(date -u +%FT%TZ)" >> $L
echo "{\"worker\":\"$N\",\"ended_utc\":\"$(date -u +%FT%TZ)\"}" >> $E/ends.jsonl
