"""Repetita: read the List of CFR Sections Affected (LSA) from govinfo, month by month, and list every Title 3 entry and
every entry anywhere that names an executive order, with the exact bytes and byte span each came from.

Named for Justinian's Codex repetitae praelectionis (534), the revised edition of his Code. Zero model tokens.

Route (robots-permitted, documented bulk access): https://www.govinfo.gov/sitemap/LSA_sitemap_index.xml lists the
year sitemaps, which list the monthly packages; each package's bytes are https://www.govinfo.gov/content/pkg/<id>.zip
(html member per CFR title, a pdf per title, mods/premis/dip xml). Parsing reads only the html members.

The LSA is cumulative within a calendar year (the December issue repeats every entry of January to November), so a
row is kept once, at the first issue that prints it, with first_issue, last_issue and n_issues. Each row carries the
sha256 of the html member that holds it and the entry's byte span in that member; the zip's sha256 is in
SOURCES.jsonl. Raw bytes stay in the job cache and are never committed.

An entry's last column is a Federal Register citation: from 1997 into the 2010s "YY-PAGE" (two-digit year of the
Federal Register volume, then the first page, so 97-4415 is 62 FR 4415), in recent issues the page alone. Either way
it is a pointer to a page that this job does not hold: every revocation or amendment it reads is a lead until that
Federal Register page is held and read.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import io
import json
import os
import re
import sys
import threading
import time
import zipfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_lib"))
from fetch_pool import FetchPool, FetchError  # noqa: E402

UA = "EO-Road-System/1.0 (Repetita LSA reader; owner-run research)"
SITEMAP_INDEX = "https://www.govinfo.gov/sitemap/LSA_sitemap_index.xml"
PKG_ZIP = "https://www.govinfo.gov/content/pkg/{issue}.zip"
MEMBER_URL = "https://www.govinfo.gov/content/pkg/{issue}/html/{issue}-title{title}.htm"
FIRST_YEAR = 1997
MAX_MEMBER_BYTES = 30_000_000
MAX_MEMBERS = 400
LOCATOR = "repetita-lsa-1"
GRADE = ("government_printed_lsa_listing (GPO/OFR List of CFR Sections Affected, govinfo html member; a pointer to "
         "the Federal Register page, not that page and not the text of any order)")
SMOKE_ISSUES = ["LSA-1997-01", "LSA-2003-03", "LSA-2018-01"]

# ---------------------------------------------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------------------------------------------
REF = r"(?:\d{2}-)?\d{1,6}"
REFLIST = REF + r"(?:\s*,\s*" + REF + r")*"
LEADER = re.compile(r"^(?P<text>.*?)\s*\.{2,}\s*(?P<ref>" + REFLIST + r")\s*$")
REFONLY = re.compile(r"^(?P<ref>" + REFLIST + r")$")
LEADER_ANYWHERE = re.compile(r"\.{2,}[ \t]*" + REFLIST + r"[ \t]*\r?$|^" + REFLIST + r"[ \t]*\r?$", re.M)
PAGE_MARK = re.compile(r"^\[\[Page (\d+)\]\]$")
TAGS = re.compile(r"<[^>]+>")
T3_HEADING = re.compile(
    r"^(Presidential Documents|Proclamations?|Executive Orders?|Administrative Orders?|Memorand\w+|Notices?|"
    r"Presidential Determinations?|Determinations?|Orders?|Letters?|Messages?|Reorganization Plans?|"
    r"Other Presidential Documents|Directives?|Authorizations?|Statements?)\s*:?$")
OTHER_HEADING = re.compile(r"^(Chapter|Subchapter|Subtitle|Subpart|Part|PART|Appendix|Title|[A-Z][A-Za-z ,&'-]{2,60}:$)")
HEADER_SKIP = re.compile(r"^(\[List of CFR|\[From the|TITLE\s+\d+)")
VERBS = (r"See|Amended|Amends|Revoked|Revoking|Rescinded|Superseded|Continued|Supplemented|Revised|Terminated|"
         r"Modified|Corrected|Expanded|Added|Removed|Delegated|Extended|Implemented|Clarified|Reinstated|"
         r"Reaffirmed|Suspended|Partially|Further|Reissued|Redesignated|Withdrawn|Vacated|Designated|Transferred")
VERB_START = re.compile(r"^(?:" + VERBS + r")\b")
VERB_ANY = re.compile(r"\s(?:" + VERBS + r")\b")
SECTION_TOKEN = re.compile(r"^(\d+[A-Za-z]?(?:\.[\w-]+)?(?:--\d+(?:\.[\w-]+)?)?)(?:\s+(.*))?$", re.S)
EO_MENTION = re.compile(r"\bE\.\s?O\.|\bEO\s?\d|\bExecutive\s+Orders?\b|\bExec\.\s+Orders?\b|\bEx\.\s?Ord\b", re.I)
EO_NUMBERS = re.compile(r"(?:\bE\.\s?O\.|\bEO\b|\bExecutive\s+Orders?\b|\bExec\.\s+Orders?\b|\bEx\.\s?Ord\.)"
                        r"\s*(?:No\.|Nos\.)?\s*(\d{3,5})", re.I)
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10,
          "nov": 11, "dec": 12}
DATE_TXT = r"([A-Z][a-z]{2,8})\.?\s+(\d{1,2}),\s+(\d{4})"
ACT_EO = re.compile(r"\b(?:EO|E\.O\.)\s+(\d{3,5})\b")
ACT_PROC = re.compile(r"\bProc\.\s+(\d{3,5})\b")
ACT_PLO = re.compile(r"\bPLO\s+(\d{3,5})\b")
ACT_NOTICE = re.compile(r"\bNotice of\s+" + DATE_TXT)
ACT_MEMO = re.compile(r"\bMemorandum of\s+" + DATE_TXT)
ACT_PL = re.compile(r"\bPub\.\s+L\.\s+(\d{2,3})-(\d{1,4})\b")
ACT_BARE = re.compile(r"\b(?:by|See)\s+(\d{3,5})\b")
MECH = [  # (word, mechanism, mechanism_class)
    ("revoked", "revocation", "ending"), ("revoking", "revocation", "ending"), ("rescinded", "rescission", "ending"),
    ("superseded", "supersession", "ending"), ("terminated", "termination", "ending"),
    ("withdrawn", "withdrawal", "ending"), ("vacated", "vacation", "ending"),
    ("amended", "amendment", "modifying"), ("amends", "amendment", "modifying"), ("revised", "amendment", "modifying"),
    ("modified", "modification", "modifying"), ("supplemented", "supplement", "modifying"),
    ("expanded", "amendment", "modifying"), ("extended", "extension", "modifying"),
    ("corrected", "correction", "modifying"), ("reinstated", "restoration", "ending"),
    ("continued", "continuation", "continuing"), ("reaffirmed", "continuation", "continuing"),
    ("see", "cross_reference", "mention"),
]


class Entry:
    __slots__ = ("title", "category", "item", "change", "ref", "start", "end", "lsa_page", "continuation", "text")

    def tup(self):
        return (self.title, self.category, self.item, self.change, self.ref)

    def refs(self):
        return [r.strip() for r in self.ref.split(",") if r.strip()]


def fr_citation(ref: str, issue_year: int):
    """(volume, page, kind, year_assumed) from an LSA reference: 'YY-PAGE' or a bare page."""
    m = re.fullmatch(r"(?:(\d{2})-)?(\d{1,6})", ref)
    if not m:
        return None, None, "unparsed", False
    page = int(m.group(2))
    if m.group(1):
        yy = int(m.group(1))
        year = 1900 + yy if yy >= 36 else 2000 + yy
        return year - 1935, page, "yy_page", False
    return issue_year - 1935, page, "page", True


def parse_member(raw: bytes, title: int):
    """Entries of one LSA title member. Offsets are byte offsets into `raw` (decoded latin-1, one char per byte).
    Returns (entries, stats)."""
    text = raw.decode("latin-1")
    low = text.lower()
    lo = low.find("<pre>")
    hi = low.rfind("</pre>")
    stats = {"leader_lines_independent": len(LEADER_ANYWHERE.findall(text)), "entries": 0, "dropped_pending": 0,
             "dropped_samples": [], "has_pre": lo >= 0}
    if lo < 0:
        return [], stats
    lo += 5
    hi = hi if hi > lo else len(text)
    lines = []
    pos = lo
    for ln in text[lo:hi].split("\n"):
        t = ln.rstrip("\r")
        lines.append((pos, pos + len(t), t))
        pos += len(ln) + 1
    markers = {i for i, (_, _, t) in enumerate(lines) if PAGE_MARK.match(t.strip())}
    entries = []
    pending = []
    category, last_item, last_sec, lsa_page = None, None, None, None
    for i, (s, e, t) in enumerate(lines):
        st = t.strip()
        if i in markers:
            lsa_page = int(PAGE_MARK.match(st).group(1))
            continue
        if not st:
            if (i - 1 in markers) or (i + 1 in markers):
                continue
            if pending:
                stats["dropped_pending"] += len(pending)
                if len(stats["dropped_samples"]) < 5:
                    stats["dropped_samples"].append(" ".join(p[2].strip() for p in pending)[:120])
                pending = []
            continue
        m = LEADER.match(st) or (REFONLY.match(st) if pending else None)
        if not m:
            clean = html.unescape(TAGS.sub("", st))
            if not pending and HEADER_SKIP.match(clean):
                continue
            if not pending and title == 3 and T3_HEADING.match(clean):
                category = clean.rstrip(":").strip().lower()
                continue
            if not pending and title != 3 and OTHER_HEADING.match(clean):
                continue
            pending.append((s, e, t))
            continue
        parts = [p[2] for p in pending] + [m.groupdict().get("text") or ""]
        start = pending[0][0] if pending else s
        pending = []
        full = html.unescape(TAGS.sub("", " ".join(x.strip() for x in parts)))
        full = re.sub(r"\s+", " ", full).strip()
        en = Entry()
        en.title, en.category, en.ref, en.start, en.end, en.lsa_page, en.text = title, category, m.group("ref"), start, e, lsa_page, full
        en.continuation = False
        if title == 3:
            nm = re.match(r"^(\d{1,5}[A-Z]?)(?:\s+(.*))?$", full)
            if nm:
                en.item, en.change = nm.group(1), (nm.group(2) or "")
                last_item = en.item
            elif VERB_START.match(full):
                en.item, en.change, en.continuation = last_item, full, True
            else:
                vm = VERB_ANY.search(full)
                if vm:
                    en.item, en.change = full[:vm.start()].strip(), full[vm.start():].strip()
                else:
                    en.item, en.change = full, ""
                last_item = en.item
        else:
            sm = SECTION_TOKEN.match(full)
            if sm:
                en.item, en.change = sm.group(1), (sm.group(2) or "")
                last_sec = en.item
            else:
                en.item, en.change, en.continuation = last_sec, full, True
        entries.append(en)
    if pending:
        stats["dropped_pending"] += len(pending)
    stats["entries"] = len(entries)
    return entries, stats


def mechanism_of(change: str):
    m = re.match(r"^(?:Partially\s+|Further\s+)?(\w+)", change.strip(), re.I)
    word = (m.group(1) if m else "").lower()
    if change.strip().lower().startswith("revoked in part") or change.strip().lower().startswith("partially"):
        qual = "in part"
    else:
        qual = ""
    # "Partially revoked by ..." -> read the next word
    mm = re.match(r"^(?:partially|further)\s+(\w+)", change.strip(), re.I)
    if mm:
        word = mm.group(1).lower()
    for w, mech, cls in MECH:
        if word == w:
            return word, mech, cls, qual
    return word, "", "", qual


def acting_ids(change: str):
    out = []

    def date_iso(g):
        mo = MONTHS.get(g[0][:3].lower())
        if not mo:
            return None
        try:
            return dt.date(int(g[2]), mo, int(g[1])).isoformat()
        except ValueError:
            return None
    for m in ACT_EO.finditer(change):
        out.append(("EO:" + m.group(1), m.start()))
    for m in ACT_PROC.finditer(change):
        out.append(("PROC:" + m.group(1), m.start()))
    for m in ACT_PLO.finditer(change):
        out.append(("PLO:" + m.group(1), m.start()))
    for m in ACT_NOTICE.finditer(change):
        d = date_iso(m.groups())
        if d:
            out.append(("NOTICE:" + d, m.start()))
    for m in ACT_MEMO.finditer(change):
        d = date_iso(m.groups())
        if d:
            out.append(("MEMORANDUM:" + d, m.start()))
    for m in ACT_PL.finditer(change):
        out.append((f"PL:{m.group(1)}-{m.group(2)}", m.start()))
    ids = []
    for a, _ in sorted(out, key=lambda x: x[1]):
        if a not in ids:
            ids.append(a)
    bare = [m.group(1) for m in ACT_BARE.finditer(change)] if not ids else []
    return ids, bare


def row_from_entry(en: Entry, issue: str, issue_date: str, member: str, member_sha: str, ref: str):
    year = int(issue[4:8])
    vol, page, kind, assumed = fr_citation(ref, year)
    word, mech, cls, qual = mechanism_of(en.change) if en.change else ("", "", "", "")
    acts, bare = acting_ids(en.change)
    eo_mention = bool(EO_MENTION.search(en.text))
    eo_nums = sorted({n for n in EO_NUMBERS.findall(en.text)})
    eo_target = ""
    if en.title == 3 and en.category in ("executive orders", "executive order") and en.item and re.fullmatch(r"\d{1,5}", en.item):
        eo_target = "EO:" + en.item
    cite = f"{en.title} CFR {en.item}" if en.item and en.title != 3 else (f"3 CFR (Presidential Documents: {en.category or 'uncategorized'}) {en.item or ''}".strip())
    return {
        "issue": issue, "issue_date": issue_date, "title": en.title, "cfr_cite": cite, "category": en.category or "",
        "item": en.item or "", "change": en.change, "continuation_line": int(en.continuation),
        "mechanism_printed": word, "mechanism": mech, "mechanism_class": cls, "qualifier": qual,
        "acting": "|".join(acts), "acting_bare_number": "|".join(bare),
        "fr_ref": ref, "ref_kind": kind, "fr_volume": vol if vol else "", "fr_page": page if page is not None else "",
        "fr_cite": f"{vol} FR {page}" if vol else "", "year_assumed": int(assumed),
        "eo_mention": int(eo_mention), "eo_numbers_cited": "|".join(eo_nums), "eo_target": eo_target,
        "lsa_page": en.lsa_page if en.lsa_page is not None else "", "member": member, "member_sha256": member_sha,
        "span_start": en.start, "span_end": en.end,
        "first_issue": issue, "last_issue": issue, "n_issues": 1, "_quote": en.text,
    }


ROW_COLUMNS = ["issue", "issue_date", "title", "cfr_cite", "category", "item", "change", "continuation_line",
               "mechanism_printed", "mechanism", "mechanism_class", "qualifier", "acting", "acting_bare_number",
               "fr_ref", "ref_kind", "fr_volume", "fr_page", "fr_cite", "year_assumed", "eo_mention",
               "eo_numbers_cited", "eo_target", "lsa_page", "member", "member_sha256", "span_start", "span_end",
               "first_issue", "last_issue", "n_issues"]


def row_key(r):
    return (str(r["first_issue"])[4:8] if r.get("first_issue") else str(r["issue"])[4:8], str(r["title"]), r["category"],
            r["item"], r["change"], str(r["fr_ref"]))


def verify_entry(raw: bytes, en: Entry) -> bool:
    """The span re-sliced from the held bytes ends with the entry's reference after a dot leader and, for a
    non-continuation entry, begins with the item token."""
    s = raw[en.start:en.end].decode("latin-1")
    last = s.strip().split("\n")[-1].strip()
    m = LEADER.match(last) or REFONLY.match(last)
    if not m or m.group("ref") != en.ref:
        return False
    if not en.continuation and en.item:
        first = html.unescape(TAGS.sub("", s.strip()))
        if not first.startswith(en.item) and not (en.title == 3 and not re.match(r"^\d", en.item or "")):
            return False
    return True


# ---------------------------------------------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------------------------------------------
# Independent facts (known from the orders themselves, not from the parser): the LSA issue that must print the
# Title 3 entry, the order, the change, the printed reference and the Federal Register citation it stands for.
KNOWN = [
    {"issue": "LSA-2018-01", "item": "13799", "change": "Revoked by EO 13820", "fr_cite": "83 FR 969",
     "fact": "EO 13799 (Presidential Advisory Commission on Election Integrity) revoked by EO 13820 of 2018-01-03"},
    {"issue": "LSA-2003-03", "item": "10865", "change": "Amended by EO 13284", "fr_cite": "68 FR 4075",
     "fact": "EO 10865 amended by EO 13284 of 2003-01-23"},
    {"issue": "LSA-1997-01", "item": "12543", "change": "Continued by Notice of Jan. 2, 1997", "fr_cite": "62 FR 587",
     "fact": "EO 12543 national emergency continued by notice of 1997-01-02"},
    {"issue": "LSA-2010-05", "item": "13292", "change": "Revoked by EO 13526", "fr_cite": "75 FR 707",
     "fact": "EO 13292 revoked by EO 13526 of 2009-12-29"},
    {"issue": "LSA-2001-11", "item": "12667", "change": "Revoked by EO 13233", "fr_cite": "66 FR 56025",
     "fact": "EO 12667 revoked by EO 13233 of 2001-11-01"},
]
NEG_MADE_UP = [  # must not be found anywhere in the entries
    {"title": 3, "category": "executive orders", "item": "99999", "note": "made-up order number"},
    {"title": 3, "category": "executive orders", "item": "13799", "change": "Revoked by EO 13821",
     "note": "near miss of a real entry: wrong revoking order"},
    {"title": 3, "category": "executive orders", "item": "13799", "change": "Revoked by EO 13820", "fr_ref": "18-970",
     "note": "near miss of a real entry: wrong page"},
    {"title": 3, "category": "executive orders", "item": "10865", "change": "Amended by EO 13285",
     "note": "near miss of a real entry: wrong amending order"},
    {"title": 99, "category": "", "item": "9999.99", "note": "made-up CFR section of a made-up title"},
    {"title": 32, "category": "", "item": "99999.99", "note": "made-up section of a real title"},
]
PLANT_HEADING = "Executive Orders"
PLANT_POS = ("99998", "Amended by EO 99999", "99-77777")


def _dotted(text, ref, width=66):
    return text + "." * max(3, width - len(text) - len(ref)) + ref


def plant(raw: bytes):
    """Insert a planted block before </pre>: a heading, a positive entry, a line with no leader, and a line whose
    reference is not a number. Returns (planted_bytes, positive_line)."""
    pos_line = _dotted(f"{PLANT_POS[0]} {PLANT_POS[1]}", PLANT_POS[2])
    block = (f"\n\n{PLANT_HEADING}\n\n{pos_line}\n\n99997 Revoked by EO 99996 99-77776\n\n"
             f"99996 Revoked by EO 99995.........see page 7\n\n")
    text = raw.decode("latin-1")
    i = text.lower().rfind("</pre>")
    if i < 0:
        return raw + block.encode("latin-1"), pos_line
    return (text[:i] + block + text[i:]).encode("latin-1"), pos_line


def plant_controls(raw3: bytes):
    """Planted control on the issue's own Title 3 bytes. Returns a list of {name, expected, found, ok}."""
    before, _ = parse_member(raw3, 3)
    planted, pos_line = plant(raw3)
    after, _ = parse_member(planted, 3)
    old = {(e.start, e.tup()) for e in before}
    new = [e for e in after if (e.start, e.tup()) not in old]
    res = []
    pos = [e for e in new if e.item == PLANT_POS[0]]
    ok = (len(pos) == 1 and pos[0].change == PLANT_POS[1] and pos[0].ref == PLANT_POS[2]
          and pos[0].category == PLANT_HEADING.lower()
          and planted[pos[0].start:pos[0].end].decode("latin-1") == pos_line)
    res.append({"name": "planted_positive_found_with_exact_span", "kind": "positive", "ok": ok})
    res.append({"name": "planted_line_without_leader_not_an_entry", "kind": "negative",
                "ok": not any(e.item in ("99997",) for e in after)})
    res.append({"name": "planted_line_with_non_numeric_reference_not_an_entry", "kind": "negative",
                "ok": not any(e.item in ("99996",) for e in after)})
    res.append({"name": "planted_block_adds_exactly_one_entry", "kind": "negative", "ok": len(new) == 1})
    return res


