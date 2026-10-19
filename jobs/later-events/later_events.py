"""Later-events job: a candidate graph of later legal events affecting each order.

Two kinds of evidence are turned into EDGES (acting instrument -> target order):

1. The Office of the Federal Register (OFR) executive-order catalog, fetched
   from the documented public API at federalregister.gov/api/v1. Each record
   carries an editorial "disposition_notes" field ("Revoked by: EO 9521,
   February 13, 1945", "Revokes: EO 6119, May 2, 1933 (in part)", ...).
2. The text of later orders (saved by other jobs or earlier stages), scanned
   for operative language such as "Executive Order No. 9876 of May 1, 1948,
   is hereby revoked".

Everything produced here is a LEAD for human review. An editorial note or a
sentence in an order is not a finding of when (or whether) an order stopped
having legal effect. Nothing here changes any provisional status or count.

Standard library only; PDF text extraction uses pypdf when it is installed.
"""
from __future__ import annotations

import bisect
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

JOB_NAME = "later-events"
CUTOFF = "2026-10-14"
USER_AGENT = "EO-afterlife-research/1.0 (owner-run research; contact via repo)"
API_BASE = "https://www.federalregister.gov/api/v1/documents.json"
API_HOSTS = {"www.federalregister.gov", "federalregister.gov"}
API_FIELDS = (   # kept short: the page URL is repeated in every source reference
    "citation", "disposition_notes", "document_number", "executive_order_number",
    "html_url", "pdf_url", "president", "publication_date", "raw_text_url",
    "signing_date", "title",
)
MIN_FULL_CATALOG = 6000          # the full catalog had 6,939 rows in Oct 2026
REQUEST_GAP_SECONDS = 1.1        # at most ~1 request per second
OPUS_ZIP = "releases/opus_stage11_complete/OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip"

MONTHS = ("january february march april may june july august september "
          "october november december").split()
MONTH_RE = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_RE = re.compile(MONTH_RE + r"\.?\s*,?\s*(\d{1,2})\s*,?\s*(\d{4})", re.I)

# Mechanisms that, when not partial, count as a full-revocation candidate.
FULL_END_MECHANISMS = {"revocation", "rescission", "supersession_or_revocation"}
# Order texts that are secondary transcriptions (American Presidency Project pages harvested by
# app-executive-orders, read through jobs/app-transcriptions/output/SOURCES.jsonl). Their "in part" wording is
# recorded as a conflict flag but never withholds a whole-order end stated in an OFR note: a transcription must not
# make a provisional YES order look free of a contrary full-revocation lead.
TRANSCRIPTION_TEXT_EVIDENCE = {"order_text_app_transcriptions"}
DEFAULT_TEXT_JOBS = "fr-originals,app-transcriptions"

EDGE_COLUMNS = [
    "edge_id", "acting_id", "acting_label", "target_id", "target_label", "target_in_universe",
    "mechanism", "qualifier", "date_candidate", "date_basis", "date_flags", "stated_effective_date",
    "evidence_type", "stated_on", "source_id", "source_url", "source_sha256",
    "page_or_item", "note_label", "quote_kind", "quote_span", "quote",
]


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def collapse_ws(text):
    return re.sub(r"[ \t\r\f\v ]+", " ", text or "").strip()


def iso_date(year, month, day):
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except (ValueError, TypeError):
        return None


def month_number(token):
    token = token.lower().rstrip(".")
    for i, name in enumerate(MONTHS, 1):
        if name.startswith(token[:3]):
            return i
    return None


def find_dates(text):
    """All exact 'Month D, YYYY' dates in text as (iso, start, end)."""
    found = []
    for m in DATE_RE.finditer(text or ""):
        month = month_number(m.group(0).split()[0].rstrip(",."))
        iso = iso_date(m.group(2), month, m.group(1)) if month else None
        if iso:
            found.append((iso, m.start(), m.end()))
    return found


def first_date(text):
    dates = find_dates(text)
    return dates[0][0] if dates else None


EFFECTIVE_RE = re.compile(
    r"\beffective\s*,?\s*(?:as\s+of\s+|on\s+|from\s+|at\s+[^,.;]{0,40}?\s*(?:on|,)\s+)?"
    r"(" + MONTH_RE + r"\.?\s*\d{1,2}\s*,\s*\d{4})", re.I)


def stated_effective_date(text):
    """A date written as 'effective <date>' in the text, or ''. It is recorded
    beside (never instead of) the acting instrument's date."""
    m = EFFECTIVE_RE.search(text or "")
    return (first_date(m.group(1)) or "") if m else ""


def eo_id(number, suffix=""):
    """Normalise an order number to the project's id form, e.g. EO:10026A."""
    suffix = (suffix or "").strip().upper().replace("1/2", "½")
    return "EO:%d%s" % (int(number), suffix)


def normalize_catalog_number(raw, title=""):
    """OFR executive_order_number ('7677-A', '11359A', '10571') -> id."""
    if raw is None:
        return None
    value = str(raw).strip()
    m = re.fullmatch(r"0*(\d{1,5})\s*-?\s*([A-Za-z])?", value)
    if not m:
        return None
    suffix = m.group(2) or ""
    # Quirk seen in the catalog: a second record for 10571 whose title begins
    # "-A Assignment of ..." is the separately numbered order 10571-A.
    if not suffix and isinstance(title, str):
        t = re.match(r"\s*-\s*([A-Z])\s", title)
        if t:
            suffix = t.group(1)
    return eo_id(m.group(1), suffix)


def split_top_level(text, sep=";"):
    """Split on sep at parenthesis depth 0."""
    parts, depth, cur = [], 0, []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


# --------------------------------------------------------------------------
# Order-number references in free text / note items
# --------------------------------------------------------------------------

# "EO 9521", "E.O. 12866", "Executive Order 13563", "Executive Order No. 9876",
# "Executive Orders Nos. 9001 and 9002", "EO 325-A", "EO 1182 1/2".
EO_ANCHOR = re.compile(
    r"\b(?:E\.\s?O\.|EO|Ex(?:ecutive|\.)\s+Orders?)\s*(?=(?:Nos?\.?\s*)?\d)", re.I)
NUM_TOKEN = re.compile(
    r"(?:Nos?\.?\s*)?(\d{1,5})(?![\d,]*\s*(?:Stat\b|FR\b|U\.S\.C|CFR\b))"
    r"(\s*-\s*[A-Za-z](?![A-Za-z])|[A-Za-z](?![A-Za-z])|\s*½|\s*-?\s*1/2)?")
OF_DATE = re.compile(r"\s*,?\s*(?:of|dated)\s+(" + MONTH_RE + r"\.?\s*\d{1,2}\s*,\s*\d{4})", re.I)
RANGE_SEP = re.compile(r"\s*(?:-|–|—|through|to)\s*(?=(?:Nos?\.?\s*)?\d)", re.I)
LIST_SEP = re.compile(r"\s*(?:,\s*(?:and|or)\s+|,|\band\b|\bor\b|&)\s*(?=(?:Nos?\.?\s*)?\d)", re.I)
AS_AMENDED = re.compile(r"\s*,?\s*as amended\b", re.I)
MAX_RANGE = 200


def _suffix(raw):
    if not raw:
        return ""
    raw = raw.strip().lstrip("-").strip()
    if raw in ("½", "1/2") or raw.endswith("1/2"):
        return "½"
    return raw.upper()


def eo_references(text):
    """Every order number referenced in text.

    Returns dicts {id, start, end, date (iso or None), in_range} in order.
    Handles lists ("Nos. 9001, 9002 and 9005"), ranges ("9001-9010"),
    letter suffixes ("325-A") and halves ("1182 1/2").
    """
    refs = []
    for anchor in EO_ANCHOR.finditer(text):
        pos = anchor.end()
        prev_num = None
        while True:
            m = NUM_TOKEN.match(text, pos)
            if not m:
                break
            num = int(m.group(1))
            suffix = _suffix(m.group(2))
            # a single letter immediately followed by a word char is not a suffix
            ref = {"id": eo_id(num, suffix), "start": m.start(1), "end": m.end(),
                   "date": None, "in_range": False, "anchor": anchor.start()}
            pos = m.end()
            d = OF_DATE.match(text, pos)
            if d:
                ref["date"] = first_date(d.group(1))
                pos = d.end()
            ref["tail"] = pos
            a = AS_AMENDED.match(text, pos)
            if a:
                pos = a.end()
            refs.append(ref)
            r = RANGE_SEP.match(text, pos)
            if r and not suffix:
                m2 = NUM_TOKEN.match(text, r.end())
                if m2 and not m2.group(2):
                    end_num = int(m2.group(1))
                    if num < end_num <= num + MAX_RANGE:
                        for n in range(num + 1, end_num + 1):
                            refs.append({"id": eo_id(n), "start": m2.start(1),
                                         "end": m2.end(), "date": None,
                                         "in_range": True, "anchor": anchor.start()})
                        pos = m2.end()
                        d = OF_DATE.match(text, pos)
                        if d:
                            pos = d.end()
                        refs[-1]["tail"] = pos
            s = LIST_SEP.match(text, pos)
            if not s:
                break
            pos = s.end()
            prev_num = num
    # de-duplicate overlapping anchors ("Executive Order" then "EO" inside)
    seen, out = set(), []
    for r in refs:
        key = (r["id"], r["start"])
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


# --------------------------------------------------------------------------
# Disposition-note parsing (OFR editorial notes)
# --------------------------------------------------------------------------

LABEL_RE = re.compile(r"(?:^|(?<=[;\n]))[ \t]*;?[ \t]*([A-Z][A-Za-z ()\-]{0,80}?)[ \t]*(:|;)(?=\s|$)", re.M)
OUTBOUND_VERB = re.compile(
    r"^(?:partially |partly |provisionally )?(revokes|amends|supersedes|continues|supplements|"
    r"suspends|reinstates|modifies|rescinds|ratifies|extends|nullifies|terminates|"
    r"abolishes|voids|suspersedes)\b")
MECHANISM_KEYWORDS = [
    (r"supersed\w* or revok", "supersession_or_revocation"),
    ("ceased to function", "ceased_to_function"),
    ("revok", "revocation"),
    ("supersed", "supersession"),
    ("spersed", "supersession"),
    ("amend", "amendment"),
    ("continu", "continuation"),
    ("supplement", "supplementation"),
    ("ratif", "ratification"),
    ("rescind", "rescission"),
    ("reinstat", "reinstatement"),
    ("suspend", "suspension"),
    ("nullif", "nullification"),
    ("authority repeal", "authority_repeal"),
    ("repeal", "repeal"),
    ("extend", "extension"),
    ("modif", "modification"),
    ("abolish", "abolition"),
    ("terminat", "termination"),
    ("expir", "expiration"),
    ("void", "voiding"),
]
METADATA_LABELS = {"effective date", "effective", "federal register correction page and date"}
# Note lines that carry no "Label:" colon. They are tried on EVERY line of a
# note (and on each ';' item), never only on the first line.
SEE_LEAD = re.compile(r"^(See(?:\s+also)?\b|ee(?=\s*:))\s*:?\s*(\S.*)$", re.I)
LEAD_OUT = re.compile(
    r"^((?:partly\s+|partially\s+|provisionally\s+)?(?:revokes|amends|supersedes|modifies|"
    r"continues(?:\s+in\s+effect)?|supplements|suspends|reinstates|rescinds|extends|ratifies)"
    r"(?:\s+in\s+part)?)\s*:?\s+(\S.*)$", re.I)
