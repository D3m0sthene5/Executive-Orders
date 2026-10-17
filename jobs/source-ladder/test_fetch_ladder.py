"""Unit tests for the source ladder. Small fixtures, no network."""
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eo_extract  # noqa: E402
import fetch_ladder as fl  # noqa: E402
import fr_pages  # noqa: E402
import ladder_queue  # noqa: E402
import ofr_index  # noqa: E402


def make_pdf(pages):
    """A tiny valid PDF, one text line per row, one page per list item."""
    objs = []
    kids = []
    font_id = 3
    objs.append(None)  # 1 catalog
    objs.append(None)  # 2 pages
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for lines in pages:
        content = "BT /F1 10 Tf 40 760 Td 12 TL " + " ".join(
            "(" + ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") Tj T*" for ln in lines) + " ET"
        cb = content.encode("latin-1")
        objs.append(b"<< /Length %d >>\nstream\n" % len(cb) + cb + b"\nendstream")
        content_id = len(objs)
        objs.append(None)
        page_id = len(objs)
        objs[page_id - 1] = (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents %d 0 R "
                             b"/Resources << /Font << /F1 %d 0 R >> >> >>" % (content_id, font_id))
        kids.append(page_id)
    objs[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[1] = b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % k for k in kids) + b"] /Count %d >>" % len(kids)
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % i + body + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1))
    for off in offsets:
        out.write(b"%010d 00000 n \n" % off)
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref))
    return out.getvalue()


class FakeResp:
    def __init__(self, body):
        self.buf = io.BytesIO(body)

    def read(self, n=-1):
        return self.buf.read(n)

    def close(self):
        pass


class FakeTransport:
    """routes: url -> list of (status, headers, body); the last entry repeats."""

    def __init__(self, routes, robots=None):
        self.routes = routes
        self.robots = robots or {}
        self.calls = []

    def __call__(self, url, headers, timeout):
        self.calls.append(url)
        if url.endswith("/robots.txt"):
            host = url.split("/")[2]
            if host in self.robots:
                return 200, {}, FakeResp(self.robots[host].encode())
            return 404, {}, FakeResp(b"")
        seq = self.routes.get(url)
        if not seq:
            return 404, {"content-type": "text/html"}, FakeResp(b"<html>not found</html>")
        status, hdrs, body = seq.pop(0) if len(seq) > 1 else seq[0]
        return status, hdrs, FakeResp(body)


PDF = make_pdf([["Executive Order 12345 of May 1, 1990", "Text of the order.", "[FR Doc. 90-1 Filed 5-2-90]"]])
CAPTCHA = b"<html><head><title>Just a moment...</title></head><body>" + b"x" * 3000 + b"captcha</body></html>"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.sleeps = []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def fetcher(self, transport, **kw):
        return fl.Fetcher(self.tmp / "cache", transport=transport, sleep=self.sleeps.append,
                          clock=lambda: 1000.0, log=lambda *a: None, **kw)


class CitationTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(fl.parse_citation("STAT::66 Stat. 259"), ("STAT", {"volume": 66, "page": 259}))
        self.assertEqual(fl.parse_citation("EO::9337"), ("EO", {"number": "9337"}))
        self.assertEqual(fl.parse_citation("Executive Order No. 7677-A"), ("EO", {"number": "7677A"}))
        self.assertEqual(fl.parse_citation("2 FR 63"), ("FR", {"volume": 2, "page": 63}))
        k, p = fl.parse_citation("USC::31 U.S.C. 1552")
        self.assertEqual((k, p["title"], p["section"]), ("USC", 31, "1552"))
        self.assertEqual(fl.parse_citation("USC::43 U.S.C. 1714(j).")[1]["section"], "1714")
        self.assertEqual(fl.parse_citation("USC::50 U.S.C. 4701-4703")[1]["section"], "4701")
        self.assertEqual(fl.parse_citation("USC::16 U.S.C. 668dd(a)(6)")[1]["section"], "668dd")
        self.assertEqual(fl.parse_citation("CFR::5 CFR 6.8"), ("CFR", {"title": 5, "part": 6, "section": "8"}))
        self.assertEqual(fl.parse_citation("CFR::41 CFR 102"), ("CFR", {"title": 41, "part": 102, "section": ""}))
        self.assertEqual(fl.parse_citation("something else"), (None, {}))

    def test_alternate_forms(self):
        alts = dict(fl.alternate_forms("http://govinfo.gov/app/details/FR-1994-02-24/94-4472"))
        self.assertEqual(alts["alt_https"], "https://govinfo.gov/app/details/FR-1994-02-24/94-4472")
        self.assertEqual(alts["alt_www_host"], "https://www.govinfo.gov/app/details/FR-1994-02-24/94-4472")
        self.assertEqual(alts["alt_govinfo_content_pdf"], "https://www.govinfo.gov/content/pkg/FR-1994-02-24/pdf/94-4472.pdf")
        pdf_alts = dict(fl.alternate_forms("https://www.govinfo.gov/content/pkg/FR-1994-02-24/pdf/94-4472.pdf"))
        self.assertEqual(set(pdf_alts), {"alt_bare_host", "alt_govinfo_html"})  # never the /app/ landing page
        fr = dict(fl.alternate_forms("https://www.federalregister.gov/documents/1994/02/24/94-4472/educational-excellence"))
        self.assertEqual(fr["alt_federalregister_api_json"], "https://www.federalregister.gov/api/v1/documents/94-4472.json")

    def test_plan_order_statute(self):
        w = fl.Wanted("STAT::66 Stat. 259", ["EO:1"], urls=["https://www.govinfo.gov/content/pkg/STATUTE-66/pdf/STATUTE-66-Pg259.pdf"],
                      citation="STAT::66 Stat. 259")
        plan = fl.plan_routes(w)
        tiers = [r.tier for r in plan]
        self.assertEqual(tiers[0], "given")
        self.assertEqual(tiers, sorted(tiers, key=fl.TIER_ORDER.index))
        urls = [r.url for r in plan]
        self.assertIn("https://www.govinfo.gov/link/statute/66/259", urls)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertTrue(any(r.kind == "cdx" for r in plan))

    def test_plan_eo_from_index(self):
        rec = {"citation": "2 FR 63", "publication_date": "1937-01-12"}
        w = fl.Wanted("x", ["EO:1"], citation="EO 7532", eo_record=rec)
        urls = [r.url for r in fl.plan_routes(w)]
        self.assertEqual(urls[0], "https://www.govinfo.gov/content/pkg/FR-1937-01-12/pdf/FR-1937-01-12.pdf")
        self.assertIn("https://www.govinfo.gov/link/fr/2/63", urls)
        self.assertIn("https://en.wikisource.org/wiki/Executive_Order_7532", urls)
        only = fl.plan_routes(w, tiers=("official",))
        self.assertTrue(all(r.tier == "official" for r in only))


