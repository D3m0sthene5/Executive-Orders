"""Formulario: a checked library of small, citable lifecycle statements ("lemmas") about executive orders.

Named for Giuseppe Peano's *Formulario mathematico* (1895-1908), the first attempt to state every known theorem
in one formal notation, each with its source: the ancestor of Lean's mathlib.

The analogy, and where it stops:

- A dossier is a theorem about one order. Its lifecycle facts are lemmas; the documents they rest on are axioms.
- A lemma here is one atomic statement ("Proclamation 2714 terminates <class>", "EO 7234 revokes EO 2040") with
  a proof term: the source (URL, SHA-256 of bytes the repository keeps, text path and its SHA-256) and the exact
  character span of the words that state it.
- The kernel is deliberately small and mechanical. A lemma is `proved` only when its quoted words are found, by a
  normalisation-tolerant exact match, in the text of bytes this repository retains. Anything else stays `sorry`
  (Lean's placeholder for an unproved step) with the reason. A `proved` lemma is a checked quotation, NOT a legal
  finding, an identity authentication, a readiness step or a human certification (certified count: 0).
- General theorems: a class lemma names a class of orders in the document's own words (e.g. every order resting
  on a terminated emergency). Applying it to a given order is legal judgment; `exact` lists it beside the order's
  family as a candidate, never as proved for that order.
- Imports, not copies: lemmas are sharded by order number and loaded one shard at a time, and `supplement` prints
  a ready-made claim-kit source-excerpt declaration (`source_supplement.py`), so a producer cites one span instead
  of reading whole documents. Retained source bytes are listed in `output/SOURCES.jsonl`, the shared format the
  claim checker already reads, so they are checkable with no code change.

    python3 -I formulario.py build [REPO_ROOT] [OUTPUT_DIR]       (the job; zero model tokens)
    python3 -I formulario.py exact EO:2040 [--goal end|basis|any] [--json]
    python3 -I formulario.py supplement F-1a2b3c4d5e6f [...]
"""
import argparse
import collections
import csv
import glob
import gzip
import hashlib
import html.parser
import io
import json
import os
import re
import sys
import tempfile

csv.field_size_limit(min(2 ** 31 - 1, 10 ** 9))
HERE = os.path.dirname(os.path.abspath(__file__))
BAND = 500
END_RELATIONS = {"terminates", "revokes", "supersedes", "abolishes_agency", "transfers_functions", "repeals_authority",
                 "holds_invalid", "holds_expired", "revocation", "supersession", "termination", "abolition",
                 "rescission", "authority_repeal", "nullification", "records_disposition"}
BASIS_RELATIONS = {"declares_in_force", "continues", "continuation", "extension"}
# Non-terminal relations: an opinion that construes an act ("interprets"), a statement of what a finding aid records
# ("describes_source"), and anything else ("other"). They never answer an end or basis goal by themselves.
# later-events mechanism -> Formulario relation
MECHANISM = {"revocation": "revokes", "supersession": "supersedes", "termination": "terminates",
             "abolition": "abolishes_agency", "rescission": "revokes", "authority_repeal": "repeals_authority",
             "nullification": "holds_invalid", "amendment": "amends", "modification": "amends",
             "continuation": "continues", "extension": "continues", "cross_reference": "cites"}
# sha256 -> text resolvers: the shared source records of the jobs whose retained texts later-events quotes.
TEXT_INDEXES = ["jobs/fr-originals/output/SOURCES.jsonl", "jobs/app-executive-orders/output/SOURCES.jsonl",
                "jobs/app-transcriptions/output/SOURCES.jsonl", "jobs/opus-media-match/output/SOURCES.jsonl",
                "jobs/wikisource-texts/output/SOURCES.jsonl", "jobs/later-events/output/SOURCES.jsonl"]
LATER_EDGES = "jobs/later-events/output/EDGES.csv"
TYPES = "jobs/x1-class-engine/output/TYPES.csv"
DOCTRINES = "research/pothier/doctrines/*.json"
NOT_A_FINDING = ("A proved lemma is a checked quotation from bytes this repository keeps: not a legal finding, "
                 "identity authentication, readiness step or human certification (certified count: 0).")


# ---------------------------------------------------------------- the kernel: normalisation-tolerant exact match
_TRANS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-",
                        " ": " ", "­": None, "ﬁ": "fi", "ﬂ": "fl"})


def _normalise(text, alnum):
    """Return (normalised string, list mapping each normalised char to its index in `text`)."""
    out, pos = [], []
    prev_space = True
    i, n = 0, len(text)
    while i < n:
        ch = text[i].translate(_TRANS) if text[i] in "‘’“”–— ­ﬁﬂ" else text[i]
        if ch == "-" and i + 1 < n and text[i + 1] == "\n":  # word broken across a line: join it
            i += 2
            continue
        for c in ch:
            c = c.casefold()
            if alnum:
                if c.isalnum():
                    out.append(c)
                    pos.append(i)
            elif c.isspace():
                if not prev_space:
                    out.append(" ")
                    pos.append(i)
                prev_space = True
            else:
                out.append(c)
                pos.append(i)
                prev_space = False
        i += 1
    return "".join(out).strip(), pos


