"""Tests for tracker.py on a tiny made-up repo, using the project's real claim gate."""

import copy
import csv
import json
import os
import pathlib
import shutil
import tempfile
import unittest

import tracker

REAL_ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = {"url": "https://www.govinfo.gov/x.pdf", "sha256": "a" * 64, "page_or_item": "p. 1"}

COMPLETE_NO_CLAIM = {
    "schema": "eo-lifecycle-claim/v1",
    "instrument_id": "EO:2",
    "whole_order_status": "no",
    "original_representation": SRC,
    "operative_clauses": [{
        "scope_id": "s1",
        "original_operative_text": "The board shall report by June 30, 1950.",
        "original_source": SRC,
        "state_at_cutoff": "terminated",
        "first_end": {"date": "1950-06-30", "actor": "board", "mechanism": "own end date", "source": SRC},
        "later_events": [],
    }],
    "whole_order_end": {"date": "1950-06-30", "actor": "board", "mechanism": "own end date", "source": SRC},
    "savings_residuals": {"state": "none_after_bounded_search", "reason": "No savings clause.", "source": SRC},
    "later_source_search": [{"repository": "govinfo", "query_or_scope": "EO 2 citations", "checked_on": "2026-10-17"}],
    "unresolved_material_gaps": [],
    "research_rationale": "The order's only clause ended by its own terms on June 30, 1950.",
}


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class TrackerTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        r = self.root
        shutil.copytree(REAL_ROOT / "research/stage19/code", r / "research/stage19/code",
                        ignore=shutil.ignore_patterns("test_*", "__pycache__"))
        write_csv(r / tracker.P["universe"], [{"id": f"EO:{n}", "included_in_bibliography": "1"} for n in (1, 2, 3, 4)])
        write_csv(r / tracker.P["decided"], [
            {"instrument_id": "EO:1", "provisional_substantive_status": "yes", "decision_origin": "inherited_legacy_v2"},
            {"instrument_id": "EO:2", "provisional_substantive_status": "no", "decision_origin": "inherited_legacy_v2"},
            {"instrument_id": "EO:3", "provisional_substantive_status": "no", "decision_origin": "opus_checkpoint2"},
        ])
        write_csv(r / tracker.P["causal"], [
            {"instrument_id": "EO:1", "locally_preserved_primary_representation": "0", "quarantined_relationship_count": "0"},
            {"instrument_id": "EO:2", "locally_preserved_primary_representation": "1", "quarantined_relationship_count": "0"},
            {"instrument_id": "EO:3", "locally_preserved_primary_representation": "0", "quarantined_relationship_count": "2"},
        ])
        write_csv(r / tracker.P["crosswalk"], [
            {"instrument_id": "EO:1", "selected_literal_URL": "https://www.govinfo.gov/eo1.pdf"},
            {"instrument_id": "EO:3", "selected_literal_URL": ""},
        ])
        write_csv(r / tracker.P["custody"], [{"instrument_id": "EO:9", "custody_state": "not_attempted"}])
        write_csv(r / tracker.P["shared"], [
            {"authority": "STAT::1 Stat. 1", "cited_in": "EO:1", "source_already_retrieved": "no"},
            {"authority": "STAT::1 Stat. 1", "cited_in": "EO:3", "source_already_retrieved": "no"},
            {"authority": "STAT::2 Stat. 2", "cited_in": "EO:3", "source_already_retrieved": "no"},
        ])
        write_csv(r / tracker.P["statute"], [{"source_key": "STAT::2 Stat. 2", "instrument_id": "EO:3", "acquired_pdf_bytes": "yes"}])
        write_csv(r / tracker.P["media"], [{"association_grade": "no_case_specific_evidence", "example_case_ids": "EO:3"}])
        (r / "research/readiness/claims").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_tracker(self, claims=(), exhausted=()):
        r = self.root
        with open(r / "research/readiness/claims/test.jsonl", "w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(c) + "\n" for c in claims)
        with open(r / tracker.P["exhausted"], "w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(e) + "\n" for e in exhausted)
        orders, problems = tracker.build(str(r))
        return {o["instrument_id"]: o for o in orders}, tracker.summarise(orders, problems)

    def test_without_claims_nothing_is_ready_and_blockers_are_specific(self):
        orders, s = self.run_tracker()
        self.assertEqual(s["ready_for_human_review"], 0)
        self.assertEqual(s["orders_with_provisional_status"], 3)
        self.assertIn("OFFICIAL_URL_KNOWN_NOT_DOWNLOADED", orders["EO:1"]["blockers"])
        self.assertIn("NO_OFFICIAL_SOURCE_LOCATED", orders["EO:3"]["blockers"])
        self.assertEqual(orders["EO:2"]["step_original_text"], "done")
        self.assertIn("CURRENT_BASIS_UNPROVED", orders["EO:1"]["blockers"])
        self.assertIn("QUARANTINED_RELATIONSHIP_CONFLICT", orders["EO:3"]["blockers"])
        self.assertEqual(orders["EO:3"]["step_opus_media"], "open")
        self.assertEqual(orders["EO:1"]["step_opus_media"], "n/a")
        self.assertEqual(orders["EO:4"]["blockers"], "NO_PROVISIONAL_STATUS|NO_OFFICIAL_SOURCE_LOCATED")
        self.assertEqual(s["decided_orders_blocked_by"]["FIRST_END_UNPROVED"], 2)

    def test_shared_sources_group_into_one_unlock_and_retrieved_statutes_count(self):
        orders, s = self.run_tracker()
        unlock = {u["blocker"]: u["orders_unblocked"] for u in s["shared_unlocks"]}
        self.assertEqual(unlock["SHARED_SOURCE_NOT_RETRIEVED:STAT::1 Stat. 1"], 2)
        self.assertNotIn("SHARED_SOURCE_NOT_RETRIEVED:STAT::2 Stat. 2", unlock)
        self.assertEqual(orders["EO:2"]["step_shared_sources"], "n/a")

    def test_complete_claim_makes_an_order_ready(self):
        orders, s = self.run_tracker([COMPLETE_NO_CLAIM])
        self.assertEqual(orders["EO:2"]["ready_for_human_review"], "yes", orders["EO:2"])
        self.assertEqual(orders["EO:2"]["ready_tier"], "complete_claim")
        self.assertEqual(s["ready_for_human_review"], 1)

    def test_partial_claim_lights_up_only_the_steps_it_satisfies(self):
        claim = copy.deepcopy(COMPLETE_NO_CLAIM)
        del claim["savings_residuals"]
        orders, _ = self.run_tracker([claim])
        o = orders["EO:2"]
        self.assertEqual(o["step_clause_inventory"], "done")
        self.assertEqual(o["step_ending_or_current_basis"], "done")
        self.assertEqual(o["step_savings_residuals"], "open")
        self.assertIn("CLAIM_INCOMPLETE:savings_residuals", o["blockers"])
        self.assertEqual(o["ready_for_human_review"], "no")

    def test_exhausted_step_counts_as_machine_finished(self):
        claim = copy.deepcopy(COMPLETE_NO_CLAIM)
        del claim["savings_residuals"]
        claim["unresolved_material_gaps"] = ["savings: no later source found"]
        record = {"instrument_id": "EO:2", "step": "savings_residuals", "searched": ["govinfo: EO 2"],
                  "recorded_by": "Opus", "recorded_on": "2026-10-17"}
        orders, s = self.run_tracker([claim], [record])
        self.assertEqual(orders["EO:2"]["ready_tier"], "machine_exhausted")
        self.assertEqual(s["ready_by_tier"], {"machine_exhausted": 1})

    def test_claim_with_no_clauses_lights_no_claim_step(self):
        claim = copy.deepcopy(COMPLETE_NO_CLAIM)
        claim["operative_clauses"] = []
        orders, _ = self.run_tracker([claim])
        o = orders["EO:2"]
        for step in ("clause_inventory", "ending_or_current_basis", "savings_residuals", "counterevidence"):
            self.assertEqual(o[f"step_{step}"], "open", step)

    def test_status_mismatch_keeps_the_ending_step_open(self):
        claim = copy.deepcopy(COMPLETE_NO_CLAIM)
        claim["instrument_id"] = "EO:1"  # EO:1 is provisionally YES
        orders, _ = self.run_tracker([claim])
        self.assertEqual(orders["EO:1"]["step_ending_or_current_basis"], "open")
        self.assertEqual(orders["EO:1"]["ready_for_human_review"], "no")

    def test_bad_exhausted_record_is_reported_not_counted(self):
        orders, s = self.run_tracker([], [{"instrument_id": "EO:2", "step": "savings_residuals", "searched": []}])
        self.assertEqual(orders["EO:2"]["step_savings_residuals"], "open")
        self.assertTrue(any("EXHAUSTED.jsonl" in p for p in s["input_problems"]))


if __name__ == "__main__":
    unittest.main()
