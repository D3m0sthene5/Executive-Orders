"""Authorized growth is separate from historical fixtures and output freshness."""
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

import population as P


def csv_bytes(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


class PopulationInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.base = [{"instrument_id": "EO:1", "provisional_substantive_status": "yes",
                      "human_certified_by_this_release": "no", "decision_origin": "historic"}]
        self.extra = [{"instrument_id": "EO:2", "provisional_substantive_status": "no",
                       "human_certified_by_this_release": "no", "decision_origin": "owner-adopted reviewed row"}]
        self.base_bytes = csv_bytes(self.base)
        self.write("census.csv", csv_bytes([{"id": "EO:1"}, {"id": "EO:2"}, {"id": "EO:3"}]))
        self.write("statuses.csv", self.base_bytes)
        self.write("adopted.csv", csv_bytes(self.extra))
        self.write("review.json", b'{"verdict":"upheld","authority":"synthetic fixture only"}\n')
        self.contract = {
            "schema": "eo-accepted-population-contract/v1",
            "census": {"path": "census.csv", "count": 3,
                       "identity_sha256": P.canonical_sha(["EO:1", "EO:2", "EO:3"])},
            "historical_status_baseline": {"path": "statuses.csv", "bytes": len(self.base_bytes),
                                           "count": 1, "sha256": P.sha(self.base_bytes),
                                           "rows_sha256": P.canonical_sha(self.base)},
            "accepted_additions": [],
        }

    def write(self, name, data):
        (self.repo / name).write_bytes(data)

    def accept_extra(self):
        self.contract["accepted_additions"].append({
            "name": "synthetic authorized delta", "accepted_in_main": "fixture-acceptance",
            "count": 1, "rows": {"path": "adopted.csv", "sha256": P.sha(csv_bytes(self.extra))},
            "authorization_pins": [{"path": "review.json", "sha256": P.sha((self.repo / "review.json").read_bytes())}],
        })
        self.write("statuses.csv", csv_bytes(self.base + self.extra))

    def test_frozen_fixture_and_explicitly_authorized_addition(self):
        self.assertEqual(P.validate_inputs(self.repo, self.contract)["decided"], 1)
        self.accept_extra()
        result = P.validate_inputs(self.repo, self.contract)
        self.assertEqual(result["historical_decided"], 1)
        self.assertEqual(result["authorized_additions"], 1)
        self.assertEqual(result["statuses"], {"EO:1": "yes", "EO:2": "no"})

    def test_arbitrary_csv_append_cannot_authorize_itself(self):
        self.write("statuses.csv", csv_bytes(self.base + self.extra))
        with self.assertRaisesRegex(ValueError, "independently pinned"):
            P.validate_inputs(self.repo, self.contract)

    def test_duplicate_same_status_is_rejected(self):
        self.accept_extra()
        self.write("statuses.csv", csv_bytes(self.base + self.extra + self.extra))
        with self.assertRaisesRegex(ValueError, "duplicate identity"):
            P.validate_inputs(self.repo, self.contract)

    def test_current_or_adoption_row_mutation_is_rejected(self):
        self.accept_extra()
        wrong = copy.deepcopy(self.extra)
        wrong[0]["provisional_substantive_status"] = "yes"
        self.write("statuses.csv", csv_bytes(self.base + wrong))
        with self.assertRaisesRegex(ValueError, "independently pinned"):
            P.validate_inputs(self.repo, self.contract)
        self.write("adopted.csv", csv_bytes(wrong))
        with self.assertRaisesRegex(ValueError, "authorization pin changed"):
            P.validate_inputs(self.repo, self.contract)

    def test_changed_historical_rows_are_rejected(self):
        changed = copy.deepcopy(self.base)
        changed[0]["decision_origin"] = "unauthorized"
        self.write("statuses.csv", csv_bytes(changed))
        with self.assertRaisesRegex(ValueError, "historical status bytes"):
            P.validate_inputs(self.repo, self.contract)

    def test_missing_or_changed_acceptance_evidence_is_rejected(self):
        self.accept_extra()
        self.write("review.json", b"{}")
        with self.assertRaisesRegex(ValueError, "authorization pin changed"):
            P.validate_inputs(self.repo, self.contract)
        (self.repo / "review.json").unlink()
        with self.assertRaises(FileNotFoundError):
            P.validate_inputs(self.repo, self.contract)

    def test_absent_accepted_delta_is_rejected(self):
        self.accept_extra()
        self.write("statuses.csv", self.base_bytes)
        with self.assertRaisesRegex(ValueError, "independently pinned"):
            P.validate_inputs(self.repo, self.contract)

    def test_duplicate_or_swapped_census_identity_is_rejected(self):
        self.write("census.csv", csv_bytes([{"id": "EO:1"}, {"id": "EO:2"}, {"id": "EO:2"}]))
        with self.assertRaisesRegex(ValueError, "duplicate identity"):
            P.validate_inputs(self.repo, self.contract)
        self.write("census.csv", csv_bytes([{"id": "EO:1"}, {"id": "EO:2"}, {"id": "EO:4"}]))
        with self.assertRaisesRegex(ValueError, "Census identities changed"):
            P.validate_inputs(self.repo, self.contract)

    def test_status_outside_census_is_rejected(self):
        self.extra[0]["instrument_id"] = "EO:99"
        self.write("adopted.csv", csv_bytes(self.extra))
        self.accept_extra()
        with self.assertRaisesRegex(ValueError, "absent from census"):
            P.validate_inputs(self.repo, self.contract)


class DerivedCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.population = {"universe": 3, "statuses": {"EO:1": "yes", "EO:2": "no"}}
        self.drafts = self.repo / "drafts"
        self.kit = self.repo / "kit"
        self.drafts.mkdir()
        (self.kit / "dossiers").mkdir(parents=True)
        self.write_json(self.drafts / "SUMMARY.json",
                        {"scope": "decided", "job_limit": None, "decided_orders_with_draft": 2})
        self.draft_rows = [{"instrument_id": iid, "_draft": {"provisional_status": status}}
                           for iid, status in self.population["statuses"].items()]
        self.write_drafts(self.draft_rows)
        index = []
        for iid, status in self.population["statuses"].items():
            dossier = {"instrument_id": iid, "whole_order_status": status, "schema": "fixture"}
            dossier["fingerprint"] = P.canonical_sha(dossier)
            name = "dossiers/" + iid.replace(":", "_") + ".json"
            self.write_json(self.kit / name, dossier)
            index.append({"instrument_id": iid, "status": status, "dossier": name,
                          "fingerprint": dossier["fingerprint"]})
        self.write_json(self.kit / "INDEX.json", index)
        self.write_json(self.kit / "SUMMARY.json",
                        {"counts": {"decided_orders": 2, "dossiers": 2, "universe_orders": 3}})

    def write_json(self, path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def write_drafts(self, rows):
        (self.drafts / "DRAFT_CLAIMS.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def test_exact_current_coverage_passes(self):
        checked = P.validate_derived(self.population, self.drafts, self.kit)
        self.assertTrue(checked["drafts"] and checked["dossiers"])

    def test_stale_draft_membership_fails_despite_correct_summary_count(self):
        self.draft_rows[1]["instrument_id"] = "EO:3"
        self.write_drafts(self.draft_rows)
        with self.assertRaisesRegex(ValueError, "Draft coverage stale"):
            P.validate_derived(self.population, drafts=self.drafts)

    def test_duplicate_and_wrong_status_drafts_fail(self):
        self.write_drafts([self.draft_rows[0], self.draft_rows[0]])
        with self.assertRaisesRegex(ValueError, "duplicate identity"):
            P.validate_derived(self.population, drafts=self.drafts)
        self.draft_rows[1]["_draft"]["provisional_status"] = "yes"
        self.write_drafts(self.draft_rows)
        with self.assertRaisesRegex(ValueError, "Draft statuses stale"):
            P.validate_derived(self.population, drafts=self.drafts)

    def test_missing_shard_fails_even_when_summary_is_current(self):
        self.write_drafts(self.draft_rows[:1])
        with self.assertRaisesRegex(ValueError, "Draft coverage stale"):
            P.validate_derived(self.population, drafts=self.drafts)

    def test_real_rolling_writer_shard_names_are_included(self):
        self.write_drafts(self.draft_rows[:1])
        (self.drafts / "DRAFT_CLAIMS_2.jsonl").write_text(
            json.dumps(self.draft_rows[1]) + "\n", encoding="utf-8")
        (self.drafts / "DRAFT_CLAIMS_UNDECIDED.jsonl").write_text(
            '{"instrument_id":"EO:3","_draft":{"provisional_status":null}}\n', encoding="utf-8")
        self.assertTrue(P.validate_derived(self.population, drafts=self.drafts)["drafts"])

    def test_stale_dossier_summary_is_reported_separately(self):
        self.write_json(self.kit / "SUMMARY.json",
                        {"counts": {"decided_orders": 1, "dossiers": 1, "universe_orders": 3}})
        with self.assertRaisesRegex(ValueError, "Dossier summary population stale"):
            P.validate_derived(self.population, dossiers=self.kit)

    def test_missing_or_wrong_identity_dossier_fails(self):
        path = self.kit / "dossiers/EO_2.json"
        dossier = json.loads(path.read_text())
        dossier["instrument_id"] = "EO:3"
        self.write_json(path, dossier)
        with self.assertRaisesRegex(ValueError, "Dossier identity/status stale"):
            P.validate_derived(self.population, dossiers=self.kit)
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            P.validate_derived(self.population, dossiers=self.kit)

    def test_dossier_content_and_index_fingerprints_must_match(self):
        path = self.kit / "dossiers/EO_2.json"
        dossier = json.loads(path.read_text())
        dossier["changed"] = True
        self.write_json(path, dossier)
        with self.assertRaisesRegex(ValueError, "fingerprint stale"):
            P.validate_derived(self.population, dossiers=self.kit)

    def test_unindexed_obsolete_dossier_fails(self):
        self.write_json(self.kit / "dossiers/EO_3.json", {"instrument_id": "EO:3"})
        with self.assertRaisesRegex(ValueError, "Dossier file coverage stale"):
            P.validate_derived(self.population, dossiers=self.kit)


if __name__ == "__main__":
    unittest.main()
