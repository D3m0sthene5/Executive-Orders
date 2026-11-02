"""Held-corpus checks for instruments, reports and names a claim leaves unaddressed.

The corpus is name_checks' exact Git-retained jobs/**/texts inventory, read
through the same command snapshot so the searched bytes are reverified before
output.  An instrument identity comes only from retained publisher metadata:
the APP listing (one instrument per item) or the Federal Register originals
SOURCES record, with the citation located inside that order's own boundaries
by the clause-drafts locator.  A text whose identity cannot be bound is never
a counterexample.  Nothing here reads review outcomes or names specific orders.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import citation_checks as CC
import name_checks as NC
import source_checks as SC

CLAUSE_DRAFTS = Path(__file__).resolve().parents[1] / "clause-drafts"
if str(CLAUSE_DRAFTS) not in sys.path:
    sys.path.insert(0, str(CLAUSE_DRAFTS))

APP_DIR = "jobs/app-executive-orders/output/texts/"
FR_DIRS = ("jobs/fr-originals/output/", "jobs/fr-originals/data/full_run/")
MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"


def _tol(word):
    """OCR tolerance: soft hyphens, line-break hyphens and stray single spaces."""
    return r"[­\-]?\s{0,2}".join(map(re.escape, word))


CUE = r"(?:" + _tol("Executive") + r"\s*" + _tol("Order") + r"s?|Ex\.\s*Ord\.|E\.\s?O\.|\bEO)\s*(?:" + _tol("No") + r"s?\s*[.,]?\s*)?"
CUE_NUMBER = re.compile(CUE + r"(\d(?: ?\d){2,4})(?!\d)(?:\s*[-‐–]?\s*([A-Z])\b)?", re.I)
AMEND_CONTEXT = re.compile(r"\b(?:amend\w*|modif\w*|supplement\w*|as\s+amended)\b", re.I)
_ABBR = r"(?<!\bNo)(?<!\bNos)(?<!\bSec)(?<!\bStat)(?<!\bCh)(?<!\bPub)(?<!\bOrd)(?<!\bCo)(?<!\bInc)(?<!\bMr)(?<!\bU\.S\.C)(?<!\bU\.S)(?<!\bF\.R)(?<!\bS)"
SENTENCE_END = re.compile(_ABBR + r"\.\s+(?=[A-Z(\[])")
REVOKED_AFTER = re.compile(r"\b(?:is|are|be|shall\s+be)\s+(?:hereby\s+)?(?:revoked|superseded|rescinded)\b", re.I)
REVOKES_BEFORE = re.compile(r"\b(?:hereby\s+)?(?:revok(?:e|es|ing)|supersed(?:e|es|ing)|rescind(?:s|ing)?)\b|\b(?:are|is)\s+(?:hereby\s+)?(?:revoked|superseded|rescinded)\s*:", re.I)
LEADERS = re.compile(r"_\s?_\s?_")

NO_REPORT = re.compile(
    r"\b(?:no|not\s+any)\s+(?:held\s+)?(?:\w+\s+){0,3}?(?:board\s+|board's\s+)?reports?\b[^.;]{0,100}?\b(?:is|was|are|were)\s+(?:held|in\s+the\s+packet|available)"
    r"|\breport\b[^.;]{0,60}\b(?:is|was|are)\s+not\s+held"
    r"|\bno\s+held\s+(?:\w+\s+){0,3}(?:source|record|text)s?\s+(?:\w+\s+){0,2}(?:establish|fix|show|give|record|date)s?\b[^.;]{0,80}\breport", re.I)
REPORT_HEADING = re.compile(r"\bREPORT\s+(?:TO\s+)?T\S{1,3}\s+PRESIDENT\s+BY\s+T\S{1,3}\s+(?:EMERGENCY\s+BOARD|BOARD\s+OF\s+INQUIRY)", re.I)
REPORT_ORDER = re.compile(r"(?:EXECUTIVE\s+ORDER|E\.\s*O\.)\s*(?:No\.?\s*)?([0-9IlO](?: ?[0-9IlO]){3,4})(?:\s*-?\s*([A-Z])\b)?", re.I)

# "known as" tolerates a two- or three-character OCR misreading of "as" (e.g. "£ts").
CREATED_NAME = re.compile(r"\b(?:shall\s+(?:hereafter\s+)?be\s+known\s+(?:as|\S{2,3})|(?:is|are)\s+hereby\s+(?:named|designated\s+as)|to\s+be\s+known\s+(?:as|\S{2,3}))\s+(?:the\s+)?"
                          r"([A-Z][A-Za-z'’-]*(?:[ \t]*\n?[ \t]*(?:of|and|the|for|[A-Z][A-Za-z'’-]*)){1,8})")
RENAME = re.compile(r"\bnames?\s+of\b[^.]{0,160}?\b(?:are|is)\s+hereby\s+changed\b|\bhereby\s+renamed\b|\bshall\s+hereafter\s+be\s+(?:known|designated)\s+as\b|\b(?:is|are)\s+hereby\s+abolished\b", re.I | re.S)
CLAIM_RENAME = re.compile(r"\brenam\w*|\bnames?\s+(?:was|were|is|are)?\s*changed\b|\bchang\w*\s+(?:the|its)\s+names?\b|\babolish\w*", re.I)
NO_LATER_NAMING = re.compile(r"\bno\s+(?:other\s+|earlier\s+|later\s+|such\s+)?(?:held\s+)?(?:\w+\s+)?(?:instruments?|orders?|proclamations?|sources?|acts?)\b[^.;]{0,120}?\b(?:names?|named|was\s+found|were\s+found|found|shows?|touch\w*)\b", re.I)

REFERENCE = re.compile(r"\b(?:matching|companion|corresponding)\s+note\s+on\s+(?:EO|Executive\s+Order)\s*(?:No\.?\s*)?(\d{3,6}(?:-?[A-Z])?)\b"
                       r"|\bfull\s+read\s+of\s+(?:EO|Executive\s+Order)\s*(?:No\.?\s*)?(\d{3,6}(?:-?[A-Z])?)\b", re.I)
UNPINNED = re.compile(r"\bheld\s+text\s+of\s+(?:EO|Executive\s+Order)\s*(?:No\.?\s*)?(\d{3,6}(?:-?[A-Z])?)\b[^.;]{0,80}?\bnot\s+(?:one\s+of\s+(?:the\s+)?)?(?:its\s+|the\s+claim's\s+)?(?:cited|pinned)\b", re.I)


def _number_pattern(number):
    import segment
    return segment.number_pattern(number)


def _norm_id(value):
    return re.sub(r"[- ]", "", str(value or "")).upper().removeprefix("EO:")


def _git_rows(repo, rel, cache):
    """Parse a JSONL metadata file only when its bytes equal the HEAD blob."""
    path = Path(repo) / rel
    if not path.is_file():
        return None
    raw = path.read_bytes()
    try:
        expected = subprocess.check_output(["git", "rev-parse", f"HEAD:{rel}"], cwd=repo, stderr=subprocess.DEVNULL).decode().strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    if hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != expected:
        return None
    key = ("citing-jsonl", rel, expected)
    if key not in cache:
        cache[key] = [json.loads(line) for line in raw.splitlines() if line.strip()]
    return cache[key]


class Corpus:
    """Snapshot-verified texts plus publisher identity for one command."""

    def __init__(self, repo, packet_path, cache):
        self.repo = Path(repo).resolve()
        self.cache = cache
        head, inventory, issue = NC._inventory(self.repo, cache)
        self.issue = issue
        self.scope = {"inventory_commit": head, "tracked_files": len(inventory)}
        if issue:
            self.texts = {}
            self.missing = []
        else:
            snapshot = cache.get("_snapshot")
            if isinstance(snapshot, NC.Snapshot) and snapshot.active and snapshot.repo == self.repo:
                available, missing, bad = snapshot.read(inventory, "git_blob_sha1", [])
            else:
                available, missing, bad = NC._read_inventory(self.repo, inventory, "git_blob_sha1", [])
            self.texts = available
            self.missing = list(missing) + list(bad)
        self.scope.update({"verified_files": len(self.texts), "missing_or_changed_files": len(self.missing)})
        app, _ = NC._publisher_records(self.repo, cache)
        self.app = {APP_DIR + name: rows for name, rows in app.items()}
        self.fr = {}
        for base in FR_DIRS:
            rows = _git_rows(self.repo, base + "SOURCES.jsonl", cache)
            for row in rows or []:
                if isinstance(row.get("text_path"), str):
                    self.fr[base + row["text_path"]] = row
        self.identity_metadata = bool(self.app) and bool(self.fr)

    def number_index(self):
        key = ("citing-number-index", self.scope.get("inventory_commit"), len(self.texts))
        if key not in self.cache:
            index = defaultdict(set)
            for rel, (text, _) in self.texts.items():
                if rel.startswith(APP_DIR) or rel.startswith(FR_DIRS):
                    for n in set(re.findall(r"(?<!\d)\d{3,5}(?!\d)", re.sub(r"(?<=\d) (?=\d)", "", text))):
                        index[n].add(rel)
            self.cache[key] = index
        return self.cache[key]

    def identity(self, rel, pos=None):
        """(instrument_id, date, (start, end), basis) for a position, or None."""
        text = self.texts.get(rel, ("", None))[0]
        if rel in self.app:
            ids = {r.get("instrument_id") for r in self.app[rel]}
            if len(ids) == 1 and self.app[rel][0].get("date"):
                return next(iter(ids)), self.app[rel][0]["date"], (0, len(text)), "app_publisher_listing"
            return None
        row = self.fr.get(rel)
        if row and len(row.get("instrument_ids") or []) == 1:
            ident = row["instrument_ids"][0]
            issue = re.search(r"/FR-(\d{4}-\d{2}-\d{2})/", str(row.get("url") or ""))
            key = ("citing-locate", rel, ident)
            if key not in self.cache:
                import segment
                loc = segment.locate_order(text, ident.removeprefix("EO:"))
                self.cache[key] = (loc.doc_start, loc.doc_end) if loc and loc.heading_style != "unnumbered_hint" else None
            span = self.cache[key]
            if span and issue and (pos is None or span[0] <= pos < span[1]):
                return ident, issue.group(1), span, "fr_sources_record_and_located_order"
        return None

    def held_texts_for(self, eo):
        eo = "EO:" + _norm_id(eo)
        rows = []
        for rel, listing in self.app.items():
            if rel in self.texts and {r.get("instrument_id") for r in listing} == {eo}:
                ident = self.identity(rel)
                if ident:
                    rows.append((rel, ident))
        for rel, row in self.fr.items():
            if rel in self.texts and row.get("instrument_ids") == [eo]:
                ident = self.identity(rel)
                if ident:
                    rows.append((rel, ident))
        return rows

    def source(self, rel, start, end, extra=None):
        text, digest = self.texts[rel]
        out = {"text_path": rel, "text_sha256": digest, "char_start": start, "char_end": end, "quote": text[start:end]}
        out.update(extra or {})
        return out


def own_date_of(dossier):
    """The pinned signing date: dossier field, else the original record's source."""
    date = dossier.get("signing_date")
    if not date:
        record = (dossier.get("evidence") or {}).get(dossier.get("original_source_id")) or {}
        date = (record.get("source") or {}).get("signing_date") if isinstance(record, dict) else None
    return date if isinstance(date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) else None


