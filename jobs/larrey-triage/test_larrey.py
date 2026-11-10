"""Larrey triage tests on synthetic fixtures (CI checks out no job outputs)."""
import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "jobs/llull"))
sys.path.insert(0, str(REPO / "jobs/claim-kit"))

import kit_features as KF  # noqa: E402
import larrey as L  # noqa: E402
import llull  # noqa: E402

SRC = {"text_path": "jobs/x/texts/a.txt", "text_sha256": "0" * 64}


def original(iid, acceptable=True, page_check=False, grade="original_representation_unverified", text="order text",
             signing="1950-01-01"):
    return {"id": "ORIGINAL:" + iid, "source": dict(SRC), "text": text, "acceptable_as_original": acceptable,
            "requires_page_check": page_check, "grade": grade, "signing_date": signing, "role": "original"}


def dossier(iid, status=None, orig=True, clauses=1, records=(), **kw):
    ev = {}
    if orig:
        ev["ORIGINAL:" + iid] = original(iid, **kw)
    for n in range(clauses):
        ev[f"CLAUSES:{iid}#{n}"] = {"id": f"CLAUSES:{iid}#{n}", "source": dict(SRC), "text": "Sec. 1."}
    for k, v in records:
        ev[k] = v
    return {"instrument_id": iid, "whole_order_status": status, "original_source_id": "ORIGINAL:" + iid if orig else None,
            "evidence": ev, "current_law_leads": []}


def held(text="x", **extra):
    return dict({"source": dict(SRC), "text": text}, **extra)


class FeatureTests(unittest.TestCase):
    def test_basis_kinds_mirror_status_overlay(self):
        d = dossier("EO:1", records=[
            ("TERM:EO:1:a", held(kind="report_deadline")),          # a report deadline is never a basis
            ("ACT:EO:1>EO:2:effective#0", held()),                  # effective wording is not a basis
            ("ACT:EO:1>EO:3", {"source": {}, "text": "x"}),        # no text path: not exact held evidence
        ])
        self.assertEqual(KF.from_dossier(d)["basis_kinds"], [])
        d["evidence"]["ACTOR_TEXT:EO:4"] = held()
        d["evidence"]["TERM:EO:1:b"] = held(kind="fixed_term")
        f = KF.from_dossier(d)
        self.assertEqual(f["basis_kinds"], ["ACTOR_TEXT", "TERM"])
        self.assertTrue(f["actor_text"])

    def test_emergency_needs_notice_only_when_declared_before_the_anniversary(self):
        old = KF.from_dossier(dossier("EO:13000", "yes", text="declare a national emergency", signing="2001-01-01"))
        new = KF.from_dossier(dossier("EO:14400", "yes", text="declare a national emergency", signing="2026-05-01"))
        plain = KF.from_dossier(dossier("EO:13001", "yes", text="establish a council", signing="2001-01-01"))
        self.assertEqual((old["emergency_needs_notice"], new["emergency_needs_notice"],
                          plain["emergency_needs_notice"]), (True, False, False))
        d = dossier("EO:13000", "yes", text="International Emergency Economic Powers Act", signing="2001-01-01",
                    records=[("NOTICE:2026-03-01", held())])
        self.assertTrue(KF.from_dossier(d)["notice_held"])

    def test_working_grades_match_the_kit(self):
        import working_text
        self.assertEqual(KF.WORKING_GRADES, frozenset(working_text.GRADES))