class ValidationTests(unittest.TestCase):
    def test_reject(self):
        self.assertEqual(fl.reject_reason(b"x", 1, "", "https://www.govinfo.gov/error", "pdf"), "govinfo_error_page")
        self.assertTrue(fl.reject_reason(CAPTCHA, len(CAPTCHA), "text/html", "https://a.gov/x", "html").startswith("bot_or_captcha"))
        self.assertEqual(fl.reject_reason(b"<html>hi</html>", 15, "text/html", "https://a.gov/x", "html"), "tiny_html")
        self.assertEqual(fl.reject_reason(b"<html>" + b"y" * 5000, 5006, "text/html", "https://a.gov/x.pdf", "pdf"), "html_instead_of_pdf")
        self.assertIsNone(fl.reject_reason(PDF, len(PDF), "application/pdf", "https://a.gov/x.pdf", "pdf"))
        self.assertEqual(fl.reject_reason(b"not json", 8, "application/json", "https://a.gov/x", "json"), "invalid_json")
        self.assertIsNone(fl.reject_reason(b"[]", 2, "application/json", "https://a.gov/x", "json"))
        self.assertEqual(fl.reject_reason(b"x", 1, "", "https://unblock.federalregister.gov/", "any"), "federalregister_unblock_page")


class FetcherTests(Base):
    def test_redirect_hint_retry_and_cache(self):
        t = FakeTransport({
            "https://www.govinfo.gov/link/fr/2/63": [(302, {"location": "https://www.govinfo.gov/content/pkg/FR-1937-01-12/pdf/FR-1937-01-12.pdf#page=4"}, b"")],
            "https://www.govinfo.gov/content/pkg/FR-1937-01-12/pdf/FR-1937-01-12.pdf": [
                (503, {"retry-after": "5"}, b""), (200, {"content-type": "application/pdf"}, PDF)],
        })
        f = self.fetcher(t)
        a = f.fetch("https://www.govinfo.gov/link/fr/2/63", "r", "pdf")
        self.assertTrue(a["accepted"], a)
        self.assertEqual(a["page_hint"], 4)
        self.assertEqual(a["final_url"], "https://www.govinfo.gov/content/pkg/FR-1937-01-12/pdf/FR-1937-01-12.pdf")
        self.assertEqual(a["sha256"], fl.sha256_bytes(PDF))
        self.assertIn(5.0, self.sleeps)  # honoured Retry-After
        before = len(t.calls)
        b = f.fetch("https://www.govinfo.gov/link/fr/2/63", "r", "pdf")
        self.assertTrue(b["from_cache"])
        self.assertEqual(len(t.calls), before)
        self.assertEqual(Path(b["path"]).read_bytes(), PDF)
        self.assertTrue(f.forget_body(b["path"]))
        self.assertIsNone(f.cached("https://www.govinfo.gov/link/fr/2/63"))

    def test_redirect_to_cached_target_is_not_downloaded_again(self):
        issue = "https://www.govinfo.gov/content/pkg/FR-1937-01-12/pdf/FR-1937-01-12.pdf"
        t = FakeTransport({issue: [(200, {"content-type": "application/pdf"}, PDF)],
                           "https://www.govinfo.gov/link/fr/2/63": [(302, {"location": issue + "#page=3"}, b"")]})
        f = self.fetcher(t)
        self.assertTrue(f.fetch(issue, "r", "pdf")["accepted"])
        a = f.fetch("https://www.govinfo.gov/link/fr/2/63", "r", "pdf")
        self.assertTrue(a["accepted"] and a["from_cache"])
        self.assertEqual((a["page_hint"], a["sha256"], a["final_url"]), (3, fl.sha256_bytes(PDF), issue))
        self.assertEqual(t.calls.count(issue), 1)

    def test_error_redirect_robots_and_https(self):
        t = FakeTransport({
            "https://www.govinfo.gov/content/pkg/STATUTE-66/pdf/STATUTE-66-Pg259.pdf": [(302, {"location": "/error"}, b"")],
            "https://blocked.example.org/doc": [(200, {}, b"x" * 5000)],
        }, robots={"blocked.example.org": "User-agent: *\nDisallow: /\n"})
        f = self.fetcher(t)
        a = f.fetch("https://www.govinfo.gov/content/pkg/STATUTE-66/pdf/STATUTE-66-Pg259.pdf", "r", "pdf")
        self.assertFalse(a["accepted"])
        self.assertEqual(a["error"], "redirect_to_error_page")
        b = f.fetch("https://blocked.example.org/doc", "r")
        self.assertEqual(b["error"], "blocked_by_robots_txt")
        self.assertNotIn("https://blocked.example.org/doc", t.calls)
        self.assertEqual(f.fetch("http://x.gov/a", "r")["error"], "not_https")

    def test_captcha_is_not_cached(self):
        t = FakeTransport({"https://a.example.org/x": [(200, {"content-type": "text/html"}, CAPTCHA)]})
        f = self.fetcher(t)
        a = f.fetch("https://a.example.org/x", "r", "html")
        self.assertFalse(a["accepted"])
        self.assertTrue(a["reject_reason"].startswith("bot_or_captcha"))
        self.assertIsNone(f.cached("https://a.example.org/x"))

    def test_budget(self):
        f = self.fetcher(FakeTransport({}), max_requests=1)
        with self.assertRaises(fl.BudgetExceeded):
            f.fetch("https://a.example.org/x", "r")
            f.fetch("https://b.example.org/x", "r")


