"""Independent regression cases for whole-head evidence and source boundaries."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build
import current_evidence
import inputs
import population


class WholeHeadReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.corpus = {"universe": {f"EO:{n}": {} for n in (1, 2, 3)},
                       "statuses": {f"EO:{n}": "no" for n in (1, 2, 3)},
                       "texts": [], "pairs": [], "drafts": {},
                       "current_law": {}, "machine_searches": {}, "warnings": []}

    def text(self, iid, filename, text, original=True):
        path = self.repo / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        source = {"url": "https://example.gov/" + filename,
                  "sha256": hashlib.sha256(text.encode()).hexdigest(),
                  "page_or_item": "PDF page 1", "text_path": filename,
                  "text_sha256": hashlib.sha256(text.encode()).hexdigest()}
        self.corpus["texts"].append({"instrument_id": iid, "text_path": filename,
                                     "source": source, "grade": "original" if original else "derivative_lead",
                                     "acceptable_as_original": original,
                                     "signing_date": "2000-01-01", "filing_date": None})

    def run_build(self):
        out = self.repo / "result"
        with patch.object(build, "load_corpus", return_value=self.corpus):
            build.build(self.repo, out)
        return out

    def test_nonselected_text_own_terms_are_not_lost(self):
        self.text("EO:1", "a.txt", "I hereby establish a board.")
        self.text("EO:1", "z.txt", "The board continues for four years from January 1, 2000.", False)
        out = self.run_build()
        records = [json.loads(s) for s in (out / "OWN_TERMS.jsonl").read_text().splitlines()]
        self.assertTrue(any(r["computed_end_candidate"] == "2004-01-01" for r in records))
        dossier = json.loads((out / "dossiers/EO_1.json").read_text())
        self.assertTrue(dossier["own_terms"])

    def test_one_contract_act_record_per_target_actor(self):
        self.text("EO:1", "one.txt", "Executive Order 3 is amended by adding an office.")
        self.text("EO:3", "three.txt", "I hereby establish these offices.")
        self.text("EO:2", "two.txt", "Executive Orders 1 and 3, as amended, are revoked.")
        self.corpus["pairs"] = [{"target_id": "EO:1", "actor_id": "EO:2", "parent_id": "EO:3"}]
        out = self.run_build()
        records = [json.loads(s) for s in (out / "ACTING_PROVISIONS.jsonl").read_text().splitlines()]
        ids = [r["id"] for r in records]
        self.assertEqual(len(ids), len(set(ids)))

    def test_parent_route_never_reaches_a_future_amender(self):
        self.text('EO:1','one.txt','Executive Order 3 is amended by adding an office.')
        self.corpus['texts'][-1]['signing_date']='2005-01-01'
        self.text('EO:3','three.txt','I hereby establish these offices.')
        self.corpus['texts'][-1]['signing_date']='1990-01-01'
        self.text('EO:2','two.txt','Executive Order 3, as amended, is revoked.')
        self.corpus['texts'][-1]['signing_date']='2001-01-01'
        out=self.run_build()
        records=[json.loads(s) for s in (out/'ACTING_PROVISIONS.jsonl').read_text().splitlines()]
        self.assertFalse(any(r['target_id']=='EO:1' and r['actor_id']=='EO:2' for r in records))

    def test_unlocated_known_provision_keeps_held_actor_context(self):
        self.text('EO:1','one.txt','I hereby establish a board.')
        self.text('EO:2','two.txt','I hereby revoke the earlier board direction.')
        self.corpus['pairs']=[{'target_id':'EO:1','actor_id':'EO:2'}]
        out=self.run_build()
        d=json.loads((out/'dossiers/EO_1.json').read_text())
        self.assertEqual(d['actor_provisions'],[])
        self.assertIn('ACTOR_TEXT:EO:2',d['evidence'])
        self.assertTrue(any('not located' in x for x in d['missing']))

    def test_page_label_aliases_are_preserved_without_repeating_extraction(self):
        from copy import deepcopy
        self.text('EO:1','one.txt','I hereby establish a board for four years from January 1, 2000.')
        alias=deepcopy(self.corpus['texts'][0]);alias['source']['page_or_item']='PDF page 1; clause 2'
        self.corpus['texts'].append(alias)
        out=self.run_build();summary=json.loads((out/'SUMMARY.json').read_text())
        self.assertEqual(summary['counts']['declared_text_representations'],2)
        self.assertEqual(summary['counts']['held_texts_scanned'],1)
        self.assertEqual(len((out/'TEXT_REPRESENTATIONS.jsonl').read_text().splitlines()),2)
        self.assertEqual(len((out/'TEXT_CLAUSES.jsonl').read_text().splitlines()),1)

    def test_nonselected_generic_reference_is_counted(self):
        self.text("EO:1", "a.txt", "I hereby establish a board.")
        self.text("EO:1", "z.txt", "All prior orders are revoked.", False)
        out = self.run_build()
        self.assertEqual(json.loads((out / "SUMMARY.json").read_text())["counts"]["generic_references_excluded"], 1)


class CurrentLawEvidenceReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.source = {"url": "https://example.gov/current.xml", "sha256": "a" * 64, "page_or_item": "section 1"}

    def write(self, name, text):
        path = self.repo / "jobs/current-law/output" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_exact_legal_text_slice_is_normalized_without_currency_upgrade(self):
        text = "Section 1. Powers under Executive Order 1 continue.\r\n"
        path = self.write("current.txt", text)
        lead = {"text_path": "current.txt", "snippet": "Powers under Executive Order 1 continue.",
                "checked_through": "2026-10-09", "source": self.source}
        result = current_evidence.enrich_current(self.repo, [lead])[0]
        raw = path.read_bytes().decode()
        self.assertEqual(raw[result["char_start"]:result["char_end"]], result["text"])
        self.assertEqual(result["checked_through"], "2026-10-09")
        self.assertEqual(result["source"]["text_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertNotIn("text", lead)

    def test_serialized_note_never_becomes_legal_quote(self):
        self.write("USC_EO_NOTES.jsonl", json.dumps({"note_id": "n", "text": "The powers continue."}) + "\n")
        lead = {"source": self.source, "snippet": "The powers continue.", "text_path": "USC_EO_NOTES.jsonl#note_id=n"}
        result = current_evidence.enrich_current(self.repo, [lead])[0]
        self.assertIn("evidence_gap", result)
        self.assertNotIn("text", result)
        self.assertNotIn("char_start", result)

    def test_missing_and_unsafe_pointers_remain_explicit_gaps(self):
        for pointer in ["missing.txt", "../../../../outside.txt", "/etc/passwd", "https://example.gov/file.txt"]:
            result = current_evidence.enrich_current(self.repo, [{"source": self.source, "text_path": pointer, "snippet": "Powers."}])[0]
            self.assertIn("evidence_gap", result)
            self.assertNotIn("text", result)

    def test_wrong_hash_and_ambiguous_snippet_are_not_evidence(self):
        self.write("current.txt", "Repeated. Repeated.")
        lead = {"source": self.source, "text_path": "current.txt", "snippet": "Repeated."}
        self.assertIn("evidence_gap", current_evidence.enrich_current(self.repo, [lead])[0])
        self.write("single.txt", "Unique.")
        lead = {"source": dict(self.source, text_sha256="f" * 64), "text_path": "single.txt", "snippet": "Unique."}
        self.assertIn("evidence_gap", current_evidence.enrich_current(self.repo, [lead])[0])


class CommittedBaselineReviewTests(unittest.TestCase):
    def test_historical_fixture_and_current_accepted_population(self):
        repo = Path(__file__).resolve().parents[2]
        census, status = repo / inputs.UNIVERSE, repo / inputs.STATUSES
        if not census.is_file() or not status.is_file():
            self.skipTest("Full committed baseline metadata is absent from this synthetic checkout")
        checked = population.validate_inputs(repo)
        # The historical 3,359 pin remains a fixture, not a ceiling on current
        # owner-adopted inputs. The independent contract checks exact rows,
        # census membership, duplicates, ruling/review pins and accepted deltas.
        self.assertEqual(checked["historical_decided"], 3359)
        self.assertEqual(checked["universe"], 14972)
        self.assertEqual(checked["decided"],
                         checked["historical_decided"] + checked["authorized_additions"])
        # Existing outputs may be stale precisely because this pre-build test
        # used to fail. job.py validates exact derived coverage after rebuilding.


if __name__ == "__main__":
    unittest.main()
