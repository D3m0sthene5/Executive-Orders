# PDF evidence bytes and duplicate plan (Task B5, measured 2026-11-06, read-only)

Method: `git ls-files -s -z`, `git cat-file --batch-check` (blob sizes), LFS-pointer detection on blobs <300 bytes. Script: `dedup/scripts/b5.py`. Nothing in the repository was touched.
A machine measurement of byte identity (same git blob id = same SHA-1 of content) is exact for identity of bytes. It says nothing about which copy is the cited one.

## 1. Measured numbers
| measure | value |
|--|--|
| tracked paths ending `.pdf` (case-insens.) | 3,904 |
| of which LFS pointers (all under `releases/**/*.pdf`, matched by `.gitattributes`) | 9 |
| PDFs stored in git proper | 3,895 files, **4,496,141,888 bytes (4.50 GB)** |
| distinct PDF blobs | 3,759, **3,083,474,468 bytes (3.08 GB)** |
| duplicate groups (same blob, >1 path) | 99 (71 x2, 24 x3, 1 x4, 2 x5, 1 x7) |
| redundant copies | 136 files, **1,412,667,420 bytes (1.41 GB, 31% of PDF bytes)** |
| `git count-objects` pack size | 4.66 GiB (all objects, all types) |

Where the redundancy sits:
- 1,359,277,052 bytes (96%) are groups spanning `jobs/astra-source-retention/output/pdf/` and `research/excavator/` (48 groups; `research/excavator/` touches 63 groups, 1.369 GB redundant including salvage and other overlaps).
  The retention job's files are named by sha256 (`<sha256>.pdf`); the excavator copies keep the same file name in per-batch directories.
- `research/excavator/` vs `research/salvage/`: 8,469,177 bytes.
- `ProQuest Pre-1937 Orders/` copies like `X (1).pdf`, `X (2).pdf` and `research/pre-1937-sources/ProQuest Pre-1937 Orders/` (about 54 MB combined; mostly download-duplicates with " (n)" suffixes).
- Top 50 groups account for 1,402,162,366 of the 1,412,667,420 redundant bytes (99.3%).

**Important nuance:** git stores identical blobs once. Clone/pack size is NOT inflated by these 1.41 GB; they inflate the working-tree checkout (and runner disk/time on every Actions checkout) and the number of files an agent can wrongly treat as separate evidence. A history rewrite would save no pack bytes for exact duplicates.

### Top-level directories by PDF bytes (first two path components; full table `dedup/PDF_BYTES_BY_DIR.csv`)
| dir | PDFs | bytes |
|--|--|--|
| jobs/astra-source-retention | 251 | 1,591,813,885 |
| research/excavator | 138 | 1,426,613,801 |
| jobs/ptolemy-custody | 398 | 664,113,387 |
| ProQuest Pre-1937 Orders | 2793 | 427,627,763 |
| research/stage18 | 16 | 111,005,196 |
| jobs/hathi-gpo-orders | 38 | 100,911,782 |
| research/salvage | 21 | 87,569,277 |
| research/stage21 | 160 | 40,391,444 |
| jobs/fr-pages | 28 | 15,402,202 |
| research/pre-1937-sources | 13 | 15,047,435 |
| research/stage20 | 7 | 10,228,137 |
| jobs/library-survey | 2 | 2,046,699 |
| jobs/shepard-citations | 24 | 1,779,644 |
| research/production | 3 | 1,551,908 |
| jobs/early-ranger-facsimiles | 3 | 39,328 |

### 30 largest directories (exact directory) by PDF bytes
See `dedup/PDF_BYTES_BY_DIR.csv` rows `top30_exact_dir`. Top 5:

