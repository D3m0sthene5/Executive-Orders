"""Photius Lane 2: Civil Service Commission annual reports as official printings (R37).

Step A (promote): for the 798 orders csc-annual-reports located from WPA citations, re-read the cited PDF page from
the report PDFs (held in a private cache; GovInfo serves them publicly), check the date line and signature block,
and build Opus page-check packets: a seeded 10% sample of the high-confidence locations, every medium and low one.
Step B (rescan): read every page of all 37 reports, find each date line, and match it to the orders in the frame
that have no WPA printed citation (dates from the identity layer); candidates with a signature block and a date match
go to an Opus page check too.

Outputs under jobs/photius-csc-printings/work/ (page texts cached in the scratch dir, never committed):
  LOCATED.csv        the 798 with the re-read page's date and signature findings
  RESCAN.csv         date-line hits for orders without a WPA citation
  packets/<p>/ORDERS.jsonl  Opus packets (page text, expected facts, render path)

    python -I jobs/photius-csc-printings/scan.py --pdfs SCRATCH/csc/pdfs --cache SCRATCH/csc/pages --renders SCRATCH/csc/renders
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import random
import re
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.append(r"C:\Users\danie\AppData\Roaming\Python\Python312\site-packages")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "jobs" / "csc-annual-reports"))
csv.field_size_limit(10**9)

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
MON = {m[:3].lower(): i + 1 for i, m in enumerate(MONTHS.split("|"))}
DATE_LINE = re.compile(rf"^\s*({MONTHS}|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\.?\s+(\d{{1,2}})\s*,?\s*(1[89]\d\d)\s*[.,:;]?\s*$", re.I)
ANY_DATE = re.compile(rf"\b({MONTHS}|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\.?\s+(\d{{1,2}})\s*,?\s*(1[89]\d\d)\b", re.I)
PRES = ["LINCOLN", "JOHNSON", "GRANT", "HAYES", "GARFIELD", "ARTHUR", "CLEVELAND", "HARRISON", "McKINLEY", "ROOSEVELT", "TAFT",
        "WILSON", "HARDING", "COOLIDGE", "HOOVER"]
SIGN = re.compile(r"(THE\s+WHITE\s+HOUSE|EXECUTIVE\s+MANSION|" + "|".join(PRES) + r")", re.I)
SEED = 20261106


def iso(m):
    mo = MON.get(m.group(1)[:3].lower())
    return f"{int(m.group(3)):04d}-{mo:02d}-{int(m.group(2)):02d}" if mo else ""


def extract_pages(args):
    pdf, cache = args
    out = cache / (pdf.stem + ".json")
    if out.exists():
        return pdf.stem, "cached"
    import pypdfium2 as pdfium
    d = pdfium.PdfDocument(str(pdf))
    texts = [d[i].get_textpage().get_text_range() for i in range(len(d))]
    out.write_text(json.dumps(texts), encoding="utf-8")
    return pdf.stem, len(texts)


def render(pdf, idx, renders, dpi=150):
    import pypdfium2 as pdfium
    p = renders / f"{pdf.stem}_p{idx + 1}.png"
    if not p.exists():
        d = pdfium.PdfDocument(str(pdf))
        d[idx].render(scale=dpi / 72, grayscale=True).to_pil().save(p, format="PNG", compress_level=3)
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdfs", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--renders", required=True)
    ap.add_argument("--work", default=str(REPO / "jobs/photius-csc-printings/work"))
    ap.add_argument("--batch", type=int, default=12)
    a = ap.parse_args(argv)
    pdfs, cache, renders, work = Path(a.pdfs), Path(a.cache), Path(a.renders), Path(a.work)
    for d in (cache, renders, work, work / "packets"):
        d.mkdir(parents=True, exist_ok=True)

    import csc  # the parser the csc-annual-reports job used: page_map, segments_on, date_regex
    reports = {r["package_id"]: r for r in csv.DictReader(open(REPO / "jobs/csc-annual-reports/output/REPORTS_FETCHED.csv", encoding="utf-8"))}
    with Pool(max(2, os.cpu_count() - 2)) as pool:
        for stem, n in pool.imap_unordered(extract_pages, [(pdfs / f"{pid}.pdf", cache) for pid in reports if (pdfs / f"{pid}.pdf").exists()]):
            print("pages", stem, n, flush=True)
    texts = {pid: json.loads((cache / f"{pid}.json").read_text(encoding="utf-8")) for pid in reports if (cache / f"{pid}.json").exists()}
    pmaps = {pid: csc.page_map(t) for pid, t in texts.items()}

    ident = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "research/photius/IDENTITY_DATES.csv", encoding="utf-8"))}
    tracker = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv", encoding="utf-8"))}
    frame = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "research/mabillon/frame/FRAME.csv", encoding="utf-8"))}

    # ---- Step A: the located 798 -------------------------------------------------------------------------------
    located = []
    frags = {}
    for line in open(REPO / "jobs/csc-annual-reports/output/FRAGMENTS.jsonl", encoding="utf-8"):
        f = json.loads(line)
        frags[f["instrument_id"]] = f
    for r in csv.DictReader(open(REPO / "jobs/csc-annual-reports/output/CITATION_RESULTS.csv", encoding="utf-8")):
        if not r["pdf_page"]:
            continue
        iid, pid, idx = r["id"], r["package_id"], int(r["pdf_page"]) - 1
        page = texts.get(pid, [""])[idx] if pid in texts and idx < len(texts[pid]) else ""
        seg_path = REPO / "jobs/csc-annual-reports/output" / frags[iid]["data"]["text_path"] if iid in frags else None
        seg = seg_path.read_text(encoding="utf-8", errors="replace") if seg_path and seg_path.exists() else ""
        exp = ident.get(iid, {}).get("date", "")
        dates = {iso(m) for m in ANY_DATE.finditer(page)} - {""}
        located.append({
            "instrument_id": iid, "cited": r["cited"], "wpa_date": r["wpa_date"], "package_id": pid, "pdf_page": idx + 1,
            "confidence": r["confidence"], "how": r["how"], "identity_date": exp, "date_on_page": "yes" if exp in dates else "no",
            "signature_on_page": "yes" if SIGN.search(page) else "no", "segment_chars": len(seg),
            "segment_has_signature": "yes" if SIGN.search(seg) else "no", "report_sha256": reports[pid]["sha256"],
            "tracker_step": tracker.get(iid, {}).get("step_original_text", ""),
        })
    with open(work / "LOCATED.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(located[0].keys()))
        w.writeheader()
        w.writerows(located)
    rnd = random.Random(SEED)
    queue_a = [l for l in located if l["confidence"] != "high"] + [l for l in located if l["confidence"] == "high" and rnd.random() < 0.10]
    print("located", len(located), collections.Counter(l["confidence"] for l in located), "queue A", len(queue_a),
          "date_on_page", collections.Counter(l["date_on_page"] for l in located))

    # ---- Step B: rescan every page by date line for orders without a WPA printed citation --------------------
    no_cite = {iid: fr for iid, fr in frame.items() if not fr["wpa_citations"] and fr.get("date") and len(fr["date"]) >= 10
               and tracker.get(iid, {}).get("step_original_text") != "done"}
    by_date = collections.defaultdict(list)
    for iid, fr in no_cite.items():
        by_date[fr["date"]].append(iid)
    hits = []
    for pid, pages in texts.items():
        fy = reports[pid]["fy_on_title_page"] or reports[pid]["title_fy"]
        for idx, page in enumerate(pages):
            lines = page.splitlines()
            for n, line in enumerate(lines):
                m = DATE_LINE.match(line)
                if not m:
                    continue
                d = iso(m)
                if d not in by_date:
                    continue
                body = "\n".join(lines[n:n + 40])
                for iid in by_date[d]:
                    fr = frame[iid]
                    title_words = set(re.findall(r"[a-z]{4,}", (fr["title"] or "").lower()))
                    body_words = set(re.findall(r"[a-z]{4,}", body.lower()))
                    ov = len(title_words & body_words) / max(1, len(title_words)) if title_words else 0.0
                    hits.append({"instrument_id": iid, "date": d, "package_id": pid, "report_fy": fy, "pdf_page": idx + 1, "line": n,
                                 "same_date_candidates": len(by_date[d]), "title_overlap": round(ov, 2),
                                 "signature_near": "yes" if SIGN.search(body) else "no", "wpa_subject": fr["wpa_subject"],
                                 "title": (fr["title"] or "")[:120], "report_sha256": reports[pid]["sha256"]})
    # one best hit per order (highest overlap, then signature), keep all in the CSV
    best = {}
    for h in sorted(hits, key=lambda h: (-h["title_overlap"], h["signature_near"] != "yes")):
        best.setdefault(h["instrument_id"], h)
    with open(work / "RESCAN.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(hits[0].keys()) if hits else ["instrument_id"])
        w.writeheader()
        w.writerows(hits)
    print("no-citation frame orders with dates", len(no_cite), "date-line hits", len(hits), "orders hit", len(best),
          "with signature near", sum(1 for h in best.values() if h["signature_near"] == "yes"))

    # ---- Packets for the Opus page check ----------------------------------------------------------------------
    items = []
    for l in queue_a:
        items.append({"kind": "located", "instrument_id": l["instrument_id"], "package_id": l["package_id"], "pdf_page": l["pdf_page"],
                      "expected_date": l["identity_date"] or l["wpa_date"], "wpa_citation": l["cited"], "prior_confidence": l["confidence"],
                      "expected_title": ident.get(l["instrument_id"], {}).get("title", "") or frame.get(l["instrument_id"], {}).get("title", "")})
    for iid, h in best.items():
        if h["signature_near"] != "yes" and h["title_overlap"] < 0.3:
            continue  # a bare date line with no signature block nearby and no subject overlap is not worth an Opus read
        items.append({"kind": "rescan", "instrument_id": iid, "package_id": h["package_id"], "pdf_page": h["pdf_page"],
                      "expected_date": h["date"], "wpa_citation": "", "prior_confidence": f"overlap {h['title_overlap']}, {h['same_date_candidates']} same-date candidates",
                      "expected_title": h["title"], "wpa_subject": h["wpa_subject"]})
    for i, it in enumerate(items):
        pid, idx = it["package_id"], it["pdf_page"] - 1
        it["page_text"] = texts[pid][idx][:6000]
        it["next_page_text"] = texts[pid][idx + 1][:2500] if idx + 1 < len(texts[pid]) else ""
        it["report"] = f"{reports[pid]['title_fy']} annual report, GovInfo {pid}, sha256 {reports[pid]['sha256'][:12]}"
        it["render"] = str(render(pdfs / f"{pid}.pdf", idx, renders))
        it["render_next"] = str(render(pdfs / f"{pid}.pdf", idx + 1, renders)) if idx + 1 < len(texts[pid]) else ""
        it["expected_number"] = it["instrument_id"].split(":")[1]
    for b0 in range(0, len(items), a.batch):
        d = work / "packets" / f"c{b0 // a.batch + 1:03d}"
        d.mkdir(exist_ok=True)
        with open(d / "ORDERS.jsonl", "w", encoding="utf-8") as f:
            for it in items[b0:b0 + a.batch]:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    json.dump({"located": len(located), "queue_a": len(queue_a), "rescan_hits": len(hits), "rescan_orders": len(best), "packets": (len(items) + a.batch - 1) // a.batch,
               "items": len(items)}, open(work / "SCAN_SUMMARY.json", "w"), indent=1)
    print("packets", (len(items) + a.batch - 1) // a.batch, "items", len(items))


if __name__ == "__main__":
    main()
