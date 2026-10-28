"""NORTON factual citations require both review gates and cannot become endings."""
from copy import deepcopy
import csv
import json
import shutil
import sys
import unittest

import assemble as A
import factual_events as F
import test_assemble as fixtures


class FactualEventTests(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.AssemblyTests(methodName="test_complete_claim_passes_real_gate_and_strict_check")
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.repo = self.base.repo
        self.text = "Harbor Board submitted its final report to the President on December 15, 1999."
        (self.repo / "report.txt").write_text(self.text, encoding="utf-8")
        (self.repo / "report.html").write_text(self.text, encoding="utf-8")
        src = {"url": "https://example.gov/report", "sha256": F.MODEL.sha(self.text),
               "raw_path": "report.html", "text_path": "report.txt", "text_sha256": F.MODEL.sha(self.text),
               "page_or_item": "transmittal", "primary": True, "edition": "1999 original",
               "route": "held_primary", "retrieved_utc": "2026-10-20T00:00:00Z"}
        q = {"schema": "norton-question/v1", "entity_id": "Harbor Board established by EO:1", "object": "final report",
             "scope": "report to President", "interval_start": "1999-01-01", "interval_end": "2000-01-01",
             "proposition": "Was the specified final report delivered to the President?", "event_kind": "report_delivery",
             "origin": "owner_seeded"}
        q["question_key"] = F.MODEL.question_key(q)
        evidence = {"schema": "norton-candidate-evidence/v1", "id": "NE:report", "question_key": q["question_key"],
                    "event_kind": q["event_kind"], "entity_id": q["entity_id"], "event_date": "1999-12-15",
                    "source": src, "text": self.text, "char_start": 0, "char_end": len(self.text)}
        clause = dict(self.base.dossier["clauses"][0], instrument_id="EO:1")
        answer = {"schema": "norton-factual-answer/v1", "id": "NFA:report", "question_key": q["question_key"],
                  "producer": "fact-producer", "answer": "The identified final report was delivered to the President on December 15, 1999.",
                  "evidence_ids": [evidence["id"]]}
        app = {"schema": "norton-application/v1", "id": "NA:report", "question_key": q["question_key"],
               "instrument_id": "EO:1", "scope_id": "EO:1#whole", "legal_effect": "unresolved", "state": "ai_reviewed",
               "producer": "app-producer", "answer_id": answer["id"], "clause_evidence": clause,
               "checks": {k: "The exact clause and specific report were examined separately for this application."
                          for k in F.MODEL.CHECKS}}
        def review(record, kind):
            return {"schema": "norton-factual-review/v1", "record_kind": kind, "record_id": record["id"],
                    "record_sha256": F.MODEL.fingerprint(record), "reviewer": "separate-reviewer", "reviewer_type": "independent_ai",
                    "independent": True, "decision": "uphold", "reviewed_on": "2026-10-22", "d6_searched": True,
                    "checked_evidence_ids": record.get("evidence_ids", []),
                    "rationale": "Read the exact source and tested entity, date meaning, scope and competing later-event evidence."}
        ar, pr = review(answer, "answer"), review(app, "application")
        self.registry = {"questions": [q], "evidence": [evidence], "answers": [answer],
                         "applications": [app], "reviews": [ar, pr]}
        self.data = {"application": app, "question": q, "reviewed_answer": dict(answer, review=ar),
                     "application_review": pr, "reviewed_evidence": [evidence], "legal_effect": "unresolved"}
        self.write_registry()

    def write_registry(self):
        root = self.repo / "research/readiness/factual/test"
        root.mkdir(parents=True, exist_ok=True)
        for kind, rows in self.registry.items():
            (root / (kind + ".jsonl")).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    def claim(self):
        events, errors = F.reviewed_events(self.repo, "EO:1", self.data)
        self.assertEqual(errors, [])
        event = events[0]
        self.base.dossier["evidence"][event["id"]] = event
        self.base.refresh()
        self.base.sheet["dossier_sha256"] = self.base.dossier["fingerprint"]
        self.base.sheet["clauses"][0]["later_events"] = [
            {"id": event["id"], "effective_date": event["event_date"], "effective_date_confirmed": True}]
        claim, errors = self.base.assemble()
        self.assertEqual(errors, [])
        return claim, event

    def test_explicit_fact_passes_actual_assembler_and_recheck(self):
        claim, _ = self.claim()
        self.assertEqual(F.claim_errors(claim, self.repo), [])
        self.assertEqual(A.check_claim(claim, self.repo, self.base.dossier), [])
        self.assertEqual(claim["whole_order_end"]["date"], "2000-01-02")
        self.assertEqual(claim["operative_clauses"][0]["later_events"][0]["effective_date"], "1999-12-15")

    def test_pinned_fragment_consumer_packages_fact_without_legal_inference(self):
        import inputs
        import build
        census = self.repo / inputs.UNIVERSE
        census.parent.mkdir(parents=True, exist_ok=True)
        census.write_text("id,included_in_bibliography\nEO:1,1\n", encoding="utf-8")
        out = self.repo / "jobs/norton/output"; out.mkdir(parents=True)
        held = list((self.repo / "research/readiness/factual/test").glob("*.jsonl"))
        held += [self.repo / name for name in ("report.txt", "report.html", "held.txt")]
        pins = {p.relative_to(self.repo).as_posix(): F.MODEL.sha(p.read_bytes()) for p in held}
        (out / "INPUTS.json").write_text(json.dumps({"sha256": pins}), encoding="utf-8")
        (out / "FRAGMENTS.jsonl").write_text(json.dumps({"instrument_id": "EO:1",
            "kind": "shared_factual_obligations", "data": self.data}) + "\n", encoding="utf-8")
        corpus = inputs.load_corpus(self.repo)
        self.assertFalse(corpus["texts"]); self.assertFalse(corpus["pairs"]); self.assertFalse(corpus["current_law"])
        dossier = build.package("EO:1", corpus, {}, None, [], [], {}, [])
        self.assertEqual(len(dossier["factual_event_ids"]), 1)
        event = dossier["evidence"][dossier["factual_event_ids"][0]]
        self.assertEqual(event["role"], F.ROLE)
        self.assertEqual(event["legal_effect"], "unresolved")
        self.assertIsNone(dossier["original_source_id"])
        self.assertFalse(dossier["actor_provisions"]); self.assertFalse(dossier["own_terms"])
        # A still-valid fragment cannot outlive its reviewed source input pin.
        (self.repo / "report.html").write_text("replacement", encoding="utf-8")
        stale = inputs.load_corpus(self.repo)
        self.assertFalse(stale["factual_obligations"])
        self.assertTrue(any("NORTON input changed" in w for w in stale["warnings"]))

    def test_candidate_application_never_becomes_evidence(self):
        data = deepcopy(self.data); data["application"]["state"] = "candidate"
        self.assertEqual(F.reviewed_events(self.repo, "EO:1", data), ([], []))

    def test_answer_review_does_not_substitute_for_application_review(self):
        data = deepcopy(self.data); data["application_review"] = None
        events, errors = F.reviewed_events(self.repo, "EO:1", data)
        self.assertFalse(events); self.assertIn("wrong_review_schema", errors)

    def test_self_review_changed_registry_and_duplicate_records_fail(self):
        for mutate in ("self", "changed", "duplicate"):
            with self.subTest(mutate=mutate):
                data = deepcopy(self.data)
                if mutate == "self": data["application_review"]["reviewer"] = "app-producer"
                elif mutate == "changed": data["reviewed_answer"]["answer"] += " altered"
                else:
                    self.registry["applications"].append(deepcopy(self.registry["applications"][0])); self.write_registry()
                events, errors = F.reviewed_events(self.repo, "EO:1", data)
                self.assertFalse(events); self.assertTrue(errors)

    def test_reviewed_malformed_answer_still_fails_compile_requirements(self):
        for field, value in (("schema", "wrong"), ("producer", ""), ("answer", "Too short")):
            data = deepcopy(self.data)
            original = deepcopy(self.registry["answers"][0]); original[field] = value
            review = deepcopy(self.registry["reviews"][0]); review["record_sha256"] = F.MODEL.fingerprint(original)
            data["reviewed_answer"] = dict(original, review=review)
            self.registry["answers"] = [original]; self.registry["reviews"][0] = review; self.write_registry()
            events, errors = F.reviewed_events(self.repo, "EO:1", data)
            self.assertFalse(events, field); self.assertTrue(errors, field)

    def test_malformed_question_cannot_cross_consumer_boundary(self):
        for field, value in (("schema", "wrong"), ("origin", "unregistered_origin")):
            with self.subTest(field=field):
                data = deepcopy(self.data)
                data["question"][field] = value
                self.registry["questions"] = [data["question"]]; self.write_registry()
                events, errors = F.reviewed_events(self.repo, "EO:1", data)
                self.assertFalse(events); self.assertTrue(errors)

    def test_custody_only_and_changed_bytes_fail(self):
        (self.repo / "report.html").unlink()
        events, errors = F.reviewed_events(self.repo, "EO:1", self.data)
        self.assertFalse(events); self.assertIn("source_bytes_not_held", errors)
        (self.repo / "report.html").write_text("new edition", encoding="utf-8")
        events, errors = F.reviewed_events(self.repo, "EO:1", self.data)
        self.assertFalse(events); self.assertIn("source_bytes_hash_mismatch", errors)

    def test_wrong_entity_event_kind_quote_hash_and_order_fail(self):
        for field, value in (("entity_id", "Another Board"), ("event_kind", "report_publication"),
                             ("text", "Changed quotation"), ("event_date", "2027-01-01")):
            data = deepcopy(self.data); data["reviewed_evidence"][0][field] = value
            events, errors = F.reviewed_events(self.repo, "EO:1", data)
            self.assertFalse(events, field); self.assertTrue(errors, field)
        self.assertFalse(F.reviewed_events(self.repo, "EO:2", self.data)[0])

    def test_fact_cannot_supply_ending_current_basis_savings_or_original(self):
        claim, event = self.claim()
        src = claim["operative_clauses"][0]["later_events"][0]["source"]
        for target in ("first_end", "current_predicate", "savings_residuals", "original_representation"):
            bad = deepcopy(claim)
            if target in ("first_end", "current_predicate"):
                bad["operative_clauses"][0][target] = {"source": src}
            elif target == "savings_residuals": bad[target] = {"source": src}
            else: bad[target] = src
            self.assertTrue(any("cannot_supply_legal_effect" in e for e in F.claim_errors(bad, self.repo)), target)
        self.base.sheet["clauses"][0]["end_id"] = event["id"]
        self.assertIsNone(self.base.assemble()[0])

    def test_citation_cannot_be_repurposed_or_delabeled(self):
        claim, _ = self.claim()
        for field, value in (("effective_date", "2000-01-14"), ("mechanism", "revoke"), ("actor", "Another Board")):
            bad = deepcopy(claim); bad["operative_clauses"][0]["later_events"][0][field] = value
            self.assertIn("factual_event_date_or_meaning_changed", F.claim_errors(bad, self.repo))
        bad = deepcopy(claim); bad["operative_clauses"][0]["scope_id"] = "EO:1#another"
        self.assertIn("factual_event_application_mismatch", F.claim_errors(bad, self.repo))
        bad = deepcopy(claim); del bad["operative_clauses"][0]["later_events"][0]["source"][F.MARKER]
        self.assertIn("factual_event_marker_missing", F.claim_errors(bad, self.repo))

    def test_same_scope_cannot_reuse_application_review_for_changed_clause(self):
        claim, _ = self.claim()
        for field in ("original_operative_text", "quote", "char_start", "sha256", "text_sha256"):
            with self.subTest(field=field):
                bad = deepcopy(claim)
                clause = bad["operative_clauses"][0]
                if field == "original_operative_text": clause[field] += " A different command."
                elif field == "char_start": clause["original_source"][field] += 1
                else: clause["original_source"][field] = "different"
                self.assertIn("factual_event_clause_evidence_mismatch", F.claim_errors(bad, self.repo))

    def test_unchanged_claim_fails_when_raw_source_or_review_changes(self):
        claim, _ = self.claim()
        self.registry["reviews"][0]["decision"] = "reject"; self.write_registry()
        self.assertTrue(F.claim_errors(claim, self.repo))
        self.registry["reviews"][0]["decision"] = "uphold"; self.write_registry()
        (self.repo / "report.txt").write_text("replacement", encoding="utf-8")
        self.assertIn("text_hash_mismatch", F.claim_errors(claim, self.repo))

    def test_actual_checker_blocks_factual_role_bypass_and_changed_review(self):
        # Exercise the independent entry point, not just the shared validator.
        sys.path.insert(0, str(F.HERE.parent / "claim-checker"))
        import checker as checker
        claim, _ = self.claim()
        universe = self.repo / checker.P["universe"]
        universe.parent.mkdir(parents=True, exist_ok=True)
        universe.write_text("id,date_effective\nEO:1,1999\nEO:2,2000\n", encoding="utf-8")
        decided = self.repo / checker.P["decided"]
        decided.parent.mkdir(parents=True, exist_ok=True)
        decided.write_text("instrument_id,provisional_substantive_status\nEO:1,no\n", encoding="utf-8")
        ctx = checker.Context(self.repo, self.repo / "jobs/claim-checker", self.repo / "checker-cache")
        rows, _, _ = checker.check_claim(claim, ctx)
        self.assertFalse([r for r in rows if r["check"] == "factual_event_policy"])
        bad = deepcopy(claim)
        bad["operative_clauses"][0]["first_end"]["source"] = deepcopy(
            bad["operative_clauses"][0]["later_events"][0]["source"])
        rows, errors, status = checker.check_claim(bad, ctx)
        self.assertTrue(any(r["check"] == "factual_event_policy" and r["result"] == "fail" for r in rows))
        summary = checker.summarise_claim("test:1", "test", 1, bad, rows, errors, status, ctx)
        self.assertFalse(summary["all_checks_passed"])
        self.assertFalse(any(s["checker_passed"] for s in summary["steps"].values()))
        self.registry["reviews"][0]["decision"] = "reject"; self.write_registry()
        rows, _, _ = checker.check_claim(claim, ctx)
        self.assertTrue(any(r["check"] == "factual_event_policy" and r["result"] == "fail" for r in rows))

    def test_tracker_revalidates_facts_with_unchanged_claim_and_checker_receipt(self):
        sys.path.insert(0, str(F.HERE.parent / "readiness-tracker"))
        import test_tracker as tracker_fixtures
        tracker = tracker_fixtures.tracker
        fixture = tracker_fixtures.TrackerTest()
        fixture.setUp(); self.addCleanup(fixture.tearDown)
        claim, _ = self.claim()
        shutil.copytree(self.repo, fixture.root, dirs_exist_ok=True)
        with (fixture.root / tracker.P["decided"]).open(encoding="utf-8", newline="") as fh:
            decided = list(csv.DictReader(fh))
        for row in decided:
            if row["instrument_id"] == "EO:1": row["provisional_substantive_status"] = "no"
        tracker_fixtures.write_csv(fixture.root / tracker.P["decided"], decided)
        with (fixture.root / tracker.P["shared"]).open(encoding="utf-8", newline="") as fh:
            shared = [r for r in csv.DictReader(fh) if r["cited_in"] != "EO:1"]
        tracker_fixtures.write_csv(fixture.root / tracker.P["shared"], shared)
        # Existing helper seeds a synthetic matching checker receipt. No legal
        # claim or real reviewer receipt is created by this readiness test.
        orders, _ = fixture.run_tracker([claim])
        self.assertEqual(orders["EO:1"]["ready_for_human_review"], "yes")
        receipt_path = fixture.root / tracker.J["checker"]
        receipt = receipt_path.read_bytes()
        reviews_path = fixture.root / "research/readiness/factual/test/reviews.jsonl"
        held_reviews = reviews_path.read_bytes()
        reviews = [json.loads(line) for line in held_reviews.splitlines()]
        reviews[0]["decision"] = "reject"
        reviews_path.write_text("".join(json.dumps(r) + "\n" for r in reviews), encoding="utf-8")
        for mutation in ("revoked_review", "changed_raw_bytes"):
            with self.subTest(mutation=mutation):
                if mutation == "changed_raw_bytes":
                    reviews_path.write_bytes(held_reviews)
                    (fixture.root / "report.html").write_text("changed report edition", encoding="utf-8")
                rows, _ = tracker.build(str(fixture.root))
                result = next(r for r in rows if r["instrument_id"] == "EO:1")
                self.assertEqual(result["ready_for_human_review"], "no")
                self.assertIn("FACTUAL_EVENT_REVALIDATION_REQUIRED", result["blockers"])
                self.assertTrue(result["factual_event_policy_errors"])
                self.assertEqual(receipt_path.read_bytes(), receipt)


if __name__ == "__main__":
    unittest.main()
