"""Offline tests for Cotton: WARC decoding, hash gating, route order, reuse of committed bytes."""
import gzip
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cotton  # noqa: E402

URL = "https://www.presidency.ucsb.edu/documents/executive-order-7310"


def warc(body, uri=URL):
    http = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + body
    return gzip.compress(b"WARC/1.0\r\nWARC-Type: response\r\nWARC-Target-URI: " + uri.encode() +
                         b"\r\n\r\n" + http + b"\r\n\r\n")


class CottonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.job = self.repo / "jobs/cotton-capture-custody"
        (self.job / "data").mkdir(parents=True)
        (self.repo / "jobs/app-executive-orders/output").mkdir(parents=True)
        (self.repo / "research/readiness/claims").mkdir(parents=True)
        self.raw = warc(b"<html>page</html>")
        _, self.page = cotton.warc_response_body(self.raw)
        self.sha = hashlib.sha256(self.page).hexdigest()
        cap = {"archive": "common-crawl", "warc_filename": "crawl-data/CC/x.warc.gz", "warc_offset": 5,
               "warc_length": len(self.raw), "captured_utc": "2025-12-16T00:59:36Z"}
        (self.repo / "jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl").write_text(
            json.dumps({"sha256": self.sha, "url": URL, "heading": "Executive Order 7310", "capture": cap}) + "\n")
        claim = {"instrument_id": "EO:7310", "original_representation": {"url": URL, "sha256": self.sha}}
        (self.repo / "research/readiness/claims/x.jsonl").write_text(json.dumps(claim) + "\n")
        self.out = Path(self.tmp.name) / "out"

    def test_matching_capture_is_published_with_cache_path(self):
        calls = []

        def get(url, headers=None):
            calls.append((url, headers))
            return self.raw

        summary = cotton.run(self.repo, self.job, self.out, get=get)
        self.assertEqual((summary["published"], summary["failed"]), (1, 0))
        self.assertEqual(calls, [(cotton.CC_DATA + "crawl-data/CC/x.warc.gz", {"Range": f"bytes=5-{5 + len(self.raw) - 1}"})])
        rec = json.loads((self.out / "SOURCES.jsonl").read_text())
        self.assertEqual((rec["sha256"], rec["url"], rec["instrument_ids"]), (self.sha, URL, ["EO:7310"]))
        self.assertEqual(hashlib.sha256((self.out / rec["cache_path"]).read_bytes()).hexdigest(), self.sha)

    def test_changed_bytes_are_never_published_and_live_route_is_tried(self):
        def get(url, headers=None):
            return warc(b"<html>other</html>") if headers else b"<html>live, changed</html>"

        summary = cotton.run(self.repo, self.job, self.out, get=get)
        self.assertEqual((summary["published"], summary["failed"]), (0, 1))
        fail = json.loads((self.out / "FAILURES.jsonl").read_text())
        self.assertEqual([e.split(":")[0] for e in fail["errors"]], ["capture", "live"])
        self.assertEqual(list((self.out / "captures").iterdir()), [])

    def test_wrong_page_in_capture_is_refused(self):
        def get(url, headers=None):
            if headers:
                return warc(b"<html>page</html>", uri=URL + "-other")
            raise OSError("offline")

        self.assertEqual(cotton.run(self.repo, self.job, self.out, get=get)["published"], 0)

    def test_committed_bytes_are_reused_without_download(self):
        (self.job / "output/captures").mkdir(parents=True)
        (self.job / "output/captures" / (self.sha + ".bin")).write_bytes(self.page)

        def get(url, headers=None):
            raise AssertionError("no download expected")

        self.assertEqual(cotton.run(self.repo, self.job, self.out, get=get)["published"], 1)

    def test_bytes_in_the_runners_prior_output_are_reused(self):
        prior = Path(self.tmp.name) / "prior"
        (prior / "captures").mkdir(parents=True)
        (prior / "captures" / (self.sha + ".bin")).write_bytes(self.page)

        def get(url, headers=None):
            raise OSError("network down")

        old = os.environ.get("JOB_PRIOR_OUTPUT_DIR")
        os.environ["JOB_PRIOR_OUTPUT_DIR"] = str(prior)
        try:
            summary = cotton.run(self.repo, self.job, self.out, get=get)
        finally:
            if old is None:
                os.environ.pop("JOB_PRIOR_OUTPUT_DIR", None)
            else:
                os.environ["JOB_PRIOR_OUTPUT_DIR"] = old
        self.assertEqual((summary["published"], summary["failed"]), (1, 0))

    def test_wanted_file_and_non_web_sources(self):
        (self.job / "data/WANTED.jsonl").write_text(json.dumps({"sha256": "a" * 64, "url": None, "instrument_id": "EO:1"}) + "\n")
        summary = cotton.run(self.repo, self.job, self.out, get=lambda url, headers=None: self.raw)
        self.assertEqual((summary["wanted_hashes"], summary["published"], summary["not_web_sources"]), (2, 1, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
