#!/bin/bash
# usage: reveal.sh WORKER MSGFILE -> resumes one finished reviewer session with a reveal message (guarded, logged).
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5
L=/home/claude/executive-orders/research/herschel/H5/COORDINATOR_LOG.txt; N=$1; M=$2
SID=$(python3 -c "import json;print(json.load(open('$E/run/$N.json'))['session_id'])")
while [ $(pgrep -fc "claude -p") -ge 18 ] || [ $(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo) -le 900 ]; do sleep 20; done
cd $E/run; echo "$N-reveal opus resume $SID launched $(date -u +%FT%TZ)" >> $L
claude -p --resume $SID --permission-mode auto --output-format json "$(cat $M)" > $E/run/$N-reveal.json 2> $E/run/$N-reveal.err
python3 -c "import json;d=json.load(open('$E/run/$N-reveal.json'));print('$N-reveal', d.get('session_id'), 'cost', d.get('total_cost_usd'), 'turns', d.get('num_turns'))" >> $L 2>&1 || echo "$N-reveal RESULT_UNREADABLE" >> $L
echo "$N-reveal done $(date -u +%FT%TZ)" >> $L
