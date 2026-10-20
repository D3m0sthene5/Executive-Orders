"""Mountweazel tests (standard library only).  Run:  python3 -I jobs/mountweazel/test_mountweazel.py

Core claims proved here:
  1. seeding is deterministic (same seed, same bytes) and varies with the seed;
  2. the answer key is never written into the blinded batch, and plants look like real items;
  3. `check` catches a seeded item leaked anywhere a job reads, and passes on the real repository;
  4. every flagged fixture is rejected by the production claim gate, while the de-flagged copy passes it;
  5. scoring gives catch rate per defect type, false-alarm bounds and Wilson intervals, and refuses an edited key.
"""
import contextlib, io, json, shutil, sys, tempfile, unittest
sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mountweazel as mw  # noqa: E402

REPO = mw.REPO


def run(*args):
    buf, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        try:
            rc = mw.main(["--repo", str(REPO)] + [str(a) for a in args])
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 2
            err.write(str(e.code))
    return rc, buf.getvalue(), err.getvalue()


def tree(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(Path(root).rglob("*")) if p.is_file()}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mw-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def seed(self, name, track="C", seed="t1", n=12, batch="MW-C1", extra=()):
        out, fx = self.tmp / name / "out", self.tmp / name / "fx"
        rc, so, se = run("seed", "--track", track, "--batch-id", batch, "--seed", seed, "--n", n,
                         "--out", out, "--fixtures-dir", fx, *extra)
        self.assertEqual(rc, 0, se + so)
        return out / batch, fx / batch


class SeedTests(Base):
    def test_deterministic(self):
        a_out, a_fx = self.seed("a")
        b_out, b_fx = self.seed("b")
        self.assertEqual(tree(a_out), tree(b_out))
        self.assertEqual(tree(a_fx), tree(b_fx))

    def test_seed_changes_selection(self):
        a_out, _ = self.seed("a", seed="alpha")
        b_out, _ = self.seed("b", seed="beta")
        self.assertNotEqual(tree(a_out / "batch"), tree(b_out / "batch"))

    def test_key_never_in_batch(self):
        out, fx = self.seed("a")
        key = json.loads((out / "key" / "KEY.sealed.json").read_text())
        self.assertGreaterEqual(key["n_seeded"], 1)
        self.assertFalse(mw.inside(out / "key", out / "batch"))
        blob = "".join(p.read_text() for p in (out / "batch").rglob("*") if p.is_file())
        for forbidden in ("is_seeded", "defect_code", "SEEDED", "seeded", "refuting", "locus_terms", "key_seal", "mountweazel", key["seed"]):
            self.assertNotIn(forbidden, blob, forbidden)
        for it in key["items"]:
            if it["is_seeded"]:
                self.assertNotIn(it["defect_code"] + ".", blob)

    def test_plants_share_layout_with_real_items(self):
        out, _ = self.seed("a")
        key = json.loads((out / "key" / "KEY.sealed.json").read_text())
        shapes = {}
        for it in key["items"]:
            data = json.loads((out / "batch" / "items" / f"{it['item_id']}.json").read_text())
            shapes.setdefault(it["is_seeded"], set()).add(tuple(sorted(data)) + tuple(sorted(data["claim"])))
        self.assertEqual(shapes[True], shapes[False])
        self.assertTrue(0.15 <= key["seeded_share"] <= 0.35)

    def test_order_appears_once_per_batch_and_exclusions_hold(self):
        out, _ = self.seed("a")
        key = json.loads((out / "key" / "KEY.sealed.json").read_text())
        orders = [i["base_order"] for i in key["items"]]
        self.assertEqual(len(orders), len(set(orders)))
        out2, _ = self.seed("b", batch="MW-C2", extra=("--exclude-orders", ",".join(orders)))
        key2 = json.loads((out2 / "key" / "KEY.sealed.json").read_text())
        self.assertFalse(set(orders) & {i["base_order"] for i in key2["items"]})

    def test_refuses_render_inside_repo(self):
        rc, _, err = run("seed", "--track", "C", "--batch-id", "MW-C9", "--seed", "x", "--n", 6,
                         "--out", REPO / "research" / "mw-leak", "--fixtures-dir", self.tmp / "fx")
        self.assertNotEqual(rc, 0)
        self.assertIn("inside the repository", err)
        self.assertFalse((REPO / "research" / "mw-leak").exists())
        rc, _, err = run("seed", "--track", "C", "--batch-id", "MW-C9", "--seed", "x", "--n", 6,
                         "--out", self.tmp / "o", "--fixtures-dir", REPO / "research" / "mw-fx")
        self.assertNotEqual(rc, 0)
        self.assertFalse((REPO / "research" / "mw-fx").exists())

    def test_track_s_batch(self):
        out, fx = self.seed("s", track="S", batch="MW-S1", n=12)
        key = json.loads((out / "key" / "KEY.sealed.json").read_text())
        self.assertTrue({i["defect_code"] for i in key["items"] if i["is_seeded"]} <= {"D10", "D13"})
        for p in fx.glob("*.seeded.json"):
            self.assertTrue(json.loads(p.read_text())["SEEDED"])


