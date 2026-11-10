"""F7 reach measure for the fr-originals / source-ladder page-span and closing-tag fixes (offline).

Usage: python -I measure_fr_pages.py REF_REPO OLD_FR_PAGES NEW_FR_PAGES OUT_DIR

Only the span pages of each order are saved (jobs/fr-originals/data/full_run/texts), not whole PDFs, so this
cannot re-run the locator over a full issue. It measures what the saved page text can answer:

 A. closing tag (fix 3): for every order graded medium/low, does the closing-number-tag pattern find the order's
    own tag in its saved text, old pattern versus new pattern?
 B. continued order (fix 2, EO 8109/8494/8617 type): for every low-grade order, does the new "order starts after
    another order's filing line on the cited page" anchor differ from the old first-heading anchor?
 C. bundled PDF (fix 2, EO 11728/13294 type): for every order whose saved text is whole PDF pages 1-n of a
    per-document PDF, does the new single-document locator move the start past PDF page 1?
 E. long order (fix 2, EO 11905 type): medium orders whose note says no filing line was found; these are the orders
    the new 80-page filing search can change (it needs the whole PDF, so it cannot be re-run here).
 (The neighbour-page-file adoption, EO 8965/8534, was removed from this change after review.)
"""
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

ref, old_path, new_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


old, new = load(old_path, "frp_old"), load(new_path, "frp_new")
base = ref / "jobs/fr-originals/data/full_run"
PAGE = re.compile(r"^=== PDF page (\d+) of (\d+) ===$", re.M)


def pages_of(text):
    """{pdf_page_number: text} from a saved span text."""
    marks = list(PAGE.finditer(text))
    return {int(m.group(1)): text[m.end():(marks[i + 1].start() if i + 1 < len(marks) else len(text))].strip("\n")
            for i, m in enumerate(marks)}


def tag_hit(mod, number, text):
    pat = dict(mod.marker_patterns(number))["closing_number_tag"]
    return any(mod.tag_context_ok(text, m.start()) for m in pat.finditer(text))


sources = [json.loads(l) for l in open(base / "SOURCES.jsonl", encoding="utf-8")]
rows = {"A": [], "B": [], "C": [], "E": []}
n_graded = 0
for rec in sources:
    iid = rec["instrument_ids"][0]
    number = iid.split(":", 1)[1]
    if not re.fullmatch(r"\d+", number):
        continue
    tpath = base / rec["text_path"]
    if not tpath.is_file():
        continue
    text = tpath.read_text(encoding="utf-8", errors="replace")
    conf = rec.get("location_confidence")
    if conf in ("medium", "low"):
        n_graded += 1
        o, n = tag_hit(old, number, text), tag_hit(new, number, text)
        if n and not o:
            rows["A"].append({"instrument_id": iid, "confidence": conf, "page_or_item": rec["page_or_item"]})
    pages = pages_of(text)
    if conf == "low" and pages:
        first = min(pages)
        pt = [pages[k] for k in sorted(pages)]
        if new.continued_anchor(pt, 0, number) is not None:
            rows["B"].append({"instrument_id": iid, "confidence": conf, "page_or_item": rec["page_or_item"]})
    m = re.search(r"PDF pages 1-(\d+)$", rec.get("page_or_item") or "")
    if m and rec.get("route") in ("official/ofr_index_pdf_url", "official/govinfo_link_fr", "reuse/stage21_original_sources"):
        pt = [pages[k] for k in sorted(pages)]
        if pt and len(pt) == len(pages) and min(pages) == 1:
            r = new.locate_order(pt, number, None, single_document=True)
            if r.get("start_moved"):
                rows["C"].append({"instrument_id": iid, "old_pages": rec["page_or_item"],
                                  "new_first_page": r["first_page"], "start_printed_page": r.get("start_printed_page")})

# E: orders whose filing line was not found within 25 pages (medium, "no filing line"): the 80-page search may now end them
for rec in sources:
    if rec.get("location_confidence") == "medium" and "no filing line" in (rec.get("notes") or ""):
        rows["E"].append({"instrument_id": rec["instrument_ids"][0], "page_or_item": rec["page_or_item"]})

summary = {"sources": len(sources), "medium_or_low_graded": n_graded,
           "A_closing_tag_newly_matched": len(rows["A"]), "B_continued_anchor_differs": len(rows["B"]),
           "C_bundled_pdf_start_moves": len(rows["C"]), "E_no_filing_line_candidates_for_80_page_search": len(rows["E"])}
for k, v in rows.items():
    if v:
        with open(out / f"fr_pages_{k}.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(v[0]))
            w.writeheader()
            w.writerows(v)
(out / "fr_pages_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
print(json.dumps(summary, indent=1))
