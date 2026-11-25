"""Photius P4 (D-20261106-photius-p4): a page-checked ProQuest replica becomes the order's held working text.

A replica that passed the Photius page check (grade archival_replica_checked, needs_page_check false, final pass)
is read from its Pinakes text file, hash-checked against the fragment's text_sha256, and selected ahead of an
unconfirmed transcription. The kit inventories its clauses, discloses the grade and keeps acceptable_as_original
false; the source keeps ProQuest's PDF hash. A failed or pending check, or a changed text file, earns no credit.
"""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import build as B
import status_overlay as SO
import working_text as W
import test_build as TB

PDF_SHA = {"EO:1": "1" * 64, "EO:4": "4" * 64}
MIRROR_TEXT = {"EO:1": "EXECUTIVE ORDER 1\nThe First Board shall perform the specified duties.\n",
               "EO:4": "EXECUTIVE ORDER 4\nThe Temporary Committee shall operate for a period of two years from January 1, 1990.\n"}
REPLICA_TEXT = {"EO:1": "Executive Order No. 1\nThe First Board shall perform the specified duties and report to the President.\n"
                        "The Secretary shall publish the rules.\n",
                "EO:4": "Executive Order No. 4\nThe Temporary Committee shall operate for a period of two years from January 1, 1990.\n"
                        "The Committee shall report its findings.\n"}


