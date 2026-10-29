"""Offline tests for the live-only backfill in app_mirror.py: host guard, seed, index, documents, merge."""
import gzip
import hashlib
import json
import shutil
import socket
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import app_harvest as live  # noqa: E402
import app_mirror as m  # noqa: E402

APP = "https://www.presidency.ucsb.edu"


def page(number, text="Whereas the successful prosecution of the war requires every possible protection."):
    return (f'<section id="block-system-main"><div class="field-ds-doc-title"><h1>Executive Order {number}—Title</h1></div>'
            f'<div class="field-docs-start-date-time"><span content="1935-01-02T00:00:00+00:00">January 2, 1935</span></div>'
            f'<div class="field-docs-content"><p>{text}</p></div>'
            f'<div class="field-prez-document-citation"><p class="ucsbapp_citation">x https://www.presidency.ucsb.edu/node/{number}</p></div>'
            f'</section>').encode()


def warc(body, uri):
    http = b"HTTP/1.1 200 OK\r\ncontent-type: text/html\r\n\r\n" + body
    return gzip.compress(b"WARC/1.0\r\nWARC-Type: response\r\nWARC-Date: 2025-09-09T11:29:43Z\r\nWARC-Target-URI: " +
                         uri.encode() + b"\r\nContent-Length: " + str(len(http)).encode() + b"\r\n\r\n" + http)


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