def _flag(code, field, span, detail, source):
    return {"code": code, "scope_id": "whole", "field": field, "span": span, "detail": detail, "source": source}


def _claim_mentions(claim_text, number):
    base = re.match(r"\d+", number).group()
    return bool(re.search(r"(?<![\d])" + base + r"(?![\d])", claim_text))


def _sentence_bounds(text, start, end, reach=800):
    head = text[max(0, start - 250):start]
    marks = list(SENTENCE_END.finditer(head))
    a = max(0, start - 250) + (marks[-1].end() if marks else 0)
    tail = text[end:end + reach]
    stop = SENTENCE_END.search(tail)
    return a, end + (stop.start() + 1 if stop else len(tail))


def _revokes(text, m):
    a, b = _sentence_bounds(text, m.start(), m.end())
    head, tail = text[a:m.start()], text[m.end():b]
    if LEADERS.search(text[max(0, m.start() - 80):m.end() + 120]):
        return False
    if re.search(r"\((?:revoked|amended|superseded)\s+by\b", tail[:120] + head[-60:], re.I):
        return False
    return bool(REVOKED_AFTER.search(tail) or REVOKES_BEFORE.search(head))


def _parents(body, own):
    parents = set()
    for m in CUE_NUMBER.finditer(body):
        number = m.group(1).replace(" ", "") + (m.group(2) or "").upper()
        if number != own and AMEND_CONTEXT.search(body[max(0, m.start() - 200):m.end() + 200]):
            parents.add(number)
    return parents


