"""Pothier, source acquisition: fetch the primary sources the family doctrines name but the project does not hold.

Reads every `research/pothier/work/*/FETCH_PROPOSED.jsonl` line (shape of research/readiness/FETCH_QUEUE.jsonl),
fetches each distinct HTTPS URL once with the source ladder's polite client (robots.txt, per-host spacing,
retries), and writes custody records: `output/sources/<sha256>.<ext>` (bytes as served), a text file extracted
from PDFs with pypdf (`output/sources/<sha256>.txt`), and `output/SOURCES.jsonl` (url, final url, sha256, bytes,
content type, retrieval time, text path, the requesting doctrine). Failures are kept in `output/FETCH_FAILURES.jsonl`.

Bounds: at most MAX_URLS distinct URLs and MAX_BYTES per file per run; nothing is fetched outside GitHub Actions
unless POTHIER_FETCH=1. A fetched source is custody only: a doctrine may mark it held after a reader opens the
text and finds its pin phrase. No legal finding, status or count follows from a fetch.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MAX_URLS = 140
MAX_BYTES = 40_000_000


PER_ORDER_RE = re.compile(r"\bPLO\b|Public Land Order")


def proposals(root=REPO):
    """Class-wide sources only. Per-order acting instruments (Public Land Orders) belong to Selden and are listed in
    research/pothier/FOR_SELDEN.csv; URLs Ptolemy already keeps (work/PTOLEMY_SKIP.txt) are skipped."""
    skip_file = root / "research/pothier/work/PTOLEMY_SKIP.txt"
    seen = set(skip_file.read_text().split()) if skip_file.exists() else set()
    out = []
    for p in sorted((root / "research/pothier/work").glob("*/FETCH_PROPOSED.jsonl")):
        doctrine = p.parent.name
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            text = " ".join([r.get("citation", ""), r.get("note", "")] + list(r.get("urls") or []))
            if PER_ORDER_RE.search(text):
                continue
            for url in r.get("urls") or []:
                if isinstance(url, str) and url.startswith("https://") and url not in seen:
                    seen.add(url)
                    out.append({"url": url, "citation": r.get("citation", ""), "doctrine": doctrine,
                                "note": r.get("note", "")})
    return out


def pdf_text(path):
    try:
        import pypdf
    except Exception:
        return "", "pypdf not installed"
    try:
        reader = pypdf.PdfReader(str(path))
        parts = []
        for i, page in enumerate(reader.pages[:400]):
            parts.append(f"\n[[page {i + 1}]]\n" + (page.extract_text() or ""))
        return "".join(parts), ""
    except Exception as exc:  # pragma: no cover - depends on the file
        return "", f"{type(exc).__name__}: {exc}"[:200]


def main():
    out = Path(os.environ.get("OUTPUT_DIR") or HERE / "output")
    if not (os.environ.get("GITHUB_ACTIONS") or os.environ.get("POTHIER_FETCH") == "1"):
        print("fetch: skipped (not on GitHub Actions; set POTHIER_FETCH=1 to force)")
        return 0
    sys.path.insert(0, str(REPO / "jobs/source-ladder"))
    from fetch_ladder import Fetcher  # noqa: E402
    items = proposals()[:MAX_URLS]
    src_dir = out / "sources"
    src_dir.mkdir(parents=True, exist_ok=True)
    cache = Path(os.environ.get("RUNNER_TEMP") or "/tmp") / "pothier-fetch-cache"
    fetcher = Fetcher(cache, max_bytes=MAX_BYTES, max_requests=MAX_URLS * 4, log=print)
    ok, failed = [], []
    for it in items:
        att = fetcher.fetch(it["url"], route="pothier")
        if not att.get("accepted"):
            failed.append(dict(it, status=att.get("status"), error=att.get("error") or att.get("reject_reason")))
            continue
        raw = Path(att["path"]).read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        ext = "pdf" if raw[:5] == b"%PDF-" else ("html" if b"<html" in raw[:2000].lower() else "bin")
        dest = src_dir / f"{sha}.{ext}"
        dest.write_bytes(raw)
        text, err = (pdf_text(dest) if ext == "pdf" else (raw.decode("utf-8", "replace"), ""))
        tpath = ""
        if text:
            tpath = src_dir / f"{sha}.txt"
            tpath.write_text(text, encoding="utf-8")
        ok.append(dict(it, final_url=att.get("final_url"), sha256=sha, bytes=len(raw), content_type=att.get("content_type"),
                       retrieved_utc=att.get("time_utc"), path=str(dest.relative_to(out)),
                       text_path=str(tpath.relative_to(out)) if tpath else "", text_error=err))
        time.sleep(0.5)
    with open(out / "SOURCES.jsonl", "w", encoding="utf-8") as f:
        for r in ok:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    with open(out / "FETCH_FAILURES.jsonl", "w", encoding="utf-8") as f:
        for r in failed:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"fetch: {len(ok)} fetched, {len(failed)} failed of {len(items)} proposed URLs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
