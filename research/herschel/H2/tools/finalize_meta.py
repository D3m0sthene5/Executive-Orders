"""Write run/NAME.meta.json for a worker whose launch.sh post-processing broke (coordinator tool).
usage: python3 -I finalize_meta.py NAME MODEL STARTED_UTC CONCURRENT_BEFORE RESUME_SID"""
import json, sys, os, datetime
from pathlib import Path
E = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H2/run")
n, m, st, c, sid = sys.argv[1:6]
d = json.load(open(E / f"{n}.json"))
en = datetime.datetime.fromtimestamp(os.path.getmtime(E / f"{n}.json"), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
meta = {"worker": n, "model": m, "started_utc": st, "ended_utc": en, "concurrent_workers_at_start": int(c), "resume_of": sid or None,
        "session_id": d.get("session_id"), "cost_reported": d.get("total_cost_usd"), "turns": d.get("num_turns"),
        "is_error": d.get("is_error"), "result_head": (d.get("result") or "")[:600], "note": "meta written by finalize_meta.py (launch.sh edited while running)"}
json.dump(meta, open(E / f"{n}.meta.json", "w"), indent=1)
(E / f"{n}.running").unlink(missing_ok=True)
print(n, meta["session_id"], meta["cost_reported"], meta["turns"], en)
