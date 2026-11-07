#!/usr/bin/env python3
"""Export "Nihil obstat" cards: one self-contained JSON file per filed claim.

A card gathers, for one executive order, everything a human certifier needs on one page:
the exact filed claim (with its SHA-256 recomputed), every source it cites with the saved
text those quotations were checked against, the located byte span of every quotation,
the claim checker's results, and every AI review record that names the exact claim hash.

Standard library only. It reads the repository and writes only the --out folder; it never
changes a status, a count or a claim.

  python export_cards.py REPO --ids EO:8123 EO:10080 --out cards_out
  python export_cards.py REPO --git-ref origin/main --ids EO:8123 --out cards_out
  python export_cards.py REPO --git-ref origin/main --list-ready 20

REPO is a checkout, or (with --git-ref) any git repository whose objects hold the ref, so a
sparse checkout can export without widening. See README.md.
"""

import argparse
import base64
import collections
import csv
import datetime as dt
import hashlib
import json
import os
import pathlib
import posixpath
import re
import subprocess
import sys

EXPORTER_VERSION = "0.1.0"
CARD_SCHEMA = "eo-nihil-obstat-card/v1"

# Paths inside the repository, as the claim checker and readiness tracker publish them.
READINESS_CSV = "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
READINESS_STATUS = "jobs/readiness-tracker/output/STATUS.json"
PER_CLAIM = "jobs/claim-checker/output/PER_CLAIM.json"
CLAIM_CHECKS = "jobs/claim-checker/output/CLAIM_CHECKS.csv"
CHECKER_STATUS = "jobs/claim-checker/output/STATUS.json"

MAX_TEXT_BYTES_DEFAULT = 600_000
MAX_RAW_BYTES_DEFAULT = 262_144
MAX_OCCURRENCES_KEPT = 8

# --------------------------------------------------------------- claim hash (claim_gate.claim_sha)


