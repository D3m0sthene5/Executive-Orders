# Executive Orders

This repository holds the consolidated input archive for **The Afterlife of Executive Orders**. It is a research handoff, not an executed Stage 17 release or a set of human-certified legal findings.

The original ZIP is **2,966,329,767 bytes**, above GitHub's per-file limit. Its two byte-exact parts are stored with Git LFS:

| File | Bytes | SHA-256 |
|---|---:|---|
| `EO_STAGE17_CONSOLIDATED_INPUTS_2026-10-16.zip.part01` | 1,500,000,000 | `42dc6f48c13550647896a708ed0bc5be27acc271c81509cc361588137b2fcef8` |
| `EO_STAGE17_CONSOLIDATED_INPUTS_2026-10-16.zip.part02` | 1,466,329,767 | `7f587b22e38c029f749bdca5d2c9381710c850775128421d8ece525364ca13a1` |

To restore the original ZIP after cloning with Git LFS installed:

```sh
git lfs pull
python restore_archive.py
```

The restore script verifies the complete ZIP's SHA-256: `52edb4d40d07fb713514968684f1adeb7cd65a52b9f89c9216fd44c590fc8775`.

The ZIP contains the named Stage 16 and Opus Stage 11 checkpoint releases, the provisional Stage 17 bridge, unique prior source packages, all ten Stage 2 source volumes, the verified Stage 3 archive, and the Clifford Lord scan. Read its `README.md` and `manifest.json` after extraction for provenance and exact file hashes.

**Known gap:** `OPUS_STAGE11_CHECKPOINT2_EVIDENCE_ORIGINALS.zip` was not found among the available local files. The Opus checkpoint findings still require independent source reinspection. No Stage 17 research prompt was executed in preparing this archive.