class LadderTests(Base):
    def test_wayback_rescue(self):
        given = "https://www.govinfo.gov/content/pkg/FR-1990-05-02/pdf/90-1.pdf"
        cdx = fl.cdx_url(given)
        rows = [["timestamp", "original", "mimetype", "statuscode", "digest"],
                ["20200101000000", given, "application/pdf", "200", "AAA"]]
        t = FakeTransport({
            cdx: [(200, {"content-type": "application/json"}, json.dumps(rows).encode())],
            f"https://web.archive.org/web/20200101000000id_/{given}": [(200, {"content-type": "application/pdf"}, PDF)],
        })
        w = fl.Wanted("EO:12345", ["EO:12345"], urls=[given], citation="EO 12345",
                      eo_record={"citation": "55 FR 1", "publication_date": "1990-05-02"})
        res = fl.Ladder(self.fetcher(t), extract=eo_extract.eo_extract).walk(w)
        src = res["source"]
        self.assertIsNotNone(src, res["attempts"])
        self.assertEqual(src["route"], "wayback_given/wayback_id_")
        self.assertEqual(src["sha256"], fl.sha256_bytes(PDF))
        for key in ("source_id", "instrument_ids", "url", "sha256", "bytes", "content_type", "retrieved_utc",
                    "route", "page_or_item", "text_path", "cache_path", "notes"):
            self.assertIn(key, src)
        self.assertEqual(src["page_or_item"], "55 FR 1, PDF pages 1-1")
        self.assertIn("Executive Order 12345", res["text"])
        self.assertEqual(res["attempts"][0]["error"], "http_404")

    def test_exhausted_format(self):
        w = fl.Wanted("USC::31 U.S.C. 1552", ["EO:1", "EO:2"], citation="USC::31 U.S.C. 1552", step="shared_sources")
        res = fl.Ladder(self.fetcher(FakeTransport({}))).walk(w)
        self.assertIsNone(res["source"])
        ex = res["exhausted"]
        self.assertEqual([e["instrument_id"] for e in ex], ["EO:1", "EO:2"])
        self.assertEqual(set(ex[0]), {"instrument_id", "step", "searched", "recorded_by", "recorded_on", "note"})
        self.assertEqual(ex[0]["recorded_by"], "source-ladder job")
        self.assertEqual(ex[0]["step"], "shared_sources")
        self.assertTrue(len(ex[0]["searched"]) >= 3)
        self.assertTrue(any("uscode.house.gov" in s for s in ex[0]["searched"]))

    def test_content_check_failure_moves_on(self):
        a = "https://www.govinfo.gov/content/pkg/FR-1990-05-02/pdf/90-9.pdf"
        other = make_pdf([["Executive Order 99 of May 1, 1990"]])
        t = FakeTransport({a: [(200, {"content-type": "application/pdf"}, other)]})
        w = fl.Wanted("EO:12345", ["EO:12345"], urls=[a], citation="EO 12345")
        res = fl.Ladder(self.fetcher(t), extract=eo_extract.eo_extract, tiers=("given",)).walk(w)
        # a per-document PDF without the number is still accepted (medium confidence)
        self.assertIsNotNone(res["source"])
        self.assertIn("not seen", res["source"]["notes"])