_NORM_CACHE = collections.OrderedDict()


def _normalised_text(text, alnum):
    key = (hashlib.sha1(text.encode("utf-8", "surrogatepass")).hexdigest(), alnum)
    hit = _NORM_CACHE.get(key)
    if hit is None:
        hit = _normalise(text, alnum)
        _NORM_CACHE[key] = hit
        if len(_NORM_CACHE) > 256:
            _NORM_CACHE.popitem(last=False)
    else:
        _NORM_CACHE.move_to_end(key)
    return hit


def locate(quote, text):
    """(char_start, char_end, tier) of `quote` in `text`, or None. Tier 'spaced' tolerates case, quote marks, dashes
    and whitespace; tier 'alnum' compares letters and digits only (OCR spacing, punctuation)."""
    if not quote or not text:
        return None
    for tier in ("spaced", "alnum"):
        q, _ = _normalise(quote, tier == "alnum")
        if len(q) < 12:
            return None
        t, pos = _normalised_text(text, tier == "alnum")
        k = t.find(q)
        if k >= 0:
            return pos[k], pos[k + len(q) - 1] + 1, tier
    return None


# ---------------------------------------------------------------- text from retained bytes
class _HTMLText(html.parser.HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "td", "pre"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def kind_of(raw):
    if raw[:5] == b"%PDF-":
        return "pdf"
    head = raw[:2048].lstrip().lower()
    if head[:1] in (b"{", b"["):
        return "json"
    if b"<html" in head or b"<!doctype html" in head or b"<body" in head or b"<div" in head:
        return "html"
    return "txt"


def text_of(raw):
    """Plain text of retained bytes. PDF text layer via pypdf (no OCR); HTML without markup; JSON as-is except the
    Federal Register API's executive-order pages, rendered one record per line."""
    k = kind_of(raw)
    if k == "pdf":
        try:
            import pypdf
        except ImportError:
            return "", "pypdf not installed"
        try:
            reader = pypdf.PdfReader(io.BytesIO(raw))
            return "\n".join((p.extract_text() or "") for p in reader.pages[:600]), ""
        except Exception as exc:  # noqa: BLE001
            return "", f"pdf: {type(exc).__name__}"
    s = raw.decode("utf-8", errors="replace")
    if k == "html":
        p = _HTMLText()
        p.feed(s)
        return re.sub(r"\n\s*\n+", "\n\n", "".join(p.parts)), ""
    if k == "json":
        try:
            d = json.loads(s)
        except json.JSONDecodeError:
            return s, ""
        if isinstance(d, dict) and isinstance(d.get("results"), list):
            lines = []
            for r in d["results"]:
                if isinstance(r, dict) and r.get("executive_order_number") is not None:
                    lines.append(f"EO {r.get('executive_order_number')} ({r.get('citation') or ''}; signed "
                                 f"{r.get('signing_date') or ''}): {r.get('disposition_notes') or ''}")
            return "\n".join(lines), ""
        return s, ""
    return s, ""


# ---------------------------------------------------------------- repository access
class Repo:
    def __init__(self, root):
        self.root = root
        try:
            import subprocess
            out = subprocess.run(["git", "-C", root, "ls-tree", "-r", "--name-only", "-z", "HEAD"],
                                 capture_output=True, check=True).stdout
            self.tree = {p.decode("utf-8") for p in out.split(b"\0") if p}
        except Exception:  # noqa: BLE001  (a fixture directory, not a repository)
            self.tree = {os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/")
                         for d, _, fs in os.walk(root) for f in fs}

    def path(self, rel):
        return os.path.join(self.root, rel)

    def read(self, rel, binary=False):
        full = self.path(rel)
        if os.path.isfile(full):
            with open(full, "rb") as fh:
                b = fh.read()
            return b if binary else b.decode("utf-8", errors="replace")
        if rel in self.tree:
            import subprocess
            r = subprocess.run(["git", "-C", self.root, "show", f"HEAD:{rel}"], capture_output=True)
            if r.returncode == 0:
                return r.stdout if binary else r.stdout.decode("utf-8", errors="replace")
        return None

    def jsonl(self, rel):
        out = []
        for line in (self.read(rel) or "").splitlines():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return out


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def band_of(eo_id):
    m = re.match(r"EO:(\d+)", eo_id or "")
    return f"{int(m.group(1)) // BAND * BAND:05d}" if m else "other"


def eo_id(label):
    """'EO 1234A' / 'Executive Order No. 1234' / 'EO:1234' -> 'EO:1234A' (letters kept), else ''."""
    m = re.search(r"(?:EO|E\.O\.|Executive Order(?: No\.)?)[\s:]*(\d+)([A-Z]?|-\d+|½)?\b", label or "", re.I)
    return f"EO:{m.group(1)}{(m.group(2) or '').upper()}" if m else ""


def lemma_id(statement, proof_key):
    return "F-" + sha256(json.dumps([statement, proof_key], sort_keys=True).encode())[:12]


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s or "").strip("_")[:60]