LEAD_BY = re.compile(
    r"^((?:[A-Za-z][^:;\d]{0,120}?\s+)?(?:revoked|rescinded|superseded(?:\s+or\s+revoked)?|amended|"
    r"modified|continued|nullified|terminated|abolished|extended|suspended|reinstated|"
    r"supplemented|repealed|ratified|voided|continuation(?:\s+and\s+[a-z ]+?)?)"
    r"(?:\s+in\s+\w+)?\s+by)\s*:?\s*(\S.*)$", re.I)
STATUS_LEAD = re.compile(
    r"^((?:This\s+(?:Executive\s+)?order|(?:The\s+)?[A-Z][A-Za-z'’.\- ]{0,100}?)\s+(?:was\s+)?"
    r"(?:ceased\s+to\s+function|terminated|terminates|expired|expires|abolished))\b\s*,?\s*(.*)$")
UNLABELLED_LEAD = LEAD_BY   # kept for backward compatibility of the name


def classify_label(label):
    """Map an OFR note label to (mechanism, direction, label_qualifier).

    direction: 'inbound' (items acted on THIS order), 'outbound' (THIS order
    acted on the items), 'see', 'note', 'status', 'metadata' or 'unrecognized'.
    """
    l = collapse_ws(label).lower().strip(" ;:")
    if l in ("see", "see also", "ee"):
        return "cross_reference", "see", ""
    if l in ("note", "notes"):
        return "editorial_note", "note", ""
    if l in METADATA_LABELS:
        return None, "metadata", ""
    mechanism, pos = None, 0
    for key, mech in MECHANISM_KEYWORDS:
        km = re.search(key, l)
        if km:
            mechanism, pos = mech, km.start()
            break
    if mechanism is None:
        return None, "unrecognized", ""
    quals = []
    if re.search(r"\bin par[a-z]*\b|\bpartially\b|\bpartly\b|\bpart by\b", l):
        quals.append("in part")
    if l.startswith("provisionally"):
        quals.append("provisionally")
    paren = re.findall(r"\(([^)]*)\)", l)
    quals += [p for p in paren if p not in ("in part", "continued")]
    outbound = bool(OUTBOUND_VERB.match(l))
    subject = re.match(r"^(committee|commission|board|council|authority|provisions)\b", l)
    prefix = re.sub(r"\s+(?:was|were|is)$", "", l[:pos].strip(" ,"))
    if subject:
        quals.append("affects the %s" % subject.group(1))
    elif prefix.startswith("this"):
        quals.append("statement about the order itself")
    elif prefix and prefix not in ("partly", "partially", "provisionally", "the") and not outbound:
        quals.append("affects the %s" % re.sub(r"^the\s+", "", prefix))
    if outbound:
        direction = "outbound"
        if "established by" in l:
            quals.append("bodies established by the listed orders")
    elif re.search(r"\bby\b", l):
        direction = "inbound"
    elif re.search(r"(?:^|\s)(?:expired|expires|terminated|terminates|voided|abolished|nullified|"
                   r"ceased to function)$", l):
        direction = "status"
    else:
        direction = "unrecognized"
    return mechanism, direction, "; ".join(quals)


def unlabelled_segment(text, allow_status=True):
    """A note line (or item) without 'Label:' -> (label, body) or (None, text)."""
    s = collapse_ws(text).strip(" ;")
    pats = [SEE_LEAD, LEAD_OUT, LEAD_BY] + ([STATUS_LEAD] if allow_status else [])
    for pat in pats:
        m = pat.match(s)
        if not m:
            continue
        direction = classify_label(m.group(1))[1]
        if direction in ("inbound", "outbound", "see", "status"):
            return m.group(1).strip(), m.group(2).strip(" ;")
    return None, s


def split_note_segments(note):
    """Split one disposition note into (label, body, raw) segments.

    Every newline is a hard segment boundary: a line never continues the
    previous line's list. A line (or the part of a line before its first
    'Label:') that has no colon label is matched against the unlabelled
    grammar (SEE_LEAD, LEAD_OUT, LEAD_BY, STATUS_LEAD); when nothing matches it
    is returned with label None so the caller can log it as unparsed.
    """
    segments = []
    for line in (note or "").replace("\r", "").split("\n"):
        line = collapse_ws(line)
        if not line.strip(" ;"):
            continue
        matches = []
        for m in LABEL_RE.finditer(line):
            label = m.group(1).strip()
            mech, direction, _ = classify_label(label)
            if m.group(2) == ";" and direction in ("unrecognized", "metadata"):
                continue  # an item separator, not a mistyped label
            if direction == "unrecognized" and len(label.split()) > 6:
                continue
            matches.append(m)
        lead = line[:matches[0].start()] if matches else line
        lead = lead.strip(" ;")
        if lead:
            label, body = unlabelled_segment(lead)
            segments.append((label, body, lead))
        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(line)
            body = line[m.end():end].strip(" ;")
            segments.append((m.group(1).strip(), body, line[m.start():end].strip(" ;")))
    return segments


NESTED_RE = re.compile(r"\(\s*which\s+was\s+(\w+(?:\s+in\s+part)?)\s+by\s+([^()]*(?:\([^()]*\)[^()]*)*)\)", re.I)
IN_PART_RE = re.compile(r"\(\s*in\s+part\s*\)|\bin\s+part\b", re.I)
FR_CITE_RE = re.compile(r"\b(\d{1,3})\s+FR\s+(\d{1,6})\b")


def other_actor(item):
    """Identify a non-EO acting/target instrument in a note item."""
    s = collapse_ws(item)
    rules = [
        (r"Public\s+Land\s+Order\s+(?:No\.\s*)?(\d+)", "PLO:%s"),
        (r"Proc(?:lamation|\.)?\.?\s+(?:No\.\s*)?(\d+)", "PROC:%s"),
        (r"(?:Pub(?:lic|\.)\s*L(?:aw|\.)|P\.\s?L\.)\s*(?:No\.\s*)?(\d+\s*[-–]\s*\d+)", "PL:%s"),
        (r"Reorganization\s+Plan\s+(?:No\.\s*)?(\d+\s+of\s+\d{4})", "REORG_PLAN:%s"),
        (r"Presidential\s+Determination\s+(?:No\.\s*)?([\d\-–]+)", "PRES_DETERMINATION:%s"),
        (r"Transfer\s+Order\s+(\d+)", "TRANSFER_ORDER:%s"),
        (r"Canal\s+Zone\s+Order\s+(?:No\.\s*)?(\d+)", "CANAL_ZONE_ORDER:%s"),
    ]
    for pattern, fmt in rules:
        m = re.search(pattern, s, re.I)
        if m:
            return fmt % re.sub(r"\s+", "", m.group(1)).replace("–", "-").replace("of", "-")
    m = re.search(r"\bPLO\s+(\d+)", s)
    if m:
        return "PLO:%s" % m.group(1)
    m = re.match(r"\s*(\d{1,3})\s+Stat\.?\s+(\d{1,5})", s)
    if m:
        return "STAT:%s-%s" % m.groups()
    m = re.match(r"\s*(?:a\s+|the\s+)?treaty\b", s, re.I)
    if m and first_date(s):
        return "TREATY:%s" % first_date(s)
    m = re.search(r"Foreign\s+Service\s+Reg(?:ulation|\.)?\s+([A-Z]-\d+)", s, re.I)
    if m:
        return "FS_REG:%s" % m.group(1).upper()
    d = first_date(s)
    if re.search(r"\b(?:Executive\s+orders?|EO)\s+of\b", s, re.I) and d:
        return "UNNUMBERED_EO:%s" % d
    if re.match(r"(?:Notice)\b", s, re.I) and d:
        return "NOTICE:%s" % d
    if re.match(r"(?:Memo(?:randum|\.)?)\b", s, re.I) and d:
        return "MEMORANDUM:%s" % d
    if re.search(r"\bAct of\b", s) and d:
        return "ACT:%s" % d
    return None


LEADING_FILLER = re.compile(r"\b(?:the|and|also|certain|E\.\s?O\.|EO|Ex(?:ecutive|\.)|orders?|Nos?\.?)\b", re.I)


def parse_item(item, previous_kind=None, require_leading=False):
    """Parse one ';'-separated note item into instrument references.

    Returns a list of {id, label, date, in_part, fr_cite, nested:[...], raw,
    kind, mentions_dropped:[ids]}. With require_leading, an item whose first
    order number comes only after other words ("Proc. 4768 ... Amended by EO
    12371", "Final Rule ... which replaced EO 12173") is taken to be about the
    leading instrument, and the order numbers are logged as dropped mentions.
    """
    raw = collapse_ws(item)
    nested = []
    for nm in NESTED_RE.finditer(raw):
        nested.append({"verb": nm.group(1).lower(), "body": nm.group(2).strip()})
    stripped = NESTED_RE.sub("", raw)
    in_part = bool(IN_PART_RE.search(stripped))
    fr = FR_CITE_RE.search(stripped)
    fr_cite = "%s FR %s" % fr.groups() if fr else ""
    refs = eo_references(stripped)
    dropped = []
    actor_text = stripped
    if refs and require_leading:
        lead_text = stripped[:refs[0]["anchor"]]
        if re.search(r"[A-Za-z]{3,}", LEADING_FILLER.sub(" ", lead_text)):
            dropped = [r["id"] for r in refs]
            refs = []
            actor_text = lead_text
    # Keep only the listed instruments: a later reference joined by words such
    # as "read in conjunction with EO 12333" or "issued under EO X" is a mention.
    listed = []
    for ref in refs:
        if listed:
            gap = stripped[listed[-1]["end"]:ref["start"]]
            gap = DATE_RE.sub(" ", gap)
            gap = FR_CITE_RE.sub(" ", gap)
            gap = re.sub(r"\([^()]*\)", " ", gap)
            gap = re.sub(r"\b(?:E\.\s?O\.|EO|Executive|Orders?|Nos?\.?|and|or|through|to)\b", " ", gap, flags=re.I)
            if re.search(r"[A-Za-z]{2,}", gap):
                dropped += [r["id"] for r in refs[len(listed):]]
                break
        listed.append(ref)
    refs = listed
    out = []
    if refs:
        for i, ref in enumerate(refs):
            nxt = refs[i + 1]["start"] if i + 1 < len(refs) else len(stripped)
            seg = stripped[ref["end"]:nxt]
            d = ref["date"] or first_date(seg)
            out.append({"id": ref["id"], "label": collapse_ws(stripped[max(0, ref["start"] - 3):nxt]).strip(" ,;"),
                        "date": d, "in_part": in_part or bool(IN_PART_RE.search(seg)),
                        "fr_cite": fr_cite, "nested": nested if i == 0 else [], "raw": raw,
                        "kind": "EO", "mentions_dropped": dropped if i == 0 else []})
        return out
    actor = other_actor(actor_text)
    kind = actor.split(":")[0] if actor else None
    if actor is None and previous_kind == "UNNUMBERED_EO" and re.fullmatch(
            r"\s*" + MONTH_RE + r"\.?\s*\d{1,2}\s*,\s*\d{4}\s*", stripped, re.I):
        d = first_date(stripped)
        actor, kind = "UNNUMBERED_EO:%s" % d, "UNNUMBERED_EO"
    out.append({"id": actor, "label": stripped.strip(" ,;"), "date": first_date(actor_text),
                "in_part": in_part, "fr_cite": fr_cite, "nested": nested, "raw": raw,
                "kind": kind or "OTHER", "mentions_dropped": dropped})
    return out


NOTE_MECHANISMS = [
    (r"nullif", "nullification"), (r"\brepeal", "authority_repeal"),
    (r"terminat", "termination"), (r"abolish", "abolition"),
    (r"revok", "revocation"), (r"supersed", "supersession"),
    (r"rescind", "rescission"), (r"suspend", "suspension"),
    (r"expire", "expiration"),
]