def canonical(value):
    """research/stage19/code/claim_gate.py canonical(): the exact bytes the claim hash covers."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def claim_sha(claim):
    return hashlib.sha256(canonical(claim).encode("utf-8")).hexdigest()


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------- repository access


class FsRepo:
    """A repository checkout on disk."""

    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()
        self._tree = None

    def _safe(self, rel):
        p = (self.root / rel).resolve()
        try:
            p.relative_to(self.root)
        except ValueError:
            return None
        return p

    def exists(self, rel):
        p = self._safe(rel)
        return bool(p and p.is_file())

    def size(self, rel):
        p = self._safe(rel)
        return p.stat().st_size if p and p.is_file() else None

    def read_bytes(self, rel):
        p = self._safe(rel)
        if not p or not p.is_file():
            raise FileNotFoundError(rel)
        return p.read_bytes()

    def files(self, prefix):
        """Repo-relative POSIX paths of every file under prefix (a folder, with trailing slash)."""
        base = self._safe(prefix)
        if not base or not base.is_dir():
            return
        for dirpath, _dirs, names in os.walk(base):
            for n in names:
                yield pathlib.Path(dirpath, n).relative_to(self.root).as_posix()

    def close(self):
        pass


class GitRepo:
    """Reads blobs from a git ref without a checkout (one persistent `git cat-file --batch`)."""

    def __init__(self, root, ref):
        self.root, self.ref = str(root), ref
        self._sizes = None
        self._batch = None

    def _load_tree(self):
        if self._sizes is None:
            out = subprocess.run(["git", "-C", self.root, "ls-tree", "-r", "-l", "-z", self.ref],
                                 capture_output=True, check=True).stdout
            sizes = {}
            for rec in out.split(b"\0"):
                if not rec:
                    continue
                meta, _, path = rec.partition(b"\t")
                parts = meta.split()
                if len(parts) >= 4 and parts[1] == b"blob":
                    sizes[path.decode("utf-8", "replace")] = int(parts[3])
            self._sizes = sizes
        return self._sizes

    def exists(self, rel):
        return rel in self._load_tree()

    def size(self, rel):
        return self._load_tree().get(rel)

    def read_bytes(self, rel):
        if rel not in self._load_tree():
            raise FileNotFoundError(rel)
        if self._batch is None:
            self._batch = subprocess.Popen(["git", "-C", self.root, "cat-file", "--batch"],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self._batch.stdin.write(f"{self.ref}:{rel}\n".encode("utf-8"))
        self._batch.stdin.flush()
        header = self._batch.stdout.readline().split()
        if len(header) < 3 or header[1] != b"blob":
            raise FileNotFoundError(rel)
        size = int(header[2])
        data = self._batch.stdout.read(size)
        self._batch.stdout.read(1)
        return data

    def files(self, prefix):
        for p in self._load_tree():
            if p.startswith(prefix):
                yield p

    def close(self):
        if self._batch is not None:
            self._batch.stdin.close()
            self._batch.wait()
            self._batch.stdout.close()
            self._batch = None


def open_repo(path, git_ref=None):
    return GitRepo(path, git_ref) if git_ref else FsRepo(path)


def read_json(repo, rel):
    return json.loads(repo.read_bytes(rel).decode("utf-8"))


def norm_id(value):
    v = value.strip()
    return v if v.upper().startswith("EO:") else f"EO:{v}"


# --------------------------------------------------------------- walking a claim (mirrors the checker)

SOURCE_KEYS = ("original_representation", "original_source", "source")
SOURCE_LIST_KEYS = ("sources", "source_refs")
QUOTE_KEY = re.compile(r"(^|_)(quote|quotes|quoted|quotation|quotations|verbatim|excerpt|excerpts)($|_)")
REF_IN_LIST = re.compile(r"(^|\.)(sources|source_refs)\[\d+\]$")
REF_KEY_PATH = re.compile(r"(^|\.)(original_representation|original_source|source)$")


def walk(obj, path="", chain=()):
    """Yield (path, key, value, chain_of_parent_dicts) like jobs/claim-checker/checker.py walk()."""
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


def element_of(path):
    """Which part of the claim a path belongs to: the unit a human certifies separately."""
    if path.startswith("original_representation"):
        return "original"
    m = re.match(r"operative_clauses\[(\d+)\]", path)
    if m:
        return f"clause:{m.group(1)}"
    if path.startswith(("whole_order_end", "whole_order_status", "formal_disposition")):
        return "ending"
    if path.startswith("savings_residuals"):
        return "savings"
    if path.startswith(("later_source_search", "counterevidence", "source_notes")):
        return "search"
    return "other"


def collect_refs_and_quotes(claim):
    """([(path, ref_dict)], [(quote_path, quote_text, ref_path, ref_dict)]) as the checker pairs them."""
    refs, quotes = [], []
    for path, key, val, chain in walk(claim):
        if key in SOURCE_KEYS and isinstance(val, dict):
            refs.append((path, val))
        elif key in SOURCE_LIST_KEYS and isinstance(val, list):
            refs += [(f"{path}[{n}]", v) for n, v in enumerate(val) if isinstance(v, dict)]
        if key is None:
            continue
        found = []
        parent_path = path.rsplit(".", 1)[0] if "." in path else ""
        if key == "original_operative_text" or QUOTE_KEY.search(key):
            if isinstance(val, str):
                found = [(path, val, chain, parent_path)]
            elif isinstance(val, list):
                found = [(f"{path}[{n}]", v, chain, parent_path) for n, v in enumerate(val) if isinstance(v, str)]
            elif isinstance(val, dict) and isinstance(val.get("text"), str):
                found = [(f"{path}.text", val["text"], chain + (val,), path)]
        for field, q, qchain, own_path in found:
            ref, ref_path = None, None
            own = qchain[-1] if qchain else None
            if isinstance(own, dict) and (REF_KEY_PATH.search(own_path) or REF_IN_LIST.search(own_path)) and \
                    any(k in own for k in ("sha256", "local_file_sha256", "url")):
                ref, ref_path = own, own_path
            else:
                for obj in reversed(qchain):
                    for k in ("original_source", "source"):
                        if isinstance(obj.get(k), dict) and obj.get(k) is not val:
                            ref, ref_path = obj[k], k
                            break
                    if ref is not None:
                        break
            if ref is None and isinstance(claim.get("original_representation"), dict):
                ref, ref_path = claim["original_representation"], "original_representation"
            quotes.append((field, q, ref_path, ref))
    return refs, quotes


# --------------------------------------------------------------- locating a quotation (offset-preserving)

LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl",
             "ﬅ": "st", "ﬆ": "st", "­": ""}
HYPHEN_BREAK = re.compile(r"(\w)-[ \t]*\n[ \t]*(?=\w)")
HYPHEN_KEEP = re.compile(r"(\w-)[ \t]*\n[ \t]*(?=\w)")
WS_RUN = re.compile(r"\s+")
SPACE_BEFORE_CLOSE = re.compile(r" (?=[.,;:!?)\]}’”])")
SPACE_AFTER_OPEN = re.compile(r"(?<=[(\[{‘“]) ")


def _sub(pairs, regex, keep):
    """Rewrite [(char, original_index)] where regex matches; keep(m) gives the pairs to retain."""
    s = "".join(c for c, _ in pairs)
    out, pos = [], 0
    for m in regex.finditer(s):
        out.extend(pairs[pos:m.start()])
        out.extend(keep(m, pairs))
        pos = m.end()
    out.extend(pairs[pos:])
    return out


def _prepare(text):
    pairs = []
    for i, ch in enumerate(text):
        rep = LIGATURES.get(ch)
        if rep is None:
            pairs.append((ch, i))
        else:
            pairs.extend((c, i) for c in rep)
    pairs = _sub(pairs, re.compile(r"\r\n"), lambda m, p: [(p[m.start() + 1][0], p[m.start()][1])])
    return [(("\n" if c == "\r" else c), i) for c, i in pairs]


def _ws_pairs(pairs):
    pairs = _sub(pairs, WS_RUN, lambda m, p: [(" ", p[m.start()][1])])
    while pairs and pairs[0][0] == " ":
        pairs.pop(0)
    while pairs and pairs[-1][0] == " ":
        pairs.pop()
    pairs = _sub(pairs, SPACE_BEFORE_CLOSE, lambda m, p: [])
    return _sub(pairs, SPACE_AFTER_OPEN, lambda m, p: [])


def normalised_readings(text):
    """The checker's three readings of a text, each as (string, original_char_index_per_char)."""
    base = _prepare(text)
    readings = []
    for regex, keep in ((HYPHEN_BREAK, lambda m, p: [p[m.start()]]),
                        (HYPHEN_KEEP, lambda m, p: p[m.start():m.start() + 2]),
                        (None, None)):
        pairs = _sub(base, regex, keep) if regex else list(base)
        pairs = _ws_pairs(pairs)
        reading = ("".join(c for c, _ in pairs), [i for _, i in pairs])
        if all(reading[0] != r[0] for r in readings):
            readings.append(reading)
    return readings


