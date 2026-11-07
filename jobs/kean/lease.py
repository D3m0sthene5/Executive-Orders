#!/usr/bin/env python3
"""Kean leases: one short record of who holds a batch, job or stream, until when.

Sessions kept starting the same batch or job. A lease is a claim with an expiry, so a crashed session
releases it by doing nothing. All leases live on one shared branch, `kean-leases`, one JSON file per
resource under `leases/`. A claim is a commit pushed without force: if someone else pushed first, the
push is rejected as non-fast-forward, the claimant re-reads the branch and either sees the other lease
and backs off, or (if the other push touched a different resource) claims again. That rejected push is
the atomic step; there is no server or database. The idea comes from Beads' and MCP Agent Mail's
atomic claim; neither tool is used.

Commits are built with git plumbing and a private index, so this works from any worktree, sparse or
not, without switching branches or touching the working tree.

    python3 -I jobs/kean/lease.py claim  --resource job:lsa-editions --holder claude-encyclopedie --minutes 240 --purpose "..."
    python3 -I jobs/kean/lease.py renew  --resource job:lsa-editions --holder claude-encyclopedie --minutes 240
    python3 -I jobs/kean/lease.py release --resource job:lsa-editions --holder claude-encyclopedie
    python3 -I jobs/kean/lease.py check  --resource job:lsa-editions --holder claude-encyclopedie
    python3 -I jobs/kean/lease.py list

Exit codes: 0 done (or free / yours), 3 held by another holder, 2 usage or git error.
Resource names are free text by convention `job:<name>`, `batch:<packet>`, `order:<instrument id>` (e.g. `order:EO:10340`),
`stream:<name>`. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

BRANCH = "kean-leases"
REMOTE_REF = "refs/remotes/origin/" + BRANCH
MAX_MINUTES = 24 * 60
DEFAULT_MINUTES = 120
RETRIES = 6
HELD = 3


class LeaseError(Exception):
    pass


def utcnow():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso(t):
    return t.isoformat().replace("+00:00", "Z")


def parse(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def slug(resource):
    """File name for a resource: readable prefix plus a hash so distinct names never collide."""
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", resource).strip("-")[:60] or "lease"
    return base + "-" + hashlib.sha256(resource.encode("utf-8")).hexdigest()[:10] + ".json"


def active(rec, now=None):
    return bool(rec) and not rec.get("released_utc") and parse(rec["until_utc"]) > (now or utcnow())


class Store:
    def __init__(self, root=".", remote="origin"):
        self.root = os.path.abspath(root)
        self.remote = remote

    def git(self, *args, env=None, stdin=None, check=True):
        p = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", input=stdin, env={**os.environ, **(env or {})})
        if check and p.returncode:
            raise LeaseError("git %s failed: %s" % (" ".join(args[:2]), (p.stderr or p.stdout).strip()[:400]))
        return p

    def fetch(self):
        """Update the remote-tracking ref; returns the tip or None when the branch does not exist yet."""
        p = self.git("fetch", "--quiet", self.remote, "+refs/heads/%s:%s" % (BRANCH, REMOTE_REF), check=False)
        if p.returncode:
            if "couldn't find remote ref" in (p.stderr or "").lower():
                self.git("update-ref", "-d", REMOTE_REF, check=False)
                return None
            raise LeaseError("git fetch failed: " + p.stderr.strip()[:400])
        return self.tip()

    def tip(self):
        p = self.git("rev-parse", "--verify", "--quiet", REMOTE_REF, check=False)
        return p.stdout.strip() or None

    def read_all(self, tip):
        if not tip:
            return {}
        out = {}
        names = self.git("ls-tree", "--name-only", tip, "leases/", check=False).stdout.split()
        for name in names:
            raw = self.git("show", "%s:%s" % (tip, name), check=False).stdout
            try:
                rec = json.loads(raw)
                out[rec["resource"]] = rec
            except (ValueError, KeyError):
                continue
        return out

    def commit(self, tip, path, rec, message):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"GIT_INDEX_FILE": os.path.join(tmp, "index")}
            if tip:
                self.git("read-tree", tip, env=env)
            blob = self.git("hash-object", "-w", "--stdin", stdin=json.dumps(rec, indent=1, sort_keys=True) + "\n").stdout.strip()
            self.git("update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path), env=env)
            tree = self.git("write-tree", env=env).stdout.strip()
        ident = {"GIT_AUTHOR_NAME": "kean-lease", "GIT_AUTHOR_EMAIL": "kean-lease@users.noreply.github.com",
                 "GIT_COMMITTER_NAME": "kean-lease", "GIT_COMMITTER_EMAIL": "kean-lease@users.noreply.github.com"}
        args = ["commit-tree", tree, "-m", message] + (["-p", tip] if tip else [])
        return self.git(*args, env=ident).stdout.strip()

    def push(self, commit):
        """True when the push landed; False when another claimant moved the branch first."""
        p = self.git("push", "--quiet", "--porcelain", self.remote, "%s:refs/heads/%s" % (commit, BRANCH), check=False)
        if p.returncode == 0:
            self.git("update-ref", REMOTE_REF, commit, check=False)
            return True
        text = (p.stderr + p.stdout).lower()
        if any(k in text for k in ("non-fast-forward", "fetch first", "rejected", "stale info", "cannot lock ref")):
            return False
        raise LeaseError("git push failed: " + (p.stderr or p.stdout).strip()[:400])


def _write(store, resource, holder, mutate, message):
    """Read, decide, commit and push; on a lost race re-read and decide again."""
    for _ in range(RETRIES):
        tip = store.fetch()
        current = store.read_all(tip).get(resource)
        rec = mutate(current)
        if rec is None:
            return current, False
        if store.push(store.commit(tip, "leases/" + slug(resource), rec, message)):
            return rec, True
    raise LeaseError("lost the race %d times for %s; try again" % (RETRIES, resource))


def claim(store, resource, holder, minutes=DEFAULT_MINUTES, purpose="", branch="", renew_only=False):
    if not 1 <= minutes <= MAX_MINUTES:
        raise LeaseError("minutes must be 1..%d" % MAX_MINUTES)

    def mutate(cur):
        now = utcnow()
        if active(cur, now) and cur["holder"] != holder:
            return None
        if renew_only and not (active(cur, now) and cur["holder"] == holder):
            raise LeaseError("no active lease of yours on %s to renew" % resource)
        mine = active(cur, now) and cur["holder"] == holder
        return {"resource": resource, "holder": holder,
                "purpose": purpose or (cur or {}).get("purpose", "") if mine else purpose,
                "branch": branch or ((cur or {}).get("branch", "") if mine else ""),
                "claimed_utc": cur["claimed_utc"] if mine else iso(now),
                "renewed_utc": iso(now) if mine else "",
                "until_utc": iso(now + dt.timedelta(minutes=minutes)),
                "released_utc": "", "rev": int((cur or {}).get("rev", -1)) + 1}

    rec, wrote = _write(store, resource, holder, mutate, "lease %s %s by %s" % ("renew" if renew_only else "claim", resource, holder))
    return rec, wrote


def release(store, resource, holder):
    def mutate(cur):
        if not active(cur) or cur["holder"] != holder:
            return None
        return {**cur, "released_utc": iso(utcnow()), "rev": int(cur.get("rev", 0)) + 1}

    return _write(store, resource, holder, mutate, "lease release %s by %s" % (resource, holder))


def check(store, resource, holder=None, offline=False):
    """(code, record): 0 when free or held by `holder`, HELD when another holder's lease is active."""
    tip = store.tip() if offline else store.fetch()
    rec = store.read_all(tip).get(resource)
    if active(rec) and rec["holder"] != holder:
        return HELD, rec
    return 0, rec


