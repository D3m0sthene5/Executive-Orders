"""Where the project holds saved copies of sources, and how to read their text.

The claim checker asks two questions of every source a claim cites:

1. Does the project hold a saved copy with exactly the SHA-256 the claim gives?
2. If so, what is the text of that copy (to check quotations against)?

This module answers both. It builds an index of every saved copy the project
records, from these places (all are optional; a missing file is skipped and
noted):

* ``jobs/*/output/SOURCES.jsonl`` (the shared source-record format every job
  writes; the extracted text sits next to it at ``text_path``),
* Stage 21 ``original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv`` and
  ``ACQUISITION_LOG.jsonl`` (official PDFs saved in the repo),
* Stage 20 ``STATUTE_FETCH_INDEX.csv`` (Statutes at Large PDFs saved in the
  repo) and ``OPUS_ORIGINAL_MEDIA_MEMBER_MAP.csv`` (Opus images and PDFs),
* Stage 18 ``SOURCE_MANIFEST.json`` (early FR/LoC/Statutes excerpts),
* the Opus Stage 11 release manifest (every file in the complete Opus zip,
  read from the zip when it is on this machine, otherwise from the small
  committed index ``data/opus_manifest_index.csv.gz``).

Nothing here downloads anything or changes any file outside the cache folder.
"""

import collections
import csv
import gzip
import hashlib
import html
import html.parser
import io
import json
import os
import pathlib
import re
import zipfile
from urllib.parse import urlsplit, urlunsplit

HEX64 = re.compile(r"^[0-9a-f]{64}$")
LFS_MAGIC = b"version https://git-lfs.github.com/spec/v1"

OPUS_DIR = "releases/opus_stage11_complete"
OPUS_COMPLETE_ZIP = OPUS_DIR + "/OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip"
OPUS_MEDIA_ZIP = OPUS_DIR + "/OPUS_STAGE11_EVIDENCE_ORIGINALS.zip"
OPUS_PREFIX = "OPUS_STAGE11_FINITE_STATUS_DELTA/"

INPUTS = {
    "stage21_custody": "research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv",
    "stage21_acquisition_log": "research/stage21/original_sources/ACQUISITION_LOG.jsonl",
    "stage20_statutes": "research/stage20/output/STATUTE_FETCH_INDEX.csv",
    "stage20_opus_media": "research/stage20/output/OPUS_ORIGINAL_MEDIA_MEMBER_MAP.csv",
    "stage18_manifest": "research/stage18/SOURCE_MANIFEST.json",
}


def sha_hex(value):
    """Lower-case 64-hex SHA-256, or None if the value is not one."""
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    return v if HEX64.match(v) else None


def norm_url(url):
    """Comparable form of a URL: https, lower-case host, no fragment or trailing slash."""
    if not isinstance(url, str) or not url.strip():
        return None
    try:
        p = urlsplit(url.strip())
    except ValueError:
        return None
    if not p.netloc:
        return None
    scheme = "https" if p.scheme in ("http", "https") else p.scheme
    return urlunsplit((scheme, p.netloc.lower(), p.path.rstrip("/") or "/", p.query, ""))


def is_lfs_pointer(path):
    try:
        if path.stat().st_size > 1024:
            return False
        with open(path, "rb") as fh:
            return fh.read(len(LFS_MAGIC)) == LFS_MAGIC
    except OSError:
        return False


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# Where a copy's original bytes are kept:
#   repo_file     a file committed in this repository (re-hashed when checked out here)
#   opus_release  a member of the Opus Stage 11 Git LFS release (re-hashed when the zip is here)
#   job_cache     another job's download cache, found on this machine (re-hashed here)
#   record_only   only a custody record (hash, maybe text): the bytes are in no committed place
CUSTODY_KINDS = ("repo_file", "opus_release", "job_cache", "record_only")


