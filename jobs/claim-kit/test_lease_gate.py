"""kit.py dispatch-check honours Kean leases (offline: a local bare repository stands in for GitHub)."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "kean"))
import kit  # noqa: E402
import lease  # noqa: E402


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


class LeaseGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        git(root, "init", "--quiet", "--bare", "origin.git")
        git(root, "clone", "--quiet", "origin.git", "repo")
        self.repo = root / "repo"
        (self.repo / "jobs/kean").mkdir(parents=True)
        shutil.copy(HERE.parent / "kean/lease.py", self.repo / "jobs/kean/lease.py")
        self.packet = self.repo / "research/p1/packet"
        self.packet.mkdir(parents=True)
        self.old = os.environ.get("KEAN_LEASE_HOLDER")

    def tearDown(self):
        if self.old is None:
            os.environ.pop("KEAN_LEASE_HOLDER", None)
        else:
            os.environ["KEAN_LEASE_HOLDER"] = self.old
        self.tmp.cleanup()

    def gate(self, holder):
        os.environ["KEAN_LEASE_HOLDER"] = holder
        result = {"ok": True, "dispatchable_ids": ["EO:1", "EO:2"]}
        kit.lease_gate(self.repo, self.packet, result)
        return result

    def test_no_lease_branch_is_unknown_and_does_not_block(self):
        r = self.gate("bob")
        self.assertTrue(r["ok"])
        self.assertIn(r["lease"]["state"], ("free", "unknown"))

    def test_other_holders_order_lease_blocks(self):
        lease.claim(lease.Store(self.repo), "order:EO:2", "alice", 30, "batch b1")
        r = self.gate("bob")
        self.assertFalse(r["ok"])
        self.assertEqual(r["lease"]["state"], "held_by_other")
        self.assertEqual(r["lease"]["conflicts"][0]["resource"], "order:EO:2")

    def test_own_packet_lease_passes(self):
        lease.claim(lease.Store(self.repo), "batch:packet", "bob", 30)
        r = self.gate("bob")
        self.assertTrue(r["ok"])
        self.assertEqual(r["lease"]["state"], "free")


if __name__ == "__main__":
    unittest.main()
