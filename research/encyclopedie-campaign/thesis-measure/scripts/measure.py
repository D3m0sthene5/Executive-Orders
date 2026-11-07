"""Thesis measure: was an order formally revoked after it had already stopped operating?

Usage:  py -I measure.py <repository path> [--rev origin/main] [--out <folder>]

Reads only committed files at one pinned commit (default origin/main) and writes MEASURE.csv and SUMMARY.json
into --out (default: the folder above this script). It changes no status, claim, codebook, census or tracker
file. Every count in REPORT.md comes from SUMMARY.json.

Definitions (TC01: formal validity and operative force are separate axes):

* Formal revocation (F): the earliest later instrument that expressly revokes or supersedes the whole order by
  name. Sources: the order's filed claim (whole_order_end, v2 formal_disposition, or a revocation event listed
  on every clause), Formulario instance lemmas built from jobs/later-events (relations revokes, supersedes,
  supersession_or_revocation, with no qualifier and no partial evidence for the same pair), and the 1989 OFR
  disposition table (categories revoked and superseded).
* Earlier end (E): the earliest evidenced end of operative force of the whole order before F. Routes: own terms,
  exhaustion of a one-time command, implied supersession or earlier revocation of the remaining clauses,
  termination of the order or its body by a later instrument that names the order, and a statute or plan that
  names the order. When the order has a filed claim with a whole-order end, only the claim decides E. Without
  one, E comes from leads: an own-terms clause found by a regular-expression scan of the order's held text,
  Formulario lemmas, and the 1989 table's "temporary" and "executed and obsolete" entries.
* A claim-cited revocation whose held text does not contain the order's number, and which names a parent order
  "as amended", is not a revocation of this order by name (TC09); it is set aside and noted.
* The text scan has a second pass with spaces removed, for OCR that splits words; it runs only on clauses where
  the first pass found nothing.
* Statutory end without naming the order is the provisional route of A-20261106-1, kept apart (P).
* Not ends: a report deadline (D-20261021-report-deadline), a strike-and-insert amendment
  (D-20261021-strike-and-insert), an end bounded only by the cleanup instrument (R3, v2 not_later_than), and a
  judicial holding (TC12). These make an order "blocked" when they are its only candidate.

Evidence levels: held_verified (official text whose committed bytes match the recorded SHA-256 and, for a
Formulario lemma, the kernel found the quote), held_unverified (bytes or a hash recorded but not matched here,
or a secondary transcription), lead_only (a disposition-table or catalog note, or text not retained), none.
"""

import argparse
import collections
import csv
import datetime
import gzip
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gitread import Git  # noqa: E402

CUTOFF = "2026-10-14"
LEVEL_RANK = {"held_verified": 3, "held_unverified": 2, "lead_only": 1, "none": 0, "": 0}
OFFICIAL_GRADES = {"order_text_fr_originals", "order_text_govinfo_pdf", "order_text_opus_official_copy"}
MIRROR_GRADES = {"order_text_app_transcriptions", "order_text_opus_mirror"}
F_RELATIONS = {"revokes", "supersedes", "supersession_or_revocation"}
E_RELATIONS = {"terminates", "abolishes_agency", "expiration", "ceased_to_function", "voiding", "repeal",
               "repeals_authority"}
EXT_MECHANISMS = {"amendment", "extension", "continuation", "modification", "supplementation", "reinstatement",
                  "suspension"}
SECONDARY_TEXT = re.compile(r"app-executive-orders|app-transcriptions|wikisource|presidency\.ucsb", re.I)

CATEGORIES = ["formally_revoked_after_evidenced_earlier_end", "formally_revoked_no_earlier_end_evidenced",
              "earlier_end_but_never_formally_revoked", "neither", "blocked"]


def eo_ids(text):
    """Canonical EO ids named in free text: 'EO:12553', 'EO 12553', 'Executive Order No. 12553'."""
    out = []
    for m in re.finditer(r"\b(?:EO|E\.\s?O\.|Executive\s+Orders?)(?:\s*No\.?|\s*Nos\.?)?\s*:?\s*(\d{1,5}(?:-?[A-Z])?)\b",
                         text or ""):
        out.append("EO:" + m.group(1).replace("-", ""))
    return out


def is_date(s):
    try:
        return bool(s) and datetime.date.fromisoformat(s).isoformat() == s
    except ValueError:
        return False


