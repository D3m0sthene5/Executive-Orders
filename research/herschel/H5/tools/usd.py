"""Price a sessions.py output as jobs/bentham/measure.py prices tokens (coordinator tool).
usage: python3 -I usd.py SESSIONS_OUT_DIR -> total and per-agent USD (cache writes 5m+1h+unclassified count as cache_write)."""
import csv, importlib.util, json, sys
spec = importlib.util.spec_from_file_location("measure", "/home/claude/executive-orders/jobs/bentham/measure.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rows = list(csv.DictReader(open(sys.argv[1] + "/AGENT_USAGE.csv")))
def n(x):
    try: return int(float(x or 0))
    except ValueError: return 0
tot = 0; per = {}
for r in rows:
    mod = (r.get("model") or "").lower(); fam = "opus" if "opus" in mod else "sonnet" if "sonnet" in mod else "opus"
    tok = {"fresh_input": n(r.get("fresh_input")), "output": n(r.get("output")), "cache_read": n(r.get("cache_read")),
           "cache_write": n(r.get("cache_write_5m")) + n(r.get("cache_write_1h")) + n(r.get("cache_write_unclassified"))}
    u = m.usd(fam, tok); tot += u
    per[(r.get("session_id") or r.get("agent_id") or "?")] = round(u, 3)
print(json.dumps({"total_usd": round(tot, 2), "agents": len(rows)}))
if len(sys.argv) > 2: print(json.dumps(per, indent=0))
