"""Tests for the defects found in review. Sentences are real OLRC text from
release point 119-121 (usc05.xml, usc03.xml, usc10.xml, usc12.xml,
usc20.xml, usc22.xml, usc50.xml), shortened where noted. No network."""

import hashlib
import json
import os
import pathlib
import tempfile
import unittest
import urllib.error
import zipfile

import build
import ecfr_scan
import eo_refs
import job
import net
import usc_scan


def events(text):
    return eo_refs.editorial_events(text)


def actor_num(e):
    return ((e["actor"] or {}).get("ref") or {}).get("number")


class RealSentences(unittest.TestCase):
    def test_relative_clause_subject(self):
        # 5 U.S.C. 601 note (shortened): EO 14015 was revoked, not EO 14205.
        s = ("[Ex. Ord. No. 14205, which directed amendment of Ex. Ord. No. 13198, set out above, by substituting "
             "“White House Faith Office” for “White House OFBCI”, was executed by substituting "
             "“White House Faith Office” for “White House Office of Faith-Based and Neighborhood "
             "Partnerships”, due to the intervening amendment by Ex. Ord. No. 14015, which was revoked by "
             "Ex. Ord. No. 14148, § 2(y), Jan. 20, 2025, 90 F.R. 8238.]")
        ev = events(s)
        self.assertEqual([(e["subject"]["number"], actor_num(e)) for e in ev], [(14015, 14148)])

    def test_savings_clause_is_not_an_event(self):
        # 3 U.S.C. 301 note (Ex. Ord. No. 11012)
        s = ("Existing regulations prescribed by the Director of the Office of Management and Budget under the "
             "authority of Section 1(b) of Executive Order No. 10530, as amended and in effect immediately prior to "
             "the issuance of this order, shall remain in effect until they are superseded in pursuance of the "
             "provisions of this order.")
        self.assertEqual(events(s), [])
        self.assertEqual(eo_refs.ended_subject_keys(s), set())

    def test_subject_side_scope(self):
        cases = [
            ("(a) Section 3 of Executive Order 13492 of January 22, 2009 (Review and Disposition of Individuals "
             "Detained at the Guantánamo Bay Naval Base) [formerly set out above], ordering the closure of "
             "detention facilities at U.S. Naval Station Guantánamo Bay, is hereby revoked.", 13492, "Section 3 of"),
            ("Section 1(u) of Ex. Ord. No. 13889 was superseded by Ex. Ord. No. 13935, § 4(a), July 9, 2020, "
             "85 F.R. 42685, formerly set out below.", 13889, "Section 1(u) of"),
            ("The fifth and sixth paragraphs of Ex. Ord. No. 6073, relating to the removal of gold coin, were revoked "
             "by Ex. Ord. No. 11825, Dec. 31, 1974, 40 F.R. 1003.", 6073, "fifth and sixth paragraphs of"),
            ("Functions Abolished Section 18 of Ex. Ord. No. 6166, which provided for the partial abolition of "
             "cooperative vocational education payments, was revoked by Ex. Ord. No. 6536 of Feb. 6, 1934.", 6166,
             "Section 18 of"),
            ("Burma Ex. Ord. No. 13047, May 20, 1997, 62 F.R. 28301, sections 1 to 7 of which were revoked by "
             "Ex. Ord. No. 13310, § 12, July 28, 2003, 68 F.R. 44855.", 13047, "sections 1 to 7 of which"),
        ]
        for text, num, scope in cases:
            ev = events(text)
            self.assertEqual(len(ev), 1, text)
            self.assertEqual(ev[0]["subject"]["number"], num)
            self.assertIn(scope, ev[0]["subject_scope"])

    def test_statute_named_before_verb_is_the_actor(self):
        # 5 U.S.C. 901 note (EO 6166): an Act superseded part of the printed order.
        s = ("Section 102(c) of act June 30, 1949, as renumbered by act Sept. 5, 1950, ch. 849, §§ 6(a), "
             "(b), 7(e), 64 Stat. 583, provided that: “The provisions of the first, third, and fifth paragraphs "
             "of section 1 of Executive Order Numbered 6166 of June 10, 1933 [this Ex. Ord.], are hereby superseded, "
             "insofar as they relate to any function now administered by the Bureau of Federal Supply.”")
        ev = events(s)
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["actor"]["kind"], "statute")
        self.assertTrue(ev[0]["qualified"])
        self.assertIn("paragraphs of section 1 of", ev[0]["subject_scope"])
        # 22 U.S.C. 2381 note (EO 12163): Pub. L. 105-277 repealed parts of it.
        s2 = ("[Pub. L. 105–277, div. G, subdiv. A, title XIV, § 1422(a)(2), Oct. 21, 1998, 112 Stat. "
              "2681–792, provided that sections 1–101 through 1–103, 1–401 through 1–403, and "
              "1–801(a), and other provisions of Ex. Ord. No. 12163 that relate to the United States "
              "International Development Cooperation Agency or the Director thereof were repealed.]")
        ev2 = events(s2)
        self.assertEqual(ev2[0]["subject"]["number"], 12163)
        self.assertEqual(ev2[0]["actor"]["kind"], "statute")
        self.assertEqual(ev2[0]["actor"]["publ"], "Pub. L. 105-277")
        self.assertTrue(ev2[0]["subject_scope"])

    def test_as_amended_by_actor(self):
        # 50 U.S.C. 3036 note
        s = ("Ex. Ord. No. 13355, Aug. 27, 2004, 69 F.R. 53593, which related to strengthened management of the "
             "Intelligence Community, was revoked by Ex. Ord. No. 12333, § 3.6, Dec. 4, 1981, 46 F.R. 59954, as "
             "amended by Ex. Ord. No. 13470, § 4(j), July 30, 2008, 73 F.R. 45341, set out as a note under "
             "section 3001 of this title.")
        ev = events(s)[0]
        self.assertEqual(ev["subject"]["number"], 13355)
        self.assertEqual(actor_num(ev), 12333)
        self.assertEqual(ev["actor"]["amended_by"]["ref"]["number"], 13470)
        self.assertEqual(ev["actor"]["amended_by"]["date"], "2008-07-30")

    def test_amendment_after_ending_verb_belongs_to_actor(self):
        s = ("Ex. Ord. No. 13355, Aug. 27, 2004, 69 F.R. 53593, which related to strengthened management of the "
             "Intelligence Community, was revoked by Ex. Ord. No. 12333, § 3.6, Dec. 4, 1981, 46 F.R. 59954, as "
             "amended by Ex. Ord. No. 13470, § 4(j), July 30, 2008, 73 F.R. 45341.")
        self.assertEqual(eo_refs.amendments_listed(s), [])
        s2 = ("Ex. Ord. No. 11230, June 28, 1965, 30 F.R. 8847, as amended by Ex. Ord. No. 11275, Mar. 31, 1966, "
              "31 F.R. 5283, was superseded by Ex. Ord. No. 11609, July 22, 1971, 36 F.R. 13747.")
        self.assertEqual([a["ref"]["number"] for a in eo_refs.amendments_listed(s2)], [11275])

    def test_order_inside_a_phrase_is_flagged(self):
        for s in ("(a) Civil Service Rule 9 (5 CFR Part 9), as established by Executive Order No. 11315, as amended, "
                  "is revoked.",
                  "The Office of Alien Property Custodian in the Office for Emergency Management of the Executive Office "
                  "of the President, established by Executive Order No. 9095 of March 11, 1942 [7 F.R. 1971], is hereby "
                  "terminated."):
            ev = events(s)
            self.assertEqual(ev[0]["context"], "subject_inside_prepositional_phrase", s)
            self.assertEqual(eo_refs.ended_subject_keys(s), set())
        book = small_book()
        row = book.add_event(eo_refs.make_event(events("(a) Civil Service Rule 9, as established by Executive Order "
                                                       "No. 11764, is revoked.")[0], {"citation": "c"}), "usc", "e", "s", "p")
        self.assertEqual(row["caution"], "subject_inside_prepositional_phrase")
        self.assertEqual(book.fragments(), [])
        # back-references and relative clauses keep the order as the subject
        for s, num in (("(a) The Federal Energy Office established by Executive Order No. 11748 is hereby abolished, "
                        "and that Executive order is hereby revoked.", 11748),
                       ("Functions were previously delegated by Ex. Ord. No. 11958, which was formerly set out as a note "
                        "under section 2751 of this title and which was revoked by Ex. Ord. No. 13637, Mar. 8, 2013.", 11958),
                       ("refer the matter to the Recreation Advisory Council established under Executive Order No. 11017 "
                        "[superseded by Ex. Ord. No. 11278, which in turn was revoked by Ex. Ord. No. 11472, May 29, "
                        "1969].", 11278)):
            ev = events(s)[-1]
            self.assertEqual((ev["subject"]["number"], ev["context"]), (num, ""), s)
        # a real whole-order revocation in the same style is not flagged
        self.assertEqual(events("Executive Order No. 11726 of June 29, 1973, is hereby superseded.")[0]["context"], "")

    def test_sentence_ends_after_closing_quote(self):
        # 50 U.S.C. 1701 note (shortened): EO 13224 is not the subject of the bracketed note's verb.
        s = ("“(2) is no longer designated for the imposition of sanctions pursuant to Executive Order 13224 "
             "(50 U.S.C. 1701 note; relating to blocking property).” [Pub. L. 117–263, § 6811(e), which "
             "directed amendment of section 204(b) of Pub. L. 114–102, was executed to section 204(b), which was "
             "rescinded by Memorandum of President of the United States, Jan. 2, 2025.]")
        self.assertEqual(events(s), [])

    def test_section_label_before_verb_is_partial(self):
        # 22 U.S.C. 3901 note (printed Ex. Ord. No. 12292)
        ev = events("Executive Order No. 12163 is amended as follows: (a) Section 1–201(a)(14) is revoked.")
        self.assertEqual(ev[0]["subject"]["number"], 12163)
        self.assertIn("Section 1–201(a)(14)", ev[0]["subject_scope"])
        # an ordinary whole-order status line stays whole
        ev2 = events("Ex. Ord. No. 12438, Aug. 23, 1983, 48 F.R. 39205, which related to review of increases in rates "
                     "of basic pay, was revoked by Ex. Ord. No. 12797, Apr. 3, 1992, 57 F.R. 11411.")
        self.assertEqual(ev2[0]["subject_scope"], "")

    def test_list_subject(self):
        s = ("3.6 Revocation Executive Orders 13354 and 13355 of August 27, 2004, are revoked; and paragraphs "
             "1.3(b)(9) and (10) of Part 1 supersede provisions within Executive Order 12958.")
        self.assertEqual(sorted(e["subject"]["number"] for e in events(s)), [13354, 13355])

    def test_active_voice(self):
        ev = eo_refs.active_events("Information classified under Executive Order 12356, which superseded E.O. 12065, "
                                   "remains classified.")
        self.assertEqual([(e["subject"]["number"], actor_num(e)) for e in ev], [(12065, 12356)])
        ev2 = eo_refs.active_events("This order supersedes Executive Order 13560 of December 14, 2010.")
        self.assertTrue(ev2[0]["self_ref"])


