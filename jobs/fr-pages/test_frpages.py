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
import hashlib  # noqa: E402

ISSUE_BYTES = b"%PDF-1.4 fake issue"

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


def make_pdf(raw, first, last):
    """Stand-in for extract_pdf: deterministic bytes naming the source and the pages."""
    return b"%PDF-1.4 extract of " + hashlib.sha256(raw).hexdigest()[:16].encode() + f" pages {first}-{last}".encode(), "fake 1"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def routes(pdf=ISSUE_BYTES):
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
        s = F.run(str(self.root), str(self.job), str(out1), str(self.cache), "", transport=tr, extract=extract, log=lambda *a: None, make_pdf=make_pdf)
        self.assertEqual((s["pages_held"], s["committed_pdfs"], s["failures"]), (1, 1, 0))
        rec = json.loads((out1 / "SOURCES.jsonl").read_text())
        self.assertEqual(rec["instrument_ids"], ["PLO:936", "EO:7185", "EO:7212"])
        self.assertEqual(rec["url"], ISSUE + "#page=9")
        self.assertEqual(rec["issue_url"], ISSUE)
        self.assertEqual(rec["issue_sha256"], sha(ISSUE_BYTES))
        self.assertEqual(rec["issue_pdf_pages"], [9, 9])
        self.assertEqual(rec["issue_printed_pages"], [769])
        self.assertEqual(rec["location_confidence"], "high")
        extract_bytes, _ = make_pdf(ISSUE_BYTES, 8, 8)
        self.assertEqual(rec["sha256"], sha(extract_bytes))
        self.assertEqual(rec["cache_path"], f"captures/{sha(extract_bytes)}.pdf")
        self.assertEqual((out1 / rec["cache_path"]).read_bytes(), extract_bytes)
        self.assertIn("issue_sha256", rec["derivation"])
        # The whole issue is never committed.
        self.assertEqual([p.name for p in (out1 / "captures").iterdir()], [f"{sha(extract_bytes)}.pdf"])
        text = (out1 / rec["text_path"]).read_text()
        self.assertIn("Public Land Order 936", text)
        self.assertNotIn("NEIGHBOUR DOCUMENT", text)
        self.assertIn("PDF pages 9-9 of 10", rec["page_or_item"])
        # Second run: the previous output is the prior generation; nothing is requested.
        out2 = pathlib.Path(self.tmp.name) / "out2"
        out2.mkdir()
        tr2 = Transport({})
        s2 = F.run(str(self.root), str(self.job), str(out2), str(self.cache) + "2", str(out1), transport=tr2,
                   extract=extract, log=lambda *a: None, make_pdf=make_pdf)
        self.assertEqual((s2["pages_held"], s2["carried_forward"], s2["requests"]), (1, 1, 0))
        self.assertEqual(tr2.calls, [])
        self.assertTrue((out2 / rec["cache_path"]).is_file())

    def test_extract_over_cap_is_record_only(self):
        (self.job / "settings.json").write_text(json.dumps({"min_interval_seconds": 0, "commit_max_bytes": 10}))
        out = pathlib.Path(self.tmp.name) / "out"
        out.mkdir()
        s = F.run(str(self.root), str(self.job), str(out), str(self.cache), "", transport=Transport(routes()),
                  extract=extract, log=lambda *a: None, make_pdf=make_pdf)
        rec = json.loads((out / "SOURCES.jsonl").read_text())
        self.assertNotIn("cache_path", rec)
        self.assertEqual(s["record_only"], 1)

    def test_whole_issue_record_of_first_runs_is_converted_without_requests(self):
        prior = pathlib.Path(self.tmp.name) / "prior"
        (prior / "captures").mkdir(parents=True)
        (prior / "texts").mkdir()
        (prior / "captures" / f"{sha(ISSUE_BYTES)}.pdf").write_bytes(ISSUE_BYTES)
        (prior / "texts/FR_19_769.txt").write_text("old text")
        (prior / "SOURCES.jsonl").write_text(json.dumps({
            "url": ISSUE, "sha256": sha(ISSUE_BYTES), "bytes": len(ISSUE_BYTES), "cache_path": f"captures/{sha(ISSUE_BYTES)}.pdf",
            "text_path": "texts/FR_19_769.txt", "fr_volume": 19, "fr_page": 769, "link_page_hint": 9,
            "route": "official/govinfo_link_fr"}) + "\n")
        out = pathlib.Path(self.tmp.name) / "out"
        out.mkdir()
        tr = Transport({})
        s = F.run(str(self.root), str(self.job), str(out), str(self.cache), str(prior), transport=tr,
                  extract=extract, log=lambda *a: None, make_pdf=make_pdf)
        self.assertEqual((s["pages_held"], s["requests"]), (1, 0))
        self.assertEqual(tr.calls, [])
        rec = json.loads((out / "SOURCES.jsonl").read_text())
        self.assertEqual(rec["issue_sha256"], sha(ISSUE_BYTES))
        self.assertNotEqual(rec["sha256"], sha(ISSUE_BYTES))
        self.assertFalse((out / "captures" / f"{sha(ISSUE_BYTES)}.pdf").exists())
        self.assertTrue((out / rec["cache_path"]).is_file())

    def test_refresh_keeps_earlier_extract_when_issue_hash_matches(self):
        out1 = pathlib.Path(self.tmp.name) / "out1"
        out1.mkdir()
        F.run(str(self.root), str(self.job), str(out1), str(self.cache), "", transport=Transport(routes()),
              extract=extract, log=lambda *a: None, make_pdf=make_pdf)
        first = json.loads((out1 / "SOURCES.jsonl").read_text())
        out2 = pathlib.Path(self.tmp.name) / "out2"
        out2.mkdir()
        os.environ["FR_PAGES_REFRESH"] = "1"
        try:
            F.run(str(self.root), str(self.job), str(out2), str(self.cache) + "2", str(out1), transport=Transport(routes()),
                  extract=extract, log=lambda *a: None, make_pdf=lambda raw, a, b: (b"%PDF other pypdf version", "fake 2"))
        finally:
            del os.environ["FR_PAGES_REFRESH"]
        second = json.loads((out2 / "SOURCES.jsonl").read_text())
        self.assertEqual(second["sha256"], first["sha256"])
        self.assertEqual(second["extract_tool"], "fake 1")
        self.assertEqual(sha((out2 / second["cache_path"]).read_bytes()), first["sha256"])

    def test_budget(self):
        (self.job / "settings.json").write_text(json.dumps({"min_interval_seconds": 0, "max_requests": 0}))
        out = pathlib.Path(self.tmp.name) / "out"
        out.mkdir()
        s = F.run(str(self.root), str(self.job), str(out), str(self.cache), "", transport=Transport(routes()),
                  extract=extract, log=lambda *a: None, make_pdf=make_pdf)
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
        s = F.run(str(self.root), str(self.job), str(out), str(self.cache), "", transport=tr, extract=extract, log=lambda *a: None, make_pdf=make_pdf)
        rec = json.loads((out / "SOURCES.jsonl").read_text())
        self.assertEqual(rec["route"], "official/govinfo_link_fr")   # fell back to the issue PDF
        self.assertEqual(rec["issue_url"], ISSUE)
        self.assertEqual(s["pages_held"], 1)


