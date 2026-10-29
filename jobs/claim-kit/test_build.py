"""Offline full-corpus integration fixtures for the model-neutral claim kit."""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import build as B
import kit as K
import assemble as A
import inputs as I

REPO = HERE.parents[1]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class BuildIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.out = self.repo / "jobs/claim-kit/output"
        census = self.repo / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
        census.parent.mkdir(parents=True)
        with census.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["id", "included_in_bibliography"])
            writer.writeheader()
            writer.writerows({"id": f"EO:{number}", "included_in_bibliography": "1"} for number in range(1, 7))
        self.status = self.repo / I.STATUSES
        self.status.parent.mkdir(parents=True)
        self.status.write_text("instrument_id,provisional_substantive_status\nEO:1,no\nEO:2,no\nEO:3,yes\nEO:5,no\nEO:6,no\n", encoding="utf-8")
        gate = self.repo / "research/stage19/code/claim_gate.py"
        gate.parent.mkdir(parents=True)
        gate.write_bytes((REPO / "research/stage19/code/claim_gate.py").read_bytes())
        texts = {
            "EO:1": "EXECUTIVE ORDER 1\nThe First Board shall perform the specified duties.\n",
            "EO:2": "EXECUTIVE ORDER 2\nThe Second Board shall perform the specified duties.\n",
            "EO:3": "EXECUTIVE ORDER 3\nThe Service shall provide the specified services.\n",
            "EO:4": "EXECUTIVE ORDER 4\nThe Temporary Committee shall operate for a period of two years from January 1, 1990.\n",
            "EO:5": "EXECUTIVE ORDER 5\nExecutive Order 1 is hereby revoked effective January 2, 2000.\nExecutive Order 2 is hereby revoked effective January 2, 2000.\n",
            "EO:999": "EXECUTIVE ORDER 999\nThis outside-census lead shall never create an identity.\n",
        }
        provenance = []
        for iid, text in texts.items():
            rel = "jobs/future-source/data/texts/" + iid.replace(":", "_") + ".txt"
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            provenance.append({"instrument_id": iid, "text_path": rel,
                               "kind": "original_representation", "acceptable_as_original": True,
                               "signing_date": "2000-01-01" if iid == "EO:5" else "1990-01-01",
                               "source": {"url": "https://example.gov/" + iid.replace(":", "_"),
                                          "sha256": digest, "text_sha256": digest, "page_or_item": "PDF page 1"}})
        write_json(self.repo / "jobs/future-source/data/PROVENANCE.json", {"representations": provenance})
        search = {"search_id": "complete", "repository": "complete synthetic held corpus",
                  "query_or_scope": "all held orders through 2026-10-14", "checked_on": "2026-10-18"}
        write_json(self.repo / "jobs/claim-drafts/output/SUMMARY.json", {"machine_searches": [search]})
        drafts = []
        for iid in ("EO:1", "EO:2", "EO:3", "EO:5", "EO:6"):
            drafts.append({"instrument_id": iid, "claim": {"unresolved_material_gaps": []},
                           "_draft": {"provisional_status": "yes" if iid == "EO:3" else "no", "conflicts": [],
                                      "proposals": {"later_source_search_machine": [{"search_id": "complete"}]}}})
        write_jsonl(self.repo / "jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl", drafts)
        # Known pairs include one absent actor source, kept visible as missing.
        write_jsonl(self.repo / "jobs/future-source/output/FRAGMENTS.jsonl", [
            {"instrument_id": "EO:1", "kind": "later_event_candidates", "data": [
                {"actor_id": "EO:5"}, {"actor_id": "EO:6"}]},
            {"instrument_id": "EO:2", "kind": "later_event_candidates", "data": [{"actor_id": "EO:5"}]},
        ])

    def run_build(self, output=None, cache=None):
        with redirect_stdout(io.StringIO()):
            return B.build(self.repo, output or self.out, cache)

    def dossier(self, iid):
        return json.loads((self.out / "dossiers" / (B.filename(iid) + ".json")).read_text(encoding="utf-8"))

    def decision(self, iid="EO:1"):
        dossier = self.dossier(iid)
        sheet = A.blank_sheet(dossier, "synthetic-producer")
        ending = next(eid for eid in dossier["actor_provisions"] if dossier["evidence"][eid]["actor_id"] == "EO:5")
        sheet.update({"approved": True, "original_confirmed": True, "inventory_confirmed": True,
                      "unresolved_material_gaps": [], "search_ids": ["complete"],
                      "research_rationale": "Synthetic fixture: the cited original and acting provision were inspected, including all prior terms and savings.",
                      "savings": {"state": "none_after_bounded_search", "source_id": ending,
                                  "reason": "The bounded synthetic corpus includes no savings provisions."}})
        for clause in sheet["clauses"]:
            clause.update({"state": "terminated", "end_id": ending,
                           "effective_date": "2000-01-02", "effective_date_confirmed": True,
                           "reason": "The fixture's express revocation ends this duty; no earlier term applies."})
        return sheet

    def test_whole_population_including_yes_no_undecided_and_missing(self):
        summary = self.run_build()
        self.assertTrue(summary["lead_only"])
        self.assertEqual(summary["counts"]["universe_orders"], 6)
        self.assertEqual(summary["counts"]["decided_orders"], 5)
        self.assertEqual(summary["counts"]["status_leads"], 1)
        self.assertEqual(summary["counts"]["dossiers"], 5)
        index = json.loads((self.out / "INDEX.json").read_text(encoding="utf-8"))
        self.assertEqual({r["instrument_id"] for r in index}, {"EO:1", "EO:2", "EO:3", "EO:5", "EO:6"})
        self.assertEqual(self.dossier("EO:3")["whole_order_status"], "yes")
        self.assertTrue(any("Current legal predicate" in text for text in self.dossier("EO:3")["missing"]))
        self.assertFalse(self.dossier("EO:6")["clauses"])
        self.assertTrue(self.dossier("EO:6")["missing"])
        status_leads = read_jsonl(self.out / "STATUS_LEADS.jsonl")
        self.assertEqual([r["instrument_id"] for r in status_leads], ["EO:4"])
        self.assertIsNone(status_leads[0]["status"])
        self.assertEqual({r["target_id"] for r in read_jsonl(self.out / "CHAINS.jsonl")},
                         {"EO:" + str(number) for number in range(1, 7)})
        self.assertNotIn("EO:999", json.dumps(index))
        self.assertFalse((self.out / "dossiers/EO_999.json").exists())
        self.assertTrue(any(row["actor_id"] == "EO:6" for row in read_jsonl(self.out / "MISSING_SOURCES.jsonl")))

    def test_new_source_automatically_plugs_in_and_exact_offsets_round_trip(self):
        self.run_build()
        self.assertEqual(len(read_jsonl(self.out / "TEXT_CLAUSES.jsonl")), 5)
        for row in read_jsonl(self.out / "CLAUSES.jsonl"):
            text = (self.repo / row["source"]["text_path"]).read_bytes().decode("utf-8")
            for clause in row["clauses"]:
                self.assertEqual(text[clause["char_start"]:clause["char_end"]], clause["text"])
        for row in read_jsonl(self.out / "ACTING_PROVISIONS.jsonl"):
            text = (self.repo / row["actor_source"]["text_path"]).read_bytes().decode("utf-8")
            self.assertEqual(text[row["char_start"]:row["char_end"]], row["provision_text"])
        families = json.loads((self.out / "FAMILIES.json").read_text(encoding="utf-8"))
        actor = next(f for f in families if f["family_id"] == "actor:EO:5")
        self.assertEqual(actor["instrument_ids"], ["EO:1", "EO:2"])

    def test_reruns_deterministic_semantic_outputs_with_incremental_cache(self):
        cache = self.repo / "cache"
        self.run_build(cache=cache)
        first = {p.relative_to(self.out).as_posix(): p.read_bytes() for p in self.out.rglob("*")
                 if p.is_file() and p.name not in {"METRICS.json", "SUMMARY.json"}}
        summary1 = json.loads((self.out / "SUMMARY.json").read_text(encoding="utf-8"))
        summary2 = self.run_build(cache=cache)
        second = {p.relative_to(self.out).as_posix(): p.read_bytes() for p in self.out.rglob("*")
                  if p.is_file() and p.name not in {"METRICS.json", "SUMMARY.json"}}
        self.assertEqual(first, second)
        metrics = json.loads((self.out / "METRICS.json").read_text(encoding="utf-8"))
        self.assertGreater(metrics.get("cache_hits", 0), 0)
        summary1["counts"].pop("cache_hits", None)
        summary2["counts"].pop("cache_hits", None)
        self.assertEqual(summary1, summary2)

    def test_corpus_build_never_mutates_status_sources_or_claim_data(self):
        protected = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.run_build(cache=self.repo / "cache")
        self.run_build(cache=self.repo / "cache")
        self.assertEqual({p: p.read_bytes() for p in protected}, protected)
        self.assertFalse((self.repo / "research/readiness/claims").exists())
        self.assertFalse((self.repo / "research/readiness/reviews").exists())

    def test_blank_sheets_never_assemble_and_each_failure_reported(self):
        self.run_build()
        blank = A.blank_sheet(self.dossier("EO:1"), "test")
        write_json(self.repo / "research/readiness/decisions/test-date/one.json", blank)
        summary = self.run_build()
        self.assertEqual(summary["counts"]["assembled_claims"], 0)
        self.assertEqual((self.out / "ASSEMBLED_CLAIMS.jsonl").read_bytes(), b"")
        report = json.loads((self.out / "ASSEMBLY_REPORT.json").read_text(encoding="utf-8"))
        self.assertEqual(len(report), 1)
        self.assertIn("approved_required", report[0]["errors"])

    def test_committed_decision_assembly_roundtrip_real_stage19(self):
        self.run_build()
        sheet = self.decision()
        claim, errors = A.assemble(sheet, self.dossier("EO:1"), self.repo)
        self.assertEqual(errors, [])
        write_json(self.repo / "research/readiness/decisions/test-date/one.json", sheet)
        summary = self.run_build()
        self.assertEqual(summary["counts"]["assembled_claims"], 1)
        self.assertEqual(read_jsonl(self.out / "ASSEMBLED_CLAIMS.jsonl"), [claim])
        self.assertEqual(A._gate(self.repo).validate_claim(claim, "no"), [])

    def test_cli_sheet_assemble_check_and_failed_batch(self):
        self.run_build()
        args = ["--repo", str(self.repo), "--output", str(self.out)]
        dest = self.repo / "decision.json"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(K.main(args + ["sheet", "EO:1", "--agent", "model-neutral", "--write", str(dest)]), 0)
            self.assertEqual(K.main(args + ["sheet", "EO:1", "--write", str(dest)]), 2)
            self.assertEqual(K.main(args + ["assemble", str(dest), "--write", str(self.repo / "failed.jsonl")]), 1)
        self.assertFalse((self.repo / "failed.jsonl").exists())
        self.assertTrue((self.repo / "failed.report.json").exists())
        write_json(dest, self.decision())
        claims = self.repo / "claims.jsonl"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(K.main(args + ["assemble", str(dest), "--write", str(claims)]), 0)
            self.assertEqual(K.main(args + ["check", str(claims)]), 0)
        self.assertEqual(len(read_jsonl(claims)), 1)

    def test_reservations_disjoint_and_respect_existing_claims(self):
        self.run_build()
        write_jsonl(self.repo / "research/readiness/claims/existing.jsonl", [{"instrument_id": "EO:1"}])
        first = K.pick(self.repo, self.out, "producer-a", 2)
        second = K.pick(self.repo, self.out, "producer-b", 20)
        first_ids = {r["instrument_id"] for r in first}
        second_ids = {r["instrument_id"] for r in second}
        self.assertTrue(first_ids.isdisjoint(second_ids))
        self.assertNotIn("EO:1", first_ids | second_ids)
        self.assertNotIn("EO:4", first_ids | second_ids)
        self.assertEqual(first_ids | second_ids, {"EO:2", "EO:3", "EO:5", "EO:6"})
        lock = json.loads((self.repo / "research/readiness/CLAIM_KIT_LOCK.json").read_text(encoding="utf-8"))
        self.assertEqual(set(lock["orders"]), first_ids | second_ids)

    def test_crlf_source_preserves_raw_hash_and_character_offsets(self):
        path = self.repo / "jobs/future-source/data/texts/EO_1.txt"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        provenance_path = self.repo / "jobs/future-source/data/PROVENANCE.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        record = next(r for r in provenance["representations"] if r["instrument_id"] == "EO:1")
        record["source"]["sha256"] = record["source"]["text_sha256"] = digest
        write_json(provenance_path, provenance)
        self.run_build()
        dossier = self.dossier("EO:1")
        original = dossier["evidence"][dossier["original_source_id"]]
        self.assertEqual(original["source"]["text_sha256"], digest)
        self.assertIn("\r\n", original["text"])
        self.assertEqual(original["text"], path.read_bytes().decode("utf-8"))
        for clause in dossier["clauses"]:
            self.assertEqual(original["text"][clause["char_start"]:clause["char_end"]], clause["text"])

    def test_malformed_committed_sheets_each_get_reported_without_crashing_build(self):
        self.run_build()
        decisions = self.repo / "research/readiness/decisions/test-date"
        write_json(decisions / "one.json", [])
        write_json(decisions / "two.json", None)
        write_json(decisions / "valid.json", self.decision())
        summary = self.run_build()
        report = json.loads((self.out / "ASSEMBLY_REPORT.json").read_text(encoding="utf-8"))
        self.assertEqual(len(report), 3)
        self.assertEqual(sum(bool(row["errors"]) for row in report), 2)
        self.assertEqual(summary["counts"]["assembled_claims"], 1)

    def test_cli_reports_all_malformed_sheets_and_no_partial_batch(self):
        self.run_build()
        sheets = self.repo / "decisions"
        write_json(sheets / "one.json", [])
        write_json(sheets / "two.json", None)
        write_json(sheets / "valid.json", self.decision())
        args = ["--repo", str(self.repo), "--output", str(self.out)]
        target = self.repo / "assembled.jsonl"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(K.main(args + ["assemble", str(sheets), "--write", str(target)]), 1)
        self.assertFalse(target.exists())
        report = json.loads(target.with_suffix(".report.json").read_text(encoding="utf-8"))
        self.assertEqual(len(report), 3)
        self.assertEqual(sum(bool(row["errors"]) for row in report), 2)

    def test_output_cannot_overwrite_protected_inputs_or_other_source_jobs(self):
        protected = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        for target in (self.repo, self.repo / "research", self.repo / "progress/test",
                       self.repo / "jobs/future-source/output", self.repo / "jobs/claim-kit/data"):
            with self.assertRaises(ValueError):
                self.run_build(output=target)
        self.assertEqual({p: p.read_bytes() for p in protected}, protected)

    def test_removed_provisional_status_cannot_reuse_stale_dossier(self):
        self.run_build()
        self.assertTrue((self.out / "dossiers/EO_1.json").exists())
        self.status.write_text(self.status.read_text(encoding="utf-8").replace("EO:1,no\n", ""), encoding="utf-8")
        self.run_build()
        with self.assertRaises(ValueError):
            K.load_dossier(self.out, "EO:1")


