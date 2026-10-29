"""Shepard: a reverse-citation index for land and other pre-1937 executive orders.

Named for Frank Shepard, whose citator (1873) listed every later citation of a decided case.

For each target order this job lists every later instrument that cites it, with the acting phrase
and where the citation was found. Four sources, each with its own evidence_type in EDGES.csv:

  shepard_ofr1989_table     rows of the 1989 OFR codification disposition table naming an ending or amending
                            instrument that jobs/ofr-codification-1989 does not already emit (PLOs, "Amended by",
                            "Modified by", "Continued by", and the "Revokes ..." direction)
  shepard_blm_plo_table     BLM "Table of Public Land Orders" rows (24 PDFs, PLOs 1-7898): each PLO's subject
                            heading names the orders it revokes, modifies or amends (see blm.py)
  shepard_text_number       held order texts citing a target by number ("Executive Order No. 6910")
  shepard_text_date         ... by date ("Executive order of June 6, 1906"), only when the date maps to exactly
                            one census order and no unnumbered census cluster
  shepard_text_reserve      ... by reserve number ("Power Site Reserve No. 325"), resolved to the earliest held
                            order naming that reserve
  shepard_fr_contents       Federal Register codification-guide entries already extracted by source-ladder and
                            fr-originals ("4872 (revoked by PLO 4620) ..... 6689")

Every row is a LEAD. A relation word printed near a citation is not a finding that the instrument did
what the word says, to that order, in whole. Nothing here changes a status, ledger, count or the codebook.
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
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import cites as C  # noqa: E402
import eo_identity as ident  # noqa: E402

csv.field_size_limit(min(2**31 - 1, 10**9))

JOB = "shepard-citations"
EDGE_COLUMNS = [
    "edge_id", "acting_id", "acting_label", "target_id", "target_label", "target_in_universe",
    "mechanism", "qualifier", "date_candidate", "date_basis", "date_flags", "stated_effective_date",
    "evidence_type", "stated_on", "source_id", "source_url", "source_sha256",
    "page_or_item", "note_label", "quote_kind", "quote_span", "quote",
]
PLO_COLUMNS = ["plo_number", "plo_id", "signature_date", "signature_date_raw", "fr_citation", "fr_volume", "fr_page",
               "subject", "eo_refs", "eo_ids", "eo_dates_unresolved", "plo_refs", "reserve_refs", "relation_words",
               "fr_contents_pages", "source_table", "source_url", "source_sha256", "pdf_page", "parse_flags"]
RESERVE_COLUMNS = ["reserve", "kind", "number", "creator_id", "creator_date", "status", "candidates"]
UNRESOLVED_COLUMNS = ["source", "citation_form", "cited", "citing_id", "reason", "candidates", "source_ref", "quote"]

TYPES = "jobs/x1-class-engine/output/TYPES.csv"
CATALOG = "jobs/later-events/output/CATALOG_INDEX.csv"
LATER_EDGES = "jobs/later-events/output/EDGES.csv"
DISPOSITION = "jobs/ofr-codification-1989/output/DISPOSITION_1989.csv"
CODIFICATION_FRAGMENTS = "jobs/ofr-codification-1989/output/FRAGMENTS.jsonl"
CLUSTERS = "jobs/census-completeness/output/CLUSTERS.csv"
CONTENTS_SOURCES = ["jobs/source-ladder/output/SOURCES.jsonl", "jobs/fr-originals/output/SOURCES.jsonl",
                    "jobs/fr-originals/data/full_run/SOURCES.jsonl"]
CODIFICATION_URL = "https://hdl.handle.net/2027/uiug.30112026470077"
LAND_TITLE_RE = re.compile(r"withdraw|reservation|refuge|reserve|public\s+land|national\s+forest|range\b|restor", re.I)
PROBE_ORDERS = ["EO:4109", "EO:4430", "EO:4262", "EO:4872", "EO:5038", "EO:5214", "EO:6143", "EO:6276", "EO:6604",
                "EO:6910", "EO:7185", "EO:7212", "EO:7452", "EO:7373", "EO:7435", "EO:7504", "EO:7509", "EO:7510",
                "EO:6210", "EO:5511", "EO:5799", "EO:1237", "EO:2901", "EO:709", "EO:3853", "EO:4810", "EO:7069",
                "EO:6740", "EO:1304", "EO:455"]
ENDING = {"revocation", "rescission", "supersession", "replacement", "termination", "vacation", "abolition"}
MAX_QUOTE = 600
MAX_UNRESOLVED = 20000


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def read_jsonl(path):
    out = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    return out


def norm_actor(value):
    """'Proc:2318' / 'PROC:2318' / 'EO:7442' -> upper-case prefix form used for de-duplication."""
    if not value:
        return ""
    head, _, tail = value.partition(":")
    return head.upper() + ":" + tail.upper()


# --- context ---------------------------------------------------------------------------------------

class Context:
    """Census, dates, targets and already-emitted edges, loaded once."""

    def __init__(self, root, fragments=None):
        self.root = root
        self.universe = ident.load_universe(root)
        self.canon = {}
        for iid in self.universe:
            p = ident.parse_eo_id(iid)
            self.canon[ident.canon_id(*p) if p else iid] = iid
        self.fragments = fragments if fragments is not None else ident.load_fragments(root)
        self.dates = ident.load_dates(root, self.fragments)
        self.types = {r["instrument_id"]: r for r in read_csv(os.path.join(root, TYPES))}
        self.catalog = {r["id"]: r for r in read_csv(os.path.join(root, CATALOG))}
        self.disposition = read_csv(os.path.join(root, DISPOSITION))
        self.targets, self.land = self._targets()
        self.by_date = self._date_index()
        self.known = self._known_edges()

    def census_id(self, number, suffix=""):
        """Census id for an order number, or None when the census has no such order."""
        try:
            return self.canon.get(ident.canon_id(int(number), suffix))
        except (TypeError, ValueError):
            return None

    def full_date(self, iid):
        d = (self.dates.get(iid) or {}).get("date", "")
        return d if len(d) >= 10 else ""

    def _targets(self):
        targets, land = set(), set()
        for iid, r in self.types.items():
            if iid in self.universe:
                targets.add(iid)
                if r.get("class") == "land":
                    land.add(iid)
        for iid in self.universe:
            d = self.full_date(iid) or (self.dates.get(iid) or {}).get("date", "")
            if d and d[:4].isdigit() and int(d[:4]) <= 1936:
                targets.add(iid)
        for iid, r in self.catalog.items():
            sd = r.get("signing_date") or ""
            if iid in self.universe and sd[:4].isdigit() and 1937 <= int(sd[:4]) <= 1942 and LAND_TITLE_RE.search(r.get("title") or ""):
                targets.add(iid)
                land.add(iid)
        return targets, land

    def _date_index(self):
        by = collections.defaultdict(set)
        for iid in self.universe:
            d = self.full_date(iid)
            if d:
                by[d].add(iid)
        for r in self.disposition:
            key, cid = r.get("key") or "", r.get("census_id") or ""
            if key.startswith("date:") and cid in self.universe:
                by[key[5:]].add(cid)
        self.clusters = collections.defaultdict(set)
        for r in read_csv(os.path.join(self.root, CLUSTERS)):
            if len(r.get("date", "")) >= 10:
                self.clusters[r["date"]].add(r.get("cluster_id", ""))
        return by

    def resolve_date(self, iso):
        """(census id, None) when the date maps to exactly one census order and no unnumbered cluster; else (None, reason)."""
        ids = sorted(self.by_date.get(iso, ()))
        if self.clusters.get(iso):
            return None, "unnumbered_census_cluster_same_date:" + "|".join(sorted(self.clusters[iso]))
        if len(ids) == 1:
            return ids[0], None
        if not ids:
            return None, "no_census_order_with_this_date"
        return None, "several_census_orders_same_date:" + "|".join(ids[:12])

    def _known_edges(self):
        """(acting, target, mechanism) already emitted by later-events and ofr-codification-1989."""
        known = set()
        for r in read_csv(os.path.join(self.root, LATER_EDGES)):
            known.add((norm_actor(r.get("acting_id")), r.get("target_id") or "", r.get("mechanism") or ""))
        for rec in read_jsonl(os.path.join(self.root, CODIFICATION_FRAGMENTS)):
            for d in rec.get("data") or []:
                known.add((norm_actor(d.get("actor")), rec.get("instrument_id") or "", d.get("mechanism") or ""))
        return known


# --- edge construction -----------------------------------------------------------------------------

class Edges:
    def __init__(self, ctx):
        self.ctx = ctx
        self.rows = []
        self.keys = {}
        self.skipped_known = collections.Counter()
        self.skipped = collections.Counter()
        self.unresolved = []

    def unresolved_row(self, **kw):
        if len(self.unresolved) < MAX_UNRESOLVED:
            row = {k: kw.get(k, "") for k in UNRESOLVED_COLUMNS}
            row["quote"] = C.squeeze(str(row["quote"]))[:MAX_QUOTE]
            self.unresolved.append(row)
        self.skipped["unresolved:" + kw.get("reason", "").split(":")[0]] += 1

    def add(self, *, acting, target, mechanism, evidence_type, source_id, source_url, source_sha256, page_or_item,
            quote, quote_kind, qualifier="", flags=(), note_label="", acting_label="", target_label="", stated_on="",
            quote_span="", dedupe_known=True, date_candidate="", date_basis=""):
        if not acting or not target or norm_actor(acting) == norm_actor(target):
            self.skipped["self_or_empty"] += 1
            return None
        if dedupe_known and (norm_actor(acting), target, mechanism) in self.ctx.known:
            self.skipped_known[evidence_type] += 1
            return None
        key = (evidence_type, norm_actor(acting), target, mechanism, qualifier, source_id)
        if key in self.keys:
            row = self.keys[key]
            if "occurrences=" in row["date_flags"]:
                n = int(re.search(r"occurrences=(\d+)", row["date_flags"]).group(1)) + 1
                row["date_flags"] = re.sub(r"occurrences=\d+", f"occurrences={n}", row["date_flags"])
            else:
                row["date_flags"] = ";".join(x for x in (row["date_flags"], "occurrences=2") if x)
            return row
        edge_id = "SH-" + hashlib.sha1("|".join(map(str, key + (quote_span, C.squeeze(quote)[:200]))).encode()).hexdigest()[:12]
        row = {"edge_id": edge_id, "acting_id": acting, "acting_label": acting_label, "target_id": target,
               "target_label": target_label, "target_in_universe": "yes" if target in self.ctx.universe else "no",
               "mechanism": mechanism, "qualifier": qualifier, "date_candidate": date_candidate,
               "date_basis": date_basis, "date_flags": ";".join(f for f in flags if f), "stated_effective_date": "",
               "evidence_type": evidence_type, "stated_on": stated_on, "source_id": source_id,
               "source_url": source_url, "source_sha256": source_sha256, "page_or_item": page_or_item,
               "note_label": note_label, "quote_kind": quote_kind, "quote_span": quote_span,
               "quote": C.squeeze(quote)[:MAX_QUOTE]}
        self.keys[key] = row
        self.rows.append(row)
        return row


def eo_or_other(ctx, kind, number, suffix=""):
    """Instrument id: the census id for an EO when the census has it, else 'EO:<n>', 'PLO:<n>', 'PROC:<n>'."""
    if kind == "EO":
        return ctx.census_id(number, suffix) or f"EO:{int(number)}{suffix}"
    return f"{kind}:{int(number)}{suffix}"


# --- source 1: the 1989 OFR disposition table --------------------------------------------------------

AMEND_VERB = re.compile(
    r"(?P<verb>Amended|Modified|Continued|Ratified|Supplemented|Extended|Clarified|Corrected|Revoked(?:inpart)?|"
    r"Superseded|Terminated|Restored)(?P<by>by)?(?P<kind>EOs?|Procs?\.?|PLOs?)(?P<nums>\d+[A-Z]?(?:,(?:and)?\d+[A-Z]?)*)",
    re.I)
VERB_MECH = {"amended": "amendment", "modified": "modification", "continued": "continuation",
             "ratified": "ratification", "supplemented": "supplementation", "extended": "extension",
             "clarified": "clarification", "corrected": "correction", "revoked": "revocation",
             "revokedinpart": "revocation", "superseded": "supersession", "terminated": "termination",
             "restored": "restoration"}
CATEGORY_MECH = {"revoked": "revocation", "superseded": "supersession", "terminated": "termination",
                 "nullified": "nullification", "replaced": "replacement", "abolished": "abolition",
                 "revokes_other_document": "revocation", "supersedes_other_document": "supersession",
                 "amends_other_document": "amendment", "modifies_other_document": "modification",
                 "terminates_other_document": "termination", "continues_other_document": "continuation",
                 "abolishes_other_document": "abolition", "discontinues_other_document": "termination"}


def codification_source(ctx):
    for rec in read_jsonl(os.path.join(ctx.root, CODIFICATION_FRAGMENTS)):
        for s in rec.get("sources") or []:
            if s.get("sha256"):
                return s.get("url") or CODIFICATION_URL, s["sha256"]
    return CODIFICATION_URL, ""


def from_disposition(ctx, edges):
    url, sha = codification_source(ctx)
    n_rows = 0
    for r in ctx.disposition:
        row_id = r.get("census_id") or ""
        if not row_id:
            continue
        n_rows += 1
        page = f"OFR Codification 1945-1989 (1989), Executive Orders disposition table, printed page {r.get('printed')}, PDF page {r.get('page')}"
        flags = ["status_as_of_1989-01-20", "ocr_table_cell_not_human_verified"]
        if r.get("pairing_confidence") and r["pairing_confidence"] != "high":
            flags.append("pairing_confidence_" + r["pairing_confidence"])
        common = dict(evidence_type="shepard_ofr1989_table", source_id=f"ofr1989:row:{r.get('seq')}", source_url=url,
                      source_sha256=sha, page_or_item=page, quote_kind="ocr_table_cell")
        # Amendments column: 'Amendedby EOs 8536,9787' (row is the target) / 'AmendedEO 2932' (row is the actor).
        flat = re.sub(r"\s+", "", r.get("amendments") or "").replace("EOS", "EOs")
        for m in AMEND_VERB.finditer(flat):
            mech = VERB_MECH[m.group("verb").lower()]
            kind = "PLO" if m.group("kind").upper().startswith("PLO") else "PROC" if m.group("kind").lower().startswith("proc") else "EO"
            qual = "in part" if "inpart" in m.group("verb").lower() else ""
            for num in re.findall(r"\d+[A-Z]?", m.group("nums")):
                n, suf = re.match(r"(\d+)([A-Z]?)", num).groups()
                other = eo_or_other(ctx, kind, n, suf)
                acting, target = (other, row_id) if m.group("by") else (row_id, other)
                edges.add(acting=acting, target=target, mechanism=mech, qualifier=qual, stated_on=row_id,
                          flags=flags + ["amendments_column"], note_label="amendments column",
                          quote=r.get("amendments"), **common)
        # Disposition column: acting_documents as parsed by ofr-codification-1989, with the verb before each.
        cat = r.get("category") or ""
        mech = CATEGORY_MECH.get(cat)
        acting_docs = [a for a in (r.get("acting_documents") or "").split("|") if a]
        if not mech or not acting_docs:
            continue
        disp_flat = re.sub(r"\s+", "", r.get("disposition") or "")
        for a in acting_docs:
            kind, _, num = a.partition(":")
            if kind not in ("EO", "PLO", "Proc") or not re.fullmatch(r"\d+[A-Z]?", num):
                continue
            n, suf = re.match(r"(\d+)([A-Z]?)", num).groups()
            other = eo_or_other(ctx, "PROC" if kind == "Proc" else kind, n, suf)
            own_mech, qual = mech, ""
            pos = disp_flat.find(num)
            if pos > 0:
                verbs = list(re.finditer(r"(Revoked(?:inpart)?|Superseded|Terminated|Amended|Modified|Nullified|Abolished)",
                                         disp_flat[:pos], re.I))
                if verbs:
                    v = verbs[-1].group(1).lower()
                    own_mech = VERB_MECH.get(v, {"nullified": "nullification", "abolished": "abolition"}.get(v, mech))
                    qual = "in part" if "inpart" in v else ""
            if cat.endswith("_other_document"):
                acting, target = row_id, other
            else:
                acting, target = other, row_id
            edges.add(acting=acting, target=target, mechanism=own_mech, qualifier=qual, stated_on=row_id,
                      flags=flags + ["disposition_column", "category_" + cat], note_label="disposition column",
                      quote=r.get("disposition"), **common)
    return n_rows


# --- source 2: BLM Public Land Order tables ------------------------------------------------------------

def plo_rows_and_edges(ctx, edges, tables, reserve_map):
    """PLO_TABLE rows from parsed BLM tables, and their edges. tables: dicts from blm.fetch_tables()."""
    out = []
    for t in tables:
        rows = C.parse_plo_table(t.get("pages") or [], t.get("lo"), t.get("hi"))
        t["rows_parsed"] = len(rows)
        for row in rows:
            plo_id = f"PLO:{row['number']}"
            refs = C.plo_subject_refs(row["subject"])
            eo_refs, eo_ids, unresolved, plo_refs, reserves, words = [], [], [], [], [], set()
            label = f"PLO {row['number']}" + (f" ({row['fr_citation']})" if row["fr_citation"] else "")
            page = f"BLM Table of Public Land Orders {t['name']}, PDF page {row['pdf_page']}, row PLO {row['number']}"
            base = dict(evidence_type="shepard_blm_plo_table", source_id=f"blm-plo-table:{t['name']}",
                        source_url=t["url"], source_sha256=t.get("sha256") or "", page_or_item=page,
                        quote=row["raw"], quote_kind="table_row_text_layer", acting_label="",
                        date_candidate="", date_basis="")
            for ref in refs:
                words.update(ref["words"])
                qual = "in part" if ref["partial"] else ""
                flags = ["blm_editorial_subject_heading", "relation_word:" + (ref["word"] or "none")]
                if ref["negated"]:
                    flags.append("negation_in_clause")
                if ref["kind"] == "eo_number":
                    num = re.match(r"(\d+)([A-Z]?)", ref["value"])
                    target = eo_or_other(ctx, "EO", num.group(1), num.group(2))
                    stated = ref["stated_date"]
                    cd = ctx.full_date(target)
                    if stated and cd and stated != cd:
                        flags.append(f"stated_date_{stated}_differs_from_census_date_{cd}")
                    eo_refs.append(f"{target}@{stated or cd}={ref['mechanism']}{'(in part)' if qual else ''}")
                    eo_ids.append(target)
                    edges.add(acting=plo_id, target=target, mechanism=ref["mechanism"], qualifier=qual, flags=flags,
                              note_label="subject heading: " + ref["clause"][:120], acting_label=label,
                              stated_on=plo_id, **{k: v for k, v in base.items() if k != "acting_label"})
                elif ref["kind"] == "eo_date":
                    target, why = ctx.resolve_date(ref["value"])
                    if target:
                        eo_refs.append(f"{target}@{ref['value']}={ref['mechanism']}{'(in part)' if qual else ''}")
                        eo_ids.append(target)
                        edges.add(acting=plo_id, target=target, mechanism=ref["mechanism"], qualifier=qual,
                                  flags=flags + ["resolved_by_date_unique_in_census",
                                                 "unnumbered_orders_outside_census_may_share_date"],
                                  note_label="subject heading (date): " + ref["clause"][:120], acting_label=label,
                                  stated_on=plo_id, **{k: v for k, v in base.items() if k != "acting_label"})
                    else:
                        unresolved.append(f"{ref['value']}:{why.split(':')[0]}")
                        edges.unresolved_row(source="blm_plo_table", citation_form="date", cited=ref["value"],
                                             citing_id=plo_id, reason=why, source_ref=page, quote=ref["clause"])
                elif ref["kind"] == "plo":
                    other = f"PLO:{ref['value']}"
                    plo_refs.append(f"{other}={ref['mechanism']}{' by' if ref['actor_named'] else ''}")
                    acting, target = (other, plo_id) if ref["actor_named"] else (plo_id, other)
                    edges.add(acting=acting, target=target, mechanism=ref["mechanism"], qualifier=qual, flags=flags,
                              note_label="subject heading: " + ref["clause"][:120], stated_on=plo_id,
                              acting_label=label if acting == plo_id else "",
                              **{k: v for k, v in base.items() if k != "acting_label"})
                elif ref["kind"] == "reserve":
                    reserves.append(ref["value"])
                    creator = reserve_map.get(ref["value"], {}).get("creator_id")
                    if creator:
                        edges.add(acting=plo_id, target=creator, mechanism=ref["mechanism"], qualifier=qual,
                                  flags=flags + ["resolved_by_reserve_number", "reserve_creator_inferred"],
                                  note_label=f"subject heading ({ref['phrase']}): " + ref["clause"][:100],
                                  acting_label=label, stated_on=plo_id,
                                  **{k: v for k, v in base.items() if k != "acting_label"})
            out.append({"plo_number": row["number"], "plo_id": plo_id, "signature_date": row["date"],
                        "signature_date_raw": row["date_raw"], "fr_citation": row["fr_citation"],
                        "fr_volume": row["fr_volume"], "fr_page": row["fr_page"], "subject": row["subject"],
                        "eo_refs": " | ".join(eo_refs), "eo_ids": "|".join(dict.fromkeys(eo_ids)),
                        "eo_dates_unresolved": "|".join(unresolved), "plo_refs": " | ".join(plo_refs),
                        "reserve_refs": "|".join(dict.fromkeys(reserves)), "relation_words": "|".join(sorted(words)),
                        "fr_contents_pages": "", "source_table": t["name"], "source_url": t["url"],
                        "source_sha256": t.get("sha256") or "", "pdf_page": row["pdf_page"],
                        "parse_flags": "|".join(row["flags"] + (["carried_forward_text"] if t.get("carried_forward") else []))})
    return out


# --- source 3: held texts ---------------------------------------------------------------------------

def _fr_pages_module():
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "source-ladder"))
    try:
        import fr_pages  # noqa: WPS433
        return fr_pages
    except ImportError:
        return None


FR_PAGES = None


def strip_header(text):
    i = text.find("\n=== PDF page")
    if i >= 0:
        return text[i:], i
    if re.match(r"(?:Instrument|Wanted|Source|SHA-256|Location|Machine)[^\n]*:", text):
        j = text.find("\n\n")
        if 0 <= j < 2000:
            return text[j:], j
    return text, 0


def own_span(text, iid):
    """(start, end, located) of the citing order's own text inside a Federal Register page text.

    From its heading ('EXECUTIVE ORDER 7532') or, failing that, from the filing line before its closing tag
    ('[No. 7532]'), to the next filing line ('[F. R. Doc. ...]'). Neighbouring documents on the same pages are
    cut away. located=False means neither marker was found and the whole text is used."""
    global FR_PAGES
    if FR_PAGES is None:
        FR_PAGES = _fr_pages_module() or False
    p = ident.parse_eo_id(iid)
    if not FR_PAGES or not p:
        return 0, len(text), False
    number = f"{p[0]}{p[1] if p[1] and p[1][0] != '-' and p[1] != '½' else ''}"
    pats = dict(FR_PAGES.marker_patterns(number))
    filing = FR_PAGES.FILING
    m = pats["heading"].search(text)
    if m and FR_PAGES.heading_context(text, m.start()) != "reference":
        f = filing.search(text, m.end())
        return m.start(), f.end() if f else len(text), True
    m = pats["closing_number_tag"].search(text)
    if m:
        prev = [f.end() for f in filing.finditer(text, 0, m.start())]
        f = filing.search(text, m.end())
        return (prev[-1] if prev else 0), (f.end() if f else len(text)), True
    return 0, len(text), False


def iter_held_texts(ctx):
    """(citing id, fragment summary, body text, offset of body in file, flags) for every held order text, once each."""
    seen = set()
    order = {"official": 0, "archival_replica": 1, "transcription": 2}
    items = sorted(((iid, f) for iid, fs in ctx.fragments.items() for f in fs),
                   key=lambda x: (order.get(x[1]["class"], 3), x[0], x[1]["text_path"] or ""))
    for iid, f in items:
        path = f.get("text_path")
        if not path or path in seen or not os.path.isfile(path):
            continue
        seen.add(path)
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                raw = fh.read(3_000_000)
        except OSError:
            continue
        flags = []
        notes = []
        if f["produced_by"] == "wikisource-texts":
            body, off, notes = C.wikisource_parts(raw)
        else:
            body, off = strip_header(raw)
        if f["produced_by"] in ("fr-originals",) or "FR-" in (f.get("url") or ""):
            s, e, located = own_span(body, iid)
            if located:
                body, off = body[s:e], off + s
            else:
                flags.append("citing_span_not_located_neighbouring_documents_possible")
        if f["class"] == "transcription":
            flags.append("transcription_may_include_editorial_notes")
        yield iid, f, body, off, flags, notes


def build_reserve_map(ctx):
    """'PSR:325' -> creator: the earliest-dated target order whose own text (first 4,000 characters) or index title
    names the reserve. Ties or undated candidates leave the reserve unresolved."""
    cands = collections.defaultdict(set)
    for iid, f, body, off, flags, _notes in iter_held_texts(ctx):
        if iid not in ctx.targets:
            continue
        for s, e, code, n, phrase in C.reserve_mentions(body[:4000]):
            cands[f"{code}:{n}"].add(iid)
    for iid, r in ctx.types.items():
        if iid not in ctx.targets:
            continue
        for s, e, code, n, phrase in C.reserve_mentions(" ".join([r.get("app_title") or "", r.get("wpa_summary") or ""])):
            cands[f"{code}:{n}"].add(iid)
    out = {}
    for key, ids in cands.items():
        dated = sorted((ctx.full_date(i), i) for i in ids if ctx.full_date(i))
        row = {"reserve": key, "kind": key.split(":")[0], "number": key.split(":")[1], "creator_id": "",
               "creator_date": "", "candidates": "|".join(f"{i}@{ctx.full_date(i) or '?'}" for i in sorted(ids))}
        if not dated:
            row["status"] = "no_dated_candidate"
        elif len(dated) > 1 and dated[0][0] == dated[1][0]:
            row["status"] = "tie_on_earliest_date"
        else:
            row.update(creator_id=dated[0][1], creator_date=dated[0][0], status="earliest_naming_order")
        out[key] = row
    return out


def from_texts(ctx, edges, reserve_map, limit=None):
    stats = collections.Counter()
    for iid, f, body, off, tflags, notes in iter_held_texts(ctx):
        stats["texts"] += 1
        stats["texts_" + f["produced_by"]] += 1
        if limit and stats["texts"] > limit:
            break
        acting_date = ctx.full_date(iid)
        src = dict(source_id="text:" + os.path.relpath(f["text_path"], ctx.root).replace(os.sep, "/"),
                   source_url=f.get("url") or "", source_sha256=f.get("sha256") or "",
                   page_or_item=(f.get("page_or_item") or "") + f" [held text of {iid}, produced by {f['produced_by']}]")

        def emit(target, s, e, form, extra_flags=(), cited=""):
            if target == iid:
                return
            tdate = ctx.full_date(target)
            if acting_date and tdate and acting_date < tdate:
                stats["skipped_acting_before_target"] += 1
                return
            pa, pt = ident.parse_eo_id(iid), ident.parse_eo_id(target)
            if pa and pt and pa[0] < pt[0]:
                # Numbers run in date order: an order citing a higher-numbered one is almost always a neighbouring
                # document on the same printed page, or an editorial note.
                stats["skipped_acting_number_below_target"] += 1
                return
            lo, hi = C.sentence_bounds(body, s, e)
            seg = body[lo:hi]
            c = C.classify(seg, s - lo, e - lo, prefer="text")
            flags = list(tflags) + list(extra_flags) + ["relation_word:" + (c["word"] or "none")]
            mech = c["mechanism"]
            if mech == "cross_reference" and not c["actor_named"]:
                # Long land descriptions put the verb far from the citation: '... (No. 1237) of August 15, 1910,
                # reserving ... [metes and bounds] ... is hereby rescinded'. Look ahead to the first 'hereby <verb>'
                # before any other order is cited.
                ahead = body[e:e + 4000]
                nxt = re.search(r"Executive\s+Order|\bE\.\s?O\.|Proclamation", ahead, re.I)
                ahead = ahead[:nxt.start()] if nxt else ahead
                hm = re.search(r"\bhereby\s+(?:\w+\s+){0,2}?(" + C.RELATION_RE.pattern + r")", ahead, re.I)
                if hm:
                    far = C.relation_matches(hm.group(1))
                    if far and far[0][2] != "cross_reference":
                        mech = far[0][2]
                        flags.append("relation_word_far_after_citation:" + far[0][3])
                        hi = max(hi, e + hm.end())
                        seg = body[lo:hi]
            if c["actor_named"]:
                flags.append("cited_as_actor_in_as_amended_by_phrase")
                mech = "cross_reference"
            if c["negated"]:
                flags.append("negation_in_sentence")
            edges.add(acting=iid, target=target, mechanism=mech, qualifier="in part" if c["partial"] else "",
                      evidence_type="shepard_text_" + form, flags=flags, stated_on=iid,
                      note_label=f"cited by {form}" + (f" ({cited})" if cited else "") + "; words: " + ",".join(c["words"]),
                      quote=seg, quote_kind="verbatim_text_sentence(whitespace squeezed)",
                      quote_span=f"{off + lo}-{off + hi}", date_candidate=acting_date,
                      date_basis="citing order's date from the project's indexes" if acting_date else "", **src)

        for s, e, n, suf, stated in C.eo_number_mentions(body):
            target = ctx.census_id(n, suf)
            if not target or target not in ctx.targets:
                continue
            stats["number_mentions"] += 1
            fl = []
            if stated and ctx.full_date(target) and stated.isoformat() != ctx.full_date(target):
                fl.append(f"stated_date_{stated.isoformat()}_differs_from_census_date_{ctx.full_date(target)}")
            emit(target, s, e, "number", fl)
        for s, e, d, phrase in C.eo_date_mentions(body):
            iso = d.isoformat()
            target, why = ctx.resolve_date(iso)
            stats["date_mentions"] += 1
            if not target:
                if acting_date and iso <= acting_date:
                    edges.unresolved_row(source="held_text", citation_form="date", cited=iso, citing_id=iid,
                                         reason=why, source_ref=src["source_id"], quote=phrase)
                continue
            if target not in ctx.targets:
                continue
            emit(target, s, e, "date", ["resolved_by_date_unique_in_census",
                                        "unnumbered_orders_outside_census_may_share_date"], cited=iso)
        for s, e, code, n, phrase in C.reserve_mentions(body):
            key = f"{code}:{n}"
            creator = reserve_map.get(key, {}).get("creator_id")
            stats["reserve_mentions"] += 1
            if not creator:
                continue
            emit(creator, s, e, "reserve", ["resolved_by_reserve_number", "reserve_creator_inferred"], cited=phrase)
        for mech, partial, item_is_actor, kind, num, suf, d, line, pos in notes:
            other = eo_or_other(ctx, kind, num, suf)
            acting, target = (other, iid) if item_is_actor else (iid, other)
            if mech == "cross_reference":
                # 'See Related' has no direction: the later instrument is taken as the citing one.
                da, do = ctx.full_date(iid), ctx.full_date(other)
                if not (da and do) or da == do:
                    continue
                acting, target = (iid, other) if da > do else (other, iid)
            if target not in ctx.universe:
                continue
            stats["wikisource_notes"] += 1
            fl = ["wikisource_editorial_note_not_the_order_text"]
            if d and ctx.full_date(other) and d.isoformat() != ctx.full_date(other):
                fl.append(f"stated_date_{d.isoformat()}_differs_from_census_date_{ctx.full_date(other)}")
            edges.add(acting=acting, target=target, mechanism=mech, qualifier="in part" if partial else "",
                      evidence_type="shepard_wikisource_note", flags=fl, stated_on=iid,
                      note_label="Wikisource Notes section", quote=line, quote_kind="verbatim_note_line",
                      quote_span=f"{pos}-{pos + len(line)}", **src)
    return stats


# --- source 4: Federal Register codification guides already held --------------------------------------

def from_contents(ctx, edges, plo_dates):
    stats = collections.Counter()
    plo_pages = collections.defaultdict(set)
    seen = set()
    for rel in CONTENTS_SOURCES:
        path = os.path.join(ctx.root, rel)
        base = os.path.dirname(path)
        for rec in read_jsonl(path):
            url = rec.get("url") or ""
            m = re.search(r"FR-(\d{4})-(\d{2})-(\d{2})", url)
            tp = rec.get("text_path")
            if not m or not tp:
                continue
            tpath = os.path.normpath(os.path.join(base, tp))
            if not os.path.isfile(tpath):
                continue
            try:
                text = open(tpath, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            digest = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            if not re.search(r"\(\s*(?:Executive|Public\s+land)\s+orders?\s*\)|Public\s+land\s+orders?\s*:", text, re.I):
                continue
            stats["texts_with_codification_guide"] += 1
            issue = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            vol = int(m.group(1)) - 1935
            entries, page_index = C.contents_entries(text)
            for (kind, num), page in page_index.items():
                if kind == "PLO" and num.isdigit():
                    plo_pages[int(num)].add(f"{vol} FR {page} ({issue} codification guide)")
            for en in entries:
                stats["entries"] += 1
                num = re.match(r"(\d+)([A-Z]?)", en["number"])
                target = eo_or_other(ctx, en["section"], num.group(1), num.group(2))
                rel_words = C.relation_matches(en["rel"])
                mech = rel_words[0][2] if rel_words else "cross_reference"
                qual = "in part" if C.PARTIAL_RE.search(en["rel"]) else ""
                for an in en["acting_numbers"]:
                    acting = eo_or_other(ctx, en["acting_kind"], an)
                    apage = page_index.get((en["acting_kind"], str(an))) or en["page"]
                    if en["acting_kind"] == "PLO" and apage:
                        plo_pages[an].add(f"{vol} FR {apage} ({issue} codification guide)")
                    label = f"{en['acting_kind']} {an}" + (f" ({vol} FR {apage})" if apage else "")
                    flags = ["ocr_codification_guide_entry", "fr_issue_" + issue]
                    if not apage:
                        flags.append("acting_page_not_read")
                    dc, db = "", ""
                    if en["acting_kind"] == "PLO" and plo_dates.get(an):
                        dc, db = plo_dates[an], "PLO signature date from the BLM PLO table"
                    elif en["acting_kind"] == "EO" and ctx.full_date(acting):
                        dc, db = ctx.full_date(acting), "acting order's date from the project's indexes"
                    edges.add(acting=acting, target=target, mechanism=mech, qualifier=qual, flags=flags,
                              evidence_type="shepard_fr_contents", stated_on=target,
                              source_id="fr-contents:" + os.path.relpath(tpath, ctx.root).replace(os.sep, "/"),
                              source_url=url, source_sha256=rec.get("sha256") or "",
                              page_or_item=f"Federal Register {issue} (vol. {vol}) codification guide, PDF page {en['pdf_page']}; "
                                           f"entry lists the acting document at {vol} FR {apage or '?'}",
                              note_label="codification guide: " + en["rel"], acting_label=label,
                              quote=en["raw"], quote_kind="ocr_contents_entry", date_candidate=dc, date_basis=db)
    return stats, plo_pages


# --- finishing ---------------------------------------------------------------------------------------

def fill_dates(ctx, edges, plo_dates):
    for row in edges.rows:
        if row["date_candidate"]:
            continue
        a = row["acting_id"]
        if a.startswith("PLO:") and a[4:].isdigit() and plo_dates.get(int(a[4:])):
            row["date_candidate"], row["date_basis"] = plo_dates[int(a[4:])], "PLO signature date from the BLM PLO table"
        elif ctx.full_date(a):
            row["date_candidate"], row["date_basis"] = ctx.full_date(a), "acting order's date from the project's indexes"


def write_csv(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def probe_check(ctx, rows):
    out = {}
    by_target = collections.defaultdict(list)
    for r in rows:
        by_target[r["target_id"]].append(r)
    for iid in PROBE_ORDERS:
        ending = sorted({f"{r['acting_id']} ({r['mechanism']}{', in part' if r['qualifier'] else ''}; {r['evidence_type']})"
                         for r in by_target.get(iid, []) if r["mechanism"] in ENDING})
        out[iid] = {"edges": len(by_target.get(iid, [])), "ending_candidates": ending[:12]}
    return out


def run(root, out_dir, tables=None, text_limit=None, log=print):
    t0 = time.time()
    ctx = Context(root)
    log(f"census {len(ctx.universe)}; targets {len(ctx.targets)} (land {len(ctx.land)}); "
        f"known edges for de-duplication {len(ctx.known)}; {time.time() - t0:.0f}s")
    edges = Edges(ctx)
    n_disp = from_disposition(ctx, edges)
    log(f"1989 table: {n_disp} rows read; edges so far {len(edges.rows)}")
    reserve_map = build_reserve_map(ctx)
    log(f"reserve map: {len(reserve_map)} reserves, {sum(1 for r in reserve_map.values() if r['creator_id'])} resolved")
    plo_rows = plo_rows_and_edges(ctx, edges, tables or [], reserve_map)
    plo_dates = {r["plo_number"]: r["signature_date"] for r in plo_rows if r["signature_date"]}
    log(f"BLM PLO tables: {len(plo_rows)} PLO rows from {len(tables or [])} tables; edges so far {len(edges.rows)}")
    text_stats = from_texts(ctx, edges, reserve_map, limit=text_limit)
    log(f"held texts: {text_stats['texts']} scanned; edges so far {len(edges.rows)}; {time.time() - t0:.0f}s")
    contents_stats, plo_pages = from_contents(ctx, edges, plo_dates)
    log(f"FR codification guides: {contents_stats['texts_with_codification_guide']} texts, {contents_stats['entries']} entries")
    for r in plo_rows:
        r["fr_contents_pages"] = "|".join(sorted(plo_pages.get(r["plo_number"], ())))
    fill_dates(ctx, edges, plo_dates)
    rows = sorted(edges.rows, key=lambda r: (r["target_id"], r["acting_id"], r["evidence_type"], r["edge_id"]))
    write_csv(os.path.join(out_dir, "EDGES.csv"), rows, EDGE_COLUMNS)
    write_csv(os.path.join(out_dir, "PLO_TABLE.csv"), plo_rows, PLO_COLUMNS)
    write_csv(os.path.join(out_dir, "RESERVE_INDEX.csv"), sorted(reserve_map.values(), key=lambda r: (r["kind"], int(r["number"]))),
              RESERVE_COLUMNS)
    write_csv(os.path.join(out_dir, "UNRESOLVED.csv"), edges.unresolved, UNRESOLVED_COLUMNS)
    targets_hit = {r["target_id"] for r in rows if r["target_id"] in ctx.targets}
    summary = {
        "job": JOB, "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "every_row_is_a_lead": True,
        "edges": len(rows),
        "edges_by_evidence_type": dict(collections.Counter(r["evidence_type"] for r in rows)),
        "edges_by_mechanism": dict(collections.Counter(r["mechanism"] for r in rows)),
        "edges_with_census_target": sum(1 for r in rows if r["target_in_universe"] == "yes"),
        "edges_with_census_actor": sum(1 for r in rows if r["acting_id"] in ctx.universe),
        "targets": len(ctx.targets), "land_targets": len(ctx.land),
        "targets_with_any_edge": len(targets_hit),
        "land_targets_with_any_edge": len(targets_hit & ctx.land),
        "land_targets_with_ending_candidate": len({r["target_id"] for r in rows
                                                    if r["target_id"] in ctx.land and r["mechanism"] in ENDING}),
        "skipped_already_in_later_events_or_codification": dict(edges.skipped_known),
        "skipped_other": dict(edges.skipped),
        "plo_table_rows": len(plo_rows),
        "plo_tables": [{k: t.get(k) for k in ("name", "url", "lo", "hi", "sha256", "bytes", "status", "error",
                                              "rows_parsed", "carried_forward", "committed")} for t in (tables or [])],
        "reserves_indexed": len(reserve_map),
        "reserves_resolved": sum(1 for r in reserve_map.values() if r["creator_id"]),
        "held_texts": dict(text_stats), "fr_contents": dict(contents_stats),
        "unresolved_rows_written": len(edges.unresolved),
        "probe_check_30_orders": probe_check(ctx, rows),
        "seconds": round(time.time() - t0, 1),
        "note": "Every row is a lead, not a finding. Nothing here changes a status, count or the codebook. Certified: 0.",
    }
    with open(os.path.join(out_dir, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return summary
