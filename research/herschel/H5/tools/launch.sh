#!/bin/bash
# usage: launch.sh NAME MODEL PROMPTFILE  -> one fresh headless Claude Code worker (no fork) run from the H5 scratch
# run folder (so its transcript sits in its own projects/ folder for sessions.py). Records start/end, concurrency at
# start and every limit/overload message (UTC) to the H5 log; on a limit it backs off and resumes the same session.
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5
L=/home/claude/executive-orders/research/herschel/H5/COORDINATOR_LOG.txt
N=$1; M=$2; P=$3
mkdir -p $E/active $E/run; cd $E/run
# shared integrator guard (2026-11-05): launch only if fewer than 18 "claude -p" processes run and MemAvailable > 900 MB;
# otherwise wait 20 s; log MEMGUARD at most once per minute.
guard(){ LG=0; while :; do NP=$(pgrep -fc "claude -p"); MA=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)
  [ $NP -lt 18 ] && [ $MA -gt 900 ] && break
  NOW=$(date +%s); [ $((NOW-LG)) -ge 60 ] && { echo "MEMGUARD $N $(date -u +%FT%TZ) claude_p=$NP avail=${MA}MB" >> $L; LG=$NOW; }; sleep 20; done; }
guard
C=$(ls $E/active | wc -l); touch $E/active/$N
S=$(date -u +%FT%TZ)
echo "$N $M launched $S concurrent_at_start=$C" >> $L
echo "{\"worker\":\"$N\",\"model\":\"$M\",\"started_utc\":\"$S\",\"concurrent_workers_at_start\":$C}" > $E/run/$N.start.json
SID=""; try=0
while :; do
  [ $try -gt 0 ] && guard
  if [ -z "$SID" ]; then
    claude -p --model $M --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
  else
    claude -p --resume $SID --permission-mode auto --output-format json "Continue your assigned task exactly where you left off (an API limit or overload interrupted you). Finish every remaining step, then give the final reply your instructions ask for." > $E/run/$N.json 2> $E/run/$N.err
  fi
  cp $E/run/$N.json $E/run/$N.try$try.json 2>/dev/null
  NEWSID=$(python3 -c "import json;print(json.load(open('$E/run/$N.json')).get('session_id') or '')" 2>/dev/null)
  [ -n "$NEWSID" ] && SID=$NEWSID
  HIT=$(grep -hoiE "[^\"]{0,80}(rate.?limit|usage.?limit|overload|529|too many requests|limit reached|quota)[^\"]{0,80}" $E/run/$N.err $E/run/$N.json 2>/dev/null | head -3)
  ERR=$(python3 -c "import json;d=json.load(open('$E/run/$N.json'));print('1' if d.get('is_error') else '')" 2>/dev/null || echo 1)
  if [ ! -s $E/run/$N.json ] && [ $try -lt 8 ]; then
    T=$(date -u +%FT%TZ); echo "KILLED $N $T try=$try: empty result (host OOM killer; dmesg: $(dmesg 2>/dev/null | grep -c 'Killed process') kills so far); retrying" >> $L
    echo "{\"worker\":\"$N\",\"utc\":\"$T\",\"try\":$try,\"message\":\"empty result: process killed (host memory cgroup OOM)\"}" >> $E/run/LIMITS.jsonl
    try=$((try+1)); sleep $((60*try + RANDOM % 60))
    guard; continue
  fi
  if [ -n "$ERR" ] && [ -n "$HIT" ] && [ $try -lt 8 ]; then
    T=$(date -u +%FT%TZ); echo "LIMIT $N $T try=$try: $(echo $HIT | tr '\n' ' ' | cut -c1-400)" >> $L
    echo "{\"worker\":\"$N\",\"utc\":\"$T\",\"try\":$try,\"message\":$(python3 -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$HIT")}" >> $E/run/LIMITS.jsonl
    try=$((try+1)); sleep $((90*try)); continue
  fi
  break
done
rm -f $E/active/$N
python3 -c "import json;d=json.load(open('$E/run/$N.json'));print('$N', d.get('session_id'), 'cost', d.get('total_cost_usd'), 'turns', d.get('num_turns'), 'is_error', d.get('is_error'))" >> $L 2>&1 || echo "$N RESULT_UNREADABLE $(head -c 300 $E/run/$N.err)" >> $L
echo "$N done $(date -u +%FT%TZ)" >> $L
