import csv
import hashlib
import io
import json
import os
import pathlib
import tempfile
import unittest

import hunt as H

HERE = pathlib.Path(__file__).resolve().parent
PROV = json.loads((HERE / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
BOOKS = json.loads((HERE / "data" / "BOOKS.json").read_text(encoding="utf-8"))


class Citations(unittest.TestCase):
    def kinds(self, text):
        return [(c["kind"], c.get("book_key"), c.get("page")) for c in H.parse_citations(text)]

    def test_richardson_appendix_and_volume(self):
        cs = H.parse_citations("Annals , 2 Cong . , 1 sess . , 1247 ; X Richardson App . 84")
        rich = [c for c in cs if c["kind"] == "richardson"][0]
        self.assertEqual((rich["volume"], rich["appendix"], rich["page"], rich["book_key"], rich["section"]), (10, True, 84, "RICH_X", "appendix"))
        ann = [c for c in cs if c["kind"] == "annals_of_congress"][0]
        self.assertEqual((ann["congress"], ann["session"], ann["column"]), (2, 1, 1247))
        self.assertEqual(self.kinds("II Richardson 544"), [("richardson", "RICH_II", 544)])
        self.assertIn(("richardson", "RICH_X", 895), self.kinds("Annals, 1 1046; X Richardson App. 895 2 Congse"))
        self.assertEqual(self.kinds("X Richard- son App . 33"), [("richardson", "RICH_X", 33)])

    def test_reservation_and_land_office_books(self):
        cs = self.kinds("( 1898 MR 26 ; 1907 MR 40 ; 1910 MR 46 ; 1916 MR 55 ; I CFR")
        self.assertEqual(cs, [("mr", "MR_1898", 26), ("mr", "MR_1907", 40), ("mr", "MR_1910", 46), ("mr", "MR_1916", 55)])
        cs = self.kinds("( 1880 GLO 53 ; 1884 GLO 41 ; 1892 GLO 82 )")
        self.assertEqual(cs, [("glo", "GLO_1880", 53), ("glo", "GLO_1884", 41), ("glo", "GLO_1892", 82)])

    def test_routes_for_sources_without_a_book(self):
        cs = H.parse_citations("under the acts of Aug. 4 , 1790 ( 1 Stat.L. 138 ) and Aug. 1 ( 1 Stat.L. 136 ); Amer . St. Papers , Indian Affairs I , 96 ; Kappler I 823; S. Doc . 12 ")
        kinds = {c["kind"] for c in cs}
        self.assertEqual(kinds, {"statutes_at_large", "american_state_papers", "kappler", "congressional_document"})
        stat = [c for c in cs if c["kind"] == "statutes_at_large"]
        self.assertEqual({(c["volume"], c["page"]) for c in stat}, {(1, 138), (1, 136)})
        self.assertTrue(all(c.get("route") for c in cs))
        asp = [c for c in cs if c["kind"] == "american_state_papers"][0]
        self.assertEqual((asp["series"], asp["volume"], asp["page"]), ("Indian Affairs", 1, 96))

    def test_no_citation_no_output(self):
        self.assertEqual(H.parse_citations("Fort Brooke Military Reservation , Florida Territory , established ."), [])


class Dates(unittest.TestCase):
    def test_lord_dates(self):
        self.assertEqual(H.parse_lord_date("1790", "Aug 28"), ("1790-08-28", "day"))
        self.assertEqual(H.parse_lord_date("1828", "Sept. 287"), ("1828-09", "month"))
        self.assertEqual(H.parse_lord_date("1789", ""), ("1789", "year"))
        self.assertEqual(H.parse_lord_date("1806", "Mar 18"), ("1806-03-18", "day"))

    def test_date_patterns_match_printed_forms(self):
        pats = H.date_patterns("1789-10-06", "day")
        self.assertTrue(any(p.search("this 6th day of October, A. D. 1789") for p in pats))
        self.assertTrue(any(p.search("Washington, October 6, 1789.") for p in pats))
        self.assertTrue(any(p.search("Reserved by Executive Order for military purposes February 13, 1844") for p in H.date_patterns("1844-02-13", "day")))
        self.assertFalse(any(p.search("October 16, 1789") for p in H.date_patterns("1789-10-06", "day")))

    def test_keywords_skip_boilerplate(self):
        kws = H.keywords("Certain described lands on Bois Blanc Island , Michigan Territory , reserved for fuel supply for Fort Mackinac .")
        self.assertIn("mackinac", kws)
        self.assertNotIn("reserved", kws)
        self.assertNotIn("territory", kws)


def djvu_xml(pages):
    parts = ['<?xml version="1.0" encoding="UTF-8"?><DjVuXML><BODY>']
    for i, text in enumerate(pages, 1):
        parts.append(f'<OBJECT data="x" type="image/x.djvu" usemap="p_{i:04d}.djvu"><PARAM name="PAGE" value="p_{i:04d}.djvu"/><HIDDENTEXT><PAGECOLUMN><REGION><PARAGRAPH>')
        for line in text.split("\n"):
            words = "".join(f'<WORD coords="0,0,0,0">{w}</WORD>' for w in line.split(" ") if w)
            parts.append(f"<LINE>{words}</LINE>")
        parts.append("</PARAGRAPH></REGION></PAGECOLUMN></HIDDENTEXT></OBJECT>")
    parts.append("</BODY></DjVuXML>")
    return "".join(parts).encode("utf-8")


def fake_book(n_front=3, n_main=30, appendix_from=None):
    pages = ["title page", "blank", "contents"][:n_front]
    for p in range(1, n_main + 1):
        if appendix_from and p >= appendix_from:
            head = f"Appendix {p}" if p % 2 else f"{p} Messages and Papers of the Presidents"
        else:
            head = f"{p} Messages and Papers of the Presidents" if p % 2 == 0 else f"George Washington {p}"
        body = f"{head}\nBody text of printed page {p}.\nMore text."
        if p == 7:
            body += "\nUNITED STATES, October 6, 1789.\nTo Arthur St. Clair, Governor:\nYou will ascertain the intentions of the Wabash Indians.\nGiven under my hand this 6th day of October, A. D. 1789.\nWASHINGTON.\nNEXT TITLE"
        pages.append(body)
    return pages


class PagesAndMap(unittest.TestCase):
    def test_djvu_pages_join_words(self):
        pages = H.djvu_pages(djvu_xml(["A  B\nC", "", "D"]))
        self.assertEqual(pages, [(1, "A B\nC"), (2, ""), (3, "D")])

    def test_head_number_reads_both_sides_and_sections(self):
        self.assertEqual(H.head_number("84 Messages and Papers of the Presidents\nbody"), ("main", 84))
        self.assertEqual(H.head_number("Appendix 83\nGiven under my hand"), ("appendix", 83))
        self.assertEqual(H.head_number("MILITARY RESERVATIONS, ETC. 27\nBARRANCAS"), ("main", 27))
        self.assertEqual(H.head_number("Index 281\nCalifornia"), ("index", 281))
        self.assertEqual(H.head_number("Given under my hand, in the city of New York"), ("main", None))

    def test_printed_page_map_survives_misreads_and_fills_gaps(self):
        pages = fake_book(n_front=3, n_main=30)
        pages[3 + 9] = "9O Messages and Papers of the Presidents\nmisread head"  # OCR 'O' for 0: unreadable number
        pages[3 + 14] = "150 Messages and Papers of the Presidents\nwrong head"  # misread 15 as 150
        pm, stats = H.printed_page_map([(i + 1, t) for i, t in enumerate(pages)])
        self.assertEqual(pm[3 + 7], ("main", 7))
        self.assertEqual(pm[3 + 15], ("main", 15), "a misread head does not shift the map")
        self.assertEqual(pm[3 + 10], ("main", 10), "an unreadable head is filled from its neighbours")
        self.assertGreaterEqual(stats["heads_agree"], 25)
        self.assertEqual(stats["heads_disagree"], 1)
        inv = H.inverse_map(pm)
        self.assertEqual(inv[("main", 7)], [10])

    def test_appendix_pages_map_in_their_own_section(self):
        pages = fake_book(n_front=2, n_main=40, appendix_from=21)
        pm, stats = H.printed_page_map([(i + 1, t) for i, t in enumerate(pages)])
        inv = H.inverse_map(pm)
        self.assertEqual(inv[("appendix", 23)], [2 + 23])
        self.assertIn("appendix", stats["sections"])


class Locate(unittest.TestCase):
    def test_locate_and_excerpt_richardson(self):
        pages = fake_book()
        lead = {"date": "1789-10-06", "date_precision": "day", "keywords": ["clair", "wabash", "indians"]}
        hit = H.locate(lead, [(10, pages[3 + 6])])
        self.assertEqual(hit["grade"], "page_date_and_subject")
        body, first, last = H.excerpt(pages[3 + 6], hit["date_span"], "richardson")
        self.assertTrue(body.startswith("UNITED STATES, October 6, 1789."))
        self.assertTrue(body.rstrip().endswith("WASHINGTON."))
        self.assertNotIn("NEXT TITLE", body)

    def test_locate_grades_without_date(self):
        text = "FORT MORGAN.\nContains about 322.42 acres on Mobile Point.\nReserved by Executive Order for military purposes February 13, 1844.\nFORT GAINES.\nother"
        lead = {"date": "1844-02-13", "date_precision": "day", "keywords": ["morgan", "mobile"]}
        hit = H.locate(lead, [(5, text)])
        self.assertEqual(hit["grade"], "page_date_and_subject")
        body, _, _ = H.excerpt(text, hit["date_span"], "mr")
        self.assertTrue(body.startswith("FORT MORGAN."))
        self.assertNotIn("FORT GAINES", body)
        lead2 = {"date": "1844-02-14", "date_precision": "day", "keywords": ["gaines"]}
        self.assertEqual(H.locate(lead2, [(5, text)])["grade"], "page_only")


class Registry(unittest.TestCase):
    def test_books_have_unique_keys_and_lord_forms(self):
        keys = [b["key"] for b in BOOKS["books"]]
        self.assertEqual(len(keys), len(set(keys)))
        for b in BOOKS["books"]:
            self.assertIn(b["kind"], ("richardson", "mr", "glo"))
            self.assertTrue(b["key"].startswith({"richardson": "RICH_", "mr": "MR_", "glo": "GLO_"}[b["kind"]]))
        self.assertEqual([b for b in BOOKS["books"] if b["key"] == "RICH_X"][0]["appendix"], True)

    def test_edition_check(self):
        meta = {"title": "A compilation of the messages and papers of the presidents, 1789-1897", "publisher": "[Washington], Congress", "date": "1899"}
        self.assertTrue(H.check_edition(meta, BOOKS["books"][9]["verify"])["edition_ok"])
        bad = dict(meta, publisher="New York : Bureau of National Literature", date="1913")
        self.assertFalse(H.check_edition(bad, BOOKS["books"][9]["verify"])["edition_ok"])

    def test_vendored_lord_subset_matches_provenance(self):
        path = HERE / PROV["lord_subset"]["file"]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), PROV["lord_subset"]["sha256"])
        with path.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), PROV["lord_subset"]["rows"])
        self.assertTrue(all(int(r["year"]) < 1900 for r in rows))

    def test_rank_books_weights_pre_1862_three_times(self):
        books = {b["key"]: b for b in BOOKS["books"]}
        leads = [{"lead_id": "a", "year": 1850, "citations": H.parse_citations("1898 MR 23")},
                 {"lead_id": "b", "year": 1890, "citations": H.parse_citations("1898 MR 24; 1880 GLO 5")},
                 {"lead_id": "c", "year": 1891, "citations": H.parse_citations("1880 GLO 6")}]
        r = H.rank_books(leads, books)
        self.assertEqual([x["book_key"] for x in r], ["MR_1898", "GLO_1880"])
        self.assertEqual(r[0]["weight"], 4)


