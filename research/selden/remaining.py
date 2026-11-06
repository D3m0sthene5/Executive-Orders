"""Which acting instruments Selden now supplies, and the ranked table of those still missing.

Reads research/selden/census/ACTING_INSTRUMENTS.csv and ORDER_NEEDS.csv (census.py) and the Selden job outputs on
this checkout; writes research/selden/census/SUPPLIED.csv and research/selden/REMAINING.csv. Zero tokens.
"""
import collections
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent / "census"
LANES = {"executive_order": "order-originals lane (fr-originals, Tischendorf, Mabillon)",
         "executive_order_unnumbered": "order-originals lane", "public_land_order": "selden-fr-acting",
         "proclamation": "selden-fr-acting (1936-93 FR) / selden-statutes (Stat. volumes)",
         "statute": "selden-statutes", "statute_or_agency_act": "selden-statutes / selden-fr-acting",
         "agency_document": "selden-fr-acting", "presidential_notice": "theophilus-sources (1994 on) / selden-fr-acting",
         "reorganization_plan": "selden-statutes (printed in Stat.)", "treaty": "selden-statutes (Stat. to 1948)",
         "presidential_memorandum": "selden-fr-citers (1994 on)", "presidential_determination": "selden-fr-citers"}


def read_jsonl(p):
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    inst = list(csv.DictReader(open(C / "ACTING_INSTRUMENTS.csv", encoding="utf-8")))
    needs = {r["instrument_id"]: r for r in csv.DictReader(open(C / "ORDER_NEEDS.csv", encoding="utf-8"))}
    held = collections.defaultdict(set)   # actor -> jobs holding its text
    located = collections.defaultdict(set)  # actor -> targets with a located acting sentence
    for job in ("selden-fr-acting", "selden-statutes", "selden-fr-citers"):
        out = ROOT / "jobs" / job / "output"
        for s in read_jsonl(out / "SOURCES.jsonl"):
            ids = s.get("instrument_ids") or []
            if ids:
                held[ids[0]].add(job)
        for f in read_jsonl(out / "FRAGMENTS.jsonl"):
            for d in f.get("data") or []:
                if d.get("mechanism") not in ("cross_reference", None):
                    located[d["acting_id"]].add(d["target_id"])
    # selden-statutes keys statutes by STAT:vol-page; the census by PL:/STAT: ids. Map STAT ids from labels.
    stat_alias = {}
    for r in inst:
        m = re.search(r"\b(\d{1,3}) Stat\.? (\d{1,5})", r["label"])
        if m:
            stat_alias[r["actor"]] = f"STAT:{m.group(1)}-{m.group(2)}"
    supplied, remaining = [], []
    for r in inst:
        a = r["actor"]
        if r["holding"] in ("held_official", "held_official_page"):
            continue
        keys = {a, stat_alias.get(a, a)}
        jobs = set().union(*(held.get(k, set()) for k in keys))
        locs = set().union(*(located.get(k, set()) for k in keys))
        row = dict(r, now_held_by="|".join(sorted(jobs)), targets_with_located_acting_sentence=len(locs),
                   route=LANES.get(r["type"], "unassigned"))
        (supplied if jobs else remaining).append(row)
    cols = ["actor", "type", "era", "holding", "fr", "orders_ending", "orders_modifying", "orders_acted_on",
            "orders_pop_S", "now_held_by", "targets_with_located_acting_sentence", "route", "label"]
    supplied.sort(key=lambda x: (-int(x["orders_acted_on"]), x["actor"]))
    remaining.sort(key=lambda x: (-int(x["orders_pop_S"]), -int(x["orders_acted_on"]), x["actor"]))
    for path, rows in ((C / "SUPPLIED.csv", supplied), (Path(__file__).resolve().parent / "REMAINING.csv", remaining)):
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    pop_s = {o for o, r in needs.items() if r["pop_S"] == "yes"}
    def orders(rows):
        out = set()
        for r in rows:
            out |= set(filter(None, r["targets_ending_sample"].split("|")))
        return out
    summary = {
        "unheld_instruments": len(supplied) + len(remaining), "now_supplied": len(supplied),
        "still_missing": len(remaining),
        "supplied_by_type": dict(collections.Counter(r["type"] for r in supplied).most_common()),
        "missing_by_type": dict(collections.Counter(r["type"] for r in remaining).most_common()),
        "missing_by_route": dict(collections.Counter(r["route"] for r in remaining).most_common()),
        "orders_acted_on_by_supplied": sum(int(r["orders_acted_on"]) for r in supplied),
    }
    (C / "SUPPLIED_SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
