"""Unit tests for the claim-drafts job: small fixtures, no network.

The project's own claim gate (research/stage19/code/claim_gate.py) is copied
into a temporary fake repo so every test runs the real gate.
"""

import csv
import hashlib
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stdout

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
REAL_REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import drafts as D  # noqa: E402

SHA = {k: (k * 64)[:64] for k in "abcdef0123456789"}
CLAIM_KEYS = {"schema", "instrument_id", "whole_order_status", "original_representation", "operative_clauses",
              "whole_order_end", "savings_residuals", "later_source_search", "unresolved_material_gaps",
              "research_rationale"}
CLAUSE_KEYS = {"scope_id", "original_operative_text", "original_source", "state_at_cutoff", "first_end",
               "current_predicate", "later_events"}


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0])
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def frag(iid, kind, data, job, **extra):
    return {"instrument_id": iid, "kind": kind, "data": data, "sources": [], "confidence_note": "test",
            "produced_by": job, **extra}


CLAUSE_TEXT = "Section 1. The Board is hereby established. Sec. 2. The Board shall report each year."


def make_repo(root, *, cl_sample=True):
    """A fake repo with four orders. EO:100 NO (full evidence), EO:200 YES, EO:300 undecided, EO:400 NO bare."""
    root = pathlib.Path(root)
    gate_src = REAL_REPO / "research/stage19/code/claim_gate.py"
    (root / "research/stage19/code").mkdir(parents=True)
    shutil.copy(gate_src, root / "research/stage19/code/claim_gate.py")
    tracker_src = REAL_REPO / "jobs/readiness-tracker/tracker.py"
    if tracker_src.is_file():
        (root / "jobs/readiness-tracker").mkdir(parents=True)
        shutil.copy(tracker_src, root / "jobs/readiness-tracker/tracker.py")
    # The actual tracker/checker share these policy dependencies. Keep the
    # isolated fixture complete so tests cannot silently use a fallback mapping.
    for relative in ("jobs/claim-kit/working_text.py", "jobs/claim-kit/factual_events.py",
                     "jobs/norton/model.py"):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REAL_REPO / relative, target)
    write_csv(root / D.P["universe"], [{"id": i, "included_in_bibliography": "1", "date_effective": y}
                                       for i, y in (("EO:100", "1950"), ("EO:200", "1990"), ("EO:300", "1960"),
                                                    ("EO:400", "1940"), ("EO:500", "1951"))])
    write_csv(root / D.P["decided"], [
        {"instrument_id": "EO:100", "provisional_substantive_status": "no", "decision_origin": "inherited_legacy_v2"},
        {"instrument_id": "EO:200", "provisional_substantive_status": "yes", "decision_origin": "opus_checkpoint2"},
        {"instrument_id": "EO:400", "provisional_substantive_status": "no", "decision_origin": "inherited_legacy_v2"},
    ])
    out = root / "jobs"
    # fr-originals: EO:100 high, EO:200 medium (needs a page check)
    fr = out / "fr-originals/output"
    write_jsonl(fr / "FRAGMENTS.jsonl", [
        frag("EO:100", "original_representation", {
            "url": "https://www.govinfo.gov/content/pkg/FR-1950-01-03/pdf/FR-1950-01-03.pdf", "sha256": SHA["a"],
            "page_or_item": "15 FR 1, PDF pages 2-2", "location_confidence": "high", "needs_page_check": False,
            "location_verified": False, "fr_citation": "15 FR 1", "signing_date": "1950-01-02",
            "source_id": "fr-originals:EO:100:aaaa", "text_path": "texts/EO_100.txt"}, "fr-originals"),
        frag("EO:200", "original_representation", {
            "url": "https://www.govinfo.gov/content/pkg/FR-1990-05-03/pdf/FR-1990-05-03.pdf", "sha256": SHA["b"],
            "page_or_item": "55 FR 10, PDF pages 3-4", "location_confidence": "medium", "needs_page_check": True,
            "location_verified": False, "fr_citation": "55 FR 10", "signing_date": "1990-05-01"}, "fr-originals"),
    ])
    write_jsonl(fr / "SOURCES.jsonl", [{"source_id": "fr-originals:EO:100:aaaa", "instrument_ids": ["EO:100"],
                                        "url": "https://www.govinfo.gov/content/pkg/FR-1950-01-03/pdf/FR-1950-01-03.pdf",
                                        "sha256": SHA["a"], "bytes": 10, "retrieved_utc": "2026-10-17T00:00:00Z",
                                        "route": "official/govinfo_fr_issue_pdf", "page_or_item": "15 FR 1",
                                        "text_path": None, "cache_path": None, "content_type": "application/pdf",
                                        "notes": ""}])
    (fr / "SUMMARY.json").write_text(json.dumps({"job": "fr-originals", "shrink_check": "ok"}), encoding="utf-8")
    # clause-drafts: EO:100 and EO:200
    cd = out / "clause-drafts/output"
    (cd / "texts").mkdir(parents=True)
    with open(cd / "texts/cd-100.txt", "w", encoding="utf-8", newline="") as fh:
        fh.write(CLAUSE_TEXT)
    s1, s2 = CLAUSE_TEXT.index("Section 1."), CLAUSE_TEXT.index("Sec. 2.")
    src = {"url": "https://www.presidency.ucsb.edu/documents/executive-order-100", "sha256": SHA["c"],
           "page_or_item": "APP page"}

    def clause(iid, sid, a, b, label):
        return {"scope_id": f"{iid}#{sid}", "label": label, "heading": None, "clause_kind": "operative",
                "related_orders": [], "original_operative_text": CLAUSE_TEXT[a:b], "original_source": dict(src),
                "text_offsets": {"text_path": "texts/cd-100.txt", "start": a, "end": b},
                "state_at_cutoff": None, "first_end": None, "current_predicate": None, "later_events": [],
                "needs_judgment": ["state_at_cutoff"], "draft_status": "machine_draft_unverified"}

    write_jsonl(cd / "FRAGMENTS.jsonl", [
        frag("EO:100", "operative_clauses", [clause("EO:100", "sec1", s1, s2 - 1, "Sec. 1"),
                                             clause("EO:100", "sec2", s2, len(CLAUSE_TEXT), "Sec. 2")],
             "clause-drafts", source_grade="mirror_transcription_app", segmentation_quality="good",
             source_id="cd-100"),
        frag("EO:200", "operative_clauses", [clause("EO:200", "sec1", s1, s2 - 1, "Sec. 1")], "clause-drafts",
             source_grade="mirror_transcription_app", segmentation_quality="good", source_id="cd-100"),
    ])
    write_jsonl(cd / "SOURCES.jsonl", [])
    write_csv(cd / "IDENTITY_QUARANTINE.csv", [{"instrument_id": "EO:400", "reasons": "no_heading_in_text"}])
    (cd / "SUMMARY.json").write_text(json.dumps({"job": "clause-drafts"}), encoding="utf-8")
    # later-events: EO:100 revoked by EO:150 on 1955-03-01 (complete catalog); EO:200 too (YES conflict)
    le = out / "later-events/output"
    api = {"url": "https://www.federalregister.gov/api/v1/documents.json?x=1", "sha256": SHA["d"],
           "page_or_item": "OFR API record executive_order_number=150; field disposition_notes"}
    item = {"date_candidate": "1955-03-01", "date_candidates_conflicting": [], "date_basis": ["catalog"],
            "stated_effective_date_candidates": [], "actor": "EO:150", "mechanism": "revocation", "qualifier": "",
            "evidence_types": ["ofr_note_on_acting"], "edge_ids": ["LE-1"], "flags": [], "source": api,
            "all_source_positions": [0], "quote": "Revokes: EO 100", "quote_kind": "verbatim_note_item",
            "later_reinstatement_candidates": [], "status": "CANDIDATE_UNVERIFIED"}
    late = dict(item, date_candidate="2026-12-01", actor="EO:999", edge_ids=["LE-9"])
    write_jsonl(le / "FRAGMENTS.jsonl", [
        frag("EO:100", "whole_order_end_candidates", [item], "later-events"),
        frag("EO:100", "later_event_candidates", [dict(item, mechanism="amendment", qualifier="section 2",
                                                       edge_ids=["LE-2"]), late], "later-events"),
        frag("EO:200", "whole_order_end_candidates", [dict(item, date_candidate="1995-01-01")], "later-events"),
    ])
    write_jsonl(le / "SOURCES.jsonl", [{"source_id": "ofr-api-page:1", "instrument_ids": [], "url": api["url"],
                                        "sha256": SHA["d"], "bytes": 5, "retrieved_utc": "2026-10-17T01:00:00Z",
                                        "route": "ofr_api", "page_or_item": "page 1", "text_path": None,
                                        "cache_path": None, "content_type": "application/json", "notes": ""}])
    (le / "SUMMARY.json").write_text(json.dumps({
        "job": "later-events", "generated_utc": "2026-10-17T01:00:00Z", "catalog_complete": True,
        "job_limit": None, "catalog_records_used": 6938, "text_documents_scanned": 1002}), encoding="utf-8")
    # current-law: EO:100 (provisional NO) still cited; a second, different-date ending for EO:100
    cl = out / "current-law/output"
    usc = {"url": "https://uscode.house.gov/download/releasepoints/us/pl/119/121/xml_usc05@119-121.zip",
           "sha256": SHA["e"], "page_or_item": "5 U.S.C. 101 note"}
    write_jsonl(cl / "FRAGMENTS.jsonl", [
        frag("EO:100", "current_predicate_candidates", [{
            "system": "usc", "legal_basis_candidate": "statutory note names the order (5 U.S.C. 101 note)",
            "basis_code": "statutory_note_reference", "where": "USC 5 U.S.C. 101 note", "checked_through": "2026-10-09",
            "snippet": "Ex. Ord. No. 100", "source": usc}], "current-law"),
        frag("EO:100", "whole_order_end_candidates", [{
            "system": "usc", "date_candidate": "1956-07-01", "date_basis_code": "printed_next_to_acting_instrument",
            "actor_candidate": "President, by Ex. Ord. No. 160", "mechanism_candidate": "revocation (as stated in an "
            "OLRC note)", "acting_instrument_id": "EO:160", "where": "USC", "snippet": "revoked by Ex. Ord. No. 160",
            "event_id": "usc:ev:1", "source": usc}], "current-law"),
        frag("EO:200", "current_predicate_candidates", [{
            "system": "ecfr", "legal_basis_candidate": "CFR authority citation", "basis_code": "cfr_authority_citation",
            "where": "5 CFR 1", "checked_through": "2026-10-14", "snippet": "E.O. 200", "source": usc}], "current-law"),
    ])
    write_jsonl(cl / "SOURCES.jsonl", [{"source_id": "usc05", "instrument_ids": [], "url": usc["url"], "sha256": SHA["e"],
                                        "bytes": 5, "retrieved_utc": "2026-10-16T05:00:00Z", "route": "usc",
                                        "page_or_item": "zip", "text_path": None, "cache_path": None,
                                        "content_type": "application/zip", "notes": ""}])
    (cl / "SUMMARY.json").write_text(json.dumps({
        "job": "current-law", "sample_mode": cl_sample, "job_limit": 2 if cl_sample else None,
        "usc": {"release_point": "119-121", "current_through_public_law_date": "2026-10-09",
                "titles": [{"member": "usc05.xml"}]},
        "ecfr": {"date": "2026-10-14", "search_complete": False, "titles": [{"title": 5}]}}), encoding="utf-8")
    # opus-media-match: EO:500 (undecided) archived page
    om = out / "opus-media-match/output"
    write_jsonl(om / "FRAGMENTS.jsonl", [frag("EO:500", "original_representation", {
        "archival_id": "opus_stage11_evidence_originals:evidence/x.pdf", "local_file_sha256": SHA["f"],
        "sha256": SHA["f"], "page_or_item": "PDF page 1 of archived member evidence/x.pdf",
        "upstream_url": "https://www.govinfo.gov/content/pkg/FR-1951-01-01/pdf/FR-1951-01-01.pdf",
        "upstream_sha256": SHA["0"], "status": "candidate_unverified"}, "opus-media-match")])
    write_jsonl(om / "SOURCES.jsonl", [])
    (om / "SUMMARY.json").write_text(json.dumps({"job": "opus-media-match"}), encoding="utf-8")
    (root / "research/readiness/claims").mkdir(parents=True)
    return root


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="claim-drafts-test-")
        self.repo = make_repo(pathlib.Path(self.tmp) / "repo")
        self.reload()

    def reload(self, env=None):
        inputs, self.notes = D.discover_inputs(self.repo, env)
        self.merged = D.load_inputs(inputs)
        self.rd = D.RepoData(self.repo)
        self.gate = D.load_gate(self.repo)
        self.step_for, _ = D.load_step_mapper(self.repo)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def draft(self, iid):
        return D.build_draft(iid, self.merged, self.rd, self.gate, self.step_for)