def held_by_others(root, resources, holder, offline=False, remote="origin"):
    """For other tools (claim-kit dispatch-check, runners): active leases on any of `resources` that
    belong to someone other than `holder`. Never raises: an unreadable lease branch returns
    (None, reason), so callers can report 'lease state unknown' instead of failing."""
    try:
        store = Store(root, remote)
        tip = store.tip() if offline else store.fetch()
        leases = store.read_all(tip)
    except LeaseError as e:
        return None, str(e)
    now = utcnow()
    return [leases[r] for r in resources if r in leases and active(leases[r], now) and leases[r]["holder"] != holder], ""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--remote", default="origin")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("claim", "renew", "release", "check"):
        s = sub.add_parser(name)
        s.add_argument("--resource", required=True)
        s.add_argument("--holder", default=os.environ.get("KEAN_LEASE_HOLDER", ""), required=name != "check"
                       and not os.environ.get("KEAN_LEASE_HOLDER"))
        if name in ("claim", "renew"):
            s.add_argument("--minutes", type=int, default=DEFAULT_MINUTES)
        if name == "claim":
            s.add_argument("--purpose", default="")
            s.add_argument("--branch", default="")
        if name == "check":
            s.add_argument("--offline", action="store_true")
    ls = sub.add_parser("list")
    ls.add_argument("--all", action="store_true", help="include expired and released leases")
    a = ap.parse_args(argv)
    store = Store(a.repo, a.remote)
    try:
        if a.cmd == "claim":
            rec, wrote = claim(store, a.resource, a.holder, a.minutes, a.purpose, a.branch)
            if not wrote:
                print("HELD %s by %s until %s (%s)" % (a.resource, rec["holder"], rec["until_utc"], rec.get("purpose", "")))
                return HELD
            print("CLAIMED %s for %s until %s" % (a.resource, a.holder, rec["until_utc"]))
        elif a.cmd == "renew":
            rec, _ = claim(store, a.resource, a.holder, a.minutes, renew_only=True)
            if rec["holder"] != a.holder:
                print("HELD %s by %s until %s" % (a.resource, rec["holder"], rec["until_utc"]))
                return HELD
            print("RENEWED %s until %s" % (a.resource, rec["until_utc"]))
        elif a.cmd == "release":
            rec, wrote = release(store, a.resource, a.holder)
            print(("RELEASED %s" % a.resource) if wrote else ("NOT HELD by %s: %s" % (a.holder, a.resource)))
        elif a.cmd == "check":
            code, rec = check(store, a.resource, a.holder or None, a.offline)
            print("HELD %s by %s until %s" % (a.resource, rec["holder"], rec["until_utc"]) if code
                  else ("FREE %s" % a.resource if not active(rec) else "YOURS %s until %s" % (a.resource, rec["until_utc"])))
            return code
        else:
            leases = store.read_all(store.fetch())
            now = utcnow()
            rows = sorted((r for r in leases.values() if a.all or active(r, now)), key=lambda r: r["until_utc"])
            for r in rows:
                state = "active" if active(r, now) else ("released" if r.get("released_utc") else "expired")
                print("%-8s %-40s %-28s until %s  %s" % (state, r["resource"], r["holder"], r["until_utc"], r.get("purpose", "")[:60]))
            if not rows:
                print("no active leases")
    except LeaseError as e:
        print("lease: " + str(e), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
