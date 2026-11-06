"""Photius Lane 4, step 1: deterministic read of every ProQuest replica awaiting a page check.

For each order whose tracker row carries ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK and whose original-text step is
open, read the Pinakes text (the PDF's own layer or its OCR; the Pinakes HTR reading for handwritten scans) and record
what a page check needs: the order number seen, the dates seen, the signature block, the first and last words, and
whether each agrees with the identity layer. Writes CANDIDATES.csv and the worker packets. Changes no status.

    python -I jobs/photius-replica-check/extract.py [--packets DIR] [--batch 30]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
csv.field_size_limit(10**9)

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
MONTH_ABBR = {m[:3].lower(): i + 1 for i, m in enumerate(MONTHS.split("|"))}
DATE_RE = re.compile(rf"\b({MONTHS}|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\.?\s+(\d{{1,2}})\s*(?:st|nd|rd|th)?\s*,?\s*(1[89]\d\d)\b", re.I)
NUM_TAG_RE = re.compile(r"\[\s*No\.?\s*([0-9][0-9 ]{0,5})\s*[-]?\s*([A-Za-z])?\s*[.,]?\s*[\]\}1lI]")
NUM_RE = re.compile(r"(?:Executive\s+Order|E\.?\s*O\.?|Order)\s*(?:No\.?|Number|#)?\s*([0-9][0-9 ]{0,5})\s*[-]?\s*([A-Za-z])?\b", re.I)
NUM_LOOSE_RE = re.compile(r"\bNo\.?\s*([0-9][0-9 ]{1,5})\b")
PRESIDENTS = ["LINCOLN", "JOHNSON", "GRANT", "HAYES", "GARFIELD", "ARTHUR", "CLEVELAND", "HARRISON", "McKINLEY", "MCKINLEY",
              "ROOSEVELT", "TAFT", "WILSON", "HARDING", "COOLIDGE", "HOOVER"]
SIG_RE = re.compile(r"(THE\s+WHITE\s+HOUSE|EXECUTIVE\s+MANSION|By\s+the\s+President|Secretary\s+of\s+State|" + "|".join(PRESIDENTS) + r")", re.I)
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]+")


def norm_num(s):
    return int(re.sub(r"\D", "", s)) if re.sub(r"\D", "", s) else None


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def words(text, n, tail=False):
    ws = WORD_RE.findall(text)
    ws = [w for w in ws if len(w) > 1]
    return " ".join(ws[-n:] if tail else ws[:n])


def body(text):
    """Drop ProQuest cover furniture: lines before the first line with 5+ words that is not a URL or header."""
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if len(WORD_RE.findall(l)) >= 5 and "proquest" not in l.lower() and "http" not in l.lower():
            return "\n".join(lines[i:])
    return text


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets", default=str(REPO / "research/excavator/photius-replica/packets"))
    ap.add_argument("--batch", type=int, default=30)
    ap.add_argument("--out", default=str(REPO / "jobs/photius-replica-check/work"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    ident = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "research/photius/IDENTITY_DATES.csv", encoding="utf-8"))}
    tracker = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv", encoding="utf-8"))}
    pq = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "jobs/pinakes-proquest-ingest/output/ORDERS.csv", encoding="utf-8"))}
    htr = {}
    htr_csv = REPO / "jobs/pinakes-htr/output/HTR.csv"
    if htr_csv.exists():
        for r in csv.DictReader(open(htr_csv, encoding="utf-8")):
            htr[r.get("instrument_id", "")] = r

    targets = [i for i, t in tracker.items()
               if "ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK" in t["blockers"] and t["step_original_text"] != "done" and i in pq]
    targets.sort(key=lambda i: (int(pq[i]["number"]), pq[i]["suffix"]))
    rows = []
    for iid in targets:
        p = pq[iid]
        text_path = REPO / "jobs/pinakes-proquest-ingest/output" / p["text_path"]
        text = read_text(text_path)
        text_kind = "pinakes_" + p["text_source"]
        if p["text_usable"] != "yes":
            h = REPO / "jobs/pinakes-htr/output/texts" / f"EO_{p['number']}{p['suffix']}.txt"
            alt = read_text(h) if h.exists() else ""
            if len(alt) > 200:
                text, text_kind = alt, "pinakes_htr_backbone"
        b = body(text)
        exp_num = int(p["number"])
        exp_suffix = (p["suffix"] or "").upper()
        idd = ident.get(iid, {})
        exp_date = idd.get("date", "") or (p.get("signing_date") or "")
        nums = []
        for m in NUM_TAG_RE.finditer(text):
            nums.append((norm_num(m.group(1)), (m.group(2) or "").upper(), "tag"))
        for m in NUM_RE.finditer(text):
            nums.append((norm_num(m.group(1)), (m.group(2) or "").upper(), "heading"))
        for m in NUM_LOOSE_RE.finditer(text[:1500]):
            nums.append((norm_num(m.group(1)), "", "loose_top"))
        num_hit = [n for n in nums if n[0] == exp_num]
        number_seen = ";".join(sorted({f"{n[0]}{n[1]}:{n[2]}" for n in nums if n[0]}))[:200]
        dates = []
        for m in DATE_RE.finditer(text):
            mon = MONTH_ABBR.get(m.group(1)[:3].lower())
            try:
                dates.append(f"{int(m.group(3)):04d}-{mon:02d}-{int(m.group(2)):02d}")
            except (TypeError, ValueError):
                pass
        date_exact = bool(exp_date) and len(exp_date) >= 10 and exp_date in dates
        date_year = bool(exp_date) and any(d[:4] == exp_date[:4] for d in dates)
        sig = SIG_RE.findall(text[-2500:]) or SIG_RE.findall(text)
        sig_seen = ";".join(sorted({s.upper().replace("\n", " ") for s in sig}))[:120]
        first = words(b, 12)
        last = words(b, 12, tail=True)
        if num_hit and (date_exact or (date_year and not exp_date[5:])) and sig_seen:
            auto = "strong"
        elif num_hit and (date_exact or date_year or sig_seen):
            auto = "likely"
        elif num_hit or date_exact:
            auto = "weak"
        else:
            auto = "none"
        rows.append({
            "instrument_id": iid, "number": exp_num, "suffix": exp_suffix, "expected_date": exp_date,
            "expected_title": (idd.get("title") or p.get("title") or "")[:160], "file": p["file"], "folder": p["folder"],
            "sha256": p["sha256"], "pages": p["pages"], "text_kind": text_kind, "text_usable": p["text_usable"],
            "text_chars": len(text), "number_found": "yes" if num_hit else "no", "numbers_seen": number_seen,
            "date_exact": "yes" if date_exact else "no", "date_year": "yes" if date_year else "no",
            "dates_seen": ";".join(sorted(set(dates)))[:200], "signature_seen": sig_seen,
            "first_words": first, "last_words": last, "auto_verdict": auto,
            "tracker_blockers": tracker[iid]["blockers"],
        })
    with open(out / "CANDIDATES.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    summary = {"targets": len(rows), "auto_verdict": dict(Counter(r["auto_verdict"] for r in rows)),
               "text_kind": dict(Counter(r["text_kind"] for r in rows)),
               "below_4306": sum(1 for r in rows if r["number"] < 4306)}
    (out / "EXTRACT_SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))

    # Packets: each order's excerpt (head, tail, and every line that carries a number, date or signature word).
    pk = Path(a.packets)
    pk.mkdir(parents=True, exist_ok=True)
    for b0 in range(0, len(rows), a.batch):
        batch = rows[b0:b0 + a.batch]
        name = f"p{b0 // a.batch + 1:03d}"
        d = pk / name
        d.mkdir(exist_ok=True)
        with open(d / "ORDERS.jsonl", "w", encoding="utf-8") as f:
            for r in batch:
                p = pq[r["instrument_id"]]
                text = read_text(REPO / "jobs/pinakes-proquest-ingest/output" / p["text_path"])
                if r["text_kind"] == "pinakes_htr_backbone":
                    text = read_text(REPO / "jobs/pinakes-htr/output/texts" / f"EO_{p['number']}{p['suffix']}.txt")
                lines = text.splitlines()
                keep = [l for l in lines if DATE_RE.search(l) or SIG_RE.search(l) or NUM_TAG_RE.search(l) or NUM_RE.search(l)]
                f.write(json.dumps({
                    "instrument_id": r["instrument_id"], "expected_number": f"{r['number']}{r['suffix']}",
                    "expected_date": r["expected_date"], "expected_title": r["expected_title"],
                    "text_kind": r["text_kind"], "text_usable": r["text_usable"], "pages": r["pages"],
                    "pdf": str(Path(r["folder"]) / r["file"]),
                    "machine_read": {k: r[k] for k in ("number_found", "numbers_seen", "date_exact", "date_year", "dates_seen",
                                                        "signature_seen", "first_words", "last_words", "auto_verdict")},
                    "head": text[:1500], "tail": text[-1200:], "marker_lines": keep[:40],
                }, ensure_ascii=False) + "\n")
    print("packets:", (len(rows) + a.batch - 1) // a.batch, "in", pk)


if __name__ == "__main__":
    main()