class HeldCopy:
    """One saved copy the project records."""

    __slots__ = ("origin", "sha256", "url", "bytes", "local_path", "text_path",
                 "zip_members", "page_or_item", "instrument_ids", "note", "custody")

    def __init__(self, origin, sha256, url=None, nbytes=None, local_path=None,
                 text_path=None, zip_members=(), page_or_item=None,
                 instrument_ids=(), note="", custody="repo_file"):
        self.origin = origin
        self.sha256 = sha256
        self.url = url if isinstance(url, str) else None
        self.bytes = nbytes if isinstance(nbytes, int) else None
        self.local_path = local_path  # pathlib.Path or None
        self.text_path = text_path  # pathlib.Path or None (or (zip, member))
        self.zip_members = list(zip_members)  # [(zip_path, member_name)]
        self.page_or_item = page_or_item if isinstance(page_or_item, str) else None
        self.instrument_ids = [i.strip() for i in instrument_ids if isinstance(i, str) and i.strip()]
        self.note = note if isinstance(note, str) else ""
        self.custody = custody if custody in CUSTODY_KINDS else "record_only"

    @property
    def bytes_kept(self):
        """False when only the hash (and maybe text) was recorded."""
        return self.custody != "record_only"

    def describe(self):
        where = self.origin
        if self.url:
            where += f" ({self.url})"
        return where


class HeldIndex:
    def __init__(self):
        self.by_sha = {}
        self.by_url = {}
        self.origin_counts = {}
        self.notes = []  # plain-English notes about inputs (missing files etc.)
        self.packed_texts = {}  # sha256 -> (pages, how), from the committed Opus text pack

    def add(self, copy):
        if not copy.sha256:
            return
        self.by_sha.setdefault(copy.sha256, []).append(copy)
        u = norm_url(copy.url)
        if u:
            self.by_url.setdefault(u, []).append(copy)
        self.origin_counts[copy.origin] = self.origin_counts.get(copy.origin, 0) + 1

    def lookup_sha(self, sha):
        return self.by_sha.get(sha, [])

    def lookup_url(self, url):
        u = norm_url(url)
        return self.by_url.get(u, []) if u else []


def _read_csv(path):
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def _read_jsonl(path, problems=None):
    """JSON objects, one per line. Lines that are not JSON objects are skipped and counted."""
    rows = []
    bad = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    bad += 1
                    continue
                if isinstance(obj, dict):
                    rows.append(obj)
                else:
                    bad += 1
    if problems is not None:
        problems.append(bad)
    return rows


def _str(value):
    return value.strip() if isinstance(value, str) and value.strip() else None


def _int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return int(value) if isinstance(value, str) and value.strip().isdigit() else None


def _safe_child(base, rel):
    """base/rel for a relative path that stays inside base; None otherwise."""
    rel = _str(rel)
    if rel is None:
        return None
    try:
        p = pathlib.PurePosixPath(rel.replace("\\", "/"))
        if p.is_absolute() or ".." in p.parts or re.match(r"^[A-Za-z]:", rel):
            return None
        return base / pathlib.Path(*p.parts)
    except (TypeError, ValueError):
        return None


def _local(repo, rel):
    if not rel:
        return None
    p = pathlib.Path(rel)
    return p if p.is_absolute() else repo / rel


def load_job_sources(index, repo, cache_roots=(), exclude_jobs=()):
    """Every jobs/*/output/SOURCES.jsonl (the shared source-record format)."""
    for path in sorted((repo / "jobs").glob("*/output/SOURCES.jsonl")):
        job = path.parent.parent.name
        if job in exclude_jobs:
            continue
        out_dir = path.parent
        roots = [out_dir.parent / f"{job}-cache", out_dir.parent.parent / f"{job}-cache"]
        for r in cache_roots:
            roots += [pathlib.Path(r), pathlib.Path(r) / f"{job}-cache"]
        n, skipped, bad_paths, local_found = 0, 0, 0, 0
        try:
            bad_lines = []
            records = _read_jsonl(path, bad_lines)
        except OSError as exc:
            index.notes.append(f"jobs/{job}/output/SOURCES.jsonl: unreadable ({type(exc).__name__}); skipped")
            continue
        for rec in records:
            try:
                sha = sha_hex(rec.get("sha256"))
                if not sha:
                    skipped += 1
                    continue
                text = _safe_child(out_dir, rec.get("text_path"))
                if rec.get("text_path") is not None and text is None:
                    bad_paths += 1
                local = None
                cache_rel = rec.get("cache_path")
                if cache_rel is not None and _str(cache_rel) is None:
                    bad_paths += 1
                for root in (roots + [out_dir]) if _str(cache_rel) else []:
                    cand = _safe_child(root, cache_rel)
                    if cand is None:
                        bad_paths += 1
                        break
                    if cand.is_file():
                        local = cand
                        break
                ids = rec.get("instrument_ids")
                index.add(HeldCopy(f"jobs/{job}/output/SOURCES.jsonl", sha, rec.get("url"),
                                   _int(rec.get("bytes")), local, text, (), rec.get("page_or_item"),
                                   ids if isinstance(ids, list) else [], rec.get("route") or "",
                                   custody="job_cache" if local is not None else "record_only"))
                n += 1
                local_found += local is not None
            except (TypeError, ValueError, AttributeError, OSError):
                skipped += 1
        note = f"jobs/{job}/output/SOURCES.jsonl: {n} source records ({local_found} with saved bytes on this machine)"
        if bad_lines[0] or skipped or bad_paths:
            note += (f"; ignored {bad_lines[0]} non-object/non-JSON lines, {skipped} records without a usable sha256,"
                     f" {bad_paths} unusable text_path/cache_path values")
        index.notes.append(note)


