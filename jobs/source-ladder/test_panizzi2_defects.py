"""PANIZZI-2 (2026-10-20): tests for the five defects Craigellachie II found, no network.

D1 Wayback pages stored as gzip bytes; D2 only 40 PDF pages of a Public Law; D3 a table of contents or an
editions list accepted as the document; D4 a current CFR/Code edition accepted for a question dated earlier;
D5 a listing of laws accepted as the instrument.
"""
import gzip
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_ladder as fl  # noqa: E402
from test_fetch_ladder import Base, FakeResp, FakeTransport, make_pdf  # noqa: E402

H = {"content-type": "text/html"}
PDFH = {"content-type": "application/pdf"}


def sha(b):
    return hashlib.sha256(b).hexdigest()


GOOD_HTML = (b"<html><head><title>Page</title></head><body><p>" + (b"Ex. Ord. No. 11145 as amended by Ex. Ord. No. 11565 "
             b"provided: the Committee for the Preservation of the White House shall advise. ") * 12 + b"</p></body></html>")


class GzipTests(Base):
    URL = "https://web.archive.org/web/20261011070632id_/https://www.ssa.gov/history/reports/gspan.html"

    def test_gzip_body_is_decoded_before_hashing_and_both_hashes_kept(self):
        gz = gzip.compress(GOOD_HTML)
        f = self.fetcher(FakeTransport({self.URL: [(200, H, gz)]}))
        att = f.fetch(self.URL, "wayback_id_", "html")
        self.assertTrue(att["accepted"], att)
        self.assertEqual(att["sha256"], sha(GOOD_HTML))          # the document's own bytes
        self.assertEqual(att["raw_sha256"], sha(gz))              # what the archive sent
        self.assertEqual((att["bytes"], att["raw_bytes"]), (len(GOOD_HTML), len(gz)))
        self.assertEqual(Path(att["path"]).read_bytes(), GOOD_HTML)
        text, _ = fl.extract_text(att["path"], att["content_type"], "html")
        self.assertIn("Committee for the Preservation", text)
        self.assertNotIn("�", text)
        # the raw gzip blob is kept too (hashes preserved)
        self.assertTrue(f.blob_path(sha(gz), "gzip").exists())

    def test_cache_hit_returns_decoded_body_and_both_hashes(self):
        gz = gzip.compress(GOOD_HTML)
        tr = FakeTransport({self.URL: [(200, H, gz)]})
        self.fetcher(tr).fetch(self.URL, "w", "html")
        again = self.fetcher(tr, offline=True).fetch(self.URL, "w", "html")
        self.assertTrue(again["from_cache"] and again["accepted"])
        self.assertEqual((again["sha256"], again["raw_sha256"]), (sha(GOOD_HTML), sha(gz)))
        self.assertEqual(Path(again["path"]).read_bytes(), GOOD_HTML)

    def test_old_cache_entry_with_undecoded_gzip_is_redecoded_offline(self):
        gz = gzip.compress(GOOD_HTML)
        f = self.fetcher(FakeTransport({}), offline=True)
        blob = f.blob_path(sha(gz), "text/html")
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_bytes(gz)
        meta = {"url": self.URL, "final_url": self.URL, "status": 200, "bytes": len(gz), "sha256": sha(gz),
                "content_type": "text/html", "page_hint": None, "redirects": [], "retrieved_utc": "2026-10-20T05:00:00Z",
                "blob": f.rel_cache(blob)}
        mp = f.meta_path(self.URL)
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_text(json.dumps(meta), encoding="utf-8")
        att = f.fetch(self.URL, "w", "html")
        self.assertTrue(att["accepted"], att)
        self.assertEqual(att["sha256"], sha(GOOD_HTML))
        self.assertEqual(att["raw_sha256"], sha(gz))
        self.assertEqual(Path(att["path"]).read_bytes(), GOOD_HTML)

    def test_gzipped_pdf_is_decoded_to_a_pdf(self):
        pdf = make_pdf([["Executive Order 12345", "Text of the order, long enough to be real. " * 3]])
        f = self.fetcher(FakeTransport({self.URL: [(200, {"content-type": "application/octet-stream"}, gzip.compress(pdf))]}))
        att = f.fetch(self.URL, "w", "pdf")
        self.assertTrue(att["accepted"], att)
        self.assertEqual(att["sha256"], sha(pdf))
        self.assertTrue(str(att["path"]).endswith(".pdf"))

    def test_corrupt_and_truncated_gzip_are_rejected_and_never_exhaustion(self):
        gz = gzip.compress(GOOD_HTML)
        for body in (gz[:40], gz[:20] + b"\x00" * 30 + gz[50:]):
            f = self.fetcher(FakeTransport({self.URL: [(200, H, body)]}))
            att = f.fetch(self.URL, "w", "html")
            self.assertFalse(att["accepted"])
            self.assertTrue(att["reject_reason"].startswith("undecodable_gzip"), att)
            self.assertEqual(fl.attempt_outcome(att), "transient")
            self.assertFalse(list(Path(f.cache_dir, "tmp").glob("*")))   # nothing left behind

    def test_decoded_body_is_bounded(self):
        bomb = gzip.compress(b"A" * 5_000_000)
        f = self.fetcher(FakeTransport({self.URL: [(200, H, bomb)]}), max_bytes=1_000_000)
        att = f.fetch(self.URL, "w", "html")
        self.assertFalse(att["accepted"])
        self.assertIn("larger than", att["error"])

    def test_binary_garbage_with_text_content_type_is_rejected(self):
        junk = bytes(range(128, 256)) * 60
        f = self.fetcher(FakeTransport({self.URL: [(200, H, junk)]}))
        att = f.fetch(self.URL, "w", "html")
        self.assertFalse(att["accepted"])
        self.assertEqual(att["reject_reason"], "binary_or_undecodable_text")
        self.assertEqual(fl.attempt_outcome(att), "transient")

    def test_gz_file_asked_for_as_gz_is_left_alone(self):
        url = "https://www.govinfo.gov/bulkdata/x/data.xml.gz"
        gz = gzip.compress(b"<a>" + b"x" * 400 + b"</a>")
        f = self.fetcher(FakeTransport({url: [(200, {"content-type": "application/gzip"}, gz)]}))
        att = f.fetch(url, "w", "any")
        self.assertFalse(att.get("content_encoding"))
        self.assertNotEqual(att["reject_reason"], "undecodable_gzip")

    def test_ladder_end_to_end_gzip_wayback_then_text_readable(self):
        w = fl.Wanted("w", ["EO:12335"], urls=["https://www.ssa.gov/history/reports/gspan.html"],
                      citation="Date the commission submitted its report")
        cdx = [["timestamp", "original", "mimetype", "statuscode", "digest"],
               ["20261011070632", "https://www.ssa.gov/history/reports/gspan.html", "text/html", "200", "X"]]
        tr = FakeTransport({
            "https://www.ssa.gov/history/reports/gspan.html": [(403, H, b"forbidden")],
            fl.cdx_url("https://www.ssa.gov/history/reports/gspan.html"): [(200, {"content-type": "application/json"}, json.dumps(cdx).encode())],
            self.URL: [(200, H, gzip.compress(GOOD_HTML))]})
        res = fl.Ladder(self.fetcher(tr), log=lambda *a: None).walk(w)
        self.assertEqual(res["outcome"], "found")
        self.assertNotIn("�", res["text"])
        self.assertIn("Committee for the Preservation", res["text"])
        self.assertEqual(res["source"]["sha256"], sha(GOOD_HTML))
        self.assertEqual(res["source"]["raw_sha256"], sha(gzip.compress(GOOD_HTML)))
        self.assertEqual(res["source"]["content_encoding_decoded"], "gzip")