def names_number(quote, instrument):
    """True if `quote` names the instrument by its number(s): every digit group of 3+ digits in its id or label
    (EO:7234, PLO:936, PL:95-495, '51 FR 2353') appears as a whole number, or, if it has none, any group does.
    OCR-spaced digits are joined first. An instrument with no number at all cannot be bound."""
    groups = re.findall(r"\d+", instrument or "")
    if not groups:
        return False
    qs = (quote or "", re.sub(r"(?<=\d)[\s,]+(?=\d)", "", quote or ""))
    hit = lambda g: any(re.search(rf"(?<!\d){g.lstrip('0') or '0'}(?!\d)", q) for q in qs)  # noqa: E731
    long_groups = [g for g in groups if len(g) >= 3]
    return all(hit(g) for g in long_groups) if long_groups else any(hit(g) for g in groups)


def record_span(src, number):
    """(start, end) of the Federal Register API record line for EO `number` in a retained API page's text."""
    lines = src.get("_lines")
    if lines is None:
        lines = {}
        starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^EO (\d+[A-Za-z]?) \(", src["_text"])]
        for k, (pos, num) in enumerate(starts):  # a record runs to the next record (notes span lines)
            end = starts[k + 1][0] if k + 1 < len(starts) else len(src["_text"])
            lines.setdefault(num, (pos, end))
        src["_lines"] = lines
    return lines.get(str(number))


# ---------------------------------------------------------------- build
class Library:
    def __init__(self, repo, out, prior, pool=None):
        self.repo, self.out, self.prior, self.pool = repo, out, prior, pool
        self.lemmas, self.sources, self.sorry = [], {}, collections.Counter()
        os.makedirs(os.path.join(out, "raw"), exist_ok=True)
        os.makedirs(os.path.join(out, "texts"), exist_ok=True)
        self.prior_by_url = {}
        for r in Repo(prior).jsonl("SOURCES.jsonl") if prior and os.path.isdir(prior) else []:
            if r.get("url") and (r.get("cache_path") or r.get("text_path")):
                self.prior_by_url[r["url"]] = r
        self.retain_max = int(float(os.environ.get("FORMULARIO_RETAIN_MAX_MB", "3")) * 1024 * 1024)

    # A document: carried forward from the prior generation, else fetched. Bytes up to FORMULARIO_RETAIN_MAX_MB (3) are
    # committed; a larger official file keeps only its text and byte hash and is re-fetched on later runs to
    # re-verify (custody "bytes_refetchable"), so the repository does not grow by whole court reports.
    def retain(self, url, budget):
        if url in self.sources:
            return self.sources[url]
        raw, prior_text = None, None
        p = self.prior_by_url.get(url)
        if p and p.get("cache_path"):
            path = os.path.join(self.prior, p["cache_path"])
            if os.path.isfile(path):
                with open(path, "rb") as fh:
                    raw = fh.read()
                if sha256(raw) != p["sha256"]:
                    raw = None
        error = ""
        if raw is None and self.pool is not None and budget["fetches"] > 0 and budget["bytes"] > 0:
            budget["fetches"] -= 1
            try:
                got = self.pool.fetch(url)
                raw = got["body"]
                budget["bytes"] -= len(raw)
            except Exception as exc:  # noqa: BLE001  (every failure is a recorded sorry)
                error = f"fetch_failed: {type(exc).__name__}: {str(exc)[:120]}"
        if raw is None and p and not p.get("cache_path") and p.get("text_path"):
            tpath = os.path.join(self.prior, p["text_path"])
            if os.path.isfile(tpath):
                with open(tpath, "rb") as fh:
                    tb = fh.read()
                if sha256(tb) == p.get("text_sha256"):
                    prior_text = tb.decode("utf-8")
        if raw is None and prior_text is None:
            self.sources[url] = {"error": error or ("not_fetched_this_run" if self.pool is not None else "offline")}
            return self.sources[url]
        if raw is not None:
            h, size, kind = sha256(raw), len(raw), kind_of(raw)
            text, terr = text_of(raw)
            verified = "this_run"
        else:  # a large file not re-fetched this run: its text, verified when its bytes were last read
            h, size, kind, text, terr = p["sha256"], p.get("bytes"), p.get("content_kind", ""), prior_text, ""
            verified = p.get("verified", "earlier_run")
        cache_rel = None
        if raw is not None and size <= self.retain_max:
            ext = {"pdf": "pdf", "html": "html", "json": "json"}.get(kind, "txt")
            cache_rel = f"raw/{h[:2]}/{h}.{ext}"
            os.makedirs(os.path.join(self.out, "raw", h[:2]), exist_ok=True)
            with open(os.path.join(self.out, cache_rel), "wb") as fh:
                fh.write(raw)
        text_rel = f"texts/{h[:2]}/{h}.txt"
        os.makedirs(os.path.join(self.out, "texts", h[:2]), exist_ok=True)
        tb = text.encode("utf-8")
        with open(os.path.join(self.out, text_rel), "wb") as fh:
            fh.write(tb)
        rec = {"url": url, "sha256": h, "bytes": size, "cache_path": cache_rel, "text_path": text_rel,
               "text_sha256": sha256(tb), "text_error": terr, "content_kind": kind,
               "custody": "bytes_retained" if cache_rel else "bytes_refetchable",
               "verified": verified if verified != "this_run" else os.environ.get("JOB_GENERATION_ID", "this_run"),
               "retrieved_from_prior": bool(p and p.get("sha256") == h), "_text": text}
        self.sources[url] = rec
        return rec

    def add(self, lemma):
        self.lemmas.append(lemma)
        if lemma["status"] == "sorry":
            self.sorry[lemma["sorry_reason"].split(":")[0]] += 1

    def prove(self, quote, src, rel_text, text, scope=None):
        off = 0
        if scope:
            off, text = scope[0], text[scope[0]:scope[1]]
        hit = locate(quote, text)
        if not hit:
            return None, "quote_not_found_in_retained_text"
        a, b, tier = hit
        a, b = a + off, b + off
        return {"quote": quote, "match_tier": tier, "char_start": a, "char_end": b, "source": src,
                "text_path": rel_text}, ""


def load_axioms(job_dir):
    out = []
    for path in sorted(glob.glob(os.path.join(job_dir, "axioms", "*.jsonl"))):
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                line = line.strip()
                if line and not line.startswith("#"):
                    a = json.loads(line)
                    a["_file"] = f"axioms/{os.path.basename(path)}:{n}"
                    out.append(a)
    return out


def build_axioms(lib, axioms, budget):
    for a in axioms:
        targets = sorted({eo_id(t) for t in a.get("targets_named") or [] if eo_id(t)})
        statement = {"subject": a["instrument"], "subject_kind": a.get("instrument_kind", ""),
                     "relation": a["relation"], "objects": targets, "class_scope": a.get("class_scope", ""),
                     "families": sorted(a.get("census_families_hint") or []), "date": a.get("date", "")}
        src = lib.retain(a["url"], budget)
        proof, reason = None, ""
        if "error" in src:
            reason = src["error"]
        else:
            proof, reason = lib.prove(a["quote"], {k: src[k] for k in ("url", "sha256", "text_sha256", "custody", "verified")},
                                      f"jobs/peano-formulario/output/{src['text_path']}", src["_text"])
            if src.get("text_error") and not proof:
                reason = f"no_text_layer: {src['text_error']}"
            if proof and targets:
                near = src["_text"][max(0, proof["char_start"] - 1500):proof["char_end"] + 1500]
                missing = [t for t in targets if not names_number(near, t)]
                if missing:
                    proof, reason = None, "targets_not_named_near_quote: " + "|".join(missing)
        kind = "class" if statement["class_scope"] or not targets else "instance"
        lib.add({
            "lemma_id": lemma_id(statement, a["url"]), "kind": kind,
            "name": f"{slug(a['instrument'])}.{a['relation']}" + (f".{slug(targets[0])}" if targets else ".class"),
            "statement": statement, "status": "proved" if proof else "sorry", "sorry_reason": "" if proof else reason,
            "proof": proof or {"quote": a["quote"], "source": {"url": a["url"]}},
            "grade": a.get("instrument_kind", ""), "page_or_item": a.get("page_or_item", ""),
            "origin": {"from": a["_file"], "axiom_id": a.get("axiom_id", ""), "found_by": a.get("found_by", ""),
                       "agent_verified_by_fetch": a.get("verified_by_fetch"), "notes": a.get("notes", "")},
        })


# ---------------------------------------------------------------- tactic: search for a provable copy (Lean's `exact?`)
OFFICIAL_HOSTS = ("govinfo.gov", "loc.gov", "archives.gov", "justice.gov", "supremecourt.gov", "uscode.house.gov",
                  "federalregister.gov", "gao.gov", "courtlistener.com", "archive.org", "hathitrust.org", "ecfr.gov",
                  "senate.gov", "house.gov", "congress.gov")
TACTIC_REASONS = ("fetch_failed", "quote_not_found_in_retained_text", "no_text_layer", "targets_not_named_near_quote")


def _official(url):
    import urllib.parse
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS)


