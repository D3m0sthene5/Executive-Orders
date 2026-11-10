"""Pacioli: double-entry reconciliation of the later events that independent official compilers record for an order.

Named for Luca Pacioli, whose Summa (1494) set out double-entry bookkeeping: every amount entered in two books, so a
disagreement between them shows an error. Zero model tokens, offline: every input is a committed job output.

Three compilers keep tables of what later happened to executive orders, independently of one another:
  OFR   the Office of the Federal Register: the online disposition notes (jobs/later-events, read from the
        federalregister.gov API; NARA's HTML disposition tables print the same notes), the 1989 Codification's
        disposition table (jobs/ofr-codification-1989) and eCFR notes. One family: two OFR tables agreeing is not
        two entries (jobs/claim-drafts/drafts.py JOB_SOURCE_FAMILY).
  OLRC  the Office of the Law Revision Counsel: U.S. Code note status lines (jobs/current-law EVENT_CANDIDATES).
  BLM   the Bureau of Land Management: the Tables of Public Land Orders (jobs/shepard-citations, shepard_blm_plo_table).
The Lord 1944 WPA list is not a fourth: its entries summarize each order's own command and carry no later
dispositions (research/linnaeus/SOURCE_MEASURES.json).

An AGREED record is an (order, acting instrument) pair that at least two families record with the same relation
class (ending or modifying), the same whole-or-part scope and no disagreeing date. It is discovery evidence that lets
a producer skip the finding step. It is not a claim, a status or a certification: a claim still cites the acting
instrument's own held text, whose path and hash are given when the project holds it. Pairs that two families record
differently go to DISAGREED for an agent to read. A family's silence about a pair is never evidence: a pair recorded by
one family is neither agreed nor disagreed and is not listed. Human-certified: 0.
"""
from __future__ import annotations

import argparse
import ast
import collections
import csv
import hashlib
import json
import re
from pathlib import Path

csv.field_size_limit(min(2 ** 31 - 1, 10 ** 9))
SCHEMA = "pacioli-reconciliation/v1"
PATHS = {
    "tracker": "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv",
    "later": "jobs/later-events/output/EDGES.csv",
    "ofr1989": "jobs/ofr-codification-1989/output/FRAGMENTS.jsonl",
    "shepard": "jobs/shepard-citations/output/EDGES.csv",
    "usc_events": "jobs/current-law/output/EVENT_CANDIDATES.csv",
    "usc_sources": "jobs/current-law/output/SOURCES.jsonl",
    "plo_located": "jobs/selden-fr-acting/output/LOCATED.csv",
    "plo_sources": "jobs/selden-fr-acting/output/SOURCES.jsonl",
}
COMPILER = {"OFR": "Office of the Federal Register", "OLRC": "Office of the Law Revision Counsel",
            "BLM": "Bureau of Land Management"}
ENDING = ("revoc", "supersed", "supersess", "replace", "termin", "abol", "resc", "vacat", "nullif", "restor")
MODIFYING = ("amend", "modif", "extens", "correct", "suspen", "supplement", "continu")
NOTICE = ("Discovery evidence from independent official finding aids that record the same later event. Not a claim, "
          "status, original text or certification; a claim cites the acting instrument's own held text. A table's "
          "silence is never evidence.")


def read_csv(p):
    if not Path(p).is_file():
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_jsonl(p):
    out = []
    if Path(p).is_file():
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    out.append(json.loads(line))
    return out


def rel_class(mech):
    m = (mech or "").lower()
    if any(w in m for w in ENDING):
        return "ending"
    if any(w in m for w in MODIFYING):
        return "modifying"
    return None


def norm_actor(a):
    """'EO:9761', 'EO 9761', 'Proc:2318', 'PLO 945' -> 'EO:9761', 'PROC:2318', 'PLO:945'. Anything else is kept."""
    a = (a or "").strip()
    m = re.fullmatch(r"(?i)(EO|PLO|PROC)[: ]?\s*(\d+[A-Z]?)", a)
    return f"{m.group(1).upper()}:{m.group(2)}" if m else a


def _lit(v):
    if isinstance(v, (dict, list)):
        return v
    try:
        return ast.literal_eval(v) if isinstance(v, str) and v[:1] in "[{" else v
    except (ValueError, SyntaxError):
        return v