class FrPagesTests(unittest.TestCase):
    def issue(self):
        return [
            "REGISTER\nVOLUME 2 NUMBER 7\nExecutive Order\nESTABLISHING A REFUGE\nstuff\n[No. 75321\nfP. R. Doc. 37-94; Filed]\nOTHER AGENCY",
            "64 FEDERAL REGISTER, January 12, 1937\nCONTENTS\nExecutive Order 7533 .... 65",
            "FEDERAL REGISTER, January 12, 1937 65\nEXECUTIVE ORDER 7533\nbody\nbody",
            "66 FEDERAL REGISTER, January 12, 1937\nmore body\nTHE WHITE HOUSE\n[F. R. Doc. 37-95; Filed]\nnext doc",
            "FEDERAL REGISTER, January 12, 1937 67\nunrelated",
        ]

    def test_page_map(self):
        m = fr_pages.printed_page_map(self.issue())
        self.assertEqual(m.get(1), 64)
        self.assertEqual(m.get(2), 65)
        self.assertEqual(fr_pages.find_printed_page(self.issue(), m, 63), (0, "counted_back_from_next_numbered_page"))

    def test_closing_tag_style(self):
        r = fr_pages.locate_order(self.issue(), "7532", 63)
        self.assertEqual((r["found"], r["first_page"], r["last_page"], r["marker_kind"], r["confidence"]),
                         (True, 1, 1, "closing_number_tag", "high"))

    def test_heading_style_skips_contents(self):
        r = fr_pages.locate_order(self.issue(), "7533", 65)
        self.assertEqual((r["first_page"], r["last_page"], r["marker_kind"], r["confidence"]), (3, 4, "heading", "high"))
        r2 = fr_pages.locate_order(self.issue(), "7533", None)
        self.assertEqual(r2["first_page"], 3)
        self.assertEqual(r2["method"], "order_number_marker_only")

    def test_not_found_and_low(self):
        self.assertFalse(fr_pages.locate_order(self.issue(), "9999", None)["found"])
        low = fr_pages.locate_order(self.issue(), "9999", 66)
        self.assertEqual((low["found"], low["confidence"], low["first_page"], low["last_page"]), (True, "low", 4, 4))

    def test_ocr_damaged_heading(self):
        pages = ["5515 FEDERAL REGISTER\nEXECUTIVE ORDER 9336\nx\n[F. R. Doc. 43-1; Filed]",
                 "5516 FEDERAL REGISTER\n[F. R. Doc. 43-2; Filed]\nEXECUTIVE ORDER 9�37\nbody\n[F. R. Doc. 43-3; Filed]",
                 "5517 FEDERAL REGISTER\nmore"]
        r2 = fr_pages.locate_order(["4558 FEDERAL REGISTER\nx", "4559 FEDERAL REGISTER\nExecutive Order 1T  401\nbody\n[FR Doc. 1]"], "11401", 4559)
        self.assertEqual((r2["first_page"], r2["marker_kind"]), (2, "heading_ocr_damaged"))
        r = fr_pages.locate_order(pages, "9337", 5516)
        self.assertEqual((r["first_page"], r["last_page"], r["marker_kind"], r["confidence"]),
                         (2, 2, "heading_ocr_damaged", "medium"))
        self.assertIsNone(fr_pages.fuzzy_heading("EXECUTIVE ORDER 9336", "9337"))  # a real different number

    def test_ocr_filing_line_and_billing_code(self):
        pages = ["12107 Federal Register / Presidential Documents\nExecutive Order 12757 of March 19, 1991\nSec. 1",
                 "12108 Federal Register / Presidential Documents\nSec. 6 more\nP H  D oc. 91-6047\nFiled 3-20-91\nBilling code 3195-01-M",
                 "Reader Aids"]
        r = fr_pages.locate_order(pages, "12757", 12107)
        self.assertEqual((r["first_page"], r["last_page"], r["confidence"]), (1, 2, "high"))
        r2 = fr_pages.locate_order([pages[0], "12108 Federal Register\nmore", "12109 Federal Register\nx", "y"], "12757", 12107)
        self.assertEqual((r2["first_page"], r2["last_page"], r2["confidence"]), (1, 3, "medium"))

    def test_ocr_split_digits(self):
        self.assertTrue(fr_pages.marker_patterns("10586")[0][1].search("EXECUTIVE ORDER 1 0586"))
        self.assertFalse(fr_pages.marker_patterns("1058")[0][1].search("EXECUTIVE ORDER 10586"))


