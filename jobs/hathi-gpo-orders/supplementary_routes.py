"""Bounded remaining-source discovery; only exact, attributed order passages saved."""
import argparse
import html
import json
from pathlib import Path
import re
import gzip
import csv
from urllib.parse import urlencode, urljoin

from harvest import Harvest, HERE, OUT, ROOT, append, sha, fetch_ladder
from commons_scan import extract


class Supplements:
    def __init__(self):
        self.h = Harvest()

    def fetch(self, route, name, url):
        result = self.h.net.fetch(route, url)
        (OUT / "discovery" / name).write_bytes(result["body"])
        return result

    def fdr_books(self):
        for ident in ("4925381.1933.001.umich.edu", "4925383.1934.001.umich.edu", "4925387.1935.001.umich.edu", "4925988.1936.001.umich.edu"):
            try:
                record, pages, pm = self.h.book(ident, {"title_words": ["public", "papers", "roosevelt"], "year_any": [1938], "publisher_any": ["random house"]}, "ia_fdr_reprints", keep_raw=False)
                custody = record["custody"]
                source = {"volume": ident, "url": custody["item_url"], "source_bytes_url": custody["page_text_url"],
                          "sha256": custody["page_text_sha256"], "retrieved_utc": record.get("retrieved_utc", "recorded in download log"),
                          "source_artifact": None, "copy_kind": "machine_read_reprint_of_government_order"}
                result = extract(self.h, pages, source, 6071, 7531, route="ia_fdr_reprints")
                append(OUT / "ROUTE_RESULTS.jsonl", result)
                print(json.dumps(result), flush=True)
            except Exception as exc:
                self.h.failure("ia_fdr_reprints", str(exc), book=ident)

    def fdr_captioned_entries(self):
        route = "ia_fdr_reprints"
        for ident in ("4925381.1933.001.umich.edu", "4925383.1934.001.umich.edu", "4925387.1935.001.umich.edu", "4925988.1936.001.umich.edu"):
            path = HERE / ".cache/books" / (ident + "_pages.jsonl.gz")
            if not path.exists():
                continue
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                pages = [json.loads(s) for s in fh]
            full, positions = "", []
            for page in pages:
                positions.append((len(full), page["image"]))
                full += page["text"] + "\n\f\n"
            entries = list(re.finditer(r"(?m)^\s*\d{1,3}[A-Z]?\s+[\[({]", full))
            saved = 0
            for n, entry in enumerate(entries):
                image = max(p for off, p in positions if off <= entry.start())
                if image < 35:  # contents and introductory finding aids
                    continue
                end = entries[n + 1].start() if n + 1 < len(entries) else len(full)
                chunk = full[entry.start():end]
                marker = re.search(r"Exec(?:-\s*)?utive\s+Or(?:-\s*)?der\s+No\.?\s*(\d{4}(?:-?[A-Z])?)", chunk[:700], re.I)
                if not marker:
                    continue
                identity = "EO:" + marker[1].replace("-", "").upper()
                if identity not in self.h.missing:
                    continue
                date = re.search(r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+19\d\d", chunk[marker.end():marker.end() + 150], re.I)
                if not date:
                    self.h.failure(route, "caption_has_no_readable_date", identity, volume=ident)
                    continue
                begin = marker.end() + date.end()
                note = re.search(r"(?m)^NOTE\s*[:.]", chunk[begin:])
                body = chunk[begin:begin + note.start()] if note else chunk[begin:]
                if re.search(r"(?:\.\s*){3,}|…", body):
                    self.h.failure(route, "reprint_contains_ellipsis_not_counted_as_full_order", identity, volume=ident)
                    continue
                if len(body.strip()) < 100 or len(body) > 50000:
                    self.h.failure(route, "reprint_boundary_not_confident", identity, volume=ident)
                    continue
                rec = json.loads((OUT / "books" / (ident + ".json")).read_text())
                c = rec["custody"]
                last = max(p for off, p in positions if off <= entry.start() + begin + len(body))
                source = {"url": c["item_url"], "sha256": c["page_text_sha256"], "source_bytes_url": c["page_text_url"],
                          "volume": ident, "scan_image_start": image, "scan_image_end": last,
                          "page_or_item": f"{ident}; exact dated caption for {identity}; scanned pages {image}-{last}",
                          "entry_caption": chunk[:begin].strip(), "page_url": c["item_url"] + "/page/n" + str(image - 1) + "/mode/1up",
                          "notes": "Government-order body in a commercial Public Papers reprint. Editorial NOTE and visibly abbreviated/ellipsis entries excluded; source OCR unchanged. Not authenticated as original."}
                saved += self.h.save(identity, body, route, source, "machine_read_reprint_of_government_order")
            append(OUT / "ROUTE_RESULTS.jsonl", {"route": route, "volume": ident, "captioned_order_texts_saved": saved, "remaining": len(self.h.missing)})
            print(json.dumps({"route": route, "volume": ident, "saved": saved, "remaining": len(self.h.missing)}), flush=True)

    def agency_books(self):
        for ident, words in (("codeoffaircompet2975unit", ["code", "competition"]), ("measuves00cana", ["vessels"]), ("publicactsnos27800unit", ["public", "acts"])):
            try:
                rec, pages, pm = self.h.book(ident, {"title_words": words, "year_any": [1933, 1937]}, "agency_reprints")
                c = rec["custody"]
                record = {"volume": ident, "url": c["item_url"], "sha256": c["page_text_sha256"],
                          "source_bytes_url": c["page_text_url"], "retrieved_utc": "see route log", "source_artifact": "books/" + ident + "_pages.jsonl.gz"}
                result = extract(self.h, pages, record, 5076, 7531, route="agency_reprints")
                append(OUT / "ROUTE_RESULTS.jsonl", result)
                print(json.dumps(result), flush=True)
            except Exception as exc:
                self.h.failure("agency_reprints", str(exc), book=ident)

    def fraser(self):
        route = "fraser"
        sources = []
        for row in (json.loads(s) for s in (OUT / "CATALOG_ROUTE_RESULTS.jsonl").read_text().splitlines()):
            if row["route"] == route:
                sources += [x for x in row["links"] if x.startswith("https://fraser.stlouisfed.org/title/")]
        count = 0
        for url in list(dict.fromkeys(sources)):
            try:
                result = self.h.net.fetch(route, url)
                raw = result["body"].decode("utf-8", "replace")
                links = [urljoin(url, html.unescape(x)) for x in re.findall(r'href=["\']([^"\']+)', raw)]
                # Current FRASER puts the public PDF offer in scholarly
                # citation metadata consumed by its viewer, not an <a> tag.
                links += [html.unescape(x) for x in re.findall(r'<meta\s+name="citation_pdf_url"\s+content="([^"]+)"', raw)]
                offered = [x for x in links if x.startswith("https://fraser.stlouisfed.org/") and (x.endswith("/fulltext") or x.endswith(".pdf"))]
                if not offered:
                    self.h.failure(route, "no_offered_fulltext_or_pdf_on_result", source_url=url)
                    continue
                for full_url in sorted(set(offered))[:2]:
                    r = self.h.net.fetch(route, full_url)
                    if r["body"].startswith(b"%PDF-"):
                        p = HERE / ".cache" / (r["sha256"] + ".pdf")
                        p.write_bytes(r["body"])
                        _, pages = fetch_ladder.pdf_pages_text(p)
                    else:
                        text = fetch_ladder.html_to_text(r["body"].decode("utf-8", "replace"))
                        pages = [(1, text)]
                    rec = {"volume": url.rstrip("/").rsplit("/", 1)[-1], "url": full_url,
                           "sha256": r["sha256"], "source_bytes_url": full_url, "retrieved_utc": "see route log",
                           "source_artifact": None, "copy_kind": "government_printed_reproduction"}
                    recovered = extract(self.h, pages, rec, 5076, 7531, route=route)
                    count += recovered["saved"]
                    append(OUT / "ROUTE_RESULTS.jsonl", recovered)
                print(json.dumps({"route": route, "result_checked": url, "saved": count}), flush=True)
            except Exception as exc:
                self.h.failure(route, str(exc), source_url=url)
        append(OUT / "ROUTE_RESULTS.jsonl", {"route": route, "search_results_checked": len(set(sources)), "saved": count})

    def loc(self):
        route = "loc_cfr"
        try:
            url = "https://www.loc.gov/collections/code-of-federal-regulations/?" + urlencode({"fo": "json", "q": "executive orders", "c": 150, "dates": "1938"})
            data = json.loads(self.fetch(route, "loc_executive_orders.json", url)["body"])
            candidates = [{"id": row["id"], "title": row.get("title")} for row in data.get("results", [])]
            append(OUT / "ROUTE_RESULTS.jsonl", {"route": route, "query": url, "candidate_items": candidates})
            downloaded = set()
            for row in data.get("results", []):
                title = row.get("title", "")
                if not ("3 C.F.R." in title and "Executive Orders" in title):
                    continue
                # Tables and indexes are retained as finding aids, not texts.
                item_url = row["id"].replace("http://", "https://")
                metadata = json.loads(self.fetch(route, row["id"].rstrip("/").rsplit("/", 1)[-1] + ".json", item_url + "?fo=json")["body"])
                pdfs = set()
                def walk(node):
                    if isinstance(node, dict):
                        for v in node.values(): walk(v)
                    elif isinstance(node, list):
                        for v in node: walk(v)
                    elif isinstance(node, str) and node.startswith("https://tile.loc.gov/") and node.endswith(".pdf"):
                        pdfs.add(node)
                walk(metadata.get("resources", []))
                for pdf in sorted(pdfs):
                    if pdf in downloaded:
                        continue
                    downloaded.add(pdf)
                    r = self.h.net.fetch(route, pdf)
                    p = HERE / ".cache" / (sha(r["body"]) + ".pdf")
                    p.write_bytes(r["body"])
                    n, pages = fetch_ladder.pdf_pages_text(p)
                    source = {"volume": p.name, "url": pdf, "source_bytes_url": pdf, "sha256": r["sha256"],
                              "retrieved_utc": "see route log", "source_artifact": None,
                              "copy_kind": "machine_read_government_codification"}
                    result = extract(self.h, pages, source, 5076, 7531, route=route)
                    append(OUT / "ROUTE_RESULTS.jsonl", result)
                    print(json.dumps(result), flush=True)
        except Exception as exc:
            self.h.failure(route, str(exc))

    def government_html(self):
        route = "nara_static_codification"
        try:
            url = "https://www.archives.gov/federal-register/codification/numeric-executive-orders.html"
            r = self.fetch(route, "nara_codification_index.html", url)
            raw = r["body"].decode("utf-8", "replace")
            for part in ("executive-orders-02.html", "executive-orders-03.html"):
                index_url = urljoin(url, part)
                if part not in raw:
                    continue
                page = self.fetch(route, "nara_" + part, index_url)
                raw += "\n" + page["body"].decode("utf-8", "replace")
            links = [(urljoin(url, html.unescape(link)), int(number)) for link, number in
                     re.findall(r'href="([^"]*executive-order/(\d+)\.html[^"]*)"', raw)]
            count = 0
            for page_url, number in sorted(set(links)):
                identity = "EO:" + str(number)
                if identity not in self.h.missing:
                    continue
                page = self.fetch(route, f"nara_EO_{number}.html", page_url)
                text = fetch_ladder.html_to_text(page["body"].decode("utf-8", "replace"))
                start = re.search(r"Executive\s+Order\s+(?:No\.?\s*)?" + str(number) + r"\b", text, re.I)
                if not start:
                    self.h.failure(route, "exact_order_heading_not_read", identity)
                    continue
                source = {"url": page_url, "sha256": page["sha256"], "page_or_item": "Official codification page, Executive Order " + str(number),
                          "notes": "Government codification with editorial/amendment material; not necessarily text as issued."}
                count += self.h.save(identity, text[start.start():], route, source, "government_codified_website_text")
            append(OUT / "ROUTE_RESULTS.jsonl", {"route": route, "index_links": len(links), "saved": count, "remaining": len(self.h.missing)})
        except Exception as exc:
            self.h.failure(route, str(exc))

    def catalog_routes(self):
        queries = [
            ("university_repositories", "upenn_hoover.html", "https://onlinebooks.library.upenn.edu/webbin/book/lookupname?" + urlencode({"key": "Hoover, Herbert, 1874-1964"})),
            ("hoover_library", "hoover_ebooks.html", "https://hoover.archives.gov/research/ebooks"),
            ("fdr_library", "fdr_digital.html", "https://www.fdrlibrary.org/digital-collections"),
            ("fraser", "fraser_search.html", "https://fraser.stlouisfed.org/search.php?" + urlencode({"q": '"executive order" 1933'})),
            ("govinfo_govpub", "govpub_search.html", "https://www.govinfo.gov/app/search/" + urlencode({"query": '"Herbert Hoover" "executive orders"'})),
            ("google_books", "google_hoover.json", "https://www.googleapis.com/books/v1/volumes?" + urlencode({"q": 'intitle:"Herbert Hoover" intitle:"Proclamations"', "maxResults": 40})),
            ("google_books", "google_gpo.json", "https://www.googleapis.com/books/v1/volumes?" + urlencode({"q": 'intitle:"Executive order" 1933 GPO', "maxResults": 40})),
            ("agency_reprints", "ia_agency_reprints.json", "https://archive.org/advancedsearch.php?" + urlencode([("q", 'title:("executive orders") AND year:[1929 TO 1938] AND NOT title:("Herbert Hoover")'), ("fl[]", "identifier"), ("fl[]", "title"), ("rows", 100), ("output", "json")])),
        ]
        for route, name, url in queries:
            try:
                r = self.fetch(route, name, url)
                text = r["body"].decode("utf-8", "replace")
                links = list(dict.fromkeys(html.unescape(x) for x in re.findall(r'href=["\'](https?://[^"\']+)', text)))
                details = {"route": route, "discovery_url": url, "links": links[:100], "saved": 0,
                           "finding_aid_only_until_full_order_source_verified": True}
                try:
                    data = json.loads(text)
                    details["items"] = data.get("items", data.get("response", {}).get("docs", []))
                except ValueError:
                    details["excerpt"] = fetch_ladder.html_to_text(text)[:5000]
                append(OUT / "CATALOG_ROUTE_RESULTS.jsonl", details)
                print(json.dumps({"route": route, "metadata_bytes": len(r["body"]), "links": len(links)}), flush=True)
            except Exception as exc:
                self.h.failure(route, str(exc))
                print(json.dumps({"route": route, "failed": str(exc)}), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--route", choices=["all", "fdr", "loc", "nara", "catalogs", "followup", "fraser"], default="all")
    args = ap.parse_args()
    s = Supplements()
    if args.route in ("all", "fdr"): s.fdr_books()
    if args.route in ("all", "loc"): s.loc()
    if args.route in ("all", "nara"): s.government_html()
    if args.route in ("all", "catalogs"): s.catalog_routes()
    if args.route == "followup":
        s.fdr_captioned_entries()
        s.agency_books()
        s.fraser()
    if args.route == "fraser": s.fraser()


if __name__ == "__main__":
    main()
