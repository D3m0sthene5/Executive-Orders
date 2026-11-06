#!/bin/bash
# usage: launch.sh NAME MODEL PROMPTFILE [RESUME_SESSION_ID]
# One fresh headless Claude Code worker (separate context) run from the H2 scratch run folder so jobs/bentham/sessions.py
# finds its transcript. Result JSON in run/NAME.json; start/end/concurrency in run/NAME.meta.json. Coordinator tool.
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H2
L=/home/claude/executive-orders/research/herschel/H2/COORDINATOR_LOG.txt
N=$1; M=$2; P=$3; SID=$4
cd $E/run
# MEMGUARD (integrator, 2026-11-06): launch only if fewer than 18 'claude -p' processes and MemAvailable > 900 MB;
# otherwise wait 20 s and recheck; log a deferral at most once per minute.
LAST=0
while true; do
  NP=$(pgrep -fc "claude -p"); MA=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)
  if [ "$NP" -lt 18 ] && [ "$MA" -gt 900 ]; then break; fi
  NOW=$(date +%s); if [ $((NOW-LAST)) -ge 60 ]; then echo "MEMGUARD $(date -u +%FT%TZ): $N deferred (claude -p=$NP, MemAvailable=${MA}MB)" >> $L; LAST=$NOW; fi
  sleep 20
done
C=$(ls $E/run/*.running 2>/dev/null | wc -l)
touch $E/run/$N.running
ST=$(date -u +%FT%TZ)
echo "$N $M ${SID:+resume $SID }launched $ST concurrent_before=$C" >> $L
if [ -n "$SID" ]; then
  claude -p --resume $SID --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
else
  claude -p --model $M --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
fi
EN=$(date -u +%FT%TZ)
rm -f $E/run/$N.running
python3 - "$E/run/$N.json" "$E/run/$N.meta.json" "$N" "$M" "$ST" "$EN" "$C" "$SID" <<'PY' >> $L 2>&1
import json,sys
p,mp,n,m,st,en,c,sid=sys.argv[1:9]
try: d=json.load(open(p))
except Exception as e: d={"parse_error":str(e)}
meta={"worker":n,"model":m,"started_utc":st,"ended_utc":en,"concurrent_workers_at_start":int(c),"resume_of":sid or None,
      "session_id":d.get("session_id"),"cost_reported":d.get("total_cost_usd"),"turns":d.get("num_turns"),"is_error":d.get("is_error"),
      "result_head":(d.get("result") or "")[:600]}
json.dump(meta,open(mp,"w"),indent=1)
print(n,meta["session_id"],"cost",meta["cost_reported"],"turns",meta["turns"],"error",meta["is_error"],"done",en)
PY
