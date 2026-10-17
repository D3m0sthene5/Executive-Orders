"""Unit tests for the later-events job. Small fixtures, no network."""
import csv
import json
import re
import shutil
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import later_events as le  # noqa: E402

FIX = HERE / "fixtures"


def fixture_catalog():
    page = json.loads((FIX / "catalog_page.json").read_text("utf-8"))
    records = []
    for rec in page["results"]:
        rec = dict(rec)
        rec["_page"] = 0
        records.append(rec)
    body = (FIX / "catalog_page.json").read_bytes()
    meta = {"url": "https://www.federalregister.gov/api/v1/documents.json?fixture=1",
            "sha256": le.sha256_bytes(body), "bytes": len(body),
            "content_type": "application/json", "retrieved_utc": "2026-10-17T00:00:00Z"}
    return records, [meta]


def build(tmp, text_docs=(), decided=None, universe=None):
    records, pages = fixture_catalog()
    index, rows = le.build_index(records)
    sources = le.page_sources_from(pages, {0: [r["id"] for r in rows]})
    summary = le.build_outputs(tmp, rows, index, sources, list(text_docs),
                               universe, decided or {}, log=lambda *a: None)
    with (Path(tmp) / "EDGES.csv").open(encoding="utf-8") as fh:
        edges = list(csv.DictReader(fh))
    frags = [json.loads(x) for x in (Path(tmp) / "FRAGMENTS.jsonl").read_text("utf-8").splitlines()]
    return summary, edges, frags


def find(edges, **kw):
    return [e for e in edges if all(e.get(k) == v for k, v in kw.items())]


class References(unittest.TestCase):
    def ids(self, text):
        return [r["id"] for r in le.eo_references(text)]

    def test_list_and_suffix_forms(self):
        self.assertEqual(self.ids("Executive Orders Nos. 9001, 9002 and 9005 are revoked"),
                         ["EO:9001", "EO:9002", "EO:9005"])
        self.assertEqual(self.ids("EO 325-A, May 18, 1905"), ["EO:325A"])
        self.assertEqual(self.ids("EO 11359A"), ["EO:11359A"])
        self.assertEqual(self.ids("Executive Order No. 1182 1/2"), ["EO:1182½"])

    def test_range_expansion(self):
        self.assertEqual(self.ids("Executive Orders 9001-9004"),
                         ["EO:9001", "EO:9002", "EO:9003", "EO:9004"])
        # an implausible "range" is not expanded
        self.assertEqual(self.ids("Executive Order 9001-12000"), ["EO:9001"])

    def test_dates_attached_to_references(self):
        refs = le.eo_references("Executive Order No. 9876 of May 1, 1948, is hereby revoked")
        self.assertEqual(refs[0]["date"], "1948-05-01")

    def test_statute_numbers_are_not_orders(self):
        self.assertEqual(self.ids("Executive Order 66 Stat. 280"), [])

    def test_catalog_number_normalisation(self):
        self.assertEqual(le.normalize_catalog_number("7677-A"), "EO:7677A")
        self.assertEqual(le.normalize_catalog_number("7933-a"), "EO:7933A")
        self.assertEqual(le.normalize_catalog_number("10571", "-A Assignment of"), "EO:10571A")
        self.assertIsNone(le.normalize_catalog_number(None))


class NoteGrammar(unittest.TestCase):
    def test_label_classification(self):
        self.assertEqual(le.classify_label("Revoked by")[:2], ("revocation", "inbound"))
        self.assertEqual(le.classify_label("Revokes in part"), ("revocation", "outbound", "in part"))
        self.assertEqual(le.classify_label("Revoked in pary by")[2], "in part")
        self.assertEqual(le.classify_label("Superseded or revoked by")[0], "supersession_or_revocation")
        self.assertEqual(le.classify_label("See")[:2], ("cross_reference", "see"))
        self.assertEqual(le.classify_label("Continues certain committees established by")[1], "outbound")
        self.assertEqual(le.classify_label("Committee continued by")[1], "inbound")
        self.assertEqual(le.classify_label("Expired")[1], "status")
        self.assertEqual(le.classify_label("Effective date")[1], "metadata")

    def test_inline_labels_split(self):
        segs = le.split_note_segments("Supplements: EO 1, May 1, 1950; Revokes: EO 2, June 1, 1951")
        self.assertEqual([s[0] for s in segs], ["Supplements", "Revokes"])

    def test_mention_after_read_in_conjunction_is_not_a_target(self):
        items = le.parse_item("EO 13354, August 27, 2004, and EO 13355, August 27, 2004, "
                              "read in conjunction with EO 12333, December 4, 1981")
        self.assertEqual([i["id"] for i in items], ["EO:13354", "EO:13355"])

    def test_unnumbered_and_other_actors(self):
        self.assertEqual(le.parse_item("Executive order of June 8, 1909 (unnumbered series)")[0]["id"],
                         "UNNUMBERED_EO:1909-06-08")
        self.assertEqual(le.parse_item("Public Land Order 801, February 5, 1952 (17 FR 1357)")[0]["id"],
                         "PLO:801")
        self.assertEqual(le.parse_item("Pub. L. 94-412 (90 Stat. 1255)")[0]["id"], "PL:94-412")


