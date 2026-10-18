"""Read existing volunteer scan-page transcriptions for residual order ranges."""
import csv
import html
import json
import re
from urllib.parse import quote
from harvest import Harvest, HERE, OUT, read_lines, append, iid, fetch_ladder


def main():
    h = Harvest()
    queue = list(csv.DictReader((OUT / "PAGE_CHECK_QUEUE.csv").open(encoding="utf-8")))
    volumes = [(5800, 6070), (6071, 6250), (6251, 6479), (6480, 6689), (6690, 6935), (6936, 7081), (7082, 7261), (7262, 8027)]
    attempts = {r.get("source_url") for r in read_lines(OUT / "EXTRACTION_FAILURES.jsonl") if r["route"] == "wikisource_scan_pages"}
    originals = OUT / "originals"
    originals.mkdir(exist_ok=True)
    for low, high in volumes:
        if not any(low <= int(re.match(r"EO:(\d+)", i)[1]) <= high for i in h.missing):
            continue
        book = f"Executive_Orders_{low}-{high}.djvu"
        url = "https://en.wikisource.org/wiki/Index:" + book
        index_path = OUT / "discovery" / f"wikisource_index_{low}-{high}.html"
        try:
            if not index_path.exists():
                if url in attempts:
                    continue
                index_path.write_bytes(h.net.fetch("wikisource_scan_pages", url)["body"])
            raw = index_path.read_text(encoding="utf-8")
            links = {}
            for tag, href, number in re.findall(r'(<a\b[^>]*href="(/wiki/Page:[^"]+/(\d+))"[^>]*>)', raw):
                quality = re.search(r'prp-pagequality-([1-4])\b', tag)
                if quality:
                    links[int(number)] = ("https://en.wikisource.org" + html.unescape(href), int(quality[1]))
            wanted = set()
            for row in queue:
                if row["volume"] == book and row["instrument_id"] in h.missing:
                    for p in map(int, row["candidate_scan_pages"].split(";")):
                        if p > 8:  # contents pages are not order texts
                            wanted.update(range(max(1, p - 2), p + 3))
            # Neighbouring already-held order pages are navigation hints only.
            # The downloaded transcription still needs its own exact number.
            held = [r for r in h.sources.values() if r.get("volume") == book]
            for identity in h.missing:
                number = int(re.match(r"EO:(\d+)", identity)[1])
                if not low <= number <= high:
                    continue
                before = [r for r in held if int(re.match(r"EO:(\d+)", r["instrument_ids"][0])[1]) < number]
                after = [r for r in held if int(re.match(r"EO:(\d+)", r["instrument_ids"][0])[1]) > number]
                if before and after:
                    a = max(before, key=lambda r: int(re.match(r"EO:(\d+)", r["instrument_ids"][0])[1]))["scan_image_end"]
                    b = min(after, key=lambda r: int(re.match(r"EO:(\d+)", r["instrument_ids"][0])[1]))["scan_image_start"]
                    if 0 < b - a < 20:
                        wanted.update(range(a, b + 1))
            pages, receipts = {}, {}
            for number in sorted(wanted & links.keys()):
                page_url, quality = links[number]
                path = originals / f"WikiPage_{low}-{high}_{number}.html"
                try:
                    if path.exists():
                        raw_bytes = path.read_bytes()
                        from harvest import sha
                        result = {"body": raw_bytes, "sha256": sha(raw_bytes)}
                    else:
                        result = h.net.fetch("wikisource_scan_pages", page_url)
                        path.write_bytes(result["body"])
                    raw_page = result["body"].decode("utf-8")
                    revision = re.search(r'"wgRevisionId"\s*:\s*(\d+)', raw_page)
                    if not revision or revision[1] == "0":
                        raise ValueError("No saved scan-page revision")
                    pages[number] = fetch_ladder.html_to_text(raw_page)
                    receipts[number] = {"url": page_url, "sha256": result["sha256"], "revision_id": revision[1],
                        "revision_url": "https://en.wikisource.org/w/index.php?title=" + quote("Page:" + book + "/" + str(number)) + "&oldid=" + revision[1],
                        "proofread_page_quality": quality, "source_artifact": path.relative_to(OUT).as_posix()}
                except Exception as exc:
                    h.failure("wikisource_scan_pages", str(exc), source_url=page_url)
            full, spans = "", []
            for number in sorted(pages):
                spans.append((len(full), number))
                full += pages[number] + "\n\f\n"
            saved = 0
            ends = list(re.finditer(r'(?im)^\s*[\[(]\s*No[.,]?\s*(\d{4}(?:\s*-?\s*[A-Z])?)\s*[\])]\s*$', full))
            for tag in ends:
                identity = iid(tag[1])
                if identity not in h.missing:
                    continue
                earlier_end = max((t.end() for t in ends if t.end() <= tag.start()), default=0)
                heads = list(re.finditer(r'(?im)^\s*Executive\s+Order\s*$', full[earlier_end:tag.start()]))
                if not heads:
                    h.failure("wikisource_scan_pages", "No complete transcribed order heading", identity, volume=book)
                    continue
                start = earlier_end + heads[-1].start()
                a = max(n for off, n in spans if off <= start)
                b = max(n for off, n in spans if off <= tag.end())
                if any(n not in pages for n in range(a, b + 1)):
                    h.failure("wikisource_scan_pages", "Gap in transcribed pages", identity, volume=book)
                    continue
                text = full[start:tag.end()]
                if not re.search(r'The\s+White\s+House', text, re.I):
                    h.failure("wikisource_scan_pages", "No White House dateline in transcribed passage", identity, volume=book)
                    continue
                primary = receipts[a]
                source = {**primary, "volume": book, "page_or_item": f"Volunteer transcription of {book}, scan pages {a}-{b}; exact closing number {identity[3:]}",
                          "page_url": primary["url"], "scan_image_start": a, "scan_image_end": b,
                          "archival_id": "wikisource:en:revision/" + primary["revision_id"],
                          "transcribed_pages": [receipts[n] for n in range(a, b + 1)],
                          "notes": "Volunteer scan-page transcription, possibly unvalidated or with omissions/typos. Exact order heading and closing number checked; scan link and every page revision retained. Not original."}
                saved += h.save(identity, text, "wikisource_scan_pages", source, "website_transcription")
            result = {"route": "wikisource_scan_pages", "volume": book, "existing_text_pages": len(links),
                      "candidate_pages_checked": len(pages), "saved": saved, "remaining": len(h.missing)}
            append(OUT / "ROUTE_RESULTS.jsonl", result)
            print(json.dumps(result), flush=True)
        except Exception as exc:
            h.failure("wikisource_scan_pages", str(exc), source_url=url)
            print(json.dumps({"route": "wikisource_scan_pages", "volume": book, "failed": str(exc)}), flush=True)


if __name__ == "__main__":
    main()