def norm_quote(q):
    """checker.norm_quote: whitespace, ligatures and line-break hyphenation evened out."""
    pairs = _prepare(q)
    pairs = _sub(pairs, HYPHEN_BREAK, lambda m, p: [p[m.start()]])
    return "".join(c for c, _ in _ws_pairs(pairs))


def find_occurrences(quote, text, readings=None):
    """(status, [(char_start, char_end)]) with status exact | normalised | not_found."""
    if not quote or not quote.strip():
        return "not_found", []
    hits, pos = [], text.find(quote)
    while pos != -1:
        hits.append((pos, pos + len(quote)))
        pos = text.find(quote, pos + len(quote))
    if hits:
        return "exact", hits
    nq = norm_quote(quote)
    if not nq:
        return "not_found", []
    for s, idx in readings if readings is not None else normalised_readings(text):
        hits, pos = [], s.find(nq)
        while pos != -1:
            hits.append((idx[pos], idx[pos + len(nq) - 1] + 1))
            pos = s.find(nq, pos + len(nq))
        if hits:
            return "normalised", hits
    return "not_found", []


def byte_offsets(text, spans, ascii_only):
    """UTF-8 byte offsets of char spans (lone surrogates from undecodable bytes round-trip)."""
    if ascii_only:
        return list(spans)
    out = []
    for a, b in spans:
        sa = len(text[:a].encode("utf-8", "surrogateescape"))
        sb = sa + len(text[a:b].encode("utf-8", "surrogateescape"))
        out.append((sa, sb))
    return out


