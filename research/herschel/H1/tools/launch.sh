#!/bin/bash
# usage: launch.sh NAME MODEL PROMPTFILE [SESSION_ID]  -> one fresh headless Claude Code worker (separate context),
# run from the H1 scratch run folder so jobs/bentham/sessions.py finds its transcript under one project.
# Result JSON in run/NAME.json; launch/finish lines in scratch LAUNCH_LOG.txt (copied to COORDINATOR_LOG at the end).
# Shared memory guard (integrator, 2026-11-06): launch only if fewer than 18 "claude -p" processes run AND
# MemAvailable > 900 MB; else wait 20 s (MEMGUARD logged at most once a minute). A worker killed by SIGKILL (OOM)
# is re-run once; its first attempt is kept as NAME.attempt1.json and logged OOM_RERUN.
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H1
N=$1; M=$2; P=$(realpath "$3"); SID=$4
mkdir -p $E/run; cd $E/run
guard() {
  local last=0
  while true; do
    local procs=$(pgrep -fc "claude -p")
    local mem=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
    if [ "$procs" -lt 18 ] && [ "$mem" -gt 900 ]; then break; fi
    local now=$(date +%s)
    if [ $((now - last)) -ge 60 ]; then
      echo "MEMGUARD $N deferred $(date -u +%FT%TZ) claude_p=$procs mem_available_mb=$mem" >> $E/LAUNCH_LOG.txt; last=$now
    fi
    sleep 20
  done
}
for attempt in 1 2; do
  guard
  RUNNING=$(ls $E/run/*.running 2>/dev/null | wc -l)
  touch $E/run/$N.running
  echo "$N $M ${SID:+resume $SID }launched $(date -u +%FT%TZ) concurrent_at_start=$RUNNING" >> $E/LAUNCH_LOG.txt
  if [ -n "$SID" ]; then
    claude -p --resume $SID --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
  else
    claude -p --model $M --permission-mode auto --output-format json "$(cat $P)" > $E/run/$N.json 2> $E/run/$N.err
  fi
  RC=$?
  rm -f $E/run/$N.running
  if [ $RC -eq 137 ] || [ $RC -eq 9 ]; then
    echo "OOM_RERUN $N attempt $attempt rc=$RC $(date -u +%FT%TZ)" >> $E/LAUNCH_LOG.txt
    mv $E/run/$N.json $E/run/$N.attempt$attempt.json 2>/dev/null; mv $E/run/$N.err $E/run/$N.attempt$attempt.err 2>/dev/null
    continue
  fi
  break
done
python3 -c "import json;d=json.load(open('$E/run/$N.json'));print('$N', d.get('session_id'), 'cost', d.get('total_cost_usd'), 'turns', d.get('num_turns'), 'is_error', d.get('is_error'), 'subtype', d.get('subtype'))" >> $E/LAUNCH_LOG.txt 2>&1
echo "$N done $(date -u +%FT%TZ) rc=$RC" >> $E/LAUNCH_LOG.txt
