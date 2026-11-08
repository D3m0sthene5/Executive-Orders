"""Offline tests for candidates.py: fixtures in a temp dir use the real file shapes."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import candidates as C  # noqa: E402

STEPS = ["provisional_status", "original_text", "clause_inventory", "ending_or_current_basis", "savings_residuals",
         "counterevidence", "shared_sources", "opus_media"]
HEADER = (["instrument_id", "provisional_status", "ready_for_human_review", "claim_present", "blockers", "working_text_policy_errors"]
          + ["step_" + s for s in STEPS])
NONGATE = "NO_CLAUSE_INVENTORY|FIRST_END_UNPROVED|SAVINGS_RESIDUALS_NOT_CLOSED"


def row(eo, status, orig, counter, blockers, claim="no", clause="open", end="open", sav="open", shared="n/a", opus="n/a"):
    return {"instrument_id": "EO:%d" % eo, "provisional_status": status, "ready_for_human_review": "no",
            "claim_present": claim, "blockers": blockers, "step_provisional_status": "done", "step_original_text": orig,
            "step_clause_inventory": clause, "step_ending_or_current_basis": end, "step_savings_residuals": sav,
            "step_counterevidence": counter, "step_shared_sources": shared, "step_opus_media": opus}


ROWS = [
    # a filed claim whose working-text confirmation went stale (Photius 2026-11-07), and a ready custody-recovery order
    dict(row(9060, "no", "done", "done", "WORKING_TEXT_REVIEW_OR_DISCLOSURE_REQUIRED|" + NONGATE, claim="yes"),
         working_text_policy_errors="working_text:prior_confirmation_stale"),
    dict(row(9051, "no", "done", "done", "", claim="yes"), ready_for_human_review="yes"),
    # claim-ready strata
    row(9000, "no", "done", "done", NONGATE),
    row(9001, "no", "provisional", "done", NONGATE),
    row(9002, "yes", "done", "done", "NO_CLAUSE_INVENTORY|CURRENT_BASIS_UNPROVED|SAVINGS_RESIDUALS_NOT_CLOSED"),
    row(5000, "no", "done", "done", NONGATE),                       # prefr stratum (EO < 7532)
    row(9003, "no", "open", "done", NONGATE),                       # counterevidence done but text open: not claim-ready
    row(9004, "no", "done", "open", NONGATE + "|NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE"),
    # held by an unretrieved shared source: out of the stratum, unlocked by the one_source action
    row(9010, "no", "done", "done", NONGATE + "|SHARED_SOURCE_NOT_RETRIEVED:EO::4314", shared="open"),
    row(9011, "no", "done", "done", NONGATE + "|SHARED_SOURCE_NOT_RETRIEVED:EO::4314|SHARED_SOURCE_NOT_RETRIEVED:EO::6868", shared="open"),
    # fetch-officials unlocks: fr era counts, prefr does not
    row(9020, "no", "open", "done", "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND|" + NONGATE),
    row(9021, "yes", "open", "done", "ONLY_COMPILED_TRANSCRIPTION_FOUND|NO_CLAUSE_INVENTORY|CURRENT_BASIS_UNPROVED|SAVINGS_RESIDUALS_NOT_CLOSED"),
    row(6000, "no", "open", "done", "ONLY_COMPILED_TRANSCRIPTION_FOUND|" + NONGATE),
    # needs two acquisitions (fetch + OFR catalog search): not counted
    row(9022, "no", "open", "open", "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND|" + NONGATE + "|NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE"),
    # page check covers original-found plus compiled; must not also count for fetch-officials
    row(9030, "no", "open", "done", "ORIGINAL_FOUND_NEEDS_PAGE_CHECK|ONLY_COMPILED_TRANSCRIPTION_FOUND|" + NONGATE),
    # one step away: claim present, exactly one applicable step open
    row(9040, "no", "done", "done", "CLAIM_INCOMPLETE:ending_or_current_basis", claim="yes", clause="done", end="open", sav="done"),
    row(9041, "no", "done", "done", "CLAIM_INCOMPLETE:ending_or_current_basis", claim="yes", clause="done", end="open", sav="done", opus="open"),  # two open
    row(9042, "no", "done", "done", "CLAIM_INCOMPLETE:ending_or_current_basis", claim="no", clause="done", end="open", sav="done"),   # no claim
    # custody-stranded recovery order that would otherwise sit in the no.fr stratum
    row(9050, "no", "done", "done", NONGATE),
]
TRACKER_MD = """# Readiness tracker

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 30 | machine job | Fetch an official original for orders held only as a compiled transcription |
| 8 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
| 10 | one source | Retrieve shared source EO::4314 |
| 6 | one source | Retrieve shared source EO::6868 |
| 5 | machine job | Re-fetch the PDFs Opus downloaded but left out of its release |
"""
SHARED = [(30, "machine_job", "Fetch an official original for orders held only as a compiled transcription", "ONLY_COMPILED_TRANSCRIPTION_FOUND"),
          (8, "agent_check", "Check the page location of fr-originals and official-compilation finds marked medium/low confidence", "ORIGINAL_FOUND_NEEDS_PAGE_CHECK"),
          (10, "one_source", "Retrieve shared source EO::4314", "SHARED_SOURCE_NOT_RETRIEVED:EO::4314"),
          (6, "one_source", "Retrieve shared source EO::6868", "SHARED_SOURCE_NOT_RETRIEVED:EO::6868"),
          (5, "machine_job", "Re-fetch the PDFs Opus downloaded but left out of its release", "OPUS_MEDIA_REFETCH_NEEDED")]


def make_repo(root):
    def w(rel, text):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    p = root / C.TRACKER_CSV
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=HEADER, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(ROWS)
    w(C.TRACKER_MD, TRACKER_MD)
    with open(root / C.SHARED_CSV, "w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["orders_unblocked", "kind", "action", "blocker"])
        wr.writerows(SHARED)
    w(C.DISPOSITION, json.dumps({"schema": "tribonian-disposition/v1", "batches": [
        {"batch": "a", "not_filed": [{"instrument_id": "EO:9050", "outcome": "rejected_mechanical", "reason": ""},
                                     {"instrument_id": "EO:77", "outcome": "rejected_mechanical", "reason": ""},
                                     {"instrument_id": "EO:9051", "outcome": "rejected_mechanical", "reason": ""},
                                     {"instrument_id": "EO:78", "outcome": "blocked", "reason": "x"}]},
        {"batch": "b", "not_filed": [{"instrument_id": "EO:77", "outcome": "rejected_mechanical", "reason": ""}]}]}, indent=2))
    w(C.TRIBONIAN_REPORT, "x\n47 reviewed claims are blocked by source custody. y\nEmergency-dependent YES orders lack the yearly National Emergencies Act continuation notices.\nThe current texts of parent orders and statutes are not held.\n")
    w(C.POLYA_COMPARE, json.dumps({"frames": [{"frame": "F7_aux_current_predicate_table", "decided_not_ready_reachable": 340}]}, indent=1))
    w(C.POLYA_ACTIONS, "{}")


class CandidatesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        make_repo(cls.root)
        cls.out = C.candidates(cls.root)
        cls.by = {a["id"]: a for a in cls.out["actions"]}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def ids(self, aid):
        return set((self.root / self.by[aid]["order_ids_path"]).read_text().split())

    def test_strata_assignment(self):
        no_fr = self.ids("production.claim_ready.no.fr")
        self.assertEqual(no_fr, {"EO:9000", "EO:9001"})  # 9050 is recovery, 9003/9004 fail a gate
        self.assertEqual(self.ids("production.claim_ready.yes.fr"), {"EO:9002"})
        self.assertEqual(self.ids("production.claim_ready.no.prefr"), {"EO:5000"})  # pre-FR era
        self.assertEqual(self.by["production.claim_ready.no.fr"]["rate_key"], "filed_per_attempt.no.fr")
        self.assertEqual(self.by["production.claim_ready.no.fr"]["cost_key"], "wave.per_attempt")
        self.assertEqual(self.by["production.claim_ready.no.fr"]["orders"], 2)

    def test_stratum_unit_rules(self):
        o = {r["instrument_id"]: r for r in C.load_orders(self.root)}
        self.assertTrue(C.in_claim_ready_stratum(o["EO:9001"]))   # provisional text counts
        self.assertFalse(C.in_claim_ready_stratum(o["EO:9003"]))
        self.assertFalse(C.in_claim_ready_stratum(o["EO:9010"]))  # held by shared source
        self.assertEqual(C.era(7531), "prefr")
        self.assertEqual(C.era(7532), "fr")

    def test_one_step_rule(self):
        self.assertEqual(self.ids("production.one_step_away"), {"EO:9040"})
        self.assertEqual(self.by["production.one_step_away"]["rate_key"], "filed_per_attempt.correction")

    def test_recovery(self):
        r = self.by["recovery.custody_stranded"]
        self.assertEqual(r["kind"], "recovery")
        self.assertEqual(r["orders"], 2)  # EO:77 counted once; EO:9051 is ready now and drops out
        self.assertEqual(r["cost_key"], "review.per_submitted")
        self.assertIn("review", r["description"])
        self.assertEqual(self.ids("recovery.custody_stranded"), {"EO:9050", "EO:77"})

    def test_working_text_stale_recovery(self):
        r = self.by["recovery.working_text_stale"]
        self.assertEqual((r["kind"], r["cost_key"], r["rate_key"]), ("recovery", "review.per_submitted", "filed_per_attempt.correction"))
        self.assertEqual(self.ids("recovery.working_text_stale"), {"EO:9060"})
        for aid in self.by:
            if aid.startswith("production."):
                self.assertNotIn("EO:9060", self.ids(aid), aid)

    def unlock_total(self, aid):
        return sum(u["orders"] for u in self.by[aid]["unlocks"])

    def test_unlocks_without_double_counting(self):
        # 9020 (no) and 9021 (yes) are fr and covered; 6000 is pre-FR; 9022 needs two actions; 9030 goes to page check.
        fetch = self.by["acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND"]
        self.assertEqual(fetch["kind"], "acquisition")
        self.assertEqual(fetch["cost_override_usd"], 0)
        self.assertEqual(fetch["orders"], 0)
        got = {u["rate_key"]: u["orders"] for u in fetch["unlocks"]}
        self.assertEqual(got, {"filed_per_attempt.no.fr": 1, "filed_per_attempt.yes.fr": 1})
        self.assertEqual(self.unlock_total("acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK"), 1)
        self.assertEqual(self.unlock_total("acquire.shared.EO_4314"), 1)   # 9011 also needs EO::6868
        self.assertEqual(self.unlock_total("acquire.shared.EO_6868"), 0)
        # every order is assigned to one action at most
        seen = []
        for a in self.out["actions"]:
            seen += [u["orders"] for u in a["unlocks"]]
        self.assertEqual(sum(seen), 1 + 1 + 1 + 1)
        for a in self.out["actions"]:
            for u in a["unlocks"]:
                self.assertTrue({"orders", "rate_key", "delay_days", "basis"} <= set(u))

    def test_yield_lift_actions_count_nothing(self):
        for aid in ("acquire.nea_continuation_notices", "acquire.current_law_sections"):
            self.assertEqual(self.by[aid]["unlocks"], [])
            self.assertIn("overlaps_with", self.by[aid])
        self.assertEqual(self.by["acquire.nea_continuation_notices"]["yield_lift_not_counted"]["orders"], 1)

    def test_zero_agent_and_evidence(self):
        z = self.by["zero_agent.opus_media_refetch"]
        self.assertEqual((z["kind"], z["cost_override_usd"], z["unlocks"]), ("zero_agent", 0, []))
        for a in self.out["actions"]:
            for e in a["evidence"]:
                self.assertIn(e["quote"], (self.root / e["source"]).read_text(encoding="utf-8"))

    def test_output_ids_files_and_hashes(self):
        for a in self.out["actions"]:
            if "order_ids_path" in a:
                p = self.root / a["order_ids_path"]
                self.assertTrue(p.exists())
                self.assertEqual(len(p.read_text().split()), a["orders"])
        self.assertIn(C.TRACKER_CSV, self.out["generated_from"])
        self.assertEqual(len(self.out["generated_from"][C.TRACKER_CSV]), 64)


if __name__ == "__main__":
    unittest.main()
