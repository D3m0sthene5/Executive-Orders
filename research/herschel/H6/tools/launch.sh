#!/bin/bash
# usage: launch.sh NAME MODEL PROMPTFILE [SESSION_ID]  -> one fresh headless Claude Code worker (separate context)
# run from the H6 scratch run/ folder (unique transcript project dir). Result JSON in run/NAME.json; one line per run
# in run/LAUNCHES.jsonl with start/end UTC, concurrency at start, cost, session and any limit/overload text seen.
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H6
N=$1; M=$2; P=$3; SID=$4; L=/home/claude/executive-orders/research/herschel/H6/COORDINATOR_LOG.txt
cd $E/run
T0=$(date -u +%FT%TZ); touch $E/run/$N.running
CONC=$(ls $E/run/*.running 2>/dev/null | wc -l)
echo "$N $M ${SID:+resume $SID }launched $T0 concurrent=$CONC" >> $L
TRY=0
while :; do
  if [ -n "$SID" ]; then
    claude -p --resume $SID --permission-mode auto --output-format json "$(cat $P)" < /dev/null > $E/run/$N.json 2> $E/run/$N.err; RC=$?
  else
    claude -p --model $M --permission-mode auto --output-format json "$(cat $P)" < /dev/null > $E/run/$N.json 2> $E/run/$N.err; RC=$?
  fi
  LIM=$(grep -ihoE ".{0,80}(rate.?limit|usage.?limit|overloaded|too many requests|limit reached|API Error: ?(429|529)|"status": ?(429|529)|status code (429|529)).{0,120}" $E/run/$N.err $E/run/$N.json 2>/dev/null | head -5)
  if [ -n "$LIM" ]; then echo "{\"worker\":\"$N\",\"utc\":\"$(date -u +%FT%TZ)\",\"text\":$(printf '%s' "$LIM" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')}" >> $E/run/LIMITS.jsonl; echo "LIMIT $N $(date -u +%FT%TZ): $LIM" >> $L; fi
  ERR=$(python3 -c "import json;d=json.load(open('$E/run/$N.json'));print(1 if d.get('is_error') else 0)" 2>/dev/null || echo 1)
  if [ "$ERR" = 1 ] && [ -n "$LIM" ] && [ $TRY -lt 6 ]; then TRY=$((TRY+1)); cp $E/run/$N.json $E/run/$N.try$TRY.json 2>/dev/null; sleep $((120*TRY)); 
    S2=$(python3 -c "import json;print(json.load(open('$E/run/$N.json')).get('session_id') or '')" 2>/dev/null); [ -n "$S2" ] && SID=$S2 && P=$E/prompts/continue.txt; continue; fi
  break
done
T1=$(date -u +%FT%TZ); rm -f $E/run/$N.running
python3 - "$E/run/$N.json" "$N" "$M" "$T0" "$T1" "$CONC" >> $E/run/LAUNCHES.jsonl <<'PY'
import json,sys
f,n,m,t0,t1,c=sys.argv[1:]
try: d=json.load(open(f))
except Exception as e: d={"parse_error":str(e)}
print(json.dumps({"worker":n,"model":m,"started_utc":t0,"ended_utc":t1,"concurrent_at_start":int(c),"session_id":d.get("session_id"),
 "cost":d.get("total_cost_usd"),"turns":d.get("num_turns"),"is_error":d.get("is_error"),"result":(d.get("result") or "")[:600]}))
PY
[ ! -s $E/run/$N.json ] && echo "{\"worker\":\"$N\",\"utc\":\"$T1\",\"text\":\"worker process exited rc=$RC with no output (machine memory OOM kill suspected; see dmesg)\"}" >> $E/run/LIMITS.jsonl
echo "$N done $T1 rc=$RC cost $(python3 -c "import json;print(json.load(open('$E/run/$N.json')).get('total_cost_usd'))" 2>/dev/null)" >> $L