def days(a, b):
    return (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days


def classify_mechanism(text):
    t = (text or "").lower()
    # Negated wording names a mechanism only to deny it ("not a revocation or supersession of EO 9278").
    t = re.sub(r"\b(not|no|neither|nor)\s+(a\s+|an\s+|the\s+)?(express\s+)?(revocation|supersession|revoked|superseded"
               r"|amendment|second end|end)\b[^;.)]*", " ", t)
    if re.search(r"strik|substitut|deletes? (this|the|item)|deletion|amendment by|^amend$|inserts? a different"
                 r"|to read as follows|amended to read", t):
        return "amendment_treated_as_end"
    if "implied" in t:
        return "implied_supersession"
    if re.search(r"revo|supersed|supersess|rescind|rescission", t):
        return "formal"
    if re.search(r"statut|joint res|s\.\s?j\.\s?res|act of congress|legislat|public law|pub\.\s?l", t):
        return "statutory"
    if re.search(r"own[_ -]terms|expir|sunset|fixed[_ ]term|fixed[_ ]period|until|single[_ ]day|fiscal|date[_ ]cap"
                 r"|cessation_date|of term|fixed[_ ]date|fixed[_ ]end|period", t):
        return "own_terms"
    if re.search(r"exhaust|perform|one[_ -]time|self[_ ]executing|dispositive|completed|successor appointed", t):
        return "exhaustion"
    if re.search(r"discontinu|terminat|lapse|abolish|ceased", t):
        return "termination_by_later_instrument_or_body_end"
    if "report" in t:
        return "report_deadline"
    return "other"


class Measure:
    def __init__(self, git):
        self.g = git
        self.summary = collections.OrderedDict()
        self.parent_only = collections.defaultdict(list)
        self.inputs = collections.OrderedDict()

    # ------------------------------------------------------------------ inputs
    def csv_rows(self, path):
        csv.field_size_limit(10 ** 9)
        data = self.g.text(path)
        self.inputs[path] = self.g.sha256(path)
        return list(csv.DictReader(io.StringIO(data)))

    def load(self):
        g = self.g
        self.tracker = {r["instrument_id"]: r for r in self.csv_rows("jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")}
        self.universe = list(self.tracker)
        self.U = set(self.universe)
        # Claims: tracker rule, sorted files, later files and lines win.
        self.claims, self.claim_file = {}, {}
        for n in sorted(x for x in g.ls("research/readiness/claims") if x.endswith(".jsonl")):
            self.inputs[n] = g.sha256(n)
            for line in g.text(n).splitlines():
                if line.strip():
                    c = json.loads(line)
                    i = c.get("instrument_id")
                    if isinstance(i, str):
                        self.claims[i] = c
                        self.claim_file[i] = n
        # Catalog: signing dates of acting orders.
        self.catalog = {r["id"]: r for r in self.csv_rows("jobs/later-events/output/CATALOG_INDEX.csv")}
        self.census_year = {r["id"]: r["date_effective"][:4] for r in
                            self.csv_rows("research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv")}
        # Later-events edges: stated effective dates, qualifiers, partial-evidence flags, extensions.
        self.edges = {}
        self.ext_edges = collections.defaultdict(list)
        self.partial_pairs = set()
        for r in self.csv_rows("jobs/later-events/output/EDGES.csv"):
            self.edges[r["edge_id"]] = r
            t, a = r["target_id"], r["acting_id"]
            if r["mechanism"] in EXT_MECHANISMS and t:
                self.ext_edges[t].append(r)
            if t and a and r["mechanism"] in ("revocation", "supersession", "supersession_or_revocation",
                                              "rescission") and (r["qualifier"] or "partial" in r["date_flags"]):
                self.partial_pairs.add((a, t))
        # Formulario lemmas.
        self.lemmas = collections.defaultdict(list)
        self.class_lemmas = []
        for n in g.ls("jobs/peano-formulario/output/lemmas"):
            if not n.endswith(".jsonl.gz"):
                continue
            self.inputs[n] = g.sha256(n)
            for line in gzip.decompress(g.read(n)).decode("utf-8").splitlines():
                o = json.loads(line)
                if o["kind"] == "class":
                    self.class_lemmas.append(o)
                    continue
                s = o["statement"]
                for t in s.get("objects") or []:
                    if t in self.U:
                        self.lemmas[t].append(o)
                        if s["relation"] in F_RELATIONS and s.get("qualifier"):
                            self.partial_pairs.add((s["subject"], t))
        self.families = json.loads(g.text("jobs/peano-formulario/output/FAMILIES.json"))
        self.inputs["jobs/peano-formulario/output/FAMILIES.json"] = g.sha256("jobs/peano-formulario/output/FAMILIES.json")
        self.d1989 = collections.defaultdict(list)
        for r in self.csv_rows("jobs/ofr-codification-1989/output/DISPOSITION_1989.csv"):
            if r["census_id"] in self.U:
                self.d1989[r["census_id"]].append(r)
        # Held originals: every job's SOURCES.jsonl links the SHA-256 of an original to its committed text
        # (the same records jobs/claim-checker/sources.py reads).
        self.held_by_sha = {}
        for job in g.dirs("jobs"):
            n = f"jobs/{job}/output/SOURCES.jsonl"
            if g.sha256(n) is None:
                continue
            secondary = bool(re.search(r"app-|wikisource", job))
            self.inputs[n] = g.sha256(n)
            for line in g.text(n).splitlines():
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                sha, tp = rec.get("sha256"), rec.get("text_path")
                if not (isinstance(sha, str) and isinstance(tp, str)):
                    continue
                self.held_by_sha.setdefault(sha, []).append(dict(
                    job=job, text_path=f"jobs/{job}/output/{tp}", text_sha256=rec.get("text_sha256"),
                    secondary=secondary, ids=[x for x in rec.get("instrument_ids") or [] if isinstance(x, str)]))
        # Clause drafts: one held text per order with its clause spans.
        self.drafts = collections.defaultdict(list)
        for r in self.csv_rows("jobs/clause-drafts/output/CLAUSES.csv"):
            if r["instrument_id"] in self.U:
                self.drafts[r["instrument_id"]].append(r)

    # ------------------------------------------------------------ evidence
    def text_level(self, text_path, text_sha, url=""):
        """held_verified when the committed text bytes match the recorded hash and the text is official."""
        if not text_path or not text_sha:
            return None
        h = self.g.sha256(text_path)
        if h is None:
            return None
        if h != text_sha:
            return "held_unverified"
        return "held_unverified" if SECONDARY_TEXT.search(text_path + " " + (url or "")) else "held_verified"

    def claim_source_level(self, src, actor=""):
        if not isinstance(src, dict):
            return "lead_only", ""
        lv = self.text_level(src.get("text_path"), src.get("text_sha256"), src.get("url", ""))
        if lv:
            return lv, src.get("text_path")
        lp = src.get("local_path")
        if lp and src.get("sha256"):
            h = self.g.sha256(lp)
            if h is not None:
                return ("held_verified" if h == src["sha256"] else "held_unverified"), lp
        recs = self.held_by_sha.get(src.get("sha256") or "") or []
        actor_ids = set(eo_ids(actor)) | {actor}
        # Prefer the held text recorded for the acting instrument itself, then a full-issue Federal Register text.
        recs = sorted(recs, key=lambda x: (not (set(x["ids"]) & actor_ids), x["job"] != "fr-originals", x["job"]))
        for held in recs[:6]:
            h = self.g.sha256(held["text_path"])
            if h is not None and (not held["text_sha256"] or h == held["text_sha256"]):
                secondary = held["secondary"] or SECONDARY_TEXT.search(src.get("url", "") or "")
                return ("held_unverified" if secondary else "held_verified"), held["text_path"]
        if src.get("sha256") or src.get("local_file_sha256"):
            return "held_unverified", src.get("url") or src.get("archival_id") or ""
        return "lead_only", src.get("url") or ""

    def lemma_level(self, o):
        grade, status = o.get("grade", ""), o["status"]
        if grade.startswith("ofr_note"):
            return "lead_only"
        if status == "proved":
            if grade in OFFICIAL_GRADES:
                p = o["proof"]
                lv = self.text_level(p.get("text_path"), p["source"].get("text_sha256"), p["source"].get("url", ""))
                flags = o.get("origin", {}).get("date_flags", "")
                # The sentence was found on the acting order's pages, but not under its own heading (or the
                # target's date disagrees): the attribution to that instrument is not confirmed.
                if "heading_not_found" in flags or "differs_from_catalog" in flags:
                    return "held_unverified"
                return lv or "held_unverified"
            if grade in MIRROR_GRADES:
                return "held_unverified"
            return "held_verified" if o.get("origin", {}).get("from", "").startswith("axioms") else "held_unverified"
        if o.get("sorry_reason", "").startswith("quote_not_found"):
            return "held_unverified"
        return "lead_only"

    def lemma_date(self, o):
        e = self.edges.get(o.get("origin", {}).get("edge_id", ""), {})
        if is_date(e.get("stated_effective_date", "")):
            return e["stated_effective_date"], "stated effective date in the quoted wording"
        d = o["statement"].get("date", "")
        return (d, o.get("origin", {}).get("date_basis", "")) if is_date(d) else ("", "")

    def order_date(self, i):
        c = self.catalog.get(i)
        if c and is_date(c.get("signing_date", "")):
            return c["signing_date"]
        y = self.census_year.get(i, "")
        return f"{y}-01-01" if re.fullmatch(r"\d{4}", y or "") else ""

    # --------------------------------------------------- formal revocation
    def formal_candidates(self, i):
        cands = []
        c = self.claims.get(i)
        if c:
            w = c.get("whole_order_end") if isinstance(c.get("whole_order_end"), dict) else None
            if w:
                mech = " ".join(str(w.get(k, "")) for k in ("mechanism", "mechanism_note", "mechanism_detail"))
                if classify_mechanism(mech) == "formal":
                    actor = (eo_ids(str(w.get("actor", ""))) or [str(w.get("actor", ""))])[0]
                    lv, path = self.claim_source_level(w.get("source"), actor)
                    if is_date(w.get("date", "")):
                        cands.append(dict(instrument=actor, date=w["date"], level=lv, basis="filed_claim",
                                          source=path, ref=self.claim_file[i], kind="whole_order_end", mech=mech))
            fd = c.get("formal_disposition")
            if isinstance(fd, dict) and is_date(fd.get("date", "")):
                ids = eo_ids(str(fd.get("instrument", "")))
                mech = str((w or {}).get("mechanism", ""))
                if ids and classify_mechanism(mech) == "formal":
                    lv, path = self.claim_source_level(fd.get("source"), ids[0])
                    cands.append(dict(instrument=ids[0], date=fd["date"], level=lv, basis="filed_claim",
                                      source=path, ref=self.claim_file[i], kind="formal_disposition_v2"))
            clauses = [cl for cl in c.get("operative_clauses") or [] if isinstance(cl, dict)]
            per_actor = collections.defaultdict(list)
            for cl in clauses:
                seen = set()
                for e in cl.get("later_events") or []:
                    if not isinstance(e, dict):
                        continue
                    mech = " ".join(str(e.get(k, "")) for k in ("mechanism", "mechanism_detail"))
                    if classify_mechanism(mech) != "formal" or not is_date(str(e.get("effective_date", ""))):
                        continue
                    ids = eo_ids(str(e.get("actor", "")))
                    if ids and ids[0] not in seen:
                        seen.add(ids[0])
                        per_actor[ids[0]].append(e)
            for a, evs in per_actor.items():
                if clauses and len(evs) == len(clauses):  # named against every clause: a whole-order revocation
                    lv, path = self.claim_source_level(evs[0].get("source"), a)
                    cands.append(dict(instrument=a, date=min(e["effective_date"] for e in evs), level=lv,
                                      basis="filed_claim", source=path, ref=self.claim_file[i],
                                      kind="later_event_on_every_clause",
                                      mech=" ".join(str(e.get("mechanism", "")) for e in evs)))
        for o in self.lemmas.get(i, []):
            s = o["statement"]
            if s["relation"] not in F_RELATIONS or s.get("qualifier") or (s["subject"], i) in self.partial_pairs:
                continue
            d, basis = self.lemma_date(o)
            cands.append(dict(instrument=s["subject"], date=d, level=self.lemma_level(o), basis="formulario_lemma",
                              source=o["proof"].get("text_path") or o["proof"].get("source", {}).get("url", ""),
                              ref=o["lemma_id"], kind=f"{s['relation']}:{o.get('grade', '')}:{o['status']}",
                              date_basis=basis))
        for r in self.d1989.get(i, []):
            if r["category"] in ("revoked", "superseded"):
                for a in [x for x in r["acting_documents"].split("|") if x.strip()]:
                    a = a.strip()
                    d = self.catalog.get(a, {}).get("signing_date", "")
                    cands.append(dict(instrument=a, date=d if is_date(d) else "", level="lead_only",
                                      basis="disposition_table_1989",
                                      source="jobs/ofr-codification-1989/output/DISPOSITION_1989.csv",
                                      ref=f"seq {r['seq']}: {r['disposition']}", kind=r["category"]))
        out = []
        for x in cands:
            if x["date"] and x["date"] > CUTOFF:
                continue
            if x["basis"] == "filed_claim":
                named = self.names_target(i, x["source"])
                if named is False:
                    mech = x.get("mech", "")
                    others = [e for e in eo_ids(mech) if e not in (i, x["instrument"])]
                    if "as amended" in mech.lower() or others:
                        # TC09: revoking the parent order "as amended" is no revocation of this order by name.
                        self.parent_only[i].append(x)
                        continue
                    x = dict(x, level="held_unverified")
            out.append(x)
        return out

    def names_target(self, i, path):
        """True/False when the held text does/does not contain the order's number; None when no text is held."""
        if not path or not str(path).endswith(".txt"):
            return None
        t = self.g.text(path)
        if t is None:
            return None
        num = i.split(":", 1)[1]
        return bool(re.search(r"(?<![\d])" + re.escape(num) + r"(?![\d])", t))

    def choose_formal(self, cands):
        groups = collections.defaultdict(list)
        for x in cands:
            groups[x["instrument"]].append(x)
        best = []
        for a, xs in groups.items():
            lv = max(xs, key=lambda x: LEVEL_RANK[x["level"]])
            claim = [x for x in xs if x["basis"] == "filed_claim" and x["date"]]
            dated = claim or sorted([x for x in xs if x["date"]], key=lambda x: (-LEVEL_RANK[x["level"]], x["date"]))
            d = dated[0]["date"] if dated else ""
            rep = dict(lv)
            rep["date"] = d
            rep["sources_n"] = len(xs)
            rep["bases"] = "|".join(sorted({x["basis"] for x in xs}))
            if dated and dated[0] is not lv:
                rep["date_from"] = dated[0]["basis"]
            best.append(rep)
        dated = sorted([b for b in best if b["date"]], key=lambda b: (b["date"], -LEVEL_RANK[b["level"]]))
        if dated:
            return dated[0], best
        return (best[0] if best else None), best

    # ------------------------------------------------------ earlier ends
    def claim_end(self, i):
        """(E candidates, provisional candidates, blocked candidates, note) from the filed claim."""
        c = self.claims.get(i)
        E, P, B = [], [], []
        if not c:
            return None
        w = c.get("whole_order_end") if isinstance(c.get("whole_order_end"), dict) else None
        if not w:
            return dict(E=E, P=P, B=B, status=c.get("whole_order_status"), route="no_whole_order_end")
        mech = " ".join(str(w.get(k, "")) for k in ("mechanism", "mechanism_note", "mechanism_detail"))
        route = classify_mechanism(mech)
        lv, path = self.claim_source_level(w.get("source"), str(w.get("actor", "")))
        kind = w.get("date_kind", "exact")
        date = w.get("date") if kind in ("exact", "not_later_than") else w.get("latest")
        rec = dict(route=route, date=date or "", level=lv, basis="filed_claim", source=path,
                   ref=self.claim_file[i], actor=str(w.get("actor", "")), date_kind=kind)
        if kind == "not_later_than":
            B.append(dict(rec, blocker="R3_FIRST_END_UNRESOLVED_CLEANUP_BOUND"))
        elif route == "statutory":
            # A-20261106-1 (provisional): counted only when the statute's bytes are held and verified and the
            # order's own clause text names the statute or authority it rests on.
            quoted = any(re.search(r"Recovery Act|National Industrial|Title I\b|Act of|Stat\.|Public (Law|Resolution)",
                                   str(cl.get("original_operative_text", "")), re.I)
                         for cl in c.get("operative_clauses") or [] if isinstance(cl, dict))
            P.append(dict(rec, route="statutory_end_unnamed_order",
                          qualifies=lv == "held_verified" and quoted))
        elif route == "amendment_treated_as_end":
            B.append(dict(rec, blocker="STRIKE_AND_INSERT_RULING_RECHECK"))
        elif route == "report_deadline":
            B.append(dict(rec, blocker="REPORT_DEADLINE_IS_NOT_AN_END"))
        elif route == "other":
            B.append(dict(rec, blocker="CLAIM_END_ROUTE_UNCLASSIFIED"))
        elif route == "formal":
            # The claim's whole-order end is itself an express revocation or supersession. It is an earlier end
            # only if it is not the formal revocation chosen for the order (a revocation of the remaining
            # clauses before a later whole-order revocation); row() decides.
            return dict(E=E, P=P, B=B, R=rec, status=c.get("whole_order_status"), route=route, claim=c)
        else:
            E.append(rec)
        return dict(E=E, P=P, B=B, R=None, status=c.get("whole_order_status"), route=route, claim=c)

    DATE_RE = (r"(January|February|March|April|May|June|July|August|September|October|November|December|Jan\.|Feb\.|"
               r"Mar\.|Apr\.|Aug\.|Sept?\.|Oct\.|Nov\.|Dec\.)\s*(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(\d{4})")
    MONTHS = {m: n for n, ms in enumerate([("january", "jan."), ("february", "feb."), ("march", "mar."),
                                           ("april", "apr."), ("may",), ("june",), ("july",), ("august", "aug."),
                                           ("september", "sept.", "sep."), ("october", "oct."),
                                           ("november", "nov."), ("december", "dec.")], 1) for m in ms}
    # Each pattern ends just before the date. A stated *start* ("shall be effective on") never matches: the
    # force words must be followed by "until", "through" or "to and including".
    NO_TERMS = r"(?:(?!\bterms?\b|\bmembers?\b|\bappointed\b|\beffective\s+(on|as\s+of)\b)[^.;])"
    SCAN = [
        ("own_terms_order_expiry",
         r"\b(this|the\s+present|said|the\s+foregoing)\s+(executive\s+)?(order|proclamation|regulations?|exemption"
         r"|suspension|waiver|extension|authorization|designation)\b" + NO_TERMS + r"{0,160}?\b(shall|will|is\s+to)\s+"
         r"(?:(terminate|expire|cease\s+to\s+be\s+(in\s+)?(effect|effective|in\s+force)|cease|end)\b" + NO_TERMS +
         r"{0,60}?\b(on|at\s+the\s+close\s+of|at\s+the\s+end\s+of|not\s+later\s+than|after|upon)"
         r"|(remain|continue|be)\s+in\s+(full\s+)?(force|effect)" + NO_TERMS + r"{0,60}?\b(until|through|to\s+and\s+including)"
         r"|be\s+effective" + NO_TERMS + r"{0,60}?\b(until|through|to\s+and\s+including))\s+(the\s+close\s+of\s+)?"),
        ("own_terms_until_date",
         r"\b(exempt(ed|ion)?|excepted|suspend(ed)?|extended|permitted|authorized|continued?|remain)\b" + NO_TERMS +
         r"{0,160}?\b(until|to\s+and\s+including)\s+(and\s+including\s+)?(the\s+close\s+of\s+)?"),
        ("own_terms_body_sunset",
         r"\b(board|commission|committee|council|panel|office|administration|agency|task\s+force|authority|corporation"
         r"|conference|delegation)\b" + NO_TERMS + r"{0,80}?\b(shall|will)\s+(terminate|expire|cease\s+to\s+exist"
         r"|cease\s+to\s+function|cease|end|be\s+abolished)\b" + NO_TERMS + r"{0,60}?\b(on|by|not\s+later\s+than"
         r"|at\s+the\s+close\s+of|at\s+the\s+end\s+of|upon)\s+(the\s+close\s+of\s+)?"),
    ]
    DATE_FLAT = (r"(?P<mon>january|february|march|april|may|june|july|august|september|october|november|december"
                 r"|jan\.|feb\.|mar\.|apr\.|aug\.|sept\.|sep\.|oct\.|nov\.|dec\.)(?P<d>\d{1,2})(st|nd|rd|th)?,?(?P<y>\d{4})")
    NO_TERMS_FLAT = r"(?:(?!terms|members|appointed|effectiveon|effectiveasof)[^.;])"
    SCAN_FLAT = [
        ("own_terms_order_expiry",
         r"this(executive)?order" + NO_TERMS_FLAT + r"{0,120}?(shall|will)(terminate|expire|ceasetobeeffective"
         r"|ceasetobeineffect)(on|atthecloseof|attheendof|notlaterthan)(thecloseof)?"),
        ("own_terms_until_date",
         r"(exempt|excepted|suspended|extended|continue|remain)" + NO_TERMS_FLAT + r"{0,140}?(until|toandincluding)"
         r"(andincluding)?(thecloseof)?"),
        ("own_terms_body_sunset",
         r"(board|commission|committee|council|panel|taskforce|administration|agency|conference)" + NO_TERMS_FLAT +
         r"{0,70}?(shall|will)(terminate|expire|ceasetoexist|ceasetofunction)(on|by|notlaterthan|atthecloseof"
         r"|attheendof)(thecloseof)?"),
    ]
    SCAN_KINDS = {"operative", "operative_in_preamble", "general_provisions", "effective_date"}

    def scan_text_ends(self, i):
        rows = self.drafts.get(i)
        if not rows:
            return []
        text = self.g.text("jobs/clause-drafts/output/" + rows[0]["text_path"])
        if text is None:
            return []
        lv = "held_unverified" if rows[0]["source_grade"].startswith("mirror") or rows[0]["source_grade"] == "other_copy" \
            else "held_verified"
        out = []
        od = self.order_date(i)
        for r in rows:
            if r["clause_kind"] not in self.SCAN_KINDS:
                continue
            span = re.sub(r"\s+", " ", text[int(r["start"]):int(r["end"])])
            n0 = len(out)
            for route, pat in self.SCAN:
                for m in re.finditer(pat + self.DATE_RE, span, re.I):
                    mon = self.MONTHS.get(m.group(m.lastindex - 2).lower())
                    try:
                        d = datetime.date(int(m.group(m.lastindex)), mon, int(m.group(m.lastindex - 1))).isoformat()
                    except (TypeError, ValueError):
                        continue
                    if d > CUTOFF or (od and d < od):
                        continue
                    out.append(dict(route=route, date=d, level=lv, basis="machine_text_scan",
                                    source="jobs/clause-drafts/output/" + rows[0]["text_path"], ref=r["scope_id"],
                                    quote=span[max(0, m.start()):m.end()][:300], source_grade=rows[0]["source_grade"]))
            if len(out) > n0:
                continue
            # OCR of old Federal Register scans splits words ("term inate on D ecem ber 31,1981"). Second pass on
            # the clause with every space removed; it runs only where the spaced pass found nothing in this clause.
            flat = re.sub(r"\s+", "", span).lower()
            for route, pat in self.SCAN_FLAT:
                for m in re.finditer(pat + self.DATE_FLAT, flat):
                    mon = self.MONTHS.get(m.group("mon"))
                    try:
                        d = datetime.date(int(m.group("y")), mon, int(m.group("d"))).isoformat()
                    except (TypeError, ValueError):
                        continue
                    if d > CUTOFF or (od and d < od):
                        continue
                    out.append(dict(route=route, date=d, level=lv, basis="machine_text_scan",
                                    source="jobs/clause-drafts/output/" + rows[0]["text_path"], ref=r["scope_id"],
                                    quote="[spaces removed] " + flat[max(0, m.start()):m.end()][:280],
                                    source_grade=rows[0]["source_grade"], ocr_tolerant=True))
        return out

    def lead_ends(self, i):
        E, P, B = [], [], []
        od = self.order_date(i)
        for x in self.scan_text_ends(i):
            ext = [e for e in self.ext_edges.get(i, []) if e["date_candidate"] and e["date_candidate"] <= x["date"]]
            if ext:
                B.append(dict(x, blocker="AMENDMENT_OR_EXTENSION_BEFORE_STATED_END_UNCHECKED",
                              ext=ext[0]["acting_id"] + " " + ext[0]["date_candidate"]))
            else:
                E.append(x)
        for o in self.lemmas.get(i, []):
            s = o["statement"]
            rel = s["relation"]
            d, basis = self.lemma_date(o)
            if not d or (od and d < od):
                continue
            rec = dict(date=d, level=self.lemma_level(o), basis="formulario_lemma",
                       source=o["proof"].get("text_path") or o["proof"].get("source", {}).get("url", ""),
                       ref=o["lemma_id"], actor=s["subject"], quote=o["proof"].get("quote", "")[:300])
            if rel == "holds_invalid":
                B.append(dict(rec, route="judicial_holding", blocker="JUDICIAL_SCOPE_TC12"))
            elif rel in E_RELATIONS and not s.get("qualifier"):
                subj = s["subject"]
                if subj.startswith(("EO:", "PROC:", "PLO:", "MEMORANDUM:")):
                    E.append(dict(rec, route="termination_by_named_instrument"))
                elif subj == i or rel in ("expiration", "ceased_to_function"):
                    E.append(dict(rec, route="own_terms_editorial_note"))
                else:
                    E.append(dict(rec, route="statute_or_plan_naming_order"))
        for r in self.d1989.get(i, []):
            cat = r["category"]
            rec = dict(date="1989-01-20", date_kind="not_later_than", level="lead_only", basis="disposition_table_1989",
                       source="jobs/ofr-codification-1989/output/DISPOSITION_1989.csv",
                       ref=f"seq {r['seq']}: {r['disposition']}", actor=r["acting_documents"])
            if cat in ("temporary", "executed_obsolete"):
                E.append(dict(rec, route="disposition_table_temporary_or_executed"))
            elif cat in ("free_text_ended", "terminated", "eliminated", "nullified"):
                if re.search(r"\bact\b|stat\.|public law|congress", r["disposition"], re.I) and not eo_ids(r["acting_documents"]):
                    P.append(dict(rec, route="statutory_end_unnamed_order"))
                else:
                    E.append(dict(rec, route="termination_by_named_instrument"))
        return E, P, B

    def class_candidates(self, i):
        """Provisional A-20261106-1 candidates from Formulario class lemmas (war and emergency family only)."""
        fam = set(self.families.get(i, []))
        if "PD-WAR-EMERGENCY" not in fam:
            return []
        od = self.order_date(i)
        out = []
        for o in self.class_lemmas:
            s = o["statement"]
            if o["status"] != "proved" or s["relation"] not in ("terminates", "repeals_authority"):
                continue
            if "PD-WAR-EMERGENCY" not in (s.get("families") or []) or not is_date(s.get("date", "")):
                continue
            if od and s["date"] <= od:
                continue
            out.append(dict(route="statutory_end_unnamed_order", date=s["date"], level="held_verified",
                            basis="formulario_class_lemma", source=o["proof"].get("text_path", ""),
                            ref=o["lemma_id"], actor=s["subject"][:80]))
        return sorted(out, key=lambda x: x["date"])[:1]

    # ---------------------------------------------------------------- rows
    @staticmethod
    def pick(cands, before):
        ok = [x for x in cands if x.get("date") and (not before or x["date"] < before)]
        if not ok:
            return None
        return sorted(ok, key=lambda x: (-LEVEL_RANK[x["level"]], x["date"]))[0]

    def row(self, i):
        tr = self.tracker[i]
        fc = self.formal_candidates(i)
        F, groups = self.choose_formal(fc)
        ce = self.claim_end(i)
        revoked_while_operative = False
        if ce is not None and ce.get("R"):
            R = ce["R"]
            if F and F["instrument"] not in (eo_ids(R["actor"]) or [R["actor"]]) and F["date"] and R["date"] < F["date"]:
                ce["E"].append(dict(R, route="earlier_revocation_or_supersession_of_clauses"))
            else:
                revoked_while_operative = True
        if ce is not None and (ce["E"] or ce["P"] or ce["B"] or ce.get("R")):
            E_all, P_all, B_all = ce["E"], ce["P"], ce["B"]
            basis_scope = "filed_claim"
        else:
            E_all, P_all, B_all = self.lead_ends(i)
            basis_scope = "leads"
        if not P_all and basis_scope == "leads":
            P_all = self.class_candidates(i)
        fdate = F["date"] if F else ""
        E = self.pick(E_all, fdate)
        P = self.pick([p for p in P_all], fdate)
        notes, blockers = [], []
        late = [x for x in E_all if fdate and x.get("date") and x["date"] >= fdate]
        if F and not E and late:
            notes.append(f"candidate end {late[0]['date']} ({late[0]['route']}) is not before the formal revocation")
        if revoked_while_operative and F and not E:
            notes.append("filed claim: the formal revocation is the whole-order end (revoked while operative)")
        if ce is not None and ce.get("route") == "no_whole_order_end":
            notes.append(f"filed claim without whole-order end; claim status {ce.get('status')}")
        blocked_by = [b for b in B_all if b.get("date") and (not fdate or b["date"] <= fdate)] or \
                     [b for b in B_all if not b.get("date")]
        if F and not fdate:
            blockers.append("FORMAL_REVOCATION_UNDATED")
        # category
        if F and fdate and E:
            cat = "formally_revoked_after_evidenced_earlier_end"
        elif not F and E:
            cat = "earlier_end_but_never_formally_revoked"
        elif blocked_by or P or (F and not fdate and E_all):
            cat = "blocked"
            blockers += sorted({b["blocker"] for b in blocked_by})
            if P:
                blockers.append("OWNER_RULING_A-20261106-1_STATUTE_WITHOUT_NAMING" if P.get("qualifies")
                                else "A-20261106-1_DEPENDENCY_NOT_QUOTED_FROM_BOTH_TEXTS")
        elif F:
            cat = "formally_revoked_no_earlier_end_evidenced"
        else:
            cat = "neither"
        if cat == "blocked" and not blockers:
            blockers.append("FORMAL_REVOCATION_UNDATED")
        # Provisional reading: A-20261106-1 adopted for qualifying statutory ends.
        prov = cat
        if cat in ("blocked", "formally_revoked_no_earlier_end_evidenced", "neither") and P and P.get("qualifies") \
                and not blocked_by:
            prov = "formally_revoked_after_evidenced_earlier_end" if F and fdate else "earlier_end_but_never_formally_revoked"
        eend = E or (blocked_by[0] if cat == "blocked" and blocked_by else None) or (P if cat == "blocked" else None)
        gap = days(E["date"], fdate) if (cat == "formally_revoked_after_evidenced_earlier_end") else ""
        if E and E.get("date_kind") == "not_later_than" and gap != "":
            notes.append("earlier end is a not-later-than bound; the gap is a lower bound")
        if len([g for g in groups if g.get("date")]) > 1 and F:
            later = sorted({g["instrument"] for g in groups if g.get("date") and g["date"] > fdate})
            if later:
                notes.append("also expressly revoked or superseded later by " + ", ".join(later[:4]))
        if self.parent_only.get(i):
            p0 = self.parent_only[i][0]
            same = F and p0["instrument"] == F["instrument"]
            notes.append(f"the held text of {p0['instrument']} ({p0['date']}) revokes only a parent order 'as amended' (TC09), "
                         f"not this order by name" + ("; the revocation shown rests on disposition notes only" if same else ""))
        if E and E["basis"] == "machine_text_scan":
            notes.append("earlier end is a regular-expression lead in held text, not a reviewed reading")
        if E and E["basis"] == "disposition_table_1989":
            notes.append("earlier end is the 1989 editors' label, undated")
        if E and E["route"] == "own_terms_body_sunset":
            notes.append("body sunset: TC10 asks whether any other authority of the order survived")
        if E and E["route"] == "termination_by_named_instrument" and E["basis"] != "filed_claim":
            notes.append("TC10: the named termination may end the body only, not every authority")
        has_info = bool(fc or E_all or P_all or B_all or ce is not None or tr["provisional_status"])
        return dict(
            eo=i,
            provisional_status=tr["provisional_status"],
            claim=("v2" if ce and ce.get("claim", {}).get("schema", "").endswith("v2") else "v1") if i in self.claims else "",
            ready_for_human_review=tr["ready_for_human_review"],
            formal_revocation_instrument=F["instrument"] if F else "",
            formal_revocation_date=fdate,
            formal_revocation_evidence=F["level"] if F else "none",
            formal_revocation_basis=F["bases"] if F else "",
            formal_revocation_source=(F["source"] or F["ref"]) if F else "",
            formal_revocation_ref=F["ref"] if F else "",
            earliest_earlier_end_route=eend["route"] if eend else "",
            earliest_earlier_end_date=eend.get("date", "") if eend else "",
            earliest_earlier_end_evidence=eend["level"] if eend else "none",
            earliest_earlier_end_basis=eend["basis"] if eend else "",
            earliest_earlier_end_source=(eend.get("source") or "") if eend else "",
            earliest_earlier_end_ref=(eend.get("ref") or "") if eend else "",
            gap_days=gap,
            category=cat,
            blocker="|".join(dict.fromkeys(blockers)),
            category_if_A_20261106_1_adopted=prov,
            provisional_statutory_end=f"{P['date']} {P['actor'][:60]} ({P['basis']})" if P else "",
            end_scope=basis_scope,
            confidence_note="; ".join(notes),
            _has_info=has_info,
            _E=E, _F=F, _P=P,
        )

    def run(self):
        self.load()
        self.rows = [self.row(i) for i in self.universe]
        return self.rows


def lvl_pair(r):
    a, b = r["formal_revocation_evidence"], r["earliest_earlier_end_evidence"]
    return min(a, b, key=lambda x: LEVEL_RANK[x])


def summarize(m, rows):
    S = collections.OrderedDict()
    S["commit"] = m.g.commit
    S["generated_utc"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    S["orders_in_tracker"] = len(rows)
    S["orders_with_any_record"] = sum(1 for r in rows if r["_has_info"])
    S["category"] = dict(collections.Counter(r["category"] for r in rows))
    S["category_if_A_20261106_1_adopted"] = dict(collections.Counter(r["category_if_A_20261106_1_adopted"] for r in rows))
    S["neither_without_any_record"] = sum(1 for r in rows if r["category"] == "neither" and not r["_has_info"])
    by = collections.defaultdict(collections.Counter)
    for r in rows:
        c = r["category"]
        if c == "formally_revoked_after_evidenced_earlier_end":
            k = f"F:{r['formal_revocation_evidence']} / E:{r['earliest_earlier_end_evidence']} ({r['earliest_earlier_end_basis']})"
        elif c == "formally_revoked_no_earlier_end_evidenced":
            k = f"F:{r['formal_revocation_evidence']}"
        elif c == "earlier_end_but_never_formally_revoked":
            k = f"E:{r['earliest_earlier_end_evidence']} ({r['earliest_earlier_end_basis']})"
        elif c == "blocked":
            k = f"F:{r['formal_revocation_evidence']}"
        else:
            k = "ledger:" + (r["provisional_status"] or "undecided") + (" claim" if r["claim"] else "")
        by[c][k] += 1
    S["category_by_evidence"] = {k: dict(v.most_common()) for k, v in by.items()}
    both = [r for r in rows if r["category"] == "formally_revoked_after_evidenced_earlier_end"]
    S["both_sides_level"] = dict(collections.Counter(lvl_pair(r) for r in both))
    S["both_sides_held_verified_filed_claim"] = sum(1 for r in both if lvl_pair(r) == "held_verified"
                                                    and r["earliest_earlier_end_basis"] == "filed_claim")
    formal = [r for r in rows if r["formal_revocation_instrument"]]
    S["formally_revoked_total"] = len(formal)
    S["formally_revoked_by_evidence"] = dict(collections.Counter(r["formal_revocation_evidence"] for r in formal))
    S["formally_revoked_dated"] = sum(1 for r in formal if r["formal_revocation_date"])

    def share(sub):
        n = len(sub)
        k = sum(1 for r in sub if r["category"] == "formally_revoked_after_evidenced_earlier_end")
        return dict(formally_revoked=n, with_evidenced_earlier_end=k, share=round(k / n, 4) if n else None)
    S["share_all_formally_revoked"] = share(formal)
    S["share_formal_held_verified"] = share([r for r in formal if r["formal_revocation_evidence"] == "held_verified"])
    claimed = [r for r in formal if r["claim"]]
    S["share_formally_revoked_with_filed_claim"] = share(claimed)
    S["share_formally_revoked_with_filed_claim_both_held_verified"] = dict(
        formally_revoked_with_claim=len(claimed),
        earlier_end_both_sides_held_verified=sum(1 for r in claimed if r["category"] ==
                                                 "formally_revoked_after_evidenced_earlier_end" and lvl_pair(r) == "held_verified"))
    S["filed_claim_formal_is_the_end"] = sum(1 for r in claimed if "revoked while operative" in r["confidence_note"])
    S["filed_claim_formally_revoked_blocked"] = dict(collections.Counter(
        r["blocker"] for r in claimed if r["category"] == "blocked"))
    S["routes_of_earlier_end"] = {
        c: dict(collections.Counter(f"{r['earliest_earlier_end_route']} [{r['earliest_earlier_end_basis']}]"
                                    for r in rows if r["category"] == c).most_common())
        for c in ("formally_revoked_after_evidenced_earlier_end", "earlier_end_but_never_formally_revoked")}
    gaps = sorted(int(r["gap_days"]) for r in both)

    def dist(g):
        if not g:
            return {}
        q = lambda p: g[min(len(g) - 1, int(p * (len(g) - 1) + 0.5))]
        bins = collections.OrderedDict((k, 0) for k in ("<1 year", "1-5 years", "5-10 years", "10-25 years",
                                                         "25-50 years", ">=50 years"))
        for d in g:
            y = d / 365.25
            k = "<1 year" if y < 1 else "1-5 years" if y < 5 else "5-10 years" if y < 10 else "10-25 years" \
                if y < 25 else "25-50 years" if y < 50 else ">=50 years"
            bins[k] += 1
        return dict(n=len(g), min=g[0], p25=q(.25), median=q(.5), p75=q(.75), max=g[-1], bins=bins)
    S["gap_days_all"] = dist(gaps)
    S["gap_days_filed_claim"] = dist(sorted(int(r["gap_days"]) for r in both if r["earliest_earlier_end_basis"] == "filed_claim"))
    S["gap_days_both_held_verified"] = dist(sorted(int(r["gap_days"]) for r in both if lvl_pair(r) == "held_verified"))
    S["formal_revoker_top_in_category1"] = dict(collections.Counter(r["formal_revocation_instrument"] for r in both).most_common(12))
    claimed_all = [r for r in formal if r["claim"]]
    S["formally_revoked_with_claim_by_category"] = dict(collections.Counter(
        r["category"] + (" (claim: revoked while operative)" if "revoked while operative" in r["confidence_note"] else "")
        for r in claimed_all).most_common())

    def era(r):
        d = m.order_date(r["eo"])
        return "unknown" if not d else "before 1937" if d < "1937" else "1937-1988" if d < "1989" else "1989 on"
    eras = collections.defaultdict(collections.Counter)
    for r in rows:
        e = era(r)
        eras[e]["orders"] += 1
        eras[e]["formal_revocation_found"] += bool(r["formal_revocation_instrument"])
        eras[e]["formal_revocation_held_verified"] += r["formal_revocation_evidence"] == "held_verified"
        eras[e][r["category"]] += 1
    S["by_era"] = {k: dict(v) for k, v in sorted(eras.items())}
    # The Stage 15 stratified blind sample (a protected stratum, R4): design-weighted shares.
    smp = list(csv.DictReader(io.StringIO(m.g.text("research/stage15/STATISTICS/STRATIFIED_POPULATION_SAMPLE_120_BLIND.csv"))))
    byid = {r["eo"]: r for r in rows}
    W = sum(float(x["design_weight"]) for x in smp)
    cat_w, cat_n = collections.Counter(), collections.Counter()
    for x in smp:
        r = byid.get(x["id"])
        c = r["category"] if r else "not_in_tracker"
        cat_w[c] += float(x["design_weight"])
        cat_n[c] += 1
    fr_w = sum(float(x["design_weight"]) for x in smp if byid.get(x["id"]) and byid[x["id"]]["formal_revocation_instrument"])
    S["stage15_sample"] = dict(n=len(smp), total_weight=round(W, 1), category_n=dict(cat_n.most_common()),
                               category_weighted_share={k: round(v / W, 4) for k, v in cat_w.most_common()},
                               formal_revocation_found_weighted_share=round(fr_w / W, 4),
                               formal_revocation_found_n=sum(1 for x in smp if byid.get(x["id"]) and
                                                             byid[x["id"]]["formal_revocation_instrument"]))
    S["claim_revocation_of_parent_as_amended_only"] = sum(1 for i in m.parent_only if m.parent_only[i])
    bl = collections.Counter()
    for r in rows:
        for b in filter(None, r["blocker"].split("|")):
            bl[b] += 1
    S["blocker_flags_all_rows"] = dict(bl.most_common())
    return S


def blockers_extra(m, rows, S):
    """Counts for the 'what blocks the rest' section."""
    B = collections.OrderedDict()
    formal = [r for r in rows if r["formal_revocation_instrument"]]
    noE = [r for r in formal if r["category"] != "formally_revoked_after_evidenced_earlier_end"]
    B["formal_lead_only"] = sum(1 for r in formal if r["formal_revocation_evidence"] == "lead_only")
    B["formal_lead_only_by_basis"] = dict(collections.Counter(r["formal_revocation_basis"] for r in formal
                                                              if r["formal_revocation_evidence"] == "lead_only").most_common())
    lead_actors = collections.Counter(r["formal_revocation_instrument"] for r in formal
                                      if r["formal_revocation_evidence"] == "lead_only")
    B["formal_lead_only_top_acting_instruments"] = dict(lead_actors.most_common(15))
    B["formal_lead_only_acting_instruments_distinct"] = len(lead_actors)
    have_draft = set(m.drafts)
    B["formally_revoked_without_earlier_end_total"] = len(noE)
    B["formally_revoked_no_E_without_claim_or_clause_draft"] = sum(1 for r in noE if not r["claim"] and r["eo"] not in have_draft)
    B["formally_revoked_no_E_with_clause_draft_only"] = sum(1 for r in noE if not r["claim"] and r["eo"] in have_draft)
    B["formally_revoked_no_E_with_claim"] = sum(1 for r in noE if r["claim"])
    B["orders_without_claim_or_clause_draft"] = sum(1 for r in rows if not r["claim"] and r["eo"] not in have_draft)
    pre = [r for r in rows if r["eo"] in m.U and not r["claim"] and m.order_date(r["eo"])[:4].isdigit()
           and m.order_date(r["eo"]) < "1937-01-01"]
    B["pre1937_orders_without_claim"] = len(pre)
    B["pre1937_orders_without_claim_with_formal_revocation"] = sum(1 for r in pre if r["formal_revocation_instrument"])
    # sorry lemmas
    sorry_f = collections.Counter()
    only_sorry = 0
    for i in m.universe:
        f = [o for o in m.lemmas.get(i, []) if o["statement"]["relation"] in F_RELATIONS and not o["statement"].get("qualifier")]
        if f and all(o["status"] == "sorry" for o in f):
            only_sorry += 1
        for o in f:
            if o["status"] == "sorry":
                sorry_f[o.get("sorry_reason", "")[:60]] += 1
    B["orders_whose_whole_revocation_lemmas_are_all_sorry"] = only_sorry
    B["sorry_whole_revocation_lemmas_by_reason"] = dict(sorry_f.most_common())
    B["sorry_class_lemmas"] = [dict(id=o["lemma_id"], subject=o["statement"]["subject"][:70],
                                    relation=o["statement"]["relation"], reason=o.get("sorry_reason", "")[:60])
                               for o in m.class_lemmas if o["status"] == "sorry"]
    # Formal revocation upgradable: lead-only F where the acting order's FR original text is committed.
    up = collections.Counter()
    for r in formal:
        if r["formal_revocation_evidence"] == "lead_only":
            a = r["formal_revocation_instrument"]
            p = f"jobs/fr-originals/data/full_run/texts/{a.replace('EO:', 'EO_')}.txt"
            up["acting_text_committed" if m.g.sha256(p) else "acting_text_not_committed"] += 1
    B["lead_only_formal_acting_text"] = dict(up)
    # Upgrade test: does the committed official text of the acting order contain the target's number at all?
    # (A table-form revocation such as EO 12553's list is not parsed by the later-events sentence scanner.)
    found = collections.Counter()
    for r in formal:
        if r["formal_revocation_evidence"] != "lead_only" or not r["formal_revocation_instrument"].startswith("EO:"):
            continue
        a = r["formal_revocation_instrument"].replace("EO:", "EO_")
        hit = None
        for p in (f"jobs/fr-originals/data/full_run/texts/{a}.txt", f"jobs/fr-originals/output/texts/{a}.txt"):
            hit = m.names_target(r["eo"], p)
            if hit is not None:
                break
        found["number_found" if hit else "number_not_found" if hit is False else "no_committed_text"] += 1
    B["lead_only_formal_number_in_committed_acting_text"] = dict(found)
    # Targeting: formally revoked orders with no claim and no evidenced earlier end whose revoking instrument is
    # one that, elsewhere in this table, revoked an order already spent (category 1) or is a claim's cleanup bound.
    cleanup = {r["formal_revocation_instrument"] for r in rows
               if r["category"] == "formally_revoked_after_evidenced_earlier_end" or "R3_" in r["blocker"]} - {""}
    tgt = [r for r in noE if not r["claim"] and r["formal_revocation_instrument"] in cleanup]
    B["cleanup_revokers"] = len(cleanup)
    B["unclaimed_formally_revoked_no_E_by_cleanup_revoker"] = len(tgt)
    B["unclaimed_formally_revoked_no_E_by_cleanup_revoker_top"] = dict(collections.Counter(
        r["formal_revocation_instrument"] for r in tgt).most_common(10))
    r3 = [r for r in rows if "R3_FIRST_END_UNRESOLVED" in r["blocker"]]
    B["r3_rows"] = len(r3)
    B["r3_by_formal_instrument"] = dict(collections.Counter(r["formal_revocation_instrument"] for r in r3).most_common(6))
    B["r3_claims_disclosing_functionally_spent"] = sum(
        1 for r in r3 if "functionally spent" in json.dumps(m.claims.get(r["eo"], {})).lower())
    B["claims_whole_end_route"] = dict(collections.Counter(
        (m.claim_end(i) or {}).get("route", "") for i in m.claims).most_common())
    # Tracker code path.
    v1 = [i for i, c in m.claims.items() if c.get("schema", "").endswith("v1")]
    v2 = [i for i, c in m.claims.items() if c.get("schema", "").endswith("v2")]
    B["tracker_claims_v1"] = len(v1)
    B["tracker_claims_v2"] = len(v2)
    B["tracker_v2_not_later_than"] = sum(1 for i in v2 if (m.claims[i].get("whole_order_end") or {}).get("date_kind") == "not_later_than")
    return B


def tracker_fix_counts(m, rows):
    """Orders with a filed claim whose row this measure fills from held verified bytes on the revocation side
    (claim or Formulario lemma); compare tracker_fix_claim_only(), which reads the claim alone."""
    out = collections.Counter()
    for r in rows:
        if not r["claim"]:
            continue
        F = r["_F"]
        held = F and F["level"] == "held_verified" and r["formal_revocation_date"]
        if r["category"] == "formally_revoked_after_evidenced_earlier_end" and held \
                and r["earliest_earlier_end_basis"] == "filed_claim":
            out["yes"] += 1
        elif r["category"] == "formally_revoked_no_earlier_end_evidenced" and held:
            out["no"] += 1
        else:
            out["blank"] += 1
    return dict(out)


EO_NUM_RE = re.compile(r"\b(?:EO|Executive\s+Orders?)(?:\s*Nos?\.?)?\s*:?\s*(\d{1,5}[A-Z]?)\b")


def v1_formal_after_cessation(claim):
    """The rule TRACKER_FIX.md proposes for v1 claims, using only the claim's own fields.

    True: the whole-order end is exact and is an own-terms, exhaustion, implied-supersession or termination end
    (not a revocation, and not a route an owner ruling keeps open), and the earliest instrument listed as an
    express revocation or supersession on every operative clause takes effect after that end, without naming a
    different order "as amended" instead of this one (TC09). False: the whole-order end is itself an express
    revocation or supersession, or the earliest such instrument takes effect on or before the end. None otherwise.
    """
    w = claim.get("whole_order_end") if isinstance(claim.get("whole_order_end"), dict) else None
    if not w or not is_date(w.get("date", "")):
        return None
    route = classify_mechanism(" ".join(str(w.get(k, "")) for k in ("mechanism", "mechanism_note", "mechanism_detail")))
    if route == "formal":
        return False
    if route not in ("own_terms", "exhaustion", "implied_supersession", "termination_by_later_instrument_or_body_end"):
        return None
    me = claim.get("instrument_id", "").split(":", 1)[-1]
    clauses = [c for c in claim.get("operative_clauses") or [] if isinstance(c, dict)]
    if not clauses:
        return None
    per = []
    for c in clauses:
        acts = {}
        for e in c.get("later_events") or []:
            if not isinstance(e, dict) or not is_date(str(e.get("effective_date", ""))):
                continue
            mech = " ".join(str(e.get(k, "")) for k in ("mechanism", "mechanism_detail"))
            if classify_mechanism(mech) != "formal":
                continue
            named = set(EO_NUM_RE.findall(mech)) - set(EO_NUM_RE.findall(str(e.get("actor", ""))))
            if "as amended" in mech.lower() and named and me not in named:
                continue  # revokes another (parent) order as amended, not this one by name
            for a in EO_NUM_RE.findall(str(e.get("actor", ""))) or [str(e.get("actor", ""))]:
                acts[a] = min(acts.get(a, "9999"), e["effective_date"])
        per.append(acts)
    common = set.intersection(*[set(a) for a in per])
    if not common:
        return None
    first = min(max(a[x] for a in per) for x in common)
    return first > w["date"]


def tracker_fix_claim_only(m):
    out = collections.Counter()
    for i, c in m.claims.items():
        if c.get("schema", "").endswith("v2"):
            out["v2 (unchanged: derived(), bounded ends stay blank)"] += 1
            continue
        out[{True: "yes", False: "no", None: "blank"}[v1_formal_after_cessation(c)]] += 1
    return dict(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--rev", default="origin/main")
    ap.add_argument("--out", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args()
    g = Git(a.repo, a.rev)
    m = Measure(g)
    rows = m.run()
    S = summarize(m, rows)
    S["blockers"] = blockers_extra(m, rows, S)
    S["tracker_fix_would_write"] = tracker_fix_counts(m, rows)
    S["tracker_fix_claim_only_rule"] = tracker_fix_claim_only(m)
    S["inputs_sha256"] = dict(sorted((k, v) for k, v in m.inputs.items() if not k.startswith("jobs/peano-formulario/output/lemmas/")))
    S["inputs_formulario_lemma_shards"] = sum(1 for k in m.inputs if k.startswith("jobs/peano-formulario/output/lemmas/"))
    cols = [k for k in rows[0] if not k.startswith("_")]
    keep = [r for r in rows if r["_has_info"]]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in keep:
        w.writerow(r)
    data = buf.getvalue().encode("utf-8")
    if len(data) > 5 * 2 ** 20:
        raise SystemExit(f"MEASURE.csv would be {len(data)} bytes, over the 5 MiB cap")
    with open(os.path.join(a.out, "MEASURE.csv"), "wb") as f:
        f.write(data)
    S["measure_csv_rows"] = len(keep)
    S["measure_csv_bytes"] = len(data)
    with open(os.path.join(a.out, "SUMMARY.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(S, f, indent=1, ensure_ascii=False)
        f.write("\n")
    g.close()
    print(json.dumps({k: S[k] for k in ("commit", "category", "category_if_A_20261106_1_adopted",
                                        "share_all_formally_revoked", "measure_csv_bytes")}, indent=1))


if __name__ == "__main__":
    main()
