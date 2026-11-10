"""Admission: claim-kit work only on orders a Bentham action lists (admission.py).

Unit tests on a minimal plan, then the real pick and prepare on the kit's integration corpus with a plan added.
"""
import json
import tempfile
import unittest
from pathlib import Path

import admission
import batch
import kit as K
import test_build as T


def write_plan(repo, ranked=(), unranked=(), strata=None):
    out = Path(repo) / "jobs/bentham/output"
    (out / "strata").mkdir(parents=True, exist_ok=True)
    (out / "PLAN.json").write_text(json.dumps({"ranked": [{"id": a} for a in ranked],
                                               "unranked": [{"id": a} for a in unranked]}), encoding="utf-8")
    for action, ids in (strata or {}).items():
        (out / "strata" / (action + ".txt")).write_text("\n".join(ids) + "\n", encoding="utf-8")


class AdmissionUnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_checkout_without_bentham_is_not_checked(self):
        self.assertFalse(admission.applies(self.repo))

    def test_bentham_folder_without_plan_is_refused(self):
        (self.repo / "jobs/bentham").mkdir(parents=True)
        self.assertTrue(admission.applies(self.repo))
        with self.assertRaisesRegex(ValueError, "Bentham plan missing"):
            admission.admit(self.repo, "production.x", ["EO:1"], {})

    def test_sparse_project_checkout_without_bentham_is_refused(self):
        (self.repo / "AGENTS.md").write_text("project root\n", encoding="utf-8")
        self.assertTrue(admission.applies(self.repo))
        with self.assertRaisesRegex(ValueError, "Bentham plan missing"):
            admission.admit(self.repo, "production.x", ["EO:1"], {})

    def test_action_is_required_and_must_be_in_the_plan(self):
        write_plan(self.repo, ranked=["production.x"], strata={"production.x": ["EO:1"]})
        for action in (None, ""):
            with self.assertRaisesRegex(ValueError, "name the Bentham action"):
                admission.admit(self.repo, action, ["EO:1"], {})
        with self.assertRaisesRegex(ValueError, "unknown Bentham action"):
            admission.admit(self.repo, "production.invented", ["EO:1"], {})

    def test_orders_outside_the_action_are_refused(self):
        write_plan(self.repo, ranked=["production.x"], strata={"production.x": ["EO:1", "EO:2"]})
        self.assertEqual(admission.admit(self.repo, "production.x", ["EO:1", "EO:2"], {}), {"EO:1", "EO:2"})
        with self.assertRaisesRegex(ValueError, "1 orders are not in Bentham action production.x: EO:7"):
            admission.admit(self.repo, "production.x", ["EO:1", "EO:7"], {})

    def test_action_without_an_order_list_is_refused(self):
        write_plan(self.repo, ranked=["acquire.shared.EO_4314"])
        with self.assertRaisesRegex(ValueError, "lists no orders"):
            admission.admit(self.repo, "acquire.shared.EO_4314", ["EO:1"], {})

    def test_probe_admits_at_most_thirty_orders_across_agents(self):
        ids = [f"EO:{i}" for i in range(100)]
        write_plan(self.repo, ranked=["probe.production.y"], strata={"production.y": ids})
        held = {f"EO:{i}": {"agent": "a", "action": "probe.production.y"} for i in range(25)}
        held["EO:99"] = {"agent": "b", "action": "production.other"}   # another action does not count
        admission.admit(self.repo, "probe.production.y", ids[25:30], held)
        with self.assertRaisesRegex(ValueError, "is a probe: at most 30 orders"):
            admission.admit(self.repo, "probe.production.y", ids[25:31], held)
        self.assertEqual(admission.capacity(self.repo, "probe.production.y", held)[1], 5)

    def test_unranked_action_is_capped_like_a_probe(self):
        ids = [f"EO:{i}" for i in range(40)]
        write_plan(self.repo, unranked=["production.z"], strata={"production.z": ids})
        with self.assertRaisesRegex(ValueError, "is a probe"):
            admission.admit(self.repo, "production.z", ids[:31], {})
        admission.admit(self.repo, "production.z", ids[:30], {})

    def test_ranked_action_has_no_cap(self):
        ids = [f"EO:{i}" for i in range(200)]
        write_plan(self.repo, ranked=["production.w"], strata={"production.w": ids})
        admission.admit(self.repo, "production.w", ids, {})
        self.assertIsNone(admission.capacity(self.repo, "production.w", {})[1])


