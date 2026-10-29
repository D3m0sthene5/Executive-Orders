"""Offline tests for fr-pages (injected HTTP transport and page texts; no network, no PDF library)."""
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import frpages as F  # noqa: E402

ISSUE = "https://www.govinfo.gov/content/pkg/FR-1954-02-10/pdf/FR-1954-02-10.pdf"
LINK = "https://www.govinfo.gov/link/fr/19/769"
FIX = HERE / "fixtures"


def issue_pages():
    """Ten pages printed 761-770; PLO 936 on page 769 with its filing line, a neighbour after it."""
    text = FIX.joinpath("fr_1954-02-10_pages.txt").read_text(encoding="utf-8")
    return [p for p in text.split("\f")]


def extract(raw, wanted=None):
    pages = issue_pages()
    return pages if wanted is None else [p if i in wanted else "" for i, p in enumerate(pages)]


class Transport:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def __call__(self, url, headers, timeout):
        self.calls.append(url)
        status, hdrs, body = self.routes.get(url, (404, {}, b""))
        if callable(body):
            body = body()
        return status, dict(hdrs, **{"content-length": str(len(body))}), io.BytesIO(body)


def routes(pdf=b"%PDF-1.4 fake issue"):
    return {"https://www.govinfo.gov/robots.txt": (404, {}, b""),
            LINK: (302, {"location": ISSUE + "#page=9"}, b""),
            ISSUE: (200, {}, pdf)}


class Resolve(unittest.TestCase):
    def test_plo_table_and_failures(self):
        plos = {936: {"fr_volume": "19", "fr_page": "769"}, 945: {"fr_volume": "19", "fr_page": "1583"}}
        wanted = [{"want_id": "a", "plo": 936, "targets": ["EO:7185"]},
                  {"want_id": "b", "plo": 936, "fr": "19 FR 769", "targets": ["EO:7212"]},
                  {"want_id": "c", "plo": 945, "fr": "19 FR 1584", "targets": ["EO:5214"]},
                  {"want_id": "d", "plo": 4079, "targets": ["EO:7373"]}, {"_bad_line": 7}]
        jobs, failures = F.resolve(wanted, plos)
        by = {(j["vol"], j["page"]): j for j in jobs}
        self.assertEqual(by[(19, 769)]["targets"], ["EO:7185", "EO:7212"])
        self.assertIn("fr_citation_from_blm_plo_table", by[(19, 769)]["flags"])
        self.assertIn("blm_plo_table_cites_19_FR_1583", by[(19, 1584)]["flags"])
        self.assertEqual(sorted(f["reason"] for f in failures), ["malformed_json", "plo_not_in_plo_table_and_no_fr_citation"])


class Locate(unittest.TestCase):
    def test_heading_and_filing(self):
        job = {"vol": 19, "page": 769, "plo": 936, "printed_id": "PLO:936"}
        first, last, notes, conf = F.locate(issue_pages(), job)
        self.assertEqual((first, last, conf), (8, 8, "high"))
        job = {"vol": 19, "page": 769, "plo": 999, "printed_id": "PLO:999"}
        first, last, notes, conf = F.locate(issue_pages(), job)
        self.assertEqual((first, last, conf), (8, 9, "medium"))
        self.assertIn("instrument_heading_not_found_cited_page_and_next_taken", notes)


class Run(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = pathlib.Path(self.tmp.name)
        self.root, self.job, self.cache = t / "repo", t / "job", t / "cache"
        (self.job / "data").mkdir(parents=True)
        (self.job / "data/WANTED.jsonl").write_text("# comment\n" + json.dumps(
            {"want_id": "w1", "plo": 936, "fr": "19 FR 769", "targets": ["EO:7185", "EO:7212"]}) + "\n")
        (self.job / "settings.json").write_text(json.dumps({"min_interval_seconds": 0, "commit_max_bytes": 1000}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_fetch_commit_and_carry_forward(self):
        out1 = pathlib.Path(self.tmp.name) / "out1"
        out1.mkdir()
        tr = Transport(routes())
        s = F.run(str(self.root), str(self.job), str(out1), str(self.cache), "", transport=tr, extract=extract, log=lambda *a: None)
        self.assertEqual((s["pages_held"], s["committed_pdfs"], s["failures"]), (1, 1, 0))
        rec = json.loads((out1 / "SOURCES.jsonl").read_text())
        self.assertEqual(rec["instrument_ids"], ["PLO:936", "EO:7185", "EO:7212"])
        self.assertEqual(rec["url"], ISSUE)
        self.assertEqual(rec["location_confidence"], "high")
        self.assertTrue((out1 / rec["cache_path"]).is_file())
        text = (out1 / rec["text_path"]).read_text()
        self.assertIn("Public Land Order 936", text)
        self.assertNotIn("NEIGHBOUR DOCUMENT", text)
        self.assertIn("PDF pages 9-9 of 10", rec["page_or_item"])
        # Second run: the previous output is the prior generation; nothing is requested.
        out2 = pathlib.Path(self.tmp.name) / "out2"
        out2.mkdir()
        tr2 = Transport({})
        s2 = F.run(str(self.root), str(self.job), str(out2), str(self.cache) + "2", str(out1), transport=tr2,
                   extract=extract, log=lambda *a: None)
        self.assertEqual((s2["pages_held"], s2["carried_forward"], s2["requests"]), (1, 1, 0))
        self.assertEqual(tr2.calls, [])
        self.assertTrue((out2 / rec["cache_path"]).is_file())

    def test_large_pdf_is_record_only(self):
        out = pathlib.Path(self.tmp.name) / "out"
        out.mkdir()
        s = F.run(str(self.root), str(self.job), str(out), str(self.cache), "", transport=Transport(routes(b"%PDF" + b"x" * 5000)),
                  extract=extract, log=lambda *a: None)
        rec = json.loads((out / "SOURCES.jsonl").read_text())
        self.assertNotIn("cache_path", rec)
        self.assertEqual(s["record_only"], 1)

    def test_budget(self):
        (self.job / "settings.json").write_text(json.dumps({"min_interval_seconds": 0, "max_requests": 0}))
        out = pathlib.Path(self.tmp.name) / "out"
        out.mkdir()
        s = F.run(str(self.root), str(self.job), str(out), str(self.cache), "", transport=Transport(routes()),
                  extract=extract, log=lambda *a: None)
        self.assertEqual((s["pages_held"], s["requests"]), (0, 0))
        fail = json.loads((out / "FAILURES.jsonl").read_text())
        self.assertEqual(fail["reason"], "request_or_byte_budget_exhausted")

    def test_unstable_slice_rejected(self):
        (self.job / "settings.json").write_text(json.dumps({"min_interval_seconds": 0, "try_issue_slice": True}))
        r = routes()
        n = {"i": 0}

        def changing():
            n["i"] += 1
            return b"%PDF slice " + str(n["i"]).encode()
        r["https://archives.federalregister.gov/robots.txt"] = (404, {}, b"")
        r["https://archives.federalregister.gov/issue_slice/1954/2/10/769-769.pdf"] = (200, {}, changing)
        out = pathlib.Path(self.tmp.name) / "out"
        out.mkdir()
        tr = Transport(r)
        s = F.run(str(self.root), str(self.job), str(out), str(self.cache), "", transport=tr, extract=extract, log=lambda *a: None)
        rec = json.loads((out / "SOURCES.jsonl").read_text())
        self.assertEqual(rec["route"], "official/govinfo_link_fr")   # fell back to the issue PDF
        self.assertEqual(rec["url"], ISSUE)
        self.assertEqual(s["pages_held"], 1)


if __name__ == "__main__":
    unittest.main()