def parse_free_note(body, record_id):
    """'Note:' text -> at most one edge candidate (target, actor, mechanism, date)."""
    text = collapse_ws(body)
    mech = "editorial_note"
    for pat, name in NOTE_MECHANISMS:
        if re.search(pat, text, re.I):
            mech = name
            break
    target = record_id
    subj = re.match(r"(?:The authority of\s+)?(?:this Executive order|EO\s+(\d+)(?:-?([A-Z]))?)", text, re.I)
    if subj and subj.group(1):
        target = eo_id(subj.group(1), subj.group(2) or "")
    actor, actor_date = None, None
    by = re.search(r"\bby\b(?: virtue of)?(.*)$", text, re.I)
    if by:
        tail = by.group(1)
        refs = [r for r in eo_references(tail) if r["id"] != target]
        if refs:
            actor = refs[0]["id"]
            near = tail[refs[0]["end"]:refs[0]["end"] + 40]
            actor_date = refs[0]["date"] or first_date(near)
        else:
            actor = other_actor(tail)
            if actor:
                actor_date = first_date(tail)
    basis = "date stated next to the acting instrument in the OFR note" if actor_date else ""
    if not actor:
        actor = other_actor(text)
    return {"target": target, "actor": actor, "date": actor_date, "date_basis": basis,
            "mechanism": mech, "text": text, "stated_effective_date": stated_effective_date(text)}


# --------------------------------------------------------------------------
# Catalog (OFR API) fetch with cache
# --------------------------------------------------------------------------

def api_first_url(per_page):
    pairs = [
        ("conditions[correction]", "0"),
        ("conditions[presidential_document_type]", "executive_order"),
        ("conditions[type][]", "PRESDOCU"),
        ("include_pre_1994_docs", "true"),
        ("order", "executive_order_number"),
        ("per_page", str(per_page)),
    ] + [("fields[]", f) for f in API_FIELDS]
    return API_BASE + "?" + urllib.parse.urlencode(pairs)


class Fetcher:
    """Polite HTTPS GET with on-disk cache (cache key = sha1 of the URL)."""

    def __init__(self, cache_dir, refresh=False, log=print):
        self.cache_dir = Path(cache_dir)
        self.refresh = refresh
        self.log = log
        self.requests_made = 0
        self.cache_hits = 0
        self._last = 0.0

    def get(self, url, allowed_hosts):
        key = hashlib.sha1(url.encode("utf-8")).hexdigest()
        body_path = self.cache_dir / "ofr_api" / (key + ".json")
        meta_path = self.cache_dir / "ofr_api" / (key + ".meta.json")
        if not self.refresh and body_path.is_file() and meta_path.is_file():
            meta = json.loads(meta_path.read_text("utf-8"))
            body = body_path.read_bytes()
            if sha256_bytes(body) == meta.get("sha256"):
                self.cache_hits += 1
                return body, meta
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            raise ValueError("refusing non-allowed URL: %s" % url)
        last_error = None
        for attempt in range(4):
            wait = self._last + REQUEST_GAP_SECONDS - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            self.requests_made += 1
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                           "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=120) as resp:
                    final = urllib.parse.urlsplit(resp.geturl())
                    if final.scheme != "https" or final.hostname not in allowed_hosts:
                        raise ValueError("unexpected redirect to %s (not following; may be a "
                                         "bot check - never bypassed)" % final.hostname)
                    body = resp.read()
                    ctype = resp.headers.get("Content-Type") or ""
                if "json" not in ctype:
                    raise ValueError("response is not JSON (%s)" % ctype)
                meta = {"url": url, "final_url": resp.geturl(), "retrieved_utc": utc_now(),
                        "content_type": ctype, "sha256": sha256_bytes(body), "bytes": len(body)}
                body_path.parent.mkdir(parents=True, exist_ok=True)
                body_path.write_bytes(body)
                meta_path.write_text(json.dumps(meta, indent=1), "utf-8")
                return body, meta
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code not in (429, 500, 502, 503, 504):
                    break
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                delay = int(retry_after) if retry_after and retry_after.isdigit() else 10 * (attempt + 1)
                self.log("  HTTP %s; waiting %ss before retry" % (exc.code, delay))
                time.sleep(min(delay, 120))
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                last_error = exc
                time.sleep(5 * (attempt + 1))
        raise RuntimeError("fetch failed for %s: %s" % (url, last_error))


def fetch_catalog(fetcher, limit=None, log=print):
    """Fetch the OFR EO catalog page by page.

    Returns (records, pages) where each record carries '_page' (index into
    pages) and pages hold the custody metadata of every page fetched.
    """
    per_page = 1000 if not limit else max(20, min(1000, limit))
    url = api_first_url(per_page)
    records, pages, expected = [], [], None
    while url:
        body, meta = fetcher.get(url, API_HOSTS)
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise ValueError("OFR API page has no results array")
        expected = payload.get("count", expected)
        page_index = len(pages)
        pages.append(meta)
        for rec in payload["results"]:
            if isinstance(rec, dict):
                rec = dict(rec)
                rec["_page"] = page_index
                records.append(rec)
        log("  catalog page %d: %d records (total so far %d of %s)" % (
            page_index + 1, len(payload["results"]), len(records), expected))
        if limit and len(records) >= limit:
            break
        nxt = payload.get("next_page_url")
        if nxt:
            nxt_parts = urllib.parse.urlsplit(nxt)
            if nxt_parts.scheme != "https" or nxt_parts.hostname not in API_HOSTS:
                raise ValueError("next_page_url points outside federalregister.gov")
        url = nxt
        if len(pages) > 40:
            raise ValueError("too many catalog pages; stopping")
    if not limit:
        if expected is None or len(records) != expected or len(records) < MIN_FULL_CATALOG:
            raise ValueError("partial OFR catalog: %d of %s records" % (len(records), expected))
    return (records[:limit] if limit else records), pages


# --------------------------------------------------------------------------
# Catalog -> index + note edges
# --------------------------------------------------------------------------

def build_index(records):
    """Normalise catalog records; drop corrections; keep duplicates visible."""
    index = defaultdict(list)
    rows = []
    for rec in records:
        title = rec.get("title") or ""
        docnum = rec.get("document_number") or ""
        if title.strip().lower() == "correction" or str(docnum).startswith(("C1-", "C2-", "R1-")):
            continue
        ident = normalize_catalog_number(rec.get("executive_order_number"), title)
        if not ident:
            continue
        signing = rec.get("signing_date") or ""
        if signing and not re.fullmatch(r"\d{4}-\d\d-\d\d", signing):
            signing = ""
        row = {"id": ident, "record": rec, "signing_date": signing,
               "post_cutoff": bool(signing and signing > CUTOFF)}
        index[ident].append(row)
        rows.append(row)
    return index, rows


def signing_date_of(index, ident):
    rows = [r for r in index.get(ident, []) if r["signing_date"] and not r["post_cutoff"]]
    dates = {r["signing_date"] for r in rows}
    return dates.pop() if len(dates) == 1 else None


def record_page_item(rec):
    bits = ["OFR API record executive_order_number=%s" % rec.get("executive_order_number")]
    if rec.get("citation"):
        bits.append("citation %s" % rec["citation"])
    if rec.get("document_number"):
        bits.append("document_number %s" % rec["document_number"])
    bits.append("field disposition_notes")
    return "; ".join(bits)


def note_edges(row, index, page_source):
    """Turn one catalog record's disposition note into edge dicts.

    Every quote is a verbatim (whitespace-collapsed) substring of the note:
    the item text for list items, or the whole segment for status and free-text
    notes. The note label the item sat under is kept in note_label.
    """
    rec = row["record"]
    rid = row["id"]
    note = rec.get("disposition_notes") or ""
    edges, unparsed = [], []
    if not note.strip() or row["post_cutoff"]:
        return edges, unparsed
    base = {"source_id": page_source["source_id"], "source_url": page_source["url"],
            "source_sha256": page_source["sha256"], "page_or_item": record_page_item(rec)}

    def add(acting, acting_label, target, mechanism, qualifier, date_candidate,
            date_basis, flags, evidence_type, stated_on, quote, target_label="",
            note_label="", quote_kind="verbatim_note_item", stated_eff=""):
        e = dict(base)
        e.update({"acting_id": acting or "", "acting_label": acting_label or "",
                  "target_id": target or "", "target_label": target_label or "",
                  "mechanism": mechanism,
                  "qualifier": qualifier, "date_candidate": date_candidate or "",
                  "date_basis": date_basis, "date_flags": flags,
                  "stated_effective_date": stated_eff or "",
                  "evidence_type": evidence_type, "stated_on": stated_on,
                  "note_label": note_label, "quote_kind": quote_kind, "quote_span": "",
                  "quote": quote})
        edges.append(e)

    for label, body, raw in split_note_segments(note):
        if label is None:
            unparsed.append({"instrument_id": rid, "segment": raw, "reason": "no label"})
            continue
        mechanism, direction, lqual = classify_label(label)
        if direction == "status":
            actor = other_actor(body)
            d = first_date(body)
            add(actor, "" if actor else "(no acting instrument stated)", rid, mechanism,
                "; ".join(q for q in ["status statement in OFR note", lqual] if q), d,
                "date stated in the OFR note" if d else "no date in data", "",
                "ofr_note_freetext", rid, raw, note_label=label, quote_kind="verbatim_note_segment",
                stated_eff=stated_effective_date(body))
            continue
        if direction == "metadata":
            continue
        if direction == "unrecognized":
            unparsed.append({"instrument_id": rid, "segment": raw, "reason": "unrecognized label"})
            continue
        if direction == "note":
            fn = parse_free_note(body, rid)
            ad, basis = fn["date"], fn["date_basis"] or "no date in data"
            if fn["actor"] and fn["actor"].startswith("EO:") and not ad:
                ad = signing_date_of(index, fn["actor"])
                basis = "acting order signing_date from OFR catalog" if ad else basis
            add(fn["actor"], "" if fn["actor"] else "(not identified; see quote)", fn["target"],
                fn["mechanism"], "free-text editorial note", ad, basis, "", "ofr_note_freetext", rid, raw,
                note_label=label, quote_kind="verbatim_note_segment",
                stated_eff=fn["stated_effective_date"])
            continue
        items = split_top_level(body)
        prev_kind = None
        cur_label, cur_mech, cur_dir, cur_lqual = label, mechanism, direction, lqual
        for item_no, item in enumerate(items):
            # an item can start a new unlabelled clause ("Revoked by: EO 1; Amended by EO 2")
            sub_label, sub_body = unlabelled_segment(item, allow_status=False)
            item_text = item
            if sub_label is not None:
                m2, d2, q2 = classify_label(sub_label)
                if d2 in ("inbound", "outbound", "see"):
                    cur_label, cur_mech, cur_dir, cur_lqual = sub_label, m2, d2, q2
                    item_text = sub_body
            quote = collapse_ws(item).strip(" ;")
            if item_no == 0 and quote and quote in raw:
                # the label and the first item are contiguous in the note: quote both
                quote = raw[:raw.index(quote) + len(quote)]
            for ref in parse_item(item_text, prev_kind, require_leading=cur_dir in ("inbound", "outbound")):
                prev_kind = ref["kind"]
                for mention in ref.get("mentions_dropped") or []:
                    unparsed.append({"instrument_id": rid, "segment": quote,
                                     "reason": "order %s named after other words; read as a mention, "
                                               "not as a listed instrument" % mention})
                quals = [q for q in [cur_lqual, "in part" if ref["in_part"] and "in part" not in cur_lqual else ""] if q]
                qualifier = "; ".join(quals)
                flags = []
                if not ref["id"]:
                    flags.append("instrument_not_identified(label_only)")
                if cur_dir in ("inbound", "see"):
                    acting, target = ref["id"], rid
                    d = ref["date"]
                    basis = "date stated next to the acting instrument in the OFR note"
                    idx_date = signing_date_of(index, acting) if acting and acting.startswith("EO:") else None
                    if d and idx_date and d != idx_date:
                        flags.append("note_states_%s_but_catalog_signing_date_is_%s" % (d, idx_date))
                        d, basis = idx_date, "acting order signing_date from OFR catalog (note date differs)"
                    if not d and idx_date:
                        d, basis = idx_date, "acting order signing_date from OFR catalog"
                    if not d:
                        basis = "no date in data"
                    if cur_dir == "see":
                        basis = "date of the referenced instrument (a cross-reference, not an event date)"
                    add(acting, ref["label"], target, cur_mech, qualifier, d, basis,
                        ";".join(flags), "ofr_note_on_target" if cur_dir == "inbound" else "ofr_note_see_reference",
                        rid, quote, note_label=cur_label)
                else:  # outbound: this record acted on the item
                    acting, target = rid, ref["id"]
                    d = row["signing_date"] or None
                    basis = "acting order signing_date from OFR catalog" if d else "no date in data"
                    tgt_idx = signing_date_of(index, target) if target and target.startswith("EO:") else None
                    if ref["date"] and tgt_idx and ref["date"] != tgt_idx:
                        flags.append("note_target_date_%s_differs_from_catalog_%s" % (ref["date"], tgt_idx))
                    add(acting, "", target, cur_mech, qualifier, d, basis,
                        ";".join(flags), "ofr_note_on_acting", rid, quote, target_label=ref["label"],
                        note_label=cur_label)
                for nest in ref["nested"]:
                    nmech = "revocation"
                    for key, mech in MECHANISM_KEYWORDS:
                        if re.search(key, nest["verb"]):
                            nmech = mech
                            break
                    for nref in parse_item(nest["body"]):
                        if not nref["id"] or not ref["id"]:
                            continue
                        add(nref["id"], nref["label"], ref["id"], nmech,
                            "in part" if "in part" in nest["verb"] or nref["in_part"] else "",
                            nref["date"], "date stated in nested OFR note" if nref["date"] else "no date in data",
                            "", "ofr_note_nested", rid, quote, note_label=cur_label)
    return edges, unparsed


