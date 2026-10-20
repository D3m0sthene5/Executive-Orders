"""POLYA tests (standard library only).  Run:  python3 -I jobs/polya/test_polya.py

Claims proved: statistics are right on hand-built data; frames compute reach from a fixture repo
exactly; a missing input degrades one frame instead of crashing; outputs hold aggregates only;
export leaves cost/E_ready null (reach is never turned into a forecast); live data is consistent.
"""
import contextlib, io, json, os, sys, tempfile, unittest
sys.dont_write_bytecode = True
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import polya  # noqa: E402

COLS = ["instrument_id", "provisional_status", "ready_for_human_review", "blockers"] + ["step_" + s for s in polya.STEPS]


def readiness(rows):
    out = [",".join(COLS)]
    for iid, st, ready, bl, open_ in rows:
        steps = ["open" if s in open_ else "done" for s in polya.STEPS]
        out.append(",".join([iid, st, ready, bl] + steps))
    return "\n".join(out) + "\n"


def make_repo(root, with_edges=True):
    def put(rel, text):
        p = Path(root, rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    ALL = set(polya.STEPS)
    put("jobs/readiness-tracker/output/READINESS_BY_ORDER.csv", readiness([
        ("EO:1", "no", "no", "A", {"ending_or_current_basis"}),
        ("EO:2", "no", "no", "A", {"ending_or_current_basis", "clause_inventory"}),
        ("EO:3", "no", "no", "B", ALL - {"provisional_status"}),
        ("EO:4", "", "no", "NO_PROVISIONAL_STATUS", ALL),
        ("EO:5", "", "no", "NO_PROVISIONAL_STATUS", ALL),
        ("EO:6", "yes", "yes", "", set()),
        ("EO:7", "yes", "no", "A", {"ending_or_current_basis"}),
    ]))
    if with_edges:
        put("jobs/later-events/output/EDGES.csv",
            "edge_id,acting_id,target_id,mechanism\n"
            "e1,EO:100,EO:1,revocation\ne2,EO:100,EO:2,supersession\ne3,EO:100,EO:3,amendment\n"
            "e4,EO:200,EO:4,revocation\ne5,EO:200,EO:5,termination\ne6,EO:200,EO:6,revocation\ne7,EO:300,EO:1,termination\n")
    put("jobs/claim-kit/output/MISSING_SOURCES.jsonl",
        json.dumps({"actor_id": "EO:100", "target_id": "EO:1", "reason": "target provision not located"}) + "\n" +
        json.dumps({"actor_id": "EO:100", "target_id": "EO:2", "reason": "acting text absent"}) + "\n")
    put("jobs/claim-kit/output/FAMILIES.json", json.dumps([
        {"family_id": "own_term:condition", "instrument_ids": ["EO:1", "EO:2", "EO:3", "EO:6"]},
        {"family_id": "source:abc", "instrument_ids": ["EO:4", "EO:5"]}]))


class Stats(unittest.TestCase):
    def test_gini(self):
        self.assertEqual(polya.gini([1, 1, 1, 1]), 0.0)
        self.assertEqual(polya.gini([]), 0.0)
        self.assertAlmostEqual(polya.gini([0, 0, 0, 10]), 0.75, places=4)   # (n-1)/n for one unit holding all
        self.assertGreater(polya.gini([1, 2, 30]), polya.gini([9, 11, 13]))

    def test_coverage_top_vs_greedy(self):
        units = {"a": {1, 2, 3}, "b": {1, 2}, "c": {4}}
        pool = {1, 2, 3, 4, 5}
        cv = polya.coverage(units, pool, ks=(1, 2))
        self.assertEqual(cv["top1"], 0.6)
        self.assertEqual(cv["top2"], 0.6)      # b adds nothing to a
        self.assertEqual(cv["greedy2"], 0.8)   # greedy takes c instead
        self.assertEqual(cv["greedy1"], 0.6)

    def test_dist_restricts_to_pool(self):
        d = polya.dist({"u": {1, 2, 99}, "v": {2}}, {1, 2})
        self.assertEqual((d["units"], d["distinct_orders_reached"], d["sum_leverage"], d["max"]), (2, 2, 3, 2))
        self.assertEqual(d["overlap_factor"], 1.5)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        make_repo(self.tmp.name)
        self.c = polya.Ctx(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pool(self):
        c = self.c
        self.assertEqual((len(c.notready), len(c.dec_nr), len(c.undec)), (6, 4, 2))
        self.assertEqual(c.rows["EO:6"]["ready_for_human_review"], "yes")

    def test_f1_edges_exact(self):
        v = {x["name"]: x for x in polya.f1(self.c)}
        self.assertEqual({k: set(o) for k, o in v["ending_of_decided_NO"]["units"].items()},
                         {"EO:100": {"EO:1", "EO:2"}, "EO:300": {"EO:1"}})   # EO:3 amendment excluded
        self.assertEqual({k: set(o) for k, o in v["NO_hypothesis_for_undecided"]["units"].items()},
                         {"EO:200": {"EO:4", "EO:5"}})   # ready EO:6 never counted

    def test_f2_and_step_sufficiency(self):
        v = polya.f2(self.c)[0]
        self.assertEqual({k: set(o) for k, o in v["units"].items()}, {"EO:100": {"EO:1", "EO:2"}})
        # only EO:1 has the ending as its sole open step; EO:2 also needs clause_inventory
        self.assertEqual(polya.would_complete(self.c, {"EO:1", "EO:2"}, v["steps"]), 1)

    def test_step_filter_drops_orders_whose_step_is_done(self):
        # source:abc serves EO:4/EO:5 (original_text open) -> kept; own_term family: EO:1,2,3 have the ending open
        views, _ = polya.build(self.c, "F3_source_document")
        v = {x["name"]: x for x in views}["claim_kit_source_family"]
        self.assertEqual({k: set(o) for k, o in v["units"].items()}, {"source:abc": {"EO:4", "EO:5"}})
        c = self.c
        c.rows["EO:5"]["step_original_text"] = "done"
        v = {x["name"]: x for x in polya.build(c, "F3_source_document")[0]}["claim_kit_source_family"]
        self.assertEqual({k: set(o) for k, o in v["units"].items()}, {"source:abc": {"EO:4"}})
        self.assertEqual(v["dropped_orders_step_not_open"], 1)

    def test_export_marks_same_unit_across_frames(self):
        out = os.path.join(self.tmp.name, "out2")
        with contextlib.redirect_stdout(io.StringIO()):
            polya.main(["--repo", self.tmp.name, "--output", out, "export", "--min-reach", "1"])
        acts = {a["action_id"]: a for a in json.load(open(os.path.join(out, "CANDIDATE_ACTIONS.json")))["actions"]}
        self.assertIn("POLYA:F2:actor_provision_record:EO:100", acts["POLYA:F1:ending_of_decided_NO:EO:100"]["same_unit_actions"])

    def test_f9_sole_blocker(self):
        v = polya.f9(self.c)[0]
        self.assertEqual({k: len(o) for k, o in v["units"].items()}, {"A": 3, "B": 1, "NO_PROVISIONAL_STATUS": 2})

    def test_f0_is_aggregate_only(self):
        rep = polya.view_report(self.c, polya.f0(self.c)[0])
        self.assertEqual(rep["top"], [])
        self.assertEqual(rep["gini"], 0.0)

    def test_missing_input_degrades_one_frame(self):
        with tempfile.TemporaryDirectory() as t:
            make_repo(t, with_edges=False)
            c = polya.Ctx(t)
            views, why = polya.build(c, "F1_ending_instrument")
            self.assertIsNone(views)
            self.assertIn("unavailable", why)
            self.assertIsNotNone(polya.build(c, "F2_actor_provision_record")[0])

    def test_commands_write_aggregates_and_null_forecasts(self):
        out = os.path.join(self.tmp.name, "out")
        with contextlib.redirect_stdout(io.StringIO()):
            for argv in (["leverage", "F1"], ["compare"], ["export", "--min-reach", "1"]):
                self.assertEqual(polya.main(["--repo", self.tmp.name, "--output", out] + argv), 0)
        names = set(os.listdir(out))
        self.assertTrue({"COMPARE.json", "COMPARE.md", "CANDIDATE_ACTIONS.json", "LEVERAGE_F1_ending_instrument.json"} <= names)
        acts = json.load(open(os.path.join(out, "CANDIDATE_ACTIONS.json")))
        self.assertEqual(acts["schema"], "polya.actions/1")
        self.assertTrue(acts["actions"])
        for a in acts["actions"]:
            self.assertIsNone(a["cost_usd"])
            self.assertIsNone(a["E_ready"])           # reach is never presented as a forecast
            self.assertEqual(a["status"], "hypothesis")
            self.assertEqual(a["ceiling_orders"], a["reach_orders"] - a["reach_already_ready"])
        text = open(os.path.join(out, "COMPARE.json")).read()
        self.assertNotIn('"EO:1",', text.split('"frames"')[0] + "")   # no per-order id lists in the header sections
        cmp_ = json.loads(text)
        self.assertEqual(cmp_["frames"][0]["top20_units"], "aggregate only (one order per unit)")

    def test_resolve_aliases(self):
        self.assertEqual(polya.resolve("f3"), "F3_source_document")
        self.assertEqual(polya.resolve("ending"), "F1_ending_instrument")
        with self.assertRaises(SystemExit):
            polya.resolve("nope")


class Live(unittest.TestCase):
    """Smoke test on the real committed data (skipped when the tracker output is absent)."""

    def setUp(self):
        if not os.path.exists(os.path.join(polya.DEFAULT_REPO, "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")):
            self.skipTest("no tracker output")
        self.c = polya.Ctx(polya.DEFAULT_REPO)

    def test_pool_identity_and_bounds(self):
        c = self.c
        self.assertEqual(len(c.notready) + (len(c.rows) - len(c.notready)), len(c.rows))
        self.assertEqual(len(c.dec_nr) + len(c.undec), len(c.notready))
        for fid, *_ in polya.FRAMES:
            views, why = polya.build(c, fid)
            if why:
                continue
            for v in views:
                d = polya.dist(v["units"], v["pool"])
                self.assertLessEqual(d["distinct_orders_reached"], len(v["pool"]))
                self.assertLessEqual(d["max"], len(v["pool"]))
                self.assertTrue(0 <= d["gini"] < 1)
                self.assertLessEqual(d["coverage"]["top10"], d["coverage"]["top100"])
                self.assertLessEqual(d["coverage"]["top10"], d["coverage"]["greedy10"] + 1e-9)


if __name__ == "__main__":
    unittest.main(verbosity=1)
