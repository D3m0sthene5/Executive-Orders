import hashlib
import json
import pathlib
import tempfile
import unittest

import build
import usc_extracts as X
from tests.test_build_and_net import FIX, make_book
import usc_scan

ZIP = {"source_id": "usc:119-121:xml_uscAll@119-121.zip", "instrument_ids": ["EO:1"],
       "url": "https://uscode.house.gov/download/releasepoints/us/pl/119/121/xml_uscAll@119-121.zip",
       "sha256": "c" * 64, "bytes": 99, "content_type": "application/zip", "retrieved_utc": "2026-11-06T00:00:00Z",
       "route": "usc_release_point_xml_zip", "page_or_item": "xml_uscAll@119-121.zip (all)",
       "text_path": "USC_EO_NOTES.jsonl", "cache_path": "usc/x.zip", "notes": ""}
POI = ("5 U.S.C. 5941 note; note 'Ex. Ord. No. 10000. Regulations' [USLM note id id27f6]; "
       "usc05.xml (sha256 " + "d" * 64 + ") in xml_uscAll@119-121.zip")
NOTE_TEXT = ("Ex. Ord. No. 10000. Regulations\n"
             "Ex. Ord. No. 10000, Sept. 16, 1948, 13 F.R. 5453, as amended by Ex. Ord. No. 10636, Sept. 16, 1955,\n"
             "20 F.R. 7025, provided:\nSection 1. The allowances continue.")


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


class Locate(unittest.TestCase):
    def test_exact_ellipsis_and_whitespace(self):
        text = "Heading text here\nStatus line of the order, provided:\nBody."
        self.assertEqual(X.locate(text, "Status line"), (18, 29))
        self.assertEqual(X.locate(text, "...line of the order..."), (25, 25 + len("line of the order")))
        start, end = X.locate(text, "Heading text here | Status line of the order, provided:")
        self.assertEqual(text[start:end], "Heading text here\nStatus line of the order, provided:")

    def test_ambiguous_or_short_quote_is_not_located(self):
        self.assertIsNone(X.locate("Repeated words. Repeated words.", "...Repeated words..."))
        self.assertIsNone(X.locate("a b c", "a  b"))  # too short to match without whitespace
        self.assertIsNone(X.locate("text", "absent words"))

    def test_whitespace_runs_collapse_but_spaces_are_not_deleted(self):
        # A quote about order 12345 must not land on text about order 1234 (finding 4).
        self.assertIsNone(X.locate("Ex. Ord. No. 1234 5 U.S.C. 301 applies", "Ex. Ord. No. 12345 U.S.C. 301"))
        text = "Ex. Ord. No. 1234\n  5 U.S.C. 301 applies"
        start, end = X.locate(text, "Ex. Ord. No. 1234 5 U.S.C. 301")
        self.assertEqual(text[start:end], "Ex. Ord. No. 1234\n  5 U.S.C. 301")

    def test_exact_hit_must_also_be_unique_with_whitespace_collapsed(self):
        text = "Executive Order 12345 is revoked. Later text. Executive Order 12345\nis revoked."
        self.assertIsNone(X.locate(text, "Executive Order 12345 is revoked."))
        self.assertIsNone(X.locate(text, "...Executive Order 12345 is revoked..."))


class ScannerContainers(unittest.TestCase):
    def test_mentions_carry_their_whole_note_or_section_text(self):
        with open(FIX / "usc_sample.xml", "rb") as f:
            recs = list(usc_scan.scan_uslm(f, "usc99.xml"))
        notes = {r["note_id"]: r["text"] for k, r in recs if k == "eo_note"}
        printed = [r for k, r in recs if k == "mention" and r["role"] == "printed_eo_text"]
        self.assertTrue(printed)
        for m in printed:
            self.assertEqual(m["_container_text"], notes[m["note_id"]])
            start, end = X.locate(m["_container_text"], m["snippet"])
            self.assertTrue(m["_container_text"][start:end].startswith(m["note_heading"][:20]))
        sections = [r for k, r in recs if k == "mention" and r["role"] == "statutory_text_reference"]
        for m in sections:
            self.assertIn(m["eo_raw"], m["_container_text"])

    def test_book_rows_do_not_carry_container_text(self):
        book = make_book()
        self.assertFalse(any("_container_text" in m for m in book.mentions))
        for f in book.fragments():
            for d in f["data"]:
                self.assertFalse(str(d.get("text_path") or "").startswith("USC_EO_NOTES.jsonl#"))


