"""Print the tables REPORT.md quotes, from SUMMARY.json. Usage: py -I tables.py [path to SUMMARY.json]"""

import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "SUMMARY.json"), encoding="utf-8"))


def table(title, d, total=None):
    print(f"\n**{title}**\n")
    print("| | Orders |\n|---|---:|")
    for k, v in sorted(d.items(), key=lambda kv: -kv[1]):
        print(f"| {k} | {v:,} |")
    if total is not None:
        print(f"| **Total** | **{total:,}** |")


print("commit", S["commit"])
table("Categories", S["category"], sum(S["category"].values()))
table("Categories if A-20261106-1 is adopted", S["category_if_A_20261106_1_adopted"])
for c, d in S["category_by_evidence"].items():
    table(f"{c}, by evidence", d, sum(d.values()))
table("Category 1, weakest side", S["both_sides_level"])
for k in ("share_all_formally_revoked", "share_formal_held_verified", "share_formally_revoked_with_filed_claim"):
    print(k, S[k])
print("formally revoked with claim, by category", S["formally_revoked_with_claim_by_category"])
for c, d in S["routes_of_earlier_end"].items():
    table(f"Routes: {c}", d, sum(d.values()))
for k in ("gap_days_all", "gap_days_filed_claim", "gap_days_both_held_verified"):
    g = S[k]
    print(f"\n{k}: n={g['n']} min={g['min']} p25={g['p25']} median={g['median']} p75={g['p75']} max={g['max']}"
          f" (median {g['median'] / 365.25:.1f} years)")
    print("  " + ", ".join(f"{b}: {n}" for b, n in g["bins"].items()))
print("\nrevokers in category 1", S["formal_revoker_top_in_category1"])
print("by era", json.dumps(S["by_era"], indent=1))
print("stage 15 sample", S["stage15_sample"])
table("Blocker flags (all rows)", S["blocker_flags_all_rows"])
print("\nblockers", json.dumps(S["blockers"], indent=1)[:6000])
print("tracker fix (claim-only rule)", S["tracker_fix_claim_only_rule"])
