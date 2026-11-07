"""Build the Opus page-check packets for the GPO volumes: render each queued order's pages (private cache) and write
ORDERS.jsonl per packet with the located text, the expected facts and the render paths.

    python -I jobs/photius-gpo-volumes/check_packets.py --renders research/owner-inbox/hathi-gpo/renders [--batch 12]
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.append(r"C:\Users\danie\AppData\Roaming\Python\Python312\site-packages")
REPO = Path(__file__).resolve().parents[2]
INBOX = Path(r"C:\Users\danie\Projects\Executive-Orders\research\owner-inbox\hathi-gpo")
MAX_PAGES = 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", default=str(INBOX / "renders"))
    ap.add_argument("--batch", type=int, default=12)
    ap.add_argument("--packets", default=str(REPO / "research/excavator/photius-gpo/packets"))
    a = ap.parse_args()
    import pypdfium2 as pdfium
    renders, packets = Path(a.renders), Path(a.packets)
    renders.mkdir(parents=True, exist_ok=True)
    packets.mkdir(parents=True, exist_ok=True)
    out = REPO / "jobs/photius-gpo-volumes/output"
    orders = {r["instrument_id"]: r for r in csv.DictReader(open(out / "ORDERS.csv", encoding="utf-8"))}
    ident = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "research/photius/IDENTITY_DATES.csv", encoding="utf-8"))}
    queue = list(csv.DictReader(open(out / "PAGE_CHECK_QUEUE.csv", encoding="utf-8")))
    docs = {}
    items = []
    for q in queue:
        o = orders[q["instrument_id"]]
        htid = o["htid"]
        if htid not in docs:
            docs[htid] = pdfium.PdfDocument(str(INBOX / f"{htid}.pdf"))
        first, last = int(o["pdf_page_first"]), int(o["pdf_page_last"])
        pages = list(range(max(first, last - MAX_PAGES + 1), last + 1))  # the tag page is the last; keep it in view
        paths = []
        for p in pages:
            png = renders / f"{htid}_p{p:05d}.png"
            if not png.exists():
                docs[htid][p - 1].render(scale=150 / 72, grayscale=True).to_pil().save(png, format="PNG", compress_level=3)
            paths.append(str(png))
        text = (out / o["text_path"]).read_text(encoding="utf-8", errors="replace")
        items.append({
            "instrument_id": o["instrument_id"], "expected_number": f"{o['number']}{o['suffix']}", "identity_date": o["identity_date"],
            "expected_title": ident.get(o["instrument_id"], {}).get("title", ""), "htid": htid, "pdf_pages": f"{first}-{last}",
            "pages_rendered": pages, "renders": paths, "machine_dateline": o["dateline_seen"], "date_test": o["date_test"],
            "alignment_verdict": o["verdict"], "alignment_reasons": o["reasons"], "why_queued": q["why_queued"],
            "gap_before": o["gap_before"], "text_head": text[:2500], "text_tail": text[-1500:],
        })
    for b0 in range(0, len(items), a.batch):
        d = packets / f"g{b0 // a.batch + 1:03d}"
        d.mkdir(exist_ok=True)
        with open(d / "ORDERS.jsonl", "w", encoding="utf-8") as f:
            for it in items[b0:b0 + a.batch]:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print("items", len(items), "packets", (len(items) + a.batch - 1) // a.batch, "renders", len(list(renders.glob("*.png"))))


if __name__ == "__main__":
    main()