# --------------------------------------------------------------- source index (for refs without text_path)


class SourceIndex:
    """sha256 -> records from jobs/*/output/SOURCES.jsonl, read only if a source needs it."""

    def __init__(self, repo):
        self.repo, self.by_sha, self.loaded = repo, collections.defaultdict(list), False

    def load(self, wanted):
        if self.loaded:
            return
        self.loaded = True
        pat = re.compile(r'"sha256":\s*"([0-9a-f]{64})"')
        for rel in sorted(self.repo.files("jobs/")):
            if not re.fullmatch(r"jobs/[^/]+/output/SOURCES\.jsonl", rel):
                continue
            try:
                data = self.repo.read_bytes(rel).decode("utf-8", "replace")
            except OSError:
                continue
            for line in data.splitlines():
                m = pat.search(line)
                if m and m.group(1) in wanted:
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    rec["_source_file"] = rel
                    self.by_sha[m.group(1)].append(rec)

    def text_candidates(self, sha):
        base = None
        for rec in self.by_sha.get(sha, []):
            tp = rec.get("text_path")
            if isinstance(tp, str) and tp.strip():
                base = posixpath.dirname(rec["_source_file"])
                yield posixpath.normpath(posixpath.join(base, tp.replace("\\", "/"))), rec


def safe_rel(path):
    if not isinstance(path, str) or not path.strip():
        return None
    p = posixpath.normpath(path.replace("\\", "/"))
    if p.startswith(("/", "../")) or p == ".." or re.match(r"^[A-Za-z]:", p):
        return None
    return p


# --------------------------------------------------------------- reviews


REVIEW_NAME = re.compile(r"(?i)(review|reveal|verdict|certif).*\.jsonl$")


def find_reviews(repo, wanted, extra_files=()):
    """{(instrument_id, claim_sha256): [review records]} for the wanted claims only."""
    found = collections.defaultdict(list)
    files = [f for f in repo.files("research/") if REVIEW_NAME.search(posixpath.basename(f))
             and "/receipts/" not in f]
    files += [f for f in extra_files if f not in files]
    wanted_shas = {sha for _, sha in wanted}
    for rel in sorted(files):
        try:
            data = repo.read_bytes(rel).decode("utf-8", "replace")
        except OSError:
            continue
        if not any(s in data for s in wanted_shas):
            continue
        for n, line in enumerate(data.splitlines(), 1):
            line = line.strip()
            if not line or not any(s in line for s in wanted_shas):
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            key = (rec.get("instrument_id"), rec.get("claim_sha256"))
            if key in wanted:
                found[key].append({"file": rel, "line": n, "record": rec})
    return found


REVIEW_KEEP = ("review_id", "reviewer", "model_family", "independent", "separate_context", "review_kind",
               "scope", "verdict", "defects", "evidence_checked", "reasoning", "started_utc", "ended_utc",
               "reviewed_on", "rationale", "decision", "reviewer_role")


def review_view(item):
    rec = item["record"]
    out = {k: rec[k] for k in REVIEW_KEEP if k in rec}
    out["file"], out["line"] = item["file"], item["line"]
    name = posixpath.basename(item["file"]).upper()
    out["phase"] = ("after_reveal" if "REVEAL" in name else "correction" if "CORRECT" in name
                    else "blind" if "BLIND" in name else "review")
    return out


def review_gate(reviews):
    """Informational summary against the campaign rule: two blind AI reviewers uphold the exact hash."""
    up, rej, fam = set(), set(), set()
    for r in reviews:
        who = r.get("reviewer") or r.get("review_id") or "?"
        verdict = str(r.get("verdict") or r.get("decision") or "")
        if verdict.startswith("upheld") or verdict == "uphold":
            up.add(who)
            if r.get("model_family"):
                fam.add(r["model_family"])
        elif verdict.startswith("reject"):
            rej.add(who)
    return {"rule": "two blind AI reviewers must uphold the exact claim hash",
            "distinct_upholding_reviewers": len(up), "upholding_reviewers": sorted(up),
            "rejecting_reviewers": sorted(rej), "model_families": sorted(fam),
            "met": len(up) >= 2 and not (rej - up)}


