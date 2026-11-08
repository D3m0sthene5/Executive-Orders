"""Offline tests for measure.py, using small fixtures that copy the real file shapes."""
import csv
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M  # noqa: E402

USAGE_COLS = ["agent_id", "role", "phase", "batch", "model", "fresh_input", "cache_read", "cache_write_5m",
              "cache_write_1h", "cache_write_unclassified", "output"]


def write(root: Path, rel: str, text: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def build(root: Path, with_usage_model=True):
    # a01: 4 orders (2 filed), o01: 3 orders (3 filed), c01: 2 orders (1 filed), o02 never tallied
    ids = {"a01": ["EO:7531", "EO:7532", "EO:10026A", "EO:9000"],
           "o01": ["EO:8000", "EO:10100", "EO:106½"],
           "c01": ["EO:8001", "EO:8002"], "o02": ["EO:1"]}
    disp = {"schema": "tribonian-disposition/v1", "batches": [
        {"batch": "a01", "attempted": 4, "claims_filed": 2, "state": "completed",
         "blind_review_verdicts": {"upheld": 2, "rejected": 2},
         "not_filed": [{"instrument_id": "EO:7531", "outcome": "blocked", "reason": "x"},
                       {"instrument_id": "EO:9000", "outcome": "rejected_mechanical", "reason": ""}]},
        {"batch": "o01", "attempted": 3, "claims_filed": 3, "state": "completed",
         "blind_review_verdicts": {"upheld": 3}, "not_filed": []},
        {"batch": "c01", "attempted": 2, "claims_filed": 1, "state": "completed",
         "blind_review_verdicts": {"upheld": 1},
         "not_filed": [{"instrument_id": "EO:8002", "outcome": "blocked", "reason": "y"}]},
        {"batch": "o02", "attempted": None, "claims_filed": 0, "state": "prepared_not_started",
         "blind_review_verdicts": {}}], "totals": {"claims_filed": 6, "batches": 4}}
    base = M.WAVE_DIR
    write(root, M.DISPOSITION, json.dumps(disp, indent=1))
    write(root, M.BATCHES, json.dumps(ids, indent=1))
    write(root, M.SUMMARY, "{}")
    status = {"EO:7531": "yes", "EO:7532": "yes", "EO:10026A": "no", "EO:9000": "no",
              "EO:8000": "no", "EO:10100": "", "EO:106½": "yes", "EO:8001": "no", "EO:8002": "no"}
    p = root / M.READINESS
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["instrument_id", "provisional_status", "decision_origin"])
        for k, v in status.items():
            w.writerow([k, v, ""])
    rows = [
        ["p1", "producer", "production", "a01", "claude-sonnet-5-5", 100, 1000000, 500000, 0, 0, 200000],
        ["p2", "producer", "production", "o01", "claude-sonnet-5-5", 0, 0, 0, 1000000, 0, 0],
        ["p3", "producer", "production", "o02", "claude-sonnet-5-5", 50, 50, 50, 0, 0, 50],
        ["r1", "reviewer", "review", "a01+o01", "claude-opus-5-5" if with_usage_model else "",
         0, 2000000, 0, 0, 0, 100000],
        ["r2", "reviewer", "review", "lind-a03-A", "claude-opus-5-5", 9, 9, 9, 0, 0, 9],
        ["k1", "coordinator", "coordination", "", "claude-opus-5-5", 0, 0, 0, 0, 0, 1000000],
        ["c1", "correction_producer", "correction", "c01", "claude-sonnet-5-5", 0, 0, 0, 0, 0, 1000000],
    ]
    p = root / M.USAGE
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(USAGE_COLS)
        w.writerows(rows)


