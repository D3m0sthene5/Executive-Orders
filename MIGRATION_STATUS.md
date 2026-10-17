# Historical research migration status

Last updated: 2026-10-17. This is an operational status record, not a legal-research revision.

The public repository contains the Stage 17 research source and the original consolidated historical-input archive as Git LFS objects. **All 74 Stage 12–17 public release parts have been committed and pushed to `main`; independent fresh-checkout retrieval is the next gate.** `research/releases/RELEASES_MANIFEST.json` is the recovery specification. Check the machine-readable `research/releases/MIGRATION_JOURNAL.json` for each part's prepared, verified, committed, pushed, and independently retrieved state.

The published release package has 74 binary parts: six versioned releases, a 250-file workpaper pack, and a compressed Stage 17 SQLite database. Stage 12, 13, and 15 public releases omit sealed blind-review answers. The Stage 13 original had a nested Stage 12 sealed key; its sanitized public hash is recorded separately from its original hash. The original sealed releases and coordinator keys must not be added to this public repository. The older 29-part transfer is overlapping and may contain sealed material; it is not the public publication baseline.

The Stage 17 checkpoint has 14,972 working bibliographic identities; provisional substantive YES / NO / UNKNOWN counts are 268 / 2,787 / 11,917. There are 13 scoped provision histories, 26 dated transitions, and zero independently human-certified legal claims. The historical census and first-cessation reconstruction remain incomplete.

Known missing companion: `OPUS_STAGE11_CHECKPOINT2_EVIDENCE_ORIGINALS.zip`. Do not infer authentication of its source images. The original 2.97 GB consolidated archive has a local copy with the expected size; remote LFS payload retrieval still needs independent verification. Original sealed answer materials remain in protected ChatGPT Library storage; no private GitHub archive has yet been established.

## Recovery instructions

1. Read `research/releases/RELEASES_MANIFEST.json` and `research/releases/MIGRATION_JOURNAL.json`.
2. Check the live `main` tree and compare each listed part's size and SHA-256 with the manifest.
3. Run `python research/releases/restore_releases.py --all --decompress --out restored_research`. Install the `zstd` CLI or Python `zstandard` package for decompression.
4. Verify the restored Stage 17 database SHA-256 `c362f5a8de7c31be2d1a700b00272aca9597136d74ff575fdc72ac24373984e1` and SQLite `PRAGMA integrity_check`.
5. Independently clone from GitHub and repeat the verification. Never equate local staging with remote publication.

