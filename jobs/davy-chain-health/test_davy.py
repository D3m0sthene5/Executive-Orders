"""Davy's own tests: a failing validator is reported plainly, dependent checks say why they did not run, and the
verdict reaches VERDICT.json for the runner's STATUS."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import davy  # noqa: E402


def ok_population(P, pop):
    return {"universe": 3, "decided": 2, "contract_sha256": "a" * 64, "statuses": {"EO:1": "no", "EO:2": "yes"},
            "id_aliases": {}}


class DavyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.saved = (davy.OUT, davy.DRAFTS, davy.DOSSIERS, davy.REPO)
        davy.OUT = Path(self.tmp.name)

    def tearDown(self):
        davy.OUT, davy.DRAFTS, davy.DOSSIERS, davy.REPO = self.saved
        self.tmp.cleanup()

    def test_every_real_check_takes_validator_and_population(self):
        import inspect
        for name, fn in davy.CHECKS:
            self.assertGreaterEqual(len(inspect.signature(fn).parameters), 2, name)

    def test_pass(self):
        r = davy.run([("population", ok_population), ("drafts", lambda P, pop: "exact")])
        doc = davy.write(r)
        self.assertEqual(doc["verdict"], "pass")
        self.assertEqual(json.loads((davy.OUT / "VERDICT.json").read_text())["verdict"], "pass")

    def test_stale_drafts_named_plainly(self):
        """Haloander break 2: drafts built for 4,291 while the ledger holds 4,301."""
        def stale(P, pop):
            P.require(False, "Draft summary population stale")
        doc = davy.write(davy.run([("population", ok_population), ("drafts", stale)]))
        self.assertEqual(doc["verdict"], "fail")
        self.assertIn("FAIL in drafts", doc["summary"])
        self.assertIn("Draft summary population stale", doc["summary"])
        self.assertIn("| drafts | FAIL |", (davy.OUT / "HEALTH.md").read_text())

    def test_population_failure_marks_dependents(self):
        def bad(P, pop):
            P.require(False, "Census identities changed")
        r = davy.run([("population", bad), ("drafts", lambda P, pop: "x"), ("unit_tests", lambda P, pop: "ok")])
        self.assertEqual([x["result"] for x in r], ["FAIL", "FAIL", "PASS"])
        self.assertIn("not run", r[1]["detail"])

    def test_identity_case_variant_detected(self):
        """Haloander break 3: EO:7933a in one input and EO:7933A in another, with no declared alias."""
        d = Path(self.tmp.name) / "drafts"
        k = Path(self.tmp.name) / "kit"
        d.mkdir(); k.mkdir()
        (d / "DRAFT_CLAIMS.jsonl").write_text(json.dumps({"instrument_id": "EO:7933a"}) + "\n")
        (k / "INDEX.json").write_text(json.dumps([{"instrument_id": "EO:7933A"}]))
        davy.DRAFTS, davy.DOSSIERS = d, k
        sys.path.insert(0, str(davy.KIT))
        import population as P
        pop = {"statuses": {"EO:7933A": "no"}, "id_aliases": {}}
        with self.assertRaises(ValueError) as cm:
            davy.check_identity_case(P, pop)
        self.assertIn("7933", str(cm.exception))
        pop["id_aliases"] = {"EO:7933a": "EO:7933A"}
        self.assertIn("no undeclared", davy.check_identity_case(P, pop))

    def test_declared_path_missing(self):
        root = Path(self.tmp.name)
        (root / "jobs/claim-kit").mkdir(parents=True)
        (root / "jobs/claim-drafts").mkdir(parents=True)
        (root / "jobs/claim-kit/inputs.txt").write_text("research/readiness/owner_rulings/renamed.md\njobs/*/x\n")
        old = davy.REPO
        davy.REPO = root
        try:
            sys.path.insert(0, str(davy.KIT))
            import population as P
            with self.assertRaises(ValueError) as cm:
                davy.check_declarations(P, None)
            self.assertIn("renamed.md", str(cm.exception))
        finally:
            davy.REPO = old


if __name__ == "__main__":
    unittest.main()
