"""Machine-lead transport regressions; no test supplies a legal status verdict."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import excavate as E
import test_build as TB

SOURCE = {"text_path": "held/actor.txt", "text_sha256": "a" * 64}
RESTORE = ("Executive Order 1 is hereby reinstated as it was prior to the issuance "
           "of Executive Order 2.")


class ReinstatementExtractionTests(unittest.TestCase):
    def test_historical_revoker_is_not_reinstated(self):
        acts, refs = E.discover_mentions("EO:9", RESTORE, SOURCE, with_references=True)
        self.assertEqual([(a["target_id"], a["verb"]) for a in acts], [("EO:1", "reinstate")])
        self.assertEqual([r["target_id"] for r in refs], ["EO:2"])
        self.assertEqual(acts[0]["provision_text"], RESTORE)
        self.assertIsNone(acts[0]["effective_date"])
        self.assertIn("no date, duration, expired obligation or earlier gap is reset", acts[0]["notes"])

    def test_same_actor_retains_reinstatement_and_separate_amendment(self):
        text = RESTORE + "\nSection 3(c)(ii) of Executive Order 1 is amended by striking a date."
        acts = E.discover_mentions("EO:9", text, SOURCE, signing_date="2025-01-29")
        self.assertEqual([(a["target_id"], a["verb"], a["scope"]) for a in acts],
                         [("EO:1", "reinstate", "whole"), ("EO:1", "amend", "partial")])
        self.assertEqual(len({a["id"] for a in acts}), 2)
        for a in acts:
            self.assertEqual(text[a["char_start"]:a["char_end"]], a["provision_text"])
            self.assertIsNone(a["effective_date"])
        self.assertEqual([e["verb"] for e in E.chain("EO:1", acts)["events"]], ["reinstate", "amend"])

    def test_same_sentence_different_targets_do_not_cross_bind(self):
        text = "Executive Order 1 is reinstated, and Executive Order 2 is amended."
        acts = E.discover_mentions("EO:9", text, SOURCE)
        self.assertEqual([(a["target_id"], a["verb"]) for a in acts],
                         [("EO:1", "reinstate"), ("EO:2", "amend")])

    def test_mixed_transfer_remains_target_scoped_without_cross_binding(self):
        clauses = ["Executive Order 1 is reinstated",
                   "functions under Executive Order 2 are transferred to the Secretary of State"]
        for text in [", and ".join(clauses) + ".", " and ".join(clauses) + ".",
                     "; ".join(reversed(clauses)) + ".", " and ".join(reversed(clauses)) + ".",
                     "Executive Order 1 is reinstated and Executive Order 2 is transferred to the Secretary of State.",
                     "Executive Order 1 is reinstated and I hereby transfer functions under Executive Order 2 to the Secretary of State."]:
            with self.subTest(text=text):
                acts = E.discover_mentions("EO:9", text, SOURCE)
                self.assertEqual([(a["target_id"], a["verb"]) for a in acts],
                                 [("EO:1", "reinstate"), ("EO:2", "transfer")])
                self.assertEqual([e["verb"] for e in E.chain("EO:1", acts)["events"]], ["reinstate"])
                self.assertEqual([e["verb"] for e in E.chain("EO:2", acts)["events"]], ["transfer"])
                for act in acts:
                    self.assertEqual(text[act["char_start"]:act["char_end"]], act["provision_text"])
                transfer = acts[1]
                self.assertNotIn("Executive Order 1", transfer["provision_text"])
        negated = ", and ".join(clauses).replace("are transferred", "are not transferred") + "."
        self.assertEqual(E.chain("EO:2", E.discover_mentions("EO:9", negated, SOURCE))["events"], [])

    def test_bare_join_preserves_transfer_target_list_suffixes(self):
        text = ("Executive Order 1 is reinstated and functions under Executive Orders 2A and 2½ "
                "are transferred to the Secretary of State.")
        acts = E.discover_mentions("EO:9", text, SOURCE)
        self.assertEqual([(a["target_id"], a["verb"]) for a in acts],
                         [("EO:1", "reinstate"), ("EO:2A", "transfer"), ("EO:2½", "transfer")])
        self.assertIsNone(E.acting_provision("EO:2", "EO:9", text, SOURCE))

    def test_mixed_transfer_join_keeps_reinstated_target_list(self):
        text = ("Executive Orders 1 and 2 are reinstated, and functions under Executive Order 3 "
                "are transferred to the Secretary of State.")
        acts = E.discover_mentions("EO:9", text, SOURCE)
        self.assertEqual([(a["target_id"], a["verb"]) for a in acts],
                         [("EO:1", "reinstate"), ("EO:2", "reinstate"), ("EO:3", "transfer")])

    def test_mixed_same_target_keeps_both_reinstatement_and_transfer(self):
        text = ("Executive Order 1 is reinstated, and functions under Executive Order 1 "
                "are transferred to the Secretary of State.")
        acts = E.discover_mentions("EO:9", text, SOURCE)
        self.assertEqual([a["verb"] for a in acts], ["reinstate", "transfer"])
        self.assertEqual([e["verb"] for e in E.chain("EO:1", acts)["events"]], ["reinstate", "transfer"])

    def test_plural_suffix_partial_and_exception_are_preserved(self):
        text = "The prohibitions of Executive Orders 1A and 1½ are hereby reinstated except as to pending cases."
        acts = E.discover_mentions("EO:9", text, SOURCE)
        self.assertEqual({a["target_id"] for a in acts}, {"EO:1A", "EO:1½"})
        self.assertEqual({a["verb"] for a in acts}, {"reinstate"})
        self.assertTrue(all(a["scope"] == "partial" and a["exceptions_text"] for a in acts))
        self.assertIsNone(E.acting_provision("EO:1", "EO:9", text, SOURCE))

    def test_negation_historical_descriptor_and_generic_do_not_create_events(self):
        for text in ["Executive Order 1 is not reinstated.",
                     "Executive Order 1 has never been reinstated.",
                     "Nothing shall be construed to reinstate Executive Order 1.",
                     "Executive Order 1, as reinstated, establishes a board.",
                     "All prior orders are reinstated."]:
            with self.subTest(text=text):
                self.assertEqual(E.chain("EO:1", E.discover_mentions("EO:9", text, SOURCE))["events"], [])

    def test_chain_expands_existing_alternatives_once(self):
        text = RESTORE + " Executive Order 1 is amended."
        acts = E.discover_mentions("EO:9", text, SOURCE)
        primary = deepcopy(acts[0])
        primary["alternative_provisions"] = deepcopy(acts + [acts[0]])
        unrelated = deepcopy(acts[0]); unrelated["target_id"] = "EO:3"
        primary["alternative_provisions"].append(unrelated)
        events = E.chain("EO:1", [primary])["events"]
        self.assertEqual([e["verb"] for e in events], ["reinstate", "amend"])
        self.assertTrue(all("chronology does not decide legal effect" in e["notes"] for e in events))

    def test_later_reinstatement_does_not_restart_an_original_fixed_term(self):
        text = "Sec. 5. This section shall terminate 6 months from the date of this order unless extended by the President."
        source = dict(SOURCE, signing_date="2020-06-26")
        terms = E.own_terms("EO:1", text, source, E.segment("EO:1", text, source))
        fixed = next(t for t in terms if t["kind"] == "fixed_term")
        self.assertEqual(fixed["computed_end_candidate"], "2020-12-26")
        acts = E.discover_mentions("EO:9", RESTORE, SOURCE, signing_date="2025-01-29")
        E.chain("EO:1", acts)
        self.assertEqual(terms, E.own_terms("EO:1", text, source, E.segment("EO:1", text, source)))
        self.assertEqual(fixed["computed_end_candidate"], "2020-12-26")
        self.assertIsNone(acts[0]["effective_date"])

    def test_held_eo14189_four_distinct_operations_and_unchanged_target_terms(self):
        root = HERE.parents[1]
        path = root / "jobs/fr-originals/data/full_run/texts/EO_14189.txt"
        if not path.is_file():
            self.skipTest("held EO14189 text not materialized")
        text = path.read_text(encoding="utf-8")
        acts = E.discover_mentions("EO:14189", text, SOURCE, signing_date="2025-01-29")
        self.assertEqual([(a["target_id"], a["verb"]) for a in acts],
                         [("EO:13933", "reinstate"), ("EO:13934", "reinstate"),
                          ("EO:13934", "amend"), ("EO:13978", "reinstate")])
        for a in acts:
            self.assertEqual(text[a["char_start"]:a["char_end"]], a["provision_text"])
            self.assertIsNone(a["effective_date"])
        self.assertEqual([a["scope"] for a in acts], ["whole", "whole", "partial", "whole"])
        for target in ("13933", "13934", "13978"):
            target_path = path.with_name("EO_" + target + ".txt")
            target_text = target_path.read_text(encoding="utf-8")
            clauses = E.segment("EO:" + target, target_text, SOURCE)
            before = E.own_terms("EO:" + target, target_text, SOURCE, clauses)
            E.chain("EO:" + target, acts)
            self.assertEqual(E.own_terms("EO:" + target, target_text, SOURCE, clauses), before)


class ReinstatementBuildTransportTests(unittest.TestCase):
    setUp = TB.BuildIntegrationTests.setUp
    run_build = TB.BuildIntegrationTests.run_build
    dossier = TB.BuildIntegrationTests.dossier

    def test_existing_dossier_alternatives_and_chain_keep_both_operations(self):
        text = "EXECUTIVE ORDER 5\n" + RESTORE + "\nSection 3(c)(ii) of Executive Order 1 is amended.\n"
        path = self.repo / "jobs/future-source/data/texts/EO_5.txt"
        path.write_text(text, encoding="utf-8")
        prov_path = self.repo / "jobs/future-source/data/PROVENANCE.json"
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        row = next(r for r in prov["representations"] if r["instrument_id"] == "EO:5")
        row["source"]["sha256"] = row["source"]["text_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        TB.write_json(prov_path, prov)
        self.run_build()
        dossier = self.dossier("EO:1")
        self.assertEqual([e["verb"] for e in dossier["chain"]["events"]], ["reinstate", "amend"])
        carried = [v for k, v in dossier["evidence"].items()
                   if k.startswith("ACT:") and v.get("actor_id") == "EO:5"]
        self.assertEqual({a["verb"] for a in carried}, {"reinstate", "amend"})
        self.assertEqual(TB.read_jsonl(self.out / "ASSEMBLED_CLAIMS.jsonl"), [])
        self.assertEqual(row["acceptable_as_original"], True)


if __name__ == "__main__":
    unittest.main()
