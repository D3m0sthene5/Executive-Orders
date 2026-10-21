"""Lewis: find an official original for every order the project holds only as a transcription.

Scope. An order is Lewis's when the readiness tracker leaves its `original_text` step open with the
blocker ONLY_COMPILED_TRANSCRIPTION_FOUND (a Richardson, American Presidency Project, Wikisource,
HathiTrust or other printed-copy lead exists, so the order's date and wording are known, but no
official original is saved), plus any order Clark hands over with identity evidence
(jobs/clark-discovery/output/HANDOFF_TO_LEWIS.jsonl).

For each order Lewis walks a fixed ladder of routes and records where the order stands on it:

  1. proquest_local          a ProQuest "Replica of Original" PDF is already in the repository folder
                             (verified: %PDF- signature, SHA-256, page count, text-layer quality)
  2. proquest_supplied_link  the owner's ProQuest list has a link for it; the PDF is not yet uploaded
  3. federal_register        signed on or after 1936-03-14: the Federal Register printed it; a fetch
                             request for the source-ladder job is proposed with the OFR citation
  4. proquest_phrase_search  before 1937 and not on the ProQuest list: the ProQuest Congressional
                             phrase search for "Executive Order No. N" (a manual lead; sign-in needed)
  5. nara_rg11               the National Archives RG 11 numbered series (manual lead)

This offline stage writes leads and verified file facts and fetches nothing; the web stage in
online.py then hunts the open web for every order in scope (see jobs/_lib/eo_websearch.py). Neither
changes a readiness count, and neither gives a ProQuest file a custody grade: every fragment it writes carries
acceptable_as_original=false and needs_page_check=true until a person compares the pages and the
codebook assigns the grade. Only the owner enqueues its proposed fetch requests.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "source-ladder"))
import eo_identity as ident  # noqa: E402

try:  # the source-ladder request contract validates the proposals Lewis writes
    import request_contract  # noqa: E402
except Exception:  # pragma: no cover - the contract module is optional at import time
    request_contract = None

try:
    import pypdf  # noqa: E402
except Exception:  # pragma: no cover
    pypdf = None

JOB = "lewis-originals"
CLARK_HANDOFF = "jobs/clark-discovery/output/HANDOFF_TO_LEWIS.jsonl"
GPO_VOLUMES = (5800, 8027)      # GPO bound Executive Orders volumes (hathi-gpo-orders)
HOOVER_VOLUMES = (5076, 5549)   # OFR 1974 Hoover compilation vol. I (ofr-compilations)
TEXT_QUALITY_MIN = 0.55         # share of alphabetic tokens that look like words; below this the layer is noise


# --- ProQuest folder ------------------------------------------------------------------------------

import eo_pdf  # noqa: E402

text_quality = eo_pdf.text_quality
inspect_pdf = eo_pdf.inspect_pdf


PINAKES_ORDERS = "jobs/pinakes-proquest-ingest/output/ORDERS.csv"


def pinakes_orders(root):
    """id -> row from the Pinakes ingest (the ProQuest authority once it has run), in Lewis's inventory shape."""
    out = {}
    for r in ident.read_csv(os.path.join(root, PINAKES_ORDERS)):
        if not r.get("instrument_id"):
            continue
        out[r["instrument_id"]] = {"file": r["file"], "folder": r.get("folder", ""), "instrument_id": r["instrument_id"],
                                   "year": r.get("year", ""), "number": r.get("number", ""), "suffix": r.get("suffix", ""),
                                   "sha256": r["sha256"], "bytes": r.get("bytes", ""), "pages": int(r["pages"]) if r.get("pages") else None,
                                   "text_chars": int(r["text_chars"]) if r.get("text_chars") else None,
                                   "text_quality": float(r["text_quality"]) if r.get("text_quality") else None,
                                   "text_layer_usable": r.get("text_usable", ""), "text_path": r.get("text_path", ""),
                                   "text_sha256": r.get("text_sha256", ""), "duplicate_of": "", "pdf_signature": "yes",
                                   "name_parsed": "yes", "copy": 0, "pdf_error": ""}
    return out


