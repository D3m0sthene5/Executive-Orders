#!/bin/bash
# usage: prepare_retry.sh BATCH -> runs prepare.sh; while the kit refuses a member with "no dated history located for EO:X",
# drops X from the batch (recorded in tools/DROPPED.tsv with the kit's message) and retries. Coordinator tool.
S=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5
R=/home/claude/executive-orders; H=$R/research/herschel/H5; B=$1; cd $R
for i in $(seq 1 8); do
  rm -rf $H/packets/$B/packet; bash $H/tools/prepare.sh $B > /dev/null
  [ -f $H/packets/$B/packet/PACKET.json ] && { echo "OK $B"; exit 0; }
  X=$(grep -o "no dated history located for EO:[^ ]*" $S/prep-$B.log | head -1 | sed 's/.*for //')
  [ -z "$X" ] && { echo "FAIL $B $(grep -m1 -i error $S/prep-$B.log)"; exit 1; }
  printf "$B\t$X\tclaim-kit: no dated history located for $X\t$(date -u +%FT%TZ)\n" >> $H/tools/DROPPED.tsv
  python3 - $H/tools/batches.json $B "$X" <<'PY'
import json,sys
p,b,x=sys.argv[1:]; d=json.load(open(p)); d[b]=[o for o in d[b] if o!=x]; json.dump(d,open(p,'w'),indent=1,ensure_ascii=False)
PY
  python3 -c "import json;import sys;sys.exit(0 if json.load(open('$H/tools/batches.json'))['$B'] else 1)" || { echo "EMPTY $B"; exit 0; }
done