class RealExtract(unittest.TestCase):
    def test_deterministic_page_extract(self):
        try:
            import pypdf
        except ImportError:
            self.skipTest("pypdf not installed")
        w = pypdf.PdfWriter()
        for size in (200, 300, 400):
            w.add_blank_page(width=size, height=size)
        buf = io.BytesIO()
        w.write(buf)
        a, tool = F.extract_pdf(buf.getvalue(), 1, 2)
        b, _ = F.extract_pdf(buf.getvalue(), 1, 2)
        self.assertEqual(a, b)
        self.assertTrue(tool.startswith("pypdf "))
        pages = pypdf.PdfReader(io.BytesIO(a)).pages
        self.assertEqual([round(float(p.mediabox.width)) for p in pages], [300, 400])


class ClaimCheckerHeld(unittest.TestCase):
    """jobs/claim-checker/sources.py must count a committed extract as held bytes (re-hashed on the machine)."""

    def test_extract_counts_as_held(self):
        src = HERE.parent / "claim-checker" / "sources.py"
        if not src.is_file():
            self.skipTest("claim-checker not in this checkout")
        import importlib.util
        spec = importlib.util.spec_from_file_location("cc_sources", src)
        S = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(S)
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            out = repo / "jobs/fr-pages/output"
            out.mkdir(parents=True)
            (repo / "jobs/fr-pages/data").mkdir()
            (repo / "jobs/fr-pages/data/WANTED.jsonl").write_text(json.dumps(
                {"want_id": "w1", "plo": 936, "fr": "19 FR 769", "targets": ["EO:7185"]}) + "\n")
            (repo / "jobs/fr-pages/settings.json").write_text(json.dumps({"min_interval_seconds": 0}))
            F.run(str(repo), str(repo / "jobs/fr-pages"), str(out), str(repo / "cache"), "", transport=Transport(routes()),
                  extract=extract, log=lambda *a: None, make_pdf=make_pdf)
            rec = json.loads((out / "SOURCES.jsonl").read_text())
            index = S.HeldIndex()
            S.load_job_sources(index, repo)
            copies = index.lookup_sha(rec["sha256"])
            self.assertEqual(len(copies), 1)
            self.assertEqual(copies[0].custody, "job_cache")
            self.assertTrue(copies[0].bytes_kept)
            self.assertTrue(S.TextReader().verify_bytes(copies[0]))
            self.assertEqual(index.lookup_sha(rec["issue_sha256"]), [])


if __name__ == "__main__":
    unittest.main()