class Base(unittest.TestCase):
    """A base output folder: EO:1 mirrored, EO:2 and EO:3 live only (EO:2 has a CC pointer), one unnumbered."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.base, self.out, self.cache = self.tmp / "base", self.tmp / "out", self.tmp / "cache"
        self.out.mkdir()
        rows = [{"instrument_id": f"EO:{n}", "path": f"/documents/executive-order-{n}", "url": f"{APP}/documents/executive-order-{n}",
                 "title": f"Executive Order {n}", "date": "1935-01-02"} for n in (1, 2, 3)]
        rows.append({"instrument_id": None, "path": "/documents/executive-order-x", "url": APP + "/documents/executive-order-x",
                     "title": "Executive Order X", "date": ""})
        write(self.base / "INDEX.jsonl", rows)
        live_text = (self.base / "texts/executive-order-2.txt")
        live_text.parent.mkdir(parents=True)
        live_text.write_bytes(b"live text\n")
        write(self.base / "DOCUMENTS.jsonl", [
            {"instrument_id": "EO:1", "path": rows[0]["path"], "sha256": "a" * 64, "text_sha256": "b" * 64, "audit_of_mirror": "archive/common-crawl"},
            {"instrument_id": "EO:2", "path": rows[1]["path"], "sha256": "c" * 64, "text_path": "texts/executive-order-2.txt",
             "text_sha256": hashlib.sha256(b"live text\n").hexdigest(), "retrieved_utc": "2026-10-18T00:00:00Z"},
            {"instrument_id": "EO:3", "path": rows[2]["path"], "sha256": "d" * 64, "text_sha256": "e" * 64},
            {"instrument_id": None, "path": rows[3]["path"], "sha256": "f" * 64, "text_sha256": "0" * 64}])
        write(self.base / "MIRROR_DOCUMENTS.jsonl", [{"instrument_id": "EO:1", "path": rows[0]["path"], "sha256": "1" * 64,
                                                      "route": "archive/common-crawl", "text_sha256": "2" * 64}])
        self.raw2 = warc(page(2), rows[1]["url"])
        write(self.base / "MIRROR_INDEX.jsonl", [
            {"path": rows[0]["path"], "archive": "common-crawl", "crawl": "CC-MAIN-2025-38", "timestamp": "20250905000000",
             "url": rows[0]["url"], "digest": "", "warc_filename": "crawl-data/one.warc.gz", "warc_offset": 0, "warc_length": 10},
            {"path": rows[1]["path"], "archive": "common-crawl", "crawl": "CC-MAIN-2025-38", "timestamp": "20250905000000",
             "url": rows[1]["url"], "digest": "D2", "warc_filename": "crawl-data/two.warc.gz", "warc_offset": 100,
             "warc_length": len(self.raw2)}])
        for name in ("MIRROR_FAILURES.jsonl", "MIRROR_SOURCES.jsonl", "MIRROR_FRAGMENTS.jsonl", "MIRROR_ATTEMPTS.jsonl"):
            (self.base / name).touch()
        self.rows = rows
        self.calls = []
        self.responses = {}
        original = m.http_get

        def fake(url, headers=None, timeout=90, tries=6, throttle=None):
            m.require_archive_host(url)  # the real guard still applies
            self.calls.append(url)
            for prefix, answer in self.responses.items():
                if url.startswith(prefix):
                    return answer(url, headers) if callable(answer) else answer
            return 404, {}, b""

        m.http_get = fake
        self.addCleanup(setattr, m, "http_get", original)

    def snapshot(self):
        return {p.relative_to(self.base).as_posix(): p.read_bytes() for p in self.base.rglob("*") if p.is_file()}


class HostGuard(unittest.TestCase):
    def test_app_and_other_hosts_are_refused_before_any_connection(self):
        for url in (APP + "/documents/executive-order-1", "https://presidency.ucsb.edu/x",
                    "http://web.archive.org/web/1id_/x", "https://example.org/"):
            with self.assertRaises(m.ArchiveRefused):
                m.http_get(url, tries=1)
        m.require_archive_host("https://web.archive.org/cdx/search/cdx?url=x")

    def test_redirect_to_app_is_refused(self):
        req = urllib.request.Request("https://web.archive.org/web/2025id_/" + APP + "/x")
        with self.assertRaises(m.ArchiveRefused):
            m._ArchiveOnlyRedirects().redirect_request(req, None, 302, "Found", {}, APP + "/documents/x")

    def test_process_lock_refuses_app_dns(self):
        original = m.lock_to_archives()
        try:
            for host in ("www.presidency.ucsb.edu", "WWW.PRESIDENCY.UCSB.EDU.", "presidency.ucsb.edu"):
                with self.assertRaises(m.ArchiveRefused):
                    socket.getaddrinfo(host, 443)
        finally:
            socket.getaddrinfo = original

    def test_app_host_is_not_an_archive_host(self):
        self.assertNotIn(live.HOST, m.ARCHIVE_HOSTS)


class Backfill(Base):
    def test_seed_is_live_ids_minus_mirrored_ids(self):
        self.assertEqual(m.live_only_ids(self.base), ["EO:2", "EO:3"])

    def test_index_asks_only_for_pages_without_a_pointer_and_only_appends(self):
        before = self.snapshot()
        cc_row = {"url": self.rows[2]["url"], "mime": "text/html", "status": "200", "timestamp": "20190101000000",
                  "filename": "crawl-data/three.warc.gz", "offset": "5", "length": "50", "digest": "D3"}
        self.responses = {
            "https://index.commoncrawl.org/CC-MAIN-2019-04-index?": lambda url, h: (
                (200, {}, b'{"pages": 1}') if "showNumPages" in url else (200, {}, (json.dumps(cc_row) + "\n").encode())),
        }
        result = m.run_backfill_index(self.base, self.out, {"EO:2", "EO:3"},
                                      ["CC-MAIN-2025-38", "CC-MAIN-2019-04", "CC-MAIN-2018-01"],
                                      m.Throttle(0), m.Throttle(0))
        self.assertEqual(self.snapshot(), before)  # base untouched
        added = live.lines(self.out / "MIRROR_INDEX.jsonl")
        self.assertEqual([(c["path"], c["crawl"]) for c in added], [(self.rows[2]["path"], "CC-MAIN-2019-04")])
        # CC-MAIN-2025-38 was read in full before (it holds pointers), and the search stops once EO:3 is found.
        self.assertTrue(all("CC-MAIN-2019-04" in u for u in self.calls), self.calls)
        self.assertEqual(result["no_capture_found"], [])
        self.calls.clear()
        m.run_backfill_index(self.base, self.out, {"EO:2", "EO:3"}, ["CC-MAIN-2017-01"], m.Throttle(0), m.Throttle(0))
        self.assertEqual(self.calls, [])  # every target has a pointer now: no request at all

    def test_index_falls_back_to_one_wayback_query_per_page(self):
        cdx = [["original", "timestamp", "digest"], [self.rows[2]["url"], "20240101000000", "W1"],
               [self.rows[2]["url"], "20250101000000", "W2"], [APP + "/documents/executive-order-9", "20250101000000", "W9"]]
        self.responses = {"https://web.archive.org/cdx/search/cdx?": (200, {}, json.dumps(cdx).encode())}
        m.run_backfill_index(self.base, self.out, {"EO:3"}, [], m.Throttle(0), m.Throttle(0))
        self.assertEqual(len(self.calls), 1)
        self.assertIn("executive-order-3", self.calls[0])
        self.assertEqual([(c["archive"], c["timestamp"]) for c in live.lines(self.out / "MIRROR_INDEX.jsonl")],
                         [("wayback", "20250101000000")])

    def test_documents_append_capture_beside_live_text(self):
        before = self.snapshot()
        self.responses = {"https://data.commoncrawl.org/crawl-data/two.warc.gz": (206, {}, self.raw2)}
        state = m.run_backfill_documents(self.base, self.out, self.cache, {"EO:2", "EO:3"}, 2, 0, {"common-crawl", "wayback"})
        self.assertEqual(self.snapshot(), before)  # base untouched, live text included
        docs = live.lines(self.out / "MIRROR_DOCUMENTS.jsonl")
        self.assertEqual(len(docs), 1)
        d = docs[0]
        self.assertEqual((d["instrument_id"], d["route"], d["live_backfill"]), ("EO:2", "archive/common-crawl", True))
        self.assertEqual(d["text_path"], "texts/executive-order-2.capture.txt")
        self.assertEqual(d["live_comparison"]["live_page_sha256"], "c" * 64)
        self.assertFalse(d["live_comparison"]["text_agrees"])
        self.assertEqual(hashlib.sha256((self.out / d["text_path"]).read_bytes()).hexdigest(), d["text_sha256"])
        self.assertEqual(d["capture"]["warc_offset"], 100)
        frag = live.lines(self.out / "MIRROR_FRAGMENTS.jsonl")
        self.assertEqual([(f["instrument_id"], f["data"]["text_path"]) for f in frag], [("EO:2", d["text_path"])])
        self.assertEqual(len(live.lines(self.out / "MIRROR_SOURCES.jsonl")), 1)
        self.assertEqual(state["still_without_capture"], ["EO:3"])
        self.calls.clear()
        m.run_backfill_documents(self.base, self.out, self.cache, {"EO:2", "EO:3"}, 2, 0, {"common-crawl"})
        self.assertEqual(self.calls, [])  # saved pages are not read again

    def test_identity_mismatch_is_a_permanent_failure_without_rows(self):
        wrong = warc(page(7), self.rows[1]["url"])
        index = live.lines(self.base / "MIRROR_INDEX.jsonl")
        index[1]["warc_length"] = len(wrong)
        write(self.base / "MIRROR_INDEX.jsonl", index)
        self.responses = {"https://data.commoncrawl.org/": (206, {}, wrong)}
        m.run_backfill_documents(self.base, self.out, self.cache, {"EO:2"}, 1, 0, {"common-crawl"})
        self.assertEqual(live.lines(self.out / "MIRROR_DOCUMENTS.jsonl"), [])
        fail = live.lines(self.out / "MIRROR_FAILURES.jsonl")
        self.assertTrue(fail[0]["reason"].startswith("identity_mismatch: listing EO:2 page EO:7"))
        self.assertEqual(m.backfill_targets(self.base, self.out, {"EO:2"}), [])

    def test_archive_outage_is_retried_next_run(self):
        def down(url, headers):
            raise m.ArchiveError("HTTP 503")
        self.responses = {"https://data.commoncrawl.org/": down}
        m.run_backfill_documents(self.base, self.out, self.cache, {"EO:2"}, 1, 0, {"common-crawl"})
        self.assertEqual(live.lines(self.out / "MIRROR_FAILURES.jsonl"), [])
        self.assertEqual(len(m.backfill_targets(self.base, self.out, {"EO:2"})), 1)

    def test_local_run_into_base_is_append_only(self):
        before = self.snapshot()
        self.responses = {"https://data.commoncrawl.org/": (206, {}, self.raw2)}
        m.run_backfill_documents(self.base, self.base, self.cache, {"EO:2"}, 1, 0, {"common-crawl"})
        after = self.snapshot()
        for name, data in before.items():
            self.assertTrue(after[name].startswith(data), name)
        self.assertEqual(after["texts/executive-order-2.txt"], b"live text\n")
        self.assertIn("texts/executive-order-2.capture.txt", after)

    def test_merge_appends_once_and_refuses_bad_rows(self):
        self.responses = {"https://data.commoncrawl.org/": (206, {}, self.raw2)}
        m.run_backfill_documents(self.base, self.out, self.cache, {"EO:2"}, 1, 0, {"common-crawl"})
        before = self.snapshot()
        counts = m.run_merge(self.out, self.base)
        self.assertEqual(counts["MIRROR_DOCUMENTS.jsonl"], 1)
        after = self.snapshot()
        for name, data in before.items():
            self.assertTrue(after[name].startswith(data), name)
        self.assertEqual(after["texts/executive-order-2.txt"], b"live text\n")
        self.assertEqual(after["texts/executive-order-2.capture.txt"], (self.out / "texts/executive-order-2.capture.txt").read_bytes())
        self.assertEqual(m.live_only_ids(self.base), ["EO:3"])
        again = m.run_merge(self.out, self.base)
        self.assertEqual(sum(again.values()), 0)
        self.assertEqual(self.snapshot(), after)
        # A tampered delta (record names another order) is refused before anything is written.
        docs = live.lines(self.out / "MIRROR_DOCUMENTS.jsonl")
        docs[0].update(path=self.rows[2]["path"], instrument_id="EO:3")
        write(self.out / "MIRROR_DOCUMENTS.jsonl", docs)
        with self.assertRaises(SystemExit):
            m.run_merge(self.out, self.base)
        self.assertEqual(self.snapshot(), after)

    def test_audit_sample_ignores_backfill_rows(self):
        out = self.tmp / "audit"
        out.mkdir()
        rows = [{"path": f"/documents/executive-order-{i:02d}", "route": "archive/common-crawl", "sha256": "s",
                 "text_sha256": "t"} for i in range(20)]
        write(out / "MIRROR_DOCUMENTS.jsonl", rows)
        _, audit_before = live.mirror_covered(out, 4)
        extra = [{"path": f"/documents/executive-order-0{i}a", "route": "archive/common-crawl", "sha256": "s",
                  "text_sha256": "t", "live_backfill": True} for i in range(5)]
        write(out / "MIRROR_DOCUMENTS.jsonl", rows + extra)
        skip, audit_after = live.mirror_covered(out, 4)
        self.assertEqual(set(audit_after), set(audit_before))
        self.assertTrue(all(r["path"] in skip for r in extra))


class TruncatedReadRetry(unittest.TestCase):
    def test_incomplete_read_is_retried_not_fatal(self):
        import http.client
        from unittest import mock
        calls = {"n": 0}

        class Resp:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise http.client.IncompleteRead(b"")
                return b"ok"

        with mock.patch.object(m._OPENER, "open", return_value=Resp()), mock.patch.object(m.time, "sleep"):
            status, _, body = m.http_get("https://index.commoncrawl.org/collinfo.json")
        self.assertEqual((status, body, calls["n"]), (200, b"ok", 2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