if __name__ == "__main__":
    unittest.main()


class PrintedReferenceTests(unittest.TestCase):
    """A later order that cites the target by number but changes nothing it can quote (an extension,
    a confirmation, a boundary modification) still becomes a known actor whose text enters the packet."""

    def setUp(self):
        BuildIntegrationTests.setUp(self)
        text = ("EXECUTIVE ORDER 7\nWhereas John T. Crowley was exempted from compulsory retirement for one year by "
                "Executive Order No. 4, dated January 1, 1990, he is hereby further exempted until May 31, 1993.\n")
        rel = "jobs/future-source/data/texts/EO_7.txt"
        path = self.repo / rel
        path.write_bytes(text.encode("utf-8"))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        prov = self.repo / "jobs/future-source/data/PROVENANCE.json"
        data = json.loads(prov.read_text(encoding="utf-8"))
        data["representations"].append({"instrument_id": "EO:7", "text_path": rel, "kind": "original_representation",
                                        "acceptable_as_original": True, "signing_date": "1992-01-01",
                                        "source": {"url": "https://example.gov/EO_7", "sha256": digest,
                                                   "text_sha256": digest, "page_or_item": "PDF page 1"}})
        write_json(prov, data)
        census = self.repo / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
        with census.open("a", encoding="utf-8", newline="") as fh:
            fh.write("EO:7,1\n")
        self.status.write_text(self.status.read_text(encoding="utf-8") + "EO:4,no\nEO:7,no\n", encoding="utf-8")

    run_build, dossier = BuildIntegrationTests.run_build, BuildIntegrationTests.dossier

    def test_citation_without_change_provision_is_a_known_actor(self):
        self.run_build()
        d = self.dossier("EO:4")
        self.assertIn(B.CITED_NO_PROVISION + ": EO:7", d["missing"])
        self.assertNotIn(B.TARGET_NOT_LOCATED + ": EO:7", d["missing"])
        self.assertEqual([a["actor_id"] for a in d["actor_contexts"]], ["EO:7"])
        self.assertIn("ACTOR_TEXT:EO:7", d["evidence"])
        self.assertIn("further exempted", d["evidence"]["ACTOR_TEXT:EO:7"]["text"])
        # No provision, no event: the chain stays empty and nothing is asserted.
        self.assertEqual(d["chain"]["events"], [])
        self.assertEqual(d["actor_provisions"], [])
        rows = read_jsonl(self.out / "MISSING_SOURCES.jsonl")
        row = next(r for r in rows if r["target_id"] == "EO:4" and r["actor_id"] == "EO:7")
        self.assertEqual(row["reason"], B.CITED_NO_PROVISION)
        self.assertEqual(row["source_event"]["kind"], B.PRINTED_REFERENCE_KIND)
        self.assertIn("Executive Order No. 4", row["source_event"]["context"])

    def test_name_match_lead_reason(self):
        self.assertEqual(B.unlocated_reason({"mechanism": "names_same_person"}), B.NAME_MATCH_LEAD)
        self.assertEqual(B.unlocated_reason({"proposal": {"mechanism": "names_same_person"}}), B.NAME_MATCH_LEAD)
        self.assertEqual(B.unlocated_reason({"kind": B.PRINTED_REFERENCE_KIND}), B.CITED_NO_PROVISION)
        self.assertEqual(B.unlocated_reason(None), B.TARGET_NOT_LOCATED)

    def test_printed_reference_outranks_a_name_match_for_the_same_pair(self):
        nm = self.repo / "jobs/namier/output"
        nm.mkdir(parents=True)
        with (nm / "EDGES.csv").open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["edge_id", "acting_id", "target_id", "mechanism", "qualifier"])
            writer.writeheader()
            writer.writerow({"edge_id": "NM-1", "acting_id": "EO:7", "target_id": "EO:4", "mechanism": "names_same_person",
                             "qualifier": "names John T. Crowley; cites this order by number; relation by date: later"})
            writer.writerow({"edge_id": "NM-2", "acting_id": "EO:7", "target_id": "EO:2", "mechanism": "names_same_person",
                             "qualifier": "names John T. Crowley; does not cite this order by number; relation by date: later"})
        self.run_build()
        d4 = self.dossier("EO:4")
        self.assertIn(B.CITED_NO_PROVISION + ": EO:7", d4["missing"])
        self.assertNotIn(B.NAME_MATCH_LEAD + ": EO:7", d4["missing"])
        row = next(r for r in read_jsonl(self.out / "MISSING_SOURCES.jsonl") if r["target_id"] == "EO:4" and r["actor_id"] == "EO:7")
        self.assertEqual(row["source_event"]["also_names_same_person"]["mechanism"], "names_same_person")
        d2 = self.dossier("EO:2")
        self.assertIn(B.NAME_MATCH_LEAD + ": EO:7", d2["missing"])
        self.assertIn("ACTOR_TEXT:EO:7", d2["evidence"])
