"""Offline tests for Cotton: WARC decoding, hash gating, route order, reuse of committed bytes."""
import gzip
import hashlib
import json
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
        self.assertEqual([e.split(":")[0] for e in fail["errors"]], ["capture"])  # never the live APP site
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

    def test_wanted_file_and_non_web_sources(self):
        (self.job / "data/WANTED.jsonl").write_text(json.dumps({"sha256": "a" * 64, "url": None, "instrument_id": "EO:1"}) + "\n")
        summary = cotton.run(self.repo, self.job, self.out, get=lambda url, headers=None: self.raw)
        self.assertEqual((summary["wanted_hashes"], summary["published"], summary["not_web_sources"]), (2, 1, 1))


    def test_unmerged_backfill_capture_is_preserved_as_successor_of_a_live_hash(self):
        live_url = "https://www.presidency.ucsb.edu/documents/executive-order-7208-x"
        live_sha = "c" * 64
        (self.repo / "jobs/app-executive-orders/output/DOCUMENTS.jsonl").write_text(
            json.dumps({"sha256": live_sha, "url": live_url}) + "\n")
        claim = {"instrument_id": "EO:7208", "original_representation": {"url": live_url, "sha256": live_sha}}
        (self.repo / "research/readiness/claims/x.jsonl").write_text(json.dumps(claim) + "\n")
        raw = warc(b"<html>7208 capture</html>", uri=live_url)
        _, body = cotton.warc_response_body(raw)
        succ = hashlib.sha256(body).hexdigest()
        cap = {"archive": "common-crawl", "warc_filename": "crawl-data/CC/y.warc.gz", "warc_offset": 0,
               "warc_length": len(raw), "captured_utc": "2025-09-05T00:00:00Z"}
        delta = self.repo / "jobs/poggio-archive-backfill/output"
        delta.mkdir(parents=True)
        (delta / "MIRROR_DOCUMENTS.jsonl").write_text(
            json.dumps({"sha256": succ, "url": live_url, "heading": "Executive Order 7208", "capture": cap}) + "\n")
        calls = []

        def get(url, headers=None):
            calls.append(url)
            return raw if headers else b"<html>live page, changed since</html>"

        summary = cotton.run(self.repo, self.job, self.out, get=get)
        self.assertEqual((summary["wanted_hashes"], summary["archive_successors"]), (1, 1))
        self.assertEqual((summary["published"], summary["failed"], summary["not_web_sources"]), (1, 0, 1))  # the live hash has no route
        rec = json.loads((self.out / "SOURCES.jsonl").read_text())
        self.assertEqual((rec["sha256"], rec["successor_of"], rec["instrument_ids"]), (succ, live_sha, ["EO:7208"]))
        self.assertEqual((self.out / "FAILURES.jsonl").read_text(), "")
        self.assertEqual(calls.count(live_url), 0)  # Cotton never requests the live APP site


if __name__ == "__main__":
    unittest.main(verbosity=2)