class Fixture:
    """A miniature repository: tracker, compiled claim-kit outputs and (optionally) Bentham strata."""

    def __init__(self, root):
        self.root = Path(root)
        self.out = self.root / KF.KIT_OUT
        (self.out / "dossiers").mkdir(parents=True)
        (self.out / "actor-texts").mkdir()
        self.rows, self.jsonl = [], {}

    def decided(self, iid, status, **kw):
        d = dossier(iid, status, **kw)
        (self.out / "dossiers" / (iid.replace(":", "_") + ".json")).write_text(json.dumps(d), encoding="utf-8")
        self.rows.append({"instrument_id": iid, "provisional_status": status})

    def undecided(self, iid, acceptable=True, page_check=False, terms=(), acts=(), known=(), clauses=1,
                  grade="original_representation_unverified"):
        sel = {"instrument_id": iid, "acceptable_as_original": acceptable, "requires_page_check": page_check,
               "grade": grade, "source": dict(SRC), "text_path": SRC["text_path"]}
        self.add("OVERLAY_INPUTS", {"instrument_id": iid, "schema": "eo-claim-kit-overlay-input/v1",
                                    "selected": sel, "known_actor_ids": list(known)})
        for t in terms:
            self.add("OWN_TERMS", dict(held(), instrument_id=iid, kind=t))
        for actor in acts:
            self.add("ACTING_PROVISIONS", {"target_id": iid, "actor_id": actor, "actor_source": dict(SRC),
                                           "provision_text": "revoked", "verb": "revoke", "scope": "whole"})
        self.add("CLAUSES", {"instrument_id": iid, "source": dict(SRC),
                             "clauses": [{"scope_id": f"{iid}#{n}"} for n in range(clauses)]})
        self.add("STATUS_LEADS", {"instrument_id": iid, "status": None, "current_law_leads": []})
        self.rows.append({"instrument_id": iid, "provisional_status": ""})

    def actor(self, iid, overflow=False):
        self.add("CLAUSES", {"instrument_id": iid, "source": dict(SRC), "clauses": [{"scope_id": iid + "#1"}]})
        if overflow:
            (self.out / "actor-texts" / (iid.replace(":", "_") + ".json")).write_text(
                json.dumps({"instrument_id": iid}), encoding="utf-8")

    def add(self, stem, rec):
        self.jsonl.setdefault(stem, []).append(rec)

    def write(self, summary="s1"):
        for stem, recs in self.jsonl.items():
            (self.out / (stem + ".jsonl")).write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
        (self.out / "SUMMARY.json").write_text(json.dumps({"x": summary}), encoding="utf-8")
        t = self.root / "jobs/readiness-tracker/output"
        t.mkdir(parents=True, exist_ok=True)
        with open(t / "READINESS_BY_ORDER.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["instrument_id", "provisional_status", "step_original_text",
                                               "step_ending_or_current_basis"])
            w.writeheader()
            for r in self.rows:
                w.writerow(dict(r, step_original_text="done", step_ending_or_current_basis="open"))

    def strata(self, action, ids):
        d = self.root / "jobs/bentham/output/strata"
        d.mkdir(parents=True, exist_ok=True)
        (d / (action + ".txt")).write_text("\n".join(ids) + "\n", encoding="utf-8")

    def install_larrey(self):
        """The real larrey.py, llull gates and a back-test calibrated on this fixture's kit code."""
        for rel in ("jobs/larrey-triage/larrey.py", "jobs/llull/llull.py", "jobs/llull/kit_features.py"):
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / rel, self.root / rel)
        for rel in ("jobs/claim-kit/status_overlay.py", "jobs/claim-kit/assemble.py"):
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text("# kit code v1\n", encoding="utf-8")
        self.calibrate()

    def calibrate(self, lost=0):
        bt = {"calibrated_code_sha256": {rel: hashlib.sha256((self.root / rel).read_bytes()).hexdigest()
                                         for rel in ("jobs/claim-kit/status_overlay.py", "jobs/claim-kit/assemble.py")},
              "undecided": {"curve": [{"successes": 33, "successes_lost": lost}]},
              "decided": {"curve": [{"successes": 97, "successes_lost": 0}]}}
        (self.root / L.BACKTEST).write_text(json.dumps(bt), encoding="utf-8")