- `jobs/astra-source-retention/output/pdf`: 251 PDFs, 1,591,813,885 bytes
- `jobs/ptolemy-custody/output/raw`: 398 PDFs, 664,113,387 bytes
- `research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf`: 15 PDFs, 524,238,805 bytes
- `ProQuest Pre-1937 Orders`: 2793 PDFs, 427,627,763 bytes
- `research/excavator/astra-production-2026-10-24/b01/page-checks`: 4 PDFs, 272,336,749 bytes
- Positions 11-30 are mostly `research/excavator/codex-continuous-2026-10-24/*/source-cache/ladder/blobs/<xx>/` (one large PDF each) and `research/excavator/machiavelli-*` acquisition dirs.

## 2. Duplicate groups
Full list: `dedup/DUPLICATE_PDFS.csv` (blob,size,copies,redundant_bytes,paths; sorted by redundant bytes; paths joined by ` | `). Top 50 (paths abbreviated to the first 3):

| # | blob | size | copies | redundant | paths |
|--|--|--|--|--|--|
| 1 | c12064f19d | 91,189,374 | 4 | 273,568,122 | jobs/astra-source-retention/output/pdf/5432431cc09039ad5672f86f17e1fb6dddf44075581197caa24cd70f1448da4a.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/5432431cc09039ad5672f86f17e1fb6dddf44075581197caa24cd70f1448da4a.pdf ; research/excavator/astra-production-2026-10-24/b01/page-checks/5432431cc09039ad5672f86f17e1fb6dddf44075581197caa24cd70f1448da4a.pdf ; (+1 more) |
| 2 | 583276c4a1 | 87,835,654 | 3 | 175,671,308 | jobs/astra-source-retention/output/pdf/2bbe84367ac61a00fa9305998fc1ffef94854553ab085e5eeed81296a09c918b.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/2bbe84367ac61a00fa9305998fc1ffef94854553ab085e5eeed81296a09c918b.pdf ; research/excavator/astra-production-2026-10-24/b01/page-checks/2bbe84367ac61a00fa9305998fc1ffef94854553ab085e5eeed81296a09c918b.pdf |
| 3 | 2e2d3b83ce | 85,067,410 | 3 | 170,134,820 | jobs/astra-source-retention/output/pdf/56b46770ca89bc4f1e85cec8842eb0e28a4dd0cfb466a6513647bdeeb7dceba2.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/56b46770ca89bc4f1e85cec8842eb0e28a4dd0cfb466a6513647bdeeb7dceba2.pdf ; research/excavator/astra-production-2026-10-24/b01/page-checks/56b46770ca89bc4f1e85cec8842eb0e28a4dd0cfb466a6513647bdeeb7dceba2.pdf |
| 4 | 63ef62f54e | 104,612,053 | 2 | 104,612,053 | jobs/astra-source-retention/output/pdf/aacf815d01c9c3d797d7c516d9ccddd1f723dc1a44e47f8899ba742d988e2127.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/aacf815d01c9c3d797d7c516d9ccddd1f723dc1a44e47f8899ba742d988e2127.pdf |
| 5 | 8b968a781f | 51,299,593 | 3 | 102,599,186 | jobs/astra-source-retention/output/pdf/c5e3e5df15eaac449cc25acd03a1988903fb13937ed5a77a3710a668f16fb9b0.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/c5e3e5df15eaac449cc25acd03a1988903fb13937ed5a77a3710a668f16fb9b0.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition/output/pdf/c5e3e5df15eaac449cc25acd03a1988903fb13937ed5a77a3710a668f16fb9b0.pdf |
| 6 | 45ca749704 | 25,704,200 | 3 | 51,408,400 | jobs/astra-source-retention/output/pdf/29fae75564861cf26957fcae2aaf0f457e8808bcd4d7126a4def5300405b0477.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/29fae75564861cf26957fcae2aaf0f457e8808bcd4d7126a4def5300405b0477.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition/output/pdf/29fae75564861cf26957fcae2aaf0f457e8808bcd4d7126a4def5300405b0477.pdf |
| 7 | 6c13ce9fbd | 50,880,443 | 2 | 50,880,443 | jobs/astra-source-retention/output/pdf/60f5f901b9bc7b14406c7082eac59f97944e56cfa36c4ceb1318c67f006f4e5a.pdf ; research/excavator/codex-continuous-2026-10-24/b04/source-cache/ladder/blobs/60/60f5f901b9bc7b14406c7082eac59f97944e56cfa36c4ceb1318c67f006f4e5a.pdf |
| 8 | 4da68517b3 | 25,324,548 | 3 | 50,649,096 | jobs/astra-source-retention/output/pdf/505bf209599462426ba77bf26b929632994cee5e1692b66441ce77dc5cc55c3c.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/505bf209599462426ba77bf26b929632994cee5e1692b66441ce77dc5cc55c3c.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition/output/pdf/505bf209599462426ba77bf26b929632994cee5e1692b66441ce77dc5cc55c3c.pdf |
| 9 | 3b2b6f1e10 | 43,486,275 | 2 | 43,486,275 | jobs/astra-source-retention/output/pdf/a8fcd871b57293f84d43698f549f62968fb2f85ed72331d2085be12b806ba951.pdf ; research/excavator/codex-continuous-2026-10-24/comparison/legacy-10016/source-cache/ladder/blobs/a8/a8fcd871b57293f84d43698f549f62968fb2f85ed72331d2085be12b806ba951.pdf |
| 10 | be1091b588 | 17,387,298 | 3 | 34,774,596 | jobs/astra-source-retention/output/pdf/004032553b304bea1ecb57bcbb4f6a3190070aa6b10acf8b4ed349392dc27ce7.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/004032553b304bea1ecb57bcbb4f6a3190070aa6b10acf8b4ed349392dc27ce7.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition/output/pdf/004032553b304bea1ecb57bcbb4f6a3190070aa6b10acf8b4ed349392dc27ce7.pdf |
| 11 | 99faa6c5e8 | 32,816,122 | 2 | 32,816,122 | jobs/astra-source-retention/output/pdf/82d8db2e7db11e843e0d32f791865b23dceb7ae2ca6835c15b725abf1169fc65.pdf ; research/excavator/astra-production-2026-10-24/b02/sources/82d8db2e7db11e843e0d32f791865b23dceb7ae2ca6835c15b725abf1169fc65.pdf |
| 12 | 3de9ab273d | 30,679,360 | 2 | 30,679,360 | jobs/astra-source-retention/output/pdf/947c6c1e557d78dba61ee8b8dda4e2f66b335044e09147b4e524b765ce9d2167.pdf ; research/excavator/codex-continuous-2026-10-24/b04/source-cache/ladder/blobs/94/947c6c1e557d78dba61ee8b8dda4e2f66b335044e09147b4e524b765ce9d2167.pdf |
| 13 | a1a0c3f3cf | 28,002,812 | 2 | 28,002,812 | jobs/astra-source-retention/output/pdf/ac8d200fd50f26761579d3a53b94eb1df435d7b7fce4d60b056996703f186663.pdf ; research/excavator/astra-production-2026-10-24/b02/sources/ac8d200fd50f26761579d3a53b94eb1df435d7b7fce4d60b056996703f186663.pdf |
| 14 | f5391cba2b | 11,848,060 | 3 | 23,696,120 | jobs/astra-source-retention/output/pdf/1964472bf5aab066f4cc1a8fe5f305e2a7883d83fabf21f604eb85aab8b9cb5a.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/1964472bf5aab066f4cc1a8fe5f305e2a7883d83fabf21f604eb85aab8b9cb5a.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition/output/pdf/1964472bf5aab066f4cc1a8fe5f305e2a7883d83fabf21f604eb85aab8b9cb5a.pdf |
| 15 | dac04b19b0 | 22,363,218 | 2 | 22,363,218 | jobs/astra-source-retention/output/pdf/bf530ba580045b65beb2121a2fba191485ed8c40a5af5c81ee37a9e25c4b8eec.pdf ; research/excavator/codex-continuous-2026-10-24/b03/source-cache/ladder/blobs/bf/bf530ba580045b65beb2121a2fba191485ed8c40a5af5c81ee37a9e25c4b8eec.pdf |
| 16 | 0028261c23 | 8,244,311 | 3 | 16,488,622 | jobs/astra-source-retention/output/pdf/982a91c8a31ea0c55a6dae51918dc8efc122a3e7c0654b6c4b5c228e8bb46996.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/982a91c8a31ea0c55a6dae51918dc8efc122a3e7c0654b6c4b5c228e8bb46996.pdf ; research/excavator/astra-production-2026-10-24/b01/page-checks/982a91c8a31ea0c55a6dae51918dc8efc122a3e7c0654b6c4b5c228e8bb46996.pdf |
| 17 | e5e6a12a66 | 14,565,002 | 2 | 14,565,002 | jobs/astra-source-retention/output/pdf/af695cc5e2340fb4897e436fbf0ba7da7292e577d4c6f40f7bf3f2f43792042c.pdf ; research/excavator/codex-continuous-2026-10-24/b03/source-cache/ladder/blobs/af/af695cc5e2340fb4897e436fbf0ba7da7292e577d4c6f40f7bf3f2f43792042c.pdf |
| 18 | 5d1c50c619 | 7,280,970 | 3 | 14,561,940 | jobs/astra-source-retention/output/pdf/78ed0072ef4c3dbf17a8eaf492d3afc07dd19d34c43044f8dab1d571ae761dee.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/78ed0072ef4c3dbf17a8eaf492d3afc07dd19d34c43044f8dab1d571ae761dee.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition/output/pdf/78ed0072ef4c3dbf17a8eaf492d3afc07dd19d34c43044f8dab1d571ae761dee.pdf |
| 19 | 73ab73d37f | 2,263,557 | 7 | 13,581,342 | ProQuest Pre-1937 Orders/PT1-1865-EO-4 (1).pdf ; ProQuest Pre-1937 Orders/PT1-1865-EO-4 (2).pdf ; ProQuest Pre-1937 Orders/PT1-1865-EO-4 (3).pdf ; (+4 more) |
| 20 | 5f70ce7074 | 13,050,443 | 2 | 13,050,443 | jobs/astra-source-retention/output/pdf/51ed2ca036d6de3b93004fa031b0e4de7fd198f81297f8b65892f9e9f361ff41.pdf ; research/excavator/codex-continuous-2026-10-24/b04/source-cache/ladder/blobs/51/51ed2ca036d6de3b93004fa031b0e4de7fd198f81297f8b65892f9e9f361ff41.pdf |
| 21 | 282bb79fa8 | 9,770,162 | 2 | 9,770,162 | jobs/astra-source-retention/output/pdf/85d2772b432a9f1dcb2d07242d73c62db6f6b366f27af267d653eca2c7e47eeb.pdf ; research/excavator/codex-continuous-2026-10-24/b04/source-cache/ladder/blobs/85/85d2772b432a9f1dcb2d07242d73c62db6f6b366f27af267d653eca2c7e47eeb.pdf |
| 22 | 445da3ef32 | 9,263,833 | 2 | 9,263,833 | jobs/astra-source-retention/output/pdf/edb67f0fcb47c4306bcf6cc82d7748afb2474b59336f47e2251f6d00a7b193ca.pdf ; research/excavator/codex-continuous-2026-10-24/b03/source-cache/ladder/blobs/ed/edb67f0fcb47c4306bcf6cc82d7748afb2474b59336f47e2251f6d00a7b193ca.pdf |
| 23 | a024f75c5b | 8,856,868 | 2 | 8,856,868 | jobs/astra-source-retention/output/pdf/48545ad00786958e71108e98c2452e30d12dfbf86cd34560b38aceeecc7cf82b.pdf ; research/excavator/codex-continuous-2026-10-24/b04/source-cache/ladder/blobs/48/48545ad00786958e71108e98c2452e30d12dfbf86cd34560b38aceeecc7cf82b.pdf |
| 24 | db893b00ee | 4,251,786 | 3 | 8,503,572 | ProQuest Pre-1937 Orders/PT1-1887-EO-26 (1).pdf ; ProQuest Pre-1937 Orders/PT1-1887-EO-26.pdf ; research/pre-1937-sources/ProQuest Pre-1937 Orders/PT1-1887-EO-26.pdf |
| 25 | 4cbec782c2 | 7,430,984 | 2 | 7,430,984 | jobs/astra-source-retention/output/pdf/d3cd700660b3142d7f3c9a5ba4953015f96973fe5ae08824f8b2ecccc5262a68.pdf ; research/excavator/codex-continuous-2026-10-24/b03/source-cache/ladder/blobs/d3/d3cd700660b3142d7f3c9a5ba4953015f96973fe5ae08824f8b2ecccc5262a68.pdf |
| 26 | d2c90ff1b5 | 1,666,097 | 5 | 6,664,388 | ProQuest Pre-1937 Orders/PT1-1893-EO-29 (1).pdf ; ProQuest Pre-1937 Orders/PT1-1893-EO-29 (2).pdf ; ProQuest Pre-1937 Orders/PT1-1893-EO-29 (3).pdf ; (+2 more) |
| 27 | eb5ccb282e | 6,600,143 | 2 | 6,600,143 | research/excavator/machiavelli-modern-undecided-20261105/acquisition/modern-12-native-v1/pdf/cef9c38aa78a29fec988f17fdc0337a21c70b720ec16b4cca2a25c2251f0f166.pdf ; research/salvage/frozen-drafts-2026-11-05/codex-machiavelli/retained-sources/pdf/cef9c38aa78a29fec988f17fdc0337a21c70b720ec16b4cca2a25c2251f0f166.pdf |
| 28 | 61394abad5 | 6,438,970 | 2 | 6,438,970 | jobs/astra-source-retention/output/pdf/c758ede0941834de8fc07130b1ec673f224d88af218f52897359f5c0db1d95eb.pdf ; research/excavator/codex-continuous-2026-10-24/b04/source-cache/ladder/blobs/c7/c758ede0941834de8fc07130b1ec673f224d88af218f52897359f5c0db1d95eb.pdf |
| 29 | 3a4fb8cc0c | 6,436,469 | 2 | 6,436,469 | jobs/astra-source-retention/output/pdf/7d7b7389da9e2401d4e63fd05686a8d0736f661ab84f1412cc76d594395cc145.pdf ; research/excavator/codex-continuous-2026-10-24/b02/source-ladder-cache/ladder/blobs/7d/7d7b7389da9e2401d4e63fd05686a8d0736f661ab84f1412cc76d594395cc145.pdf |
| 30 | 42ac5cc9b5 | 6,378,055 | 2 | 6,378,055 | jobs/astra-source-retention/output/pdf/4296b00f6953354f038adb105b5bff22037b8df32e9482123a9548b2ac8de2f6.pdf ; research/excavator/codex-continuous-2026-10-24/b01/source-cache/ladder/blobs/42/4296b00f6953354f038adb105b5bff22037b8df32e9482123a9548b2ac8de2f6.pdf |
| 31 | 450b706432 | 6,050,610 | 2 | 6,050,610 | jobs/astra-source-retention/output/pdf/144846d6cda2b8c9f6722e6a42d7acdde89ef946502246330f45784df894f609.pdf ; research/excavator/codex-continuous-2026-10-24/b02/source-ladder-cache/ladder/blobs/14/144846d6cda2b8c9f6722e6a42d7acdde89ef946502246330f45784df894f609.pdf |
| 32 | bb452d71be | 6,002,522 | 2 | 6,002,522 | jobs/astra-source-retention/output/pdf/39220c46225baceebda54c83bce087309e6e64c6749fe2d7b9e528aa35947d04.pdf ; research/excavator/codex-continuous-2026-10-24/b04/source-cache/ladder/blobs/39/39220c46225baceebda54c83bce087309e6e64c6749fe2d7b9e528aa35947d04.pdf |
| 33 | 59f17b279f | 5,140,885 | 2 | 5,140,885 | jobs/astra-source-retention/output/pdf/11dea6ab328b27c2447a40d6b1d148a9b365b19a3b6ea6a210f1d9ee4c028410.pdf ; research/excavator/codex-continuous-2026-10-24/b01/source-cache/ladder/blobs/11/11dea6ab328b27c2447a40d6b1d148a9b365b19a3b6ea6a210f1d9ee4c028410.pdf |
| 34 | 3b1fe6779a | 5,134,537 | 2 | 5,134,537 | jobs/astra-source-retention/output/pdf/10c71f49142e2cdc1635f8e5a52bbe28d86f760259ea4d3c2b73a493d8178d21.pdf ; research/excavator/codex-continuous-2026-10-24/b03/source-cache/ladder/blobs/10/10c71f49142e2cdc1635f8e5a52bbe28d86f760259ea4d3c2b73a493d8178d21.pdf |
| 35 | 99e9ee75a8 | 5,086,840 | 2 | 5,086,840 | jobs/astra-source-retention/output/pdf/cea5509545c9944ce10a384a19d76e78abf6bbec0c66c2eff53880e09d06732d.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/cea5509545c9944ce10a384a19d76e78abf6bbec0c66c2eff53880e09d06732d.pdf |
| 36 | 6d9ae9a0d7 | 4,837,140 | 2 | 4,837,140 | jobs/astra-source-retention/output/pdf/70e12a69f6248188bf6929cb691c3aee7efc9d3965a1cb1741080e66252ffdf2.pdf ; research/excavator/codex-continuous-2026-10-24/comparison/legacy-10016/source-cache/ladder/blobs/70/70e12a69f6248188bf6929cb691c3aee7efc9d3965a1cb1741080e66252ffdf2.pdf |
| 37 | bbacf5e9c1 | 3,571,745 | 2 | 3,571,745 | jobs/astra-source-retention/output/pdf/5a2608ad32e9f53d3365577ac32c5f277ed9af90e2dc8ddca7d58fbc0ab7f4a1.pdf ; research/excavator/codex-continuous-2026-10-24/b03/source-cache/ladder/blobs/5a/5a2608ad32e9f53d3365577ac32c5f277ed9af90e2dc8ddca7d58fbc0ab7f4a1.pdf |
| 38 | 63af3c12ed | 1,414,993 | 3 | 2,829,986 | jobs/astra-source-retention/output/pdf/d46eb8e8384da8352c9619cf2c5df1c534e0b20dd36b68317c76bf5b612718d8.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/d46eb8e8384da8352c9619cf2c5df1c534e0b20dd36b68317c76bf5b612718d8.pdf ; research/excavator/machiavelli-modern-undecided-20261105/continuation-20261105/acquisition-v4/pdf-run-1/pdf/d46eb8e8384da8352c9619cf2c5df1c534e0b20dd36b68317c76bf5b612718d8.pdf |
| 39 | 936ffcfba6 | 694,449 | 5 | 2,777,796 | ProQuest Pre-1937 Orders/PT1-1897-EO-99 (1).pdf ; ProQuest Pre-1937 Orders/PT1-1897-EO-99 (2).pdf ; ProQuest Pre-1937 Orders/PT1-1897-EO-99 (3).pdf ; (+2 more) |
| 40 | 865538e26c | 2,608,121 | 2 | 2,608,121 | jobs/astra-source-retention/output/pdf/98bd563c74a955ee0518c99c94ffea818963210588aaa05df6a8d349212f61cb.pdf ; research/excavator/codex-continuous-2026-10-24/b03/source-cache/ladder/blobs/98/98bd563c74a955ee0518c99c94ffea818963210588aaa05df6a8d349212f61cb.pdf |
| 41 | bffe0242aa | 2,469,827 | 2 | 2,469,827 | jobs/astra-source-retention/output/pdf/3b49dbad0980b7e745d8d4360a340aa073859b4580b0c3243142a5ecfafb3fd1.pdf ; research/excavator/astra-production-2026-10-24/b02/sources/3b49dbad0980b7e745d8d4360a340aa073859b4580b0c3243142a5ecfafb3fd1.pdf |
| 42 | 324dc63356 | 1,063,772 | 3 | 2,127,544 | jobs/astra-source-retention/output/pdf/958927407bf09446e5e678a91dd91b633d8bec4a4519900c422532e48d0bbf94.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/958927407bf09446e5e678a91dd91b633d8bec4a4519900c422532e48d0bbf94.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition/output/pdf/958927407bf09446e5e678a91dd91b633d8bec4a4519900c422532e48d0bbf94.pdf |
| 43 | 87c666d057 | 1,003,672 | 3 | 2,007,344 | ProQuest Pre-1937 Orders/PT1-1890-EO-28 (1).pdf ; ProQuest Pre-1937 Orders/PT1-1890-EO-28.pdf ; research/pre-1937-sources/ProQuest Pre-1937 Orders/PT1-1890-EO-28.pdf |
| 44 | 0591546d03 | 879,729 | 3 | 1,759,458 | jobs/astra-source-retention/output/pdf/2ff7480200648a0fb6525a90d888296a73434f7f13cded9fe733457bc55a426d.pdf ; research/excavator/astra-production-2026-10-24/b01/acquisition-raw-recovery/output/pdf/2ff7480200648a0fb6525a90d888296a73434f7f13cded9fe733457bc55a426d.pdf ; research/excavator/astra-production-2026-10-24/b02/acquisition-v1/pdf/2ff7480200648a0fb6525a90d888296a73434f7f13cded9fe733457bc55a426d.pdf |
| 45 | d6973cc08c | 694,633 | 3 | 1,389,266 | ProQuest Pre-1937 Orders/PT1-1884-EO-23 (1).pdf ; ProQuest Pre-1937 Orders/PT1-1884-EO-23.pdf ; research/pre-1937-sources/ProQuest Pre-1937 Orders/PT1-1884-EO-23.pdf |
| 46 | 84e21fc223 | 569,765 | 3 | 1,139,530 | ProQuest Pre-1937 Orders/PT1-1874-EO-13 (1).pdf ; ProQuest Pre-1937 Orders/PT1-1874-EO-13.pdf ; research/pre-1937-sources/ProQuest Pre-1937 Orders/PT1-1874-EO-13.pdf |
| 47 | 55debaa665 | 555,282 | 3 | 1,110,564 | ProQuest Pre-1937 Orders/PT1-1868-EO-7 (1).pdf ; ProQuest Pre-1937 Orders/PT1-1868-EO-7.pdf ; research/pre-1937-sources/ProQuest Pre-1937 Orders/PT1-1868-EO-7.pdf |
| 48 | eea3c2b51d | 452,495 | 3 | 904,990 | ProQuest Pre-1937 Orders/1873-EO-10 (1).pdf ; ProQuest Pre-1937 Orders/1873-EO-10.pdf ; research/pre-1937-sources/ProQuest Pre-1937 Orders/1873-EO-10.pdf |
| 49 | da1b015825 | 320,318 | 3 | 640,636 | jobs/astra-source-retention/output/pdf/2fdd6fb850d32b1314b90c2cff693fe7159b5fd16eb84263e957c13652eabfe0.pdf ; research/excavator/codex-continuous-2026-10-24/b01/source-cache/ladder/blobs/2f/2fdd6fb850d32b1314b90c2cff693fe7159b5fd16eb84263e957c13652eabfe0.pdf ; research/excavator/machiavelli-modern-undecided-20261105/continuation-20261105/acquisition-v1/pdf-run-2/pdf/2fdd6fb850d32b1314b90c2cff693fe7159b5fd16eb84263e957c13652eabfe0.pdf |
| 50 | d6a08dbd8d | 640,301 | 2 | 640,301 | ProQuest Pre-1937 Orders/PT1-1904-EO-251 (1).pdf ; ProQuest Pre-1937 Orders/PT1-1904-EO-251.pdf |

