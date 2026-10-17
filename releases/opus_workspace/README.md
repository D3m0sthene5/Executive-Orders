# Opus working folders (Stages 9 and 11)

This folder is the complete working state of the Opus session (2026-10-16 to 10-17), not a curated release. It holds every producer shard and every reviewer folder, the protocols, coordinator rulings, telemetry, packets, scripts, text extractions, web-page captures and metadata files. Each original download has a metadata file with its URL, real retrieval time and SHA-256.

The curated results are in `../opus_stage9/` and `../opus_stage11_complete/`. Use those first.

| Part | Files | Raw | Zip | SHA-256 |
|---|---:|---:|---:|---|
| `OPUS_WORKSPACE_PART01.zip` | 6,574 | 991 MB | 318 MB | `ad3f4fd5a900715f0e16e67418075eeb5792971db35fee7a60096bdcc230bc00` |
| `OPUS_WORKSPACE_PART02.zip` | 16,758 | 997 MB | 407 MB | `98ac7c51fe5124f1d1c4dc1327de646e6fae1fc9192f74d0f01e4323986a7872` |
| `OPUS_WORKSPACE_PART03.zip` | 7,949 | 879 MB | 232 MB | `9ffd4739dc441e57386e9e40eb96aa5ca6c9387152c8e1a3064de4f1dff70f6f` |
| `OPUS_WORKSPACE_PART04.zip` | 5,155 | 905 MB | 219 MB | `fa99d9c38dcb535ef7478c7a2afcfe420378e96527f3cb11ac44f25a6a86defa` |

Each part is a standalone zip and is stored with Git LFS. Unzipping all four into one folder rebuilds `opus_workspace/`. `PARTS_INDEX.json` lists which shard and review folders each part holds. Part 01 also has the small top-level files: code, protocols, input extractions and Stage 9 leads.

**Left out:** 2,145 large public originals (17.64 GB): Federal Register and other government PDFs, U.S. Code release zips and large XML files. They are public, can be downloaded again, and would exceed this account's free Git LFS storage. `EXCLUDED_PUBLIC_ORIGINALS.jsonl` lists each one by path and size, and gives the source URL and recorded SHA-256 where a metadata file exists (1,907 of the 2,145). The PDF page excerpts that the evidence relies on are in the curated releases' image/originals companions.

**Also left out:** the session's own chat transcript, because it contains account details and this repository is public.
