"""Automatic claim checker: the mechanical half of reviewing a claim.

For every claim in research/readiness/claims/*.jsonl (Stage 19 claim format)
it checks, without any judgment about the law:

1. source_held       every cited source's SHA-256 matches a copy the project holds
   source_identity   the original text / clause sources belong to the claim's own order
2. quote_verbatim    every quoted text appears word for word in that copy's text
3. date_valid        dates are real ISO dates; legal dates not after the cutoff
   date_after_signing  ending/event dates are not before the order was signed
4. order_exists      every executive order number cited is in the 14,972 universe
5. structural_gate   the project's own Stage 19 claim_gate.validate_claim

Results are LEADS for reviewers, never legal conclusions. Nothing here changes
a status, a ledger or a count. See README.md.
"""

import argparse
import collections
import csv
import datetime as dt
import glob
import importlib.util
import inspect
import io
import json
import os
import pathlib
import re
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sources as S  # noqa: E402

JOB_NAME = "claim-checker"
SCHEMA = "eo-claim-check/v1"
LEGAL_CUTOFF = "2026-10-14"
STEPS = ["original_text", "clause_inventory", "ending_or_current_basis", "savings_residuals", "counterevidence"]
MECHANICAL_CHECKS = ["source_held", "source_identity", "quote_verbatim", "date_valid", "date_after_signing",
                     "order_exists"]

# The owner's policy: which custody status of a cited source counts as "held" (pass). A "skip" is
# reported as unverified and stops the step from counting as checker-passed. See README.md.
SOURCE_STATUS_RESULT = {
    "held_bytes_verified": "pass",            # the saved bytes were re-hashed on this machine and match
    "held_bytes_in_release_or_repo": "pass",  # bytes are committed (repo file or Opus LFS release), not re-hashed here
    "custody_record_only": "skip",            # only a record (hash, maybe text); the bytes are in no committed place
}
# Warnings that also stop a step from counting as checker-passed (they need a person to look).
BLOCKING_WARN_STATUSES = {"too_short_to_verify", "recorded_for_other_order_but_text_names_this_order",
                          "text_does_not_name_this_order"}
MIN_QUOTE_WORDS, MIN_QUOTE_CHARS = 6, 30  # a shorter quotation proves nothing about the clause
IDENTITY_FIELD = re.compile(r"^(original_representation|operative_clauses\[\d+\]\.original_source)$")
REF_IN_LIST = re.compile(r"(^|\.)(sources|source_refs)\[\d+\]$")
REF_KEY_PATH = re.compile(r"(^|\.)(original_representation|original_source|source)$")
CSV_MAX_MB_DEFAULT = 50  # the runner cannot commit files over 95 MB
MAX_FAILURES_LISTED = 50

P = {
    "universe": "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv",
    "decided": "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv",
    "crosswalk": "research/stage21/sources_index/OFFICIAL_SOURCE_CASE_CROSSWALK.csv",
    "stage14_fetch": "research/stage14/QUEUES/OFFICIAL_DIRECT_DOCUMENT_FETCH_MANIFEST.csv",
    "claims": "research/readiness/claims/*.jsonl",
    "claim_gate_dir": "research/stage19/code",
    "tracker_dir": "jobs/readiness-tracker",
    "ladder": "jobs/source-ladder/fetch_ladder.py",
}

SOURCE_KEYS = ("original_representation", "original_source", "source")
SOURCE_LIST_KEYS = ("sources", "source_refs")
QUOTE_KEY = re.compile(r"(^|_)(quote|quotes|quoted|quotation|quotations|verbatim|excerpt|excerpts)($|_)")
LEGAL_DATE_KEYS = {"date", "effective_date", "checked_through", "signing_date", "signed_on", "effective_on",
                   "end_date", "start_date", "expiration_date", "terminated_on", "publication_date"}
ACTIVITY_DATE_KEYS = {"checked_on", "reviewed_on", "recorded_on", "retrieved_on", "accessed_on",
                      "searched_on", "retrieved_utc", "attempted_utc", "fetched_utc", "built_utc"}
ACTIVITY_PREFIXES = ("retriev", "access", "review", "search", "record", "fetch", "download", "captur", "attempt")
CHECK_AGAINST_SIGNING = [
    re.compile(r"^operative_clauses\[\d+\]\.first_end\.date$"),
    re.compile(r"^operative_clauses\[\d+\]\.later_events\[\d+\]\.effective_date$"),
    re.compile(r"^operative_clauses\[\d+\]\.current_predicate\.checked_through$"),
    re.compile(r"^whole_order_end\.date$"),
]

# Fallback only: the readiness tracker's own mapping is imported when present.
FALLBACK_GATE_ERROR_STEP = [
    ("original_representation", "original_text"), ("operative_clauses_empty", "clause_inventory"),
    ("_scope_id", "clause_inventory"), ("_original_text_or_source", "clause_inventory"),
    ("_state", "clause_inventory"), ("_later_event", "clause_inventory"), ("_not_object", "clause_inventory"),
    ("_current_predicate", "ending_or_current_basis"), ("_first_end", "ending_or_current_basis"),
    ("whole_order", "ending_or_current_basis"), ("continuing_clause", "ending_or_current_basis"),
    ("savings_residuals", "savings_residuals"), ("bounded_later_search", "counterevidence"),
]

CSV_FIELDS = ["claim_key", "instrument_id", "effective_for_tracker", "step", "check",
              "field", "result", "status", "detail"]


# ---------------------------------------------------------------- helpers

def exact_date(value):
    if not isinstance(value, str):
        return False
    try:
        return dt.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def activity_date(value):
    """Date or date-time in ISO form; returns the date or None."""
    if not isinstance(value, str):
        return None
    try:
        if len(value) == 10:
            return dt.date.fromisoformat(value) if exact_date(value) else None
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def walk(obj, path="", chain=()):
    """Yield (path, key, value, chain_of_parent_dicts) for every dict entry and list item."""
    if isinstance(obj, dict):
        chain = chain + (obj,)
        for key, val in obj.items():
            p = f"{path}.{key}" if path else key
            yield p, key, val, chain
            yield from walk(val, p, chain)
    elif isinstance(obj, list):
        for n, val in enumerate(obj):
            p = f"{path}[{n}]"
            yield p, None, val, chain
            yield from walk(val, p, chain)


def step_for_path(path):
    if path.startswith("original_representation"):
        return "original_text"
    m = re.match(r"operative_clauses\[\d+\]\.(\w+)", path)
    if m:
        return "ending_or_current_basis" if m.group(1) in ("first_end", "current_predicate") else "clause_inventory"
    if path.startswith("operative_clauses"):
        return "clause_inventory"
    if path.startswith("whole_order_end"):
        return "ending_or_current_basis"
    if path.startswith("savings_residuals"):
        return "savings_residuals"
    if path.startswith(("later_source_search", "counterevidence")):
        return "counterevidence"
    return "claim_record"


# ------------------------------------------------------------ text matching

LIGATURES = str.maketrans({"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
                           "\ufb05": "st", "\ufb06": "st", "\u00ad": None})
FOLD = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'", "\u2032": "'",
                      "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u2033": '"',
                      "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2015": "-",
                      "\u2212": "-"})
HYPHEN_BREAK = re.compile(r"(\w)-[ \t]*\n[ \t]*(?=\w)")
HYPHEN_KEEP = re.compile(r"(\w-)[ \t]*\n[ \t]*(?=\w)")