def known_control(issue: str, entries):
    out = []
    for k in KNOWN:
        if k["issue"] != issue:
            continue
        found = False
        for e in entries:
            if e.title == 3 and e.item == k["item"] and e.change == k["change"]:
                for r in e.refs():
                    v, p, _, _ = fr_citation(r, int(issue[4:8]))
                    if f"{v} FR {p}" == k["fr_cite"]:
                        found = True
        out.append({"name": f"known_fact:{k['item']}:{k['change']}", "kind": "positive", "fact": k["fact"],
                    "expected_fr_cite": k["fr_cite"], "ok": found})
    return out


def negative_controls(rows):
    """Made-up and near-miss entries must be absent from the final rows."""
    out = []
    for n in NEG_MADE_UP:
        hit = [r for r in rows if r["title"] == n["title"] and r["category"] == n["category"] and r["item"] == n["item"]
               and ("change" not in n or r["change"] == n["change"])
               and ("fr_ref" not in n or r["fr_ref"] == n["fr_ref"])]
        out.append({"name": "negative:" + n["note"], "kind": "negative", "ok": not hit, "hits": len(hit)})
    return out


# ---------------------------------------------------------------------------------------------------------------
# One issue
# ---------------------------------------------------------------------------------------------------------------
def issue_date_of(issue: str) -> str:
    y, m = int(issue[4:8]), int(issue[9:11])
    nxt = dt.date(y + (m == 12), m % 12 + 1, 1)
    return (nxt - dt.timedelta(days=1)).isoformat()


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def process_zip(issue: str, zip_bytes: bytes, retrieved: str):
    """Parse one LSA package. Returns dict(rows, members, stats, controls, errors)."""
    res = {"rows": [], "members": [], "stats": defaultdict(int), "controls": [], "errors": []}
    issue_date = issue_date_of(issue)
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as e:
        res["errors"].append(f"bad zip: {e}")
        return res
    pat = re.compile(r"^" + re.escape(issue) + r"/html/" + re.escape(issue) + r"-title(\d+)\.htm$")
    infos = [i for i in zf.infolist() if pat.match(i.filename)]
    if len(zf.infolist()) > MAX_MEMBERS:
        res["errors"].append("too many zip members")
        return res
    t3_raw = None
    all_entries = []
    for info in sorted(infos, key=lambda i: int(pat.match(i.filename).group(1))):
        title = int(pat.match(info.filename).group(1))
        if info.file_size > MAX_MEMBER_BYTES:
            res["errors"].append(f"member too large: {info.filename}")
            continue
        raw = zf.read(info)
        msha = sha256(raw)
        entries, st = parse_member(raw, title)
        res["stats"]["members"] += 1
        for k in ("leader_lines_independent", "entries", "dropped_pending"):
            res["stats"][k] += st[k]
        if st["dropped_samples"]:
            res["stats"].setdefault("dropped_samples", [])
        member = f"html/{info.filename.rsplit('/', 1)[-1]}"
        kept = 0
        span_bad = 0
        for en in entries:
            if not verify_entry(raw, en):
                span_bad += 1
            if title == 3 or EO_MENTION.search(en.text):
                for ref in en.refs():
                    res["rows"].append(row_from_entry(en, issue, issue_date, member, msha, ref))
                    kept += 1
        res["stats"]["span_check_failures"] += span_bad
        res["stats"]["span_checks"] += len(entries)
        res["members"].append({"title": title, "member": member, "sha256": msha, "bytes": len(raw), "entries": len(entries),
                               "rows": kept, "dropped_samples": st["dropped_samples"]})
        if title == 3:
            t3_raw = raw
            all_entries = entries
    res["stats"] = dict(res["stats"])
    if t3_raw is not None:
        res["controls"] += plant_controls(t3_raw)
        res["controls"] += known_control(issue, all_entries)
    else:
        res["controls"].append({"name": "title3_member_present", "kind": "positive", "ok": False})
    return res


