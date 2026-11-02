#!/bin/bash
# usage: prepare.sh BATCH  (repo root). c* batches are replacement proposals; c1 and r1 are NRA (source supplement).
set -e
S=/tmp/claude-0/-home-claude/79a6cc5c-022c-506a-a289-86cc7ef89ecd/scratchpad/erasmus
B=$1; R=research/excavator/claude-erasmus-2026-11-02/$B
IDS=$(python3 -c "import json;print(' '.join(json.load(open('$S/batches.json'))['$B']))")
FLAG=""; [[ $B == c* || $B == e1 || $B == e2 ]] && FLAG="--replacement-proposal"
mkdir -p $R
python3 jobs/claim-kit/kit.py prepare $IDS --agent claude $FLAG --write $R/packet > $S/prep-$B.log 2>&1
if [[ $B == c1 || $B == r1 || $B == e1 ]]; then
  python3 -I research/excavator/claude-nira-sweep-2026-10-29/make_declarations.py $R/packet $R/packet/SUPPLEMENT_DECLARATIONS.json >> $S/prep-$B.log 2>&1
  python3 jobs/claim-kit/source_supplement.py --repo . prepare --parent $R/packet --sources $R/packet/SUPPLEMENT_DECLARATIONS.json --agent claude --write $R/packet/supp >> $S/prep-$B.log 2>&1
  python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/packet/supp >> $S/prep-$B.log 2>&1
else
  python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/packet >> $S/prep-$B.log 2>&1
fi
echo "DONE $B"
