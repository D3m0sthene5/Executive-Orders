"""Regression tests for rejected real requests and unsafe historical carries."""
import contextlib
import copy
import csv
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_lib"))
import fetch_ladder as fl
import job
import ladder_queue
import request_contract as rc
from prior_output import PriorOutput
from test_fetch_ladder import Base, FakeTransport


class RequestContractTests(unittest.TestCase):
    def test_real_seventeen_rows_are_reconciled_without_guessed_endings(self):
        fixtures = [json.loads(x) for x in (HERE / "fixtures/legacy_requests.jsonl").read_text().splitlines()]
        audits = [rc.normalize_request(x["request"], line_number=x["line_number"]) for x in fixtures]
        self.assertEqual(len(audits), 17)
        self.assertEqual(sum(a["status"] == "corrected" for a in audits), 15)
        self.assertEqual([a["line_number"] for a in audits if a["status"] == "unresolved"], [515, 523])
        for a, f in zip(audits, fixtures):
            self.assertEqual(a["original_request"], f["request"])
            self.assertTrue(a["corrections"])

    def test_compound_request_names_distinct_original_and_actor(self):
        raw = {"instrument_id": "EO:9132A", "citation": "EO 9132-A and EO 9427-A",
               "step": "original_and_ending_basis"}
        a = rc.normalize_request(raw)
        self.assertEqual([(t["step"], t["citation"]) for t in a["tasks"]],
                         [("original_text", "EO 9132A"), ("ending_or_current_basis", "EO 9427A")])
        self.assertNotEqual(a["tasks"][0]["task_id"], a["tasks"][1]["task_id"])

    def test_unidentified_ending_does_not_duplicate_original_fetch(self):
        raw = {"instrument_id": "EO:8586", "citation": "5 FR 4444", "urls": ["https://example.gov/original.pdf"],
               "step": "original_and_ending_basis"}
        a = rc.normalize_request(raw)
        self.assertEqual(a["status"], "unresolved")
        self.assertEqual(a["tasks"][1]["urls"], [])
        self.assertEqual(a["tasks"][1]["citation"], "")

    def test_note_recovery_requires_the_same_exact_order(self):
        raw = {"instrument_id": "EO:7899", "note": "Original text of EO 7899 (May 26, 1938)",
               "step": "ending_or_current_basis"}
        a = rc.normalize_request(raw)
        self.assertEqual(a["tasks"][0]["citation"], "EO 7899")
        self.assertEqual(a["tasks"][0]["step"], "ending_or_current_basis")
        raw["note"] = "Possibly a later order or a library collection"
        self.assertEqual(rc.normalize_request(raw)["status"], "invalid")
        raw["note"] = "Original text of EO 7900"
        self.assertEqual(rc.normalize_request(raw)["status"], "invalid")

    def test_alias_does_not_promote_page_review(self):
        raw = {"instrument_id": "EO:9636", "citation": "10 FR 12543", "step": "original_page_check"}
        a = rc.normalize_request(raw)
        self.assertEqual(raw["step"], "original_page_check")
        self.assertEqual(a["tasks"][0]["step"], "original_text")
        self.assertIn("remains required", a["tasks"][0]["extra"]["review_requirement"])

    def test_stable_id_survives_queue_reordering(self):
        raw = {"instrument_id": "EO:1", "citation": "66 Stat. 259", "step": "current_basis"}
        a = rc.normalize_request(raw, line_number=2)
        b = rc.normalize_request(raw, line_number=500)
        self.assertEqual(a["request_id"], b["request_id"])
        self.assertEqual(a["tasks"][0]["task_id"], b["tasks"][0]["task_id"])

    def test_invalid_json_shape_types_urls_and_dates_are_visible(self):
        for raw in ([], {"instrument_id": "EO:1", "citation": 45},
                    {"instrument_id": "EO:1", "urls": ["file:///etc/passwd"]},
                    {"instrument_id": "EO:1", "urls": ["https://["]},
                    {"instrument_id": "EO:1", "citation": "EO 1", "as_of": "yesterday"},
                    {"instrument_id": "EO:1", "citation": "EO 1", "as_of": "1999", "required_date": "2000"}):
            a = rc.normalize_request(raw)
            self.assertEqual(a["status"], "invalid", raw)
            self.assertTrue(a["errors"])
            self.assertEqual(a["original_request"], raw)

    def test_enqueue_validates_entire_batch_before_appending_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "queue.jsonl"
            first = {"instrument_id": "EO:1", "citation": "EO 1"}
            rc.enqueue_requests(path, [first])
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                rc.enqueue_requests(path, [{"instrument_id": "EO:2", "citation": "EO 2"}, {}])
            self.assertEqual(path.read_bytes(), before)
            rc.enqueue_requests(path, [first])
            self.assertEqual(path.read_bytes(), before)

    def test_dates_and_originals_survive_embedded_citation_split(self):
        raw = {"instrument_id": "EO:1", "citation": "Please find 5 CFR 6 and 3 U.S.C. 110",
               "as_of": "1999-01-01", "edition_year": 1999}
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "q.jsonl"
            path.write_text(json.dumps(raw) + "\n")
            wanted, problems = ladder_queue.read_fetch_queue(path)
        self.assertEqual(problems, [])
        self.assertEqual(len(wanted), 2)
        for w in wanted:
            self.assertEqual(w.extra["as_of"], "1999-01-01")
            self.assertEqual(w.extra["edition_year"], 1999)
            self.assertEqual(w.extra["original_request"], raw)


