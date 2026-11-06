#!/bin/bash
# usage: run_step.sh WORKER STEP BATCH "EO:a EO:b" [FINALIZE_FILE]  (coordinator tool; no legal judgment)
# fresh dispatch-check for the explicit members, render the production prompt for one step, launch one Sonnet worker.
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5
R=/home/claude/executive-orders; T=$R/research/herschel/H5/tools; L=$R/research/herschel/H5/COORDINATOR_LOG.txt
W=$1; STEP=$2; B=$3; ORDERS=$4; FIN=$5; P=$R/research/herschel/H5/packets/$B/packet
cd $R; mkdir -p $P/STEP_NOTES /tmp/claude-0/herschel-H5/$W
OPTS=""; for o in $ORDERS; do OPTS="$OPTS --order $o"; done
flock /tmp/claude-0/herschel-H5/heavy.lock python3 jobs/claim-kit/kit.py dispatch-check $P $OPTS --write $P/dispatch-$W.json > $E/logs/dispatch-$W.log 2>&1
echo "dispatch-check $W $B exit=$? $(date -u +%FT%TZ)" >> $L
RULES=$(cat $T/steps/$STEP.txt); [ -n "$FIN" ] && RULES="$RULES $(cat $T/steps/$FIN.txt)"
python3 - "$T/prompt_production.txt" "$E/prompts/$W.txt" "$W" "$STEP" "$ORDERS" "$P" "$RULES" <<'PY'
import sys
t=open(sys.argv[1]).read()
rules=sys.argv[7].replace("PACKETPATH",sys.argv[6])
t=t.replace("STEPRULES",rules).replace("WORKER",sys.argv[3]).replace("ASSIGNEDLIST",", ".join(sys.argv[5].split())).replace("PACKETPATH",sys.argv[6]).replace("THESTEP",sys.argv[4])
open(sys.argv[2],"w").write(t)
PY
printf "$W\t$STEP\tsonnet\t-\t$B\t$ORDERS\n" >> $E/WORKERS.tsv
bash $T/launch.sh $W sonnet $E/prompts/$W.txt
