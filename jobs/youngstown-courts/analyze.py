"""Youngstown analysis: one opinion row -> order citations and rule classes; opinion records -> court-hit rows;
selection under the committed-bytes budget; the SOURCES / FRAGMENTS / COURT_HITS writers. Standard library only.

A court hit is a lead. It never says an order was enjoined, vacated or upheld; it says a CourtListener opinion prints
the order's number and that the sentence around it holds (or does not hold) words of one of three kinds.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import opinion
import scan

ANALYSIS_VERSION = scan.CLASS_VERSION + "+" + opinion.OPINION_VERSION
OPINION_URL = "https://www.courtlistener.com/opinion/{cid}/{slug}/"
GRADE = "court_opinion_text_courtlistener_bulk (an opinion's text column from CourtListener's public bulk CSV)"
MECHANISM = {"enjoined_vacated_invalidated": "court_enjoined_vacated_or_invalidated_lead", "upheld": "court_upheld_lead",
             "interpreted": "court_interpreted_lead", "mentioned": "court_mention"}
MAX_MENTIONS_KEPT = 40


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


# ---- register -----------------------------------------------------------------------------------------------------

def load_register(path):
    """{instrument_id: signing date or ''} and {(number, suffix): instrument_id} from data/ORDER_DATES.csv."""
    dates, keys = {}, {}
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            iid = r["instrument_id"]
            m = re.fullmatch(r"EO:(\d+)([A-Z]?)", iid)
            if not m:
                continue
            dates[iid] = r["date"]
            keys[(int(m.group(1)), m.group(2))] = iid
    return dates, keys


# ---- one opinion --------------------------------------------------------------------------------------------------

def compact_mention(m, r):
    return {"s": m["start"], "e": m["end"], "form": m["form"], "list": m["in_list"], "range": m["range"],
            "cls": r["class"], "cue": r["cue"], "cue_text": r["cue_text"], "fam": r["cue_family"], "neg": r["negated"],
            "arg": r["argument_frame"], "lower": r["reports_lower_court"], "fed": r["federal_signal"],
            "state": r["state_signal"], "adj": r["adjacent_class"], "adjcue": r["adjacent_cue"],
            "sent": list(r["sentence_span"])}


def analyze_text(text: str, keys: dict):
    """({eo_id: {class, idx, mentions}}, Counter of unregistered numbers) for one opinion's derived text."""
    by_id = defaultdict(list)
    unreg = Counter()
    allm = scan.eo_mentions(text)
    refs = opinion.references(text, allm)
    for m in allm:
        iid = keys.get((m["number"], m["suffix"])) if m["suffix"] else keys.get((m["number"], ""))
        if iid is None:
            unreg[str(m["number"]) + m["suffix"]] += 1
            continue
        by_id[iid].append(m)
    orders = {}
    for iid, ms in by_id.items():
        ms = ms[:MAX_MENTIONS_KEPT]
        results = [scan.classify_mention(text, m["start"], m["end"]) for m in ms]
        cls, idx = scan.pair_class(results)
        key = (ms[0]["number"], ms[0]["suffix"])
        op = opinion.opinion_class(text, list(zip(ms, results)), refs.get(key, []))
        orders[iid] = {"class": cls, "idx": idx, "mentions": [compact_mention(m, r) for m, r in zip(ms, results)], "op": op}
    return orders, unreg


def analyze_row(row: dict, keys: dict):
    """(record or None, unregistered Counter, notes dict, raw text or None) for one CourtListener opinion row."""
    col, raw = scan.pick_text(row)
    if not col:
        return None, Counter(), {"no_text": 1}, None
    text = scan.derive_text(raw, col)
    orders, unreg = analyze_text(text, keys)
    if not orders:
        return None, unreg, {"text_no_registered_order": 1}, None
    rec = {"oid": int(row["id"]), "cid": int(row["cluster_id"]), "type": row.get("type", ""), "col": col,
           "raw_sha256": sha256(raw.encode("utf-8")), "raw_bytes": len(raw.encode("utf-8")),
           "text_sha256": sha256(text.encode("utf-8")), "chars": len(text),
           "ocr": row.get("extracted_by_ocr") in ("t", "true", "True"), "orders": orders, "analysis": ANALYSIS_VERSION}
    return rec, unreg, {}, raw


def save_raw(cache: Path, oid: int, raw: str):
    p = cache / "texts" / f"{oid % 1000:03d}" / f"{oid}.txt.gz"
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with gzip.open(tmp, "wb", compresslevel=6) as fh:
        fh.write(raw.encode("utf-8"))
    tmp.replace(p)


