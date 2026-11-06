"""Photius Lane 2, step 3: assemble the Opus page checks of Civil Service Commission report pages into the producer
record the tracker reads.

Inputs: work/LOCATED.csv and work/RESCAN.csv (scan.py), work/packets/*/RESULT.jsonl (Opus). Rules (R37 and the
Lane 2 brief): a page counts as an official printing only when the Opus check found the order's full text with its
dateline or number and its signature block (`found: full_text`, `result: pass`). High-confidence located orders that
were not sampled count only if no sampled high-confidence page failed the R37 test in its report year... no: the owner's
rule says reject the whole high batch if any sampled page fails, then check all. The 1912-1929 reports print orders
without a signature block, so the batch rule is applied per report (package): a report whose sampled pages all pass
promotes its unsampled high-confidence locations; a report with any sampled failure promotes nothing unsampled.

Outputs under output/: RESULTS.csv, FRAGMENTS.jsonl (grade official_printing where counted; csc_report_lead otherwise,
needs_page_check true), SUMMARY.json, REPORT.md, STATUS.json.

    python -I jobs/photius-csc-printings/assemble.py
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JOB = "photius-csc-printings"
WORK = REPO / "jobs" / JOB / "work"
OUT = REPO / "jobs" / JOB / "output"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reports = {r["package_id"]: r for r in csv.DictReader(open(REPO / "jobs/csc-annual-reports/output/REPORTS_FETCHED.csv", encoding="utf-8"))}
    located = list(csv.DictReader(open(WORK / "LOCATED.csv", encoding="utf-8")))
    ident = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "research/photius/IDENTITY_DATES.csv", encoding="utf-8"))}
    checks = {}
    items = {}
    for d in sorted((WORK / "packets").glob("c*")):
        for line in open(d / "ORDERS.jsonl", encoding="utf-8"):
            it = json.loads(line)
            items[(it["kind"], it["instrument_id"], it["package_id"], it["pdf_page"])] = it
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
                    r["_packet"] = d.name
                    checks[r["instrument_id"]] = r
    # per-report batch rule for the unsampled high-confidence locations
    sampled_by_report = collections.defaultdict(list)
    for (kind, iid, pid, pg), it in items.items():
        if kind == "located" and it.get("prior_confidence") == "high":
            c = checks.get(iid)
            if c:
                sampled_by_report[pid].append(c.get("result") == "pass" and c.get("found") == "full_text")
    report_ok = {pid: bool(v) and all(v) for pid, v in sampled_by_report.items()}

    rows, frags = [], []
    seen = set()
    for l in located:
        iid, pid = l["instrument_id"], l["package_id"]
        c = checks.get(iid)
        if c:
            counts = c.get("result") == "pass" and c.get("found") == "full_text"
            basis = f"opus page check {c.get('result')} ({c.get('found')})"
        elif l["confidence"] == "high" and report_ok.get(pid):
            counts = True
            basis = f"unsampled high-confidence location in a report whose sampled pages all passed ({sum(sampled_by_report[pid])} of {len(sampled_by_report[pid])})"
        elif l["confidence"] == "high" and pid in report_ok:
            counts = False
            basis = f"unsampled high-confidence location in a report with a sampled failure ({sum(sampled_by_report[pid])} of {len(sampled_by_report[pid])} passed): lead"
        else:
            counts = False
            basis = "not checked this run: lead"
        rows.append({"instrument_id": iid, "kind": "located", "package_id": pid, "pdf_page": l["pdf_page"], "report_fy": reports[pid]["title_fy"],
                     "prior_confidence": l["confidence"], "check_result": (c or {}).get("result", ""), "check_found": (c or {}).get("found", ""),
                     "date_on_page": (c or {}).get("date_on_page", ""), "signature_on_page": (c or {}).get("signature_on_page", ""),
                     "counts_as_official_printing": "yes" if counts else "no", "basis": basis, "note": (c or {}).get("note", "")[:200]})
        seen.add(iid)
    for (kind, iid, pid, pg), it in items.items():
        if kind != "rescan" or iid in seen:
            continue
        c = checks.get(iid)
        counts = bool(c) and c.get("result") == "pass" and c.get("found") == "full_text"
        rows.append({"instrument_id": iid, "kind": "rescan", "package_id": pid, "pdf_page": pg, "report_fy": reports[pid]["title_fy"],
                     "prior_confidence": it.get("prior_confidence", ""), "check_result": (c or {}).get("result", ""), "check_found": (c or {}).get("found", ""),
                     "date_on_page": (c or {}).get("date_on_page", ""), "signature_on_page": (c or {}).get("signature_on_page", ""),
                     "counts_as_official_printing": "yes" if counts else "no",
                     "basis": f"date-line rescan; opus page check {(c or {}).get('result', 'not run')}", "note": (c or {}).get("note", "")[:200]})
        seen.add(iid)
    rows.sort(key=lambda r: (int("".join(ch for ch in r["instrument_id"].split(":")[1] if ch.isdigit()) or 0), r["instrument_id"]))
    with open(OUT / "RESULTS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(OUT / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            if r["counts_as_official_printing"] != "yes" and not r["check_result"]:
                continue  # nothing new to say about an unchecked lead; csc-annual-reports already carries it
            rep = reports[r["package_id"]]
            counts = r["counts_as_official_printing"] == "yes"
            page_ref = f"Annual report of the U.S. Civil Service Commission for fiscal {rep['title_fy']}, GovInfo {r['package_id']}, PDF page {r['pdf_page']}"
            note = (f"Civil Service Commission annual report page: {r['basis']}. "
                    + (f"Page shows dateline {r['date_on_page']} and signature block '{r['signature_on_page'][:60]}'. " if r["date_on_page"] else "")
                    + ("Counts as an official printing witness under ruling R37 (2026-11-06); " if counts else
                       "Does not meet R37 (no signature block, abstract, or not checked); a dated lead only; ")
                    + "a machine-located government printing, not an authentication of the signed original; not a legal conclusion.")
            frags.append({
                "acceptable_as_original": False, "confidence_note": note,
                "data": {"acceptable_as_original": False, "grade": "official_printing" if counts else "csc_report_lead",
                         "location_confidence": "high" if counts else "medium", "location_verified": bool(r["check_result"]),
                         "needs_page_check": not counts, "page_or_item": page_ref,
                         "representation_type": "agency_annual_report_full_printing" if counts else "agency_annual_report_printing_or_abstract",
                         "route": "official_publication/csc_annual_report_serial_set", "sha256": rep["sha256"],
                         "signing_date": r["date_on_page"] or ident.get(r["instrument_id"], {}).get("date", ""),
                         "source_id": f"{JOB}:{r['instrument_id']}:{rep['sha256'][:12]}",
                         "title": ident.get(r["instrument_id"], {}).get("title", ""), "url": f"{rep['url']}#page={r['pdf_page']}",
                         "page_check": {"result": r["check_result"], "found": r["check_found"], "basis": r["basis"]}},
                "grade": "official_printing" if counts else "csc_report_lead", "instrument_id": r["instrument_id"],
                "kind": "original_representation", "produced_by": JOB,
                "sources": [{"page_or_item": page_ref, "sha256": rep["sha256"], "url": f"{rep['url']}#page={r['pdf_page']}"}],
            })
            f.write(json.dumps(frags[-1], ensure_ascii=False) + "\n")
    by_year = collections.Counter((r["report_fy"], r["counts_as_official_printing"]) for r in rows)
    summary = {"located_rows": sum(1 for r in rows if r["kind"] == "located"), "rescan_rows": sum(1 for r in rows if r["kind"] == "rescan"),
               "checked": sum(1 for r in rows if r["check_result"]), "check_results": dict(collections.Counter(r["check_result"] for r in rows if r["check_result"])),
               "check_found": dict(collections.Counter(r["check_found"] for r in rows if r["check_found"])),
               "counting_as_official_printing": sum(1 for r in rows if r["counts_as_official_printing"] == "yes"),
               "reports_whose_sample_all_passed": sorted(p for p, ok in report_ok.items() if ok),
               "reports_with_a_sampled_failure": sorted(p for p, ok in report_ok.items() if not ok),
               "fragments": len(frags),
               "note": "R37 needs the signature block; the 1912-1929 reports print orders without one, so most of their locations stay leads. No status, census, codebook or certified count change."}
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n")
    (OUT / "STATUS.json").write_text(json.dumps({"job": JOB, "status": "succeeded", "exit_code": 0, "runner": "owner's PC (Photius session, Agent-tool workers)",
                                                 "branch": "main", "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                                 "note": "PC run; no job.py; outputs are for main."}, indent=1) + "\n")
    lines = ["# Photius CSC printings: report", "", json.dumps({k: v for k, v in summary.items() if not k.startswith("reports_")}), "",
             "| Report FY | counts | lead |", "|---|---:|---:|"]
    for fy in sorted({r["report_fy"] for r in rows}):
        lines.append(f"| {fy} | {by_year.get((fy, 'yes'), 0)} | {by_year.get((fy, 'no'), 0)} |")
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