class FixtureGateTests(Base):
    def test_gate_rejects_flagged_and_accepts_deflagged_claims(self):
        _, fx = self.seed("a", n=24)
        gate = mw.load_gate()
        files = sorted(fx.glob("*.seeded.json"))
        self.assertGreaterEqual(len(files), 3)
        for f in files:
            d = json.loads(f.read_text())
            self.assertTrue(d["SEEDED"] and d["instrument_id"].startswith("SEEDED:"))
            errs = gate.validate_claim(d["seeded_payload"])
            self.assertIn("schema", errs)
            self.assertIn("instrument_id", errs)
            clean = dict(d["seeded_payload"], schema="eo-lifecycle-claim/v1", instrument_id=d["instrument_id"][len("SEEDED:"):])
            self.assertEqual(gate.validate_claim(clean), [], f.name)

    def test_each_plant_differs_from_its_base_in_exactly_one_documented_field(self):
        out, fx = self.seed("a", n=24)
        pool = mw.load_claim_pool(REPO)
        for f in fx.glob("*.seeded.json"):
            d = json.loads(f.read_text())
            base = pool[d["instrument_id"][len("SEEDED:"):]]["claim"]
            self.assertEqual(d["base"]["sha256"], mw.sha(base))
            self.assertTrue(d["mutation"]["refuting_span"]["quote"])
            self.assertIn(d["defect_code"], mw.TAXONOMY)