## 3. Constraint: cited paths must stay resolvable
Frozen workpapers (`research/production/**`, `research/excavator/**` are `-text` and "cited by exact SHA-256" per `.gitattributes`) cite these paths. Moving or deleting any file in `research/excavator/` or `jobs/astra-source-retention/` would break citations. I did not check which duplicate paths are actually cited; that must be done before any change (grep of all frozen workpapers for each path in the CSV: not done here).
Rule for any option: every currently cited path must still resolve to the same SHA-256 bytes, and the frozen workpapers themselves must not be edited.

## 4. Options
**(a) Git LFS for new PDFs only.** Add `*.pdf filter=lfs` (today only `releases/**/*.pdf` is LFS, 9 files).
- Pro: no existing path changes; new PDFs leave git proper; small change to `.gitattributes`.
- Con: does nothing for the 1.41 GB already present; LFS deduplicates by sha256 so new identical copies cost storage once, but checkouts still materialize every path; adds LFS bandwidth/quota and breaks `-text`-pinned workflows and Actions that read PDFs by blob (`git cat-file`) because they would see pointers. Pointer vs bytes ambiguity is a risk for "exact SHA-256" citations (the cited hash is of the PDF bytes, not the pointer).

**(b) Separate evidence data repo, content-addressed (`sha256/ab/cd/<sha256>.pdf`) plus manifest mapping every cited path to its hash.**
- Pro: one copy per hash by construction; solves new and old duplication; checkout of this repo shrinks by up to 4.5 GB.
- Con: largest migration; two-repo coordination (the project says GitHub is the evidence base, and tests/Actions would need a second checkout); old history still holds the bytes (no pack saving unless rewritten, which must not be done because commit SHAs are cited); every consumer needs a resolver.
- Needs: manifest `path,blob,sha256,size,cited_by` generated from the tree at a pinned commit; a resolver script `resolve(path)->bytes` that first tries the repo path, then the manifest and the data repo, and verifies sha256; a CI check that every cited path resolves and hashes match.

