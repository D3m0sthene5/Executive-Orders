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
3. opus-media-match's re-fetch list (jobs/opus-media-match/output/REFETCH_LIST.jsonl):
   originals Opus downloaded but its release left out, one item per URL, with
   the sha256 Opus recorded so the copy can be checked byte for byte.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import embedded_cites
import fetch_ladder
import report_dates
import request_contract

STEPS = request_contract.STEPS
FETCH_QUEUE = "research/readiness/FETCH_QUEUE.jsonl"
SHARED = "research/stage20/output/SHARED_SOURCE_CASE_REVIEW_QUEUE.csv"
STATUTE = "research/stage20/output/STATUTE_CASE_REVIEW_QUEUE.csv"
STATUTE_INDEX = "research/stage20/output/STATUTE_FETCH_INDEX.csv"
HINTS = "research/stage14/QUEUES/INDEXED_CACHED_EO_SOURCE_HINTS.csv"
OPUS_REFETCH = "jobs/opus-media-match/output/REFETCH_LIST.jsonl"


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def eo_key(number):
    return "EO:" + number


def read_fetch_queue(path, eo_index=None, audit=None):
    """Validated wanted items plus unresolved problems; optional full audit list.

    Historical lines stay byte-for-byte unchanged. Every correction, split,
    duplicate and unresolved mapping remains in the audit, including originals.
    """
    path = Path(path)
    wanted, problems, seen = [], [], {}
    if not path.exists():
        return wanted, problems
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except ValueError as exc:
            problem = f"FETCH_QUEUE.jsonl line {n}: not JSON ({exc})"
            problems.append(problem)
            if audit is not None:
                audit.append({"schema": request_contract.VERSION, "line_number": n,
                              "source": str(path), "status": "invalid", "original_text": line,
                              "original_sha256": fetch_ladder.sha256_bytes(line.encode()),
                              "errors": [problem], "tasks": [], "corrections": []})
            continue
        rec = request_contract.normalize_request(raw, line_number=n, source=str(path))
        if audit is not None:
            audit.append(rec)
        if rec["errors"]:
            problems.append(f"FETCH_QUEUE.jsonl line {n}: " + "; ".join(rec["errors"]))
        for task in rec["tasks"]:
            if task["status"] != "valid":
                problems.append(f"FETCH_QUEUE.jsonl line {n}: {task['step']}: {task['reason']}")
                continue
            iid, urls, citation, step = (task[k] for k in ("instrument_id", "urls", "citation", "step"))
            # Preserve every previously valid wanted ID. Newly split tasks have
            # stable step suffixes, independent of line position or later appends.
            wanted_id = f"queue:{iid}:{citation or urls[0]}"
            if len(rec["tasks"]) > 1:
                wanted_id += f" <task:{step}>"
            if wanted_id in seen:
                if seen[wanted_id] == (urls, step):
                    task["duplicate_of"] = wanted_id
                    continue
                wanted_id = f"{wanted_id} [{urls[0]}]" if urls else wanted_id
                if wanted_id in seen:
                    wanted_id = f"{wanted_id} #{n}"
            seen[wanted_id] = (urls, step)
            task["wanted_id"] = wanted_id
            w = fetch_ladder.Wanted(wanted_id=wanted_id, instrument_ids=[iid], urls=urls,
                                    citation=citation, step=step, requested_by=task["requested_by"],
                                    extra=dict(task["extra"]))
            attach_eo_record(w, eo_index)
            note = w.extra["queue_note"]
            spec = report_dates.build_spec(citation, [iid], eo_signing_dates(eo_index, [iid], citation), note)
            if spec:
                w.extra["report_date"] = spec
            if not spec and not urls and fetch_ladder.parse_citation(citation)[0] is None:
                kids = embedded_children(w, eo_index)
                if kids:
                    task["embedded_wanted_ids"] = [k.wanted_id for k in kids]
                    wanted.extend(kids)
                    continue
            wanted.append(w)
    return wanted, problems