def load_text(cache: Path, rec):
    """(raw bytes sha ok?, derived text) of a held opinion, or (None, None) when the cache lost it."""
    p = cache / "texts" / f"{rec['oid'] % 1000:03d}" / f"{rec['oid']}.txt.gz"
    try:
        with gzip.open(p, "rb") as fh:
            raw = fh.read()
    except (OSError, EOFError):
        return None, None
    ok = sha256(raw) == rec["raw_sha256"]
    return ok, scan.derive_text(raw.decode("utf-8"), rec["col"])


# ---- court-hit rows -----------------------------------------------------------------------------------------------

LEAD_TYPES = {"020lead": 0, "010combined": 0, "015unamimous": 0, "025plurality": 1, "030concurrence": 2, "040dissent": 3}


def court_level(court_id, jurisdiction):
    if court_id == "scotus":
        return 0
    if jurisdiction == "F":
        return 1
    if jurisdiction in ("FD", "FB", "FBP", "FS"):
        return 2
    return 3


def build_rows(records, clusters, dockets, courts, citations, dates, stats):
    """One row per (order, cluster): the strongest class over the cluster's opinions, with court and date joined."""
    rows = {}
    for rec in records:
        cl = clusters.get(rec["cid"])
        if cl is None:
            stats["no_cluster_metadata"] += 1
            continue
        dk = dockets.get(cl["docket_id"]) or {}
        if not dk:
            stats["no_docket_metadata"] += 1
        court_id = dk.get("court_id", "")
        court = courts.get(court_id, {})
        date = cl.get("date_filed", "")
        for iid, info in rec["orders"].items():
            odate = dates.get(iid, "")
            if odate and date and date < odate:
                stats["dropped_opinion_dated_before_the_order"] += 1
                continue
            key = (iid, rec["cid"])
            ms = info["mentions"]
            fed = any(m["fed"] for m in ms)
            state_only = all(m["state"] and not m["fed"] for m in ms)
            op = info.get("op") or {"class": "mentioned", "sent": [0, 0], "via": "", "cue": "", "cue_text": "", "references": 0,
                                    "conflict": False, "a": -1, "b": -1}
            eff = op["class"] if scan.RANK[op["class"]] > scan.RANK[info["class"]] else info["class"]
            cand = {"eo": iid, "cid": rec["cid"], "oids": [rec["oid"]], "recs": [rec], "class": info["class"],
                    "op_class": op["class"], "eff_class": eff, "eff": scan.RANK[eff],
                    "rank": scan.RANK[info["class"]], "idx": info["idx"], "n_mentions": len(ms), "fed": fed,
                    "state_only": state_only, "court_id": court_id, "court": court.get("name", court_id),
                    "jurisdiction": court.get("jurisdiction", ""), "date": date, "case_name": cl.get("case_name", ""),
                    "slug": cl.get("slug", ""), "docket_number": dk.get("docket_number", ""),
                    "cites": citations.get(rec["cid"], []), "deciding": rec,
                    "lead": LEAD_TYPES.get(rec["type"], 4)}
            old = rows.get(key)
            if old is None:
                rows[key] = cand
                continue
            old["oids"].append(rec["oid"])
            old["recs"].append(rec)
            old["n_mentions"] += len(ms)
            old["fed"] = old["fed"] or fed
            old["state_only"] = old["state_only"] and state_only
            if (cand["eff"], cand["rank"], -cand["lead"]) > (old["eff"], old["rank"], -old["lead"]):
                for k in ("class", "rank", "idx", "deciding", "lead", "op_class", "eff_class", "eff"):
                    old[k] = cand[k]
    out = sorted(rows.values(), key=lambda r: (r["eo"], r["cid"]))
    for r in out:
        r["level"] = court_level(r["court_id"], r["jurisdiction"])
        r["url"] = OPINION_URL.format(cid=r["cid"], slug=r["slug"] or "case")
        r["eligible"] = r["fed"]
    return out


def priority(r):
    return (-r["eff"], 0 if r["fed"] else 1, r["level"], r["date"] or "9999", r["eo"], r["cid"])