# --------------------------------------------------------------------------
# Text scanning (operative language in later orders)
# --------------------------------------------------------------------------

PASSIVE_VERB = re.compile(
    r"\b(?:is|are|be|been|shall\s+be|hereby)\s+(?:hereby\s+)?(?:further\s+)?(?:also\s+)?"
    r"(revoked|rescinded|superseded|amended|suspended|reinstated|terminated|canceled|"
    r"cancelled|abolished|modified|continued|extended|supplemented|nullified)\b", re.I)
ACTIVE_VERB = re.compile(
    r"\b(?:I\s+hereby|hereby|this\s+order(?:\s+hereby)?)\s+"
    r"(revoke|rescind|supersede|amend|suspend|reinstate|terminate|revokes|rescinds|"
    r"supersedes|amends|suspends|reinstates|terminates)\b", re.I)
VERB_MECH = {
    "revok": "revocation", "rescind": "rescission", "supersed": "supersession",
    "amend": "amendment", "suspend": "suspension", "reinstat": "reinstatement",
    "terminat": "termination", "cancel": "revocation", "abolish": "abolition",
    "modif": "modification", "continu": "continuation", "extend": "extension",
    "supplement": "supplementation", "nullif": "nullification",
}
# "Section 3 of", "Sections 5 (b), 7, and 8 of", "Paragraph 6 of the said"
SEC_TOKEN = r"(?:[\w.\-]+|\(\w{1,4}\))(?:\s*\(\w{1,4}\))*"
PART_BEFORE = re.compile(
    r"((?:(?:Sec(?:tion)?s?\.?|Subsections?|Paragraphs?|Parts?|Subparagraphs?|Clauses?|Subdivisions?|"
    r"Articles?|Subparts?)\s+" + SEC_TOKEN +
    r"(?:\s*(?:,\s*(?:and\b|or\b)?|\band\b|\bor\b|\bthrough\b|\bto\b)\s*" + SEC_TOKEN + r")*"
    r"\s*(?:,\s*)?(?:of\s+)?(?:the\s+(?:said\s+)?)?)+)\s*$", re.I)
# "The prohibitions contained in", "the provisions of", "the authority granted by"
PROVISIONS_BEFORE = re.compile(
    r"\b(prohibitions?|provisions?|authorit(?:y|ies)|restrictions?|requirements?|delegations?|"
    r"functions?|amendments?|designations?|portions?|so\s+much|that\s+part|those\s+parts|"
    r"(?:first|second|third|last)\s+sentence|sentences?|subparts?|items?|annex(?:es)?)\b[^.;:]{0,80}?"
    r"\b(?:contained\s+in|of|granted\s+(?:by|in|under)|in|under|set\s+(?:forth|out)\s+in|made\s+(?:by|in)|"
    r"issued\s+(?:by|under)|prescribed\s+(?:by|in)|conferred\s+(?:by|in))\s+(?:the\s+(?:said\s+)?)?$", re.I)
ANCHOR_TAIL = re.compile(r"(?:E\.\s?O\.|EO|Ex(?:ecutive|\.)\s+Orders?)\s*(?:Nos?\.?\s*)?$", re.I)
EXTENT_RE = re.compile(r"\b(in part|insofar as[^.;]{0,160}|in so far as[^.;]{0,160}|so far as[^.;]{0,160}|"
                       r"to the extent[^.;]{0,160}|except[^.;]{0,160}|with respect to[^.;]{0,160}|"
                       r"as (?:it|they) (?:relates?|appl(?:y|ies))[^.;]{0,160}|"
                       r"(?:conflicting|inconsistent)[^.;]{0,120}|as to (?:the|such)[^.;]{0,120})", re.I)
BODY_MECHANISMS = {"abolition", "termination"}
ESTABLISHED_BY = re.compile(r"\b(?:established|created|constituted)\s+(?:by|under|pursuant to)\s*$", re.I)
NEGATION_BEFORE = re.compile(r"\b(?:not|never|nor)\b(?:\s+\w+){0,2}\s*$", re.I)
CONSTRUED_RE = re.compile(r"\bnothing\b[^.;]{0,200}?\b(?:construed|deemed|interpreted)\b", re.I)
COMPOUND_AFTER = re.compile(
    r"\s*,?\s*(?:or|and/or)\s+(?:hereby\s+)?(?:further\s+)?(revoked|rescinded|superseded|amended|"
    r"modified|suspended|revoke|amend|modify|supersede)\b", re.I)
CLAUSE_CONJ = re.compile(
    r",\s*(?:and|but|or)\b|;|\band\s+(?=(?:the\s+(?:said\s+)?)?(?:E\.\s?O\.|EO\b|Ex(?:ecutive|\.)\s+Orders?|"
    r"Sec|Part|Para|Subsec))", re.I)


AS_AMENDED_LEAD = re.compile(r",?\s*\(?\s*as\s+(?:previously\s+)?amended(?:\s*,)?(?:\s+by\s+(?:the\s+said\s+)?)?", re.I)
AMEND_LIST_CONT = re.compile(
    r"\s*,?\s*(?:and|or)\s+(?:by\s+)?(?:the\s+(?:said\s+)?)?(?=(?:E\.\s?O\.|EO\b|Ex(?:ecutive|\.)\s+Orders?))", re.I)
SINGULAR_VERB_AHEAD = re.compile(r"\s*,?\s*(?:is|was|has\s+been|shall\s+be)\b", re.I)
OPEN_PAREN = re.compile(r"\s*\(")


def skip_parenthetical(s, pos):
    """If a balanced '( ... )' starts at pos (after spaces), return the index after it."""
    m = OPEN_PAREN.match(s, pos)
    if not m:
        return pos
    depth = 0
    for i in range(m.end() - 1, len(s)):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
    return pos   # unbalanced: do not skip


def remove_as_amended(sentence):
    """Blank 'as amended [by Executive Order(s) Nos. A, B and C of <date>] (title)'
    phrases, so the amending orders named there are not mistaken for targets.
    'as amended by EO A (title), and EO B (title), is further amended' blanks B
    too, but only when a singular verb follows (with 'are revoked', B may be a
    second target)."""
    out, pos = [], 0
    for m in AS_AMENDED_LEAD.finditer(sentence):
        if m.start() < pos:
            continue
        end = m.end()
        refs = eo_references(sentence[m.end():m.end() + 1200])
        if refs and refs[0]["anchor"] <= 2:
            first_anchor = refs[0]["anchor"]
            same = [r for r in refs if r["anchor"] == first_anchor]
            end = m.end() + max(r.get("tail", r["end"]) for r in same)
            probe, chain = end, []
            while True:
                p = skip_parenthetical(sentence, probe)
                if p == probe:
                    break               # only extend across parenthetical titles
                c = AMEND_LIST_CONT.match(sentence, p)
                if not c:
                    break
                sub = eo_references(sentence[c.end():c.end() + 600])
                if not sub or sub[0]["anchor"] != 0:
                    break
                grp = [r for r in sub if r["anchor"] == 0]
                probe = c.end() + max(r.get("tail", r["end"]) for r in grp)
                chain.append(probe)
            if chain and SINGULAR_VERB_AHEAD.match(sentence, skip_parenthetical(sentence, chain[-1])):
                end = chain[-1]
            end = skip_parenthetical(sentence, end)   # the amending order's own title
        out.append(sentence[pos:m.start()])
        out.append(" " * (end - m.start()))   # keep offsets stable
        pos = end
    out.append(sentence[pos:])
    return "".join(out)


DASH_TRANS = str.maketrans({c: "-" for c in "‐‑‒–—―−"})
DELETE_RE = re.compile(r"­|(?<=\w)[-‐‑][ \t]*\r?\n\s*(?=\w)")


def clean_with_map(text):
    """Normalise dashes, drop soft hyphens and join 'word-\\nword' line breaks.

    Returns (cleaned, offset_map); map_offset(offset_map, i) gives the index in
    the ORIGINAL text of cleaned[i], so quotes can be cut from the original."""
    spans = [(m.start(), m.end()) for m in DELETE_RE.finditer(text)]
    if not spans:
        return text.translate(DASH_TRANS), None
    pieces, cstarts, ostarts = [], [], []
    pos = clen = 0
    for s, e in spans:
        if s > pos:
            pieces.append(text[pos:s])
            cstarts.append(clen)
            ostarts.append(pos)
            clen += s - pos
        pos = max(pos, e)
    if pos < len(text):
        pieces.append(text[pos:])
        cstarts.append(clen)
        ostarts.append(pos)
    return "".join(pieces).translate(DASH_TRANS), (cstarts, ostarts)


def map_offset(cmap, i):
    if cmap is None:
        return i
    cstarts, ostarts = cmap
    k = bisect.bisect_right(cstarts, i) - 1
    if k < 0:
        return i
    return ostarts[k] + (i - cstarts[k])


def clean_text(text):
    return clean_with_map(text)[0]


APP_MARK = "The American Presidency Project"
APP_START = re.compile(r"President of the United States:?[ \t]*\s*\n[^\n]*\d{4}[^\n]*\n")
APP_FOOTER = "Online by Gerhard Peters"


def app_body(text):
    """For an American Presidency Project page, the document body between the
    president/years block and the 'Online by Gerhard Peters ...' citation line.
    Returns (body, offset_of_body_in_text, cut_applied)."""
    if APP_MARK not in text[:6000]:
        return text, 0, False
    start = 0
    m = APP_START.search(text)
    if m:
        start = m.end()
    end = len(text)
    j = text.find(APP_FOOTER, start)
    if j >= 0:
        nl = text.rfind("\n", start, j)
        end = nl if nl >= 0 else j
    if start == 0 and end == len(text):
        return text, 0, False
    return text[start:end], start, True


