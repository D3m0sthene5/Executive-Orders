"""Mountweazel tests (standard library only).  Run:  python3 -I jobs/mountweazel/test_mountweazel.py

Core claims proved here:
  1. seeding is deterministic (same seed, same bytes) and varies with the seed;
  2. the answer key is never written into the blinded batch, and plants look like real items;
  3. `check` catches a seeded item leaked anywhere a job reads, and passes on the real repository;
  4. every flagged fixture is rejected by the production claim gate, while the de-flagged copy passes it;
  5. scoring gives catch rate per defect type, false-alarm bounds and Wilson intervals, and refuses an edited key.
"""
import contextlib, hashlib, io, json, shutil, sys, tempfile, unittest
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
        needles = [n for p in fx.glob("*.seeded.json") for n in json.loads(p.read_text())["leak_needles"]]
        if not needles:
            self.skipTest("this seed produced no novel plant text")
        (repo / "jobs/other/output/DIGEST.txt").write_text("copied: " + needles[0])
        self.assertFalse(mw.check(repo, fx.parent)["ok"])

    def test_real_text_shared_with_a_plant_is_not_a_leak(self):
        """Regression for the MW-C1 false positives: a D3 cut is a prefix of the real quote, so every real copy
        of the order contained the old raw needle.  Real base items placed in the repo must pass."""
        out, fx = self.seed("a", n=24)
        repo = self.make_repo(fx)
        lines = []
        for p in fx.glob("*.seeded.json"):
            d = json.loads(p.read_text())
            lines.append(Path(REPO, d["base"]["path"]).read_text().splitlines()[d["base"]["line"] - 1])
            for n in d["leak_needles"]:
                self.assertNotIn(n, lines[-1])
        (repo / "research/readiness/claims/real-bases.jsonl").write_text("\n".join(lines) + "\n")
        res = mw.check(repo, fx.parent)
        self.assertTrue(res["ok"], res["problems"][:3])

    def _d8_like(self):
        """A fixture whose only leak needle is wording that a real donor claim in the repo also contains."""
        out, fx = self.seed("a", n=12)
        repo = self.make_repo(fx)
        f = sorted(fx.glob("*.seeded.json"))[0]
        d = json.loads(f.read_text())
        donor_text = "Donor order wording: the Secretary shall furnish a detailed statement of expenditures \u2014 verbatim."
        d["leak_needles"] = [json.dumps(donor_text, ensure_ascii=False)]
        f.write_text(json.dumps(d))
        donor = {"schema": "eo-lifecycle-claim/v1", "instrument_id": "EO:99999",
                 "operative_clauses": [{"original_operative_text": donor_text}]}
        (repo / "research/readiness/claims/donor.jsonl").write_text(json.dumps(donor) + "\n")
        (repo / "jobs/other/output/copy.jsonl").write_text(json.dumps(donor, ensure_ascii=False) + "\n")
        return fx, repo, d, donor_text

    def test_plant_text_that_is_real_donor_wording_is_not_a_leak(self):
        """Regression for the MW-C2 false positives: a D8 plant reuses a donor order's real wording, which
        sits in the donor's own claim and in its downstream copies."""
        fx, repo, d, _ = self._d8_like()
        res = mw.check(repo, fx.parent)
        self.assertTrue(res["ok"], res["problems"][:3])

    def test_donor_wording_does_not_hide_a_real_leak(self):
        fx, repo, d, donor_text = self._d8_like()
        payload = d["seeded_payload"]
        deflag = mw._deflag(payload)
        leaks = {
            "marker": ("jobs/other/output/m.json", json.dumps(payload)),
            "exact copy without markers": ("jobs/other/output/q.jsonl", json.dumps(deflag) + "\n"),
            "exact copy placed among the claims": ("research/readiness/claims/leak.jsonl", json.dumps(deflag) + "\n"),
        }
        for label, (rel, text) in leaks.items():
            path = repo / rel
            path.write_text(text)
            self.assertFalse(mw.check(repo, fx.parent)["ok"], label)
            path.unlink()
            self.assertTrue(mw.check(repo, fx.parent)["ok"], "clean again after removing " + label)

    def test_novel_needle_still_fails_when_another_needle_is_donor_wording(self):
        fx, repo, d, _ = self._d8_like()
        f = sorted(fx.glob("*.seeded.json"))[0]
        d["leak_needles"].append(json.dumps("Wording that exists only in the plant and nowhere in the repository."))
        f.write_text(json.dumps(d))
        self.assertTrue(mw.check(repo, fx.parent)["ok"])
        (repo / "jobs/other/output/DIGEST.txt").write_text("copied: " + d["leak_needles"][1])
        self.assertFalse(mw.check(repo, fx.parent)["ok"])

    def test_scan_covers_job_inputs_beyond_output_and_data(self):
        out, fx = self.seed("a", n=12)
        repo = self.make_repo(fx)
        (repo / "jobs/other/inputs").mkdir(parents=True)
        f = sorted(fx.glob("*.seeded.json"))[0]
        d = json.loads(f.read_text())
        (repo / "jobs/other/inputs/claims.jsonl").write_text(json.dumps(mw._deflag(d["seeded_payload"])) + "\n")
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

    def runner_manifest(self, inputs=None):
        inputs = inputs or {"jobs/mountweazel/fixtures/MW-C1/MW-C1-01.seeded.json": "100644:" + "a" * 40}
        return {"schema": 1, "job": "portfolio-repair-check", "base_commit": "b" * 40,
                "run_url": "https://github.com/example/repository/actions/runs/1",
                "scope": {"roots": ["jobs/mountweazel/fixtures"], "patterns": [],
                          "exclude": "jobs/portfolio-repair-check/output"},
                "inputs": inputs,
                "inputs_sha256": hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                "base_output_sha256": hashlib.sha256(b"{}").hexdigest()}

    def test_runner_manifest_fixture_inventory_is_not_a_leak(self):
        repo = self.make_repo(self.tmp / "none")
        for rel in ("oversized/runner-freshness/portfolio-repair-check-inputs.json",
                    "jobs/portfolio-repair-check/output/RUNNER_INPUTS.json"):
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(self.runner_manifest(), indent=2))
        result = mw.check(repo, self.tmp / "none")
        self.assertTrue(result["ok"], result["problems"])
        self.assertEqual(result["files_scanned"], 5)  # manifests are scanned, not skipped

    def test_runner_manifest_exception_rejects_invalid_or_duplicate_structure(self):
        repo = self.make_repo(self.tmp / "none")
        p = repo / "oversized/runner-freshness/portfolio-repair-check-inputs.json"
        p.parent.mkdir(parents=True)
        variants = []
        for field, value in (("job", "other"), ("schema", True), ("inputs_sha256", "0" * 64),
                             ("base_output_sha256", "bad"), ("extra_payload", {"item_id": "MW-C1-01"})):
            m = self.runner_manifest()
            m[field] = value
            variants.append((field, json.dumps(m)))
        m = self.runner_manifest({"jobs/mountweazel/fixtures/MW-C1/MW-C1-01.seeded.json": "actual payload"})
        variants.append(("non-hash inventory value", json.dumps(m)))
        variants.append(("duplicate field", json.dumps(self.runner_manifest()).replace('"schema": 1', '"schema": 0, "schema": 1')))
        for name, raw in variants:
            with self.subTest(name=name):
                p.write_text(raw)
                self.assertIsNone(mw._runner_inventory_for_item_scan(p, repo))
                self.assertFalse(mw.check(repo, self.tmp / "none")["ok"])

    def test_runner_manifest_exception_is_limited_to_exact_locations(self):
        repo = self.make_repo(self.tmp / "none")
        for rel in ("oversized/arbitrary-inputs.json", "oversized/runner-freshness/other-inputs.json",
                    "jobs/other/output/RUNNER_INPUTS.json", "jobs/portfolio-repair-check/output/notes.json"):
            with self.subTest(path=rel):
                p = repo / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(self.runner_manifest()))
                self.assertFalse(mw.check(repo, self.tmp / "none")["ok"])
                p.unlink()

    def test_runner_manifest_other_ids_and_payloads_still_fail(self):
        repo = self.make_repo(self.tmp / "none")
        p = repo / "oversized/runner-freshness/portfolio-repair-check-inputs.json"
        p.parent.mkdir(parents=True)
        variants = []
        m = self.runner_manifest()
        m["run_url"] += "/MW-C1-01"
        variants.append(m)
        m = self.runner_manifest()
        m["scope"]["roots"].append("jobs/other/MW-C1-01")
        variants.append(m)
        inputs = dict(self.runner_manifest()["inputs"])
        inputs["research/readiness/claims/MW-C1-01.json"] = "100644:" + "c" * 40
        variants.append(self.runner_manifest(inputs))  # recomputed digest does not exempt other paths
        m = self.runner_manifest()
        m["run_url"] += "/SEEDED:EO:1"
        variants.append(m)
        for m in variants:
            p.write_text(json.dumps(m))
            self.assertFalse(mw.check(repo, self.tmp / "none")["ok"])
        out, fx = self.seed("a", n=12)
        payload = json.loads(sorted(fx.glob("*.seeded.json"))[0].read_text())["seeded_payload"]
        for obj in (payload, mw._deflag(payload)):
            p.write_text(json.dumps(obj))
            self.assertFalse(mw.check(repo, fx.parent)["ok"])

    def test_valid_runner_inventory_still_scans_raw_planted_text(self):
        repo = self.make_repo(self.tmp / "none")
        p = repo / "oversized/runner-freshness/portfolio-repair-check-inputs.json"
        p.parent.mkdir(parents=True)
        m = self.runner_manifest()
        m["run_url"] = "Novel planted wording must remain detectable inside an otherwise valid inventory."
        p.write_text(json.dumps(m))
        view = mw._runner_inventory_for_item_scan(p, repo)
        self.assertIsNotNone(view)
        hits = mw.scan_file(p, [json.dumps(m["run_url"]).encode()], set(), item_id_data=view)
        self.assertTrue(any(h.startswith("planted text ") for h in hits), hits)

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
    def correct_reason(self, it):
        issue = {"D1": "deadline is not demonstrated performance", "D2": "one-time performance already completed",
                 "D3": "quote truncated before the operative verb", "D4": "partial scope is not the whole order",
                 "D5": "earlier end was missed in favor of later revocation", "D6": "omitted later event",
                 "D7": "wrong effective date", "D8": "wrong order text from a neighbour", "D9": "coverage overstated",
                 "D10": "wrong target does not revoke this order", "D13": "source is already held"}
        return issue[it["defect_code"]] + ": " + " ".join(it.get("locus_terms", []))

    def verdicts(self, key, catch=(), wrong_reason=(), flag_real=(), voids=()):
        rows = []
        for it in key["items"]:
            if it["is_seeded"]:
                if it["item_id"] in catch:
                    rows.append({"item_id": it["item_id"], "decision": "reject", "locus": it["field"], "reason": self.correct_reason(it), "confidence": 0.9})
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

    def test_generic_field_name_is_not_a_strict_catch(self):
        key = self.setup_batch()
        plants = [i for i in key["items"] if i["is_seeded"]]
        rows = [{"item_id": i["item_id"], "decision": "reject" if i["is_seeded"] else "accept",
                 "locus": "first_end whole_order_end quote later_events", "reason": "looks off"} for i in key["items"]]
        res = mw.score(key, rows)
        self.assertEqual(res["pooled"]["strict"]["k"], 0)
        self.assertEqual(res["pooled"]["lenient"]["k"], len(plants))

    def test_relabel_tells_noticed_and_verdict_alias(self):
        key = self.setup_batch()
        plants = [i for i in key["items"] if i["is_seeded"]]
        a, b = plants[0], plants[1]
        rows = []
        for i in key["items"]:
            if i["item_id"] == a["item_id"]:
                rows.append({"item_id": i["item_id"], "verdict": "reject", "locus": i["field"], "reason": self.correct_reason(i)})
            elif i["item_id"] == b["item_id"]:
                rows.append({"item_id": i["item_id"], "verdict": "accept", "locus": i["field"], "reason": self.correct_reason(i)})
            else:
                rows.append({"item_id": i["item_id"], "verdict": "accept"})
        res = mw.score(key, rows, relabel={a["item_id"]: "D11"}, tells=[a["item_id"]], production=(0, 15))
        self.assertIn("D11", res["by_defect_type"])
        self.assertEqual(res["pooled"]["tell_free"]["strict"]["n"], len(plants) - 1)
        self.assertEqual(res["pooled"]["tell_free"]["strict"]["k"], 0)
        if mw.specific_terms(b):
            self.assertEqual([x["item_id"] for x in res["pooled"]["noticed_but_accepted"]], [b["item_id"]])
        self.assertIn("tell_free", res["implied_for_production"])
        with self.assertRaises(SystemExit):
            mw.score(key, rows, relabel={a["item_id"]: "D99"})

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


