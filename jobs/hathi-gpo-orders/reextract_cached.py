"""Offline source-boundary recovery for still-missing orders; no new downloads."""
import gzip
import json
from harvest import Harvest, OUT, append
from commons_scan import extract


def main():
    h = Harvest()
    for ident in ("4731703.proc.001.umich.edu", "4731703.proc.002.umich.edu"):
        rec = json.loads((OUT / "books" / (ident + ".json")).read_text())
        with gzip.open(OUT / "books" / (ident + "_pages.jsonl.gz"), "rt", encoding="utf-8") as fh:
            pages = [(r["image"], r["text"]) for r in (json.loads(s) for s in fh)]
        c = rec["custody"]
        source = {"volume": ident, "url": c["item_url"], "sha256": c["page_text_sha256"],
                  "source_bytes_url": c["page_text_url"], "retrieved_utc": "original volume acquisition; see custody log",
                  "source_artifact": "books/" + ident + "_pages.jsonl.gz"}
        result = extract(h, pages, source, 5076, 6070, route="ia_hoover")
        append(OUT / "ROUTE_RESULTS.jsonl", result)
        print(json.dumps(result), flush=True)
    for low, high in ((5800, 6070), (6071, 6250), (6251, 6479), (6480, 6689), (6690, 6935), (6936, 7081), (7082, 7261), (7262, 8027)):
        title = f"Executive_Orders_{low}-{high}.djvu"
        rec_path = OUT / "books" / (title + ".json")
        dump = OUT / "books" / (title + "_ocr.jsonl.gz")
        if not (rec_path.exists() and dump.exists()):
            continue
        source = json.loads(rec_path.read_text())
        with gzip.open(dump, "rt", encoding="utf-8") as fh:
            pages = [(r["image"], r["text"]) for r in (json.loads(s) for s in fh)]
        result = extract(h, pages, source, low, high)
        append(OUT / "ROUTE_RESULTS.jsonl", result)
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