def inventory_proquest(root, universe, out_dir=None, write_texts=True):
    """Every PDF in the ProQuest folders, read by name, with its byte facts. Returns rows and id -> best row.

    Used only when the Pinakes ingest has not run; Pinakes also OCRs and is the ProQuest authority."""
    rows, by_id = [], {}
    seen_hash = {}
    entries = []
    for rel in ident.PROQUEST_DIRS:
        folder = os.path.join(root, rel)
        if os.path.isdir(folder):
            entries += [(folder, n) for n in os.listdir(folder) if n.lower().endswith(".pdf")]
    # the plain file first, then Chrome's ' (1)', ' (2)' copies, so a duplicate points at the plain name
    entries.sort(key=lambda e: ((ident.proquest_filename(e[1]) or {}).get("copy", 0), e[1]))
    for folder, name in entries:
        parsed = ident.proquest_filename(name)
        path = os.path.join(folder, name)
        info = inspect_pdf(path)
        row = {"file": name, "instrument_id": "", "year": "", "number": "", "suffix": "", "copy": "",
               "in_universe": "", "name_parsed": "yes" if parsed else "no", **{k: v for k, v in info.items() if k != "text"}}
        row["pdf_signature"] = "yes" if info["pdf_signature"] else "no"
        if parsed:
            iid = ident.canon_id(parsed["number"], parsed["suffix"])
            row.update({"instrument_id": iid, "year": parsed["year"], "number": parsed["number"],
                        "suffix": parsed["suffix"], "copy": parsed["copy"],
                        "in_universe": "yes" if iid in universe else "no"})
        row["duplicate_of"] = seen_hash.get(info["sha256"], "")
        seen_hash.setdefault(info["sha256"], name)
        row["text_path"] = ""
        if parsed and info["pdf_signature"] and not row["duplicate_of"]:
            usable = (info["text_quality"] or 0) >= TEXT_QUALITY_MIN and (info["text_chars"] or 0) >= 80
            row["text_layer_usable"] = "yes" if usable else "no"
            if usable and write_texts and out_dir:
                tdir = os.path.join(out_dir, "texts")
                os.makedirs(tdir, exist_ok=True)
                tp = os.path.join("texts", row["instrument_id"].replace(":", "_") + ".txt")
                with open(os.path.join(out_dir, tp), "w", encoding="utf-8") as fh:
                    fh.write(info["text"])
                row["text_path"] = tp
                row["text_sha256"] = hashlib.sha256(info["text"].encode("utf-8")).hexdigest()
            cur = by_id.get(row["instrument_id"])
            if cur is None or (cur["pages"] or 0) < (info["pages"] or 0):
                by_id[row["instrument_id"]] = row
        else:
            row["text_layer_usable"] = ""
        rows.append(row)
    return rows, by_id