def entries(root):
    """(target, actor) -> family -> [entry]. Each entry pins its table: job, record id, locator, sha256, quote."""
    r = Path(root)
    ev = collections.defaultdict(lambda: collections.defaultdict(list))

    def add(fam, target, actor, mech, date, partial, job, rid, locator, sha, url, quote):
        c = rel_class(mech)
        actor = norm_actor(actor)
        if not c or not target or not actor or not re.fullmatch(r"(EO|PLO|PROC):\d+[A-Z]?", actor) or actor == target:
            return  # only instruments named by number can be matched explicitly
        ev[(target, actor)][fam].append({
            "family": fam, "compiler": COMPILER[fam], "job": job, "record_id": rid, "relation": mech,
            "relation_class": c, "scope": "part" if partial else "whole", "date_candidate": date or "",
            "locator": locator, "source_sha256": sha, "source_url": url, "quote": (quote or "")[:400]})

    for x in read_csv(r / PATHS["later"]):
        if (x.get("evidence_type") or "").startswith("ofr_note"):
            add("OFR", x["target_id"], x["acting_id"], x["mechanism"], x["date_candidate"], bool(x["qualifier"]),
                "later-events", x["edge_id"], x["page_or_item"], x["source_sha256"], x["source_url"], x["quote"])
    for f in read_jsonl(r / PATHS["ofr1989"]):
        if f.get("kind") != "later_event_candidates":
            continue
        for d in f.get("data") or []:
            src = _lit(d.get("source")) or {}
            add("OFR", f.get("instrument_id"), d.get("actor"), d.get("mechanism"), d.get("date_candidate"),
                bool(d.get("qualifier")), "ofr-codification-1989", "|".join(_lit(d.get("edge_ids")) or []),
                src.get("page_or_item", ""), src.get("sha256", ""), src.get("url", ""), d.get("quote"))
    for x in read_csv(r / PATHS["shepard"]):
        if x.get("evidence_type") == "shepard_blm_plo_table":
            add("BLM", x["target_id"], x["acting_id"], x["mechanism"], x["date_candidate"], bool(x["qualifier"]),
                "shepard-citations", x["edge_id"], x["page_or_item"], x["source_sha256"], x["source_url"], x["quote"])
    usc_sha = {s["source_id"]: (s.get("sha256", ""), s.get("url", "")) for s in read_jsonl(r / PATHS["usc_sources"])}
    for x in read_csv(r / PATHS["usc_events"]):
        fam = "OLRC" if x.get("system") == "usc" else "OFR"
        sha, url = usc_sha.get(x.get("source_id"), ("", ""))
        add(fam, x["subject_instrument_id"], x["acting_instrument_id"], x["event_type_candidate"], x["date_candidate"],
            x.get("scope_candidate") == "partial_candidate", "current-law", x["event_id"],
            f"{x['citation']}; {x['page_or_item']}", sha, url, x["sentence"])
    return ev


def actor_text(root, tracker, plo_texts, target, actor):
    """Where the acting instrument's own text is held, with the sha256 of the committed bytes; None if not held."""
    r = Path(root)
    if actor.startswith("EO:"):
        row = tracker.get(actor) or {}
        if row.get("text_evidence_tier") != "original_supported":
            return None
        n = actor.split(":", 1)[1]
        for rel in (f"jobs/fr-originals/output/texts/EO_{n}.txt", f"jobs/fr-originals/data/full_run/texts/EO_{n}.txt"):
            p = r / rel
            if p.is_file():
                return {"path": rel, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                        "grade": row.get("provisional_text_grade") or "original_supported"}
        return {"path": "", "sha256": row.get("provisional_text_sha256") or "", "grade": "original_supported",
                "note": "tracker credits an original; locate it with kit.py prepare"}
    if actor.startswith("PLO:"):
        rec = plo_texts.get((actor, target))
        if rec:
            return rec
    return None