class ExecutionTests(Base):
    def test_invalid_in_memory_request_never_reaches_transport(self):
        tr = FakeTransport({})
        w = fl.Wanted("x", ["EO:1"], urls=["https://example.gov/a.pdf"], step="bogus")
        res = fl.Ladder(self.fetcher(tr), log=lambda *a: None).walk(w)
        self.assertEqual(res["outcome"], "invalid_request")
        self.assertEqual(tr.calls, [])
        self.assertIsNone(res["exhausted"])

    def test_two_tasks_share_one_source_download(self):
        url = "https://example.gov/document.html"
        body = b"<html><body>" + b"The official document contains substantive provisions. " * 100 + b"</body></html>"
        tr = FakeTransport({url: [(200, {"content-type": "text/html"}, body)]})
        ladder = fl.Ladder(self.fetcher(tr), log=lambda *a: None, tiers=("given",))
        for step in ("original_text", "ending_or_current_basis"):
            r = ladder.walk(fl.Wanted("task:" + step, ["EO:1"], urls=[url], step=step))
            self.assertEqual(r["outcome"], "found")
        self.assertEqual(tr.calls.count(url), 1)

    def test_wrong_public_law_is_not_found_or_exhausted(self):
        url = "https://www.govinfo.gov/content/pkg/PLAW-119publ1/html/PLAW-119publ1.htm"
        body = b"<html><body>PUBLIC LAW 119-1. " + b"Substantive law text. " * 200 + b"</body></html>"
        tr = FakeTransport({url: [(200, {"content-type": "text/html"}, body)]})
        w = fl.Wanted("wrong-law", ["EO:1"], urls=[url], citation="Pub. L. 118-1")
        r = fl.Ladder(self.fetcher(tr), log=lambda *a: None, tiers=("given",)).walk(w)
        self.assertEqual(r["outcome"], "retry_later")
        self.assertIsNone(r["source"])
        self.assertIn("identity_mismatch", r["attempts"][0]["reject_reason"])

    def test_expected_hash_mismatch_is_neither_found_nor_exhaustion(self):
        url = "https://example.gov/document.html"
        body = b"<html><body>" + b"Substantive source text. " * 200 + b"</body></html>"
        tr = FakeTransport({url: [(200, {"content-type": "text/html"}, body)]})
        w = fl.Wanted("wrong-bytes", ["EO:1"], urls=[url], extra={"expected_sha256": "0" * 64})
        r = fl.Ladder(self.fetcher(tr), log=lambda *a: None, tiers=("given",)).walk(w)
        self.assertEqual(r["outcome"], "retry_later")
        self.assertIsNone(r["source"])
        self.assertIn("source_hash_mismatch", r["attempts"][0]["reject_reason"])


