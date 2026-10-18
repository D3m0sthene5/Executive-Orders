"""Contract and adversarial synthetic tests for the pure excavators."""
import importlib.util
import json
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("excavate", Path(__file__).with_name("excavate.py"))
excavate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(excavate)
SOURCE = {"url": "https://example.test/original.pdf", "sha256": "a" * 64, "page_or_item": "1 FR 1, PDF pages 5-6", "text_path": "held/order.txt", "text_sha256": "b" * 64}


class ExcavatorTests(unittest.TestCase):
    def act(self, text, **kwargs):
        return excavate.acting_provision("EO:1", "EO:9", text, SOURCE, **kwargs)

    def assert_quote(self, text, record, field="text"):
        self.assertEqual(text[record["char_start"]:record["char_end"]], record[field])

    def test_single_sentence_unicode_exact(self):
        text = "By virtue of the authority vested in me, I hereby extend the café commission for four years.\nTHE WHITE HOUSE\nJune 1, 1940."
        record = excavate.segment("EO:1", text, SOURCE)
        self.assertEqual(len(record["clauses"]), 1)
        clause = record["clauses"][0]
        self.assertEqual(clause["scope_id"], "EO:1#whole")
        self.assertEqual(clause["char_start"], 0)
        self.assertNotIn("WHITE HOUSE", clause["text"])
        self.assert_quote(text, clause)
        self.assertEqual(clause["pdf_page"], 5)

    def test_hierarchy_lead_schedules_and_amendment(self):
        text = "WHEREAS an emergency exists;\n\nI hereby establish a council.\n\nSection 1. The following duties apply:\n(a) First duty.\n(1) First item.\n(2) Second item.\n(b) Second duty.\nSection 2. Executive Order 2 is amended by adding this provision.\nSCHEDULE A\n(1) A scheduled office.\n"
        record = excavate.segment("EO:1", text, SOURCE)
        clauses = record["clauses"]
        self.assertTrue(clauses[0]["text"].startswith("I hereby"))
        self.assertNotIn("WHEREAS", " ".join(c["text"] for c in clauses))
        self.assertIn("EO:1#sec1-a-2", [c["scope_id"] for c in clauses])
        self.assertIn("schedule", [c["kind"] for c in clauses])
        self.assertIn("amendment_instruction", [c["kind"] for c in clauses])
        self.assertEqual(len({c["id"] for c in clauses}), len(clauses))
        for left, right in zip(clauses, clauses[1:]):
            self.assertLessEqual(left["char_end"], right["char_start"])
        for clause in clauses:
            self.assert_quote(text, clause)

    def test_unknown_pdf_page_stays_unknown(self):
        clause = excavate.segment("EO:1", "I hereby establish a body.", {})["clauses"][0]
        self.assertIsNone(clause["pdf_page"])

    def test_pdf_page_markers_override_first_page_for_later_clauses(self):
        text = "=== PDF page 9 of 248 ===\nSection 1. First duty.\n=== PDF page 10 of 248 ===\nSec. 2. Second duty."
        clauses = excavate.segment("EO:1", text, SOURCE)["clauses"]
        self.assertEqual([c["pdf_page"] for c in clauses], [9, 10])

    def test_signature_before_schedule_and_neighboring_order(self):
        text = "EXECUTIVE ORDER 1\n\nI hereby establish these offices:\nJOHN DOE\nTHE WHITE HOUSE\nJune 1, 1940\nSCHEDULE A\n1. First office.\n2. Second office.\nEXECUTIVE ORDER 2\n\nI hereby establish something else."
        clauses = excavate.segment("EO:1", text, SOURCE)["clauses"]
        combined = " ".join(c["text"] for c in clauses)
        self.assertIn("Second office", combined)
        self.assertNotIn("something else", combined)
        self.assertNotIn("JOHN DOE", combined)
        self.assertEqual(len([c for c in clauses if c["kind"] == "item"]), 2)

    def test_fixed_term_requires_stated_start(self):
        text = "I hereby extend the existence of the Committee for a period of four years, from June 30,\n1938 to June 30, 1942."
        clauses = excavate.segment("EO:1", text, SOURCE)
        findings = excavate.own_terms("EO:1", text, SOURCE, clauses)
        fixed = next(f for f in findings if f["kind"] == "fixed_term")
        self.assertEqual(fixed["start_date"], "1938-06-30")
        self.assertEqual(fixed["stated_end_date"], "1942-06-30")
        self.assertEqual(fixed["computed_end_candidate"], "1942-06-30")
        self.assert_quote(text, fixed)
        text = "The Committee shall continue for a period of four years."
        findings = excavate.own_terms("EO:1", text, SOURCE, [])
        self.assertIsNone(findings[0]["computed_end_candidate"])

    def test_deadline_never_becomes_end(self):
        text = "The Committee shall report within thirty days from January 1, 1940."
        findings = excavate.own_terms("EO:1", text, SOURCE, [])
        self.assertEqual([f["kind"] for f in findings], ["report_deadline"])
        self.assertIsNone(findings[0]["computed_end_candidate"])
        self.assertIsNone(findings[0]["stated_end_date"])

    def test_all_own_term_classes(self):
        text = "A temporary commission is established.\n\nIt shall expire on June 1, 1940.\n\nThe body continues until its work is completed.\n\nThe grant is subject to available funds.\n\nIt remains for the duration of the emergency."
        kinds = {f["kind"] for f in excavate.own_terms("EO:1", text, SOURCE, [])}
        self.assertTrue({"temporary_body", "sunset_date", "until_event", "condition", "emergency_duration"} <= kinds)

    def test_parent_exceptions_are_partial(self):
        text = "Sec. 3. Except with respect to the positions enumerated in section 2 of this order, Executive Order No. 11248 of October 10, 1965, as amended, is hereby revoked."
        r = excavate.acting_provision("EO:11389", "EO:11708", text, SOURCE, signing_date="1973-03-23", parent_id="EO:11248")
        self.assertFalse(r["names_target"])
        self.assertEqual(r["scope"], "partial")
        self.assertEqual(r["verb"], "revoke")
        self.assertTrue(r["exceptions_text"])
        self.assert_quote(text, r, "provision_text")
        self.assertIsNone(self.act("Executive Order No. 11248 is revoked.", parent_id="EO:11248"))

    def test_whole_parent_and_section_only(self):
        r = self.act("Executive Order No. 2, as amended, is revoked.", parent_id="EO:2")
        self.assertEqual(r["scope"], "whole_via_parent")
        r = self.act("Section 2 of Executive Order No. 1 is hereby revoked.")
        self.assertEqual(r["scope"], "partial")
        r = self.act("Executive Order No. 1 is amended by adding a new paragraph.")
        self.assertEqual(r["scope"], "partial")

    def test_no_fabricated_missing_provision(self):
        self.assertIsNone(self.act("All orders inconsistent herewith are revoked."))
        r = self.act("The report mentions Executive Order No. 1.")
        self.assertEqual(r["provision_text"], "")
        self.assertIsNone(r["char_start"])
        self.assertIn("MISSING_CHANGE_PROVISION", r["notes"])
        r = self.act("By the authority in Executive Order 1, as amended, I hereby establish a body.")
        self.assertEqual(r["provision_text"], "")
        r = self.act("Executive Order 1 is not revoked.")
        self.assertEqual(r["verb"], "other")
        self.assertEqual(excavate.chain("EO:1", [r])["events"], [])

    def test_effective_dates(self):
        r = self.act("Executive Order 1 is revoked. This order is effective on June 30, 1942.")
        self.assertEqual((r["effective_class"], r["effective_date"]), ("stated_date", "1942-06-30"))
        for span in r["effective_wording"]:
            self.assert_quote("Executive Order 1 is revoked. This order is effective on June 30, 1942.", span)
        r = self.act("Executive Order 1 is revoked. This order takes effect thirty days after January 1, 1940.")
        self.assertEqual((r["effective_class"], r["effective_date"]), ("relative", "1940-01-31"))
        r = self.act("Executive Order 1 is revoked. This order takes effect thirty days after the date of this order.", signing_date="1940-01-01")
        self.assertEqual(r["effective_date"], "1940-01-31")
        r = self.act("Executive Order 1 is revoked. This order takes effect thirty days after the date of this order.")
        self.assertIsNone(r["effective_date"])
        r = self.act("Executive Order 1 is revoked.", signing_date="1940-01-01")
        self.assertEqual(r["effective_class"], "on_signing")
        self.assertIsNone(r["effective_date"])
        self.assertIn("assumption", r["notes"])
        r = self.act("Executive Order 1 is revoked. This order is effective upon signing.", signing_date="1940-01-01")
        self.assertEqual(r["effective_date"], "1940-01-01")
        for wording in ["effective June 30, 1942", "effective on and after June 30, 1942"]:
            self.assertEqual(self.act("Executive Order 1 is revoked. This order is " + wording + ".")["effective_date"], "1942-06-30")

    def test_variable_and_other_section_dates(self):
        r = self.act("Executive Order 1 is revoked. This order becomes effective with respect to any agency concerned as of the close of its pay period terminating or current on January 31, 1946.")
        self.assertEqual(r["effective_class"], "agency_variable")
        self.assertIsNone(r["effective_date"])
        r = self.act("Section 1. Executive Order 1 is revoked.\nSection 2. This section is effective on June 30, 1942.")
        self.assertIsNone(r["effective_date"])

    def test_savings(self):
        r = self.act("Executive Order 1 is revoked. This order shall not affect rights accrued or pending proceedings.")
        self.assertEqual(r["savings_phrases"], ["This order shall not affect rights accrued or pending proceedings."])

    def test_discovery_plural_generic_and_suffixes(self):
        text = "Executive Orders Nos. 1, 2 and 3A are revoked. All orders inconsistent herewith are revoked."
        records = excavate.discover_mentions("EO:9", text, SOURCE)
        self.assertEqual({r["target_id"] for r in records}, {"EO:1", "EO:2", "EO:3A"})
        self.assertEqual(excavate.generic_reference_count(text), 1)
        for record in records:
            self.assert_quote(text, record, "provision_text")

    def test_change_list_instruction_reaches_later_items(self):
        text = "The following orders are revoked:\n(1) Executive Order 1 of June 1, 1940.\n(2) Executive Order 2 of June 2, 1940."
        records = excavate.discover_mentions("EO:9", text, SOURCE)
        self.assertEqual({r["target_id"] for r in records}, {"EO:1", "EO:2"})
        self.assertEqual({r["verb"] for r in records}, {"revoke"})
        for record in records:
            self.assert_quote(text, record, "provision_text")

    def test_dated_plural_order_references_keep_exact_ids_and_spans(self):
        text = ("Executive Orders No. 7057 of May 28, 1935, No. 7180 of September 6, 1935, "
                "as amended, and No. 7493 of November 14, 1936, are hereby amended accordingly.")
        records = excavate.discover_mentions("EO:7689", text, SOURCE)
        self.assertEqual({r["target_id"] for r in records}, {"EO:7057", "EO:7180", "EO:7493"})
        self.assertEqual({r["verb"] for r in records}, {"amend"})
        for record in records:
            self.assert_quote(text, record, "provision_text")
        refs = list(excavate._references(text))
        self.assertEqual([text[a:b] for _, a, b in refs][1:], ["7180", "7493"])

    def test_plural_dates_are_not_ids_and_unrelated_numbers_stay_out(self):
        text = "Executive Orders 1 dated January 2, 1940, and 3A dated February 2, 1940 are revoked; report No. 99 is preserved."
        self.assertEqual({r[0] for r in excavate._references(text)}, {"EO:1", "EO:3A"})
        # Comma-grouped/OCR-corrupt identifiers need source reconciliation; do
        # not silently admit a prefix or strip punctuation to infer an identity.
        for text in ["Executive Order No. 10,0041 is revoked.", "Executive Orders No. 10,0041 and 2 are revoked.", "Executive O rder No. 1234 is revoked."]:
            self.assertEqual(list(excavate._references(text)), [])

    def test_chain_sort_and_filter(self):
        a = self.act("Executive Order 1 is revoked.", signing_date="1942-01-01")
        b = self.act("Executive Order 1 is amended.", signing_date="1940-01-01")
        c = self.act("Executive Order 1 was mentioned in a report.")
        chain = excavate.chain("EO:1", [a, c, b], 7)
        self.assertEqual([e["verb"] for e in chain["events"]], ["amend", "revoke"])
        self.assertEqual(chain["generic_refs_excluded"], 7)
        self.assertEqual(chain["events"][0]["id"], "CHAIN:EO:1#1")

    def test_month_end_ambiguity_and_determinism(self):
        text = "The body continues for one year from February 29, 1940."
        result = excavate.own_terms("EO:1", text, SOURCE, [])
        self.assertIsNone(result[0]["computed_end_candidate"])
        self.assertEqual(result, excavate.own_terms("EO:1", text, SOURCE, []))
        self.assertEqual(json.loads(json.dumps(result)), result)
        text = "The body continues for twenty-four years from January 1, 1940."
        result = excavate.own_terms("EO:1", text, SOURCE, [])
        self.assertEqual(result[0]["computed_end_candidate"], "1964-01-01")

    def test_stated_date_of_order_term_uses_source_signing_date_only(self):
        text = "The Commission shall terminate two years from the date of this order, unless extended."
        for source, expected in [(dict(SOURCE, signing_date="1995-10-03"), "1997-10-03"), (SOURCE, None), (dict(SOURCE, signing_date="invalid"), None)]:
            findings = excavate.own_terms("EO:12975", text, source, [])
            fixed = next(f for f in findings if f["kind"] == "fixed_term")
            self.assertEqual(fixed["computed_end_candidate"], expected)
            self.assertIn("printed signing date", fixed["notes"])
        # A supplied signing date alone supplies no unstated temporal base.
        findings = excavate.own_terms("EO:1", "The body shall continue for two years.", dict(SOURCE, signing_date="1995-10-03"), [])
        self.assertIsNone(findings[0]["computed_end_candidate"])

    def test_authority_only_preamble_and_ocr_signature_regression(self):
        text = ("Instrument: EO:12462\nSource: https://example.gov/order.pdf\n\n"
                "=== PDF page 9 of 248 ===\nFederal Register\nExecutive Order 12462\nTitle\n"
                "By the authority vested in me as President, it is\nhereby ordered as follow s:\n"
                "Section 1. There is established a Committee.\n"
                "Sec. 2. The Committee shall terminate, unless sooner\nextended.\n"
                "TH E W H ITE HOUSE, \nF e b ru a ry 17, 1984.\n[FR Doc. 84-4874]")
        clauses = excavate.segment("EO:12462", text, SOURCE)["clauses"]
        self.assertEqual([c["scope_id"] for c in clauses], ["EO:12462#sec1", "EO:12462#sec2"])
        self.assertTrue(clauses[-1]["text"].endswith("extended."))
        self.assertNotIn("HOUSE", clauses[-1]["text"])
        for c in clauses:
            self.assert_quote(text, c)

    def test_lowercase_crossrefs_and_comma_parenthetical_are_not_headings(self):
        text = ("Section 601. Policies consistent with\nsection 6002 of RCRA shall apply.\n"
                "(a) The first duty applies.\n(b) The goals in subsections\n"
                "(a), (b), and (c) above shall apply.\nSec. 602. More duties.")
        clauses = excavate.segment("EO:13101", text, SOURCE)["clauses"]
        self.assertEqual([c["scope_id"] for c in clauses], ["EO:13101#sec601", "EO:13101#sec601-a", "EO:13101#sec601-b", "EO:13101#sec602"])
        self.assertIn("(a), (b)", clauses[-2]["text"])

    def test_multiline_revocation_list_and_historical_amenders(self):
        text = ("Sec. 4. The following Executive orders or sections thereof, which established\n"
                "committees that have terminated or whose work is completed, are revoked:\n"
                "(a) Executive Order No. 12792, establishing a Commission;\n"
                "(b ) Executive Order No. 12813, as amended by Executive Order No. 12815,\n"
                "establishing a Commission;\n"
                "(c) Section 5 of Executive Order No. 12675, establishing a Board.\n"
                "Sec. 5. Other matters.")
        r = excavate.acting_provision("EO:12813", "EO:12869", text, SOURCE)
        self.assertEqual((r["verb"], r["scope"]), ("revoke", "whole"))
        self.assert_quote(text, r, "provision_text")
        self.assertIsNone(excavate.acting_provision("EO:12815", "EO:12869", text, SOURCE))
        r = excavate.acting_provision("EO:12675", "EO:12869", text, SOURCE)
        self.assertEqual(r["scope"], "partial")
        text = text.replace("12813", "1 2813")
        r = excavate.acting_provision("EO:12813", "EO:12869", text, SOURCE)
        self.assertEqual(r["verb"], "revoke")
        self.assertIn("1 2813", r["provision_text"])

    def test_real_hydrated_segmentation_regressions(self):
        repo = Path(__file__).resolve().parents[2]
        texts = repo / "jobs/fr-originals/output/texts"
        ids = ["10222", "12462", "13101"]
        if not all((texts / ("EO_" + iid + ".txt")).is_file() for iid in ids):
            self.skipTest("Real FR source text is not hydrated in this checkout")
        for iid in ids:
            text = (texts / ("EO_" + iid + ".txt")).read_bytes().decode("utf-8")
            clauses = excavate.segment("EO:" + iid, text, SOURCE)["clauses"]
            self.assertFalse(any(c["scope_id"].endswith("#lead") for c in clauses))
            self.assertEqual(len({c["scope_id"] for c in clauses}), len(clauses))
            self.assertFalse(any("6002" in c["scope_id"] for c in clauses))
            self.assertNotIn("HOUSE", clauses[-1]["text"])
            for c in clauses:
                self.assert_quote(text, c)
            if iid == "10222":
                self.assertEqual(len(clauses), 3)
            if iid == "12462":
                self.assertTrue(clauses[-1]["text"].endswith("extended."))

    def test_real_hydrated_actor_list_regressions(self):
        repo = Path(__file__).resolve().parents[2]
        texts = repo / "jobs/fr-originals/output/texts"
        if not all((texts / ("EO_" + actor + ".txt")).is_file() for actor in ["12692", "12869"]):
            self.skipTest("Real FR acting source text is not hydrated in this checkout")
        for actor, target, scope in [("12692", "12462", "whole"), ("12692", "12592", "whole"), ("12869", "12813", "whole"), ("12869", "12675", "partial")]:
            text = (texts / ("EO_" + actor + ".txt")).read_bytes().decode("utf-8")
            r = excavate.acting_provision("EO:" + target, "EO:" + actor, text, SOURCE)
            self.assertIsNotNone(r)
            self.assertEqual((r["verb"], r["scope"]), ("revoke", scope))
            self.assert_quote(text, r, "provision_text")

    def test_contract_examples_parse_and_roundtrip(self):
        fixtures = Path(__file__).resolve().parents[2] / "research/plans/claim_kit_contract/fixtures"
        paths = sorted(fixtures.glob("*.example.jsonl"))
        self.assertEqual(len(paths), 4)
        counts = []
        for path in paths:
            records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            self.assertEqual(json.loads(json.dumps(records)), records)
            counts.append(len(records))
            for record in records:
                # Held fixture texts may be absent in an offline checkout.
                source = record.get("source", record.get("actor_source", {}))
                source_path = Path(__file__).resolve().parents[2] / source.get("text_path", "__missing__")
                if source_path.is_file():
                    text = source_path.read_text(encoding="utf-8")
                    for quote in record.get("clauses", [record]):
                        field = "provision_text" if "provision_text" in quote else "text"
                        if quote.get(field) and quote.get("char_start") is not None:
                            self.assert_quote(text, quote, field)
        self.assertEqual(counts, [2, 1, 2, 1])


if __name__ == "__main__":
    unittest.main()