def statute_pdf(n_pages, section_page=None, toc_pages=0, section="15"):
    pages = []
    for i in range(1, n_pages + 1):
        if i <= toc_pages:
            pages.append([f"TABLE OF CONTENTS {i}"] + [f"Sec. {i * 100 + k}. Short title number {k} of the act." for k in range(30)])
        elif i == section_page:
            pages.append([f"SEC. {section}. EFFECTIVE DATES.", "The Postal Service shall commence on July 1, 1971.",
                          "The Post Office Department is abolished and the Act is amended as follows.", f"page {i}"])
        else:
            pages.append([f"84 STAT. {718 + i}", "The Postmaster General shall appoint officers. This section is amended.", f"page {i}"])
    return make_pdf(pages)


class PublicLawPagesTests(Base):
    def walk(self, wanted, url, pdf, hdrs=PDFH):
        tr = FakeTransport({url: [(200, hdrs, pdf)]})
        return fl.Ladder(self.fetcher(tr), log=lambda *a: None).walk(wanted)

    def test_all_69_pages_of_a_public_law_are_extracted_not_40(self):
        url = "https://www.govinfo.gov/content/pkg/STATUTE-84/pdf/STATUTE-84-Pg719.pdf"
        pdf = statute_pdf(69, section_page=67)
        w = fl.Wanted("queue:EO:11468:Postal", ["EO:11468"], urls=[url],
                      citation="Postal Reorganization Act, Pub. L. 91-375 (84 Stat. 719, August 12, 1970): text of the sections")
        res = self.walk(w, url, pdf)
        self.assertEqual(res["outcome"], "found")
        self.assertIn("PDF pages 1-69 of 69", res["source"]["page_or_item"])
        self.assertNotIn("PARTIAL", res["source"]["page_or_item"])
        self.assertIn("=== PDF page 67 of 69 ===", res["text"])
        self.assertIn("SEC. 15. EFFECTIVE DATES", res["text"])

    def test_stat_cite_page_is_inside_the_range_via_link_service_hint(self):
        # 84 Stat. 785 is PDF page 67 of the 719 granule; the link service answers with #page=67.
        url = "https://www.govinfo.gov/link/statute/84/785"
        final = "https://www.govinfo.gov/content/pkg/STATUTE-84/pdf/STATUTE-84-Pg719.pdf"
        tr = FakeTransport({url: [(302, {"location": final + "#page=67"}, b"")], final: [(200, PDFH, statute_pdf(69, section_page=67))]})
        w = fl.Wanted("queue:EO:11468:84 Stat. 785", ["EO:11468"], citation="84 Stat. 785")
        res = fl.Ladder(self.fetcher(tr), log=lambda *a: None).walk(w)
        self.assertEqual(res["outcome"], "found")
        self.assertIn("=== PDF page 67 of 69 ===", res["text"])
        self.assertIn("1-69 of 69", res["source"]["page_or_item"])

    def test_169_page_law_with_a_late_section_is_whole_and_section_seen(self):
        url = "https://www.govinfo.gov/content/pkg/STATUTE-98/pdf/STATUTE-98-Pg2492.pdf"
        pdf = statute_pdf(169, section_page=150, toc_pages=2, section="1632")
        w = fl.Wanted("queue:EO:12499:98-525", ["EO:12499"], urls=[url],
                      citation="Text and effective date of sec. 1632 of Pub. L. 98-525 (98 Stat. 2492, Department of Defense Authorization Act, 1985)")
        res = self.walk(w, url, pdf)
        self.assertEqual(res["outcome"], "found")
        self.assertIn("1-169 of 169", res["source"]["page_or_item"])
        self.assertIn("section 1632 seen", res["source"]["notes"])

    def test_table_of_contents_only_is_not_found(self):
        url = "https://www.govinfo.gov/content/pkg/STATUTE-98/pdf/STATUTE-98-Pg2492.pdf"
        pdf = statute_pdf(12, toc_pages=12)
        w = fl.Wanted("queue:EO:12502:98-525", ["EO:12502"], urls=[url], citation="Text of sec. 1511 of Pub. L. 98-525")
        res = self.walk(w, url, pdf)
        self.assertIsNone(res["source"])
        self.assertTrue(any("toc_only" in (a.get("reject_reason") or "") for a in res["attempts"]))
        self.assertNotEqual(res["outcome"], "exhausted")          # a bad copy is not proof the law is absent

    def test_toc_followed_by_body_is_accepted(self):
        url = "https://www.govinfo.gov/content/pkg/STATUTE-98/pdf/STATUTE-98-Pg2492.pdf"
        res = self.walk(fl.Wanted("w", ["EO:1"], urls=[url], citation="Text of sec. 15 of Pub. L. 98-525"),
                        url, statute_pdf(30, section_page=25, toc_pages=3))
        self.assertEqual(res["outcome"], "found")

    def test_partial_extraction_missing_the_section_is_rejected(self):
        url = "https://www.govinfo.gov/content/pkg/FR-1969-10-30/pdf/FR-1969-10-30.pdf"
        pdf = make_pdf([[f"Page {i}", "Notice text here for the issue."] for i in range(1, 131)])
        w = fl.Wanted("w", ["EO:1"], urls=[url], citation="Text of sec. 3014 of Pub. L. 91-999")
        res = self.walk(w, url, pdf)
        self.assertIsNone(res["source"])
        self.assertTrue(any("partial_extraction" in (a.get("reject_reason") or "") for a in res["attempts"]))

    def test_citation_pdf_pages_range_is_honoured(self):
        url = "https://www.govinfo.gov/content/pkg/FR-1969-10-30/pdf/FR-1969-10-30.pdf"
        pdf = make_pdf([[f"Page marker {i}", "Notice text here for the issue and more words."] for i in range(1, 131)])
        w = fl.Wanted("w", ["EO:11490"], urls=[url],
                      citation="34 FR 17567 through 17599; full order PDF pages 63-95 including sections 3014-3015")
        res = self.walk(w, url, pdf)
        self.assertEqual(res["outcome"], "found")
        self.assertIn("Page marker 63", res["text"])
        self.assertIn("Page marker 95", res["text"])
        self.assertNotIn("Page marker 62\n", res["text"])
        self.assertNotIn("Page marker 96", res["text"])
        self.assertIn("PDF pages 63-95 of 130", res["source"]["page_or_item"])

    def test_two_ranges_in_one_request_are_both_read(self):
        text = "44 FR 1053, PDF pages 319-320; include EO12107, 44 FR 1055-1064, PDF pages 321-330"
        self.assertEqual(fl.ranges_from_text(text), [(319, 330)])
        self.assertEqual(fl.merge_ranges([(1, 3), (50, 60)]), [(1, 3), (50, 60)])

    def test_url_fragment_page_hint_is_used_not_ignored(self):
        url = "https://www.govinfo.gov/content/pkg/FR-1958-08-09/pdf/FR-1958-08-09.pdf#page=73"
        pdf = make_pdf([[f"Page marker {i}", "Notice text for the issue and more filler words."] for i in range(1, 131)])
        tr = FakeTransport({url.split("#")[0]: [(200, PDFH, pdf)], url: [(200, PDFH, pdf)]})
        w = fl.Wanted("opus-refetch:x", ["EO:8123"], urls=[url], expect="pdf")
        res = fl.Ladder(self.fetcher(tr), log=lambda *a: None).walk(w)
        self.assertEqual(res["outcome"], "found")
        self.assertIn("Page marker 73", res["text"])
        self.assertIn("(PARTIAL", res["source"]["page_or_item"])
        self.assertIn("page hint 73", res["source"]["page_or_item"])


