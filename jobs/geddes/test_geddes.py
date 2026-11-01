import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geddes


def _sha(text): return hashlib.sha256(text.encode()).hexdigest()


def fixture(root):
    own = "Executive Order 12345\nI hereby establish the Blue Marsh Refuge. This reservation shall be known as the Blue Marsh Refuge.\nFRANKLIN D. ROOSEVELT\nThe White House,\nJanuary 1, 1937.\n"
    neighbor = "Executive Order 12346\nI hereby order payment of every outstanding claim.\nFRANKLIN D. ROOSEVELT\nThe White House,\nJanuary 2, 1937.\n"
    original = own + "\n" + neighbor
    actor = "Executive Order 7001A. The Blue Marsh Refuge is renamed Green Marsh Refuge."
    def src(path, text, page, url, iid):
        (root / path).write_text(text, encoding="utf-8")
        return {"text_path": path, "text_sha256": _sha(text), "page_or_item": page, "url": url,
                "instrument_id": iid, "signing_date": "1937-01-01", "filing_date": "1937-01-02"}
    own_src = src("own.txt", original, "2 FR 63", "https://www.govinfo.gov/content/pkg/FR-1937-01-03/pdf/FR-1937-01-03.pdf", "EO:12345")
    actor_src = src("actor.txt", actor, "Executive Order 7001A; 3 FR 100", "https://www.govinfo.gov/content/pkg/FR-1938-01-03/pdf/FR-1938-01-03.pdf", "EO:7001A")
    evidence = {
        "ORIGINAL:EO:12345": {"id": "ORIGINAL:EO:12345", "source": own_src, "text": original, "char_start": 0, "char_end": len(original)},
        "CLAUSES:EO:12345#whole": {"id": "CLAUSES:EO:12345#whole", "source": own_src, "text": own, "char_start": 0, "char_end": len(own)},
        "ACT:EO:12345>EO:7001A": {"id": "ACT:EO:12345>EO:7001A", "actor_id": "EO:7001A", "actor_source": actor_src, "source": actor_src, "text": actor, "char_start": 0, "char_end": len(actor)},
    }
    dossier = {"schema": "eo-claim-kit-dossier/v1", "instrument_id": "EO:12345", "original_source_id": "ORIGINAL:EO:12345",
               "evidence": evidence, "clauses": [{"id": "CLAUSES:EO:12345#whole", "scope_id": "EO:12345#whole", "source": own_src, "text": own, "char_start": 0, "char_end": len(own)}],
               "actor_provisions": [evidence["ACT:EO:12345>EO:7001A"]]}
    def cite(source, ident, text):
        encoded = __import__("base64").urlsafe_b64encode(ident.encode()).decode().rstrip("=")
        return {**source, "evidence_id": encoded, "evidence_id_encoding": "base64url-utf8", "quote": text, "char_start": 0, "char_end": len(text)}
    claim = {"instrument_id": "EO:12345", "original_representation": {**cite(own_src, "ORIGINAL:EO:12345", original), "instrument_id": "EO:12345"},
             "operative_clauses": [{"scope_id": "EO:12345#whole", "original_operative_text": own,
                 "original_source": cite(own_src, "CLAUSES:EO:12345#whole", own),
                 "first_end": {"actor": "EO:7001A", "source": cite(actor_src, "ACT:EO:12345>EO:7001A", actor)},
                 "judgment_reason": "The command ended through Executive Order 7001A.",
                 "later_events": [{"actor": "EO:7001A", "source": cite(actor_src, "ACT:EO:12345>EO:7001A", actor)}]}],
             "later_source_search": [{"query_or_scope": "literal Blue Marsh Refuge search"}]}
    packet_dir = root / "research/apollo/g01/packet"; packet_dir.mkdir(parents=True)
    packet = {"dossiers": {"EO:12345": dossier}, "sources": {}, "text_blocks": {}, "shared_objects": {},
              "held_text_file_pins": {"own.txt": own_src["text_sha256"], "actor.txt": actor_src["text_sha256"]}, "fingerprint": "fixture"}
    dossier["fingerprint"] = geddes.batch.canonical_sha(dossier)
    packet_path = packet_dir / "PACKET.json"; packet_path.write_text(json.dumps(packet), encoding="utf-8")
    return dossier, claim, packet_path


class GeddesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.dossier, self.claim, self.packet = fixture(self.repo)
    def tearDown(self): self.temp.cleanup()
    def lint(self, claim=None):
        return geddes.lint_one(1, claim or self.claim, {"EO:12345": self.dossier}, self.repo, self.packet, {})

    def test_neighboring_order_text_is_not_own_text(self):
        c = copy.deepcopy(self.claim)
        c["research_rationale"] = 'This order states "I hereby order payment of every outstanding claim."'
        self.assertIn("attributed_quote_not_verbatim", {x["code"] for x in self.lint(c)["flags"]})

    def test_unquoted_positive_attribution_is_checked_and_negation_is_not(self):
        c = copy.deepcopy(self.claim); c["research_rationale"] = "This order directs the Secretary to pay all outstanding claims."
        self.assertFalse(self.lint(c)["flags"])  # Unquoted paraphrases are not proof of false content.
        c["research_rationale"] = "This order does not establish a status quo."
        self.assertNotIn("attributed_stock_phrase_absent", {x["code"] for x in self.lint(c)["flags"]})

    def test_lost_suffix_on_actor_is_flagged_from_source_label(self):
        c = copy.deepcopy(self.claim); c["operative_clauses"][0]["first_end"]["actor"] = "EO:7001"
        self.assertIn("suffix_dropped", {x["code"] for x in self.lint(c)["flags"]})

    def test_original_operative_quote_must_match_citation(self):
        c = copy.deepcopy(self.claim); c["operative_clauses"][0]["original_operative_text"] = "Wrong words."
        self.assertIn("quotation_not_verbatim", {x["code"] for x in self.lint(c)["flags"]})

    def test_later_quote_is_checked_against_later_source(self):
        c = copy.deepcopy(self.claim); c["operative_clauses"][0]["later_events"][0]["source"]["quote"] = "A different source quotation."
        self.assertIn("later_event_quote_not_in_cited_source", {x["code"] for x in self.lint(c)["flags"]})
        c = copy.deepcopy(self.claim); c["operative_clauses"][0]["later_events"][0]["source"]["quote"] = c["operative_clauses"][0]["later_events"][0]["source"]["quote"].lower()
        self.assertIn("later_event_quote_not_in_cited_source", {x["code"] for x in self.lint(c)["flags"]})

    def test_federal_register_page_and_issue_date_are_source_specific(self):
        for label, mutate in (
            ("fr_citation_mismatch", lambda s: s.update(page_or_item="3 FR 101")),
            ("fr_issue_date_mismatch", lambda s: s.update(page_or_item="3 FR 100; issue of 1938-01-04")),
        ):
            c = copy.deepcopy(self.claim); mutate(c["operative_clauses"][0]["first_end"]["source"])
            self.assertIn(label, {x["code"] for x in self.lint(c)["flags"]})

    def test_named_later_instrument_needs_event_source(self):
        c = copy.deepcopy(self.claim); cl = c["operative_clauses"][0]
        cl["judgment_reason"] = "Proclamation No. 2416 renamed the refuge."; cl["later_events"] = [{"actor": "PROC:2416"}]
        row = self.lint(c)
        self.assertIn("later_instrument_named_without_event_source", {x["code"] for x in row["flags"]})
        self.assertIn("later_event_source_missing", {x["code"] for x in row["coverage_gaps"]})

    def test_revoked_object_is_not_mistaken_for_later_actor(self):
        c = copy.deepcopy(self.claim)
        c["operative_clauses"][0]["judgment_reason"] = "Executive Order 7001A revoked Executive Order 99."
        row = self.lint(c)
        self.assertNotIn("later_instrument_named_without_event_source", {x["code"] for x in row["flags"]})

    def test_member_check_stock_concept_and_attached_negation(self):
        c = copy.deepcopy(self.claim)
        c["research_rationale"] = "Member checks: " + json.dumps({"scope_check": "The inventory includes the standstill recital."})
        self.assertIn("attributed_stock_phrase_absent", {x["code"] for x in self.lint(c)["flags"]})
        c["research_rationale"] = "Member checks: " + json.dumps({"scope_check": "The order contains no statutory standstill."})
        self.assertNotIn("attributed_stock_phrase_absent", {x["code"] for x in self.lint(c)["flags"]})

    def test_standstill_concept_accepts_no_change_source_wording(self):
        self.assertIsNotNone(geddes.SOURCE_CONCEPTS["standstill"].search("From this date no change shall be made in conditions."))

    def test_no_other_order_requires_literal_name_in_search_query(self):
        c = copy.deepcopy(self.claim); c["research_rationale"] = "No other held order names Blue Marsh Refuge."
        c["later_source_search"] = [{"query_or_scope": "Executive Order 100"}]
        row = self.lint(c)
        self.assertTrue(any(x["code"] == "literal_name_search_performed" and "blue marsh refuge" in x["names"] for x in row["coverage_gaps"]))
        hits, missing, count, scope = geddes.held_corpus_search(self.packet, ["Blue Marsh Refuge"], self.repo)
        self.assertTrue(hits["Blue Marsh Refuge"])
        self.assertFalse(scope["full_discovered_corpus_covered"])

    def test_hash_mismatch_fails_closed_as_coverage(self):
        (self.repo / "own.txt").write_text("changed", encoding="utf-8")
        row = self.lint()
        self.assertGreater(row["held_text_integrity_failures"], 0)
        self.assertTrue(any("hash" in str(g) for g in row["coverage_gaps"]))

    def test_cost_keeps_reported_roles_separate_and_uses_track_denominator(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "t.csv"
            p.write_text("batch,role,model,input_tokens,output_tokens,cache_read_input_tokens,active_seconds\nn01,producer,m,10,2,4,1.5\nn02,producer,m,,4,8,2.5\n")
            filed = Path(temp) / "counts.json"; filed.write_text('{"filed_claims":{"NRA":2}}')
            result = geddes.cost(p, filed)
        self.assertEqual(len(result["groups"]), 1)
        self.assertEqual(result["groups"][0]["active_seconds"], 4.0)
        self.assertEqual(result["groups"][0]["active_seconds_per_filed_claim"], 2.0)
        self.assertIsNone(result["groups"][0]["input_tokens"])
        self.assertIsNone(result["groups"][0]["input_tokens_per_filed_claim"])

    def test_view_includes_operative_text_and_compact_size_estimates(self):
        result = geddes.view(self.packet, "EO:12345", repo=self.repo)
        self.assertIn("I hereby establish", result["own_original_text"])
        self.assertNotIn("payment of every outstanding claim", result["own_original_text"])
        self.assertTrue(result["own_text_boundary"]["verified_whole_order"])


if __name__ == "__main__": unittest.main()
