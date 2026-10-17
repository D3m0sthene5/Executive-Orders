"""Unit tests for media_match.py. Small fixtures only, no network."""

import csv
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import media_match as mm  # noqa: E402


def _lines(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()


def _csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _esc(s):
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(pages):
    """A minimal valid PDF whose pages carry the given text lines."""
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>"]
    kids = [4 + 2 * i for i in range(len(pages))]
    objs.append(("<< /Type /Pages /Kids [" + " ".join(f"{k} 0 R" for k in kids)
                 + f"] /Count {len(pages)} >>").encode())
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for i, lines in enumerate(pages):
        content = ("BT /F1 10 Tf 50 750 Td 14 TL " + " ".join(f"({_esc(x)}) Tj T*" for x in lines) + " ET").encode("latin-1")
        objs.append((f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> "
                     f"/Contents {5 + 2 * i} 0 R >>").encode())
        objs.append(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
    out = b"%PDF-1.4\n"
    offsets = []
    for k, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{k} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


class TextHelpers(unittest.TestCase):
    def test_collapse(self):
        self.assertEqual(mm.collapse("Exec utive  Order No. 9054,\npro-\nvided"), "executiveorderno9054provided")

    def test_eo_number_variants(self):
        known = {"9054", "9055", "9056", "11234", "9727"}
        for text in ("Executive Order No. 9054", "E.O. 9054", "Exec. Order 9054", "EXECUTIVE ORDER 9054",
                     "Executive Order\nNo. 9054", "EO 9054"):
            self.assertIn("9054", mm.find_eo_numbers(text, known), text)
        self.assertIn("11234", mm.find_eo_numbers("Exec utive Order 1 1 234", known))
        lst = mm.find_eo_numbers("Executive Orders Nos. 9054, 9055 and 9056 are revoked", known)
        self.assertEqual(set(lst), {"9054", "9055", "9056"})
        # the FR citation after the number must not be glued onto it
        self.assertEqual(set(mm.find_eo_numbers("Pursuant to Executive Order 9727 (11 F.R. 5461)", known)), {"9727"})
        # unknown numbers are ignored; plain numbers without "Executive Order" are ignored
        self.assertEqual(mm.find_eo_numbers("Executive Order 1234 of 1910; page 9054", known), {})

    def test_headings_and_signature_block(self):
        known = {"9054", "11234", "7504", "2211", "9616"}
        self.assertEqual(mm.find_eo_headings("EXECUTIVE ORDER 9054\nCreating a board", known), {"9054"})
        self.assertEqual(mm.find_eo_headings("Exec utive Order 1 1 234\nESTABLISHING", known), {"11234"})
        # a suffixed heading belongs to the suffixed order only (9616A is not 9616)
        self.assertEqual(mm.find_eo_headings("EXECUTIVE ORDER 9 6 1 6 A -\nCreation", known), set())
        self.assertEqual(mm.find_eo_headings("EXECUTIVE ORDER 9 6 1 6 A -\nCreation", known | {"9616A"}), {"9616A"})
        self.assertEqual(mm.find_eo_headings("EXECUTIVE ORDER 9616\nCreation", known | {"9616A"}), {"9616"})
        sig = "T he W hite  H ouse ,\nSeptember 20, 1945.\n[No. 9616 A]\n"
        self.assertEqual(mm.find_eo_headings(sig, known | {"9616A"}), {"9616A"})
        self.assertEqual(mm.find_eo_headings("EXECUTIVE ORDER\nNo. 7504\n", known), {"7504"})
        sig = "revoked by the President.\nFranklin D Roosevelt\nT he W hite  H ouse ,\nDecember 11, 1936.\n[No. 7504]\n"
        self.assertEqual(mm.find_eo_headings(sig, known), {"7504"})
        procl = "Franklin D Roosevelt\nBy the President:\nR. Walton Moore,\nActing Secretary of State.\n[No. 2211]\n"
        self.assertEqual(mm.find_eo_headings(procl, known), set())
        # a mention inside a sentence is not a heading
        self.assertEqual(mm.find_eo_headings("as provided in Executive Order 9054, the board", known), set())

    def test_suffix_letters_keep_orders_apart(self):
        known = {"9616", "9616A", "9054", "6711A"}
        self.assertEqual(mm.order_number("EO:9616A"), "9616A")
        self.assertEqual(mm.order_number("EO:09054"), "9054")
        self.assertEqual(dict(mm.find_eo_numbers("Executive Order No. 9616A and Executive Order 9616", known)),
                         {"9616A": 1, "9616": 1})
        self.assertEqual(dict(mm.find_eo_numbers("Executive Order 9616A, as amended", {"9616"})), {})
        self.assertEqual(dict(mm.find_eo_numbers("Exec utive Order 6 7 1 1 A ,", known)), {"6711A": 1})
        self.assertEqual(dict(mm.find_eo_numbers("EO 9054 A N D", known)), {"9054": 1})
        self.assertEqual(mm.filename_features("a/cache/fr_1945_eo9616a_p1.pdf")["eo"], {"9616A"})
        # the heading "9616A" gives EO:9616 no heading signal
        mf = mm.MemberFeatures("evidence/s/cache/fr_1945-09-22_p1-2.pdf",
                               "a" * 64, ["EXECUTIVE ORDER 9616A\nText of the order"], known)
        c = mm.Case("EO:9616")
        c.finish()
        self.assertIsNone(mm.score_pair(mf, c, [], []))
        c2 = mm.Case("EO:9616A")
        c2.finish()
        self.assertEqual(mm.score_pair(mf, c2, [], [])["details"]["eo_number_in_text"], ["heading@p1"])

    def test_citations(self):
        self.assertEqual(mm.find_fr_cites("see 11 F.R. 5847 and 11 FR 5848 and (11 P.R. 5461)"),
                         {(11, 5847), (11, 5848), (11, 5461)})
        self.assertEqual(mm.find_fr_cites("3 CFR 1943"), set())
        self.assertEqual(mm.find_stat_cites("55 Stat. 838; 60 S ta t 418"), {(55, 838), (60, 418)})

    def test_page_heads(self):
        h = mm.page_header_features("FEDERAL REGISTER, Wednesday, May 29, 1946 5835\nOFFICE OF DEFENSE")
        self.assertEqual(h["fr_date"], "1946-05-29")
        self.assertEqual(h["fr_vol"], 11)
        self.assertEqual(h["fr_pages"], {5835})
        h = mm.page_header_features("838 PUBLIC LAWS-CHS. 591, 593-DEC. 17, 18, 1941 [55 Stat .\n59 Stat. 298.")
        self.assertEqual((h["stat_vol"], h["stat_pages"]), (55, {838}))
        h = mm.page_header_features("55 Stat .] 77th CONG., 1st SESS.-CH. 593-DEC. 18, 1941 839\ntext")
        self.assertEqual((h["stat_vol"], h["stat_pages"]), (55, {839}))
        h = mm.page_header_features("55 Stat.] 77th CONG.-CHS. 593, 594-DEC. 18,19, 1941\ntext")
        self.assertEqual(h["stat_pages"], set())  # the trailing year is not a page

    def test_glued_statute_head(self):
        pages = ["838 PUBLIC LAWS [55 Stat.\nx", "84155 Stat .] 77th CONG.-DEC. 18,19, 1941\ny"]
        mf = mm.MemberFeatures("evidence/x/cache/stat_55_838.pdf", "0" * 64, pages, set())
        self.assertEqual(dict(mf.stat_vol_pages), {55: {838: 1, 841: 2}})

    def test_filename_features(self):
        f = mm.filename_features("evidence/reviews/V/cache/fr_1946-05-29.p19-20.pdf")
        self.assertEqual(f["fr_dates"], {"1946-05-29"})
        self.assertEqual(f["pages"], (19, 20))
        f = mm.filename_features("evidence/shards/S/cache/fr_1968-09-04_eo11425_p9-10.pdf")
        self.assertEqual((f["fr_dates"], f["eo"]), ({"1968-09-04"}, {"11425"}))
        for name, cite in (("stat_55_838.pdf", (55, 838)), ("STATUTE-55-Pg838.pdf", (55, 838)),
                           ("stat_103_Pg37.pdf", (103, 37)), ("R_STAT_49_375.pdf", (49, 375)),
                           ("rstat_94_2835.excerpt.pdf", (94, 2835)), ("STAT-70-786.pdf", (70, 786))):
            self.assertIn(cite, mm.filename_features("a/cache/" + name)["stat"], name)
        self.assertEqual(mm.filename_features("a/cache/FR-04-55526.pdf")["fr_docs"], {"2004-55526"})
        self.assertEqual(mm.filename_features("a/cache/fr_1999-12-30_99-33908.pdf")["fr_docs"], {"1999-33908"})
        self.assertEqual(mm.filename_features("a/cache/plumbook2024.pdf")["fr_dates"], set())

    def test_member_key(self):
        self.assertEqual(mm.member_key("a/cache/fr_1946-05-29.p19-20.pdf"), "fr_1946-05-29")
        self.assertEqual(mm.member_key("a/cache/fr_1963-01-18_p7-8-1.png"), "fr_1963-01-18")
        self.assertIsNone(mm.member_key("a/unts_png/p-1.png"))

    def test_quotes(self):
        pt = mm.PageText(["Until it is other­wise pro-\nvided, the Alien Property",
                          "Cus todian is authorized and empowered to pay"])
        segs = mm.quote_segments("Until it is otherwise provided, the Alien Property Custodian is authorized")
        self.assertEqual(pt.verbatim(segs), [1, 2])  # crosses the page break
        segs2 = mm.quote_segments("Until it is otherwise provided ... authorized and empowered to pay")
        self.assertEqual(len(segs2), 2)
        self.assertTrue(pt.verbatim(segs2))
        self.assertIsNone(pt.verbatim(mm.quote_segments("Until it is otherwise provided, the Treasury shall")))
        noisy = mm.PageText(["Until it is otherwise provided, the Alien Property Custodlan is authorlzed and "
                             "empowered to pay out of any funds lawfully in his custody"])
        q = mm.quote_segments("Until it is otherwise provided, the Alien Property Custodian is authorized and "
                              "empowered to pay out of any funds lawfully in his custody")
        self.assertIsNone(noisy.verbatim(q))
        self.assertTrue(noisy.near(q))
        self.assertLess(mm.specific_length(mm.quote_segments(
            "By virtue of the authority vested in me as President of the United States, it is hereby ordered")), 10)


class Grading(unittest.TestCase):
    def _case(self, iid, quotes=(), **kw):
        c = mm.Case(iid)
        for q, own in quotes:
            c.add_quote(q, "E1", "https://example.gov/eo" + (c.num if own else "x"), "", "")
        for k, v in kw.items():
            getattr(c, k).update(v)
        c.finish()
        return c

    def _mf(self, path, pages, known):
        return mm.MemberFeatures(path, "a" * 64, pages, known)

    def test_heading_plus_filename_is_unique_and_order_text(self):
        c = self._case("EO:11425")
        mf = self._mf("evidence/s/cache/fr_1968-09-04_eo11425_p9-10.pdf", ["EXECUTIVE ORDER 11425\nText"], {"11425"})
        s = mm.score_pair(mf, c, [], [])
        self.assertEqual(s["grade"], "unique_supported")
        self.assertEqual(s["role"], "order_text_candidate")
        self.assertEqual(s["families"], ["eo_number_in_text", "filename_match"])

    def test_citation_plus_filename_is_only_ambiguous(self):
        c = self._case("EO:9000", stat_cites={(55, 838)})
        mf = self._mf("evidence/s/cache/stat_55_838.pdf", ["838 PUBLIC LAWS [55 Stat.\nAN ACT"], {"9000"})
        s = mm.score_pair(mf, c, [], [])
        self.assertEqual(s["families"], ["citation_in_text", "filename_match"])
        self.assertEqual(s["grade"], "ambiguous")
        c.hashes.add("a" * 64)  # the order's own records cite this exact file
        s = mm.score_pair(mf, c, [], [])
        self.assertEqual(s["grade"], "unique_supported")
        self.assertEqual(s["role"], "cited_source")

    def test_long_rare_quote_alone_is_enough_but_not_own_text_in_other_document(self):
        text = ("the Secretary shall transfer to the Administrator all records relating to the surplus vessels "
                "located in the Canal Zone together with the unexpended balances of appropriations")
        mf = self._mf("evidence/s/cache/stat_60_418.pdf", [text], {"9000"})
        c = self._case("EO:9000", quotes=[(text, False)])
        hits = [(c.quotes[0], [1], "verbatim")]
        c.quotes[0]["files"] = 1
        self.assertEqual(mm.score_pair(mf, c, [], hits)["grade"], "unique_supported")
        c.quotes[0]["files"] = 5  # found in many files: not distinctive
        self.assertEqual(mm.score_pair(mf, c, [], hits)["grade"], "ambiguous")
        c2 = self._case("EO:9000", quotes=[(text, True)])  # the order's own words found in a statute
        c2.quotes[0]["files"] = 1
        self.assertEqual(mm.score_pair(mf, c2, [], [(c2.quotes[0], [1], "verbatim")])["grade"], "ambiguous")

    def test_stock_phrase_on_page_of_other_orders_is_not_counted(self):
        phrase = "shall remain in force until revoked by the President or by act of Congress"
        page = "land withdrawn.\n" + phrase + "\nThe White House,\nDecember 11, 1936.\n[No. 7504]\n"
        mf = self._mf("evidence/s/cache/FR-1936-12-16.pdf", [page], {"7504", "7622"})
        c = self._case("EO:7622", quotes=[(phrase, True)])
        s = mm.score_pair(mf, c, [], [(c.quotes[0], [1], "verbatim")])
        self.assertEqual(s["families"], [])
        self.assertEqual(s["grade"], "ambiguous")
        self.assertTrue(any("quote_on_page_of_other_orders" in n for n in s["notes"]))

    def _issue_excerpt(self, page_text, member_sha="a" * 64, meta_sha="b" * 64):
        url = "https://www.govinfo.gov/content/pkg/FR-1948-07-14/pdf/FR-1948-07-14.pdf"
        mf = mm.MemberFeatures("evidence/s/cache/fr_1948-07-14.p11-12.pdf", member_sha, [page_text], {"9976", "9871"})
        metas = [("evidence/s/cache/fr_1948-07-14.meta.json", {"url": url, "sha256": meta_sha})]
        return mf, metas, url

    def test_citing_the_same_whole_issue_is_not_order_specific(self):
        # regression: fr_1948-07-14.p11-12.pdf was unique_supported for EO:9976 although the
        # excerpt (FR pages 3975-3976) never mentions the order
        mf, metas, url = self._issue_excerpt("FEDERAL REGISTER, Wednesday, July 14, 1948 3975\nNotices of other matters")
        c = self._case("EO:9976", urls={url})
        s = mm.score_pair(mf, c, metas, [])
        self.assertIn("cites_same_document", s["families"])
        self.assertNotIn("opus_record_link", s["families"])
        self.assertEqual(s["grade"], "ambiguous")
        self.assertTrue(mm.is_whole_package_url(url))
        self.assertFalse(mm.is_whole_package_url("https://www.govinfo.gov/content/pkg/FR-1999-12-30/pdf/99-33908.pdf"))

    def test_whole_issue_link_still_counts_when_cited_page_is_in_the_excerpt(self):
        mf, metas, url = self._issue_excerpt("FEDERAL REGISTER, Wednesday, July 14, 1948 3975\nNotices")
        c = self._case("EO:9976", urls={url}, fr_cites={(13, 3975)})
        s = mm.score_pair(mf, c, metas, [])
        self.assertIn("opus_record_link", s["families"])
        self.assertEqual(s["grade"], "unique_supported")
        # and when the member is the whole downloaded issue itself (same bytes)
        mf, metas, url = self._issue_excerpt("FEDERAL REGISTER, Wednesday, July 14, 1948 3975\nx", meta_sha="a" * 64)
        s = mm.score_pair(mf, self._case("EO:9976", urls={url}), metas, [])
        self.assertIn("opus_record_link", s["families"])

    def test_order_text_span(self):
        self.assertEqual(mm.order_text_span([1], [2]), "PDF pages 1-2 (heading on p1)")
        self.assertEqual(mm.order_text_span([2], [1, 2]), "PDF pages 1-2 (heading on p2)")
        self.assertEqual(mm.order_text_span([1], [9]), "PDF page 1 (heading on p1)")

    def test_page_ranges(self):
        self.assertEqual(mm.page_ranges([3, 1, 2, 5]), "1-3,5")


class OcrPath(unittest.TestCase):
    def test_image_ocr_with_stand_in_tesseract_and_cache(self):
        with tempfile.TemporaryDirectory() as d:
            fake = pathlib.Path(d) / "fake_tesseract.py"
            fake.write_text("print('EXECUTIVE ORDER 9054')\nprint('The Board shall advise the President')\n",
                            encoding="utf-8")
            ocr = mm.Ocr(enabled=False, tmpdir=d)
            ocr.tesseract = [sys.executable, str(fake)]
            png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
            res = mm.extract_member_text(png, "png", ocr, d, "f" * 64)
            self.assertEqual(res["ocr_pages"], [1])
            self.assertIn("EXECUTIVE ORDER 9054", res["pages"][0])
            self.assertEqual(res["pages_without_text"], [])
            self.assertEqual(mm.find_eo_headings(res["pages"][0], {"9054"}), {"9054"})
            # second call is served from the cache without running OCR again
            again = mm.extract_member_text(png, "png", mm.Ocr(enabled=False), d, "f" * 64)
            self.assertEqual(again["pages"], res["pages"])
            self.assertEqual(ocr.used, 1)

    def test_failing_ocr_is_counted_and_page_stays_open(self):
        with tempfile.TemporaryDirectory() as d:
            fake = pathlib.Path(d) / "bad_tesseract.py"
            fake.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
            ocr = mm.Ocr(enabled=False, tmpdir=d)
            ocr.tesseract = [sys.executable, str(fake)]
            res = mm.extract_member_text(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16, "png", ocr, d, "d" * 64)
            self.assertEqual(ocr.failures, 1)
            self.assertEqual(res["ocr_pages"], [])
            self.assertEqual(res["pages_without_text"], [1])

    def test_without_ocr_images_are_counted_as_needing_it(self):
        with tempfile.TemporaryDirectory() as d:
            res = mm.extract_member_text(b"\xff\xd8\xff" + b"\x00" * 8, "jpg", mm.Ocr(enabled=False), d, "e" * 64)
            self.assertEqual(res["pages_without_text"], [1])
            self.assertEqual(res["ocr_pages"], [])


class EndToEnd(unittest.TestCase):
    def test_run_on_fixture_release(self):
        P = mm.PKG
        own_quote = ("The Board shall consist of five members appointed by the President and shall advise him "
                     "on the allocation of strategic shipping tonnage")
        stat_quote = "The President is hereby authorized to make such redistribution of functions among executive agencies"
        old_quote = ("the lands are hereby reserved for the use of the Department of Agriculture as a refuge and "
                     "breeding ground for migratory birds at Lake Lenore")
        fr_pdf = make_pdf([["FEDERAL REGISTER, Thursday, February 5, 1942 1003", "EXECUTIVE ORDER 9054",
                            own_quote], ["1004 FEDERAL REGISTER, Thursday, February 5, 1942", "other text"]])
        stat_pdf = make_pdf([["838 PUBLIC LAWS-CHS. 591, 593-DEC. 17, 18, 1941 [55 Stat.", "AN ACT", stat_quote]])
        old_pdf = make_pdf([["FEDERAL REGISTER, Wednesday, December 16, 1936", old_quote, "Franklin D Roosevelt",
                             "The White House,", "December 11, 1936.", "[No. 7504]"]])
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
        html = b"<HTML><HEAD><TITLE>Access Denied</TITLE></HEAD><BODY>denied</BODY></HTML>"
        media = {
            "evidence/shards/S_T/cache/fr_1942-02-05_p3-4.pdf": fr_pdf,
            "evidence/shards/S_T/cache/stat_55_838.pdf": stat_pdf,
            "evidence/shards/S_T/cache/FR-1936-12-16.pdf": old_pdf,
            "evidence/shards/S_T/cache/scan.png": png,
            "evidence/reviews/V_T/cache/denied.pdf": html,
            "evidence/reviews/V_T/cache/empty.pdf": b"",
        }
        sha = {k: hashlib.sha256(v).hexdigest() for k, v in media.items()}
        tmpfile = "/tmp/claude-0/x/scratchpad/s11/"
        evidence = [
            {"evidence_id": "T1", "quote": own_quote, "url": "https://www.govinfo.gov/content/pkg/FR-1942-02-05/pdf/FR-1942-02-05.pdf",
             "source_title": "FR printing of EO 9054", "local_file": tmpfile + "shards/S_T/cache/fr_1942-02-05.txt"},
            {"evidence_id": "T2", "quote": stat_quote, "url": "https://www.govinfo.gov/content/pkg/STATUTE-55/pdf/STATUTE-55-Pg838.pdf",
             "source_title": "55 Stat. 838", "local_file": tmpfile + "shards/S_T/cache/stat_55_838.pdf"},
            {"evidence_id": "T3", "quote": old_quote, "url": "https://www.govinfo.gov/content/pkg/FR-1936-12-16/pdf/FR-1936-12-16.pdf",
             "source_title": "EO 7504 in FR", "local_file": tmpfile + "shards/S_T/cache/FR-1936-12-16.txt"},
        ]
        proposals = [
            {"instrument_id": "EO:9054", "operative_footprint": [{"evidence_ids": ["T1", "T2"]}], "note": "cites 55 Stat. 838"},
            {"instrument_id": "EO:7504", "operative_footprint": [{"evidence_ids": ["T3"]}]},
        ]
        reviews = [{"instrument_id": "EO:9054", "reviewer_evidence": [
            {"sha256": sha["evidence/shards/S_T/cache/fr_1942-02-05_p3-4.pdf"], "quote": "no match here at all, short"}]}]
        status = [{"instrument_id": i, "evidence_dir": "evidence/shards/S_T/", "review_dir": "evidence/reviews/V_T/"}
                  for i in ("EO:9054", "EO:7504", "EO:8000", "EO:8100")]
        status[2]["note"] = "see " + tmpfile + "shards/S_T/cache/huge_scan.pdf"
        # EO:8100 cites a PDF only by URL plus a local .txt conversion: the original is missing,
        # which is NOT the same as citing no media
        status[3]["note"] = ("https://www.govinfo.gov/content/pkg/FR-1950-01-01/pdf/FR-1950-01-01.pdf "
                             + tmpfile + "shards/S_T/cache/fr_1950-01-01.txt")
        meta_1950 = {"url": "https://www.govinfo.gov/content/pkg/FR-1950-01-01/pdf/FR-1950-01-01.pdf",
                     "content_type": "application/pdf", "sha256": "d" * 64}
        denied_meta = {"url": "https://www.example.mil/Portals/doc.pdf", "sha256": "e" * 64,
                       "retrieved_utc": "2026-10-16T20:00:00Z"}
        meta = {"url": "https://www.govinfo.gov/content/pkg/FR-1942-02-05/pdf/FR-1942-02-05.pdf", "sha256": "b" * 64,
                "excerpt_sha256": sha["evidence/shards/S_T/cache/fr_1942-02-05_p3-4.pdf"],
                "retrieved_utc": "2026-10-16T21:00:00Z"}
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)

            def jl(rows):
                return "\n".join(json.dumps(r) for r in rows) + "\n"
            with zipfile.ZipFile(d / "complete.zip", "w") as z:
                z.writestr(P + "STAGE11_ACCEPTED.jsonl", jl([{"instrument_id": "EO:9054"}, {"instrument_id": "EO:7504"},
                                                            {"instrument_id": "EO:9999"}, {"instrument_id": "EO:8100"}]))
                z.writestr(P + "STAGE11_STATUS_RECORDS.jsonl", jl(status))
                z.writestr(P + "evidence/shards/S_T/evidence.jsonl", jl(evidence))
                z.writestr(P + "evidence/shards/S_T/status_proposals.jsonl", jl(proposals))
                z.writestr(P + "evidence/reviews/V_T/reviews.jsonl", jl(reviews))
                z.writestr(P + "evidence/shards/S_T/cache/fr_1942-02-05.meta.json", json.dumps(meta))
                z.writestr(P + "evidence/shards/S_T/cache/fr_1950-01-01.meta.json", json.dumps(meta_1950))
                z.writestr(P + "evidence/reviews/V_T/cache/denied.meta.json", json.dumps(denied_meta))
                z.writestr(P + "evidence/UNPACKAGED_LARGE_ORIGINALS.jsonl",
                           jl([{"path": "evidence/shards/S_T/cache/huge_scan.pdf", "bytes": 9, "sha256": "c" * 64}]))
            with zipfile.ZipFile(d / "media.zip", "w") as z:
                for k, v in media.items():
                    z.writestr(P + k, v)
            with open(d / "map.csv", "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["manifest_path", "sha256"])
                for k in media:
                    w.writerow([k, sha[k]])
            (d / "full844.jsonl").write_text(jl([{"instrument_id": "EO:9054"}, {"instrument_id": "EO:7504"},
                                                 {"instrument_id": "EO:9999"}, {"instrument_id": "EO:8100"}]),
                                             encoding="utf-8")
            out = d / "out"
            summary = mm.run(d, out, cache_dir=d / "cache", ocr_enabled=False, progress=lambda s: None,
                             paths={"media_zip": str(d / "media.zip"), "complete_zip": str(d / "complete.zip"),
                                    "member_map": str(d / "map.csv"), "full_844": str(d / "full844.jsonl"),
                                    "note_leads": None, "integrity": None})
            rows = _csv(out / "MATCHES.csv")
            by = {(r["member_path"].rsplit("/", 1)[-1], r["instrument_id"]): r for r in rows}

            fr = by[("fr_1942-02-05_p3-4.pdf", "EO:9054")]
            self.assertEqual(fr["grade"], "unique_supported")
            self.assertEqual(fr["role"], "order_text_candidate")
            for fam in ("eo_number_in_text", "quote_in_text", "citation_in_text", "opus_record_link", "filename_match"):
                self.assertIn(fam, fr["signal_families"])
            self.assertIn("1", fr["page_refs"])

            st = by[("stat_55_838.pdf", "EO:9054")]
            self.assertEqual(st["grade"], "unique_supported")
            self.assertEqual(st["role"], "cited_source")

            old = by[("FR-1936-12-16.pdf", "EO:7504")]
            self.assertEqual(old["grade"], "unique_supported")
            self.assertEqual(old["role"], "order_text_candidate")

            self.assertEqual(by[("scan.png", "")]["grade"], "unmatched")
            self.assertIn("OCR", by[("scan.png", "")]["notes"])
            self.assertEqual(by[("denied.pdf", "")]["grade"], "unmatched")

            frags = [json.loads(x) for x in _lines(out / "FRAGMENTS.jsonl")]
            self.assertEqual(sorted(f["instrument_id"] for f in frags), ["EO:7504", "EO:9054"])
            for f in frags:
                self.assertEqual(f["kind"], "original_representation")
                ref = f["sources"][0]
                self.assertTrue(ref["archival_id"].startswith(mm.ARCHIVE_ID_PREFIX + ":"))
                self.assertEqual(len(ref["local_file_sha256"]), 64)
                self.assertTrue(ref["page_or_item"])
                self.assertEqual(f["data"]["status"], "candidate_unverified")
            f9054 = next(f for f in frags if f["instrument_id"] == "EO:9054")
            self.assertEqual(f9054["sources"][0]["upstream_url"], meta["url"])
            self.assertIn("heading on p1", f9054["sources"][0]["page_or_item"])

            srcs = [json.loads(x) for x in _lines(out / "SOURCES.jsonl")]
            self.assertEqual(len(srcs), 6)
            by_src = {s["source_id"].rsplit("/", 1)[-1]: s for s in srcs}
            for bad, defect in (("denied.pdf", "access_denied_or_error_html"), ("empty.pdf", "empty_file")):
                s = by_src[bad]
                self.assertIs(s["usable_as_document"], False)
                self.assertEqual(s["defect"], defect)
                self.assertIsNone(s["url"])
                self.assertTrue(s["notes"].startswith("NOT the document"))
                self.assertEqual(s["instrument_ids"], [])
            self.assertEqual(by_src["denied.pdf"]["upstream_url"], denied_meta["url"])
            self.assertEqual(by_src["denied.pdf"]["upstream_retrieved_utc"], denied_meta["retrieved_utc"])
            # an excerpt: its bytes are not what the upstream URL served, so url stays null
            ex = by_src["fr_1942-02-05_p3-4.pdf"]
            self.assertIs(ex["sha256_is_of_url_bytes"], False)
            self.assertIsNone(ex["url"])
            self.assertEqual(ex["upstream_url"], meta["url"])
            self.assertTrue(by_src["stat_55_838.pdf"]["usable_as_document"])
            # every output is written with LF line ends on every OS
            for name in ("SUMMARY.json", "SOURCES.jsonl", "MATCHES.csv", "OPUS_CASE_MEDIA_STATUS.csv"):
                self.assertNotIn(b"\r\n", (out / name).read_bytes(), name)
            for s in srcs:
                for k in ("source_id", "instrument_ids", "url", "sha256", "bytes", "content_type", "retrieved_utc",
                          "route", "page_or_item", "text_path", "cache_path", "notes"):
                    self.assertIn(k, s)
                if s["text_path"]:
                    self.assertTrue((out / s["text_path"]).exists())

            status_rows = {r["instrument_id"]: r for r in _csv(out / "OPUS_CASE_MEDIA_STATUS.csv")}
            self.assertEqual(status_rows["EO:9054"]["media_status"], "unique_supported")
            self.assertEqual(status_rows["EO:9999"]["media_status"], "no_member_signal")
            self.assertIn("cite no PDF", status_rows["EO:9999"]["note"])
            self.assertEqual(status_rows["EO:9999"]["media_gap"], "none_cited")
            r8100 = status_rows["EO:8100"]
            self.assertEqual(r8100["media_status"], "no_member_signal")
            self.assertEqual(r8100["media_gap"], "originals_not_in_companion")
            self.assertEqual(r8100["media_urls_cited_in_case_records"], "1")
            self.assertEqual(r8100["cited_media_kept_only_as_text"], "1")
            self.assertNotIn("cite no PDF", r8100["note"])
            self.assertIn("re-fetched", r8100["note"])
            # EO:7504's cited FR issue is in the companion (same file name in its folder)
            self.assertEqual(status_rows["EO:7504"]["cited_media_urls_not_in_companion"], "0")
            self.assertEqual(status_rows["EO:8000"]["in_accepted_844"], "no")
            self.assertIn("left out of the release", status_rows["EO:8000"]["note"])

            self.assertEqual(summary["sha256_check"]["matches_member_map"], 6)
            self.assertEqual(summary["member_kinds"]["html_saved_under_media_name"], 1)
            self.assertEqual(summary["text"]["members_needing_ocr"], 1)
            self.assertEqual(summary["accepted_844"]["with_unique_supported_member"], 2)
            self.assertEqual(summary["accepted_844"]["no_member_signal_because_records_cite_no_media_at_all"], 1)
            self.assertEqual(summary["accepted_844"]["no_member_signal_because_cited_originals_not_in_companion"], 1)
            self.assertEqual(summary["sources"]["usable_as_document_false"], 2)
            self.assertTrue((out / "SUMMARY.json").exists())

            # rerun uses the text cache and gives the same matches
            mm.run(d, d / "out2", cache_dir=d / "cache", ocr_enabled=False, progress=lambda s: None,
                   paths={"media_zip": str(d / "media.zip"), "complete_zip": str(d / "complete.zip"),
                          "member_map": str(d / "map.csv"), "full_844": str(d / "full844.jsonl"),
                          "note_leads": None, "integrity": None})
            self.assertEqual((out / "MATCHES.csv").read_text(encoding="utf-8"),
                             (d / "out2" / "MATCHES.csv").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