def _unaddressed_citing(claim, dossier, corpus, body, claim_text):
    flags, gaps = [], []
    own = _norm_id(claim.get("instrument_id"))
    own_date = own_date_of(dossier)
    parents = _parents(body, own)
    index = corpus.number_index()
    found = {}
    for target, role in [(own, "own")] + [(p, "parent") for p in sorted(parents)]:
        base = re.match(r"\d+", target).group()
        pattern = re.compile(CUE + _number_pattern(target), re.I)
        for rel in sorted(index.get(base, ())):
            text = corpus.texts[rel][0]
            for m in pattern.finditer(text):
                if LEADERS.search(text[max(0, m.start() - 80):m.end() + 80]):
                    continue
                ident = corpus.identity(rel, m.start())
                if not ident:
                    continue
                actor, date, _, basis = ident
                number = _norm_id(actor)
                if number == own or number in parents or _claim_mentions(claim_text, number) or actor in found:
                    continue
                if role == "own" and (not own_date or date <= own_date):
                    continue
                if role == "parent" and not _revokes(text, m):
                    continue
                a, b = _sentence_bounds(text, m.start(), m.end())
                found[actor] = (role, target, rel, date, basis, a, b)
                break
    for actor, (role, target, rel, date, basis, a, b) in sorted(found.items()):
        what = "cites this order by number" if role == "own" else f"revokes EO {target}, which this order amends or modifies"
        flags.append(_flag("unaddressed_citing_instrument", "claim", f"{actor} ({date})",
                           f"Held {actor} ({date}) {what}; the claim never mentions {actor} in its ends, events, reasoning, searches or gaps.",
                           corpus.source(rel, a, b, {"instrument_id": actor, "date": date, "identity_basis": basis, "cited_order": "EO:" + target})))
    return flags, gaps


