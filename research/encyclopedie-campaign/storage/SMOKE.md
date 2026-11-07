# Pergamon release backend: live smoke test

Run 2026-11-06 from the owner's PC (`py -I research/encyclopedie-campaign/storage/smoke_release.py`). The token came from
`gh auth token` and was never printed. Nothing but the one 64-byte test file below was uploaded.

| Item | Value |
|---|---|
| Release | tag `pergamon-selftest`, name "Pergamon self-test (no evidence)", prerelease, not a draft |
| Release page | https://github.com/D3m0sthene5/Executive-Orders/releases/tag/pergamon-selftest |
| Asset | `7ba1250c7ea62e20f4b0bc90f1b740793bbce96224bff3f0417fb6612e4f62a2.txt`, 64 bytes, state `uploaded` |
| Public URL (no token) | https://github.com/D3m0sthene5/Executive-Orders/releases/download/pergamon-selftest/7ba1250c7ea62e20f4b0bc90f1b740793bbce96224bff3f0417fb6612e4f62a2.txt |
| SHA-256 recorded at upload | `7ba1250c7ea62e20f4b0bc90f1b740793bbce96224bff3f0417fb6612e4f62a2` |
| SHA-256 of the bytes downloaded by a separate tokenless reader (`Store.get_verified`) | `7ba1250c7ea62e20f4b0bc90f1b740793bbce96224bff3f0417fb6612e4f62a2` (equal) |
| SHA-256 of `curl -sL <public URL>`, run separately | `7ba1250c7ea62e20f4b0bc90f1b740793bbce96224bff3f0417fb6612e4f62a2` (equal) |
| Second `put` of the same bytes | deduplicated: same locator, no second asset (the release lists exactly one asset) |
| Effect on "latest release" | none: `releases/latest` still returns 404, because shard and self-test releases are created as prereleases with `make_latest: false` |

Manifest record the store returned:

```json
{"backend": "release", "bytes": 64, "ext": ".txt",
 "locator": "https://github.com/D3m0sthene5/Executive-Orders/releases/download/pergamon-selftest/7ba1250c7ea62e20f4b0bc90f1b740793bbce96224bff3f0417fb6612e4f62a2.txt",
 "meta": {"purpose": "smoke test"}, "sha256": "7ba1250c7ea62e20f4b0bc90f1b740793bbce96224bff3f0417fb6612e4f62a2",
 "stored_utc": "2026-11-06T22:35:58Z"}
```

The release creates one git tag `pergamon-selftest` on the default branch's head (a few bytes of refs). The self-test
release may be deleted at any time without touching anything else. It is not evidence and no manifest should cite it.
