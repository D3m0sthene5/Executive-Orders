"""Mabillon, step 1: the order-level frame of orders that lack an official printing or page image.

Named for Jean Mabillon (1632-1707), whose De re diplomatica (1681) founded diplomatics, the science of telling an
authentic original document from a copy. Mabillon looks for the bulk sources that hold official originals of the
project's open orders and proves coverage by machine-verified matches.

Herschel's figure of 5,313 orders (1,234 for which it is the only root blocker) is a projection from 110 sampled
orders (research/herschel/ATLAS/BLOCKERS.csv). The census itself names the orders: the readiness tracker's blocker
NO_OFFICIAL_SOURCE_LOCATED marks every order whose original-text step has no official find at all (5,943 on
2026-11-05). This script writes that census list with the features a source router needs (number, date, what is
held, the 1944 WPA list's subject hint and print citations), and the Herschel sampled orders whose root blockers
include the official original, with their stratum weights, so a source's coverage can be projected onto Herschel's
5,313 and 1,234 the same way Herschel projected them.

Inputs are committed files only; no network, no tokens. Run: python3 -I research/mabillon/frame.py
Outputs (research/mabillon/frame/): FRAME.csv, HERSCHEL_SAMPLE.csv, FRAME_SUMMARY.json
"""
from __future__ import annotations

import collections
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "frame"
csv.field_size_limit(10**9)

REGISTER = REPO / "jobs/domesday-register/output/REGISTER.csv"
WPA = REPO / "jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv"
HERSCHEL = REPO / "research/herschel"
BLOCKER = "NO_OFFICIAL_SOURCE_LOCATED"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def band(number):
    return f"{(number // 500) * 500:05d}-{(number // 500) * 500 + 499:05d}" if number is not None else "unnumbered"


def herschel_sample():
    """Sampled orders whose root blockers include the official original, with Herschel's projection weights."""
    sys.path.insert(0, str(HERSCHEL))
    import project as hp  # read-only use of Herschel's own outcome classifier
    strata = json.loads((HERSCHEL / "frame/STRATA.json").read_text())["strata"]
    sample = {}
    for name in ("SAMPLE.csv", "SAMPLE_R2.csv"):
        p = HERSCHEL / "frame" / name
        if p.is_file():
            for r in read_csv(p):
                if r.get("sample_kind", "deep") == "deep":
                    sample[r["instrument_id"]] = r["stratum"]
    steps = collections.defaultdict(list)
    for h in sorted(HERSCHEL.glob("H[0-9]*")):
        p = h / "ORDER_OUTCOMES.csv"
        if p.is_file():
            for r in read_csv(p):
                steps[r["instrument_id"]].append(r.get("outcome", ""))
    reached = collections.Counter(sample[i] for i in sample if i in steps)
    rows = []
    for iid, outs in steps.items():
        if iid not in sample:
            continue
        classes = {hp.blocker_class(hp.acquisition(o)) for o in outs if hp.acquisition(o)} - {"knock_on"}
        if "official_original" not in classes:
            continue
        h = sample[iid]
        rows.append({"instrument_id": iid, "stratum": h, "weight": round(strata[h]["population"] / reached[h], 4),
                     "sole": len(classes) == 1, "root_classes": "|".join(sorted(classes))})
    return rows


def main():
    reg = read_csv(REGISTER)
    wpa = collections.defaultdict(list)
    for w in read_csv(WPA):
        wpa[w["id"]].append(w)
    frame = []
    for r in reg:
        if BLOCKER not in r["blockers"].split("|"):
            continue
        n = int(r["number"]) if r["number"].isdigit() else None
        ws = wpa.get(r["instrument_id"], [])
        kinds = sorted({k.strip() for w in ws for k in w["source_kinds_joined"].split("|") if k.strip()})
        cites = sorted({c.strip() for w in ws for c in re.split(r"[;|]", w["citations_joined"]) if c.strip()})
        frame.append({
            "instrument_id": r["instrument_id"], "number": "" if n is None else n, "suffix": r["suffix"],
            "band": band(n), "date": r["date"], "year": (r["date"] or "")[:4], "era": r["era"],
            "census_class": r["census_class"], "best_held": r["best_held"],
            "transcription_sources": r["transcription_sources"], "archival_replica": r["archival_replica"],
            "provisional_status": r["provisional_status"],
            "wpa_subject": "|".join(sorted({w["family_hint"] for w in ws if w["family_hint"]})),
            "wpa_print_kinds": "|".join(kinds), "wpa_citations": "|".join(cites),
            "title": r["title"][:160]})
    frame.sort(key=lambda x: (x["number"] == "", x["number"] or 0, x["suffix"], x["instrument_id"]))
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "FRAME.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(frame[0]))
        w.writeheader()
        w.writerows(frame)
    hs = herschel_sample()
    with open(OUT / "HERSCHEL_SAMPLE.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["instrument_id", "stratum", "weight", "sole", "root_classes"])
        w.writeheader()
        w.writerows(sorted(hs, key=lambda x: x["instrument_id"]))
    in_frame = {x["instrument_id"] for x in frame}
    summary = {
        "frame_orders": len(frame),
        "frame_definition": f"REGISTER.csv rows whose blockers include {BLOCKER}",
        "by_era": collections.Counter(x["era"] for x in frame),
        "by_best_held": collections.Counter(x["best_held"] for x in frame),
        "by_band": dict(sorted(collections.Counter(x["band"] for x in frame).items())),
        "wpa_print_kinds": collections.Counter(x["wpa_print_kinds"] or ("none" if x["wpa_subject"] else "no_wpa_entry")
                                               for x in frame),
        "wpa_subjects": collections.Counter(s for x in frame for s in (x["wpa_subject"] or "none").split("|")),
        "herschel_sampled_official_original": len(hs),
        "herschel_projected": round(sum(x["weight"] for x in hs)),
        "herschel_projected_sole": round(sum(x["weight"] for x in hs if x["sole"])),
        "herschel_sampled_in_frame": sum(x["instrument_id"] in in_frame for x in hs),
        "inputs": {str(p.relative_to(REPO)): None for p in (REGISTER, WPA)},
    }
    (OUT / "FRAME_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=dict) + "\n")
    print(json.dumps({k: summary[k] for k in ("frame_orders", "by_era", "herschel_sampled_official_original",
                                              "herschel_projected", "herschel_projected_sole",
                                              "herschel_sampled_in_frame")}, default=dict, indent=1))


if __name__ == "__main__":
    main()