MENU = "\n".join(["Result 1 of 1", "Current"] + [f"{y} Ed. and Supplement V (1/3/{y + 6})" for y in (2018, 2012, 2006)] +
                  ["2000 Main Ed. (1/2/2001)", "Back to Original Document", "<< Previous", "Next >>", "[Print]", "[Print selection]",
                   "[OLRC Home]Help"])


def uscode_page(body):
    lines = "".join(f"<p>{ln}</p>" for ln in MENU.splitlines())
    return f"<html><head><title>US Code</title></head><body>{lines}{body}</body></html>".encode()


class EditionsAndListingTests(Base):
    LIVE = "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title3-section110&num=0&edition=prelim"
    WB = "https://web.archive.org/web/20250212055331id_/http://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title3-section110&num=0&edition=prelim"

    def test_editions_list_alone_is_not_the_note(self):
        tr = FakeTransport({self.LIVE: [(200, H, uscode_page("<p>See editions.</p>" * 3 + "<!-- " + "x" * 1500 + " -->"))]})
        w = fl.Wanted("w", ["EO:11145"], urls=[self.LIVE], citation="3 U.S.C. 110 note")
        res = fl.Ladder(self.fetcher(tr), log=lambda *a: None, tiers=("given",)).walk(w)
        self.assertIsNone(res["source"])
        self.assertTrue(any("index_page" in (a.get("reject_reason") or "") for a in res["attempts"]))
        self.assertEqual(res["outcome"], "retry_later")

    def test_menu_is_stripped_and_stale_capture_is_flagged(self):
        body = ("<p>§110. Furniture for the Executive Residence</p><p>Ex. Ord. No. 11145, Mar. 7, 1964, 29 F.R. 3189, as amended by "
                "Ex. Ord. No. 11565, Oct. 13, 1970, 35 F.R. 16155, provided: Committee for the Preservation of the White House "
                "shall advise the President on the White House collection and its curator.</p>")
        body += "<!-- " + "x" * 1500 + " -->"
        tr = FakeTransport({self.LIVE: [(503, H, b"busy")], self.WB: [(200, H, uscode_page(body))],
                            fl.cdx_url(self.LIVE): [(200, {"content-type": "application/json"}, json.dumps(
                                [["timestamp", "original", "mimetype", "statuscode", "digest"],
                                 ["20250212055331", "http://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title3-section110&num=0&edition=prelim",
                                  "text/html", "200", "X"]]).encode())]})
        w = fl.Wanted("queue:EO:11145:note", ["EO:11145"], urls=[self.LIVE],
                      citation="3 U.S.C. 110 note ('Ex. Ord. No. 11145 ... as amended by Ex. Ord. No. 11565')")
        res = fl.Ladder(self.fetcher(tr, max_retries=0), log=lambda *a: None, tiers=("given", "wayback_given")).walk(w)
        self.assertEqual(res["outcome"], "found")
        self.assertNotIn("Ed. and Supplement", res["text"])
        self.assertNotIn("Back to Original Document", res["text"])
        self.assertIn("Ex. Ord. No. 11145", res["text"])
        self.assertIn("Wayback capture of 2025-02-12", res["source"]["notes"])
        self.assertIn("older than the legal cutoff", res["source"]["notes"])

    def test_live_official_page_is_tried_before_the_wayback_copy(self):
        w = fl.Wanted("queue:EO:11145:note", ["EO:11145"], urls=[self.LIVE],
                      citation="3 U.S.C. 110 note ('Ex. Ord. No. 11145 ... as amended by Ex. Ord. No. 11565'); statute 3 U.S.C. 110 and 40 U.S.C. 8101")
        tiers = [r.tier for r in fl.plan_routes(w)]
        self.assertLess(tiers.index("official"), tiers.index("wayback_given"))

    def test_congress_gov_listing_is_not_a_public_law(self):
        url = "https://www.congress.gov/public-laws/119th-congress"
        page = b"<html><head><title>Public Laws</title></head><body>" + b"<li>Public Law 119-1 something</li>" * 50 + b"</body></html>"
        tr = FakeTransport({url: [(200, H, page)]})
        w = fl.Wanted("queue:EO:13306:x", ["EO:13306"], urls=[url], citation="10USC subtitleA partII chapter57; EO13306")
        res = fl.Ladder(self.fetcher(tr), log=lambda *a: None, tiers=("given",)).walk(w)
        self.assertIsNone(res["source"])
        self.assertEqual(res["outcome"], "retry_later")             # never proposed as exhausted
        self.assertTrue(fl.is_listing_url("https://web.archive.org/web/2025id_/https://www.federalregister.gov/presidential-documents/executive-orders"))
        self.assertFalse(fl.is_listing_url("https://www.congress.gov/119/plaws/publ1/PLAW-119publ1.pdf"))


