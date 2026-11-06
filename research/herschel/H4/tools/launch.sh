#!/bin/bash
# usage: launch.sh NAME MODEL PROMPTFILE [SESSION_ID]  -> one fresh headless worker (or one resume); waits for a free
# slot: H4 cap 16 AND integrator guard (pgrep -fc "claude -p" < 18 AND MemAvailable > 900 MB), logging every wait. Result JSON in run/NAME.json.
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4
L=/home/claude/executive-orders/research/herschel/H4/COORDINATOR_LOG.txt
N=$1; M=$2; P=$3; SID=$4; mkdir -p $E/run $E/slots
waited=0; lastlog=0
while true; do
  exec 8>$E/slot.lock; flock 8
  busy=$(ls $E/slots | wc -l); mem=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo); allp=$(pgrep -fc "claude -p")
  if [ $busy -lt 16 ] && [ $allp -lt 18 ] && [ $mem -gt 900 ]; then echo "$N" > $E/slots/$N; flock -u 8; break; fi
  flock -u 8
  now=$(date +%s); if [ $((now-lastlog)) -ge 60 ]; then echo "MEMGUARD $N $(date -u +%FT%TZ) h4_busy=$busy claude_p_all=$allp memavail=${mem}MB" >> $L; lastlog=$now; fi
  waited=1; sleep 20
done
[ $waited -eq 1 ] && echo "GATE-PASS $N $(date -u +%FT%TZ)" >> $L
echo "$N $M ${SID:+resume $SID }launched $(date -u +%FT%TZ) h4_concurrent=$busy claude_p_all=$allp memavail=${mem}MB" >> $L
cd $E/run
if [ -n "$SID" ]; then
  claude -p --resume $SID --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
else
  claude -p --model $M --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
fi
rc=$?
rm -f $E/slots/$N
python3 -c "import json;d=json.load(open('$E/run/$N.json'));print('$N', d.get('session_id'), 'cost', d.get('total_cost_usd'), 'turns', d.get('num_turns'), 'is_error', d.get('is_error'), 'subtype', d.get('subtype'))" >> $L 2>&1 || echo "$N RESULT-UNREADABLE rc=$rc" >> $L
{ cat $E/run/$N.err; python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(d.get(\"result\",\"\")[:4000] if d.get(\"is_error\") else \"\")" $E/run/$N.json 2>/dev/null; } | grep -i -E "rate.?limit|overload|usage limit|api error|quota|Killed|out of memory" | head -3 | sed "s/^/LIMIT-EVENT $N $(date -u +%FT%TZ) /" >> $L
echo "$N done $(date -u +%FT%TZ) rc=$rc" >> $L
