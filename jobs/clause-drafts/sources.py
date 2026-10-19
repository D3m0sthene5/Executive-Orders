"""Find saved original texts of executive orders and describe their custody.

Three kinds of input, all read-only:

* Stage 21 original PDFs (research/stage21/original_sources/*.pdf) listed in
  CASE_ORIGINAL_SOURCE_CUSTODY.csv. Text is extracted here with pypdf.
* Text extractions inside the Opus Stage 11 release zip (each with a
  ``.meta.json`` that records the URL and SHA-256 of the original bytes).
  Zip members are read one at a time; the zip is never unpacked.
* SOURCE RECORDS (SOURCES.jsonl) written by other jobs, e.g.
  jobs/fr-originals/output/ and jobs/source-ladder/output/, whose
  ``text_path`` points at extracted text inside that job's output folder.
* American Presidency Project pages harvested by jobs/app-executive-orders/
  (DOCUMENTS.jsonl live, MIRROR_DOCUMENTS.jsonl web-archive captures). These are
  TRANSCRIPTIONS, never originals: a fallback draft input used only when no other
  copy of the order gives a usable draft (see app_job_candidates).

Every candidate keeps: url (https), sha256 + bytes of the ORIGINAL bytes,
retrieval time, content type, route (how it was found) and a grade.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import re
import subprocess
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import segment as S

GRADE_RANK = {
    "official_fr_pdf_text_layer": 0,       # born-digital GovInfo FR PDF (1994+), text layer
    "official_fr_html_text": 1,            # GovInfo FR HTML rendition (/html/...htm) of the same document
    "federalregister_gov_edition": 2,      # FederalRegister.gov text (not the official legal edition)
    "mirror_transcription_app": 3,         # American Presidency Project transcription (reputable mirror)
    "official_fr_scan_ocr_text": 4,        # GovInfo scan of an old FR issue; OCR text (noisy)
    "other_copy": 5,
}
# Text near the top of a saved web page that means it is an error or block page, not a document.
ERROR_PAGE = re.compile(
    r"(?i)\b404\b[^\n]{0,40}(?:not\s+found|error)|page\s+not\s+found|access\s+denied|just\s+a\s+moment\.\.\.|"
    r"\bcaptcha\b|request\s+rejected|are\s+you\s+a\s+robot|service\s+unavailable"
)
APP_SUFFIX = " | The American Presidency Project"
APP_TITLE_EO = re.compile(r"^\s*Executive\s+Order\s+(?:No\.\s*)?(\d{1,5})(?:\s*[-‐–]\s*([A-Z])\b|([A-Z])\b)?")
APP_CHROME = re.compile(r"(?m)^\s*(?:Skip to main content|Toggle navigation)\s*$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
FALLBACK_RANK = 20
APP_JOB = "app-executive-orders"
APP_RECORDS = (("DOCUMENTS.jsonl", "live"), ("MIRROR_DOCUMENTS.jsonl", "archive"))
APP_HEADING_EO = re.compile(r"\s*Executive\s+Order\s+(?:No\.\s*)?\d+(?:\s*[-‐–]\s*[A-Z]\b|[A-Z]\b)?\s*(?:[—–:-]|$)")
APP_TEXT_PATH = re.compile(r"texts/[A-Za-z0-9._-]+\.txt")
OPUS_ZIP = "releases/opus_stage11_complete/OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip"
STAGE21_DIR = "research/stage21/original_sources"
CROSSWALK = "research/stage21/sources_index/OFFICIAL_SOURCE_CASE_CROSSWALK.csv"


@dataclass
class Candidate:
    instrument_id: str
    number: str
    origin: str                 # "stage21" | "opus_zip" | "job:<name>"
    route: str
    url: str
    sha256: str
    bytes: int | None
    content_type: str
    retrieved_utc: str
    grade: str
    page_or_item: str
    locator: str                # zip member / file path the text came from
    body_only_ok: bool = False  # identity known from URL; text may lack a heading
    fr_volume: str | None = None
    fr_start_page: int | None = None
    notes: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def rank(self):
        # Fallback-only inputs (APP transcriptions from app-executive-orders) are tried after every other copy.
        return GRADE_RANK.get(self.grade, 9) + (FALLBACK_RANK if self.extra.get("fallback_only") else 0)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def grade_for_url(url: str) -> str | None:
    """Grade a source by where its bytes came from; None means 'not an order text source'."""
    p = urlparse(url or "")
    host, path = p.netloc.lower(), p.path
    if p.scheme != "https":
        return None
    if host.endswith("presidency.ucsb.edu") and path.startswith("/documents/"):
        return "mirror_transcription_app"
    if host.endswith("govinfo.gov") and ("/FR-" in path or "/link/fr" in path.lower() or "/pkg/FR" in path):
        m = re.search(r"FR-(\d{4})-", path)
        if m and int(m.group(1)) >= 1994:
            if "/html/" in path or path.lower().endswith((".htm", ".html")):
                return "official_fr_html_text"
            return "official_fr_pdf_text_layer"
        return "official_fr_scan_ocr_text"
    if host.endswith("federalregister.gov") and "/api/" not in path and (
        path.startswith("/documents/") or path.startswith("/d/") or "full_text" in path
    ):
        return "federalregister_gov_edition"
    return None


def issue_year(url: str) -> int | None:
    """Publication year of an FR issue/document from its URL, if the URL shows it."""
    m = re.search(r"/FR-(\d{4})-\d{2}-\d{2}/", url or "") or re.search(r"federalregister\.gov/(?:documents|d)/(\d{4})/", url or "")
    return int(m.group(1)) if m else None


def app_number_from_url(url: str, universe: set | None = None) -> str | None:
    """Order number in an American Presidency Project address.

    A one-letter word after the number ("...-6513-j-amendments") is read as a
    suffix only when the universe really has that suffixed order; otherwise it
    is an initial in the title ("...-11669-j-edgar-hoover" is EO 11669)."""
    m = re.search(r"/documents/executive-order-(\d{1,5})(?:-?([a-z]))?(?:-|$)", url or "")
    if not m:
        return None
    digits, suf = m.group(1), (m.group(2) or "").upper()
    if suf and (not universe or to_instrument_id(digits + "-" + suf, universe)):
        return digits + "-" + suf
    return digits


def number_digits(number: str | None) -> str:
    m = re.match(r"0*(\d+)", number or "")
    return m.group(1) if m else ""


def app_page_identity(text: str):
    """Which order an American Presidency Project text is about, from the page itself.

    Returns (number or None, basis, flags). basis is "page_title" (the HTML title
    line "Executive Order 4359-A—... | The American Presidency Project"),
    "first_line_heading" (a body extract whose first line is the order's own
    heading), "not_an_order_page" (the title names a statement, proclamation,
    error page ...), or "body_only" (no title or heading: identity can only come
    from the web address)."""
    first = next((l.strip() for l in text.split("\n") if l.strip()), "")
    if APP_SUFFIX.strip() in first:
        title = first.split(" | ", 1)[0]
        m = APP_TITLE_EO.match(title)
        if not m:
            return None, "not_an_order_page", ["app_page_title_is_not_an_executive_order:" + title[:60]]
        suf = m.group(2) or m.group(3) or ""
        return m.group(1) + ("-" + suf if suf else ""), "page_title", []
    m = APP_TITLE_EO.match(first)
    if m and re.match(r"\s*Executive\s+Order\s+(?:No\.\s*)?\d+(?:\s*[-‐–]\s*[A-Z]\b|[A-Z]\b)?\s*(?:[—–:-]|$)", first):
        suf = m.group(2) or m.group(3) or ""
        return m.group(1) + ("-" + suf if suf else ""), "first_line_heading", []
    return None, "body_only", []


def to_instrument_id(number: str, universe: set) -> str | None:
    """Map '4359-A' / '12944' to an id that exists in the universe (or plain if no universe)."""
    number = number.strip()
    m = re.fullmatch(r"(\d+)(?:-?([A-Za-z]))?", number)
    if not m:
        return None
    digits = str(int(m.group(1)))
    suf = (m.group(2) or "").upper()
    options = [f"EO:{digits}{suf}", f"EO:{digits}-{suf}"] if suf else [f"EO:{digits}"]
    if not universe:
        return options[0]
    for o in options:
        if o in universe:
            return o
    return None


# ---------------------------------------------------------------------------
# Stage 21 PDFs
# ---------------------------------------------------------------------------


def pdf_text(data: bytes):
    """Extract text page by page with pypdf; drop page furniture lines.

    Returns (text, page_starts, raw_first_page). page_starts[i] is the offset of
    PDF page i+1 in ``text``.
    """
    import pypdf  # pinned in requirements.txt

    logging.getLogger("pypdf").setLevel(logging.ERROR)
    reader = pypdf.PdfReader(io.BytesIO(data))
    parts, starts, pos = [], [], 0
    raw_first = ""
    for i, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        if i == 0:
            raw_first = raw
        lines = [l.rstrip() for l in raw.split("\n")]
        kept = [l for l in lines if not S.is_furniture(l)]
        page_text = "\n".join(kept).strip("\n")
        starts.append(pos)
        parts.append(page_text)
        pos += len(page_text) + 1
    return "\n".join(parts), starts, raw_first


def stage21_candidates(repo: Path, universe: set, log):
    out, problems = [], []
    custody = repo / STAGE21_DIR / "CASE_ORIGINAL_SOURCE_CUSTODY.csv"
    if not custody.exists():
        log(f"Stage 21 custody list not found: {custody}")
        return out, problems
    cross = {}
    cw = repo / CROSSWALK
    if cw.exists():
        with open(cw, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                cross[row["instrument_id"]] = row
    with open(custody, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        iid = row["instrument_id"]
        rel = (row.get("source_repository_path") or "").strip()
        url = row["official_PDF_candidate_URL"]
        if not rel:
            problems.append((iid, "stage21_no_pdf_captured", row.get("retrieval_error") or row.get("custody_state") or ""))
            continue
        path = repo / rel
        if not path.is_file():
            problems.append((iid, "stage21_pdf_missing_locally", rel))
            continue
        data = path.read_bytes()
        if data.startswith(b"version https://git-lfs"):
            problems.append((iid, "stage21_pdf_is_lfs_pointer", str(path)))
            continue
        sha = sha256_bytes(data)
        if row["sha256_source_bytes_if_present"] and sha != row["sha256_source_bytes_if_present"]:
            problems.append((iid, "stage21_pdf_sha256_mismatch", f"{sha} != {row['sha256_source_bytes_if_present']}"))
            continue
        vol = start = None
        cite = (cross.get(iid) or {}).get("FR_citation_from_cached_index", "")
        m = re.match(r"\s*(\d+)\s+FR\s+(\d+)", cite)
        if m:
            vol, start = m.group(1), int(m.group(2))
        number = iid.split(":", 1)[1]
        out.append(Candidate(
            instrument_id=iid, number=number, origin="stage21",
            route="stage21_original_sources_pdf+pypdf_text_layer",
            url=url, sha256=sha, bytes=len(data), content_type="application/pdf",
            retrieved_utc=row.get("attempted_utc", ""), grade=grade_for_url(url) or "other_copy",
            page_or_item=(f"{vol} FR {start}" if vol else "GovInfo FR document PDF"),
            locator=row["source_repository_path"], fr_volume=vol, fr_start_page=start,
            notes="Stage 21 custody state: " + row.get("custody_state", ""),
        ))
    return out, problems


# ---------------------------------------------------------------------------
# Opus Stage 11 release zip
# ---------------------------------------------------------------------------


def ensure_lfs(repo: Path, rel: str, log) -> Path | None:
    path = repo / rel
    if not path.exists():
        return None
    with open(path, "rb") as fh:
        head = fh.read(64)
    if head.startswith(b"version https://git-lfs"):
        log(f"{rel} is a Git LFS pointer; running git lfs pull for it")
        try:
            subprocess.run(["git", "lfs", "pull", "--include", rel], cwd=repo, check=True, timeout=1800)
        except Exception as exc:  # noqa: BLE001
            log(f"git lfs pull failed: {exc}")
            return None
        with open(path, "rb") as fh:
            if fh.read(64).startswith(b"version https://git-lfs"):
                return None
    return path


def _meta_for(member: str, names: set):
    """Find the .meta.json that describes a text member (strip derived suffixes)."""
    base = member[:-4]  # drop .txt
    while True:
        if base + ".meta.json" in names:
            return base + ".meta.json"
        d, _, leaf = base.rpartition("/")
        if "." not in leaf:
            return None
        base = d + "/" + leaf.rsplit(".", 1)[0]


VARIANT_PREF = (".raw.txt", ".norm.txt", ".n.txt")


def _variant_rank(member: str) -> int:
    leaf = member.rsplit("/", 1)[-1]
    if re.search(r"\.(?:lay|layout)\.", leaf) or leaf.endswith((".lay.txt", ".layout.txt")):
        return 9
    for i, suf in enumerate(VARIANT_PREF, 1):
        if leaf.endswith(suf):
            return i
    return 0


def looks_like_columns(text: str) -> bool:
    lines = [l for l in text.split("\n") if l.strip()]
    if len(lines) < 20:
        return False
    wide = sum(1 for l in lines if re.search(r"\S {4,}\S", l.strip()))
    return wide / len(lines) > 0.25


def scan_opus_zip(zpath: Path, universe: set, log, cache_dir: Path | None):
    """Return a list of lightweight entries: dicts with member, meta, numbers, flags."""
    key = None
    if cache_dir:
        st = zpath.stat()
        here = Path(__file__).resolve().parent
        code = sha256_bytes((here / "segment.py").read_bytes() + (here / "sources.py").read_bytes())[:12]
        key = cache_dir / f"opus_scan_{st.st_size}_{int(st.st_mtime)}_{code}.json"
        if key.exists():
            try:
                return json.loads(key.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                pass
    entries = []
    stats = {"text_members": 0, "with_meta": 0, "source_ok": 0, "skipped": {}, "member_text_hash_check": {}}

    def skip(reason):
        stats["skipped"][reason] = stats["skipped"].get(reason, 0) + 1

    with zipfile.ZipFile(zpath) as z:
        names = set(z.namelist())
        texts = sorted(n for n in names if n.endswith(".txt") and "/cache/" in n)
        meta_cache = {}
        for member in texts:
            stats["text_members"] += 1
            meta_name = _meta_for(member, names)
            if not meta_name:
                stats["skipped"]["no_meta"] = stats["skipped"].get("no_meta", 0) + 1
                continue
            stats["with_meta"] += 1
            if meta_name not in meta_cache:
                try:
                    meta_cache[meta_name] = json.loads(z.read(meta_name))
                except Exception:  # noqa: BLE001
                    meta_cache[meta_name] = None
            meta = meta_cache[meta_name]
            if not isinstance(meta, dict):
                stats["skipped"]["bad_meta"] = stats["skipped"].get("bad_meta", 0) + 1
                continue
            url = meta.get("final_url") or meta.get("url") or meta.get("source_url") or ""
            grade = grade_for_url(url) or grade_for_url(meta.get("url") or "")
            if not grade:
                stats["skipped"]["not_an_order_text_host"] = stats["skipped"].get("not_an_order_text_host", 0) + 1
                continue
            sha = str(meta.get("sha256") or "").lower()
            if not HEX64.match(sha):
                stats["skipped"]["no_original_sha256"] = stats["skipped"].get("no_original_sha256", 0) + 1
                continue
            if _variant_rank(member) == 9:
                stats["skipped"]["layout_columns_text"] = stats["skipped"].get("layout_columns_text", 0) + 1
                continue
            info = z.getinfo(member)
            if info.file_size > 6_000_000:
                stats["skipped"]["text_too_large"] = stats["skipped"].get("text_too_large", 0) + 1
                continue
            status = str(meta.get("http_status") if meta.get("http_status") is not None else "").strip()
            if status and status != "200":
                skip(f"http_status_{status}")
                continue
            raw = z.read(member)
            text = raw.decode("utf-8", "replace")
            if ERROR_PAGE.search(text.lstrip()[:2500]) and grade != "official_fr_scan_ocr_text":
                skip("error_or_block_page_text")
                continue
            if looks_like_columns(text):
                skip("layout_columns_text")
                continue
            # Which orders this text is about. An American Presidency Project page is
            # about ONE order: the one in its own title (never a number from its body).
            url_number = app_number_from_url(url, universe) if grade == "mirror_transcription_app" else None
            flags = []
            if grade == "mirror_transcription_app":
                own, basis, flags = app_page_identity(text)
                if basis == "not_an_order_page":
                    skip("app_page_not_an_executive_order")
                    continue
                if own is None:
                    if APP_CHROME.search(text):
                        skip("app_page_without_order_title")
                        continue
                    nums = []  # body-only extract: identity only from the URL (flagged)
                else:
                    nums = [own]
                    if url_number and number_digits(url_number) != number_digits(own):
                        flags.append(f"app_page_title_number_{own}_differs_from_url_number_{url_number}")
            else:
                basis = "headings_in_text"
                nums = sorted({n for n, _ in S.find_headings(text)})
            # Does the zip member match the text hash recorded in its meta file?
            member_sha = sha256_bytes(raw)
            recorded = {str(meta.get(k)).lower() for k in ("text_sha256", "txt_sha256", "raw_txt_sha256", "raw_text_sha256")
                        if isinstance(meta.get(k), str) and HEX64.match(str(meta.get(k)).lower())}
            text_file_leaf = str(meta.get("text_file") or "").replace("\\", "/").rsplit("/", 1)[-1]
            if member_sha in recorded:
                hash_check = "match"
            elif not recorded:
                hash_check = "not_recorded"
            elif text_file_leaf == member.rsplit("/", 1)[-1] or (not text_file_leaf and member == meta_name[:-len(".meta.json")] + ".txt"):
                hash_check = "MISMATCH"
            else:
                hash_check = "recorded_hash_is_for_another_text_variant"
            stats["member_text_hash_check"][hash_check] = stats["member_text_hash_check"].get(hash_check, 0) + 1
            stats["source_ok"] += 1
            nbytes = meta.get("bytes")
            if nbytes in (None, ""):
                nbytes = meta.get("bytes_size")
            entries.append({
                "member": member, "meta_name": meta_name, "url": url, "sha256": sha,
                "bytes": nbytes, "content_type": meta.get("content_type") or "",
                "retrieved_utc": meta.get("retrieved_utc") or "", "grade": grade,
                "numbers": nums, "url_number": url_number, "identity_basis": basis, "identity_flags": flags,
                "variant_rank": _variant_rank(member),
                "member_sha256": member_sha, "member_hash_check": hash_check,
                "pages": meta.get("pages"),
            })
    result = {"entries": entries, "stats": stats}
    if key:
        try:
            key.parent.mkdir(parents=True, exist_ok=True)
            key.write_text(json.dumps(result), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return result


def _fr_item(member: str, url: str, pages) -> str:
    leaf = member.rsplit("/", 1)[-1]
    m = re.search(r"FR-(\d{4}-\d{2}-\d{2})", url)
    issue = f"FR issue {m.group(1)}" if m else "GovInfo FR PDF"
    pm = re.search(r"[._]pp?(\d+)(?:-(\d+))?", leaf)
    if pm:
        a, b = pm.group(1), pm.group(2) or pm.group(1)
        return f"{issue}, PDF pages {a}-{b} (Opus text extract)"
    if pages:
        return f"{issue}, PDF pages {pages} (Opus text extract)"
    return f"{issue}, whole-issue PDF (Opus text extract)"


def first_pdf_page(member: str) -> int:
    """PDF page number of the first page in an Opus text extract (1 for a whole issue)."""
    pm = re.search(r"[._]pp?(\d+)(?:-(\d+))?", member.rsplit("/", 1)[-1])
    return int(pm.group(1)) if pm else 1


def ocr_page_map(text: str):
    """Page starts of a pdftotext extract (pages are separated by form feeds) and a
    CANDIDATE FR page number for each page, read from the printed page numbers.

    Old FR pages print their page number alone on a line or next to the running
    head ("FEDERAL REGISTER, Thursday, July 4, 1940 2471"). OCR misreads some of
    them, so a number is trusted only when most pages agree on one offset
    (FR page = offset + page index). Returns (starts, offset or None)."""
    starts = [0] + [m.end() for m in re.finditer("\f", text)]
    if len(starts) < 2:
        return starts, None
    votes = {}
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(text)
        page = text[s:e]
        zone = page[:500] + "\n" + page[-300:]
        nums = set(re.findall(r"(?m)^[ \t]*(\d{2,5})[ \t]*$", zone))
        nums |= set(re.findall(r"(?mi)R\s?E\s?G\s?I\s?S\s?T\s?E\s?R\b[^\n]{0,40}\d{4}[ \t]+(\d{2,5})[ \t]*$", zone))
        nums |= set(re.findall(r"(?mi)^[ \t]*(\d{2,5})[ \t]+F\s?E\s?D\s?E\s?R\s?A\s?L\s+R\s?E\s?G", zone))
        for n in nums:
            d = int(n) - i
            if d > 0:
                votes[d] = votes.get(d, 0) + 1
    if not votes:
        return starts, None
    d, n = max(votes.items(), key=lambda kv: (kv[1], -kv[0]))
    if n >= 3 and n >= 0.4 * len(starts):
        return starts, d
    return starts, None


def ocr_page_label(starts, offset, a: int, b: int, year: int | None, first_pdf: int = 1) -> str | None:
    """'5 FR 2470-2471 (candidate page from OCR page numbers; PDF pp. 4-5)' for offsets [a, b)."""
    if len(starts) < 2:
        return None
    pa = max(i for i, p in enumerate(starts) if p <= a)
    pb = max(i for i, p in enumerate(starts) if p <= max(a, b - 1))
    pdf = f"PDF p. {pa + first_pdf}" if pa == pb else f"PDF pp. {pa + first_pdf}-{pb + first_pdf}"
    if offset is None:
        return pdf
    fa, fb = offset + pa, offset + pb
    vol = f"{year - 1935} FR " if year and year >= 1936 else "FR p. "
    fr = f"{vol}{fa}" if fa == fb else f"{vol}{fa}-{fb}"
    return f"{fr} (candidate FR page read from OCR page numbers; {pdf})"


def opus_candidates(scan: dict, universe: set):
    """One candidate per (text, order). A web page gives only the order in its own
    title (or, for a body-only extract, the order in its URL, flagged so that
    the build quarantines it); an FR text gives every order heading it prints."""
    out = []
    for e in scan["entries"]:
        nums = set(e["numbers"])
        url_only = False
        if e["grade"] == "mirror_transcription_app" and not nums and e["url_number"]:
            nums = {e["url_number"]}
            url_only = True
        for num in sorted(nums):
            iid = to_instrument_id(num, universe)
            if not iid:
                continue
            flags = list(e.get("identity_flags") or [])
            if url_only:
                flags.append("no_heading_in_text_identity_from_source_url_only")
            if e["grade"] == "mirror_transcription_app":
                item = "American Presidency Project web page (transcription; not an official edition)"
            elif e["grade"] == "federalregister_gov_edition":
                item = "FederalRegister.gov document text (not the official legal edition)"
            else:
                item = _fr_item(e["member"], e["url"], e.get("pages"))
            try:
                nbytes = int(e["bytes"]) if e["bytes"] not in (None, "") else None
            except (TypeError, ValueError):
                nbytes = None
            out.append(Candidate(
                instrument_id=iid, number=iid.split(":", 1)[1], origin="opus_zip",
                route="opus_stage11_release_zip_text:" + e["member"].split("/evidence/", 1)[-1],
                url=e["url"], sha256=e["sha256"], bytes=nbytes, content_type=e["content_type"],
                retrieved_utc=e["retrieved_utc"], grade=e["grade"], page_or_item=item,
                locator=e["member"],
                body_only_ok=url_only,
                notes=("text extracted by Opus (see meta: " + e["meta_name"].rsplit("/", 1)[-1] + "); "
                       + ("" if nbytes is not None else "original byte count not recorded by Opus; ")
                       + "original bytes not stored in repo; sha256 not re-verifiable here (re-fetch the url to check it)"),
                extra={"variant_rank": e["variant_rank"], "member_text_sha256": e["member_sha256"],
                       "member_hash_check": e["member_hash_check"], "identity_basis": e.get("identity_basis"),
                       "identity_flags": flags, "url_number": e["url_number"]},
            ))
    return out


# ---------------------------------------------------------------------------
# Other jobs' SOURCE RECORDS
# ---------------------------------------------------------------------------


def job_candidates(repo: Path, job_names, universe: set, log):
    out, problems, seen = [], [], {}
    for name in job_names:
        out_dir = repo / "jobs" / name / "output"
        src = out_dir / "SOURCES.jsonl"
        if not src.exists():
            seen[name] = "no SOURCES.jsonl yet"
            continue
        n = 0
        with open(src, encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    problems.append((f"job:{name}", "bad_json_line", str(line_no)))
                    continue
                url = rec.get("url") or ""
                sha = str(rec.get("sha256") or "").lower()
                ids = [i for i in (rec.get("instrument_ids") or []) if isinstance(i, str) and i.startswith("EO:")]
                tp = rec.get("text_path")
                if not ids or not tp or not HEX64.match(sha) or not url.startswith("https://"):
                    problems.append((",".join(ids) or f"job:{name}", "source_record_unusable", rec.get("source_id", str(line_no))))
                    continue
                text_file = out_dir / tp
                if not text_file.exists():
                    problems.append((",".join(ids), "text_path_missing", str(text_file)))
                    continue
                grade = grade_for_url(url) or "other_copy"
                for iid in ids:
                    if universe and iid not in universe:
                        continue
                    out.append(Candidate(
                        instrument_id=iid, number=iid.split(":", 1)[1], origin=f"job:{name}",
                        route=f"job:{name}:" + str(rec.get("route") or ""),
                        url=url, sha256=sha, bytes=rec.get("bytes"), content_type=rec.get("content_type") or "",
                        retrieved_utc=rec.get("retrieved_utc") or "", grade=grade,
                        page_or_item=str(rec.get("page_or_item") or f"whole saved text of {rec.get('source_id') or url}"),
                        locator=str(text_file),
                        body_only_ok=(len(ids) == 1),
                        notes=f"source_id {rec.get('source_id')} from jobs/{name}/output/SOURCES.jsonl",
                    ))
                    n += 1
        seen[name] = f"{n} order-text candidates"
    return out, problems, seen


# ---------------------------------------------------------------------------
# American Presidency Project pages harvested by app-executive-orders
# ---------------------------------------------------------------------------


def app_job_candidates(repo: Path, universe: set, dates: dict | None = None, log=print):
    """APP order pages (live and web-archive captures) as FALLBACK, transcription-based draft inputs.

    The held APP text is the page body only; the page heading is kept in the record. The draft text is
    the heading line followed by the body, so the order is located by its own heading as for any page.
    Wrong-order protection, as for APP pages in the Opus zip: a page counts only for the order in its
    own heading, never for a number in its body or address. A heading that is not a numbered executive
    order, or names another order than the record, is refused; an address naming another order, or a page
    date more than a year from the census date, gets an identity marker, so the draft is quarantined.
    A record whose text file does not hash to its text_sha256 (the file holds another capture) is refused.
    """
    out, problems, seen = [], [], {}
    out_dir = repo / "jobs" / APP_JOB / "output"
    kept = set()
    for name, lane in APP_RECORDS:
        path = out_dir / name
        if not path.exists():
            seen[name] = "not present"
            continue
        n = 0
        with open(path, encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    problems.append((f"job:{APP_JOB}", "bad_json_line", f"{name}:{line_no}"))
                    continue
                iid = rec.get("instrument_id")
                if not isinstance(iid, str) or (universe and iid not in universe):
                    continue  # unnumbered page or not a census identity: no order to draft
                where = f"{name}:{line_no}"
                url = rec.get("final_url") or rec.get("url") or ""
                sha = str(rec.get("sha256") or "").lower()
                tp, tsha = str(rec.get("text_path") or ""), str(rec.get("text_sha256") or "").lower()
                heading = " ".join(str(rec.get("heading") or "").split())
                if grade_for_url(url) != "mirror_transcription_app" or not HEX64.match(sha):
                    problems.append((iid, "app_record_unusable_no_app_url_or_page_sha256", where))
                    continue
                m = APP_TITLE_EO.match(heading)
                if not m or not APP_HEADING_EO.match(heading):
                    problems.append((iid, "app_heading_is_not_a_numbered_executive_order", f"{where}: {heading[:80]}"))
                    continue
                suf = m.group(2) or m.group(3) or ""
                own = m.group(1) + ("-" + suf if suf else "")
                if to_instrument_id(own, universe) != iid:
                    problems.append((iid, f"app_heading_names_another_order_{own}", where))
                    continue
                text_file = out_dir / tp
                if not APP_TEXT_PATH.fullmatch(tp) or not text_file.is_file():
                    problems.append((iid, "text_path_missing", f"{where}: {tp}"))
                    continue
                if not HEX64.match(tsha) or sha256_file(text_file) != tsha:
                    problems.append((iid, "app_text_file_holds_another_capture", f"{where}: {tp}"))
                    continue
                if (iid, tsha) in kept:
                    continue  # the same text from the other lane
                with open(text_file, encoding="utf-8", errors="replace") as tf:
                    head = tf.read(2500)
                if ERROR_PAGE.search(head.lstrip()):
                    problems.append((iid, "error_or_block_page_text", where))
                    continue
                flags = []
                url_number = app_number_from_url(url, universe)
                if url_number and number_digits(url_number) != number_digits(own):
                    flags.append(f"app_page_title_number_{own}_differs_from_url_number_{url_number}")
                page_year, census_year = str(rec.get("date") or "")[:4], str((dates or {}).get(iid) or "")[:4]
                if page_year.isdigit() and census_year.isdigit() and abs(int(page_year) - int(census_year)) > 1:
                    flags.append(f"identity_doubt_app_page_date_{page_year}_vs_census_year_{census_year}")
                cap = rec.get("capture") if isinstance(rec.get("capture"), dict) else {}
                when = (f"{cap.get('archive')} capture {cap.get('captured_utc')}" if cap
                        else f"live page retrieved {str(rec.get('retrieved_utc') or '')[:10]}")
                kept.add((iid, tsha))
                out.append(Candidate(
                    instrument_id=iid, number=iid.split(":", 1)[1], origin=f"job:{APP_JOB}",
                    route=f"job:{APP_JOB}:{lane}:" + str(rec.get("route") or "live"),
                    url=url, sha256=sha, bytes=rec.get("bytes"), content_type="text/html",
                    retrieved_utc=(cap.get("captured_utc") or rec.get("retrieved_utc") or ""),
                    grade="mirror_transcription_app",
                    page_or_item=(f"American Presidency Project web page (transcription; not an official edition); "
                                  f"APP node {rec.get('app_node')}; {when}"),
                    locator=str(text_file),
                    notes=(f"APP {lane} record {where} in jobs/{APP_JOB}/output; draft text is the APP page heading "
                           f"line, a blank line, then the held body text {tp} (sha256 {tsha[:12]}); "
                           "TRANSCRIPTION-BASED, not an original; the page sha256 is of the page bytes as captured"),
                    extra={"heading_prefix": heading, "fallback_only": True, "transcription_based": True,
                           "identity_basis": "app_page_heading", "identity_flags": flags,
                           "variant_rank": 0 if lane == "live" else 1, "url_number": url_number,
                           "app_text_sha256": tsha},
                ))
                n += 1
        seen[name] = f"{n} order-text candidates"
    return out, problems, seen


# ---------------------------------------------------------------------------
# Loading text for a candidate
# ---------------------------------------------------------------------------


class TextLoader:
    def __init__(self, repo: Path, zpath: Path | None):
        self.repo = repo
        self.zpath = zpath
        self._zip = None
        self._pdf_cache = {}

    def load(self, cand: Candidate):
        """Return (text, page_starts or None)."""
        if cand.origin == "stage21":
            if cand.locator not in self._pdf_cache:
                data = (self.repo / cand.locator).read_bytes()
                text, starts, raw_first = pdf_text(data)
                self._pdf_cache = {cand.locator: (text, starts, raw_first)}
            text, starts, raw_first = self._pdf_cache[cand.locator]
            cand.extra["first_page_raw_numbers"] = re.findall(r"(?m)^\s*(\d{2,6})\s*$", raw_first)[:3]
            return text, starts
        if cand.origin == "opus_zip":
            if self._zip is None:
                self._zip = zipfile.ZipFile(self.zpath)
            return self._zip.read(cand.locator).decode("utf-8", "replace"), None
        with open(cand.locator, encoding="utf-8", errors="replace", newline="") as fh:
            text = fh.read()
        if cand.extra.get("heading_prefix"):
            # APP body texts hold no heading; the page's own heading line identifies the order.
            text = cand.extra["heading_prefix"] + "\n\n" + text
        return text, None

    def close(self):
        if self._zip is not None:
            self._zip.close()