class FakeTransport:
    """Serves Internet Archive metadata and page text for fake books; refuses everything else.
    'fakeident' is a complete 32-page book; 'shortident' is a 6-page extract of it."""

    def __init__(self):
        self.pages = fake_book(n_front=2, n_main=30)
        self.books = {"fakeident": djvu_xml(self.pages), "shortident": djvu_xml(self.pages[:6])}
        self.calls = []

    def __call__(self, url, headers, timeout):
        self.calls.append(url)
        if url.endswith("/robots.txt"):
            return 200, {}, io.BytesIO(b"User-agent: *\nDisallow: /control/\n")
        for ident, xml in self.books.items():
            if url == H.IA_METADATA.format(ident=ident):
                body = json.dumps({"metadata": {"title": "A compilation of the messages and papers of the presidents, 1789-1897", "publisher": "[Washington], Congress", "date": "1899"},
                                   "files": [{"name": f"{ident}_djvu.xml", "sha1": hashlib.sha1(xml).hexdigest(), "size": str(len(xml))},
                                             {"name": f"{ident}.pdf", "sha1": "abc", "size": "1234"}]}).encode()
                return 200, {"content-length": str(len(body))}, io.BytesIO(body)
            if url == H.IA_DOWNLOAD.format(ident=ident, name=f"{ident}_djvu.xml"):
                return 200, {"content-length": str(len(xml))}, io.BytesIO(xml)
        return 404, {}, io.BytesIO(b"")


