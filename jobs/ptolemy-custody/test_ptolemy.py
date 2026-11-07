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
import pergamon_store as PS  # noqa: E402

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


class MemBackend:
    """An in-memory stand-in for a non-git Pergamon backend."""
    name = "release"

    def __init__(self):
        self.objects, self.down = {}, False

    def locator_for(self, sha, ext):
        return f"mem://{sha}{ext}"

    def put(self, raw, sha, ext):
        if self.down:
            raise PS.Unavailable("store is down")
        self.objects[sha + ext] = raw
        return self.locator_for(sha, ext)

    def has(self, sha, ext=None):
        return (sha + ext) in self.objects

    def get(self, locator, max_bytes=0):
        try:
            return self.objects[locator[len("mem://"):]]
        except KeyError:
            raise PS.NotFound(locator)


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
        self.assertLessEqual(routes, {"archive", "live", "import"})

    def test_import_route_keeps_exact_repository_files_only(self):
        rel = "research/salvage/test-ptolemy-import.pdf"
        reqs = [{"sha256": SHA_PDF, "route": "import", "path": rel, "url": "https://www.govinfo.gov/a.pdf"},
                {"sha256": SHA_BAD, "route": "import", "path": "../outside.pdf"}]
        (self.job / "REQUESTS.jsonl").write_text("".join(json.dumps(r) + "\n" for r in reqs), encoding="utf-8")
        target = P.REPO / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(PDF)
        self.addCleanup(target.unlink)
        out = self.root / "out1"
        s = self.run_once(out)
        self.assertTrue((out / "raw" / (SHA_PDF + ".pdf")).is_file())
        ledger = {r["sha256"]: r["result"] for r in P.read_jsonl(out / "LEDGER.jsonl")}
        self.assertEqual(ledger[SHA_BAD], "fetch_failed")
        self.assertEqual(s["kept_total"], 1)