def _report_texts(corpus):
    key = ("citing-report-texts", corpus.scope.get("inventory_commit"), len(corpus.texts))
    if key not in corpus.cache:
        rows = []
        for rel, (text, _) in corpus.texts.items():
            head = re.sub(r"\s+", " ", text[:5000])
            m = REPORT_HEADING.search(head)
            if not m:
                continue
            region = head[m.start():m.start() + 700]
            orders = set()
            for o in REPORT_ORDER.finditer(region):
                digits = o.group(1).replace(" ", "").translate(str.maketrans("IlO", "110"))
                orders.add(digits + (o.group(2) or "").upper())
            board = re.search(r"\bNo\.\s*(\d{1,3})\b", region)
            rows.append((rel, orders, board.group(1) if board else None, region))
        corpus.cache[key] = rows
    return corpus.cache[key]


def _held_report(claim, corpus, body, claim_text):
    flags = []
    own = _norm_id(claim.get("instrument_id"))
    assertions = [(field, text[max(0, m.start() - 40):m.end() + 40].strip())
                  for field, text in CC._reason_parts(claim) for m in NO_REPORT.finditer(text)]
    if not assertions:
        return flags
    board_no = re.search(r"\bEmergency\s+Board\s+No\.?\s*(\d{1,3})\b", body or "")
    for rel, orders, board, region in _report_texts(corpus):
        if not (own in orders or (board_no and board == board_no.group(1))) or rel in claim_text:
            continue
        text = corpus.texts[rel][0]
        start = text.find(region[:40]) if region[:40] in text else 0
        dates = list(re.finditer(MONTH + r"\s+\d{1,2},\s*\d{4}", region, re.I))
        dated = dates[-1] if len(dates) > 1 else None
        field, span = assertions[0]
        flags.append(_flag("held_board_report_unaddressed", field, span,
                           f"The claim says no board report is held, but held {rel} is a report to the President by the board appointed by EO {own}"
                           + (f" (dated {dated.group()})." if dated else "."),
                           corpus.source(rel, max(0, start), max(0, start) + min(len(text) - max(0, start), 700), {"matched_by": "order_number" if own in orders else "board_number"})))
        break
    return flags


def _segment(text, pos):
    starts = [m.end() for m in re.finditer(r"\[\s*F\.\s*R\.\s*Doc\.[^\]]*\]", text[:pos])]
    a = starts[-1] if starts else 0
    nxt = re.search(r"\[\s*F\.\s*R\.\s*Doc\.[^\]]*\]", text[pos:])
    return a, pos + (nxt.end() if nxt else len(text) - pos)


