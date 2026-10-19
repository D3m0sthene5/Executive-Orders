"""American Presidency Project (APP) page footnotes as structured leads.

Reads jobs/app-executive-orders/output/DOCUMENTS.jsonl (live pages) and MIRROR_DOCUMENTS.jsonl (web-archive
captures of the same pages), never writes there, and splits every footnote into sentences. Each sentence gets
one or more note types:

* fr_citation:   a Federal Register publication note about this order ("published in the Federal Register on
                 April 26", "3 FR 547", "The annexes are printed in the Federal Register of July 1, 1981")
* not_published: the order was not printed / published / filed in the Federal Register
* revoked_by, amended_by, superseded_by: the note says another order revoked (rescinded), amended (modified)
                 or superseded this order
* other:         anything else (press release, release place, source citation, cross-reference, APP note)

Outputs: FOOTNOTE_LEADS.csv/.jsonl (one row per sentence and type), EDGES.csv (the revoked/amended/superseded
rows in jobs/later-events' EDGES.csv column shape; claim-kit reads every job's EDGES.csv as target/actor pairs),
SUMMARY.json.

These are editorial notes on a secondary transcription: leads, never endings, effective dates, status
findings or evidence that an order was or was not published. They change no census, ledger, codebook or count.
"""

import collections
import csv
import datetime
import importlib.util
import json
import os
import pathlib
import re

JOB = "app-footnote-leads"
SOURCE_JOB = "app-executive-orders"
SOURCE_OUT = f"jobs/{SOURCE_JOB}/output"
RECORDS = (("DOCUMENTS.jsonl", "live"), ("MIRROR_DOCUMENTS.jsonl", "archive"))
TYPES = ("fr_citation", "not_published", "revoked_by", "amended_by", "superseded_by", "other")
EDGE_COLUMNS = [
    "edge_id", "acting_id", "acting_label", "target_id", "target_label", "target_in_universe",
    "mechanism", "qualifier", "date_candidate", "date_basis", "date_flags", "stated_effective_date",
    "evidence_type", "stated_on", "source_id", "source_url", "source_sha256",
    "page_or_item", "note_label", "quote_kind", "quote_span", "quote",
]
LEAD_COLUMNS = ["instrument_id", "app_path", "app_node", "note_type", "detail", "referenced_eo", "fr_volume",
                "fr_page", "fr_publication_date_text", "fr_publication_date_inferred", "sentence", "raw_note",
                "lanes", "page_sha256", "url"]

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov",
                                      "dec"], 1)}
ABBREV = {"no", "nos", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec", "comp",
          "p", "pp", "u.s", "fed", "reg", "stat", "vol", "calif", "colo", "fla", "tex", "va", "md", "mass", "mr", "mrs",
          "dr", "st", "gen", "lt", "col", "inc", "co", "ltd", "sec", "secs", "ch", "cf"}
SENTENCE_BREAK = re.compile(r"[.!?]\s+(?=[\"“(]?[A-Z*])")
FR_CITE = re.compile(r"\b(\d{1,3})\s*F\.?\s?R\.?\s*(\d{1,6})\b")
FR_PUBLISHED = re.compile(
    r"\b(?:was|were|is|are|will\s+be|to\s+be)\s+(?:also\s+)?(?:published|printed|reproduced)\s+(?:in\s+(?:the\s+)?)"
    r"[\"“]?(?:Federal\s+Register|FEDERAL\s+REGISTER)[\"”]?(?:\s+(?:on|of|dated)\s+([A-Z][a-z]+\.?\s+\d{1,2}(?:,\s*\d{4})?))?",
    re.I)
NOT_PUBLISHED = re.compile(
    r"\bnot\s+(?:been\s+)?(?:printed|published|filed)\s+(?:in|with)\s+(?:the\s+)?(?:Federal\s+Register|Office\s+of\s+the\s+"
    r"Federal\s+Register|Division\s+of\s+the\s+Federal\s+Register)|\[\s*not\s+published\.?\s*\]", re.I)
VERB_BY = re.compile(
    r"\b(revoked|rescinded|amended|modified|superseded)\b((?:\s+(?:in\s+part|in\s+its\s+entirety|further|also))*)"
    r"\s+by\b", re.I)
SELF_SUBJECT = re.compile(r"\b(?:this|the\s+said|the)\s+(?:Executive\s+)?order\b", re.I)
VERB_TYPE = {"revoked": "revoked_by", "rescinded": "revoked_by", "amended": "amended_by", "modified": "amended_by",
             "superseded": "superseded_by"}
