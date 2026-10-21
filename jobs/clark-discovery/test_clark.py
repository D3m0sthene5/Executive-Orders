"""Offline tests for Clark with a synthetic repository. No network, no real repo data."""
import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import eo_identity as ident  # noqa: E402
import clark  # noqa: E402


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def census_row(iid, year, cls="validated_numbered"):
    return {"id": iid, "bibliographic_class": cls, "included_in_bibliography": "1",
            "date_effective": str(year), "year_group": "1907–1936" if year < 1937 else "1937–1989"}


def readiness_row(iid, blockers, step="open"):
    return {"instrument_id": iid, "provisional_status": "", "blockers": blockers, "step_original_text": step}


class SyntheticRepo(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="clark-")
        self.out = os.path.join(self.root, "_out")
        r = self.root
        # universe: 5850, 5851, 5852, 5857 (so 5853-5856 are gaps), 6000, 6852, 7543, 7933a, 10860, 11060
        write_csv(os.path.join(r, ident.UNIVERSE), [
            census_row("EO:5850", 1932), census_row("EO:5851", 1932), census_row("EO:5852", 1932), census_row("EO:5857", 1932),
            census_row("EO:6000", 1932), census_row("EO:6852", 1934), census_row("EO:7543", 1937), census_row("EO:7933a", 1938),
            census_row("EO:8640", 1940), census_row("EO:10860", 1959), census_row("EO:11060", 1962)])
        write_csv(os.path.join(r, ident.READINESS), [
            readiness_row("EO:5850", "NO_OFFICIAL_SOURCE_LOCATED"),                                   # number only
            readiness_row("EO:5851", "NO_OFFICIAL_SOURCE_LOCATED"),                                   # ProQuest link: year known
            readiness_row("EO:5852", "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND"),  # Lewis's
            readiness_row("EO:5857", "NO_OFFICIAL_SOURCE_LOCATED"),                                   # APP index knows it
            readiness_row("EO:6000", "", step="done"), readiness_row("EO:6852", "", step="done"),
            readiness_row("EO:7543", "", step="done"), readiness_row("EO:7933a", "NO_OFFICIAL_SOURCE_LOCATED"),
            readiness_row("EO:8640", "", step="done"), readiness_row("EO:10860", "", step="done"),
            readiness_row("EO:11060", "", step="done")])
        texts = os.path.join(r, "jobs/app-executive-orders/output/texts")
        os.makedirs(texts)
        bodies = {
            "EO:6852": "It is ordered that Executive Order No. 5862, dated June 23, 1932, withdrawing public lands, is revoked in part. "
                       "Executive order of January 17, 1873 is also noted. See Executive Order 7933-A.",
            "EO:8640": "Executive Order No. 86402 is a footnote slip. Executive Orders Nos. 5853, 5854 and 5855 are continued. "
                       "EXECUTIVE ORDER 8640 E stablishing a board. E.O. 9322, 8 F.R. 1234.",
            "EO:11060": "Title 3 Executive Order 1T 060 PRESCRIBING. This supersedes Executive Order 12845 of April 21, 1993.",
        }
        frags = []
        for iid, body in bodies.items():
            name = iid.replace(":", "_") + ".txt"
            with open(os.path.join(texts, name), "w", encoding="utf-8") as fh:
                fh.write(body)
            frags.append({"instrument_id": iid, "kind": "original_representation", "produced_by": "app-executive-orders",
                          "acceptable_as_original": False, "grade": "mirror_transcription",
                          "sources": [{"url": f"https://example.org/{iid}", "sha256": "0" * 64, "page_or_item": "p"}],
                          "data": {"text_path": "texts/" + name, "app_date": {"EO:6852": "1934-09-01", "EO:8640": "1940-12-20",
                                                                               "EO:11060": "1962-11-07"}[iid],
                                   "title": "", "sha256": "0" * 64, "url": f"https://example.org/{iid}"}})
        frags.append({"instrument_id": "EO:5852", "kind": "original_representation", "produced_by": "app-executive-orders",
                      "acceptable_as_original": False, "grade": "mirror_transcription", "sources": [{}],
                      "data": {"text_path": None, "app_date": "1932-06-01", "title": "Lewis's order"}})
        write_jsonl(os.path.join(r, "jobs/app-executive-orders/output/FRAGMENTS.jsonl"), frags)
        write_csv(os.path.join(r, ident.APP_INDEX), [
            {"instrument_id": "EO:5853", "eo_number_raw": "5853", "date": "1932-06-03", "title": "Executive Order 5853—Waiver",
             "president": "Herbert Hoover", "url": "https://www.presidency.ucsb.edu/5853"},
            {"instrument_id": "EO:5857", "eo_number_raw": "5857", "date": "1932-06-16", "title": "Executive Order 5857—Known",
             "president": "Herbert Hoover", "url": "https://www.presidency.ucsb.edu/5857"},
            {"instrument_id": "EO:6852", "eo_number_raw": "6852", "date": "1934-09-01", "title": "Executive Order 6852",
             "president": "FDR", "url": "https://www.presidency.ucsb.edu/6852"}])
        write_csv(os.path.join(r, ident.OFR_CATALOG), [
            {"id": "EO:7543", "signing_date": "1937-01-29", "citation": "2 FR 263", "title": "x", "html_url": "https://fr/7543",
             "disposition_notes": "See: EO 7933-A, July 14, 1938; Revokes: EO 5856, June 11, 1932"},
            {"id": "EO:10860", "signing_date": "1959-02-05", "citation": "24 FR 1", "title": "y", "html_url": "https://fr/10860",
             "disposition_notes": ""},
            {"id": "EO:11060", "signing_date": "1962-11-07", "citation": "27 FR 1", "title": "z", "html_url": "https://fr/11060",
             "disposition_notes": ""},
            {"id": "EO:8640", "signing_date": "1940-12-20", "citation": "5 FR 1", "title": "w", "html_url": "https://fr/8640",
             "disposition_notes": ""}])
        os.makedirs(os.path.join(r, ident.PROQUEST_DIR, "_resume"))
        rows = [{"id": "EO:5851", "n": "5851", "y": 1932, "pdf": "https://congressional.proquest.com/p", "rec": "https://congressional.proquest.com/r"}]
        with open(os.path.join(r, ident.PROQUEST_LINKS), "w", encoding="utf-8") as fh:
            fh.write("<html><script>const ROWS=" + json.dumps(rows) + ";</script></html>")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def run_job(self):
        return clark.run(self.root, self.out)

    def read(self, name):
        with open(os.path.join(self.out, name), encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    def test_number_gaps_with_windows_and_index_evidence(self):
        self.run_job()
        gaps = {g["instrument_id"]: g for g in self.read("NUMBER_GAPS.csv")}
        self.assertEqual(len(gaps), 11060 - 10, "every integer up to the highest number, less the 10 numbered census rows")
        for known in ("EO:5852", "EO:5857", "EO:6000", "EO:11060"):
            self.assertFalse(known in gaps, known)
        self.assertTrue("EO:7933" in gaps, "7933 is in the census only as 7933a, so the bare number is a gap")
        self.assertEqual(gaps["EO:5853"]["strength"], "strong", "APP index names it with a date and title")
        self.assertIn("app_index:1932-06-03", gaps["EO:5853"]["identity_evidence"])
        self.assertEqual(gaps["EO:5854"]["strength"], "cited", "named in a saved text, no index entry")
        self.assertEqual(gaps["EO:5854"]["cited_plausibly_by"], "EO:8640")
        self.assertEqual(gaps["EO:5862"]["strength"], "strong", "cited with a stated date")
        self.assertIn("cited_with_date:1932-06-23", gaps["EO:5862"]["identity_evidence"])
        self.assertEqual(gaps["EO:5856"]["strength"], "strong", "an OFR note names it with a date")
        self.assertTrue(gaps["EO:5853"]["window_from"].startswith("EO:5852 1932"))
        self.assertTrue(gaps["EO:5853"]["window_to"].startswith("EO:5857 1932-06-16"))
        self.assertEqual(gaps["EO:5900"]["strength"], "number_only")

    def test_cited_but_unknown_separates_real_citations_from_ocr(self):
        self.run_job()
        rows = self.read("CITED_BUT_UNKNOWN.csv")
        by = {}
        for r in rows:
            by.setdefault(r["cited_id"], []).append(r)
        self.assertEqual(by["EO:5862"][0]["plausibility"], "plausible")
        self.assertEqual(by["EO:5862"][0]["date_stated"], "1932-06-23")
        self.assertEqual(by["EO:5862"][0]["citing_id"], "EO:6852")
        self.assertIn("revoked in part", by["EO:5862"][0]["quote"])
        self.assertEqual(by["EO:86402"][0]["plausibility"], "likely_ocr_footnote_digit")
        self.assertEqual(by["EO:86402"][0]["glued_candidate"], "EO:8640")
        self.assertEqual(by["EO:1T"][0]["plausibility"], "likely_ocr_letter_for_digit")
        self.assertEqual(by["EO:1T"][0]["glued_candidate"], "EO:11060")
        self.assertEqual(by["EO:12845"][0]["plausibility"], "exceeds_numbers_issued_by_citing_date",
                         "a 1962 order cannot cite a 1993 number")
        self.assertNotIn("EO:8640E", by, "spaced small-caps title letter is not a suffix")
        self.assertNotIn("EO:8", by, "the 8 in '8 F.R.' is a volume, not an order")
        self.assertNotIn("EO:7933A", by, "EO:7933a is in the census under a lower-case letter")
        self.assertNotIn("EO:8640", by, "a document's own number is not a citation of an unknown")
        ids = [r["cited_id"] for r in rows]
        self.assertLess(ids.index("EO:5862"), ids.index("EO:86402"), "plausible rows sort first")

    def test_identity_unknown_is_number_without_any_index(self):
        s = self.run_job()
        rows = {r["instrument_id"]: r for r in self.read("IDENTITY_UNKNOWN.csv")}
        self.assertIn("EO:5850", rows)
        self.assertEqual(rows["EO:5850"]["what_is_known"], "census_year_1932")
        self.assertIn("EO:5851", rows)
        self.assertEqual(rows["EO:5851"]["proquest_link_supplied"], "yes")
        self.assertNotIn("EO:5852", rows, "transcription-only orders are Lewis's")
        self.assertNotIn("EO:5857", rows, "the APP index gives it a date and title")
        self.assertNotIn("EO:6000", rows, "original already saved")
        self.assertEqual(s["identity_unknown"]["number_only"], 2, "EO:5850 and EO:7933a")
        self.assertEqual(s["identity_unknown"]["with_proquest_link"], 1)

    def test_dated_unnumbered_reference_without_a_match(self):
        self.run_job()
        rows = self.read("DATED_UNNUMBERED.csv")
        self.assertEqual([r["date"] for r in rows], ["1873-01-17"])
        self.assertEqual(rows[0]["citing_id"], "EO:6852")
        self.assertEqual(rows[0]["numbered_orders_that_day"], "")

    def test_handoff_to_lewis_carries_evidence_and_no_census_claim(self):
        s = self.run_job()
        rows = {r["instrument_id"]: r for r in ident.read_jsonl(os.path.join(self.out, "HANDOFF_TO_LEWIS.jsonl"))}
        self.assertIn("EO:5853", rows)
        self.assertEqual(rows["EO:5853"]["clark_class"], "number_gap")
        self.assertIs(rows["EO:5853"]["in_census"], False)
        self.assertIn("EO:5851", rows, "ProQuest link gives a year to route on")
        self.assertEqual(rows["EO:5851"]["clark_class"], "identity_unknown")
        self.assertIs(rows["EO:5851"]["in_census"], True)
        self.assertNotIn("EO:5850", rows, "nothing to route on")
        self.assertNotIn("EO:5900", rows, "number-only gaps are not handed over")
        self.assertNotIn("EO:86402", rows, "OCR artifacts are never handed over")
        for r in rows.values():
            self.assertIn("Lead only", r["note"])
        self.assertEqual(s["handoff_to_lewis"]["rows"], len(rows))

    def test_lewis_proquest_texts_are_scanned_next_run(self):
        lewis_out = os.path.join(self.root, "jobs/lewis-originals/output")
        os.makedirs(os.path.join(lewis_out, "texts"))
        with open(os.path.join(lewis_out, "texts", "EO_5857.txt"), "w", encoding="utf-8") as fh:
            fh.write("This order amends Executive Order No. 5859 of June 21, 1932.")
        write_jsonl(os.path.join(lewis_out, "FRAGMENTS.jsonl"), [
            {"instrument_id": "EO:5857", "produced_by": "lewis-originals", "acceptable_as_original": False,
             "sources": [{}], "data": {"text_path": "texts/EO_5857.txt", "signing_date": "1932-06-16"}}])
        self.run_job()
        gaps = {g["instrument_id"]: g for g in self.read("NUMBER_GAPS.csv")}
        self.assertIn("cited_with_date:1932-06-21", gaps["EO:5859"]["identity_evidence"])
        self.assertEqual(gaps["EO:5859"]["cited_plausibly_by"], "EO:5857")

    def test_outputs_are_deterministic(self):
        self.run_job()
        first = {}
        for name in ("NUMBER_GAPS.csv", "CITED_BUT_UNKNOWN.csv", "IDENTITY_UNKNOWN.csv", "DATED_UNNUMBERED.csv", "HANDOFF_TO_LEWIS.jsonl"):
            with open(os.path.join(self.out, name), "rb") as fh:
                first[name] = fh.read()
        shutil.rmtree(self.out)
        self.run_job()
        for name, data in first.items():
            with open(os.path.join(self.out, name), "rb") as fh:
                self.assertEqual(fh.read(), data, name)

    def test_missing_inputs_are_reported_not_fatal(self):
        os.remove(os.path.join(self.root, ident.UNIVERSE))
        s = self.run_job()
        self.assertTrue(any("universe" in p for p in s["problems"]))
        self.assertEqual(s["number_gaps"]["total"], 0)


class MentionParsing(unittest.TestCase):
    def test_lists_suffixes_halves_and_dates(self):
        t = ("Executive Orders Nos. 9001, 9002 and 9005 of May 1, 1942; Executive Order 325-A; "
             "Executive Order No. 1182 1/2; E. O. 10,000, Sept. 16, 1948; Executive Order 3016B.")
        got = [(m["number"], m["suffix"], m["date"]) for m in ident.find_mentions(t)]
        self.assertEqual(got, [(9001, "", "1942-05-01"), (9002, "", "1942-05-01"), (9005, "", "1942-05-01"),
                               (325, "A", ""), (1182, "½", ""), (10000, "", "1948-09-16"), (3016, "B", "")])

    def test_ocr_shapes_are_not_mentions(self):
        self.assertEqual(ident.find_mentions("E. O. 1C480 and Executive Order No. 00 of July 2, 1918"), [])
        self.assertEqual([(m["number"], m["suffix"]) for m in ident.find_mentions("EXECUTIVE ORDER 10728 E stablishing")],
                         [(10728, "")])
        self.assertEqual([(m["number"], m["suffix"]) for m in ident.find_mentions("E.O. 9322, 8 F.R. 1; E.O. 9070, 7 F.R.")],
                         [(9322, ""), (9070, "")])

    def test_ids_round_trip(self):
        for s in ("EO:1234", "EO:1234A", "EO:1182½", "EO:23-1"):
            self.assertEqual(ident.canon_id(*ident.parse_eo_id(s)), s)
        self.assertEqual(ident.canon_id(*ident.parse_eo_id("EO:7933a")), "EO:7933A")
        self.assertEqual(ident.canon_id(*ident.parse_eo_id("EO:1234-A")), "EO:1234A")
        self.assertIsNone(ident.parse_eo_id("EO:UN:executive-orders-01:row:1"))
        self.assertIsNone(ident.parse_eo_id("PROC:4707"))


if __name__ == "__main__":
    unittest.main()
