"""Regression checks for the missing-plant continuation failure."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gates import GateStopped, evaluate_gate, require_gate


CONTRACT = {"schema": "llull.gate-contract/v1", "gate_id": "probe",
            "planted_defects": {"required": 3, "minimum_caught": 2},
            "minimums": {"upheld": 5}, "maximums": {"savings_overturned": 1}}
OBSERVATION = {"schema": "llull.gate-observation/v1", "gate_id": "probe",
               "planted_defects": {"present": 3, "reviewed": 3, "caught": 2},
               "metrics": {"upheld": 6, "savings_overturned": 0}}


class GateTests(unittest.TestCase):
    def test_one_of_one_is_untested_for_two_of_three(self):
        o = copy.deepcopy(OBSERVATION)
        o["planted_defects"] = {"present": 1, "reviewed": 1, "caught": 1}
        self.assertEqual(evaluate_gate(CONTRACT, o)["status"], "untested")
        with self.assertRaises(GateStopped):
            require_gate(CONTRACT, o)

    def test_full_probe_passes_only_when_all_thresholds_hold(self):
        self.assertTrue(require_gate(CONTRACT, OBSERVATION)["may_continue"])
        for key, value in (("upheld", 4), ("savings_overturned", 2)):
            o = copy.deepcopy(OBSERVATION)
            o["metrics"][key] = value
            self.assertEqual(evaluate_gate(CONTRACT, o)["status"], "fail")
        o = copy.deepcopy(OBSERVATION)
        o["planted_defects"]["caught"] = 1
        self.assertEqual(evaluate_gate(CONTRACT, o)["status"], "fail")

    def test_missing_review_metric_and_invalid_counts_are_untested(self):
        for counts in ({"present": 3, "caught": 2}, {"present": 3, "reviewed": 2, "caught": 2},
                       {"present": 3, "reviewed": 3, "caught": 4},
                       {"present": 4, "reviewed": 4, "caught": 2}):
            o = copy.deepcopy(OBSERVATION)
            o["planted_defects"] = counts
            self.assertEqual(evaluate_gate(CONTRACT, o)["status"], "untested")
        o = copy.deepcopy(OBSERVATION)
        del o["metrics"]["savings_overturned"]
        self.assertEqual(evaluate_gate(CONTRACT, o)["status"], "untested")

    def test_malformed_objects_fail_closed(self):
        for contract, observation in (([], OBSERVATION), (CONTRACT, []),
                                      ({**CONTRACT, "planted_defects": []}, OBSERVATION),
                                      ({**CONTRACT, "minimums": []}, OBSERVATION),
                                      (CONTRACT, {**OBSERVATION, "metrics": [6, 0]})):
            self.assertEqual(evaluate_gate(contract, observation)["status"], "untested")
            with self.assertRaises(GateStopped):
                require_gate(contract, observation)

    def test_cli_cannot_execute_failed_or_unpinned_probe(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / "observed.json"
            source.write_text("{}")
            o = copy.deepcopy(OBSERVATION)
            o["evidence"] = [{"path": "observed.json", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]
            (root / "c.json").write_text(json.dumps(CONTRACT))
            (root / "o.json").write_text(json.dumps(o))
            sentinel = root / "executed"
            cmd = [sys.executable, "-I", str(Path(__file__).with_name("gates.py")),
                   "--contract", str(root / "c.json"), "--observation", str(root / "o.json"),
                   "--repo", str(root), "--out", str(root / "receipt.json"), "--run", sys.executable,
                   "-c", "from pathlib import Path;Path(%r).write_text('ran')" % str(sentinel)]
            o["planted_defects"] = {"present": 1, "reviewed": 1, "caught": 1}
            (root / "o.json").write_text(json.dumps(o))
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 5)
            self.assertFalse(sentinel.exists())
            self.assertEqual(json.loads((root / "receipt.json").read_text())["status"], "untested")
            o["planted_defects"] = OBSERVATION["planted_defects"]
            o["evidence"][0]["sha256"] = "wrong"
            (root / "o.json").write_text(json.dumps(o))
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 5)
            self.assertFalse(sentinel.exists())
            o["evidence"][0]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            (root / "o.json").write_text(json.dumps(o))
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(sentinel.read_text(), "ran")


if __name__ == "__main__":
    unittest.main()