class T(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        build(self.root)
        self.m = M.measure(self.root)
        self.rate = {r["key"]: r for r in self.m["rates"]}

    def tearDown(self):
        self.td.cleanup()

    def test_era_and_suffix(self):
        self.assertEqual(M.era_of("EO:7531"), "prefr")
        self.assertEqual(M.era_of("EO:7532"), "fr")
        self.assertEqual(M.era_of("EO:10026A"), "fr")
        self.assertEqual(M.era_of("EO:106½"), "prefr")
        self.assertEqual(M.eo_number("EO:106-1"), 106)
        self.assertIsNone(M.era_of("junk"))

    def test_stratification(self):
        r = self.rate
        # yes.prefr: 7531 (not filed), 106 1/2 (filed) ; yes.fr: 7532 (filed)
        self.assertEqual((r["filed_per_attempt.yes.prefr"]["num"], r["filed_per_attempt.yes.prefr"]["den"]), (1, 2))
        self.assertEqual((r["filed_per_attempt.yes.fr"]["num"], r["filed_per_attempt.yes.fr"]["den"]), (1, 1))
        # no.fr: 10026A filed, 9000 not, 8000 filed
        self.assertEqual((r["filed_per_attempt.no.fr"]["num"], r["filed_per_attempt.no.fr"]["den"]), (2, 3))
        self.assertEqual(r["filed_per_attempt.no.prefr"]["den"], 0)
        self.assertIsNone(r["filed_per_attempt.no.prefr"]["value"])
        # all excludes correction batch and untallied batch; blank-status order 10100 counts in all only
        self.assertEqual((r["filed_per_attempt.all"]["num"], r["filed_per_attempt.all"]["den"]), (5, 7))
        self.assertAlmostEqual(r["filed_per_attempt.all"]["value"], 5 / 7)
        self.assertEqual((r["filed_per_attempt.correction"]["num"], r["filed_per_attempt.correction"]["den"]), (1, 2))
        for x in self.m["rates"]:
            self.assertEqual(x["unit"], "share")
            self.assertEqual(x["population"], M.WAVE)
            self.assertEqual(x["n_studies"], 1)

    def test_waves(self):
        w = self.m["waves"][0]
        self.assertEqual((w["attempted"], w["filed"]), (9, 6))
        self.assertEqual((w["production_attempted"], w["production_filed"]), (7, 5))

    def test_cost_arithmetic(self):
        c = self.m["costs"]
        # production: p1 sonnet = (100*3 + 200000*15 + 1e6*.3 + 5e5*3.75)/1e6 ; p2 = 1e6*3.75/1e6
        p1 = (100 * 3 + 200000 * 15 + 1_000_000 * 0.30 + 500_000 * 3.75) / 1e6
        self.assertAlmostEqual(c["production.per_attempt"]["total_usd"], p1 + 3.75)
        self.assertEqual(c["production.per_attempt"]["denominator"], 7)  # o02 untallied, excluded
        self.assertAlmostEqual(c["production.per_attempt"]["usd"], (p1 + 3.75) / 7)
        rv = (2_000_000 * 0.50 + 100_000 * 25) / 1e6  # opus; lind arm excluded
        self.assertAlmostEqual(c["review.per_submitted"]["total_usd"], rv)
        self.assertEqual(c["review.per_submitted"]["denominator"], 7)  # verdicts 4 + 3, not c01's 1
        self.assertAlmostEqual(c["coordination.per_attempt"]["usd"], 25.0 / 7)
        share = 7 / 7
        expect = c["production.per_attempt"]["usd"] + c["review.per_submitted"]["usd"] * share \
            + c["coordination.per_attempt"]["usd"]
        self.assertAlmostEqual(c["wave.per_attempt"]["usd"], expect)
        self.assertAlmostEqual(c["wave.per_filed_dossier"]["usd"], c["wave.per_attempt"]["total_usd"] / 5)
        self.assertAlmostEqual(c["correction.per_attempt"]["usd"], 15.0 / 2)
        self.assertEqual(c["review.per_submitted"]["tokens"]["cache_read"], 2_000_000)
        self.assertEqual(c["production.per_attempt"]["tokens"]["cache_write"], 500_000 + 1_000_000)
        self.assertEqual(self.m["price_table"]["sonnet"]["cache_write"], 3.75)
        self.assertTrue(self.m["price_table"]["source"].startswith("assumption"))

    def test_family_fallback_by_phase(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            build(root, with_usage_model=False)
            c = M.measure(root)["costs"]
            self.assertAlmostEqual(c["review.per_submitted"]["total_usd"], (2_000_000 * 0.50 + 100_000 * 25) / 1e6)
            self.assertIn("inferred from phase", c["review.per_submitted"]["basis"])

    def test_evidence_quotes_present(self):
        for r in self.m["rates"]:
            self.assertTrue(r["evidence"])
            for e in r["evidence"]:
                txt = (self.root / e["source"]).read_text(encoding="utf-8")
                self.assertIn(re.sub(r"\s+", "", e["quote"]), re.sub(r"\s+", "", txt))

    def test_missing_file_is_clear_error(self):
        for rel in (M.DISPOSITION, M.READINESS, M.USAGE, M.BATCHES):
            with tempfile.TemporaryDirectory() as t:
                root = Path(t)
                build(root)
                (root / rel).unlink()
                with self.assertRaises(M.MeasureError) as cm:
                    M.measure(root)
                self.assertIn(rel, str(cm.exception))

    def test_mismatch_is_error_not_guess(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            build(root)
            ids = json.loads((root / M.BATCHES).read_text())
            ids["a01"].pop()
            (root / M.BATCHES).write_text(json.dumps(ids))
            with self.assertRaises(M.MeasureError):
                M.measure(root)

    def test_other_waves_and_skipped(self):
        write(self.root, "research/excavator/odd/DISPOSITION.json", json.dumps({"rows": []}))
        write(self.root, "research/excavator/other/evidence/DISPOSITION.json", json.dumps(
            {"batches": [{"batch": "z1", "attempted": 5, "claims_filed": 2}]}))
        m = M.measure(self.root)
        self.assertEqual([w["wave"] for w in m["waves"]], [M.WAVE, "other"])
        self.assertEqual(m["waves"][1]["attempted"], 5)
        self.assertEqual(len(m["skipped"]), 1)
        self.assertIn("odd", m["skipped"][0]["source"])

    def test_undecided_measure_sets_undecided_rate(self):
        r = {x["key"]: x for x in M.measure(self.root)["rates"]}
        self.assertNotIn("filed_per_attempt.undecided", r)
        write(self.root, "research/excavator/probe/evidence/DISPOSITION.json", json.dumps(
            {"batches": [{"batch": "u", "attempted": 30, "claims_filed": 3}],
             "undecided_measure": {"attempted": 30, "filed": 3}}, indent=1))
        m = M.measure(self.root)
        u = {x["key"]: x for x in m["rates"]}["filed_per_attempt.undecided"]
        self.assertEqual((u["num"], u["den"]), (3, 30))
        self.assertAlmostEqual(u["value"], 0.1)
        self.assertTrue(u["evidence"])

    def test_pooling_is_opt_in(self):
        disp = {"schema": "tribonian-disposition/v1", "batches": [
            {"batch": "no", "attempted": 2, "claims_filed": 1, "state": "completed",
             "blind_review_verdicts": {"upheld": 1},
             "not_filed": [{"instrument_id": "EO:9000", "outcome": "blocked", "reason": "z"}]},
            {"batch": "rc", "kind": "correction", "attempted": 1, "claims_filed": 1, "state": "completed",
             "not_filed": []}]}
        write(self.root, "research/excavator/core/evidence/DISPOSITION.json", json.dumps(disp))
        write(self.root, "research/excavator/core/tools/batches.json",
              json.dumps({"no": ["EO:8000", "EO:9000"], "rc": ["EO:8001"]}))
        r = {x["key"]: x for x in M.measure(self.root)["rates"]}
        self.assertEqual(r["filed_per_attempt.no.fr"]["den"], 3)  # not pooled: fixture's 3 only
        self.assertEqual(r["filed_per_attempt.no.fr"]["n_studies"], 1)
        disp["pool_into_rates"] = True
        write(self.root, "research/excavator/core/evidence/DISPOSITION.json", json.dumps(disp, indent=1))
        m = M.measure(self.root)
        r = {x["key"]: x for x in m["rates"]}
        no = r["filed_per_attempt.no.fr"]
        self.assertEqual((no["num"], no["den"]), (3, 5))
        self.assertEqual(no["by_wave"], {M.WAVE: [2, 3], "core": [1, 2]})
        self.assertEqual(no["n_studies"], 2)
        self.assertEqual((r["filed_per_attempt.correction"]["num"], r["filed_per_attempt.correction"]["den"]), (2, 3))
        self.assertTrue(any(w["wave"] == "core" and w["pooled_into_rates"] for w in m["waves"]))
        self.assertAlmostEqual(m["costs"]["wave.per_filed_dossier"]["denominator"], 5)  # costs stay Tribonian
        for e in no["evidence"]:
            self.assertIn(re.sub(r"\s+", "", e["quote"]),
                          re.sub(r"\s+", "", (self.root / e["source"]).read_text(encoding="utf-8")))
        (self.root / "research/excavator/core/tools/batches.json").unlink()
        with self.assertRaises(M.MeasureError):
            M.measure(self.root)

    def test_sample_of_remaining_sets_stratum_rate(self):
        ids = ["EO:%d" % (8100 + i) for i in range(30)]
        disp = {"schema": "tribonian-disposition/v1", "pool_into_rates": True, "sample_of_remaining": True,
                "batches": [{"batch": "no", "attempted": 30, "claims_filed": 3, "state": "completed",
                             "not_filed": [{"instrument_id": i, "outcome": "blocked", "reason": "r"} for i in ids[3:]]}]}
        write(self.root, "research/excavator/core/evidence/DISPOSITION.json", json.dumps(disp, indent=1))
        write(self.root, "research/excavator/core/tools/batches.json", json.dumps({"no": ids}))
        p = self.root / M.READINESS
        with p.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for i in ids:
                w.writerow([i, "no", ""])
        r = {x["key"]: x for x in M.measure(self.root)["rates"]}
        no = r["filed_per_attempt.no.fr"]
        self.assertEqual((no["num"], no["den"]), (3, 30))
        self.assertEqual(no["pooled_alternative"]["den"], 33)
        self.assertIn("no longer in the pool", no["note"])
        self.assertNotIn("pooled_alternative", r["filed_per_attempt.yes.fr"])  # below MIN_SAMPLE: pooled
        self.assertEqual(r["filed_per_attempt.all"]["den"], 37)  # .all stays pooled


if __name__ == "__main__":
    unittest.main()