def small_book():
    ids = ["EO:12919", "EO:11858", "EO:13456", "EO:13355", "EO:12333", "EO:13470", "EO:14205", "EO:14015",
           "EO:14148", "EO:6166", "EO:12163", "EO:13889", "EO:13935", "EO:12065", "EO:12356", "EO:11764"]
    u = eo_refs.Universe(ids, {"EO:12919": "no", "EO:12065": "no", "EO:11764": "no"})
    u.origins = {}
    book = build.Book(u)
    book.usc_currency = "test"
    meta = {"url": "https://uscode.house.gov/x.zip", "sha256": "b" * 64, "bytes": 1, "content_type": "application/zip",
            "retrieved_utc": "2026-10-17T00:00:00Z", "route": "t", "cache_path": "x.zip"}
    book.add_source("s", meta, page_or_item="zip")
    return book


def ref(n, raw=None):
    return {"number": n, "suffix": "", "raw": raw or f"Ex. Ord. No. {n}", "start": 0, "end": 0}


class Chronology(unittest.TestCase):
    base = {"citation": "50 U.S.C. 4565 note", "note_id": "n1", "note_role": "printed_eo_text_body"}

    def add(self, book, subject, actor, **extra):
        rec = dict(self.base, subject_number=subject, subject_suffix="", subject_raw=f"EO {subject}", verb="revoked",
                   actor=actor, sentence=f"Section 801 of Executive Order {subject} is revoked.", **extra)
        return book.add_event(rec, "usc", "ed", "s", "poi")

    def test_acting_order_equal_to_subject_dropped(self):
        book = small_book()
        self.assertIsNone(self.add(book, 6166, {"kind": "executive_order", "ref": ref(6166), "date": "1933-06-10"}))
        self.assertEqual(book.dropped_events["acting_order_is_the_subject"], 1)

    def test_text_inserted_by_later_amendment(self):
        # Printed EO 11858 (as amended by EO 13456) revokes a section of EO 12919.
        book = small_book()
        self_actor = {"kind": "executive_order", "ref": ref(11858), "date": "1975-05-07", "fr": None,
                      "scope_text": "the printed order itself",
                      "amenders": [{"kind": "executive_order", "ref": ref(13456), "date": "2008-01-23"}]}
        row = self.add(book, 12919, self_actor, subject_scope="Section 801 of")
        self.assertEqual(row["caution"], "text_inserted_by_later_amendment_candidate")
        self.assertEqual(row["acting_instrument_id"], "")
        self.assertEqual(row["date_candidate"], "")
        self.assertIn("13456", row["actor"])
        self.assertEqual(row["scope_candidate"], "partial_candidate")

    def test_chronology_impossible_excluded_from_fragments(self):
        book = small_book()
        row = self.add(book, 12919, {"kind": "executive_order", "ref": ref(11858), "date": "1975-05-07",
                                     "scope_text": "the printed order itself"})
        self.assertEqual(row["caution"], "chronology_impossible")
        self.assertFalse([f for f in book.fragments() if f["instrument_id"] == "EO:12919"])

    def test_as_amended_by_switches_actor(self):
        book = small_book()
        actor = {"kind": "executive_order", "ref": ref(12333), "date": "1981-12-04", "fr": "46 F.R. 59954",
                 "scope_text": "", "amended_by": {"kind": "executive_order", "ref": ref(13470), "date": "2008-07-30",
                                                  "fr": "73 F.R. 45341", "scope_text": ""}}
        row = self.add(book, 13355, actor)
        self.assertEqual(row["acting_instrument_id"], "EO:13470")
        self.assertEqual(row["date_candidate"], "2008-07-30")
        self.assertEqual(row["caution"], "actor_is_amending_order_of_named_order")
        kinds = {f["kind"] for f in book.fragments() if f["instrument_id"] == "EO:13355"}
        self.assertEqual(kinds, {"later_event_candidates", "whole_order_end_candidates"})

    def test_whole_vs_partial_fragments(self):
        book = small_book()
        self.add(book, 13889, {"kind": "executive_order", "ref": ref(13935), "date": "2020-07-09"},
                 subject_scope="Section 1(u) of")
        self.add(book, 14015, {"kind": "executive_order", "ref": ref(14148), "date": "2025-01-20"})
        frags = {(f["instrument_id"], f["kind"]): f for f in book.fragments()}
        self.assertIn(("EO:13889", "later_event_candidates"), frags)
        self.assertNotIn(("EO:13889", "whole_order_end_candidates"), frags)
        w = frags[("EO:14015", "whole_order_end_candidates")]["data"][0]
        self.assertEqual(w["date_candidate"], "2025-01-20")
        self.assertEqual(w["actor_candidate"], "President, by Ex. Ord. No. 14148")
        self.assertTrue(set(w) >= {"date_candidate", "actor_candidate", "mechanism_candidate", "source"})

    def test_bracketed_insert_is_partial(self):
        # 3 U.S.C. 301 note, printed Ex. Ord. No. 10530: "[Superseded by Ex. Ord. No. 11196, Feb. 2, 1965, ...]"
        book = small_book()
        row = self.add(book, 14015, {"kind": "executive_order", "ref": ref(14148), "date": "2025-01-20"},
                       note_role="bracketed_editorial_insert", scope_hint="")
        self.assertEqual(row["scope_candidate"], "partial_candidate")
        self.assertTrue(row["scope_hint"])
        self.assertFalse(any(f["kind"] == "whole_order_end_candidates" for f in book.fragments()))

    def test_one_fragment_per_order_and_kind(self):
        book = small_book()
        self.add(book, 14015, {"kind": "executive_order", "ref": ref(14148), "date": "2025-01-20"})
        rec = dict(self.base, subject_number=14015, subject_suffix="", subject_raw="E.O. 14015", verb="revoked",
                   actor={"kind": "executive_order", "ref": ref(14148), "date": "2025-01-20"},
                   sentence="E.O. 14015 was revoked by E.O. 14148.", citation="5 CFR 1.1")
        book.add_event(rec, "ecfr", "ed2", "s", "poi2")
        keys = [(f["instrument_id"], f["kind"]) for f in book.fragments()]
        self.assertEqual(len(keys), len(set(keys)))
        f = next(f for f in book.fragments() if f["instrument_id"] == "EO:14015" and f["kind"] == "later_event_candidates")
        self.assertEqual({d["system"] for d in f["data"]}, {"usc", "ecfr"})