class _Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.f = Fixture(self.tmp.name)
        f = self.f
        f.decided("EO:9001", "no", records=[("ACT:EO:9001>EO:9500", held())])           # admitted
        f.decided("EO:9002", "yes", page_check=True)                                       # page check owed
        f.decided("EO:9003", "yes", acceptable=False, grade="mirror_transcription")       # working text: admitted
        f.decided("EO:9004", "yes", acceptable=False, grade="archival_replica_checked")   # not usable here
        f.decided("EO:9005", "yes", text="a national emergency", signing="2001-02-01")    # soft: NEA notice
        f.decided("EO:9006", "no", clauses=0)                                              # no inventory
        f.actor("EO:9500")
        f.actor("EO:9600", overflow=True)
        f.undecided("EO:8001", acts=["EO:9500"])                                           # admitted
        f.undecided("EO:8002", terms=["condition"])                                        # soft: no actor text
        f.undecided("EO:8003", terms=["report_deadline"])                                  # no basis
        f.undecided("EO:8004", acceptable=False, grade="mirror_transcription", acts=["EO:9500"])
        f.undecided("EO:8005", page_check=True, known=["EO:9500"])
        f.undecided("EO:8006", terms=["fixed_term"], known=["EO:9600"])                   # overflow actor: no id
        f.write()

    def tearDown(self):
        self.tmp.cleanup()

    def run_triage(self, **kw):
        out = Path(self.tmp.name) / L.OUTPUT
        return L.triage(self.tmp.name, out, **kw), out

    def verdicts(self, out):
        return {(route, i): v for route in L.ROUTES for i, v in L.verdicts_for(self.tmp.name, route).items()}


class TriageTests(_Base):
    def test_verdicts_and_reasons(self):
        (summary, reasons, pools), out = self.run_triage()
        v = self.verdicts(out)
        dl = lambda i: v[("decided_lifecycle", i)]
        uf = lambda i: v[("undecided_full", i)]
        self.assertEqual(dl("EO:9001")["admit"], "yes")
        self.assertEqual(dl("EO:9002")["reasons"], "page_check_owed")
        self.assertEqual(dl("EO:9003")["admit"], "yes")
        self.assertEqual(dl("EO:9004")["reasons"], "original_not_usable:archival_replica_checked")
        self.assertEqual((dl("EO:9005")["admit"], dl("EO:9005")["admit_hard_only"], dl("EO:9005")["reasons"]),
                         ("no", "yes", "soft:nea_continuation_notice_not_held"))
        self.assertEqual(dl("EO:9006")["reasons"], "no_clause_inventory")
        self.assertEqual(uf("EO:8001")["admit"], "yes")
        self.assertEqual(uf("EO:8002")["reasons"], "soft:no_later_order_text_held")
        self.assertIn("no_status_basis_record", uf("EO:8003")["reasons"])
        self.assertTrue(uf("EO:8004")["reasons"].startswith("original_not_usable:mirror_transcription"))
        self.assertTrue(uf("EO:8005")["reasons"].startswith("page_check_owed"))
        self.assertEqual(uf("EO:8006")["reasons"], "soft:no_later_order_text_held")
        self.assertEqual(reasons["decided_lifecycle"]["admitted"], 2)
        self.assertEqual(reasons["undecided_full"]["admitted"], 1)
        self.assertEqual(reasons["undecided_full"]["admitted_hard_only"], 3)
        self.assertEqual(reasons["undecided_full"]["reasons_sole"]["soft:no_later_order_text_held"], 2)
        self.assertTrue((out / "TODO.md").read_text(encoding="utf-8").startswith("# Larrey triage"))

    def test_pools_per_bentham_action_keep_out_orders_without_a_verdict(self):
        self.f.strata("status_assignment.undecided", ["EO:8001", "EO:8002", "EO:7777"])
        self.f.strata("production.one_step_away", ["EO:9001"])
        (_, _, pools), _ = self.run_triage(strata_dir=Path(self.tmp.name) / "jobs/bentham/output/strata")
        p = pools["status_assignment.undecided"]
        self.assertEqual((p["members"], p["admitted"], p["no_verdict_kept_out"]), (3, 1, 1))
        self.assertEqual(p["top_reasons"], {"soft:no_later_order_text_held": 1, "no_compiled_inputs": 1})
        self.assertIsNone(pools["production.one_step_away"]["route"])

    def test_gates_file_carries_the_whitworth_fields(self):
        _, out = self.run_triage()
        lines = [json.loads(l) for l in (out / L.GATES_FILE).read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(lines), 6 + 2 * 6)       # decided: one route; undecided: full and status-only
        g = next(x for x in lines if x["instrument_id"] == "EO:8003" and x["route"] == "undecided_full")
        self.assertFalse(g["pass"])
        self.assertIn("status_basis_record", g["missing"])
        self.assertIn("gates_commit", g)
        self.assertTrue({"instrument_id", "route", "pass", "missing", "gates_commit"} <= set(g))
        ok = next(x for x in lines if x["instrument_id"] == "EO:8001" and x["route"] == "status_only")
        self.assertEqual((ok["pass"], ok["missing"]), (True, []))

    def test_no_pools_mode_reads_no_strata(self):
        self.f.strata("status_assignment.undecided", ["EO:8001"])
        (_, _, pools), _ = self.run_triage(pools=False)
        self.assertEqual(pools, {})

    def test_light_reader_agrees_with_a_dossier_of_the_same_order(self):
        feats = KF.load(self.tmp.name)
        d = dossier("EO:8001", records=[("ACT:EO:8001>EO:9500", held()), ("ACTOR_TEXT:EO:9500", held())])
        a, b = feats["EO:8001"], KF.from_dossier(d)
        for k in ("original_acceptable", "page_check_owed", "basis_kinds", "actor_text"):
            self.assertEqual(a[k], b[k], k)