class ClaimShape(Fixture):
    def test_claim_has_exactly_the_stage19_fields(self):
        for iid in ("EO:100", "EO:200", "EO:300", "EO:400", "EO:500"):
            c = self.draft(iid)["claim"]
            self.assertEqual(set(c), CLAIM_KEYS, iid)
            self.assertEqual(c["schema"], "eo-lifecycle-claim/v1")
            for cl in c["operative_clauses"]:
                self.assertEqual(set(cl), CLAUSE_KEYS)
                self.assertIsNone(cl["state_at_cutoff"])  # judgment, never machine-filled
                self.assertEqual(cl["later_events"], [])
            self.assertIsNone(c["whole_order_end"])
            self.assertIsNone(c["savings_residuals"])
            self.assertEqual(c["research_rationale"], "")

    def test_status_copied_from_ledger_only(self):
        self.assertEqual(self.draft("EO:100")["claim"]["whole_order_status"], "no")
        self.assertEqual(self.draft("EO:200")["claim"]["whole_order_status"], "yes")
        d = self.draft("EO:300")
        self.assertIsNone(d["claim"]["whole_order_status"])
        self.assertIn("provisional_status", [m["step"] for m in d["_draft"]["missing_evidence"]])

    def test_unresolved_gaps_listed_so_draft_never_passes_as_is(self):
        line = self.draft("EO:100")
        self.assertTrue(line["claim"]["unresolved_material_gaps"])
        self.assertIn("unresolved_material_gaps", line["_draft"]["gate"]["errors_now"])


class Originals(Fixture):
    def test_high_confidence_fr_original_is_filled(self):
        c = self.draft("EO:100")["claim"]
        self.assertEqual(c["original_representation"]["sha256"], SHA["a"])
        self.assertTrue(self.gate.source_ok(c["original_representation"]))

    def test_needs_page_check_is_never_filled(self):
        line = self.draft("EO:200")
        self.assertIsNone(line["claim"]["original_representation"])
        props = line["_draft"]["proposals"]["original_representation"]
        self.assertEqual(props[0]["grade"], "fr_originals_needs_page_check")
        self.assertFalse(props[0]["strong"])
        self.assertIn("original_representation", [j["field"] for j in line["_draft"]["needs_judgment"]])

    def test_opus_ref_uses_archival_form_not_upstream_url(self):
        ref = self.draft("EO:500")["claim"]["original_representation"]
        self.assertEqual(ref["archival_id"], "opus_stage11_evidence_originals:evidence/x.pdf")
        self.assertEqual(ref["local_file_sha256"], SHA["f"])
        self.assertNotIn("url", ref)
        self.assertTrue(self.gate.source_ok(ref))


class Clauses(Fixture):
    def test_clause_offsets_verified(self):
        d = self.draft("EO:100")["_draft"]
        self.assertEqual(d["clause_inventory_info"]["offset_checks"], {"verified": 2})

    def test_offset_mismatch_is_a_conflict(self):
        p = self.repo / "jobs/clause-drafts/output/texts/cd-100.txt"
        p.write_text("X" + CLAUSE_TEXT, encoding="utf-8")
        self.reload()
        codes = [c["code"] for c in self.draft("EO:100")["_draft"]["conflicts"]]
        self.assertIn("CLAUSE_TEXT_NOT_AT_OFFSETS", codes)

    def test_quarantined_order_says_why(self):
        d = self.draft("EO:400")["_draft"]
        what = " ".join(m["what"] for m in d["missing_evidence"] if m["step"] == "clause_inventory")
        self.assertIn("quarantined", what)

    def test_section_hint_for_later_event(self):
        ev = self.draft("EO:100")["_draft"]["proposals"]["later_events"]
        self.assertEqual(ev[0]["clause_hint_scope_ids"], ["EO:100#sec2"])

    def test_section_lists_in_qualifier(self):
        meta = [{"scope_id": f"EO:1#sec{i}", "label": f"Sec. {i}"} for i in range(1, 13)]
        self.assertEqual(D.clause_hints("sections 1 and 2; to the extent inconsistent", meta),
                         ["EO:1#sec1", "EO:1#sec2"])
        self.assertEqual(D.clause_hints("secs. 3, 4 and 7", meta), ["EO:1#sec3", "EO:1#sec4", "EO:1#sec7"])
        self.assertEqual(D.clause_hints("Section 12", meta), ["EO:1#sec12"])

    def test_wrong_type_scope_id_does_not_crash(self):
        p = self.repo / "jobs/clause-drafts/output/FRAGMENTS.jsonl"
        rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()]
        rows[0]["data"][0]["scope_id"] = ["EO:100#sec1"]
        write_jsonl(p, rows)
        self.reload()
        g = self.draft("EO:100")["_draft"]["gate"]
        self.assertEqual(g["errors_now"], ["gate_raised_exception"])
        self.assertTrue(g["gate_exception"])


