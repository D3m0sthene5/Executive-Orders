"""Offline tests for Pacioli on a small fixture repository."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pacioli  # noqa: E402


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def le(target, actor, mech, date, edge, qual=""):
    return {"evidence_type": "ofr_note_on_target", "target_id": target, "acting_id": actor, "mechanism": mech,
            "date_candidate": date, "qualifier": qual, "edge_id": edge, "page_or_item": "OFR API record",
            "source_sha256": "a" * 64, "source_url": "https://www.federalregister.gov/api", "quote": f"{mech} by {actor}"}


def usc(target, actor, mech, date, eid, scope=""):
    return {"system": "usc", "subject_instrument_id": target, "acting_instrument_id": actor,
            "event_type_candidate": mech, "date_candidate": date, "scope_candidate": scope, "event_id": eid,
            "citation": "5 U.S.C. 1 note", "page_or_item": "note", "source_id": "usc:zip", "sentence": "revoked"}


class Pacioli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = self.root = Path(self.tmp.name)
        write_csv(r / pacioli.PATHS["tracker"], [
            {"instrument_id": "EO:9000", "provisional_status": "", "ready_for_human_review": "no",
             "text_evidence_tier": "missing", "provisional_text_grade": "", "provisional_text_sha256": ""},
            {"instrument_id": "EO:9100", "provisional_status": "no", "ready_for_human_review": "no",
             "text_evidence_tier": "missing", "provisional_text_grade": "", "provisional_text_sha256": ""},
            {"instrument_id": "EO:9500", "provisional_status": "", "ready_for_human_review": "no",
             "text_evidence_tier": "original_supported", "provisional_text_grade": "official", "provisional_text_sha256": ""},
            {"instrument_id": "EO:5214", "provisional_status": "", "ready_for_human_review": "no",
             "text_evidence_tier": "missing", "provisional_text_grade": "", "provisional_text_sha256": ""}])
        t = r / "jobs/fr-originals/output/texts/EO_9500.txt"
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_bytes(b"EXECUTIVE ORDER 9500 ... Executive Order No. 9000 is hereby revoked.")
        self.sha = hashlib.sha256(t.read_bytes()).hexdigest()
        write_csv(r / pacioli.PATHS["later"], [
            le("EO:9000", "EO:9500", "revocation", "1945-01-01", "LE-1"),
            le("EO:9100", "EO:9500", "revocation", "1945-01-01", "LE-2"),
            le("EO:5214", "PLO:945", "revocation", "1954-03-18", "LE-3"),
            le("EO:9000", "EO:9600", "amendment", "1946-01-01", "LE-4"),
            dict(le("EO:9100", "EO:9700", "revocation", "1950-01-01", "LE-5"), evidence_type="order_text_fr_originals")])
        write_jsonl(r / pacioli.PATHS["ofr1989"], [
            {"kind": "later_event_candidates", "instrument_id": "EO:9000", "data": [
                {"actor": "EO:9500", "mechanism": "revocation", "date_candidate": "1945-01-01", "qualifier": "",
                 "edge_ids": ["OC89-1"], "quote": "Revoked by EO 9500",
                 "source": {"page_or_item": "page 1021", "sha256": "b" * 64}}]}])
        write_csv(r / pacioli.PATHS["shepard"], [
            {"evidence_type": "shepard_blm_plo_table", "target_id": "EO:5214", "acting_id": "PLO:945",
             "mechanism": "revocation", "date_candidate": "1954-03-18", "qualifier": "", "edge_id": "SH-1",
             "page_or_item": "BLM table p. 3", "source_sha256": "c" * 64, "source_url": "https://www.blm.gov/x.pdf",
             "quote": "revoking EO No. 5214"}])
        write_csv(r / pacioli.PATHS["usc_events"], [
            usc("EO:9000", "EO:9500", "revocation", "1945-01-01", "u1"),
            usc("EO:9100", "EO:9500", "revocation", "1945-01-01", "u2", scope="partial_candidate"),
            usc("EO:9000", "EO:9600", "amendment", "1946-02-02", "u3")])
        write_jsonl(r / pacioli.PATHS["usc_sources"], [{"source_id": "usc:zip", "sha256": "d" * 64, "url": "https://x"}])
        write_csv(r / pacioli.PATHS["plo_located"], [{"actor": "PLO:945", "target_id": "EO:5214", "located": "True"}])
        cap = r / "jobs/selden-fr-acting/output/captures/x.pdf"
        cap.parent.mkdir(parents=True, exist_ok=True)
        cap.write_bytes(b"%PDF plo 945")
        write_jsonl(r / pacioli.PATHS["plo_sources"], [
            {"instrument_ids": ["PLO:945", "EO:5214"], "cache_path": "captures/x.pdf",
             "sha256": hashlib.sha256(b"%PDF plo 945").hexdigest(), "text_path": "texts/FR_19_1583.txt", "grade": "fr"}])
        self.s = pacioli.run(r, r / "out")
        self.agreed = {(x["target_id"], x["acting_id"]): x for x in map(json.loads, (r / "out/AGREED.jsonl").read_text().splitlines())}
        self.dis = {(x["target_id"], x["acting_id"]): x for x in map(json.loads, (r / "out/DISAGREED.jsonl").read_text().splitlines())}

    def tearDown(self):
        self.tmp.cleanup()

    def test_two_families_agree(self):
        a = self.agreed[("EO:9000", "EO:9500")]
        self.assertEqual((a["families"], a["relation_class"], a["scope"], a["agreed_date"]),
                         (["OFR", "OLRC"], "ending", "whole", "1945-01-01"))
        self.assertEqual(a["actor_text"]["sha256"], self.sha)
        self.assertEqual(len(a["entries"]), 3)  # two OFR tables (one family) + OLRC
        for e in a["entries"]:
            self.assertTrue(e["source_sha256"] and e["locator"] and e["record_id"])

    def test_one_family_is_not_two(self):
        # OFR notes and the 1989 table alone would not agree; only the OLRC entry makes EO:9000 a pair
        self.assertNotIn(("EO:9100", "EO:9700"), self.agreed)   # actor's own text is not a table
        self.assertNotIn(("EO:9100", "EO:9700"), self.dis)

    def test_blm_and_ofr_with_plo_text(self):
        a = self.agreed[("EO:5214", "PLO:945")]
        self.assertEqual(a["families"], ["BLM", "OFR"])
        self.assertTrue(a["actor_text"]["path"].endswith("captures/x.pdf"))

    def test_disagreements_listed_not_agreed(self):
        self.assertEqual(self.dis[("EO:9100", "EO:9500")]["disagreement"], ["whole_vs_part_differs"])
        self.assertEqual(self.dis[("EO:9000", "EO:9600")]["disagreement"], ["date_differs"])
        self.assertNotIn(("EO:9100", "EO:9500"), self.agreed)

    def test_summary(self):
        self.assertEqual(self.s["orders_with_agreed_whole_ending"]["undecided"], 2)
        self.assertEqual(self.s["orders_with_agreed_whole_ending_and_actor_text_held"]["orders"], 2)
        self.assertEqual(self.s["orders_on_disagreement_list"]["decided_not_ready"], 1)
        self.assertIn("never evidence", self.s["notice"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
