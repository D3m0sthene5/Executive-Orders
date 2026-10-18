"""Offline import of lawfully supplied source files, with mandatory source metadata."""
import argparse
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
from harvest import HERE, OUT, Harvest, hunt, fetch_ladder, fr_pages, sha, append
from commons_scan import page_texts, extract


def pdf_pages(path):
    n, pages = fetch_ladder.pdf_pages_text(path)
    if sum(len(t.strip()) for _, t in pages) > 500:
        return pages
    # Same Tesseract/Poppler image-OCR route used by the existing media job,
    # with its tools and temporary files confined to this producer's cache.
    pdftoppm = os.environ.get("PDFTOPPM") or shutil.which("pdftoppm")
    if not pdftoppm and os.name == "nt":
        candidate = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe"
        if candidate.exists():
            pdftoppm = str(candidate)
    if not pdftoppm:
        raise ValueError("Scanned PDF needs pdftoppm; set PDFTOPPM to the installed tool")
    sys.path.insert(0, str(HERE / ".cache/ocr/python"))
    import tesserocr
    cache = HERE / ".cache/local-pdf" / sha(path.read_bytes())[:16]
    cache.mkdir(parents=True, exist_ok=True)
    results = []
    with tesserocr.PyTessBaseAPI(path=str(HERE / ".cache/ocr/tessdata"), lang="eng") as api:
        for number in range(1, n + 1):
            prefix = cache / f"page{number:05d}"
            text_path = prefix.with_suffix(".txt")
            if text_path.exists():
                text = text_path.read_text(encoding="utf-8")
            else:
                subprocess.run([pdftoppm, "-f", str(number), "-l", str(number), "-singlefile", "-r", "200", "-gray", str(path), str(prefix)], check=True, capture_output=True)
                image = prefix.with_suffix(".pgm")
                api.SetImageFile(str(image))
                text = api.GetUTF8Text()
                text_path.write_text(text, encoding="utf-8")
                image.unlink(missing_ok=True)
            results.append((number, text))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", type=Path, default=HERE / "incoming")
    args = ap.parse_args()
    folder = args.folder.resolve()
    assert folder.is_relative_to(HERE.resolve()), "Keep supplied files inside this job's folder"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8-sig"))
    harvest = Harvest()
    for item in manifest["files"]:
        try:
            path = (folder / item["path"]).resolve()
            assert path.is_relative_to(folder) and path.is_file()
            assert item.get("source_url", "").startswith("https://") and item.get("permission_note", "").strip()
            assert urlsplit(item["source_url"]).hostname not in {"example.edu", "example.org", "example.com"}, "Replace the example source URL"
            raw = path.read_bytes()
            digest = sha(raw)
            record = {"volume": path.name, "url": item["source_url"], "sha256": digest,
                      "source_bytes_url": item["source_url"], "retrieved_utc": item.get("downloaded_utc", "human supplied; date not recorded"),
                      "permission_note": item["permission_note"], "source_artifact": "../" + path.relative_to(HERE).as_posix(),
                      "copy_kind": item.get("copy_kind", "machine_read_government_printed_copy")}
            kind = item["format"]
            if kind == "orders_jsonl":
                for row in (json.loads(s) for s in raw.decode("utf-8-sig").splitlines() if s.strip()):
                    identity, text = row["instrument_id"], row["text"]
                    if identity not in harvest.missing:
                        continue
                    loc = fr_pages.locate_order([text], identity[3:])
                    if not loc["found"] or not loc.get("marker_kind"):
                        harvest.failure("human_import", "order_number_not_identified_in_supplied_text", identity)
                        continue
                    source = {**record, "url": row.get("url", item["source_url"]), "page_or_item": row.get("page_or_item", "supplied per-order text record")}
                    harvest.save(identity, text, "human_import", source, item.get("copy_kind", "website_transcription"))
                continue
            if kind == "pdf":
                pages = pdf_pages(path)
            elif kind == "djvu":
                pages = page_texts(path, record)
            elif kind == "djvu_xml":
                pages = hunt.djvu_pages(raw)
            elif kind == "pages_jsonl":
                decoded = gzip.decompress(raw) if path.suffix == ".gz" else raw
                rows = [json.loads(s) for s in decoded.decode("utf-8-sig").splitlines() if s.strip()]
                pages = [(int(r.get("image", r.get("page"))), r["text"]) for r in rows]
            elif kind == "text":
                pages = list(enumerate(raw.decode("utf-8-sig").split("\f"), 1))
            else:
                raise ValueError("Unsupported format " + kind)
            result = extract(harvest, pages, record, item.get("range_min", 5076), item.get("range_max", 7531), route="human_import")
            append(OUT / "ROUTE_RESULTS.jsonl", result)
            print(json.dumps(result), flush=True)
        except Exception as exc:
            harvest.failure("human_import", str(exc), supplied_file=item.get("path"))
            print(json.dumps({"file": item.get("path"), "failed": str(exc)}), flush=True)


if __name__ == "__main__":
    main()