class Endings(Fixture):
    def test_two_jobs_disagree_on_whole_end(self):
        d = self.draft("EO:100")["_draft"]
        codes = {c["code"] for c in d["conflicts"]}
        self.assertIn("WHOLE_END_DATE_DISAGREEMENT", codes)
        self.assertIn("WHOLE_END_ACTOR_DISAGREEMENT", codes)
        sugg = [w for w in d["proposals"]["whole_order_end"] if w["suggested"]]
        self.assertEqual(len(sugg), 1)
        self.assertEqual(sugg[0]["proposal"]["date"], "1955-03-01")  # the earlier one
        self.assertEqual(set(sugg[0]["proposal"]), {"date", "actor", "mechanism", "source"})

    def test_current_law_actor_and_mechanism_normalised(self):
        props = self.draft("EO:100")["_draft"]["proposals"]["whole_order_end"]
        cl = [p for p in props if p["meta"]["from_job"] == "current-law"][0]
        self.assertEqual(cl["proposal"]["actor"], "EO:160")
        self.assertEqual(cl["proposal"]["mechanism"], "revocation")

    def test_yes_order_with_whole_end_candidate_is_conflict(self):
        codes = {c["code"] for c in self.draft("EO:200")["_draft"]["conflicts"]}
        self.assertIn("YES_ORDER_HAS_WHOLE_END_CANDIDATE", codes)

    def test_no_order_cited_in_current_law_is_conflict(self):
        codes = {c["code"] for c in self.draft("EO:100")["_draft"]["conflicts"]}
        self.assertIn("NO_ORDER_CITED_IN_CURRENT_LAW", codes)

    def test_events_after_cutoff_are_excluded(self):
        d = self.draft("EO:100")["_draft"]
        actors = [e["proposal"]["actor"] for e in d["proposals"]["later_events"]]
        self.assertNotIn("EO:999", actors)
        self.assertEqual(d["proposals"]["excluded_after_cutoff"], 1)
        self.assertIn("CANDIDATE_DATED_AFTER_CUTOFF", {c["code"] for c in d["conflicts"]})

    def test_later_event_shape_matches_claim(self):
        ev = self.draft("EO:100")["_draft"]["proposals"]["later_events"][0]["proposal"]
        # date_candidate, not effective_date: the date is the acting instrument's signing or printed date
        self.assertEqual(set(ev), {"date_candidate", "actor", "mechanism", "source"})


class GateAndReadiness(Fixture):
    def test_judgment_only_when_evidence_exists(self):
        g = self.draft("EO:100")["_draft"]["gate"]
        self.assertIn("clause_0_state", g["errors_now"])
        self.assertIn("whole_order_end_evidence", g["errors_now"])
        self.assertEqual(g["errors_if_proposals_accepted"], [])
        self.assertTrue(g["only_judgment_left"])

    def test_yes_needs_predicate_through_cutoff(self):
        d = self.draft("EO:200")["_draft"]
        # predicate checked through 2026-10-14 exists; only the page-check original is weak
        self.assertTrue(d["gate"]["only_judgment_left"])
        self.assertEqual(d["readiness"]["by_step"]["ending_or_current_basis"], "confirm")

    def test_bare_order_needs_research(self):
        d = self.draft("EO:400")["_draft"]
        self.assertFalse(d["gate"]["only_judgment_left"])
        self.assertIn("clause_inventory", d["readiness"]["needs_research"])
        self.assertEqual(d["effort"], "large")

    def test_machine_searches_are_never_put_into_the_claim(self):
        c = self.draft("EO:100")
        self.assertEqual(c["claim"]["later_source_search"], [])
        machine = c["_draft"]["proposals"]["later_source_search_machine"]
        entries = {s["search_id"]: s["entry"] for s in self.merged.searches}
        self.assertTrue(all("entry" not in m for m in machine))  # wording kept once, in SUMMARY.json
        repos = [entries[m["search_id"]]["repository"] for m in machine]
        self.assertTrue(any("Federal Register executive-order catalog" in r for r in repos))
        self.assertFalse(any("U.S. Code" in r for r in repos))  # current-law ran in sample mode
        ids = [p["search_id"] for p in c["_draft"]["proposals"]["later_source_search_partial"]]
        self.assertIn("current-law:usc", ids)
        for m in machine:
            self.assertTrue(D.exact_date(entries[m["search_id"]]["checked_on"]))
        self.assertIn("bounded_later_search", c["_draft"]["gate"]["errors_now"])

    def test_full_current_law_run_enters_usc_search(self):
        shutil.rmtree(self.repo)
        self.repo = make_repo(self.repo, cl_sample=False)
        self.reload()
        machine = self.draft("EO:100")["_draft"]["proposals"]["later_source_search_machine"]
        entries = {s["search_id"]: s["entry"] for s in self.merged.searches}
        repos = [entries[m["search_id"]]["repository"] for m in machine]
        self.assertTrue(any("U.S. Code" in r for r in repos))
        self.assertFalse(any("eCFR" in r for r in repos))  # search_complete is false

    def test_compress_errors(self):
        self.assertEqual(D.compress_errors(["clause_0_state", "clause_1_state", "schema"]),
                         ["clause_*_state x2", "schema"])


class Inputs(Fixture):
    def test_env_inputs_infer_job_and_skip_bad(self):
        a = self.repo / "jobs/later-events/output"
        env = f"{a};clause-drafts={self.repo / 'jobs/clause-drafts/output'};{self.repo / 'nope'}"
        inputs, notes = D.discover_inputs(self.repo, env)
        self.assertEqual([i.job for i in inputs], ["later-events", "clause-drafts"])
        self.assertTrue(any("not a folder" in n for n in notes))

    def test_fr_originals_falls_back_to_full_run(self):
        out = self.repo / "jobs/fr-originals/output"
        (out / "SUMMARY.json").write_text(json.dumps({"job": "fr-originals", "shrink_check": "shrank"}), encoding="utf-8")
        full = self.repo / "jobs/fr-originals/data/full_run"
        shutil.copytree(out, full)
        inputs, notes = D.discover_inputs(self.repo)
        fr = [i for i in inputs if i.job == "fr-originals"]
        self.assertEqual(fr[0].origin, "jobs/fr-originals/data/full_run")

    def test_decided_first_and_limit(self):
        orders = D.select_orders(self.merged, self.rd, limit=3)
        self.assertEqual(len(orders), 3)
        self.assertTrue(all(o in self.rd.decided for o in orders))
        self.assertIn("EO:500", D.select_orders(self.merged, self.rd))
        self.assertNotIn("EO:500", D.select_orders(self.merged, self.rd, scope="decided"))


