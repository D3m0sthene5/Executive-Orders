"""Offline tests for the Pothier engine: python3 -I jobs/pothier/test_pothier.py"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pothier  # noqa: E402


def doctrine(**over):
    d = {
        "schema": pothier.SCHEMA, "doctrine_id": "PD-TEST", "family": "test", "version": 1,
        "members": {"field": "x1_type", "in": ["t"]},
        "mechanisms": [{"id": "M1", "kind": "own_terms", "effect": "ends", "description": "d",
                        "effective_date_rule": "r", "source_ids": ["S1"]}],
        "sources": [{"id": "S1", "citation": "1 Stat. 1", "held": False, "url": "https://example.gov/x"}],
        "procedure": [
            {"branch_id": "B1", "when": [{"text_regex": r"period of (\w+) years"}],
             "lead": {"status_lead": "no", "lead_kind": "ended_on_own_terms", "basis_kind": "TERM",
                      "basis": "own stated period", "mechanism_ids": ["M1"], "source_ids": ["S1"],
                      "date_rule": {"kind": "order_date_plus_years", "regex": r"period of (\w+) years"}},
             "gaps": []},
            {"branch_id": "B2", "when": [{"mechanism_in": ["revocation"]}],
             "lead": {"status_lead": "no", "lead_kind": "ended_by_later_instrument", "basis_kind": "ACT",
                      "basis": "held revocation edge", "date_rule": {"kind": "edge_date"}}, "gaps": []},
            {"branch_id": "B9", "when": [],
             "lead": {"status_lead": "open", "lead_kind": "persists_no_end_found", "basis_kind": "NONE",
                      "basis": "no end found"}, "gaps": ["needs land records"]},
        ],
    }
    d.update(over)
    return d


def member(iid, text="", **over):
    m = {"instrument_id": iid, "x1_type": "t", "date": "1910-06-25", "title": "", "wpa_summary": "",
         "primary_text_path": "", "primary_text_grade": "official", "later_edges": [], "name_later_hits": [],
         "current_law": {}, "_text": text}
    m.update(over)
    return m


class Engine(unittest.TestCase):
    def setUp(self):
        self._orig = pothier.member_text
        pothier.member_text = lambda m: m.get("_text", "")

    def tearDown(self):
        pothier.member_text = self._orig

    def test_validate_ok(self):
        self.assertEqual(pothier.validate(doctrine()), [])

    def test_validate_rejects_yes_without_current(self):
        d = doctrine()
        d["procedure"][0]["lead"]["status_lead"] = "yes"
        self.assertTrue(any("CURRENT" in e for e in pothier.validate(d)))

    def test_validate_rejects_no_without_ending_basis(self):
        d = doctrine()
        d["procedure"][0]["lead"]["basis_kind"] = "NONE"
        self.assertTrue(any("TERM or ACT" in e for e in pothier.validate(d)))

    def test_validate_needs_catch_all_and_known_ids(self):
        d = doctrine()
        d["procedure"] = d["procedure"][:2]
        d["procedure"][0]["lead"]["source_ids"] = ["S9"]
        errs = pothier.validate(d)
        self.assertTrue(any("catch-all" in e for e in errs))
        self.assertTrue(any("unknown source S9" in e for e in errs))

    def test_held_source_path_must_exist(self):
        d = doctrine()
        d["sources"][0].update(held=True, held_path="no/such/file.txt")
        self.assertTrue(any("does not exist" in e for e in pothier.validate(d)))

    def test_own_terms_period_and_gap_for_unheld_source(self):
        r = pothier.decide(member("EO:1", "trust extended for a period of ten years"), doctrine())
        self.assertEqual((r["branch_id"], r["status_lead"], r["date"]["date"]), ("B1", "no", "1920-06-25"))
        self.assertTrue(any("not yet held" in g for g in r["gaps"]))
        self.assertTrue(r["decides"])

    def test_edge_branch_uses_earliest_edge(self):
        m = member("EO:2", later_edges=[{"edge_id": "E2", "mechanism": "revocation", "date_candidate": "1950-01-01"},
                                        {"edge_id": "E1", "mechanism": "revocation", "date_candidate": "1940-01-01"}])
        r = pothier.decide(m, doctrine())
        self.assertEqual((r["branch_id"], r["date"]["date"]), ("B2", "1940-01-01"))

    def test_catch_all_open_and_persistence_contradiction(self):
        d = doctrine()
        d["procedure"].pop(1)
        m = member("EO:3", later_edges=[{"edge_id": "E1", "mechanism": "revocation", "date_candidate": "1940-01-01"}])
        r = pothier.decide(m, d)
        self.assertEqual(r["status_lead"], "open")
        self.assertFalse(r["decides"])
        self.assertEqual(r["contradictions"][0]["kind"], "persistence_lead_but_held_ending_edge")

    def test_acted_on_after_end_is_a_contradiction(self):
        m = member("EO:4", "for a period of two years",
                   later_edges=[{"edge_id": "E1", "mechanism": "amendment", "date_candidate": "1930-01-01"}])
        r = pothier.decide(m, doctrine())
        self.assertEqual(r["contradictions"][0]["kind"], "acted_on_after_lead_end")

    def test_non_member_and_logic(self):
        self.assertIsNone(pothier.decide(member("EO:5", x1_type="other"), doctrine()))
        c = {"all_of": [{"field": "date", "gte": "1910"}, {"not": {"field": "date", "lt": "1900-01-01"}}]}
        self.assertTrue(pothier.holds(member("EO:6"), c, {}))
        self.assertFalse(pothier.holds(member("EO:6", date=""), {"field": "date", "gte": "1900"}, {}))

    def test_run_coverage_and_determinism(self):
        ms = [member("EO:1", "for a period of ten years"), member("EO:3"), member("EO:7", x1_type="other")]
        docs = [(Path("x.json"), doctrine())]
        a = pothier.run(ms, docs)
        b = pothier.run(list(reversed(ms)), docs)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        cov = pothier.coverage(ms, a, docs)
        self.assertEqual((cov["covered_by_a_doctrine"], cov["no_doctrine"], cov["decides_total"]), (2, 1, 1))
        with tempfile.TemporaryDirectory() as t:
            pothier.write_outputs(Path(t), a, cov, [(pothier.REPO / "x.json", doctrine())])
            self.assertTrue((Path(t) / "LEADS.jsonl").read_text().count("\n") == 2)

    def test_word_numbers(self):
        d = doctrine()
        d["procedure"][0]["when"] = [{"text_regex": r"period of ([\w-]+) years"}]
        d["procedure"][0]["lead"]["date_rule"]["regex"] = r"period of ([\w-]+) years"
        r = pothier.decide(member("EO:8", "for a period of twenty-five years"), d)
        self.assertEqual(r["date"]["date"], "1935-06-25")

    def test_committed_doctrines_validate(self):
        for p in sorted(pothier.DOCTRINES.glob("*.json")):
            with open(p) as f:
                self.assertEqual(pothier.validate(json.load(f)), [], str(p))


if __name__ == "__main__":
    unittest.main()
