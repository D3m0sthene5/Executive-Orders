"""Selden shared code: locate the sentence of a later instrument that acts on a target order, and write the shared
SOURCES.jsonl / FRAGMENTS.jsonl records. Standard library only.

Named for John Selden (1584-1654), who went back to the records for the actual texts of statutes and precedents
instead of trusting what later writers said they contained.

The locator reuses jobs/shepard-citations/cites.py (citation forms, relation words, sentence bounds); nothing here
re-implements them. A located sentence is a lead to what the instrument says, not a finding about its legal effect.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shepard-citations"))
import cites  # noqa: E402  (jobs/shepard-citations/cites.py, read-only reuse)

LOCATOR_VERSION = "selden-locate-2"
LEGAL_CUTOFF = "2026-10-14"
ENDING = {"revocation", "rescission", "supersession", "replacement", "termination", "abolition", "vacation",
          "restoration"}
MODIFYING = {"amendment", "modification", "extension", "correction", "suspension"}
EO_ID = re.compile(r"EO:(\d{1,5})(?:-?([A-Za-z])|-(\d{1,2}))?$")
# Relation words cites.RELATIONS lacks that matter in later presidential documents.
CONTINUE_RE = re.compile(r"\bcontinu(?:e|ed|es|ing|ation)\b", re.I)
UNDER_RE = re.compile(r"\b(?:pursuant\s+to|under|in\s+accordance\s+with|as\s+(?:directed|required)\s+(?:by|in)"
                      r"|consistent\s+with|implement\w*)\b", re.I)


# Version 2 fallbacks for OCR and printed lists that cites.EO_NUMBER_RE does not read (measured on OFR pairs in
# research/selden/tools/locator_eval.py): split letters ("E xecutive O rder"), "Ho." for "No.", space-separated
# number lists ("Executive Orders Numbered 8744 9230 9712"), repeated "No. N of <date>" lists, and revocation
# tables whose rows start with the order number ("No. Subject" / "10919 Creating an emergency board").
def _spaced(word):
    # letters may be split by an OCR space, or by a soft hyphen or hyphen at a line break ("Ex\xad\necutive")
    return r"(?:[\xad-]?\s*)?".join(re.escape(c) for c in word)


LEAD_FUZZY = re.compile(r"(?:\b" + _spaced("Executive") + r"\s+" + _spaced("Order") + r"s?\b|\bE\.\s?O\.|\bEx\.\s*Ord\.)", re.I)
COLUMN_HEAD = re.compile(r"\bNo\.\s+Subject\b")
TABLE_HEAD = re.compile(r"\bNo\.\s+Subject\b|Executive\s+Orders?\s+(?:Numbered|Nos\.)|following\s+Executive\s+[Oo]rders",
                        re.I)


_SEP_RE = re.compile(r"(?:[\s,;&|\xad]|\band\b|\bor\b|\.(?=\s))+", re.I)
_NO_RE = re.compile(r"(?:[NH]o[s]?\.?|Numbered|Numbers?)(?![A-Za-z])", re.I)
_DATE_RE = re.compile(r"(?:of|dated)\s+" + cites.DATE_ANY, re.I)
_NUM_RE = re.compile(r"(\d{1,5})(\s?-?\s?[A-Z](?![A-Za-z]))?(?![\d])")
_SPLIT_NUM = re.compile(r"\d{1,4} \d{1,4}(?![\d])")
_PAREN_RE = re.compile(r"\([^()]{0,80}\)")
_LINE_NUM = re.compile(r"(?m)^[ \t]*(\d{4,5})[ \t]*$")


def _list_zone_numbers(text, start, limit=1500):
    """[(start, end, number)] of the order numbers in an executive-order list that begins at `start` (right after
    'Executive Orders'): only numbers, 'No.'/'Nos.'/'Numbered', separators, dates ('of May 14, 1962') and short
    parentheticals may follow one another; any other word ends the list, so years inside dates, page numbers and
    statute citations after the list are never read as order numbers."""
    out, pos, end = [], start, min(len(text), start + limit)
    while pos < end:
        for rx in (_SEP_RE, _NO_RE, _DATE_RE, _PAREN_RE):
            m = rx.match(text, pos)
            if m and m.end() > pos:
                pos = m.end()
                break
        else:
            sp = _SPLIT_NUM.match(text, pos)
            if sp and 4 <= len(sp.group(0).replace(" ", "")) <= 5:
                pos = sp.end()  # an OCR-split number ('1 2552'): ambiguous, never read as either part
                continue
            m = _NUM_RE.match(text, pos)
            if not m:
                break
            if re.match(r"[ \t|]*\n?[ \t|]*[A-Z][a-z]", text[m.end():m.end() + 6]):
                break  # a number followed by a capitalized word is a year or title ('2011 Amendments'), not a list item
            if not m.group(2):  # a suffixed citation ('6980-C', '9395B') is not the plain-numbered order
                out.append((m.start(), m.end(), m.group(1)))
            pos = m.end()
    return out


def _fallback_spans(text, num):
    """(start, end, form) of citations of number `num` (4-5 digits) in printed lists or tables, not already read."""
    out = []
    if len(num) < 4:
        return out
    for lead in LEAD_FUZZY.finditer(text):
        for s0, e0, n in _list_zone_numbers(text, lead.end()):
            if n == num:
                out.append((lead.start(), e0, "list"))
    if TABLE_HEAD.search(text):
        for m in re.finditer(r"(?m)^[ \t]*" + num + r"(?![\d])[ \t]+(?=[A-Z][a-z])", text):
            out.append((m.start(), m.end(), "table_row"))
    if COLUMN_HEAD.search(text):
        # a column of bare numbers (four or more consecutive lines) in an OFR "No. Subject" revocation table
        lines = list(_LINE_NUM.finditer(text))
        for k, m in enumerate(lines):
            if m.group(1) != num:
                continue
            run = [x for x in lines[max(0, k - 3):k + 4]
                   if abs(text.count("\n", min(x.start(), m.start()), max(x.start(), m.start()))) <= 3]
            if len(run) >= 4:
                out.append((m.start(1), m.end(1), "table_column"))
    return out


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def mech_class(mech: str) -> str:
    if mech in ENDING:
        return "ending"
    if mech in MODIFYING:
        return "modifying"
    if mech == "continuation":
        return "continuing"
    return "mention"


def parse_eo(iid: str):
    m = EO_ID.match(iid or "")
    if not m:
        return None
    return m.group(1), (m.group(2) or "").upper(), m.group(3) or ""


FILING = re.compile(r"(?:[\[\(|]\s*|\b)[fl1I]?\s?[FP]\.?\s?[RHK]\.?\s*D\s?o\s?c\.?\s*\d|B\s?i\s?l\s?l\s?i\s?n\s?g\s+c\s?o\s?d\s?e", re.I)


def own_span(text: str, acting_id: str):
    """(start, end, found) of the acting instrument's own text inside a page text that may also print neighbouring
    documents: from its heading ('Public Land Order 936', 'EXECUTIVE ORDER 8861', 'Executive Order 13879 of ...')
    to the next Federal Register filing line or billing code (source-ladder's patterns). found is False, and the
    whole text is returned, when no heading is printed."""
    digits = None
    if acting_id.startswith("PLO:"):
        num = acting_id.split(":", 1)[1]
        head = re.compile(_spaced("Public") + r"\s+" + _spaced("Land") + r"\s+" + _spaced("Order") + r"\s*(?:N\s?o\.?\s*)?"
                          + r"\s?".join(num) + r"(?![\d])", re.I)
    elif parse_eo(acting_id):
        num = parse_eo(acting_id)[0]
        head = re.compile(r"(?:\[\s*N\s?o\.?\s*\d+\s?[\]1lI|)]\s*)?" + _spaced("Executive") + r"\s+" + _spaced("Order")
                          + r"\s*(?:N\s?o\.?\s*)?" + r"\s?".join(num) + r"(?![\d])", re.I)
    else:
        return 0, len(text), False
    m = head.search(text)
    if not m:
        return 0, len(text), False
    f = FILING.search(text, m.end())
    return m.start(), (f.end() + 60 if f else len(text)), True


def find_citations(text: str, target: str, target_date: str | None = None, allow_date_only: bool = False,
                   within=None):
    """Every sentence of `text` that cites `target`, with the relation printed near the citation.

    target: "EO:6910", "EO:2656A", "PLO:936". target_date (ISO) confirms a citation that prints a date, and lets a
    date-only citation ('Executive Order of June 6, 1906') count when allow_date_only is set (the caller must know
    the date names one order only). Returns a list of dicts sorted by position:
    start/end (sentence span), cite_start/cite_end, quote, mechanism, word, partial, negated, actor_named (the
    target is printed as the one acting: 'as amended by Executive Order No. N'), date_stated, date_match, form.
    """
    hits = []
    eo = parse_eo(target)
    if eo:
        num, suf, dsuf = eo
        for (s, e, n, sx, d) in cites.eo_number_mentions(text):
            d = d.isoformat() if hasattr(d, "isoformat") else d
            if n != num or (sx or "") != suf:
                continue
            # cites.NUMBER_LIST reads at most five digits, so '138790' yields '13879': require digit boundaries.
            if not any(not text[s + m.end():s + m.end() + 1].isdigit()
                       for m in re.finditer(r"(?<!\d)" + num, text[s:e])):
                continue
            if dsuf and not re.match(r"\s*-\s*" + dsuf + r"(?!\d)", text[e:e + 6]):
                continue
            hits.append((s, e, d, "number"))
        if not hits and not suf and not dsuf:
            for s0, e0, form in _fallback_spans(text, num):
                hits.append((s0, e0, None, form))
        if allow_date_only and target_date:
            for (s, e, d, phrase) in cites.eo_date_mentions(text):
                d = d.isoformat() if hasattr(d, "isoformat") else d
                if d == target_date:
                    hits.append((s, e, d, "date_only"))
    elif target.startswith("PLO:"):
        num = int(target.split(":", 1)[1])
        for (s, e, n) in cites.plo_mentions(text):
            if n == num:
                hits.append((s, e, None, "number"))
    if within:
        hits = [h for h in hits if within[0] <= h[0] < within[1]]
    # OCR junk right after the number ('EXECUTIVE ORDER 994*' for 9947) makes the number unreliable.
    hits = [h for h in hits if not re.match(r"[*^~#]", text[h[1]:h[1] + 1])]
    out, seen = [], set()
    for s, e, d, form in sorted(hits):
        lo, hi = cites.sentence_bounds(text, s, e)
        if (lo, hi) in seen:
            continue
        seen.add((lo, hi))
        seg = text[lo:hi]
        c = cites.classify(seg, s - lo, e - lo, prefer="text")
        mech = c["mechanism"]
        w0 = seg.lower().find(c["word"]) if c["word"] else -1
        if c["word"] and re.search(r"\bas\s+(?:further\s+)?$", seg[max(0, w0 - 12):w0], re.I) \
                and re.match(r"(?:amend|modif|extend|continu|supersed)", c["word"]):
            mech = "cross_reference"  # 'Executive Order N, as amended': the order's history, not an act on it
            later = re.search(r"\b(?:is|are|shall\s+be)\s+(?:hereby\s+)?(?:further\s+)?(revoked|amended|superseded|"
                              r"modified|terminated|rescinded|extended|continued)\b", seg[e - lo:], re.I)
            if later:
                mech = {"revoked": "revocation", "amended": "amendment", "superseded": "supersession",
                        "modified": "modification", "terminated": "termination", "rescinded": "rescission",
                        "extended": "extension", "continued": "continuation"}[later.group(1).lower()]
        if mech == "cross_reference" and CONTINUE_RE.search(seg):
            mech = "continuation"
        tag = bool(re.fullmatch(r"\s*\[?\s*" + _spaced("EXECUTIVE") + r"\s+" + _spaced("ORDER") + r"\s*(?:N[Oo]\.?\s*)?[\d\s]+\]?\s*",
                                text[max(0, s - 2):e + 2])) or bool(re.match(r"\s*\]", text[e:e + 3]))
        out.append({
            "heading_or_closing_tag": tag,
            "start": lo, "end": hi, "cite_start": s, "cite_end": e, "quote": seg, "mechanism": mech,
            "mechanism_class": mech_class(mech), "word": c["word"], "partial": c["partial"], "negated": c["negated"],
            "actor_named": c["actor_named"], "under_or_pursuant": bool(UNDER_RE.search(seg)),
            "date_stated": d, "date_match": (d == target_date) if (d and target_date) else None, "form": form,
        })
    return out


def acting_on_target(hit) -> bool:
    """A sentence that prints a change to the target: an ending or modifying word governs the citation, the sentence
    is not negated, and the target is not printed as the actor ('as amended by Executive Order N')."""
    return hit["mechanism_class"] in ("ending", "modifying", "continuing") and not hit["negated"] \
        and not hit["actor_named"] and not hit.get("heading_or_closing_tag")


def best_hit(hits):
    rank = {"ending": 0, "modifying": 1, "continuing": 2, "mention": 3}
    good = sorted(hits, key=lambda h: (not acting_on_target(h), rank[h["mechanism_class"]], h["start"]))
    return good[0] if good else None


def fragment(target, acting_id, acting_label, hit, source, producer, date_candidate, date_basis, evidence_type,
             flags=(), extra=None):
    """One later_event_candidates fragment in the shape jobs/claim-kit/inputs.py reads (acting_id/target_id),
    carrying the exact sentence span in the held text so a claim can quote it and the checker can verify it."""
    row = {
        "acting_id": acting_id, "acting_label": acting_label, "target_id": target,
        "mechanism": hit["mechanism"] if acting_on_target(hit) else "cross_reference",
        "mechanism_printed": hit["mechanism"], "mechanism_class": hit["mechanism_class"],
        "relation_word": hit["word"], "qualifier": "in part" if hit["partial"] else "",
        "date_candidate": date_candidate, "date_basis": date_basis, "evidence_type": evidence_type,
        "quote": hit["quote"], "quote_kind": "verbatim_sentence", "quote_span": f"{hit['start']}-{hit['end']}",
        "citation_span": f"{hit['cite_start']}-{hit['cite_end']}", "citation_form": hit["form"],
        "date_stated_in_citation": hit["date_stated"], "date_matches_target": hit["date_match"],
        "flags": sorted(set(flags) | ({"negation_in_sentence"} if hit["negated"] else set())
                        | ({"target_printed_as_actor"} if hit["actor_named"] else set())
                        | ({"heading_or_closing_tag_of_a_printed_order"} if hit.get("heading_or_closing_tag") else set())),
        "source_id": source["source_id"], "source_url": source["url"], "source_sha256": source["sha256"],
        "page_or_item": source.get("page_or_item"), "text_path": source.get("text_path"),
        "located_by": LOCATOR_VERSION,
    }
    if extra:
        row.update(extra)
    return {"instrument_id": target, "kind": "later_event_candidates", "produced_by": producer,
            "confidence_note": "Machine-located sentence of a later instrument that prints the target order's number "
                               "near a relation word. A lead to what the instrument says: not a finding that it ended "
                               "or changed the order, in whole, or on that date. A person reads the cited text.",
            "data": [row]}


def source_record(source_id, acting_id, targets, url, raw_sha, nbytes, route, page_or_item, text_path, grade,
                  notes, cache_path=None, retrieved=None, extra=None):
    """Shared SOURCES.jsonl record. instrument_ids lists the acting instrument first, then the target orders, so the
    record never reads as a single order's own text (jobs/claim-kit/inputs.py attributes a text only to a record that
    names exactly one order)."""
    ids = [acting_id] + sorted(t for t in set(targets) if t != acting_id)
    if len(ids) < 2:
        ids.append("SELDEN:acting-instrument")
    rec = {"source_id": source_id, "instrument_ids": ids, "url": url, "sha256": raw_sha, "bytes": nbytes,
           "retrieved_utc": retrieved or now_utc(), "route": route, "page_or_item": page_or_item,
           "text_path": text_path, "grade": grade, "acceptable_as_original": False,
           "role": "acting_instrument_text", "notes": notes}
    if cache_path:
        rec["cache_path"] = cache_path
    if extra:
        rec.update(extra)
    return rec


# ---- planted controls --------------------------------------------------------------------------------------------

def near_miss_targets(target, text):
    """Targets an honest locator must never find in `text`: the number with its last digit dropped (a prefix of the
    printed number), with a digit appended (a longer number containing it) and one more than it, when the text
    prints none of them as an order number."""
    eo = parse_eo(target)
    if not eo:
        return []
    num = eo[0]
    cands = [num[:-1] if len(num) > 1 else None, num + "7", str(int(num) + 1)]
    return [f"EO:{c}" for c in cands if c and not c.startswith("0") and not printed_anywhere(text, c)]


def printed_anywhere(text, num):
    """The number appears anywhere in the text as a whole number (so it cannot serve as a negative control)."""
    return re.search(r"(?<!\d)" + re.escape(num) + r"(?!\d)", text) is not None


def run_controls(positives, texts, seed=1584):
    """positives: [(target, acting_id, expected_class, text_key)], texts: text_key -> text.

    Positive: the locator must find a sentence citing the target in the acting instrument's text (recall); the
    printed relation should fall in the expected class (agreement). Negatives: near-miss numbers in the same text,
    and the same text paired with another positive's target that the text does not print: any hit is a false
    location. Returns a summary with the measured rates and every miss and false hit."""
    rng = random.Random(seed)
    pos_found = pos_agree = 0
    misses, false_hits, neg_total = [], [], 0
    keys = [p[3] for p in positives]
    for target, actor, expected, key in positives:
        text = texts.get(key)
        if text is None:
            continue
        hits = find_citations(text, target)
        b = best_hit(hits)
        if b:
            pos_found += 1
            got = b["mechanism_class"] if acting_on_target(b) else "mention"
            if got == expected or (expected == "ending" and got == "ending"):
                pos_agree += 1
        else:
            misses.append({"target": target, "acting": actor, "text": key})
        negs = near_miss_targets(target, text)
        other = rng.choice(positives)
        if other[0] != target and other[3] != key and parse_eo(other[0]) \
                and not printed_anywhere(text, parse_eo(other[0])[0]):
            negs.append(other[0])
        for n in negs:
            neg_total += 1
            if find_citations(text, n):
                false_hits.append({"target": n, "text": key, "control_of": target})
    n_pos = sum(1 for p in positives if p[3] in texts)
    return {"positives": n_pos, "positives_located": pos_found, "positive_class_agreement": pos_agree,
            "recall": round(pos_found / n_pos, 4) if n_pos else None,
            "negatives": neg_total, "false_locations": len(false_hits),
            "false_location_rate": round(len(false_hits) / neg_total, 4) if neg_total else None,
            "passed": bool(n_pos) and not false_hits,
            "misses": misses[:50], "false_hits": false_hits[:50]}


def order_dates(repo: Path):
    """instrument_id -> signing date (ISO) from jobs/domesday-register (every census order), then later-events'
    OFR catalog for 1937 on, which wins where both have one."""
    import csv
    dates = {}
    for rel, key, col in (("jobs/domesday-register/output/REGISTER.csv", "instrument_id", "date"),
                          ("jobs/later-events/output/CATALOG_INDEX.csv", "id", "signing_date")):
        p = Path(repo) / rel
        if not p.is_file():
            continue
        with open(p, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                d = (r.get(col) or "").strip()
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
                    dates[r[key]] = d
    return dates


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path):
    out = []
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out
