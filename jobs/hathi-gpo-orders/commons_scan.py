"""Read offered public-domain GPO scans and OCR locally when no text is embedded."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading

sys.dont_write_bytecode = True
from harvest import Harvest, HERE, OUT, ROOT, hunt, sha, iid, append, fr_pages
from djvu_render import DjvuBook


def download(harvest, low, high):
    title = f"Executive_Orders_{low}-{high}.djvu"
    file_page = "https://commons.wikimedia.org/wiki/File:" + title
    page_path = OUT / "discovery" / (title + ".html")
    if not page_path.exists():
        r = harvest.net.fetch("commons_gpo", file_page)
        page_path.write_bytes(r["body"])
    raw = page_path.read_text(encoding="utf-8")
    if not ("Public domain" in raw and "U.S._government" in raw):
        raise ValueError("public_domain_government_notice_not_verified")
    match = re.search(r'<a[^>]+href="([^"]+)"[^>]*>Original file', raw)
    if not match:
        raise ValueError("no_offered_original_file_download")
    url = html.unescape(match[1])
    assert url.startswith("https://upload.wikimedia.org/") and ".djvu" in url
    dest = OUT / "books" / title
    record_path = OUT / "books" / (title + ".json")
    if record_path.exists() and dest.exists():
        record = json.loads(record_path.read_text())
        assert sha(dest.read_bytes()) == record["sha256"]
    else:
        if dest.exists() and title == "Executive_Orders_6071-6250.djvu":
            # The already completed one-volume discovery download is reused.
            prior = json.loads((OUT / "books/Executive_Orders_6071-6250_download.json").read_text())
            data, digest = dest.read_bytes(), prior["sha256"]
            assert sha(data) == digest
        else:
            r = harvest.net.fetch("commons_gpo", url)
            data, digest = r["body"], r["sha256"]
            assert data.startswith(b"AT&TFORM")
            dest.write_bytes(data)
        revision = re.search(r'"wgRevisionId"\s*:\s*(\d+)', raw)
        record = {"volume": title, "url": file_page, "source_bytes_url": url, "sha256": digest,
                  "bytes": len(data), "file_page_sha256": sha(page_path.read_bytes()),
                  "file_page_revision": revision[1] if revision else None,
                  "license": "Public domain, work of the United States government, as declared on Commons",
                  "retrieved_utc": datetime.now(timezone.utc).isoformat()}
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return dest, record


def page_texts(path, record, workers=4):
    key = path.name
    cache = HERE / ".cache/ocr-pages" / key
    cache.mkdir(parents=True, exist_ok=True)
    local = threading.local()
    os.environ["OMP_THREAD_LIMIT"] = "1"
    sys.path.insert(0, str(HERE / ".cache/ocr/python"))
    import tesserocr
    first = DjvuBook(path)
    count = first.pages
    first.close()

    def one(number):
        result = cache / f"{number:05d}.txt"
        if result.exists():
            return number, result.read_text(encoding="utf-8")
        if not hasattr(local, "book"):
            local.book = DjvuBook(path)
            local.api = tesserocr.PyTessBaseAPI(path=str(HERE / ".cache/ocr/tessdata"), lang="eng", psm=tesserocr.PSM.AUTO)
        image = cache / f"{number:05d}.pgm"
        try:
            image.write_bytes(local.book.render(number))
            local.api.SetImageFile(str(image))
            text = local.api.GetUTF8Text()
            result.write_text(text, encoding="utf-8")
            return number, text
        except Exception as exc:
            return number, "[PAGE OCR FAILED: " + str(exc) + "]"
        finally:
            image.unlink(missing_ok=True)

    pages = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for number, text in executor.map(one, range(1, count + 1)):
            pages.append((number, text))
            if number % 40 == 0:
                print(json.dumps({"book": key, "ocr_pages_done": number, "total_pages": count}), flush=True)
    # Retain machine-read government pages as a reproducible source derivative.
    dump = OUT / "books" / (key + "_ocr.jsonl.gz")
    with gzip.open(dump, "wt", encoding="utf-8") as fh:
        for number, text in pages:
            fh.write(json.dumps({"image": number, "text": text}, ensure_ascii=False) + "\n")
    record.update(ocr_engine="Tesseract 5.5.3 via tesserocr 2.11.0; eng tessdata_fast 4.1.0",
                  ocr_pages=count, ocr_page_dump=dump.relative_to(OUT).as_posix(),
                  ocr_page_dump_sha256=sha(dump.read_bytes()))
    (OUT / "books" / (key + ".json")).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return pages


def extract(harvest, pages, record, low, high, route="commons_gpo_ocr"):
    full, positions = "", []
    for number, text in pages:
        positions.append((len(full), number))
        full += text + "\n\f\n"
    # A standalone bracketed number at the foot of the actual signed text,
    # not a citation within its body or a table of contents.
    pattern = re.compile(r"(?im)^\s*[\[(]\s*No\.?\s*(\d{4}(?:\s*[-]?\s*[A-Z])?)\s*[\])]\s*\.?\s*$")
    tags = list(pattern.finditer(full))
    saved = 0
    previous_end = 0
    for tag in tags:
        identity = iid(tag[1])
        if not low <= int(re.match(r"EO:(\d+)", identity)[1]) <= high:
            continue
        region = full[previous_end:tag.end()]
        offset = previous_end
        previous_end = tag.end()
        if identity not in harvest.missing:
            continue
        # The fr-originals generic heading recognizer is reused on this
        # pre-Federal-Register printed layout; the closing tag identifies ID.
        heads = list(fr_pages.HEADING_ANY.finditer(region))
        # GPO headings are standalone; inline references are not boundaries.
        real = [m for m in heads if len(region[region.rfind("\n", 0, m.start()) + 1:m.start()].strip()) == 0
                and len(region[m.end():region.find("\n", m.end()) if "\n" in region[m.end():] else len(region)].strip()) < 10]
        signatures = list(re.finditer(r"(?im)^\s*(?:FRANKLIN\s+D\W*\s*ROOSEVELT|HERBERT\s+HOOVER)\s*\.?\s*$", region))
        if not signatures:
            harvest.failure(route, "signature_not_read_before_closing_tag", identity, volume=record["volume"])
            continue
        if real:
            local_start = real[0].start()
            method = "generic_order_heading_and_exact_closing_number"
        elif len(signatures) == 1 and offset > 0:
            # Gothic headings can be unreadable to the English OCR model.
            # A single standalone signature between consecutive numbered ends
            # gives a complete source passage; preserve its furniture and flag
            # it for page checking rather than silently repairing its letters.
            imprints = list(re.finditer(r"(?im)^.*GOVERNMENT\s+PRINTING\s+OFFICE.*$", region[:signatures[0].start()]))
            local_start = imprints[-1].end() if imprints else 0
            method = "consecutive_exact_numbered_ends_and_one_standalone_signature; Gothic heading needs page check"
        else:
            harvest.failure(route, "ambiguous_order_start_after_OCR", identity, volume=record["volume"])
            continue
        body = region[local_start:]
        start = offset + local_start
        a = max(n for pos, n in positions if pos <= start)
        b = max(n for pos, n in positions if pos <= tag.end())
        source = {k: record[k] for k in ("url", "sha256", "source_bytes_url", "volume", "retrieved_utc")}
        source.update(scan_image_start=a, scan_image_end=b,
                      page_or_item=f"{record['volume']}; scanned pages {a}-{b}; closing number {identity[3:]}",
                      page_url=(record["url"] + "/page/n" + str(a - 1) + "/mode/1up" if "archive.org/details/" in record["url"] else record["url"] + "?page=" + str(a)),
                      file_page_revision=record.get("file_page_revision"),
                      source_artifact=record.get("source_artifact", "books/" + record["volume"]), identity_method=method, needs_page_check=True,
                      notes="Machine-read printed copy, identified by exact closing number and printed signature; boundary method recorded separately. Page furniture or adjacent order context may remain. OCR is not authenticated original text.")
        saved += harvest.save(identity, body, route, source, copy_kind=record.get("copy_kind", "machine_read_government_printed_copy"))
    return {"route": route, "volume": record["volume"], "number_tags": len(tags), "saved": saved, "remaining": len(harvest.missing)}


def main():
    harvest = Harvest()
    volumes = [(5800, 6070), (6071, 6250), (6251, 6479), (6480, 6689), (6690, 6935), (6936, 7081), (7082, 7261), (7262, 8027)]
    for low, high in volumes:
        if not any(low <= int(re.match(r"EO:(\d+)", i)[1]) <= high for i in harvest.missing):
            continue
        try:
            path, record = download(harvest, low, high)
            pages = page_texts(path, record)
            result = extract(harvest, pages, record, low, high)
            append(OUT / "ROUTE_RESULTS.jsonl", result)
            print(json.dumps(result), flush=True)
        except Exception as exc:
            harvest.failure("commons_gpo_ocr", str(exc), volume=f"{low}-{high}")
            print(json.dumps({"volume": f"{low}-{high}", "failed": str(exc)}), flush=True)


if __name__ == "__main__":
    main()