# --------------------------------------------------------------- checker rows


def load_checker_rows(repo, claim_keys):
    rows = collections.defaultdict(list)
    if not repo.exists(CLAIM_CHECKS):
        return rows
    text = repo.read_bytes(CLAIM_CHECKS).decode("utf-8", "replace")
    for row in csv.DictReader(text.splitlines()):
        if row.get("claim_key") in claim_keys:
            rows[row["claim_key"]].append({k: row.get(k) for k in
                                           ("step", "check", "field", "result", "status", "detail")})
    return rows


# --------------------------------------------------------------- building a card


def decode_text(raw):
    """(text, encoding, ascii_only): utf-8 text; undecodable bytes become lone surrogates."""
    try:
        text = raw.decode("utf-8")
        return text, "utf-8", text.isascii()
    except UnicodeDecodeError:
        return raw.decode("utf-8", "surrogateescape"), "base64", False


def build_source(repo, index, ref, ctx):
    """One source entry (text layer + raw custody) for a ref dict; ctx caches by key."""
    sha = ref.get("sha256") or ref.get("local_file_sha256")
    tp = safe_rel(ref.get("text_path"))
    local = safe_rel(ref.get("local_path"))
    key = f"{sha or ref.get('archival_id') or ref.get('url')}|{tp or ''}"
    if key in ctx["sources"]:
        return ctx["sources"][key]
    src = {"source_key": key, "url": ref.get("url"), "archival_id": ref.get("archival_id"),
           "page_or_item": ref.get("page_or_item"), "sha256": sha,
           "text_path": tp, "text_sha256_claimed": ref.get("text_sha256"),
           "grade": ref.get("grade"), "acceptable_as_original": ref.get("acceptable_as_original"),
           "requires_page_check": ref.get("requires_page_check"),
           "location_verified": ref.get("location_verified"), "uses": []}
    # Text layer: the claim's own text_path, else the source record the job kept for this hash.
    text_rel, how = None, None
    if tp and repo.exists(tp):
        text_rel, how = tp, "claim text_path"
    elif sha:
        index.load(ctx["wanted_shas"])
        for cand, rec in index.text_candidates(sha):
            if repo.exists(cand):
                text_rel, how = cand, f"{rec['_source_file']} text_path"
                break
    src["text_found_at"], src["text_found_by"] = text_rel, how
    if text_rel:
        raw = repo.read_bytes(text_rel)
        src["text_bytes"] = len(raw)
        src["text_sha256_export"] = sha256_hex(raw)
        src["text_sha256_matches_claim"] = (None if not src["text_sha256_claimed"]
                                            else src["text_sha256_claimed"] == src["text_sha256_export"])
        text, enc, ascii_only = decode_text(raw)
        src["_text"], src["_ascii"], src["_readings"] = text, ascii_only, None
        if len(raw) <= ctx["max_text"]:
            src["text_embedded"], src["text_encoding"] = True, enc
            if enc == "utf-8":
                src["text"] = text
            else:
                src["text_b64"] = base64.b64encode(raw).decode("ascii")
        else:
            src["text_embedded"] = False
            src["text_note"] = (f"saved text is {len(raw)} bytes, over the {ctx['max_text']}-byte export cap; "
                                "attach it in the page (it is matched by SHA-256)")
    else:
        src["text_embedded"] = False
        src["text_note"] = "no saved text found for this source in the repository"
    # Raw custody: a committed copy of the claimed bytes, embedded only when small.
    raw_rel = local if local and repo.exists(local) else None
    src["raw_in_repo"] = bool(raw_rel)
    if raw_rel:
        src["raw_path"], src["raw_bytes"] = raw_rel, repo.size(raw_rel)
        if src["raw_bytes"] is not None and src["raw_bytes"] <= ctx["max_raw"]:
            data = repo.read_bytes(raw_rel)
            src["raw_sha256_export"] = sha256_hex(data)
            if src["raw_sha256_export"] == sha:
                src["raw_embedded"], src["raw_b64"] = True, base64.b64encode(data).decode("ascii")
        elif ctx.get("copy_to") is not None:
            data = repo.read_bytes(raw_rel)
            src["raw_sha256_export"] = sha256_hex(data)
            if src["raw_sha256_export"] == sha:
                ext = posixpath.splitext(raw_rel)[1] or ".bin"
                dest = ctx["copy_to"] / f"{sha}{ext}"
                dest.write_bytes(data)
                src["raw_copied_to"] = f"sources/{dest.name}"
    src.setdefault("raw_embedded", False)
    ctx["sources"][key] = src
    return src