class AdmissionIntegrationTests(T.BuildIntegrationTests):
    """The kit's real pick and prepare, on the integration corpus, once a Bentham plan is present."""

    def lock(self):
        return json.loads((self.repo / "research/readiness/CLAIM_KIT_LOCK.json").read_text(encoding="utf-8"))["orders"]

    def test_pick_reserves_only_action_members_and_records_the_action(self):
        self.run_build()
        write_plan(self.repo, ranked=["production.p"], strata={"production.p": ["EO:2", "EO:3"]})
        picked = {r["instrument_id"] for r in K.pick(self.repo, self.out, "producer", 20, action="production.p")}
        self.assertEqual(picked, {"EO:2", "EO:3"})
        self.assertEqual({v["action"] for v in self.lock().values()}, {"production.p"})

    def test_pick_without_action_is_refused_once_a_plan_exists(self):
        self.run_build()
        write_plan(self.repo, ranked=["production.p"], strata={"production.p": ["EO:2"]})
        with self.assertRaisesRegex(ValueError, "name the Bentham action"):
            K.pick(self.repo, self.out, "producer", 5)

    def test_pick_stops_at_the_probe_cap(self):
        self.run_build()
        write_plan(self.repo, ranked=["probe.production.q"], strata={"production.q": ["EO:2", "EO:3", "EO:5"]})
        old = admission.PROBE_ORDERS
        admission.PROBE_ORDERS = 2
        try:
            self.assertEqual(len(K.pick(self.repo, self.out, "a", 20, action="probe.production.q")), 2)
            with self.assertRaisesRegex(ValueError, "already reserved"):
                K.pick(self.repo, self.out, "b", 20, action="probe.production.q")
        finally:
            admission.PROBE_ORDERS = old

    def test_prepare_refuses_orders_outside_the_action_and_writes_no_packet(self):
        self.run_build()
        write_plan(self.repo, ranked=["production.p"], strata={"production.p": ["EO:2"]})
        dest = self.repo / "research/experiment/outside"
        with self.assertRaisesRegex(ValueError, "not in Bentham action production.p: EO:1"):
            batch.prepare(self.repo, self.out, dest, ["EO:1"], "producer", action="production.p")
        self.assertFalse(dest.exists())

    def test_prepare_admitted_writes_the_receipt_beside_the_packet(self):
        self.run_build()
        write_plan(self.repo, ranked=["production.p"], strata={"production.p": ["EO:1", "EO:2"]})
        dest = self.repo / "research/experiment/admitted"
        batch.prepare(self.repo, self.out, dest, ["EO:1"], "producer", action="production.p")
        receipt = json.loads((dest / "ADMISSION.json").read_text(encoding="utf-8"))
        self.assertEqual((receipt["bentham_action"], receipt["instrument_ids"]), ("production.p", ["EO:1"]))
        self.assertTrue((dest / "PACKET.json").exists())

    def test_replacement_proposals_are_exempt(self):
        self.run_build()
        write_plan(self.repo, ranked=["production.p"], strata={"production.p": ["EO:2"]})
        T.write_jsonl(self.repo / "research/readiness/claims/existing.jsonl", [{"instrument_id": "EO:1"}])
        dest = self.repo / "research/experiment/replacement"
        batch.prepare(self.repo, self.out, dest, ["EO:1"], "producer", replacement_proposal=True)
        self.assertFalse((dest / "ADMISSION.json").exists())

    def test_replacement_flag_cannot_admit_a_new_order(self):
        self.run_build()
        write_plan(self.repo, ranked=["production.p"], strata={"production.p": ["EO:2"]})
        dest = self.repo / "research/experiment/sneak"
        with self.assertRaisesRegex(ValueError, "name the Bentham action"):
            batch.prepare(self.repo, self.out, dest, ["EO:3"], "producer", replacement_proposal=True)
        with self.assertRaisesRegex(ValueError, "not in Bentham action production.p: EO:3"):
            batch.prepare(self.repo, self.out, dest, ["EO:3"], "producer", replacement_proposal=True,
                          action="production.p")
        self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