def _renamed_names(claim, dossier, corpus, body, claim_text, packet_path):
    flags, gaps = [], []
    names = []
    for m in CREATED_NAME.finditer(body or ""):
        name = re.sub(r"\s+", " ", m.group(1)).strip(" .,")
        if len(name.split()) >= 2:
            names.append(name)
    names = list(dict.fromkeys(names))
    if not names:
        return flags, gaps
    negative = [(field, m.group()) for field, text in CC._reason_parts(claim) for m in NO_LATER_NAMING.finditer(text)]
    if not negative or CLAIM_RENAME.search(claim_text):
        return flags, gaps
    hits, failures, _, scope = NC.scan_names(packet_path, names, corpus.repo, corpus.cache)
    if failures:
        gaps.append({"code": "created_name_corpus_incomplete", "missing_or_changed": len(failures)})
    own = _norm_id(claim.get("instrument_id"))
    own_date = own_date_of(dossier)
    for name in names:
        pattern = re.compile(r"\b" + r"[\W_]+".join(re.escape(w) for w in NC._norm(name).split()) + r"\b", re.I)
        for hit in hits.get(name, []):
            rel = hit["path"]
            if rel not in corpus.texts:
                continue
            text = corpus.texts[rel][0]
            for m in pattern.finditer(text):
                a, b = _segment(text, m.start())
                seg = text[a:b]
                change = None
                for c in RENAME.finditer(seg):
                    if a + c.start() < m.start():
                        change = c
                if not change or re.search(r"known\s+as\s+(?:the\s+)?" + pattern.pattern, seg, re.I) or re.search(CUE + _number_pattern(own), seg, re.I):
                    continue
                row = corpus.fr.get(rel)
                issue = re.search(r"/FR-(\d{4}-\d{2}-\d{2})/", str((row or {}).get("url") or ""))
                date = issue.group(1) if issue else (corpus.app.get(rel, [{}])[0].get("date") if rel in corpus.app else None)
                if not date or not own_date or date <= own_date:
                    if not date:
                        gaps.append({"code": "created_name_hit_undated", "path": rel, "name": name})
                    continue
                label = re.search(r"\[\s*No\.\s*(\d{3,5})\s*\]", seg)
                kind = "Proclamation" if re.search(r"\bA\s+PROCLAMATION\b", seg[:2000]) else "instrument"
                instrument = f"{kind} No. {label.group(1)}" if label else "an unnumbered held instrument"
                if label and _claim_mentions(claim_text, label.group(1)):
                    continue
                field, assertion = negative[0]
                said = re.sub(r"\s+", " ", change.group())
                flags.append(_flag("created_name_changed_by_later_instrument", field, assertion,
                                   f"This order creates the name '{name}'. Held {rel} (published {date}) prints {instrument}, whose text says '{said}' and lists that name; the claim neither records nor discusses the change.",
                                   corpus.source(rel, m.start(), m.end(), {"change_char_start": a + change.start(), "change_char_end": a + change.end(),
                                                                          "instrument_label": instrument, "date": date})))
                break
            else:
                continue
            break
    return flags, gaps


def _reference_instruments(claim, corpus):
    flags, gaps = [], []
    own = _norm_id(claim.get("instrument_id"))
    own_pat = re.compile(r"(?<![\d.])" + _number_pattern(own))
    seen = set()
    for field, text in CC._reason_parts(claim):
        for m in REFERENCE.finditer(text):
            ref = _norm_id(m.group(1) or m.group(2))
            if ref == own or ref in seen:
                continue
            seen.add(ref)
            # A reference the claim discusses elsewhere (for example a revoker of
            # the parent that was read in full) is explained there; only a bare
            # search-account reference is compared with its held text.
            number = re.compile(r"(?<!\d)" + re.escape(re.match(r"\d+", ref).group()) + r"(?!\d)")
            in_refs = sum(len(number.findall(sent)) for _, t in CC._reason_parts(claim)
                          for sent in re.split(r"(?<=[.;])\s+", t) if REFERENCE.search(sent))
            if len(number.findall(json.dumps(claim, ensure_ascii=False))) > in_refs:
                continue
            held = corpus.held_texts_for(ref)
            if not held:
                gaps.append({"code": "reference_instrument_text_unavailable", "field": field, "instrument": "EO:" + ref})
                continue
            if any(own_pat.search(corpus.texts[rel][0][span[0]:span[1]]) for rel, (_, _, span, _) in held):
                continue
            rel, (actor, date, span, basis) = held[0]
            flags.append(_flag("reference_instrument_does_not_cite_order", field, text[max(0, m.start() - 120):m.end() + 40].strip(),
                               f"The reasoning names EO {ref} as a matching note or full-read reference for this order, but no held, identity-bound text of EO {ref} contains the number {own} ({len(held)} text(s) checked).",
                               corpus.source(rel, span[0], span[1], {"instrument_id": actor, "date": date, "identity_basis": basis, "checked_texts": [r for r, _ in held]})))
    return flags, gaps