def _ws(s):
    """Collapse whitespace; drop spaces an extractor puts before closing / after opening punctuation."""
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r" (?=[.,;:!?)\]}\u2019\u201d])", "", s)
    return re.sub(r"(?<=[(\[{\u2018\u201c]) ", "", s)


def norm_variants(text):
    """Text with only whitespace, ligatures and line-break hyphenation normalised (3 readings)."""
    t = text.translate(LIGATURES).replace("\r\n", "\n").replace("\r", "\n")
    out = []
    for v in (_ws(HYPHEN_BREAK.sub(r"\1", t)), _ws(HYPHEN_KEEP.sub(r"\1", t)), _ws(t)):
        if v not in out:
            out.append(v)
    return out


def norm_quote(q):
    return _ws(HYPHEN_BREAK.sub(r"\1", q.translate(LIGATURES).replace("\r\n", "\n")))


def fold(s):
    return _ws(s.translate(FOLD).lower())


class Prepared:
    """A source text with its normalised readings computed once (reused for every quotation)."""

    __slots__ = ("pages", "full", "variants", "_folded", "_page_variants")

    def __init__(self, pages):
        self.pages = list(pages)
        self.full = "\n".join(self.pages)
        self.variants = norm_variants(self.full)
        self._folded = None
        self._page_variants = None

    @property
    def folded(self):
        if self._folded is None:
            self._folded = [fold(v) for v in self.variants]
        return self._folded

    @property
    def page_variants(self):
        if self._page_variants is None:
            self._page_variants = [norm_variants(p) for p in self.pages]
        return self._page_variants

    def occurrences(self, nq):
        return max((v.count(nq) for v in self.variants), default=0) if nq else 0


def find_quote(quote, pages):
    """(status, where, hint): status is exact | normalised | not_found. pages: list of str or Prepared."""
    prep = pages if isinstance(pages, Prepared) else Prepared(pages)
    nq = norm_quote(quote)
    if not nq:
        return "not_found", "", "empty quotation"

    def where():  # only computed for quotations that were found
        if len(prep.pages) == 1:
            return ""
        hits = [str(i + 1) for i, pv in enumerate(prep.page_variants) if any(nq in v for v in pv)]
        return ("text page " + ",".join(hits)) if hits else "spans a page break"

    if quote in prep.full:
        return "exact", where(), ""
    variants = prep.variants
    if any(nq in v for v in variants):
        return "normalised", where(), ""
    hints = []
    fq = fold(nq)
    if any(fq in v for v in prep.folded):
        hints.append("would match only after folding quote marks/dashes/letter case (not accepted)")
    words = nq.split(" ")
    lo, hi = 0, len(words)
    while lo < hi:  # longest leading run of words found
        mid = (lo + hi + 1) // 2
        if any(" ".join(words[:mid]) in v for v in variants):
            lo = mid
        else:
            hi = mid - 1
    hints.append(f"first {lo} of {len(words)} words found in order")
    return "not_found", "", "; ".join(hints)


# ----------------------------------------------------------- order citations

ID_TOKEN = re.compile(r"\bEO:[0-9A-Za-z\u00bd][0-9A-Za-z\u00bd:._\-]*")
# A number: "12944" or "12,944"; then an optional "-1" (EO:106-1) or letter suffix (EO:3016N / 3016-N).
_END = r"(?!\d)(?!,\d{3}(?!\d))"  # not inside a longer number or before a thousands group
_NUM = r"(\d{1,2},\d{3}|\d{1,5})" + _END + r"(?:-(\d{1,2})(?!\d)|-?([A-Z])(?![A-Za-z]))?"
_NUM_MORE = r"(\d{1,2},\d{3}|\d{3,5})" + _END + r"(?:-(\d{1,2})(?!\d)|-?([A-Z])(?![A-Za-z]))?"
# A number in a list that is really a citation part ("1995 Comp.", "60 FR 309", "92 Stat.") is not an order.
_NOT_ORDER_AFTER = r"(?!\s*(?:Comp\b|FR\b|F\.R\.|Fed\.\s*Reg|Stat\b|U\.S\.C|USC\b|C\.F\.R|CFR\b))"
PROSE = re.compile(
    r"(?i:\b(executive\s+orders?|exec\.\s*orders?|ex\.\s*ords?\.|e\.\s?o\.|eos?)(?=[\s.#\d]))"
    r"\s*(?i:(nos?)\.?|numbers?|#)?\s*" + _NUM)
PROSE_MORE = re.compile(r"\s*(?:,\s*and|,|and|&|or)\s*(?i:nos?\.\s*)?" + _NUM_MORE + _NOT_ORDER_AFTER)


def cited_orders(text):
    """[(as_written, candidate_ids)] for each executive order cited in a string."""
    out = []
    for m in ID_TOKEN.finditer(text):
        tok = m.group(0).rstrip(".,;:-_")
        out.append((tok, [tok, tok.replace("-", "", 1)] if re.match(r"EO:\d+-[A-Z]$", tok) else [tok]))
    for m in PROSE.finditer(text):
        nums = [(m.group(3), m.group(4), m.group(5))]
        plural = m.group(1).lower().rstrip(".").endswith("s") or (m.group(2) or "").lower() == "nos"
        end = m.end()
        while plural:
            more = PROSE_MORE.match(text, end)
            if not more:
                break
            nums.append((more.group(1), more.group(2), more.group(3)))
            end = more.end()
        for num, dsuf, suf in nums:
            n = str(int(num.replace(",", "")))
            if dsuf:
                cands, shown = [f"EO:{n}-{dsuf}"], f"{num}-{dsuf}"
            elif suf:
                cands, shown = [f"EO:{n}{suf}", f"EO:{n}-{suf}"], f"{num}-{suf}"
            else:
                cands, shown = [f"EO:{n}"], num
            out.append((f"{m.group(1)} {shown}", cands))
    return out


# --------------------------------------------------------------- inputs

def read_csv(path):
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def load_universe(repo):
    return {r["id"] for r in read_csv(repo / P["universe"])}


def load_statuses(repo):
    p = repo / P["decided"]
    return {r["instrument_id"]: r["provisional_substantive_status"] for r in read_csv(p)} if p.is_file() else {}


def load_signing(repo):
    """{id: {"full": set(ISO dates), "year": int|None}} and counts by origin."""
    sig = collections.defaultdict(lambda: {"full": set(), "year": None})
    counts = collections.Counter()

    def add_full(i, d, origin):
        if i and exact_date(d) and d <= LEGAL_CUTOFF:
            if d not in sig[i]["full"]:
                counts[origin] += 1
            sig[i]["full"].add(d)

    p = repo / P["crosswalk"]
    if p.is_file():
        for r in read_csv(p):
            add_full(r["instrument_id"], r.get("signing_date_from_cached_index"), "stage21_crosswalk")
    p = repo / P["stage14_fetch"]
    if p.is_file():
        for r in read_csv(p):
            add_full(r["instrument_id"], r.get("signing_date"), "stage14_fetch_manifest")
    for p in sorted((repo / "jobs").glob("*/output/*.csv")):
        # Other jobs are written in parallel: a file that cannot be read is noted and skipped.
        try:
            if p.parent.parent.name == JOB_NAME or p.stat().st_size > 50_000_000:
                continue
            with open(p, encoding="utf-8", errors="replace", newline="") as fh:
                header = next(csv.reader(fh), [])
            if "instrument_id" in header and "signing_date" in header:
                for r in read_csv(p):
                    add_full(r.get("instrument_id"), r.get("signing_date"), f"jobs/{p.parent.parent.name}/output/{p.name}")
        except (OSError, csv.Error, ValueError) as exc:
            counts[f"unreadable:jobs/{p.parent.parent.name}/output/{p.name}:{type(exc).__name__}"] += 1
    p = repo / P["universe"]
    for r in read_csv(p):
        y = r.get("date_effective") or ""
        if re.fullmatch(r"\d{4}", y):
            sig[r["id"]]["year"] = int(y)
            counts["identity_layer_year_only"] += 1
    return sig, counts