**(c) Leave history and existing files alone; stop new duplicates with a check.**
- Pro: zero risk to citations; cheap; the large pile (96% in astra-retention vs excavator) is a one-time event from retention jobs copying acquisition outputs.
- Con: 1.41 GB of redundancy stays in every checkout.
- Check: a PR/pre-commit script (`git ls-files -s` blob ids of `*.pdf` in the diff vs base; fail if a new path's blob id already exists at another path, unless listed in an allowlist file with a reason). Also have `jobs/astra-source-retention` write a manifest entry instead of a second copy when the hash is already tracked.

## 5. Recommendation
Do (c) now (days of work, no risk), and prepare (b) in its non-destructive half only: generate the manifest and resolver and a CI check, but leave all originals in place. Defer any removal until the owner sees (i) the cited-path scan result and (ii) a decision on whether the checkout size justifies a second repo. Do not choose (a) alone: it does not touch the existing 1.41 GB and the LFS pointer ambiguity conflicts with SHA-256-pinned evidence.
If the owner later wants to reclaim checkout space, the lowest-risk move is only for the `jobs/astra-source-retention/output/pdf/` vs `research/excavator/` overlap (1.36 GB): keep the excavator originals (frozen, cited) and replace the retention copies with the manifest + resolver, after confirming no workpaper cites the retention paths. Alternative: symlinks (git tracks them as blobs, but they break on Windows checkouts, which `.gitattributes` says matter here), so prefer manifest + resolver.

## 6. Limits of this measurement
- Only files whose path ends in `.pdf` were counted. `research/excavator/**/source-cache/ladder/blobs/<xx>/` entries appear to include PDFs under their `.pdf` names, but extensionless PDFs, zipped PDFs and `releases/**` LFS objects (23 LFS entries per `git lfs ls-files`) were not measured.
- Sizes are uncompressed blob sizes, not pack sizes.
- Git blob identity is SHA-1; the repository's own sha256 citations were not verified.
- Same-content PDFs with different bytes (re-downloads, re-saves) are not detected; only exact duplicates.
