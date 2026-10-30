"""Bounded temporary-repository probes for dynamic checker providers."""
import hashlib
import importlib.util
import json
import os
import pathlib
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[5]
import sys
sys.path.insert(0, str(ROOT / "jobs/claim-checker"))
sys.path.insert(0, str(ROOT / "jobs/claim-kit"))
import sources
import working_text
_model_spec = importlib.util.spec_from_file_location("fixture_norton_model", ROOT / "jobs/norton/model.py")
model = importlib.util.module_from_spec(_model_spec)
_model_spec.loader.exec_module(model)


def put(root, rel, data):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


def main():
    checks = {}
    with tempfile.TemporaryDirectory(prefix="checker-closure-", dir=os.environ.get("CHECKER_FIXTURE_TMPDIR")) as td:
        repo = pathlib.Path(td)
        # A SOURCES record can select an arbitrary nested text file under a
        # different job's output, and a FRAGMENTS record does likewise.
        txt = b"EO 90001 fixture source text\n"
        put(repo, "jobs/source-a/output/deep/texts/source.txt", txt)
        sha = hashlib.sha256(b"raw source bytes").hexdigest()
        rec = {"sha256": sha, "url": "https://example.test/eo.pdf", "text_path": "deep/texts/source.txt"}
        put(repo, "jobs/source-a/output/SOURCES.jsonl", (json.dumps(rec) + "\n").encode())
        ix = sources.HeldIndex()
        sources.load_job_sources(ix, repo)
        copy = ix.lookup_sha(sha)[0]
        checks["dynamic_sources_text_path"] = copy.text_path.read_bytes() == txt

        frag = {"instrument_id": "EO:90001", "kind": "original_representation", "produced_by": "source-b",
                "data": {"sha256": sha, "text_path": "../../source-a/output/deep/texts/source.txt",
                         "text_sha256": hashlib.sha256(txt).hexdigest(), "grade": "compiled_transcription",
                         "acceptable_as_original": False}}
        put(repo, "jobs/source-b/output/FRAGMENTS.variant.jsonl", (json.dumps(frag) + "\n").encode())
        wi = working_text.Index(repo)
        checks["dynamic_fragment_discovery"] = bool(wi.by_sha.get(sha))

        # The provenance path is nested and need not live in source_books; the
        # reader follows it only after a validated PROVENANCE record names it.
        pdf = b"synthetic printed volume"
        pdfsha = hashlib.sha256(pdf).hexdigest()
        put(repo, "releases/arbitrary/nested/volume.pdf",
            f"version https://git-lfs.github.com/spec/v1\noid sha256:{pdfsha}\nsize {len(pdf)}\n".encode())
        prov = {"volume": {"pdf": "releases/arbitrary/nested/volume.pdf", "pdf_sha256": pdfsha}}
        put(repo, "jobs/book-job/data/PROVENANCE.json", json.dumps(prov).encode())
        book_ix = sources.HeldIndex()
        sources.load_source_books(book_ix, repo)
        checks["arbitrary_release_provenance"] = bool(book_ix.lookup_sha(pdfsha))

        # Mirror captures are a separate, literal provider in checker.py.
        mirror = {"sha256": sha, "url": "https://example.test/page",
                  "capture": {"archive": "common-crawl", "warc_filename": "crawl-data/x.warc.gz",
                              "warc_offset": 0, "warc_length": 12}}
        put(repo, "jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl",
            (json.dumps(mirror) + "\n").encode())
        spec = importlib.util.spec_from_file_location("checker_fixture", ROOT / "jobs/claim-checker/checker.py")
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        checks["mirror_capture_record"] = sha in checker.load_archive_captures(repo)

        # Norton factual source paths are repository-root-relative and dynamic.
        raw = b"factual event raw bytes"
        body = b"A sufficiently long synthetic factual text span."
        put(repo, "research/custom-provider/raw.pdf", raw)
        put(repo, "research/custom-provider/text.txt", body)
        source = {"sha256": hashlib.sha256(raw).hexdigest(), "text_sha256": hashlib.sha256(body).hexdigest(),
                  "text_path": "research/custom-provider/text.txt", "raw_path": "research/custom-provider/raw.pdf",
                  "url": "https://example.test/fact", "page_or_item": "p. 1"}
        record = {"source": source, "char_start": 0, "char_end": len(body), "text": body.decode()}
        checks["arbitrary_factual_raw_and_text_paths"] = model.source_span(repo, record, require_bytes=True) == []

    failed = [k for k, v in checks.items() if not v]
    print(json.dumps({"fixture": "temporary repository only", "checks": checks,
                      "passed": len(checks) - len(failed), "failed": failed}, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