def search_tactic(lib, root, out, budget, axioms, prior, env=None, searcher=None):
    """For axioms still `sorry` after their own URL, ask the shared web-search engines (jobs/_lib/eo_websearch.py:
    free engines first; a paid engine such as Brave's API only when the free ones found no official candidate, and
    only within the project's paid-query caps) for the quote's opening words, fetch official-host candidates through
    the same retained-copy path, and run the kernel again. Every attempt is logged in TACTICS.jsonl."""
    env = os.environ if env is None else env
    sys.path.insert(0, os.path.join(root, "jobs", "_lib"))
    import eo_websearch as W
    todo = [lm for lm in lib.lemmas if lm["status"] == "sorry" and lm["origin"]["from"].startswith("axioms/")
            and lm["sorry_reason"].split(":")[0] in TACTIC_REASONS]
    limit = int(env.get("FORMULARIO_TACTIC_LEMMAS", "40"))
    mine = 0
    try:
        with open(os.path.join(prior, W.PAID_LEDGER), encoding="utf-8") as fh:
            mine = int(json.load(fh).get("lifetime_paid_queries", 0))
    except (OSError, ValueError, TypeError):
        pass
    _, everyone = W.load_paid_ledgers(root, "peano-formulario")
    allowance = max(0, min(int(env.get("FORMULARIO_PAID_PER_RUN", "20")),
                           W._int_env(env, "EO_PAID_SEARCHES_PER_JOB", W.PAID_PER_JOB_DEFAULT) - mine,
                           W._int_env(env, "EO_PAID_SEARCHES_TOTAL", W.PAID_TOTAL_DEFAULT) - everyone - mine))
    if searcher is None:
        searcher = W.Searcher(env.get("JOB_CACHE_DIR") or tempfile.mkdtemp(prefix="formulario-search-"),
                              max_requests=int(env.get("FORMULARIO_TACTIC_REQUESTS", "160")), env=env,
                              paid_allowance=allowance)
    ready = searcher.ready_engines()
    free = [e for e in ready if not e.get("paid")]
    paid = [e for e in ready if e.get("paid")]
    by_axiom = {a.get("axiom_id"): a for a in axioms}
    log = []
    for lm in todo[:limit]:
        a = by_axiom.get(lm["origin"].get("axiom_id"))
        if not a:
            continue
        words = re.findall(r"[A-Za-z0-9']+", a["quote"])[:12]
        query = '"' + " ".join(words) + '"'
        proved = False
        for tier, engines in (("free", free), ("paid", paid)):
            if proved or not searcher.budget_left():
                break
            cands = []
            for e in engines:
                r = searcher.search(e, query)
                cands += [h["url"] for h in r.get("hits", []) if _official(h.get("url", "")) and h["url"] != a["url"]]
                log.append({"lemma_id": lm["lemma_id"], "tier": tier, "engine": e["name"], "query": query,
                            "status": r.get("status"), "error": r.get("error", ""), "official_hits": len(cands)})
                if cands:
                    break
            for url in list(dict.fromkeys(cands))[:3]:
                src = lib.retain(url, budget)
                if "error" in src:
                    continue
                proof, _ = lib.prove(a["quote"], {k: src[k] for k in ("url", "sha256", "text_sha256", "custody", "verified")},
                                     f"jobs/peano-formulario/output/{src['text_path']}", src["_text"])
                targets = lm["statement"]["objects"]
                if proof and targets:
                    near = src["_text"][max(0, proof["char_start"] - 1500):proof["char_end"] + 1500]
                    if any(not names_number(near, t) for t in targets):
                        proof = None
                if proof:
                    lib.sorry[lm["sorry_reason"].split(":")[0]] -= 1
                    proof["found_by_tactic"] = {"query": query, "tier": tier, "url": url}
                    lm.update(status="proved", sorry_reason="", proof=proof)
                    proved = True
                    break
    used = sum(searcher.paid_used.values())
    with open(os.path.join(out, "TACTICS.jsonl"), "w", encoding="utf-8") as fh:
        for r in log:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    with open(os.path.join(out, W.PAID_LEDGER), "w", encoding="utf-8") as fh:
        json.dump({"job": "peano-formulario", "this_run": dict(sorted(searcher.paid_used.items())),
                   "this_run_allowance": allowance, "lifetime_paid_queries": mine + used,
                   "engine_status": dict(sorted(searcher.engine_status.items())),
                   "rule": "Paid engines (Brave's API among them) are asked only after the free engines found no official "
                           "candidate for that lemma, within the shared caps of jobs/_lib/eo_websearch.py."},
                  fh, indent=1, sort_keys=True)
    return {"tried": min(len(todo), limit), "proved_by_tactic": sum(1 for lm in todo if lm["status"] == "proved"),
            "paid_used": used, "engines_ready": [e["name"] for e in ready]}


