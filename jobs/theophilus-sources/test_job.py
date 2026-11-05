"""Offline tests for Theophilus (fake transport, no network). Run: python -I test_job.py"""
import csv, io, json, sys, tempfile, unittest, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import theophilus as T

USC_XML = b"""<?xml version="1.0"?>
<uscDoc xmlns="http://xml.house.gov/schemas/uslm/1.0"><main><title identifier="/us/usc/t50">
<chapter><section identifier="/us/usc/t50/s1701"><num value="1701">&#167;1701.</num><heading>Unusual threat</heading>
<content>Any authority granted.</content>
<notes><note topic="executiveOrder"><p>EX. ORD. NO. 12170. Iran.</p>
<quotedContent><section><num>1-101.</num><content>nested quoted</content></section></quotedContent></note></notes></section>
<section identifier="/us/usc/t50/s1702"><num>&#167;1702.</num><content>Other.</content></section></chapter></title></main></uscDoc>"""

CFR_XML = b"""<?xml version="1.0"?><ECFR><DIV1 TYPE="TITLE" N="5"><DIV5 TYPE="PART" N="591"><HEAD>PART 591</HEAD>
<DIV8 TYPE="SECTION" N="&#167; 591.205"><HEAD>&#167; 591.205 Allowance.</HEAD><P>Text of 205.</P></DIV8>
<DIV8 TYPE="SECTION" N="&#167; 591.206"><HEAD>&#167; 591.206 Other.</HEAD><P>Text of 206.</P></DIV8></DIV5>
<DIV5 TYPE="PART" N="592"><DIV8 TYPE="SECTION" N="&#167; 592.1"><P>Skip.</P></DIV8></DIV5></DIV1></ECFR>"""

NOTICE = (b"Notice of February 14, 2023. Continuation of the National Emergency With Respect to Iran. "
          b"Pursuant to Executive Order 12170 and E.O. 13222 and Executive Orders 12957, 99999 ... Executive Order (E.O.) 12170.")


class Parse(unittest.TestCase):
    def test_citations(self):
        P = T.parse_citation
        self.assertEqual(P("50 U.S.C. 1701 note"), ("usc", 50, "1701"))
        self.assertEqual(P("42 U.S.C. 2000e–16"), ("usc", 42, "2000e-16"))
        self.assertEqual(P("5 CFR 591.205"), ("cfr", 5, "591", "591.205"))
        self.assertEqual(P("5 CFR part 591"), ("cfr", 5, "591", None))
        self.assertEqual(P("31 CFR part 128, Appendix A to Part 128"), ("cfr", 31, "128", None))
        self.assertEqual(P("41 CFR 101-39.101-1"), ("cfr", 41, "101-39", "101-39.101-1"))
        self.assertEqual(P("33 CFR 6.18-1"), ("cfr", 33, "6", "6.18-1"))
        self.assertEqual(P("10 U.S.C. subtitle A, pt. II, ch. 57 note")[0], "bad")
        self.assertEqual(P("5 U.S.C. 1...5 note")[0], "bad")

    def test_mentions(self):
        reg = {"EO:12170", "EO:13222", "EO:12957", "EO:5"}
        self.assertEqual(T.mentioned_orders(NOTICE.decode(), reg), ["EO:12170", "EO:12957", "EO:13222"])
        html = b"<html><pre>pursuant to E.O.&nbsp;13222</pre></html>"
        self.assertEqual(T.mentioned_orders(T.notice_plain_text(html), reg), ["EO:13222"])

    def test_fr_page(self):
        raw = json.dumps({"total_pages": 3, "results": [{"document_number": "x", "title": "Continuation of the National Emergency"}]}).encode()
        n, res = T.parse_fr_page(raw)
        self.assertEqual((n, len(res)), (3, 1))
        self.assertTrue(T.is_continuation(res[0]["title"]))
        self.assertFalse(T.is_continuation("Notice of something"))

    def test_usc_extract(self):
        f = T.extract_usc_sections(io.BytesIO(USC_XML), 50, {"1701", "9999"})
        self.assertEqual(list(f), ["1701"])
        self.assertIn("Any authority granted.", f["1701"])
        self.assertIn("EX. ORD. NO. 12170", f["1701"])
        self.assertIn("nested quoted", f["1701"])
        self.assertNotIn("Other.", f["1701"])

    def test_cfr_extract(self):
        f = T.extract_cfr(io.BytesIO(CFR_XML), {("591", "591.205"), ("592", None), ("591", None)})
        self.assertIn("Text of 205.", f[("591", "591.205")])
        self.assertNotIn("Text of 206.", f[("591", "591.205")])
        self.assertIn("Text of 206.", f[("591", None)])
        self.assertIn("Skip.", f[("592", None)])
        self.assertEqual(list(T.extract_cfr(io.BytesIO(CFR_XML), {("591", "591.999")})), [])


