"""Planted controls for the Youngstown job. Standard library only.

Positives: eight real opinions read in full (fixtures/CONTROL_OPINIONS.json, excerpts around every citation of the
order, with a hand label for each citation and for each opinion as a whole). Negatives: invented order numbers,
statute and Federal Register numbers with similar digits, a state executive order, an opinion older than the order.
Stream control: the same planted text inside a synthetic bzip2 CSV, read through the job's own segment decoder, row
scanner and row analysis. Measured, not asserted: every miss and false hit is listed.
"""
from __future__ import annotations

import bz2
import json
import random
import re
from collections import Counter
from pathlib import Path

import analyze
import bulk
import bz2seg
import scan

HERE = Path(__file__).resolve().parent
# Name patterns that identify each planted opinion among the real court hits of a full run.
CASE_PATTERNS = {"youngstown": r"youngstown", "korematsu": r"korematsu", "endo": r"\bendo\b", "wash": r"washington v\.? trump",
                 "reich": r"chamber of commerce.*reich", "contractors": r"contractors? ass", "dames": r"dames\s*&\s*moore",
                 "irap": r"international refugee"}


def fixtures(path=None):
    return json.loads((Path(path) if path else HERE / "fixtures" / "CONTROL_OPINIONS.json").read_text(encoding="utf-8"))


def locator_and_class_controls(cases, keys):
    """Locator recall (is the order number found at the hand-marked citation?), mention-level class accuracy against
    the hand labels, and opinion-level class agreement against the hand-read holding."""
    total = found = 0
    confusion = Counter()
    errors, misses = [], []
    pair_rows = []
    for c in cases:
        by_number = {}
        for ctx in c["contexts"]:
            total += 1
            w = ctx["window"]
            ms = [m for m in scan.eo_mentions(w) if m["number"] == ctx["number"] and m["start"] == ctx["mention"][0]]
            if not ms:
                misses.append({"case": c["key"], "i": ctx["i"], "number": ctx["number"]})
                continue
            found += 1
            m = ms[0]
            r = scan.classify_mention(w, m["start"], m["end"])
            confusion[(ctx["label"], r["class"])] += 1
            if r["class"] != ctx["label"]:
                errors.append({"case": c["key"], "i": ctx["i"], "number": ctx["number"], "label": ctx["label"],
                               "rule": r["class"], "cue": r["cue"], "cue_text": r["cue_text"],
                               "argument_frame": r["argument_frame"]})
            by_number.setdefault(ctx["number"], []).append(r)
        for eo, expected in c["expected_pair_class"].items():
            n = int(re.match(r"EO:(\d+)", eo).group(1))
            results = by_number.get(n, [])
            got, _ = scan.pair_class(results) if results else ("not_located", -1)
            pair_rows.append({"case": c["key"], "case_name": c["case_name"], "eo": eo, "expected_by_reading": expected,
                              "rule_class": got, "agree": got == expected, "located": bool(results),
                              "support_quote": c["pair_support_quote"], "source_url": c["source_url"]})
    labels = sorted({k[0] for k in confusion} | set(scan.CLASSES))
    per_class = {}
    for lab in labels:
        tp = confusion[(lab, lab)]
        lab_total = sum(v for (a, b), v in confusion.items() if a == lab)
        rule_total = sum(v for (a, b), v in confusion.items() if b == lab)
        per_class[lab] = {"labelled": lab_total, "rule_said": rule_total, "both": tp,
                          "recall": round(tp / lab_total, 3) if lab_total else None,
                          "precision": round(tp / rule_total, 3) if rule_total else None}
    n_cls = sum(confusion.values())
    return {
        "locator": {"citations_marked_by_hand": total, "located": found, "recall": round(found / total, 4) if total else None,
                    "misses": misses},
        "mention_class": {"n": n_cls, "correct": sum(v for (a, b), v in confusion.items() if a == b),
                          "accuracy": round(sum(v for (a, b), v in confusion.items() if a == b) / n_cls, 4) if n_cls else None,
                          "error_rate": round(1 - sum(v for (a, b), v in confusion.items() if a == b) / n_cls, 4) if n_cls else None,
                          "per_class": per_class, "confusion": {f"{a} -> {b}": v for (a, b), v in sorted(confusion.items())},
                          "errors": errors[:60],
                          "note": "Labels were written after the rule set was drafted, on the same opinions: an optimistic figure, "
                                  "not a held-out test."},
        "opinion_class": {"planted_positives": len(pair_rows), "agree": sum(1 for r in pair_rows if r["agree"]),
                          "rows": pair_rows,
                          "note": "Expected class is what the hand-read opinion holds about the order; the rule class sees only the "
                                  "sentences that print the number. Disagreement is the expected weakness of a sentence rule."},
    }


