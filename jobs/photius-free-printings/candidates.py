"""Photius Lane 3: free official printings on the Internet Archive (R40), step 1.

Reads each source's djvu XML (one page per OBJECT), writes page texts, and finds candidate executive orders: pages with
an "EXECUTIVE ORDER" heading or a "[No. NNNN]" closing tag, the dates on them, and the identity-layer orders those
numbers or dates point to. Writes work/<source>/PAGES.json.gz, work/CANDIDATES.jsonl and the Opus packets.

    python -I jobs/photius-free-printings/candidates.py --ia SCRATCH/ia [--batch 10]
"""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "jobs" / "_lib"))
import eo_identity as ei  # noqa: E402

SOURCES = json.load(open(REPO / "jobs/photius-free-printings/data/SOURCES.json"))
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
MON = {m[:3].lower(): i + 1 for i, m in enumerate(MONTHS.split("|"))}
DATE = re.compile(rf"\b({MONTHS}|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\.?\s+(\d{{1,2}})\s*,?\s*(1[89]\d\d)\b", re.I)
HEAD = re.compile(r"EXECUTIVE\s+ORDER", re.I)
BLOCK_HEAD = re.compile(r"(EXECUTIVE\s+ORDER(?!\s+of\s+(?:Oct|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Nov|Dec))|Order\s+of\s+the\s+President,|Executive\s+order\s+of\s+the\s+President)", re.I)
TAG = re.compile(r"\[\s*No\.?\s*(\d{2,4})\s*(?:-\s*|\s)?([A-Za-z])?\s*\.?\s*[\]\}]")
NUMBERED = re.compile(r"Executive\s+Order\s*(?:No\.?|Number)?\s*(\d{2,4})\s*(?:-\s*|\s)?([A-Z])?\b", re.I)
PRES = ["LINCOLN", "JOHNSON", "GRANT", "HAYES", "GARFIELD", "ARTHUR", "CLEVELAND", "HARRISON", "McKINLEY", "ROOSEVELT", "TAFT",
        "WILSON", "HARDING", "COOLIDGE", "HOOVER"]
SIGN = re.compile(r"(THE\s+WHITE\s+HOUSE|EXECUTIVE\s+MANSION|" + "|".join(PRES) + r")", re.I)


def iso(m):
    mo = MON.get(m.group(1)[:3].lower())
    return f"{int(m.group(3)):04d}-{mo:02d}-{int(m.group(2)):02d}" if mo else ""