class CheckedReplicaWorkingTextTests(unittest.TestCase):
    setUp = TB.BuildIntegrationTests.setUp
    run_build = TB.BuildIntegrationTests.run_build
    dossier = TB.BuildIntegrationTests.dossier

    def registered_mirror(self, iid):
        """Make the fixture's text a registered mirror transcription, the text the kit selected before P4."""
        path = self.repo / "jobs/future-source/data/PROVENANCE.json"
        provenance = json.loads(path.read_text())
        entry = next(r for r in provenance["representations"] if r["instrument_id"] == iid)
        (self.repo / entry["text_path"]).write_bytes(MIRROR_TEXT[iid].encode())
        digest = hashlib.sha256(MIRROR_TEXT[iid].encode()).hexdigest()
        entry.update(acceptable_as_original=False, grade="mirror_transcription")
        entry["source"].update(sha256=digest, text_sha256=digest, grade="mirror_transcription",
                               acceptable_as_original=False)
        TB.write_json(path, provenance)
        fragments = self.repo / "jobs/future-source/output/FRAGMENTS.jsonl"
        TB.write_jsonl(fragments, TB.read_jsonl(fragments) + [
            {"instrument_id": iid, "kind": "original_representation", "produced_by": "future-source",
             "grade": "mirror_transcription", "acceptable_as_original": False,
             "data": {"sha256": digest, "text_sha256": digest, "text_path": entry["text_path"],
                      "grade": "mirror_transcription", "acceptable_as_original": False,
                      "needs_page_check": False}}])

    def replica(self, iid, final="pass", text_sha256=None):
        """A Pinakes text and its two declarations: Pinakes (pending codebook) and Photius (the page check)."""
        rel = "texts/" + iid.replace(":", "_") + ".txt"
        text = self.repo / "jobs/pinakes-proquest-ingest/output" / rel
        text.parent.mkdir(parents=True, exist_ok=True)
        text.write_bytes(REPLICA_TEXT[iid].encode())
        digest = hashlib.sha256(text.read_bytes()).hexdigest()
        url = "https://congressional.proquest.com/congressional/docview/" + iid.replace(":", "-")
        source = {"sha256": PDF_SHA[iid], "url": url, "page_or_item": "ProQuest replica " + iid}
        pinakes = {"instrument_id": iid, "kind": "original_representation", "produced_by": "pinakes-proquest-ingest",
                   "grade": "archival_replica_scan_pending_codebook", "acceptable_as_original": False,
                   "sources": [source],
                   "data": dict(source, grade="archival_replica_scan_pending_codebook", acceptable_as_original=False,
                                needs_page_check=True, location_confidence="medium", text_path=rel,
                                text_sha256=digest)}
        grade = W.REPLICA_GRADE if final == "pass" else "archival_replica_check_failed_or_pending"
        photius = {"instrument_id": iid, "kind": "original_representation", "produced_by": "photius-replica-check",
                   "grade": grade, "acceptable_as_original": False, "sources": [source],
                   "data": dict(source, grade=grade, acceptable_as_original=False, needs_page_check=final != "pass",
                                location_confidence="high", location_verified=True,
                                text_path="../../pinakes-proquest-ingest/output/" + rel,
                                text_sha256=text_sha256 or digest, check={"final": final})}
        for job, row in (("pinakes-proquest-ingest", pinakes), ("photius-replica-check", photius)):
            path = self.repo / "jobs" / job / "output/FRAGMENTS.jsonl"
            TB.write_jsonl(path, (TB.read_jsonl(path) if path.exists() else []) + [row])
        return "jobs/pinakes-proquest-ingest/output/" + rel, digest

    def overlay_input(self, iid):
        for path in sorted(self.out.glob("OVERLAY_INPUTS*.jsonl")):
            for row in TB.read_jsonl(path):
                if row["instrument_id"] == iid:
                    return row
        raise AssertionError("no overlay input for " + iid)

    def clauses(self, iid):
        for path in sorted(self.out.glob("CLAUSES*.jsonl")):
            for row in TB.read_jsonl(path):
                if row["instrument_id"] == iid:
                    return row
        return None

    def build(self, final="pass", text_sha256=None):
        for iid in ("EO:1", "EO:4"):
            self.registered_mirror(iid)
        held = {iid: self.replica(iid, final, text_sha256) for iid in ("EO:1", "EO:4")}
        summary = self.run_build()
        return held, summary

    def test_checked_replica_becomes_the_working_text_with_clause_inventory(self):
        held, _ = self.build()
        rel, digest = held["EO:1"]
        d = self.dossier("EO:1")
        original = d["evidence"][d["original_source_id"]]
        self.assertEqual(original["grade"], W.REPLICA_GRADE)
        self.assertIs(original["acceptable_as_original"], False)
        self.assertFalse(original["requires_page_check"])
        self.assertEqual(original["text"], REPLICA_TEXT["EO:1"])
        source = original["source"]
        self.assertEqual((source["text_path"], source["text_sha256"]), (rel, digest))
        # The bytes stay ProQuest's: the PDF hash and URL, with the held text file hashed beside them.
        self.assertEqual(source["sha256"], PDF_SHA["EO:1"])
        self.assertIn("proquest.com", source["url"])
        self.assertEqual((source["grade"], source["acceptable_as_original"]), (W.REPLICA_GRADE, False))
        self.assertTrue(d["clauses"])
        self.assertTrue(all(c["source"]["text_path"] == rel for c in d["clauses"]))
        self.assertTrue(any("Checked ProQuest replica credits the text step" in m for m in d["missing"]))
        self.assertEqual(SO.working_text_basis(d), "tracker_original_supported")
        # The undecided order's overlay input and clause inventory read the same replica.
        selected = self.overlay_input("EO:4")["selected"]
        self.assertEqual((selected["grade"], selected["text_path"]), (W.REPLICA_GRADE, held["EO:4"][0]))
        self.assertFalse(selected["requires_page_check"])
        self.assertIs(selected["acceptable_as_original"], False)
        record = self.clauses("EO:4")
        self.assertEqual(record["source"]["text_path"], held["EO:4"][0])
        self.assertTrue(record["clauses"])

    def test_failed_or_pending_replica_is_not_the_working_text(self):
        for final in ("fail", "unsure"):
            with self.subTest(final=final):
                self.setUp()
                held, _ = self.build(final=final)
                d = self.dossier("EO:1")
                original = d["evidence"][d["original_source_id"]]
                self.assertEqual(original["grade"], "mirror_transcription")
                self.assertNotEqual(original["source"]["text_path"], held["EO:1"][0])
                self.assertIsNone(SO.working_text_basis(d))
                self.assertNotEqual(self.overlay_input("EO:4")["selected"]["grade"], W.REPLICA_GRADE)

    def test_hash_mismatch_is_refused(self):
        held, summary = self.build(text_sha256="f" * 64)
        d = self.dossier("EO:1")
        original = d["evidence"][d["original_source_id"]]
        # The Photius declaration is skipped; the same file keeps only its Pinakes grade, which earns no credit.
        self.assertNotEqual(original["grade"], W.REPLICA_GRADE)
        self.assertEqual(original["grade"], "archival_replica_scan_pending_codebook")
        self.assertIsNone(SO.working_text_basis(d))
        self.assertNotEqual(self.overlay_input("EO:4")["selected"]["grade"], W.REPLICA_GRADE)
        self.assertTrue(any("photius-replica-check" in w and "text_sha256 mismatch" in w
                            for w in summary["warnings"]))

    def test_official_printing_of_the_same_order_still_wins(self):
        self.registered_mirror("EO:1")
        self.replica("EO:1")
        rel = "jobs/photius-gpo-volumes/output/texts/EO_1.txt"
        text = "EXECUTIVE ORDER No. 1\nThe First Board shall perform the specified duties.\nTHE WHITE HOUSE\n"
        (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / rel).write_bytes(text.encode())
        digest = hashlib.sha256(text.encode()).hexdigest()
        TB.write_jsonl(self.repo / "jobs/photius-gpo-volumes/output/FRAGMENTS.jsonl", [
            {"instrument_id": "EO:1", "kind": "original_representation", "produced_by": "photius-gpo-volumes",
             "grade": "official_printing", "acceptable_as_original": False,
             "sources": [{"sha256": "9" * 64, "url": "https://www.govinfo.gov/x.pdf", "page_or_item": "p. 1"}],
             "data": {"sha256": "9" * 64, "url": "https://www.govinfo.gov/x.pdf", "page_or_item": "p. 1",
                      "grade": "official_printing", "acceptable_as_original": False, "needs_page_check": False,
                      "location_confidence": "high", "text_path": "texts/EO_1.txt", "text_sha256": digest}}])
        self.run_build()
        d = self.dossier("EO:1")
        original = d["evidence"][d["original_source_id"]]
        self.assertEqual((original["grade"], original["source"]["text_path"]), ("official_printing", rel))