# a sentence ends at ". X" / "; X", or at a blank line (paragraph break) unless the
# paragraph ends with ":" "," "-" or the next starts like a list item "(1)" / "8744" / lowercase
SENT_BOUND = re.compile(r"(?<=[.;])\s+(?=[A-Z(\"'])|(?<=[^\s:,\-])[ \t]*\n[ \t]*\n\s*(?![(\da-z])")
MAX_SENTENCE = 1500


def split_sentence_spans(text, begin=0, end=None):
    """(start, end) spans of sentences in text[begin:end]; long runs are cut at 1500 chars."""
    end = len(text) if end is None else end
    spans, pos = [], begin
    for m in SENT_BOUND.finditer(text, begin, end):
        spans.append((pos, m.start()))
        pos = m.end()
    spans.append((pos, end))
    out = []
    for s, t in spans:
        while s < t and text[s].isspace():
            s += 1
        while t > s and text[t - 1].isspace():
            t -= 1
        while t - s > MAX_SENTENCE:
            out.append((s, s + MAX_SENTENCE))
            s += MAX_SENTENCE
        if t > s:
            out.append((s, t))
    return out


def split_sentences(text):
    return [re.sub(r"\s+", " ", text[s:t]).strip() for s, t in split_sentence_spans(text)]


# A heading line: "Executive Order 12944 of December 28, 1994", "Executive Order 12683-Prescribing ..."
# or the number alone on its line. "Executive Order No. 8000 is hereby revoked." is not a heading.
HEADING_RE = re.compile(r"(?im)^[ \t]*(?:TITLE:[ \t]*)?(?:executive\s+order|E\.\s?O\.)\s*(?:No\.?\s*)?(\d{1,5})(?:-?([A-Z])\b)?"
                        r"(?=[ \t]+of[ \t]+" + MONTH_RE + r"\.?[ \t]*\d{1,2}[ \t]*,[ \t]*\d{4}[ \t]*(?:\r?\n|$)"
                        r"|[ \t]*-|[ \t]*\r?\n|[ \t]*$)")


def segment_bounds(text, acting_id):
    """(begin, end, located): the part of text that belongs to the acting order."""
    heads = [(m.start(), eo_id(m.group(1), m.group(2) or "")) for m in HEADING_RE.finditer(text)]
    starts = [i for i, (pos, ident) in enumerate(heads) if ident == acting_id]
    if not starts:
        return 0, len(text), False
    first = starts[0]
    begin = heads[first][0]
    end = len(text)
    for pos, ident in heads[first + 1:]:
        if ident != acting_id:
            end = pos
            break
    return begin, end, True


def segment_for_order(text, acting_id):
    """Return (segment, located) - the part of text that belongs to the acting order."""
    b, e, located = segment_bounds(text, acting_id)
    return text[b:e], located


SUBJECT_WINDOW = 600
LIST_LIKE_BEFORE = re.compile(r"(?:^|,|;|:|\band\b|\bor\b|\(\w{1,4}\)|\b\d{1,2}\.|\bof\b|\bthat\b|\btogether with\b)"
                              r"\s*(?:the\s+(?:said\s+)?)?$", re.I)
STRONG_LIST_BEFORE = re.compile(r"(?:,\s*and|;|\(\w{1,4}\))\s*(?:the\s+(?:said\s+)?)?$", re.I)


def listed_only(work, refs):
    """Keep the leading list of order references; drop ones that only appear in a
    descriptive phrase ("Executive Order 10077, which ... revokes Executive Order 108-A").
    The first reference is always kept; a later one is kept only when the words
    just before it are list-like (",", "and", "(b)", "of" ...) and no relative
    clause ("which", "that") intervenes, unless it follows ", and" / ";" / "(b)"."""
    kept, kept_anchors = [], set()
    for r in refs:
        anchor = r.get("anchor", r["start"])
        if not kept or anchor in kept_anchors:
            kept.append(r)
            kept_anchors.add(anchor)
            continue
        before = work[max(0, anchor - 40):anchor]
        between = work[kept[-1]["end"]:anchor]
        relative = re.search(r"\b(?:which|whereby|that)\b", between, re.I)
        if (LIST_LIKE_BEFORE.search(before) and not relative) or STRONG_LIST_BEFORE.search(before):
            kept.append(r)
            kept_anchors.add(anchor)
    return kept


def _base_and_suffix(ident):
    m = re.fullmatch(r"EO:(\d+)(.*)", ident or "")
    return (m.group(1), m.group(2)) if m else (None, None)


def scan_sentence(sentence, acting_id):
    """Find operative later-event language in one sentence.

    Returns list of {target, mechanism, qualifier, date_stated, stated_effective_date}.
    """
    hits = []
    work = remove_as_amended(sentence)
    passive = list(PASSIVE_VERB.finditer(work))
    active = list(ACTIVE_VERB.finditer(work))
    if not passive and not active:
        return hits
    # the acting order's own number (title line, "this order") is never a target
    refs = [r for r in eo_references(work) if r["id"] != acting_id]
    if not refs:
        return hits
    extent = EXTENT_RE.search(work)
    extent_q = collapse_ws(extent.group(1)) if extent else ""
    eff = stated_effective_date(work)
    verbs = sorted(passive + active, key=lambda v: v.start())
    acting_base, acting_suffix = _base_and_suffix(acting_id)
    used = set()

    def mech_for(verb):
        v = verb.lower()
        for key, mech in VERB_MECH.items():
            if v.startswith(key):
                return mech
        return "unrecognized"

    def clause_start_for(verb):
        cs = max(work.rfind(";", 0, verb.start()), work.rfind(":", 0, verb.start()))
        prev = [v for v in verbs if v.end() <= verb.start()]
        if prev:   # "EO 13000 is amended, and EO 13001 is revoked": 13000 is not revoked
            c = CLAUSE_CONJ.search(work, prev[-1].end(), verb.start())
            if c:
                cs = max(cs, c.start())
        return cs

    def next_verb_start(verb):
        return min([v.start() for v in verbs if v.start() >= verb.end()] + [len(work)])

    def negated(verb, clause_start):
        if NEGATION_BEFORE.search(work[max(0, verb.start() - 30):verb.start()]):
            return True
        return bool(CONSTRUED_RE.search(work, clause_start + 1, verb.start()))

    def provisions_qual(ref):
        before = ANCHOR_TAIL.sub("", work[max(0, ref["start"] - 160):ref["start"]])
        m = PROVISIONS_BEFORE.search(before)
        return ("partial wording: %s" % collapse_ws(m.group(0)).strip()) if m else ""

    def qual_for(ref, mech, extras):
        before = ANCHOR_TAIL.sub("", work[max(0, ref["start"] - 140):ref["start"]])
        quals = []
        pm = PART_BEFORE.search(before)
        if pm:
            part = collapse_ws(pm.group(1))
            part = re.sub(r"(?:\s*,)?(?:\s+of)?(?:\s+the(?:\s+said)?)?\s*$", "", part)
            quals.append(part)
        pq = provisions_qual(ref)
        if pq:
            quals.append(pq)
        if ESTABLISHED_BY.search(before):
            quals.append("acts on a body established by the order (not necessarily the order itself)")
        if ref["in_range"]:
            quals.append("number expanded from a range")
        if mech in BODY_MECHANISMS:
            quals.append("abolition/termination wording: may concern a body, function or suspension, not the order itself")
        quals += [x for x in extras if x]
        return "; ".join(dict.fromkeys(q for q in quals if q))

    def same_number_other_suffix(ident):
        base, suffix = _base_and_suffix(ident)
        return base is not None and base == acting_base and suffix != acting_suffix

    def add_hit(r, mech, qualifier):
        used.add((r["id"], mech))
        hits.append({"target": r["id"], "mechanism": mech, "qualifier": qualifier,
                     "date_stated": r["date"], "stated_effective_date": eff})

    for verb in passive:
        mech = mech_for(verb.group(1))
        cs = clause_start_for(verb)
        if negated(verb, cs):
            continue
        comp = COMPOUND_AFTER.match(work, verb.end())
        compound_q = ("compound wording '%s or %s': mechanism uncertain" % (
            verb.group(1).lower(), comp.group(1).lower())) if comp else ""
        # subject = refs before the verb, within the same clause
        subject = [r for r in refs if cs < r["start"] < verb.start()]
        # "The following Executive orders are hereby revoked: ..." -> list after
        if not subject and not comp and re.search(r"following", work[max(0, verb.start() - 80):verb.start()], re.I):
            nv = next_verb_start(verb)
            subject = [r for r in refs if verb.end() < r["start"] < nv]
        subject = listed_only(work, [r for r in subject if verb.start() - r["start"] < SUBJECT_WINDOW
                                     or r["start"] > verb.end()])
        lead_q = provisions_qual(subject[0]) if subject else ""
        for r in subject:
            if r["id"] == acting_id or (r["id"], mech) in used:
                continue
            if same_number_other_suffix(r["id"]) and not (0 <= verb.start() - r["end"] <= 80):
                continue
            add_hit(r, mech, qual_for(r, mech, [lead_q, compound_q, extent_q]))
    for verb in active:
        mech = mech_for(verb.group(1))
        if NEGATION_BEFORE.search(work[max(0, verb.start() - 30):verb.start()]):
            continue
        comp = COMPOUND_AFTER.match(work, verb.end())
        compound_q = ("compound wording '%s or %s': mechanism uncertain" % (
            verb.group(1).lower(), comp.group(1).lower())) if comp else ""
        nxt = next_verb_start(verb)
        objects = listed_only(work, [r for r in refs if verb.end() <= r["start"] < nxt])
        lead_q = provisions_qual(objects[0]) if objects else ""
        for r in objects:
            if r["id"] == acting_id or (r["id"], mech) in used:
                continue
            if same_number_other_suffix(r["id"]) and not (0 <= r["start"] - verb.end() <= 80):
                continue
            add_hit(r, mech, qual_for(r, mech, [lead_q, compound_q, extent_q]))
    return hits


def scan_text_detail(text, acting_id):
    """Scan an order's text. Quotes are cut from the ORIGINAL text (whitespace
    collapsed only), with their character span in that text."""
    body, body_off, app_cut = app_body(text)
    cleaned, cmap = clean_with_map(body)
    b, e, located = segment_bounds(cleaned, acting_id)
    results = []
    for s, t in split_sentence_spans(cleaned, b, e):
        sentence = re.sub(r"\s+", " ", cleaned[s:t]).strip()
        hits = scan_sentence(sentence, acting_id)
        if not hits:
            continue
        os_, oe = map_offset(cmap, s), map_offset(cmap, t - 1) + 1
        quote = re.sub(r"\s+", " ", body[os_:oe]).strip()
        span = "chars %d-%d of the scanned text" % (body_off + os_, body_off + oe)
        for h in hits:
            h["quote"] = quote
            h["quote_span"] = span
            h["quote_kind"] = ("verbatim_text_sentence" if t - s < MAX_SENTENCE
                               else "verbatim_text_chunk(1500-char cut of a longer run)")
            results.append(h)
    return {"hits": results, "located": located, "app_body_cut": app_cut}


def scan_text(text, acting_id):
    """Scan an order's text; returns (hits_with_quotes, segment_located)."""
    d = scan_text_detail(text, acting_id)
    return d["hits"], d["located"]


# --------------------------------------------------------------------------
# Text inputs
# --------------------------------------------------------------------------

