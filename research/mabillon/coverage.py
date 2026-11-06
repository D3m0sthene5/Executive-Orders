"""Mabillon coverage: for each order lacking an official original, the best route to one and its grade.

Joins the frame (frame.py) with every route's committed output and gives each order its best route, in this order
of grade: a machine-verified official printing (strong), a NARA image of the signed original, an archival replica
(ProQuest scan, pending a page check), an official-printing lead, a reprint lead (Civil Service Commission reports),
a volume whose title range includes the order (ceiling only), none. Counts are census counts over the frame and
Horvitz-Thompson projections over Herschel's sampled orders, the same way Herschel projected 5,313 and 1,234.

Run after the jobs: python3 -I research/mabillon/coverage.py  ->  frame/COVERAGE.csv, COVERAGE.md
"""
from __future__ import annotations

import collections
import csv
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
csv.field_size_limit(10**9)

ROUTES = [  # (route, grade under the codebook and the project's rules)
    ("held_printing_strong", "official printing, machine-located (Tischendorf rule plus segment and margin); counts only after the owner registers the job"),
    ("tischendorf_strong", "official printing, machine-located (Tischendorf); counts only after registration"),
    ("nara_signed_original_image", "image of the signed original in RG 11; codebook grade pending; page check"),
    ("proquest_archival_replica", "archival replica of the signed original; stays pending a page check"),
    ("held_printing_lead", "official printing held, lead (a check failed or no independent text)"),
    ("tischendorf_lead", "official-printing or reprint lead; page check"),
    ("csc_report_reprint", "reprint in a Civil Service Commission annual report; lead only, never the original"),
    ("official_find_page_check_pending", "official find already on file (fr-originals, ofr-compilations), flagged for a page check; Tischendorf corroborates"),
    ("listed_volume_range", "a digitized volume's title range includes the number; ceiling only"),
    ("none", "no route found; signed original at NARA (RG 11, not digitized) is the only known witness"),
]