class Regenerate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = pathlib.Path(self.tmp.name)
        write_jsonl(self.out / "USC_EO_NOTES.jsonl", [{
            "member": "usc05.xml", "note_id": "id27f6", "citation": "5 U.S.C. 5941 note",
            "heading": "Ex. Ord. No. 10000. Regulations", "subjects": ["10000"],
            "status_line": "Ex. Ord. No. 10000, Sept. 16, 1948, 13 F.R. 5453, as amended by Ex. Ord. No. 10636, "
                           "Sept. 16, 1955, 20 F.R. 7025, provided:",
            "text": NOTE_TEXT, "instrument_ids": ["EO:10000"], "edition": "U.S. Code release point 119-121",
            "source_id": ZIP["source_id"], "page_or_item": POI}])
        write_jsonl(self.out / "SOURCES.jsonl", [ZIP])
        ref = {"url": ZIP["url"], "sha256": ZIP["sha256"], "page_or_item": POI}
        self.frags = [
            {"instrument_id": "EO:10000", "kind": "current_predicate_candidates", "data": [
                {"system": "usc", "basis_code": "printed_eo_text", "where": "USC 5 U.S.C. 5941 note",
                 "snippet": ("Ex. Ord. No. 10000. Regulations | Ex. Ord. No. 10000, Sept. 16, 1948, 13 F.R. 5453, "
                             "as amended by Ex. Ord. No. 10636, Sept. 16, 1955, 20 F.R. 7025, provided:"),
                 "source": ref, "text_path": "USC_EO_NOTES.jsonl#note_id=id27f6"},
                {"system": "ecfr", "basis_code": "cfr_text_reference", "where": "CFR 5 CFR 1.1", "snippet": "x",
                 "source": {"url": "https://www.govinfo.gov/x.xml", "sha256": "e" * 64, "page_or_item": "5 CFR 1.1"}}],
             "sources": [ref]},
            {"instrument_id": "EO:10636", "kind": "current_predicate_candidates", "data": [
                {"system": "usc", "basis_code": "amending_order_in_status_line", "where": "USC 5 U.S.C. 5941 note",
                 "snippet": "...16, 1948, 13 F.R. 5453, as amended by Ex. Ord. No. 10636, Sept. 16, 1955, 20 F.R. 7025, provided:",
                 "source": ref}], "sources": [ref]},
            {"instrument_id": "EO:10636", "kind": "later_event_candidates", "data": [{"system": "usc", "source": ref}],
             "sources": [ref]}]
        write_jsonl(self.out / "FRAGMENTS.jsonl", self.frags)
        (self.out / "SUMMARY.json").write_text(json.dumps({"job": "current-law"}), encoding="utf-8")

    def read(self, name):
        return [json.loads(l) for l in (self.out / name).read_text(encoding="utf-8").splitlines()]

    def test_extract_declaration_and_exact_spans(self):
        counts = X.regenerate(self.out)
        self.assertEqual(counts["extracts"], 1)
        self.assertEqual((counts["usc_leads"], counts["with_extract"], counts["located"]), (2, 2, 2))
        rel = "usc-notes/id27f6.txt"
        raw = (self.out / rel).read_bytes()
        self.assertEqual(raw, NOTE_TEXT.encode("utf-8"))
        digest = hashlib.sha256(raw).hexdigest()
        sources = self.read("SOURCES.jsonl")
        self.assertEqual(sources[0], ZIP)  # the release-point record itself is unchanged
        decl = sources[1]
        # Own identity is the extract; the ZIP it was cut from is extracted_from.
        self.assertEqual((decl["url"], decl["sha256"], decl["bytes"], decl["text_path"], decl["text_sha256"]),
                         (ZIP["url"], digest, len(raw), rel, digest))
        self.assertEqual(decl["extracted_from"], {"url": ZIP["url"], "sha256": ZIP["sha256"], "bytes": ZIP["bytes"]})
        self.assertEqual(decl["instrument_ids"], [])
        self.assertEqual(decl["printed_instrument_ids"], ["EO:10000"])
        self.assertEqual((decl["page_or_item"], decl["item_extract"], decl["note_id"]), (POI, "page_or_item", "id27f6"))
        self.assertEqual((decl["member"], decl["member_sha256"], decl["zip"]), ("usc05.xml", "d" * 64, "xml_uscAll@119-121.zip"))
        frags = self.read("FRAGMENTS.jsonl")
        printed, ecfr = frags[0]["data"]
        amending = frags[1]["data"][0]
        for entry in (printed, amending):
            self.assertEqual((entry["text_path"], entry["text_sha256"]), (rel, digest))
            self.assertEqual(NOTE_TEXT[entry["char_start"]:entry["char_end"]], entry["text"])
            self.assertEqual(entry["source"], {"url": ZIP["url"], "sha256": ZIP["sha256"], "page_or_item": POI})
        self.assertTrue(printed["text"].startswith("Ex. Ord. No. 10000. Regulations\nEx. Ord. No. 10000, Sept. 16"))
        self.assertEqual(printed["char_start"], 0)
        self.assertNotIn("text_path", ecfr)
        self.assertEqual(frags[2], self.frags[2])
        summary = json.loads((self.out / "SUMMARY.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["usc_text_extracts"]["located"], 2)

    def test_regeneration_is_deterministic(self):
        X.regenerate(self.out)
        first = {p.name: p.read_bytes() for p in self.out.rglob("*") if p.is_file()}
        X.regenerate(self.out)
        second = {p.name: p.read_bytes() for p in self.out.rglob("*") if p.is_file()}
        self.assertEqual(first, second)

    def test_lead_of_an_item_that_is_not_held_loses_its_old_pointer(self):
        # Scenario C: a section extract whose bytes fail its declaration is dropped on regeneration,
        # and the lead that pointed at it must not keep the stale text_path or pin.
        section_poi = "5 U.S.C. 5941; usc05.xml (sha256 " + "d" * 64 + ") in xml_uscAll@119-121.zip"
        (self.out / "usc-sections").mkdir()
        (self.out / "usc-sections/s-1.txt").write_text("Section text naming Ex. Ord. No. 10000 here.", encoding="utf-8")
        stale = {"source_id": "usc:x:section:s", "route": X.EXTRACT_ROUTE, "page_or_item": section_poi,
                 "url": ZIP["url"], "sha256": "f" * 64, "text_path": "usc-sections/s-1.txt", "text_sha256": "f" * 64}
        write_jsonl(self.out / "SOURCES.jsonl", [ZIP, stale])
        self.frags[0]["data"].append({"system": "usc", "basis_code": "statutory_text_reference", "where": "USC 5 U.S.C. 5941",
                                      "snippet": "naming Ex. Ord. No. 10000", "text_path": "usc-sections/s-1.txt",
                                      "text_sha256": "f" * 64, "text": "naming Ex. Ord. No. 10000", "char_start": 13,
                                      "char_end": 38, "source": {"url": ZIP["url"], "sha256": ZIP["sha256"],
                                                                 "page_or_item": section_poi}})
        write_jsonl(self.out / "FRAGMENTS.jsonl", self.frags)
        X.regenerate(self.out)
        entry = self.read("FRAGMENTS.jsonl")[0]["data"][2]
        for key in ("text_path", "text_sha256", "text", "char_start", "char_end"):
            self.assertNotIn(key, entry)
        self.assertNotIn(section_poi, [r.get("page_or_item") for r in self.read("SOURCES.jsonl")])

    def test_unlocatable_quote_keeps_pointer_without_span(self):
        self.frags[0]["data"][0]["snippet"] = "Words that the note does not contain at all."
        write_jsonl(self.out / "FRAGMENTS.jsonl", self.frags)
        X.regenerate(self.out)
        entry = self.read("FRAGMENTS.jsonl")[0]["data"][0]
        self.assertEqual(entry["text_path"], "usc-notes/id27f6.txt")
        for key in ("text", "char_start", "char_end"):
            self.assertNotIn(key, entry)

    def test_conflicting_texts_under_one_locator_are_not_extracted(self):
        ex = X.Extracts()
        ex.add(POI, "one text", ZIP["source_id"], "c", "note", note_id="n")
        ex.add(POI, "another text", ZIP["source_id"], "c", "note", note_id="n")
        held, rows = ex.write(self.out, {ZIP["source_id"]: ZIP})
        self.assertEqual((held, rows), ({}, []))

    def test_job_path_writes_section_extracts(self):
        book = make_book()
        with open(FIX / "usc_sample.xml", "rb") as f:
            for kind, rec in usc_scan.scan_uslm(f, "usc99.xml"):
                if kind == "mention" and rec["role"] in build.PREDICATE_ROLES:
                    book.extracts.add(rec["citation"] + "; usc99.xml", rec["_container_text"], "usc:test",
                                      rec["citation"], "note" if rec["location_kind"] == "note" else "section",
                                      note_id=rec.get("note_id", ""), container_id=rec.get("container_id", ""))
        frags = book.fragments()
        held, rows = book.extracts.write(self.out, book.sources)
        counts = X.attach(frags, held)
        self.assertGreater(counts["located"], 0)
        self.assertTrue(all(r["instrument_ids"] == [] and r["url"] == book.sources["usc:test"]["url"] for r in rows))
        for f in frags:
            for d in f["data"]:
                if "text" in d:
                    held_text = (self.out / d["text_path"]).read_text(encoding="utf-8")
                    self.assertEqual(held_text[d["char_start"]:d["char_end"]], d["text"])


if __name__ == "__main__":
    unittest.main()