class CheckTests(Base):
    def make_repo(self, fx):
        repo = self.tmp / "repo"
        for d in ("research/readiness/claims", "jobs/other/output", "jobs/mountweazel/output"):
            (repo / d).mkdir(parents=True, exist_ok=True)
        (repo / "research/readiness/claims/real.jsonl").write_text('{"schema":"eo-lifecycle-claim/v1","instrument_id":"EO:1"}\n')
        (repo / "jobs/other/output/SUMMARY.json").write_text("{}")
        (repo / "jobs/mountweazel/output/STATUS.json").write_text("{}")
        return repo

    def test_clean_repo_passes_and_leaks_fail(self):
        out, fx = self.seed("a", n=12)
        repo = self.make_repo(fx)
        self.assertTrue(mw.check(repo, fx.parent)["ok"])
        fixture = json.loads(sorted(fx.glob("*.seeded.json"))[0].read_text())
        payload = fixture["seeded_payload"]
        deflag = dict(payload, schema="eo-lifecycle-claim/v1", instrument_id=fixture["instrument_id"][len("SEEDED:"):])
        leaks = {
            "flagged jsonl in claims": (repo / "research/readiness/claims/leak.jsonl", json.dumps(payload) + "\n"),
            "marker in another job output": (repo / "jobs/other/output/x.csv", "instrument_id\nSEEDED:EO:11\n"),
            "flagged fixture copied under research": (repo / "research/excavator-leak.json", (fx / sorted(p.name for p in fx.glob("*.json"))[0]).read_text()),
            "de-flagged exact copy (no markers)": (repo / "research/readiness/claims/quiet.jsonl", json.dumps(deflag) + "\n"),
            "forbidden mountweazel output": (repo / "jobs/mountweazel/output/SUMMARY.json", "{}"),
            "batch item id": (repo / "jobs/other/output/ids.txt", "see MW-C1-03 here"),
        }
        for label, (path, text) in leaks.items():
            path.write_text(text)
            res = mw.check(repo, fx.parent)
            self.assertFalse(res["ok"], label)
            self.assertGreaterEqual(res["problem_count"], 1, label)
            path.unlink()
            self.assertTrue(mw.check(repo, fx.parent)["ok"], "clean again after removing " + label)

    def test_planted_text_is_found_even_without_markers(self):
        out, fx = self.seed("a", n=24)
        repo = self.make_repo(fx)
        texts = [json.loads(p.read_text())["mutation"]["after"] for p in fx.glob("*.seeded.json")]
        long = [t for t in texts if isinstance(t, str) and len(t) >= 40]
        if not long:
            self.skipTest("this seed produced no long mutation text")
        (repo / "jobs/other/output/DIGEST.txt").write_text("copied: " + long[0])
        self.assertFalse(mw.check(repo, fx.parent)["ok"])

    def test_check_flags_fixture_without_flag(self):
        out, fx = self.seed("a", n=12)
        repo = self.make_repo(fx)
        f = sorted(fx.glob("*.seeded.json"))[0]
        d = json.loads(f.read_text())
        d["seeded_payload"]["schema"] = "eo-lifecycle-claim/v1"
        d["seeded_payload"]["instrument_id"] = "EO:11"
        f.write_text(json.dumps(d))
        res = mw.check(repo, fx.parent)
        self.assertFalse(res["ok"])
        self.assertTrue(any("claim gate does not reject" in p["problem"] for p in res["problems"]))

    def test_real_repository_has_no_seeded_item(self):
        res = mw.check(REPO, HERE_FIXTURES)
        self.assertTrue(res["ok"], res["problems"][:5])
        self.assertGreater(res["files_scanned"], 100)

    def test_cli_exit_code_and_status_file(self):
        repo = self.make_repo(self.tmp / "fx")
        argv = ["--repo", str(repo), "check", "--fixtures-dir", str(self.tmp / "none")]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(mw.main(argv), 0)
            self.assertEqual(json.loads((repo / "jobs/mountweazel/output/STATUS.json").read_text()), {})  # untouched without the flag
            (repo / "research/readiness/claims/leak.jsonl").write_text('{"instrument_id":"SEEDED:EO:5"}\n')
            self.assertEqual(mw.main(argv + ["--write-status"]), 1)
        status = json.loads((repo / "jobs/mountweazel/output/STATUS.json").read_text())
        self.assertFalse(status["ok"])


HERE_FIXTURES = Path(mw.HERE) / "fixtures"


