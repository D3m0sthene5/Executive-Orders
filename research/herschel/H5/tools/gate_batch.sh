#!/bin/bash
# usage: gate_batch.sh BATCH ATTEMPTED SUBMITTED FILED MISSED "W1 W2 ..." -> appends to BATCHES.json (usd = sum of the
# listed workers' final total_cost_usd, reveals included) and runs the Bentham gate; output kept in gate/. Coordinator tool.
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5; H=/home/claude/executive-orders/research/herschel/H5
B=$1; mkdir -p $H/gate
python3 - $H/BATCHES.json "$@" <<'PY'
import json, os, sys
p, b, att, sub, fil, mis, ws = sys.argv[1:8]
E = "/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5/run"
usd = 0.0
for w in ws.split():
    for f in (f"{E}/{w}-reveal.json", f"{E}/{w}.json"):   # a resumed session's total includes the first run
        if os.path.exists(f) and os.path.getsize(f):
            usd += json.load(open(f)).get("total_cost_usd") or 0; break
rows = json.load(open(p)) if os.path.exists(p) else []
rows.append({"batch": b, "attempted": int(att), "submitted": int(sub), "filed": int(fil), "controls_missed": int(mis), "usd": round(usd, 2)})
json.dump(rows, open(p, "w"), indent=1)
PY
cd /home/claude/executive-orders && python3 -I jobs/bentham/gate.py --batches $H/BATCHES.json --prior-rate 0.3 --cost-per-attempt 2 --next-best 0.5 --window 2 > $H/gate/gate-$B.txt 2>&1
echo "GATE $B $(head -c 300 $H/gate/gate-$B.txt | tr '\n' ' ')" >> $H/COORDINATOR_LOG.txt; cat $H/gate/gate-$B.txt | head -20
