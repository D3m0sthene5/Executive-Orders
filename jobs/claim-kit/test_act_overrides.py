"""Agent-located ACT records (act_overrides): only verified, independently upheld records enter."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import act_overrides as AO
import test_build as TB
from test_build import read_jsonl, write_json, write_jsonl

# The scanner finds no sentence naming "Executive Order 1" here (a title-style reference).
EO6 = ("EXECUTIVE ORDER 6\nBy the authority vested in me, the order of the First Board, numbered 1 in this series,\n"
       "is ended effective March 3, 1991.\n")
LEDGER = "research/excavator/test-review/review/REVIEW.jsonl"
sha = lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()


class ActOverrideTests(unittest.TestCase):
    # Reuse the synthetic corpus fixture without re-running its own tests.
    run_build, dossier = TB.BuildIntegrationTests.run_build, TB.BuildIntegrationTests.dossier

    def setUp(self):
        TB.BuildIntegrationTests.setUp(self)
        rel = "jobs/future-source/data/texts/EO_6.txt"
        (self.repo / rel).write_bytes(EO6.encode("utf-8"))
        prov = self.repo / "jobs/future-source/data/PROVENANCE.json"
        data = json.loads(prov.read_text(encoding="utf-8"))
        digest = sha(EO6)
        data["representations"].append({"instrument_id": "EO:6", "text_path": rel, "kind": "original_representation",
            "acceptable_as_original": True, "signing_date": "1991-03-01",
            "source": {"url": "https://example.gov/EO_6", "sha256": digest, "text_sha256": digest, "page_or_item": "PDF page 1"}})
        write_json(prov, data)
        self.rel6, self.digest6 = rel, digest
        self.target_digest = sha("EXECUTIVE ORDER 1\nThe First Board shall perform the specified duties.\n")
        self.path = self.repo / AO.DIRECTORY / "agent.jsonl"
        self.write_ledger(self.record(), dict(self.record(), id="ACT:EO:1>EO:6@agent2"))

    def write_ledger(self, *records, verdict="upheld"):
        """The reviewer's own ledger: REVIEW.jsonl plus the reviewed records beside it."""
        reviews, upheld = [], []
        for r in records:
            v = r["review"]
            reviews.append({"id": r["id"], "target_id": r["target_id"], "actor_id": r["actor_id"], "verdict": verdict,
                            **{k: v[k] for k in ("reviewer", "review_kind", "d6_searched", "d6_found")}})
            u = {k: x for k, x in r.items() if k not in ("review", "provision_sha256", "target_text_sha256")}
            u["target_naming"] = {k: x for k, x in u["target_naming"].items() if k != "sha256"}
            upheld.append(u)
        write_jsonl(self.repo / LEDGER, reviews)
        write_jsonl(self.repo / LEDGER.replace("REVIEW.jsonl", "UPHELD_ACT_RECORDS.jsonl"), upheld)

    def record(self):
        start = EO6.index("the order of the First Board")
        end = EO6.index("1991.") + len("1991.")
        naming = "numbered 1 in this series"
        n0 = EO6.index(naming)
        return {"id": "ACT:EO:1>EO:6@agent", "target_id": "EO:1", "actor_id": "EO:6", "producer": "agent-producer",
                "actor_source": {"text_path": self.rel6, "text_sha256": self.digest6},
                "char_start": start, "char_end": end, "provision_text": EO6[start:end], "provision_sha256": sha(EO6[start:end]),
                "target_naming": {"char_start": n0, "char_end": n0 + len(naming), "text": naming, "sha256": sha(naming)},
                "verb": "revoke", "scope": "whole", "names_target": True, "reaches_target_via": "",
                "effective_class": "stated_date", "effective_date": "1991-03-03", "effective_wording": [],
                "exceptions_text": [], "savings_phrases": [], "target_text_sha256": self.target_digest,
                "review": {"verdict": "upheld", "independent": True, "reviewer": "agent-reviewer", "review_kind": "AI review, held sources",
                           "d6_searched": "later events on EO 1 and EO 6", "d6_found": "none changes the clause",
                           "source_file": LEDGER}}

    def build_with(self, *records):
        if records:
            write_jsonl(self.path, records)
        self.run_build()
        return json.loads((self.out / "ACT_OVERRIDES_REPORT.json").read_text(encoding="utf-8"))

    def acting(self):
        rows = []
        for p in sorted(self.out.glob("ACTING_PROVISIONS*.jsonl")):
            rows += read_jsonl(p)
        return [r for r in rows if r["target_id"] == "EO:1" and r["actor_id"] == "EO:6"]

    def assert_refused(self, record, code):
        report = self.build_with(record)
        self.assertEqual(report[0]["status"], "refused", report)
        self.assertTrue(any(code in r for r in report[0]["reasons"]), report)
        self.assertEqual(self.acting(), [])
        missing = self.dossier("EO:1")["missing"]
        self.assertIn("target provision not located: EO:6", missing)

    def test_fixture_pair_is_unlocated_without_override(self):
        self.run_build()
        # No override lines: no report file and no extra counts, so the build is unchanged.
        self.assertFalse((self.out / "ACT_OVERRIDES_REPORT.json").exists())
        counts = json.loads((self.out / "SUMMARY.json").read_text(encoding="utf-8"))["counts"]
        self.assertNotIn("act_overrides_ingested", counts)
        self.assertNotIn("act_overrides_refused", counts)
        self.assertIn("target provision not located: EO:6", self.dossier("EO:1")["missing"])
        self.assertTrue(any(r["target_id"] == "EO:1" and r["actor_id"] == "EO:6" for r in read_jsonl(self.out / "MISSING_SOURCES.jsonl")))

    def test_valid_record_ingested_with_provenance(self):
        report = self.build_with(self.record())
        self.assertEqual([r["status"] for r in report], ["ingested"], report)
        (act,) = self.acting()
        self.assertEqual(act["provenance"], "agent_located")
        self.assertEqual(act["id"], "ACT:EO:1>EO:6")
        self.assertEqual(act["override_id"], "ACT:EO:1>EO:6@agent")
        self.assertEqual(act["signing_date"], "1991-03-01")
        self.assertTrue(act["names_target"] and act["scope"] == "whole" and act["verb"] == "revoke")
        dossier = self.dossier("EO:1")
        self.assertNotIn("target provision not located: EO:6", dossier["missing"])
        self.assertIn("ACT:EO:1>EO:6", dossier["actor_provisions"])
        self.assertFalse(any(r["target_id"] == "EO:1" and r["actor_id"] == "EO:6" for r in read_jsonl(self.out / "MISSING_SOURCES.jsonl")))
        self.assertTrue(any(e["actor_id"] == "EO:6" for e in dossier["chain"]["events"]))
        summary = json.loads((self.out / "SUMMARY.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["counts"]["act_overrides_ingested"], 1)

    def test_hash_mismatches_refused(self):
        r = self.record(); r["actor_source"]["text_sha256"] = "0" * 64
        self.assert_refused(r, "actor_text_sha256_mismatch")
        r = self.record(); r["provision_sha256"] = sha("other")
        self.assert_refused(r, "span_sha256_mismatch:provision")
        r = self.record(); r["target_naming"]["sha256"] = sha("other")
        self.assert_refused(r, "span_sha256_mismatch:target_naming")
        r = self.record(); r["target_text_sha256"] = "f" * 64
        self.assert_refused(r, "target_text_sha256_mismatch")

    def test_span_text_that_is_not_the_held_slice_refused(self):
        r = self.record(); r["provision_text"] = r["provision_text"].replace("ended", "continued"); r["provision_sha256"] = sha(r["provision_text"])
        self.assert_refused(r, "span_text_mismatch:provision")
        r = self.record(); r["char_start"] += 1
        self.assert_refused(r, "span_text_mismatch:provision")
        r = self.record(); r["target_naming"]["text"] = "Executive Order 1"; r["target_naming"]["sha256"] = sha("Executive Order 1")
        self.assert_refused(r, "span_text_mismatch:target_naming")
        r = self.record(); r["target_naming"] = dict(r["target_naming"], char_start=0, char_end=17, text=EO6[:17], sha256=sha(EO6[:17]))
        self.assert_refused(r, "target_number_not_in_naming_span")

    def test_unreviewed_refused(self):
        r = self.record(); del r["review"]
        self.assert_refused(r, "missing_field:review")
        r = self.record(); r["review"]["verdict"] = "refuted"
        self.assert_refused(r, "not_upheld")
        r = self.record(); r["review"]["verdict"] = "pending"
        self.assert_refused(r, "not_upheld")
        r = self.record(); r["review"]["independent"] = False
        self.assert_refused(r, "review_not_independent")
        r = self.record(); r["review"]["reviewer"] = r["producer"]
        self.assert_refused(r, "reviewer_is_producer")
        r = self.record(); r["review"]["d6_searched"] = ""
        self.assert_refused(r, "d6_step_missing")

    def test_null_hashes_and_unknown_fields_refused(self):
        r = self.record(); r["provision_sha256"] = None
        self.assert_refused(r, "span_sha256_missing:provision")
        r = self.record(); del r["target_naming"]["sha256"]
        self.assert_refused(r, "span_sha256_missing:target_naming")
        r = self.record(); r["status"] = "revoked"
        self.assert_refused(r, "unknown_field:status")
        r = self.record(); r["effective_class"] = "certain"
        self.assert_refused(r, "bad_effective_class")
        r = self.record(); r["additional_target_namings"] = [{"char_start": 0, "char_end": 5, "text": "XXXXX"}]
        self.assert_refused(r, "span_text_mismatch:additional_target_namings[0]")

    def test_review_must_match_reviewer_ledger(self):
        r = self.record(); r["review"]["source_file"] = "research/excavator/none/review/REVIEW.jsonl"
        self.assert_refused(r, "review_ledger_unreadable")
        r = self.record(); r["review"]["source_file"] = "/etc/REVIEW.jsonl"
        self.assert_refused(r, "review_source_file_invalid")
        r = self.record(); r["review"]["reviewer"] = "someone-else"
        self.assert_refused(r, "review_ledger_mismatch")
        r = self.record(); r["review"]["d6_found"] = "nothing"
        self.assert_refused(r, "review_ledger_mismatch")
        # A field changed after review (spans and hashes still valid) is refused.
        r = self.record(); r["verb"] = "suspend"
        self.assert_refused(r, "changed_after_review:verb")
        r = self.record(); r["effective_date"] = "1991-03-04"
        self.assert_refused(r, "changed_after_review:effective_date")
        r = self.record(); r["id"] = "ACT:EO:1>EO:6@unreviewed"
        self.assert_refused(r, "review_ledger_entry_missing")
        self.write_ledger(self.record(), verdict="refuted")
        self.assert_refused(self.record(), "review_ledger_not_upheld")

    def test_planted_and_seeded_refused(self):
        r = self.record(); r["id"] = "ACT:EO:1>EO:6@SEEDED-01"
        self.assert_refused(r, "seeded_or_planted")
        r = self.record(); r["producer"] = "planted-producer"
        self.assert_refused(r, "seeded_or_planted")
        r = self.record(); r["seeded"] = True
        self.assert_refused(r, "seeded_or_planted")
        r = self.record(); r["review"]["planted"] = True
        self.assert_refused(r, "seeded_or_planted")
        r = self.record(); r["effective_basis"] = "EXAMPLE ONLY"
        self.assert_refused(r, "seeded_or_planted")

    def test_pairs_the_scanner_located_or_cannot_hold_are_refused(self):
        r = self.record(); r["actor_id"] = "EO:5"; r["id"] = "ACT:EO:1>EO:5@agent"
        report = self.build_with(r)
        self.assertEqual(report[0]["reasons"], ["pair_not_unlocated"])
        located = [a for p in self.out.glob("ACTING_PROVISIONS*.jsonl") for a in read_jsonl(p) if a["target_id"] == "EO:1" and a["actor_id"] == "EO:5"]
        self.assertTrue(located and all(a.get("provenance") != "agent_located" for a in located))
        r = self.record(); r["target_id"] = "EO:999"; r["id"] = "ACT:EO:999>EO:6@agent"
        self.assertEqual(self.build_with(r)[0]["reasons"], ["identity_not_in_census"])

    def test_duplicate_pair_refuses_every_line(self):
        second = self.record(); second["id"] = "ACT:EO:1>EO:6@agent2"
        report = self.build_with(self.record(), second)
        self.assertEqual([r["status"] for r in report], ["refused", "refused"])
        self.assertTrue(all(r["reasons"][0] == "duplicate_pair" for r in report), report)
        self.assertEqual(self.acting(), [])
        self.assertIn("target provision not located: EO:6", self.dossier("EO:1")["missing"])
        # The same id twice is refused too, wherever the lines are.
        report = self.build_with(self.record(), self.record())
        self.assertEqual([r["status"] for r in report], ["refused", "refused"])

    def test_stale_report_removed_when_overrides_emptied(self):
        self.assertEqual([r["status"] for r in self.build_with(self.record())], ["ingested"])
        self.path.unlink()
        self.run_build()
        self.assertFalse((self.out / "ACT_OVERRIDES_REPORT.json").exists())
        self.assertEqual(self.acting(), [])

    def test_not_located_example_and_bad_dates_refused(self):
        r = self.record(); r["located"] = False
        self.assert_refused(r, "not_located_record")
        r = self.record(); r["notes"] = "Example only: copied from the pre-gate"
        self.assert_refused(r, "seeded_or_planted")
        r = self.record(); r["producer_d6"] = "EXAMPLE ONLY"
        self.assert_refused(r, "seeded_or_planted")
        r = self.record(); r["effective_date"] = "1991-02-30"
        self.assert_refused(r, "bad_effective_date")

    def test_review_ledger_cannot_sit_in_the_override_directory(self):
        r = self.record(); r["review"]["source_file"] = AO.DIRECTORY + "/x/REVIEW.jsonl"
        self.assert_refused(r, "review_source_file_invalid")
        link = self.repo / "research/excavator/link"
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(self.repo / "jobs", target_is_directory=True)
        r = self.record(); r["review"]["source_file"] = "research/excavator/link/REVIEW.jsonl"
        self.assert_refused(r, "review_source_file_invalid")

    def test_malformed_line_refused_not_crashing(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("{not json\n" + json.dumps(self.record()) + "\n", encoding="utf-8")
        self.run_build()
        report = json.loads((self.out / "ACT_OVERRIDES_REPORT.json").read_text(encoding="utf-8"))
        self.assertEqual([r["status"] for r in report], ["refused", "ingested"])


class NamesNumberTests(unittest.TestCase):
    """Lettered order numbers match their hyphenated, spaced and lowercase forms only."""

    def test_lettered_number_matches_its_written_forms(self):
        for text in ("No. 7975-A of September 16, 1938.", "No. 7975A of", "Order 7975 A,", "order 7975a",
                     "No. 7975-a.", "(7975A)"):
            self.assertTrue(AO.names_number("7975A", text), text)

    def test_lettered_number_rejects_other_numbers_and_letters(self):
        for text in ("No. 7975 of September 16, 1938.", "No. 7975-B", "No. 17975-A", "No. 7975-AB",
                     "No. 79751A", "No. 7975AA", "No. 7975--A", "No. 7975.A"):
            self.assertFalse(AO.names_number("7975A", text), text)

    def test_plain_number_unchanged_but_not_lettered(self):
        for text in ("No. 7975 of September 16, 1938.", "Order 7975,", "Order 7975.", "Order 7975 and later orders"):
            self.assertTrue(AO.names_number("7975", text), text)
        for text in ("No. 7975A of", "No. 7975-A of", "No. 79750", "No. 17975", "No. 7975a,",
                     "No. 7975 A,", "No. 7975  A,", "No. 7975 - A,", "No. 7975AB"):
            self.assertFalse(AO.names_number("7975", text), text)


if __name__ == "__main__":
    unittest.main()