class QueueAndIndexTests(Base):
    def test_fetch_queue(self):
        p = self.tmp / "FETCH_QUEUE.jsonl"
        p.write_text("\n".join([
            json.dumps({"instrument_id": "EO:1234", "urls": ["http://example.gov/a.pdf"], "citation": "", "step": "original_text", "requested_by": "Astra"}),
            "not json",
            json.dumps({"instrument_id": "1234", "urls": []}),
            json.dumps({"instrument_id": "EO:5", "citation": "66 Stat. 259", "step": "nope"}),
            json.dumps({"instrument_id": "EO:6", "citation": "EO 9337", "step": "shared_sources"}),
        ]), encoding="utf-8")
        idx = {"EO:9337": {"primary": {"citation": "8 FR 5355"}, "others": []}}
        items, problems = ladder_queue.read_fetch_queue(p, idx)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].urls, ["https://example.gov/a.pdf"])
        self.assertEqual(items[1].eo_record, {"citation": "8 FR 5355"})
        self.assertEqual(len(problems), 3)

    def test_shared_queue(self):
        out = self.tmp / "research/stage20/output"
        out.mkdir(parents=True)
        (out / "SHARED_SOURCE_CASE_REVIEW_QUEUE.csv").write_text(
            "authority,cited_in,provisional_status,source_already_retrieved\n"
            "STAT::66 Stat. 259,EO:1,no,no\nSTAT::66 Stat. 259,EO:2,no,no\nSTAT::60 Stat. 501,EO:3,no,no\n"
            "USC::48 U.S.C. 863,EO:4,no,no\nUSC::48 U.S.C. 863),EO:5,no,no\nEO::9337,EO:6,no,yes\n", encoding="utf-8")
        (out / "STATUTE_CASE_REVIEW_QUEUE.csv").write_text(
            "source_key,citation,instrument_id,acquired_pdf_bytes\nSTAT::60 Stat. 501,60 Stat. 501,EO:3,yes\n", encoding="utf-8")
        items = ladder_queue.shared_source_wanted(self.tmp)
        got = {w.wanted_id: w.instrument_ids for w in items}
        self.assertEqual(got, {"STAT::66 Stat. 259": ["EO:1", "EO:2"], "USC::48 U.S.C. 863": ["EO:4", "EO:5"]})
        self.assertTrue(all(w.step == "shared_sources" for w in items))

    def test_index(self):
        self.assertEqual(ofr_index.normalize_number("7933-a"), "7933A")
        self.assertEqual(ofr_index.normalize_number("10571", "-A Assignment of Frequencies"), "10571A")
        self.assertEqual(ofr_index.resolve_id("7933A", {"EO:7933a"}), "EO:7933a")
        rows = [{"executive_order_number": "13526", "citation": "75 FR 1013", "title": "Correction", "publication_date": "2010-01-08"},
                {"executive_order_number": "13526", "citation": "75 FR 707", "title": "Classified", "publication_date": "2010-01-05"},
                {"executive_order_number": "99999", "signing_date": "2026-10-20", "title": "late"}]
        idx = ofr_index.build_index(rows)
        self.assertEqual(idx["EO:13526"]["primary"]["citation"], "75 FR 707")
        self.assertEqual(len(idx["EO:13526"]["others"]), 1)
        self.assertNotIn("EO:99999", idx)


def fr_issue(first_page, bodies, head="FEDERAL REGISTER, June 1, 1943"):
    """Pages of a fake scanned issue: running head with the printed page number, then the body."""
    return [f"{first_page + i} {head}\n{b}" for i, b in enumerate(bodies)]


