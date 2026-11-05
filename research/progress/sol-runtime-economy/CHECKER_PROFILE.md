# Bounded checker source-index profile

Baseline `2c85459cf38b08dc1eea6d7c84a74268fa45c28e`; configured worker `gpt-6.1-terra`, high reasoning. Token and cash usage were not exposed. No commit or publication was made.

The checker previously kept all parsed JSON dictionaries for one source file while building its index. The candidate keeps only the eight fields the adapter consumes in compact tuples, releasing each as it processes the file after EOF. It retains the shared JSONL parser and list wrapper; custody checks and index additions still begin after the entire file closes. The independent checker and completion input pinning remain separate.

The probe invokes `sources.build_index` twice in each fresh process. Wall time covers index construction, rchar is the per-build `/proc/self/io` read count, and RSS is the process high-water mark. Each baseline arm ran first, followed by the candidate, once per fixture.

| Fixture | Baseline seconds (two builds) | Candidate seconds | Baseline peak RSS | Candidate peak RSS | rchar per build |
|---|---|---|---:|---:|---:|
| Synthetic: 100,000 records, 22,477,792-byte source file | 4.182, 3.417 | 1.950, 2.026 | 190,372 KiB | 127,092 KiB | ~22.48 MB |
| Retained sparse checkout: 20 source files, 51,595 source lines / 59,192,917 bytes, plus materialized context | 8.623, 8.352 | 6.199, 5.702 | 163,252 KiB | 152,860 KiB | ~60.99 MB |

The synthetic fixture produced 100,000 entries in both arms and the same full HeldCopy field/order digest `0c018dd35dbbcdcb3fa7e0acce6964b2d6396585a0ea8fddb80f2da1a67664e1`. The retained fixture produced 87,855 entries and digest `d07104852a68b4f80018399d7da1f0d91e1d8ab0a0e420fc306f8fb8edb9c8c1` in both arms. Notes matched. These are single ordered measurements; filesystem cache and machine effects can affect timings. The retained checkout lacks some source inventories and the Opus text pack, so its numbers are not full-corpus estimates. Index-field digest and notes are not a substitute for full checker receipts.

Six focused regression tests pass: malformed and non-object rows, duplicates and URL order, path/custody fields, list-wrapper malformed counts, mid-read OSError and UnicodeError without partial index additions, index-add failure after partial mutation with a later valid row, and a file appearing on input close. Seven existing source-book and replica tests also passed on the final compact-row revision. Independent review identified the prior candidate's custody timing defect; the rejected hypothesis and evidence are retained in `experiments/REJECTED_EARLY_STREAMING.md`.

Source SHA256 `7bb63fdb6f154ee67a568bc690a3d3c081f3d6d39137ec7bb55b7d551695679b`; focused test `d38cef189fa6ccd2d2d7d451a7c82d55d92f2745e35ce6d5c7666778e327594f`; probe `5516f04e47736c00d3774f2861d48737906d056e0a84a5ad421c25548cd63715`. The controller separately runs the ordinary retained-claim checker replay.
