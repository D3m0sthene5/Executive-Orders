"""Tests for the one-order view: machine searches, later-event chain, clause drafts, filed claim, bounds, --write."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geddes
from test_geddes import fixture


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.dossier, self.claim, self.packet = fixture(self.repo)

    def tearDown(self): self.temp.cleanup()

    def rewrite_packet(self, **extra):
        dossier = self.dossier
        dossier.update(extra)
        dossier["fingerprint"] = geddes.batch.canonical_sha({k: v for k, v in dossier.items() if k != "fingerprint"})
        packet = json.loads(self.packet.read_text())
        packet["dossiers"]["EO:12345"] = dossier
        self.packet.write_text(json.dumps(packet), encoding="utf-8")

    def search(self, n, hits=0, complete=True):
        return {"search_id": f"current-law:s{n}", "complete": complete, "machine_hits_for_this_order": hits, "scope_note": "scope note %d" % n,
                "entry": {"checked_on": "2026-10-17", "query_or_scope": "query " + "q" * 900, "repository": "repo", "searched_by": "jobs/current-law"}}

    def test_machine_searches_report_hits_coverage_and_caps_long_lists(self):
        self.rewrite_packet(machine_searches=[self.search(i, hits=i) for i in range(15)])
        view = geddes.view(self.packet, "EO:12345", repo=self.repo)["machine_searches"]
        self.assertEqual(view["bound"]["total"], 15)
        self.assertEqual(len(view["searches"]), geddes.VIEW_CAPS["machine_searches"])
        self.assertTrue(view["bound"]["truncated"])
        self.assertEqual(view["bound"]["hit_total"], sum(range(15)))
        first = view["searches"][0]
        self.assertEqual((first["search_id"], first["kind"], first["machine_hits_for_this_order"]), ("current-law:s0", "current-law", 0))
        self.assertIn("truncated", first["coverage"]["query_or_scope"])
        self.assertEqual(first["coverage"]["scope_note"], "scope note 0")

    def test_unknown_hit_count_stays_unknown_and_incomplete_search_is_counted(self):
        s = self.search(1); s["machine_hits_for_this_order"] = None; s["complete"] = False
        self.rewrite_packet(machine_searches=[s])
        view = geddes.view(self.packet, "EO:12345", repo=self.repo)["machine_searches"]
        self.assertEqual(view["bound"]["hit_total"], "unknown")
        self.assertEqual(view["bound"]["incomplete_searches"], 1)

    def test_chain_events_and_citable_evidence_ids_include_actor_text(self):
        actor_source = self.dossier["evidence"]["ACT:EO:12345>EO:7001A"]["actor_source"]
        evidence = dict(self.dossier["evidence"])
        evidence["ACTOR_TEXT:EO:9999"] = {"id": "ACTOR_TEXT:EO:9999", "role": "actor_context", "actor_id": "EO:9999", "source": actor_source,
                                          "char_start": 0, "char_end": 3}
        chain = {"id": "CHAIN:EO:12345", "confidence": "medium", "notes": "lead only", "generic_refs_excluded": 4, "target_id": "EO:12345",
                 "events": [{"id": "CHAIN:EO:12345#1", "actor_id": "EO:9999", "signing_date": "1950-01-01", "verb": "revokes",
                             "how_named": "direct", "confidence": "medium", "sections_touched": ["whole"], "notes": "n",
                             "provision_text": "x" * 1000, "source": actor_source}]}
        self.rewrite_packet(evidence=evidence, chain=chain, actor_contexts=[{"actor_id": "EO:9999", "evidence_id": "ACTOR_TEXT:EO:9999"}])
        view = geddes.view(self.packet, "EO:12345", repo=self.repo)["later_events_chain"]
        event = view["chain"]["events"][0]
        self.assertEqual(event["citable_evidence_ids"], ["ACTOR_TEXT:EO:9999"])
        self.assertIn("truncated", event["provision_text"])
        ids = {r["evidence_id"] for r in view["citable_evidence"]["records"]}
        self.assertIn("ACTOR_TEXT:EO:9999", ids)
        self.assertIn("ACT:EO:12345>EO:7001A", ids)
        self.assertFalse(any(i.startswith(("CLAUSES:", "ORIGINAL:", "TERM:")) for i in ids))
        self.assertEqual(view["chain"]["generic_refs_excluded"], 4)

    def test_clause_inventory_carries_obligation_fields_and_draft_sheet_reasons(self):
        ob = {"scope_id": "EO:12345#whole", "state": "requires_clause_specific_research", "established_ending": None,
              "wording_features": ["deadline"], "own_term_evidence_ids": ["TERM:x"], "later_actor_evidence_ids": [],
              "questions": [f"question {i}" for i in range(9)]}
        self.rewrite_packet(lifecycle_obligations=[ob], draft_gate_errors=["clause_0_state"], draft_material_gaps=["DRAFT: not decided"])
        folder = self.packet.parent
        (folder / "RATIONALES.json").write_text(json.dumps({"r1": "Shared reason text."}))
        (folder / "clauses.csv").write_text(
            "instrument_id,scope_id,state,end_id,effective_date,mechanism,reason,inventory_source_id,inventory_char_start,inventory_char_end,inventory_reason\n"
            "EO:12345,EO:12345#whole,terminated,ACT:EO:12345>EO:7001A,1938-01-01,express,@rationale:r1,ORIGINAL:EO:12345,0,10,Own inventory reason\n"
            "EO:12345,EO:12345#other,,,,,,,,,\n"
            "EO:99999,EO:99999#whole,terminated,,,,not this order,,,,\n", encoding="utf-8")
        inv = geddes.view(self.packet, "EO:12345", repo=self.repo)["clause_inventory"]
        clause = inv["clauses"][0]
        self.assertEqual(clause["lifecycle_state"], "requires_clause_specific_research")
        self.assertEqual(len(clause["questions"]), geddes.VIEW_CAPS["questions_per_clause"])
        self.assertEqual(clause["questions_bound"]["total"], 9)
        self.assertEqual(inv["dossier_draft_gate_errors"], ["clause_0_state"])
        rows = inv["draft_sheet"]["rows"]
        self.assertEqual([r["scope_id"] for r in rows], ["EO:12345#whole", "EO:12345#other"])
        self.assertEqual(rows[0]["reason"], "Shared reason text.")
        self.assertEqual(rows[0]["inventory_reason"], "Own inventory reason")
        self.assertTrue(rows[0]["in_dossier_inventory"]); self.assertFalse(rows[1]["in_dossier_inventory"])
        self.assertIn("not evidence", inv["draft_sheet"]["note"])

    def test_missing_draft_sheet_is_reported_not_invented(self):
        self.assertEqual(geddes.view(self.packet, "EO:12345", repo=self.repo)["clause_inventory"]["draft_sheet"], {"present": False})

    def claims_dir(self):
        d = self.repo / "research/readiness/claims"; d.mkdir(parents=True); return d

    def test_current_claim_is_latest_file_and_line_and_marked_prior_draft(self):
        d = self.claims_dir()
        old, new, newest_line = dict(self.claim, research_rationale="old"), dict(self.claim, research_rationale="new"), dict(self.claim, research_rationale="newest")
        other = {"instrument_id": "EO:77777"}
        (d / "a-first.jsonl").write_text(json.dumps(old) + "\n")
        (d / "b-second.jsonl").write_text(json.dumps(other) + "\n" + json.dumps(new) + "\n" + json.dumps(newest_line) + "\n")
        view = geddes.view(self.packet, "EO:12345", repo=self.repo)["current_canonical_claim"]
        self.assertTrue(view["found"])
        self.assertEqual((view["path"], view["line"], view["owner"]), ("research/readiness/claims/b-second.jsonl", 3, "b-second"))
        self.assertEqual(view["claim"]["research_rationale"], "newest")
        self.assertEqual(view["status"], "prior draft")
        self.assertEqual(view["claim_sha256"], geddes.batch.canonical_sha(newest_line))
        self.assertFalse(view["claim_strings_truncated"])

    def test_no_filed_claim_is_reported_and_large_claim_strings_are_cut_unless_full_claim(self):
        self.assertFalse(geddes.view(self.packet, "EO:12345", repo=self.repo)["current_canonical_claim"]["found"])
        d = self.claims_dir()
        big = dict(self.claim, research_rationale="z" * (geddes.VIEW_CAPS["claim_bytes"] + 500))
        (d / "c.jsonl").write_text(json.dumps(big) + "\n")
        cut = geddes.view(self.packet, "EO:12345", repo=self.repo)["current_canonical_claim"]
        self.assertTrue(cut["claim_strings_truncated"])
        self.assertLess(len(cut["claim"]["research_rationale"]), 1000)
        self.assertEqual(cut["claim_full_bytes"], len(json.dumps(big, ensure_ascii=False).encode()))
        full = geddes.view(self.packet, "EO:12345", repo=self.repo, full_claim=True)["current_canonical_claim"]
        self.assertEqual(full["claim"], big)

    def test_write_prints_only_the_short_summary(self):
        out_path = self.repo / "out/view.json"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = geddes.main(["view", str(self.packet), "EO:12345", "--write", str(out_path), "--repo", str(self.repo)])
        self.assertEqual(code, 0)
        printed = json.loads(out.getvalue())
        self.assertEqual(printed["written_to"], str(out_path))
        self.assertNotIn("own_original_text", printed)
        self.assertNotIn("clauses", printed)
        self.assertLess(len(out.getvalue()), 4000)
        written = json.loads(out_path.read_text())
        self.assertIn("own_original_text", written)
        self.assertEqual(printed["view_bytes"], written["view_bytes"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            geddes.main(["view", str(self.packet), "EO:12345", "--repo", str(self.repo)])
        self.assertIn("own_original_text", json.loads(out.getvalue()))  # without --write the full view is printed


if __name__ == "__main__": unittest.main()