class ReplicaRankUnitTests(unittest.TestCase):
    REPLICA = {"instrument_id": "EO:1", "grade": W.REPLICA_GRADE, "acceptable_as_original": False,
               "text_path": "jobs/pinakes-proquest-ingest/output/texts/EO_1.txt", "requires_page_check": False}

    def test_checked_replica_outranks_unconfirmed_working_texts_and_leads(self):
        registered = {("EO:1", self.REPLICA["text_path"], W.REPLICA_GRADE)}
        self.assertEqual(B.text_tier(self.REPLICA, registered), 1)
        for grade in ("mirror_transcription", "compiled_transcription_lead", "machine_read_government_printed_copy",
                      "government_printed_copy", "held_text_lead"):
            other = {"instrument_id": "EO:1", "grade": grade, "acceptable_as_original": False,
                     "text_path": "jobs/aaa/texts/EO_1.txt"}
            reg = registered | {("EO:1", other["text_path"], grade)}
            self.assertLess(B.rank_text(self.REPLICA, reg), B.rank_text(other, reg), grade)

    def test_unregistered_or_page_check_owed_replica_gets_no_credit(self):
        self.assertEqual(B.text_tier(self.REPLICA, set()), 2)
        owed = dict(self.REPLICA, requires_page_check=True)
        registered = {("EO:1", owed["text_path"], W.REPLICA_GRADE)}
        self.assertEqual(B.credited_rank(owed, registered), 2)
        self.assertLess(B.rank_text(self.REPLICA, registered), B.rank_text(owed, registered))

    def test_official_printing_keeps_its_rank_without_a_replica(self):
        printing = {"instrument_id": "EO:2", "grade": "official_printing", "acceptable_as_original": False,
                    "text_path": "jobs/photius-gpo-volumes/output/texts/EO_2.txt"}
        registered = {("EO:1", self.REPLICA["text_path"], W.REPLICA_GRADE)}
        self.assertEqual(B.text_tier(printing, registered), 2)
        self.assertEqual(B.text_tier(dict(printing, instrument_id="EO:1"), registered), 1)


if __name__ == "__main__":
    unittest.main()