VERB_MECHANISM = {"revoked": "revocation", "rescinded": "rescission", "amended": "amendment",
                  "modified": "modification", "superseded": "supersession"}
# Weekly Compilation timing notes: the order had not reached the Federal Register when that issue went to press.
NOT_YET_FILED = re.compile(r"before\s+the\s+cutoff\s+time|not\s+received\s+in\s+time", re.I)
OTHER_KINDS = [
    ("weekly_compilation_timing", NOT_YET_FILED),
    ("press_release", re.compile(r"press\s+release|announced\s+by\s+the\s+White\s+House|White\s+House\s+(?:Press\s+Office\s+)?announced|released\s+by\s+the\s+(?:Office|White\s+House)|"
                                 r"Office\s+of\s+the\s+(?:White\s+House\s+)?Press\s+Secretary|released\s+on\s+[A-Z]", re.I)),
    ("release_place", re.compile(r"\breleased\s+(?:at|in)\s+[A-Z]", re.I)),
    ("source_citation", re.compile(r"^\s*SOURCE\s*:", re.I)),
    ("app_editorial_note", re.compile(r"^\s*APP\s+NOTE|Gerhard\s+Peters|can\s+be\s+found\s+here", re.I)),
    ("list_or_table_item", re.compile(r"^\s*(?:\d{1,3}\.|[A-Z][A-Z ,'-]{3,}$|REV\.)")),
    ("cross_reference", re.compile(r"^\s*(?:NOTE\s*:\s*)?For\s+(?:the|a|an)\b|\bsee\s+(?:the\s+)?(?:following|page|item)", re.I)),
]