class TrackerSafety(Fixture):
    """A draft claim committed exactly as written must not light any readiness step except original_text."""

    CLAIM_STEPS = ("clause_inventory", "ending_or_current_basis", "savings_residuals", "counterevidence")

    def failing_steps(self, claim):
        status = (self.rd.decided.get(claim["instrument_id"]) or {}).get("provisional_substantive_status")
        errors = self.gate.validate_claim(claim, expected_status=status)
        return {self.step_for(e) for e in errors}

    def assert_safe(self, iid):
        claim = self.draft(iid)["claim"]
        failing = self.failing_steps(claim)
        for step in self.CLAIM_STEPS:
            self.assertIn(step, failing, f"{iid}: an unchanged draft would light {step}")

    def test_uses_the_real_tracker_mapping(self):
        _, source = D.load_step_mapper(self.repo)
        self.assertEqual(source, "jobs/readiness-tracker/tracker.py")

    def test_every_fixture_draft_is_safe(self):
        for iid in ("EO:100", "EO:200", "EO:300", "EO:400", "EO:500"):
            self.assert_safe(iid)

    def test_full_runs_and_conflicts_still_safe(self):
        shutil.rmtree(self.repo)
        self.repo = make_repo(self.repo, cl_sample=False)
        self.reload()
        for iid in ("EO:100", "EO:200", "EO:400"):
            self.assert_safe(iid)
        self.assertTrue(self.draft("EO:100")["_draft"]["conflicts"])

    def test_no_clause_draft_has_placeholder_so_gate_checks_everything(self):
        line = self.draft("EO:400")
        cl = line["claim"]["operative_clauses"]
        self.assertEqual([c["scope_id"] for c in cl], [D.PLACEHOLDER_SCOPE_ID])
        self.assertTrue(line["_draft"]["gate"]["placeholder_clause"])
        self.assertEqual(line["_draft"]["clause_count"], 0)
        errs = line["_draft"]["gate"]["errors_now"]
        self.assertNotIn("operative_clauses_empty", errs)
        for e in ("whole_order_end_evidence", "savings_residuals_evidence", "bounded_later_search"):
            self.assertIn(e, errs)
        self.assertEqual(line["_draft"]["readiness"]["by_step"]["counterevidence"], "research")

    def test_counterevidence_needs_status_and_clauses(self):
        self.assertEqual(self.draft("EO:300")["_draft"]["readiness"]["by_step"]["counterevidence"], "research")
        self.assertEqual(self.draft("EO:500")["_draft"]["readiness"]["by_step"]["counterevidence"], "research")

    def test_pre_1937_order_catalog_search_flagged(self):
        self.rd.universe["EO:400"]["date_effective"] = "1930"

        def catalog(iid):
            m = self.draft(iid)["_draft"]["proposals"]["later_source_search_machine"]
            return [x for x in m if x["search_id"] == "later-events:ofr_catalog"][0]

        self.assertIn("coverage_warning", catalog("EO:400"))
        self.assertNotIn("coverage_warning", catalog("EO:100"))
        # an order with clauses, signed before 1937: the U.S. Code search alone does not make counterevidence 'confirm'
        self.rd.crosswalk["EO:100"] = {"signing_date_from_cached_index": "1930-01-02"}
        self.assertIn("coverage_warning", catalog("EO:100"))
        self.assertEqual(self.draft("EO:100")["_draft"]["readiness"]["by_step"]["counterevidence"], "research")


class PartialEndOnYes(Fixture):
    def setUp(self):
        super().setUp()
        le = self.repo / "jobs/later-events/output/FRAGMENTS.jsonl"
        rows = [json.loads(x) for x in le.read_text(encoding="utf-8").splitlines()]
        api = {"url": "https://www.federalregister.gov/api/v1/documents.json?x=2", "sha256": SHA["d"],
               "page_or_item": "OFR API record executive_order_number=210"}
        rows.append(frag("EO:200", "later_event_candidates", [{
            "date_candidate": "1996-02-01", "actor": "EO:210", "mechanism": "revocation",
            "qualifier": "section 1, to the extent inconsistent", "edge_ids": ["LE-20"], "source": api,
            "quote": "Revokes: EO 200 (sec. 1)"}], "later-events"))
        write_jsonl(le, rows)
        self.reload()

    def test_conflict_judgment_and_effort(self):
        d = self.draft("EO:200")["_draft"]
        self.assertIn("PARTIAL_END_CANDIDATE_ON_YES_ORDER", {c["code"] for c in d["conflicts"]})
        self.assertNotEqual(d["readiness"]["by_step"]["ending_or_current_basis"], "confirm")
        self.assertNotEqual(d["effort"], "small")
        named = [j for j in d["needs_judgment"] if j["field"] == "operative_clauses[*].state_at_cutoff / first_end"]
        self.assertEqual(named[0]["clauses_named"], ["EO:200#sec1"])
        # the feasibility copy no longer marks the revoked clause operative
        self.assertFalse(d["gate"]["only_judgment_left"])
        self.assertIn("yes_without_continuing_clause", d["gate"]["errors_if_proposals_accepted"])


BOOK = {"ofr-compilations": ("https://hdl.handle.net/2027/uc1.c025504761", SHA["1"]),
        "isthmian-canal-1911": ("https://hdl.handle.net/2027/ufl1.ark:/13960/t3dz15k02", SHA["2"]),
        "richardson-volumes": ("https://hdl.handle.net/2027/ufl.31262091102953", SHA["3"]),
        "ofr-codification-1989": ("https://hdl.handle.net/2027/uiug.30112026470077", SHA["4"])}


def book_original(iid, job, *, check, conf="high", page="printed pages 5-6, PDF pages 20-21", **data):
    url, sha = BOOK[job]
    return frag(iid, "original_representation", {
        "url": url, "sha256": sha, "page_or_item": f"{job} volume, {page}", "location_confidence": conf,
        "needs_page_check": check, "location_verified": False, "signing_date": data.pop("signing_date", None),
        "source_id": f"{job}:{iid}", "text_path": f"texts/{iid.replace(':', '_')}.txt", **data}, job,
        sources=[{"url": url, "sha256": sha, "page_or_item": page}])


def codification_item(actor, date, mechanism="revocation", flags=(), qualifier=""):
    url, sha = BOOK["ofr-codification-1989"]
    return {"actor": actor, "date_basis": ["acting document date from its SOURCE line in this codification"],
            "date_candidate": date, "date_candidates_conflicting": [], "edge_ids": [f"OC89-{actor}-{mechanism}"],
            "evidence_types": ["ofr_codification_1989_table"],
            "flags": ["status_as_of_1989-01-20", "ocr_table_cell_not_human_verified", *flags],
            "mechanism": mechanism, "qualifier": qualifier, "quote": f"Revokedby EO {actor.split(':')[1]}",
            "quote_kind": "ocr_table_cell", "status": "CANDIDATE_UNVERIFIED", "stated_effective_date_candidates": [],
            "source": {"url": url, "sha256": sha, "page_or_item": "OFR Codification 1945-1989 (1989), Executive "
                                                                    "Orders disposition table, printed page 1021, PDF page 1032"}}


CODIFIED_FIELDS = ["instrument_id", "census_id", "date", "fr_citation", "restated_by", "restated_by_date", "chapter",
                   "chapter_title", "pdf_pages", "printed_pages", "confidence", "table_disposition", "source_text",
                   "text_path", "text_sha256"]


def codified_row(iid, **kw):
    row = {"instrument_id": iid, "census_id": iid, "date": "1950-01-02", "fr_citation": "15 FR 1", "restated_by": "",
           "restated_by_date": "", "chapter": "3", "chapter_title": "Executive Office of the President",
           "pdf_pages": "24-25", "printed_pages": "13-14", "confidence": "high",
           "table_disposition": "Codified atChapter 3, p. 13", "source_text": "SOURCE: The provisions of ...",
           "text_path": f"texts/{iid.replace(':', '_')}.txt", "text_sha256": SHA["5"]}
    row.update(kw)
    return row