def text_resolver(repo):
    """sha256 of a source -> repository path of its retained text, from the shared source records."""
    m = {}
    for rel in TEXT_INDEXES:
        out_dir = os.path.dirname(rel)
        for r in repo.jsonl(rel):
            s, t = r.get("sha256"), r.get("text_path")
            if not (isinstance(s, str) and isinstance(t, str) and t):
                continue
            for cand in (os.path.normpath(os.path.join(out_dir, t)), os.path.normpath(t)):
                cand = cand.replace(os.sep, "/")
                if cand in repo.tree:
                    m.setdefault(s, cand)
                    break
    return m


def build_later_events(lib, repo, budget):
    """Each later-events edge becomes a lemma; the kernel proves it from a retained text (order-text edges) or from
    Formulario's own retained copy of the Federal Register API page (disposition-note edges)."""
    rows = list(csv.DictReader(io.StringIO(repo.read(LATER_EDGES) or "")))
    texts = text_resolver(repo)
    cache = {}
    for e in rows:
        target = e.get("target_id") or ""
        rel = MECHANISM.get(e.get("mechanism", ""), e.get("mechanism", "") or "other")
        statement = {"subject": e.get("acting_id") or e.get("acting_label") or "", "subject_kind": "instrument",
                     "relation": rel, "objects": [target] if target else [], "class_scope": "",
                     "families": [], "date": e.get("date_candidate", ""),
                     "qualifier": e.get("qualifier", ""), "target_label": e.get("target_label", "")}
        quote = e.get("quote", "")
        proof, reason = None, ""
        stated = e.get("stated_on", "")
        counterparty = target if stated == statement["subject"] else statement["subject"]
        if not target:
            reason = "target_not_identified_in_census"
        elif e.get("evidence_type", "").startswith("ofr_note"):
            src = lib.retain(e["source_url"], budget)
            m = re.match(r"EO:(\d+[A-Za-z]?)", stated)
            span = record_span(src, m.group(1)) if "error" not in src and m else None
            if "error" in src:
                reason = "source_bytes_not_retained: " + src["error"]
            elif not span:
                reason = f"record_for_{stated}_not_in_retained_page"
            else:
                proof, reason = lib.prove(quote, {k: src[k] for k in ("url", "sha256", "text_sha256", "custody", "verified")},
                                          f"jobs/peano-formulario/output/{src['text_path']}", src["_text"], span)
                if reason:
                    reason = "quote_not_in_record_in_current_snapshot (the API's notes may have changed since later-events read them)"
        else:
            tp = texts.get(e.get("source_sha256", ""))
            if not tp:
                reason = "source_text_not_retained"
            else:
                if tp not in cache:
                    cache[tp] = repo.read(tp) or ""
                    if len(cache) > 400:
                        cache.pop(next(iter(cache)))
                proof, reason = lib.prove(quote, {"url": e.get("source_url", ""), "sha256": e.get("source_sha256", ""),
                                                  "text_sha256": ""}, tp, cache[tp])
        if proof and not names_number(quote, counterparty):
            proof, reason = None, ("quote_does_not_name_counterparty" if re.search(r"\d", counterparty or "")
                                   else "counterparty_has_no_number_to_check")
        if proof:
            proof["binding"] = {"stated_on": stated, "counterparty_named": counterparty}
        if proof and not proof["source"].get("text_sha256"):
            proof["source"]["text_sha256"] = sha256((repo.read(proof["text_path"]) or "").encode("utf-8"))
        lib.add({
            "lemma_id": lemma_id(statement, e.get("edge_id", "")), "kind": "instance",
            "name": f"{slug(target)}.{rel}_by.{slug(statement['subject'])}",
            "statement": statement, "status": "proved" if proof else "sorry", "sorry_reason": "" if proof else reason,
            "proof": proof or {"quote": quote, "source": {"url": e.get("source_url", ""), "sha256": e.get("source_sha256", "")}},
            "grade": e.get("evidence_type", ""), "page_or_item": e.get("page_or_item", ""),
            "origin": {"from": "later-events", "edge_id": e.get("edge_id", ""), "date_basis": e.get("date_basis", ""),
                       "date_flags": e.get("date_flags", ""), "stated_on": e.get("stated_on", "")},
        })


