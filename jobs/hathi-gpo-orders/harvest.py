"""Collect allowed alternative sources; exact numbered derivatives, no status writes."""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "output"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "jobs/source-ladder"))
from routes_net import RouteNetwork


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


hunt = module("reused_early_hunt", ROOT / "jobs/early-orders-hunt/hunt.py")
fr = module("reused_fr_originals", ROOT / "jobs/fr-originals/fr_originals.py")
import fetch_ladder
import fr_pages


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()] if path.exists() else []


def append(path, row):
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def iid(number):
    return "EO:" + re.sub(r"-(?=[A-Z]$)", "", re.sub(r"\s+", "", number.upper()))


class Harvest:
    def __init__(self):
        assert (ROOT / "research/orders-1929-1936/ROUTES.md").is_file()
        self.targets = {r["instrument_id"] for r in json.loads((HERE / "data/TARGETS.json").read_text())["orders"]}
        self.sources = {r["instrument_ids"][0]: r for r in read_lines(OUT / "SOURCES.jsonl")}
        assert set(self.sources) <= self.targets
        self.net = RouteNetwork()
        (OUT / "texts").mkdir(exist_ok=True)
        (OUT / "books").mkdir(exist_ok=True)

    @property
    def missing(self):
        return self.targets - set(self.sources)

    def failure(self, route, reason, instrument=None, **extra):
        append(OUT / "EXTRACTION_FAILURES.jsonl", {"route": route, "instrument_id": instrument,
               "reason": reason, **extra})

    def save(self, identity, text, route, source, copy_kind="machine_read_government_printed_copy"):
        if identity not in self.missing:
            return False
        if len(text.strip()) < 100:
            self.failure(route, "insufficient_order_text", identity)
            return False
        rel = "texts/EO_" + identity[3:] + ".txt"
        label = copy_kind.replace("_", " ")
        decorated = (f"# Copy: {label}; not authenticated as an original.\n"
                     f"# Source: {source['url']}\n# Location: {source['page_or_item']}\n"
                     "----- EXACT SOURCE TEXT -----\n" + text.strip() + "\n")
        fetch_ladder.write_text_lf(OUT / rel, decorated)
        source = {**source, "instrument_ids": [identity], "route": route,
                  "source_id": "hathi-gpo-orders:" + route + ":" + identity,
                  "representation_type": copy_kind, "grade": copy_kind,
                  "acceptable_as_original": False, "text_path": rel,
                  "text_sha256": sha((OUT / rel).read_bytes()),
                  "exact_source_text_sha256": sha(text.strip().encode("utf-8")),
                  "retrieved_utc": source.get("retrieved_utc", datetime.now(timezone.utc).isoformat())}
        append(OUT / "SOURCES.jsonl", source)
        fragment = {"kind": "original_representation", "instrument_id": identity,
                    "produced_by": "hathi-gpo-orders", "grade": copy_kind,
                    "representation_type": copy_kind, "acceptable_as_original": False,
                    "data": {k: source[k] for k in ("source_id", "url", "sha256", "page_or_item",
                             "text_path", "text_sha256", "grade", "representation_type", "acceptable_as_original")},
                    "sources": [{k: source[k] for k in ("url", "sha256", "page_or_item")}],
                    "confidence_note": "Order identity checked using the recorded source caption, closing number or locator, including letter suffix. Attributed derivative; OCR and page context need checking before claims. No legal or original-authentication finding."}
        if source.get("archival_id"):
            fragment["data"]["archival_id"] = source["archival_id"]
            fragment["sources"][0]["archival_id"] = source["archival_id"]
        append(OUT / "FRAGMENTS.jsonl", fragment)
        self.sources[identity] = source
        return True

    def book(self, ident, verify, route, keep_raw=True):
        meta_path = OUT / "discovery" / (ident + ".json")
        if meta_path.exists():
            metadata = json.loads(meta_path.read_text())
        else:
            metadata, result = self.net.json(route, "https://archive.org/metadata/" + ident)
            meta_path.write_bytes(result["body"])
        if str(metadata.get("metadata", {}).get("access-restricted-item", "")).lower() == "true":
            raise ValueError("restricted_or_borrow_only_item")
        wanted = ident + "_djvu.xml"
        files = {f["name"]: f for f in metadata.get("files", [])}
        if wanted not in files or str(files[wanted].get("private", "")).lower() == "true":
            raise ValueError("no_public_djvu_xml")
        record_path = OUT / "books" / (ident + ".json")
        pages_folder = OUT / "books" if keep_raw else HERE / ".cache/books"
        pages_folder.mkdir(parents=True, exist_ok=True)
        pages_path = pages_folder / (ident + "_pages.jsonl.gz")
        if record_path.exists() and pages_path.exists():
            record = json.loads(record_path.read_text())
            with gzip.open(pages_path, "rt", encoding="utf-8") as fh:
                pages = [(r["image"], r["text"]) for r in (json.loads(s) for s in fh)]
        else:
            record = hunt.fetch_copy(ident, {"kind": "government", "verify": verify}, self.net.pool, hunt.Budget(5))
            pages = record.pop("pages")
            if record["status"] != "fetched" or not record["edition"].get("edition_ok") or record["custody"].get("sha1_matches_archive") is not True:
                raise ValueError("book_custody_or_edition_check_failed: " + record["status"])
        # The Hoover/GPO folios are at the bottom. Reorder only the mapper input;
        # the saved/extracted source text is never altered for this mapping step.
        mapping_input = []
        for image, text in pages:
            lines = text.splitlines()
            bottom = next((line for line in reversed(lines[-3:]) if re.fullmatch(r"\s*\d{1,4}\s*", line)), "")
            mapping_input.append((image, bottom + "\n" + text if bottom else text))
        page_map, stats = hunt.printed_page_map(mapping_input)
        with gzip.open(pages_path, "wt", encoding="utf-8") as fh:
            for image, text in pages:
                fh.write(json.dumps({"image": image, "printed": page_map.get(image), "text": text}, ensure_ascii=False) + "\n")
        record.update(page_count=len(pages), page_map=stats, mapping_adapter="bottom folio supplied to unchanged early-orders-hunt.printed_page_map")
        record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record, pages, page_map

    def extract_hoover(self, record, pages, page_map):
        route = "ia_hoover"
        starts, full, spans = [], "", []
        for image, text in pages:
            spans.append((len(full), image))
            full += text + "\n\f\n"
        pattern = re.compile(r"^Executive\s+Order\s+(\d{4}(?:\s*-?\s*[A-Z])?)[.,]?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+19\d\d", re.M | re.I)
        for match in pattern.finditer(full):
            starts.append((match.start(), iid(match[1])))
        saved = 0
        for n, (start, identity) in enumerate(starts):
            if identity not in self.missing:
                continue
            end = starts[n + 1][0] if n + 1 < len(starts) else len(full)
            block = full[start:end]
            tag = re.search(r"[\[(]\s*No\.?\s*" + fr_pages.digits_pattern(identity[3:]) + r"\s*[\])]?", block, re.I)
            if tag:
                block = block[:tag.end()]
                boundary = "matching_closing_number_tag"
            elif n + 1 < len(starts) and re.search(r"(?:HERBERT|White\s+House)", block[-600:], re.I):
                # OCR may damage the repeated footer number. Keep its bytes,
                # using the next exact dated order caption as the boundary.
                boundary = "next_exact_dated_order_caption; footer OCR needs page check"
            else:
                self.failure(route, "missing_complete_order_boundary", identity, book=record["ia_identifier"])
                continue
            first_image = max((image for offset, image in spans if offset <= start), default=1)
            last_image = max((image for offset, image in spans if offset <= start + len(block)), default=first_image)
            p1, p2 = page_map.get(first_image, ("", None))[1], page_map.get(last_image, ("", None))[1]
            source = {"url": record["custody"]["item_url"], "sha256": record["custody"]["page_text_sha256"],
                      "source_bytes_url": record["custody"]["page_text_url"],
                      "volume": record["ia_identifier"], "printed_page_start": p1, "printed_page_end": p2,
                      "scan_image_start": first_image, "scan_image_end": last_image,
                      "page_or_item": f"{record['ia_identifier']}; printed pages {p1}-{p2}; scanned images {first_image}-{last_image}",
                      "page_url": record["custody"]["item_url"] + "/page/n" + str(first_image - 1) + "/mode/1up",
                      "boundary": boundary, "closing_number_matches": bool(tag),
                      "notes": "OCR of the 1974 official GPO compilation. Exact dated caption; end boundary recorded separately. OCR bytes unchanged; no legal status or signed-original claim."}
            saved += self.save(identity, block, route, source)
        return {"route": route, "book": record["ia_identifier"], "heading_candidates": len(starts), "saved": saved, "remaining": len(self.missing)}

    def federal_register(self):
        route = "govinfo_fr"
        sitemap = OUT / "discovery/govinfo_fr1936.raw"
        if not sitemap.exists():
            sitemap.write_bytes(self.net.fetch(route, "https://www.govinfo.gov/sitemap/FR_1936_sitemap.xml")["body"])
        dates = sorted(set(re.findall(r"FR-(1936-\d\d-\d\d)", sitemap.read_text())))
        finished = {r["issue"] for r in read_lines(OUT / "FR_ISSUES.jsonl")}
        all_saved = 0
        for date in dates:
            if date in finished:
                continue
            candidates = sorted(i for i in self.missing if 7316 <= int(re.match(r"EO:(\d+)", i)[1]) <= 7531)
            if not candidates:
                break
            url = f"https://www.govinfo.gov/content/pkg/FR-{date}/pdf/FR-{date}.pdf"
            try:
                result = self.net.fetch(route, url)
                assert result["body"].lstrip().startswith(b"%PDF-")
                temp = HERE / ".cache" / ("FR-" + date + ".pdf")
                temp.write_bytes(result["body"])
                n, numbered = fetch_ladder.pdf_pages_text(temp)
                texts = [t for _, t in numbered]
                page_map = fr_pages.printed_page_map(texts)
                found = []
                for identity in candidates:
                    loc = fr_pages.locate_order(texts, identity[3:])
                    if not loc["found"] or loc.get("marker_kind") not in ("heading", "closing_number_tag"):
                        continue
                    if any("no filing line" in note for note in loc["notes"]):
                        self.failure(route, "missing_filing_end", identity, issue=date)
                        continue
                    a, b = loc["first_page"], loc["last_page"]
                    text = "\n\f\n".join(texts[a - 1:b])
                    printed = page_map.get(a - 1)
                    source = {"url": url, "sha256": result["sha256"], "volume": "Federal Register volume 1",
                              "publication_date": date, "pdf_first_page": a, "pdf_last_page": b,
                              "printed_page_start": printed,
                              "page_or_item": f"Federal Register {date}; PDF pages {a}-{b}; printed page {printed}",
                              "page_url": url + "#page=" + str(a), "locator": loc,
                              "notes": "Official printed Federal Register scan with machine-read layer. Unchanged fr-originals/source-ladder page locator; includes page context. Not authenticated as signed original."}
                    if self.save(identity, text, route, source):
                        found.append(identity)
                if found:
                    (OUT / "books" / ("FR-" + date + ".pdf")).write_bytes(result["body"])
                append(OUT / "FR_ISSUES.jsonl", {"issue": date, "pdf_pages": n, "saved": found, "source_sha256": result["sha256"]})
                all_saved += len(found)
                if found or len(finished) % 20 == 0:
                    print(json.dumps({"route": route, "issue": date, "issues_done": len(finished) + 1, "saved": len(found), "route_saved_this_run": all_saved, "remaining": len(self.missing)}), flush=True)
                finished.add(date)
            except Exception as exc:
                self.failure(route, str(exc), issue=date)
                if "Host stopped" in str(exc) or "Host already stopped" in str(exc):
                    break
        append(OUT / "ROUTE_RESULTS.jsonl", {"route": route, "issues_checked": len(finished), "saved_this_run": all_saved, "remaining": len(self.missing)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hoover", action="store_true")
    ap.add_argument("--federal-register", action="store_true")
    args = ap.parse_args()
    harvest = Harvest()
    if args.hoover:
        for ident in ("4731703.proc.001.umich.edu", "4731703.proc.002.umich.edu"):
            try:
                record, pages, pm = harvest.book(ident, {"title_words": ["hoover", "proclamations", "executive"], "year_any": [1974], "publisher_any": ["national archives", "g.p.o."]}, "ia_hoover")
                result = harvest.extract_hoover(record, pages, pm)
                append(OUT / "ROUTE_RESULTS.jsonl", result)
                print(json.dumps(result), flush=True)
            except Exception as exc:
                harvest.failure("ia_hoover", str(exc), book=ident)
                print(json.dumps({"book": ident, "failed": str(exc)}), flush=True)
    if args.federal_register:
        harvest.federal_register()


if __name__ == "__main__":
    main()
