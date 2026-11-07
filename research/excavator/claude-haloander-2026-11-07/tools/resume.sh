#!/bin/bash
# usage: resume.sh NAME SESSION_ID MSGFILE -> one follow-up into an existing headless worker's own context
E=/tmp/claude-0/-home-user-Executive-Orders/b948d1cb-92e5-5ecb-8cbe-fc3fb7b3e2c6/scratchpad/necker
N=$1; SID=$2; P=$3
cd $E/run
echo "$N resume $SID launched $(date -u +%FT%TZ)" >> $E/COORDINATOR_LOG.txt
claude -p --resume $SID --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
python3 -I -c "import json;d=json.load(open('$E/run/$N.json'));print('$N', d.get('session_id'), 'cost', d.get('total_cost_usd'), 'turns', d.get('num_turns'), 'ms', d.get('duration_ms'))" >> $E/COORDINATOR_LOG.txt 2>&1
echo "$N done $(date -u +%FT%TZ)" >> $E/COORDINATOR_LOG.txt