def _cited_ids(claim):
    ids = set()
    def visit(obj):
        if isinstance(obj, dict):
            if obj.get("evidence_id"):
                ident = SC._source_id(obj)
                if ident:
                    ids.add(ident)
            for v in obj.values():
                visit(v)
        elif isinstance(obj, list):
            for v in obj:
                visit(v)
    visit(claim)
    return ids


def _unpinned(claim, corpus):
    flags, gaps = [], []
    cited = _cited_ids(claim)
    for field, text in CC._reason_parts(claim):
        for m in UNPINNED.finditer(text):
            ref = _norm_id(m.group(1))
            if any(re.search(r"(?:>|:)EO:" + re.escape(ref) + r"(?:@|$)", c) for c in cited):
                continue
            held = corpus.held_texts_for(ref)
            if not held:
                gaps.append({"code": "unpinned_reference_text_unavailable", "field": field, "instrument": "EO:" + ref})
                continue
            rel, (actor, date, span, basis) = held[0]
            flags.append(_flag("held_source_left_unpinned", field, m.group(),
                               f"The reasoning relies on the held text of EO {ref} but states it is not cited; an identity-bound held text exists and no claim source pins it.",
                               corpus.source(rel, span[0], span[1], {"instrument_id": actor, "date": date, "identity_basis": basis})))
    return flags, gaps


REASON_EO = re.compile(r"\b(?:Executive\s+Order|EO)\s*(?:No\.?\s*)?(\d{1,6}(?:\s*-\s*[A-Z]|[A-Z])?)(?![\w-])", re.I)
DATE_AFTER = re.compile(r"\s*(?:\(|,)?\s*(?:of|dated|signed|issued)?\s*(?:on\s+)?(" + MONTH + r"\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})", re.I)
DATE_BEFORE = re.compile(r"\b(?:order|approval|instrument)\s+(?:dated|of|signed)\s+(" + MONTH + r"\s+\d{1,2},\s+\d{4})\s*\(\s*$", re.I)


def _iso(value):
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    try:
        return datetime.strptime(re.sub(r"\s+", " ", value).title(), "%B %d, %Y").date().isoformat()
    except ValueError:
        return None


def _suffix_siblings(claim, corpus):
    """An EO number whose locally stated date belongs to a same-number sibling.

    Binding uses only the Git-verified publisher listing: the asserted id must
    be listed under a different date, and exactly one same-base sibling must be
    listed under the stated date.  The sibling's held item is the source span.
    """
    flags, gaps = [], []
    by_base = defaultdict(list)
    for rel, rows in corpus.app.items():
        for row in rows:
            ident = _norm_id(row.get("instrument_id"))
            if re.fullmatch(r"\d+[A-Z]?", ident):
                by_base[re.match(r"\d+", ident).group()].append((ident, row, rel))
    own = _norm_id(claim.get("instrument_id"))
    seen = set()
    for field, text in CC._reason_parts(claim):
        for m in REASON_EO.finditer(text):
            asserted = _norm_id(m.group(1))
            base = re.match(r"\d+", asserted).group()
            after = DATE_AFTER.match(text[m.end():m.end() + 60])
            before = DATE_BEFORE.search(text[max(0, m.start() - 80):m.start()])
            stated = _iso((after or before).group(1)) if (after or before) else None
            if not stated or asserted == own or (asserted, stated) in seen:
                continue
            seen.add((asserted, stated))
            family = by_base.get(base, [])
            mine = [r for r in family if r[0] == asserted]
            if not mine:
                if any(r[1].get("date") == stated for r in family):
                    gaps.append({"code": "reasoning_order_not_in_publisher_listing", "field": field, "asserted": "EO:" + asserted})
                continue
            if any(r[1].get("date") == stated for r in mine):
                continue
            matches = {r[0]: r for r in family if r[0] != asserted and r[1].get("date") == stated}
            if len(matches) != 1:
                if matches:
                    gaps.append({"code": "reasoning_order_sibling_ambiguous", "field": field, "asserted": "EO:" + asserted, "candidates": sorted(matches)})
                continue
            sibling, row, rel = next(iter(matches.values()))
            if rel in corpus.texts:
                text_held = corpus.texts[rel][0]
                source = corpus.source(rel, 0, min(len(text_held), 400), {"instrument_id": "EO:" + sibling, "date": stated,
                                                                     "identity_basis": "app_publisher_listing", "publisher_title": row.get("title")})
            else:
                source = {"publisher_listing": row, "text_path": None, "detail": "held APP item not in the verified corpus"}
            flags.append(_flag("reasoning_order_suffix_sibling_mismatch", field, text[max(0, m.start() - 80):m.end() + 60].strip(),
                               f"Reasoning dates EO {asserted} {stated}; the publisher listing dates EO {asserted} {mine[0][1].get('date')} "
                               f"({mine[0][1].get('title')}) and lists same-number EO {sibling} on {stated} ({row.get('title')}).",
                               source))
    return flags, gaps


