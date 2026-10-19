"""Bounded retention of explicitly queued PDFs using the existing ladder client.

Custody and page artifacts only. No exhaustion, source-quality or legal finding.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(os.environ.get("REPO_ROOT", ".")).resolve()
JOB = ROOT / "jobs/astra-source-retention"
sys.path.insert(0, str(ROOT / "jobs/source-ladder"))
from fetch_ladder import Fetcher, BudgetExceeded, now_utc
from pypdf import PdfReader


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_manifest(items, queue):
    if len(items) > 30:
        raise ValueError("Maximum 30 retained URLs per run")
    queued = {(q.get("instrument_id"), u) for q in queue for u in q.get("urls", [])}
    seen = set()
    for item in items:
        url = item["url"]
        if not url.startswith("https://") or url in seen:
            raise ValueError("Manifest URLs must be unique HTTPS URLs")
        seen.add(url)
        if not item.get("instrument_ids") or any((i, url) not in queued for i in item["instrument_ids"]):
            raise ValueError("Every instrument/URL pair must already be in FETCH_QUEUE")
        pages = item.get("pages", [])
        if len(pages) > 40 or any(type(p) is not int or p < 1 for p in pages):
            raise ValueError("Page requests must be bounded, positive one-based integers")
        expected = item.get("expected_sha256")
        if expected and (len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected)):
            raise ValueError("Invalid expected SHA-256")


def main():
    start = time.monotonic()
    out = Path(os.environ["OUTPUT_DIR"]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = JOB / "REQUESTS.json"
    queue_path = ROOT / "research/readiness/FETCH_QUEUE.jsonl"
    items = json.loads(manifest_path.read_text(encoding="utf-8"))
    queue = [json.loads(s) for s in queue_path.read_text(encoding="utf-8").splitlines() if s.strip()]
    validate_manifest(items, queue)
    # Shared client preserves host pacing, robots handling, retries and logging.
    # Small same-host batch remains serial to preserve its global host pacing.
    fetcher = Fetcher(os.environ.get("JOB_CACHE_DIR", str(out / "cache")),
                      max_requests=90, max_bytes=250_000_000, max_retries=2, timeout=120)
    renderer = shutil.which("pdftoppm")
    records = []
    for item in items:
        record = dict(item)
        try:
            attempt = fetcher.fetch(item["url"], route="queued_astra_retention", expect="pdf")
            record["attempt"] = {k: v for k, v in attempt.items() if k != "path"}
            if not attempt["accepted"]:
                records.append(record)
                continue
            source = Path(attempt["path"])
            digest = sha(source)  # Rehash even a cache hit.
            record["sha256"] = digest
            if digest != attempt["sha256"] or (item.get("expected_sha256") and digest != item["expected_sha256"]):
                record["error"] = "hash_mismatch; no accepted page artifact"
                records.append(record)
                continue
            pdf = out / "pdf" / (digest + ".pdf")
            pdf.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, pdf)
            record["retained_pdf"] = pdf.relative_to(out).as_posix()
            reader = PdfReader(pdf)
            record["page_count"] = len(reader.pages)
            requested = item.get("pages") or list(range(1, min(len(reader.pages), 40) + 1))
            record["pages"] = []
            page_dir = out / "pages" / digest
            page_dir.mkdir(parents=True, exist_ok=True)
            for p in sorted(set(requested)):
                if p > len(reader.pages):
                    record.setdefault("page_errors", []).append({"page": p, "error": "out_of_range"})
                    continue
                text_file = page_dir / f"page-{p}.txt"
                text_file.write_text(reader.pages[p-1].extract_text() or "", encoding="utf-8", newline="\n")
                page_record = {"pdf_page": p, "text": text_file.relative_to(out).as_posix(), "text_sha256": sha(text_file)}
                if renderer:
                    prefix = page_dir / f"page-{p}"
                    proc = subprocess.run([renderer, "-f", str(p), "-l", str(p), "-r", "130", "-singlefile", "-png", str(pdf), str(prefix)], capture_output=True, timeout=90)
                    png = prefix.with_suffix(".png")
                    if proc.returncode == 0 and png.exists():
                        page_record.update(image=png.relative_to(out).as_posix(), image_sha256=sha(png))
                    else:
                        page_record["render_error"] = proc.stderr.decode("utf-8", "replace")[:500]
                else:
                    page_record["render_error"] = "pdftoppm unavailable; retained PDF still needs visual review"
                record["pages"].append(page_record)
        except BudgetExceeded as exc:
            record["error"] = str(exc)
            records.append(record)
            break
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"[:600]
        records.append(record)
        print(json.dumps({"url": item["url"], "retained": bool(record.get("retained_pdf")), "error": record.get("error")}))
    summary = {"generated_utc": now_utc(), "manifest_sha256": sha(manifest_path), "queue_sha256": sha(queue_path),
               "requested": len(items), "attempted": len(records), "retained": sum(bool(r.get("retained_pdf")) for r in records),
               "http_requests": fetcher.requests, "download_bytes": fetcher.bytes_downloaded,
               "wall_seconds": time.monotonic()-start, "model_usage": None,
               "reviewer_role": None, "legal_findings": False, "exhaustion_findings": False}
    (out / "RESULTS.json").write_text(json.dumps(records, indent=2)+"\n", encoding="utf-8")
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
