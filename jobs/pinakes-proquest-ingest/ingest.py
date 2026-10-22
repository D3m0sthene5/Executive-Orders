"""Pinakes: wire the uploaded ProQuest PDFs into the project, by machine, without spending tokens on them.

Named for Callimachus's Pinakes, the first library catalogue. For every PDF in the ProQuest folders
(the owner's upload at the repo root, `ProQuest Pre-1937 Orders/`, and the research folder
`research/pre-1937-sources/ProQuest Pre-1937 Orders/`) it records the byte facts, decides which file
stands for each order, gets a text for it, and writes the records the rest of the pipeline reads:

  INVENTORY.csv      every file: parsed year/number/suffix, bytes, SHA-256, %PDF- signature, pages,
                     text-layer size and quality, duplicate-of, page range in the name, stray or not
  ORDERS.csv         one row per order: the file chosen (the plain copy, most pages), its hash,
                     text_source (layer: the PDF's own text; ocr: read by tesseract; none), text path,
                     characters, quality, and whether the order is in the census
  texts/EO_<n>.txt   the text, one file per order
  FRAGMENTS.jsonl    one project fragment per order, grade archival_replica_scan_pending_codebook,
                     acceptable_as_original false, needs_page_check true; the readiness tracker reads
                     these as a lead class (ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK), never as the original
  SUPPLIED_LINKS_RECONCILED.csv / MISSING_FROM_UPLOAD.csv   the owner's link list against the files
  STRAY_FILES.csv    files whose names are not ProQuest order accessions (left alone, listed for the owner)
  PROGRESS_EVENTS.jsonl   verified_repository events in the acquisition folder's audit format, for the
                     owner to append to its _resume/progress.jsonl if wanted

OCR is bounded per run (JOB_OCR_PAGES, default 4000 pages) and resumes: texts already produced for the
same PDF bytes are carried forward from the last committed output, so the backlog shrinks every day
until every order has a text. A text's quality is scored the same way for layer and OCR; a handwritten
original scores low either way and is flagged, not hidden.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import hashlib
import json
import os
import posixpath
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "source-ladder"))
import eo_identity as ident  # noqa: E402
import eo_pdf  # noqa: E402

JOB = "pinakes-proquest-ingest"
INVENTORY_FIELDS = ["file", "folder", "instrument_id", "year", "number", "suffix", "copy", "page_range", "in_census", "name_parsed",
                    "bytes", "sha256", "pdf_signature", "pages", "text_chars", "text_quality", "common_share", "duplicate_of", "pdf_error"]
ORDER_FIELDS = ["instrument_id", "number", "suffix", "year", "in_census", "file", "folder", "sha256", "bytes", "pages", "copies",
                "text_source", "text_path", "text_sha256", "text_chars", "text_quality", "common_share", "text_usable", "ocr_pages", "ocr_error",
                "signing_date", "title", "proquest_link_supplied", "accession_url"]


def prior_texts(root):
    """sha256 of the PDF -> (text, text_source, ocr_pages) from the last committed output, for resuming OCR."""
    out = {}
    try:
        import prior_output
        prior = prior_output.PriorOutput.from_git_head(root, f"jobs/{JOB}/output")
        rows = prior.csv_rows("ORDERS.csv")
        texts = prior.texts("texts") if rows else {}
    except Exception:
        return out
    for r in rows or []:
        if r.get("text_source") in ("ocr", "layer") and r.get("text_path"):
            name = os.path.basename(r["text_path"])
            body = texts.get(name) if isinstance(texts, dict) else None
            if body is None and isinstance(texts, dict):
                body = texts.get(r["text_path"])
            if body is not None:
                if isinstance(body, bytes):
                    body = body.decode("utf-8", "replace")
                if hashlib.sha256(body.encode("utf-8")).hexdigest() == r.get("text_sha256"):
                    out[r["sha256"]] = (body, r["text_source"], int(r.get("ocr_pages") or 0))
    return out


def scan_folders(root, universe):
    rows, seen_hash = [], {}
    for rel in ident.PROQUEST_DIRS:
        folder = os.path.join(root, rel)
        if not os.path.isdir(folder):
            continue
        names = [n for n in os.listdir(folder) if n.lower().endswith(".pdf") and os.path.isfile(os.path.join(folder, n))]
        names.sort(key=lambda n: ((ident.proquest_filename(n) or {}).get("copy", 0), n))
        for name in names:
            parsed = ident.proquest_filename(name)
            info = eo_pdf.inspect_pdf(os.path.join(folder, name))
            row = {"file": name, "folder": rel, "instrument_id": "", "year": "", "number": "", "suffix": "", "copy": "", "page_range": "",
                   "in_census": "", "name_parsed": "yes" if parsed else "no", "bytes": info["bytes"], "sha256": info["sha256"],
                   "pdf_signature": "yes" if info["pdf_signature"] else "no", "pages": info["pages"], "text_chars": info["text_chars"],
                   "text_quality": info["text_quality"], "common_share": info["common_share"],
                   "duplicate_of": seen_hash.get(info["sha256"], ""), "pdf_error": info["pdf_error"],
                   "_text": info["text"], "_path": os.path.join(folder, name)}
            if parsed:
                iid = ident.canon_id(parsed["number"], parsed["suffix"])
                row.update({"instrument_id": iid, "year": parsed["year"], "number": parsed["number"], "suffix": parsed["suffix"],
                            "copy": parsed["copy"], "page_range": parsed["page_range"], "in_census": "yes" if iid in universe else "no"})
            seen_hash.setdefault(info["sha256"], posixpath.join(rel, name))
            rows.append(row)
    return rows


def choose_files(rows):
    """id -> the file that stands for the order: a real PDF, the plain copy over Chrome's ' (n)' copies, most pages."""
    best, copies = {}, collections.Counter()
    for r in rows:
        if not r["instrument_id"] or r["pdf_signature"] != "yes":
            continue
        copies[r["instrument_id"]] += 1
        cur = best.get(r["instrument_id"])
        key = (r["pages"] or 0, -int(r["copy"] or 0), r["page_range"] == "")
        if cur is None or key > cur["_key"]:
            best[r["instrument_id"]] = {**r, "_key": key}
    return best, copies