def int_or_none(value):
    """Byte counts copied from other files: int when numeric, else None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def is_lfs_pointer(path):
    try:
        with open(path, "rb") as fh:
            return fh.read(60).startswith(b"version https://git-lfs")
    except OSError:
        return True


def text_docs_from_job_sources(repo, jobs=("fr-originals",), log=print):
    """Texts saved by other jobs, read through their SOURCES.jsonl records."""
    docs = []
    for job in jobs:
        out = repo / "jobs" / job / "output"
        src = out / "SOURCES.jsonl"
        if not src.is_file():
            log("  jobs/%s/output/SOURCES.jsonl not present yet (built in parallel); skipped" % job)
            continue
        for line in src.read_text("utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ids = rec.get("instrument_ids") or []
            tp = rec.get("text_path")
            if len(ids) != 1 or not tp or not str(ids[0]).startswith("EO:"):
                continue
            path = out / tp
            if not path.is_file():
                continue
            docs.append({"acting_id": ids[0], "text": path.read_text("utf-8", errors="replace"),
                         "source": {"source_id": rec.get("source_id") or "", "url": rec.get("url") or "",
                                    "sha256": rec.get("sha256") or "", "page_or_item": rec.get("page_or_item") or "",
                                    "bytes": int_or_none(rec.get("bytes")), "content_type": rec.get("content_type") or "",
                                    "retrieved_utc": rec.get("retrieved_utc") or "",
                                    "route": "jobs/%s SOURCES.jsonl text_path" % job,
                                    "cache_path": rec.get("cache_path"),
                                    "text_path_foreign": "jobs/%s/output/%s" % (job, tp)},
                         "evidence_type": "order_text_%s" % job.replace("-", "_")})
    return docs


def pdf_text(path):
    try:
        import logging
        import pypdf  # noqa: WPS433 (optional dependency)
        logging.getLogger("pypdf").setLevel(logging.ERROR)
    except ImportError:
        return None
    try:
        reader = pypdf.PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as exc:  # malformed PDFs must not stop the job
        return "__PDF_ERROR__ %s" % exc


def text_docs_from_stage21_pdfs(repo, log=print):
    folder = repo / "research/stage21/original_sources"
    custody = folder / "CASE_ORIGINAL_SOURCE_CUSTODY.csv"
    docs = []
    if not custody.is_file():
        log("  research/stage21/original_sources not available; skipped")
        return docs
    try:
        import pypdf  # noqa: F401
    except ImportError:
        log("  pypdf not installed: Stage 21 PDFs skipped (pip install -r requirements.txt)")
        return docs
    with custody.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rel = row.get("source_repository_path") or ""
            path = repo / rel
            if not rel or not path.is_file() or is_lfs_pointer(path):
                continue
            data = path.read_bytes()
            digest = sha256_bytes(data)
            if row.get("sha256_source_bytes_if_present") and digest != row["sha256_source_bytes_if_present"]:
                log("  WARNING: %s sha256 differs from custody record; skipped" % rel)
                continue
            text = pdf_text(path)
            if not text or text.startswith("__PDF_ERROR__"):
                log("  could not extract text from %s" % rel)
                continue
            docs.append({"acting_id": row["instrument_id"], "text": text,
                         "source": {"source_id": "stage21pdf:%s" % row["instrument_id"],
                                    "url": row.get("official_PDF_candidate_URL") or "",
                                    "sha256": digest, "bytes": len(data),
                                    "content_type": "application/pdf",
                                    "retrieved_utc": row.get("attempted_utc") or "",
                                    "route": "research/stage21/original_sources custody CSV + pypdf text",
                                    "page_or_item": "whole PDF (govinfo FR document)",
                                    "cache_path": rel},
                         "evidence_type": "order_text_govinfo_pdf"})
    return docs


OPUS_TEXT_NAME = re.compile(
    r"^(?:app|rapp|r_app|fr(?:_\d{4}-\d\d-\d\d)?)_eo[_-]?(\d{3,5})([a-z])?"
    r"(?:_\d{4}-\d\d-\d\d)?(?:\.(?:n|norm|body))?\.txt$", re.I)


SEARCH_URL = re.compile(r"/search|[?&](?:q|query|conditions%5Bterm%5D|conditions\[term\])=|/api/", re.I)


def text_names_order(text, acting_id, window=6000):
    """Identity check: the acting order's own number must appear near the top."""
    return any(r["id"] == acting_id for r in eo_references(clean_text(text[:window])))


def url_names_order(url, acting_id):
    """The source URL names the order, e.g. .../executive-order-10557-approving-...;
    a URL naming 4359-a does not identify order 4359."""
    m = re.fullmatch(r"EO:(\d+)([A-Z½]?)", acting_id)
    if not m:
        return False
    num, suffix = m.groups()
    if suffix:
        pattern = r"(?<!\d)%s[-_]?%s(?![a-z])" % (num, suffix.lower())
    else:
        pattern = r"(?<!\d)%s(?!\d)(?![-_][a-z](?:[-_.]|$))" % num
    return bool(re.search(pattern, url.lower()))


ERROR_PHRASES = re.compile(
    r"\b404\b\s*[-|:]?\s*(?:error|(?:page\s+)?not\s+found)|\bpage\s+not\s+found\b|"
    r"^\s*not\s+found\b|\bfile\s+not\s+found\b|\bthe\s+requested\s+url\s+was\s+not\s+found", re.I)
BLOCK_PHRASES = re.compile(
    r"ip\s+address\s+(?:has\s+been\s+|is\s+|was\s+)?(?:temporarily\s+)?blocked|\bcaptcha\b|"
    r"\baccess\s+denied\b|\brequest\s+(?:was\s+|has\s+been\s+)?rejected\b|are\s+you\s+a\s+robot|"
    r"verify\s+(?:that\s+)?you\s+are\s+(?:a\s+)?human|unusual\s+traffic|too\s+many\s+requests|"
    r"attention\s+required|enable\s+javascript\s+and\s+cookies", re.I)


def error_page_reason(text):
    """Why a saved text is not an order text (error, block or bot page), or ''."""
    flat = re.sub(r"\s+", " ", text or "").strip()
    if len(flat) < 200:
        return "near-empty text"
    if flat[:1] in "{[":
        return "JSON, not a document text"
    if ERROR_PHRASES.search(flat[:600]):
        return "error page"
    if BLOCK_PHRASES.search(flat[:1500]):
        return "block or bot-check page"
    return ""


def looks_like_error_page(text):
    return bool(error_page_reason(text))


