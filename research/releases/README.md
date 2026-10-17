# Executive Orders — Stage 12–17 complete progress archive

This directory preserves **the original versioned research releases**, supporting workpapers, code, progress reports, evidence manifests, charts, reviewer examples, and the complete Stage 17 canonical SQLite database.

This repository is public. **Sealed blind-review answer keys are intentionally withheld**, because publication would undermine the validity of future blind quality-control work. The privately held originals remain preserved in the project Library.

## Restore a release

Clone the GitHub repository and run:

```sh
python research/releases/restore_releases.py --all --out restored_research
```

Or reconstruct only the latest canonical SQLite database:

```sh
python research/releases/restore_releases.py --database --decompress --out restored_research
```

This verifies the SHA-256 of every chunk, every complete archive, the 250 extracted workpapers, and the uncompressed Stage 17 canonical SQLite file. It also tests ZIP integrity and runs SQLite `PRAGMA integrity_check`. Decompression uses the `zstd` command if installed, or the Python `zstandard` package (`python -m pip install zstandard`). Restore scripts never change the original Git repository archives.

## Release inventory

| Release | Size of recovered archive | SHA-256 | Uploaded form |
|---|---:|---|---|
| Stage 12 (sanitized; sealed 60-case key withheld) | 5,060,613 B | `48c344cf17b609b901399c1b9ff9bdc87419101d6296703696f0e47b69ee77a8` | 3 chunks |
| Stage 13 (sanitized nested Stage 12 key) | 5,764,999 B | `f13553da811042087c5f9b0ac1099e913e4689851d79793cbf13ffa20dd58115` | 3 chunks |
| Stage 14 | 21,699,451 B | `8550aec887fafe9fc2e5fca6edfeb91d3496dcd845bb18acc6a7957d53569324` | 11 chunks |
| Stage 15 | 895,582 B | `5937c3b815de38b3df3c62bfadeb6871c4529aa79af7db042180fbf4fe39d97e` | 1 chunks (sanitized; sealed answers omitted) |
| Stage 16 | 33,267,405 B | `8c453684269dbd42083a36d6defde2a016d115d86fd63e8f8817bee9328b52e2` | 17 chunks |
| Stage 17 | 61,536,729 B | `2501c2d276a8bb262f5f3b20d75d09fea3561c73ed734e6333d11ebff39c2498` | 31 chunks |
| Workpapers pack (250 nonsealed files) | 4,438,569 B | `c2d0be1a699a325da017762dc5d177d3ddd892c67a14d9ae5f3eeadae95b9fd5` | 3 zstd chunks |
| Database pack | 8,244,934 B | `1ff2cebcba4f3c4fef08140d15e0fc958a26b743fdd41acb4c8f3585e4a9f923` | 5 zstd chunks |

**Total:** 74 content-verified archival fragments. The workpaper pack comprises 250 accessible source-code, report, statistical, review-workpaper, and visualization files selected from the Stage 12–17 originals. Each workpaper is individually listed with a SHA-256 in `RESEARCH_FILES_SHA256.json` inside that pack.

**Excluded from public archives:** sealed Stage 12 review answer key, including its copy nested inside the original Stage 13 release; sealed Stage 15 source labels and separate coordinator answer keys. The original Stage 13 archive is recorded by SHA-256 in the manifest but must not be published to this public repository. Enormous preexisting source vaults/duplicated pinned inputs are preserved in the existing 2.97GB LFS source archive and original release ZIPs. GitHub source bytes under Git LFS must be independently fetched and verified against the source repository's README; retaining pointers does not certify payload availability.

## Statistical meaning of progress

As of the Stage 17 legal cutoff (October 14, 2026): 14,972 bibliographic **proxies** included; 268 legacy YES and 2,787 legacy NO classifications, 11,917 UNKNOWN. These 3,055 provisional decisions represent 20.404756% of the working bibliography, **not** a national survival rate, a percentage of actual work complete, or independent certification. New Stage 17 research adds 13 scoped provision histories, 26 dated transitions, and 14 bounded AI assessments. Human-certified claims remain **zero**. National issuance total and most first-cessation causes remain unresolved.

## Browser-friendly reports and code

In addition to this complete archive, key stage reports and reproducibility scripts are published as ordinary text files in `research/stage12/` through `research/stage17/`. The most current legal findings and research queue remain in [`research/stage17/`](../stage17/README.md). Use the release manifest for complete archival reconstruction.

## Integrity and limitations

- Original releases and their hashes are recorded; Stage 12, 13, and 15 published ZIPs are **not byte-identical** to the originals since they omit sealed answers. The manifest records both hashes.
- Compressed Stage 17 database is SHA-256 verified against `c362f5a8de7c31be2d1a700b00272aca9597136d74ff575fdc72ac24373984e1` after restoration.
- GitHub deployment of file bytes does not establish historical authentication, legal validity, or independent human legal review.
- The separately mentioned `OPUS_STAGE11_CHECKPOINT2_EVIDENCE_ORIGINALS.zip` was not recovered in Stage 17. Original-image gaps remain and are documented in the source register.
