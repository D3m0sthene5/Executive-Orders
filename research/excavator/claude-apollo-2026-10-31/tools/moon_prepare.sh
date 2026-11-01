#!/bin/bash
# usage: moon_prepare.sh BATCH   (run from repo root)
set -e
S=/tmp/claude-0/-home-claude/79a6cc5c-022c-506a-a289-86cc7ef89ecd/scratchpad
B=$1; R=research/excavator/claude-apollo-2026-10-31/$B
IDS=$(python3 -c "import json;print(' '.join(json.load(open('$S/moon_batches.json'))['$B']))")
mkdir -p $R
python3 jobs/claim-kit/kit.py prepare $IDS --agent claude --write $R/packet > $S/prep-$B.log 2>&1
if [[ $B == n* ]]; then
  python3 -I research/excavator/claude-nira-sweep-2026-10-29/make_declarations.py $R/packet $R/packet/SUPPLEMENT_DECLARATIONS.json >> $S/prep-$B.log 2>&1
  python3 jobs/claim-kit/source_supplement.py --repo . prepare --parent $R/packet --sources $R/packet/SUPPLEMENT_DECLARATIONS.json --agent claude --write $R/packet/supp >> $S/prep-$B.log 2>&1
  python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/packet/supp >> $S/prep-$B.log 2>&1
else
  python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups $R/packet >> $S/prep-$B.log 2>&1
fi
echo "DONE $B"