def eo_signing_dates(eo_index, instrument_ids, text):
    """{'12335': '1981-12-28'}: signing dates (OFR index) of the orders a request names. Empty without the index."""
    out = {}
    nums = [i.split(":", 1)[1] for i in instrument_ids if i.startswith("EO:")] + report_dates.eo_numbers(text)
    for n in dict.fromkeys(nums):
        hit = lookup_eo(eo_index, n)
        d = ((hit or {}).get("primary") or {}).get("signing_date")
        if d:
            out[n] = d
    return out


def own_fr_pages(text, instrument_ids, eo_index):
    """(volume, page) where the orders named in a request were themselves printed.

    Those pages are the orders' own publication (already held); a request that mentions them is
    asking about something else (the ending instrument, a report date), so they are not re-fetched."""
    nums = list(embedded_cites.eo_numbers(text))
    nums += [i.split(":", 1)[1] for i in instrument_ids if i.startswith("EO:")]
    pages = set()
    for n in nums:
        hit = lookup_eo(eo_index, n)
        kind, p = fetch_ladder.parse_citation(((hit or {}).get("primary") or {}).get("citation") or "")
        if kind == "FR":
            pages.add((p["volume"], p["page"]))
    return pages


def embedded_children(w, eo_index):
    """One work item per citation embedded in w.citation (see embedded_cites), or [] if none."""
    cites, overflow = embedded_cites.find_embedded_with_overflow(
        w.citation, skip_fr=own_fr_pages(w.citation, w.instrument_ids, eo_index))
    out = []
    for c in cites:
        out.append(fetch_ladder.Wanted(
            wanted_id=f"{w.wanted_id} <{c['cite']}>", instrument_ids=list(w.instrument_ids),
            urls=[], citation=c["cite"], step=w.step, requested_by=w.requested_by,
            extra={**(w.extra or {}), "parent_wanted_id": w.wanted_id, "parent_citation": w.citation,
                   "queue_note": (w.extra or {}).get("queue_note", ""),
                   "embedded_cite_kind": c["kind"],
                   "embedded_cites_not_queued": [o["cite"] for o in overflow]}))
    return out


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


def opus_refetch_key(row):
    """One work item per expected file: rows with the same expected sha256 are the same
    document under different URLs, so they are fetched once."""
    return "opus-refetch:" + (row.get("expected_sha256") or row.get("url") or "")


def opus_refetch_wanted(repo):
    """One item per distinct file on opus-media-match's re-fetch list (missing file = none)."""
    path = Path(repo) / OPUS_REFETCH
    groups, problems = {}, []
    if not path.exists():
        return [], problems
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError as exc:
            problems.append(f"REFETCH_LIST.jsonl line {n}: not JSON ({exc})")
            continue
        url = r.get("url")
        ids = r.get("instrument_ids") or []
        if not isinstance(url, str) or not url.startswith("https://") or not ids:
            problems.append(f"REFETCH_LIST.jsonl line {n}: needs an https url and instrument_ids")
            continue
        g = groups.setdefault(opus_refetch_key(r), {"urls": [], "ids": set(), "row": r})
        if url not in g["urls"]:
            g["urls"].append(url)
        g["ids"].update(ids)
    out = []
    for key, g in groups.items():
        r = g["row"]
        expect = "pdf" if any(".pdf" in u.split("?", 1)[0].lower() for u in g["urls"]) else "any"
        out.append(fetch_ladder.Wanted(
            wanted_id=key, instrument_ids=sorted(g["ids"]), urls=g["urls"], citation="",
            step="opus_media", requested_by="opus-media-match re-fetch list", expect=expect,
            extra={"expected_sha256": r.get("expected_sha256"), "expected_bytes": r.get("expected_bytes")}))
    out.sort(key=lambda w: (-len(w.instrument_ids), w.wanted_id))
    return out, problems