def proquest_fragment(row, dates):
    """A project fragment for a verified local ProQuest PDF. Custody grade deliberately left open."""
    d = dates.get(row["instrument_id"], {})
    return {
        "instrument_id": row["instrument_id"],
        "kind": "original_representation",
        "produced_by": JOB,
        "acceptable_as_original": False,
        "grade": "archival_replica_scan_pending_codebook",
        "representation_type": "proquest_replica_of_original_scan",
        "confidence_note": ("ProQuest Congressional 'Replica of Original - Complete' PDF matched to the order by its "
                            "file name (year and number) only. Bytes, signature and page count verified; the "
                            "identity, page contents and custody grade are NOT verified. acceptable_as_original "
                            "stays false until a person compares the pages and the codebook assigns the grade. "
                            "Not a legal conclusion."),
        "sources": [{"page_or_item": f"ProQuest accession PT1-{row['year']}-EO-{row['number']}{row['suffix']}; "
                                     f"{row['pages'] or '?'} pages", "sha256": row["sha256"],
                     "url": f"https://congressional.proquest.com/congressional/docview/t67.d72.{row['year']}-eo-"
                            f"{row['number']}{row['suffix'].lower()}"}],
        "data": {
            "acceptable_as_original": False, "needs_page_check": True, "location_verified": False,
            "location_confidence": "medium", "grade": "archival_replica_scan_pending_codebook",
            "representation_type": "proquest_replica_of_original_scan",
            "file": os.path.join(ident.PROQUEST_DIR, row["file"]), "sha256": row["sha256"], "bytes": row["bytes"],
            "pages": row["pages"], "text_chars": row["text_chars"], "text_quality": row["text_quality"],
            "text_layer_usable": row["text_layer_usable"], "text_path": row["text_path"] or None,
            "text_sha256": row.get("text_sha256", ""), "signing_date": d.get("date", ""), "title": d.get("title", ""),
            "page_or_item": f"ProQuest PT1-{row['year']}-EO-{row['number']}{row['suffix']}",
            "source_id": f"{JOB}:proquest:{row['instrument_id']}:{row['sha256'][:12]}",
            "url": f"https://congressional.proquest.com/congressional/docview/t67.d72.{row['year']}-eo-"
                   f"{row['number']}{row['suffix'].lower()}",
            "route": "archival/proquest_replica_local_file",
        },
    }


# --- scope and routing ----------------------------------------------------------------------------

def load_scope(root, readiness, universe):
    """Orders Lewis works: transcription-only (tracker) plus Clark's handoff. id -> reason."""
    scope, skipped = {}, []
    for iid, r in readiness.items():
        if r.get("step_original_text") == "open" and "ONLY_COMPILED_TRANSCRIPTION_FOUND" in (r.get("blockers") or ""):
            if ident.parse_eo_id(iid) is None:  # unnumbered census rows (EO:UN:...) have no number to route by
                skipped.append(iid)
                continue
            scope[iid] = "transcription_only"
    for r in ident.read_jsonl(os.path.join(root, CLARK_HANDOFF)):
        iid = r.get("instrument_id")
        if iid and ident.parse_eo_id(iid) and iid not in scope:
            if iid in readiness and readiness[iid].get("step_original_text") == "done":
                continue
            scope[iid] = "clark_identified" if iid in universe else "clark_identified_not_in_universe"
    return scope, skipped


def proquest_search_hint(number, suffix):
    return f'ProQuest Congressional, Presidential Materials 1789-1936, phrase search "Executive Order No. {number}{suffix}"'


