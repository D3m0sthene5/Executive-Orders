"""Offline tests for Ptolemy: hash discipline, carry-forward, retries and budgets. No network."""
import hashlib
import json
import pathlib
import sys
import tempfile
import time
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ptolemy as P  # noqa: E402

PAGE = b"<html>an APP transcription</html>"
PDF = b"%PDF-1.4 an FR document"
SHA_PAGE = hashlib.sha256(PAGE).hexdigest()
SHA_PDF = hashlib.sha256(PDF).hexdigest()
SHA_BAD = "c" * 64


class FakePool:
    def __init__(self, bodies, errors=()):
        self.bodies, self.errors, self.calls = bodies, dict(errors), []

    def fetch(self, url):
        self.calls.append(url)
        if url in self.errors:
            raise RuntimeError(self.errors[url])
        return {"url": url, "final_url": url, "body": self.bodies[url]}


class PtolemyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.job = self.root / "job"
        self.job.mkdir()
        reqs = [
            {"sha256": SHA_PAGE, "url": "https://www.presidency.ucsb.edu/documents/eo-1", "route": "archive",
             "instrument_ids": ["EO:1"], "capture": {"archive": "common-crawl", "warc_filename": "w.gz",
                                                     "warc_offset": 1, "warc_length": 2, "url": "u"}},
            {"sha256": SHA_PDF, "url": "https://www.govinfo.gov/a.pdf", "route": "live", "instrument_ids": ["EO:2"]},
            {"sha256": SHA_BAD, "url": "https://www.govinfo.gov/changed.pdf", "route": "live", "instrument_ids": ["EO:3"]},
            {"sha256": "d" * 64, "url": "https://www.govinfo.gov/flaky.pdf", "route": "live", "instrument_ids": ["EO:4"]},
        ]
        (self.job / "REQUESTS.jsonl").write_text("".join(json.dumps(r) + "\n" for r in reqs), encoding="utf-8")
        self.pool = FakePool({"https://www.govinfo.gov/a.pdf": PDF, "https://www.govinfo.gov/changed.pdf": b"new"},
                             {"https://www.govinfo.gov/flaky.pdf": "HTTP 503"})

    def fetch_archive(self, record, cache, throttles):
        return PAGE, "common-crawl WARC range w.gz@1"

    def run_once(self, out, prior=None, **kw):
        return P.run(self.job, out, self.root / "cache", prior=prior, fetch_archive=self.fetch_archive,
                     pool=self.pool, **kw)

    def test_keeps_only_exact_bytes_and_records_every_outcome(self):
        out = self.root / "out1"
        s = self.run_once(out)
        self.assertTrue((out / "raw" / (SHA_PAGE + ".html")).is_file())
        self.assertTrue((out / "raw" / (SHA_PDF + ".pdf")).is_file())
        self.assertFalse(any(p.name.startswith(SHA_BAD) for p in (out / "raw").iterdir()))
        src = {r["sha256"]: r for r in P.read_jsonl(out / "SOURCES.jsonl")}
        self.assertEqual(set(src), {SHA_PAGE, SHA_PDF})
        self.assertEqual(src[SHA_PDF]["cache_path"], "raw/" + SHA_PDF + ".pdf")
        ledger = {r["sha256"]: r["result"] for r in P.read_jsonl(out / "LEDGER.jsonl")}
        self.assertEqual(ledger[SHA_BAD], "hash_mismatch")
        self.assertEqual(ledger["d" * 64], "fetch_failed")
        self.assertEqual(s["kept_total"], 2)

    def test_next_run_carries_forward_and_retries_only_what_is_due(self):
        first = self.root / "out1"
        self.run_once(first)
        self.pool.calls.clear()
        second = self.root / "out2"
        s = self.run_once(second, prior=first)
        self.assertEqual(self.pool.calls, ["https://www.govinfo.gov/flaky.pdf"])  # mismatch is final, kept is done
        self.assertEqual(s["kept_total"], 2)
        self.assertEqual(len(P.read_jsonl(second / "SOURCES.jsonl")), 2)
        third = self.root / "out3"
        self.run_once(third, prior=second)
        self.pool.calls.clear()
        fourth = self.root / "out4"
        s = self.run_once(fourth, prior=third)
        self.assertEqual(self.pool.calls, [])  # three failed attempts: no fourth
        self.assertEqual(s["still_due"], 0)

    def test_tampered_carried_file_is_dropped(self):
        first = self.root / "out1"
        self.run_once(first)
        (first / "raw" / (SHA_PDF + ".pdf")).write_bytes(b"tampered")
        second = self.root / "out2"
        self.run_once(second, prior=first)
        self.assertEqual((second / "raw" / (SHA_PDF + ".pdf")).read_bytes(), PDF)  # re-fetched, exact again

    def test_byte_budget_stops_new_fetches(self):
        out = self.root / "out1"
        budget = P.Budget(time.monotonic(), max_bytes=1)
        budget.add(1)
        s = self.run_once(out, budget=budget)
        self.assertEqual(s["kept_total"], 0)
        self.assertEqual(self.pool.calls, [])

    def test_archive_route_uses_cassiodorus_reader_with_recorded_capture(self):
        from unittest import mock
        import app_mirror as M
        seen = {}

        def fake_read_cc(c, cache, throttle):
            seen.update(c)
            return PAGE, {}
        with mock.patch.object(M, "read_cc", fake_read_cc):
            out = self.root / "out1"
            P.run(self.job, out, self.root / "cache", pool=self.pool, live_limit=0)
        self.assertEqual(seen["warc_filename"], "w.gz")
        self.assertEqual((seen["warc_offset"], seen["warc_length"]), (1, 2))
        self.assertTrue((out / "raw" / (SHA_PAGE + ".html")).is_file())

    def test_requests_file_routes_are_known(self):
        real = HERE / "REQUESTS.jsonl"
        if not real.is_file():
            self.skipTest("no committed request list")
        routes = {r.get("route") for r in P.read_jsonl(real)}
        self.assertLessEqual(routes, {"archive", "live"})


if __name__ == "__main__":
    unittest.main()