def absent_numbers(keys, k=3):
    have = {n for n, _ in keys}
    out = []
    for n in (99999, 77777, 31337, 14999, 12345):
        if n not in have:
            out.append(n)
    return out[:k]


def negative_controls(keys, dates):
    """Texts that must produce NO registered, federal-signalled court hit."""
    absent = absent_numbers(keys)
    texts = [(f"fake_number_{n}", f"The President issued Executive Order No. {n}, 17 Fed. Reg. 2955, directing the Secretary.")
             for n in absent]
    texts += [
        ("statute_section_digits", "Jurisdiction rests on 42 U.S.C. § 10340 and section 9066 of the Act, Pub. L. No. 12954."),
        ("federal_register_page", "See 82 Fed. Reg. 13,769 and 60 Fed. Reg. 12,954 (1995); 3 C.F.R. 10340 (1952)."),
        ("proclamation_and_board_order", "Proclamation No. 10340 and Order No. 9066 of the Wage Stabilization Board were filed."),
        ("year_after_lead", "Executive Order in effect since 1952 was reviewed by the board in 2011 and again in 1999."),
        ("order_in_prose", "The executive order issued last week by the Governor's office was not numbered."),
    ]
    rows, false_hits = [], []
    for name, text in texts:
        orders, unreg = analyze.analyze_text(text, keys)
        row = {"control": name, "registered_orders_found": sorted(orders), "unregistered_numbers_seen": dict(unreg)}
        rows.append(row)
        if orders:
            false_hits.append(row)
    return {"negatives": len(texts), "false_hits": len(false_hits), "false_hit_rate": round(len(false_hits) / len(texts), 4),
            "rows": rows, "false_hit_rows": false_hits}


def structure_controls(keys):
    """Citation shapes that must yield exactly the numbers listed (no page number or volume read as an order)."""
    cases = [
        ("Executive Order No. 12,954, 60 Fed.Reg. 13,023 (1995), on March 8, 1995", [12954]),
        ("E.O. 11,246, 3 C.F.R. 339 (1964-65 Compilation) (1965); E.O. 11,141, 3 C.F.R. 179 (1964-65 Compilation)", [11246, 11141]),
        ("Executive Orders 10925 and 11246", [10925, 11246]),
        ("Executive Orders Nos. 10925, 11114 and 11246, 30 Fed. Reg. 12319", [10925, 11114, 11246]),
        ("Exec. Orders Nos. 12276-12285, 46 Fed.Reg. 7913 -7932", list(range(12276, 12286))),
        ("Executive Order No. 9066, 7 Fed.Reg. 1407", [9066]),
        ("Exec. Order No. 10340, 17 Fed. Reg. 2955", [10340]),
        ("Executive Order 13769, “Protecting the Nation From Foreign Terrorist Entry”, 82 Fed. Reg. 8,977", [13769]),
        ("EXECUTIVE ORDER 10340", [10340]),
    ]
    rows, bad = [], []
    for text, expected in cases:
        got = [m["number"] for m in scan.eo_mentions(text)]
        row = {"text": text, "expected": expected, "got": got, "ok": got == expected}
        rows.append(row)
        if not row["ok"]:
            bad.append(row)
    return {"cases": len(cases), "wrong": len(bad), "rows": rows}


# ---- the same planted text through the real segment decoder, scanner and row analysis -------------------------------

HEADER = ["id", "date_created", "date_modified", "author_str", "per_curiam", "joined_by_str", "type", "sha1", "page_count",
          "download_url", "local_path", "plain_text", "html", "html_lawbox", "html_columbia", "html_anon_2020", "xml_harvard",
          "xml_scan", "html_with_citations", "extracted_by_ocr", "author_id", "cluster_id"]


def _q(v):
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def csv_row(oid, cid, plain="", html_cit="", typ="020lead"):
    f = {h: "" for h in HEADER}
    f.update({"id": str(oid), "date_created": "2022-07-24 12:05:34.084035+00", "date_modified": "2025-06-06 18:30:39.451266+00",
              "author_str": "Curiam", "per_curiam": "f", "type": typ, "plain_text": plain, "html_with_citations": html_cit,
              "extracted_by_ocr": "f", "cluster_id": str(cid)})
    return ",".join(_q(f[h]) if f[h] != "" or h in ("id", "date_created", "date_modified", "type", "cluster_id") else "" for h in HEADER) + "\n"