class BookSources(Fixture):
    """The printed-volume jobs: official compilations, Richardson, and the OFR 1989 Codification."""

    def write_job(self, job, fragments, summary=None, codified=None):
        out = self.repo / "jobs" / job / "output"
        write_jsonl(out / "FRAGMENTS.jsonl", fragments)
        (out / "SUMMARY.json").write_text(json.dumps(summary or {"job": job}), encoding="utf-8")
        if codified is not None:
            write_csv(out / "CODIFIED_1989.csv", codified, CODIFIED_FIELDS)

    def proposals(self, iid):
        return self.draft(iid)["_draft"]["proposals"]

    # --- official compilations

    def test_official_compilation_high_is_filled_and_strong(self):
        self.write_job("ofr-compilations", [book_original("EO:400", "ofr-compilations", check=False)])
        self.reload()
        line = self.draft("EO:400")
        ref = line["claim"]["original_representation"]
        self.assertEqual(ref, {"url": BOOK["ofr-compilations"][0], "sha256": BOOK["ofr-compilations"][1],
                               "page_or_item": "ofr-compilations volume, printed pages 5-6, PDF pages 20-21"})
        self.assertTrue(self.gate.source_ok(ref))
        cand = line["_draft"]["proposals"]["original_representation"][0]
        self.assertEqual((cand["grade"], cand["strong"], cand["acceptable_as_original"]),
                         ("official_compilation_high", True, True))
        filled = [m for m in line["_draft"]["machine_filled"] if m["field"] == "original_representation"]
        self.assertEqual(filled[0]["grade"], "official_compilation_high")

    def test_official_compilation_needs_page_check_is_never_strong(self):
        # flagged by the job, or a medium location without the flag: both stay weak (the fr-originals rule)
        self.write_job("isthmian-canal-1911", [book_original("EO:400", "isthmian-canal-1911", check=True,
                                                             conf="medium"),
                                               book_original("EO:300", "isthmian-canal-1911", check=False,
                                                             conf="medium")])
        self.reload()
        for iid in ("EO:400", "EO:300"):
            line = self.draft(iid)
            self.assertIsNone(line["claim"]["original_representation"], iid)
            cand = line["_draft"]["proposals"]["original_representation"][0]
            self.assertEqual((cand["grade"], cand["strong"]), ("official_compilation_needs_page_check", False))
        # still acceptable after a page check: the feasibility test may use it
        g = self.draft("EO:400")["_draft"]["gate"]
        self.assertNotIn("original_representation_provenance", g["errors_if_proposals_accepted"])

    def test_fr_original_outranks_an_official_compilation(self):
        self.write_job("ofr-compilations", [book_original("EO:100", "ofr-compilations", check=False)])
        self.reload()
        line = self.draft("EO:100")
        self.assertEqual(line["claim"]["original_representation"]["sha256"], SHA["a"])  # the FR page
        grades = [c["grade"] for c in line["_draft"]["proposals"]["original_representation"]]
        self.assertEqual(grades[:2], ["fr_originals_high", "official_compilation_high"])

    # --- Richardson

    def test_richardson_is_a_lead_never_the_original(self):
        self.write_job("richardson-volumes", [book_original(
            "EO:400", "richardson-volumes", check=False, source_kind="printed compilation, not the signed original",
            identified_by="wpa_citation")])
        self.reload()
        line = self.draft("EO:400")
        d = line["_draft"]
        self.assertIsNone(line["claim"]["original_representation"])
        cand = d["proposals"]["original_representation"][0]
        self.assertEqual((cand["grade"], cand["strong"], cand["acceptable_as_original"]),
                         ("compiled_transcription_lead", False, False))
        what = " ".join(m["what"] for m in d["missing_evidence"] if m["step"] == "original_text")
        self.assertIn("compiled-transcription", what)
        # the feasibility test never accepts it, so original_text stays a research step
        self.assertIn("original_representation_provenance", d["gate"]["errors_if_proposals_accepted"])
        self.assertEqual(d["readiness"]["by_step"]["original_text"], "research")
        self.assertIn("original_representation (lead)", [j["field"] for j in d["needs_judgment"]])

    def test_richardson_beside_an_official_candidate_does_not_block_it(self):
        self.write_job("richardson-volumes", [book_original("EO:400", "richardson-volumes", check=False)])
        self.write_job("ofr-compilations", [book_original("EO:400", "ofr-compilations", check=True, conf="medium")])
        self.reload()
        d = self.draft("EO:400")["_draft"]
        grades = [c["grade"] for c in d["proposals"]["original_representation"]]
        self.assertEqual(grades, ["official_compilation_needs_page_check", "compiled_transcription_lead"])
        self.assertNotIn("original_representation_provenance", d["gate"]["errors_if_proposals_accepted"])
        self.assertNotIn("original_text", [m["step"] for m in d["missing_evidence"]])

    # --- American Presidency Project and other declared transcriptions

    def app_original(self, iid, job, node):
        url = f"https://www.presidency.ucsb.edu/documents/executive-order-{iid[3:]}-x"
        data = {"url": url, "sha256": SHA["5"], "page_or_item": f"APP node {node}", "needs_page_check": False,
                "location_confidence": "high", "acceptable_as_original": False, "grade": "mirror_transcription",
                "representation_type": "secondary_compilation_transcription", "source_id": f"app:{iid}:{node}",
                "text_path": "texts/x.txt"}
        return frag(iid, "original_representation", data, job, grade="mirror_transcription",
                    acceptable_as_original=False, sources=[{"url": url, "sha256": SHA["5"], "page_or_item": node}])

    def test_app_and_declared_transcriptions_are_leads_never_the_original(self):
        # Even with needs_page_check false and high location confidence, as the APP records carry.
        self.write_job("app-executive-orders", [self.app_original("EO:400", "app-executive-orders", "1")])
        self.write_job("some-new-mirror", [self.app_original("EO:400", "some-new-mirror", "2")])
        self.reload()
        line = self.draft("EO:400")
        self.assertIsNone(line["claim"]["original_representation"])
        cands = line["_draft"]["proposals"]["original_representation"]
        self.assertEqual(len(cands), 2)
        for c in cands:
            self.assertEqual((c["grade"], c["strong"], c["acceptable_as_original"]),
                             ("compiled_transcription_lead", False, False))
        self.assertIn("web transcription", " ".join(c["why"] for c in cands))
        self.assertEqual(line["_draft"]["readiness"]["by_step"]["original_text"], "research")

    def test_split_fragment_files_are_read(self):
        out = self.repo / "jobs" / "app-transcriptions" / "output"
        self.write_job("app-transcriptions", [])
        write_jsonl(out / "FRAGMENTS_APP.jsonl", [self.app_original("EO:400", "app-transcriptions", "3")])
        self.reload()
        cands = self.draft("EO:400")["_draft"]["proposals"]["original_representation"]
        self.assertEqual([c["grade"] for c in cands], ["compiled_transcription_lead"])

    # --- the 1989 Codification: endings

    def test_codification_revocation_becomes_a_whole_order_end_proposal(self):
        self.write_job("ofr-codification-1989", [frag("EO:400", "later_event_candidates", [
            codification_item("EO:450", "1945-06-01"),
            codification_item("EO:460", "1946-01-01", flags=["needs_page_check"]),
            codification_item("EO:470", "1947-01-01", mechanism="supersession")], "ofr-codification-1989")])
        self.reload()
        d = self.draft("EO:400")["_draft"]
        whole = d["proposals"]["whole_order_end"]
        self.assertEqual([w["proposal"]["actor"] for w in whole], ["EO:450"])  # only the clean revocation
        w = whole[0]
        self.assertEqual(set(w["proposal"]), {"date", "actor", "mechanism", "source"})
        self.assertEqual(w["proposal"]["date"], "1945-06-01")
        self.assertIn(D.CODIFICATION_FLAG, w["meta"]["flags"])
        self.assertIn("whole_end_from_1989_disposition_table", w["meta"]["flags"])
        self.assertIn("not its effective date", w["meta"]["caution"])
        self.assertTrue(w["suggested"])
        self.assertFalse(w["group"]["corroborated_by_two_jobs"])
        # every item is also a later event, in the later-event shape (date_candidate, never effective_date)
        events = d["proposals"]["later_events"]
        self.assertEqual(sorted(e["proposal"]["actor"] for e in events), ["EO:450", "EO:460", "EO:470"])
        for e in events:
            self.assertEqual(set(e["proposal"]), {"date_candidate", "actor", "mechanism", "source"})
            self.assertIn(D.CODIFICATION_FLAG, e["meta"]["flags"])
        # a provisional NO order with a dated ending: the ending is now a judgment, not missing evidence
        self.assertNotIn("ending_or_current_basis", [m["step"] for m in d["missing_evidence"]])
        self.assertIsNone(self.draft("EO:400")["claim"]["whole_order_end"])  # never machine-filled

    def test_codification_end_withheld_when_any_job_says_partial(self):
        self.write_job("ofr-codification-1989", [frag("EO:400", "later_event_candidates", [
            codification_item("EO:450", "1945-06-01")], "ofr-codification-1989")])
        le = self.repo / "jobs/later-events/output/FRAGMENTS.jsonl"
        rows = [json.loads(x) for x in le.read_text(encoding="utf-8").splitlines()]
        rows.append(frag("EO:400", "later_event_candidates", [{
            "date_candidate": "1945-06-01", "actor": "EO:450", "mechanism": "revocation", "qualifier": "section 3",
            "edge_ids": ["LE-450"], "flags": [], "evidence_types": ["ofr_note_on_target"],
            "source": codification_item("EO:450", "1945-06-01")["source"], "quote": "Sec. 3 revoked by EO 450"}],
            "later-events"))
        write_jsonl(le, rows)
        self.reload()
        d = self.draft("EO:400")["_draft"]
        self.assertEqual(d["proposals"]["whole_order_end"], [])
        codes = {c["code"] for c in d["conflicts"]}
        self.assertIn("FULL_AND_PARTIAL_EVIDENCE_CONFLICT", codes)
        cod = [e for e in d["proposals"]["later_events"] if e["meta"]["from_job"] == "ofr-codification-1989"][0]
        self.assertIn("full_and_partial_evidence_conflict", cod["meta"]["flags"])

    def test_codification_and_later_events_are_one_source_not_two(self):
        # later-events' OFR catalog notes are the online edition of the same 1989 tables
        self.write_job("ofr-codification-1989", [frag("EO:100", "later_event_candidates", [
            codification_item("EO:150", "1955-03-01")], "ofr-codification-1989")])
        self.reload()
        whole = self.proposals("EO:100")["whole_order_end"]
        grp = [w["group"] for w in whole if w["proposal"]["actor"] == "EO:150"][0]
        self.assertEqual(grp["jobs"], ["later-events", "ofr-codification-1989"])
        self.assertFalse(grp["corroborated_by_two_jobs"])
        # later-events stays first in the group, so its proposal is the suggested one
        sugg = [w for w in whole if w["suggested"]][0]
        self.assertEqual(sugg["meta"]["from_job"], "later-events")

    # --- the 1989 Codification: in-force snapshot

    def test_in_force_1989_is_a_lead_that_never_reaches_the_cutoff(self):
        self.write_job("ofr-codification-1989", [], codified=[codified_row("EO:200")])
        prov = self.repo / "jobs/ofr-codification-1989/data/PROVENANCE.json"
        prov.parent.mkdir(parents=True)
        prov.write_text(json.dumps({"book": {"handle_url": BOOK["ofr-codification-1989"][0],
                                             "pdf_sha256": BOOK["ofr-codification-1989"][1]}}), encoding="utf-8")
        self.reload()
        d = self.draft("EO:200")["_draft"]
        preds = d["proposals"]["current_predicate"]
        self.assertEqual(preds[0]["meta"]["basis_code"], "cfr_authority_citation")  # current law first
        snap = preds[-1]
        self.assertEqual(snap["meta"]["basis_code"], D.CODIFICATION_BASIS_CODE)
        self.assertEqual(snap["proposal"]["checked_through"], "1989-01-20")
        self.assertTrue(snap["proposal"]["legal_basis"].startswith("LEAD ONLY"))
        self.assertTrue(self.gate.source_ok(snap["proposal"]["source"]))
        self.assertEqual(snap["proposal"]["source"]["sha256"], BOOK["ofr-codification-1989"][1])
        self.assertTrue(d["gate"]["only_judgment_left"])  # the current-law lead, not the snapshot, is used
        # Without the current-law lead the snapshot alone is never enough.
        cl = self.repo / "jobs/current-law/output/FRAGMENTS.jsonl"
        rows = [json.loads(x) for x in cl.read_text(encoding="utf-8").splitlines()]
        write_jsonl(cl, [r for r in rows if r["instrument_id"] != "EO:200"])
        self.reload()
        d = self.draft("EO:200")["_draft"]
        self.assertTrue(any(D.CODIFICATION_BASIS_CODE == p["meta"]["basis_code"]
                            for p in d["proposals"]["current_predicate"]))
        # the feasibility test does not use the snapshot, so no clause can be shown operative
        self.assertIn("yes_without_continuing_clause", d["gate"]["errors_if_proposals_accepted"])
        self.assertFalse(d["gate"]["only_judgment_left"])
        # and pasting the snapshot itself into a clause still fails the gate (checked_through is 1989-01-20)
        claim = self.draft("EO:200")["claim"]
        snap = [p for p in d["proposals"]["current_predicate"] if p["meta"]["basis_code"] == D.CODIFICATION_BASIS_CODE]
        claim["operative_clauses"][0].update(state_at_cutoff="operative", current_predicate=snap[0]["proposal"])
        self.assertIn("clause_0_current_predicate", self.gate.validate_claim(claim, expected_status="yes"))
        what = " ".join(m["what"] for m in d["missing_evidence"] if m["step"] == "ending_or_current_basis")
        self.assertIn("no job found a current-law predicate lead", what)
        self.assertIn("1989", what)
        self.assertEqual(d["readiness"]["by_step"]["ending_or_current_basis"], "research")

    def test_no_order_in_force_in_1989_without_a_later_end_is_a_conflict(self):
        self.write_job("ofr-codification-1989", [frag("EO:100", "later_event_candidates", [
            codification_item("EO:150", "1955-03-01")], "ofr-codification-1989")],
            codified=[codified_row("EO:100"), codified_row("EO:400", restated_by="EO:410",
                                                            restated_by_date="1964-09-01")])
        self.reload()
        d = self.draft("EO:100")["_draft"]
        codes = [c["code"] for c in d["conflicts"]]
        self.assertIn("NO_ORDER_IN_FORCE_ON_1989_01_20", codes)
        # the 1989 snapshot is not a current-law citation: that conflict still names only the U.S. Code lead
        cited = [c for c in d["conflicts"] if c["code"] == "NO_ORDER_CITED_IN_CURRENT_LAW"][0]
        self.assertIn("1 current-law predicate lead", cited["detail"])
        # an order whose text was restated by a later order is not flagged
        d400 = self.draft("EO:400")["_draft"]
        self.assertNotIn("NO_ORDER_IN_FORCE_ON_1989_01_20", [c["code"] for c in d400["conflicts"]])
        snap = [p for p in d400["proposals"]["current_predicate"]
                if p["meta"]["basis_code"] == D.CODIFICATION_BASIS_CODE]
        self.assertIn("restated_in_entirety_by_later_order", snap[0]["meta"]["flags"])
        self.assertIn("EO:410", snap[0]["proposal"]["legal_basis"])

    def test_no_order_in_force_in_1989_with_a_later_end_is_not_a_conflict(self):
        self.write_job("ofr-codification-1989", [frag("EO:400", "later_event_candidates", [
            codification_item("EO:450", "1995-06-01")], "ofr-codification-1989")],
            codified=[codified_row("EO:400")])
        self.reload()
        codes = [c["code"] for c in self.draft("EO:400")["_draft"]["conflicts"]]
        self.assertNotIn("NO_ORDER_IN_FORCE_ON_1989_01_20", codes)

    def test_book_drafts_stay_tracker_safe(self):
        self.write_job("ofr-compilations", [book_original("EO:400", "ofr-compilations", check=False)])
        self.write_job("richardson-volumes", [book_original("EO:200", "richardson-volumes", check=False)])
        self.write_job("ofr-codification-1989", [frag("EO:400", "later_event_candidates", [
            codification_item("EO:450", "1945-06-01")], "ofr-codification-1989")],
            codified=[codified_row("EO:200"), codified_row("EO:400")])
        self.reload()
        safety = TrackerSafety("test_uses_the_real_tracker_mapping")
        safety.gate, safety.rd, safety.step_for = self.gate, self.rd, self.step_for
        safety.draft = self.draft
        for iid in ("EO:100", "EO:200", "EO:300", "EO:400", "EO:500"):
            safety.assert_safe(iid)
            self.assertEqual(self.draft(iid)["claim"]["later_source_search"], [])