class CfrTextSaysRevoked(unittest.TestCase):
    def test_revoked_order_is_not_a_predicate_lead(self):
        recs = list(ecfr_scan._emit("1-501. Executive Order No. 11764 is revoked. 1-502. Executive Order No. 12250 "
                                    "applies to this part.", {"title": "28", "part": "41", "section": "",
                                                              "citation": "28 CFR part 41, Appendix A",
                                                              "container_id": "x"}, "cfr_appendix_text_reference",
                                    events=True))
        ms = {r["eo_number"]: r for k, r in recs if k == "mention"}
        self.assertEqual(ms[11764]["caution"], "text_says_revoked_or_superseded")
        self.assertEqual(ms[12250]["caution"], "")
        evs = [r for k, r in recs if k == "event"]
        self.assertEqual([(e["subject_number"], e["verb"]) for e in evs], [(11764, "revoked")])
        book = small_book()
        book.add_mention(ms[11764], "ecfr", "govinfo_ecfr_bulk_xml", "ed", "s", "poi", "2026-10-14")
        self.assertEqual(book.mentions[0]["is_predicate_lead"], "no_caution")

    def test_which_superseded_in_cfr_text(self):
        recs = list(ecfr_scan._emit("Information classified under Executive Order 12356, which superseded E.O. 12065, "
                                    "is protected.", {"title": "41", "part": "105-53", "section": "105-53.133",
                                                      "citation": "41 CFR 105-53.133", "container_id": "x"},
                                    "cfr_text_reference", events=True))
        ms = {r["eo_number"]: r for k, r in recs if k == "mention"}
        self.assertEqual(ms[12065]["caution"], "text_says_revoked_or_superseded")
        self.assertEqual(ms[12356]["caution"], "")