class _Mem:
    def __init__(self, b):
        self.b, self.size = b, len(b)

    def read_range(self, a, b):
        return self.b[a:b + 1]

    def open_stream(self, a, b):
        for i in range(a, b + 1, 40000):
            yield self.b[i:min(b + 1, i + 40000)]


def build_stream(cases, keys, seed=1584, filler_rows=600):
    """(bz2 bytes, expected {oid: set(eo ids)}, planted negative oids). Positives are real excerpts as html columns."""
    rng = random.Random(seed)
    words = ["".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(3, 9))) for _ in range(800)]
    parts = [",".join(HEADER) + "\n"]
    expected, negatives = {}, []
    oid = 1000
    plants = []
    for c in cases:
        for ctx in c["contexts"][:3]:
            plants.append((c, ctx))
    plant_at = set(rng.sample(range(filler_rows + len(plants)), len(plants)))
    queue = list(plants)
    for i in range(filler_rows + len(plants)):
        oid += 1
        if i in plant_at and queue:
            c, ctx = queue.pop()
            html_text = "<p>" + ctx["window"].replace("&", "&amp;").replace("<", "&lt;").replace("\n", "</p>\n<p>") + "</p>"
            parts.append(csv_row(oid, 50000 + oid, html_cit=html_text))
            iid = keys.get((ctx["number"], ""))
            if iid:
                expected.setdefault(oid, set()).add(iid)
        else:
            body = " ".join(rng.choice(words) for _ in range(rng.randint(30, 300)))
            if i % 17 == 0:
                body += " The executive branch and the chief executive officer. Exec. summary. E.O.C. v. Smith. See 42 U.S.C. § 10340."
                negatives.append(oid)
            parts.append(csv_row(oid, 50000 + oid, plain=body))
    return bz2.compress("".join(parts).encode("utf-8"), 1), expected, negatives


def stream_controls(cases, keys, seg_bytes=120_000):
    data, expected, negatives = build_stream(cases, keys)
    src = _Mem(data)
    level = bz2seg.stream_level(src)
    header = bulk.decode_header(src, level)
    bounds = bz2seg.block_boundaries(src, seg_bytes, level)
    eos = bz2seg.end_of_stream_bit(src)
    got, rows_seen = {}, Counter()

    def handle(raw):
        row = bulk.parse_row(raw, header)
        if row is None:
            rows_seen["unparsed"] += 1
            return
        rec, _, _, _ = analyze.analyze_row(row, keys)
        rows_seen["parsed"] += 1
        if rec:
            got.setdefault(rec["oid"], set()).update(rec["orders"])
    stats = []
    for k, sb in enumerate(bounds):
        last = k + 1 == len(bounds)
        eb = eos if last else bounds[k + 1]
        stats.append(bulk.scan_segment(src, level, sb, eb, last, bulk.prefilter_select, handle, extra_bytes=60_000, eos_bit=eos))
    missing = {o: sorted(v) for o, v in expected.items() if not v <= got.get(o, set())}
    extra = {o: sorted(v) for o, v in got.items() if o not in expected}
    dup = None
    return {"segments": len(bounds), "planted_positive_rows": len(expected), "found": len(expected) - len(missing),
            "recall": round((len(expected) - len(missing)) / len(expected), 4) if expected else None,
            "planted_negative_rows": len(negatives), "false_rows": len(extra), "missing": missing, "false": extra,
            "rows_unparsed": rows_seen["unparsed"], "row_start_lost": sum(s["row_start_lost"] for s in stats),
            "rows_selected": sum(s["rows_selected"] for s in stats)}


def stream_recall_in_hits(cases, rows):
    """Full runs: is each planted opinion among the real court hits (matched by case name and order id)?"""
    out = []
    for c in cases:
        pat = re.compile(CASE_PATTERNS[c["key"]], re.I)
        for eo, expected in c["expected_pair_class"].items():
            hit = [r for r in rows if r["eo"] == eo and pat.search(r["case_name"] or "")]
            out.append({"case": c["key"], "eo": eo, "found_in_bulk": bool(hit), "rule_class": hit[0]["class"] if hit else None,
                        "expected_by_reading": expected, "cluster_ids": [r["cid"] for r in hit][:5],
                        "citation": c["citation"]})
    return out