# ---------------------------------------------------------------------------------------------------------------
# Listing the issues
# ---------------------------------------------------------------------------------------------------------------
def api_key(env):
    """(key, kind). Reads API_DATA_GOV_KEY, then GOVINFO_API_KEY; never prints it. DEMO_KEY is reported as kind
    'demo' and may be used in smoke runs only."""
    for name in ("API_DATA_GOV_KEY", "GOVINFO_API_KEY"):
        v = (env.get(name) or "").strip()
        if v:
            return v, ("demo" if v == "DEMO_KEY" else "real"), name
    return "", "none", ""


def api_listing(key, opener=None, timeout=60, pages=20):
    """LSA package ids from the keyed govinfo API (the key goes in an X-Api-Key header, never in a URL or log). Used
    only to cross-check the sitemap listing; the bytes always come from the keyless content URLs."""
    import urllib.request
    ids, url = [], "https://api.govinfo.gov/collections/LSA/1990-01-01T00:00:00Z?pageSize=100&offsetMark=*"
    for _ in range(pages):
        req = urllib.request.Request(url, headers={"X-Api-Key": key, "User-Agent": UA})
        with (opener or urllib.request.urlopen)(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        ids += [p["packageId"] for p in d.get("packages", []) if str(p.get("packageId", "")).startswith("LSA-")]
        url = d.get("nextPage")
        if not url:
            break
    return ids


def list_issues(pool: FetchPool, today: dt.date):
    """Issue ids from govinfo's LSA sitemaps, plus every month through last month that they omit (marked
    speculative: a 404 on one of those is not a failure)."""
    listed = {}
    problems = []
    try:
        idx = pool.fetch(SITEMAP_INDEX)["body"].decode("utf-8", "replace")
        years = sorted(set(re.findall(r"https://www\.govinfo\.gov/sitemap/LSA_\d{4}_sitemap\.xml", idx)))
    except Exception as e:
        problems.append(f"sitemap index: {type(e).__name__}: {e}"[:200])
        years = []
    for u in years:
        try:
            body = pool.fetch(u)["body"].decode("utf-8", "replace")
            for iss in re.findall(r"/app/details/(LSA-\d{4}-\d{2})\b", body):
                listed[iss] = False
        except Exception as e:
            problems.append(f"{u}: {type(e).__name__}: {e}"[:200])
    last = dt.date(today.year, today.month, 1) - dt.timedelta(days=1)
    newest = max(listed) if listed else None
    for y in range(FIRST_YEAR, last.year + 1):
        for m in range(1, 13):
            if (y, m) > (last.year, last.month):
                break
            iid = f"LSA-{y}-{m:02d}"
            # fill only what the sitemaps cannot have: months after the newest listed one, or everything when
            # the sitemaps could not be read
            if newest is None or iid > newest:
                listed.setdefault(iid, True)
    return [(i, listed[i]) for i in sorted(listed) if int(i[4:8]) >= FIRST_YEAR], problems


# ---------------------------------------------------------------------------------------------------------------
# Output with a byte budget
# ---------------------------------------------------------------------------------------------------------------
class Budget:
    def __init__(self, out: Path, total=20 * 1024 * 1024, per_file=5 * 1024 * 1024):
        self.out, self.total, self.per_file = out, total, per_file
        self.files = {}
        self.refused = []

    def used(self):
        return sum(self.files.values())

    def write(self, name: str, data: bytes) -> bool:
        if len(data) > self.per_file or self.used() + len(data) > self.total:
            self.refused.append({"file": name, "bytes": len(data), "used_before": self.used()})
            return False
        (self.out / name).write_bytes(data)
        self.files[name] = len(data)
        return True


def jsonl_bytes(rows):
    return "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows).encode("utf-8")


def csv_bytes(rows, columns):
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue().encode("utf-8")


def write_sharded(b: Budget, base: str, ext: str, rows, serialize, year_of):
    """One file if it fits under the per-file cap, else one file per year (and per half-year when still too big)."""
    data = serialize(rows)
    if len(data) <= min(b.per_file - 1024, 4 * 1024 * 1024):
        return [base + ext] if b.write(base + ext, data) else []
    by = defaultdict(list)
    for r in rows:
        by[year_of(r)].append(r)
    names = []
    for y in sorted(by):
        d = serialize(by[y])
        if len(d) <= min(b.per_file - 1024, 4 * 1024 * 1024):
            if b.write(f"{base}.{y}{ext}", d):
                names.append(f"{base}.{y}{ext}")
        else:
            half = len(by[y]) // 2
            for k, part in enumerate((by[y][:half], by[y][half:])):
                n = f"{base}.{y}-{k + 1}{ext}"
                if b.write(n, serialize(part)):
                    names.append(n)
    return names


# ---------------------------------------------------------------------------------------------------------------
# Fragments and sources
# ---------------------------------------------------------------------------------------------------------------
def source_record(issue, kind, url, sha, nbytes, retrieved, page_or_item, extra=None):
    rec = {"source_id": f"lsa:{issue}:{kind}", "instrument_ids": [], "url": url, "sha256": sha, "bytes": nbytes,
           "retrieved_utc": retrieved,
           "route": "govinfo_content_pkg_zip" if kind == "zip" else "govinfo_content_pkg_zip_html_member",
           "page_or_item": page_or_item, "text_path": None, "grade": GRADE, "acceptable_as_original": False,
           "role": "lsa_listing", "lsa_issue": issue,
           "notes": "List of CFR Sections Affected, a GPO/OFR listing. It lists the Federal Register page of a "
                    "change; it is not that page and not an order's text. instrument_ids is empty on purpose so "
                    "the claim kit never reads it as an order's own text."}
    if extra:
        rec.update(extra)
    return rec


def fragments_for(row, member_src):
    """later_event_candidates fragments for one Title 3 'Executive Orders' row with a parseable acting instrument."""
    if not row["eo_target"] or not row["acting"] or not row["mechanism"]:
        return []
    out = []
    quote = row.get("_quote") or row["change"]
    short = member_src["page_or_item"].split(" (", 1)[0]
    for actor in row["acting"].split("|"):
        if actor == row["eo_target"]:
            continue
        data = {
            "acting_id": actor, "acting_label": actor, "target_id": row["eo_target"],
            "mechanism": row["mechanism"] if row["mechanism_class"] in ("ending", "modifying", "continuing") else "cross_reference",
            "mechanism_printed": row["mechanism_printed"], "mechanism_class": row["mechanism_class"],
            "qualifier": row["qualifier"], "date_candidate": "",
            "date_basis": "LSA issue month " + row["issue_date"][:7] + " bounds it; the FR page dates it once held",
            "evidence_type": "lsa_title3_entry", "quote": quote, "quote_kind": "verbatim_entry",
            "quote_span": f"{row['span_start']}-{row['span_end']}", "citation_form": "lsa_entry",
            "flags": ["lead_until_fr_page_held"] + (["fr_year_assumed"] if row["year_assumed"] else []),
            "source_id": member_src["source_id"], "source_url": member_src["url"], "source_sha256": member_src["sha256"],
            "page_or_item": short, "located_by": LOCATOR, "fr_ref": row["fr_ref"], "fr_cite": row["fr_cite"],
            "first_issue": row["first_issue"],
        }
        out.append({"instrument_id": row["eo_target"], "kind": "later_event_candidates", "produced_by": "repetita-lsa",
                    "confidence_note": "Machine-read LSA Title 3 entry: a lead, not a finding. The Federal Register page is not held.",
                    "data": [data]})
    return out