def select_rows(rows, caps):
    """Rows to commit: every federal-signal hit of the three holding classes, then up to caps['mentions_per_order']
    mention-only hits per order (highest court first), until the byte caps are reached. Returns (selected, omitted
    counters). Each row's byte cost is measured by the caller through cost(r) = (hits, fragments, sources) bytes."""
    cost = caps["cost"]
    chosen, used = [], {"hits": 0, "fragments": 0, "sources": 0}
    seen_sources = set()
    omitted = Counter()
    mention_count = Counter()
    for r in sorted((r for r in rows), key=priority):
        if not r["eligible"]:
            omitted["no_federal_signal"] += 1
            continue
        if r["eff_class"] == "mentioned":
            if mention_count[r["eo"]] >= caps["mentions_per_order"]:
                omitted["mention_only_beyond_per_order_cap"] += 1
                continue
        c = cost(r, seen_sources)
        if any(used[k] + c[k] > caps[k] for k in used):
            omitted["byte_budget_" + r["eff_class"]] += 1
            continue
        for k in used:
            used[k] += c[k]
        seen_sources.update(r["oids"])
        if r["eff_class"] == "mentioned":
            mention_count[r["eo"]] += 1
        chosen.append(r)
    return chosen, omitted, used


# ---- writers ------------------------------------------------------------------------------------------------------

def quote_of(text: str, mention: dict, limit=1400):
    lo, hi = mention["sent"]
    q = text[lo:hi]
    if len(q) > limit:
        q = q[:limit]
        hi = lo + limit
    return q, lo, hi


def row_texts(r, cache):
    """(derived text of the deciding opinion, integrity ok) for a selected row, or (None, False)."""
    ok, text = load_text(cache, r["deciding"])
    if text is None:
        return None, False
    return text, ok and sha256(text.encode("utf-8")) == r["deciding"]["text_sha256"]


def hit_record(r, text, bulk):
    rec = r["deciding"]
    info = rec["orders"][r["eo"]]
    m = info["mentions"][info["idx"]] if info["idx"] >= 0 else info["mentions"][0]
    quote, lo, hi = quote_of(text, m)
    op = info.get("op") or {}
    olo, ohi = (op.get("sent") or [0, 0])
    same = [olo, ohi] == [lo, hi]
    oquote = text[olo:min(ohi, olo + 1400)] if ohi > olo else ""
    return {
        "eo": r["eo"], "court": r["court"], "court_id": r["court_id"], "jurisdiction": r["jurisdiction"],
        "date_filed": r["date"], "case_name": r["case_name"], "citations": "; ".join(r["cites"][:4]),
        "docket_number": r["docket_number"], "cluster_id": r["cid"], "opinion_ids": " ".join(map(str, r["oids"])),
        "url": r["url"], "class": r["class"], "cue": m["cue"], "cue_text": m["cue_text"],
        "scope": "sentence", "n_mentions": r["n_mentions"], "federal_signal": r["fed"],
        "span": re.sub(r"\s+", " ", quote).strip()[:500], "quote_span": f"{lo}-{hi}",
        "citation_span": f"{m['s']}-{m['e']}", "adjacent_class": m["adj"], "argument_frame": m["arg"],
        "reports_lower_court": m["lower"], "source": "courtlistener_bulk", "text_origin": rec["col"],
        "source_sha256": rec["raw_sha256"], "text_sha256": rec["text_sha256"],
        "bulk_snapshot": bulk["date"],
        "opinion_class": op.get("class", "mentioned"), "opinion_via": op.get("via", ""), "opinion_cue": op.get("cue", ""),
        "opinion_cue_text": op.get("cue_text", ""), "opinion_references": op.get("references", 0),
        "opinion_conflict": op.get("conflict", False),
        "opinion_span": "" if same else re.sub(r"\s+", " ", oquote).strip()[:500],
        "opinion_quote_span": f"{olo}-{ohi}", "opinion_span_same_as_sentence": same,
        "_opinion_quote": oquote, "_opinion_span": (olo, ohi)}, quote, (lo, hi), m


HIT_COLUMNS = ["eo", "court", "court_id", "jurisdiction", "date_filed", "case_name", "citations", "docket_number",
               "cluster_id", "opinion_ids", "url", "class", "cue", "cue_text", "scope", "n_mentions", "federal_signal",
               "span", "quote_span", "citation_span", "adjacent_class", "argument_frame", "reports_lower_court",
               "source", "text_origin", "source_sha256", "text_sha256", "bulk_snapshot", "opinion_class", "opinion_via",
               "opinion_cue", "opinion_cue_text", "opinion_references", "opinion_conflict", "opinion_span", "opinion_quote_span",
               "opinion_span_same_as_sentence"]


