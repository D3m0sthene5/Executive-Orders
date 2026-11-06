# Denominator repairs E1–E4: prepared for the owner, nothing applied (COUNT-CHANGING)

Justinian, 2026-11-06. Each part is a list a person checks against a held official page before anything changes
the census. **The census (14,972), the codebook and every status are unchanged.** Each part was produced by a
bounded Sonnet worker (`research/justinian/WORKERS.csv` in the Kean PR). I checked the key claims myself; those
checks are marked "verified" below.

## E1: the "46 missing integers" (`e1/`)

The audit's claim is wrong as stated. Over integers 1–8030:

- **46 numbers are missing from the census.** They match exactly the 46 in `jobs/clark-discovery/output/NUMBER_GAPS.csv`.
- **75 numbers are missing from the WPA parse.** 33 of those are already in the census.

The 1944 WPA parser (`wpa.py`, archived under `research/progress/branch-recovery-2026-10-29/legacy/wpa-lists/`)
reproduces the committed CSV exactly. It misses entries for these reasons:

- multi-number heads such as "36, 37:" and "43-46:" (17);
- a second entry starting mid-line (8);
- a sequence guard tripped by a misread neighbour (7);
- OCR-misread head digits, inferred from sequence and date (12);
- a starred head (2), an odd head (1), a head with no colon (1);
- **EO 5853–5879: the scan skips printed folios 486–487**, two missing pages (27 numbers). Verified: scan page 502 ends
  at folio [485] (EO 5852), and page 503 starts at EO 5880 with folio [488].

`RECOVERED_IDENTITIES.csv` lists 75 rows: 48 located in the OCR text with their snippet, and 27 that need the
missing pages. Only 4 have a held official printing (5659, 6117, 6171, 7586); the rest say "none found".

WPA lists **2103, 2703, 3493 and 3733**, but the census does not. They are the only four such numbers. No held
printing names them, and no documented exclusion explains their absence (`WPA_ONLY_CENSUS_ABSENT.csv`).

## E2: admit list (`e2/ADMIT_LIST.csv`, 61 rows, 39 distinct instruments)

- **The 30 orders of `research/niebuhr/ADMISSION_QUEUE.csv`.** None is in the census. 26 have a held OFR 1974 Hoover
  vol. II page span; 4 have none (5151A, 6585, 7010F, 8606A).
- **The June 1932 run, EO 5853–5879** (A-20261021-1, answered yes on 11-04: admit as compiled-source-only working
  identities). 22 are not in the census; they are the same 22 as in the queue, so count them once. The other 5 are
  in the census with a blank date, so they need a date fill, not an admission.
- **The four lettered ids:**
  - 27A resolves (medium confidence) to existing EO:28. A person must read its ProQuest scan.
  - 130A: no printing is held, only the WPA index.
  - 967A is probably an OCR misreading of existing EO:1967A. Alias it; do not admit it.
  - 2687A: only secondary lists name it.

Each row names the held official page a person must check, or says "none held".

## E3: dates, the lowercase id, and the 18 `EO:UN` ids (`e3/`)

- **EO 8969 is dated 1946-12-11; it is 1941-12-11. EO 10276 is dated 1961-07-31; it is 1951-07-31.**
  - Root cause: lines 1449 and 2781 of `jobs/later-events/output/CATALOG_INDEX.csv`. `jobs/_lib/eo_identity.load_dates()`
    reads that file first and keeps its value, so 64 rows in its consumers repeat the error (`DATE_FIXES.csv`).
  - Fix the catalog rows at their source (the later-events catalog parser) and regenerate the consumers.
  - EO 10276 has a held FR printing (16 FR 7535; "The White House, July 31, 1951"). EO 8969 has no held official
    printing, only the APP text ("December 11, 1941"), so its correct date is corroborated, not officially confirmed.
- **`EO:7933a`** is the only lowercase-suffix id among 525 lettered ids. The code already treats `EO:7933A` as the
  canonical form. Renaming the census row also requires dropping the Stage 12–14 alias
  `{'EO:7933A': 'EO:7933a'}`. `ID_NORMALIZATION.csv` lists all 289 files that use it.
- **18 `EO:UN:...:row:N` ids** (not 19). All come from the NARA 1989 codification tables, and every one already has
  a full reference date in its NARA row. The census's "Unknown date" is therefore stale: this is a date-field repair,
  not an identity resolution.
  - Against `PLO_TABLE.csv`: 1 strong citation link (row:4, the EO of July 21, 1871, cited by PLO 1359 and 5585),
    6 weak links, and 11 with no link.
  - No EO number is established for any of the 18.

## E4: catalogued unnumbered series (`e4/UNNUMBERED_SEED.csv`)

The seed has one row per Lord 1943 unnumbered entry: 1,562 rows, `seed_id CU:<seq>`.

- 1,158 rows join the census-completeness clusters (`jobs/census-completeness/output/CLUSTERS.csv`: 1,476 clusters,
  not 1,420, and pre-1900 only). The 404 rows dated 1900–1913 have no cluster.
- **0 rows join an unnumbered census id.** 68 rows share a cluster with a numbered census id; that is a
  many-to-many link, not an identity.

**Not done in this PR:**

- adding the `catalogued_unnumbered` identity class to the census;
- printing two denominators wherever a denominator appears.

Both change the census and every report, so they need the owner's ruling first (Kean A-20261106-justinian-e4).
Proposed: report "numbered series: 14,389 base numbers in the census, 46 gaps" and "catalogued unnumbered
series: 1,562 Lord entries, 18 in the census" side by side. Then point Clark and census-candidates at the
1,494 unlinked rows instead of open-ended search.

## What the owner decides (Kean asks)

- A-20261105-niebuhr-admit (open): admit the 30 queue orders after a person checks each page.
- A-20261106-justinian-e1e3: apply the E3 date fixes at the catalog source, rename `EO:7933a`, and fill the 18
  `EO:UN` dates. All are census or record changes.
- A-20261106-justinian-e4: adopt the `catalogued_unnumbered` class and the two-denominator reporting.
