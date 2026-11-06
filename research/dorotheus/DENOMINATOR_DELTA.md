# Denominator delta, 2026-11-06 (owner ruling R9, task B1)

Census `research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv`: **14,972 rows before, 14,998 after** (+26 admitted; 0 removed; 1 id renamed; 23 date fields filled).
Included in bibliography (counted): 14,972 -> 14,998. The file name keeps `14972` (frozen name, many readers); the 14,972 original rows are those whose class is not `admitted_numbered_2026_11_06`.

## Admitted (26) - each has a held official page (OFR 1974 Hoover vol. II)

Class `admitted_numbered_2026_11_06`, included=1, proxy=1, authentication fields `unadjudicated`, status `indeterminate`, date_source_type `ofr_1974_hoover_compilation`, date_effective = the printing's full ISO date. Full detail incl. SHA-256 and text path: `research/stage15/CENSUS/ADMISSIONS_2026-11-06.csv`.

| id | date | held official page |
|---|---|---|
| EO:5853 | 1932-06-03 | PDF pp. 371-371 (printed pp. 1142-1142) |
| EO:5854 | 1932-06-03 | PDF pp. 371-372 (printed pp. 1142-1143) |
| EO:5855 | 1932-06-06 | PDF pp. 372-404 (printed pp. 1143-1175) |
| EO:5856 | 1932-06-11 | PDF pp. 408-413 (printed pp. 1179-1184) |
| EO:5858 | 1932-06-17 | PDF pp. 415-416 (printed pp. 1186-1187) |
| EO:5859 | 1932-06-21 | PDF pp. 416-416 (printed pp. 1187-1187) |
| EO:5861 | 1932-06-23 | PDF pp. 430-430 (printed pp. 1201-1201) |
| EO:5862 | 1932-06-23 | PDF pp. 431-431 (printed pp. 1202-1202) |
| EO:5863 | 1932-06-23 | PDF pp. 431-432 (printed pp. 1202-1203) |
| EO:5864 | 1932-06-23 | PDF pp. 432-432 (printed pp. 1203-1203) |
| EO:5867 | 1932-06-28 | PDF pp. 441-441 (printed pp. 1212-1212) |
| EO:5868 | 1932-06-28 | PDF pp. 442-442 (printed pp. 1213-1213) |
| EO:5870 | 1932-06-30 | PDF pp. 446-446 (printed pp. 1217-1217) |
| EO:5871 | 1932-06-30 | PDF pp. 447-447 (printed pp. 1218-1218) |
| EO:5872 | 1932-06-30 | PDF pp. 447-449 (printed pp. 1218-1220) |
| EO:5873 | 1932-06-30 | PDF pp. 449-450 (printed pp. 1220-1221) |
| EO:5874 | 1932-06-30 | PDF pp. 450-493 (printed pp. 1221-1264) |
| EO:5875 | 1932-06-30 | PDF pp. 493-493 (printed pp. 1264-1264) |
| EO:5876 | 1932-06-30 | PDF pp. 494-496 (printed pp. 1265-1267) |
| EO:5877 | 1932-07-05 | PDF pp. 496-496 (printed pp. 1267-1267) |
| EO:5878 | 1932-07-06 | PDF pp. 497-497 (printed pp. 1268-1268) |
| EO:5879 | 1932-07-07 | PDF pp. 497-498 (printed pp. 1268-1269) |
| EO:5605A | 1931-04-21 | PDF pp. 54-54 (printed pp. 825-825) |
| EO:5638A | 1931-06-08 | PDF pp. 125-129 (printed pp. 896-900) |
| EO:5855A | 1932-06-06 | PDF pp. 404-408 (printed pp. 1175-1179) |
| EO:6005A | 1933-01-21 | PDF pp. 634-634 (printed pp. 1405-1405) |

The 22 June-July 1932 orders EO 5853-5879 (5853-5856, 5858, 5859, 5861-5864, 5867, 5868, 5870-5879) plus 5605A, 5638A, 5855A, 6005A. All 26 dates agree with `jobs/ofr-compilations/output/HOOVER_V2_ORDERS.csv` (asserted in the script). `held_official_sha256` is the sha256 of the OFR 1974 Hoover PDF; the PDF is a git-LFS pointer in checkouts, so the value is the pointer's `oid` (the real file's sha256), not a hash of the pointer.