def text_docs_from_opus(repo, limit=None, log=print):
    zpath = repo / OPUS_ZIP
    docs = []
    if not zpath.is_file():
        log("  Opus release zip not present; skipped")
        return docs
    if is_lfs_pointer(zpath):
        log("  Opus release zip is a Git LFS pointer (not downloaded); skipped")
        return docs
    zf = zipfile.ZipFile(zpath)
    names = set(zf.namelist())
    chosen = {}
    for name in sorted(names):
        base = name.rsplit("/", 1)[-1]
        m = OPUS_TEXT_NAME.match(base)
        if not m:
            continue
        acting = eo_id(m.group(1), m.group(2) or "")
        stem = name[:-4]
        meta_name = None
        for cand in (stem + ".meta.json", re.sub(r"\.(n|norm|body)$", "", stem) + ".meta.json"):
            if cand in names:
                meta_name = cand
                break
        if not meta_name:
            continue
        try:
            meta = json.loads(zf.read(meta_name).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        url = meta.get("final_url") or meta.get("url") or ""
        if not url.startswith("https://") or SEARCH_URL.search(url):
            continue  # search-result pages are ABOUT an order, not its text
        # one text per acting order + original URL (prefer plain .txt variants)
        key = (acting, url)
        rank = 0 if re.search(r"\.(?:n|norm|body)\.txt$", base) is None else 1
        if key not in chosen or rank < chosen[key][0]:
            chosen[key] = (rank, name, meta_name, meta, url)
    skipped = Counter()
    for (acting, url), (rank, name, meta_name, meta, _) in sorted(chosen.items()):
        if limit and len(docs) >= limit:
            break
        raw = zf.read(name)
        text = raw.decode("utf-8", errors="replace")
        reason = error_page_reason(text)
        if reason:
            skipped[reason] += 1
            continue
        if not (text_names_order(text, acting) or url_names_order(url, acting)):
            skipped["neither the text nor its URL names the acting order"] += 1
            continue
        host = urllib.parse.urlsplit(url).hostname or ""
        grade = "order_text_opus_official_copy" if host.endswith(("govinfo.gov", "federalregister.gov",
                                                                  "archives.gov", "loc.gov")) else "order_text_opus_mirror"
        docs.append({"acting_id": acting, "text": text,
                     "source": {"source_id": "opus:%s" % name,   # full member path: unique
                                "url": url, "sha256": meta.get("sha256") or "",
                                "bytes": int_or_none(meta.get("bytes")),
                                "content_type": meta.get("content_type") or "",
                                "retrieved_utc": meta.get("retrieved_utc") or "",
                                "route": "Opus Stage 11 release text extraction (%s)" % meta.get("text_extraction", "?"),
                                "page_or_item": "text extracted from %s" % url,
                                "cache_path": "%s!%s" % (OPUS_ZIP, name),
                                "text_sha256_this_job": sha256_bytes(raw),
                                "opus_meta_text_sha256": meta.get("text_sha256") or ""},
                     "evidence_type": grade})
    if skipped:
        log("  Opus texts skipped: %s" % dict(skipped))
    return docs


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------

def load_universe(repo, log=print):
    p = repo / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
    if not p.is_file():
        log("  universe file missing; target_in_universe left blank")
        return None
    with p.open(newline="", encoding="utf-8") as fh:
        return {r["id"] for r in csv.DictReader(fh)}


def load_decided(repo, log=print):
    p = repo / "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv"
    if not p.is_file():
        log("  decided-case file missing; decided counts left at 0")
        return {}
    with p.open(newline="", encoding="utf-8") as fh:
        return {r["instrument_id"]: r.get("provisional_substantive_status", "") for r in csv.DictReader(fh)}


def text_edges(doc, index):
    acting = doc["acting_id"]
    src = doc["source"]
    detail = scan_text_detail(doc["text"], acting)
    hits, located = detail["hits"], detail["located"]
    d = signing_date_of(index, acting)
    edges = []
    for h in hits:
        flags = [] if located else ["acting_order_heading_not_found_in_text(whole text scanned)"]
        if h.get("date_stated") and h["target"].startswith("EO:"):
            idx = signing_date_of(index, h["target"])
            if idx and idx != h["date_stated"]:
                flags.append("text_target_date_%s_differs_from_catalog_%s" % (h["date_stated"], idx))
        if h.get("stated_effective_date"):
            flags.append("sentence_states_effective_date_%s" % h["stated_effective_date"])
        edges.append({"acting_id": acting, "acting_label": "", "target_id": h["target"], "target_label": "",
                      "mechanism": h["mechanism"], "qualifier": h["qualifier"],
                      "date_candidate": d or "",
                      "date_basis": "acting order signing_date from OFR catalog" if d else "no date in data",
                      "date_flags": ";".join(flags),
                      "stated_effective_date": h.get("stated_effective_date") or "",
                      "evidence_type": doc["evidence_type"],
                      "stated_on": acting, "source_id": src["source_id"], "source_url": src["url"],
                      "source_sha256": src["sha256"], "page_or_item": src.get("page_or_item") or "",
                      "note_label": "", "quote_kind": h["quote_kind"], "quote_span": h["quote_span"],
                      "quote": h["quote"]})
    doc["_app_body_cut"] = detail["app_body_cut"]
    return edges, located, len(hits)


def finalize_edges(edges, universe):
    """Drop post-cutoff and self edges, add ids and universe flags."""
    kept, excluded = [], Counter()
    seen = set()
    for e in edges:
        if e["date_candidate"] and e["date_candidate"] > CUTOFF:
            excluded["date_after_cutoff"] += 1
            continue
        if e["acting_id"] and e["acting_id"] == e["target_id"]:
            excluded["self_reference"] += 1
            continue
        key = (e["acting_id"], e["target_id"], e["mechanism"], e["qualifier"], e["evidence_type"],
               e["source_id"], e["stated_on"], collapse_ws(e["quote"]).lower())
        if key in seen:
            excluded["duplicate"] += 1
            continue
        seen.add(key)
        e["target_in_universe"] = "" if universe is None else ("yes" if e["target_id"] in universe else "no")
        e["edge_id"] = "LE-" + hashlib.sha1("|".join(key).encode("utf-8")).hexdigest()[:12]
        kept.append(e)
    kept.sort(key=lambda e: (e["target_id"], e["date_candidate"] or "9999", e["acting_id"], e["edge_id"]))
    return kept, excluded


PARTIAL_RE = re.compile(
    r"in part|section|sec\.|subsection|paragraph|\bparts?\b|clause|insofar|in so far|so far as|extent|"
    r"except|with respect|as (?:it|they) relat|appl(?:y|ies)|provisionally|body established|"
    r"affects the|bodies established|range|not the order itself|partial|compound|uncertain|"
    r"status statement|statement about|\(.*\)", re.I)


def is_partial(qualifier):
    """Any qualifier at all (scope words, parentheses, ranges) means 'not a full end'."""
    return bool(qualifier and PARTIAL_RE.search(qualifier))


def build_fragments(edges):
    """Group edges by target -> later_event_candidates (+ whole_order_end_candidates).

    A full-mechanism group (revocation, rescission, 'superseded or revoked',
    no qualifier) becomes a whole_order_end item only when
      - no other edge for the same actor and target says the action was partial
        (else flag full_and_partial_evidence_conflict), and
      - it is stated in an OFR note, or an OFR note corroborates a full end by the
        same actor (else flag text_only_unverified).
    Withheld items stay in later_event_candidates with the flag.

    Returns (fragments, stats).
    """
    by_target = defaultdict(list)
    for e in edges:
        if e["target_id"].startswith("EO:"):
            by_target[e["target_id"]].append(e)
    fragments = []
    stats = Counter()
    scope_mechanisms = FULL_END_MECHANISMS | {"supersession"}
    for target in sorted(by_target):
        partial_full = defaultdict(list)   # actor -> edge ids saying "in part"/section/...
        partial_transcription = defaultdict(list)  # the same, from transcription texts only
        note_full = set()                  # actors with an unqualified full end in an OFR note
        groups = defaultdict(list)
        for e in by_target[target]:
            actor = e["acting_id"] or e["acting_label"]
            groups[(actor, e["mechanism"], e["qualifier"])].append(e)
            if e["mechanism"] in scope_mechanisms and is_partial(e["qualifier"]):
                if e["evidence_type"] in TRANSCRIPTION_TEXT_EVIDENCE:
                    partial_transcription[actor].append(e["edge_id"])
                else:
                    partial_full[actor].append(e["edge_id"])
            elif (e["mechanism"] in FULL_END_MECHANISMS and not is_partial(e["qualifier"])
                  and e["evidence_type"].startswith("ofr_note")):
                note_full.add(actor)
        events, end_items, sources = [], [], {}
        for (actor, mech, qual), es in sorted(groups.items(), key=lambda kv: (
                min((x["date_candidate"] or "9999") for x in kv[1]), kv[0])):
            dates = sorted({x["date_candidate"] for x in es if x["date_candidate"]})
            refs, positions = [], []
            for x in es:
                ref = {"url": x["source_url"], "sha256": x["source_sha256"], "page_or_item": x["page_or_item"]}
                key = (ref["url"], ref["sha256"], ref["page_or_item"])
                if key not in sources:
                    sources[key] = (len(sources), ref)
                if sources[key][0] not in positions:
                    positions.append(sources[key][0])
                    refs.append(ref)
            flags = sorted({f for x in es for f in x["date_flags"].split(";") if f})
            ev = {"date_candidate": dates[0] if len(dates) == 1 else None,
                  "date_candidates_conflicting": dates if len(dates) > 1 else [],
                  "date_basis": sorted({x["date_basis"] for x in es}),
                  "stated_effective_date_candidates": sorted({x["stated_effective_date"] for x in es
                                                              if x.get("stated_effective_date")}),
                  "actor": actor, "mechanism": mech, "qualifier": qual,
                  "evidence_types": sorted({x["evidence_type"] for x in es}),
                  "edge_ids": sorted(x["edge_id"] for x in es),
                  "source": refs[0], "all_source_positions": positions,
                  "quote": es[0]["quote"], "quote_kind": es[0].get("quote_kind") or "",
                  "flags": flags,
                  "status": "CANDIDATE_UNVERIFIED"}
            if mech in FULL_END_MECHANISMS and not is_partial(qual):
                text_only = all(x["evidence_type"].startswith("order_text") for x in es) and actor not in note_full
                if partial_full.get(actor):
                    ev["flags"] = sorted(set(ev["flags"]) | {"full_and_partial_evidence_conflict"})
                    ev["conflicting_edge_ids"] = sorted(set(partial_full[actor]))
                    stats["withheld_full_and_partial_evidence_conflict"] += 1
                elif text_only:
                    ev["flags"] = sorted(set(ev["flags"]) | {"text_only_unverified"})
                    stats["withheld_text_only_unverified"] += 1
                else:
                    if partial_transcription.get(actor):
                        ev["flags"] = sorted(set(ev["flags"]) | {"transcription_text_says_partial_end_kept"})
                        ev["conflicting_transcription_edge_ids"] = sorted(set(partial_transcription[actor]))
                        stats["kept_despite_transcription_partial_evidence"] += 1
                    end_items.append(ev)
            events.append(ev)
        all_sources = [ref for _, ref in sorted(sources.values(), key=lambda pr: pr[0])]
        fragments.append({
            "instrument_id": target, "kind": "later_event_candidates", "data": events,
            "sources": all_sources,
            "confidence_note": ("Machine-extracted leads from OFR editorial disposition notes and/or "
                                "operative sentences in later order texts. date_candidate is the acting "
                                "instrument's stated or catalog signing date, not a proven effective "
                                "date; a date written as 'effective <date>' is listed separately in "
                                "stated_effective_date_candidates. 'cross_reference' items are 'See:' "
                                "pointers only. Items flagged full_and_partial_evidence_conflict or "
                                "text_only_unverified were NOT offered as whole-order ends. Every item "
                                "needs a human to read the cited source."),
            "produced_by": JOB_NAME})
        if not end_items:
            continue
        revivals = [{"date_candidate": ev["date_candidate"], "actor": ev["actor"],
                     "mechanism": ev["mechanism"], "qualifier": ev["qualifier"]}
                    for ev in events if ev["mechanism"] in ("reinstatement", "ratification")]
        # whole-order-end fragments carry only the sources their own items cite
        used = []
        for ev in end_items:
            for pos in ev["all_source_positions"]:
                if pos not in used:
                    used.append(pos)
        remap = {old: new for new, old in enumerate(used)}
        ends = []
        for ev in end_items:
            ends.append({
                "date_candidate": ev["date_candidate"],
                "date_candidates_conflicting": ev["date_candidates_conflicting"],
                "date_basis": ev["date_basis"],
                "stated_effective_date_candidates": ev["stated_effective_date_candidates"],
                "actor": ev["actor"], "mechanism": ev["mechanism"], "qualifier": ev["qualifier"],
                "evidence_types": ev["evidence_types"], "edge_ids": ev["edge_ids"], "flags": ev["flags"],
                "source": ev["source"],
                "all_source_positions": [remap[p] for p in ev["all_source_positions"]],
                "quote": ev["quote"], "quote_kind": ev["quote_kind"],
                "later_reinstatement_candidates": [
                    r for r in revivals
                    if not ev["date_candidate"] or not r["date_candidate"] or r["date_candidate"] >= ev["date_candidate"]],
                "status": "CANDIDATE_UNVERIFIED"})
        fragments.append({
            "instrument_id": target, "kind": "whole_order_end_candidates", "data": ends,
            "sources": [all_sources[p] for p in used],
            "confidence_note": ("An unqualified revocation/rescission ('superseded or revoked') stated in "
                                "an OFR editorial note (possibly also in an order text), with no "
                                "'in part'/section/provision wording for the same acting instrument "
                                "anywhere in the data. This is a CANDIDATE only: the note may be wrong, "
                                "the order (or parts) may have ceased earlier for other reasons, the "
                                "revocation may carry savings clauses, and date_candidate is the "
                                "acting instrument's date, not necessarily its effective date."),
            "produced_by": JOB_NAME})
    return fragments, stats


def write_csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


CATALOG_COLUMNS = ["id", "executive_order_number_raw", "signing_date", "publication_date", "citation",
                   "document_number", "president", "title", "html_url", "pdf_url", "raw_text_url",
                   "disposition_notes", "post_cutoff", "api_page_source_id"]


def build_outputs(out_dir, catalog_rows, index, pages_sources, text_docs, universe, decided,
                  extra_summary=None, log=print):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    edges, unparsed = [], []
    for row in catalog_rows:
        page_src = pages_sources[row["record"]["_page"]]
        e, u = note_edges(row, index, page_src)
        edges += e
        unparsed += u
    scan_log = []
    sources = list(pages_sources)
    for doc in text_docs:
        e, located, n = text_edges(doc, index)
        edges += e
        scan_log.append({"acting_id": doc["acting_id"], "source_id": doc["source"]["source_id"],
                         "evidence_type": doc["evidence_type"], "url": doc["source"]["url"],
                         "acting_heading_located": "yes" if located else "no",
                         "app_body_cut": "yes" if doc.get("_app_body_cut") else "no",
                         "candidate_hits": n, "text_chars": len(doc["text"])})
        s = doc["source"]
        notes = "acting-order text scanned for operative later-event language"
        if s.get("bytes") is None:
            notes += "; original byte count unknown (not recorded as an integer by the source record)"
        if s.get("text_sha256_this_job"):
            notes += ("; sha256 is of the original bytes as recorded by Opus (not re-verified here); "
                      "extracted-text sha256 %s" % s["text_sha256_this_job"])
        if s.get("text_path_foreign"):
            notes += "; text at %s" % s["text_path_foreign"]
        sources.append({"source_id": s["source_id"], "instrument_ids": [doc["acting_id"]],
                        "url": s["url"], "sha256": s["sha256"], "bytes": s.get("bytes"),
                        "content_type": s.get("content_type") or "",
                        "retrieved_utc": s.get("retrieved_utc") or "", "route": s["route"],
                        "page_or_item": s.get("page_or_item") or "", "text_path": None,
                        "cache_path": s.get("cache_path"), "notes": notes})
    kept, excluded = finalize_edges(edges, universe)
    fragments, frag_stats = build_fragments(kept)

    # catalog index (compact, committed) ------------------------------------
    cat_out = []
    for row in catalog_rows:
        rec = row["record"]
        cat_out.append({"id": row["id"], "executive_order_number_raw": rec.get("executive_order_number"),
                        "signing_date": row["signing_date"], "publication_date": rec.get("publication_date") or "",
                        "citation": rec.get("citation") or "", "document_number": rec.get("document_number") or "",
                        "president": (rec.get("president") or {}).get("name", "") if isinstance(rec.get("president"), dict) else "",
                        "title": rec.get("title") or "", "html_url": rec.get("html_url") or "",
                        "pdf_url": rec.get("pdf_url") or "", "raw_text_url": rec.get("raw_text_url") or "",
                        "disposition_notes": collapse_ws((rec.get("disposition_notes") or "").replace("\n", " | ")),
                        "post_cutoff": "yes" if row["post_cutoff"] else "no",
                        "api_page_source_id": pages_sources[rec["_page"]]["source_id"]})

    # conflict leads for the counterevidence step ---------------------------
    conflicts = []
    for frag in fragments:
        if frag["kind"] != "whole_order_end_candidates":
            continue
        status = decided.get(frag["instrument_id"])
        if status == "yes":
            first = sorted(frag["data"], key=lambda x: x["date_candidate"] or "9999")[0]
            conflicts.append({"instrument_id": frag["instrument_id"], "provisional_status": status,
                              "lead": "provisional YES but a full revocation candidate exists",
                              "earliest_candidate_date": first["date_candidate"] or "",
                              "actor": first["actor"], "mechanism": first["mechanism"],
                              "evidence_types": "|".join(first["evidence_types"]),
                              "later_reinstatement_candidates": "; ".join(dict.fromkeys(
                                  "%s %s %s" % (r["actor"], r["mechanism"], r["date_candidate"] or "")
                                  for e in frag["data"] for r in e.get("later_reinstatement_candidates", []))),
                              "quote": first["quote"][:300]})
    # orders whose decided status is "no" but where nothing ends them in the data
    ending_targets = {f["instrument_id"] for f in fragments if f["kind"] == "whole_order_end_candidates"}

    write_csv(out_dir / "EDGES.csv", kept, EDGE_COLUMNS)
    write_jsonl(out_dir / "FRAGMENTS.jsonl", fragments)
    write_jsonl(out_dir / "SOURCES.jsonl", sources)
    write_csv(out_dir / "CATALOG_INDEX.csv", cat_out, CATALOG_COLUMNS)
    write_csv(out_dir / "UNPARSED_NOTE_SEGMENTS.csv", unparsed, ["instrument_id", "reason", "segment"])
    write_csv(out_dir / "TEXT_SCAN_LOG.csv", scan_log,
              ["acting_id", "source_id", "evidence_type", "url", "acting_heading_located",
               "app_body_cut", "candidate_hits", "text_chars"])
    write_csv(out_dir / "COUNTEREVIDENCE_LEADS.csv", conflicts,
              ["instrument_id", "provisional_status", "lead", "earliest_candidate_date", "actor",
               "mechanism", "evidence_types", "later_reinstatement_candidates", "quote"])

    targets_any = {e["target_id"] for e in kept}
    targets_event = {e["target_id"] for e in kept if e["mechanism"] != "cross_reference"}
    decided_ids = set(decided)
    summary = {
        "job": JOB_NAME,
        "generated_utc": utc_now(),
        "legal_cutoff": CUTOFF,
        "catalog_records_used": len(catalog_rows),
        "catalog_records_with_notes": sum(1 for r in catalog_rows if (r["record"].get("disposition_notes") or "").strip()),
        "catalog_records_post_cutoff_ignored": sum(1 for r in catalog_rows if r["post_cutoff"]),
        "text_documents_scanned": len(text_docs),
        "text_documents_by_evidence_type": dict(Counter(d["evidence_type"] for d in text_docs)),
        "edges": len(kept),
        "edges_by_mechanism": dict(sorted(Counter(e["mechanism"] for e in kept).items())),
        "edges_by_evidence_type": dict(sorted(Counter(e["evidence_type"] for e in kept).items())),
        "edges_excluded": dict(excluded),
        "edges_with_date_flags": sum(1 for e in kept if e["date_flags"]),
        "edges_without_date": sum(1 for e in kept if not e["date_candidate"]),
        "unparsed_note_segments": len(unparsed),
        "unparsed_note_segments_by_reason": dict(sorted(Counter(
            u["reason"] if not u["reason"].startswith("order ") else "order named after other words (mention)"
            for u in unparsed).items())),
        "edges_by_quote_kind": dict(sorted(Counter(e.get("quote_kind") or "" for e in kept).items())),
        "edges_with_stated_effective_date": sum(1 for e in kept if e.get("stated_effective_date")),
        "full_end_items_withheld_from_whole_order_end": dict(sorted(frag_stats.items())),
        "target_orders_with_any_edge": len(targets_any),
        "target_orders_with_event_edge_excluding_see": len(targets_event),
        "orders_with_whole_order_end_candidate": len(ending_targets),
        "source_records": len(sources),
        "source_ids_unique": len({x["source_id"] for x in sources}) == len(sources),
        "fragments_by_kind": dict(Counter(f["kind"] for f in fragments)),
        "decided_orders_total": len(decided_ids),
        "decided_orders_with_any_candidate": len(decided_ids & targets_any),
        "decided_orders_with_event_candidate_excluding_see": len(decided_ids & targets_event),
        "decided_orders_with_whole_order_end_candidate": len(decided_ids & ending_targets),
        "decided_yes_with_full_revocation_candidate": len(conflicts),
        "decided_no_with_full_revocation_candidate": sum(1 for i in ending_targets if decided.get(i) == "no"),
        "legal_conclusions": 0,
        "statuses_changed": 0,
    }
    if extra_summary:
        summary.update(extra_summary)
    (out_dir / "SUMMARY.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", "utf-8")
    return summary


def page_sources_from(pages, records_per_page):
    out = []
    for i, meta in enumerate(pages):
        out.append({"source_id": "ofr-api-page:%s" % meta["sha256"][:16],
                    "instrument_ids": sorted(records_per_page.get(i, [])),
                    "url": meta["url"], "sha256": meta["sha256"], "bytes": meta["bytes"],
                    "content_type": meta.get("content_type") or "",
                    "retrieved_utc": meta.get("retrieved_utc") or "",
                    "route": "federalregister.gov API v1 documents.json (executive orders, include_pre_1994_docs), page %d" % (i + 1),
                    "page_or_item": "API JSON page %d" % (i + 1),
                    "text_path": None,
                    "cache_path": "ofr_api/%s.json" % hashlib.sha1(meta["url"].encode("utf-8")).hexdigest(),
                    "notes": ("OFR catalog page; disposition_notes are editorial cross-references, "
                              "not legal findings. The API is dynamic: a re-fetch may differ byte-for-byte; "
                              "the cached copy is the custody copy.")})
    return out


def text_inputs_present(repo, extra_jobs):
    """Which text inputs this machine had. GitHub runs normally lack the Opus zip
    (a Git LFS pointer there), so GitHub and PC outputs differ; this records which."""
    zpath = repo / OPUS_ZIP
    opus = "missing" if not zpath.is_file() else ("lfs_pointer_not_downloaded" if is_lfs_pointer(zpath) else "present")
    try:
        import pypdf
        pypdf_version = getattr(pypdf, "__version__", "installed")
    except ImportError:
        pypdf_version = "not installed"
    return {
        "opus_release_zip": opus,
        "stage21_custody_csv": (repo / "research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv").is_file(),
        "pypdf": pypdf_version,
        "other_job_sources_jsonl": {j: (repo / "jobs" / j / "output" / "SOURCES.jsonl").is_file() for j in extra_jobs},
        "running_on_github_actions": os.environ.get("GITHUB_ACTIONS") == "true",
        "platform": sys.platform,
    }


def main():
    repo =Path(os.environ.get("REPO_ROOT", ".")).resolve()
    out_dir = Path(os.environ.get("OUTPUT_DIR") or (repo / "jobs" / JOB_NAME / "output")).resolve()
    limit = int(os.environ["JOB_LIMIT"]) if os.environ.get("JOB_LIMIT", "").strip() else None
    cache_dir = Path(os.environ.get("JOB_CACHE_DIR") or (out_dir.parent / (JOB_NAME + "-cache"))).resolve()
    refresh = os.environ.get("LATER_EVENTS_REFRESH", "") == "1"
    extra_jobs = [j for j in os.environ.get("LATER_EVENTS_TEXT_JOBS", DEFAULT_TEXT_JOBS).split(",") if j.strip()]
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    print("later-events: repo=%s output=%s cache=%s limit=%s" % (repo, out_dir, cache_dir, limit))

    errors = []
    fetcher = Fetcher(cache_dir, refresh=refresh)
    print("Step 1: OFR executive-order catalog (federalregister.gov API)")
    try:
        records, pages = fetch_catalog(fetcher, limit=limit)
    except Exception as exc:  # keep going with texts; report failure at the end
        errors.append("catalog fetch failed: %s" % exc)
        print("  ERROR: %s" % exc)
        records, pages = [], []
    index, catalog_rows = build_index(records)
    per_page = defaultdict(list)
    for row in catalog_rows:
        per_page[row["record"]["_page"]].append(row["id"])
    pages_sources = page_sources_from(pages, per_page)

    print("Step 2: saved order texts")
    if (Path(os.environ.get("JOB_DIR", Path(__file__).parent)) / "PULL_OPUS_LFS").is_file() or \
            os.environ.get("LATER_EVENTS_PULL_OPUS_LFS") == "1":
        zpath = repo / OPUS_ZIP
        if is_lfs_pointer(zpath):
            print("  pulling Opus release zip from Git LFS (about 208 MB)")
            subprocess.run(["git", "lfs", "pull", "--include", OPUS_ZIP], cwd=repo, check=False)
    docs = text_docs_from_job_sources(repo, extra_jobs)
    docs += text_docs_from_stage21_pdfs(repo)
    opus = text_docs_from_opus(repo, limit=limit)
    docs += opus
    if limit:
        # keep the sample small but representative of every text source
        by_type = defaultdict(list)
        for d in docs:
            by_type[d["evidence_type"]].append(d)
        docs = [d for group in by_type.values() for d in group[:limit]]
    print("  %d text documents to scan: %s" % (len(docs), dict(Counter(d["evidence_type"] for d in docs))))

    universe = load_universe(repo)
    decided = load_decided(repo)
    print("Step 3: building edges and fragments")
    summary = build_outputs(out_dir, catalog_rows, index, pages_sources, docs, universe, decided,
                            extra_summary={"network_requests": fetcher.requests_made,
                                           "cache_hits": fetcher.cache_hits,
                                           "job_limit": limit, "errors": errors,
                                           "catalog_complete": bool(records) and not limit,
                                           "text_inputs_on_this_machine": text_inputs_present(repo, extra_jobs)})
    print()
    print("Summary (all items are CANDIDATES for human review, not legal findings):")
    print("  catalog records read: %d (%d with editorial notes); text documents scanned: %d" % (
        summary["catalog_records_used"], summary["catalog_records_with_notes"], summary["text_documents_scanned"]))
    print("  candidate edges: %d; by mechanism: %s" % (summary["edges"], summary["edges_by_mechanism"]))
    print("  by evidence type: %s" % summary["edges_by_evidence_type"])
    print("  orders with at least one candidate: %d; with a full-revocation candidate: %d" % (
        summary["target_orders_with_any_edge"], summary["orders_with_whole_order_end_candidate"]))
    print("  of the %d decided orders: %d have a candidate (%d excluding 'See' pointers); %d have a full-revocation candidate" % (
        summary["decided_orders_total"], summary["decided_orders_with_any_candidate"],
        summary["decided_orders_with_event_candidate_excluding_see"],
        summary["decided_orders_with_whole_order_end_candidate"]))
    print("  provisional YES orders with a full-revocation candidate (counterevidence leads): %d" %
          summary["decided_yes_with_full_revocation_candidate"])
    print("  network requests: %d (cache hits %d)" % (fetcher.requests_made, fetcher.cache_hits))
    if errors:
        print("ERRORS: %s" % errors)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