class DatedEditionTests(Base):
    PROSE_1953 = ("Civil Service Commission action completing the sec. 2 reclassification of Schedule A and B positions into "
                  "Schedules A, B and C under EO 10440 (1953): Federal Register notices amending 5 CFR Part 6 in 1953, and the "
                  "Commission's Annual Report for fiscal year 1953")

    def child(self, cite, parent):
        return fl.Wanted(f"queue:EO:10440:{parent} <{cite}>", ["EO:10440"], citation=cite, extra={"parent_citation": parent})

    def test_request_year(self):
        w = lambda c, **ex: fl.Wanted("w", [], citation=c, extra=ex)  # noqa: E731
        self.assertEqual(fl.request_year(self.child("5 CFR 6", self.PROSE_1953)), 1953)
        self.assertIsNone(fl.request_year(w("5 CFR 6.8")))
        self.assertIsNone(fl.request_year(w("50 U.S.C. 1801 and Pub. L. 98-525 and 42 U.S.C. 1983")))   # cite numbers are not years
        self.assertIsNone(fl.request_year(w("3 U.S.C. 110 note (1964 order), current legal predicate")))
        self.assertEqual(fl.request_year(w("5 CFR 6", as_of="1999")), 1999)
        self.assertIsNone(fl.request_year(w("5 CFR 6 (1953)", as_of="current")))
        self.assertFalse(fl.is_dated_earlier(w("5 CFR 6 as of 2026-10-01")))   # this year is not "earlier"
        self.assertTrue(fl.is_dated_earlier(w("5 CFR 6 as of 2025-10-01")))

    def test_1953_cfr_question_gets_no_route_and_says_why(self):
        c = self.child("5 CFR 6", self.PROSE_1953)
        self.assertEqual(fl.plan_routes(c), [])                     # no 2026 edition, no eCFR, no Cornell
        res = fl.Ladder(self.fetcher(FakeTransport({})), log=lambda *a: None).walk(c)
        self.assertEqual(res["outcome"], "no_route")
        self.assertIn("historical_cfr_not_on_govinfo", res["why"])
        self.assertIn("1953", res["why"])
        self.assertEqual(res["attempts"], [])

    def test_dated_question_in_range_routes_to_that_edition_only(self):
        c = self.child("5 CFR 6", "Reclassification under 5 CFR Part 6 completed in 1999")
        plan = fl.plan_routes(c)
        self.assertEqual([r.route for r in plan], ["govinfo_link_cfr_edition"])
        self.assertIn("year=1999", plan[0].url)
        self.assertFalse(any("ecfr.gov" in r.url or "cornell" in r.url or "mostrecent" in r.url for r in plan))

    def test_dated_uscode_question(self):
        c = self.child("3 U.S.C. 110", "Furniture statute as it read in 2010")
        plan = fl.plan_routes(c)
        self.assertIn("year=2010", plan[0].url)
        self.assertFalse(any("uscode.house.gov" in r.url or "cornell" in r.url for r in plan))
        self.assertEqual(fl.plan_routes(self.child("3 U.S.C. 110", "as it read in 1980")), [])
        self.assertIn("historical_us_code_not_on_govinfo", fl.historical_gap(self.child("3 U.S.C. 110", "as it read in 1980")))

    def test_current_edition_cannot_satisfy_an_earlier_question(self):
        link = "https://www.govinfo.gov/link/cfr/5/6?link-type=pdf&year=1999"
        cur = "https://www.govinfo.gov/content/pkg/CFR-2026-title5-vol1/pdf/CFR-2026-title5-vol1-part6.pdf"
        old = "https://www.govinfo.gov/content/pkg/CFR-1999-title5-vol1/pdf/CFR-1999-title5-vol1-part6.pdf"
        pdf = make_pdf([["5 CFR Part 6 Excepted service", "The Commission shall list exceptions in Schedule A, B and C. " * 3]])
        c = self.child("5 CFR 6", "Reclassification under 5 CFR Part 6 completed in 1999")
        # (a) the service resolves to the 2026 edition: refused
        res = fl.Ladder(self.fetcher(FakeTransport({link: [(302, {"location": cur}, b"")], cur: [(200, PDFH, pdf)]})),
                        log=lambda *a: None, tiers=("official",)).walk(c)
        self.assertIsNone(res["source"])
        self.assertTrue(any("current_edition_for_dated_request" in (a.get("reject_reason") or "") for a in res["attempts"]))
        self.assertNotEqual(res["outcome"], "exhausted")
        # (b) it resolves to the 1999 edition: accepted
        self.setUp()
        res = fl.Ladder(self.fetcher(FakeTransport({link: [(302, {"location": old}, b"")], old: [(200, PDFH, pdf)]})),
                        log=lambda *a: None, tiers=("official",)).walk(c)
        self.assertEqual(res["outcome"], "found")
        self.assertIn("1999 edition", res["source"]["notes"])

    def test_edition_conflict_rules(self):
        c = self.child("5 CFR 6", "completed in 1953")
        ok = "https://www.govinfo.gov/content/pkg/CFR-1954-title5/pdf/x.pdf"
        self.assertEqual(fl.edition_conflict(c, ok), "")
        self.assertIn("2026", fl.edition_conflict(c, "https://www.govinfo.gov/content/pkg/CFR-2026-title5-vol1/pdf/x.pdf"))
        self.assertIn("current", fl.edition_conflict(c, "https://www.ecfr.gov/on/2026-10-14/title-5/part-6"))
        self.assertIn("current", fl.edition_conflict(c, "https://www.law.cornell.edu/cfr/text/5/part-6"))
        self.assertEqual(fl.edition_conflict(c, "https://web.archive.org/web/19540101000000id_/https://www.ecfr.gov/x"), "")
        self.assertIn("capture", fl.edition_conflict(c, "https://web.archive.org/web/20250101000000id_/https://uscode.house.gov/view.xhtml?x=1"))
        undated = fl.Wanted("w", [], citation="5 CFR 6")
        self.assertEqual(fl.edition_conflict(undated, "https://www.govinfo.gov/content/pkg/CFR-2026-title5-vol1/pdf/x.pdf"), "")

    def test_undated_cfr_request_is_unchanged(self):
        plan = fl.plan_routes(fl.Wanted("CFR::5 CFR 352", ["EO:11552"], citation="5 CFR 352"))
        self.assertTrue(any("mostrecent" in r.url for r in plan))
        self.assertTrue(any("ecfr.gov/on" in r.url for r in plan))