def locate(src, quote, declared):
    """Span record for one quotation against a source's saved text."""
    span = {"quote": quote}
    if "_text" not in src:
        span["status"] = "no_text"
        return span
    text = src["_text"]
    if src["_readings"] is None:
        src["_readings"] = normalised_readings(text)
    status, hits = find_occurrences(quote, text, src["_readings"])
    span["status"], span["occurrences"] = status, len(hits)
    dcs, dce = declared
    if hits:
        pick = hits[0]
        if isinstance(dcs, int) and isinstance(dce, int):
            inside = [h for h in hits if h[0] >= dcs and h[1] <= dce]
            span["in_declared_span"] = bool(inside)
            if inside:
                pick = inside[0]
        extra = [h for h in hits if h != pick][:MAX_OCCURRENCES_KEPT]
        spans = byte_offsets(text, [pick] + extra, src["_ascii"])
        span["byte_start"], span["byte_end"] = spans[0]
        span["other_occurrences"] = [{"byte_start": a, "byte_end": b} for a, b in spans[1:]]
    if isinstance(dcs, int) and isinstance(dce, int) and 0 <= dcs <= dce <= len(text):
        (ds, de), = byte_offsets(text, [(dcs, dce)], src["_ascii"])
        span["declared"] = {"char_start": dcs, "char_end": dce, "byte_start": ds, "byte_end": de}
    return span


def build_card(repo, iid, ctx, now):
    row = ctx["readiness"].get(iid)
    if row is None:
        raise SystemExit(f"{iid}: not in {READINESS_CSV}")
    if row.get("ready_for_human_review") != "yes" and not ctx["allow_not_ready"]:
        raise SystemExit(f"{iid}: ready_for_human_review is {row.get('ready_for_human_review')!r}; "
                         "pass --allow-not-ready to export it anyway (the card will say so)")
    entry = ctx["per_claim"]["by_instrument"].get(iid)
    if entry is None:
        raise SystemExit(f"{iid}: no claim recorded in {PER_CLAIM}")
    claim_key = entry["claim_key"]
    rel, _, line_no = claim_key.rpartition(":")
    lines = repo.read_bytes(rel).decode("utf-8").splitlines()
    claim = json.loads(lines[int(line_no) - 1])
    sha = claim_sha(claim)
    if sha != entry["claim_sha256"]:
        raise SystemExit(f"{iid}: claim at {claim_key} hashes to {sha}, but the checker recorded "
                         f"{entry['claim_sha256']} (the claim changed since the checker ran; re-run it)")
    refs, quotes = collect_refs_and_quotes(claim)
    sources, spans = [], []
    for path, ref in refs:
        src = build_source(repo, ctx["index"], ref, ctx)
        if path not in src["uses"]:
            src["uses"].append(path)
    for n, (qpath, quote, rpath, ref) in enumerate(quotes):
        if ref is None:
            spans.append({"span_id": f"q{n}", "claim_path": qpath, "element": element_of(qpath),
                          "source_key": None, "quote": quote, "status": "no_source"})
            continue
        src = build_source(repo, ctx["index"], ref, ctx)
        span = locate(src, quote, (ref.get("char_start"), ref.get("char_end")))
        span.update({"span_id": f"q{n}", "claim_path": qpath, "element": element_of(qpath),
                     "source_key": src["source_key"], "ref_path": rpath})
        spans.append(span)
    used = {s["source_key"] for s in spans if s.get("source_key")}
    sources = [s for s in ctx["sources"].values() if s["source_key"] in used or s["uses"]]
    ctx["sources"] = {}
    for s in sources:
        for k in [k for k in s if k.startswith("_")]:
            del s[k]
    clauses = claim.get("operative_clauses") if isinstance(claim.get("operative_clauses"), list) else []
    elements = [{"id": "original", "label": "Original text and identity"}]
    for i, c in enumerate(clauses):
        elements.append({"id": f"clause:{i}", "label": f"Clause {i + 1}: {(c or {}).get('scope_id', '?')}"})
    elements += [{"id": "ending", "label": "Whole-order status and end"},
                 {"id": "savings", "label": "Savings and residual effects"},
                 {"id": "search", "label": "Later-source search and counterevidence"}]
    reviews = [review_view(r) for r in ctx["reviews"].get((iid, sha), [])]
    check_claims = {c["claim_key"]: c for c in ctx["per_claim"]["claims"]}
    summary = {k: v for k, v in (check_claims.get(claim_key) or entry).items()
               if k not in ("claim_key", "file", "line")}
    keep = ("provisional_status", "decision_origin", "ready_for_human_review", "ready_tier", "text_evidence_tier",
            "original_copy_replacement_required", "quotation_recheck_required", "claim_schema", "status_contested",
            "whole_end_date_kind", "blockers", "exhausted_steps", "generation_id")
    return {
        "schema": CARD_SCHEMA, "exporter_version": EXPORTER_VERSION, "exported_utc": now,
        "instrument_id": iid, "claim_sha256": sha, "claim_sha256_recomputed_at_export": True,
        "claim_key": claim_key, "claim": claim,
        "readiness": {k: row.get(k) for k in keep if k in row},
        "tracker_generation": ctx["tracker_status"], "checker_generation": ctx["checker_status"],
        "checker": {"summary": summary, "non_passing_rows": ctx["checks"].get(claim_key, []),
                    "note": "Mechanical checks only. Passing is not a legal conclusion."},
        "ai_reviews": reviews, "ai_review_gate": review_gate(reviews),
        "elements": elements, "sources": sources, "spans": spans,
    }