def fragment_record(r, hit, quote, span, m, source_id):
    return {"instrument_id": r["eo"], "kind": "court_decision_candidates", "produced_by": "youngstown-courts",
            "confidence_note": "Machine-located sentence of a court opinion that prints the order's number. The class "
                               "is a rule-based lead (words in the sentence), never a finding that the court enjoined, "
                               "vacated, upheld or construed the order. A person reads the opinion.",
            "data": [{
                "acting_id": f"CASE:cl-cluster-{r['cid']}", "acting_label": (r["case_name"] + " " + "; ".join(r["cites"][:2]))[:200].strip(),
                "target_id": r["eo"], "mechanism": MECHANISM[r["eff_class"]], "court_class": r["class"],
                "opinion_class": hit["opinion_class"], "opinion_via": hit["opinion_via"], "opinion_rule_cue": hit["opinion_cue"],
                "opinion_rule_cue_text": hit["opinion_cue_text"], "opinion_references_bound": hit["opinion_references"],
                "opinion_conflict_of_cues": hit["opinion_conflict"], "opinion_quote_span": hit["opinion_quote_span"],
                "opinion_quote": "" if hit["opinion_span_same_as_sentence"] else hit["_opinion_quote"],
                "opinion_quote_same_as_sentence": hit["opinion_span_same_as_sentence"],
                "rule_cue": m["cue"], "rule_cue_text": m["cue_text"], "classified_by": ANALYSIS_VERSION,
                "evidence_type": "court_opinion_sentence", "quote": quote, "quote_kind": "verbatim_sentence",
                "quote_span": f"{span[0]}-{span[1]}", "citation_span": f"{m['s']}-{m['e']}",
                "span_text": f"derived text of the opinion ({scan.DERIVE_VERSION}) from its {r['deciding']['col']} column",
                "date_candidate": r["date"], "date_basis": "CourtListener cluster date_filed (decision date, not the date of any effect on the order)",
                "court": r["court"], "court_id": r["court_id"], "case_name": r["case_name"], "citations": r["cites"][:4],
                "source_id": source_id, "source_url": r["url"], "source_sha256": r["deciding"]["raw_sha256"],
                "text_sha256": r["deciding"]["text_sha256"], "page_or_item": f"cluster {r['cid']} opinion {r['deciding']['oid']}",
                "text_path": None, "source": "courtlistener_bulk", "text_origin": r["deciding"]["col"],
                "federal_signal": r["fed"], "argument_frame": m["arg"], "reports_lower_court": m["lower"],
                "flags": sorted(f for f, v in (("argument_frame", m["arg"]), ("reports_lower_court", m["lower"]),
                                               ("adjacent_cue_only", bool(m["adj"]))) if v),
                "located_by": scan.SCAN_VERSION}]}


def source_record(rec, r_list, bulk, retrieved):
    """One SOURCES.jsonl record per held opinion. instrument_ids lists the opinion's own id first, then the orders it
    is attached to, so it never reads as a single order's own text (jobs/claim-kit/inputs.py attributes a text only to
    a record naming exactly one order, and this one names a court opinion)."""
    r0 = r_list[0]
    eos = sorted({r["eo"] for r in r_list})
    return {"source_id": f"courtlistener:opinion:{rec['oid']}", "instrument_ids": [f"COURT:cl-op-{rec['oid']}"] + eos,
            "url": r0["url"], "sha256": rec["raw_sha256"], "bytes": rec["raw_bytes"], "retrieved_utc": retrieved,
            "route": "courtlistener_bulk_csv_http_range", "page_or_item": f"cluster {rec['cid']} opinion {rec['oid']} ({rec['type']})",
            "text_path": None, "grade": GRADE, "acceptable_as_original": False, "role": "court_opinion_text",
            "notes": "Raw text column of the opinion row in CourtListener's bulk file, held in the runner cache "
                     "(JOB_CACHE_DIR), not committed. sha256 is of that column's UTF-8 bytes. Public Domain Mark; Free Law Project.",
            "source": "courtlistener_bulk", "text_column": rec["col"], "derive_version": scan.DERIVE_VERSION,
            "derived_text_sha256": rec["text_sha256"], "extracted_by_ocr": rec["ocr"], "opinion_id": rec["oid"],
            "cluster_id": rec["cid"], "bulk_object": bulk["key"], "bulk_etag": bulk.get("etag"),
            "bulk_last_modified": bulk.get("last_modified"), "court": r0["court"], "date_filed": r0["date"],
            "held_in": "runner cache only"}


def jsonl_line(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n"


def csv_line(cols, row):
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow([row.get(c, "") for c in cols])
    return buf.getvalue()