class PergamonRoutingTests(unittest.TestCase):
    """With PERGAMON_BACKEND other than git, kept bytes go to the store, not to output/raw."""
    fetch_archive = PtolemyTests.fetch_archive

    def setUp(self):
        PtolemyTests.setUp(self)
        self.mem = MemBackend()
        self.store = PS.Store(self.mem)

    def run_once(self, out, prior=None, **kw):
        return P.run(self.job, out, self.root / "cache", prior=prior, fetch_archive=self.fetch_archive,
                     pool=self.pool, store=self.store, **kw)

    def test_kept_bytes_go_to_the_store_and_sources_carry_the_locator(self):
        out = self.root / "out1"
        s = self.run_once(out)
        self.assertEqual(sorted(p.name for p in (out / "raw").iterdir()), [])          # nothing written to git's folder
        self.assertEqual(self.mem.objects, {SHA_PAGE + ".html": PAGE, SHA_PDF + ".pdf": PDF})
        src = {r["sha256"]: r for r in P.read_jsonl(out / "SOURCES.jsonl")}
        self.assertEqual(set(src), {SHA_PAGE, SHA_PDF})
        rec = src[SHA_PDF]
        self.assertIsNone(rec["cache_path"])
        self.assertEqual(rec["pergamon"]["locator"], f"mem://{SHA_PDF}.pdf")
        self.assertEqual(rec["pergamon"]["backend"], "release")
        self.assertEqual(rec["bytes"], len(PDF))
        self.assertEqual(self.store.get_verified(rec["pergamon"]), PDF)
        self.assertEqual(s["kept_total"], 2)
        self.assertEqual(s["store"]["stored_this_run"], 2)
        budget = json.loads((out / "BUDGET.json").read_text())
        self.assertTrue(budget["ok"])

    def test_wrong_bytes_never_reach_the_store(self):
        self.run_once(self.root / "out1")
        self.assertFalse(any(k.startswith(SHA_BAD) for k in self.mem.objects))

    def test_next_run_carries_stored_records_without_refetching_them(self):
        first = self.root / "out1"
        self.run_once(first)
        self.pool.calls.clear()
        second = self.root / "out2"
        s = self.run_once(second, prior=first)
        self.assertEqual(self.pool.calls, ["https://www.govinfo.gov/flaky.pdf"])
        self.assertEqual(s["kept_total"], 2)
        self.assertEqual({r["sha256"] for r in P.read_jsonl(second / "SOURCES.jsonl")}, {SHA_PAGE, SHA_PDF})
        self.assertTrue(all(r["pergamon"]["locator"] for r in P.read_jsonl(second / "SOURCES.jsonl")))

    def test_paused_style_run_fetches_nothing_and_carries_everything(self):
        first = self.root / "out1"
        self.run_once(first)
        self.pool.calls.clear()
        paused = self.root / "out2"
        s = self.run_once(paused, prior=first, archive_limit=0, live_limit=0)
        self.assertEqual(self.pool.calls, [])
        self.assertEqual(s["kept_total"], 2)
        self.assertEqual(len(P.read_jsonl(paused / "SOURCES.jsonl")), 2)

    def test_store_outage_is_not_charged_to_the_source_and_stops_the_run(self):
        self.mem.down = True
        out = self.root / "out1"
        s = self.run_once(out)
        self.assertEqual(s["kept_total"], 0)
        ledger = {r["sha256"]: r for r in P.read_jsonl(out / "LEDGER.jsonl")}
        self.assertEqual(ledger[SHA_PDF]["result"], "store_failed")
        self.assertEqual(ledger[SHA_PDF]["attempts"], 0)          # still due in full on the next run
        self.assertEqual(s["still_due"], 3)                       # mismatch is final; the other three can retry
        self.assertGreaterEqual(s["store"]["store_failures_this_run"], 2)

    def test_output_over_budget_fails_the_run_once_bytes_live_outside_git(self):
        out = self.root / "out1"
        out.mkdir()
        (out / "stray.bin").write_bytes(b"x" * (6 * 1024 * 1024))
        with self.assertRaises(RuntimeError):
            self.run_once(out)
        self.assertTrue((out / "BUDGET.json").is_file())

    def test_legacy_raw_files_are_carried_and_excluded_from_the_enforced_budget(self):
        legacy = self.root / "legacy"
        self.store_git = PS.Store(PS.GitBackend(legacy / "raw", legacy))
        P.run(self.job, legacy, self.root / "cache", fetch_archive=self.fetch_archive, pool=self.pool,
              store=self.store_git)
        self.assertTrue((legacy / "raw" / (SHA_PDF + ".pdf")).is_file())
        (legacy / "raw" / "padding.bin").write_bytes(b"x" * (30 * 1024 * 1024))   # far over 20 MiB, but legacy
        out = self.root / "out2"
        s = self.run_once(out, prior=legacy)
        self.assertEqual(s["kept_total"], 2)
        self.assertTrue((out / "raw" / (SHA_PDF + ".pdf")).is_file())              # old git files still resolve
        rec = {r["sha256"]: r for r in P.read_jsonl(out / "SOURCES.jsonl")}[SHA_PDF]
        self.assertEqual(rec["cache_path"], "raw/" + SHA_PDF + ".pdf")


class PtolemyDefaultStoreTests(unittest.TestCase):
    def test_default_is_git_and_environment_switch_is_honoured(self):
        self.assertEqual(PS.Store.from_env({}, git_root="x").backend_name, "git")
        env = {"PERGAMON_BACKEND": "release", "GITHUB_REPOSITORY": "o/r", "GITHUB_TOKEN": "t"}
        self.assertEqual(PS.Store.from_env(env).backend_name, "release")

    def test_job_py_keeps_the_paused_branch(self):
        src = (HERE / "job.py").read_text(encoding="utf-8")
        self.assertIn('"PAUSED"', src)
        self.assertIn("archive_limit=0, live_limit=0", src)


if __name__ == "__main__":
    unittest.main()