class LocatorSafeguardTests(unittest.TestCase):
    """The failure cases found in review (version 2 of the page locator)."""

    def test_docket_number_far_away_is_not_the_order(self):
        bodies = ["notice\n[F. R. Doc. 43-1; Filed]"] * 20
        bodies[2] = "[F. R. Doc. 43-2; Filed]\nEXECUTIVE ORDER 9§37\nREGULATIONS\nbody of the order"
        bodies[3] = "more of the order\nTHE WHITE HOUSE\n[F. R. Doc. 43-3; Filed]\nnext"
        bodies[14] = "FEDERAL COMMUNICATIONS COMMISSION\n[Docket No. 9337]\nIn re application\n[F. R. Doc. 43-9; Filed]"
        pages = fr_issue(5513, bodies)
        r = fr_pages.locate_order(pages, "9337", 5515)
        self.assertTrue(r["found"])
        self.assertEqual((r["first_page"], r["last_page"]), (3, 4))
        self.assertEqual(r["marker_kind"], "heading_ocr_damaged")
        self.assertEqual(r["confidence"], "medium")
        self.assertTrue(any("medium because" in n for n in r["notes"]))

    def test_docket_number_in_window_is_skipped(self):
        bodies = ["x\n[F. R. Doc. 43-1; Filed]", "[Docket No. 9337]\nIn re\n[F. R. Doc. 43-2; Filed]", "y"]
        r = fr_pages.locate_order(fr_issue(100, bodies), "9337", 101)
        self.assertEqual(r["confidence"], "low")          # the docket number is never taken as the order
        self.assertTrue(any("skipped" in n for n in r["notes"]))

    def test_tag_past_another_documents_filing_line_is_skipped(self):
        bodies = ["Executive Order\nA TITLE\nbody", "end of it\n[F. R. Doc. 37-1; Filed]\nOTHER AGENCY",
                  "other agency text\n[No. 7532]\n[F. R. Doc. 37-2; Filed]"]
        r = fr_pages.locate_order(fr_issue(63, bodies), "7532", 63)
        self.assertNotEqual(r["marker_kind"], "closing_number_tag")
        self.assertEqual(r["confidence"], "low")

    def test_letter_suffix_is_a_different_order(self):
        bodies = ["Executive Order\nA TITLE\nbody\nMar. 30, 1937.\nNo. 7700-A\n[F. R. Doc. 37-1; Filed]", "next"]
        r = fr_pages.locate_order(fr_issue(63, bodies), "7700", 63)
        self.assertEqual(r["confidence"], "low")              # 7700-A is EO 7700A, not EO 7700
        r2 = fr_pages.locate_order(fr_issue(63, bodies), "7700A", 63)
        self.assertEqual((r2["marker_kind"], r2["first_page"]), ("number_tag", 1))
        self.assertIsNone(fr_pages.fuzzy_heading("EXECUTIVE ORDER 77#0-A", "7700"))

    def test_1930s_order_starting_after_previous_filing_line(self):
        # EO 7594 (2 FR 739): the order begins on the next PDF page, right after EO 7593's filing line.
        bodies = ["REGISTER\nVOLUME 2\nExecutive Order\nOKEFENOKEE\nbody",
                  "more\nMarch 30, 1937.\n[No. 75931\n[F. R. Doc. 37-930; Filed]\nE x e c u t iv e O rder\n"
                  "JONES ISLAND\nbody\nMar. 30, 1937.\n[No. 7594]\n[F. R. Doc. 37-932; Filed]", "next"]
        r = fr_pages.locate_order(fr_issue(739, bodies, head="FEDERAL REGISTER, April 2, 1937"), "7594", 739)
        self.assertEqual((r["first_page"], r["last_page"], r["marker_kind"], r["confidence"]),
                         (2, 2, "closing_number_tag", "medium"))

    def test_wrong_issue_is_rejected(self):
        bodies = ["DEPARTMENT OF AGRICULTURE\npursuant to Executive Order 10153 the Secretary\n[F. R. Doc. 50-1; Filed]",
                  "EXECUTIVE ORDER 10153\nwhatever", "z", "w"]
        pages = fr_issue(5500, bodies, head="FEDERAL REGISTER, August 17, 1950")
        r = fr_pages.locate_order(pages, "10153", 5600)
        self.assertFalse(r["found"])
        self.assertIn("wrong issue", r["notes"][0])
        # ... but the govinfo link service's page hint is still used when given
        r2 = fr_pages.locate_order(pages, "10153", 5600, page_hint=2)
        self.assertTrue(r2["found"])
        self.assertEqual(r2["first_page"], 2)

    def test_reference_on_page_before_does_not_win(self):
        bodies = ["Proclamation 2900\nAMENDING EXECUTIVE ORDER NO. 10153\nsomething\n[F. R. Doc. 50-1; Filed]",
                  "EXECUTIVE ORDER 10153\nA TITLE\nbody\n[F. R. Doc. 50-2; Filed]", "next"]
        r = fr_pages.locate_order(fr_issue(5600, bodies), "10153", 5601)
        self.assertEqual((r["first_page"], r["last_page"], r["marker_kind"], r["confidence"]), (2, 2, "heading", "high"))

    def test_reference_only_is_low_not_high(self):
        bodies = ["x", "RULES\nissued pursuant to Executive Order 10153 of August 1950\nand under\n"
                       "Executive Order 10153\n[F. R. Doc. 50-1; Filed]", "y"]
        r = fr_pages.locate_order(fr_issue(5600, bodies), "10153", 5601)
        self.assertEqual(r["confidence"], "low")

    def test_modern_title_3_heading_is_a_heading(self):
        pages = ["13193\nFederal Register\nPresidential Documents\nTitle 3— Executive Order 12291 o f February 17, 1981\n"
                 "The President Federal Regulation\nbody", "13194 Federal Register\nmore\n[FR Doc. 81-1 Filed]"]
        r = fr_pages.locate_order(pages, "12291", 13193)
        self.assertEqual((r["marker_kind"], r["confidence"], r["first_page"], r["last_page"]), ("heading", "high", 1, 2))
        self.assertEqual(fr_pages.heading_context("Section 202 of Executive Order 11246", 15), "reference")

    def test_medium_always_says_why(self):
        pages = fr_issue(10, ["EXECUTIVE ORDER 7700\nbody", "body", "body", "body"])
        r = fr_pages.locate_order(pages, "7700", 10)
        self.assertEqual(r["confidence"], "medium")
        self.assertTrue(any(n.startswith("medium because") and "filing line" in n for n in r["notes"]))
        long = fr_issue(10, ["EXECUTIVE ORDER 7700\nbody"] + ["body"] * 14 + ["[F. R. Doc. 1; Filed]"])
        r2 = fr_pages.locate_order(long, "7700", 10)
        self.assertEqual(r2["confidence"], "medium")
        self.assertTrue(any("long page range" in n for n in r2["notes"]))


