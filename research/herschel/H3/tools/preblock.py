"""Fill coordinator 'blocked' rows in a packet's decisions.csv for members that failed dispatch-check (no legal judgment).
usage: python3 -I preblock.py PACKET DISPATCH_JSON EO:N [EO:N ...]"""
import csv, json, sys
pk, dj, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
d = json.load(open(dj))
why = {}
for m in d["members"]:
    if m["instrument_id"] in ids:
        bl = m.get("blockers", [])
        why[m["instrument_id"]] = "; ".join(sorted({f"{b.get('kind')} {b.get('evidence_id')} ({(b.get('source') or {}).get('page_or_item','')}): " +
                                                    ",".join(c.get('status','') for c in b.get('checks', [])) for b in bl}))
rows = list(csv.DictReader(open(pk + "/decisions.csv", encoding="utf-8")))
f = rows[0].keys()
for r in rows:
    if r["instrument_id"] in ids:
        r["outcome"] = "blocked"
        r["unresolved_material_gaps"] = json.dumps(["Coordinator dispatch-check block before assignment: " + why[r["instrument_id"]] +
                                                    ". Unblock by retaining the exact cited raw source bytes."])
with open(pk + "/decisions.csv", "w", encoding="utf-8", newline="") as o:
    w = csv.DictWriter(o, fieldnames=list(f)); w.writeheader(); w.writerows(rows)
print(json.dumps(why, indent=1))