# --------------------------------------------------------------- commands


def load_context(repo, args, wanted_ids):
    readiness = {}
    for row in csv.DictReader(repo.read_bytes(READINESS_CSV).decode("utf-8").splitlines()):
        readiness[row["instrument_id"]] = row
    per_claim = read_json(repo, PER_CLAIM)
    ctx = {"readiness": readiness, "per_claim": per_claim, "index": SourceIndex(repo),
           "max_text": args.max_text_bytes, "max_raw": args.max_raw_bytes, "sources": {},
           "allow_not_ready": args.allow_not_ready, "wanted_shas": set(), "copy_to": None,
           "tracker_status": read_json(repo, READINESS_STATUS) if repo.exists(READINESS_STATUS) else None,
           "checker_status": read_json(repo, CHECKER_STATUS) if repo.exists(CHECKER_STATUS) else None}
    wanted, keys = set(), set()
    for iid in wanted_ids:
        e = per_claim["by_instrument"].get(iid)
        if e:
            wanted.add((iid, e["claim_sha256"]))
            keys.add(e["claim_key"])
    ctx["reviews"] = find_reviews(repo, wanted, args.reviews_file)
    ctx["checks"] = load_checker_rows(repo, keys)
    return ctx


def prescan_shas(repo, ctx, ids):
    """All source hashes the wanted claims cite, so one pass over SOURCES.jsonl serves them all."""
    for iid in ids:
        e = ctx["per_claim"]["by_instrument"].get(iid)
        if not e:
            continue
        rel, _, n = e["claim_key"].rpartition(":")
        claim = json.loads(repo.read_bytes(rel).decode("utf-8").splitlines()[int(n) - 1])
        for _p, ref in collect_refs_and_quotes(claim)[0]:
            for k in ("sha256", "local_file_sha256"):
                if isinstance(ref.get(k), str):
                    ctx["wanted_shas"].add(ref[k])


