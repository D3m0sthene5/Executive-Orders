"""One live smoke test of Pergamon's release backend: upload 64 known bytes to the pergamon-selftest prerelease,
download them back by their public URL with no token, and verify the hash. Uploads nothing else.

Run: py -I research/encyclopedie-campaign/storage/smoke_release.py   (needs `gh auth login`; the token is never printed)
"""
import json
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "jobs/_lib"))
import pergamon_store as P  # noqa: E402

TEXT = (b"Pergamon self-test. Not evidence. Not a source. Safe to delete.\n" + b"." * 64)[:64]
assert len(TEXT) == 64


def main():
    token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    repo = "D3m0sthene5/Executive-Orders"
    backend = P.ReleaseBackend(
        repo, token, tag_prefix="pergamon-selftest", shard_hex=0, prerelease=True,
        release_name="Pergamon self-test (no evidence)",
        release_body="Smoke test of the Pergamon store (jobs/_lib/pergamon_store.py). Holds one 64-byte text file. "
                     "No evidence, no source bytes. Safe to delete.")
    store = P.Store(backend)
    rec = store.put(TEXT, ".txt", {"purpose": "smoke test"})
    # a separate reader: no cache, no token, public URL only
    reader = P.Store(P.ReleaseBackend(repo, None))
    got = reader.get_verified(rec)
    assert got == TEXT and P.sha256_hex(got) == rec["sha256"]
    again = P.Store(P.ReleaseBackend(repo, token, tag_prefix="pergamon-selftest", shard_hex=0)).put(TEXT, ".txt")
    print(json.dumps({"record": rec, "downloaded_sha256": P.sha256_hex(got), "bytes": len(got),
                      "second_put_locator_same": again["locator"] == rec["locator"]}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