class EndToEnd(unittest.TestCase):
    def make_repo(self, tmp):
        repo = pathlib.Path(tmp) / "repo"
        (repo / "research/stage14/LORD").mkdir(parents=True)
        (repo / "research/stage18/data").mkdir(parents=True)
        with (repo / "research/stage14/LORD/LORD_CHRONOLOGICAL_REVIEW_LEADS.csv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["candidate_id", "pdf_page", "loc_page_url", "pdf_word_y", "month", "day", "raw_month", "year_hint_UNVERIFIED", "date_status", "source_excerpt_UNVERIFIED", "flags", "identity_class", "source_pdf_sha256"])
            w.writerow(["LORD:PDF:24:1", "24", "https://www.loc.gov/resource/gdc.43013029/?sp=24", "1", "10", "6", "Oct", "1789", "NOT_AUTHENTICATED", "St. Clair instructed Wabash Indians; Amer. St. Papers, Indian Affairs I, 96; X Richardson App. 81", "", "UNRESOLVED", "0" * 64])
        with (repo / "research/stage18/data/EARLY_SOURCE_CANDIDATES.csv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["candidate_id", "date", "claimed_issuer", "document_identity", "source_representation", "primary_source_url", "local_source", "authentication_finding", "inclusion_state", "next_test"])
            w.writerow(["LORD-1789-10-06", "1789-10-06", "George Washington", "Instructions to Arthur St Clair", "ASP", "https://www.loc.gov/resource/law.llsp007/?sp=98", "", "", "candidate_not_counted", ""])
        return repo

    def test_offline_run_writes_every_output_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)
            out = pathlib.Path(tmp) / "out"
            env = dict(os.environ)
            os.environ.update(HUNT_OFFLINE="1", JOB_CACHE_DIR=str(pathlib.Path(tmp) / "cache"))
            try:
                s = H.run(repo, HERE, out, transport=lambda *a: (_ for _ in ()).throw(AssertionError("network used")))
            finally:
                os.environ.clear()
                os.environ.update(env)
            for name in ("LEADS.csv", "CITATIONS.csv", "RESOLVED.csv", "BOOKS.csv", "LIVE_ROUTES.csv", "LIVE_HITS.csv", "SUMMARY.json", "REPORT.md"):
                self.assertTrue((out / name).is_file(), name)
            self.assertTrue(s["offline"])
            self.assertEqual(s["leads"]["total"], 1158 + 1 + 1)
            self.assertEqual(s["books"]["fetched"], 0)
            self.assertEqual(s["live"]["routes"], 0)
            self.assertEqual(s["requests"]["pool_requests"], 0)
            self.assertGreater(s["citations"]["by_kind"]["glo"], 500)
            self.assertEqual(s["resolved"]["by_grade"].get("book_not_held"), s["resolved"]["citations_against_books"])

    def test_live_run_with_fake_archive_cuts_a_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)
            out = pathlib.Path(tmp) / "out"
            job = pathlib.Path(tmp) / "job"
            (job / "data").mkdir(parents=True)
            # The preferred copy is a 6-page extract; the job must fall back to the complete alternate.
            books = {"books": [{"key": "RICH_X", "kind": "richardson", "label": "fake vol X", "ia_identifier": "shortident", "ia_alternates": ["fakeident"],
                                "verify": {"title_words": ["messages"], "year_any": [1899], "publisher_any": ["congress"], "min_pages": 30}, "appendix": True}]}
            (job / "data/BOOKS.json").write_text(json.dumps(books), encoding="utf-8")
            (job / "data/lord_subset").mkdir()
            with (job / "data/lord_subset/UNNUMBERED_ENTRIES_pre1900.csv").open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh, lineterminator="\n")
                w.writerow(["seq", "year", "date", "pairing", "page", "family_hint", "source_kinds_joined", "citations_joined", "summary", "citation_text"])
                w.writerow(["1", "1789", "Oct 6", "paired", "30", "emergency_war", "", "", "Governor St. Clair instructed as to the Wabash and Illinois Indians", "Amer . St. Papers , Indian Affairs I , 96 ; X Richardson App . 7"])
                w.writerow(["2", "1830", "", "uncertain", "31", "other", "", "", "Fort Brooke Military Reservation established", "( 1916 MR 478 )"])
            transport = FakeTransport()
            env = dict(os.environ)
            os.environ.update(HUNT_LIVE_ROUTES="0", JOB_CACHE_DIR=str(pathlib.Path(tmp) / "cache"), HUNT_MAX_REQUESTS="10")
            os.environ.pop("HUNT_OFFLINE", None)
            try:
                s = H.run(repo, job, out, transport=transport)
            finally:
                os.environ.clear()
                os.environ.update(env)
            self.assertEqual(s["books"]["fetched"], 1)
            self.assertEqual(s["books"]["sha1_mismatches"], [])
            grades = s["resolved"]["by_grade"]
            self.assertEqual(grades.get("page_date_and_subject"), 1, grades)
            self.assertEqual(grades.get("book_not_held"), 1, "MR_1916 is not in this registry")
            texts = list((out / "texts").glob("*.txt"))
            self.assertEqual(len(texts), 1)
            body = texts[0].read_text(encoding="utf-8")
            self.assertIn("----- EXACT SLICE -----", body)
            self.assertIn("UNITED STATES, October 6, 1789.", body)
            rec = json.loads((out / "books/RICH_X.json").read_text(encoding="utf-8"))
            self.assertTrue(rec["custody"]["sha1_matches_archive"])
            self.assertTrue(rec["edition"]["edition_ok"])
            self.assertEqual(rec["ia_identifier"], "fakeident", "the short extract was passed over for the complete alternate")
            self.assertEqual([c["ia_identifier"] for c in rec["copies_tried"]], ["shortident", "fakeident"])
            self.assertEqual(rec["copies_tried"][0]["pages"], 6)
            self.assertTrue((out / "books/RICH_X_pages.jsonl.gz").is_file())
            self.assertLessEqual(s["requests"]["spent"], 5)

    def test_subject_only_hit_is_cut_around_the_subject(self):
        text = "SURVEYS. 169\nSchedule of military reservations.\nFort Pembina, secs. 16, 17.\nFort Totten, within the Devils Lake reservation.\n" + "filler line\n" * 40 + "SANTA ROSA ISLAND, Fla., naval reservation by order of 1838.\nmore\n"
        lead = {"date": "1838-04-21", "date_precision": "day", "keywords": ["santa", "island", "naval"]}
        hit = H.locate(lead, [(178, text)])
        self.assertEqual(hit["grade"], "page_and_subject")
        body, first, last = H.excerpt(text, hit["anchor"], "glo")
        self.assertIn("SANTA ROSA ISLAND", body)
        self.assertNotIn("Fort Pembina", body)


if __name__ == "__main__":
    unittest.main()