if __name__ == "__main__":
    unittest.main()


class CarriedDefectTests(unittest.TestCase):
    """Panizzi II review: a record found by an EARLIER run is re-checked, else the fixes never reach it."""

    HDR = "Wanted: x\nSource: y\n\nMachine-extracted text. Not an authenticated transcription; check the PDF.\n\n"

    def w(self, citation, **extra):
        return fl.Wanted(wanted_id="queue:" + citation[:20], instrument_ids=["EO:1"], citation=citation, extra=extra)

    def test_partial_statute_is_walked_again(self):
        w = self.w("Text of sec. 1632 of Pub. L. 98-525 (98 Stat. 2492)")
        src = {"url": "https://www.govinfo.gov/content/pkg/STATUTE-98/pdf/STATUTE-98-Pg2492.pdf",
               "page_or_item": "x; STATUTE-98-Pg2492.pdf PDF pages 1-40 of 169"}
        self.assertTrue(fl.carried_defect(w, src, None).startswith("partial_extraction"))
        src["page_or_item"] = "x; STATUTE-98-Pg2492.pdf PDF pages 1-169 of 169"
        self.assertEqual(fl.carried_defect(w, src, None), "")

    def test_requested_pdf_pages_already_held_are_not_walked_again(self):
        w = self.w("Pub. L. 91-375, PDF pages 63-69")
        src = {"url": "https://www.govinfo.gov/content/pkg/STATUTE-84/pdf/STATUTE-84-Pg719.pdf",
               "page_or_item": "x; STATUTE-84-Pg719.pdf PDF pages 60-69 of 69"}
        self.assertEqual(fl.carried_defect(w, src, None), "")

    def test_non_statute_partial_pdf_is_left_alone(self):
        w = self.w("27 FR 2983")
        src = {"url": "https://www.govinfo.gov/content/pkg/FR-1962-03-30/pdf/FR-1962-03-30.pdf",
               "page_or_item": "FR-1962-03-30.pdf PDF pages 1-40 of 80"}
        self.assertEqual(fl.carried_defect(w, src, None), "")

    # MABILLON (2026-10-20): EO 11490's FR issue was kept as pages 1-40 of 96 although the line named pages 63-95.
    EO11490_CITE = ("34 FR 17567 through 17599; full order PDF pages 63-95 including sections 3014-3015; "
                    "full_run currently retains only pages63-65")
    EO11490_URL = "https://www.govinfo.gov/content/pkg/FR-1969-10-30/pdf/FR-1969-10-30.pdf"

    def test_fr_issue_missing_requested_pages_is_walked_again(self):
        w = fl.Wanted(wanted_id="queue:EO:11490:" + self.EO11490_CITE, instrument_ids=["EO:11490"],
                      citation=self.EO11490_CITE)
        src = {"url": self.EO11490_URL, "page_or_item": self.EO11490_CITE + "; FR-1969-10-30.pdf PDF pages 1-40 of 96"}
        why = fl.carried_defect(w, src, None)
        self.assertTrue(why.startswith("partial_extraction"), why)
        self.assertIn("63-95", why)
        src["page_or_item"] = self.EO11490_CITE + "; FR-1969-10-30.pdf PDF pages 63-95 of 96"
        self.assertEqual(fl.carried_defect(w, src, None), "")

    def test_requested_pages_beyond_the_document_do_not_loop(self):
        w = self.w("Notice, PDF pages 120-130")
        src = {"url": "https://www.govinfo.gov/content/pkg/FR-1962-03-30/pdf/FR-1962-03-30.pdf",
               "page_or_item": "FR-1962-03-30.pdf PDF pages 1-40 of 80"}
        self.assertEqual(fl.carried_defect(w, src, None), "")

    def test_requested_pages_in_parent_line_count(self):
        w = fl.Wanted(wanted_id="queue:x <34 FR 17567>", instrument_ids=["EO:11490"], citation="34 FR 17567",
                      extra={"parent_citation": "34 FR 17567, PDF pages 63-95"})
        src = {"url": self.EO11490_URL, "page_or_item": "34 FR 17567; FR-1969-10-30.pdf PDF pages 63-65 of 96"}
        self.assertTrue(fl.carried_defect(w, src, None).startswith("partial_extraction"))

    def test_gzip_garbage_text_is_walked_again(self):
        garbage = gzip.compress(GOOD_HTML).decode("utf-8", "replace")
        src = {"url": "https://web.archive.org/web/20261011070632id_/https://www.ssa.gov/history/reports/gspan.html",
               "page_or_item": "x"}
        why = fl.carried_defect(self.w("Date the commission submitted its report"), src, (self.HDR + garbage).encode())
        self.assertTrue(why.startswith("binary_or_undecodable_text"), why)
        good = (self.HDR + GOOD_HTML.decode()).encode()
        self.assertEqual(fl.carried_defect(self.w("Date the commission submitted its report"), src, good), "")

    def test_current_edition_for_dated_question_is_walked_again(self):
        w = self.w("Civil Service Commission action in 1953 amending 5 CFR 6",
                   parent_citation="Civil Service Commission action in 1953 amending 5 CFR Part 6")
        w.citation = "5 CFR 6"
        src = {"url": "https://www.govinfo.gov/content/pkg/CFR-2026-title5-vol1/pdf/CFR-2026-title5-vol1-part6.pdf",
               "page_or_item": "x"}
        self.assertTrue(fl.carried_defect(w, src, None).startswith("current_edition_for_dated_request"))
        undated = self.w("5 CFR 6")
        self.assertEqual(fl.carried_defect(undated, src, None), "")

    def test_listing_and_finding_aid_pages_are_walked_again(self):
        w = self.w("Emergency board report, actual submission date")
        for u in ("https://web.archive.org/web/20260711014000id_/https://www.congress.gov/public-laws/119th-congress",
                  "https://www.archives.gov/research/guide-fed-records/groups/013.html"):
            self.assertTrue(fl.carried_defect(w, {"url": u, "page_or_item": "x"}, None).startswith("index_page"), u)

    def test_report_date_records_are_rechecked(self):
        src = {"url": "https://www.archives.gov/research/guide-fed-records/groups/013.html", "page_or_item": "x",
               "report_date_request": {"lane": "nmb"}}
        self.assertTrue(fl.carried_defect(self.w("x"), src, None).startswith("index_page"))
