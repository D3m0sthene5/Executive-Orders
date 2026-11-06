"""Offline tests for Kean leases against a local bare repository standing in for GitHub."""
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lease  # noqa: E402


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


class LeaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        self.origin = os.path.join(root, "origin.git")
        git(root, "init", "--quiet", "--bare", self.origin)
        self.a = os.path.join(root, "a")
        self.b = os.path.join(root, "b")
        for d in (self.a, self.b):
            git(root, "clone", "--quiet", self.origin, d)
        self.sa, self.sb = lease.Store(self.a), lease.Store(self.b)

    def tearDown(self):
        self.tmp.cleanup()

    def test_claim_then_other_holder_is_refused(self):
        rec, wrote = lease.claim(self.sa, "job:x", "alice", 30, "first")
        self.assertTrue(wrote)
        rec2, wrote2 = lease.claim(self.sb, "job:x", "bob", 30, "second")
        self.assertFalse(wrote2)
        self.assertEqual(rec2["holder"], "alice")
        self.assertEqual(lease.check(self.sb, "job:x", "bob")[0], lease.HELD)
        self.assertEqual(lease.check(self.sb, "job:x", "alice")[0], 0)

    def test_lost_race_rereads_and_backs_off(self):
        lease.claim(self.sa, "job:other", "alice", 30)
        self.sb.fetch()
        stale = self.sb.tip()
        lease.claim(self.sa, "job:x", "alice", 30)          # alice moves the branch after bob read it
        real_fetch, calls = self.sb.fetch, []

        def stale_once():
            calls.append(1)
            return stale if len(calls) == 1 else real_fetch()
        self.sb.fetch = stale_once
        rec, wrote = lease.claim(self.sb, "job:x", "bob", 30)
        self.assertFalse(wrote)                              # first push rejected, re-read shows alice
        self.assertEqual(rec["holder"], "alice")
        self.assertGreaterEqual(len(calls), 2)

    def test_lost_race_on_different_resource_still_claims(self):
        lease.claim(self.sa, "job:other", "alice", 30)
        self.sb.fetch()
        stale = self.sb.tip()
        lease.claim(self.sa, "job:third", "alice", 30)
        real_fetch, calls = self.sb.fetch, []
        self.sb.fetch = lambda: (calls.append(1), stale if len(calls) == 1 else real_fetch())[1]
        rec, wrote = lease.claim(self.sb, "job:x", "bob", 30)
        self.assertTrue(wrote)
        leases = self.sa.read_all(self.sa.fetch())
        self.assertEqual(sorted(leases), ["job:other", "job:third", "job:x"])   # nothing was overwritten

    def test_expired_lease_is_free(self):
        lease.claim(self.sa, "job:x", "alice", 30)
        tip = self.sa.fetch()
        rec = self.sa.read_all(tip)["job:x"]
        rec["until_utc"] = lease.iso(lease.utcnow() - dt.timedelta(minutes=1))
        self.assertTrue(self.sa.push(self.sa.commit(tip, "leases/" + lease.slug("job:x"), rec, "expire")))
        rec2, wrote = lease.claim(self.sb, "job:x", "bob", 30)
        self.assertTrue(wrote)
        self.assertEqual(rec2["holder"], "bob")

    def test_release_and_renew(self):
        lease.claim(self.sa, "job:x", "alice", 30, "p", "branch-a")
        rec, _ = lease.claim(self.sa, "job:x", "alice", 90, renew_only=True)
        self.assertEqual(rec["purpose"], "p")
        self.assertEqual(rec["branch"], "branch-a")
        self.assertTrue(rec["renewed_utc"])
        rec, wrote = lease.claim(self.sb, "job:x", "bob", 30, renew_only=True)
        self.assertFalse(wrote)
        self.assertEqual(rec["holder"], "alice")
        with self.assertRaises(lease.LeaseError):
            lease.claim(self.sb, "job:free", "bob", 30, renew_only=True)
        _, wrote = lease.release(self.sb, "job:x", "bob")
        self.assertFalse(wrote)
        _, wrote = lease.release(self.sa, "job:x", "alice")
        self.assertTrue(wrote)
        self.assertEqual(lease.check(self.sb, "job:x", "bob")[0], 0)

    def test_held_by_others_never_raises(self):
        lease.claim(self.sa, "batch:p1", "alice", 30)
        found, why = lease.held_by_others(self.b, ["batch:p1", "order:EO_1"], "bob")
        self.assertEqual([r["holder"] for r in found], ["alice"])
        found, why = lease.held_by_others(self.b, ["batch:p1"], "alice")
        self.assertEqual(found, [])
        found, why = lease.held_by_others(self.b, ["x"], "bob", remote="nowhere")
        self.assertIsNone(found)
        self.assertTrue(why)

    def test_cli_exit_codes(self):
        self.assertEqual(lease.main(["--repo", self.a, "claim", "--resource", "s", "--holder", "alice"]), 0)
        self.assertEqual(lease.main(["--repo", self.b, "claim", "--resource", "s", "--holder", "bob"]), lease.HELD)
        self.assertEqual(lease.main(["--repo", self.b, "check", "--resource", "s", "--holder", "bob"]), lease.HELD)
        self.assertEqual(lease.main(["--repo", self.b, "list"]), 0)

    def test_slug_distinguishes_similar_names(self):
        self.assertNotEqual(lease.slug("job:a b"), lease.slug("job:a-b"))
        self.assertTrue(lease.slug("order:EO_10340").startswith("order-EO_10340-"))

    def test_record_is_json_on_branch(self):
        lease.claim(self.sa, "job:x", "alice", 30)
        names = git(self.a, "ls-tree", "--name-only", "-r", lease.REMOTE_REF).split()
        self.assertEqual(len(names), 1)
        rec = json.loads(git(self.a, "show", lease.REMOTE_REF + ":" + names[0]))
        self.assertEqual(rec["resource"], "job:x")


if __name__ == "__main__":
    unittest.main()
