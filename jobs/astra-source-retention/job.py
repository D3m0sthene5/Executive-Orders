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
import tempfile
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


def extraction_hash(directory):
    return hashlib.sha256(json.dumps([(p.name, sha(p)) for p in sorted(directory.iterdir())], separators=(",", ":")).encode()).hexdigest()


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
        if item.get("retained_path"):
            path = Path(item["retained_path"])
            if not expected or path.is_absolute() or ".." in path.parts:
                raise ValueError("Retained imports require a relative repository path and exact expected hash")


def retained_import(root, item):
    """Resolve only an explicitly demanded existing object; never trust a path as identity."""
    if not item.get("retained_path"):
        return None
    path = (root / item["retained_path"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Retained import escapes repository")
    if not path.is_file():
        raise FileNotFoundError("Demanded retained object is not materialized: " + item["retained_path"])
    if sha(path) != item["expected_sha256"]:
        raise ValueError("Retained import hash mismatch")
    return path


def preserve_previous(out, prior):
    """Keep the prior generation without re-fetching unrelated retained objects."""
    if prior is None or not prior.is_dir() or prior.resolve() == out.resolve():
        return
    def link_or_copy(src, dst):
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
    shutil.copytree(prior, out, copy_function=link_or_copy, dirs_exist_ok=True,
                    ignore=lambda directory, names: set(names) & {"log.txt", "install-log.txt", "STATUS.json", "RUNNER_INPUTS.json"})
    # Metadata is rewritten below. Never mutate the runner's rollback generation.
    for name in ("RESULTS.json", "SOURCES.jsonl", "SUMMARY.json"):
        path = out / name
        if path.exists():
            raw = path.read_bytes()
            path.unlink()
            path.write_bytes(raw)


def main():
    start = time.monotonic()
    out = Path(os.environ["OUTPUT_DIR"]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(os.environ.get("RETENTION_MANIFEST", str(JOB / "REQUESTS.json"))).resolve()
    if not manifest_path.is_relative_to(ROOT):
        raise ValueError("Retention manifest must be a declared repository input")
    queue_path = ROOT / "research/readiness/FETCH_QUEUE.jsonl"
    items = json.loads(manifest_path.read_text(encoding="utf-8"))
    queue = [json.loads(s) for s in queue_path.read_text(encoding="utf-8").splitlines() if s.strip()]
    validate_manifest(items, queue)
    prior_env = os.environ.get("JOB_PRIOR_OUTPUT_DIR")
    prior = Path(prior_env) if prior_env else JOB / "output"
    preserve_previous(out, prior)
    # Shared client preserves host pacing, robots handling, retries and logging.
    # Small same-host batch remains serial to preserve its global host pacing.
    fetcher = Fetcher(os.environ.get("JOB_CACHE_DIR", str(out / "cache")),
                      max_requests=90, max_bytes=250_000_000, max_retries=2, timeout=120)
    renderer = shutil.which("pdftoppm") if os.environ.get("RETENTION_RENDER_PAGES", "1") != "0" else None
    records = json.loads((out / "RESULTS.json").read_text()) if (out / "RESULTS.json").exists() else []
    sources = [json.loads(line) for line in (out / "SOURCES.jsonl").read_text().splitlines() if line.strip()] if (out / "SOURCES.jsonl").exists() else []
    previous_records = len(records)
    previous_sources = len(sources)
    imported_objects = 0
    imported_bytes = 0
    for item in items:
        record = dict(item)
        staged = None
        try:
            existing = out / "pdf" / (item.get("expected_sha256", "") + ".pdf")
            if item.get("expected_sha256") and existing.is_file():
                source = retained_import(out, {"retained_path": existing.relative_to(out).as_posix(), "expected_sha256": item["expected_sha256"]})
            else:
                source = retained_import(ROOT, item)
            if source is not None:
                imported_objects += 1
                imported_bytes += source.stat().st_size
                attempt = {"accepted": True, "sha256": item["expected_sha256"], "path": str(source),
                           "final_url": item["url"], "time_utc": now_utc(), "from_retained": True,
                           "retained_path": source.relative_to(ROOT).as_posix() if source.is_relative_to(ROOT) else item.get("retained_path"),
                           "bytes": source.stat().st_size}
            else:
                attempt = fetcher.fetch(item["url"], route="queued_astra_retention", expect="pdf")
            record["attempt"] = {k: v for k, v in attempt.items() if k != "path"}
            if not attempt["accepted"]:
                records.append(record)
                continue
            source = Path(attempt["path"])
            digest = item["expected_sha256"] if attempt.get("from_retained") else sha(source)
            record["sha256"] = digest
            if digest != attempt["sha256"] or (item.get("expected_sha256") and digest != item["expected_sha256"]):
                record["error"] = "hash_mismatch; no accepted page artifact"
                quarantine = out / "quarantine" / (digest + ".pdf")
                quarantine.parent.mkdir(exist_ok=True)
                shutil.copyfile(source, quarantine)
                record["preserved_new_version"] = quarantine.relative_to(out).as_posix()
                records.append(record)
                continue
            pdf = out / "pdf" / (digest + ".pdf")
            pdf.parent.mkdir(exist_ok=True)
            if source.resolve() != pdf.resolve():
                if pdf.exists():
                    pdf.unlink()
                shutil.copyfile(source, pdf)
            record["retained_pdf"] = pdf.relative_to(out).as_posix()
            reader = PdfReader(pdf)
            record["page_count"] = len(reader.pages)
            requested = item.get("pages") or list(range(1, min(len(reader.pages), 40) + 1))
            record["pages"] = []
            selected_text = []
            # Publish an extraction only after it completes. Prior narrower/wider
            # representations remain valid independent objects on failure or success.
            staged = Path(tempfile.mkdtemp(prefix=".retention-", dir=out))
            page_dir = staged
            for p in sorted(set(requested)):
                if p > len(reader.pages):
                    record.setdefault("page_errors", []).append({"page": p, "error": "out_of_range"})
                    continue
                text_file = page_dir / f"page-{p}.txt"
                text_file.write_text(reader.pages[p-1].extract_text() or "", encoding="utf-8", newline="\n")
                selected_text.append(f"=== PDF page {p} ===\n" + text_file.read_text(encoding="utf-8"))
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
                    page_record["render_error"] = ("rendering disabled for exact-version restoration; no new page review" if os.environ.get("RETENTION_RENDER_PAGES", "1") == "0" else "pdftoppm unavailable; retained PDF still needs visual review")
                record["pages"].append(page_record)
            text_file = page_dir / "selected-pages.txt"
            text_file.write_text("\n\n".join(selected_text)+"\n", encoding="utf-8", newline="\n")
            generation = extraction_hash(page_dir)
            final_dir = out / "pages" / digest / generation
            final_dir.parent.mkdir(parents=True, exist_ok=True)
            if final_dir.exists() and extraction_hash(final_dir) != generation:
                quarantine = out / "quarantine" / (generation + staged.name)
                quarantine.parent.mkdir(exist_ok=True)
                final_dir.replace(quarantine)
                record["repaired_corrupt_extraction"] = quarantine.relative_to(out).as_posix()
            if final_dir.exists():
                shutil.rmtree(staged)
            else:
                staged.replace(final_dir)
            for page in record["pages"]:
                for key in ("text", "image"):
                    if key in page:
                        page[key] = (final_dir / Path(page[key]).name).relative_to(out).as_posix()
            text_file = final_dir / "selected-pages.txt"
            staged = None
            new_source = {"url":item["url"], "final_url":attempt.get("final_url"), "sha256":digest,
                            "bytes":pdf.stat().st_size, "cache_path":record["retained_pdf"],
                            "text_path":text_file.relative_to(out).as_posix(), "text_sha256":sha(text_file),
                            "page_or_item":"Selected PDF pages: " + ", ".join(str(p["pdf_page"]) for p in record["pages"]),
                            "instrument_ids":[], "requested_for_instrument_ids":item["instrument_ids"],
                            "route":"queued_astra_retention", "retrieved_utc":attempt.get("time_utc"),
                            "notes":"Rehashed retained PDF; selected-page text only. Requested targets are not automatically asserted as document identities. No legal or original-representation acceptance."}
            sources = [s for s in sources if (s.get("sha256"), s.get("url"), s.get("text_path")) != (digest, item["url"], new_source["text_path"])]
            sources.append(new_source)
        except BudgetExceeded as exc:
            record["error"] = str(exc)
            records.append(record)
            break
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"[:600]
        finally:
            if staged is not None and staged.exists():
                shutil.rmtree(staged)
        records.append(record)
        print(json.dumps({"url": item["url"], "retained": bool(record.get("retained_pdf")), "error": record.get("error")}))
    summary = {"generated_utc": now_utc(), "manifest_sha256": sha(manifest_path), "queue_sha256": sha(queue_path),
               "requested": len(items), "attempted": len(records)-previous_records, "retained": sum(bool(r.get("retained_pdf")) for r in records[previous_records:]),
               "previous_attempts_preserved": previous_records, "previous_source_records": previous_sources,
               "source_records_after": len(sources), "imported_objects": imported_objects, "imported_bytes": imported_bytes,
               "extractions_completed": sum(bool(r.get("pages")) and not r.get("error") for r in records[previous_records:]),
               "http_requests": fetcher.requests, "download_bytes": fetcher.bytes_downloaded,
               "wall_seconds": time.monotonic()-start, "model_usage": None,
               "reviewer_role": None, "legal_findings": False, "exhaustion_findings": False}
    (out / "RESULTS.json").write_text(json.dumps(records, indent=2)+"\n", encoding="utf-8")
    (out / "SOURCES.jsonl").write_text("".join(json.dumps(s)+"\n" for s in sources), encoding="utf-8", newline="\n")
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