def _dedupe(flags):
    """One flag per code and detail; the same discrepancy restated in several fields is one finding."""
    out, seen = [], set()
    for flag in flags:
        key = (flag["code"], flag["detail"])
        if key not in seen:
            seen.add(key)
            out.append(flag)
    return out


SEARCH_SYSTEMS = {
    "usc": re.compile(r"current-law:usc\b|\bU\.\s?S\.\s?Code\b|\bUSC\b(?!\s*note)"),
    "ecfr": re.compile(r"current-law:ecfr\b|\beCFR\b", re.I),
    "ofr_catalog": re.compile(r"later-events:ofr_catalog\b|\bcatalog\s+(?:disposition\s+)?notes?\b|\bFederal\s+Register\s+(?:executive-order\s+)?catalog\b", re.I),
    "cruden": re.compile(r"\bCruden\b|\bby-number\s+scan\b|\bnumber-citation\s+scan\b", re.I),
}
NO_HIT = re.compile(r"\b(?:no|zero|0)\s+(?:machine\s+)?(?:hits?|matches|results)\b|\b(?:found|finds|returns?|returned)\s+(?:nothing|no\s+(?:hit|match|result)s?)\b|\brecords?\s+no\s+hits?\b", re.I)
QUALIFIED = re.compile(r"\b(?:that\s+contradicts?|contradicting|other\s+than|except|besides|beyond|apart\s+from)\b(?!\s+(?:its|the\s+order's)\s+own)", re.I)
MENTIONS = "jobs/current-law/output/MENTIONS.csv"
EDGES = "jobs/later-events/output/EDGES.csv"


def _git_csv(repo, rel, cache):
    """Rows of a tracked CSV with each row's byte span, only when it equals the HEAD blob."""
    import csv
    import io
    path = Path(repo) / rel
    if not path.is_file():
        return None, None
    raw = path.read_bytes()
    try:
        expected = subprocess.check_output(["git", "rev-parse", f"HEAD:{rel}"], cwd=repo, stderr=subprocess.DEVNULL).decode().strip()
    except (OSError, subprocess.CalledProcessError):
        return None, None
    if hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != expected:
        return None, None
    key = ("citing-csv", rel, expected)
    if key not in cache:
        text = raw.decode("utf-8")
        rows, pos = [], 0
        lines = text.splitlines(keepends=True)
        header = next(csv.reader([lines[0]])) if lines else []
        pos = len(lines[0]) if lines else 0
        buffer, start = "", pos
        for line in lines[1:]:
            if not buffer:
                start = pos
            buffer += line
            pos += len(line)
            try:
                parsed = next(csv.reader(io.StringIO(buffer)))
            except (csv.Error, StopIteration):
                continue
            if buffer.count('"') % 2:
                continue
            rows.append((dict(zip(header, parsed)), start, pos))
            buffer = ""
        cache[key] = (rows, hashlib.sha256(raw).hexdigest())
    return cache[key]