class InputSafety(Fixture):
    def test_failed_run_status_is_not_merged(self):
        out = self.repo / "jobs/later-events/output"
        (out / "STATUS.json").write_text(json.dumps({"job": "later-events", "result": "failed", "exit_code": 1}),
                                         encoding="utf-8")
        inputs, notes = D.discover_inputs(self.repo)
        self.assertNotIn("later-events", [i.job for i in inputs])
        self.assertTrue(any("later-events" in n and "failed" in n for n in notes))

    def test_succeeded_status_is_merged(self):
        out = self.repo / "jobs/later-events/output"
        (out / "STATUS.json").write_text(json.dumps({"result": "succeeded", "exit_code": 0}), encoding="utf-8")
        inputs, _ = D.discover_inputs(self.repo)
        self.assertIn("later-events", [i.job for i in inputs])

    def test_duplicate_env_folders_read_once_and_labels_are_portable(self):
        a = self.repo / "jobs/later-events/output"
        outside = pathlib.Path(self.tmp) / "elsewhere" / "le-out"
        shutil.copytree(a, outside)
        with redirect_stdout(io.StringIO()):
            inputs, notes = D.discover_inputs(self.repo, f"{a};{a};{outside}")
        self.assertEqual(len(inputs), 2)
        self.assertTrue(any("more than once" in n for n in notes))
        self.assertEqual(inputs[0].origin, "env:jobs/later-events/output")
        self.assertEqual(inputs[1].origin, "env:.../elsewhere/le-out")
        for i in inputs:
            self.assertNotIn(str(self.tmp), i.label())
            self.assertNotIn(pathlib.Path(self.tmp).as_posix(), i.label())


