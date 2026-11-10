"""F7 fix 4 reach: orders whose current-law machine_hits_for_this_order changes (old fragment count vs MENTIONS rows).

Usage: python -I measure_machine_hits.py REF_REPO OUT_CSV
Old value = items in the order's current-law FRAGMENTS.jsonl records (predicate leads and event candidates).
New value = every MENTIONS.csv row of that system naming the order. Undecided = not in DECIDED_CASE_COMPLETENESS_RECONCILED.csv.
"""
import collections
import csv
import json
import sys
from pathlib import Path

ref, out = Path(sys.argv[1]), Path(sys.argv[2])
cl = ref / "jobs/current-law/output"
decided = {r["instrument_id"] for r in csv.DictReader(open(ref / "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv", encoding="utf-8", newline=""))}
old = collections.Counter()
for line in open(cl / "FRAGMENTS.jsonl", encoding="utf-8"):
    f = json.loads(line)
    d = f.get("data")
    old[f["instrument_id"]] += len(d) if isinstance(d, list) else (0 if d is None else 1)
rows = collections.Counter()
for r in csv.DictReader(open(cl / "MENTIONS.csv", encoding="utf-8", newline="")):
    rows[(r["system"], r["instrument_id"])] += 1
orders = {i for (_, i) in rows} | set(old)
res = []
for iid in sorted(orders):
    for system in ("usc", "ecfr"):
        n = rows[(system, iid)]
        # the old count is per job, not per system: it is the same number on both searches
        if n != old[iid]:
            res.append({"instrument_id": iid, "undecided": iid not in decided, "system": system, "old_hits": old[iid], "new_hits": n})
with open(out, "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["instrument_id", "undecided", "system", "old_hits", "new_hits"])
    w.writeheader()
    w.writerows(res)
undec = [r for r in res if r["undecided"]]
print(json.dumps({
    "orders_with_any_mentions_row": len({i for (_, i) in rows}),
    "order_searches_whose_count_changes": len(res),
    "of_which_undecided": len(undec),
    "undecided_orders_changed": len({r["instrument_id"] for r in undec}),
    "old_zero_new_positive_undecided_orders": len({r["instrument_id"] for r in undec if r["old_hits"] == 0 and r["new_hits"] > 0}),
    "EO:10195": [r for r in res if r["instrument_id"] == "EO:10195"],
}, indent=1))