class ScoreTests(Base):
    def verdicts(self, key, catch=(), wrong_reason=(), flag_real=(), voids=()):
        rows = []
        for it in key["items"]:
            if it["is_seeded"]:
                if it["item_id"] in catch:
                    rows.append({"item_id": it["item_id"], "decision": "reject", "locus": it["field"], "reason": "defect", "confidence": 0.9})
                elif it["item_id"] in wrong_reason:
                    rows.append({"item_id": it["item_id"], "decision": "reject", "locus": "nothing relevant", "reason": "gut feeling", "confidence": 0.4})
                else:
                    rows.append({"item_id": it["item_id"], "decision": "accept", "locus": "", "reason": "fine", "confidence": 0.8})
            else:
                rows.append({"item_id": it["item_id"], "decision": "reject" if it["item_id"] in flag_real else "accept",
                             "locus": "x", "reason": "r", "confidence": 0.5})
        return rows

    def setup_batch(self, n=24):
        out, _ = self.seed("a", n=n)
        key = json.loads((out / "key" / "KEY.sealed.json").read_text())
        return key

    def test_catch_rates_per_type_and_pooled(self):
        key = self.setup_batch()
        plants = [i["item_id"] for i in key["items"] if i["is_seeded"]]
        res = mw.score(key, self.verdicts(key, catch=plants[:-1]))
        n = len(plants)
        self.assertEqual(res["pooled"]["strict"]["k"], n - 1)
        self.assertEqual(res["pooled"]["strict"]["n"], n)
        self.assertEqual(res["pooled"]["strict"]["wilson95"], mw.wilson(n - 1, n))
        self.assertEqual(sum(t["n_plants"] for t in res["by_defect_type"].values()), n)
        self.assertEqual(res["false_alarm"]["flags_on_real"], 0)

    def test_lenient_minus_strict_is_right_verdict_wrong_reason(self):
        key = self.setup_batch()
        plants = [i["item_id"] for i in key["items"] if i["is_seeded"]]
        res = mw.score(key, self.verdicts(key, catch=plants[:1], wrong_reason=plants[1:]))
        self.assertEqual(res["pooled"]["strict"]["k"], 1)
        self.assertEqual(res["pooled"]["lenient"]["k"], len(plants))

    def test_false_alarm_is_bounded_until_adjudicated(self):
        key = self.setup_batch()
        reals = [i["item_id"] for i in key["items"] if not i["is_seeded"]]
        v = self.verdicts(key, flag_real=reals[:3])
        res = mw.score(key, v)
        fa = res["false_alarm"]
        self.assertEqual(fa["unadjudicated_flags"], 3)
        self.assertEqual(fa["lower_bound"]["k"], 0)
        self.assertEqual(fa["upper_bound"]["k"], 3)
        adj = {reals[0]: "false_alarm", reals[1]: "contestable", reals[2]: "confirmed_real_defect"}
        res = mw.score(key, v, adjudication=adj)
        fa = res["false_alarm"]
        self.assertEqual(fa["confirmed_real_defects_excluded"], [reals[2]])
        self.assertEqual((fa["lower_bound"]["k"], fa["upper_bound"]["k"]), (1, 2))
        self.assertEqual(fa["lower_bound"]["n"], len(reals) - 1)

    def test_voids_and_unreviewed(self):
        key = self.setup_batch()
        plants = [i["item_id"] for i in key["items"] if i["is_seeded"]]
        v = [r for r in self.verdicts(key, catch=plants) if r["item_id"] != plants[-1]]
        res = mw.score(key, v, voids=[plants[0]])
        self.assertEqual(res["voided_plants"], [plants[0]])
        self.assertIn(plants[-1], res["unreviewed"])
        self.assertEqual(res["pooled"]["strict"]["n"], len(plants) - 2)

    def test_edited_key_is_refused(self):
        key = self.setup_batch()
        key["items"][0]["is_seeded"] = not key["items"][0]["is_seeded"]
        with self.assertRaises(SystemExit):
            mw.score(key, self.verdicts(key))

    def test_bad_verdicts_are_refused(self):
        key = self.setup_batch()
        with self.assertRaises(SystemExit):
            mw.score(key, [{"item_id": "MW-C1-99", "decision": "accept"}])
        with self.assertRaises(SystemExit):
            mw.score(key, [{"item_id": key["items"][0]["item_id"], "decision": "maybe"}])
        r = {"item_id": key["items"][0]["item_id"], "decision": "accept"}
        with self.assertRaises(SystemExit):
            mw.score(key, [r, r])

    def test_score_cli_writes_only_outside_repo(self):
        out, _ = self.seed("a")
        key = out / "key" / "KEY.sealed.json"
        keyd = json.loads(key.read_text())
        vf = self.tmp / "v.json"
        vf.write_text(json.dumps(self.verdicts(keyd)))
        rc, so, _ = run("score", "--key", key, "--verdicts", vf, "--out", self.tmp / "res.json")
        self.assertEqual(rc, 0)
        self.assertTrue((self.tmp / "res.json").exists())
        rc, _, err = run("score", "--key", key, "--verdicts", vf, "--out", REPO / "research" / "mw-score.json")
        self.assertNotEqual(rc, 0)
        self.assertFalse((REPO / "research" / "mw-score.json").exists())


class StatsTests(unittest.TestCase):
    def test_known_intervals(self):
        lo, hi = mw.wilson(9, 10)
        self.assertAlmostEqual(lo, 0.60, places=2)
        self.assertAlmostEqual(hi, 0.98, places=2)
        self.assertEqual(mw.clopper_pearson(0, 15)[0], 0.0)
        self.assertAlmostEqual(mw.clopper_pearson(0, 15)[1], 0.218, places=3)
        self.assertEqual(mw.rate(2, 4)["indicative_only"], True)
        self.assertEqual(mw.rate(0, 0)["rate"], None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
