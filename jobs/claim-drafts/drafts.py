"""Job 8: one pre-filled DRAFT whole-lifecycle claim per order.

It merges what the other jobs found (CLAIM FRAGMENTS and SOURCE RECORDS in
jobs/*/output/, or the folders named in CLAIM_DRAFTS_INPUTS) plus the Stage 21
original PDFs and the Stage 20 shared-source queues into one draft per order:

* ``claim``: an object in the exact Stage 19 format (schema
  eo-lifecycle-claim/v1). Only mechanical facts are filled in: the provisional
  status copied from the ledger, a strong original-text candidate, and the
  drafted clause texts with their sources. Every judgment field is left empty
  on purpose, including later_source_search (machine searches are proposals).
  A draft committed unchanged lights no readiness step except original_text:
  with no clause inventory it holds one placeholder clause so the gate does
  not stop early (see placeholder_clause).
* ``_draft``: a side object saying what was machine-filled and from where, what
  still needs an agent's judgment, the candidates to choose from (already in
  the claim's field shapes), conflicts between candidates, the gate errors that
  remain, the claim-checker results, and the readiness steps the draft would
  satisfy once an agent confirms it.

Nothing here is a legal conclusion. Nothing is written to research/readiness/
claims/ (that folder holds agent-asserted claims), and no status, ledger or
count is changed. No network requests are made.
"""

import collections
import copy
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sys
import time
import urllib.parse

# Never leave __pycache__ folders in other jobs' folders when importing their code.
sys.dont_write_bytecode = True

HERE = pathlib.Path(__file__).resolve().parent
JOB_NAME = "claim-drafts"
DRAFT_SCHEMA = "eo-claim-draft/v1"
CLAIM_SCHEMA = "eo-lifecycle-claim/v1"
LEGAL_CUTOFF = "2026-10-14"

# Jobs whose outputs are merged (any other jobs/*/output with FRAGMENTS.jsonl is merged too).
KNOWN_JOBS = ["fr-originals", "source-ladder", "clause-drafts", "later-events", "current-law", "opus-media-match",
              "ofr-compilations", "isthmian-canal-1911", "indian-reservations-1912", "richardson-volumes",
              "ofr-codification-1989", "namier"]
# Official government printings of the orders' texts (GPO / Office of the Federal Register compilations): their
# original_representation fragments are graded like fr-originals (a find flagged needs_page_check is never strong).
OFFICIAL_COMPILATION_JOBS = {
    "ofr-compilations": "Office of the Federal Register compilation (GPO 1974)",
    "isthmian-canal-1911": "Isthmian Canal Commission compilation (GPO 1911)",
    "indian-reservations-1912": "Indian-reservation orders compilation (GPO 1912)",
}
# Printed compilations transcribed from department records and newspapers (Richardson's Messages and Papers): a lead
# to the original only. Never strong, never offered as the original in the feasibility test, never counted.
COMPILED_TRANSCRIPTION_JOBS = {"richardson-volumes": "Richardson, Messages and Papers of the Presidents (GPO 1896-99)",
                               "app-executive-orders": "American Presidency Project (UCSB) web transcription",
                               "app-transcriptions": "American Presidency Project (UCSB) web transcription"}
# What each compiled transcription is, for the proposal's "why".
TRANSCRIPTION_NATURE = {"richardson-volumes": "a printed compilation transcribed from department records and newspapers",
                        "app-executive-orders": "an editorial transcription published on the web, read live or from "
                                                "a web-archive capture of the page",
                        "app-transcriptions": "an editorial transcription published on the web, read live or from "
                                              "a web-archive capture of the page"}
# The OFR 1989 Codification: editorial status as of 1989-01-20 (disposition table, and the codified texts as amended
# to that day). Its later-event fragments may become whole-order-end proposals; its in-force rows are current-law
# LEADS only (a 1989 snapshot never reaches the 2026-10-14 cutoff). Its texts are never originals.
CODIFICATION_JOB = "ofr-codification-1989"
CODIFICATION_SNAPSHOT_DATE = "1989-01-20"
CODIFICATION_FLAG = "ofr_codification_1989_editorial"
CODIFICATION_BASIS_CODE = "ofr_codification_1989_in_force"
# later-events offers a whole-order end only for these mechanisms with no qualifier (FULL_END_MECHANISMS there).
FULL_END_MECHANISMS = {"revocation", "rescission", "supersession_or_revocation"}
# Jobs that read the same underlying source: the later-events OFR catalog notes are the online edition of the 1989
# disposition tables, so the two agreeing is not independent corroboration.
JOB_SOURCE_FAMILY = {CODIFICATION_JOB: "later-events"}
NOT_INPUT_JOBS = {JOB_NAME, "claim-checker", "readiness-tracker", "example-hello", "_template"}
FRAGMENT_KINDS = {"operative_clauses", "later_event_candidates", "whole_order_end_candidates",
                  "current_predicate_candidates", "savings_leads", "original_representation", "family_rule_checks"}
TRACKER_STEPS = ["original_text", "clause_inventory", "ending_or_current_basis", "savings_residuals",
                 "counterevidence", "shared_sources", "opus_media"]
CLAIM_STEPS = TRACKER_STEPS[:5]

# Copy of the readiness tracker's mapping; the tracker's own is imported when present.
FALLBACK_GATE_ERROR_STEP = [
    ("original_representation", "original_text"), ("operative_clauses_empty", "clause_inventory"),
    ("_scope_id", "clause_inventory"), ("_original_text_or_source", "clause_inventory"),
    ("_state", "clause_inventory"), ("_later_event", "clause_inventory"), ("_not_object", "clause_inventory"),
    ("_current_predicate", "ending_or_current_basis"), ("_first_end", "ending_or_current_basis"),
    ("whole_order", "ending_or_current_basis"), ("continuing_clause", "ending_or_current_basis"),
    ("savings_residuals", "savings_residuals"), ("bounded_later_search", "counterevidence"),
]

P = {
    "universe": "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv",
    "decided": "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv",
    "causal": "research/stage19/output/CAUSAL_QUEUE.csv",
    "crosswalk": "research/stage21/sources_index/OFFICIAL_SOURCE_CASE_CROSSWALK.csv",
    "custody": "research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv",
    "shared": "research/stage20/output/SHARED_SOURCE_CASE_REVIEW_QUEUE.csv",
    "statute": "research/stage20/output/STATUTE_CASE_REVIEW_QUEUE.csv",
    "media": "research/stage20/output/MEDIA_BATCH_ASSOCIATION_AUDIT.csv",
    "claim_gate_dir": "research/stage19/code",
    "tracker": "jobs/readiness-tracker/tracker.py",
    "checker": "jobs/claim-checker/checker.py",
    "claims_dir": "research/readiness/claims",
}

# Ranking of original-text candidates (lower is better).
ORIGINAL_RANK = {"stage21_per_document_pdf": 0, "opus_archived_media": 1, "fr_originals_high": 2,
                 "official_compilation_high": 3, "source_ladder_fr_page": 4, "fr_originals_needs_page_check": 5,
                 "official_compilation_needs_page_check": 6, "official_html_text": 7, "compiled_transcription_lead": 8}
STRONG_ORIGINALS = {"stage21_per_document_pdf", "opus_archived_media", "fr_originals_high", "official_compilation_high"}
# Candidates that can never be the original by themselves, even after a page check.
LEAD_ONLY_ORIGINALS = {"compiled_transcription_lead"}
CLAUSE_GRADE_RANK = {"official_fr_pdf_text_layer": 0, "official_fr_html_text": 1, "federalregister_gov_edition": 2,
                     "official_fr_scan_ocr_text": 3, "mirror_transcription_app": 4, "other_copy": 5}
BASIS_RANK = {"statutory_text_reference": 0, "cfr_authority_citation": 1, "references_in_text_note": 2,
              "cfr_text_reference": 3, "cfr_source_citation": 4, "statutory_note_reference": 5,
              "printed_eo_text": 6, "amending_order_in_status_line": 7, "cfr_appendix_text_reference": 8,
              CODIFICATION_BASIS_CODE: 20}
SOURCE_JOB_PRIORITY = {"later-events": 0, "current-law": 1, CODIFICATION_JOB: 2}
SAVINGS_RE = re.compile(
    r"shall not (?:be construed to )?(?:affect|impair|abate)|savings? (?:clause|provision)|"
    r"heretofore (?:taken|issued|prescribed|made|granted)|shall (?:remain|continue) in (?:full )?(?:force|effect)|"
    r"pending (?:proceedings|actions|suits|matters|cases)|rights? (?:accrued|vested|already acquired)|"
    r"without prejudice to|shall continue to be (?:valid|effective)|until (?:modified|superseded|revoked)",
    re.I)
# 'section 2', 'sections 1 and 2', 'secs. 3, 4 and 7': the whole list after the word is captured.
SECTION_REF_RE = re.compile(r"(?:\bsec(?:tion)?s?\.?|\bparagraphs?|\bpar\.|\bpart)\s*"
                            r"([0-9]+[A-Za-z]?(?:\s*(?:,|and|or|&)\s*(?:and\s+)?[0-9]+[A-Za-z]?)*)", re.I)
SECTION_NUM_RE = re.compile(r"[0-9]+[A-Za-z]?")

CAPS = {"later_events": 40, "current_predicate": 25, "whole_order_end": 25, "savings_leads": 15, "quote_chars": 300}


# ------------------------------------------------------------------ helpers

def exact_date(value):
    if not isinstance(value, str):
        return False
    try:
        return dt.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def date_part(value):
    """'2026-10-17T19:20:47Z' -> '2026-10-17' (or None)."""
    if isinstance(value, str) and len(value) >= 10 and exact_date(value[:10]):
        return value[:10]
    return None


class Unusable(Exception):
    """A sibling-job value has a type this job cannot use (for example a list where text belongs)."""


def as_text(value, field="value", required=False):
    """Text or None. Raises Unusable for lists, dicts, numbers and other non-text values."""
    if value is None:
        if required:
            raise Unusable(f"{field} is missing")
        return None
    if isinstance(value, str):
        return value.strip()
    raise Unusable(f"{field} is a {type(value).__name__}, not text")


def as_list(value):
    """A list (non-lists become [])."""
    return list(value) if isinstance(value, list) else []


def text_or_empty(value):
    return value if isinstance(value, str) else ""


def compact(d):
    """The dict without keys whose value is None, '', [] or {} (keeps committed output small)."""
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


# Mechanisms of later events that end (part of) an order rather than change it.
ENDING_MECHANISM_RE = re.compile(r"revo|supersed|supersession|terminat|expir|rescind|rescission|abolish|suspen", re.I)
# The later-events OFR catalog covers orders from 1937 on; earlier endings are not in it.
CATALOG_COVERAGE_START_YEAR = 1937
PLACEHOLDER_SCOPE_ID = "DRAFT-PLACEHOLDER-no-clause-inventory"


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def short_hash(value, n=12):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()[:n]


def truncate(text, n=None):
    n = n or CAPS["quote_chars"]
    if not isinstance(text, str):
        return text, False
    return (text, False) if len(text) <= n else (text[:n] + " ...", True)


def order_sort_key(iid):
    m = re.match(r"EO:(\d+)(.*)$", iid or "")
    return (0, int(m.group(1)), m.group(2)) if m else (1, 0, iid or "")


def read_csv(path):
    path = pathlib.Path(path)
    if not path.is_file():
        return None
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def read_jsonl(path, problems, label):
    rows = []
    path = pathlib.Path(path)
    if not path.is_file():
        return rows
    bad = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except (ValueError, RecursionError):
                bad += 1
                continue
            if isinstance(obj, dict):
                rows.append(obj)
            else:
                bad += 1
    if bad:
        problems.append(f"{label}: {bad} lines were not JSON objects and were skipped")
    return rows


def read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
        return obj if isinstance(obj, dict) else {}
    except (OSError, ValueError):
        return {}


def safe_child(base, rel):
    """base/rel if rel is a relative path that stays inside base, else None."""
    if not isinstance(rel, str) or not rel.strip():
        return None
    rel = rel.split("#", 1)[0]
    p = pathlib.PurePosixPath(rel.replace("\\", "/"))
    if p.is_absolute() or ".." in p.parts or re.match(r"^[A-Za-z]:", rel):
        return None
    return pathlib.Path(base).joinpath(*p.parts)


def is_within(path, parent):
    try:
        pathlib.Path(path).resolve().relative_to(pathlib.Path(parent).resolve())
        return True
    except ValueError:
        return False


def claim_ref(src):
    """The claim-compatible part of a source reference (or None)."""
    if not isinstance(src, dict):
        return None
    if src.get("archival_id") and src.get("local_file_sha256"):
        ref = {"archival_id": src["archival_id"], "local_file_sha256": src["local_file_sha256"]}
        if isinstance(src.get("sha256"), str):
            ref["sha256"] = src["sha256"]
    elif isinstance(src.get("url"), str):
        ref = {"url": src["url"]}
        if isinstance(src.get("sha256"), str):
            ref["sha256"] = src["sha256"]
    else:
        return None
    ref["page_or_item"] = src.get("page_or_item")
    return ref


def compress_errors(errors):
    """['clause_0_state', 'clause_1_state', 'schema'] -> ['clause_*_state x2', 'schema']."""
    c = collections.Counter(re.sub(r"clause_\d+_", "clause_*_", e) for e in errors)
    return [k if n == 1 else f"{k} x{n}" for k, n in sorted(c.items())]


# ------------------------------------------------------------------ inputs

class InputDir:
    def __init__(self, job, path, origin):
        self.job = job
        self.path = pathlib.Path(path)
        self.origin = origin  # never an absolute local path (it appears in committed output)
        self.summary = read_json(self.path / "SUMMARY.json")
        # Per-order coverage of a job's own machine search (SEARCH_COVERAGE.csv: instrument_id, search_id,
        # covered 1/0, note). A search listed there is entered only for the orders it covers; an order it lists
        # as not covered gets the search with the note as its coverage warning; an unlisted order gets nothing.
        self.search_coverage = {}
        for row in read_csv(self.path / "SEARCH_COVERAGE.csv") or []:
            if row.get("instrument_id") and row.get("search_id"):
                self.search_coverage[(row["instrument_id"], row["search_id"])] = row

    def label(self):
        return f"{self.job}@{self.origin}"


