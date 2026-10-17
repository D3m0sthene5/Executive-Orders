# Historical research migration status

Last updated: 2026-10-17. This is an operational status record, not a legal-research revision.

**Result: public release migration verified; overall migration partial.** A fresh GitHub clone at commit `6eadbb75e45f3166f813f08245570d9ae3706ba2` independently retrieved and restored all 74 Stage 12–17 public release parts. The six ZIPs passed archive tests, all 250 workpaper members matched their SHA-256 records, and the Stage 17 canonical SQLite matched its expected SHA-256 and passed `PRAGMA integrity_check`. The four historical database snapshots embedded in Stages 14–17 also opened and passed integrity checks. Check the machine-readable [`research/releases/MIGRATION_JOURNAL.json`](research/releases/MIGRATION_JOURNAL.json) for each part's prepared, verified, committed, pushed, and independently retrieved state.

The published release package has 74 binary parts: six versioned releases, a 250-file workpaper pack, and a compressed Stage 17 SQLite database. Stage 12, 13, and 15 public releases omit sealed blind-review answers. The Stage 13 original had a nested Stage 12 sealed key; its sanitized public hash is recorded separately from its original hash. The original sealed releases and coordinator keys must not be added to this public repository. The older 29-part transfer is overlapping and may contain sealed material; it is not the public publication baseline.

The Stage 17 checkpoint has 14,972 working bibliographic identities; provisional substantive YES / NO / UNKNOWN counts are 268 / 2,787 / 11,917. There are 13 scoped provision histories, 26 dated transitions, and zero independently human-certified legal claims. The historical census and first-cessation reconstruction remain incomplete.

Known missing companion: `OPUS_STAGE11_CHECKPOINT2_EVIDENCE_ORIGINALS.zip`. It was not found in local Downloads or Library search. Do not infer authentication of its source images. The original 2.97 GB consolidated archive's local copy matches the expected full and part SHA-256 hashes. GitHub LFS returned authenticated download actions for both objects, and HTTP 206 first/last 1 KiB byte ranges matched the local copy; a full 2.97 GB remote redownload and hash were not performed. See [`LFS_REMOTE_RANGE_VERIFICATION.json`](research/releases/LFS_REMOTE_RANGE_VERIFICATION.json).

The separate preexisting 157,990,153-byte final Opus Stage 11 Git LFS release was fully retrieved from GitHub in the independent checkout. Its SHA-256 and ZIP integrity passed; see [`OPUS_LFS_VERIFICATION.json`](research/releases/OPUS_LFS_VERIFICATION.json). These final Opus findings remain AI-reviewed and are distinct from Stage 17's earlier Checkpoint 2 import.

Original sealed Stage 12, Stage 13, and Stage 15 releases and the Stage 15 coordinator key remain in protected ChatGPT Library storage. The originals were locally retrieved, hash-checked, and excluded from the public release. **No private GitHub archive was created:** automatic approval review rejected creation of a separate private repository as a consequential access/resource change. This is the remaining publication exception. The older 29-part transfer was not published because it overlaps the final public package and may contain sealed material.

The Stage 17 builder and claim-review round-trip test ran from the fresh checkout. A clean build using local SQLite 3.49.1 yielded SHA-256 `f245257384e4d297c23495c041167229f9679abc7f47cd4fe0c66b9acd3d9e82`, reproducibly on a second run. The published database was created with SQLite 3.46.1 and has SHA-256 `c362f5a8de7c31be2d1a700b00272aca9597136d74ff575fdc72ac24373984e1`. Both have identical schema and sorted row contents across all 34 tables, but are not byte-identical. Restore the published database pack when exact canonical bytes are required. See [`STAGE17_REBUILD_COMPARISON.json`](research/releases/STAGE17_REBUILD_COMPARISON.json).

## Recovery instructions

1. Read `research/releases/RELEASES_MANIFEST.json` and `research/releases/MIGRATION_JOURNAL.json`.
2. Check the live `main` tree and compare each listed part's size and SHA-256 with the manifest.
3. Run `python research/releases/restore_releases.py --all --decompress --out restored_research`. Install the `zstd` CLI or Python `zstandard` package for decompression.
4. Verify the restored Stage 17 database SHA-256 `c362f5a8de7c31be2d1a700b00272aca9597136d74ff575fdc72ac24373984e1` and SQLite `PRAGMA integrity_check`.
5. Independently clone from GitHub and repeat the verification. The recorded clean-checkout result is tied to commit `6eadbb75e45f3166f813f08245570d9ae3706ba2`; later documentation commits do not change the archive parts.

