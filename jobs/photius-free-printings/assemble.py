"""Photius Lane 3, step 3: assemble the Opus page checks of Internet Archive pages into the producer record.

Inputs: work/CANDIDATES.jsonl and work/packets/*/ORDERS.jsonl (candidates.py), work/packets/*/RESULT.jsonl (Opus).
A page counts as an official printing only when the check found `full_text` and `result: pass` (R37: text, dateline or
number, signature block). Everything else checked is written as a lead (needs_page_check true) so the location is
not lost. Outputs under output/: RESULTS.csv, FRAGMENTS.jsonl, SUMMARY.json, REPORT.md, STATUS.json.

    python -I jobs/photius-free-printings/assemble.py
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JOB = "photius-free-printings"
WORK = REPO / "jobs" / JOB / "work"
OUT = REPO / "jobs" / JOB / "output"
SOURCES = {s["ia_id"]: s for s in json.load(open(REPO / "jobs" / JOB / "data/SOURCES.json"))["sources"]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ident = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "research/photius/IDENTITY_DATES.csv", encoding="utf-8"))}
    items, checks = {}, {}
    for d in sorted((WORK / "packets").glob("f*")):
        for line in open(d / "ORDERS.jsonl", encoding="utf-8"):
            it = json.loads(line)
            items[(it["instrument_id"], it["source"], it["page_index"])] = it
        rf = d / "RESULT.jsonl"
        if rf.exists():
            for line in open(rf, encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("instrument_id"):
                    checks[(r["instrument_id"], r.get("source", ""), int(r.get("page_index", -1)))] = r
    # best check per order: pass beats anything else
    best = {}
    for key, it in items.items():
        c = checks.get(key)
        row = {"instrument_id": it["instrument_id"], "source": it["source"], "page_index": it["page_index"],
               "by": it["by"], "expected_date": it["expected_date"], "check_result": (c or {}).get("result", ""),
               "check_found": (c or {}).get("found", ""), "date_on_page": (c or {}).get("date_on_page", ""),
               "number_on_page": (c or {}).get("number_on_page", ""), "signature_on_page": (c or {}).get("signature_on_page", ""),
               "subject_matches_title": (c or {}).get("subject_matches_title", ""), "note": (c or {}).get("note", "")[:200],
               "counts_as_official_printing": "yes" if c and c.get("result") == "pass" and c.get("found") == "full_text" else "no"}
        cur = best.get(it["instrument_id"])
        rank = (row["counts_as_official_printing"] == "yes", bool(row["check_result"]))
        if cur is None or rank > (cur["counts_as_official_printing"] == "yes", bool(cur["check_result"])):
            best[it["instrument_id"]] = row
    rows = sorted(best.values(), key=lambda r: (int("".join(ch for ch in r["instrument_id"].split(":")[1] if ch.isdigit()) or 0), r["instrument_id"]))
    with open(OUT / "RESULTS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n = 0
    with open(OUT / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            if not r["check_result"]:
                continue
            src = SOURCES[r["source"]]
            counts = r["counts_as_official_printing"] == "yes"
            page_ref = f"{src['title']}; Internet Archive {r['source']}, leaf {r['page_index']}"
            url = f"https://archive.org/details/{r['source']}/page/n{r['page_index']}"
            note = (f"Official printing located in a free government publication ({src['publisher']}); Opus page check on the text layer: "
                    f"{r['check_result']} ({r['check_found']}); dateline {r['date_on_page'] or 'not read'}, number {r['number_on_page'] or 'none printed'}, "
                    f"signature block '{r['signature_on_page'][:60]}', subject match {r['subject_matches_title']}. "
                    + ("Counts as an official printing witness under rulings R37 and R40 (2026-11-06); " if counts else "Does not meet R37; a located lead only; ")
                    + "a machine-located government printing, not an authentication of the signed original; not a legal conclusion.")
            frag = {"acceptable_as_original": False, "confidence_note": note,
                    "data": {"acceptable_as_original": False, "grade": "official_printing" if counts else "official_printing_lead",
                             "location_confidence": "high" if counts else "medium", "location_verified": True, "needs_page_check": not counts,
                             "page_or_item": page_ref, "representation_type": "government_publication_page_text_layer",
                             "route": "free/internet_archive_official_publication", "sha256": "",
                             "signing_date": r["date_on_page"] or ident.get(r["instrument_id"], {}).get("date", ""),
                             "source_id": f"{JOB}:{r['instrument_id']}:{r['source']}:{r['page_index']}", "title": ident.get(r["instrument_id"], {}).get("title", ""),
                             "url": url, "page_check": {"result": r["check_result"], "found": r["check_found"], "subject": r["subject_matches_title"]}},
                    "grade": "official_printing" if counts else "official_printing_lead", "instrument_id": r["instrument_id"],
                    "kind": "original_representation", "produced_by": JOB,
                    "sources": [{"page_or_item": page_ref, "sha256": "", "url": url}]}
            f.write(json.dumps(frag, ensure_ascii=False) + "\n")
            n += 1
    summary = {"orders_with_candidates": len(rows), "checked": sum(1 for r in rows if r["check_result"]),
               "check_results": dict(collections.Counter(r["check_result"] for r in rows if r["check_result"])),
               "check_found": dict(collections.Counter(r["check_found"] for r in rows if r["check_found"])),
               "counting_as_official_printing": sum(1 for r in rows if r["counts_as_official_printing"] == "yes"),
               "counting_by_source": dict(collections.Counter(r["source"] for r in rows if r["counts_as_official_printing"] == "yes")),
               "fragments": n, "note": "R37 and R40; text-layer page checks; no status, census, codebook or certified count change."}
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n")
    (OUT / "STATUS.json").write_text(json.dumps({"job": JOB, "status": "succeeded", "exit_code": 0, "runner": "owner's PC (Photius session, Agent-tool workers)",
                                                 "branch": "main", "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                                 "note": "PC run; no job.py; outputs are for main."}, indent=1) + "\n")
    (OUT / "REPORT.md").write_text("# Photius free printings: report\n\n" + json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