def route_order(iid, reason, dates, frags, pq_rows, pq_local, catalog):
    """One ROUTES row: where the order stands on the ladder and the single next action."""
    num, suffix = ident.parse_eo_id(iid)
    d = dates.get(iid, {})
    when = ident.parse_date(d.get("date") or "")
    leads = sorted({f["produced_by"] for f in frags.get(iid, []) if f["class"] == "transcription"})
    row = {"instrument_id": iid, "scope_reason": reason, "date": d.get("date", ""), "date_source": d.get("date_source", ""),
           "title": (d.get("title") or "")[:160], "transcription_leads": "|".join(leads),
           "proquest_file": "", "proquest_sha256": "", "proquest_pages": "", "proquest_text_layer": "",
           "proquest_link_supplied": "yes" if iid in pq_rows else "no", "fr_citation": "", "fr_pdf_url": "",
           "best_route": "", "route_status": "", "next_action": "", "action_owner": "", "lead_url_or_search": ""}
    local = pq_local.get(iid)
    cat = catalog.get(iid)
    if local:
        row.update({"proquest_file": local["file"], "proquest_sha256": local["sha256"], "proquest_pages": local["pages"],
                    "proquest_text_layer": local["text_layer_usable"], "best_route": "proquest_local",
                    "route_status": "file_verified_pages_unchecked",
                    "next_action": "Compare the PDF pages with the transcription; owner decides the custody grade",
                    "action_owner": "agent_check",
                    "lead_url_or_search": os.path.join(local.get("folder") or ident.PROQUEST_DIR, local["file"])})
    elif iid in pq_rows:
        row.update({"best_route": "proquest_supplied_link", "route_status": "awaiting_acquisition",
                    "next_action": "Upload the ProQuest PDF from the supplied link to the repository folder",
                    "action_owner": "owner", "lead_url_or_search": pq_rows[iid].get("rec") or pq_rows[iid].get("pdf") or ""})
    elif cat and (cat.get("citation") or cat.get("pdf_url")):
        row.update({"fr_citation": cat.get("citation", ""), "fr_pdf_url": cat.get("pdf_url", ""),
                    "best_route": "federal_register", "route_status": "fetch_request_proposed",
                    "next_action": "Enqueue PROPOSED_FETCH_REQUESTS.jsonl for the source-ladder job",
                    "action_owner": "machine_job", "lead_url_or_search": cat.get("pdf_url") or cat.get("html_url") or ""})
    elif cat:
        row.update({"best_route": "federal_register", "route_status": "in_ofr_catalog_no_citation",
                    "next_action": "OFR catalog lists the order without an FR citation; check govinfo FR issue for its date",
                    "action_owner": "agent_check", "lead_url_or_search": cat.get("html_url") or cat.get("raw_text_url") or ""})
    elif when and when >= ident.FIRST_FEDERAL_REGISTER:
        row.update({"best_route": "federal_register", "route_status": "fr_era_not_in_ofr_catalog",
                    "next_action": "Signed after the first Federal Register issue but not in the OFR catalog (which starts at EO 7532): "
                                   "search the 1936 FR volume on govinfo by date",
                    "action_owner": "agent_check",
                    "lead_url_or_search": f"https://www.govinfo.gov/app/collection/fr/{when.year}"})
    elif not suffix and GPO_VOLUMES[0] <= num <= GPO_VOLUMES[1]:
        row.update({"best_route": "gpo_bound_volumes", "route_status": "in_volume_range_not_found",
                    "next_action": "hathi-gpo-orders covers this range but did not match it: check the volume's index by number",
                    "action_owner": "agent_check", "lead_url_or_search": proquest_search_hint(num, suffix)})
    elif not suffix and HOOVER_VOLUMES[0] <= num <= HOOVER_VOLUMES[1]:
        row.update({"best_route": "ofr_hoover_compilation", "route_status": "in_volume_range_not_found",
                    "next_action": "ofr-compilations covers this range but did not match it: check Hoover vol. I by number",
                    "action_owner": "agent_check", "lead_url_or_search": proquest_search_hint(num, suffix)})
    elif when is None or when < ident.FIRST_FEDERAL_REGISTER:
        row.update({"best_route": "proquest_phrase_search", "route_status": "manual_lead",
                    "next_action": "Not on the supplied ProQuest list: find the record by phrase search and add its link to a new list",
                    "action_owner": "owner", "lead_url_or_search": proquest_search_hint(num, suffix)})
    else:
        row.update({"best_route": "nara_rg11", "route_status": "manual_lead",
                    "next_action": "National Archives RG 11 numbered series (catalog NAID 299999)",
                    "action_owner": "owner", "lead_url_or_search": "https://catalog.archives.gov/id/299999"})
    return row


def fetch_request(row, dates):
    """A source-ladder request for an FR-era order with an OFR citation (never for ProQuest: sign-in only)."""
    urls = [u for u in (row["fr_pdf_url"],) if u and u.startswith("http")]
    d = dates.get(row["instrument_id"], {})
    req = {"request_id": f"lewis:{row['instrument_id']}:{row['fr_citation'].replace(' ', '')}",
           "instrument_id": row["instrument_id"], "urls": urls, "citation": row["fr_citation"],
           "step": "original_text", "requested_by": JOB,
           "note": f"Original text of {row['instrument_id'].replace('EO:', 'EO ')}"
                   + (f", signed {d['date']}" if d.get("date") else "")
                   + "; the project holds only a compiled transcription (readiness blocker ONLY_COMPILED_TRANSCRIPTION_FOUND)"}
    if request_contract is not None:
        audit = request_contract.normalize_request(req, source=f"{JOB} proposal")
        req["_contract_status"] = audit.get("status", "")
        req["_contract_errors"] = audit.get("errors", [])
    return req