def load_gate(repo):
    gate_dir = repo / P["claim_gate_dir"]
    spec = importlib.util.spec_from_file_location("claim_gate", gate_dir / "claim_gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # the project's own gate, imported, not copied
    return mod


def load_step_mapper(repo):
    """The readiness tracker's gate-error -> step mapping, so both agree."""
    p = repo / P["tracker_dir"] / "tracker.py"
    if p.is_file():
        try:
            spec = importlib.util.spec_from_file_location("readiness_tracker_for_checker", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.step_for_gate_error, "jobs/readiness-tracker/tracker.py"
        except Exception as exc:  # noqa: BLE001 - fall back safely
            print(f"  note: could not import the tracker's step mapping ({exc}); using a copy")

    def fallback(error):
        for fragment, step in FALLBACK_GATE_ERROR_STEP:
            if fragment in error:
                return step
        return None

    return fallback, "fallback copy in checker.py"


def read_claims(paths, repo):
    """[(claim_key, file_rel, line, claim_or_None, parse_error)] in tracker order (file name, then line)."""
    out = []
    for path in paths:
        path = pathlib.Path(path)
        try:
            rel = path.resolve().relative_to(repo).as_posix()
        except ValueError:
            rel = path.as_posix()
        try:
            data = path.read_bytes()
        except OSError as exc:
            out.append((f"{rel}:0", rel, 0, None, f"claim file could not be read: {type(exc).__name__}: {exc}"[:200]))
            continue
        for n, raw in enumerate(data.split(b"\n"), 1):
            try:
                line = raw.decode("utf-8-sig" if n == 1 else "utf-8")
            except UnicodeDecodeError as exc:
                out.append((f"{rel}:{n}", rel, n, None, f"line is not valid UTF-8 ({exc.reason} at byte {exc.start})"))
                continue
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError("line is not a JSON object")
                out.append((f"{rel}:{n}", rel, n, obj, None))
            except (ValueError, RecursionError) as exc:
                out.append((f"{rel}:{n}", rel, n, None, f"{type(exc).__name__}: {exc}"[:200]))
    return out


# --------------------------------------------------------------- checks

class Context:
    def __init__(self, repo, job_dir, cache_dir, today=None, index=None):
        self.repo = pathlib.Path(repo).resolve()
        self.job_dir = pathlib.Path(job_dir)
        self.cache_dir = pathlib.Path(cache_dir)
        self.universe = load_universe(self.repo)
        self.statuses = load_statuses(self.repo)
        self.signing, self.signing_counts = load_signing(self.repo)
        self.gate = load_gate(self.repo)
        self.step_for_gate_error, self.step_mapping_from = load_step_mapper(self.repo)
        roots = [r for r in os.environ.get("CLAIM_CHECKER_CACHE_ROOTS", "").split(os.pathsep) if r]
        self.index = index or S.build_index(self.repo, self.job_dir, roots, exclude_jobs=(JOB_NAME,))
        self.reader = S.TextReader(self.cache_dir, packed=self.index.packed_texts)
        self._prepared = collections.OrderedDict()  # recently used source texts, normalised once
        self.today = today or dt.datetime.now(dt.timezone.utc).date()
        try:
            import pypdf  # noqa: F401
            self.pypdf = getattr(pypdf, "__version__", "yes")
        except ImportError:
            self.pypdf = None
        self.not_held = []  # (claim_key, field, ref) for --fetch

    def prepared(self, copy, pages, how):
        key = (copy.origin, copy.sha256, str(copy.text_path), how)
        prep = self._prepared.get(key)
        if prep is None:
            prep = self._prepared[key] = Prepared(pages)
            while len(self._prepared) > 32:
                self._prepared.popitem(last=False)
        self._prepared.move_to_end(key)
        return prep

    def prepared_texts(self, copies):
        """[(Prepared, how, copy)] for every readable text of the copies, and the reasons for any missing."""
        out, reasons = [], []
        for copy in copies:
            texts, why = self.reader.texts(copy)
            if why:
                reasons.append(why)
            out += [(self.prepared(copy, pages, how), how, copy) for pages, how in texts]
        return out, reasons


def _row(rows, step, check, field, result, status, detail=""):
    rows.append({"step": step, "check": check, "field": field, "result": result,
                 "status": status, "detail": (detail or "")[:600]})


def check_source(ref, field, ctx, rows):
    step = step_for_path(field)
    raw = ref.get("sha256") or ref.get("local_file_sha256")
    sha = S.sha_hex(raw)
    url = ref.get("url")
    if raw and not sha:
        _row(rows, step, "source_held", field, "fail", "malformed_sha256", f"not a 64-hex SHA-256: {str(raw)[:80]}")
        return None
    if not sha:
        if ref.get("archival_id"):
            _row(rows, step, "source_held", field, "skip", "no_hash_in_reference",
                 f"archival item {ref.get('archival_id')} without a file SHA-256; custody cannot be checked by machine")
        else:
            _row(rows, step, "source_held", field, "fail", "no_hash_in_reference", "source reference has no sha256")
        return None
    copies = ctx.index.lookup_sha(sha)
    if copies:
        kept = [c for c in copies if c.bytes_kept]
        checks = [ctx.reader.verify_bytes(c) for c in kept]
        origins = sorted({c.origin for c in copies})
        if True in checks:
            status, detail = "held_bytes_verified", "saved bytes re-hashed on this machine and match"
        elif False in checks:
            _row(rows, step, "source_held", field, "fail", "held_record_but_local_bytes_differ",
                 f"a custody record ({', '.join(origins)}) lists this hash but the saved file hashes differently")
            return sha
        elif any(c.custody in ("repo_file", "opus_release") for c in kept):
            where = sorted({"the Opus LFS release" if c.custody == "opus_release" else "a committed repo file"
                            for c in kept if c.custody in ("repo_file", "opus_release")})
            status, detail = "held_bytes_in_release_or_repo", \
                f"bytes are kept in {' and '.join(where)}, not on this machine, so not re-hashed here"
        else:
            status, detail = "custody_record_only", (
                "only a custody record (hash, perhaps extracted text) exists; the original bytes are in no "
                "committed place (another job's download cache or not kept). Unverified until the bytes are held")
        detail = f"recorded in {', '.join(origins)}; {detail}"
        urls = {S.norm_url(c.url) for c in copies if c.url}
        if url and urls and S.norm_url(url) not in urls:
            detail += f"; same bytes are recorded under a different URL ({sorted(urls)[0]})"
        _row(rows, step, "source_held", field, SOURCE_STATUS_RESULT[status], status, detail)
        return sha
    same_url = ctx.index.lookup_url(url)
    if same_url:
        held = sorted({f"{c.sha256[:12]}... ({c.origin}{', ' + c.note if c.note else ''})" for c in same_url})
        _row(rows, step, "source_held", field, "fail", "held_but_different_hash",
             f"the project holds this URL with other bytes: {'; '.join(held[:3])}")
    else:
        _row(rows, step, "source_held", field, "fail", "not_held",
             f"no saved copy with sha256 {sha[:12]}... and no saved copy of {url or 'this reference'}")
    return sha


def check_quote(quote, field, ref, ref_field, ctx, rows):
    step = step_for_path(field)
    if not isinstance(quote, str) or not quote.strip():
        _row(rows, step, "quote_verbatim", field, "fail", "empty_or_not_text", "quotation is empty or not text")
        return
    if not isinstance(ref, dict):
        _row(rows, step, "quote_verbatim", field, "skip", "no_source_for_quote", "no source reference to check it against")
        return
    sha = S.sha_hex(ref.get("sha256")) or S.sha_hex(ref.get("local_file_sha256"))
    copies = ctx.index.lookup_sha(sha) if sha else []
    other = False
    if not copies:
        copies = ctx.index.lookup_url(ref.get("url"))
        other = bool(copies)
    if not copies:
        _row(rows, step, "quote_verbatim", field, "skip", "source_text_not_available",
             f"cited source ({ref_field}) is not held, so the quotation cannot be checked")
        return
    best, reasons = None, []
    rank = {"exact": 3, "normalised": 2, "not_found": 1}
    for copy in copies:
        texts, why = ctx.reader.texts(copy)
        if why:
            reasons.append(why)
        for pages, how in texts:
            prep = ctx.prepared(copy, pages, how)
            status, where, hint = find_quote(quote, prep)
            if best is None or rank[status] > rank[best[0]]:
                best = (status, where, hint, how, copy, prep)
            if status == "exact":
                break
        if best and best[0] == "exact":
            break
    searched = f"{ref.get('url') or '(no url)'} sha256 {(sha or '?')[:12]}"
    if best is None:
        _row(rows, step, "quote_verbatim", field, "skip", "source_text_not_available",
             f"held copy of {searched} has no readable text here: " + ("; ".join(sorted(set(reasons))) or "unknown"))
        return
    status, where, hint, how, copy, prep = best
    detail = f"searched {searched} as cited at {ref_field} ({copy.origin} text, {how})" + \
        (f", {where}" if where else "") + (f"; {hint}" if hint else "")
    if other:
        _row(rows, step, "quote_verbatim", field, "warn" if status != "not_found" else "fail",
             f"other_copy_{status}", "the cited hash is not held; " + detail + " (a different saved copy of the same URL)")
        return
    if status != "not_found":
        nq = norm_quote(quote)
        n_words, times = len(nq.split()), prep.occurrences(nq)
        detail += f"; occurs {times} time(s)" if times else ""
        if n_words < MIN_QUOTE_WORDS and len(nq) < MIN_QUOTE_CHARS:
            _row(rows, step, "quote_verbatim", field, "warn", "too_short_to_verify",
                 f"found ({status}) but only {n_words} word(s) / {len(nq)} characters: too short to show that the "
                 f"claimed text is in the source (needs {MIN_QUOTE_WORDS}+ words or {MIN_QUOTE_CHARS}+ characters); "
                 + detail)
            return
    _row(rows, step, "quote_verbatim", field, "fail" if status == "not_found" else "pass", status, detail)


def _order_number_pattern(iid):
    """Regex that finds this order named in a source text ('Executive Order 12,950', 'No. 3016-N'), or None."""
    m = re.fullmatch(r"EO:(\d+)(?:-(\d{1,2})|-?([A-Za-z]))?", iid or "")
    if not m:
        return None
    digits, dsuf, lsuf = m.groups()
    num = digits if len(digits) <= 3 else f"{digits[:-3]},?{digits[-3:]}"
    num = rf"0*{num}"
    if dsuf:
        num += rf"-{dsuf}(?!\d)"
    elif lsuf:
        num += rf"\s?-?\s?{lsuf}(?![A-Za-z])"
    else:
        num += r"(?![\d]|-?[A-Za-z]\b)"
    return re.compile(rf"(?i:executive\s+order|e\.\s?o\.|\bno\.)\s*(?i:no\.?\s*)?(?<!\d){num}")


def _same_order(a, b):
    return isinstance(a, str) and isinstance(b, str) and (a == b or a.replace("-", "") == b.replace("-", ""))


def check_identity(ref, field, iid, ctx, rows):
    """Is the cited original (or clause source) a copy of the claim's own order, not another order's?"""
    step = step_for_path(field)
    sha = S.sha_hex(ref.get("sha256")) or S.sha_hex(ref.get("local_file_sha256"))
    copies = ctx.index.lookup_sha(sha) if sha else []
    if not copies or not isinstance(iid, str):
        return  # not held (source_held already fails) or no order id (order_exists fails)
    recorded = sorted({i for c in copies for i in c.instrument_ids})
    origins = sorted({c.origin for c in copies if c.instrument_ids})
    if any(_same_order(i, iid) for i in recorded):
        _row(rows, step, "source_identity", field, "pass", "recorded_for_this_order",
             f"custody record ({', '.join(origins)}) lists {iid}")
        return
    pattern = _order_number_pattern(iid)
    named, have_text = False, False
    if pattern is not None:
        for copy in copies:
            texts, _ = ctx.reader.texts(copy)
            for pages, how in texts:
                have_text = True
                if any(pattern.search(v) for v in ctx.prepared(copy, pages, how).variants):
                    named = True
                    break
            if named:
                break
    others = ", ".join(recorded[:5]) + (" ..." if len(recorded) > 5 else "")
    if named and recorded:
        _row(rows, step, "source_identity", field, "warn", "recorded_for_other_order_but_text_names_this_order",
             f"custody records list {others}, not {iid}, though the text names {iid} (perhaps a page holding "
             "several orders, or an order that amends this one); a person must confirm")
    elif named:
        _row(rows, step, "source_identity", field, "pass", "text_names_this_order",
             f"no custody record names an order; the saved text names {iid}")
    elif recorded:
        _row(rows, step, "source_identity", field, "fail", "recorded_for_other_order",
             f"this copy is recorded as {others} ({', '.join(origins)}), not {iid}"
             + ("" if have_text else "; no text to search for the order number"))
    elif have_text:
        _row(rows, step, "source_identity", field, "warn", "text_does_not_name_this_order",
             f"no custody record names an order and the saved text does not name {iid} "
             "(a poor text layer can hide it); a person must confirm")
    else:
        _row(rows, step, "source_identity", field, "skip", "no_order_association_or_text",
             "no custody record names an order and there is no text to search")


def check_dates(claim, ctx, rows):
    iid = claim.get("instrument_id")
    sig = ctx.signing.get(iid) if isinstance(iid, str) else None
    for path, key, val, _ in walk(claim):
        if key is None or val is None or isinstance(val, (dict, list)):
            continue
        step = step_for_path(path)
        activity = key in ACTIVITY_DATE_KEYS or key.endswith("_utc") or (
            key.startswith(ACTIVITY_PREFIXES) and (key.endswith("_on") or key.endswith("_date")))
        if activity and key not in LEGAL_DATE_KEYS:
            d = activity_date(val)
            if d is None:
                _row(rows, step, "date_valid", path, "fail", "not_iso_date", f"{val!r} is not an ISO date or date-time")
            elif d > ctx.today:
                _row(rows, step, "date_valid", path, "fail", "in_the_future", f"{val} is after today ({ctx.today})")
            else:
                _row(rows, step, "date_valid", path, "pass", "valid_activity_date",
                     "research activity date (may be after the legal cutoff)")
            continue
        if key not in LEGAL_DATE_KEYS and not key.endswith("_date"):
            continue
        if not exact_date(val):
            _row(rows, step, "date_valid", path, "fail", "not_exact_iso_date", f"{val!r} is not an exact YYYY-MM-DD date")
            continue
        if val > LEGAL_CUTOFF:
            _row(rows, step, "date_valid", path, "fail", "after_legal_cutoff", f"{val} is after the cutoff {LEGAL_CUTOFF}")
            continue
        _row(rows, step, "date_valid", path, "pass", "valid_legal_date", "")
        if key == "signing_date" and path == "signing_date" and sig and sig["full"] and val not in sig["full"]:
            _row(rows, step, "date_after_signing", path, "warn", "claimed_signing_date_differs_from_index",
                 f"claim says {val}; index says {', '.join(sorted(sig['full']))}")
        if not any(r.match(path) for r in CHECK_AGAINST_SIGNING):
            continue
        if sig and sig["full"]:
            first = min(sig["full"])
            note = f" (index has {len(sig['full'])} differing dates; earliest used)" if len(sig["full"]) > 1 else ""
            if val < first:
                _row(rows, step, "date_after_signing", path, "fail", "before_signing_date",
                     f"{val} is before the order's signing date {first}{note}")
            else:
                _row(rows, step, "date_after_signing", path, "pass", "on_or_after_signing_date", f"signed {first}{note}")
        elif sig and sig["year"]:
            if int(val[:4]) < sig["year"]:
                _row(rows, step, "date_after_signing", path, "warn", "before_index_year",
                     f"{val} is before the year {sig['year']} in the identity layer (year only; it may be a publication year)")
            else:
                _row(rows, step, "date_after_signing", path, "pass", "on_or_after_index_year_only",
                     f"only the year ({sig['year']}) is known")
        else:
            _row(rows, step, "date_after_signing", path, "skip", "no_signing_date_known", "")


def check_orders(claim, ctx, rows):
    seen = set()
    iid = claim.get("instrument_id")
    if isinstance(iid, str):
        seen.add(iid)
        if iid in ctx.universe:
            _row(rows, "claim_record", "order_exists", "instrument_id", "pass", "in_universe", iid)
        else:
            _row(rows, "claim_record", "order_exists", "instrument_id", "fail", "not_in_universe",
                 f"{iid} is not an id in the 14,972-order universe")
    for path, key, val, _ in walk(claim):
        if not isinstance(val, str) or path == "instrument_id":
            continue
        for written, cands in cited_orders(val):
            if cands[0] in seen:
                continue
            seen.add(cands[0])
            step = step_for_path(path)
            hit = next((c for c in cands if c in ctx.universe), None)
            if hit == cands[0] and written.startswith("EO:"):
                _row(rows, step, "order_exists", path, "pass", "in_universe", hit)
            elif hit:
                _row(rows, step, "order_exists", path, "pass" if not written.startswith("EO:") else "warn",
                     "in_universe", f"'{written}' = {hit}")
            else:
                _row(rows, step, "order_exists", path, "fail", "not_in_universe",
                     f"'{written}' is not in the 14,972-order universe")


def check_gate(claim, ctx, rows):
    iid = claim.get("instrument_id")
    status = ctx.statuses.get(iid) if isinstance(iid, str) else None
    try:
        errors = list(ctx.gate.validate_claim(claim, expected_status=status))
    except Exception as exc:  # noqa: BLE001 - a malformed value must not stop the whole run
        _row(rows, "claim_record", "structural_gate", "", "fail", "gate_raised_exception",
             f"claim_gate.validate_claim raised {type(exc).__name__}: {exc} - a value in this claim has a type the "
             "gate does not expect (for example a list where a string belongs); fix the claim line")
        return ["gate_raised_exception"], status
    for e in errors:
        _row(rows, ctx.step_for_gate_error(e) or "claim_record", "structural_gate", "", "fail", e,
             "claim_gate.validate_claim error" + (f" (provisional status is {status})" if e == "whole_order_status_mismatch" else ""))
    if not errors:
        _row(rows, "claim_record", "structural_gate", "", "pass", "gate_passed", "claim_gate.validate_claim: no errors")
    return errors, status


def check_claim(claim, ctx):
    rows = []
    for path, key, val, chain in walk(claim):
        refs = []
        if key in SOURCE_KEYS and isinstance(val, dict):
            refs = [(path, val)]
        elif key in SOURCE_LIST_KEYS and isinstance(val, list):
            refs = [(f"{path}[{n}]", v) for n, v in enumerate(val) if isinstance(v, dict)]
        for field, ref in refs:
            sha = check_source(ref, field, ctx, rows)
            if sha is None or not any(c.bytes_kept for c in ctx.index.lookup_sha(sha)):
                ctx.not_held.append((field, ref))
            if IDENTITY_FIELD.match(field):
                check_identity(ref, field, claim.get("instrument_id"), ctx, rows)
        if key is None:
            continue
        quotes = []
        parent_path = path.rsplit(".", 1)[0] if "." in path else ""
        if key == "original_operative_text" or QUOTE_KEY.search(key):
            if isinstance(val, str):
                quotes = [(path, val, chain, parent_path)]
            elif isinstance(val, list):
                quotes = [(f"{path}[{n}]", v, chain, parent_path) for n, v in enumerate(val) if isinstance(v, str)]
            elif isinstance(val, dict) and isinstance(val.get("text"), str):
                quotes = [(f"{path}.text", val["text"], chain + (val,), path)]
        for field, q, qchain, own_path in quotes:
            ref, ref_field = None, None
            own = qchain[-1] if qchain else None
            if isinstance(own, dict) and (REF_KEY_PATH.search(own_path) or REF_IN_LIST.search(own_path)) and \
                    any(k in own for k in ("sha256", "local_file_sha256", "url")):
                ref, ref_field = own, own_path  # the quote sits inside the source reference itself
            else:
                for obj in reversed(qchain):
                    for k in ("original_source", "source"):
                        if isinstance(obj.get(k), dict) and obj.get(k) is not val:
                            ref, ref_field = obj[k], k
                            break
                    if ref is not None:
                        break
            if ref is None:
                ref, ref_field = claim.get("original_representation"), "original_representation"
            check_quote(q, field, ref, ref_field, ctx, rows)
    check_dates(claim, ctx, rows)
    check_orders(claim, ctx, rows)
    errors, status = check_gate(claim, ctx, rows)
    return rows, errors, status


def parts_present(claim):
    clauses = claim.get("operative_clauses") if isinstance(claim.get("operative_clauses"), list) else []
    clauses = [c for c in clauses if isinstance(c, dict)]
    return {
        "original_text": isinstance(claim.get("original_representation"), dict),
        "clause_inventory": bool(clauses),
        "ending_or_current_basis": isinstance(claim.get("whole_order_end"), dict)
        or any(isinstance(c.get("first_end"), dict) or isinstance(c.get("current_predicate"), dict) for c in clauses),
        "savings_residuals": isinstance(claim.get("savings_residuals"), dict),
        "counterevidence": isinstance(claim.get("later_source_search"), list) and bool(claim.get("later_source_search")),
    }


def summarise_claim(key, file_rel, line, claim, rows, errors, status, ctx):
    present = parts_present(claim)

    def verdict(rs):
        if any(r["result"] == "fail" for r in rs):
            return "fail"
        if any(r["result"] == "skip" or (r["result"] == "warn" and r["status"] in BLOCKING_WARN_STATUSES)
               for r in rs):
            return "pass_with_unverified"
        return "pass"

    mech_rows = [r for r in rows if r["check"] in MECHANICAL_CHECKS]
    mech = {step: verdict([r for r in mech_rows if r["step"] == step]) for step in STEPS + ["claim_record"]}
    gate_steps = {ctx.step_for_gate_error(e) for e in errors}
    gate_crashed = "gate_raised_exception" in errors
    steps = {}
    for step in STEPS:
        gate_ok = step not in gate_steps and not gate_crashed
        steps[step] = {
            "present": present[step],
            "mechanical": mech[step] if present[step] else "absent",
            "gate": ("pass" if gate_ok else "fail") if present[step] else ("fail" if not gate_ok else "absent"),
            "checker_passed": bool(present[step] and mech[step] == "pass" and gate_ok and mech["claim_record"] != "fail"),
        }
    mechanical = verdict(mech_rows)
    failures = [f"{r['check']}:{r['status']}@{r['field'] or '-'}" for r in rows if r["result"] == "fail"]
    return {
        "claim_key": key, "file": file_rel, "line": line,
        "instrument_id": claim.get("instrument_id"),
        "claim_sha256": ctx.gate.claim_sha(claim),
        "provisional_status": status,
        "mechanical_result": mechanical,
        "gate_passed": not errors,
        "all_checks_passed": mechanical == "pass" and not errors,
        "gate_errors": errors,
        "gate_claim_level_errors": [e for e in errors if ctx.step_for_gate_error(e) is None],
        "steps": steps,
        "check_counts": {c: dict(sorted(collections.Counter(r["result"] for r in rows if r["check"] == c).items()))
                         for c in MECHANICAL_CHECKS + ["structural_gate"]},
        "failures": failures[:MAX_FAILURES_LISTED],
        "failures_total": len(failures),
        "unverified": [f"{r['check']}:{r['status']}@{r['field'] or '-'}" for r in mech_rows
                       if r["result"] == "skip" or (r["result"] == "warn" and r["status"] in BLOCKING_WARN_STATUSES)
                       ][:MAX_FAILURES_LISTED],
    }


def error_summary(key, file_rel, line, claim, exc, ctx):
    """Per-claim entry when the checker itself failed on this claim (the run continues)."""
    try:
        csha = ctx.gate.claim_sha(claim)
    except Exception:  # noqa: BLE001
        csha = ""
    iid = claim.get("instrument_id") if isinstance(claim.get("instrument_id"), str) else None
    present = {}
    try:
        present = parts_present(claim)
    except Exception:  # noqa: BLE001
        pass
    msg = f"{type(exc).__name__}: {exc}"[:300]
    return {
        "claim_key": key, "file": file_rel, "line": line, "instrument_id": iid, "claim_sha256": csha,
        "provisional_status": ctx.statuses.get(iid) if iid else None,
        "mechanical_result": "fail", "gate_passed": False, "all_checks_passed": False,
        "gate_errors": [], "gate_claim_level_errors": [], "checker_error": msg,
        "steps": {s: {"present": bool(present.get(s)), "mechanical": "error", "gate": "error", "checker_passed": False}
                  for s in STEPS},
        "check_counts": {}, "failures": [f"checker_error:{type(exc).__name__}@-"], "failures_total": 1,
        "unverified": [],
    }


# ----------------------------------------------------------------- --fetch

CITATION_LIKE = re.compile(r"^\s*\d+\s+(FR|F\.R\.|Stat\.|U\.S\.C\.|CFR|C\.F\.R\.)\s+\d+", re.I)


def _kwargs_for(fn, offered):
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return {}
    if any(p.kind == p.VAR_KEYWORD for p in params.values()):
        return dict(offered)
    return {k: v for k, v in offered.items() if k in params}


def load_ladder(repo, cache_dir):
    """A callable fetch(ref, instrument_id, step) -> (source_record|None, attempts) from
    jobs/source-ladder/fetch_ladder.py (built separately; imported defensively)."""
    p = repo / P["ladder"]
    if not p.is_file():
        return None, f"{P['ladder']} is not present"
    try:
        if str(p.parent) not in sys.path:
            sys.path.insert(0, str(p.parent))
        old = sys.modules.get("fetch_ladder")
        if old is not None and pathlib.Path(getattr(old, "__file__", "") or "").resolve() != p.resolve():
            del sys.modules["fetch_ladder"]
        mod = importlib.import_module("fetch_ladder")
    except Exception as exc:  # noqa: BLE001
        return None, f"could not import {P['ladder']}: {type(exc).__name__}: {exc}"
    cache_dir = pathlib.Path(cache_dir)
    max_req = int(os.environ.get("CLAIM_CHECKER_FETCH_MAX_REQUESTS") or 300)

    # 1. The ladder's own classes (Fetcher + Ladder + Wanted).
    if all(callable(getattr(mod, n, None)) for n in ("Fetcher", "Ladder", "Wanted")):
        try:
            fetcher = mod.Fetcher(**_kwargs_for(mod.Fetcher, {"cache_dir": cache_dir, "max_requests": max_req}))
            ladder = mod.Ladder(fetcher)
        except Exception as exc:  # noqa: BLE001
            return None, f"could not start the source ladder: {type(exc).__name__}: {exc}"

        def via_classes(ref, iid, step):
            page = ref.get("page_or_item") or ""
            wanted = mod.Wanted(**_kwargs_for(mod.Wanted, {
                "wanted_id": f"claim-checker:{iid}:{(S.sha_hex(ref.get('sha256')) or 'nohash')[:12]}",
                "instrument_ids": [iid], "urls": [ref["url"]] if ref.get("url") else [],
                "citation": page if CITATION_LIKE.match(page) else "", "step": step,
                "requested_by": "claim-checker --fetch"}))
            res = ladder.walk(wanted) or {}
            atts = [{k: a.get(k) for k in ("tier", "route", "url", "accepted", "status", "reject_reason", "error")}
                    for a in res.get("attempts", []) if isinstance(a, dict)]
            return res.get("source"), atts

        return via_classes, f"{P['ladder']}: Ladder.walk"

    # 2. A plain function.
    for name in ("fetch_source", "fetch", "fetch_url", "ladder_fetch", "run_ladder", "fetch_one"):
        fn = getattr(mod, name, None)
        if callable(fn):
            def via_function(ref, iid, step, fn=fn):
                offered = {"url": ref.get("url"), "instrument_id": iid, "instrument_ids": [iid],
                           "cache_dir": str(cache_dir), "expected_sha256": ref.get("sha256"),
                           "sha256": ref.get("sha256"), "page_or_item": ref.get("page_or_item"),
                           "step": step, "route": "claim-checker --fetch"}
                kwargs = _kwargs_for(fn, offered)
                result = fn(**kwargs) if kwargs else fn(ref.get("url"))
                if isinstance(result, list):
                    result = next((r for r in result if isinstance(r, dict) and r.get("sha256")), None)
                if isinstance(result, dict) and isinstance(result.get("source"), dict):
                    result = result["source"]
                return (result if isinstance(result, dict) else None), []

            return via_function, f"{P['ladder']}:{name}"
    return None, f"{P['ladder']} has no fetch entry point this checker recognises"


def run_fetch(ctx, pending, out):
    fn, how = load_ladder(ctx.repo, ctx.cache_dir / "fetch")
    attempts = []
    if fn is None:
        print(f"--fetch: {how}; nothing fetched.")
        attempts.append({"result": "ladder_unavailable", "detail": how})
    else:
        seen = set()
        for claim_key, iid, field, ref in pending:
            u = S.norm_url(ref.get("url"))
            if not u or u in seen:
                continue
            seen.add(u)
            rec = {"claim_key": claim_key, "instrument_id": iid, "field": field, "url": ref.get("url"),
                   "claimed_sha256": ref.get("sha256"), "ladder": how}
            try:
                got, atts = fn(ref, iid, step_for_path(field))
                got_sha = S.sha_hex((got or {}).get("sha256"))
                rec["result"] = ("fetched_and_matches_claim" if got_sha and got_sha == S.sha_hex(ref.get("sha256"))
                                 else "fetched_different_bytes" if got_sha else "not_retrieved")
                rec["source_record"] = got
                rec["ladder_attempts"] = atts[:40]
            except Exception as exc:  # noqa: BLE001 - one failure must not stop the run
                rec["result"] = "error"
                rec["detail"] = f"{type(exc).__name__}: {exc}"[:300]
            attempts.append(rec)
            print(f"  fetch {rec['url']}: {rec['result']}")
    with open(out / "FETCH_ATTEMPTS.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for a in attempts:
            fh.write(json.dumps(a, ensure_ascii=False, sort_keys=True, default=str) + "\n")
    return attempts


# -------------------------------------------------------------------- main

def _csv_text(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_FIELDS, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def select_csv_rows(all_rows, max_bytes, include_passes=False):
    """Rows for CLAIM_CHECKS.csv, kept under max_bytes so the runner can commit it.
    By default passing rows are left out (their counts are in PER_CLAIM.json check_counts)."""
    def size(rows):
        return len(_csv_text(rows).encode("utf-8"))

    stages = []
    if include_passes:
        stages.append(("all_rows", all_rows))
    non_pass = [r for r in all_rows if r["result"] != "pass"]
    stages.append(("non_pass_rows", non_pass))
    stages.append(("non_pass_rows_of_effective_claims", [r for r in non_pass if r["effective_for_tracker"] == "yes"]))
    stages.append(("fail_rows_of_effective_claims", [r for r in non_pass
                                                     if r["effective_for_tracker"] == "yes" and r["result"] == "fail"]))
    for mode, rows in stages:
        if size(rows) <= max_bytes:
            return mode, rows
    mode, rows = stages[-1]
    kept, total = [], len(_csv_text([]).encode("utf-8"))
    for r in rows:
        n = len(_csv_text([r]).encode("utf-8")) - len(_csv_text([]).encode("utf-8"))
        if total + n > max_bytes:
            break
        kept.append(r)
        total += n
    return mode + "_truncated", kept


def write_outputs(out, csv_rows, per_claim, summary):
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "CLAIM_CHECKS.csv", "w", encoding="utf-8", newline="") as fh:
        fh.write(_csv_text(csv_rows))
    by_instrument = {}
    for c in per_claim:
        if c.get("effective_for_tracker"):
            by_instrument[c["instrument_id"]] = {
                "claim_key": c["claim_key"], "claim_sha256": c["claim_sha256"],
                "mechanical_result": c["mechanical_result"], "gate_passed": c["gate_passed"],
                "all_checks_passed": c["all_checks_passed"],
                "steps_checker_passed": {s: c["steps"][s]["checker_passed"] for s in STEPS},
            }
    doc = {"schema": SCHEMA, "legal_cutoff": LEGAL_CUTOFF,
           "note": "Mechanical checks only. Passing is not a legal conclusion and changes no status or count.",
           "by_instrument": dict(sorted(by_instrument.items())), "claims": per_claim}
    (out / "PER_CLAIM.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=False) + "\n", "utf-8")
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", "utf-8")


def write_report(out, per_claim, summary):
    lines = ["# Claim checker report", "",
             "Mechanical checks of every claim in `research/readiness/claims/`. A pass means the",
             "sources are held, the quotations are word for word, the dates and order numbers are",
             "possible, and the Stage 19 gate's structure is met. **It is not a legal conclusion.**", "",
             f"- Claims checked: {summary['claims_checked']} (parse errors: {summary['claims_parse_errors']})",
             f"- Orders with a claim (latest claim per order): {summary['orders_with_claim']}",
             f"- All checks passed: {summary['claims_all_checks_passed']}",
             f"- Mechanical checks passed: {summary['claims_mechanical_pass']}; with unverifiable items: "
             f"{summary['claims_mechanical_unverified']}; failed: {summary['claims_mechanical_fail']}",
             f"- Structural gate passed: {summary['claims_gate_passed']}", "",
             "## Source references", ""]
    for k, v in summary["source_status_counts"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Quotations", ""]
    for k, v in summary["quote_status_counts"].items():
        lines.append(f"- {k}: {v}")
    bad = [c for c in per_claim if not c.get("all_checks_passed")]
    if bad:
        lines += ["", "## Claims with problems (first 100)", "", "| claim | order | problems |", "|---|---|---|"]
        for c in bad[:100]:
            probs = c.get("failures") or c.get("gate_errors") or ["unverifiable items"]
            lines.append(f"| `{c['claim_key']}` | {c.get('instrument_id')} | {'; '.join(probs[:6])}"
                         f"{' ...' if len(probs) > 6 else ''} |")
    lines += ["", "## Source identity (is the cited original this order's?)", ""]
    for k, v in summary["source_identity_counts"].items():
        lines.append(f"- {k}: {v}")
    if summary.get("claims_checker_errors"):
        lines += ["", f"**{summary['claims_checker_errors']} claim(s) could not be fully checked** (checker_error "
                      "below); fix those claim lines."]
    lines += ["", "Details: `CLAIM_CHECKS.csv` (one row per check that did not pass; mode "
                  f"`{summary['claim_checks_csv']['mode']}`). Per claim: `PER_CLAIM.json`.", ""]
    (out / "REPORT.md").write_text("\n".join(lines), "utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mechanical checks of research/readiness claims.")
    ap.add_argument("--fetch", action="store_true",
                    help="try to download not-held sources through jobs/source-ladder (off by default)")
    ap.add_argument("--claims", default=os.environ.get("CLAIM_CHECKER_CLAIMS"),
                    help="glob of claim files (default research/readiness/claims/*.jsonl)")
    args = ap.parse_args(argv)

    t0 = time.time()
    repo = pathlib.Path(os.environ.get("REPO_ROOT", ".")).resolve()
    out = pathlib.Path(os.environ.get("OUTPUT_DIR") or (HERE / "output")).resolve()
    cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / f"{JOB_NAME}-cache")).resolve()
    limit_raw = os.environ.get("JOB_LIMIT", "").strip()
    try:
        limit = int(limit_raw) if limit_raw else None
    except ValueError:
        print(f"  note: JOB_LIMIT={limit_raw!r} is not a whole number; checking every claim")
        limit = None
    try:
        csv_max_mb = float(os.environ.get("CLAIM_CHECKER_CSV_MAX_MB") or CSV_MAX_MB_DEFAULT)
    except ValueError:
        csv_max_mb = CSV_MAX_MB_DEFAULT
    csv_all = os.environ.get("CLAIM_CHECKER_CSV_ALL_ROWS", "").strip() in ("1", "yes", "true")
    pattern = args.claims or str(repo / P["claims"])
    paths = sorted(glob.glob(pattern), key=lambda p: (pathlib.Path(p).name, p))

    print(f"Loading inputs from {repo} ...")
    ctx = Context(repo, HERE, cache)
    print(f"  universe: {len(ctx.universe)} orders; provisional statuses: {len(ctx.statuses)}")
    print(f"  held source copies indexed: {sum(ctx.index.origin_counts.values())} "
          f"({', '.join(f'{k} {v}' for k, v in sorted(ctx.index.origin_counts.items()))})")
    for n in ctx.index.notes:
        print(f"  {n}")
    for k in sorted(ctx.signing_counts):
        if k.startswith("unreadable:"):
            print(f"  note: skipped {k[len('unreadable:'):]}")
    print(f"  pypdf: {ctx.pypdf or 'NOT installed (PDF quotations cannot be checked)'}")

    claims = read_claims(paths, repo)
    total_lines = len(claims)
    if limit is not None:
        claims = claims[:limit]
    last_for = {}
    for key, _, _, claim, _ in claims:
        if claim is not None and isinstance(claim.get("instrument_id"), str):
            last_for[claim["instrument_id"]] = key
    all_rows, per_claim, pending = [], [], []
    checker_errors = 0
    for key, file_rel, line, claim, err in claims:
        if claim is None:
            all_rows.append({"claim_key": key, "instrument_id": "", "effective_for_tracker": "no",
                             "step": "claim_record", "check": "parse", "field": "", "result": "fail",
                             "status": "not_json_object", "detail": err})
            per_claim.append({"claim_key": key, "file": file_rel, "line": line, "parse_error": err,
                              "all_checks_passed": False, "mechanical_result": "fail", "gate_passed": False,
                              "failures": ["parse:not_json_object"]})
            print(f"  could not read claim {key}: {err}")
            continue
        ctx.not_held = []
        effective = last_for.get(claim.get("instrument_id")) == key
        try:
            rows, errors, status = check_claim(claim, ctx)
            summary = summarise_claim(key, file_rel, line, claim, rows, errors, status, ctx)
        except Exception as exc:  # noqa: BLE001 - one bad claim must not stop the run
            checker_errors += 1
            print(f"  CHECKER ERROR on claim {key}: {type(exc).__name__}: {exc} (reported; run continues)")
            rows = [{"step": "claim_record", "check": "checker_error", "field": "", "result": "fail",
                     "status": type(exc).__name__,
                     "detail": f"the checker failed on this claim: {type(exc).__name__}: {exc}"[:600]}]
            summary = error_summary(key, file_rel, line, claim, exc, ctx)
            ctx.not_held = []
        summary["effective_for_tracker"] = effective
        per_claim.append(summary)
        iid = claim.get("instrument_id")
        for r in rows:
            all_rows.append({"claim_key": key, "instrument_id": iid if isinstance(iid, str) else json.dumps(iid),
                             "effective_for_tracker": "yes" if effective else "no", **r})
        pending += [(key, iid, f, r) for f, r in ctx.not_held]

    out.mkdir(parents=True, exist_ok=True)
    attempts = run_fetch(ctx, pending, out) if args.fetch else None

    csv_mode, csv_rows = select_csv_rows(all_rows, int(csv_max_mb * 1_000_000), include_passes=csv_all)
    if csv_mode not in ("all_rows", "non_pass_rows"):
        print(f"  NOTE: CLAIM_CHECKS.csv would exceed {csv_max_mb:g} MB; wrote {csv_mode} ({len(csv_rows)} rows)")
    checked = [c for c in per_claim if "parse_error" not in c]
    src = collections.Counter(r["status"] for r in all_rows if r["check"] == "source_held")
    quo = collections.Counter(r["status"] for r in all_rows if r["check"] == "quote_verbatim")
    ident = collections.Counter(r["status"] for r in all_rows if r["check"] == "source_identity")
    summary = {
        "schema": SCHEMA, "job": JOB_NAME, "legal_cutoff": LEGAL_CUTOFF,
        "claim_files": [pathlib.Path(p).name for p in paths],
        "claim_lines_found": total_lines, "job_limit": limit,
        "claims_checked": len(checked), "claims_parse_errors": len(per_claim) - len(checked),
        "claims_checker_errors": checker_errors,
        "orders_with_claim": len({c["instrument_id"] for c in checked if c.get("effective_for_tracker")}),
        "claims_all_checks_passed": sum(c["all_checks_passed"] for c in checked),
        "claims_mechanical_pass": sum(c["mechanical_result"] == "pass" for c in checked),
        "claims_mechanical_unverified": sum(c["mechanical_result"] == "pass_with_unverified" for c in checked),
        "claims_mechanical_fail": sum(c["mechanical_result"] == "fail" for c in checked),
        "claims_gate_passed": sum(c["gate_passed"] for c in checked),
        "steps_checker_passed_effective_claims": {
            s: sum(c["steps"][s]["checker_passed"] for c in checked if c.get("effective_for_tracker")) for s in STEPS},
        "check_results": {c: dict(sorted(collections.Counter(r["result"] for r in all_rows if r["check"] == c).items()))
                          for c in MECHANICAL_CHECKS + ["structural_gate", "parse", "checker_error"]},
        "source_status_counts": dict(sorted(src.items())),
        "source_identity_counts": dict(sorted(ident.items())),
        "quote_status_counts": dict(sorted(quo.items())),
        "source_status_policy": SOURCE_STATUS_RESULT,
        "claim_checks_csv": {"mode": csv_mode, "rows_written": len(csv_rows), "rows_total": len(all_rows),
                             "max_mb": csv_max_mb,
                             "note": "passing rows are left out unless CLAIM_CHECKER_CSV_ALL_ROWS=1; "
                                     "per-check pass counts are in PER_CLAIM.json check_counts"},
        "held_copies_indexed_by_origin": dict(sorted(ctx.index.origin_counts.items())),
        "held_distinct_sha256": len(ctx.index.by_sha),
        "opus_text_pack_texts": len(ctx.index.packed_texts),
        "signing_dates_loaded": dict(sorted(ctx.signing_counts.items())),
        "gate_error_step_mapping_from": ctx.step_mapping_from,
        "pypdf_available": bool(ctx.pypdf),
        "fetch": None if attempts is None else dict(collections.Counter(a.get("result") for a in attempts)),
        "establishes": "nothing legal: mechanical custody, identity, quotation, date, order-number and structure checks only",
    }
    write_outputs(out, csv_rows, per_claim, summary)
    write_report(out, per_claim, summary)

    print("")
    print(f"Checked {summary['claims_checked']} claim(s) from {len(paths)} file(s)"
          f"{f' (limited to {limit} of {total_lines} lines)' if limit is not None and total_lines > limit else ''}.")
    if not paths:
        print("  No claim files yet in research/readiness/claims/ - nothing to check.")
    print(f"  All checks passed: {summary['claims_all_checks_passed']}; mechanical fail: "
          f"{summary['claims_mechanical_fail']}; gate passed: {summary['claims_gate_passed']}")
    print(f"  Source references: {summary['source_status_counts'] or 'none'}")
    print(f"  Source identity: {summary['source_identity_counts'] or 'none'}")
    print(f"  Quotations: {summary['quote_status_counts'] or 'none'}")
    if checker_errors:
        print(f"  Checker errors: {checker_errors} claim(s) could not be fully checked; see REPORT.md")
    if attempts is not None:
        print(f"  Fetch attempts: {summary['fetch']}")
    print(f"  Outputs in {out} ({time.time() - t0:.1f}s). These are mechanical checks, not legal findings.")
    return summary


if __name__ == "__main__":
    main()
