"""Find citations embedded in prose (PANIZZI: the clearing of the source bottleneck).

A queue line such as "Pub. L. 94-412, National Emergencies Act, sec. 101(a),
90 Stat. 1255 (Sept. 14, 1976); status of Proclamation 2914" is not a bare
citation, so fetch_ladder.parse_citation (which needs the WHOLE string to be a
citation) gave it no official route and the ladder answered "no_route" without
a single request. This module scans such text for every embedded Statutes at
Large, Public Law, Federal Register, U.S. Code, CFR and Reorganization Plan
cite, in the order they appear, and returns each as a canonical bare citation
that parse_citation understands. ladder_queue then turns each into its own
work item, so the existing official routes (govinfo link service, uscode.house.gov,
eCFR) are used for each.

Pure text functions: no network, no file access. A cite found here is a LEAD for
fetching the cited document. It does not say what the document establishes.
"""
from __future__ import annotations

import re

MAX_CITES_PER_LINE = 6          # keeps one long sentence from spending the whole request budget
MAX_FR_VOLUME = 91              # 2026 = volume 91
MAX_STAT_VOLUME = 140
MAX_CONGRESS = 119
MAX_USC_TITLE = 54
MAX_CFR_TITLE = 50

_NUM = r"(\d{1,3})"
STAT_RE = re.compile(r"(?<![\d.])" + _NUM + r"\s*Stat(?![A-Za-z])\.?\s*(\d{1,5})", re.I)
# "Pub. L. 98-525", "Public Law93-531", "P.L.96-88"
PLAW_DASH_RE = re.compile(r"(?<![A-Za-z])(?:Pub(?:lic)?\.?\s*L(?:aw|\.)?|P\.\s*L\.)\s*(?:No\.\s*)?(\d{2,3})\s*[-–]\s*(\d{1,4})(?!\d)", re.I)
# "Public Law 724, 79th Congress", "Pub. L. 453, 83d Cong."
PLAW_CONG_RE = re.compile(r"(?<![A-Za-z])Pub(?:lic)?\.?\s*L(?:aw|\.)?\s*(?:No\.\s*)?(\d{1,4}),?\s*(\d{1,3})\s*(?:st|nd|rd|th|d)\s*Cong", re.I)
FR_RE = re.compile(r"(?<![\d.])(\d{1,2})\s*F\.?\s*R\.?\s*(\d{1,6})(?![\d])", re.I)
USC_RE = re.compile(r"(?<![\d.])(\d{1,2})\s*U\.?\s*S\.?\s*C\.?\s*(?:§+\s*)?(\d+[A-Za-z]*(?:-\d+[A-Za-z]*)?)", re.I)
CFR_RE = re.compile(r"(?<![\d.])(\d{1,2})\s*C\.?\s*F\.?\s*R\.?\s*(?:Parts?\s*|§+\s*)?(\d+(?:-\d+)?)(?:\.(\d+[A-Za-z0-9]*))?", re.I)
RP_RE = re.compile(r"Reorg(?:anization|\.)\s*Plan\s+No\.?\s*(\d+)\s+of\s+(\d{4})", re.I)
EO_MENTION_RE = re.compile(r"(?:\bEO|\bE\.\s*O\.|Executive\s+Order|Ex\.\s*Ord\.)\s*(?:No\.?\s*)?(\d{3,5})(?!\d)", re.I)


def eo_numbers(text: str):
    """Executive order numbers mentioned in the text ('EO 12616', 'Ex. Ord. No. 13883')."""
    return [m.group(1) for m in EO_MENTION_RE.finditer(text or "")]


def _hits(text):
    out = []
    for m in STAT_RE.finditer(text):
        v, p = int(m.group(1)), int(m.group(2))
        if 1 <= v <= MAX_STAT_VOLUME and p >= 1:
            out.append((m.start(), "STAT", f"{v} Stat. {p}", {"volume": v, "page": p}))
    for m in PLAW_DASH_RE.finditer(text):
        c, n = int(m.group(1)), int(m.group(2))
        if 1 <= c <= MAX_CONGRESS and n >= 1:
            out.append((m.start(), "PLAW", f"Pub. L. {c}-{n}", {"congress": c, "number": n}))
    for m in PLAW_CONG_RE.finditer(text):
        n, c = int(m.group(1)), int(m.group(2))
        if 1 <= c <= MAX_CONGRESS and n >= 1:
            out.append((m.start(), "PLAW", f"Pub. L. {c}-{n}", {"congress": c, "number": n}))
    for m in FR_RE.finditer(text):
        v, p = int(m.group(1)), int(m.group(2))
        if 1 <= v <= MAX_FR_VOLUME and p >= 1:
            out.append((m.start(), "FR", f"{v} FR {p}", {"volume": v, "page": p}))
    for m in USC_RE.finditer(text):
        t, s = int(m.group(1)), m.group(2).split("-")[0]
        if 1 <= t <= MAX_USC_TITLE:
            out.append((m.start(), "USC", f"{t} U.S.C. {s}", {"title": t, "section": s}))
    for m in CFR_RE.finditer(text):
        t, part, sec = int(m.group(1)), m.group(2), m.group(3) or ""
        # Title 3 is the compilation of presidential documents ("3 CFR 1943-1948 Comp."), not a rule text.
        if 1 <= t <= MAX_CFR_TITLE and t != 3 and not re.fullmatch(r"\d{4}-\d{4}", part):
            out.append((m.start(), "CFR", f"{t} CFR {part}" + (f".{sec}" if sec else ""),
                        {"title": t, "part": part, "section": sec}))
    for m in RP_RE.finditer(text):
        n, y = int(m.group(1)), int(m.group(2))
        out.append((m.start(), "RP", f"Reorganization Plan No. {n} of {y}", {"number": n, "year": y}))
    return out


def find_embedded(text: str, skip_fr=(), limit=MAX_CITES_PER_LINE):
    """Embedded citations in order of first appearance: [{kind, cite, parts}].

    skip_fr: (volume, page) pairs to ignore, normally the Federal Register
    pages where the orders named in the line were themselves printed (already
    held; the line is asking for something else).

    Rules, all deterministic:
      * duplicates are dropped (first position wins);
      * Public Law cites are dropped when the line has at least as many
        Statutes at Large cites (they are the same enactments, and the Stat.
        page is the more exact route);
      * a Reorganization Plan is kept only when the line gives no Stat. cite
        (otherwise the Stat. cite is the plan's own page);
      * at most `limit` cites are returned; the rest are reported by
        find_embedded_with_overflow.
    """
    return find_embedded_with_overflow(text, skip_fr, limit)[0]


def find_embedded_with_overflow(text: str, skip_fr=(), limit=MAX_CITES_PER_LINE):
    skip = {(int(v), int(p)) for v, p in skip_fr}
    seen, hits = set(), []
    for pos, kind, cite, parts in sorted(_hits(text or ""), key=lambda h: (h[0], h[2])):
        if kind == "FR" and (parts["volume"], parts["page"]) in skip:
            continue
        if cite in seen:
            continue
        seen.add(cite)
        hits.append({"kind": kind, "cite": cite, "parts": parts})
    n_stat = sum(h["kind"] == "STAT" for h in hits)
    n_plaw = sum(h["kind"] == "PLAW" for h in hits)
    if n_stat and n_stat >= n_plaw:
        hits = [h for h in hits if h["kind"] != "PLAW"]
    if n_stat:
        hits = [h for h in hits if h["kind"] != "RP"]
    return hits[:limit], hits[limit:]