# --- main ----------------------------------------------------------------------------------------

def write_csv(path, rows, fields=None):
    fields = fields or (list(rows[0].keys()) if rows else ["empty"])
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def run(root, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    universe = ident.load_universe(root)
    readiness = ident.load_readiness(root)
    frags = ident.load_fragments(root, classes=("official", "transcription"))
    dates = ident.load_dates(root, frags)
    pq_rows = {ident.canon_id(*ident.parse_eo_id(str(r["id"]))): r for r in ident.load_proquest_rows(root)}
    catalog = {r["id"]: r for r in ident.read_csv(os.path.join(root, ident.OFR_CATALOG))}
    problems = []
    if not universe:
        problems.append("universe file missing: " + ident.UNIVERSE)
    if not readiness:
        problems.append("readiness output missing: " + ident.READINESS)

    pq_local = pinakes_orders(root)
    inv_rows = list(pq_local.values()) if pq_local else []
    proquest_authority = "pinakes-proquest-ingest" if pq_local else "lewis inventory (Pinakes has not run)"
    if not pq_local:
        inv_rows, pq_local = inventory_proquest(root, universe, out_dir)
    scope, skipped = load_scope(root, readiness, universe)
    if skipped:
        problems.append(f"{len(skipped)} transcription-only ids have no order number and were not routed: " + ", ".join(skipped[:5]))
    routes = [route_order(i, reason, dates, frags, pq_rows, pq_local, catalog)
              for i, reason in sorted(scope.items(), key=lambda kv: (ident.parse_eo_id(kv[0]) or (0, ""), kv[0]))]
    proposals = [fetch_request(r, dates) for r in routes if r["route_status"] == "fetch_request_proposed"]
    fragments = ([] if proquest_authority == "pinakes-proquest-ingest" else
                 [proquest_fragment(pq_local[i], dates) for i in sorted(pq_local, key=lambda x: ident.parse_eo_id(x) or (0, ""))])

    write_csv(os.path.join(out_dir, "ROUTES.csv"), routes, list(routes[0].keys()) if routes else None)
    inv_fields = ["file", "instrument_id", "year", "number", "suffix", "copy", "in_universe", "name_parsed", "bytes", "sha256",
                  "pdf_signature", "pages", "text_chars", "text_quality", "text_layer_usable", "text_path", "text_sha256",
                  "duplicate_of", "pdf_error"]
    write_csv(os.path.join(out_dir, "PROQUEST_INVENTORY.csv"), inv_rows, inv_fields)
    with open(os.path.join(out_dir, "PROPOSED_FETCH_REQUESTS.jsonl"), "w", encoding="utf-8") as fh:
        for p in proposals:
            fh.write(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n")
    with open(os.path.join(out_dir, "FRAGMENTS.jsonl"), "w", encoding="utf-8") as fh:
        for f in fragments:
            fh.write(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n")

    by_route = collections.Counter((r["best_route"], r["route_status"]) for r in routes)
    summary = {
        "job": JOB, "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope": {"orders": len(routes), "by_reason": dict(collections.Counter(r["scope_reason"] for r in routes))},
        "routes": {f"{k[0]}:{k[1]}": v for k, v in sorted(by_route.items())},
        "by_owner": dict(collections.Counter(r["action_owner"] for r in routes)),
        "proquest_folder": {"pdf_files": len(inv_rows),
                            "unique_files": sum(1 for r in inv_rows if not r["duplicate_of"]),
                            "orders_with_verified_pdf": len(pq_local),
                            "orders_in_lewis_scope_with_pdf": sum(1 for r in routes if r["best_route"] == "proquest_local"),
                            "pdfs_for_orders_outside_lewis_scope": sum(1 for i in pq_local if i not in scope),
                            "usable_text_layers": sum(1 for r in inv_rows if r.get("text_layer_usable") == "yes"),
                            "bad_signature": sum(1 for r in inv_rows if r["pdf_signature"] == "no"),
                            "unparsed_names": sum(1 for r in inv_rows if r["name_parsed"] == "no"),
                            "supplied_links_total": len(pq_rows),
                            "supplied_links_in_lewis_scope": sum(1 for r in routes if r["proquest_link_supplied"] == "yes")},
        "proposed_fetch_requests": {"count": len(proposals),
                                    "contract_valid": sum(1 for p in proposals if p.get("_contract_status") in ("", "valid", "ok"))
                                    if request_contract is None else sum(1 for p in proposals if not p.get("_contract_errors")),
                                    "contract_available": request_contract is not None},
        "fragments_written": len(fragments), "proquest_authority": proquest_authority,
        "pypdf_available": pypdf is not None,
        "inputs": {"universe": len(universe), "readiness_rows": len(readiness), "dated_orders": len(dates),
                   "ofr_catalog_rows": len(catalog), "clark_handoff_rows": len(ident.read_jsonl(os.path.join(root, CLARK_HANDOFF)))},
        "problems": problems,
        "what_this_is_not": "Leads and byte facts only. No readiness step, count, custody grade or legal status changes here.",
    }
    with open(os.path.join(out_dir, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    write_report(os.path.join(out_dir, "REPORT.md"), summary, routes)
    return summary


def write_report(path, s, routes):
    lines = ["# Lewis: originals for transcription-only orders", "",
             f"Generated {s['generated_utc']}. Leads and verified file facts; no count or grade changes.", "",
             f"**Scope: {s['scope']['orders']} orders** ({', '.join(f'{k} {v}' for k, v in sorted(s['scope']['by_reason'].items()))}).", "",
             "## Where they stand on the ladder", "", "| Route | Status | Orders |", "|---|---|---:|"]
    for k, v in sorted(s["routes"].items(), key=lambda kv: -kv[1]):
        r, st = k.split(":", 1)
        lines.append(f"| {r} | {st} | {v} |")
    p = s["proquest_folder"]
    lines += ["", "## ProQuest folder", "",
              f"{p['pdf_files']} PDF files ({p['unique_files']} unique by SHA-256) cover {p['orders_with_verified_pdf']} orders; "
              f"{p['orders_in_lewis_scope_with_pdf']} of them are in Lewis's scope and {p['pdfs_for_orders_outside_lewis_scope']} "
              f"belong to orders outside it (Clark's no-text orders, mostly). {p['usable_text_layers']} text layers pass the "
              f"quality screen (handwritten originals give noise and are excluded). The supplied link list has {p['supplied_links_total']} "
              f"links, {p['supplied_links_in_lewis_scope']} for orders in this scope.", "",
              "## Proposed fetch requests", "",
              f"{s['proposed_fetch_requests']['count']} requests for the source-ladder job in `PROPOSED_FETCH_REQUESTS.jsonl` "
              f"(validated with the source-ladder request contract: {s['proposed_fetch_requests']['contract_available']}). "
              "To enqueue them: `python jobs/source-ladder/request_contract.py enqueue --input jobs/lewis-originals/output/PROPOSED_FETCH_REQUESTS.jsonl --queue research/readiness/FETCH_QUEUE.jsonl`.", "",
              "## Next actions by owner", "", "| Owner | Orders |", "|---|---:|"]
    for k, v in sorted(s["by_owner"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v} |")
    lines += ["", "## First twenty rows", "", "| Order | Date | Route | Status | Next action |", "|---|---|---|---|---|"]
    for r in routes[:20]:
        lines.append(f"| {r['instrument_id']} | {r['date']} | {r['best_route']} | {r['route_status']} | {r['next_action'][:90]} |")
    if s["problems"]:
        lines += ["", "## Problems", ""] + [f"- {x}" for x in s["problems"]]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
    out_dir = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
    s = run(root, out_dir)
    print(json.dumps({k: s[k] for k in ("scope", "routes", "proquest_folder", "proposed_fetch_requests", "problems")}, indent=2))


if __name__ == "__main__":
    main()