class Outputs(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="claim-drafts-out-"))
        self.repo = make_repo(self.tmp / "repo")
        self.old = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.old)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_main(self, **env):
        for k in ("JOB_LIMIT", "CLAIM_DRAFTS_INPUTS", "CLAIM_DRAFTS_IDS", "CLAIM_DRAFTS_SCOPE"):
            os.environ.pop(k, None)
        os.environ.update({"REPO_ROOT": str(self.repo), "OUTPUT_DIR": str(self.tmp / "out"),
                           "CLAIM_DRAFTS_CHECKER": "0", **env})
        with redirect_stdout(io.StringIO()):
            return D.main()

    def test_default_scope_is_decided_only(self):
        s = self.run_main()
        self.assertEqual(s["scope"], "decided")
        self.assertEqual(s["orders_with_draft"], 3)
        self.assertFalse((self.tmp / "out" / "DRAFT_CLAIMS_UNDECIDED.jsonl").exists())

    def test_end_to_end(self):
        s = self.run_main(CLAIM_DRAFTS_SCOPE="all")
        out = self.tmp / "out"
        dec = [json.loads(x) for x in (out / "DRAFT_CLAIMS.jsonl").read_text(encoding="utf-8").splitlines()]
        und = [json.loads(x) for x in (out / "DRAFT_CLAIMS_UNDECIDED.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([x["instrument_id"] for x in dec], ["EO:100", "EO:200", "EO:400"])
        self.assertEqual([x["instrument_id"] for x in und], ["EO:500"])
        self.assertEqual(s["orders_with_draft"], 4)
        self.assertEqual(s["drafts_whose_only_remaining_gaps_are_judgment_fields"], 2)
        self.assertIn("NO_ORDER_CITED_IN_CURRENT_LAW", s["top_conflict_types"])
        with open(out / "TODO_BY_ORDER.csv", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(rows[0]["instrument_id"], "EO:100")
        self.assertIn("clause_*_state x2", rows[0]["remaining_gate_errors"])
        self.assertIn(rows[0]["estimated_effort"], ("small", "medium", "large"))
        self.assertNotIn("checker_result", rows[0])
        self.assertIn("sources_and_quotes_check", rows[0])
        for x in dec + und:  # no absolute local paths in committed output
            self.assertNotIn(str(self.tmp), json.dumps(x))
            self.assertNotIn(self.tmp.as_posix(), json.dumps(x))
        self.assertEqual(list((self.repo / "research/readiness/claims").iterdir()), [])
        raw = (out / "DRAFT_CLAIMS.jsonl").read_bytes()
        self.assertNotIn(b"\r\n", raw)
        self.assertEqual(s["network_requests"], 0)

    def test_limit_and_ids(self):
        s = self.run_main(JOB_LIMIT="1")
        self.assertEqual(s["orders_with_draft"], 1)
        s = self.run_main(CLAIM_DRAFTS_IDS="EO:200,EO:999")
        self.assertEqual(s["orders_with_draft"], 1)
        self.assertEqual(s["ids_not_in_universe"], ["EO:999"])
        self.assertTrue(any("EO:999" in n for n in s["input_notes"]))

    def test_bad_limit_exits_2(self):
        with self.assertRaises(SystemExit) as cm:
            self.run_main(JOB_LIMIT="zero")
        self.assertEqual(cm.exception.code, 2)

    def test_bad_max_file_mb_exits_2(self):
        with self.assertRaises(SystemExit) as cm:
            self.run_main(CLAIM_DRAFTS_MAX_FILE_MB="lots")
        self.assertEqual(cm.exception.code, 2)

    def test_wrongly_typed_sibling_fields_do_not_stop_the_run(self):
        le = self.repo / "jobs/later-events/output/FRAGMENTS.jsonl"
        rows = [json.loads(x) for x in le.read_text(encoding="utf-8").splitlines()]
        bad = {"date_candidate": 19550301, "actor": ["EO:150"], "mechanism": 7, "qualifier": 5, "flags": 3,
               "edge_ids": "LE-x", "source": "nope", "quote": ["x"]}
        bad2 = {"date_candidate": "1960-01-01", "actor": "EO:170", "mechanism": {"m": 1}, "qualifier": ["s"]}
        odd_ok = {"date_candidate": "1961-01-01", "actor": "EO:171", "mechanism": "revocation", "qualifier": 12,
                  "flags": "x", "edge_ids": 4, "stated_effective_date_candidates": "1961", "quote": 99,
                  "later_reinstatement_candidates": {"a": 1}, "source": None}
        rows.append(frag("EO:200", "later_event_candidates", [bad, bad2, odd_ok, 17, None], "later-events"))
        rows.append(frag("EO:400", "whole_order_end_candidates", [bad, odd_ok], "later-events"))
        write_jsonl(le, rows)
        cl = self.repo / "jobs/current-law/output/FRAGMENTS.jsonl"
        rows = [json.loads(x) for x in cl.read_text(encoding="utf-8").splitlines()]
        rows.append(frag("EO:400", "current_predicate_candidates", [
            {"legal_basis_candidate": ["x"], "basis_code": ["y"], "checked_through": 2026},
            {"legal_basis_candidate": "ok basis", "basis_code": ["y"], "where": ["w"], "snippet": 4}],
            "current-law"))
        rows.append(frag("EO:400", "whole_order_end_candidates", [
            {"date_candidate": "1950-01-01", "acting_instrument_id": 7, "actor_candidate": ["x"],
             "mechanism_candidate": "revocation"}], "current-law"))
        write_jsonl(cl, rows)
        s = self.run_main()  # must not raise
        self.assertEqual(s["orders_with_draft"], 3)
        skipped = {k: v for k, v in s["input_counts"].items() if k.startswith("items_skipped_wrong_type")}
        self.assertGreaterEqual(sum(skipped.values()), 4)
        self.assertTrue(any("item skipped" in p for p in s["input_problems"]))

    def test_refuses_to_write_into_research(self):
        with self.assertRaises(SystemExit):
            self.run_main(OUTPUT_DIR=str(self.repo / "research/readiness/claims"))

    def test_rolling_writer_splits(self):
        out = self.tmp / "roll"
        out.mkdir()
        w = D.RollingWriter(out, "X.jsonl", 50)
        for n in range(5):
            w.write({"n": n, "pad": "x" * 20})
        w.close()
        self.assertEqual(w.files, ["X.jsonl", "X_2.jsonl", "X_3.jsonl", "X_4.jsonl", "X_5.jsonl"])


class EmbeddedCheckerOfflineTests(Fixture):
    def test_standalone_receipts_are_reused_read_only_and_rehashed(self):
        dest = self.repo / "jobs/claim-checker"
        dest.mkdir(parents=True)
        for name in ("checker.py", "sources.py"):
            shutil.copy(REAL_REPO / "jobs/claim-checker" / name, dest / name)
        inputs, _ = D.discover_inputs(self.repo)
        cache = pathlib.Path(self.tmp) / ".job-cache"
        data = b"verified predecessor source bytes"
        sha = hashlib.sha256(data).hexdigest()
        receipt = cache / "claim-checker/verified" / sha[:2] / (sha + ".bin")
        receipt.parent.mkdir(parents=True)
        receipt.write_bytes(data)
        url = "https://www.govinfo.gov/content/pkg/standalone.pdf"
        runner = D.CheckerRunner(self.repo, cache / "claim-drafts", inputs)
        runner.index.add(runner.mod.S.HeldCopy("predecessor", sha, url, custody="record_only"))
        ref = {"url": url, "sha256": sha, "page_or_item": "whole document"}
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
            rows = []
            runner.mod.check_source(ref, "original_representation", runner.ctx, rows)
            self.assertEqual(rows[0]["status"], "held_bytes_verified")
            self.assertEqual(runner.verification.hashes, 1)
            self.assertEqual(receipt.read_bytes(), data)
            self.assertFalse((cache / "claim-drafts/checker-text/verified").exists())
            receipt.write_bytes(b"corrupt predecessor receipt")
            rows = []
            runner.mod.check_source(ref, "original_representation", runner.ctx, rows)
            self.assertEqual(rows[0]["status"], "custody_record_only")

    def test_checker_cannot_download_even_with_standalone_allowance(self):
        dest = self.repo / "jobs/claim-checker"
        dest.mkdir(parents=True)
        for name in ("checker.py", "sources.py"):
            shutil.copy(REAL_REPO / "jobs/claim-checker" / name, dest / name)
        inputs, _ = D.discover_inputs(self.repo)
        with mock.patch.dict(os.environ, {"CLAIM_CHECKER_VERIFY_DOWNLOADS": "400"}), \
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")) as network:
            runner = D.CheckerRunner(self.repo, pathlib.Path(self.tmp) / "cache", inputs)
            result, rows = runner.check(self.draft("EO:100")["claim"], 1)
        network.assert_not_called()
        self.assertNotIn("checker_error", result)
        self.assertTrue(any(r["status"] == "custody_record_only" for r in rows))
        self.assertFalse(result["gate_passed"])
        self.assertFalse(result["steps_checker_passed"]["original_text"])


class OfflineVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.data = b"held GovInfo bytes"
        self.sha = hashlib.sha256(self.data).hexdigest()
        self.path = self.root / "verified" / self.sha[:2] / (self.sha + ".bin")
        self.url = "https://www.govinfo.gov/content/pkg/example.pdf"

    def write_receipt(self, data=None):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(self.data if data is None else data)

    def test_cold_warm_and_new_run_rehash(self):
        self.write_receipt()
        verify = D.OfflineVerification()
        self.assertIs(verify(self.url, self.sha, self.root), True)
        self.assertIs(verify(self.url, self.sha, self.root), True)
        self.assertEqual((verify.hashes, verify.cache_hits), (1, 1) if verify.reuse_unchanged else (2, 0))
        fresh = D.OfflineVerification()
        self.assertIs(fresh(self.url, self.sha, self.root), True)
        self.assertEqual(fresh.hashes, 1)

    def test_missing_receipt_is_never_fetched_or_promoted(self):
        verify = D.OfflineVerification()
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
            self.assertIsNone(verify(self.url, self.sha, self.root))
        self.assertFalse(self.path.exists())
        self.write_receipt()
        self.assertIs(verify(self.url, self.sha, self.root), True)

    def test_corruption_with_preserved_size_and_mtime_invalidates(self):
        self.write_receipt()
        verify = D.OfflineVerification()
        self.assertIs(verify(self.url, self.sha, self.root), True)
        before = self.path.stat()
        self.write_receipt(b"x" * len(self.data))
        os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertIs(verify(self.url, self.sha, self.root), False)
        self.assertIs(verify(self.url, self.sha, self.root), False)
        self.assertEqual(verify.hashes, 2 if verify.reuse_unchanged else 3)
        self.write_receipt()
        self.assertIs(verify(self.url, self.sha, self.root), True)

    def test_replacement_deletion_and_separate_cache_root(self):
        self.write_receipt()
        verify = D.OfflineVerification()
        self.assertIs(verify(self.url, self.sha, self.root), True)
        replacement = self.path.with_suffix(".replacement")
        replacement.write_bytes(b"x" * len(self.data))
        replacement.replace(self.path)
        self.assertIs(verify(self.url, self.sha, self.root), False)
        self.path.unlink()
        self.assertIsNone(verify(self.url, self.sha, self.root))
        self.assertIsNone(verify(self.url, self.sha, self.root / "another"))

    def test_restricts_verification_to_original_checker_hosts(self):
        self.write_receipt()
        verify = D.OfflineVerification()
        for url in ("http://www.govinfo.gov/example", "https://example.com/file", None):
            self.assertIsNone(verify(url, self.sha, self.root))
        self.assertEqual(verify.hashes, 0)

    def test_platform_without_change_time_rehashes_every_reference(self):
        self.write_receipt()
        verify = D.OfflineVerification()
        verify.reuse_unchanged = False
        self.assertIs(verify(self.url, self.sha, self.root), True)
        self.assertIs(verify(self.url, self.sha, self.root), True)
        self.assertEqual((verify.hashes, verify.cache_hits), (2, 0))

    def test_atomic_replacement_or_removal_during_hash_is_unverified(self):
        real_sha256 = hashlib.sha256
        for action in ("replace", "remove"):
            with self.subTest(action=action):
                self.write_receipt()
                verify = D.OfflineVerification()
                path = self.path

                class ChangedWhileHashing:
                    def __init__(self):
                        self.digest = real_sha256()

                    def update(self, chunk):
                        self.digest.update(chunk)

                    def hexdigest(self):
                        answer = self.digest.hexdigest()
                        if action == "replace":
                            replacement = path.with_suffix(".replacement")
                            replacement.write_bytes(b"different bytes")
                            replacement.replace(path)
                        else:
                            path.unlink()
                        return answer

                with mock.patch.object(D.hashlib, "sha256", ChangedWhileHashing):
                    self.assertIsNone(verify(self.url, self.sha, self.root))
                self.assertEqual(verify._verified, {})


if __name__ == "__main__":
    unittest.main()


class DeclaredSearchWithCoverage(Fixture):
    """A job that declares its own complete search in SUMMARY.json machine_searches and lists per-order
    coverage in SEARCH_COVERAGE.csv (Namier): the search is entered only for covered orders, with the
    coverage note as a warning where the job could not search, and its leads count as machine hits."""

    def setUp(self):
        super().setUp()
        nm = self.repo / "jobs/namier/output"
        nm.mkdir(parents=True)
        entry = {"repository": "held order texts in this repository (synthetic)",
                 "query_or_scope": "the full name of the person this order concerns in every other held order text",
                 "checked_on": "2026-10-29", "searched_by": "jobs/namier (machine search)"}
        (nm / "SUMMARY.json").write_text(json.dumps({"job": "namier", "machine_searches": [
            {"search_id": "namier:held_texts_person_name", "complete": True, "scope_note": "", "entry": entry}]}),
            encoding="utf-8")
        write_csv(nm / "SEARCH_COVERAGE.csv", [
            {"instrument_id": "EO:100", "search_id": "namier:held_texts_person_name", "covered": "1", "note": "searched for Ada M. Nolan"},
            {"instrument_id": "EO:400", "search_id": "namier:held_texts_person_name", "covered": "0", "note": "no personal name parsed"}])
        item = {"actor": "EO:150", "date_candidate": "1955-03-01", "mechanism": "names_same_person",
                "qualifier": "names Ada M. Nolan; does not cite this order by number; relation by date: later",
                "edge_ids": ["NM-1"], "evidence_types": ["held_text_name_match"], "flags": ["name_match_lead"],
                "quote": "Ada M. Nolan may be reinstated", "quote_kind": "verbatim_text_snippet",
                "source": {"sha256": SHA["d"], "url": "https://example.gov/EO_150", "page_or_item": "page 1",
                           "text_path": "jobs/x/texts/EO_150.txt", "text_sha256": SHA["d"]}}
        write_jsonl(nm / "FRAGMENTS.jsonl", [frag("EO:100", "later_event_candidates", [item], "namier")])
        self.reload()

    def machine(self, iid):
        m = self.draft(iid)["_draft"]["proposals"]["later_source_search_machine"]
        return [x for x in m if x["search_id"] == "namier:held_texts_person_name"]

    def test_declared_search_entered_only_where_covered(self):
        self.assertIn("namier:held_texts_person_name", {s["search_id"] for s in self.merged.searches})
        covered = self.machine("EO:100")
        self.assertEqual(len(covered), 1)
        self.assertNotIn("coverage_warning", covered[0])
        self.assertEqual(covered[0]["machine_hits_for_this_order"], 1)
        not_searched = self.machine("EO:400")
        self.assertEqual(len(not_searched), 1)
        self.assertEqual(not_searched[0]["coverage_warning"], "no personal name parsed")
        self.assertEqual(self.machine("EO:200"), [])  # not a one-person order: the search does not apply
        # The name match is a later-event proposal, never an ending.
        props = self.draft("EO:100")["_draft"]["proposals"]
        names = [c for c in props["later_events"] if c["proposal"]["mechanism"] == "names_same_person"]
        self.assertEqual(len(names), 1)
        self.assertEqual(names[0]["proposal"]["actor"], "EO:150")
        self.assertNotIn("names_same_person", [w.get("mechanism") for w in props.get("whole_order_end", [])])
