#!/bin/bash
# usage: resume.sh NAME SESSION_ID MESSAGEFILE -> sends one follow-up to an existing headless worker (same context)
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/icecore
N=$1; SID=$2; P=$3
cd $E/run
echo "$N resumed $(date -u +%FT%TZ) session $SID" >> $E/COORDINATOR_LOG.txt
claude -p --resume $SID --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
python3 -c "import json;d=json.load(open('$E/run/$N.json'));print('$N', d.get('session_id'), 'cost', d.get('total_cost_usd'), 'turns', d.get('num_turns'))" >> $E/COORDINATOR_LOG.txt 2>&1
echo "$N done $(date -u +%FT%TZ)" >> $E/COORDINATOR_LOG.txt
