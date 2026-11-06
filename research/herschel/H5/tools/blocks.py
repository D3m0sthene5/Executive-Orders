"""Summarize a packet's dispatch-check source blocks as acquisitions (coordinator tool; no legal judgment).
usage: python3 -I blocks.py PACKET_DIR  -> JSON {dispatchable:[...], blocked:{EO:N: "custody copy of URL; ..."}}"""
import json, sys
d = json.load(open(sys.argv[1] + "/DISPATCH_CHECK.json"))
out = {"dispatchable": d.get("dispatchable_ids", []), "blocked": {}}
for m in d.get("members", []):
    iid = m.get("instrument_id") or m.get("id")
    acq = []
    for b in m.get("blockers", []):
        s = b.get("source") or {}
        what = s.get("url") or s.get("page_or_item") or b.get("kind")
        k = b.get("kind", "")
        acq.append(("custody copy of " if "custody" in k else k + ": ") + str(what))
    if iid in d.get("source_blocked_ids", []):
        out["blocked"][iid] = "; ".join(sorted(set(acq)))[:600]
print(json.dumps(out, ensure_ascii=False, indent=1))