def families(repo):
    """order -> Pothier families, from the doctrines' membership rules over x1-class-engine types."""
    types = {r["instrument_id"]: r for r in csv.DictReader(io.StringIO(repo.read(TYPES) or ""))}
    fam = collections.defaultdict(list)
    for path in sorted(p for p in repo.tree if re.fullmatch(DOCTRINES.replace("*", "[^/]+"), p)):
        d = json.loads(repo.read(path) or "{}")
        m = d.get("members") or {}
        field, values = m.get("field"), set(m.get("in") or [])
        if field != "x1_type" or not values:
            continue
        for i, r in types.items():
            if r.get("type") in values:
                fam[i].append(d.get("doctrine_id") or os.path.basename(path)[:-5])
    return {i: sorted(v) for i, v in fam.items()}


def write(lib, repo, out, fams):
    # Keep bytes only for documents that prove something; the rest are refetched (within budget) on a later run.
    used = {lm["proof"]["source"].get("url") for lm in lib.lemmas if lm["status"] == "proved"}
    for url, s in list(lib.sources.items()):
        if "error" not in s and url not in used:
            for rel in (s["cache_path"], s["text_path"]):
                if not rel:
                    continue
                try:
                    os.remove(os.path.join(out, rel))
                except OSError:
                    pass
            lib.sources[url] = {"error": "retained_but_proves_nothing (dropped to keep the library small)"}
    shards = collections.defaultdict(list)
    classes = []
    for lm in lib.lemmas:
        if lm["kind"] == "class":
            classes.append(lm)
        for b in sorted({band_of(o) for o in lm["statement"]["objects"]} or ({"other"} if lm["kind"] != "class" else set())):
            shards[b].append(lm)
    os.makedirs(os.path.join(out, "lemmas"), exist_ok=True)

    def gz(path, rows):
        with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as fh:
            for r in sorted(rows, key=lambda r: (r["statement"]["objects"][:1], r["status"] != "proved", r["lemma_id"])):
                fh.write((json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))

    for b, rows in shards.items():
        gz(os.path.join(out, "lemmas", f"EO_{b}.jsonl.gz"), rows)
    gz(os.path.join(out, "lemmas", "CLASS.jsonl.gz"), classes)
    with open(os.path.join(out, "FAMILIES.json"), "w", encoding="utf-8") as fh:
        json.dump(fams, fh, sort_keys=True, separators=(",", ":"))
    with open(os.path.join(out, "SOURCES.jsonl"), "w", encoding="utf-8") as fh:
        for url, s in sorted(lib.sources.items()):
            if "error" in s:
                continue
            named = sorted({o for lm in lib.lemmas if lm["status"] == "proved" and lm["proof"]["source"].get("url") == url
                            for o in lm["statement"]["objects"]})
            fh.write(json.dumps({"url": url, "sha256": s["sha256"], "bytes": s["bytes"], "cache_path": s["cache_path"],
                                 "text_path": s["text_path"], "text_sha256": s["text_sha256"],
                                 "custody": s["custody"], "verified": s["verified"],
                                 "instrument_ids": named, "route": "formulario/axiom_source",
                                 "page_or_item": "", "content_kind": s["content_kind"],
                                 "acceptable_as_original": False,
                                 "notes": "Retained by Formulario so its lemmas' quotations can be checked. " + NOT_A_FINDING},
                                sort_keys=True) + "\n")
    C = collections.Counter
    idx = {
        "schema": "formulario-index/v1", "band": BAND, "what_this_is_not": NOT_A_FINDING,
        "lemmas": len(lib.lemmas), "by_status": dict(C(lm["status"] for lm in lib.lemmas)),
        "by_kind_status": dict(C(f"{lm['kind']}:{lm['status']}" for lm in lib.lemmas)),
        "by_relation": dict(C(lm["statement"]["relation"] for lm in lib.lemmas).most_common()),
        "by_origin_status": dict(C(f"{lm['origin']['from'].split(':')[0]}:{lm['status']}" for lm in lib.lemmas)),
        "sorry_reasons": dict(lib.sorry.most_common()),
        "orders_with_proved_end_lemma": len({o for lm in lib.lemmas if lm["status"] == "proved"
                                             and lm["statement"]["relation"] in END_RELATIONS
                                             for o in lm["statement"]["objects"]}),
        "class_lemmas": {"proved": sum(1 for c in classes if c["status"] == "proved"), "sorry": sum(1 for c in classes if c["status"] == "sorry")},
        "shards": {b: len(v) for b, v in sorted(shards.items())},
        "retained_sources": sum(1 for s in lib.sources.values() if "error" not in s),
        "retained_bytes": sum(s["bytes"] for s in lib.sources.values() if "error" not in s and s["cache_path"]),
        "refetchable_sources": sum(1 for s in lib.sources.values() if "error" not in s and not s["cache_path"]),
        "orders_with_family": len(fams),
    }
    with open(os.path.join(out, "INDEX.json"), "w", encoding="utf-8") as fh:
        json.dump(idx, fh, indent=1, sort_keys=True)
    with open(os.path.join(out, "SORRY.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["lemma_id", "kind", "subject", "relation", "objects", "reason", "url", "origin"])
        for lm in lib.lemmas:
            if lm["status"] == "sorry" and not lm["origin"]["from"].startswith("later-events"):
                w.writerow([lm["lemma_id"], lm["kind"], lm["statement"]["subject"], lm["statement"]["relation"],
                            "|".join(lm["statement"]["objects"]), lm["sorry_reason"], lm["proof"]["source"].get("url", ""),
                            lm["origin"]["from"]])
    return idx


def build(root, out, prior=None, pool=None, budget=None):
    repo = Repo(root)
    lib = Library(repo, out, prior, pool)
    budget = budget or {"fetches": int(os.environ.get("FORMULARIO_MAX_FETCHES", "400")),
                        "bytes": int(os.environ.get("FORMULARIO_MAX_MB", "600")) * 1024 * 1024}
    axioms = load_axioms(HERE)
    build_axioms(lib, axioms, budget)
    tactic = {"skipped": "offline"}
    if pool is not None and os.environ.get("FORMULARIO_TACTIC", "1") == "1":
        tactic = search_tactic(lib, root, out, budget, axioms, prior or out)
    build_later_events(lib, repo, budget)
    idx = write(lib, repo, out, families(repo))
    idx["tactic"] = tactic
    with open(os.path.join(out, "INDEX.json"), "w", encoding="utf-8") as fh:
        json.dump(idx, fh, indent=1, sort_keys=True)
    print(json.dumps({k: idx[k] for k in ("lemmas", "by_status", "by_kind_status", "sorry_reasons",
                                          "orders_with_proved_end_lemma", "retained_sources", "tactic")}, indent=1))
    return idx


# ---------------------------------------------------------------- queries (load one shard, never the library)
def _out_dir():
    return os.environ.get("FORMULARIO_OUTPUT", os.path.join(HERE, "output"))


def _shard(path):
    if not os.path.exists(path):
        return []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(l) for l in fh]


def exact(order, goal="any", out=None):
    """Lemmas that bear on `order`'s goal: instances naming it, then class lemmas for its families (candidates)."""
    out = out or _out_dir()
    want = END_RELATIONS if goal == "end" else BASIS_RELATIONS if goal == "basis" else None
    inst = [lm for lm in _shard(os.path.join(out, "lemmas", f"EO_{band_of(order)}.jsonl.gz"))
            if order in lm["statement"]["objects"] and (want is None or lm["statement"]["relation"] in want)]
    fams = []
    fpath = os.path.join(out, "FAMILIES.json")
    if os.path.exists(fpath):
        with open(fpath, encoding="utf-8") as fh:
            fams = json.load(fh).get(order, [])
    cls = [lm for lm in _shard(os.path.join(out, "lemmas", "CLASS.jsonl.gz"))
           if set(lm["statement"]["families"]) & set(fams) and (want is None or lm["statement"]["relation"] in want)]
    key = lambda lm: (lm["status"] != "proved", lm["statement"].get("date") or "9999")  # noqa: E731
    return {"order": order, "goal": goal, "families": fams, "instances": sorted(inst, key=key),
            "class_candidates": sorted(cls, key=key),
            "note": "Class candidates are general statements in the document's own words; whether one reaches this "
                    "order is legal judgment, not proved here. " + NOT_A_FINDING}


def supplement(ids, out=None):
    """claim-kit source-excerpt declaration entries for proved lemmas (jobs/claim-kit/source_supplement.py)."""
    out = out or _out_dir()
    want, entries = set(ids), []
    for path in sorted(glob.glob(os.path.join(out, "lemmas", "*.jsonl.gz"))):
        for lm in _shard(path):
            if lm["lemma_id"] in want and lm["status"] == "proved":
                want.discard(lm["lemma_id"])
                p = lm["proof"]
                entries.append({"instrument_ids": lm["statement"]["objects"], "reason": f"Formulario {lm['lemma_id']}: "
                                f"{lm['statement']['subject']} {lm['statement']['relation']}",
                                "source": {"url": p["source"].get("url", ""), "sha256": p["source"].get("sha256", ""),
                                           "text_path": p["text_path"], "text_sha256": p["source"].get("text_sha256", ""),
                                           "page_or_item": lm.get("page_or_item", "")},
                                "char_start": p["char_start"], "char_end": p["char_end"]})
    return {"entries": entries, "not_found_or_sorry": sorted(want),
            "note": "Add alias and actor_id, then declare with jobs/claim-kit/source_supplement.py. " + NOT_A_FINDING}


def _print_exact(r):
    print(f"{r['order']}  goal={r['goal']}  families={','.join(r['families']) or '-'}")
    for title, rows in (("instances", r["instances"]), ("class candidates (judgment needed)", r["class_candidates"])):
        print(f"  {title}: {len(rows)}")
        for lm in rows[:40]:
            s = lm["statement"]
            print(f"    [{lm['status']:6}] {lm['lemma_id']}  {s['subject'][:70]} {s['relation']} {','.join(s['objects']) or s['class_scope'][:60]}"
                  f"  {s.get('date') or ''}  grade={lm.get('grade', '')}" + (f"  ({lm['sorry_reason'][:50]})" if lm["status"] == "sorry" else ""))
    print("  " + r["note"])


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("root", nargs="?", default=os.environ.get("REPO_ROOT", "."))
    b.add_argument("out", nargs="?", default=os.environ.get("OUTPUT_DIR", os.path.join(HERE, "output")))
    e = sub.add_parser("exact")
    e.add_argument("order")
    e.add_argument("--goal", choices=("end", "basis", "any"), default="any")
    e.add_argument("--json", action="store_true")
    s = sub.add_parser("supplement")
    s.add_argument("ids", nargs="+")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        pool = None
        if os.environ.get("FORMULARIO_OFFLINE") != "1":
            sys.path.insert(0, os.path.join(a.root, "jobs", "_lib"))
            import fetch_pool
            pool = fetch_pool.FetchPool(os.environ.get("JOB_CACHE_DIR") or tempfile.mkdtemp(prefix="formulario-"),
                                        workers=4, per_host=2, max_bytes=60_000_000, min_interval=0.5,
                                        user_agent="EO-Road-System/1.0 (Formulario; public-domain government documents)")
        build(a.root, a.out, os.environ.get("JOB_PRIOR_OUTPUT_DIR") or os.path.join(HERE, "output"), pool)
    elif a.cmd == "exact":
        r = exact(a.order if a.order.startswith("EO:") else "EO:" + a.order, a.goal)
        print(json.dumps(r, ensure_ascii=False, indent=1)) if a.json else _print_exact(r)
    else:
        print(json.dumps(supplement(a.ids), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
