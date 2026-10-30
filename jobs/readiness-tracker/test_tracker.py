"""Tests for tracker.py on a tiny made-up repo, using the project's real claim gate."""

import copy
import hashlib
import io
import csv
import json
import os
import pathlib
import shutil
import sys
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

    def run_tracker(self, claims=(), exhausted=(), checked="all", files=None):
        """checked: "all" = claim-checker passed every step of every claim;
        None = claim-checker has not run; a dict {step: bool} applies to every claim."""
        r = self.root
        with open(r / "research/readiness/claims/test.jsonl", "w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(c) + "\n" for c in claims)
        with open(r / tracker.P["exhausted"], "w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(e) + "\n" for e in exhausted)
        if checked is not None:
            sys.path.insert(0, str(r / "research/stage19/code"))
            import claim_gate  # the project's real gate (copied into the fixture)
            steps = checked if isinstance(checked, dict) else {}
            by = {c["instrument_id"]: {"claim_sha256": claim_gate.claim_sha(c),
                                       "steps_checker_passed": {s: steps.get(s, checked == "all") for s in tracker.STEP_NAMES}}
                  for c in claims}
            self.write(tracker.J["checker"], json.dumps({"by_instrument": by}))
        for path, text in (files or {}).items():
            self.write(path, text)
        orders, problems = tracker.build(str(r))
        return {o["instrument_id"]: o for o in orders}, tracker.summarise(orders, problems)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

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

    def test_claim_steps_need_claim_checker(self):
        orders, _ = self.run_tracker([COMPLETE_NO_CLAIM], checked=None)
        self.assertEqual(orders["EO:2"]["step_clause_inventory"], "open")
        self.assertIn("CLAIM_NOT_YET_CHECKED", orders["EO:2"]["blockers"])
        self.assertEqual(orders["EO:2"]["ready_for_human_review"], "no")

    def test_claim_checker_failure_and_stale_check_keep_steps_open(self):
        orders, _ = self.run_tracker([COMPLETE_NO_CLAIM], checked={"savings_residuals": False, **{
            s: True for s in ("original_text", "clause_inventory", "ending_or_current_basis", "counterevidence")}})
        self.assertEqual(orders["EO:2"]["step_savings_residuals"], "open")
        self.assertIn("CLAIM_CHECK_FAILED:savings_residuals", orders["EO:2"]["blockers"])
        self.assertEqual(orders["EO:2"]["step_clause_inventory"], "done")
        # A claim edited after the last check (different sha) does not count.
        edited = copy.deepcopy(COMPLETE_NO_CLAIM)
        edited["research_rationale"] += " Edited after the check."
        self.write(tracker.J["checker"], json.dumps({"by_instrument": {"EO:2": {
            "claim_sha256": "0" * 64, "steps_checker_passed": {s: True for s in tracker.STEP_NAMES}}}}))
        with open(self.root / "research/readiness/claims/test.jsonl", "w", encoding="utf-8") as fh:
            fh.write(json.dumps(edited) + "\n")
        orders = {o["instrument_id"]: o for o in tracker.build(str(self.root))[0]}
        self.assertIn("CLAIM_NOT_YET_CHECKED", orders["EO:2"]["blockers"])

    def test_fr_originals_high_confidence_counts_and_low_needs_page_check(self):
        frag = lambda i, check: json.dumps({"instrument_id": i, "kind": "original_representation",
                                            "data": {"url": "https://www.govinfo.gov/x.pdf", "needs_page_check": check}})
        orders, s = self.run_tracker(files={tracker.J["fr_fragments"][1]: frag("EO:1", False) + "\n" + frag("EO:3", True) + "\n"})
        self.assertEqual(orders["EO:1"]["step_original_text"], "done")
        self.assertEqual(orders["EO:3"]["step_original_text"], "open")
        self.assertIn("ORIGINAL_FOUND_NEEDS_PAGE_CHECK", orders["EO:3"]["blockers"])
        self.assertNotIn("NO_OFFICIAL_SOURCE_LOCATED", orders["EO:3"]["blockers"])

    def test_official_compilation_counts_like_fr_originals(self):
        def frag(i, check, conf):
            return json.dumps({"instrument_id": i, "kind": "original_representation", "produced_by": "ofr-compilations",
                               "data": {"url": "https://hdl.handle.net/2027/uc1.c025504761", "sha256": "e" * 64,
                                        "page_or_item": "printed page 1", "location_confidence": conf,
                                        "needs_page_check": check}})
        files = {tracker.J["official_compilation_fragments"][0]: frag("EO:1", False, "high") + "\n"
                 + frag("EO:3", True, "medium") + "\n",
                 # a second printing of EO:3 in another volume, also flagged: still not counted
                 tracker.J["official_compilation_fragments"][2]: frag("EO:3", True, "medium") + "\n"}
        orders, s = self.run_tracker(files=files)
        self.assertEqual(orders["EO:1"]["step_original_text"], "done")
        self.assertEqual(orders["EO:3"]["step_original_text"], "open")
        self.assertIn("ORIGINAL_FOUND_NEEDS_PAGE_CHECK", orders["EO:3"]["blockers"])
        self.assertNotIn("NO_OFFICIAL_SOURCE_LOCATED", orders["EO:3"]["blockers"])
        used = tracker.build.job_outputs_used
        self.assertEqual(used["ofr-compilations"], 2)
        self.assertEqual(used["indian-reservations-1912"], 1)
        self.assertIsNone(used["isthmian-canal-1911"])  # that job has not run in this fixture

    def test_official_compilation_without_needs_page_check_flag_does_not_count(self):
        # The fr-originals rule: only needs_page_check exactly False counts; a missing flag is not a pass.
        rec = json.dumps({"instrument_id": "EO:3", "kind": "original_representation",
                          "data": {"url": "https://hdl.handle.net/2027/x", "location_confidence": "high"}})
        orders, _ = self.run_tracker(files={tracker.J["official_compilation_fragments"][1]: rec + "\n"})
        self.assertEqual(orders["EO:3"]["step_original_text"], "open")
        self.assertIn("ORIGINAL_FOUND_NEEDS_PAGE_CHECK", orders["EO:3"]["blockers"])

    def test_richardson_transcription_is_a_lead_never_the_original(self):
        rec = json.dumps({"instrument_id": "EO:3", "kind": "original_representation", "produced_by": "richardson-volumes",
                          "data": {"url": "https://hdl.handle.net/2027/ufl.31262091102953", "sha256": "f" * 64,
                                   "page_or_item": "Richardson vol. VI, printed page 1", "location_confidence": "high",
                                   "needs_page_check": False,
                                   "source_kind": "printed compilation, not the signed original"}})
        files = {tracker.J["compiled_transcription_fragments"][0]: rec + "\n"}
        orders, s = self.run_tracker(files=files)
        self.assertEqual(orders["EO:3"]["step_original_text"], "open")
        self.assertIn("NO_OFFICIAL_SOURCE_LOCATED", orders["EO:3"]["blockers"])
        self.assertIn("ONLY_COMPILED_TRANSCRIPTION_FOUND", orders["EO:3"]["blockers"])
        self.assertEqual(s["decided_orders_blocked_by"]["ONLY_COMPILED_TRANSCRIPTION_FOUND"], 1)
        # Once an official original counts, the transcription lead is no longer reported.
        fr = json.dumps({"instrument_id": "EO:3", "kind": "original_representation",
                         "data": {"url": "https://www.govinfo.gov/x.pdf", "needs_page_check": False}})
        orders, _ = self.run_tracker(files={**files, tracker.J["fr_fragments"][1]: fr + "\n"})
        self.assertEqual(orders["EO:3"]["step_original_text"], "done")
        self.assertNotIn("ONLY_COMPILED_TRANSCRIPTION_FOUND", orders["EO:3"]["blockers"])

    def test_proquest_replica_scan_is_a_lead_that_needs_a_page_check(self):
        rec = json.dumps({"instrument_id": "EO:3", "kind": "original_representation", "produced_by": "pinakes-proquest-ingest",
                          "acceptable_as_original": False, "grade": "archival_replica_scan_pending_codebook",
                          "data": {"url": "https://congressional.proquest.com/congressional/docview/t67.d72.1865-eo-3",
                                   "sha256": "a" * 64, "needs_page_check": True, "text_source": "ocr"}})
        files = {tracker.J["archival_replica_fragments"][0]: rec + "\n"}
        orders, s = self.run_tracker(files=files)
        self.assertEqual(orders["EO:3"]["step_original_text"], "open")
        self.assertIn("ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK", orders["EO:3"]["blockers"])
        self.assertEqual(s["decided_orders_blocked_by"]["ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK"], 1)
        self.assertTrue(any(u["blocker"] == "ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK" and u["kind"] == "agent_check"
                            for u in s["shared_unlocks"]))
        # even a record claiming original-like flags stays a lead
        rec2 = json.dumps({"instrument_id": "EO:3", "kind": "original_representation", "produced_by": "pinakes-proquest-ingest",
                           "data": {"needs_page_check": False, "location_confidence": "high", "acceptable_as_original": True}})
        orders, _ = self.run_tracker(files={tracker.J["archival_replica_fragments"][0]: rec2 + "\n"})
        self.assertEqual(orders["EO:3"]["step_original_text"], "open")
        # once an official original counts, the replica lead is no longer reported
        fr = json.dumps({"instrument_id": "EO:3", "kind": "original_representation",
                         "data": {"url": "https://www.govinfo.gov/x.pdf", "needs_page_check": False}})
        orders, _ = self.run_tracker(files={**files, tracker.J["fr_fragments"][1]: fr + "\n"})
        self.assertEqual(orders["EO:3"]["step_original_text"], "done")
        self.assertNotIn("ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK", orders["EO:3"]["blockers"])

    def test_new_acquisition_feeds_remain_leads_even_with_original_like_flags(self):
        for path in tracker.J["compiled_transcription_fragments"][3:]:
            with self.subTest(path=path):
                rec = json.dumps({'instrument_id':'EO:3', 'kind':'original_representation',
                                  'data':{'needs_page_check':False, 'location_confidence':'high'}})
                orders, _ = self.run_tracker(files={path:rec+'\n'})
                self.assertEqual(orders['EO:3']['step_original_text'],'open')
                self.assertIn('ONLY_COMPILED_TRANSCRIPTION_FOUND',orders['EO:3']['blockers'])

    def test_csc_report_is_a_consumed_lead_never_original_custody(self):
        path = "jobs/csc-annual-reports/output/FRAGMENTS.jsonl"
        self.assertIn(path, tracker.J["compiled_transcription_fragments"])
        record = {"instrument_id": "EO:3", "kind": "original_representation",
                  "produced_by": "csc-annual-reports", "grade": "compiled_transcription_lead",
                  "data": {"needs_page_check": False, "location_confidence": "high"}}
        orders, _ = self.run_tracker(files={path: json.dumps(record) + "\n"})
        self.assertEqual(orders["EO:3"]["step_original_text"], "open")
        self.assertEqual(orders["EO:3"]["ready_for_human_review"], "no")
        self.assertIn("ONLY_COMPILED_TRANSCRIPTION_FOUND", orders["EO:3"]["blockers"])
        self.assertEqual(tracker.build.job_outputs_used[
            "csc-annual-reports (lead only, never counted as the original)"], 1)

    def test_app_transcription_live_and_archive_is_a_lead_never_the_original(self):
        # APP pages, read live or from a web-archive capture, are the same lead-only class as Richardson,
        # even when the record carries needs_page_check=False or a high location confidence.
        def rec(iid, lane):
            return json.dumps({"instrument_id": iid, "kind": "original_representation",
                               "produced_by": "app-executive-orders", "grade": "mirror_transcription",
                               "representation_type": "secondary_compilation_transcription",
                               "acceptable_as_original": False,
                               "data": {"url": "https://www.presidency.ucsb.edu/documents/x", "sha256": "e" * 64,
                                        "route": lane, "needs_page_check": False, "location_confidence": "high",
                                        "acceptable_as_original": False}})
        live, mirror = tracker.J["compiled_transcription_fragments"][1:3]
        files = {live: rec("EO:1", "live") + "\n" + rec("EO:3", "live") + "\n",
                 mirror: rec("EO:3", "archive/common-crawl/american-presidency-project") + "\n"}
        orders, s = self.run_tracker(files=files)
        for i in ("EO:1", "EO:3"):
            self.assertEqual(orders[i]["step_original_text"], "open")
            self.assertIn("ONLY_COMPILED_TRANSCRIPTION_FOUND", orders[i]["blockers"])
        # Both lanes of one job are reported once, as distinct orders.
        self.assertEqual(tracker.build.job_outputs_used[
            "app-executive-orders (lead only, never counted as the original)"], 2)
        unlock = {u["blocker"]: u["orders_unblocked"] for u in s["shared_unlocks"]}
        self.assertEqual(unlock["ONLY_COMPILED_TRANSCRIPTION_FOUND"], 2)
        self.assertEqual(s["step_done_among_decided"]["original_text"]["done"],
                         self.run_tracker()[1]["step_done_among_decided"]["original_text"]["done"])

    def test_source_ladder_retrieval_clears_a_shared_source(self):
        rec = json.dumps({"wanted_id": "STAT::1 Stat. 1", "sha256": "b" * 64, "instrument_ids": ["EO:1", "EO:3"]})
        orders, s = self.run_tracker(files={tracker.J["ladder_sources"][0]: rec + "\n"})
        self.assertEqual(orders["EO:1"]["step_shared_sources"], "done")
        self.assertEqual(orders["EO:3"]["step_shared_sources"], "done")
        self.assertFalse(any(u["blocker"].startswith("SHARED_SOURCE") for u in s["shared_unlocks"]))

    def test_opus_media_uses_opus_media_match_status_when_present(self):
        header = "instrument_id,in_accepted_844,media_status,all_cited_media_resolved,media_gap\n"
        orders, s = self.run_tracker(files={tracker.J["opus_status"]: header + "EO:3,yes,no_member_signal,no,cited_files_not_packaged\n"})
        self.assertEqual(orders["EO:3"]["step_opus_media"], "open")
        self.assertIn("OPUS_MEDIA_REFETCH_NEEDED", orders["EO:3"]["blockers"])
        self.assertNotIn("OPUS_MEDIA_NOT_MATCHED_TO_ORDER", orders["EO:3"]["blockers"])
        orders, _ = self.run_tracker(files={tracker.J["opus_status"]: header + "EO:3,yes,unique_supported,yes,\n"})
        self.assertEqual(orders["EO:3"]["step_opus_media"], "done")

    def test_opus_media_resolved_by_byte_identical_refetch(self):
        header = "instrument_id,in_accepted_844,media_status,all_cited_media_resolved,ambiguous_members,media_gap\n"
        status = header + "EO:3,yes,no_member_signal,no,0,cited_files_not_packaged\n"
        refetch = json.dumps({"url": "https://www.govinfo.gov/a.pdf", "instrument_ids": ["EO:3"], "expected_sha256": "c" * 64})
        good = json.dumps({"wanted_id": "opus-refetch:" + "c" * 64, "sha256": "c" * 64,
                           "expected_sha256": "c" * 64, "matches_expected_sha256": True})
        bad = json.dumps({"wanted_id": "opus-refetch:" + "c" * 64, "sha256": "d" * 64,
                          "expected_sha256": "c" * 64, "matches_expected_sha256": False})
        files = {tracker.J["opus_status"]: status, tracker.J["opus_refetch"]: refetch + "\n"}
        orders, _ = self.run_tracker(files={**files, tracker.J["ladder_sources"][0]: good + "\n"})
        self.assertEqual(orders["EO:3"]["step_opus_media"], "done")
        orders, _ = self.run_tracker(files={**files, tracker.J["ladder_sources"][0]: bad + "\n"})
        self.assertEqual(orders["EO:3"]["step_opus_media"], "open")
        self.assertIn("OPUS_MEDIA_REFETCH_NEEDED", orders["EO:3"]["blockers"])

    def empty_media_files(self, claim=None, status_changes=None, check_changes=None):
        claim = claim or COMPLETE_NO_CLAIM
        rows = list(csv.DictReader((self.root / tracker.P["decided"]).open()))
        for row in rows:
            if row["instrument_id"] == "EO:2":
                row["decision_origin"] = "opus_complete_addition"
        write_csv(self.root / tracker.P["decided"], rows)
        status = {"instrument_id": "EO:2", "media_status": "no_member_signal",
                  "all_cited_media_resolved": "no", "media_gap": "none_cited",
                  **{k: "0" for k in tracker.OPUS_EMPTY_COUNTS}}
        for k, v in (status_changes or {}).items():
            if v is None:
                status.pop(k, None)
            else:
                status[k] = v
        text = io.StringIO()
        writer = csv.DictWriter(text, fieldnames=list(status))
        writer.writeheader(); writer.writerow(status)
        sys.path.insert(0, str(self.root / "research/stage19/code"))
        import claim_gate
        checked = {"claim_sha256": claim_gate.claim_sha(claim), "gate_passed": True,
                   "all_checks_passed": True, "mechanical_result": "pass",
                   "steps_checker_passed": {k: True for k in tracker.CLAIM_EVIDENCE_STEPS}}
        checked.update(check_changes or {})
        return {tracker.J["opus_status"]: text.getvalue(),
                tracker.J["checker"]: json.dumps({"by_instrument": {"EO:2": checked}})}

    def assert_media_gate_remains(self, order):
        self.assertEqual(order["step_opus_media"], "open")
        self.assertEqual(order["opus_media_applicability_note"], "")
        self.assertEqual(order["ready_for_human_review"], "no")

    def test_empty_opus_matching_set_is_disclosed_na_after_independent_claim_checks(self):
        files = self.empty_media_files()
        orders, summary = self.run_tracker([COMPLETE_NO_CLAIM], files=files)
        order = orders["EO:2"]
        self.assertEqual(order["step_opus_media"], "n/a")
        self.assertEqual(order["ready_for_human_review"], "yes")
        self.assertEqual(order["steps_applicable"], 6)
        self.assertEqual(order["exhausted_steps"], "")
        self.assertIn("No media matched or search exhausted", order["opus_media_applicability_note"])
        self.assertEqual(summary["opus_media_not_applicable"], ["EO:2"])
        self.assertNotIn("OPUS_MEDIA_NONE_CITED", order["blockers"])

    def test_empty_media_rule_requires_every_explicit_zero_count(self):
        for key in tracker.OPUS_EMPTY_COUNTS:
            for value in (None, "", "unknown", "-1", "0.0", "1"):
                with self.subTest(key=key, value=value):
                    files = self.empty_media_files(status_changes={key: value})
                    orders, _ = self.run_tracker([COMPLETE_NO_CLAIM], files=files)
                    self.assert_media_gate_remains(orders["EO:2"])

    def test_empty_media_rule_never_exempts_cited_missing_or_ambiguous_media(self):
        for changes in ({"media_gap": "cited_files_not_packaged"},
                        {"media_gap": "originals_not_in_companion"},
                        {"media_status": "ambiguous_only"}, {"ambiguous_members": "1"}):
            with self.subTest(changes=changes):
                files = self.empty_media_files(status_changes=changes)
                orders, _ = self.run_tracker([COMPLETE_NO_CLAIM], files=files)
                self.assert_media_gate_remains(orders["EO:2"])
        files = self.empty_media_files()
        files[tracker.J["opus_refetch"]] = json.dumps({"instrument_ids": ["EO:2"],
            "url": "https://www.govinfo.gov/missing.pdf", "expected_sha256": "b" * 64}) + "\n"
        orders, _ = self.run_tracker([COMPLETE_NO_CLAIM], files=files)
        self.assert_media_gate_remains(orders["EO:2"])

    def test_empty_media_rule_rejects_current_claim_opus_media_dependencies(self):
        for pointer in ("opus_stage11_evidence_originals:original.pdf",
                        "opus_stage11_manifest:original.pdf",
                        "jobs/opus-media-match/output/text/source.txt",
                        "releases/opus_stage11_complete/evidence/image.png"):
            with self.subTest(pointer=pointer):
                claim = copy.deepcopy(COMPLETE_NO_CLAIM)
                claim["original_representation"]["archival_id"] = pointer
                files = self.empty_media_files(claim)
                orders, _ = self.run_tracker([claim], files=files)
                self.assert_media_gate_remains(orders["EO:2"])

    def test_empty_media_rule_rejects_structured_opus_dependencies_without_path_markers(self):
        for changes in ({"opus_media": {"source": SRC}},
                        {"original_representation": {**SRC, "source_type": "opus_media"}},
                        {"original_representation": {**SRC, "source_type": "opus_stage11_manifest"}}):
            with self.subTest(changes=changes):
                claim = {**copy.deepcopy(COMPLETE_NO_CLAIM), **changes}
                orders, _ = self.run_tracker([claim], files=self.empty_media_files(claim))
                self.assert_media_gate_remains(orders["EO:2"])

    def test_empty_media_rule_requires_fresh_complete_checker_receipt(self):
        changes = [{"claim_sha256": "0" * 64}, {"gate_passed": False},
                   {"all_checks_passed": False}, {"mechanical_result": "unverified"}]
        changes += [{"steps_checker_passed": {s: s != missing for s in tracker.CLAIM_EVIDENCE_STEPS}}
                    for missing in tracker.CLAIM_EVIDENCE_STEPS]
        for change in changes:
            with self.subTest(change=change):
                orders, _ = self.run_tracker([COMPLETE_NO_CLAIM], files=self.empty_media_files(check_changes=change))
                self.assert_media_gate_remains(orders["EO:2"])
        files = self.empty_media_files()
        files[tracker.J["checker"]] = json.dumps({"by_instrument": {}})
        orders, _ = self.run_tracker([COMPLETE_NO_CLAIM], files=files)
        self.assert_media_gate_remains(orders["EO:2"])

    def test_empty_media_rule_keeps_incomplete_and_policy_invalid_claims_blocked(self):
        claim = copy.deepcopy(COMPLETE_NO_CLAIM)
        claim["unresolved_material_gaps"] = ["Actual delivery date unresolved"]
        orders, _ = self.run_tracker([claim], files=self.empty_media_files(claim))
        self.assert_media_gate_remains(orders["EO:2"])
        claim = self.working_claim()
        del claim["working_text"]
        orders, _ = self.run_tracker([claim], files=self.empty_media_files(claim))
        self.assert_media_gate_remains(orders["EO:2"])
        self.assertIn("WORKING_TEXT_REVIEW_OR_DISCLOSURE_REQUIRED", orders["EO:2"]["blockers"])

    def test_empty_media_rule_preserves_exact_source_audit_hold(self):
        files = self.empty_media_files()
        import claim_gate
        raw = b"Independent audit: unresolved earlier cessation."
        hold = {"schema": "eo-source-audit-hold/v1", "instrument_id": "EO:2", "state": "unresolved",
                "claim_sha256": claim_gate.claim_sha(COMPLETE_NO_CLAIM), "reason": "earlier end unresolved",
                "review_path": "research/audit.txt", "review_sha256": hashlib.sha256(raw).hexdigest()}
        files.update({"research/audit.txt": raw.decode(),
                      "research/readiness/SOURCE_AUDIT_HOLDS.jsonl": json.dumps(hold) + "\n"})
        orders, _ = self.run_tracker([COMPLETE_NO_CLAIM], files=files)
        self.assert_media_gate_remains(orders["EO:2"])
        self.assertIn("OPEN_SOURCE_AUDIT", orders["EO:2"]["blockers"])
        self.assertEqual(orders["EO:2"]["step_counterevidence"], "open")

    def search_files(self, sample=False):
        le = {"catalog_complete": True, "job_limit": None, "text_documents_scanned": 7619}
        cl = {"sample_mode": sample, "job_limit": None}
        return {
            tracker.J["le_summary"]: json.dumps(le), tracker.J["cl_summary"]: json.dumps(cl),
            tracker.J["le_status"]: json.dumps({"finished_utc": "2026-10-18T00:04:25Z"}),
            tracker.J["cl_status"]: json.dumps({"finished_utc": "2026-10-17T20:28:32Z"}),
            tracker.J["le_catalog"]: "id,post_cutoff\nEO:2,\nEO:3,\nEO:4,\n",
            tracker.J["le_conflicts"]: "instrument_id,lead\n",
            tracker.J["cl_conflicts"]: "instrument_id,signal\nEO:3,1_printed_as_current_text_in_usc\n",
        }

    def test_machine_search_counts_when_complete_and_clean(self):
        orders, s = self.run_tracker(files=self.search_files())
        self.assertEqual(orders["EO:2"]["step_counterevidence"], "done")
        self.assertIn("MACHINE_SEARCH_FOUND_CONTRARY_LEAD:current-law", orders["EO:3"]["blockers"])
        self.assertEqual(orders["EO:3"]["step_counterevidence"], "open")
        self.assertIn("NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE", orders["EO:1"]["blockers"])  # not in the catalog
        recs = tracker.build.machine_search
        self.assertEqual(list(recs), ["EO:2"])
        self.assertEqual(recs["EO:2"][2]["checked_on"], "2026-10-17")
        sys.path.insert(0, str(self.root / "research/stage19/code"))
        import claim_gate  # the record must satisfy the claim gate's bounded_later_search shape
        claim = copy.deepcopy(COMPLETE_NO_CLAIM)
        claim["later_source_search"] = recs["EO:2"]
        self.assertNotIn("bounded_later_search", claim_gate.validate_claim(claim, expected_status="no"))

    def test_machine_search_never_counts_from_a_sample_run(self):
        orders, s = self.run_tracker(files=self.search_files(sample=True))
        self.assertEqual(orders["EO:2"]["step_counterevidence"], "open")
        self.assertTrue(any("incomplete" in p for p in s["input_problems"]))

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

    def test_exact_claim_source_audit_blocks_only_readiness(self):
        sys.path.insert(0,str(self.root/'research/stage19/code'))
        import claim_gate
        raw=b'Independent AI source audit: unresolved earlier end.'
        hold={'schema':'eo-source-audit-hold/v1','instrument_id':'EO:2','state':'unresolved',
              'claim_sha256':claim_gate.claim_sha(COMPLETE_NO_CLAIM),'reason':'first end unresolved',
              'review_path':'research/audit.txt','review_sha256':hashlib.sha256(raw).hexdigest()}
        files={'research/audit.txt':raw.decode(),'research/readiness/SOURCE_AUDIT_HOLDS.jsonl':json.dumps(hold)+'\n'}
        orders,s=self.run_tracker([COMPLETE_NO_CLAIM],files=files)
        self.assertEqual(orders['EO:2']['ready_for_human_review'],'no')
        self.assertEqual(orders['EO:2']['step_ending_or_current_basis'],'done')
        self.assertIn('OPEN_SOURCE_AUDIT',orders['EO:2']['blockers'])
        self.assertEqual(orders['EO:2']['step_counterevidence'],'open')
        self.assertNotIn('counterevidence',orders['EO:2']['exhausted_steps'])
        changed=copy.deepcopy(COMPLETE_NO_CLAIM);changed['research_rationale']+=' Corrected.'
        orders,s=self.run_tracker([changed],files=files)
        self.assertEqual(orders['EO:2']['ready_for_human_review'],'yes')
        self.assertTrue(any('STALE_SOURCE_AUDIT_HOLD' in p for p in s['input_problems']))

    def test_tampered_source_audit_fails_closed(self):
        hold={'schema':'eo-source-audit-hold/v1','instrument_id':'EO:2','state':'unresolved',
              'claim_sha256':'a'*64,'reason':'first end unresolved',
              'review_path':'research/audit.txt','review_sha256':'b'*64}
        with self.assertRaises(ValueError):
            self.run_tracker([COMPLETE_NO_CLAIM],files={'research/audit.txt':'changed',
                'research/readiness/SOURCE_AUDIT_HOLDS.jsonl':json.dumps(hold)+'\n'})


    def working_claim(self):
        claim = copy.deepcopy(COMPLETE_NO_CLAIM)
        text = "The board shall report by June 30, 1950."
        rel = 'jobs/app-executive-orders/output/texts/EO_2.txt'
        self.write(rel, text)
        digest = hashlib.sha256(text.encode()).hexdigest()
        ref = dict(SRC, url='https://example.org/transcription', sha256=digest,
                   instrument_id='EO:2', grade='mirror_transcription', acceptable_as_original=False,
                   text_path=rel, text_sha256=digest, char_start=0, char_end=len(text), quote=text)
        claim['original_representation'] = ref
        claim['operative_clauses'][0]['original_source'] = copy.deepcopy(ref)
        fragment = {'kind':'original_representation', 'instrument_id':'EO:2', 'data':ref}
        self.write('jobs/app-executive-orders/output/FRAGMENTS.jsonl', json.dumps(fragment)+'\n')
        claim['working_text'] = tracker.W.blank([ref])
        claim['working_text']['confirmations'][0].update(identity_confirmed=True, complete_text_confirmed=True)
        return claim

    def test_working_text_ready_tier_retains_source_replacement_and_recheck_debt(self):
        claim = self.working_claim()
        orders, summary = self.run_tracker([claim])
        self.assertEqual(orders['EO:2']['ready_for_human_review'], 'yes')
        self.assertEqual(orders['EO:2']['text_evidence_tier'], 'transcription_dependent')
        self.assertEqual(summary['ready_by_text_evidence_tier'], {'transcription_dependent':1})
        self.assertEqual(summary['original_replacement_obligations'], 1)
        self.assertEqual(summary['quotation_recheck_obligations'], 1)

    def test_working_text_still_needs_other_steps_and_current_checker(self):
        claim = self.working_claim()
        orders, _ = self.run_tracker([claim], checked={'original_text':True})
        self.assertEqual(orders['EO:2']['step_original_text'], 'done')
        self.assertEqual(orders['EO:2']['ready_for_human_review'], 'no')
        self.assertEqual(orders['EO:2']['step_ending_or_current_basis'], 'open')

    def test_working_text_no_disclosure_or_bytes_blocks_even_with_old_checker_pass(self):
        claim = self.working_claim()
        changed = copy.deepcopy(claim); del changed['working_text']
        orders, _ = self.run_tracker([changed])
        self.assertEqual(orders['EO:2']['ready_for_human_review'], 'no')
        self.assertIn('WORKING_TEXT_REVIEW_OR_DISCLOSURE_REQUIRED', orders['EO:2']['blockers'])
        (self.root / claim['original_representation']['text_path']).unlink()
        orders, _ = self.run_tracker([claim])
        self.assertEqual(orders['EO:2']['ready_for_human_review'], 'no')



class ExhaustionAssuranceTests(unittest.TestCase):
    setUp = TrackerTest.setUp
    tearDown = TrackerTest.tearDown
    run_tracker = TrackerTest.run_tracker
    write = TrackerTest.write

    def record(self, step="savings_residuals", **changes):
        return {"instrument_id": "EO:2", "step": step,
                "searched": ["govinfo FR/Statutes: EO 2; APP; NARA and presidential-library catalog routes: no usable item"],
                "recorded_by": "independent-searcher", "recorded_on": "2026-10-17", **changes}

    def partial(self, gaps=None):
        claim = copy.deepcopy(COMPLETE_NO_CLAIM)
        del claim["savings_residuals"]
        claim["unresolved_material_gaps"] = (["Savings sources unavailable after documented route search"]
                                               if gaps is None else gaps)
        return claim

    def test_adopted_status_cannot_be_exhausted(self):
        claim = copy.deepcopy(COMPLETE_NO_CLAIM)
        claim["instrument_id"] = "EO:4"
        claim["unresolved_material_gaps"] = ["Status remains unadopted"]
        orders, summary = self.run_tracker([claim], [self.record("provisional_status", instrument_id="EO:4")])
        row = orders["EO:4"]
        self.assertEqual(row["ready_for_human_review"], "no")
        self.assertEqual(row["step_provisional_status"], "open")
        self.assertIn("NO_PROVISIONAL_STATUS", row["blockers"])
        self.assertTrue(any("bad instrument_id/step" in p for p in summary["input_problems"]))

    def test_no_claim_cannot_disclose_exhaustion(self):
        records = [self.record(s) for s in ("clause_inventory", "ending_or_current_basis", "savings_residuals", "counterevidence")]
        orders, _ = self.run_tracker(exhausted=records, checked=None)
        self.assertEqual(orders["EO:2"]["ready_for_human_review"], "no")
        self.assertIn("EXHAUSTION_GAP_NOT_DISCLOSED_IN_CLAIM", orders["EO:2"]["blockers"])

    def test_missing_or_malformed_gap_disclosure_cannot_earn_credit(self):
        for gaps in ([], "missing savings", [None], [" "], {"savings": "missing"}):
            with self.subTest(gaps=gaps):
                orders, _ = self.run_tracker([self.partial(gaps)], [self.record()])
                self.assertEqual(orders["EO:2"]["ready_for_human_review"], "no")
                self.assertEqual(orders["EO:2"]["step_savings_residuals"], "open")

    def test_documented_disclosed_exhaustion_remains_ready(self):
        orders, _ = self.run_tracker([self.partial()], [self.record()])
        self.assertEqual(orders["EO:2"]["ready_for_human_review"], "yes")
        self.assertEqual(orders["EO:2"]["ready_tier"], "machine_exhausted")

    def test_explicitly_ineligible_ladder_evidence_stays_open(self):
        for fields in ({"note": "WEAK: only mirrors were tried"},
                       {"note": "prefix weak : no official route"},
                       {"result": "retry_later"}, {"outcome": "no_route"}):
            with self.subTest(fields=fields):
                orders, summary = self.run_tracker([self.partial()], [self.record(**fields)])
                self.assertEqual(orders["EO:2"]["ready_for_human_review"], "no")
                self.assertTrue(any("ineligible search evidence" in p for p in summary["input_problems"]))

    def test_prior_retry_discussion_is_not_an_ineligible_marker(self):
        orders, _ = self.run_tracker([self.partial()], [self.record(note="Earlier retry_later was followed by completed definitive route searches.")])
        self.assertEqual(orders["EO:2"]["ready_tier"], "machine_exhausted")

    def test_non_routes_are_rejected_without_crashing(self):
        for searched in ([None], [""], [" "], [{"route": "govinfo"}]):
            with self.subTest(searched=searched):
                orders, _ = self.run_tracker([self.partial()], [self.record(searched=searched)])
                self.assertEqual(orders["EO:2"]["ready_for_human_review"], "no")
        orders, summary = self.run_tracker([self.partial()], [None])
        self.assertEqual(orders["EO:2"]["ready_for_human_review"], "no")
        self.assertTrue(any("must be an object" in p for p in summary["input_problems"]))
        for step in ([], {}):
            with self.subTest(step=step):
                orders, summary = self.run_tracker([self.partial()], [self.record(step=step)])
                self.assertEqual(orders["EO:2"]["ready_for_human_review"], "no")
                self.assertTrue(any("bad instrument_id/step" in p for p in summary["input_problems"]))

    def test_unused_exception_does_not_downgrade_complete_claim(self):
        orders, _ = self.run_tracker([COMPLETE_NO_CLAIM], [self.record()])
        self.assertEqual(orders["EO:2"]["ready_tier"], "complete_claim")
        self.assertEqual(orders["EO:2"]["exhausted_steps"], "")

    def test_all_exhaustion_subsets_preserve_status_and_claim_prerequisites(self):
        # Bounded exhaustive transition check, not a proof of arbitrary inputs
        # or historical truth. Include the prohibited status step in mutations.
        claim = copy.deepcopy(COMPLETE_NO_CLAIM)
        claim["instrument_id"] = "EO:4"
        claim["unresolved_material_gaps"] = ["Unadopted status; isolated engineering fixture"]
        for mask in range(1 << len(tracker.STEP_NAMES)):
            steps = [s for bit, s in enumerate(tracker.STEP_NAMES) if mask & (1 << bit)]
            with self.subTest(mask=mask):
                records = [self.record(s, instrument_id="EO:4") for s in steps]
                orders, _ = self.run_tracker([claim], records)
                self.assertEqual(orders["EO:4"]["ready_for_human_review"], "no")
                self.assertEqual(orders["EO:4"]["step_provisional_status"], "open")
                orders, _ = self.run_tracker(exhausted=[self.record(s) for s in steps], checked=None)
                self.assertEqual(orders["EO:2"]["ready_for_human_review"], "no")


if __name__ == "__main__":
    unittest.main()
