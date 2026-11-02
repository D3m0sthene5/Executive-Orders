import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import citation_checks


class CitationChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        app = self.repo / "jobs/app-executive-orders/output"
        (app / "texts").mkdir(parents=True)
        self.packet = self.repo / "research/run/n02/packet/supp/PACKET.json"
        self.packet.parent.mkdir(parents=True)
        self.packet.write_text("{}")
        self.original = "Own order text for Cast Iron Soil Pipe Industry."
        path = self.repo / "own.txt"
        path.write_text(self.original)
        self.dossier = {"instrument_id": "EO:6275", "original_source_id": "ORIGINAL:EO:6275", "evidence": {
            "ORIGINAL:EO:6275": {"source": {"text_path": "own.txt", "text_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                           "page_or_item": "10 FR 4057", "title": "Code of Fair Competition for the Cast Iron Soil Pipe Industry",
                           "url": "https://www.govinfo.gov/content/pkg/FR-1945-04-17/pdf/FR-1945-04-17.pdf"}}}}
        self.claim = {"instrument_id": "EO:6275", "research_rationale": ""}
        self.rows = []
        self.leads = []
        self.add_publisher("6513-I", "1933-12-18", "Code of Fair Competition for the Cast Iron Soil Pipe Industry (Amendment Number I)",
                           "An Amendment (Number I) to the Code of Fair Competition for the Cast Iron Soil Pipe Industry")
        self.add_publisher("6513", "1933-12-18", "Amendment of Executive Order No. 6433-A", "Special Industrial Recovery Board")
        self.write_inputs()

    def tearDown(self):
        self.tmp.cleanup()

    def add_publisher(self, number, date, title, text):
        name = f"executive-order-{number.lower()}-{title.lower().replace(' ', '-')[:20]}"
        rel = f"jobs/app-executive-orders/output/texts/{name}.txt"
        file = self.repo / rel
        file.write_text(text)
        self.rows.append({"instrument_id": f"EO:{number.replace('-', '')}", "date": date,
                          "title": f"Executive Order {number}—{title}", "path": f"/documents/{name}"})
        if number != "6513":
            self.leads.append({"file": rel, "raw_sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                               "match": "Code of Fair Competition for the Cast Iron Soil Pipe"})
        return file

    def write_inputs(self):
        index = self.repo / "jobs/app-executive-orders/output/INDEX.jsonl"
        index.write_text("".join(json.dumps(x) + "\n" for x in self.rows))
        (self.packet.parent / "LOOKUPS.details.json").write_text(json.dumps({"members": {
            "EO:6275": {"code_mentions": self.leads, "number_citations": []}}}))

    def check(self, claim=None):
        return citation_checks.check(claim or self.claim, self.dossier, self.repo, self.packet)

    def codes(self, claim=None):
        return {x["code"] for x in self.check(claim)["flags"]}

    def test_bound_suffixed_publisher_identity_from_reasoning(self):
        self.claim["research_rationale"] = ('A held later order, Executive Order 6513 of December 18, 1933, '
            'approves an Amendment (Number I) to this code.')
        self.assertIn("reasoning_order_identity_mismatch", self.codes())
        self.claim["research_rationale"] = self.claim["research_rationale"].replace("Order 6513 of", "Order 6513-I of")
        self.assertNotIn("reasoning_order_identity_mismatch", self.codes())

    def test_sibling_does_not_cause_suffix_inference(self):
        self.claim["research_rationale"] = ('Executive Order 6513 of December 18, 1933, amended '
                                            'Executive Order No. 6433-A for the Special Industrial Recovery Board.')
        self.assertNotIn("reasoning_order_identity_mismatch", self.codes())
        self.claim["research_rationale"] = 'Executive Order 6513 approved a later code amendment.'
        self.assertNotIn("reasoning_order_identity_mismatch", self.codes())

    def test_hash_failure_and_unrelated_subject_do_not_bind(self):
        self.claim["research_rationale"] = 'Executive Order 6513 of December 18, 1933, approved this Cast Iron Soil Pipe code amendment.'
        self.leads[0]["raw_sha256"] = "0" * 64
        self.write_inputs()
        self.assertNotIn("reasoning_order_identity_mismatch", self.codes())
        self.leads[0]["raw_sha256"] = hashlib.sha256((self.repo / self.leads[0]["file"]).read_bytes()).hexdigest()
        self.claim["research_rationale"] = 'Executive Order 6513 of December 18, 1933, discussed the Treasury building.'
        self.write_inputs()
        self.assertNotIn("reasoning_order_identity_mismatch", self.codes())

    def test_publisher_path_must_be_exact_documents_slug(self):
        self.claim["research_rationale"] = 'Executive Order 6513 of December 18, 1933, amended this Cast Iron Soil Pipe code.'
        collision = dict(self.rows[0])
        collision["instrument_id"] = "EO:6513Z"
        collision["path"] = collision["path"].replace("/documents/", "/another-catalog/")
        self.rows.append(collision)
        self.write_inputs()
        self.assertEqual(1, len(self.check()["flags"]))
        self.assertIn("EO 6513I", self.check()["flags"][0]["detail"])

    def test_optional_packet_path_reports_identity_coverage(self):
        self.claim["research_rationale"] = 'Executive Order 6513 of December 18, 1933, amended this Cast Iron Soil Pipe code.'
        result = citation_checks.check(self.claim, self.dossier, self.repo, packet_path=None)
        self.assertEqual([], result["flags"])
        self.assertIn("packet_path_unavailable", {g.get("reason") for g in result["coverage_gaps"]})

    def test_unbound_publisher_metadata_reports_coverage(self):
        self.claim["research_rationale"] = 'Executive Order 6513 of December 18, 1933, amended this Cast Iron Soil Pipe code.'
        self.rows[0]["path"] = "/unsupported/" + Path(self.rows[0]["path"]).name
        self.write_inputs()
        result = self.check()
        self.assertEqual([], result["flags"])
        self.assertIn("publisher_record_not_bound_or_text_unverified", {g.get("reason") for g in result["coverage_gaps"]})

    def test_publisher_index_git_blob_integrity_and_content_cache(self):
        self.claim["research_rationale"] = 'Executive Order 6513 of December 18, 1933, amended this Cast Iron Soil Pipe code.'
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        index = self.repo / "jobs/app-executive-orders/output/INDEX.jsonl"
        subprocess.run(["git", "-C", str(self.repo), "add", str(index)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "-qm", "pin publisher index"], check=True)
        cache = {}
        self.assertIn("reasoning_order_identity_mismatch", {f["code"] for f in citation_checks.check(
            self.claim, self.dossier, self.repo, self.packet, cache)["flags"]})
        before = index.stat()
        index.write_bytes(index.read_bytes().replace(b"EO:6513I", b"EO:6513Z"))
        os.utime(index, ns=(before.st_atime_ns, before.st_mtime_ns))
        result = citation_checks.check(self.claim, self.dossier, self.repo, self.packet, cache)
        self.assertEqual([], result["flags"])
        self.assertIn("publisher_index_git_blob_mismatch", {g.get("reason") for g in result["coverage_gaps"]})

    def test_original_fr_page_and_issue_in_reasoning(self):
        self.claim["research_rationale"] = ('Identity: the registered Federal Register original (10 F.R. 4058, '
                                            'issue of 1945-04-27), signed 1945-04-13 and filed 1945-04-14.')
        self.assertEqual({"fr_citation_mismatch", "fr_issue_date_mismatch"}, self.codes())
        self.claim["research_rationale"] = self.claim["research_rationale"].replace("4058", "4057").replace("1945-04-27", "1945-04-17")
        self.assertEqual(set(), self.codes())

    def test_member_page_same_printing_and_other_role_are_separate(self):
        self.claim["research_rationale"] = ('Member checks: ' + json.dumps({"scope_check":
            'Both orders are printed on the same Federal Register page (10 FR 4333).'}))
        self.assertIn("fr_citation_mismatch", self.codes())
        self.claim["research_rationale"] = ('EO 9733 (11 FR 6127) superseded the original. '
                                            'The source was signed 1946-06-04, filed June 4, and published June 6.')
        self.assertNotIn("fr_citation_mismatch", self.codes())


if __name__ == "__main__":
    unittest.main()