def reconcile(root):
    r = Path(root)
    tracker = {x["instrument_id"]: x for x in read_csv(r / PATHS["tracker"])}
    located = {(x["actor"], x["target_id"]) for x in read_csv(r / PATHS["plo_located"]) if x.get("located") == "True"}
    plo_texts = {}
    for s in read_jsonl(r / PATHS["plo_sources"]):
        ids = s.get("instrument_ids") or []
        if not ids or not ids[0].startswith("PLO:") or not s.get("cache_path"):
            continue
        p = r / "jobs/selden-fr-acting/output" / s["cache_path"]
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != s.get("sha256"):
            continue
        for t in ids[1:]:
            if (ids[0], t) in located:
                plo_texts[(ids[0], t)] = {"path": "jobs/selden-fr-acting/output/" + s["cache_path"], "sha256": s["sha256"],
                                          "text_path": "jobs/selden-fr-acting/output/" + (s.get("text_path") or ""),
                                          "grade": s.get("grade", "")}
    agreed, disagreed = [], []
    for (t, a), fams in sorted(entries(root).items()):
        if len(fams) < 2:
            continue  # one family only: nothing to reconcile, and its silence elsewhere is no evidence
        row = tracker.get(t) or {}
        status = row.get("provisional_status") or ""
        ready = row.get("ready_for_human_review") or ""
        classes = {f: {e["relation_class"] for e in v} for f, v in fams.items()}
        scopes = {f: {e["scope"] for e in v} for f, v in fams.items()}
        dates = {f: {e["date_candidate"] for e in v if e["date_candidate"]} for f, v in fams.items()}
        common_class = set.intersection(*classes.values())
        common_scope = set.intersection(*scopes.values())
        dated = [d for d in dates.values() if d]
        common_date = set.intersection(*dated) if len(dated) >= 2 else (dated[0] if dated else set())
        base = {"schema": SCHEMA, "target_id": t, "acting_id": a, "families": sorted(fams),
                "target_provisional_status": status, "target_ready_for_human_review": ready,
                "entries": [e for f in sorted(fams) for e in fams[f]], "notice": NOTICE}
        problems = []
        if not common_class:
            problems.append("relation_class_differs")
        if not common_scope:
            problems.append("whole_vs_part_differs")
        if len(dated) >= 2 and not common_date:
            problems.append("date_differs")
        if problems:
            disagreed.append(dict(base, disagreement=problems,
                                  by_family={f: {"relation_classes": sorted(classes[f]), "scopes": sorted(scopes[f]),
                                                 "dates": sorted(dates[f])} for f in sorted(fams)}))
            continue
        cls = "ending" if "ending" in common_class else sorted(common_class)[0]
        scope = "whole" if "whole" in common_scope else "part"
        agreed.append(dict(base, relation_class=cls, scope=scope,
                           agreed_date=sorted(common_date)[0] if common_date else "",
                           actor_text=actor_text(root, tracker, plo_texts, t, a)))
    return agreed, disagreed, tracker


def write_jsonl(p, rows):
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        for x in rows:
            fh.write(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n")


def run(root, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    agreed, disagreed, tracker = reconcile(root)
    write_jsonl(out / "AGREED.jsonl", agreed)
    write_jsonl(out / "DISAGREED.jsonl", disagreed)
    und = {i for i, x in tracker.items() if x.get("provisional_status") == ""}
    dnr = {i for i, x in tracker.items() if x.get("provisional_status") and x.get("ready_for_human_review") == "no"}

    def orders(rows, pred=lambda x: True):
        return {x["target_id"] for x in rows if pred(x)}
    whole_end = lambda x: x["relation_class"] == "ending" and x["scope"] == "whole"  # noqa: E731
    held = lambda x: bool(x["actor_text"]) and bool(x["actor_text"].get("path"))  # noqa: E731

    def split(s):
        return {"orders": len(s), "undecided": len(s & und), "decided_not_ready": len(s & dnr)}
    summary = {
        "schema": SCHEMA, "inputs": dict(PATHS), "notice": NOTICE,
        "agreed_pairs": len(agreed), "disagreed_pairs": len(disagreed),
        "agreed_by_families": dict(collections.Counter("+".join(x["families"]) for x in agreed)),
        "disagreed_by_reason": dict(collections.Counter(p for x in disagreed for p in x["disagreement"])),
        "orders_with_agreed_event": split(orders(agreed)),
        "orders_with_agreed_whole_ending": split(orders(agreed, whole_end)),
        "orders_with_agreed_event_and_actor_text_held": split(orders(agreed, held)),
        "orders_with_agreed_whole_ending_and_actor_text_held": split(orders(agreed, lambda x: whole_end(x) and held(x))),
        "orders_on_disagreement_list": split(orders(disagreed)),
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    s = run(a.root, a.out)
    print(json.dumps({k: s[k] for k in ("agreed_pairs", "disagreed_pairs", "orders_with_agreed_whole_ending",
                                         "orders_with_agreed_whole_ending_and_actor_text_held",
                                         "orders_on_disagreement_list")}, indent=1))
    return s


if __name__ == "__main__":
    main()