def _search_negatives(claim, dossier, corpus, packet_path):
    """A search the claim reports as empty must not have a retained hit naming the order."""
    flags, gaps = [], []
    own = "EO:" + _norm_id(claim.get("instrument_id"))
    reported = {}
    for field, text in CC._reason_parts(claim):
        for sentence in re.split(r"(?<=[.;])\s+", text):
            for clause in re.split(r",\s+(?=[A-Za-z(])|;\s+", sentence):
                negative = NO_HIT.search(clause)
                if not negative or QUALIFIED.search(clause):
                    continue
                for system, pattern in SEARCH_SYSTEMS.items():
                    named = pattern.search(clause)
                    # The negative must follow the search it reports on; a by-number
                    # scan negative must be about this order, not some other object.
                    if not named or named.start() > negative.start():
                        continue
                    if system == "cruden" and not re.search(r"\bthis\s+order\b|" + re.escape(own.removeprefix("EO:")), clause):
                        continue
                    reported.setdefault(system, (field, clause.strip()))
    if not reported:
        return flags, gaps
    # The dossier's machine_hits_for_this_order is a summary count; only the
    # retained search outputs themselves (rows naming the order) count as hits.
    for system, (field, clause) in sorted(reported.items()):
        hits = []
        if system in ("usc", "ecfr"):
            rows, digest = _git_csv(corpus.repo, MENTIONS, corpus.cache)
            if rows is None:
                gaps.append({"code": "search_output_unretained", "search": system, "field": field, "path": MENTIONS})
                continue
            for row, a, b in rows:
                if row.get("system") == system and row.get("instrument_id") == own:
                    hits.append((row.get("citation"), {"text_path": MENTIONS, "text_sha256": digest, "char_start": a, "char_end": b,
                                                        "mention_id": row.get("mention_id"), "citation": row.get("citation"),
                                                        "quote": (row.get("snippet") or "")[:300]}))
                    break
        elif system == "ofr_catalog":
            rows, digest = _git_csv(corpus.repo, EDGES, corpus.cache)
            if rows is None:
                gaps.append({"code": "search_output_unretained", "search": system, "field": field, "path": EDGES})
                continue
            for row, a, b in rows:
                if row.get("evidence_type", "").startswith("ofr_note") and row.get("target_id") == own:
                    hits.append((row.get("edge_id"), {"text_path": EDGES, "text_sha256": digest, "char_start": a, "char_end": b,
                                                       "edge_id": row.get("edge_id"), "quote": (row.get("quote") or "")[:300]}))
                    break
        elif system == "cruden":
            folder = Path(packet_path).parent if packet_path else None
            lookup = next((p for p in ((folder / "LOOKUPS.details.json"), (folder.parent / "LOOKUPS.details.json")) if p.is_file()), None) if folder else None
            if lookup is None:
                gaps.append({"code": "search_output_unretained", "search": system, "field": field})
                continue
            raw = lookup.read_bytes()
            member = json.loads(raw).get("members", {}).get(own, {})
            for lead in member.get("number_citations") or []:
                rel = lead.get("file")
                if rel not in corpus.texts or corpus.texts[rel][1] != lead.get("raw_sha256"):
                    continue
                ident = corpus.identity(rel, lead.get("char_start"))
                if ident and ident[0] != own:
                    hits.append((rel, corpus.source(rel, lead["char_start"], lead["char_end"], {"lookup_path": str(lookup), "lookup_sha256": hashlib.sha256(raw).hexdigest(),
                                                                                                "instrument_id": ident[0]})))
                    break
        if hits:
            label, source = hits[-1]
            flags.append(_flag("reported_empty_search_has_hit", field, clause,
                               f"The claim reports the {system} search as finding no hit, but the retained search output records one naming {own}: {label}.",
                               source))
    return flags, gaps


def check(claim, dossier, repo, packet_path=None, cache=None):
    cache = {} if cache is None else cache
    flags, gaps = [], []
    corpus = Corpus(repo, packet_path, cache)
    if corpus.issue or not corpus.texts:
        return {"flags": [], "coverage_gaps": [{"code": "citing_corpus_unavailable", "reason": corpus.issue or "no_verified_texts"}]}
    if corpus.missing:
        gaps.append({"code": "citing_corpus_incomplete", **corpus.scope,
                     "detail": "Missing or changed held texts prevent treating an absent citation as corpus-wide."})
    if not corpus.identity_metadata:
        gaps.append({"code": "citing_identity_metadata_unavailable",
                     "detail": "Publisher listing or FR originals SOURCES metadata is missing or differs from HEAD; no instrument identity is bound."})
        return {"flags": [], "coverage_gaps": gaps}
    claim_text = json.dumps(claim, ensure_ascii=False)
    body, _, body_gap = SC._own_body(claim, dossier, corpus.repo, cache.setdefault("citing-own-body", {}))
    if body is None:
        gaps.append({"code": "citing_own_body_unverified", "reason": body_gap})
    else:
        a, b = _unaddressed_citing(claim, dossier, corpus, body, claim_text)
        flags += a; gaps += b
        a, b = _renamed_names(claim, dossier, corpus, body, claim_text, packet_path)
        flags += a; gaps += b
    flags += _held_report(claim, corpus, body, claim_text)
    for fn in (_reference_instruments, _unpinned, _suffix_siblings):
        a, b = fn(claim, corpus)
        flags += a; gaps += b
    a, b = _search_negatives(claim, dossier, corpus, packet_path)
    flags += a; gaps += b
    return {"flags": _dedupe(flags), "coverage_gaps": gaps}