class AdmittedTests(_Base):
    def setUp(self):
        super().setUp()
        self.f.install_larrey()
        os.environ.pop("LARREY_LEVEL", None)

    def tearDown(self):
        os.environ.pop("LARREY_LEVEL", None)
        super().tearDown()

    def test_missing_or_stale_output_is_refused(self):
        with self.assertRaisesRegex(ValueError, "Larrey triage missing"):
            L.admitted(self.tmp.name, "status_assignment.undecided")
        self.run_triage()
        (Path(self.tmp.name) / KF.KIT_OUT / "SUMMARY.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "stale"):
            L.admitted(self.tmp.name, "status_assignment.undecided")

    def test_admitted_sets_and_levels(self):
        self.run_triage()
        ok, why, rec = L.admitted(self.tmp.name, "status_assignment.undecided")
        self.assertEqual(ok, {"EO:8001"})
        self.assertTrue(rec["larrey_enforced"])
        os.environ["LARREY_LEVEL"] = "hard"
        ok, _, rec = L.admitted(self.tmp.name, "probe.status_assignment.undecided")
        self.assertEqual(ok, {"EO:8001", "EO:8002", "EO:8006"})
        self.assertEqual(rec["larrey_level"], "hard")
        os.environ["LARREY_LEVEL"] = "off"
        with self.assertRaisesRegex(ValueError, "LARREY_LEVEL"):
            L.admitted(self.tmp.name, "status_assignment.undecided")

    def test_untriaged_action_and_changed_kit_code_are_not_enforced(self):
        self.run_triage()
        self.assertIsNone(L.admitted(self.tmp.name, "production.one_step_away")[0])
        (Path(self.tmp.name) / "jobs/claim-kit/status_overlay.py").write_text("# v2\n", encoding="utf-8")
        ok, _, rec = L.admitted(self.tmp.name, "status_assignment.undecided")
        self.assertIsNone(ok)
        self.assertFalse(rec["larrey_enforced"])
        self.assertIsNotNone(L.admitted(self.tmp.name, "production.claim_ready.yes.fr")[0])

    def test_a_backtest_that_loses_a_success_turns_the_route_advisory(self):
        self.run_triage()
        self.f.calibrate(lost=1)
        ok, _, rec = L.admitted(self.tmp.name, "status_assignment.undecided")
        self.assertIsNone(ok)
        self.assertFalse(rec["larrey_enforced"])
        self.assertIsNotNone(L.admitted(self.tmp.name, "production.claim_ready.no.fr")[0])
        # the job's own re-run back-test (output/BACKTEST.json) wins over the committed one
        bt = json.loads((Path(self.tmp.name) / L.BACKTEST).read_text(encoding="utf-8"))
        bt["undecided"]["curve"][-1]["successes_lost"] = 0
        (Path(self.tmp.name) / L.OUTPUT / "BACKTEST.json").write_text(json.dumps(bt), encoding="utf-8")
        self.assertTrue(L.admitted(self.tmp.name, "status_assignment.undecided")[2]["larrey_enforced"])

    def test_refusal_names_the_missing_input_and_fails_closed(self):
        self.run_triage()
        ok, why, _ = L.admitted(self.tmp.name, "status_assignment.undecided")
        msg = L.refusal("status_assignment.undecided", ["EO:8001", "EO:8003", "EO:7777"], ok, why)
        self.assertIn("2 orders are kept out", msg)
        self.assertIn("EO:7777 (no_compiled_inputs)", msg)
        self.assertIn("no_status_basis_record", msg)
        self.assertIsNone(L.refusal("status_assignment.undecided", ["EO:8001"], ok, why))

    def test_claim_kit_admission_applies_larrey(self):
        import admission
        root = Path(self.tmp.name)
        out = root / "jobs/bentham/output"
        out.mkdir(parents=True, exist_ok=True)
        (out / "PLAN.json").write_text(json.dumps({"ranked": [{"id": "status_assignment.undecided"}],
                                                   "unranked": []}), encoding="utf-8")
        self.f.strata("status_assignment.undecided", ["EO:8001", "EO:8002", "EO:8003"])
        with self.assertRaisesRegex(ValueError, "Larrey triage missing"):
            admission.admit(root, "status_assignment.undecided", ["EO:8001"], {})
        self.run_triage()
        self.assertEqual(admission.admit(root, "status_assignment.undecided", ["EO:8001"], {}), {"EO:8001"})
        with self.assertRaisesRegex(ValueError, "kept out of status_assignment.undecided by Larrey"):
            admission.admit(root, "status_assignment.undecided", ["EO:8001", "EO:8003"], {})
        self.assertEqual(admission.capacity(root, "status_assignment.undecided", {})[0], {"EO:8001"})
        admission.record(root / "packet", "status_assignment.undecided", ["EO:8001"], "a", root)
        rec = json.loads((root / "packet/ADMISSION.json").read_text(encoding="utf-8"))
        self.assertTrue(rec["triage"]["larrey_enforced"])

    def test_bentham_prices_only_admitted_orders(self):
        sys.path.insert(0, str(REPO / "jobs/bentham"))
        import bentham
        import candidates
        self.f.strata("status_assignment.undecided", ["EO:8001", "EO:8002", "EO:8003", "EO:8004"])
        self.run_triage()
        bt = json.loads((Path(self.tmp.name) / L.BACKTEST).read_text(encoding="utf-8"))
        bt["undecided"] = {"curve": [{"successes": 33, "successes_lost": 0}]}
        (Path(self.tmp.name) / L.BACKTEST).write_text(json.dumps(bt), encoding="utf-8")
        actions = [{"id": "status_assignment.undecided", "kind": "status_assignment", "orders": 4,
                    "order_ids_path": "jobs/bentham/output/strata/status_assignment.undecided.txt",
                    "rate_key": "r", "cost_key": "c"},
                   {"id": "production.one_step_away", "kind": "production", "orders": 1}]
        note = candidates.apply_triage(Path(self.tmp.name), actions)
        a = actions[0]
        self.assertEqual((a["orders"], a["orders_before_triage"], a["triage"]["kept_out"]), (1, 4, 3))
        self.assertIn("status_assignment.undecided", note)
        self.assertNotIn("triage", actions[1])
        measured = {"rates": [{"key": "r", "value": 0.1, "num": 9, "den": 90, "source": "s"}],
                    "costs": {"c": {"usd": 0.5, "per": "attempted order"}}}
        s = bentham.score(measured, a)
        self.assertEqual(s["cost_usd"], 0.5)                       # one admitted order is paid for
        self.assertAlmostEqual(s["expected_now"], round(min(1.0, 4 * 0.1 * 34 / 35), 1))
        self.assertTrue(any("Larrey triage" in n for n in s["notes"]))


class KitRulesTests(unittest.TestCase):
    """Accursius F5/F6 (Whitworth I2): the gates call the kit's own freeze-time functions when it has them."""

    def test_own_text_records_become_a_status_basis_on_the_undecided_route_only(self):
        seen = []

        def own_text(iid, original, clauses):
            seen.append((iid, original["text"], len(clauses)))
            return {"OWN_TEXT:" + iid + "#0": {"own_text_kind": "spent_on_issue"}}

        rules = KF.KitRules(own_text=own_text)
        d = dossier("EO:7001", text="Fort X is restored to the public domain.")
        self.assertEqual(KF.from_dossier(d, rules=rules)["basis_kinds"], ["OWN_TEXT"])
        self.assertEqual(seen, [("EO:7001", "Fort X is restored to the public domain.", 0)])
        self.assertEqual(KF.from_dossier(dossier("EO:7002", "no"), rules=rules)["basis_kinds"], [])
        inputs = {"instrument_id": "EO:7003", "selected": {"acceptable_as_original": True, "text_path": "t.txt",
                                                           "source": dict(SRC)}}
        f = KF.from_overlay(inputs, [], [], {"clauses": [{"scope_id": "EO:7003#1"}]}, lambda a: False,
                            rules=rules, read_text=lambda rel: "Sec. 1. Revoked.")
        self.assertEqual(f["basis_kinds"], ["OWN_TEXT"])

    def test_working_text_basis_credits_an_undecided_original(self):
        rules = KF.KitRules(working_text_basis=lambda d: "p4_replica" if d["evidence"][d["original_source_id"]]
                            ["grade"] == "archival_replica_checked" else None)
        f = KF.from_dossier(dossier("EO:7004", acceptable=False, grade="archival_replica_checked"), rules=rules)
        self.assertTrue(f["working_text_basis"])
        D = L._FeatData({"EO:7004": f})
        self.assertEqual(llull.GATES["original_usable"][1]({"instrument_id": "EO:7004", "provisional_status": ""}, D),
                         "held")
        g = KF.from_dossier(dossier("EO:7005", acceptable=False, grade="mirror_transcription"), rules=rules)
        self.assertFalse(g["working_text_basis"])

    def test_kit_rules_load_from_the_real_kit_without_error(self):
        rules = KF.KitRules(KF.CODE_KIT)
        self.assertFalse(any("unavailable" in x for x in rules.loaded), rules.loaded)


class ActionRouteTests(unittest.TestCase):
    def test_routes(self):
        self.assertEqual(L.action_route("status_assignment.undecided"), "undecided_full")
        self.assertEqual(L.action_route("probe.status_assignment.undecided"), "undecided_full")
        self.assertEqual(L.action_route("status_assignment.status_only.x"), "status_only")
        self.assertEqual(L.action_route("production.claim_ready.no.fr"), "decided_lifecycle")
        self.assertIsNone(L.action_route("recovery.custody_stranded"))
        self.assertIsNone(L.action_route("production.one_step_away"))

    def test_every_route_gate_is_registered_in_llull_with_a_reason(self):
        for spec in L.ROUTES.values():
            for g in spec["hard"] + spec["soft"]:
                self.assertIn(g, llull.GATES)
                self.assertIn(g, L.REASONS)


if __name__ == "__main__":
    unittest.main()