class PlantQualityTests(Base):
    def test_rewrites_never_touch_another_clause(self):
        """MW-C1 tell: global date/actor swaps rewrote sentences about sibling clauses.  Every date/actor plant
        must have an old end that no other clause or later event shares."""
        out, fx = self.seed("a", n=40, extra=("--share", "0.5", "--codes", "D2,D4,D5,D7", "--allow-short"))
        pool = mw.load_claim_pool(REPO)
        files = list(fx.glob("*.seeded.json"))
        self.assertTrue(files)
        for f in files:
            d = json.loads(f.read_text())
            base = pool[d["instrument_id"][len("SEEDED:"):]]["claim"]
            i = int(d["mutation"]["field"].split("[")[1].split("]")[0])
            fe = base["operative_clauses"][i]["first_end"]
            actor = fe.get("actor") if d["defect_code"] in ("D2", "D4", "D5") else None
            self.assertTrue(mw._swap_safe(base, i, fe["date"], actor), f.name)

    def test_recurring_duties_are_not_one_time(self):
        self.assertTrue(mw.RECURRING_RE.search("shall submit an annual report to the President"))
        for rec in mw.load_claim_pool(REPO).values():
            for spec, apply in mw.ops_c("D2", rec["claim"], {}, "x"):
                i = int(spec.split(":")[0])
                self.assertFalse(mw.RECURRING_RE.search(rec["claim"]["operative_clauses"][i]["original_operative_text"]))