def lfs_pointer_oid(path):
    """The sha256 a Git LFS pointer file names (the committed bytes' hash), or None."""
    try:
        text = path.read_text("utf-8", "replace")
    except OSError:
        return None
    m = re.search(r"^oid sha256:([0-9a-f]{64})$", text, re.M)
    return m.group(1) if m else None


def _source_book_records(obj):
    """Every {'pdf': 'releases/...', 'pdf_sha256': ...} record in a job's PROVENANCE.json (any nesting)."""
    if isinstance(obj, dict):
        if isinstance(obj.get("pdf"), str) and sha_hex(obj.get("pdf_sha256")):
            yield obj
        for v in obj.values():
            yield from _source_book_records(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _source_book_records(v)


def load_source_books(index, repo, exclude_jobs=()):
    """Printed volumes committed under releases/ (Git LFS) that a job's data/PROVENANCE.json names by sha256.

    A volume counts as committed only when the file is in the checkout and either is that file (re-hashed when a
    claim cites it) or is an LFS pointer whose oid is exactly that sha256. The job's per-order OCR texts
    (original_representation fragments citing the volume, with a text_path) are added as text copies of the same
    bytes, listed before the volume so quotations are searched in them before the whole PDF is ever parsed."""
    for prov in sorted((repo / "jobs").glob("*/data/PROVENANCE.json")):
        job = prov.parent.parent.name
        if job in exclude_jobs:
            continue
        try:
            data = json.loads(prov.read_text("utf-8"))
        except (OSError, ValueError):
            index.notes.append(f"jobs/{job}/data/PROVENANCE.json: unreadable; its volumes are not indexed")
            continue
        books = {}
        for rec in _source_book_records(data):
            rel = _safe_child(repo, rec["pdf"])
            sha = sha_hex(rec["pdf_sha256"])
            if rel is None or not rec["pdf"].replace("\\", "/").startswith("releases/"):
                continue
            if not rel.is_file():
                index.notes.append(f"jobs/{job}: {rec['pdf']} is not in this checkout (add releases/source_books to "
                                   "needs.txt); not indexed")
                continue
            if is_lfs_pointer(rel):
                oid = lfs_pointer_oid(rel)
                if oid != sha:
                    index.notes.append(f"jobs/{job}: {rec['pdf']} is an LFS pointer to {str(oid)[:12]}..., not the "
                                       f"recorded {sha[:12]}...; not indexed")
                    continue
            books[sha] = (rel, rec)
        if not books:
            continue
        texts = 0
        frag_path = repo / "jobs" / job / "output" / "FRAGMENTS.jsonl"
        if frag_path.is_file():
            with open(frag_path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if '"original_representation"' not in line:
                        continue
                    try:
                        f = json.loads(line)
                    except ValueError:
                        continue
                    d = f.get("data") if isinstance(f, dict) else None
                    if f.get("kind") != "original_representation" or not isinstance(d, dict):
                        continue
                    sha = sha_hex(d.get("sha256"))
                    text = _safe_child(frag_path.parent, d.get("text_path"))
                    if sha not in books or text is None or not isinstance(f.get("instrument_id"), str):
                        continue
                    index.add(HeldCopy(f"jobs/{job}/output/FRAGMENTS.jsonl", sha, d.get("url"),
                                       _int(books[sha][1].get("pdf_bytes")), None, text, (), d.get("page_or_item"),
                                       [f["instrument_id"]], "per-order OCR text of a committed volume",
                                       custody="repo_file"))
                    texts += 1
        for sha, (path, rec) in books.items():
            index.add(HeldCopy(f"jobs/{job}/data/PROVENANCE.json", sha, rec.get("handle_url") or rec.get("url"),
                               _int(rec.get("pdf_bytes")), path, None, (), None, (), "committed volume (Git LFS)",
                               custody="repo_file"))
        index.notes.append(f"jobs/{job}: {len(books)} committed volume(s) and {texts} per-order text(s) indexed")


def load_stage21(index, repo):
    p = repo / INPUTS["stage21_custody"]
    if p.is_file():
        for r in _read_csv(p):
            sha = sha_hex(r.get("sha256_source_bytes_if_present"))
            if sha:
                index.add(HeldCopy("stage21_custody", sha, r.get("official_PDF_candidate_URL"),
                                   int(r["bytes"]) if (r.get("bytes") or "").isdigit() else None,
                                   _local(repo, r.get("source_repository_path")),
                                   instrument_ids=[r.get("instrument_id")],
                                   note=r.get("custody_state", "")))
    else:
        index.notes.append(f"missing {INPUTS['stage21_custody']}")
    p = repo / INPUTS["stage21_acquisition_log"]
    if p.is_file():
        for r in _read_jsonl(p):
            sha = sha_hex(r.get("sha256"))
            if sha:
                index.add(HeldCopy("stage21_acquisition_log", sha, r.get("requested_url"),
                                   _int(r.get("bytes")), _local(repo, r.get("repository_path")),
                                   instrument_ids=[r.get("instrument_id")],
                                   note=r.get("custody_state", "")))
    else:
        index.notes.append(f"missing {INPUTS['stage21_acquisition_log']}")


def load_stage20(index, repo):
    p = repo / INPUTS["stage20_statutes"]
    if p.is_file():
        for r in _read_csv(p):
            sha = sha_hex(r.get("sha256"))
            if sha:
                ids = [x.strip() for x in (r.get("case_ids_mentioned") or "").split("|") if x.strip()]
                index.add(HeldCopy("stage20_statute_fetch_index", sha, r.get("source_url"),
                                   int(r["bytes"]) if (r.get("bytes") or "").isdigit() else None,
                                   _local(repo, r.get("local_relpath")),
                                   page_or_item=r.get("citation"), instrument_ids=ids))
    else:
        index.notes.append(f"missing {INPUTS['stage20_statutes']}")
    p = repo / INPUTS["stage20_opus_media"]
    if p.is_file():
        media_zip = repo / OPUS_MEDIA_ZIP
        for r in _read_csv(p):
            sha = sha_hex(r.get("sha256"))
            if sha:
                ids = [x.strip() for x in (r.get("candidate_case_ids_from_directory_only") or "").split("|") if x.strip()]
                index.add(HeldCopy("opus_media_member_map", sha, None,
                                   int(r["bytes"]) if (r.get("bytes") or "").isdigit() else None,
                                   zip_members=[(media_zip, r.get("companion_member"))],
                                   page_or_item=r.get("manifest_path"), instrument_ids=ids,
                                   custody="opus_release"))
    else:
        index.notes.append(f"missing {INPUTS['stage20_opus_media']}")


def load_stage18(index, repo):
    """Stage 18 SOURCE_MANIFEST.json: register every hash whose bytes were kept locally."""
    p = repo / INPUTS["stage18_manifest"]
    if not p.is_file():
        index.notes.append(f"missing {INPUTS['stage18_manifest']}")
        return
    base = p.parent
    try:
        data = json.loads(p.read_text("utf-8", "replace"))
    except (OSError, ValueError) as exc:
        index.notes.append(f"{INPUTS['stage18_manifest']} unreadable ({type(exc).__name__}); skipped")
        return

    def walk(obj):
        if isinstance(obj, dict):
            for key, val in obj.items():
                sha = sha_hex(val) if key.endswith("sha256") else None
                if sha:
                    stem = key[: -len("sha256")].rstrip("_")
                    local = obj.get(stem) if stem else (obj.get("local_file") or obj.get("local_path"))
                    lp = _safe_child(base, local) if isinstance(local, str) else None
                    if lp is not None:
                        url = obj.get("source_url") or obj.get("url") or obj.get("pdf_url") or obj.get("issue_url")
                        index.add(HeldCopy("stage18_source_manifest", sha, url,
                                           _int(obj.get(f"{stem}_bytes") or obj.get("bytes")),
                                           lp if lp.is_file() else _safe_child(repo, local),
                                           note="excerpt of the URL's document" if stem == "local_excerpt" else ""))
                walk(val)
        elif isinstance(obj, list):
            for x in obj:
                walk(x)

    walk(data)


# ---------- Opus release manifest ----------

INDEX_FIELDS = ["kind", "sha256", "bytes", "path", "url", "text_path"]


def opus_index_rows_from_zip(zip_path):
    """Rows for the Opus index, read from the complete Opus zip (deterministic order)."""
    rows = []
    with zipfile.ZipFile(zip_path) as z:
        manifest = json.loads(z.read(OPUS_PREFIX + "MANIFEST.json"))
        files = manifest["files"]
        by_path = {f["path"]: f for f in files}
        paths_of_sha = {}
        for f in files:
            paths_of_sha.setdefault(f["sha256"], []).append(f["path"])
        for f in files:
            rows.append({"kind": "file", "sha256": f["sha256"], "bytes": str(f["bytes"]),
                         "path": f["path"], "url": "", "text_path": ""})
        names = set(z.namelist())
        for f in files:
            path = f["path"]
            if not path.endswith(".json") or f["bytes"] > 50000 or OPUS_PREFIX + path not in names:
                continue
            try:
                meta = json.loads(z.read(OPUS_PREFIX + path))
            except (ValueError, KeyError):
                continue
            if not isinstance(meta, dict):
                continue
            sha = sha_hex(meta.get("sha256"))
            url = meta.get("final_url") or meta.get("url")
            if not sha or not isinstance(url, str) or not url.startswith("http"):
                continue
            stem = path[: -len(".meta.json")] if path.endswith(".meta.json") else path[: -len(".json")]
            original = next((p for p in sorted(paths_of_sha.get(sha, [])) if p != path), "")
            text = stem + ".txt" if stem + ".txt" in by_path and stem + ".txt" != original else ""
            rows.append({"kind": "meta", "sha256": sha, "bytes": str(meta.get("bytes") or ""),
                         "path": original, "url": url, "text_path": text})
    rows.sort(key=lambda r: (r["kind"], r["path"], r["sha256"], r["url"]))
    return rows, manifest.get("built_utc")


def load_opus(index, repo, job_dir):
    complete = repo / OPUS_COMPLETE_ZIP
    media = repo / OPUS_MEDIA_ZIP
    rows = None
    if complete.is_file() and not is_lfs_pointer(complete):
        try:
            rows, _ = opus_index_rows_from_zip(complete)
            index.notes.append("Opus manifest read from the complete Opus zip on this machine")
        except (OSError, zipfile.BadZipFile, KeyError, ValueError) as exc:
            index.notes.append(f"Opus zip present but unreadable ({exc}); using committed index")
    if rows is None:
        committed = job_dir / "data" / "opus_manifest_index.csv.gz"
        if committed.is_file():
            with gzip.open(committed, "rt", encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            index.notes.append("Opus manifest read from the committed index data/opus_manifest_index.csv.gz "
                               "(the Opus zip itself is not on this machine; Opus texts come only from the "
                               "committed text pack data/opus_text_pack.jsonl.gz)")
        else:
            index.notes.append("no Opus manifest available (zip absent and no committed index)")
            return
    load_opus_text_pack(index, job_dir)
    for r in rows:
        sha = sha_hex(r.get("sha256"))
        if not sha:
            continue
        members = []
        if r.get("path"):
            members = [(complete, OPUS_PREFIX + r["path"]), (media, OPUS_PREFIX + r["path"])]
        text = (complete, OPUS_PREFIX + r["text_path"]) if r.get("text_path") else None
        index.add(HeldCopy("opus_stage11_manifest" if r["kind"] == "file" else "opus_stage11_fetch_meta",
                           sha, r.get("url") or None,
                           int(r["bytes"]) if (r.get("bytes") or "").isdigit() else None,
                           None, text, members, r.get("path") or None,
                           note="" if r.get("path") else "Opus kept the hash and extracted text, not the original bytes",
                           custody="opus_release" if r.get("path") else "record_only"))


TEXT_PACK = "data/opus_text_pack.jsonl.gz"


def load_opus_text_pack(index, job_dir):
    """Committed texts of the Opus sources that claims cite (built on the PC by build_opus_index.py
    --text-pack), so the GitHub run, which has no Opus zip, can still check their quotations."""
    override = os.environ.get("CLAIM_CHECKER_TEXT_PACK", "").strip()  # for trying out a pack built elsewhere
    p = pathlib.Path(override) if override else pathlib.Path(job_dir) / TEXT_PACK
    if not p.is_file():
        index.notes.append(f"no Opus text pack ({TEXT_PACK}); Opus-only quotations need the Opus zip")
        return
    n = 0
    try:
        with gzip.open(p, "rt", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                sha = sha_hex(rec.get("sha256")) if isinstance(rec, dict) else None
                pages = rec.get("pages") if sha else None
                if sha and isinstance(pages, list) and all(isinstance(x, str) for x in pages):
                    index.packed_texts[sha] = (pages, f"opus_text_pack:{rec.get('how') or 'text'}")
                    n += 1
    except (OSError, EOFError, ValueError) as exc:
        index.notes.append(f"Opus text pack unreadable ({type(exc).__name__}); ignored")
        return
    index.notes.append(f"Opus text pack: texts of {n} cited Opus sources")


def build_index(repo, job_dir, cache_roots=(), exclude_jobs=()):
    repo = pathlib.Path(repo)
    index = HeldIndex()
    load_job_sources(index, repo, cache_roots, exclude_jobs)
    load_source_books(index, repo, exclude_jobs)
    load_stage21(index, repo)
    load_stage20(index, repo)
    load_stage18(index, repo)
    load_opus(index, repo, pathlib.Path(job_dir))
    return index


# ---------- reading saved bytes and text ----------

class _HTMLText(html.parser.HTMLParser):
    SKIP = {"script", "style", "noscript"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "pre"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(raw):
    p = _HTMLText()
    p.feed(raw)
    p.close()
    return html.unescape("".join(p.parts))


def pdf_pages(data):
    """Text of each PDF page using pypdf, or raise ImportError if pypdf is not installed."""
    import logging

    import pypdf  # pinned in requirements.txt

    logging.getLogger("pypdf").setLevel(logging.ERROR)  # font warnings are noise here
    reader = pypdf.PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as exc:  # a broken page must not stop the run
            pages.append("")
            print(f"  warning: pypdf could not read a page: {exc}")
    return pages


IMAGE_MAGIC = (b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"II*\x00", b"MM\x00*")


def bytes_to_pages(data):
    """(pages, how) for saved bytes. pages is None when there is no text layer."""
    head = data[:1024].lstrip()
    if data[:5] == b"%PDF-":
        try:
            pages = pdf_pages(data)
        except ImportError:
            return None, "pdf_but_pypdf_not_installed"
        if not any(p.strip() for p in pages):
            return None, "pdf_without_text_layer (scan; OCR not attempted)"
        return pages, "pdf_text_layer_pypdf"
    if data.startswith(IMAGE_MAGIC):
        return None, "image_without_text_layer (OCR not attempted)"
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    if head[:1] == b"<" and re.search(rb"<(html|body|p|div|title|!doctype)", head, re.I):
        return [html_to_text(text)], "html_text"
    if head[:1] == b"<":
        return [re.sub(r"<[^>]+>", " ", html.unescape(text))], "xml_text_tags_removed"
    return [text], "plain_text"


class TextReader:
    """Reads (and caches) the bytes and text of held copies."""

    MAX_TEXTS_IN_MEMORY = 256  # extracted texts are also cached on disk, per sha256

    def __init__(self, cache_dir=None, packed=None):
        self.cache_dir = pathlib.Path(cache_dir) if cache_dir else None
        self.packed = packed or {}
        self._sha_of_path = {}
        self._zip_ok = {}
        self._texts = collections.OrderedDict()
        self._pages_by_sha = collections.OrderedDict()

    def _remember(self, store, key, value):
        store[key] = value
        store.move_to_end(key)
        while len(store) > self.MAX_TEXTS_IN_MEMORY:
            store.popitem(last=False)

    def _zip_usable(self, zpath):
        if zpath not in self._zip_ok:
            self._zip_ok[zpath] = zpath.is_file() and not is_lfs_pointer(zpath) and zipfile.is_zipfile(zpath)
        return self._zip_ok[zpath]

    def local_sha(self, path):
        """SHA-256 of a local file, or None if it is not readable here."""
        if path is None or not path.is_file() or is_lfs_pointer(path):
            return None
        key = str(path)
        if key not in self._sha_of_path:
            self._sha_of_path[key] = file_sha256(path)
        return self._sha_of_path[key]

    def read_bytes(self, copy):
        """(bytes, where) for a copy, or (None, reason)."""
        if copy.local_path is not None and copy.local_path.is_file() and not is_lfs_pointer(copy.local_path):
            return copy.local_path.read_bytes(), str(copy.local_path)
        for zpath, member in copy.zip_members:
            if member and self._zip_usable(zpath):
                try:
                    with zipfile.ZipFile(zpath) as z:
                        return z.read(member), f"{zpath.name}:{member}"
                except KeyError:
                    continue
        if copy.zip_members:
            return None, "bytes only inside the Opus LFS release, not downloaded on this machine"
        if copy.local_path is not None:
            return None, f"saved file not on this machine ({copy.local_path.name})"
        return None, "no local copy recorded"

    def verify_bytes(self, copy):
        """True/False if the saved bytes are here and (do not) hash to the record; None if not here."""
        if copy.local_path is not None:
            sha = self.local_sha(copy.local_path)
            if sha is not None:
                return sha == copy.sha256
        for zpath, member in copy.zip_members:
            if not member or not self._zip_usable(zpath):
                continue
            key = f"{zpath}:{member}"
            if key not in self._sha_of_path:
                try:
                    with zipfile.ZipFile(zpath) as z:
                        h = hashlib.sha256()
                        with z.open(member) as fh:
                            for chunk in iter(lambda: fh.read(1 << 20), b""):
                                h.update(chunk)
                    self._sha_of_path[key] = h.hexdigest()
                except KeyError:
                    continue
            return self._sha_of_path[key] == copy.sha256
        return None

    def _cached(self, sha):
        if not self.cache_dir:
            return None
        p = self.cache_dir / "text" / f"{sha}.json"
        if p.is_file():
            try:
                d = json.loads(p.read_text("utf-8"))
                return d["pages"], d["how"]
            except (ValueError, KeyError):
                return None
        return None

    def _store(self, sha, pages, how):
        if not self.cache_dir or pages is None:
            return
        p = self.cache_dir / "text" / f"{sha}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"pages": pages, "how": how}, ensure_ascii=False), "utf-8")

    def texts(self, copy):
        """List of (pages, how) text versions of a held copy; may be empty, with a reason."""
        key = (copy.origin, copy.sha256, str(copy.text_path), str(copy.local_path))
        if key in self._texts:
            self._texts.move_to_end(key)
            return self._texts[key]
        out, reasons = [], []
        # 1. Extracted text recorded alongside the source (job SOURCES.jsonl text_path, Opus .txt).
        tp = copy.text_path
        if isinstance(tp, tuple):
            zpath, member = tp
            if self._zip_usable(zpath):
                try:
                    with zipfile.ZipFile(zpath) as z:
                        out.append(([z.read(member).decode("utf-8", "replace")], "opus_extracted_text"))
                except KeyError:
                    reasons.append("Opus text member missing")
            else:
                reasons.append("Opus text only inside the LFS release, not downloaded here")
        elif tp is not None:
            if tp.is_file() and not is_lfs_pointer(tp):
                out.append(([tp.read_text("utf-8", "replace")], "recorded_text_path"))
            else:
                reasons.append("recorded text_path not on this machine")
        # 2. Our own extraction from the saved bytes (after checking their hash).
        cached = self._pages_by_sha.get(copy.sha256) or self._cached(copy.sha256)
        if cached:
            self._remember(self._pages_by_sha, copy.sha256, cached)
            out.append(cached)
        else:
            data, where = self.read_bytes(copy)
            if data is None:
                reasons.append(where)
            elif hashlib.sha256(data).hexdigest() != copy.sha256:
                reasons.append(f"saved bytes at {where} do not hash to the record; text not used")
            else:
                pages, how = bytes_to_pages(data)
                if pages is None:
                    reasons.append(how)
                else:
                    self._store(copy.sha256, pages, how)
                    self._remember(self._pages_by_sha, copy.sha256, (pages, how))
                    out.append((pages, how))
        # 3. The committed Opus text pack (GitHub runs, where the Opus zip is absent).
        if not out and copy.sha256 in self.packed:
            out.append(self.packed[copy.sha256])
        result = (out, "; ".join(reasons))
        self._remember(self._texts, key, result)
        return result