def read_csv(path):
    p = REPO / path
    if not p.is_file():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    frame = {r["instrument_id"]: r for r in read_csv("research/mabillon/frame/FRAME.csv")}
    sample = read_csv("research/mabillon/frame/HERSCHEL_SAMPLE.csv")
    reg = {r["instrument_id"]: r for r in read_csv("jobs/domesday-register/output/REGISTER.csv")}
    ids = set(frame) | {s["instrument_id"] for s in sample}
    held = {r["instrument_id"]: r["verdict"] for r in read_csv("jobs/mabillon-held-printings/output/FINDS.csv")}
    tisch = {}
    for r in read_csv("jobs/tischendorf-originals/output/FINDS.csv"):
        if r["verdict"] == "strong" or r["instrument_id"] not in tisch:
            tisch[r["instrument_id"]] = r["verdict"]
    nara = {r["instrument_id"] for r in read_csv("jobs/mabillon-nara/output/BY_ORDER.csv") if int(r["with_objects"] or 0)}
    ranges = [(int(r["range_low"]), int(r["range_high"])) for r in
              read_csv("jobs/mabillon-scan-inventory/output/SCANS.csv") if r.get("range_low")]

    def route(iid):
        r = frame.get(iid) or reg.get(iid, {})
        n = int(r["number"]) if (r.get("number") or "").isdigit() else None
        if held.get(iid) == "strong":
            return "held_printing_strong"
        if tisch.get(iid) == "strong":
            return "tischendorf_strong"
        if iid in nara:
            return "nara_signed_original_image"
        if r.get("archival_replica"):
            return "proquest_archival_replica"
        if held.get(iid) == "lead":
            return "held_printing_lead"
        if iid in tisch:
            return "tischendorf_lead"
        if r.get("best_held") == "official_found_page_check_pending":
            return "official_find_page_check_pending"
        if "csc-annual-reports" in (r.get("transcription_sources") or ""):
            return "csc_report_reprint"
        if n is not None and any(a <= n <= b for a, b in ranges):
            return "listed_volume_range"
        return "none"

    best = {iid: route(iid) for iid in ids}
    census = collections.Counter(best[i] for i in frame)
    proj = collections.Counter()
    proj_sole = collections.Counter()
    for s in sample:
        w = float(s["weight"])
        proj[best[s["instrument_id"]]] += w
        if s["sole"] == "True":
            proj_sole[best[s["instrument_id"]]] += w
    with open(HERE / "frame/COVERAGE.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["instrument_id", "number", "era", "best_route", "in_frame", "herschel_sampled"])
        sampled = {s["instrument_id"] for s in sample}
        for iid in sorted(ids, key=lambda i: (frame.get(i, {}).get("number") or "", i)):
            r = frame.get(iid) or reg.get(iid, {})
            w.writerow([iid, r.get("number", ""), r.get("era", ""), best[iid], iid in frame, iid in sampled])
    lines = ["| Best route | Grade | Frame orders (census) | Of Herschel's 5,313 (projected) | Of the 1,234 sole-blocked (projected) |",
             "|---|---|---:|---:|---:|"]
    for k, grade in ROUTES:
        lines.append(f"| `{k}` | {grade} | {census.get(k, 0):,} | {round(proj.get(k, 0)):,} | {round(proj_sole.get(k, 0)):,} |")
    lines.append(f"| **Total** | | **{sum(census.values()):,}** | **{round(sum(proj.values())):,}** | "
                 f"**{round(sum(proj_sole.values())):,}** |")
    # Orders outside the frame whose text step rests provisionally on a transcription and still needs its official
    # original (the tracker's original_copy_replacement_required; Herschel's "replace" step).
    readiness = read_csv("jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")
    repl = [r["instrument_id"] for r in readiness if r.get("original_copy_replacement_required") == "yes"
            and r["instrument_id"] not in frame]
    rc = collections.Counter(route(i) for i in repl)
    lines += ["", f"Orders outside the frame whose working text is a transcription that must be replaced by the "
              f"official original ({len(repl):,}; Herschel's replace step):", "",
              "| Best route | Orders |", "|---|---:|"]
    lines += [f"| `{k}` | {rc.get(k, 0):,} |" for k, _ in ROUTES if rc.get(k)]
    acting = REPO / "research/mabillon/frame/ACTING_EO_TEXTS_NEEDED.csv"
    if acting.is_file():
        with open(acting, newline="", encoding="utf-8") as f:
            arows = list(csv.DictReader(f))
        ac, au = collections.Counter(), collections.Counter()
        for a in arows:
            k = route(a["instrument_id"])
            ac[k] += 1
            au[k] += int(a.get("orders_unblocked") or 0)
        lines += ["", f"Selden's acting orders without an official text ({len(arows):,}; "
                  "`research/selden/ACTING_EO_TEXTS_NEEDED.csv`, copied to `frame/`):", "",
                  "| Best route | Acting orders | Orders they act on (leads, as Selden counts them) |", "|---|---:|---:|"]
        lines += [f"| `{k}` | {ac[k]:,} | {au[k]:,} |" for k, _ in ROUTES if ac.get(k)]
    era = collections.defaultdict(collections.Counter)
    for i in frame:
        era[frame[i]["era"]][best[i]] += 1
    lines += ["", "By era (census):", "", "| Era | " + " | ".join(k for k, _ in ROUTES) + " |",
              "|---|" + "---:|" * len(ROUTES)]
    for e in sorted(era):
        lines.append(f"| {e} | " + " | ".join(f"{era[e].get(k, 0):,}" for k, _ in ROUTES) + " |")
    (HERE / "COVERAGE.md").write_text("# Mabillon coverage of the orders lacking an official original\n\n"
                                      "Generated by `research/mabillon/coverage.py` from committed job outputs.\n\n"
                                      + "\n".join(lines) + "\n")
    print("\n".join(lines))
    json.dump({"census": census, "projected": {k: round(v, 1) for k, v in proj.items()},
               "projected_sole": {k: round(v, 1) for k, v in proj_sole.items()}},
              open(HERE / "frame/COVERAGE_SUMMARY.json", "w"), indent=1, default=dict)


if __name__ == "__main__":
    main()