class MaterialCorrespondenceTests(unittest.TestCase):
    """Controlled scoring pairs, not new legal adjudications or production claims."""
    def key(self, code, field="operative_clauses[0].first_end"):
        body = {"schema": mw.SCHEMA_KEY, "batch_id": "scoring-control", "track": "C", "n_items": 1,
                "n_seeded": 1, "planned_n_seeded": 3,
                "items": [{"item_id": "control-item", "is_seeded": True, "defect_code": code,
                           "field": field, "affected_scope_id": "control-clause-a",
                           "locus_terms": ["EO:12345", "2001-01-01"],
                           "refuting_quote": "The approved test method requires investigation of this evidence."}]}
        return {**body, "key_seal_sha256": mw.sha(body)}

    def result(self, code, reason, locus="operative_clauses[0]", **kw):
        return mw.score(self.key(code), [{"item_id": "control-item", "decision": "reject",
                                        "reason": reason, "locus": locus}], **kw)

    def test_wrong_issue_in_same_order_gets_no_d6_credit(self):
        r = self.result("D6", "EO 12345 has a cut quote in a different clause.", "operative_clauses[9]")
        self.assertEqual(r["pooled"]["strict"]["k"], 0)
        self.assertEqual(r["pooled"]["lenient"]["k"], 1)

    def test_locator_alone_does_not_establish_material_issue(self):
        for reason in ("EO 12345", "2001-01-01", "Something looks questionable."):
            self.assertEqual(self.result("D6", reason)["pooled"]["strict"]["k"], 0)

    def test_missing_event_needs_matching_clause_and_event(self):
        good = "The omitted event from EO 12345 on 2001-01-01 must be investigated."
        self.assertEqual(self.result("D6", good)["pooled"]["strict"]["k"], 1)
        self.assertEqual(self.result("D6", good, "operative_clauses[7]")["pooled"]["strict"]["k"], 0)
        self.assertEqual(self.result("D6", "An omitted event needs investigation.")["pooled"]["strict"]["k"], 0)

    def test_earlier_event_performance_partial_scope_and_savings_pairs(self):
        cases = {
            "D5": "An earlier end requires investigation before selecting later revocation.",
            "D2": "Demonstrated performance of this one-time command requires clause-specific analysis.",
            "D4": "The partial scope does not establish the whole order's end.",
            "D12": "The savings provision preserves effects that this conclusion omits.",
        }
        for code, reason in cases.items():
            with self.subTest(code=code):
                self.assertEqual(self.result(code, reason)["pooled"]["strict"]["k"], 1)
                self.assertEqual(self.result(code, reason, "operative_clauses[8]")["pooled"]["strict"]["k"], 0)
        # A coherent but disputed premise does not itself make performance the end.
        self.assertEqual(self.result("D2", "The date typography is wrong.")["pooled"]["strict"]["k"], 0)

    def test_manual_correspondence_requires_provenance_and_preserves_mechanical_result(self):
        with self.assertRaises(SystemExit):
            self.result("D6", "unclear", strict_overrides={"control-item": True})
        override = {"caught": True, "adjudicator": "test-reviewer", "source": "review-decision.json",
                    "reason": "Verified the synonym against the exact omitted event.",
                    "affected_locus": "control-clause-a", "material_issue": "omitted amendment event"}
        r = self.result("D6", "The history elides the amendment.", strict_overrides={"control-item": override})
        self.assertEqual(r["pooled"]["strict"]["k"], 1)
        item = r["by_defect_type"]["D6"]["items"][0]
        self.assertFalse(item["correspondence"]["mechanical_candidate"])
        self.assertEqual(item["adjudication"], override)

    def test_missing_plants_and_blinding_are_explicit(self):
        r = mw.score(self.key("D6"), [])
        self.assertEqual(r["plants_missing_unscored"], 2)
        self.assertEqual(r["plants_unreviewed_unscored"], 1)
        self.assertIsNone(r["pooled"]["strict"]["rate"])
        self.assertFalse(r["blinding"]["technical_separation_verified"])


class StatsTests(unittest.TestCase):
    def test_implied_prevalence(self):
        catch = mw.rate(3, 6)
        r = mw.implied_prevalence(0, 15, catch)
        self.assertAlmostEqual(r["flag_rate_upper95"], 0.218, places=3)
        self.assertAlmostEqual(r["prevalence_upper95_at_point_catch"], 0.436, places=2)
        self.assertEqual(r["prevalence_upper95_at_catch_lower95"], 1.0)
        self.assertEqual(mw.implied_prevalence(0, 15, mw.rate(0, 3))["prevalence_upper95_at_point_catch"], 1.0)

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