def default_workers():
    cpus = os.cpu_count() or 2
    if os.environ.get("GITHUB_ACTIONS"):
        return min(4, cpus * 2)
    return max(1, cpus)


def run(root, out_dir, ocr_pages_budget=None, ocr=None, workers=None):
    os.makedirs(os.path.join(out_dir, "texts"), exist_ok=True)
    budget = int(os.environ.get("JOB_OCR_PAGES", "4000")) if ocr_pages_budget is None else ocr_pages_budget
    ocr = eo_pdf.ocr_pdf if ocr is None else ocr
    workers = int(os.environ.get("JOB_WORKERS") or default_workers()) if workers is None else workers
    universe = ident.load_universe(root)
    dates = ident.load_dates(root)
    pq_rows = {ident.canon_id(*ident.parse_eo_id(str(r["id"]))): r for r in ident.load_proquest_rows(root)}
    prior = prior_texts(root)
    rows = scan_folders(root, universe)
    best, copies = choose_files(rows)
    problems = []
    if not rows:
        problems.append("no ProQuest PDFs found in " + " or ".join(ident.PROQUEST_DIRS))

    # Decide the OCR work up front (greedy, in order number order, within the page budget), then run it on every
    # core: about 4 workers on GitHub's 2-CPU runner, every CPU thread on the owner's PC (JOB_WORKERS overrides).
    ordered = sorted(best, key=lambda x: ident.parse_eo_id(x) or (0, ""))
    plan, ocr_used, ocr_pending, ocr_results = [], 0, 0, {}
    can_ocr = eo_pdf.ocr_available() or ocr is not eo_pdf.ocr_pdf
    deferred = {}
    for iid in ordered:
        r = best[iid]
        if eo_pdf.usable(r["text_chars"], r["text_quality"], r["common_share"]) or r["sha256"] in prior:
            continue
        if not can_ocr:
            deferred[iid] = "OCR programs not installed on this machine"
            ocr_pending += 1
            continue
        pages = r["pages"] or 1
        if ocr_used + pages <= budget:
            plan.append(iid)
            ocr_used += pages
        else:
            deferred[iid] = "deferred: OCR page budget for this run is used up"
            ocr_pending += 1
    if plan:
        print(f"OCR: {len(plan)} orders, {ocr_used} pages, {workers} workers", flush=True)
        if workers > 1 and ocr is eo_pdf.ocr_pdf:
            import concurrent.futures
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
                for iid, res in zip(plan, ex.map(ocr, [best[i]["_path"] for i in plan], chunksize=4)):
                    ocr_results[iid] = res
        else:
            for n, iid in enumerate(plan, 1):
                ocr_results[iid] = ocr(best[iid]["_path"])
                if n % 100 == 0:
                    print(f"OCR {n}/{len(plan)}", flush=True)

    orders, fragments, events = [], [], []
    ocr_done, carried = 0, 0
    for iid in ordered:
        r = best[iid]
        text, source, ocr_pages, ocr_err = "", "none", 0, ""
        if eo_pdf.usable(r["text_chars"], r["text_quality"], r["common_share"]):
            text, source = r["_text"], "layer"
        elif r["sha256"] in prior:
            text, source, ocr_pages = prior[r["sha256"]]
            carried += 1
        elif iid in ocr_results:
            text, ocr_pages, ocr_err = ocr_results[iid]
            if text:
                source, ocr_done = "ocr", ocr_done + 1
        else:
            ocr_err = deferred.get(iid, "")
        quality = eo_pdf.text_quality(text) if text else ""
        common = eo_pdf.common_share(text) if text else ""
        text_path, text_sha = "", ""
        if text:
            text_path = "texts/" + iid.replace(":", "_") + ".txt"
            with open(os.path.join(out_dir, text_path), "w", encoding="utf-8") as fh:
                fh.write(text)
            text_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        d = dates.get(iid) or {}
        url = f"https://congressional.proquest.com/congressional/docview/t67.d72.{r['year']}-eo-{r['number']}{r['suffix'].lower()}"
        order = {"instrument_id": iid, "number": r["number"], "suffix": r["suffix"], "year": r["year"], "in_census": r["in_census"],
                 "file": r["file"], "folder": r["folder"], "sha256": r["sha256"], "bytes": r["bytes"], "pages": r["pages"], "copies": copies[iid],
                 "text_source": source, "text_path": text_path, "text_sha256": text_sha, "text_chars": len(text) if text else "",
                 "text_quality": quality, "common_share": common,
                 "text_usable": "yes" if text and eo_pdf.usable(len(text), quality, common) else ("no" if text else ""),
                 "ocr_pages": ocr_pages or "", "ocr_error": ocr_err, "signing_date": d.get("date", ""), "title": (d.get("title") or "")[:160],
                 "proquest_link_supplied": "yes" if iid in pq_rows else "no", "accession_url": url}
        orders.append(order)
        fragments.append({
            "instrument_id": iid, "kind": "original_representation", "produced_by": JOB, "acceptable_as_original": False,
            "grade": "archival_replica_scan_pending_codebook", "representation_type": "proquest_replica_of_original_scan",
            "confidence_note": ("ProQuest Congressional 'Replica of Original' PDF matched to the order by its file name (year and "
                                "number). Bytes, signature and page count verified; the text is the PDF's own layer or tesseract OCR "
                                "and may be wrong. Identity, page contents and custody grade are NOT verified; acceptable_as_original "
                                "stays false until a person compares the pages and the codebook assigns the grade. Not a legal conclusion."),
            "sources": [{"page_or_item": f"ProQuest accession {r['year']}-EO-{r['number']}{r['suffix']}; {r['pages'] or '?'} pages",
                         "sha256": r["sha256"], "url": url}],
            "data": {"acceptable_as_original": False, "needs_page_check": True, "location_verified": False, "location_confidence": "medium",
                     "grade": "archival_replica_scan_pending_codebook", "representation_type": "proquest_replica_of_original_scan",
                     "file": os.path.join(r["folder"], r["file"]), "sha256": r["sha256"], "bytes": r["bytes"], "pages": r["pages"],
                     "text_source": source, "text_path": text_path or None, "text_sha256": text_sha, "text_chars": len(text) if text else None,
                     "text_quality": quality or None, "common_share": common or None, "signing_date": d.get("date", ""), "title": d.get("title", ""),
                     "page_or_item": f"ProQuest {r['year']}-EO-{r['number']}{r['suffix']}", "source_id": f"{JOB}:{iid}:{r['sha256'][:12]}",
                     "url": url, "route": "archival/proquest_replica_local_file"}})
        events.append({"schema_version": 1, "event": "verified_repository", "id": iid, "name": r["file"], "path": posixpath.join(r["folder"], r["file"]),
                       "bytes": r["bytes"], "sha256": r["sha256"], "pdf_signature": True, "pages": r["pages"], "recorded_by": JOB,
                       "observed_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})

    # the owner's link list against the files
    recon, missing = [], []
    for iid, pq in sorted(pq_rows.items(), key=lambda kv: ident.parse_eo_id(kv[0]) or (0, "")):
        have = iid in best
        recon.append({"instrument_id": iid, "year": pq.get("y", ""), "pdf_in_repository": "yes" if have else "no",
                      "file": best[iid]["file"] if have else "", "rec": pq.get("rec", "")})
        if not have:
            missing.append(recon[-1])
    extra = sorted(i for i in best if i not in pq_rows)
    stray = [{k: r[k] for k in ("file", "folder", "bytes", "sha256", "pdf_signature")} for r in rows if r["name_parsed"] == "no" or r["pdf_signature"] != "yes"]

    def write(name, data, fields):
        with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(data)

    write("INVENTORY.csv", rows, INVENTORY_FIELDS)
    write("ORDERS.csv", orders, ORDER_FIELDS)
    write("SUPPLIED_LINKS_RECONCILED.csv", recon, ["instrument_id", "year", "pdf_in_repository", "file", "rec"])
    write("MISSING_FROM_UPLOAD.csv", missing, ["instrument_id", "year", "pdf_in_repository", "file", "rec"])
    write("STRAY_FILES.csv", stray, ["file", "folder", "bytes", "sha256", "pdf_signature"])
    with open(os.path.join(out_dir, "FRAGMENTS.jsonl"), "w", encoding="utf-8") as fh:
        for f in fragments:
            fh.write(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n")
    with open(os.path.join(out_dir, "PROGRESS_EVENTS.jsonl"), "w", encoding="utf-8") as fh:
        for e in events:
            fh.write(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n")

    by_source = collections.Counter(o["text_source"] for o in orders)
    summary = {
        "job": JOB, "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": {"pdf_files": len(rows), "unique_by_sha256": len({r["sha256"] for r in rows}), "stray_or_bad": len(stray),
                  "folders": sorted({r["folder"] for r in rows})},
        "orders": {"with_pdf": len(orders), "in_census": sum(1 for o in orders if o["in_census"] == "yes"),
                   "not_in_census": [o["instrument_id"] for o in orders if o["in_census"] != "yes"][:50],
                   "by_era": dict(collections.Counter(str(o["year"])[:3] + "0s" for o in orders))},
        "texts": {"by_source": dict(by_source), "usable": sum(1 for o in orders if o["text_usable"] == "yes"),
                  "low_quality_probably_handwritten": sum(1 for o in orders if o["text_usable"] == "no"),
                  "ocr_this_run": ocr_done, "ocr_pages_this_run": ocr_used, "ocr_page_budget": budget, "ocr_workers": workers,
                  "carried_from_prior_run": carried,
                  "still_without_text": by_source.get("none", 0), "deferred_by_budget": ocr_pending, "ocr_available_here": eo_pdf.ocr_available()},
        "supplied_links": {"total": len(pq_rows), "with_pdf": len(recon) - len(missing), "missing": len(missing),
                           "pdfs_for_orders_not_on_list": extra[:50], "pdfs_for_orders_not_on_list_count": len(extra)},
        "problems": problems,
        "what_this_is_not": "File facts and machine text. No identity, custody grade, readiness count or legal status changes here.",
    }
    with open(os.path.join(out_dir, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    write_report(os.path.join(out_dir, "REPORT.md"), summary, stray, extra)
    return summary


def write_report(path, s, stray, extra):
    f, o, t, l = s["files"], s["orders"], s["texts"], s["supplied_links"]
    lines = ["# Pinakes: ProQuest PDFs wired in", "", f"Generated {s['generated_utc']}.", "",
             f"**{f['pdf_files']} PDF files** ({f['unique_by_sha256']} unique) in {', '.join(f'`{x}`' for x in f['folders'])} cover "
             f"**{o['with_pdf']} orders**, {o['in_census']} of them in the census. The owner's link list has {l['total']} links: "
             f"{l['with_pdf']} now have a PDF, **{l['missing']} are still missing** (`MISSING_FROM_UPLOAD.csv`); "
             f"{l['pdfs_for_orders_not_on_list_count']} PDFs are for orders not on the list.", "",
             "| Text | Orders |", "|---|---:|",
             f"| From the PDF's own text layer | {t['by_source'].get('layer', 0)} |",
             f"| From OCR (tesseract) | {t['by_source'].get('ocr', 0)} |",
             f"| No text yet | {t['by_source'].get('none', 0)} |",
             f"| Usable quality | {t['usable']} |",
             f"| Low quality (probably handwritten; needs a person) | {t['low_quality_probably_handwritten']} |", "",
             f"This run OCR'd {t['ocr_this_run']} orders ({t['ocr_pages_this_run']} of {t['ocr_page_budget']} budgeted pages), carried {t['carried_from_prior_run']} "
             f"texts forward from the last run, and left {t['still_without_text']} for the next run"
             + ("" if t["ocr_available_here"] else " (OCR programs were not installed on this machine)") + ".", "",
             "Every order has a fragment in `FRAGMENTS.jsonl` with `acceptable_as_original: false` and `needs_page_check: true`; the readiness "
             "tracker reads them as the lead class ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK. A person comparing the pages and the codebook "
             "assigning the grade is what would let one count.", ""]
    if stray:
        lines += ["## Files left alone", ""] + [f"- `{r['folder']}/{r['file']}` ({r['bytes']} bytes, signature {r['pdf_signature']})" for r in stray[:20]] + [""]
    if extra:
        lines += ["## PDFs for orders not on the supplied list", "", ", ".join(extra[:60]) + (" ..." if len(extra) > 60 else ""), ""]
    if s["problems"]:
        lines += ["## Problems", ""] + [f"- {p}" for p in s["problems"]]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
    out_dir = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
    s = run(root, out_dir)
    print(json.dumps({k: s[k] for k in ("files", "orders", "texts", "supplied_links", "problems")}, indent=2))


if __name__ == "__main__":
    main()