class RevalidationTests(unittest.TestCase):
    def wanted(self, citation="66 Stat. 259", **extra):
        return fl.Wanted("w", ["EO:1"], citation=citation, extra=extra)

    def test_carried_metadata_is_not_document_text(self):
        src = {"url": "https://www.govinfo.gov/metadata/pkg/STATUTE-66/PREMIS.xml"}
        self.assertIn("metadata_not_document", fl.carried_defect(self.wanted(), src, b"<premis>metadata</premis>"))

    def test_wrong_statute_volume_and_code_section_are_rejected(self):
        self.assertIn("identity_mismatch", fl.carried_defect(self.wanted(),
            {"url": "https://www.govinfo.gov/content/pkg/STATUTE-65/pdf/STATUTE-65-Pg259.pdf"}, b"body"))
        self.assertIn("identity_mismatch", fl.carried_defect(self.wanted("3 U.S.C. 110"),
            {"url": "https://www.govinfo.gov/content/pkg/USCODE-2024-title3/pdf/USCODE-2024-title3-chap2-sec111.pdf"}, b"body"))

    def test_specific_day_and_explicit_edition_are_checked(self):
        w = self.wanted("5 CFR 6", as_of="1999-01-01")
        self.assertIn("edition_date_mismatch", fl.edition_conflict(w, "https://www.ecfr.gov/on/1999-12-31/title-5/part-6"))
        self.assertEqual(fl.edition_conflict(w, "https://www.ecfr.gov/on/1999-01-01/title-5/part-6"), "")
        w = self.wanted("5 CFR 6", edition_year=1999)
        self.assertIn("edition_date_mismatch", fl.edition_conflict(w, "https://www.govinfo.gov/content/pkg/CFR-1998-title5/pdf/x.pdf"))

    def test_report_records_have_no_exemption_for_missing_text(self):
        src = {"url": "https://example.gov/report.pdf", "report_date_request": {"kind": "peb"}}
        self.assertIn("rd_no_meaningful_text", fl.carried_defect(self.wanted("report"), src, None))

    def test_a_nearby_unrelated_report_does_not_validate_a_commission_amendment(self):
        spec = {"kind": "commission", "body_words": ["commission", "privatization"]}
        body = "Commission on Privatization. Executive Order amending the due date. " + "irrelevant text " * 100
        body += "The President transmits a report about the Belgium tax convention."
        src = {"url": "https://example.gov/public-papers.pdf", "report_date_request": spec}
        self.assertIn("report_not_local_to_named_body", fl.carried_defect(self.wanted("report"), src, body))

    def test_reporters_word_is_not_a_report(self):
        spec = {"kind": "commission", "body_words": ["chemical", "warfare", "review", "commission"]}
        body = "The spokesman read a statement to reporters. Appointment of the Chemical Warfare Review Commission. " * 4
        src = {"url": "https://example.gov/public-papers.pdf", "report_date_request": spec}
        self.assertIn("rd_not_the_report_record", fl.carried_defect(self.wanted("report"), src, body))

    def test_custody_and_substantive_text_have_distinct_tiers(self):
        self.assertEqual(fl.evidence_tier({"url": "https://example.gov/scan.pdf"}, None), "custody_only")
        self.assertEqual(fl.evidence_tier({"url": "https://example.gov/scan.pdf"}, "text " * 100), "document_text")
        self.assertEqual(fl.evidence_tier({"url": "https://www.archives.gov/research/guide-fed-records/groups/013.html"}, "text " * 100), "finding_aid")

    def test_changed_request_and_text_hash_require_revalidation(self):
        src = {"url": "https://example.gov/source.pdf", "request_sha256": "old"}
        self.assertIn("request_changed", fl.carried_defect(self.wanted(request_sha256="new"), src, "body " * 50))
        src = {"url": "https://example.gov/source.pdf", "extracted_text_sha256": fl.sha256_bytes(b"original")}
        self.assertIn("text_hash_mismatch", fl.carried_defect(self.wanted(), src, "changed"))

    def test_quarantine_preserves_bytes_and_is_resumable(self):
        source = {"wanted_id": "w", "url": "https://example.gov/source.pdf", "sha256": "abc"}
        old = {"w": (source, b"historical bytes\r\n")}
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            rows = job.preserve_rejected(None, old, {"w": "identity_mismatch"}, out)
            self.assertEqual((out / rows[0]["preserved_text_path"]).read_bytes(), old["w"][1])
            self.assertEqual(rows[0]["source_record"], source)
            (out / "REJECTED_PRIOR_SOURCES.jsonl").write_text(json.dumps(rows[0]) + "\n")
            next_out = out / "next"
            next_out.mkdir()
            again = job.preserve_rejected(PriorOutput.from_folder(out), old, {"w": "identity_mismatch"}, next_out)
            self.assertEqual(len(again), 1)
            self.assertEqual((next_out / again[0]["preserved_text_path"]).read_bytes(), old["w"][1])

    def test_missing_receipt_hash_is_not_a_valid_carry(self):
        src = {"wanted_id": "w", "url": "https://example.gov/source.pdf", "instrument_ids": ["EO:1"]}
        valid, stale, audit = job.revalidate_previous({"w": (src, b"substantive text " * 50)}, {})
        self.assertEqual(valid, {})
        self.assertIn("invalid_receipt", stale["w"])
        self.assertEqual(audit[0]["status"], "rejected")

    def test_failure_history_survives_successive_bounded_runs(self):
        earlier = {"wanted_id": "outside-next-plan", "result": "retry_later", "why": "timeout"}
        latest = {"wanted_id": "current-plan", "result": "retry_later", "why": "offline"}
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "PREVIOUS_UNRESOLVED.jsonl"
            path.write_text(json.dumps(earlier) + "\n")
            prior = PriorOutput.from_folder(td)
            merged = job.prior_history(prior, path.name, [latest])
            self.assertEqual(merged, [earlier, latest])
            path.write_text("".join(json.dumps(row) + "\n" for row in merged))
            self.assertEqual(job.prior_history(prior, path.name, [latest]), merged)

    def test_offline_bounded_execution_never_republishes_invalid_found_source(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            queue = repo / "research/readiness/FETCH_QUEUE.jsonl"
            queue.parent.mkdir(parents=True)
            raw = {"instrument_id": "EO:1", "citation": "66 Stat. 259", "urls": ["https://example.gov/source.pdf"]}
            queue.write_text(json.dumps(raw) + "\n")
            wanted, _ = ladder_queue.read_fetch_queue(queue)
            wid = wanted[0].wanted_id
            prior = Path(td) / "prior"
            prior.mkdir()
            source = {"wanted_id": wid, "url": "https://www.govinfo.gov/metadata/pkg/STATUTE-66/PREMIS.xml",
                      "sha256": "a" * 64, "page_or_item": "metadata", "route": "given/given",
                      "instrument_ids": ["EO:1"], "citation": "66 Stat. 259", "text_path": "metadata.txt"}
            (prior / "metadata.txt").write_bytes(b"<premis>immutable historical receipt</premis>")
            (prior / "SOURCES.jsonl").write_text(json.dumps(source) + "\n")
            with (prior / "RESULTS.csv").open("w", newline="") as fh:
                wr = csv.DictWriter(fh, fieldnames=job.RESULT_COLUMNS)
                wr.writeheader()
                wr.writerow({"wanted_id": wid, "result": "found"})
            out = Path(td) / "out"
            env = {"OUTPUT_DIR": str(out), "REPO_ROOT": str(repo), "JOB_NAME": "source-ladder",
                   "JOB_PRIOR_OUTPUT_DIR": str(prior), "JOB_OFFLINE": "1", "JOB_LIMIT": "1",
                   "JOB_MAX_REQUESTS": "1", "JOB_READINESS_PLAN": "0", "JOB_CARRY_FORWARD": "1", "JOB_ONLY": ""}
            with patch.dict(os.environ, env), patch.object(job, "run_tests"), contextlib.redirect_stdout(io.StringIO()):
                job.main()
            self.assertEqual((out / "SOURCES.jsonl").read_text(), "")
            q = [json.loads(x) for x in (out / "REJECTED_PRIOR_SOURCES.jsonl").read_text().splitlines()]
            self.assertEqual(len(q), 1)
            self.assertEqual(q[0]["sha256"], source["sha256"])
            s = json.loads((out / "SUMMARY.json").read_text())
            self.assertEqual(s["found"], 0)
            self.assertEqual(s["earlier_found_carried_with_defect"], 0)
            self.assertEqual(s["http_requests"], 0)
            # The original defect also affected receipts OUTSIDE the bounded
            # plan. A zero-match selection must preserve but never count them.
            unselected = out / "unselected"
            env.update(OUTPUT_DIR=str(unselected), JOB_ONLY="queue:NO-MATCH")
            with patch.dict(os.environ, env), patch.object(job, "run_tests"), contextlib.redirect_stdout(io.StringIO()):
                job.main()
            self.assertEqual((unselected / "SOURCES.jsonl").read_text(), "")
            rows = list(csv.DictReader((unselected / "RESULTS.csv").read_text().splitlines()))
            self.assertEqual(rows[0]["result"], "needs_revalidation")
            self.assertEqual(json.loads((unselected / "SUMMARY.json").read_text())["found"], 0)


if __name__ == "__main__":
    unittest.main()