class OutcomeTests(Base):
    def test_attempt_outcome(self):
        o = fl.attempt_outcome
        self.assertEqual(o({"error": "http_404"}), "definitive")
        self.assertEqual(o({"error": "http_410"}), "definitive")
        self.assertEqual(o({"error": "redirect_to_error_page", "reject_reason": "govinfo_error_page"}), "definitive")
        self.assertEqual(o({"error": "blocked_by_robots_txt"}), "definitive")
        self.assertEqual(o({"error": "rejected_not_found_page", "reject_reason": "not_found_page"}), "definitive")
        self.assertEqual(o({"reject_reason": "content_check: order not located"}), "definitive")
        self.assertEqual(o({"error": "offline_and_not_cached"}), "transient")
        self.assertEqual(o({"error": "http_503"}), "transient")
        self.assertEqual(o({"error": "http_429"}), "transient")
        self.assertEqual(o({"error": "http_403"}), "transient")
        self.assertEqual(o({"error": "URLError: <urlopen error [Errno 11001] getaddrinfo failed>"}), "transient")
        self.assertEqual(o({"error": "rejected_bot_or_captcha_page:captcha",
                            "reject_reason": "bot_or_captcha_page:captcha"}), "transient")

    def test_offline_never_proposes_exhausted(self):
        w = fl.Wanted("USC::31 U.S.C. 1552", ["EO:1"], citation="USC::31 U.S.C. 1552", step="shared_sources")
        t = FakeTransport({})
        res = fl.Ladder(self.fetcher(t, offline=True)).walk(w)
        self.assertIsNone(res["exhausted"])
        self.assertEqual(res["outcome"], "retry_later")
        self.assertEqual(t.calls, [])

    def test_transient_failure_is_retry_later(self):
        w = fl.Wanted("STAT::66 Stat. 259", ["EO:1"], citation="STAT::66 Stat. 259", step="shared_sources")
        t = FakeTransport({"https://www.govinfo.gov/link/statute/66/259": [(503, {}, b"")]})
        res = fl.Ladder(self.fetcher(t, max_retries=1)).walk(w)
        self.assertIsNone(res["exhausted"])
        self.assertEqual(res["outcome"], "retry_later")
        self.assertIn("http_503", res["why"])

    def test_network_down_is_retry_later(self):
        def down(url, headers, timeout):
            raise ConnectionError("network is unreachable")
        w = fl.Wanted("STAT::66 Stat. 259", ["EO:1"], citation="STAT::66 Stat. 259")
        res = fl.Ladder(self.fetcher(down, max_retries=0)).walk(w)
        self.assertEqual(res["outcome"], "retry_later")
        self.assertIsNone(res["exhausted"])

    def test_definitive_failures_are_proposed_with_real_counts(self):
        w = fl.Wanted("STAT::66 Stat. 259", ["EO:1"], citation="STAT::66 Stat. 259")
        res = fl.Ladder(self.fetcher(FakeTransport({}))).walk(w)
        self.assertEqual(res["outcome"], "exhausted")
        n = len(res["attempts"])
        self.assertIn(f"{n} route(s) tried, {n} answered over the network", res["exhausted"][0]["note"])

    def test_no_route(self):
        res = fl.Ladder(self.fetcher(FakeTransport({}))).walk(fl.Wanted("x", ["EO:1"], citation="nothing usable"))
        self.assertEqual(res["outcome"], "no_route")
        self.assertIsNone(res["exhausted"])


class RouteAndFileTests(Base):
    def test_1994_asks_link_service_before_the_issue_scan(self):
        rec = {"citation": "59 FR 7629", "publication_date": "1994-02-16", "document_number": "94-3685"}
        w = fl.Wanted("x", ["EO:12898"], citation="EO 12898", eo_record=rec)
        names = [r.route for r in fl.official_routes(w)[0]]
        self.assertLess(names.index("govinfo_link_fr"), names.index("govinfo_fr_issue_pdf"))
        rec2 = {"citation": "2 FR 63", "publication_date": "1937-01-12"}
        w2 = fl.Wanted("x", ["EO:7532"], citation="EO 7532", eo_record=rec2)
        names2 = [r.route for r in fl.official_routes(w2)[0]]
        self.assertLess(names2.index("govinfo_fr_issue_pdf"), names2.index("govinfo_link_fr"))

    def test_cutoff_editions(self):
        late = "https://www.govinfo.gov/content/pkg/CFR-2027-title5-vol1/pdf/x.pdf"
        self.assertIn("EDITION AFTER THE LEGAL CUTOFF", fl.edition_note("CFR", late))
        ok = "https://www.govinfo.gov/content/pkg/USCODE-2024-title31/pdf/x.pdf"
        self.assertNotIn("AFTER THE LEGAL CUTOFF", fl.edition_note("USC", ok))
        urls = [r.url for r in fl.official_routes(fl.Wanted("x", ["EO:1"], citation="CFR::5 CFR 6.8"))[0]]
        self.assertIn("https://www.ecfr.gov/on/2026-10-14/title-5/section-6.8", urls)

    def test_unique_names_and_lf(self):
        a = "queue:EO:1:https://example.gov/" + "a" * 200 + "/one.pdf"
        b = "queue:EO:1:https://example.gov/" + "a" * 200 + "/two.pdf"
        self.assertNotEqual(fl.unique_file_name(a), fl.unique_file_name(b))
        self.assertLessEqual(len(fl.unique_file_name(a)), 115)
        f = self.tmp / "x.txt"
        fl.write_text_lf(f, "one\ntwo\n")
        self.assertEqual(f.read_bytes(), b"one\ntwo\n")

    def test_eo_lookup_ignores_case(self):
        idx = {"EO:7933a": {"primary": {"citation": "3 FR 1"}, "others": []}}
        w = fl.Wanted("EO::7933a", ["EO:1"], citation="EO 7933a")
        ladder_queue.attach_eo_record(w, idx)
        self.assertEqual(w.eo_record, {"citation": "3 FR 1"})


