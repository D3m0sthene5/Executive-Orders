#!/bin/bash
# usage: launch.sh NAME MODEL PROMPTFILE -> one fresh headless Claude Code worker (separate context, no fork) run from
# the Theophilus scratch folder so jobs/bentham/sessions.py can find its transcript; result JSON in run/NAME.json.
# resume: launch.sh NAME MODEL MSGFILE SESSION_ID  (sends one follow-up into the same worker's context)
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/theophilus
N=$1; M=$2; P=$3; SID=$4
cd $E/run
echo "$N $M ${SID:+resume $SID }launched $(date -u +%FT%TZ)" >> $E/COORDINATOR_LOG.txt
if [ -n "$SID" ]; then
  claude -p --resume $SID --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
else
  claude -p --model $M --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
fi
python3 -c "import json;d=json.load(open('$E/run/$N.json'));print('$N', d.get('session_id'), 'cost', d.get('total_cost_usd'), 'turns', d.get('num_turns'))" >> $E/COORDINATOR_LOG.txt 2>&1
echo "$N done $(date -u +%FT%TZ)" >> $E/COORDINATOR_LOG.txt