class CatalogEdges(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.summary, self.edges, self.frags = build(
            self.tmp, decided={"EO:7548": "yes", "EO:7532": "no", "EO:9979": "no"},
            universe={"EO:7532", "EO:7548", "EO:9001A", "EO:7554"})

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_inbound_revocation_with_stated_date(self):
        e = find(self.edges, target_id="EO:7532", acting_id="PLO:801")
        self.assertEqual(len(e), 1)
        self.assertEqual(e[0]["mechanism"], "revocation")
        self.assertEqual(e[0]["date_candidate"], "1952-02-05")
        self.assertEqual(e[0]["evidence_type"], "ofr_note_on_target")
        self.assertEqual(e[0]["target_in_universe"], "yes")

    def test_outbound_edge_uses_acting_signing_date(self):
        e = find(self.edges, acting_id="EO:11239", target_id="EO:7548")
        self.assertEqual(e[0]["date_candidate"], "1965-07-31")
        self.assertEqual(e[0]["evidence_type"], "ofr_note_on_acting")
        part = find(self.edges, acting_id="EO:11239", target_id="EO:9001A")
        self.assertEqual(part[0]["qualifier"], "in part")

    def test_both_directions_corroborate_one_event(self):
        frag = [f for f in self.frags if f["instrument_id"] == "EO:7548" and f["kind"] == "later_event_candidates"][0]
        rev = [d for d in frag["data"] if d["actor"] == "EO:11239"][0]
        self.assertEqual(rev["evidence_types"], ["ofr_note_on_acting", "ofr_note_on_target"])
        self.assertEqual(rev["date_candidate"], "1965-07-31")
        self.assertNotIn("effective_date_candidate", rev)

    def test_note_date_conflict_prefers_catalog_and_flags(self):
        e = find(self.edges, target_id="EO:9979", acting_id="EO:9992")[0]
        self.assertEqual(e["date_candidate"], "1948-08-28")
        self.assertIn("note_states_1941-08-28", e["date_flags"])

    def test_nested_revocation(self):
        e = find(self.edges, target_id="EO:6001", acting_id="EO:6100")
        self.assertEqual(e[0]["evidence_type"], "ofr_note_nested")
        self.assertEqual(e[0]["date_candidate"], "1933-06-01")

    def test_unnumbered_targets_and_suffix_record(self):
        self.assertTrue(find(self.edges, target_id="UNNUMBERED_EO:1910-07-02", qualifier="in part"))
        self.assertTrue(find(self.edges, target_id="EO:10571A", acting_id="EO:11000", qualifier="in part"))

    def test_free_note_and_status(self):
        e = find(self.edges, target_id="EO:10210", acting_id="PL:89-554")
        self.assertEqual(e[0]["mechanism"], "authority_repeal")
        s = find(self.edges, target_id="EO:11406", mechanism="expiration")
        self.assertEqual(s[0]["date_candidate"], "1968-06-30")

    def test_post_cutoff_items_excluded(self):
        self.assertFalse(find(self.edges, acting_id="EO:14600"))
        self.assertFalse(find(self.edges, acting_id="EO:14500"))
        self.assertGreaterEqual(self.summary["edges_excluded"].get("date_after_cutoff", 0), 1)
        self.assertEqual(self.summary["catalog_records_post_cutoff_ignored"], 1)

    def test_correction_records_dropped(self):
        self.assertEqual(self.summary["catalog_records_used"], 15)

    def test_whole_order_end_only_for_full_revocation(self):
        ends = {f["instrument_id"] for f in self.frags if f["kind"] == "whole_order_end_candidates"}
        self.assertIn("EO:7548", ends)          # revoked by EO 11239 (full)
        self.assertIn("EO:7532", ends)          # revoked by Public Land Order 801 (full)
        self.assertNotIn("EO:9001A", ends)      # in part only
        self.assertNotIn("EO:10571A", ends)     # in part only
        self.assertNotIn("EO:9979", ends)       # amendment only
        self.assertNotIn("EO:12333", ends)      # only mentioned / supplemented

    def test_counterevidence_lead_for_provisional_yes(self):
        with (Path(self.tmp) / "COUNTEREVIDENCE_LEADS.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual([r["instrument_id"] for r in rows], ["EO:7548"])
        self.assertEqual(self.summary["decided_orders_with_any_candidate"], 3)

    def test_source_records_have_custody_fields(self):
        lines = (Path(self.tmp) / "SOURCES.jsonl").read_text("utf-8").splitlines()
        for line in lines:
            rec = json.loads(line)
            for key in ("source_id", "instrument_ids", "url", "sha256", "bytes", "content_type",
                        "retrieved_utc", "route", "page_or_item", "text_path", "cache_path", "notes"):
                self.assertIn(key, rec)
            self.assertTrue(rec["url"].startswith("https://"))
        for frag in self.frags:
            self.assertEqual(frag["produced_by"], "later-events")
            for src in frag["sources"]:
                self.assertEqual(set(src), {"url", "sha256", "page_or_item"})


class TextScanning(unittest.TestCase):
    def setUp(self):
        self.text = (FIX / "order_text.txt").read_text("utf-8")

    def hits(self):
        hits, located = le.scan_text(self.text, "EO:12944")
        self.assertTrue(located)
        return {(h["target"], h["mechanism"]): h for h in hits}

    def test_segment_is_limited_to_acting_order(self):
        seg, located = le.segment_for_order(self.text, "EO:12944")
        self.assertTrue(located)
        self.assertNotIn("7777", seg)
        self.assertNotIn("8888", seg)

    def test_operative_sentences(self):
        h = self.hits()
        self.assertIn(("EO:12826", "supersession"), h)
        self.assertIn(("EO:12886", "supersession"), h)
        for n in ("EO:9001", "EO:9002", "EO:9003"):
            self.assertIn((n, "revocation"), h)
        self.assertIn("range", h[("EO:9002", "revocation")]["qualifier"])
        self.assertIn(("EO:12345", "revocation"), h)
        self.assertIn(("EO:12346", "revocation"), h)

    def test_qualifiers_kept(self):
        h = self.hits()
        q = h[("EO:11111", "revocation")]["qualifier"]
        self.assertIn("Section 3", q)
        self.assertIn("insofar as", q)
        self.assertIn("body", h[("EO:12500", "abolition")]["qualifier"])

    def test_descriptive_mentions_and_self_are_ignored(self):
        h = self.hits()
        self.assertIn(("EO:10077", "amendment"), h)
        self.assertNotIn(("EO:108A", "amendment"), h)
        self.assertFalse([k for k in h if k[0] == "EO:12944"])

    def test_amending_orders_in_as_amended_lists_are_not_targets(self):
        s = ("The Manual for Courts-Martial, prescribed by Executive Order No. 11476, as amended by "
             "Executive Order Nos. 11835, 12018, and 12460 of January 24, 1984, is hereby rescinded.")
        hits = le.scan_sentence(s, "EO:12473")
        self.assertEqual([h["target"] for h in hits], ["EO:11476"])
        s2 = "The said Executive Order No. 8099 as amended by the said Executive Order No. 8461 is hereby amended accordingly."
        self.assertEqual([h["target"] for h in le.scan_sentence(s2, "EO:10122")], ["EO:8099"])

    def test_identity_and_search_page_checks(self):
        self.assertTrue(le.text_names_order("Executive Order 10557-Approving the Revised Provision", "EO:10557"))
        self.assertFalse(le.text_names_order("Executive Order 4359-A-Citizenship, Passports", "EO:4359"))
        self.assertTrue(le.url_names_order("https://www.presidency.ucsb.edu/documents/executive-order-10486-establishing-the-committee", "EO:10486"))
        self.assertFalse(le.url_names_order("https://www.presidency.ucsb.edu/documents/executive-order-4359-a-x", "EO:4359"))
        self.assertTrue(le.url_names_order("https://www.presidency.ucsb.edu/documents/executive-order-6513-j-x", "EO:6513J"))
        self.assertFalse(le.url_names_order("https://www.presidency.ucsb.edu/documents/executive-order-6543-x", "EO:6543A"))
        self.assertTrue(le.looks_like_error_page("404 Page Not Found | The American Presidency Project"))
        self.assertTrue(le.SEARCH_URL.search(
            "https://www.federalregister.gov/api/v1/documents.json?conditions%5Bterm%5D=%22Executive+Order+10104%22"))
        self.assertFalse(le.SEARCH_URL.search(
            "https://www.presidency.ucsb.edu/documents/executive-order-10557-approving-the-revised"))

    def test_text_edges_end_to_end(self):
        tmp = tempfile.mkdtemp()
        try:
            doc = {"acting_id": "EO:12944", "text": self.text, "evidence_type": "order_text_test",
                   "source": {"source_id": "t1", "url": "https://www.govinfo.gov/x.pdf",
                              "sha256": "0" * 64, "bytes": 10, "content_type": "application/pdf",
                              "retrieved_utc": "2026-10-17T00:00:00Z", "route": "test",
                              "page_or_item": "whole PDF", "cache_path": None}}
            summary, edges, frags = build(tmp, text_docs=[doc])
            e = find(edges, acting_id="EO:12944", target_id="EO:12826")
            self.assertEqual(e[0]["evidence_type"], "order_text_test")
            self.assertEqual(e[0]["date_basis"], "no date in data")   # 12944 not in the fixture catalog
            ends = {f["instrument_id"] for f in frags if f["kind"] == "whole_order_end_candidates"}
            # text evidence alone is never offered as a whole-order end
            self.assertNotIn("EO:12345", ends)
            self.assertNotIn("EO:11111", ends)
            self.assertNotIn("EO:9002", ends)
            ev = [d for f in frags if f["instrument_id"] == "EO:12345" and f["kind"] == "later_event_candidates"
                  for d in f["data"] if d["mechanism"] == "revocation"][0]
            self.assertIn("text_only_unverified", ev["flags"])
            self.assertEqual(summary["full_end_items_withheld_from_whole_order_end"].get(
                "withheld_text_only_unverified"), 3)          # 12345, 12346 and 9001
        finally:
            shutil.rmtree(tmp)


def record(number, signing, notes):
    return {"executive_order_number": number, "signing_date": signing, "publication_date": signing,
            "citation": None, "document_number": None, "title": "Test order",
            "president": {"name": "Test"}, "disposition_notes": notes, "_page": 0}


def build_records(tmp, records, text_docs=(), decided=None):
    meta = {"url": "https://www.federalregister.gov/api/v1/documents.json?fixture=2",
            "sha256": "a" * 64, "bytes": 1, "content_type": "application/json",
            "retrieved_utc": "2026-10-17T00:00:00Z"}
    index, rows = le.build_index(records)
    sources = le.page_sources_from([meta], {0: [r["id"] for r in rows]})
    summary = le.build_outputs(tmp, rows, index, sources, list(text_docs), None, decided or {},
                               log=lambda *a: None)
    with (Path(tmp) / "EDGES.csv").open(encoding="utf-8") as fh:
        edges = list(csv.DictReader(fh))
    with (Path(tmp) / "UNPARSED_NOTE_SEGMENTS.csv").open(encoding="utf-8") as fh:
        unparsed = list(csv.DictReader(fh))
    frags = [json.loads(x) for x in (Path(tmp) / "FRAGMENTS.jsonl").read_text("utf-8").splitlines()]
    return summary, edges, frags, unparsed


class NoteLinesWithoutColons(unittest.TestCase):
    """Review fix: every note line is parsed on its own; unlabelled lines are not lost."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        recs = [
            record("11903", "1976-02-02", "Amends: EO 11808, September 30, 1974\nRevoked by EO 11975, March 7, 1977"),
            record("11975", "1977-03-07", ""),
            record("11010", "1962-03-19", "Amends: EO 10713, June 5, 1957\n"
                                          "Nullified by treaty with Japan on May 15, 1972 (TIAS 7314, 23 UST 446)\n"
                                          "See: EO 11263, December 20, 1965"),
            record("11210", "1965-03-15", "Amended by: EO 11347, April 20, 1967\n"
                                          "Commission ceased to function on November 15, 1969 from lack of "
                                          "funds--order was never formally revoked"),
            record("11179", "1964-09-22", "Amended by: EO 11200, February 26, 1965\n"
                                          "Superseded or revoked by EO 12919, June 3, 1994"),
            record("11175", "1964-09-10", "Amended by: EO 11198, February 10, 1965\n"
                                          "Authority repealed by Pub. L. 94-455 (90 Stat. 1814, 26 U.S.C. 4911 nt.)"),
            record("11126", "1963-11-01", "Amended by: EO 11221, May 6, 1965\n"
                                          "Council terminated by EO 12007, August 22, 1977\n"
                                          "Commission to terminate by July 29, 1968"),
            record("13635", "2012-12-27", "Supersedes: Superseded by EO 13641, April 5, 2013"),
        ]
        self.summary, self.edges, self.frags, self.unparsed = build_records(self.tmp, recs)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_second_line_revocation_is_kept(self):
        e = find(self.edges, acting_id="EO:11975", target_id="EO:11903")
        self.assertEqual([x["mechanism"] for x in e], ["revocation"])
        self.assertEqual(e[0]["date_candidate"], "1977-03-07")
        self.assertEqual(e[0]["qualifier"], "")
        ends = {f["instrument_id"] for f in self.frags if f["kind"] == "whole_order_end_candidates"}
        self.assertIn("EO:11903", ends)
        # and the first line still works
        self.assertTrue(find(self.edges, acting_id="EO:11903", target_id="EO:11808", mechanism="amendment"))

    def test_other_unlabelled_forms(self):
        t = find(self.edges, target_id="EO:11010", mechanism="nullification")
        self.assertEqual(t[0]["acting_id"], "TREATY:1972-05-15")
        c = find(self.edges, target_id="EO:11210", mechanism="ceased_to_function")
        self.assertEqual(c[0]["date_candidate"], "1969-11-15")
        self.assertIn("commission", c[0]["qualifier"])
        self.assertTrue(find(self.edges, acting_id="EO:12919", target_id="EO:11179",
                             mechanism="supersession_or_revocation"))
        self.assertTrue(find(self.edges, acting_id="PL:94-455", target_id="EO:11175", mechanism="authority_repeal"))
        term = find(self.edges, acting_id="EO:12007", target_id="EO:11126", mechanism="termination")
        self.assertIn("council", term[0]["qualifier"])
        # "Supersedes: Superseded by EO 13641" is read as inbound
        self.assertTrue(find(self.edges, acting_id="EO:13641", target_id="EO:13635", evidence_type="ofr_note_on_target"))

    def test_lines_not_understood_go_to_unparsed(self):
        segs = [u["segment"] for u in self.unparsed]
        self.assertIn("Commission to terminate by July 29, 1968", segs)
        # nothing glued onto the previous line's list
        self.assertFalse(find(self.edges, target_id="EO:11126", acting_id="EO:11221", mechanism="termination"))
        self.assertFalse([e for e in self.edges if "Commission to terminate" in e["quote"]])

    def test_note_quotes_are_verbatim(self):
        for e in self.edges:
            self.assertIn(e["quote_kind"], ("verbatim_note_item", "verbatim_note_segment"))
        e = find(self.edges, acting_id="EO:11975", target_id="EO:11903")[0]
        self.assertEqual(e["quote"], "Revoked by EO 11975, March 7, 1977")


class PartialEvidenceConflicts(unittest.TestCase):
    def test_full_and_partial_for_same_actor_is_withheld(self):
        tmp = tempfile.mkdtemp()
        try:
            recs = [record("10480", "1953-08-14", "Revoked by: EO 10773, July 1, 1958 (in part)"),
                    record("10773", "1958-07-01", "Revokes: EO 10480, August 14, 1953")]
            summary, edges, frags, _ = build_records(tmp, recs)
            ends = {f["instrument_id"] for f in frags if f["kind"] == "whole_order_end_candidates"}
            self.assertNotIn("EO:10480", ends)
            ev = [d for f in frags if f["kind"] == "later_event_candidates" for d in f["data"]
                  if d["actor"] == "EO:10773" and d["qualifier"] == ""][0]
            self.assertIn("full_and_partial_evidence_conflict", ev["flags"])
            self.assertTrue(ev["conflicting_edge_ids"])
        finally:
            shutil.rmtree(tmp)

    def test_whole_end_items_carry_dates_flags_edges_and_only_their_sources(self):
        tmp = tempfile.mkdtemp()
        try:
            recs = [record("9979", "1948-08-28", "Amended by: EO 9992, August 28, 1948\nRevoked by: EO 10000, Sept 1, 1948"),
                    record("9992", "1948-08-28", ""), record("10000", "1948-09-01", "")]
            _, edges, frags, _ = build_records(tmp, recs)
            end = [f for f in frags if f["kind"] == "whole_order_end_candidates"][0]
            item = end["data"][0]
            for key in ("date_candidate", "date_basis", "flags", "edge_ids", "stated_effective_date_candidates"):
                self.assertIn(key, item)
            self.assertEqual(len(end["sources"]), 1)
            self.assertEqual(item["all_source_positions"], [0])
            self.assertEqual(end["sources"][0], item["source"])
        finally:
            shutil.rmtree(tmp)


class SentenceProbes(unittest.TestCase):
    """Review fix: partial wording, clause boundaries, negation, compound verbs."""

    def hits(self, sentence, acting="EO:20000"):
        return {(h["target"], h["mechanism"]): h for h in le.scan_sentence(sentence, acting)}

    def test_paragraphs_of_the_said_order_are_partial(self):
        h = self.hits("Paragraph 6 of the said Executive Order No. 8840 and paragraphs 3, 6, and 8 of the said "
                      "Executive Order No. 9182 are revoked.")
        self.assertIn("Paragraph 6", h[("EO:8840", "revocation")]["qualifier"])
        self.assertIn("paragraphs 3, 6, and 8", h[("EO:9182", "revocation")]["qualifier"])
        self.assertTrue(le.is_partial(h[("EO:9182", "revocation")]["qualifier"]))

    def test_section_tokens_with_letters(self):
        h = self.hits("Sections 5 (b), 7, and 8 of Executive Order No. 11075 of January 15, 1963, are hereby revoked.")
        self.assertIn("Sections 5 (b), 7, and 8", h[("EO:11075", "revocation")]["qualifier"])
        h = self.hits("Subsections (a) and (c) of section 3 of Executive Order No. 10096 are hereby revoked.")
        self.assertIn("Subsections (a) and (c) of section 3", h[("EO:10096", "revocation")]["qualifier"])

    def test_provisions_contained_in_are_partial_for_the_whole_list(self):
        h = self.hits("The prohibitions contained in Executive Order 12205 of April 7, 1980, and Executive Order "
                      "12211 of April 17, 1980, are hereby revoked.")
        for t in ("EO:12205", "EO:12211"):
            self.assertTrue(le.is_partial(h[(t, "revocation")]["qualifier"]), t)

    def test_revoked_or_amended_list_is_not_a_revocation(self):
        h = self.hits("The following Executive orders are revoked or amended: (1) Executive Order 12884 of "
                      "December 1, 1993, is amended by deleting section 2.")
        self.assertNotIn(("EO:12884", "revocation"), h)
        self.assertIn(("EO:12884", "amendment"), h)

    def test_subject_does_not_cross_and_after_another_verb(self):
        h = self.hits("Executive Order 13000 is amended, and Executive Order 13001 is revoked.")
        self.assertIn(("EO:13000", "amendment"), h)
        self.assertNotIn(("EO:13000", "revocation"), h)
        self.assertIn(("EO:13001", "revocation"), h)

    def test_negation_guard(self):
        self.assertEqual(self.hits("Executive Order 12866 is not hereby revoked."), {})
        self.assertEqual(self.hits("Executive Order 13000 shall not be revoked."), {})
        self.assertEqual(self.hits("Nothing in this order shall be construed to mean that Executive Order "
                                   "13000 is revoked."), {})

    def test_amending_orders_after_parenthetical_titles(self):
        s = ("Executive Order 8809 of June 28, 1941 (Good Conduct Medal), as amended by Executive Order 9323 of "
             "March 31, 1943 (Amendment of Executive Order No. 8809 of June 28, 1941, Establishing the Good "
             "Conduct Medal), and Executive Order 10444 of April 10, 1953 (Amendment of Executive Order No. 8809 "
             "of June 28, 1941, Establishing the Good Conduct Medal, As Amended by Executive Order No. 9323 of "
             "March 31, 1943), is further amended- (a) by striking \"men\".")
        self.assertEqual(sorted(t for t, m in self.hits(s, "EO:14085")), ["EO:8809"])
        plural = ("Executive Order 13001 of May 1, 1996 (Title One), as amended by Executive Order 13002 of May 2, "
                  "1996 (Title Two), and Executive Order 13003 of May 3, 1996 (Title Three), are hereby revoked.")
        self.assertEqual(sorted(t for t, m in self.hits(plural)), ["EO:13001", "EO:13003"])

    def test_stated_effective_date_is_kept_separately(self):
        h = self.hits("Executive Order No. 9876 of May 1, 1948, is hereby revoked effective April 3, 1975.")
        self.assertEqual(h[("EO:9876", "revocation")]["stated_effective_date"], "1975-04-03")

    def test_suffix_variant_of_own_number_from_title_is_ignored(self):
        s = ("Executive Order 4359-A-Citizenship, Passports and Protection | The American Presidency Project "
             "Skip to main content Documents Categories Presidential Eulogies Executive Orders Fireside Chats "
             "Interviews Letters and many more navigation words here, and Executive Order No. 1234 is hereby revoked.")
        targets = {t for t, m in self.hits(s, "EO:4359")}
        self.assertNotIn("EO:4359A", targets)
        self.assertIn("EO:1234", targets)


class TextCustody(unittest.TestCase):
    def test_text_quotes_are_verbatim_with_spans(self):
        text = ("Executive Order 20000 of May 1, 1990\nSec. 1. Executive Order No. 9001 is here-\nby­ "
                "revoked—in full.\nSec. 2. Other text.")
        hits, located = le.scan_text(text, "EO:20000")
        self.assertTrue(located)
        h = hits[0]
        self.assertEqual(h["target"], "EO:9001")
        flat = re.sub(r"\s+", " ", text)
        self.assertIn(h["quote"], flat)
        a, b = map(int, re.match(r"chars (\d+)-(\d+)", h["quote_span"]).groups())
        self.assertEqual(re.sub(r"\s+", " ", text[a:b]).strip(), h["quote"])

    def test_app_page_body_is_cut_from_navigation_and_footer(self):
        page = ("\n\nExecutive Order 9001—Title | The American Presidency Project\n\nSkip to main content\n"
                + "Navigation Executive Order 7777 is hereby revoked.\n" * 3
                + "Franklin D. Roosevelt\n32nd\nPresident of the United States:\n1933 - 1945\n"
                "Executive Order 9001—Title\nDecember 27, 1941\n\nExecutive Order No. 8000 is hereby revoked.\n\n"
                "FRANKLIN D ROOSEVELT\n\nFranklin D. Roosevelt, Executive Order 9001—Title Online by Gerhard "
                "Peters and John T. Woolley, The American Presidency Project https://www.presidency.ucsb.edu/node/1\n"
                "Executive Order 6666 is hereby revoked.\n")
        d = le.scan_text_detail(page, "EO:9001")
        self.assertTrue(d["app_body_cut"])
        self.assertTrue(d["located"])
        self.assertEqual([h["target"] for h in d["hits"]], ["EO:8000"])

    def test_error_and_block_pages(self):
        body = " The Secretary shall act. " * 20
        self.assertFalse(le.looks_like_error_page("Executive Order 11404—Providing for the Restoration "
                                                  "of Law and Order in the State of Illinois" + body))
        self.assertFalse(le.looks_like_error_page("Executive Order 10404 of 1952" + body))
        self.assertTrue(le.looks_like_error_page("Access blocked. Your IP address has been blocked because of "
                                                 "unusual activity. Executive Order 10557" + body))
        self.assertTrue(le.looks_like_error_page("Please complete the CAPTCHA to continue." + body))
        self.assertTrue(le.looks_like_error_page('{"errors": ["not found"], "status": 404}' + body))
        self.assertTrue(le.looks_like_error_page("404 Page Not Found | The American Presidency Project" + body))

    def test_byte_counts_and_unique_source_ids(self):
        self.assertEqual(le.int_or_none("4495"), 4495)
        self.assertEqual(le.int_or_none(4495), 4495)
        self.assertIsNone(le.int_or_none(None))
        self.assertIsNone(le.int_or_none("n/a"))
        tmp = tempfile.mkdtemp()
        try:
            docs = []
            for shard in ("S11_A_INST", "S11_D_REPEAL_X1"):
                docs.append({"acting_id": "EO:20000", "evidence_type": "order_text_opus_mirror",
                             "text": "Executive Order 20000\nExecutive Order No. 9001 is hereby revoked.",
                             "source": {"source_id": "opus:X/%s/cache/app_eo20000.txt" % shard,
                                        "url": "https://www.presidency.ucsb.edu/documents/%s" % shard,
                                        "sha256": "b" * 64, "bytes": le.int_or_none("12"),
                                        "route": "test", "page_or_item": "x"}})
            build_records(tmp, [record("9001", "1941-12-27", "")], text_docs=docs)
            recs = [json.loads(x) for x in (Path(tmp) / "SOURCES.jsonl").read_text("utf-8").splitlines()]
            ids = [r["source_id"] for r in recs]
            self.assertEqual(len(ids), len(set(ids)))
            for r in recs:
                self.assertTrue(r["bytes"] is None or isinstance(r["bytes"], int))
        finally:
            shutil.rmtree(tmp)


class Fetching(unittest.TestCase):
    def test_cache_is_reused_without_network(self):
        tmp = tempfile.mkdtemp()
        try:
            url = le.api_first_url(1000)
            f = le.Fetcher(tmp)
            key = le.hashlib.sha1(url.encode("utf-8")).hexdigest()
            body = json.dumps({"count": 1, "results": [{"executive_order_number": "1"}]}).encode()
            d = Path(tmp) / "ofr_api"
            d.mkdir()
            (d / (key + ".json")).write_bytes(body)
            (d / (key + ".meta.json")).write_text(json.dumps({"url": url, "sha256": le.sha256_bytes(body),
                                                              "bytes": len(body)}), "utf-8")
            original = urllib.request.urlopen
            urllib.request.urlopen = lambda *a, **k: (_ for _ in ()).throw(AssertionError("network used"))
            try:
                got, meta = f.get(url, le.API_HOSTS)
            finally:
                urllib.request.urlopen = original
            self.assertEqual(got, body)
            self.assertEqual(f.requests_made, 0)
            self.assertEqual(f.cache_hits, 1)
        finally:
            shutil.rmtree(tmp)

    def test_refuses_other_hosts(self):
        with self.assertRaises(ValueError):
            le.Fetcher(tempfile.gettempdir()).get("https://example.com/x.json", le.API_HOSTS)

    def test_pagination_and_completeness_check(self):
        pages = [
            {"count": 3, "results": [{"executive_order_number": "1"}, {"executive_order_number": "2"}],
             "next_page_url": "https://www.federalregister.gov/api/v1/documents?page=2"},
            {"count": 3, "results": [{"executive_order_number": "3"}], "next_page_url": None},
        ]

        class Fake:
            def __init__(self):
                self.calls = 0

            def get(self, url, hosts):
                body = json.dumps(pages[self.calls]).encode()
                self.calls += 1
                return body, {"url": url, "sha256": le.sha256_bytes(body), "bytes": len(body)}

        old = le.MIN_FULL_CATALOG
        le.MIN_FULL_CATALOG = 3
        try:
            records, metas = le.fetch_catalog(Fake(), log=lambda *a: None)
        finally:
            le.MIN_FULL_CATALOG = old
        self.assertEqual(len(records), 3)
        self.assertEqual([r["_page"] for r in records], [0, 0, 1])
        with self.assertRaises(ValueError):           # below the full-catalog floor
            le.fetch_catalog(Fake(), log=lambda *a: None)


if __name__ == "__main__":
    unittest.main()