def load_later_events(repo):
    """later-events' own EO-reference parser, so numbers, lists, ranges and suffixes normalise identically."""
    path = repo / "jobs" / "later-events" / "later_events.py"
    spec = importlib.util.spec_from_file_location("later_events_refs", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sentences(note):
    """Paragraphs, then sentences; whitespace collapsed. Each piece is an exact substring of the collapsed note."""
    out = []
    for para in re.split(r"\n\s*\n|\s+/\s+", note):
        para = " ".join(para.split())
        if not para:
            continue
        start = 0
        for m in SENTENCE_BREAK.finditer(para):
            word = re.search(r"([A-Za-z]+(?:\.[A-Za-z]+)*)$", para[:m.start()])
            token = word.group(1).lower() if word else ""
            if para[m.start()] == "." and (token in ABBREV or (len(token) == 1 and token.isalpha())):
                continue  # "Aug. 22", "No. 8757", "3 CFR, 1943-1948 Comp., p. 662", initials
            piece = para[start:m.start() + 1].strip()
            if piece:
                out.append(piece)
            start = m.end()
        tail = para[start:].strip()
        if tail:
            out.append(tail)
    return out


def infer_date(text, order_date):
    """'April 26' + the order's own date -> ISO date (the first such date on or after the order's date)."""
    m = re.match(r"([A-Za-z]+)\.?\s+(\d{1,2})(?:,\s*(\d{4}))?", text or "")
    if not m or m.group(1)[:3].lower() not in MONTHS:
        return ""
    month, day = MONTHS[m.group(1)[:3].lower()], int(m.group(2))
    try:
        if m.group(3):
            return datetime.date(int(m.group(3)), month, day).isoformat()
        signed = datetime.date.fromisoformat(order_date[:10])
    except (TypeError, ValueError):
        return ""
    for year in (signed.year, signed.year + 1):
        try:
            d = datetime.date(year, month, day)
        except ValueError:
            continue
        if d >= signed:
            return d.isoformat()
    return ""


def classify(iid, sentence, order_date, refs_fn):
    """[(note_type, fields)] for one footnote sentence of the page for order iid."""
    out = []
    refs = refs_fn(sentence)
    others = [r for r in refs if r["id"] != iid]
    other_ids = list(dict.fromkeys(r["id"] for r in others))
    # later-order notes: "<this order> was (further) amended by Executive Order N of <date>, ..."
    for m in VERB_BY.finditer(sentence):
        before, tail = sentence[:m.start()], sentence[m.end():]
        tail_refs = refs_fn(tail)
        if not tail_refs:
            continue
        if tail_refs[0]["id"] == iid:
            continue  # "the orders revoked by Executive Order <this order>": this order acted, not a later event
        before_ids = {r["id"] for r in refs_fn(before)}
        subject_is_self = iid in before_ids or (not before_ids and (SELF_SUBJECT.search(before) or not before.strip()))
        if not subject_is_self:
            continue  # the note is about another order
        actors = []
        for r in tail_refs:
            if r["id"] == iid:
                break
            actors.append(r)
        verb = m.group(1).lower()
        out.append((VERB_TYPE[verb], {"detail": f"{verb}{m.group(2).lower()} by", "mechanism": VERB_MECHANISM[verb],
                                      "qualifier": " ".join(m.group(2).lower().split()), "actors": actors,
                                      "referenced_eo": [a["id"] for a in actors]}))
    if NOT_PUBLISHED.search(sentence) and not NOT_YET_FILED.search(sentence):
        out.append(("not_published", {"detail": NOT_PUBLISHED.search(sentence).group(0), "referenced_eo": other_ids}))
    elif not other_ids or not out:
        pub = FR_PUBLISHED.search(sentence)
        cites = FR_CITE.findall(sentence)
        # An FR citation sitting next to another order is that order's citation, not this one's.
        own_cites = cites if not other_ids else []
        if pub or own_cites:
            date_text = pub.group(1) if pub and pub.group(1) else ""
            detail = "future tense: announced publication" if pub and re.search(r"will\s+be|to\s+be", pub.group(0), re.I) \
                else ("publication note" if pub else "citation")
            if pub and re.match(r"(?i)\s*(?:note\s*:\s*)?the\s+(?:annex|schedule|attach|map|tab|appendi|list)", sentence):
                detail += " (attachments)"
            out.append(("fr_citation", {
                "detail": detail, "referenced_eo": other_ids,
                "fr_volume": own_cites[0][0] if own_cites else "", "fr_page": own_cites[0][1] if own_cites else "",
                "fr_publication_date_text": date_text,
                "fr_publication_date_inferred": infer_date(date_text, order_date) if date_text else ""}))
    if not out:
        kind = next((name for name, pat in OTHER_KINDS if pat.search(sentence)), "unclassified")
        out.append(("other", {"detail": kind, "referenced_eo": other_ids}))
    return out


def run(repo, out):
    repo, out = pathlib.Path(repo), pathlib.Path(out)
    base = repo / SOURCE_OUT
    le = load_later_events(repo)
    refs_fn = le.eo_references
    out.mkdir(parents=True, exist_ok=True)
    # One footnote text per (order, page, note); both lanes are kept as provenance of the same note.
    notes = {}
    pages = collections.Counter()
    for name, lane in RECORDS:
        path = base / name
        if not path.is_file():
            continue
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                rec = json.loads(line)
                pages[lane] += 1
                note = (rec.get("footnote") or "").strip()
                if not note:
                    continue
                key = (rec.get("instrument_id") or "", rec.get("path") or "", " ".join(note.split()))
                cur = notes.setdefault(key, {"rec": rec, "note": note, "lanes": [], "sha": []})
                cur["lanes"].append(lane if lane == "live" else f"{(rec.get('capture') or {}).get('archive', 'archive')}"
                                    f" {(rec.get('capture') or {}).get('captured_utc', '')}".strip())
                cur["sha"].append(rec.get("sha256") or "")
    leads, edges = [], []
    # Captures that hold no text at all: the harvester reports them as APP "[Not Published.]" pages.
    path = base / "MIRROR_FAILURES.jsonl"
    empty = []
    if path.is_file():
        with open(path, encoding="utf-8") as fh:
            empty = [json.loads(l) for l in fh if l.strip()]
    for f in sorted((f for f in empty if f.get("reason") == "no_usable_text"), key=lambda f: (f.get("instrument_id") or "", f.get("path") or "")):
        leads.append({
            "instrument_id": f.get("instrument_id") or "", "app_path": f.get("path") or "", "app_node": "",
            "note_type": "not_published",
            "detail": ("APP page capture with no text (MIRROR_FAILURES no_usable_text); app-executive-orders reports these "
                       "as APP '[Not Published.]' pages; the marker itself is not stored"),
            "referenced_eo": "", "fr_volume": "", "fr_page": "", "fr_publication_date_text": "",
            "fr_publication_date_inferred": "", "sentence": "", "raw_note": "",
            "lanes": f"{f.get('archive')} {f.get('capture_timestamp')}", "page_sha256": "",
            "url": "https://www.presidency.ucsb.edu" + (f.get("path") or "")})
    by_type, orders_by_type = collections.Counter(), collections.defaultdict(set)
    for r in leads:
        by_type[r["note_type"]] += 1
        orders_by_type[r["note_type"]].add(r["instrument_id"] or r["app_path"])
    for (iid, app_path, _), n in sorted(notes.items()):
        rec = n["rec"]
        for sent in sentences(n["note"]):
            for ntype, f in classify(iid, sent, rec.get("date") or "", refs_fn):
                by_type[ntype] += 1
                orders_by_type[ntype].add(iid or app_path)
                leads.append({
                    "instrument_id": iid, "app_path": app_path, "app_node": rec.get("app_node") or "",
                    "note_type": ntype, "detail": f.get("detail", ""), "referenced_eo": "|".join(f.get("referenced_eo") or []),
                    "fr_volume": f.get("fr_volume", ""), "fr_page": f.get("fr_page", ""),
                    "fr_publication_date_text": f.get("fr_publication_date_text", ""),
                    "fr_publication_date_inferred": f.get("fr_publication_date_inferred", ""),
                    "sentence": sent, "raw_note": " ".join(n["note"].split()), "lanes": "|".join(n["lanes"]),
                    "page_sha256": "|".join(dict.fromkeys(n["sha"])), "url": rec.get("final_url") or rec.get("url") or ""})
                if ntype in ("revoked_by", "amended_by", "superseded_by") and iid:
                    for actor in f["actors"]:
                        edges.append({
                            "edge_id": f"APPFN-{iid}-{actor['id']}-{f['mechanism']}-{len(edges) + 1}",
                            "acting_id": actor["id"], "acting_label": "", "target_id": iid, "target_label": "",
                            "target_in_universe": "", "mechanism": f["mechanism"], "qualifier": f["qualifier"],
                            "date_candidate": actor.get("date") or "",
                            "date_basis": ("date stated next to the acting order in the APP footnote" if actor.get("date")
                                           else "no date in data"),
                            "date_flags": "app_editorial_note_not_ofr;lead_only_never_an_ending",
                            "stated_effective_date": "", "evidence_type": "app_footnote_on_target", "stated_on": iid,
                            "source_id": f"app:node/{rec.get('app_node')}", "source_url": rec.get("final_url") or rec.get("url") or "",
                            "source_sha256": n["sha"][0], "page_or_item": f"American Presidency Project page footnote "
                                                                          f"(transcription; not an official edition); APP node {rec.get('app_node')}",
                            "note_label": "APP footnote", "quote_kind": "verbatim_footnote_sentence", "quote_span": "",
                            "quote": sent})

    def write_csv(name, rows, fields):
        with open(out / name, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    write_csv("FOOTNOTE_LEADS.csv", leads, LEAD_COLUMNS)
    with open(out / "FOOTNOTE_LEADS.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for r in leads:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    write_csv("EDGES.csv", edges, EDGE_COLUMNS)
    other = collections.Counter(r["detail"] for r in leads if r["note_type"] == "other")
    fr = collections.Counter(r["detail"] for r in leads if r["note_type"] == "fr_citation")
    summary = {
        "job": JOB, "reads": SOURCE_OUT,
        "what_this_is": ("Editorial footnotes of American Presidency Project pages (a secondary transcription), parsed into "
                         "leads. Never an ending, effective date, status finding or proof of (non-)publication; no census, "
                         "ledger, codebook or count changes."),
        "pages_read": dict(pages),
        "distinct_footnotes": len(notes),
        "sentence_rows_by_type": {t: by_type.get(t, 0) for t in TYPES},
        "orders_or_pages_by_type": {t: len(orders_by_type.get(t, ())) for t in TYPES},
        "fr_citation_detail": dict(fr.most_common()),
        "other_detail": dict(other.most_common()),
        "fr_citations_with_volume_and_page": sum(1 for r in leads if r["note_type"] == "fr_citation" and r["fr_page"]),
        "fr_publication_dates_inferred": sum(1 for r in leads if r["fr_publication_date_inferred"]),
        "later_order_edges": len(edges),
        "edges_by_mechanism": dict(collections.Counter(e["mechanism"] for e in edges)),
    }
    with open(out / "SUMMARY.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return summary, leads, edges


def main():
    repo = pathlib.Path(os.environ.get("REPO_ROOT", ".")).resolve()
    out = pathlib.Path(os.environ["OUTPUT_DIR"]).resolve()
    summary, _, _ = run(repo, out)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
