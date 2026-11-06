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

LOCATOR_VERSION = "selden-locate-1"
LEGAL_CUTOFF = "2026-10-14"
ENDING = {"revocation", "rescission", "supersession", "replacement", "termination", "abolition", "vacation",
          "restoration"}
MODIFYING = {"amendment", "modification", "extension", "correction", "suspension"}
EO_ID = re.compile(r"EO:(\d{1,5})(?:-?([A-Za-z])|-(\d{1,2}))?$")
# Relation words cites.RELATIONS lacks that matter in later presidential documents.
CONTINUE_RE = re.compile(r"\bcontinu(?:e|ed|es|ing|ation)\b", re.I)
UNDER_RE = re.compile(r"\b(?:pursuant\s+to|under|in\s+accordance\s+with|as\s+(?:directed|required)\s+(?:by|in)"
                      r"|consistent\s+with|implement\w*)\b", re.I)


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


def find_citations(text: str, target: str, target_date: str | None = None, allow_date_only: bool = False):
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
    out, seen = [], set()
    for s, e, d, form in sorted(hits):
        lo, hi = cites.sentence_bounds(text, s, e)
        if (lo, hi) in seen:
            continue
        seen.add((lo, hi))
        seg = text[lo:hi]
        c = cites.classify(seg, s - lo, e - lo, prefer="text")
        mech = c["mechanism"]
        if mech == "cross_reference" and CONTINUE_RE.search(seg):
            mech = "continuation"
        out.append({
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
        and not hit["actor_named"]


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
                        | ({"target_printed_as_actor"} if hit["actor_named"] else set())),
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
    printed = {n for (_, _, n, _, _) in cites.eo_number_mentions(text)}
    cands = [num[:-1] if len(num) > 1 else None, num + "7", str(int(num) + 1)]
    return [f"EO:{c}" for c in cands if c and c not in printed and not c.startswith("0")]


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
        if other[0] != target and other[3] != key:
            printed = {f"EO:{n}{s}" for (_, _, n, s, _) in cites.eo_number_mentions(text)}
            if other[0] not in printed:
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
