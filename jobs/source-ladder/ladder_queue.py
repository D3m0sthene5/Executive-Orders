"""Build the source ladder's work queue.

1. research/readiness/FETCH_QUEUE.jsonl, if it exists. One JSON object per line:
   {"instrument_id": "EO:1234", "urls": ["https://..."], "citation": "66 Stat. 259",
    "step": "shared_sources", "requested_by": "Astra"}
   urls and citation are optional but at least one is needed; step defaults
   to original_text.
2. The Stage 20 shared sources not yet retrieved
   (research/stage20/output/SHARED_SOURCE_CASE_REVIEW_QUEUE.csv and
   STATUTE_CASE_REVIEW_QUEUE.csv), one item per authority, carrying every
   order that cites it.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import fetch_ladder

STEPS = ("original_text", "clause_inventory", "ending_or_current_basis", "savings_residuals",
         "counterevidence", "shared_sources", "opus_media")
FETCH_QUEUE = "research/readiness/FETCH_QUEUE.jsonl"
SHARED = "research/stage20/output/SHARED_SOURCE_CASE_REVIEW_QUEUE.csv"
STATUTE = "research/stage20/output/STATUTE_CASE_REVIEW_QUEUE.csv"
STATUTE_INDEX = "research/stage20/output/STATUTE_FETCH_INDEX.csv"
HINTS = "research/stage14/QUEUES/INDEXED_CACHED_EO_SOURCE_HINTS.csv"


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def eo_key(number):
    return "EO:" + number


def read_fetch_queue(path, eo_index=None):
    """Wanted items from FETCH_QUEUE.jsonl, plus a list of problems with bad lines."""
    path = Path(path)
    wanted, problems = [], []
    if not path.exists():
        return wanted, problems
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError as exc:
            problems.append(f"FETCH_QUEUE.jsonl line {n}: not JSON ({exc})")
            continue
        iid = r.get("instrument_id")
        urls = r.get("urls") or []
        citation = r.get("citation") or ""
        step = r.get("step") or "original_text"
        if not isinstance(iid, str) or not iid.startswith("EO:"):
            problems.append(f"FETCH_QUEUE.jsonl line {n}: instrument_id must look like EO:1234")
            continue
        if not isinstance(urls, list) or not all(isinstance(u, str) for u in urls):
            problems.append(f"FETCH_QUEUE.jsonl line {n}: urls must be a list of strings")
            continue
        if step not in STEPS:
            problems.append(f"FETCH_QUEUE.jsonl line {n}: unknown step {step!r}")
            continue
        if not urls and not citation:
            problems.append(f"FETCH_QUEUE.jsonl line {n}: needs urls or a citation")
            continue
        urls = [u if not u.startswith("http://") else "https://" + u[7:] for u in urls]
        w = fetch_ladder.Wanted(wanted_id=f"queue:{iid}:{citation or urls[0]}", instrument_ids=[iid],
                                urls=urls, citation=citation, step=step,
                                requested_by=str(r.get("requested_by") or ""))
        attach_eo_record(w, eo_index)
        wanted.append(w)
    return wanted, problems


_LOWER_INDEX = {}


def lookup_eo(eo_index, number):
    """Index entry for an order number, ignoring case ('7933A' finds 'EO:7933a')."""
    if not eo_index:
        return None
    hit = eo_index.get(eo_key(number))
    if hit:
        return hit
    key = id(eo_index)
    cached = _LOWER_INDEX.get(key)
    if cached is None or cached[0] is not eo_index:
        cached = (eo_index, {k.lower(): v for k, v in eo_index.items()})
        _LOWER_INDEX[key] = cached
    return cached[1].get(eo_key(number).lower())


def attach_eo_record(w, eo_index):
    kind, p = fetch_ladder.parse_citation(w.citation)
    if kind == "EO" and eo_index:
        hit = lookup_eo(eo_index, p["number"])
        if hit:
            w.eo_record = hit["primary"]


def load_hints(repo):
    """Mirror URLs (mostly American Presidency Project) cached by Stage 14, per order."""
    path = Path(repo) / HINTS
    out = {}
    if not path.exists():
        return out
    for r in read_csv(path):
        urls = [u.strip() for u in re.split(r"[|\s]+", r.get("cached_urls") or "") if u.strip().startswith("https://")]
        if urls:
            out[r["instrument_id_hint"]] = urls
    return out


def citation_key(authority):
    """Merge spellings like '48 U.S.C. 863' and '48 U.S.C. 863)'."""
    kind, p = fetch_ladder.parse_citation(authority)
    if kind is None:
        return authority
    return kind + ":" + ":".join(str(p[k]) for k in sorted(p) if k != "as_cited")


def shared_source_wanted(repo, eo_index=None, hints=None):
    repo = Path(repo)
    acquired = set()
    if (repo / STATUTE).exists():
        acquired = {(r["source_key"], r["instrument_id"]) for r in read_csv(repo / STATUTE)
                    if r.get("acquired_pdf_bytes") == "yes"}
    known_urls = {}
    if (repo / STATUTE_INDEX).exists():
        for r in read_csv(repo / STATUTE_INDEX):
            if r.get("source_url", "").startswith("https://"):
                known_urls["STAT::" + r["citation"]] = r["source_url"]
    groups = {}
    for r in read_csv(repo / SHARED):
        auth, cited = r["authority"].strip(), r["cited_in"].strip()
        if r.get("source_already_retrieved") == "yes" or (auth, cited) in acquired:
            continue
        key = citation_key(auth)
        g = groups.setdefault(key, {"authorities": [], "ids": set()})
        if auth not in g["authorities"]:
            g["authorities"].append(auth)
        g["ids"].add(cited)
    out = []
    for key, g in groups.items():
        auth = min(g["authorities"], key=lambda a: (a.rstrip(").;, ") != a, len(a)))  # cleanest spelling
        urls = [known_urls[a] for a in g["authorities"] if a in known_urls]
        w = fetch_ladder.Wanted(wanted_id=auth, instrument_ids=sorted(g["ids"]), urls=urls,
                                citation=auth, step="shared_sources", requested_by="stage20 shared-source queue",
                                extra={"authorities": g["authorities"]})
        attach_eo_record(w, eo_index)
        kind, p = fetch_ladder.parse_citation(auth)
        if kind == "EO" and hints:
            w.mirror_urls = list(hints.get(eo_key(p["number"]), []))
        out.append(w)
    out.sort(key=lambda w: (-len(w.instrument_ids), w.wanted_id))
    return out
