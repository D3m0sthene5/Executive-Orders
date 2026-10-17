# Executive Orders — GitHub migration status (2026-10-17)

**Status: PARTIAL.** This file is an evidence-based inventory of what is in GitHub, and what is not. Do not interpret Stage 17 source-code integration as migration of all earlier release artifacts.

## Verified on GitHub

- `main` includes the existing consolidated Git LFS source archive (two pointer files and `restore_archive.py`), plus Stage 17 source code, research facts, the 1,620-item execution queue, and the Stage 17 research report.
- Stage 12–16 human-readable primary README reports are preserved under `research/stages/stage12` through `stage16` as separately retrievable Git blobs (added in the same commit as this file).

## Preserved elsewhere, not yet committed to GitHub

- The complete Stage 12, 13, 14, 15, 16, and 17 release ZIPs are in ChatGPT Library folder `/Executive Order Research/Audit Releases/` and in the conversation artifact workspace.
- A source-derived, SHA-indexed transfer has been assembled containing 256 nonbinary Stage 12–17 workpapers (58.6 MB before compression, 14.4 MB after compression) and four SQLite research database snapshots (27.2 MB compressed). These packages and their manifests are held in the artifact workspace but **have not been fully pushed to GitHub**.
- The full 2.97 GB Git LFS source archive was not independently downloaded here; only the original Git LFS pointer files and README/restore script were inspected.
- The separate Opus Checkpoint 2 original-image companion has not been found and its claims remain source-reinspection-pending.
- The Stage 15 coordinator-only sealed reviewer key and blind sampling records are intentionally kept outside the publicly accessible repository to preserve independent review integrity.

## Next check

1. Confirm every release ZIP and the SHA of its SQLite database in Library.
2. Complete transfer of the workpapers and database snapshots with an authorized binary upload route (Git LFS, release assets, or small checked Git objects) and verify a fresh restoration from GitHub. Do **not** bypass GitHub or platform safety checks to transfer an unsupported binary.
3. Publish the exact transfer manifest and restoration tests after all required parts are present.
4. Only then mark the GitHub migration complete.

The project's historical order census and legal-effect determinations remain research-provisional regardless of file-transfer status.