class PriorOutputTests(Base):
    def test_folder(self):
        import prior_output
        d = self.tmp / "prior"
        (d / "texts").mkdir(parents=True)
        (d / "SOURCES.jsonl").write_text('{"wanted_id": "EO::9337", "text_path": "texts/a.txt"}\n', encoding="utf-8")
        (d / "RESULTS.csv").write_text("wanted_id,result\nEO::9337,found\nEO::1,exhausted_proposed\n", encoding="utf-8")
        (d / "texts" / "a.txt").write_bytes(b"hello\n")
        po = prior_output.PriorOutput.from_folder(d)
        self.assertEqual(po.jsonl("SOURCES.jsonl")[0]["wanted_id"], "EO::9337")
        self.assertEqual(po.texts(), {"a.txt": b"hello\n"})
        self.assertIsNone(po.read("missing.csv"))
        import job
        found = job.previous_found(po)
        self.assertEqual(list(found), ["EO::9337"])
        self.assertEqual(found["EO::9337"][1], b"hello\n")

    def test_git_head(self):
        import prior_output
        import subprocess
        repo = self.tmp / "gitrepo"
        out = repo / "jobs" / "x" / "output"
        (out / "texts").mkdir(parents=True)
        (out / "SOURCES.jsonl").write_bytes(b'{"a": 1}\n')
        (out / "texts" / "EO_1.txt").write_bytes(b"text one\n")
        g = ["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.invalid",
             "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false"]
        try:
            subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
            subprocess.run(g + ["add", "."], check=True, capture_output=True)
            subprocess.run(g + ["commit", "-q", "-m", "x"], check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git not available")
        po = prior_output.PriorOutput.from_git_head(repo, "jobs/x/output")
        self.assertEqual(po.jsonl("SOURCES.jsonl"), [{"a": 1}])
        self.assertEqual(po.texts(), {"EO_1.txt": b"text one\n"})
        self.assertIsNone(prior_output.PriorOutput.from_git_head(repo, "jobs/none/output").read("SOURCES.jsonl"))


if __name__ == "__main__":
    unittest.main()


class OpusRefetchQueueTest(unittest.TestCase):
    def test_reads_refetch_list_and_skips_bad_lines(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ladder_queue.OPUS_REFETCH
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"url": "https://www.govinfo.gov/a.pdf", "instrument_ids": ["EO:2", "EO:1"],
                                     "expected_sha256": "e" * 64}) + "\n" + "not json\n"
                         + json.dumps({"url": "https://www.govinfo.gov/link/a", "instrument_ids": ["EO:4"],
                                       "expected_sha256": "e" * 64}) + "\n"
                         + json.dumps({"url": "http://x", "instrument_ids": ["EO:3"]}) + "\n", encoding="utf-8")
            wanted, problems = ladder_queue.opus_refetch_wanted(d)
        self.assertEqual(len(wanted), 1)
        w = wanted[0]
        # Two URLs with the same expected sha256 are one file: one item, both URLs as routes.
        self.assertEqual((w.wanted_id, w.instrument_ids, w.step, w.expect, w.urls),
                         ("opus-refetch:" + "e" * 64, ["EO:1", "EO:2", "EO:4"], "opus_media", "pdf",
                          ["https://www.govinfo.gov/a.pdf", "https://www.govinfo.gov/link/a"]))
        self.assertEqual(w.extra["expected_sha256"], "e" * 64)
        self.assertEqual(len(problems), 2)

    def test_source_record_reports_hash_match(self):
        w = fl.Wanted(wanted_id="opus-refetch:u", instrument_ids=["EO:1"], extra={"expected_sha256": "f" * 64})
        att = {"sha256": "f" * 64, "final_url": "https://www.govinfo.gov/a.pdf", "url": "https://www.govinfo.gov/a.pdf",
               "bytes": 3, "time_utc": "2026-10-17T00:00:00Z"}
        route = fl.Route("given", "https://www.govinfo.gov/a.pdf", tier="given")
        rec = fl.Ladder.source_record(w, route, att, {})
        self.assertTrue(rec["matches_expected_sha256"])
        att["sha256"] = "0" * 64
        self.assertFalse(fl.Ladder.source_record(w, route, att, {})["matches_expected_sha256"])