class Net(unittest.TestCase):
    def test_retry_converts_socket_errors(self):
        def boom():
            raise TimeoutError("handshake timed out")
        T.time.sleep = lambda *_: None
        with self.assertRaises(T.FetchError) as cm:
            T.retry(boom, tries=2)
        self.assertEqual(T.reason_of(cm.exception), "network_error")


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class EndToEnd(unittest.TestCase):
    def test_run(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            repo, out = d / "repo", d / "out"
            j = repo / "jobs"
            write_csv(j / "domesday-register/output/REGISTER.csv",
                      [{"instrument_id": i} for i in ("EO:12170", "EO:13222", "EO:5", "EO:6")])
            write_csv(j / "readiness-tracker/output/READINESS_BY_ORDER.csv", [
                {"instrument_id": "EO:5", "ready_for_human_review": "no", "blockers": "A|CURRENT_BASIS_UNPROVED"},
                {"instrument_id": "EO:6", "ready_for_human_review": "yes", "blockers": "CURRENT_BASIS_UNPROVED"},
                {"instrument_id": "EO:12170", "ready_for_human_review": "no", "blockers": "CURRENT_BASIS_UNPROVED"}])
            write_csv(j / "current-law/output/ORDERS_CURRENT_LAW.csv", [
                {"instrument_id": "EO:5", "provisional_status": "yes", "usc_predicate_citations": "50 U.S.C. 1701 note ; 50 U.S.C. 9 note ; 10 U.S.C. ch. 57 note",
                 "cfr_predicate_citations": "5 CFR 591.205 ; 5 CFR part 591"},
                {"instrument_id": "EO:6", "provisional_status": "yes", "usc_predicate_citations": "50 U.S.C. 1702", "cfr_predicate_citations": ""},
                {"instrument_id": "EO:12170", "provisional_status": "no", "usc_predicate_citations": "50 U.S.C. 1701", "cfr_predicate_citations": ""}])
            (j / "current-law/output/SUMMARY.json").write_text(json.dumps({"usc": {"release_point": "119-121"}}))
            zb = io.BytesIO()
            with zipfile.ZipFile(zb, "w") as z:
                z.writestr("xml_usc50@119-121/usc50.xml", USC_XML)
            calls = []

            def net(url, headers, timeout):
                calls.append(url)
                if url.endswith("/robots.txt"):
                    body = b"User-agent: *\nDisallow: /api/versioner/v1/full/" if "ecfr.gov" in url else b"User-agent: *\nAllow: /"
                    return 200, {}, io.BytesIO(body)
                if "documents.json" in url:
                    res = [{"document_number": "2023-1", "title": "Continuation of the National Emergency With Respect to Iran",
                            "publication_date": "2023-02-15", "citation": "88 FR 1", "raw_text_url": "https://www.federalregister.gov/t/2023-1.txt",
                            "html_url": "h", "pdf_url": "p"},
                           {"document_number": "2023-2", "title": "Something else", "raw_text_url": "https://www.federalregister.gov/t/2023-2.txt"},
                           {"document_number": "2023-3", "title": "Continuation of the National Emergency X", "raw_text_url": "https://www.federalregister.gov/t/2023-3.txt"}]
                    return 200, {}, io.BytesIO(json.dumps({"total_pages": 1, "results": res}).encode())
                if url.endswith("2023-1.txt"):
                    return 200, {}, io.BytesIO(NOTICE)
                if url.endswith("2023-3.txt"):
                    return 404, {}, io.BytesIO(b"")
                if url.endswith("titles.json"):
                    return 200, {}, io.BytesIO(json.dumps({"titles": [{"number": 5, "up_to_date_as_of": "2026-11-03"}], "meta": {}}).encode())
                if url.endswith(".zip"):
                    return 200, {}, io.BytesIO(zb.getvalue())
                if "ECFR-title5.xml" in url:
                    return 200, {}, io.BytesIO(CFR_XML)
                return 404, {}, io.BytesIO(b"")
            s = T.run_job(repo, out, d / "cache", 2, transport=net, interval=0)
            self.assertEqual(s["notices"], {"listed": 2, "fetched": 1})
            self.assertEqual(s["orders_named_in_notices"], 2)
            self.assertEqual(s["sections_fetched"], {"usc": 1, "cfr": 2})
            self.assertEqual(s["eligible_yes_orders"], 1)
            self.assertEqual(s["yes_orders_covered_by_sections"], 1)
            self.assertEqual(s["failures_by_reason"].get("http_404"), 1)
            self.assertEqual(s["failures_by_reason"].get("section_not_found_in_title_xml"), 1)
            self.assertEqual(s["failures_by_reason"].get("usc_citation_not_a_single_section"), 1)
            self.assertFalse(any("/full/" in u for u in calls))
            recs = [json.loads(l) for l in open(out / "SOURCES.jsonl")]
            need = {"source_id", "instrument_ids", "url", "sha256", "bytes", "content_type", "retrieved_utc", "route",
                    "page_or_item", "text_path", "cache_path", "notes"}
            for r in recs:
                self.assertEqual(set(r), need)
                self.assertEqual(T.sha((out / r["text_path"]).read_bytes()), r["sha256"])
            by = {r["source_id"]: r for r in recs}
            self.assertEqual(by["fr:notice:2023-1"]["instrument_ids"], ["EO:12170", "EO:13222"])
            self.assertEqual(by["fr:notice:2023-1"]["sha256"], T.sha(NOTICE))
            self.assertEqual(by["usc:119-121:t50:s1701"]["instrument_ids"], ["EO:5"])
            self.assertIn("cfr:t5:591.205", by)
            self.assertIn("cfr:t5:part591", by)
            self.assertTrue((out / "FAILURES.jsonl").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=1)
