"""Synthetic coverage for offline discovery, attribution and census boundaries."""

import csv
import hashlib
import json
import pathlib
import tempfile
import unittest
from unittest import mock

import inputs


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name)
        self.write_csv(inputs.UNIVERSE, [
            {"id": "EO:1", "included_in_bibliography": "1"},
            {"id": "EO:2", "included_in_bibliography": "1"},
            {"id": "EO:3A", "included_in_bibliography": "1"},
            {"id": "EO:UN:catalog:1", "included_in_bibliography": "1"},
            {"id": "EO:999", "included_in_bibliography": "0"},
        ])

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_csv(self, rel, rows):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def jsonl(self, rel, records):
        return self.write(rel, "".join(json.dumps(r) + "\n" for r in records))

    def source(self, **extra):
        return {"url": "https://example.test/official.pdf", "sha256": "a" * 64,
                "page_or_item": "PDF page 2", **extra}

    def original(self, iid="EO:1", path="texts/one.txt", **extra):
        return {"instrument_id": iid, "kind": "original_representation", "data": {
            **self.source(), "text_path": path, "signing_date": "1900-01-01", **extra}}

    def test_census_required_and_not_inferred_from_sources(self):
        (self.repo / inputs.UNIVERSE).unlink()
        self.jsonl("jobs/new/output/FRAGMENTS.jsonl", [self.original()])
        with self.assertRaisesRegex(FileNotFoundError, "authoritative census"):
            inputs.load_corpus(self.repo)

    def test_family_proof_counterexamples_do_not_become_originals_of_target(self):
        text = self.write('jobs/rules/output/actor.txt', 'A different order supplies this proof.\n')
        self.jsonl('jobs/rules/output/FRAGMENTS.jsonl', [{
            'instrument_id':'EO:1', 'kind':'family_rule_checks',
            'sources':[self.source(text_sha256=hashlib.sha256(text.read_bytes()).hexdigest())],
            'data':{'counterexamples':[{'text_path':'actor.txt'}]}}])
        corpus = inputs.load_corpus(self.repo)
        self.assertEqual(corpus['texts'], [])
        self.assertEqual(corpus['pairs'], [])

    def test_shared_facts_stay_out_of_originals_events_and_predicates(self):
        p=self.write('research/readiness/factual/producer/questions.jsonl','held registry\n')
        self.write('jobs/norton/output/INPUTS.json',json.dumps({'sha256':{p.relative_to(self.repo).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()}}))
        data={'legal_effect':'unresolved','factual_review_status':'ai_reviewed',
              'reviewed_answer':{'text_path':'research/primary.txt','text':'An outside institution completed its report.'}}
        self.jsonl('jobs/norton/output/FRAGMENTS.jsonl',[{'instrument_id':'EO:1','kind':'shared_factual_obligations','data':data}])
        c=inputs.load_corpus(self.repo)
        self.assertEqual(1,len(c['factual_obligations']['EO:1']))
        self.assertEqual([],c['texts']);self.assertEqual([],c['pairs']);self.assertEqual({},c['current_law'])
        p.write_text('changed registry\n')
        c=inputs.load_corpus(self.repo);self.assertEqual({},c['factual_obligations'])
        self.assertTrue(any('NORTON input changed' in w for w in c['warnings']))

    def test_rebuilding_own_terms_does_not_destroy_independently_pinned_facts(self):
        registry=self.write('research/readiness/factual/producer/questions.jsonl','bound question\n')
        old_terms=self.write('jobs/claim-kit/output/OWN_TERMS.jsonl','prior census generation\n')
        key=registry.relative_to(self.repo).as_posix();digest=hashlib.sha256(registry.read_bytes()).hexdigest()
        prior={old_terms.relative_to(self.repo).as_posix():hashlib.sha256(old_terms.read_bytes()).hexdigest()}
        self.write('jobs/norton/output/INPUTS.json',json.dumps({'sha256':{key:digest,**prior},
                    'consumer_sha256':{key:digest},'lagged_census_sha256':prior}))
        self.jsonl('jobs/norton/output/FRAGMENTS.jsonl',[{'instrument_id':'EO:1','kind':'shared_factual_obligations',
                    'data':{'legal_effect':'unresolved','factual_review_status':'candidate'}}])
        old_terms.unlink()  # Real build.py removes this before load_corpus.
        self.assertEqual(1,len(inputs.load_corpus(self.repo)['factual_obligations']['EO:1']))
        registry.write_text('changed question\n')
        self.assertEqual({},inputs.load_corpus(self.repo)['factual_obligations'])

    def test_empty_census_and_duplicate_identity_fail(self):
        self.write_csv(inputs.UNIVERSE, [{"id": "EO:1", "included_in_bibliography": "0"}])
        with self.assertRaisesRegex(ValueError, "empty authoritative"):
            inputs.load_corpus(self.repo)
        self.write_csv(inputs.UNIVERSE, [{"id": "EO:1"}, {"id": "EO:1"}])
        with self.assertRaisesRegex(ValueError, "duplicate census"):
            inputs.load_corpus(self.repo)

    def test_statuses_come_only_from_authoritative_csv(self):
        self.write_csv(inputs.STATUSES, [
            {"instrument_id": "EO:1", "provisional_substantive_status": "no"},
            {"instrument_id": "EO:2", "provisional_substantive_status": "UNKNOWN"},
            {"instrument_id": "EO:999", "provisional_substantive_status": "yes"},
        ])
        self.jsonl("jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl", [
            {"instrument_id": "EO:1", "claim": {"whole_order_status": "yes"},
             "_draft": {"provisional_status": "yes"}},
            {"instrument_id": "EO:2", "claim": {"whole_order_status": "no"},
             "_draft": {"provisional_status": "no"}},
        ])
        corpus = inputs.load_corpus(self.repo)
        self.assertEqual(corpus["statuses"], {"EO:1": "no"})
        self.assertEqual(len(corpus["universe"]), 4)
        self.assertTrue(any("differs from authoritative" in w for w in corpus["warnings"]))

    def test_fallback_only_explicit_provisional_status(self):
        self.jsonl("jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl", [
            {"instrument_id": "EO:1", "claim": {"whole_order_status": "yes"}, "_draft": {}},
            {"instrument_id": "EO:2", "claim": {}, "_draft": {"provisional_status": "no"}},
            {"instrument_id": "EO:3A", "claim": {}, "_draft": {"provisional_status": "UNKNOWN"}},
            {"instrument_id": "EO:999", "claim": {}, "_draft": {"provisional_status": "yes"}},
        ])
        corpus = inputs.load_corpus(self.repo)
        self.assertEqual(corpus["statuses"], {"EO:2": "no"})
        self.assertEqual(set(corpus["drafts"]), {"EO:1", "EO:2", "EO:3A"})

    def test_all_text_variants_are_lazy_and_hashed(self):
        first = self.write("jobs/unregistered/output/texts/one.txt", "Section 1. A.\r\n")
        self.write("jobs/unregistered/output/texts/two.txt", "Section 1. B.")
        self.write("jobs/unregistered/data/full_run/texts/one.txt", "Earlier OCR variant.")
        self.jsonl("jobs/unregistered/output/FRAGMENTS.jsonl", [self.original()])
        self.jsonl("jobs/unregistered/output/FRAGMENTS.more.jsonl", [self.original(path="texts/two.txt")])
        self.jsonl("jobs/unregistered/data/full_run/FRAGMENTS.jsonl", [self.original()])
        with mock.patch("socket.socket", side_effect=AssertionError("network forbidden")):
            corpus = inputs.load_corpus(self.repo)
        self.assertEqual(len(corpus["texts"]), 3)
        self.assertEqual({r["instrument_id"] for r in corpus["texts"]}, {"EO:1"})
        self.assertTrue(all("text" not in record for record in corpus["texts"]))
        record = next(r for r in corpus["texts"] if r["text_path"] == first.relative_to(self.repo).as_posix())
        self.assertEqual(record["source"]["text_sha256"], hashlib.sha256(first.read_bytes()).hexdigest())
        self.assertEqual(record["source"]["sha256"], "a" * 64)
        self.assertTrue(record["acceptable_as_original"])
        self.assertEqual(corpus, inputs.load_corpus(self.repo))

    def test_provenance_nested_declares_new_producer_without_registry(self):
        self.write("jobs/future-book/data/order.txt", "A new held order.")
        prov = {"arbitrary": {"layers": [{
            "instrument_id": "EO:UN:catalog:1", "path": "data/order.txt",
            "source": self.source(), "grade": "official_compilation_high",
            "acceptable_as_original": True, "filing_date": "1900-01-02",
        }]}}
        self.write("jobs/future-book/data/PROVENANCE.json", json.dumps(prov))
        corpus = inputs.load_corpus(self.repo)
        self.assertEqual(len(corpus["texts"]), 1)
        row = corpus["texts"][0]
        self.assertEqual(row["instrument_id"], "EO:UN:catalog:1")
        self.assertEqual(row["filing_date"], "1900-01-02")
        self.assertEqual(row["grade"], "official_compilation_high")
        self.assertTrue(row["acceptable_as_original"])

    def test_provenance_can_register_external_fragment_pack(self):
        self.write("jobs/future/data/pack/order.txt", "Held order.")
        self.jsonl("jobs/future/data/pack/new-records.jsonl", [self.original(path="order.txt")])
        self.write("jobs/future/data/PROVENANCE.json", json.dumps({
            "new_source": {"fragments_path": "data/pack/new-records.jsonl"}}))
        self.assertEqual(len(inputs.load_corpus(self.repo)["texts"]), 1)

    def test_provenance_source_object_can_carry_the_text_pointer(self):
        self.write("jobs/future/data/order.txt", "A declared source text.")
        self.write("jobs/future/data/PROVENANCE.json", json.dumps({"texts": [{
            "instrument_id": "EO:1", "source": self.source(text_path="data/order.txt"),
            "grade": "custom_official", "acceptable_as_original": True}]}))
        records = inputs.load_corpus(self.repo)["texts"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["text_path"], "jobs/future/data/order.txt")

    def test_derivatives_and_explicit_false_never_become_originals(self):
        self.write("jobs/new/output/texts/one.txt", "Derivative.")
        self.jsonl("jobs/new/output/FRAGMENTS.jsonl", [
            self.original(grade="compiled_transcription_lead", acceptable_as_original=True),
            self.original(iid="EO:2", grade="custom_derivative", acceptable_as_original=False),
        ])
        records = inputs.load_corpus(self.repo)["texts"]
        self.assertEqual(len(records), 2)
        self.assertTrue(all(not r["acceptable_as_original"] for r in records))

    def test_fr_original_needs_page_check_preserves_locator_warning(self):
        self.write("jobs/fr-originals/output/texts/one.txt", "Located OCR text.")
        self.jsonl("jobs/fr-originals/output/FRAGMENTS.jsonl", [self.original(
            needs_page_check=True, location_confidence="medium", location_verified=False,
            confidence="medium")])
        record = inputs.load_corpus(self.repo)["texts"][0]
        self.assertTrue(record["acceptable_as_original"])
        self.assertTrue(record["requires_page_check"])
        self.assertIn("needs_page_check", record["grade"])
        self.assertEqual(record["location_confidence"], "medium")
        self.assertEqual(record["confidence"], "medium")
        self.assertFalse(record["location_verified"])
        self.assertTrue(record["source"]["requires_page_check"])
        self.assertEqual(record["source"]["location_confidence"], "medium")

    def test_provisional_replica_keeps_exact_grade_with_page_debt(self):
        self.write('jobs/pinakes-proquest-ingest/output/texts/one.txt','Held replica text.')
        grade = 'archival_replica_scan_pending_codebook'
        self.jsonl('jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl',[
            self.original(grade=grade,acceptable_as_original=False,needs_page_check=True,
                          location_confidence='medium',location_verified=False)])
        record = inputs.load_corpus(self.repo)['texts'][0]
        self.assertEqual(record['grade'],grade)
        self.assertEqual(record['source']['grade'],grade)
        self.assertFalse(record['source']['acceptable_as_original'])
        self.assertTrue(record['source']['requires_page_check'])

    def test_ungraded_wrapper_keeps_named_transcription_grade_for_working_text(self):
        # A wrapper that names its provenance grade only in its notes must keep that exact grade; the
        # catch-all "derivative_lead" is not an accepted working-text grade under the 2026-10-21 ruling.
        for named, expected in (("mirror_transcription", "mirror_transcription"),
                                ("compiled_transcription_lead", "compiled_transcription_lead"),
                                ("as amended editorial text", "derivative_lead")):
            self.assertEqual(inputs._grade({"confidence_note": f"APP copy ({named})"}, None, True, "x")[0], expected)
            self.assertFalse(inputs._grade({"confidence_note": f"APP copy ({named})"}, None, True, "x")[1])
        self.assertEqual(inputs._grade({"grade": "official"}, None, True, "x")[0], "official")

    def test_fr_original_low_locator_inherits_through_nested_wrapper(self):
        self.write("jobs/fr-originals/output/texts/one.txt", "Located OCR text.")
        fragment = {"instrument_id": "EO:1", "kind": "original_representation",
                    "location_confidence": "low", "confidence": "low",
                    "data": {"nested": {**self.source(), "text_path": "texts/one.txt",
                                         "needs_page_check": False}}}
        self.jsonl("jobs/fr-originals/output/FRAGMENTS.jsonl", [fragment])
        record = inputs.load_corpus(self.repo)["texts"][0]
        self.assertTrue(record["requires_page_check"])
        self.assertEqual(record["location_confidence"], "low")
        self.assertEqual(record["source"]["confidence"], "low")
        self.assertIn("needs_page_check", record["grade"])

    def test_shared_volume_and_excluded_identity_not_assigned_wholesale(self):
        self.write("jobs/new/output/book.txt", "Contains several orders.")
        self.jsonl("jobs/new/output/SOURCES.jsonl", [
            {**self.source(), "text_path": "book.txt", "instrument_ids": ["EO:1", "EO:2"]},
            {**self.source(), "text_path": "book.txt", "instrument_ids": ["EO:999"]},
        ])
        self.write("jobs/new/data/PROVENANCE.json", json.dumps({"volumes": [{
            "pdf": "releases/source_books/book.pdf", "pdf_sha256": "a" * 64,
            "text": "output/book.txt", "handle_url": "https://example.test/book"}]}))
        self.assertEqual(inputs.load_corpus(self.repo)["texts"], [])

    def test_sources_and_clause_offset_declarations_preserve_attribution(self):
        self.write("jobs/new/output/order.txt", "A complete order.")
        self.jsonl("jobs/new/output/SOURCES.jsonl", [
            {**self.source(), "text_path": "order.txt", "instrument_ids": ["EO:2"]}])
        self.jsonl("jobs/new/output/FRAGMENTS.jsonl", [{
            "instrument_id": "EO:1", "kind": "operative_clauses", "source_grade": "official_fr_scan_ocr_text",
            "data": [{"scope_id": "EO:1#whole", "original_source": self.source(),
                      "text_offsets": {"text_path": "order.txt", "start": 0, "end": 17}}]}])
        records = inputs.load_corpus(self.repo)["texts"]
        self.assertEqual({r["instrument_id"] for r in records}, {"EO:1", "EO:2"})
        self.assertEqual(next(r for r in records if r["instrument_id"] == "EO:1")["grade"],
                         "official_fr_scan_ocr_text")

    def test_unsafe_paths_and_symlink_escapes_rejected(self):
        outside = pathlib.Path(self.tmp.name).parent / (self.repo.name + "-outside.txt")
        outside.write_text("secret", encoding="utf-8")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        link = self.repo / "jobs/new/output/escape.txt"
        link.parent.mkdir(parents=True, exist_ok=True)
        has_symlink=True
        try:link.symlink_to(outside)
        except OSError as exc:
            if getattr(exc,'winerror',None)!=1314:raise
            has_symlink=False  # Windows runner lacks link privilege; retain literal-path checks.
        self.jsonl("jobs/new/output/FRAGMENTS.jsonl", [
            self.original(path="../../../../outside.txt"), self.original(path=str(outside)),
            self.original(path="C:\\secret.txt"), *([self.original(path="escape.txt")] if has_symlink else [])])
        corpus = inputs.load_corpus(self.repo)
        self.assertEqual(corpus["texts"], [])
        self.assertEqual(sum("unsafe text path" in w for w in corpus["warnings"]), 4 if has_symlink else 3)

    def test_safe_cross_directory_links_and_repo_relative_paths(self):
        self.write("jobs/new/data/order.txt", "Held.")
        self.jsonl("jobs/new/output/FRAGMENTS.jsonl", [self.original(path="../data/order.txt")])
        self.jsonl("jobs/other/output/FRAGMENTS.jsonl", [
            self.original(path="jobs/new/data/order.txt", iid="EO:2")])
        self.assertEqual(len(inputs.load_corpus(self.repo)["texts"]), 2)

    def test_unavailable_lfs_bad_hash_and_missing_provenance_are_warnings(self):
        self.write("jobs/new/output/order.txt", "Held.")
        self.write("jobs/new/output/pointer.txt", inputs.LFS_MAGIC.decode() + "\noid sha256:" + "b" * 64)
        self.jsonl("jobs/new/output/FRAGMENTS.jsonl", [
            self.original(path="missing.txt"), self.original(path="pointer.txt"),
            self.original(path="order.txt", text_sha256="f" * 64),
            self.original(path="order.txt", sha256=None),
            self.original(path="order.txt", url=None),
        ])
        corpus = inputs.load_corpus(self.repo)
        self.assertEqual(corpus["texts"], [])
        warnings = " ".join(corpus["warnings"])
        for phrase in ("missing", "LFS pointer", "text_sha256 mismatch", "lacks original-byte", "lacks source URL"):
            self.assertIn(phrase, warnings)

    def test_pairs_from_fragments_drafts_edges_and_parent_only_exact_ids(self):
        event = {"actor": "EO:2", "mechanism": "revocation", "source": self.source(),
                 "parent_id": "EO:3A"}
        self.jsonl("jobs/new/output/FRAGMENTS.jsonl", [{
            "instrument_id": "EO:1", "kind": "later_event_candidates", "data": [
                event, {"actor": "EO 2"}, {"actor": "EO:999"}, {"actor": "EO:1"}]}])
        self.write_csv("jobs/new/output/EDGES.csv", [{
            "target_id": "EO:3A", "acting_id": "EO:2", "mechanism": "amendment"}])
        self.jsonl("jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl", [{
            "instrument_id": "EO:1", "claim": {}, "_draft": {"proposals": {
                "whole_order_end": [{"proposal": {"actor": "EO:3A"}, "meta": {}}]}}}])
        pairs = inputs.load_corpus(self.repo)["pairs"]
        self.assertEqual({(p["target_id"], p["actor_id"]) for p in pairs},
                         {("EO:1", "EO:2"), ("EO:1", "EO:3A"), ("EO:3A", "EO:2")})
        self.assertEqual(next(p for p in pairs if p["actor_id"] == "EO:2" and p["target_id"] == "EO:1")["parent_id"],
                         "EO:3A")

    def test_current_law_and_machine_search_scope_are_leads(self):
        fragment = {"instrument_id": "EO:1", "kind": "current_predicate_candidates",
                    "data": [{"legal_basis": "Editorial snapshot, not a conclusion."}]}
        search = {"search_id": "example:search", "entry": {"repository": "Example"},
                  "complete": False, "scope_note": "sample only"}
        self.jsonl("jobs/new/output/FRAGMENTS.jsonl", [fragment])
        self.write("jobs/claim-drafts/output/SUMMARY.json", json.dumps({"machine_searches": [search]}))
        corpus = inputs.load_corpus(self.repo)
        self.assertEqual(corpus["current_law"]["EO:1"][0]["legal_basis"],
                         "Editorial snapshot, not a conclusion.")
        self.assertTrue(corpus["current_law"]["EO:1"][0]["machine_lead"])
        self.assertEqual(corpus["machine_searches"], {"example:search": search})
        self.assertEqual(corpus["statuses"], {})

    def test_law_and_actor_text_are_not_attributed_to_the_affected_order(self):
        self.write("jobs/new/output/statute.txt", "A statute that names EO 1.")
        self.write("jobs/new/output/actor.txt", "EO 2 revokes EO 1.")
        self.jsonl("jobs/new/output/FRAGMENTS.jsonl", [
            {"instrument_id": "EO:1", "kind": "current_predicate_candidates", "data": [{
                "source": self.source(), "text_path": "statute.txt", "text": "A statute",
                "char_start": 0, "char_end": 9}]},
            {"instrument_id": "EO:1", "kind": "later_event_candidates", "data": [{
                "actor": "EO:2", "source": self.source(), "text_path": "actor.txt"}]},
        ])
        corpus = inputs.load_corpus(self.repo)
        self.assertEqual(corpus["texts"], [])
        self.assertEqual(corpus["current_law"]["EO:1"][0]["source"]["text_path"],
                         "jobs/new/output/statute.txt")
        self.assertEqual(corpus["current_law"]["EO:1"][0]["char_end"], 9)

    def test_draft_original_and_clause_pointers_can_locate_held_texts(self):
        self.write("jobs/producer/output/order.txt", "Complete text.")
        self.write("jobs/clauses/output/copy.txt", "Clause copy.")
        self.jsonl("jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl", [{
            "instrument_id": "EO:1", "claim": {"operative_clauses": [
                {"scope_id": "EO:1#whole", "original_source": self.source()}]},
            "_draft": {"proposals": {"original_representation": [{
                "from": "producer@jobs/producer/output", "text_path": "order.txt",
                "ref": self.source(), "grade": "official_compilation_high",
                "acceptable_as_original": True}]},
                "clause_inventory_info": {"from": "clause-drafts@jobs/clauses/output",
                                          "source_grade": "mirror_transcription_app"},
                "clauses": [{"scope_id": "EO:1#whole", "text_offsets": {
                    "text_path": "copy.txt", "start": 0, "end": 12}}]}}])
        records = inputs.load_corpus(self.repo)["texts"]
        self.assertEqual(len(records), 2)
        self.assertEqual({r["grade"] for r in records}, {"official_compilation_high", "mirror_transcription_app"})
        self.assertFalse(next(r for r in records if r["grade"] == "mirror_transcription_app")["acceptable_as_original"])

    def test_catalog_filing_date_is_never_publication_date(self):
        self.write("jobs/new/output/texts/one.txt", "Text.")
        self.jsonl("jobs/new/output/FRAGMENTS.jsonl", [self.original()])
        self.write_csv("jobs/new/output/CATALOG_INDEX.csv", [{
            "id": "EO:1", "signing_date": "1900-01-01", "publication_date": "1900-01-03"}])
        self.assertIsNone(inputs.load_corpus(self.repo)["texts"][0]["filing_date"])

    def test_malformed_records_do_not_hide_following_good_records(self):
        self.write("jobs/new/output/texts/one.txt", "Text.")
        self.write("jobs/new/output/FRAGMENTS.jsonl", "{bad\n[]\n" + json.dumps(self.original()) + "\n")
        corpus = inputs.load_corpus(self.repo)
        self.assertEqual(len(corpus["texts"]), 1)
        self.assertTrue(any("malformed JSON" in w for w in corpus["warnings"]))
        self.assertTrue(any("non-object JSON" in w for w in corpus["warnings"]))

    def test_status_history_is_consumed_without_status_or_original_promotion(self):
        history={'schema':'eo-status-history/v1','instrument_id':'EO:1','provisional_status':None}
        raw=json.dumps(history)
        self.write('jobs/status-history/output/histories/EO_1.json',raw)
        self.jsonl('jobs/status-history/output/FRAGMENTS.jsonl',[{
            'instrument_id':'EO:1','kind':'status_history_candidates','data':{
                'history_path':'jobs/status-history/output/histories/EO_1.json',
                'history_sha256':hashlib.sha256(raw.encode()).hexdigest()}}])
        corpus=inputs.load_corpus(self.repo)
        self.assertIn('EO:1',corpus['status_histories'])
        self.assertNotIn('EO:1',corpus['statuses']);self.assertEqual(corpus['texts'],[])
        self.write('jobs/status-history/output/STATUS.json','{"result":"failed"}')
        self.assertEqual(inputs.load_corpus(self.repo)['status_histories'],{})
        self.write('jobs/status-history/output/STATUS.json','{"result":"succeeded"}')
        self.write('jobs/status-history/output/histories/EO_1.json','changed')
        corpus=inputs.load_corpus(self.repo)
        self.assertEqual(corpus['status_histories'],{})
        self.assertTrue(any('status history rejected' in v for v in corpus['warnings']))


if __name__ == "__main__":
    unittest.main()