def pages_from_xml(path):
    pages = []
    try:
        for _, el in ET.iterparse(str(path), events=("end",)):
            if el.tag == "OBJECT":
                lines = []
                for line in el.iter("LINE"):
                    lines.append(" ".join((w.text or "").strip() for w in line.iter("WORD")))
                pages.append("\n".join(lines))
                el.clear()
    except ET.ParseError as exc:  # a truncated download keeps the pages read so far
        print("xml truncated", path.name, "after", len(pages), "pages:", exc)
    return pages


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ia", required=True)
    ap.add_argument("--batch", type=int, default=10)
    ap.add_argument("--work", default=str(REPO / "jobs/photius-free-printings/work"))
    a = ap.parse_args(argv)
    ia, work = Path(a.ia), Path(a.work)
    (work / "packets").mkdir(parents=True, exist_ok=True)
    ident = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "research/photius/IDENTITY_DATES.csv", encoding="utf-8"))}
    by_date = collections.defaultdict(list)
    for iid, r in ident.items():
        if len(r["date"]) >= 10:
            by_date[r["date"]].append(iid)
    tracker = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv", encoding="utf-8"))}

    cands = []
    for src in SOURCES["sources"]:
        sid = src["ia_id"]
        xmls = list((ia / sid).glob("*_djvu.xml"))
        if not xmls:
            print("no xml", sid)
            continue
        pages = pages_from_xml(xmls[0])
        (work / sid).mkdir(exist_ok=True)
        with gzip.open(work / sid / "PAGES.json.gz", "wt", encoding="utf-8") as f:
            json.dump(pages, f)
        n_c = 0
        for i, text in enumerate(pages):
            # blocks: from each heading ("EXECUTIVE ORDER", "Order of the President", "Executive order of the President")
            # to the next heading; index pages (many headings) are skipped
            starts = [m.start() for m in BLOCK_HEAD.finditer(text)]
            tags = list(TAG.finditer(text))
            if len(starts) > 6:
                continue
            if not starts and not tags and not (src.get("mode") == "number_hint" and NUMBERED.search(text)):
                continue
            blocks = []
            if starts:
                for k, st in enumerate(starts):
                    en = starts[k + 1] if k + 1 < len(starts) else min(len(text), st + 3500)
                    blocks.append(text[st:en])
            else:
                blocks.append(text)
            ids = {}
            for blk in blocks:
                nums = [(int(m.group(1)), (m.group(2) or "").upper()) for m in TAG.finditer(blk)] +                        [(int(m.group(1)), (m.group(2) or "").upper()) for m in NUMBERED.finditer(blk)]
                dates = [d for d in (iso(m) for m in DATE.finditer(blk)) if d]
                for n, suf in nums:
                    iid = ei.canon_id(n, suf)
                    if iid in ident and src["range_min"] <= n <= src["range_max"]:
                        ids.setdefault(iid, ("number", nums, dates))
                if not (SIGN.search(blk) or TAG.search(blk)):
                    continue  # a citation of an order is not a printing of it: the block must carry a signature block or tag
                for d in dates[:4]:  # the dateline sits near the heading or the end of a short order
                    for iid in by_date.get(d, []):
                        pe = ei.parse_eo_id(iid)
                        if pe and src["range_min"] <= pe[0] <= src["range_max"]:
                            ids.setdefault(iid, ("date", nums, dates))
            for iid, (by, nums, dates) in sorted(ids.items()):
                t = tracker.get(iid, {})
                needs = t.get("step_original_text") != "done" or t.get("text_evidence_tier") == "transcription_dependent"
                if not needs:
                    continue
                cands.append({
                    "source": sid, "source_title": src["title"], "page_index": i, "leaf": i,
                    "instrument_id": iid, "expected_date": ident[iid]["date"], "expected_title": ident[iid]["title"][:160],
                    "numbers_on_page": sorted({f"{n}{s_}" for n, s_ in nums})[:12], "dates_on_page": sorted(set(dates))[:12],
                    "heading": bool(starts), "closing_tag": bool(tags), "signature": bool(SIGN.search(text)),
                    "by": by, "tracker_step": t.get("step_original_text", ""), "tracker_tier": t.get("text_evidence_tier", ""),
                })
                n_c += 1
        print(sid, "pages", len(pages), "candidates", n_c, flush=True)

    # one candidate row per (order, source, page); packets group by source
    with open(work / "CANDIDATES.jsonl", "w", encoding="utf-8") as f:
        for c in cands:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    # Prefer orders whose text step is open; include all, flag the rest
    items = []
    seen = set()
    rank = lambda c: (0 if c["by"] == "number" else 1, 0 if c["closing_tag"] else 1, 0 if c["signature"] else 1, c["page_index"])
    for c in sorted(cands, key=rank):
        key = (c["source"], c["instrument_id"])  # one page per order per source: the best-looking one
        if key in seen:
            continue
        seen.add(key)
        pages = json.load(gzip.open(work / c["source"] / "PAGES.json.gz", "rt", encoding="utf-8"))
        c["page_text"] = pages[c["page_index"]][:7000]
        c["next_page_text"] = pages[c["page_index"] + 1][:3000] if c["page_index"] + 1 < len(pages) else ""
        c["prev_page_tail"] = pages[c["page_index"] - 1][-1500:] if c["page_index"] > 0 else ""
        c["page_image_url"] = f"https://archive.org/download/{c['source']}/page/n{c['leaf']}.jpg"
        items.append(c)
    items.sort(key=lambda c: (c["source"], c["page_index"]))
    for b0 in range(0, len(items), a.batch):
        d = work / "packets" / f"f{b0 // a.batch + 1:03d}"
        d.mkdir(exist_ok=True)
        with open(d / "ORDERS.jsonl", "w", encoding="utf-8") as f:
            for it in items[b0:b0 + a.batch]:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    summ = {"candidates": len(cands), "items": len(items), "packets": (len(items) + a.batch - 1) // a.batch,
            "by_source": dict(collections.Counter(c["source"] for c in items)),
            "distinct_orders": len({c["instrument_id"] for c in items}),
            "distinct_orders_text_step_open": len({c["instrument_id"] for c in items if c["tracker_step"] != "done"})}
    json.dump(summ, open(work / "CANDIDATES_SUMMARY.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
