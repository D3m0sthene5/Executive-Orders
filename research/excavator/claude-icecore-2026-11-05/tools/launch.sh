#!/bin/bash
# usage: launch.sh NAME MODEL PROMPTFILE -> runs one fresh headless Claude Code worker (separate context) from the
# icecore run folder so its transcript is discoverable by jobs/bentham/sessions.py; result JSON in run/NAME.json.
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/icecore
N=$1; M=$2; P=$3
cd $E/run
echo "$N $M launched $(date -u +%FT%TZ)" >> $E/COORDINATOR_LOG.txt
claude -p --model $M --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
python3 -c "import json;d=json.load(open('$E/run/$N.json'));print('$N', d.get('session_id'), 'cost', d.get('total_cost_usd'), 'turns', d.get('num_turns'))" >> $E/COORDINATOR_LOG.txt 2>&1
echo "$N done $(date -u +%FT%TZ)" >> $E/COORDINATOR_LOG.txt