def list_ready(repo, args):
    rows = list(csv.DictReader(repo.read_bytes(READINESS_CSV).decode("utf-8").splitlines()))
    per_claim = read_json(repo, PER_CLAIM)["by_instrument"]
    ready = [r["instrument_id"] for r in rows if r["ready_for_human_review"] == "yes" and r["instrument_id"] in per_claim]
    wanted = {(i, per_claim[i]["claim_sha256"]) for i in ready}
    reviews = find_reviews(repo, wanted, args.reviews_file)
    out = []
    for iid in ready:
        rv = reviews.get((iid, per_claim[iid]["claim_sha256"]), [])
        out.append((iid, len(rv), review_gate([r["record"] for r in rv])["distinct_upholding_reviewers"]))
    out.sort(key=lambda t: (-t[2], -t[1], t[0]))
    print(f"{len(ready)} orders are ready_for_human_review=yes; {sum(1 for o in out if o[1])} have review records "
          f"naming the exact claim hash")
    for iid, n, up in out[:args.list_ready]:
        print(f"{iid}\treview_records={n}\tupholding_reviewers={up}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="repository checkout (or any git repo when --git-ref is given)")
    ap.add_argument("--git-ref", help="read the repository from this git ref instead of the working tree")
    ap.add_argument("--ids", nargs="+", default=[], help="instrument ids, e.g. EO:8123 or 8123")
    ap.add_argument("--ids-file", help="file with one instrument id per line")
    ap.add_argument("--out", help="output folder (cards/ is created inside it)")
    ap.add_argument("--list-ready", type=int, metavar="N", help="print N ready orders with review counts and stop")
    ap.add_argument("--allow-not-ready", action="store_true", help="export orders not marked ready_for_human_review")
    ap.add_argument("--max-text-bytes", type=int, default=MAX_TEXT_BYTES_DEFAULT)
    ap.add_argument("--max-raw-bytes", type=int, default=MAX_RAW_BYTES_DEFAULT,
                    help="embed a committed raw source only if at most this big")
    ap.add_argument("--copy-originals", action="store_true",
                    help="copy larger committed raw sources to <out>/sources/<sha256>.<ext> for the page's folder picker")
    ap.add_argument("--reviews-file", action="append", default=[], help="extra review JSONL path inside the repo")
    args = ap.parse_args(argv)

    repo = open_repo(args.repo, args.git_ref)
    try:
        if args.list_ready:
            list_ready(repo, args)
            return 0
        ids = [norm_id(i) for i in args.ids]
        if args.ids_file:
            ids += [norm_id(l) for l in pathlib.Path(args.ids_file).read_text("utf-8").splitlines() if l.strip()]
        if not ids or not args.out:
            ap.error("give --ids/--ids-file and --out (or --list-ready N)")
        out = pathlib.Path(args.out)
        (out / "cards").mkdir(parents=True, exist_ok=True)
        ctx = load_context(repo, args, ids)
        if args.copy_originals:
            (out / "sources").mkdir(exist_ok=True)
            ctx["copy_to"] = out / "sources"
        prescan_shas(repo, ctx, ids)
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        manifest = {"schema": "eo-nihil-obstat-manifest/v1", "exporter_version": EXPORTER_VERSION,
                    "exported_utc": now, "git_ref": args.git_ref, "cards": []}
        for iid in ids:
            card = build_card(repo, iid, ctx, now)
            data = json.dumps(card, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8")
            name = f"cards/{iid.replace(':', '_')}.json"
            (out / name).write_bytes(data)
            manifest["cards"].append({"instrument_id": iid, "file": name, "bytes": len(data),
                                      "sha256": sha256_hex(data), "claim_sha256": card["claim_sha256"],
                                      "spans": len(card["spans"]), "sources": len(card["sources"]),
                                      "ai_reviews": len(card["ai_reviews"])})
            print(f"{iid}: {len(data):,} bytes, {len(card['sources'])} sources, {len(card['spans'])} quoted spans, "
                  f"{len(card['ai_reviews'])} AI review records")
        (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", "utf-8")
        total = sum(c["bytes"] for c in manifest["cards"])
        print(f"wrote {len(ids)} cards ({total:,} bytes) to {out}")
        return 0
    finally:
        repo.close()


if __name__ == "__main__":
    sys.exit(main())