## Candidates NOT admitted

| id | reason |
|---|---|
| EO:5151A | no held official page (E2: 'none held') |
| EO:6585 | no held official page |
| EO:7010F | no held official page |
| EO:8606A | no held official page |
| EO:130A | no held printing; WPA 1944 index only (inside the EO:130 row, p.31) |
| EO:2687A | no held printing; only secondary lists/Wikisource mirror name it |
| EO:27A | probably an alias of existing EO:28 (medium confidence); a person must read its ProQuest scan; recorded, not admitted |
| EO:967A | alias of existing EO:1967A (OCR misreading); recorded, not admitted |
| EO:2103, EO:2703, EO:3493, EO:3733 | listed by WPA 1944 but absent from the census; no held printing names them (E1 `WPA_ONLY_CENSUS_ABSENT.csv`); no held official page |
| E1 RECOVERED_IDENTITIES, 75 rows | none qualifies: 4 have a held official printing (5659, 6117, 6171, 7586) but are already in the census; the other 71 say 'none found'. The 46 integers missing from the census are the NUMBER_GAPS list; the admissions above are the only held-official-page identities among the E1/E2 inputs, so the rest of the gaps stay open |
| EO 5857, 5860, 5865, 5866, 5869 | already in census (blank date): date filled, not admitted |

130A, 2103, 2703, 2687A etc. remain census candidates in `jobs/domesday-register` (`CANDIDATES`) until a held page exists.

## Other census changes (same commit series)

* `EO:7933a` -> `EO:7933A` (1 census row).
* 18 `EO:UN:...:row:N` rows: `date_effective`/`year_group` filled from `research/stage13/CENSUS/NARA_UNNUMBERED_EDITORIAL_DATES_18.csv` (`reference_date`), `date_source_type` set to `nara_codification_1989_source_row`. Group for pre-1862 dates (1849, 1852, 1856) is `1862–1906`, as the census already does for 3 other pre-1862 rows.
* EO 5857, 5860, 5865, 5866, 5869: dates from the Hoover table (1932-06-16, -22, -27, -28, -30), `year_group` `1907–1936`, `date_source_type` `ofr_1974_hoover_compilation`.
* All fills are listed in `research/dorotheus/B1_REPORT.md`.

## Date fixes EO 8969 and EO 10276 - jobs that must re-run

The catalog row values come from the live Federal Register API page fetch (no committed source row exists), so the fix is an override table `jobs/later-events/CATALOG_DATE_CORRECTIONS.csv` applied in `later_events.build_index` (signing and publication dates). Generated outputs were NOT hand-edited. To propagate: re-run **later-events** first (rewrites CATALOG_INDEX.csv; also its EDGES/FRAGMENTS that use the acting-order date), then, as they read `jobs/_lib/eo_identity.load_dates()`: **domesday-register**, **lachmann**, **norton**, **namier**, **lewis-originals**, **claim-kit** (CLAUSES, TEXT_*, OWN_TERMS, STATUS_LEADS, OVERLAY_INPUTS), **fr-originals** (NOT_FOUND.csv). `research/mabillon/frame/FRAME.csv` and `research/readiness/claims/claude-2026-11-04-tribonian-c03.jsonl` (a claim file, untouched) also repeat 8969's wrong date and need the owner/their generators. Full consumer list: `e3/DATE_FIXES.csv` (64 rows) on branch `origin/claude/justinian-denominator`.

## `EO:7933a` residue (not changed)

Frozen/generated files still carry the lowercase form: research/stage12..stage16 scripts and QA outputs, `jobs/claim-kit/output` (e.g. `dossiers/EO_7933a.json`), `research/progress/DECIDED_CASE_COMPLETENESS_*.csv` (hash-pinned status baseline), `research/readiness/reviews/astra-2026-10-18/*`, plus 289 files in `ID_NORMALIZATION.csv`. No file under `research/readiness/claims/` uses `EO:7933a`. claim-kit now maps the historical id to `EO:7933A` through `population_contract.json` `id_aliases`.