def infer_job(path):
    path = pathlib.Path(path)
    s = read_json(path / "SUMMARY.json")
    if isinstance(s.get("job"), str) and s["job"].strip():
        return s["job"].strip()
    fr = path / "FRAGMENTS.jsonl"
    if fr.is_file():
        with open(fr, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if isinstance(obj, dict) and isinstance(obj.get("produced_by"), str):
                    return obj["produced_by"]
    for part in reversed(path.resolve().parts):
        for j in KNOWN_JOBS:
            if part == j or part.startswith(j + "-") or part.startswith(j + "_"):
                return j
    return None


def portable_origin(path, repo):
    """'env:<path relative to the repo>' or 'env:<folder name>' - no absolute local paths in output."""
    path = pathlib.Path(path).resolve()
    try:
        return "env:" + path.relative_to(pathlib.Path(repo).resolve()).as_posix()
    except ValueError:
        return "env:.../" + "/".join(path.parts[-2:])


def run_status_note(out_dir, job):
    """A note when the runner's STATUS.json says that job's last run failed (None otherwise)."""
    st = read_json(pathlib.Path(out_dir) / "STATUS.json")
    result = st.get("result")
    if isinstance(result, str) and result.strip() and result.strip().lower() not in ("succeeded", "success", "ok"):
        return (f"{job}: STATUS.json says its last run {result.strip()!r} (exit code {st.get('exit_code')}); "
                "its output was NOT merged - rerun that job first")
    return None


def discover_inputs(repo, env_value=None):
    """[InputDir], notes. env_value: 'dir;dir' or 'job=dir;job=dir' (CLAIM_DRAFTS_INPUTS)."""
    notes, inputs, seen_paths = [], [], set()
    if env_value and env_value.strip():
        for item in re.split(r"[;\n]", env_value):
            item = item.strip()
            if not item:
                continue
            job = None
            m = re.match(r"^([A-Za-z0-9_.-]+)=(.+)$", item)
            if m and not re.match(r"^[A-Za-z]$", m.group(1)):
                job, item = m.group(1), m.group(2).strip()
            path = pathlib.Path(item)
            shown = portable_origin(path, repo)
            if not path.is_dir():
                notes.append(f"CLAIM_DRAFTS_INPUTS: {shown} is not a folder; skipped")
                continue
            key = str(path.resolve()).lower() if os.name == "nt" else str(path.resolve())
            if key in seen_paths:
                notes.append(f"CLAIM_DRAFTS_INPUTS: {shown} is listed more than once; read once")
                continue
            seen_paths.add(key)
            job = job or infer_job(path)
            if not job:
                notes.append(f"CLAIM_DRAFTS_INPUTS: could not tell which job wrote {shown} (no SUMMARY.json 'job', "
                             "no produced_by); write it as <job>=<folder>; skipped")
                continue
            if job in NOT_INPUT_JOBS:
                notes.append(f"CLAIM_DRAFTS_INPUTS: {shown} is {job} output, which is not merged; skipped")
                continue
            bad = run_status_note(path, job)
            if bad:
                notes.append(bad)
                continue
            print(f"  input folder {job}: {path.as_posix()}")  # the local path goes to the console only
            inputs.append(InputDir(job, path, shown))
        return inputs, notes
    jobs_dir = pathlib.Path(repo) / "jobs"
    names = sorted({p.name for p in jobs_dir.iterdir() if p.is_dir()}) if jobs_dir.is_dir() else []
    for name in names:
        if name in NOT_INPUT_JOBS:
            continue
        out = jobs_dir / name / "output"
        has = out.is_dir() and any((out / f).is_file() for f in ("FRAGMENTS.jsonl", "SOURCES.jsonl"))
        bad = run_status_note(out, name) if has else None
        if bad:
            notes.append(bad)
            has = False
            if name != "fr-originals":
                continue
        if name == "fr-originals":
            full = jobs_dir / name / "data" / "full_run"
            summ = read_json(out / "SUMMARY.json") if has else {}
            if (not has or summ.get("shrink_check") not in (None, "ok")) and full.is_dir():
                notes.append("fr-originals: output/ missing or its shrink_check is not 'ok'; using data/full_run/")
                inputs.append(InputDir(name, full, f"jobs/{name}/data/full_run"))
                continue
        if has:
            inputs.append(InputDir(name, out, f"jobs/{name}/output"))
        elif name in KNOWN_JOBS:
            notes.append(f"{name}: no output yet (jobs/{name}/output has no FRAGMENTS.jsonl or SOURCES.jsonl)")
    return inputs, notes


class Merged:
    """Everything read from the other jobs' output folders."""

    def __init__(self):
        self.frags = collections.defaultdict(lambda: collections.defaultdict(list))  # iid -> kind -> [(inp, frag)]
        self.sources_by_sha = collections.defaultdict(list)  # sha -> [(inp, record)]
        self.sources_by_url = collections.defaultdict(list)
        self.ladder_by_wanted = collections.defaultdict(list)  # wanted_id -> [(inp, record)]
        self.ladder_results = {}  # wanted_id -> RESULTS.csv row
        self.ladder_exhausted = collections.defaultdict(list)  # iid -> [EXHAUSTED_PROPOSED line]
        self.media_status = {}
        self.catalog = {}
        self.quarantine = {}
        self.not_segmented = {}
        self.fr_not_found = {}
        self.codified_1989 = {}  # iid -> (InputDir, CODIFIED_1989.csv row): printed as in force on 1989-01-20
        self.codification_book = None  # {url, sha256} of the 1989 Codification PDF
        self.searches = []  # [{job, complete, entry, scope_note}]
        self.problems = []
        self.counts = collections.Counter()
        self.inputs = []

    def has_any(self, iid):
        return iid in self.frags


def first_date_of_sources(records):
    ds = sorted(d for d in (date_part(r.get("retrieved_utc")) for r in records) if d)
    return ds[-1] if ds else None


def search_records_for(inp, records):
    """Later-source search records that a job's own SUMMARY shows it ran (complete or not)."""
    s, job, out = inp.summary, inp.job, []
    if job == "current-law":
        usc = s.get("usc") if isinstance(s.get("usc"), dict) else {}
        ecfr = s.get("ecfr") if isinstance(s.get("ecfr"), dict) else {}
        sample = bool(s.get("sample_mode")) or bool(s.get("job_limit"))
        checked_on = first_date_of_sources(records)
        if usc.get("release_point") and checked_on:
            titles = [t.get("member") for t in usc.get("titles") or [] if isinstance(t, dict)]
            through = usc.get("current_through_public_law_date") or usc.get("checked_through_for_entries")
            out.append({
                "job": job, "complete": not sample, "kind": "usc", "search_id": "current-law:usc",
                "scope_note": "" if not sample else f"sample run (JOB_LIMIT={s.get('job_limit')}): only "
                              f"{len(titles)} title file(s) read: {', '.join(t for t in titles if t)}",
                "entry": {
                    "repository": f"U.S. Code, Office of the Law Revision Counsel release point {usc['release_point']} "
                                  f"(USLM XML, {len(titles)} title files), statute text and editorial notes",
                    "query_or_scope": "every citation of this order by number (forms 'Executive Order', 'Ex. Ord.', "
                                      "'E.O.') in the text and notes of the titles read; edition current through "
                                      f"{through} (laws enacted after that date and on or before {LEGAL_CUTOFF} are "
                                      "not reflected)",
                    "checked_on": checked_on,
                    "searched_by": "jobs/current-law (machine search)"}})
        if ecfr.get("date") and checked_on:
            complete = (not sample) and ecfr.get("search_complete") is True
            titles = [str(t.get("title")) for t in ecfr.get("titles") or [] if isinstance(t, dict)]
            out.append({
                "job": job, "complete": complete, "kind": "ecfr", "search_id": "current-law:ecfr",
                "scope_note": "" if complete else ("eCFR search not complete (search_complete is not true)"
                                                   + (f"; sample run, CFR titles {', '.join(titles)} only" if sample else "")),
                "entry": {
                    "repository": f"eCFR point-in-time search as of {ecfr['date']} and GovInfo CFR bulk XML "
                                  f"({len(titles)} titles read)",
                    "query_or_scope": "full-text search for 'Executive Order', 'Executive Orders', 'E.O.', 'Ex. Ord.', "
                                      "'Exec. Order' and regulation text, authority and source citations naming this "
                                      "order",
                    "checked_on": checked_on,
                    "searched_by": "jobs/current-law (machine search)"}})
    elif isinstance(s.get("machine_searches"), list):
        # A job that declares its own complete search record (claim-kit reads the same declaration): the
        # record needs search_id, complete, entry{repository, query_or_scope, checked_on, searched_by}.
        for rec in s["machine_searches"]:
            if not isinstance(rec, dict) or not isinstance(rec.get("search_id"), str):
                continue
            e = rec.get("entry") if isinstance(rec.get("entry"), dict) else {}
            if not all(isinstance(e.get(k), str) and e.get(k) for k in ("repository", "query_or_scope", "checked_on")):
                continue
            out.append({"job": job, "complete": rec.get("complete") is True, "kind": "declared",
                        "search_id": rec["search_id"], "scope_note": text_or_empty(rec.get("scope_note")),
                        "entry": {"repository": e["repository"], "query_or_scope": e["query_or_scope"],
                                  "checked_on": e["checked_on"],
                                  "searched_by": e.get("searched_by") or f"jobs/{job} (machine search)"},
                        "per_order_coverage": bool(inp.search_coverage)})
    elif job == "later-events":
        checked_on = date_part(s.get("generated_utc")) or first_date_of_sources(records)
        if checked_on and s.get("catalog_records_used"):
            complete = s.get("catalog_complete") is True and not s.get("job_limit")
            out.append({
                "job": job, "complete": complete, "kind": "ofr_catalog", "search_id": "later-events:ofr_catalog",
                "scope_note": "" if complete else (f"catalog not complete: only {s.get('catalog_records_used')} "
                                                   f"catalog records read (JOB_LIMIT={s.get('job_limit')})"),
                "entry": {
                    "repository": "Federal Register executive-order catalog (federalregister.gov API v1, "
                                  "include_pre_1994_docs=true): Office of the Federal Register disposition notes",
                    "query_or_scope": f"disposition notes of {s.get('catalog_records_used')} catalog records (1937 "
                                      "onward) naming this order as amended, revoked, superseded or otherwise "
                                      f"affected, plus operative sentences in {s.get('text_documents_scanned', 0)} "
                                      "saved order texts",
                    "checked_on": checked_on,
                    "searched_by": "jobs/later-events (machine search)"}})
    return out


def load_inputs(inputs):
    m = Merged()
    m.inputs = inputs
    for inp in inputs:
        label = inp.label()
        frs = read_jsonl(inp.path / "FRAGMENTS.jsonl", m.problems, f"{label} FRAGMENTS.jsonl")
        # A producer may split its fragments to stay under the 95 MB file limit (clause-drafts: FRAGMENTS_APP.jsonl).
        for part in sorted(inp.path.glob("FRAGMENTS_*.jsonl")):
            frs += read_jsonl(part, m.problems, f"{label} {part.name}")
        srcs = read_jsonl(inp.path / "SOURCES.jsonl", m.problems, f"{label} SOURCES.jsonl")
        m.counts[f"fragments_read:{inp.job}"] += len(frs)
        m.counts[f"sources_read:{inp.job}"] += len(srcs)
        inp.n_fragments, inp.n_sources = len(frs), len(srcs)
        for f in frs:
            iid, kind = f.get("instrument_id"), f.get("kind")
            if not isinstance(iid, str) or not iid.startswith("EO:") or kind not in FRAGMENT_KINDS:
                m.counts["fragments_unusable"] += 1
                continue
            if f.get("data") is None:
                m.counts["fragments_without_data"] += 1
                continue
            m.frags[iid][kind].append((inp, f))
        for r in srcs:
            sha = r.get("sha256")
            if isinstance(sha, str) and re.fullmatch(r"[0-9a-fA-F]{64}", sha):
                m.sources_by_sha[sha.lower()].append((inp, r))
            if isinstance(r.get("url"), str):
                m.sources_by_url[r["url"]].append((inp, r))
            if inp.job == "source-ladder" and isinstance(r.get("wanted_id"), str):
                m.ladder_by_wanted[r["wanted_id"]].append((inp, r))
        if inp.job == "source-ladder":
            for row in read_csv(inp.path / "RESULTS.csv") or []:
                if row.get("wanted_id"):
                    m.ladder_results[row["wanted_id"]] = row
            for line in read_jsonl(inp.path / "EXHAUSTED_PROPOSED.jsonl", m.problems, f"{label} EXHAUSTED_PROPOSED"):
                if isinstance(line.get("instrument_id"), str):
                    m.ladder_exhausted[line["instrument_id"]].append(line)
        if inp.job == "opus-media-match":
            for row in read_csv(inp.path / "OPUS_CASE_MEDIA_STATUS.csv") or []:
                m.media_status[row.get("instrument_id")] = row
        if inp.job == "later-events":
            for row in read_csv(inp.path / "CATALOG_INDEX.csv") or []:
                if row.get("id"):
                    m.catalog[row["id"]] = row
        if inp.job == "clause-drafts":
            for row in read_csv(inp.path / "IDENTITY_QUARANTINE.csv") or []:
                m.quarantine[row.get("instrument_id")] = row
            for row in read_csv(inp.path / "NOT_SEGMENTED.csv") or []:
                m.not_segmented[row.get("instrument_id")] = row
        if inp.job == "fr-originals":
            for row in read_csv(inp.path / "NOT_FOUND.csv") or []:
                m.fr_not_found[row.get("instrument_id")] = row
        if inp.job == CODIFICATION_JOB:
            load_codification(m, inp, frs)
        m.searches += search_records_for(inp, srcs)
    return m


def load_codification(m, inp, frs):
    """The 1989 Codification's in-force rows (CODIFIED_1989.csv) and the PDF they are printed in."""
    book = None
    for f in frs:  # every fragment cites the same book: take its url and sha256
        for src in as_list(f.get("sources")) + [x.get("source") for x in as_list(f.get("data")) if isinstance(x, dict)]:
            if isinstance(src, dict) and isinstance(src.get("url"), str) and \
                    re.fullmatch(r"[0-9a-fA-F]{64}", str(src.get("sha256") or "")):
                book = {"url": src["url"], "sha256": src["sha256"].lower()}
                break
        if book:
            break
    if not book:  # no fragments: the job's own provenance record, when the folder sits in the repo
        prov = read_json(inp.path.parent / "data" / "PROVENANCE.json").get("book")
        if isinstance(prov, dict) and isinstance(prov.get("handle_url"), str) and \
                re.fullmatch(r"[0-9a-fA-F]{64}", str(prov.get("pdf_sha256") or "")):
            book = {"url": prov["handle_url"], "sha256": prov["pdf_sha256"].lower()}
    m.codification_book = book
    rows = read_csv(inp.path / "CODIFIED_1989.csv") or []
    for row in rows:
        iid = (row.get("census_id") or row.get("instrument_id") or "").strip()
        if iid.startswith("EO:"):
            m.codified_1989[iid] = (inp, row)
    m.counts[f"codified_1989_rows_read:{inp.job}"] += len(rows)
    if rows and not book:
        m.problems.append(f"{inp.label()}: CODIFIED_1989.csv read, but no book url/sha256 was found; its in-force "
                          "rows cannot be cited and are not proposed")


class RepoData:
    """The project files this job reads (all optional except the universe)."""

    def __init__(self, repo):
        repo = pathlib.Path(repo)
        self.notes = []
        uni = read_csv(repo / P["universe"])
        if uni is None:
            raise FileNotFoundError(f"missing {P['universe']} (add research/stage15/CENSUS to needs.txt)")
        self.universe = {r["id"]: r for r in uni if r.get("included_in_bibliography", "1") == "1"}
        self.decided = {r["instrument_id"]: r for r in self._csv(repo, "decided")}
        self.causal = {r["instrument_id"]: r for r in self._csv(repo, "causal")}
        self.crosswalk = {r["instrument_id"]: r for r in self._csv(repo, "crosswalk")}
        self.custody = {r["instrument_id"]: r for r in self._csv(repo, "custody")}
        statute_rows = self._csv(repo, "statute")
        self.statute_ok = {(r["source_key"], r["instrument_id"]) for r in statute_rows if r.get("acquired_pdf_bytes") == "yes"}
        self.shared = collections.defaultdict(list)
        for r in self._csv(repo, "shared"):
            self.shared[r.get("cited_in")].append(r)
        self.media_linked = set()
        for r in self._csv(repo, "media"):
            if r.get("association_grade") not in ("no_case_specific_evidence", ""):
                self.media_linked.update(x.strip() for x in (r.get("example_case_ids") or "").split("|") if x.strip())

    def _csv(self, repo, key):
        rows = read_csv(pathlib.Path(repo) / P[key])
        if rows is None:
            self.notes.append(f"{P[key]} not found; treated as empty")
            return []
        return rows


def load_gate(repo):
    path = pathlib.Path(repo) / P["claim_gate_dir"] / "claim_gate.py"
    spec = importlib.util.spec_from_file_location("claim_gate_for_drafts", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_step_mapper(repo):
    p = pathlib.Path(repo) / P["tracker"]
    if p.is_file():
        try:
            spec = importlib.util.spec_from_file_location("readiness_tracker_for_drafts", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.step_for_gate_error, "jobs/readiness-tracker/tracker.py"
        except Exception as exc:  # noqa: BLE001
            print(f"  note: could not import the tracker's gate-error mapping ({exc}); using a copy")

    def fallback(error):
        for fragment, step in FALLBACK_GATE_ERROR_STEP:
            if fragment in error:
                return step
        return None

    return fallback, "fallback copy in drafts.py"


def run_gate(gate, claim, status):
    try:
        return list(gate.validate_claim(claim, expected_status=status)), None
    except Exception as exc:  # noqa: BLE001 - a wrongly typed value must not stop the run
        return ["gate_raised_exception"], f"{type(exc).__name__}: {exc}"


# ------------------------------------------------------------- candidates

def source_custody(merged, ref):
    """Which merged SOURCES.jsonl records hold this reference's bytes (by sha256)."""
    if not isinstance(ref, dict):
        return []
    sha = (ref.get("sha256") or ref.get("local_file_sha256") or "")
    found = merged.sources_by_sha.get(sha.lower(), []) if isinstance(sha, str) else []
    return sorted({inp.job for inp, _ in found})


def declared_lead_only(f, d):
    """True when an original_representation record says it is a transcription, not an original."""
    for node in (f, d):
        if node.get("acceptable_as_original") is False or node.get("acceptable_as_original") == "false":
            return True
        if "transcription" in str(node.get("representation_type") or "") or \
                "mirror_transcription" in str(node.get("grade") or ""):
            return True
    return False


def original_candidates(iid, merged, rd, gate):
    cands = []
    cu = rd.custody.get(iid) or {}
    cx = rd.crosswalk.get(iid) or {}
    if cu.get("custody_state", "").startswith("PDF_BYTES_CAPTURED") and cu.get("sha256_source_bytes_if_present"):
        fr = cx.get("FR_citation_from_cached_index") or ""
        cands.append({
            "grade": "stage21_per_document_pdf",
            "ref": {"url": cu.get("official_PDF_candidate_URL"), "sha256": cu["sha256_source_bytes_if_present"],
                    "page_or_item": "whole per-document Federal Register PDF" + (f" ({fr})" if fr else "")},
            "from": "research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv",
            "repo_path": cu.get("source_repository_path"), "fr_citation": fr or None,
            "signing_date": cx.get("signing_date_from_cached_index") or None,
            "why": "official per-document PDF captured by Stage 21, bytes committed in the repo; identity and pages "
                   "not human-verified"})
    for inp, f in merged.frags.get(iid, {}).get("original_representation", []):
        d = f.get("data") if isinstance(f.get("data"), dict) else {}
        if inp.job == "opus-media-match":
            ref = claim_ref({"archival_id": d.get("archival_id"), "local_file_sha256": d.get("local_file_sha256"),
                             "sha256": d.get("sha256"), "page_or_item": d.get("page_or_item")})
            cands.append({"grade": "opus_archived_media", "ref": ref, "from": inp.label(),
                          "upstream_url": d.get("upstream_url"), "match_signals": d.get("match_signals"),
                          "why": "Opus archived file whose content names this order (unique_supported); "
                                 "candidate_unverified - read the page"})
        elif inp.job in OFFICIAL_COMPILATION_JOBS:
            # Same rule as fr-originals: medium/low location, or the job's own needs_page_check, is never strong.
            needs_check = bool(d.get("needs_page_check")) or d.get("location_confidence") not in ("high",)
            ref = claim_ref({"url": d.get("url"), "sha256": d.get("sha256"), "page_or_item": d.get("page_or_item")})
            cands.append({"grade": "official_compilation_needs_page_check" if needs_check else "official_compilation_high",
                          "ref": ref, "from": inp.label(), "source_id": d.get("source_id"),
                          "signing_date": d.get("signing_date"), "location_confidence": d.get("location_confidence"),
                          "match_level": d.get("match_level"), "text_path": d.get("text_path"),
                          "why": f"{OFFICIAL_COMPILATION_JOBS[inp.job]}: official government printing, OCR text; page "
                                 f"location {d.get('location_confidence')}" +
                                 ("; needs a page check before it can count (fr-originals rule)" if needs_check
                                  else "; location_verified is false - open the PDF pages")})
        elif inp.job in COMPILED_TRANSCRIPTION_JOBS or declared_lead_only(f, d):
            # A producer that declares its record a transcription (acceptable_as_original=false) is never graded
            # as an original, whatever its location confidence or page-check flag says.
            ref = claim_ref({"url": d.get("url"), "sha256": d.get("sha256"), "page_or_item": d.get("page_or_item")})
            name = COMPILED_TRANSCRIPTION_JOBS.get(inp.job, f"{inp.job} (declared acceptable_as_original=false)")
            nature = TRANSCRIPTION_NATURE.get(inp.job, "a transcription by the producer's own declaration")
            cands.append({"grade": "compiled_transcription_lead", "ref": ref, "from": inp.label(),
                          "source_id": d.get("source_id"), "signing_date": d.get("signing_date"),
                          "location_confidence": d.get("location_confidence"), "identified_by": d.get("identified_by"),
                          "text_path": d.get("text_path"),
                          "why": f"{name}: {nature}, NOT the signed or officially printed original; a "
                                 "lead to the original and to the text, never the original by itself"})
        else:
            needs_check = bool(d.get("needs_page_check")) or d.get("location_confidence") not in ("high",)
            ref = claim_ref({"url": d.get("url"), "sha256": d.get("sha256"), "page_or_item": d.get("page_or_item")})
            grade = "fr_originals_needs_page_check" if needs_check else "fr_originals_high"
            if inp.job != "fr-originals":
                grade = "fr_originals_needs_page_check"  # unknown producer: never strong
            cands.append({"grade": grade, "ref": ref, "from": inp.label(), "source_id": d.get("source_id"),
                          "fr_citation": d.get("fr_citation"), "signing_date": d.get("signing_date"),
                          "publication_date": d.get("publication_date"),
                          "location_confidence": d.get("location_confidence"),
                          "text_path": d.get("text_path"),
                          "why": ("page location " + str(d.get("location_confidence")) +
                                  ("; needs a page check before it can count (fr-originals rule)" if needs_check
                                   else "; location_verified is false - open the PDF pages"))})
    # The source ladder sometimes fetched this order as a shared source cited by other orders.
    num = iid.split(":", 1)[1]
    for inp, r in merged.ladder_by_wanted.get(f"EO::{num}", []):
        ref = claim_ref(r)
        cands.append({"grade": "source_ladder_fr_page", "ref": ref, "from": inp.label(),
                      "source_id": r.get("source_id"), "why": "found by the source ladder as a source cited by other "
                      "orders; page location heuristic: " + text_or_empty(r.get("notes"))[:200]})
    # Official text copies used by clause-drafts (not the printed page, so never strong).
    for inp, f in merged.frags.get(iid, {}).get("operative_clauses", []):
        if f.get("source_grade") in ("official_fr_html_text", "federalregister_gov_edition"):
            data = f.get("data") if isinstance(f.get("data"), list) else []
            src = next((c.get("original_source") for c in data if isinstance(c, dict)), None)
            if src:
                cands.append({"grade": "official_html_text", "ref": claim_ref(src), "from": inp.label(),
                              "why": f"official text edition used for the clause drafts ({f.get('source_grade')}); "
                                     "not the printed page"})
    seen, out = set(), []
    for c in sorted(cands, key=lambda c: ORIGINAL_RANK.get(c["grade"], 9)):
        ref = c.get("ref")
        if not ref or not gate.source_ok(ref):
            continue
        key = (ref.get("sha256") or ref.get("local_file_sha256"), ref.get("page_or_item"))
        if key in seen:
            continue
        seen.add(key)
        c["strong"] = c["grade"] in STRONG_ORIGINALS
        c["acceptable_as_original"] = c["grade"] not in LEAD_ONLY_ORIGINALS
        c["custody_records_in"] = source_custody(merged, ref)
        out.append(c)
    return out


def clause_inventory(iid, merged):
    """(chosen fragment info or None, alternates). Verifies text offsets where the text file is present."""
    options = []
    for inp, f in merged.frags.get(iid, {}).get("operative_clauses", []):
        data = f.get("data") if isinstance(f.get("data"), list) else []
        clauses = [c for c in data if isinstance(c, dict)]
        if not clauses:
            continue
        rank = (0 if f.get("segmentation_quality") == "good" else 1,
                CLAUSE_GRADE_RANK.get(text_or_empty(f.get("source_grade")), 9), -len(clauses))
        options.append((rank, inp, f, clauses))
    if not options:
        return None, []
    options.sort(key=lambda o: o[0])
    _, inp, f, clauses = options[0]
    texts, checks = {}, collections.Counter()
    meta = []
    for c in clauses:
        off = c.get("text_offsets") if isinstance(c.get("text_offsets"), dict) else {}
        verdict = "no_offsets"
        p = safe_child(inp.path, off.get("text_path"))
        if p is not None:
            if p not in texts:
                try:
                    with open(p, encoding="utf-8", newline="") as fh:
                        texts[p] = fh.read()
                except (OSError, UnicodeDecodeError):
                    texts[p] = None
            t = texts[p]
            if t is None:
                verdict = "text_file_missing"
            elif isinstance(off.get("start"), int) and isinstance(off.get("end"), int):
                verdict = "verified" if t[off["start"]:off["end"]] == c.get("original_operative_text") else "mismatch"
        checks[verdict] += 1
        meta.append({k: c.get(k) for k in ("scope_id", "label", "heading", "clause_kind", "related_orders",
                                             "contains_page_furniture", "needs_judgment", "draft_status")}
                    | {"text_offsets": off, "offsets_check": verdict})
    info = {"from": inp.label(), "fragment": f, "clauses": clauses, "meta": meta, "offset_checks": dict(checks),
            "source_grade": f.get("source_grade"), "segmentation_quality": f.get("segmentation_quality"),
            "segmentation_warnings": f.get("segmentation_warnings") or [], "structure": f.get("structure"),
            "source_id": f.get("source_id"), "alternate_sources": f.get("alternate_sources") or []}
    alternates = [{"from": o[1].label(), "source_grade": o[2].get("source_grade"),
                   "segmentation_quality": o[2].get("segmentation_quality"), "clauses": len(o[3])} for o in options[1:]]
    return info, alternates


def _le_item(item, inp, kind):
    """Normalise one later-events / current-law item to {proposal, meta}."""
    """Raises Unusable when actor, mechanism or date has a type this job cannot use."""
    if not isinstance(item, dict):
        return None
    if inp.job == "current-law":
        date = as_text(item.get("date_candidate"), "date_candidate")
        acting = as_text(item.get("acting_instrument_id"), "acting_instrument_id")
        actor_text = as_text(item.get("actor_candidate"), "actor_candidate")
        actor = acting or actor_text or ""
        mech_raw = as_text(item.get("event_type_candidate"), "event_type_candidate") or \
            as_text(item.get("mechanism_candidate"), "mechanism_candidate") or ""
        mech = mech_raw.split(" (")[0]
        ev_id = item.get("event_id")
        meta = {"actor_text": actor_text, "acting_instrument_id": acting,
                "acting_raw": item.get("acting_raw"), "acting_fr_citation": item.get("acting_fr_citation"),
                "mechanism_text": item.get("mechanism_candidate"), "scope_candidate": item.get("scope_candidate"),
                "qualifier": text_or_empty(item.get("scope_hint")) or text_or_empty(item.get("acting_scope")),
                "caution": item.get("caution"), "where": item.get("where"), "system": item.get("system"),
                "date_basis": item.get("date_basis_code"), "ids": [ev_id] if isinstance(ev_id, (str, int)) else [],
                "flags": [], "stated_effective_date_candidates": [], "date_candidates_conflicting": [],
                "later_reinstatement_candidates": []}
        quote = item.get("snippet")
    else:
        date = as_text(item.get("date_candidate", item.get("effective_date_candidate")), "date_candidate")
        actor = as_text(item.get("actor"), "actor") or ""
        acting = actor if actor.startswith("EO:") else None
        mech = as_text(item.get("mechanism"), "mechanism") or ""
        meta = {"actor_text": None, "acting_instrument_id": acting, "qualifier": text_or_empty(item.get("qualifier")),
                "date_basis": item.get("date_basis"), "ids": as_list(item.get("edge_ids")),
                "flags": [x for x in as_list(item.get("flags")) if isinstance(x, str)],
                "evidence_types": item.get("evidence_types"),
                "stated_effective_date_candidates": as_list(item.get("stated_effective_date_candidates")),
                "date_candidates_conflicting": as_list(item.get("date_candidates_conflicting")),
                "later_reinstatement_candidates": as_list(item.get("later_reinstatement_candidates")),
                "quote_kind": item.get("quote_kind"), "status": item.get("status")}
        quote = item.get("quote")
    if not actor and not mech:
        raise Unusable("neither an actor nor a mechanism")
    q, cut = truncate(quote if isinstance(quote, str) else None)
    src = claim_ref(item.get("source"))
    exact = date if exact_date(date) else None
    meta.update({"quote": q, "quote_truncated": cut, "from_job": inp.job, "from": inp.label(),
                 "date_raw": date if date != exact else None})
    if inp.job == CODIFICATION_JOB:
        meta["flags"] = sorted(set(meta["flags"]) | {CODIFICATION_FLAG})
        meta["caution"] = ("1989 OFR editorial codification: the Executive Orders disposition table states the order's "
                           f"status as of {CODIFICATION_SNAPSHOT_DATE} (OCR table cell, rows paired by position). The "
                           "date is the acting document's signing date, not its effective date; the order (or parts "
                           "of it) may have ceased earlier by its own terms. Read the acting instrument")
    if kind == "whole_order_end_candidates":
        proposal = {"date": exact, "actor": actor, "mechanism": mech, "source": src}
    else:
        # Not 'effective_date': the value is the acting instrument's signing or printed date. The agent renames
        # the key to effective_date only after confirming the effective date in the acting instrument.
        proposal = {"date_candidate": exact, "actor": actor, "mechanism": mech, "source": src}
    return {"proposal": proposal, "meta": meta}


def proposal_date(c):
    p = c["proposal"]
    return p.get("date") or p.get("date_candidate")


def _item_mechanism_and_scope(item):
    """(mechanism, qualifier) of a later-events, codification or current-law item."""
    mech = item.get("mechanism")
    if not isinstance(mech, str):
        mech = text_or_empty(item.get("event_type_candidate")) or text_or_empty(item.get("mechanism_candidate"))
        mech = mech.split(" (")[0]
    qual = next((v for v in (item.get("qualifier"), item.get("scope_hint"), item.get("acting_scope"))
                 if isinstance(v, str) and v.strip()), "")
    return mech.strip(), qual.strip()


def codification_end_decision(iid, item, merged):
    """('whole', None) when a 1989 Codification disposition item may be offered as a whole-order end, else
    (None, flag or None). The rule is later-events' own: an unqualified revocation / rescission / 'superseded or
    revoked' stated by the OFR, with nothing in any job's data saying the same acting instrument acted only in part.
    Items the codification job itself flags needs_page_check (medium/low pairing on the page) stay later events."""
    if not isinstance(item, dict):
        return None, None
    mech, qual = _item_mechanism_and_scope(item)
    actor = text_or_empty(item.get("actor")).strip()
    flags = [x for x in as_list(item.get("flags")) if isinstance(x, str)]
    if mech not in FULL_END_MECHANISMS or qual or not actor or "acting_document_is_the_row_itself" in flags:
        return None, None
    if "needs_page_check" in flags:
        return None, None
    for _, f in merged.frags.get(iid, {}).get("later_event_candidates", []):
        for other in f.get("data") if isinstance(f.get("data"), list) else []:
            if not isinstance(other, dict):
                continue
            o_actor = text_or_empty(other.get("actor")) or text_or_empty(other.get("acting_instrument_id"))
            if o_actor.strip().lower() != actor.lower():
                continue
            o_mech, o_qual = _item_mechanism_and_scope(other)
            o_flags = as_list(other.get("flags"))
            if (o_mech in FULL_END_MECHANISMS | {"supersession"} and o_qual) or \
                    "full_and_partial_evidence_conflict" in o_flags:
                return None, "full_and_partial_evidence_conflict"
    return "whole", None


def ending_candidates(iid, merged, kind):
    out, post_cutoff = [], []
    items = []  # (inp, item, extra flags)
    for inp, f in merged.frags.get(iid, {}).get(kind, []):
        data = f.get("data") if isinstance(f.get("data"), list) else []
        for item in data:
            extra = set()
            if inp.job == CODIFICATION_JOB and kind == "later_event_candidates":
                _, why = codification_end_decision(iid, item, merged)
                if why:
                    extra.add(why)
            items.append((inp, item, extra))
    if kind == "whole_order_end_candidates":
        # The 1989 disposition table states the order's own status: an unqualified revocation there is offered as a
        # whole-order end under later-events' rule (the job itself emits only later_event_candidates).
        for inp, f in merged.frags.get(iid, {}).get("later_event_candidates", []):
            if inp.job != CODIFICATION_JOB:
                continue
            for item in f.get("data") if isinstance(f.get("data"), list) else []:
                if codification_end_decision(iid, item, merged)[0] == "whole":
                    items.append((inp, item, {"whole_end_from_1989_disposition_table"}))
    for inp, item, extra in items:
        try:
            c = _le_item(item, inp, kind)
        except Unusable as exc:
            merged.counts[f"items_skipped_wrong_type:{inp.job}:{kind}"] += 1
            if merged.counts["_wrong_type_examples"] < 20:
                merged.counts["_wrong_type_examples"] += 1
                merged.problems.append(f"{inp.label()} {iid} {kind}: item skipped ({exc})")
            continue
        if not c:
            continue
        if extra:
            c["meta"]["flags"] = sorted(set(c["meta"]["flags"]) | extra)
        if kind == "later_event_candidates" and c["proposal"]["mechanism"] == "cross_reference":
            continue
        d = proposal_date(c)
        if d and d > LEGAL_CUTOFF:
            post_cutoff.append(c)
            continue
        out.append(c)
    seen, uniq = set(), []
    for c in out:
        k = short_hash([c["proposal"], c["meta"].get("ids"), c["meta"].get("from_job")])
        if k not in seen:
            seen.add(k)
            uniq.append(c)
    return uniq, post_cutoff


def group_whole_ends(cands):
    groups = collections.OrderedDict()
    for c in cands:
        actor = (c["meta"].get("acting_instrument_id") or c["proposal"].get("actor") or "").strip()
        groups.setdefault((actor.lower(), c["proposal"].get("date")), []).append(c)
    out = []
    for (_, date), items in groups.items():
        actor = (items[0]["meta"].get("acting_instrument_id") or items[0]["proposal"].get("actor") or "").strip()
        items.sort(key=lambda c: SOURCE_JOB_PRIORITY.get(c["meta"]["from_job"], 9))
        jobs = sorted({c["meta"]["from_job"] for c in items})
        flags = sorted({fl for c in items for fl in c["meta"].get("flags") or []})
        # Two jobs reading the same underlying source (the OFR's disposition data) are not two corroborations.
        families = {JOB_SOURCE_FAMILY.get(j, j) for j in jobs}
        out.append({"actor": actor, "date": date, "jobs": jobs, "corroborated_by_two_jobs": len(families) > 1,
                    "flags": flags, "items": items})
    return out


def choose_whole_end(groups, signing):
    usable = [g for g in groups if g["date"] and (not signing or g["date"] >= signing)]
    if not usable:
        return None
    usable.sort(key=lambda g: (g["date"], not g["corroborated_by_two_jobs"],
                               SOURCE_JOB_PRIORITY.get(g["items"][0]["meta"]["from_job"], 9)))
    return usable[0]


def is_snapshot_lead(pred):
    """True for a current_predicate proposal that is only the 1989 in-force snapshot."""
    return pred["meta"].get("basis_code") == CODIFICATION_BASIS_CODE


def codification_in_force_lead(iid, merged):
    """A current_predicate LEAD from the 1989 Codification's in-force rows (CODIFIED_1989.csv), or None.

    checked_through is 1989-01-20, the book's status date, so it can never satisfy the gate (which needs
    2026-10-14): it says only that the order was printed as in force then, in the editors' text as amended."""
    hit = merged.codified_1989.get(iid)
    book = merged.codification_book
    if not hit or not book:
        return None
    inp, row = hit
    n = iid.split(":", 1)[1]
    chapter = text_or_empty(row.get("chapter")).strip()
    title = text_or_empty(row.get("chapter_title")).strip()
    where = f"chapter {chapter}" + (f" ({title})" if title else "")
    page = (f"OFR Codification 1945-1989 (1989), codified text of EO {n}, {where}, printed pages "
            f"{text_or_empty(row.get('printed_pages')) or '?'}, PDF pages {text_or_empty(row.get('pdf_pages')) or '?'}")
    restated_by = text_or_empty(row.get("restated_by")).strip()
    flags = [CODIFICATION_FLAG, "status_as_of_1989-01-20", "as_amended_editorial_text_not_the_original"]
    if restated_by:
        flags.append("restated_in_entirety_by_later_order")
    if text_or_empty(row.get("confidence")) != "high":
        flags.append("needs_page_check")
    basis = (f"LEAD ONLY, not a legal basis: the OFR 1989 Codification prints EO {n} as in force on "
             f"{CODIFICATION_SNAPSHOT_DATE} ({where}), in the editors' text as amended to that day"
             + (f"; its provisions were revised and restated in their entirety by {restated_by}"
                f" ({text_or_empty(row.get('restated_by_date')) or 'date not read'})" if restated_by else "")
             + f"; find the law that keeps it operating after {CODIFICATION_SNAPSHOT_DATE} and check it through "
               f"{LEGAL_CUTOFF}")
    return {
        "proposal": {"legal_basis": basis, "source": {"url": book["url"], "sha256": book["sha256"],
                                                      "page_or_item": page},
                     "checked_through": CODIFICATION_SNAPSHOT_DATE},
        "meta": compact({"basis_code": CODIFICATION_BASIS_CODE, "where": f"OFR Codification 1989, {where}",
                         "system": "ofr_codification_1989", "edition": CODIFICATION_SNAPSHOT_DATE,
                         "text_path": row.get("text_path"), "text_sha256": row.get("text_sha256"),
                         "confidence": row.get("confidence"), "table_disposition": row.get("table_disposition"),
                         "source_line": truncate(text_or_empty(row.get("source_text")) or None)[0],
                         "restated_by": restated_by or None, "flags": flags,
                         "from_job": inp.job, "from": inp.label(),
                         "caution": f"a {CODIFICATION_SNAPSHOT_DATE} editorial snapshot: never enough for checked_through "
                                    f"{LEGAL_CUTOFF}; the codified text is as amended, not the original; an order "
                                    "printed here may have ended after 1989"})}


def predicate_candidates(iid, merged):
    out = []
    for inp, f in merged.frags.get(iid, {}).get("current_predicate_candidates", []):
        data = f.get("data") if isinstance(f.get("data"), list) else []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                basis = as_text(item.get("legal_basis_candidate"), "legal_basis_candidate", required=True)
                through = as_text(item.get("checked_through"), "checked_through")
            except Unusable as exc:
                merged.counts[f"items_skipped_wrong_type:{inp.job}:current_predicate_candidates"] += 1
                if merged.counts["_wrong_type_examples"] < 20:
                    merged.counts["_wrong_type_examples"] += 1
                    merged.problems.append(f"{inp.label()} {iid} current_predicate_candidates: item skipped ({exc})")
                continue
            snip, cut = truncate(item.get("snippet") if isinstance(item.get("snippet"), str) else None)
            out.append({
                "proposal": {"legal_basis": basis, "source": claim_ref(item.get("source")),
                             "checked_through": through},
                "meta": {"basis_code": item.get("basis_code"), "where": item.get("where"), "system": item.get("system"),
                         "edition": item.get("edition"), "currency_code": item.get("currency_code"),
                         "mention_id": item.get("mention_id"), "text_path": item.get("text_path"),
                         "snippet": snip, "snippet_truncated": cut, "from_job": inp.job, "from": inp.label(),
                         "caution": "a mention in current law is a LEAD, not by itself a legal basis; read the "
                                    "provision to see whether it keeps the order operating"}})
    lead = codification_in_force_lead(iid, merged)
    if lead:
        out.append(lead)
    out.sort(key=lambda c: (c["proposal"].get("checked_through") != LEGAL_CUTOFF,
                            BASIS_RANK.get(text_or_empty(c["meta"].get("basis_code")), 9), str(c["meta"].get("where"))))
    return out


def savings_leads(iid, merged, clause_info, end_cands):
    leads = []
    for inp, f in merged.frags.get(iid, {}).get("savings_leads", []):
        data = f.get("data")
        for item in data if isinstance(data, list) else [data]:
            leads.append({"from": inp.label(), "lead": item, "sources": f.get("sources")})
    if clause_info:
        for c in clause_info["clauses"]:
            t = text_or_empty(c.get("original_operative_text"))
            m = SAVINGS_RE.search(t)
            if m:
                a = max(0, m.start() - 150)
                leads.append({"from": "claim-drafts regex over the order's own clause text",
                              "scope_id": c.get("scope_id"), "phrase": m.group(0),
                              "context": t[a:m.end() + 150], "source": c.get("original_source")})
    for c in end_cands:
        q = c["meta"].get("quote") or ""
        m = SAVINGS_RE.search(q)
        if m:
            leads.append({"from": f"claim-drafts regex over an ending candidate quote ({c['meta']['from_job']})",
                          "phrase": m.group(0), "context": q[max(0, m.start() - 150):m.end() + 150],
                          "source": c["proposal"].get("source")})
    return leads[:CAPS["savings_leads"]]


def clause_hints(qualifier, clause_meta):
    """scope_ids whose id/label/heading mention a section number named in a qualifier."""
    if not qualifier or not clause_meta:
        return []
    nums = {n.lower() for grp in SECTION_REF_RE.findall(qualifier) for n in SECTION_NUM_RE.findall(grp)}
    hits = []
    for c in clause_meta:
        hay = " ".join(str(c.get(k) or "") for k in ("scope_id", "label", "heading")).lower()
        for n in nums:
            if re.search(rf"(?:sec(?:tion)?\.?\s*|#sec|paragraph\s*|par\.\s*|part\s*){re.escape(n)}(?![0-9])", hay):
                if isinstance(c.get("scope_id"), str):
                    hits.append(c["scope_id"])
                break
    return hits


# --------------------------------------------------------------- building

def signing_dates(iid, rd, merged, originals):
    found = {}
    cx = rd.crosswalk.get(iid) or {}
    if exact_date(cx.get("signing_date_from_cached_index")):
        found["stage21_crosswalk"] = cx["signing_date_from_cached_index"]
    cq = rd.causal.get(iid) or {}
    if exact_date(cq.get("issuance_date")):
        found["stage19_causal_queue"] = cq["issuance_date"]
    cat = merged.catalog.get(iid) or {}
    if exact_date(cat.get("signing_date")):
        found["later-events_catalog"] = cat["signing_date"]
    for c in originals:
        if exact_date(c.get("signing_date")):
            found.setdefault(c["from"], c["signing_date"])
    return found


def shared_source_status(iid, rd, merged):
    rows = rd.shared.get(iid, [])
    out = []
    for r in rows:
        a = r.get("authority")
        st = {"authority": a, "status": "not_retrieved"}
        if r.get("source_already_retrieved") == "yes" or (a, iid) in rd.statute_ok:
            st["status"] = "retrieved_stage20"
        else:
            found = [(inp, rec) for inp, rec in merged.ladder_by_wanted.get(a, [])
                     if iid in as_list(rec.get("instrument_ids"))] or merged.ladder_by_wanted.get(a, [])
            if found:
                inp, rec = found[0]
                st.update({"status": "found_by_source_ladder", "source": claim_ref(rec),
                           "source_id": rec.get("source_id"), "route": rec.get("route")})
            elif a in merged.ladder_results:
                res = merged.ladder_results[a]
                st.update({"status": f"source_ladder_{res.get('result')}", "why": res.get("why")})
        out.append(st)
    return out


def order_year(iid, rd, signing_min=None):
    """The order's year: from a known signing date, else from the universe's date_effective (None if unknown)."""
    raw = signing_min or (rd.universe.get(iid) or {}).get("date_effective") or ""
    m = re.match(r"^(\d{4})", raw)
    return int(m.group(1)) if m else None


def placeholder_clause():
    """Stands in for a missing clause inventory so the claim gate does not stop early (a claim with an empty
    operative_clauses list makes the gate return before it checks endings, savings and searches, and the
    readiness tracker would then count those steps). It can never pass: no text, no source, no state."""
    return {"scope_id": PLACEHOLDER_SCOPE_ID, "original_operative_text": None, "original_source": None,
            "state_at_cutoff": None, "first_end": None, "current_predicate": None, "later_events": []}


def build_draft(iid, merged, rd, gate, step_for):
    """One draft line: {draft_schema, instrument_id, claim, _draft}."""
    d = rd.decided.get(iid)
    status = d.get("provisional_substantive_status") if d else None
    status = status if status in ("yes", "no") else None
    origin = d.get("decision_origin") if d else ""
    machine, judgment, missing, conflicts = [], [], [], []

    # --- original text
    originals = original_candidates(iid, merged, rd, gate)
    strong = [c for c in originals if c["strong"]]
    acceptable = [c for c in originals if c["acceptable_as_original"]]
    leads_only = [c for c in originals if not c["acceptable_as_original"]]
    chosen_original = strong[0] if strong else None
    if chosen_original:
        machine.append({"field": "original_representation", "from": chosen_original["from"],
                        "grade": chosen_original["grade"], "basis": chosen_original["why"],
                        "agent_must": "open the pages; confirm this order's complete official text; fix page_or_item"})
    elif acceptable:
        judgment.append({"field": "original_representation",
                         "why": "only weak candidates (page location not confirmed, or not the printed edition); "
                                "check the pages and copy one into the claim",
                         "candidates": len(acceptable)})
    else:
        nf = merged.fr_not_found.get(iid) or {}
        why = "no official original-text candidate from any job"
        if nf:
            why += f"; fr-originals: {nf.get('reason')} ({(nf.get('detail') or '')[:200]})"
        if leads_only:
            why += (f"; {len(leads_only)} compiled-transcription lead(s) (for example Richardson) point to the text "
                    "but are not the original by themselves")
        missing.append({"step": "original_text", "what": why})
    if leads_only and not chosen_original:
        judgment.append({"field": "original_representation (lead)",
                         "why": "a printed compilation transcribed from records (Richardson) names this order: use "
                                "it to find and read the official original; never cite it as the original by itself",
                         "candidates": len(leads_only)})

    # --- clauses
    info, alternates = clause_inventory(iid, merged)
    claim_clauses = []
    if info:
        for c in info["clauses"]:
            claim_clauses.append({"scope_id": c.get("scope_id"), "original_operative_text": c.get("original_operative_text"),
                                  "original_source": claim_ref(c.get("original_source")), "state_at_cutoff": None,
                                  "first_end": None, "current_predicate": None, "later_events": []})
        machine.append({"field": "operative_clauses[*].scope_id / original_operative_text / original_source",
                        "from": info["from"], "grade": info["source_grade"],
                        "basis": f"{len(claim_clauses)} clauses drafted by clause-drafts "
                                 f"(segmentation {info['segmentation_quality']}); text offsets: {info['offset_checks']}",
                        "agent_must": "confirm completeness and boundaries against the official original"})
        judgment.append({"field": "operative_clauses[*].state_at_cutoff", "why": "decide for every clause: "
                         "operative, terminated or never_activated", "clauses": len(claim_clauses)})
        judgment.append({"field": "operative_clauses[*].later_events", "why": "attach the later-event candidates "
                         "that affected each clause (each needs effective_date, actor, mechanism, source; the proposals' date_candidate is the acting instrument's signing or printed date - confirm the effective date and rename the key)"})
        if info["offset_checks"].get("mismatch"):
            conflicts.append({"code": "CLAUSE_TEXT_NOT_AT_OFFSETS",
                              "detail": f"{info['offset_checks']['mismatch']} clause text(s) do not match their saved "
                                        "text offsets"})
        if info["source_grade"] in ("mirror_transcription_app", "other_copy"):
            judgment.append({"field": "operative_clauses[*].original_source",
                             "why": f"clause texts come from a {info['source_grade']} copy, not an official edition; "
                                    "check them against the official original"})
    else:
        q, ns = merged.quarantine.get(iid), merged.not_segmented.get(iid)
        why = "no clause inventory drafted"
        if q:
            why += f"; clause-drafts quarantined this order's text for identity: {q.get('reasons')}"
        elif ns:
            why += f"; clause-drafts could not segment the available text(s): {(ns.get('attempts') or '')[:200]}"
        missing.append({"step": "clause_inventory", "what": why})

    # --- signing date
    signing = signing_dates(iid, rd, merged, originals)
    sdates = sorted(set(signing.values()))
    if len(sdates) > 1:
        conflicts.append({"code": "SIGNING_DATE_DISAGREEMENT", "detail": "; ".join(f"{k}: {v}" for k, v in sorted(signing.items()))})
    signing_min = sdates[0] if sdates else None
    frs = {re.sub(r"\s+", " ", c["fr_citation"]).strip() for c in originals if isinstance(c.get("fr_citation"), str) and c["fr_citation"].strip()}
    cx_fr = (rd.crosswalk.get(iid) or {}).get("FR_citation_from_cached_index")
    if cx_fr:
        frs.add(re.sub(r"\s+", " ", cx_fr).strip())
    if len(frs) > 1:
        conflicts.append({"code": "ORIGINAL_FR_CITATION_DISAGREEMENT", "detail": " vs ".join(sorted(frs))})

    # --- endings and later events
    whole, whole_post = ending_candidates(iid, merged, "whole_order_end_candidates")
    events, events_post = ending_candidates(iid, merged, "later_event_candidates")
    preds = predicate_candidates(iid, merged)
    # The 1989 Codification's in-force rows are proposed too, but they are not current law (see is_snapshot_lead).
    preds_current = [p for p in preds if not is_snapshot_lead(p)]
    snapshot = [p for p in preds if is_snapshot_lead(p)]
    groups = group_whole_ends(whole)
    suggested = choose_whole_end(groups, signing_min)
    for c in whole_post + events_post:
        conflicts.append({"code": "CANDIDATE_DATED_AFTER_CUTOFF",
                          "detail": f"{c['meta']['from_job']}: {c['proposal'].get('actor')} "
                                    f"{c['proposal'].get('mechanism')} dated {proposal_date(c) or c['meta'].get('date_raw')} (out of scope)"})
    dated_groups = [g for g in groups if g["date"]]
    if len({g["date"] for g in dated_groups}) > 1:
        conflicts.append({"code": "WHOLE_END_DATE_DISAGREEMENT",
                          "detail": "; ".join(f"{g['date']} by {g['actor'] or '?'} ({'+'.join(g['jobs'])})" for g in dated_groups)})
    if len({g["actor"] for g in groups if g["actor"]}) > 1:
        conflicts.append({"code": "WHOLE_END_ACTOR_DISAGREEMENT",
                          "detail": ", ".join(sorted({g["actor"] for g in groups if g["actor"]}))})
    if any(not g["date"] for g in groups):
        conflicts.append({"code": "WHOLE_END_DATE_MISSING_OR_DISPUTED",
                          "detail": f"{sum(not g['date'] for g in groups)} whole-order-end candidate group(s) have no "
                                    "single exact date (undated, or the sources disagree)"})
    for c in whole + events:
        m = c["meta"]
        d0 = proposal_date(c)
        if signing_min and d0 and d0 < signing_min:
            conflicts.append({"code": "EVENT_BEFORE_SIGNING",
                              "detail": f"{m['from_job']}: {c['proposal'].get('actor')} {c['proposal'].get('mechanism')} "
                                        f"dated {d0}, before the signing date {signing_min}"})
        eff = [x for x in m.get("stated_effective_date_candidates") or [] if isinstance(x, str)]
        if d0 and eff and any(x != d0 for x in eff):
            conflicts.append({"code": "STATED_EFFECTIVE_DATE_DIFFERS",
                              "detail": f"{c['proposal'].get('actor')}: date {d0}, but the source says effective "
                                        f"{', '.join(eff)}"})
        if "full_and_partial_evidence_conflict" in (m.get("flags") or []):
            conflicts.append({"code": "FULL_AND_PARTIAL_EVIDENCE_CONFLICT",
                              "detail": f"{c['proposal'].get('actor')}: the sources read as both a whole and a partial ending"})
        if m.get("later_reinstatement_candidates"):
            conflicts.append({"code": "LATER_REINSTATEMENT_CANDIDATE",
                              "detail": f"{len(m['later_reinstatement_candidates'])} reinstatement lead(s) after "
                                        f"{c['proposal'].get('actor')}"})
    if status == "yes" and groups:
        conflicts.append({"code": "YES_ORDER_HAS_WHOLE_END_CANDIDATE",
                          "detail": f"provisional YES, but {len(whole)} whole-order-end candidate(s): "
                                    + "; ".join(f"{g['date'] or 'undated'} by {g['actor'] or '?'}" for g in groups[:5])})
    # Later events that end part of a YES order (e.g. 'sections 1 and 2 revoked'): the order is not simply
    # operative in every clause; the clauses named need a first_end, or the agent must rule the event out.
    partial_ends = []
    if status == "yes":
        for c in events:
            if ENDING_MECHANISM_RE.search(c["proposal"].get("mechanism") or ""):
                hints = clause_hints(c["meta"].get("qualifier"), info["meta"] if info else [])
                partial_ends.append((c, hints))
        if partial_ends:
            conflicts.append({"code": "PARTIAL_END_CANDIDATE_ON_YES_ORDER",
                              "detail": f"provisional YES, but {len(partial_ends)} later event(s) end part of it: "
                                        + "; ".join(f"{c['proposal'].get('actor') or '?'} {c['proposal'].get('mechanism')}"
                                                    f" {proposal_date(c) or 'undated'}"
                                                    + (f" ({', '.join(h)})" if h else
                                                       f" (scope: {(c['meta'].get('qualifier') or 'not stated')[:80]})")
                                                    for c, h in partial_ends[:5])})
    if status == "no" and preds_current:
        conflicts.append({"code": "NO_ORDER_CITED_IN_CURRENT_LAW",
                          "detail": f"provisional NO, but {len(preds_current)} current-law predicate lead(s), e.g. "
                                    + "; ".join(str(p["meta"].get("where")) for p in preds_current[:3])})
    # Printed as in force on 1989-01-20 (and not restated by a later order), yet no ending candidate after that day:
    # the order's ending, if any, came later than every candidate the machines found.
    in_force_1989 = [p for p in snapshot if not p["meta"].get("restated_by")]
    if status == "no" and in_force_1989:
        later = [c for c in whole + events if (proposal_date(c) or "") > CODIFICATION_SNAPSHOT_DATE
                 and ENDING_MECHANISM_RE.search(c["proposal"].get("mechanism") or "")]
        if not later:
            earlier = sorted({proposal_date(c) for c in whole if proposal_date(c)})
            conflicts.append({"code": "NO_ORDER_IN_FORCE_ON_1989_01_20",
                              "detail": f"provisional NO, but the OFR 1989 Codification prints it as in force on "
                                        f"{CODIFICATION_SNAPSHOT_DATE} ({in_force_1989[0]['meta'].get('where')}) and no "
                                        "ending candidate is dated after that day"
                                        + (f"; whole-order-end candidate(s) dated {', '.join(earlier[:3])} are earlier"
                                           if earlier else "")})
    cq = rd.causal.get(iid) or {}
    try:
        quarantined = int(cq.get("quarantined_relationship_count") or 0)
    except ValueError:
        quarantined = 0
    if quarantined:
        conflicts.append({"code": "QUARANTINED_RELATIONSHIP_CONFLICT",
                          "detail": f"Stage 19 causal queue: {quarantined} quarantined relationship(s)"})

    # Dedupe conflicts (same code + detail).
    seen, uniq = set(), []
    for c in conflicts:
        k = (c["code"], c["detail"])
        if k not in seen:
            seen.add(k)
            uniq.append(c)
    conflicts = uniq

    # Ending judgments / gaps.
    if status == "no":
        if suggested:
            judgment.append({"field": "whole_order_end + operative_clauses[*].first_end",
                             "why": f"choose the first ending among {len(groups)} candidate group(s) and confirm its "
                                    "EFFECTIVE date (the candidate date is the acting instrument's signing or printed "
                                    "date) and that it ended the whole order",
                             "suggested": {"date": suggested["date"], "actor": suggested["actor"]}})
        elif groups:
            judgment.append({"field": "whole_order_end", "why": "candidates exist but none has a usable exact date; "
                             "read the acting instruments"})
            missing.append({"step": "ending_or_current_basis", "what": "no whole-order-end candidate with an exact date"})
        else:
            missing.append({"step": "ending_or_current_basis",
                            "what": "provisional NO, but no job found a whole-order-end candidate"})
    elif status == "yes":
        if preds_current:
            judgment.append({"field": "operative_clauses[*].current_predicate",
                             "why": f"choose the legal basis that keeps the order operating among {len(preds_current)} "
                                    "current-law lead(s) and confirm it reaches the cutoff"
                                    + (f" (the OFR 1989 Codification also prints it as in force on "
                                       f"{CODIFICATION_SNAPSHOT_DATE}: a lead, never enough)" if snapshot else "")})
            if not any(p["proposal"].get("checked_through") == LEGAL_CUTOFF for p in preds_current):
                missing.append({"step": "ending_or_current_basis",
                                "what": f"no current-law lead is checked through {LEGAL_CUTOFF} (U.S. Code entries "
                                        "are current only through 2026-10-09); confirm the last days by hand"})
        else:
            missing.append({"step": "ending_or_current_basis",
                            "what": "provisional YES, but no job found a current-law predicate lead"
                                    + (f" (only the OFR 1989 Codification's in-force snapshot of "
                                       f"{CODIFICATION_SNAPSHOT_DATE}, which never reaches {LEGAL_CUTOFF})"
                                       if snapshot else "")})
        if partial_ends:
            judgment.append({"field": "operative_clauses[*].state_at_cutoff / first_end",
                             "why": f"{len(partial_ends)} later event(s) revoke, supersede or end part of this YES "
                                    "order; the clauses they name are not operative unless the agent rules the event "
                                    "out (see PARTIAL_END_CANDIDATE_ON_YES_ORDER)",
                             "clauses_named": sorted({h for _, hs in partial_ends for h in hs})})
    else:
        missing.append({"step": "provisional_status", "what": "no provisional YES/NO status; the order has not been "
                        "researched (the claim's whole_order_status cannot be filled)"})
    if events:
        judgment.append({"field": "later events", "why": f"{len(events)} later-event candidate(s) to read and attach "
                         "to the clauses they affected"})

    # --- savings and searches
    sav = savings_leads(iid, merged, info, whole)
    judgment.append({"field": "savings_residuals", "why": "read the ending instrument(s) and the order for savings "
                     "clauses and surviving effects; state none_after_bounded_search, continuing_independent or "
                     "transferred_or_accrued with a source",
                     "machine_leads": len(sav)})
    # Machine search records are never put into the claim: the readiness tracker lights 'counterevidence' as soon
    # as claim.later_source_search has entries, so only an agent who judged them adequate may paste them.
    year = order_year(iid, rd, signing_min)
    searches_machine, searches_prop = [], []
    for s in merged.searches:
        e = dict(s["entry"])
        hits = sum(len(f.get("data") or []) if isinstance(f.get("data"), list) else 1
                   for kind, lst in merged.frags.get(iid, {}).items() for inp, f in lst if inp.job == s["job"])
        coverage_row = None
        if s.get("per_order_coverage"):
            inp = next((x for x in merged.inputs if x.job == s["job"]), None)
            coverage_row = inp.search_coverage.get((iid, s["search_id"])) if inp else None
            if coverage_row is None:
                continue  # the search does not apply to this order (it searches for a person this order names)
        if s["complete"]:
            item = {"entry": e, "search_id": s["search_id"], "machine_hits_for_this_order": hits}
            if s["kind"] == "ofr_catalog" and year is not None and year < CATALOG_COVERAGE_START_YEAR:
                item["coverage_warning"] = (f"order dated {year}: the OFR catalog starts in "
                                            f"{CATALOG_COVERAGE_START_YEAR}, so endings before then are not in it; "
                                            "not adequate on its own")
            if coverage_row is not None and coverage_row.get("covered", "1").strip() not in ("1", "true", "yes"):
                item["coverage_warning"] = coverage_row.get("note") or "this order was not searched"
            searches_machine.append(item)
        else:  # full wording and the reason are in SUMMARY.json machine_searches
            searches_prop.append({"search_id": s["search_id"], "machine_hits_for_this_order": hits,
                                  "not_entered": "partial-scope run"})
    adequate_machine = [x for x in searches_machine if not x.get("coverage_warning")]
    judgment.append({"field": "later_source_search",
                     "why": ("paste the 'entry' of each search in _draft.proposals.later_source_search_machine (its "
                             "wording is in SUMMARY.json machine_searches, same search_id) only after "
                             "judging them adequate for this order AND resolving every CONFLICT line (the tracker "
                             "counts counterevidence as soon as this field has entries); add your own searches"
                             if searches_machine else
                             "no complete machine search covers this order yet; record your own bounded search "
                             "(repository, query_or_scope, checked_on)")
                            + (f" - {len(searches_prop)} partial machine search(es) are listed in proposals"
                               if searches_prop else "")
                            + ("; the catalog search does not reach this order's early years"
                               if len(adequate_machine) < len(searches_machine) else ""),
                     "machine_searches_complete": len(searches_machine)})
    judgment.append({"field": "research_rationale", "why": "write the substantive rationale (at least 40 characters)"})

    # --- shared sources and media (tracker steps outside the claim)
    shared = shared_source_status(iid, rd, merged)
    media = merged.media_status.get(iid)
    cu = rd.custody.get(iid) or {}
    original_saved_now = cq.get("locally_preserved_primary_representation") == "1" or \
        cu.get("custody_state", "").startswith("PDF_BYTES_CAPTURED")

    # --- the claim (exact Stage 19 shape; judgment fields empty on purpose)
    gaps = []
    if not chosen_original:
        gaps.append("DRAFT: original_representation not yet confirmed")
    if claim_clauses:
        gaps.append(f"DRAFT: state_at_cutoff not decided for {len(claim_clauses)} clause(s); clause inventory "
                    "completeness not confirmed")
    else:
        gaps.append(f"DRAFT: no clause inventory; the clause {PLACEHOLDER_SCOPE_ID} only stands in for it and must be "
                    "replaced by the order's real clauses (never commit it, and never commit an empty clause list)")
    gaps.append("DRAFT: whole-order ending not established" if status == "no" else
                "DRAFT: current legal basis not established" if status == "yes" else "DRAFT: no provisional status")
    gaps.append("DRAFT: savings and residual effects not closed")
    gaps.append("DRAFT: later_source_search not recorded (machine searches are proposals only; paste them after "
                "judging them adequate and resolving every CONFLICT line)")
    for c in conflicts:
        gaps.append(f"CONFLICT {c['code']}: {c['detail']}"[:400])
    claim = {
        "schema": CLAIM_SCHEMA,
        "instrument_id": iid,
        "whole_order_status": status,
        "original_representation": chosen_original["ref"] if chosen_original else None,
        "operative_clauses": claim_clauses or [placeholder_clause()],
        "whole_order_end": None,
        "savings_residuals": None,
        "later_source_search": [],
        "unresolved_material_gaps": gaps,
        "research_rationale": "",
    }
    if status:
        machine.insert(0, {"field": "whole_order_status", "from": P["decided"],
                           "basis": f"provisional status '{status}' ({origin}); the tracker requires the claim to match it",
                           "agent_must": "never change it; report contrary evidence (AGENT_GUIDE.md)"})
    machine.append({"field": "unresolved_material_gaps", "from": JOB_NAME,
                    "basis": "open items of this draft",
                    "agent_must": "remove each line only when resolved"})

    # --- proposals (already in the claim's field shapes)
    for g in groups:
        g["suggested"] = suggested is g
    whole_props = []
    for g in groups:
        for c in g["items"]:
            whole_props.append({**c, "meta": compact(c["meta"]), "group": {"actor": g["actor"], "date": g["date"], "jobs": g["jobs"],
                                               "corroborated_by_two_jobs": g["corroborated_by_two_jobs"]},
                                "suggested": g["suggested"] and c is g["items"][0],
                                "custody_records_in": source_custody(merged, c["proposal"].get("source"))})
    meta_for_hints = info["meta"] if info else []
    event_props = []
    for c in events[:CAPS["later_events"]]:
        c = dict(c)
        c["clause_hint_scope_ids"] = clause_hints(c["meta"].get("qualifier"), meta_for_hints)
        c["custody_records_in"] = source_custody(merged, c["proposal"].get("source"))
        c["meta"] = compact(c["meta"])
        event_props.append(c)
    pred_props = [dict(p, meta=compact(p["meta"]), custody_records_in=source_custody(merged, p["proposal"].get("source")))
                  for p in preds[:CAPS["current_predicate"]]]
    proposals = {
        "original_representation": originals,
        "whole_order_end": whole_props[:CAPS["whole_order_end"]],
        "whole_order_end_total": len(whole_props),
        "current_predicate": pred_props,
        "current_predicate_total": len(preds),
        "later_events": event_props,
        "later_events_total": len(events),
        # The entry wording is the same for every order: it is written once, in SUMMARY.json machine_searches.
        "later_source_search_machine": [{k: v for k, v in x.items() if k != "entry"} for x in searches_machine],
        "later_source_search_partial": searches_prop,
        "savings_leads": sav,
        "excluded_after_cutoff": len(whole_post) + len(events_post),
    }

    # --- gate now, and with the machine proposals accepted (feasibility test only)
    errors_now, crash_now = run_gate(gate, claim, status)
    hyp = copy.deepcopy(claim)
    if not chosen_original and acceptable:  # a compiled transcription is never accepted as the original
        hyp["original_representation"] = acceptable[0]["ref"]
    end_ref = None
    if status == "no" and suggested:
        p = suggested["items"][0]["proposal"]
        end = {"date": p["date"], "actor": p["actor"], "mechanism": p["mechanism"], "source": p["source"]}
        end_ref = p["source"]
        hyp["whole_order_end"] = end
        for c in hyp["operative_clauses"]:
            c["state_at_cutoff"], c["first_end"] = "terminated", dict(end)
    elif status == "yes" and preds_current:  # a 1989 snapshot never satisfies checked_through
        pr = preds_current[0]["proposal"]
        named_end = {}  # scope_id -> first_end from a later event that ends that clause
        for ev, hints in partial_ends:
            p = ev["proposal"]
            for h in hints:
                named_end.setdefault(h, {"date": p.get("date_candidate"), "actor": p.get("actor"),
                                         "mechanism": p.get("mechanism"), "source": p.get("source")})
        for c in hyp["operative_clauses"]:
            if isinstance(c.get("scope_id"), str) and c["scope_id"] in named_end:
                c["state_at_cutoff"], c["first_end"] = "terminated", dict(named_end[c["scope_id"]])
            else:
                c["state_at_cutoff"], c["current_predicate"] = "operative", dict(pr)
    sav_source = end_ref or hyp.get("original_representation")
    if sav_source:
        hyp["savings_residuals"] = {"state": "none_after_bounded_search", "reason": "PLACEHOLDER (feasibility test)",
                                    "source": sav_source}
    hyp["later_source_search"] = [x["entry"] for x in adequate_machine]
    hyp["unresolved_material_gaps"] = []
    hyp["research_rationale"] = "PLACEHOLDER rationale used only to test which gate errors are judgment-only."
    errors_hyp, crash_hyp = run_gate(gate, hyp, status)
    only_judgment = not errors_hyp
    only_judgment_but_search = bool(errors_hyp) and set(errors_hyp) <= {"bounded_later_search"}

    # --- readiness steps
    hyp_steps = {step_for(e) for e in errors_hyp}
    readiness = {}
    readiness["original_text"] = "done_now_by_custody" if original_saved_now else (
        "confirm" if "original_text" not in hyp_steps else "research")
    readiness["clause_inventory"] = "confirm" if claim_clauses and "clause_inventory" not in hyp_steps else "research"
    readiness["ending_or_current_basis"] = "confirm" if status and claim_clauses and \
        "ending_or_current_basis" not in hyp_steps else "research"
    if partial_ends and readiness["ending_or_current_basis"] == "confirm":
        readiness["ending_or_current_basis"] = "agent_judgment"
    readiness["savings_residuals"] = "agent_judgment" if sav_source else "research"
    # Counterevidence needs a researched order with clauses, and a machine search that reaches its years.
    if not status or not claim_clauses or not adequate_machine or len(adequate_machine) < len(searches_machine):
        readiness["counterevidence"] = "research"
    elif conflicts or quarantined:
        readiness["counterevidence"] = "resolve_conflicts"
    else:
        readiness["counterevidence"] = "confirm"
    if shared:
        open_ = [s for s in shared if s["status"] not in ("retrieved_stage20", "found_by_source_ladder")]
        readiness["shared_sources"] = "done_now" if all(s["status"] == "retrieved_stage20" for s in shared) else (
            "confirm" if not open_ else "research")
    else:
        readiness["shared_sources"] = "n/a"
    if origin.startswith("opus"):
        if iid in rd.media_linked:
            readiness["opus_media"] = "done_now"
        elif media and media.get("all_cited_media_resolved") == "yes":
            readiness["opus_media"] = "confirm"
        else:
            readiness["opus_media"] = "research"
    else:
        readiness["opus_media"] = "n/a"
    would_satisfy = [s for s in TRACKER_STEPS if readiness[s] == "confirm"]
    needs_research = [s for s in TRACKER_STEPS if readiness[s] in ("research",)]

    # --- effort
    points = 3 * len({m["step"] for m in missing}) + min(len(conflicts), 4)
    n_cl = len(claim_clauses)
    points += 2 if n_cl > 30 else 1 if n_cl > 10 else 0
    points += 1 if len(groups) > 3 or len(events) > 10 else 0
    effort = "small" if points <= 2 else "medium" if points <= 5 else "large"
    if partial_ends and effort == "small":
        effort = "medium"

    draft = {
        "family_rule_certificates": [f["data"] for _, f in merged.frags.get(iid, {}).get("family_rule_checks", [])],
        "status": "MACHINE DRAFT - UNVERIFIED; not a claim; see jobs/claim-drafts/AGENT_GUIDE.md",
        "produced_by": JOB_NAME,
        "provisional_status": status, "decision_origin": origin, "in_decided_3359": bool(d),
        "signing_dates_seen": signing,
        "machine_filled": machine,
        "needs_judgment": judgment,
        "missing_evidence": missing,
        "conflicts": conflicts,
        "proposals": proposals,
        "clauses": meta_for_hints,
        "clause_count": len(claim_clauses),
        "clause_inventory_info": None if not info else {
            "from": info["from"], "source_id": info["source_id"], "source_grade": info["source_grade"],
            "segmentation_quality": info["segmentation_quality"], "segmentation_warnings": info["segmentation_warnings"],
            "structure": info["structure"], "offset_checks": info["offset_checks"],
            "alternate_sources": info["alternate_sources"], "alternate_fragments": alternates},
        "shared_sources": shared,
        "opus_media": None if not media else {k: media.get(k) for k in (
            "media_status", "all_cited_media_resolved", "unique_supported_members", "ambiguous_members", "media_gap",
            "example_media_urls_missing")},
        "source_ladder_exhausted_proposed": merged.ladder_exhausted.get(iid, []),
        "gate": {"errors_now": errors_now, "errors_now_compact": compress_errors(errors_now),
                 "error_steps_now": sorted({step_for(e) or "claim_record" for e in errors_now}),
                 "errors_if_proposals_accepted": compress_errors(errors_hyp),
                 "only_judgment_left": only_judgment,
                 "only_judgment_and_a_later_source_search_left": only_judgment_but_search,
                 "placeholder_clause": not claim_clauses,
                 "gate_exception": crash_now or crash_hyp},
        "checker": None,
        "readiness": {"by_step": readiness, "would_satisfy_once_confirmed": would_satisfy,
                      "needs_research": needs_research},
        "effort": effort,
    }
    return {"draft_schema": DRAFT_SCHEMA, "instrument_id": iid, "claim": claim, "_draft": draft}


def evidence_score(iid, merged, rd):
    kinds = merged.frags.get(iid, {})
    s = 0
    s += 2 if "original_representation" in kinds or (rd.custody.get(iid) or {}).get("custody_state", "").startswith("PDF_BYTES") else 0
    s += 2 if "operative_clauses" in kinds else 0
    s += sum(1 for k in ("whole_order_end_candidates", "current_predicate_candidates", "later_event_candidates") if k in kinds)
    return s


def select_orders(merged, rd, scope="all", ids=None, limit=None):
    if ids:
        chosen = [i for i in ids if i in rd.universe]
    else:
        pool = set(rd.decided) & set(rd.universe)
        if scope != "decided":
            pool |= {i for i in merged.frags if i in rd.universe}
            pool |= {i for i in rd.custody if i in rd.universe and
                     (rd.custody[i].get("custody_state") or "").startswith("PDF_BYTES")}
        chosen = sorted(pool, key=lambda i: (0 if i in rd.decided else 1, -evidence_score(i, merged, rd),
                                             order_sort_key(i)))
    return chosen[:limit] if limit else chosen


# ---------------------------------------------------------------- checker

class OfflineVerification:
    """Reuse byte receipts, never acquire them while drafting.

    The standalone checker may download missing GovInfo files. Drafting is
    offline: missing receipts stay unverified. Rehash each existing receipt
    once per run/file version, including negative results; never persist a
    verdict. A replacement or in-place edit invalidates the memo even when
    its size and mtime are unchanged (ctime/inode are included).
    """

    def __init__(self, receipt_roots=()):
        self._verified = {}
        self.receipt_roots = tuple(pathlib.Path(p) for p in receipt_roots)
        # Windows ctime can be creation time rather than change time. Do not
        # trust its stat tuple to detect a same-size edit with restored mtime.
        self.reuse_unchanged = os.name == "posix"
        self.hashes = 0
        self.cache_hits = 0
        self.missing = 0

    def __call__(self, url, sha, cache_dir):
        if urllib.parse.urlsplit(url or "").hostname != "www.govinfo.gov" or not url.startswith("https://"):
            return None
        paths = [root / "verified" / sha[:2] / (sha + ".bin")
                 for root in (pathlib.Path(cache_dir), *self.receipt_roots)]
        result = None
        for path in dict.fromkeys(paths):
            verdict = self._check_file(path, sha)
            if verdict is True:
                return True
            if verdict is False:
                result = False
        if result is None:
            self.missing += 1
        return result

    def _check_file(self, path, sha):
        try:
            return self._check_existing_file(path, sha)
        except (FileNotFoundError, PermissionError, IsADirectoryError):
            # An acquisition/cleanup can remove or replace a receipt during
            # this check. It supplies no verified bytes for this invocation.
            return None

    def _check_existing_file(self, path, sha):
        if not path.is_file():
            return None
        stat = path.stat()
        key = (str(path.resolve()), sha, stat.st_dev, stat.st_ino,
               stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        if self.reuse_unchanged and key in self._verified:
            self.cache_hits += 1
            return self._verified[key]
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        self.hashes += 1
        result = digest.hexdigest() == sha
        # A matching stream is insufficient if the path now names different
        # bytes. Reject replacement/edit during hashing, without a retry loop.
        after = path.stat()
        if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) != key[2:]:
            return None
        if self.reuse_unchanged:
            self._verified[key] = result
        return result


class CheckerRunner:
    """Runs jobs/claim-checker's mechanical checks on each draft claim (if importable)."""

    def __init__(self, repo, cache_dir, inputs):
        repo = pathlib.Path(repo).resolve()
        path = repo / P["checker"]
        spec = importlib.util.spec_from_file_location("claim_checker_for_drafts", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.mod = mod
        cache_dir = pathlib.Path(cache_dir)
        # Shared runner: .job-cache/claim-drafts beside .job-cache/claim-checker.
        # Local convention: claim-drafts-cache beside claim-checker-cache.
        # Read only; the predecessor remains the owner of its receipts.
        receipt_roots = [cache_dir.parent / "claim-checker", cache_dir.parent / "claim-checker-cache"]
        roots = [r for r in os.environ.get("CLAIM_CHECKER_CACHE_ROOTS", "").split(os.pathsep) if r]
        receipt_roots.extend(pathlib.Path(r) for r in roots)
        receipt_roots.extend(pathlib.Path(r) / "claim-checker" for r in roots)
        receipt_roots.extend(pathlib.Path(r) / "claim-checker-cache" for r in roots)
        self.verification = OfflineVerification(receipt_roots)
        mod.verify_by_download = self.verification
        S = mod.S
        index = S.build_index(repo, mod.HERE, roots, exclude_jobs=("claim-checker", JOB_NAME))
        self.added = 0
        for inp in inputs:
            if is_within(inp.path, repo / "jobs") and inp.path.name == "output":
                continue  # build_index already read jobs/*/output/SOURCES.jsonl
            self.added += self._add_records(S, index, inp, roots)
        self.ctx = mod.Context(repo, mod.HERE, pathlib.Path(cache_dir) / "checker-text", index=index)
        self.index = index

    @staticmethod
    def _add_records(S, index, inp, roots):
        n = 0
        cache_roots = [inp.path.parent / f"{inp.job}-cache", inp.path.parent.parent / f"{inp.job}-cache"]
        cache_roots += [pathlib.Path(r) for r in roots] + [pathlib.Path(r) / f"{inp.job}-cache" for r in roots]
        for rec in read_jsonl(inp.path / "SOURCES.jsonl", [], inp.label()):
            sha = S.sha_hex(rec.get("sha256"))
            if not sha:
                continue
            text = safe_child(inp.path, rec.get("text_path"))
            local = None
            for root in cache_roots:
                cand = safe_child(root, rec.get("cache_path"))
                if cand is not None and cand.is_file():
                    local = cand
                    break
            ids = rec.get("instrument_ids") if isinstance(rec.get("instrument_ids"), list) else []
            nbytes = rec.get("bytes") if isinstance(rec.get("bytes"), int) else None
            index.add(S.HeldCopy(f"{inp.label()}/SOURCES.jsonl", sha, rec.get("url"), nbytes, local,
                                 text if (text is not None and text.is_file()) else None, (), rec.get("page_or_item"),
                                 ids, rec.get("route") or "", custody="job_cache" if local is not None else "record_only"))
            n += 1
        return n

    def check(self, claim, n):
        mod = self.mod
        try:
            rows, errors, status = mod.check_claim(claim, self.ctx)
            s = mod.summarise_claim(f"DRAFT_CLAIMS.jsonl:{n}", "DRAFT_CLAIMS.jsonl", n, claim, rows, errors, status, self.ctx)
        except Exception as exc:  # noqa: BLE001
            return {"checker_error": f"{type(exc).__name__}: {exc}"[:300]}, []
        res = {"mechanical_result": s["mechanical_result"], "gate_passed": s["gate_passed"],
               "steps_checker_passed": {k: v["checker_passed"] for k, v in s["steps"].items()},
               "failures_total": s["failures_total"],
               "failures": s["failures"][:25], "unverified": s["unverified"][:25]}
        mech_rows = [r for r in rows if r["check"] in mod.MECHANICAL_CHECKS]
        return res, mech_rows


# ------------------------------------------------------------------ output

LEGEND = {
    "gate.errors_now": "claim_gate.validate_claim errors of the claim exactly as drafted: the agent's to-do list",
    "gate.errors_if_proposals_accepted": "feasibility test only: the suggested candidates and placeholder text were "
        "put in a COPY of the claim; whatever still fails there has no machine evidence yet (compact form: "
        "clause_*_state x12 means twelve clauses)",
    "gate.only_judgment_left": "true when that copy passes the gate: every remaining gap is a judgment the agent "
        "makes from evidence already in the draft",
    "gate.placeholder_clause": "true when no clause inventory exists: the claim then holds one placeholder clause "
        f"({PLACEHOLDER_SCOPE_ID}) so the gate checks every part (an empty list makes the gate stop early, and the "
        "readiness tracker would count the unchecked steps); replace it with the real clauses",
    "proposals.later_source_search_machine": "complete machine searches, never put into the claim: copy the 'entry' "
        "of the same search_id from SUMMARY.json machine_searches into claim.later_source_search only after judging "
        "it adequate for the order and resolving every CONFLICT line",
    "readiness.by_step": "confirm = machine evidence is in the draft or proposals and an agent must check and "
        "accept it; agent_judgment = needs reading and a decision; resolve_conflicts = conflicts listed; research = "
        "no machine evidence yet; done_now / done_now_by_custody = the tracker already counts it; n/a = not "
        "applicable",
    "proposals": "candidates already in the claim's field shapes ('proposal'), with 'meta' explaining where each "
        "came from; dates are the acting instrument's signing or printed date, never a verified effective date "
        "(later-event proposals therefore say date_candidate; rename it to effective_date only after confirming)",
    "later_source_search_partial": "machine searches that did not cover the whole corpus (sample runs); their full "
        "wording is in SUMMARY.json machine_searches",
    "proposals.original_representation[].acceptable_as_original": "false for a compiled transcription (grade "
        "compiled_transcription_lead, Richardson): a lead to the official original, never the original by itself; "
        "the feasibility test never uses it. official_compilation_* grades are GPO/OFR printings graded like "
        "fr-originals (needs_page_check or a medium/low location is never strong)",
    "proposals.current_predicate[] basis_code ofr_codification_1989_in_force": "the OFR 1989 Codification prints the "
        "order as in force on 1989-01-20 (as amended, editorial text): a lead only; its checked_through is "
        "1989-01-20, so it never satisfies the gate and never counts as a current-law lead",
    f"flags {CODIFICATION_FLAG}": "a later event or whole-order end read from the OFR 1989 Codification's disposition "
        "table (status as of 1989-01-20, OCR cell); whole_end_from_1989_disposition_table marks unqualified "
        "revocations offered as whole-order ends under later-events' rule. That table and the later-events OFR "
        "catalog notes are the same OFR data, so their agreement is not counted as corroboration by two jobs",
}

class RollingWriter:
    """Writes JSONL lines, starting a new file before one would pass max_bytes (GitHub limit 95 MB)."""

    def __init__(self, out_dir, base, max_bytes):
        self.out_dir, self.base, self.max = pathlib.Path(out_dir), base, max_bytes
        self.files, self.fh, self.size = [], None, 0

    def _open(self):
        if self.fh:
            self.fh.close()
        stem, ext = self.base.rsplit(".", 1)
        name = self.base if not self.files else f"{stem}_{len(self.files) + 1}.{ext}"
        self.fh = open(self.out_dir / name, "w", encoding="utf-8", newline="\n")
        self.files.append(name)
        self.size = 0

    def write(self, obj):
        line = json.dumps(obj, ensure_ascii=False, sort_keys=False) + "\n"
        b = len(line.encode("utf-8"))
        if self.fh is None or (self.size and self.size + b > self.max):
            self._open()
        self.fh.write(line)
        self.size += b

    def close(self, create_if_empty=True):
        if self.fh is None:
            if not create_if_empty:
                return
            self._open()
        self.fh.close()


TODO_FIELDS = ["instrument_id", "provisional_status", "decision_origin", "in_decided_3359", "clauses",
               "original_representation_from", "gate_errors_now_count", "remaining_gate_errors",
               "gate_errors_if_proposals_accepted", "only_judgment_left", "fields_needing_judgment",
               "missing_evidence", "conflicts", "sources_and_quotes_check", "checker_failures",
               "would_satisfy_once_confirmed", "steps_needing_research", "estimated_effort"]


# The claim checker's result covers only the sources and quotations copied into the draft, never the claim.
CHECK_WORDS = {"pass": "sources_ok", "pass_with_unverified": "sources_ok_some_unverified",
               "fail": "source_or_quote_problem"}


def todo_row(line):
    c, d = line["claim"], line["_draft"]
    ch = d.get("checker") or {}
    orig = next((m for m in d["machine_filled"] if m["field"] == "original_representation"), None)
    return {
        "instrument_id": line["instrument_id"],
        "provisional_status": d["provisional_status"] or "",
        "decision_origin": d["decision_origin"],
        "in_decided_3359": "yes" if d["in_decided_3359"] else "no",
        "clauses": d["clause_count"],
        "original_representation_from": f"{orig['grade']} ({orig['from']})" if orig else "",
        "gate_errors_now_count": len(d["gate"]["errors_now"]),
        "remaining_gate_errors": " | ".join(d["gate"]["errors_now_compact"]),
        "gate_errors_if_proposals_accepted": " | ".join(d["gate"]["errors_if_proposals_accepted"]),
        "only_judgment_left": "yes" if d["gate"]["only_judgment_left"] else "no",
        "fields_needing_judgment": " | ".join(j["field"] for j in d["needs_judgment"]),
        "missing_evidence": " | ".join(f"{m['step']}: {m['what']}" for m in d["missing_evidence"])[:1000],
        "conflicts": " | ".join(x["code"] for x in d["conflicts"]),
        "sources_and_quotes_check": CHECK_WORDS.get(ch.get("mechanical_result"), ch.get("mechanical_result"))
        or ("error" if ch.get("checker_error") else "not_run"),
        "checker_failures": " | ".join(ch.get("failures") or [])[:1000],
        "would_satisfy_once_confirmed": " | ".join(d["readiness"]["would_satisfy_once_confirmed"]),
        "steps_needing_research": " | ".join(d["readiness"]["needs_research"]),
        "estimated_effort": d["effort"],
    }


def guard_output(repo, out):
    claims = pathlib.Path(repo) / P["claims_dir"]
    if is_within(out, claims) or is_within(out, pathlib.Path(repo) / "research"):
        raise SystemExit(f"Refusing to write into {out}: drafts never go into research/ "
                         "(research/readiness/claims/ holds agent-asserted claims only).")


def env_int(name):
    """A positive whole number from the environment, None if unset; exit code 2 if it is not one."""
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return None
    try:
        v = int(raw)
    except ValueError:
        v = 0
    if v <= 0:
        print(f"{name} must be a whole number above 0 (got {raw!r}).")
        raise SystemExit(2)
    return v


def env_mb(name, default):
    """A positive number of megabytes from the environment (default if unset); exit code 2 if it is not one."""
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        v = float(raw)
    except ValueError:
        v = 0
    if not v > 0 or v != v or v == float("inf"):
        print(f"{name} must be a number of megabytes above 0 (got {raw!r}).")
        raise SystemExit(2)
    return v


def main():
    t0 = time.time()
    repo = pathlib.Path(os.environ.get("REPO_ROOT", ".")).resolve()
    out = pathlib.Path(os.environ.get("OUTPUT_DIR") or (HERE / "output")).resolve()
    guard_output(repo, out)
    cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / f"{JOB_NAME}-cache")).resolve()
    limit = env_int("JOB_LIMIT")
    ids = [x.strip() for x in (os.environ.get("CLAIM_DRAFTS_IDS") or "").split(",") if x.strip()]
    # Default: the 3,359 decided orders only (undecided drafts can never pass the gate; opt in with 'all').
    scope = (os.environ.get("CLAIM_DRAFTS_SCOPE") or "decided").strip().lower()
    if scope not in ("decided", "all"):
        print(f"CLAIM_DRAFTS_SCOPE must be 'decided' or 'all' (got {scope!r}).")
        raise SystemExit(2)
    use_checker = (os.environ.get("CLAIM_DRAFTS_CHECKER") or "1").strip() not in ("0", "no", "false")
    max_mb = env_mb("CLAIM_DRAFTS_MAX_FILE_MB", 90)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Reading inputs (repo {repo}) ...")
    inputs, notes = discover_inputs(repo, os.environ.get("CLAIM_DRAFTS_INPUTS"))
    for n in notes:
        print(f"  note: {n}")
    merged = load_inputs(inputs)
    for inp in inputs:
        print(f"  input {inp.job}: {inp.path} ({getattr(inp, 'n_fragments', 0)} fragments, "
              f"{getattr(inp, 'n_sources', 0)} source records)")
    rd = RepoData(repo)
    for n in rd.notes:
        print(f"  note: {n}")
    gate = load_gate(repo)
    step_for, mapping_from = load_step_mapper(repo)
    not_in_universe = sorted(i for i in merged.frags if i not in rd.universe)

    orders = select_orders(merged, rd, scope=scope, ids=ids, limit=limit)
    ids_unknown = [i for i in ids if i not in rd.universe]
    if ids_unknown:
        notes.append(f"CLAIM_DRAFTS_IDS: {len(ids_unknown)} id(s) not in the 14,972-order universe were skipped: "
                     + ", ".join(ids_unknown[:20]))
        print(f"  note: {notes[-1]}")
    print(f"  orders to draft: {len(orders)} (decided first; scope={scope}"
          + (f", JOB_LIMIT={limit}" if limit else "") + ")")

    checker, checker_note = None, None
    if use_checker:
        try:
            checker = CheckerRunner(repo, cache, inputs)
            checker_note = (f"jobs/claim-checker imported; {sum(checker.index.origin_counts.values())} held copies "
                            f"indexed ({checker.added} from CLAIM_DRAFTS_INPUTS folders)")
        except Exception as exc:  # noqa: BLE001 - the checker is optional
            checker_note = f"jobs/claim-checker could not be used: {type(exc).__name__}: {exc}"[:300]
    else:
        checker_note = "skipped (CLAIM_DRAFTS_CHECKER=0)"
    print(f"  claim checker: {checker_note}")

    writer = RollingWriter(out, "DRAFT_CLAIMS.jsonl", int(max_mb * 1_000_000))  # the 3,359 decided orders
    writer_other = RollingWriter(out, "DRAFT_CLAIMS_UNDECIDED.jsonl", int(max_mb * 1_000_000))
    todo, conflict_rows = [], []
    stats = collections.Counter()
    conflict_orders = collections.Counter()
    gate_err_orders = collections.Counter()
    hyp_err_orders = collections.Counter()
    readiness_counts = {s: collections.Counter() for s in TRACKER_STEPS}
    check_status = collections.Counter()
    effort = collections.Counter()
    for n, iid in enumerate(orders, 1):
        line = build_draft(iid, merged, rd, gate, step_for)
        if checker:
            res, rows = checker.check(line["claim"], n)
            line["_draft"]["checker"] = res
            for r in rows:
                check_status[f"{r['check']}:{r['status']}"] += 1
            stats["checker_" + (res.get("mechanical_result") or "error")] += 1
        (writer if line["_draft"]["in_decided_3359"] else writer_other).write(line)
        row = todo_row(line)
        todo.append(row)
        d = line["_draft"]
        dec = d["in_decided_3359"]
        stats["drafts"] += 1
        stats["drafts_decided"] += dec
        stats["only_judgment_left"] += d["gate"]["only_judgment_left"]
        stats["only_judgment_left_decided"] += d["gate"]["only_judgment_left"] and dec
        stats["only_judgment_and_search_left"] += d["gate"]["only_judgment_and_a_later_source_search_left"]
        stats[f"only_judgment_left_status_{d['provisional_status'] or 'none'}"] += d["gate"]["only_judgment_left"]
        stats["with_original_filled"] += line["claim"]["original_representation"] is not None
        stats["with_original_candidate_only"] += line["claim"]["original_representation"] is None and \
            any(c.get("acceptable_as_original", True) for c in d["proposals"]["original_representation"])
        stats["with_clauses"] += bool(d["clause_count"])
        stats["clauses_total"] += d["clause_count"]
        stats["with_whole_end_candidate"] += bool(d["proposals"]["whole_order_end"])
        stats["with_predicate_candidate"] += any(not is_snapshot_lead(p) for p in d["proposals"]["current_predicate"])
        stats["with_later_event_candidate"] += bool(d["proposals"]["later_events"])
        # The book jobs wired in on 2026-10-18 (official compilations, Richardson, the 1989 Codification).
        origs = d["proposals"]["original_representation"]
        filled = next((m for m in d["machine_filled"] if m["field"] == "original_representation"), None)
        stats["book_original_filled_official_compilation"] += bool(filled and filled["grade"] == "official_compilation_high")
        stats["book_official_compilation_candidate"] += any(c["grade"].startswith("official_compilation") for c in origs)
        stats["book_compiled_transcription_lead"] += any(c["grade"] == "compiled_transcription_lead" for c in origs)
        stats["book_compiled_transcription_lead_only"] += bool(origs) and all(
            c["grade"] == "compiled_transcription_lead" for c in origs)
        whole_jobs = {p["meta"].get("from_job") for p in d["proposals"]["whole_order_end"]}
        stats["book_whole_end_from_1989_table"] += CODIFICATION_JOB in whole_jobs
        stats["book_whole_end_only_from_1989_table"] += whole_jobs == {CODIFICATION_JOB}
        stats["book_in_force_1989_lead"] += any(is_snapshot_lead(p) for p in d["proposals"]["current_predicate"])
        stats["with_later_source_search_filled"] += bool(line["claim"]["later_source_search"])  # always 0 now
        stats["with_complete_machine_search_proposed"] += bool(d["proposals"]["later_source_search_machine"])
        stats["with_partial_end_on_yes"] += any(c["code"] == "PARTIAL_END_CANDIDATE_ON_YES_ORDER"
                                                for c in d["conflicts"])
        stats["with_conflict"] += bool(d["conflicts"])
        effort[d["effort"]] += 1
        for code in {c["code"] for c in d["conflicts"]}:
            conflict_orders[code] += 1
        for c in d["conflicts"]:
            conflict_rows.append({"instrument_id": iid, "provisional_status": d["provisional_status"] or "",
                                  "code": c["code"], "detail": c["detail"][:1000]})
        for e in set(re.sub(r"clause_\d+_", "clause_*_", e) for e in d["gate"]["errors_now"]):
            gate_err_orders[e] += 1
        for e in set(re.sub(r"clause_\d+_", "clause_*_", e) for e in d["gate"]["errors_if_proposals_accepted"]):
            hyp_err_orders[e] += 1
        for s, v in d["readiness"]["by_step"].items():
            readiness_counts[s][v] += 1
        if n % 500 == 0:
            print(f"  ... {n} drafts ({time.time() - t0:.0f} s)")
    writer.close()
    writer_other.close(create_if_empty=scope == "all")  # undecided drafts only on request

    with open(out / "TODO_BY_ORDER.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=TODO_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(todo)
    with open(out / "CONFLICTS.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["instrument_id", "provisional_status", "code", "detail"], lineterminator="\n")
        w.writeheader()
        w.writerows(conflict_rows)

    summary = {
        "job": JOB_NAME,
        "legal_cutoff": LEGAL_CUTOFF,
        "establishes": "nothing legal: machine drafts and to-do lists only; no status, ledger or count is changed",
        "job_limit": limit, "scope": scope, "ids_requested": ids or None, "ids_not_in_universe": ids_unknown,
        "orders_with_draft": stats["drafts"],
        "decided_orders_with_draft": stats["drafts_decided"],
        "undecided_orders_with_draft": stats["drafts"] - stats["drafts_decided"],
        "drafts_whose_only_remaining_gaps_are_judgment_fields": stats["only_judgment_left"],
        "of_which_decided": stats["only_judgment_left_decided"],
        "only_judgment_left_by_status": {k.rsplit("_", 1)[1]: v for k, v in stats.items()
                                         if k.startswith("only_judgment_left_status_")},
        "drafts_needing_only_judgment_plus_a_recorded_later_source_search": stats["only_judgment_and_search_left"],
        "top_conflict_types": dict(conflict_orders.most_common()),
        "orders_with_any_conflict": stats["with_conflict"],
        "yes_orders_with_partial_end_candidate": stats["with_partial_end_on_yes"],
        "filled": {"original_representation": stats["with_original_filled"],
                   "original_candidate_needing_check_only": stats["with_original_candidate_only"],
                   "operative_clauses": stats["with_clauses"], "clauses_total": stats["clauses_total"],
                   "later_source_search": stats["with_later_source_search_filled"],
                   "later_source_search_note": "never machine-filled; complete machine searches are in "
                                               "_draft.proposals.later_source_search_machine",
                   "later_source_search_machine_proposed": stats["with_complete_machine_search_proposed"]},
        "candidates": {"whole_order_end": stats["with_whole_end_candidate"],
                       "current_predicate": stats["with_predicate_candidate"],
                       "later_events": stats["with_later_event_candidate"],
                       "current_predicate_note": "U.S. Code / eCFR leads only; the 1989 in-force snapshot is counted "
                                                 "under book_sources"},
        "book_sources": {
            "note": "orders whose draft uses the printed-volume jobs: official GPO/OFR compilations (ofr-compilations, "
                    "isthmian-canal-1911, indian-reservations-1912; graded like fr-originals), Richardson's compiled "
                    "transcriptions (leads only, never the original) and the OFR 1989 Codification (whole-order-end "
                    "proposals from its disposition table; in-force leads checked through 1989-01-20 only)",
            "original_filled_from_official_compilation": stats["book_original_filled_official_compilation"],
            "official_compilation_candidate": stats["book_official_compilation_candidate"],
            "compiled_transcription_lead": stats["book_compiled_transcription_lead"],
            "compiled_transcription_lead_is_the_only_original_candidate": stats["book_compiled_transcription_lead_only"],
            "whole_order_end_from_1989_disposition_table": stats["book_whole_end_from_1989_table"],
            "whole_order_end_only_from_1989_disposition_table": stats["book_whole_end_only_from_1989_table"],
            "in_force_1989_lead": stats["book_in_force_1989_lead"]},
        "orders_by_remaining_gate_error": dict(gate_err_orders.most_common()),
        "orders_by_gate_error_if_proposals_accepted": dict(hyp_err_orders.most_common()),
        "readiness_by_step": {s: dict(sorted(c.items())) for s, c in readiness_counts.items()},
        "estimated_effort": dict(sorted(effort.items())),
        "claim_checker": {"note": checker_note,
                          "drafts_by_mechanical_result": {k[len("checker_"):]: v for k, v in sorted(stats.items())
                                                          if k.startswith("checker_")},
                          "check_rows_by_status": dict(sorted(check_status.items()))},
        "inputs": [{"job": i.job, "path": i.origin} for i in inputs],
        "input_counts": {k: v for k, v in sorted(merged.counts.items()) if not k.startswith("_")},
        "input_notes": notes + rd.notes,
        "input_problems": merged.problems,
        "fragment_orders_not_in_universe": len(not_in_universe),
        "fragment_orders_not_in_universe_examples": not_in_universe[:20],
        "machine_searches": [{"search_id": s["search_id"], "complete": s["complete"], "scope_note": s["scope_note"],
                              "entry": s["entry"]} for s in merged.searches],
        "gate_error_step_mapping_from": mapping_from,
        "outputs": writer.files + writer_other.files + ["TODO_BY_ORDER.csv", "CONFLICTS.csv", "SUMMARY.json"],
        "legend": LEGEND,
        "network_requests": 0,
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    with open(out / "SUMMARY.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print()
    print(f"Drafted {stats['drafts']} orders ({stats['drafts_decided']} with a provisional status) in "
          f"{summary['elapsed_seconds']} s, with no network requests.")
    print(f"  original text filled from a strong candidate: {stats['with_original_filled']}; weak candidate only: "
          f"{stats['with_original_candidate_only']}")
    print(f"  clause inventories: {stats['with_clauses']} ({stats['clauses_total']} clauses)")
    print(f"  whole-order-end candidates: {stats['with_whole_end_candidate']}; current-law leads: "
          f"{stats['with_predicate_candidate']}; later-event candidates: {stats['with_later_event_candidate']}")
    print(f"  drafts where only judgment is left (the gate would pass once an agent accepts or decides): "
          f"{stats['only_judgment_left']} ({stats['only_judgment_left_decided']} decided)")
    print(f"  ... plus drafts where only judgment and a recorded later-source search are left: "
          f"{stats['only_judgment_and_search_left']}")
    print(f"  orders with a conflict: {stats['with_conflict']}; top: "
          + ", ".join(f"{k} {v}" for k, v in conflict_orders.most_common(5)))
    print(f"  effort: {dict(sorted(effort.items()))}")
    print(f"  claim checker: {summary['claim_checker']['drafts_by_mechanical_result'] or checker_note}")
    if checker:
        v = checker.verification
        print(f"  offline verification receipts: {v.hashes} rehashes, {v.cache_hits} reused within this run, "
              f"{v.missing} missing (left unverified); no download attempts")
    print(f"Outputs in {out}: {', '.join(summary['outputs'])}. These are drafts and leads, never claims.")
    return summary


if __name__ == "__main__":
    main()
