# Historical research migration status

Last updated: 2026-10-17. This is an operational status record, not a legal-research revision.

The public repository currently contains the Stage 17 research source and the original consolidated historical-input archive as Git LFS objects. The Stage 12–17 public release migration is **in progress**. `research/releases/RELEASES_MANIFEST.json` is a recovery specification; an entry in it does not prove that its bytes have been uploaded. Check the paths on `main` and the machine-readable `research/releases/MIGRATION_JOURNAL.json` before treating any artifact as published.

The prepared release package has 74 expected binary parts: six versioned releases, a 250-file workpaper pack, and a compressed Stage 17 SQLite database. Stage 12 and Stage 15 public releases omit sealed blind-review answers. The original sealed releases and coordinator keys must not be added to this public repository. The older 29-part transfer is overlapping and may contain sealed material; it is not the public publication baseline.

The Stage 17 checkpoint has 14,972 working bibliographic identities; provisional substantive YES / NO / UNKNOWN counts are 268 / 2,787 / 11,917. There are 13 scoped provision histories, 26 dated transitions, and zero independently human-certified legal claims. The historical census and first-cessation reconstruction remain incomplete.

Known missing companion: `OPUS_STAGE11_CHECKPOINT2_EVIDENCE_ORIGINALS.zip`. Do not infer authentication of its source images. The original 2.97 GB consolidated archive has a local copy with the expected size; remote LFS payload retrieval still needs independent verification.

## Recovery instructions

1. Read `research/releases/RELEASES_MANIFEST.json` and `research/releases/MIGRATION_JOURNAL.json`.
2. Check the live `main` tree and compare each listed part's size and SHA-256 with the manifest.
3. Run `python research/releases/restore_releases.py --all --decompress --out restored_research` only after all parts exist. This requires the `zstd` CLI.
4. Verify the restored Stage 17 database SHA-256 `c362f5a8de7c31be2d1a700b00272aca9597136d74ff575fdc72ac24373984e1` and SQLite `PRAGMA integrity_check`.
5. Independently clone from GitHub and repeat the verification. Never equate local staging with remote publication.

