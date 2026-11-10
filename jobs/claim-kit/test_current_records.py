"""F3 (Accursius, 2026-11-10): held U.S. Code note and CFR section extracts become exact CURRENT spans.

Leads stay leads: these tests check only that an exact, hash-pinned, uniquely located slice of an
attributed .txt extract is delivered, and that every other case keeps its evidence_gap.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import current_evidence as C
import inputs

ZIP_URL = "https://uscode.house.gov/download/releasepoints/us/pl/119/121/xml_uscAll@119-121.zip"
ZIP_SHA = "c" * 64
POI = ("5 U.S.C. 5941 note; note 'Ex. Ord. No. 10000. Regulations' [USLM note id n1]; "
       "usc05.xml (sha256 " + "d" * 64 + ") in xml_uscAll@119-121.zip")
OTHER_POI = POI.replace("n1", "n2")
NOTE = ("Ex. Ord. No. 10000. Regulations\nEx. Ord. No. 10000, Sept. 16, 1948, 13 F.R. 5453, provided:\n"
        "Section 1. The allowances continue.\n")
BULK_URL = "https://www.govinfo.gov/bulkdata/ECFR/title-10/ECFR-title10.xml"
BULK_SHA = "b" * 64
CFR = ("§ 10.1\nPurpose.\n(a) This part establishes the criteria under Executive Order 10865, as amended,\n"
       "and Executive Order 12968.\n[51 FR 35999, Oct. 8, 1986]\n")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class CurrentRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.cl = self.repo / "jobs/current-law/output"
        self.th = self.repo / "jobs/theophilus-sources/output"
        (self.cl / "usc-notes").mkdir(parents=True)
        (self.th / "texts").mkdir(parents=True)
        (self.cl / "usc-notes/n1.txt").write_bytes(NOTE.encode())
        (self.th / "texts/cfr-t10-10.1.txt").write_bytes(CFR.encode())
        # As usc_extracts.Extracts.write declares it: own identity is the extract, the ZIP is extracted_from.
        self.note_decl = {"source_id": "usc:x:note:n1", "instrument_ids": [], "url": ZIP_URL, "sha256": sha(NOTE.encode()),
                          "extracted_from": {"url": ZIP_URL, "sha256": ZIP_SHA},
                          "route": "usc_release_point_xml_zip_text_extract", "page_or_item": POI,
                          "text_path": "usc-notes/n1.txt", "text_sha256": sha(NOTE.encode()),
                          "item_extract": "page_or_item", "citation": "5 U.S.C. 5941 note"}
        self.cfr_decl = {"source_id": "cfr:t10:10.1", "instrument_ids": [], "mentioned_instrument_ids": ["EO:10865"],
                         "url": "https://www.ecfr.gov/on/2026-11-05/title-10/section-10.1", "sha256": sha(CFR.encode()),
                         "page_or_item": "10 CFR 10.1", "text_path": "texts/cfr-t10-10.1.txt",
                         "cache_path": "texts/cfr-t10-10.1.txt", "citation": "10 CFR 10.1", "item_extract": "citation",
                         "extracted_from": {"url": BULK_URL, "sha256": BULK_SHA}}
        self.manifests()

    def manifests(self, note=None, cfr=None):
        zip_row = {"source_id": "usc:zip", "url": ZIP_URL, "sha256": ZIP_SHA, "text_path": "USC_EO_NOTES.jsonl",
                   "cache_path": "usc/119-121/xml_uscAll@119-121.zip", "page_or_item": "xml_uscAll@119-121.zip (all)"}
        (self.cl / "SOURCES.jsonl").write_text(json.dumps(zip_row) + "\n" + json.dumps(note or self.note_decl) + "\n")
        (self.th / "SOURCES.jsonl").write_text(json.dumps(cfr or self.cfr_decl) + "\n")

    def note_lead(self, **changes):
        lead = {"system": "usc", "basis_code": "printed_eo_text", "where": "USC 5 U.S.C. 5941 note",
                "snippet": "Ex. Ord. No. 10000. Regulations | Ex. Ord. No. 10000, Sept. 16, 1948, 13 F.R. 5453, provided:",
                "source": {"url": ZIP_URL, "sha256": ZIP_SHA, "page_or_item": POI}}
        lead.update(changes)
        return lead

    def cfr_lead(self, **changes):
        lead = {"system": "ecfr", "basis_code": "cfr_text_reference", "where": "CFR 10 CFR 10.1",
                "snippet": "...criteria under Executive Order 10865, as amended, and Executive Order 12968. [51 FR 35999...",
                "source": {"url": BULK_URL, "sha256": BULK_SHA, "page_or_item": "10 CFR 10.1 (section_text; NODE 10:1)"}}
        lead.update(changes)
        return lead

    def enrich(self, lead):
        original = copy.deepcopy(lead)
        row, = C.enrich_current(self.repo, [lead])
        self.assertEqual(lead, original)
        return row

    def assert_span(self, row, held):
        self.assertNotIn("evidence_gap", row)
        self.assertEqual(held[row["char_start"]:row["char_end"]], row["text"])
        self.assertEqual(row["source"]["text_sha256"], sha(held.encode()))

    def assert_gap(self, row):
        self.assertIn("evidence_gap", row)
        for key in ("text", "char_start", "char_end", "held_extract"):
            self.assertNotIn(key, row)

    def test_note_extract_declared_under_release_zip_gives_exact_span(self):
        row = self.enrich(self.note_lead())
        self.assert_span(row, NOTE)
        self.assertEqual(row["text"], NOTE[:NOTE.index("provided:") + len("provided:")])
        self.assertEqual(row["source"]["text_path"], "jobs/current-law/output/usc-notes/n1.txt")
        self.assertEqual((row["source"]["url"], row["source"]["sha256"]), (ZIP_URL, ZIP_SHA))
        self.assertEqual(row["held_extract"]["source_id"], "usc:x:note:n1")

    def producer_lead(self, **changes):
        """A lead exactly as usc_extracts.attach writes it: text_path and text_sha256 on the entry."""
        return self.note_lead(text_path="usc-notes/n1.txt", text_sha256=sha(NOTE.encode()), **changes)

    def test_producer_lead_resolves_through_its_declaration(self):
        row = self.enrich(self.producer_lead())
        self.assert_span(row, NOTE)
        self.assertEqual(row["held_extract"]["source_id"], "usc:x:note:n1")

    def test_scenario_a_changed_bytes_without_declaration_are_refused(self):
        (self.cl / "usc-notes/n1.txt").write_bytes((NOTE + "appended line\n").encode())
        self.manifests(note={"source_id": "unrelated", "url": "https://example.gov/x", "sha256": "a" * 64})
        self.assert_gap(self.enrich(self.producer_lead()))
        # Even unchanged bytes in an item-extract folder are not citable without a declaration.
        (self.cl / "usc-notes/n1.txt").write_bytes(NOTE.encode())
        self.assert_gap(self.enrich(self.producer_lead()))

    def test_scenario_a_entry_level_pin_is_enforced(self):
        (self.cl / "usc-notes/n1.txt").write_bytes((NOTE + "appended line\n").encode())
        self.manifests(note=dict(self.note_decl, sha256=sha((NOTE + "appended line\n").encode()),
                                 text_sha256=sha((NOTE + "appended line\n").encode())))
        row = self.enrich(self.producer_lead())  # entry still pins the old bytes
        self.assert_gap(row)
        self.assertIn("text_sha256 the lead carries", row["evidence_gap"])

    def test_scenario_b_direct_pointer_to_another_items_extract_is_refused(self):
        other = self.producer_lead(source={"url": ZIP_URL, "sha256": ZIP_SHA, "page_or_item": OTHER_POI})
        self.assert_gap(self.enrich(other))  # n1 is declared for POI, not OTHER_POI
        (self.cl / "usc-notes/n1.txt").write_bytes((NOTE + "x").encode())
        unpinned = copy.deepcopy(other)
        unpinned.pop("text_sha256")
        self.assert_gap(self.enrich(unpinned))

    def test_scenario_c_section_extract_failing_or_missing_declaration_is_refused(self):
        sec_poi = "5 U.S.C. 5941; usc05.xml (sha256 " + "d" * 64 + ") in xml_uscAll@119-121.zip"
        (self.cl / "usc-sections").mkdir()
        body = "Section text naming Executive Order 10000 in the statute.\n"
        (self.cl / "usc-sections/s-1.txt").write_bytes(body.encode())
        lead = self.note_lead(basis_code="statutory_text_reference", where="USC 5 U.S.C. 5941",
                              snippet="naming Executive Order 10000 in the statute", text_path="usc-sections/s-1.txt",
                              source={"url": ZIP_URL, "sha256": ZIP_SHA, "page_or_item": sec_poi})
        declared = dict(self.note_decl, source_id="usc:x:section:s", page_or_item=sec_poi,
                        text_path="usc-sections/s-1.txt", sha256="f" * 64, text_sha256="f" * 64)
        self.manifests(note=declared)
        self.assert_gap(self.enrich(lead))  # declaration pin fails
        self.manifests(note={"source_id": "unrelated", "url": "https://example.gov/x", "sha256": "a" * 64})
        self.assert_gap(self.enrich(lead))  # declaration dropped, stale pointer left: still refused
        good = dict(declared, sha256=sha(body.encode()), text_sha256=sha(body.encode()))
        self.manifests(note=good)
        self.assert_span(self.enrich(lead), body)

    def test_both_locate_copies_are_identical(self):
        producer = Path(__file__).resolve().parents[1] / "current-law/usc_extracts.py"
        if not producer.is_file():
            self.skipTest("current-law code not checked out")

        def block(path):
            text = path.read_text(encoding="utf-8")
            start = text.index("# --- locate: identical copy")
            return text[start:text.index("# --- end of locate copy", start)]
        self.assertEqual(block(producer), block(Path(C.__file__)))

    def test_locate_collapses_whitespace_without_deleting_it(self):
        self.assertIsNone(C.locate("Ex. Ord. No. 1234 5 U.S.C. 301 applies", "Ex. Ord. No. 12345 U.S.C. 301"))
        text = "Executive Order 12345 is revoked. Later text. Executive Order 12345\nis revoked."
        self.assertIsNone(C.locate(text, "Executive Order 12345 is revoked."))
        start, end = C.locate("Heading words here\nStatus line, provided:\nBody", "Heading words here | Status line, provided:")
        self.assertEqual((start, end), (0, len("Heading words here\nStatus line, provided:")))

    def test_producer_span_with_direct_pin_is_kept(self):
        start = NOTE.index("Section 1.")
        lead = self.note_lead(text_path="usc-notes/n1.txt", text="Section 1. The allowances continue.",
                              char_start=start, char_end=start + 35)
        lead["source"]["text_sha256"] = sha(NOTE.encode())
        row = self.enrich(lead)
        self.assert_span(row, NOTE)
        self.assertEqual(row["char_start"], start)

    def test_note_extract_never_serves_another_note_of_the_same_zip(self):
        self.assert_gap(self.enrich(self.note_lead(source={"url": ZIP_URL, "sha256": ZIP_SHA, "page_or_item": OTHER_POI})))

    def test_changed_note_bytes_are_refused(self):
        (self.cl / "usc-notes/n1.txt").write_bytes((NOTE + "edited\n").encode())
        self.assert_gap(self.enrich(self.note_lead()))

    def test_serialized_or_tabular_extracts_are_never_legal_text(self):
        for name in ("n1.jsonl", "n1.json", "n1.csv"):
            with self.subTest(name=name):
                (self.cl / "usc-notes" / name).write_bytes(NOTE.encode())
                self.manifests(note=dict(self.note_decl, text_path="usc-notes/" + name))
                self.assert_gap(self.enrich(self.note_lead()))

    def test_lfs_pointer_extract_is_refused(self):
        pointer = b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"a" * 64 + b"\nsize 9\n"
        (self.cl / "usc-notes/n1.txt").write_bytes(pointer)
        self.manifests(note=dict(self.note_decl, text_sha256=sha(pointer)))
        self.assert_gap(self.enrich(self.note_lead(snippet="version https://git-lfs.github.com/spec/v1")))

    def test_theophilus_cfr_section_resolves_by_origin_and_citation(self):
        row = self.enrich(self.cfr_lead())
        self.assert_span(row, CFR)
        self.assertTrue(row["text"].startswith("criteria under Executive Order 10865, as amended,\nand"))
        self.assertEqual(row["source"]["text_path"], "jobs/theophilus-sources/output/texts/cfr-t10-10.1.txt")
        self.assertEqual((row["source"]["url"], row["source"]["sha256"]), (BULK_URL, BULK_SHA))
        self.assertEqual(row["held_extract"]["manifest"], "jobs/theophilus-sources/output/SOURCES.jsonl")

    def test_theophilus_section_needs_same_origin_bytes_citation_and_pin(self):
        for name, lead in [("other bulk sha", self.cfr_lead(source={"url": BULK_URL, "sha256": "e" * 64})),
                           ("other section", self.cfr_lead(where="CFR 10 CFR 10.2")),
                           ("snippet absent", self.cfr_lead(snippet="Executive Order 99999 is continued in force here."))]:
            with self.subTest(name):
                self.assert_gap(self.enrich(lead))
        (self.th / "texts/cfr-t10-10.1.txt").write_bytes((CFR + "x").encode())
        self.assert_gap(self.enrich(self.cfr_lead()))

    def test_ellipsis_is_stripped_only_for_a_unique_quote(self):
        twice = CFR + "criteria under Executive Order 10865, as amended,\nand Executive Order 12968.\n"
        (self.th / "texts/cfr-t10-10.1.txt").write_bytes(twice.encode())
        self.manifests(cfr=dict(self.cfr_decl, sha256=sha(twice.encode())))
        self.assert_gap(self.enrich(self.cfr_lead(snippet="...criteria under Executive Order 10865, as amended, and Executive Order 12968...")))

    def test_whole_artifact_declarations_keep_legacy_matching(self):
        (self.cl / "legal.txt").write_text("Whole artifact text naming Executive Order 1.\n")
        self.manifests(note={"url": "https://example.gov/a", "sha256": "a" * 64, "text_path": "legal.txt"})
        row = self.enrich({"snippet": "naming Executive Order 1", "source": {"url": "https://example.gov/a",
                                                                         "sha256": "a" * 64, "page_or_item": "p. 3"}})
        self.assertNotIn("evidence_gap", row)

    def test_section_declared_by_identity_is_not_a_text_of_the_citing_order(self):
        universe = {"EO:10865": {"id": "EO:10865"}, "EO:12333": {"id": "EO:12333"}}
        warnings = []
        collector = inputs._Collector(self.repo, universe, warnings)
        collector.walk_texts(self.cfr_decl, self.th, "jobs/theophilus-sources/output/SOURCES.jsonl")
        self.assertEqual(collector.texts, [])
        legacy = {k: v for k, v in self.cfr_decl.items() if k not in ("mentioned_instrument_ids", "item_extract",
                                                                     "extracted_from", "citation")}
        legacy["instrument_ids"] = ["EO:10865"]
        collector.walk_texts(legacy, self.th, "jobs/theophilus-sources/output/SOURCES.jsonl")
        self.assertEqual([t["instrument_id"] for t in collector.texts], ["EO:10865"])  # the old declaration's defect


if __name__ == "__main__":
    unittest.main()