HTML = b"<!DOCTYPE html><html><head><title>Unavailable</title></head><body><p>Please complete the CAPTCHA<br></body></html>"


def seed(cache, rel, data, url):
    p = pathlib.Path(cache) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    meta = {"url": url, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "content_type": "text/html",
            "retrieved_utc": "2026-10-17T00:00:00Z", "route": "t",
            "cache_path": rel}
    p.with_name(p.name + ".meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return p


class ContentChecks(unittest.TestCase):
    def test_check_content(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "x"
            p.write_bytes(HTML)
            for kind in ("zip", "xml", "json"):
                with self.assertRaises(net.WrongContent):
                    net.check_content(p, kind)
            net.check_content(p, "html")
            p.write_bytes(b'\xef\xbb\xbf<?xml version="1.0"?><ECFR/>')
            net.check_content(p, "xml")
            p.write_bytes(b'{"a": 1}')
            net.check_content(p, "json")
            z = pathlib.Path(d) / "z.zip"
            with zipfile.ZipFile(z, "w") as zf:
                zf.writestr("usc03.xml", "<x/>")
            net.check_content(z, "zip")

    def test_bad_cached_file_is_deleted_not_reused(self):
        with tempfile.TemporaryDirectory() as d:
            p = seed(d, "ecfr/govinfo/ECFR-title3.xml", HTML, "https://www.govinfo.gov/x.xml")
            f = net.Fetcher(d, offline=True)
            with self.assertRaises(net.FetchFailed):
                f.get("https://www.govinfo.gov/x.xml", "ecfr/govinfo/ECFR-title3.xml", route="t", expect="xml")
            self.assertFalse(p.exists())
            self.assertFalse(p.with_name(p.name + ".meta.json").exists())

    def test_wrong_download_not_cached(self):
        class Resp:
            def __init__(self):
                self._b = [HTML, b""]
                self.headers = {"Content-Type": "text/html"}

            def read(self, n=-1):
                return self._b.pop(0)

            def geturl(self):
                return "https://www.govinfo.gov/x.xml"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with tempfile.TemporaryDirectory() as d:
            f = net.Fetcher(d, min_interval=0)
            f._robots["www.govinfo.gov"] = None
            f.allowed = lambda url: True
            f._open = lambda url, headers=None: Resp()
            import time as _t
            sleep = _t.sleep
            _t.sleep = lambda s: None
            try:
                with self.assertRaises(net.WrongContent):
                    f.get("https://www.govinfo.gov/x.xml", "t3.xml", route="t", expect="xml")
            finally:
                _t.sleep = sleep
            self.assertFalse((pathlib.Path(d) / "t3.xml").exists())
            self.assertFalse((pathlib.Path(d) / "t3.xml.meta.json").exists())

    def test_robots_forbidden_means_disallow(self):
        with tempfile.TemporaryDirectory() as d:
            f = net.Fetcher(d)

            def boom(url, headers=None):
                raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
            f._open = boom
            self.assertFalse(f.allowed("https://blocked.example.gov/a"))

    def test_robots_unreachable_skips_host(self):
        with tempfile.TemporaryDirectory() as d:
            f = net.Fetcher(d)
            f.robots_retry_wait = 0
            calls = []

            def boom(url, headers=None):
                calls.append(url)
                raise urllib.error.HTTPError(url, 503, "Unavailable", {}, None)
            f._open = boom
            with self.assertRaises(net.FetchFailed):
                f.allowed("https://down.example.gov/a")
            self.assertEqual(len(calls), 2)  # one retry


class JobIsolation(unittest.TestCase):
    """A bad body in any parser path is a logged problem, not a crash."""

    ENV = ("JOB_USC_TITLES", "JOB_ECFR_TITLES", "USC_RELEASE_POINT", "JOB_LIMIT", "JOB_OFFLINE")

    def setUp(self):
        # job.py runs these tests inside a real run: do not inherit its settings
        self.saved_env = {k: os.environ.pop(k) for k in self.ENV if k in os.environ}
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = self.tmp.name
        u = eo_refs.Universe(["EO:12866"], {})
        u.origins = {}
        self.book = build.Book(u)
        self.book.ecfr_amddate = {}
        self.summary = {"problems": []}
        self.fetcher = net.Fetcher(self.cache, offline=True)

    def tearDown(self):
        self.tmp.cleanup()
        for k in self.ENV:
            os.environ.pop(k, None)
        os.environ.update(self.saved_env)

    def test_ecfr_paths(self):
        q = ecfr_scan.SEARCH_QUERIES[0]
        slug = "".join(c if c.isalnum() else "_" for c in q).strip("_")
        seed(self.cache, f"ecfr/search/{eo_refs.LEGAL_CUTOFF}/{slug}_p1.json", HTML, ecfr_scan.search_url(q, 1))
        seed(self.cache, "ecfr/titles.json", HTML, ecfr_scan.TITLES_URL)
        window = ecfr_scan.versions_url(1).rsplit("=", 1)[-1]
        seed(self.cache, f"ecfr/versions/title-3_since_{window}.json", HTML, ecfr_scan.versions_url(3))
        seed(self.cache, "ecfr/govinfo/ECFR-title3.xml", HTML, ecfr_scan.GOVINFO_URL.format(title=3))
        # well-formed start but broken XML: passes the content check, fails the parser
        seed(self.cache, "ecfr/govinfo/ECFR-title5.xml", b'<?xml version="1.0"?><ECFR><DIV5 N="1"><P>E.O. 12866',
             ecfr_scan.GOVINFO_URL.format(title=5))
        os.environ["JOB_ECFR_TITLES"] = "3,5"
        info = job.scan_ecfr(self.fetcher, self.book, 1, self.summary, ecfr_scan, net, eo_refs)
        del os.environ["JOB_ECFR_TITLES"]
        text = " ".join(self.summary["problems"])
        self.assertIn("eCFR search failed", text)
        self.assertIn("titles list failed", text)
        self.assertIn("versions failed for title 3", text)
        self.assertIn("GovInfo eCFR title 3 failed", text)
        self.assertIn("GovInfo eCFR title 5 failed", text)
        self.assertEqual(self.book.sources, {})  # nothing bad recorded as a source
        self.assertEqual(self.book.mentions, [])
        self.assertEqual(info["titles"], [])

    def test_usc_paths(self):
        # listing pages missing (offline) -> pinned 119-121 from the URL pattern
        name = "xml_usc03@119-121.zip"
        seed(self.cache, f"usc/119-121/{name}", HTML,
             "https://uscode.house.gov/download/releasepoints/us/pl/119/121/" + name)
        info = job.scan_usc(self.fetcher, self.book, 1, self.summary, usc_scan, net)
        self.assertEqual(info["release_point"], "119-121")
        self.assertEqual(info["checked_through_for_entries"], "2026-10-09")
        self.assertTrue(any("USC download failed" in p for p in self.summary["problems"]))
        # now a real ZIP whose member is a broken HTML page
        zpath = pathlib.Path(self.cache) / "usc/119-121" / name
        with zipfile.ZipFile(zpath, "w") as zf:
            zf.writestr("usc03.xml", HTML)
        data = zpath.read_bytes()
        seed(self.cache, f"usc/119-121/{name}", data,
             "https://uscode.house.gov/download/releasepoints/us/pl/119/121/" + name)
        self.summary["problems"] = []
        job.scan_usc(self.fetcher, self.book, 1, self.summary, usc_scan, net)
        self.assertTrue(any("could not be parsed" in p for p in self.summary["problems"]))
        self.assertFalse(any(k.startswith("usc:119-121") for k in self.book.sources))

    def test_limit_zero_processes_nothing(self):
        info = job.scan_usc(self.fetcher, self.book, 0, self.summary, usc_scan, net)
        self.assertEqual(info["titles"], [])
        self.assertFalse(any("USC download failed" in p for p in self.summary["problems"]))

    def test_member_codes(self):
        self.assertEqual(job.member_code("usc05A.xml"), "05a")
        self.assertEqual(job.member_code("uscode/usc50.xml"), "50")


if __name__ == "__main__":
    unittest.main()
