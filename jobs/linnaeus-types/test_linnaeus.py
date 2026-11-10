"""Offline tests for Linnaeus on a small fixture repository."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "x1-class-engine"))
import linnaeus  # noqa: E402
import taxonomy  # noqa: E402


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


class Linnaeus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = self.root = Path(self.tmp.name)
        ids = ["EO:1500", "EO:1501", "EO:1502", "EO:1503", "EO:8000", "EO:8001", "EO:9000"]
        write_csv(r / linnaeus.PATHS["tracker"],
                  [{"instrument_id": i, "provisional_status": ""} for i in ids] +
                  [{"instrument_id": "EO:9001", "provisional_status": "no"}])
        empty = {"lead_actor_ids": [], "own_terms": [], "current_law_leads": []}
        sl = [dict(empty, instrument_id=i) for i in ids if i != "EO:9000"]
        sl.append(dict(empty, instrument_id="EO:9000", lead_actor_ids=["EO:9500"]))  # has a lead: not in the set
        write_jsonl(r / linnaeus.PATHS["status_leads"], sl)
        write_csv(r / linnaeus.PATHS["types"], [
            {"instrument_id": "EO:1500", "type": "cs_waiver_individual", "class": "spent", "confidence": "high",
             "year": "1912", "wpa_summary": "J. Doe made eligible for appointment without examination."},
            {"instrument_id": "EO:1501", "type": "national_forest_boundary", "class": "land", "confidence": "high",
             "year": "1912", "wpa_summary": "Lands excluded from the Coconino National Forest."},
            {"instrument_id": "EO:1502", "type": "unknown", "class": "unknown", "confidence": "none", "year": "1912",
             "wpa_summary": ""},
            {"instrument_id": "EO:1503", "type": "land_withdrawal_general", "class": "land", "confidence": "high",
             "year": "1912", "wpa_summary": "Lands withdrawn for classification."}])
        write_jsonl(r / linnaeus.PATHS["pothier"], [
            {"instrument_id": "EO:1501", "doctrine_id": "PD-NATIONAL-FOREST", "status_lead": "no", "basis_kind": "TERM",
             "lead_kind": "spent_on_issue"},
            {"instrument_id": "EO:1502", "doctrine_id": "PD-ADMIN", "status_lead": "open", "basis_kind": "NONE",
             "lead_kind": ""}])
        write_csv(r / linnaeus.PATHS["app"], [
            {"instrument_id": "EO:8000", "date": "1938-05-09",
             "title": "Executive Order 8000—Authorizing the Appointment of Jane Roe to a Clerical Position"},
            {"instrument_id": "EO:8001", "date": "1938-05-10",
             "title": "Executive Order 8001—Amending Executive Order No. 7000"}])
        write_csv(r / linnaeus.PATHS["census"],
                  [{"id": i, "date_effective": "1912" if i < "EO:2" else "1938"} for i in ids])
        write_csv(r / linnaeus.PATHS["m1118"], [{"instrument_id": "EO:1500", "waits_on": "microfilm_pending (film)"},
                                                 {"instrument_id": "EO:1501", "waits_on": "replica_check_failed_or_unread"}])
        edge = {"target_id": "EO:1503", "mechanism": "revocation", "evidence_type": "shepard_blm_plo_table"}
        write_csv(r / linnaeus.PATHS["shepard"], [edge, dict(edge, target_id="EO:1502", mechanism="cross_reference")])
        write_csv(r / linnaeus.PATHS["later"], [dict(edge, target_id="EO:0")])
        write_csv(r / linnaeus.PATHS["frciters"], [{"target_id": "EO:8000", "acting_on_target": "True",
                                                   "mechanism_class": "modifying"}])
        write_csv(r / linnaeus.PATHS["ofr1989"], [{"census_id": "EO:8001", "group": "effect_merged_into_other_document"}])
        self.rows, self.summary = linnaeus.run(r, r / "out", taxonomy)
        self.by = {x["instrument_id"]: x for x in self.rows}

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_lead_set(self):
        self.assertEqual(sorted(self.by), ["EO:1500", "EO:1501", "EO:1502", "EO:1503", "EO:8000", "EO:8001"])
        self.assertEqual(self.summary["undecided"], 7)

    def test_types_and_precedence(self):
        self.assertEqual(self.by["EO:1500"]["family"], "CS_ONE_PERSON")
        self.assertEqual(self.by["EO:1502"]["family"], "ORGANIZATION")          # Pothier doctrine fallback
        self.assertEqual(self.by["EO:1502"]["type_source"], "pothier_doctrine")
        self.assertEqual(self.by["EO:8000"]["family"], "CS_ONE_PERSON")         # title pattern after 1937
        self.assertEqual(self.by["EO:8001"]["form"], "amends_other_order")
        self.assertEqual(self.by["EO:1500"]["m1118_gap"], "yes")

    def test_strata(self):
        self.assertEqual(self.by["EO:1501"]["stratum"], "pothier_decided_lead")
        self.assertEqual(self.by["EO:1503"]["stratum"], "held_ending_lead_unrouted")
        self.assertEqual(self.by["EO:1502"]["stratum"], "unsourced")            # a cross-reference is no ending lead
        self.assertEqual(self.by["EO:8001"]["stratum"], "unsourced")            # a merged 1989 row is no ending
        self.assertIn("ofr_1989_table", self.by["EO:8001"]["held_mentions_without_ending"])
        self.assertEqual(self.by["EO:1501"]["m1118_gap"], "")                    # replica gap, not film
        self.assertEqual(self.by["EO:1501"]["residual_replica_gap"], "yes")
        self.assertTrue(linnaeus.ending("supersession") and linnaeus.ending("replacement"))

    def test_cruden_targets_exclude_ulpian_and_leads(self):
        with open(self.root / "out/CRUDEN_TARGETS.csv", encoding="utf-8") as fh:
            t = [r["instrument_id"] for r in csv.DictReader(fh)]
        self.assertEqual(t, ["EO:1502", "EO:8001"])
        self.assertEqual(self.summary["cs_one_person_left_to_ulpian"], 2)

    def test_outputs_written(self):
        for f in ("NO_LEAD_TYPES.csv", "SUMMARY.json", "TYPE_TABLE.md", "CRUDEN_TARGETS.csv"):
            self.assertTrue((self.root / "out" / f).is_file(), f)
        self.assertIn("never evidence", (self.root / "out/TYPE_TABLE.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
