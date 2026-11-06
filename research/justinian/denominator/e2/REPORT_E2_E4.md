# E2 + E4 seeds: report
Worker: Sonnet 5.5, read-only on the repo. Outputs: `ADMIT_LIST.csv`, `UNNUMBERED_SEED.csv`, `scripts/`.
Reproduce: `python3 -I scripts/e2_admit_list.py <OUT>` and `python3 -I scripts/e4_unnumbered_seed.py <OUT>` (needs /home/user/Executive-Orders on disk).

## E2 ADMIT_LIST.csv (61 rows, 39 distinct instruments)
- **a (30 rows, ADM-a-NN)**: every row of `research/niebuhr/ADMISSION_QUEUE.csv`. None of the 30 ids is in `research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv` (14,972 ids).
  - 26 have a held official printing (OFR 1974 Hoover vol. II, PDF `releases/source_books/OFR_1974_Hoover_..._uc1.c025504761.pdf`, with PDF and printed page spans). All dates agree with APP.
  - 4 have "none held": EO:5151A, 6585, 7010F, 8606A (APP date only; an index/catalogue, not a printing). 5151A is listed only in Hoover v2 Table 2 (PDF p.699); 6585 is a dated reference in the 1989 codification (PDF p.692). Neither is the order's own printing.
- **b (27 rows, ADM-b-5853..5879)**: the June 1932 run. 22 not in census (all are also in group a: count once); 5 already census ids with blank `date_effective` (5857, 5860, 5865, 5866, 5869), so for them the task is a date fill, not an admission. Source naming per row: OFR Hoover v2 (`jobs/ofr-compilations/output/HOOVER_V2_ORDERS.csv`, text `jobs/ofr-compilations/output/texts/EO_58NN.txt`), APP `INDEX.csv` line, `jobs/clark-discovery/output/NUMBER_GAPS.csv` line, and later citing orders. Owner basis: A-20261021-1, answered by D-20261104-delegated-answers (admit as working identities flagged compiled-source-only, queued for Lewis, no authentication).
- **c (4 rows, ADM-c-*)**:
  - **27A**: cited as "27-A of September 4, 1890" by EO 399, 5658, 6247, 6680, 7298. Niebuhr resolves it (medium confidence, Wikisource secondary) to existing census EO:28. Held scan: ProQuest `PT1-1890-EO-28.pdf` pp.1-4 (on disk), but `EO_28.txt` OCR is unreadable, so a person must read it. The held OFR text of EO 5658 (PDF pp.176-177) names "27-A" but is not the order.
  - **130A**: not held. Only the WPA 1944 index (p.31, "130-A (no date)") and Wikisource-derived lists (1900-06-22). Census has 130B/C/D, not 130A.
  - **967A**: probably an OCR error for existing census EO:1967A (EO 3366's held text says "967-A, dated June 23, 1914"; WPA numbered p.184 has EO:1967A of June 23). Recommend alias, not admission. The ProQuest PDF `PT1-1914-EO-1967-A.pdf` is NOT on this checkout (18 PDFs only); only its text `texts/EO_1967A.txt`.
  - **2687A**: none held; only secondary Wikisource/Wikipedia lists (1917-08-21, Exports Administrative Board). Census has EO:2687 only. Niebuhr notes 2686-A may also be missing.

## E4 UNNUMBERED_SEED.csv (1,562 rows, one per WPA row)
- Source `jobs/x1-class-engine/data/WPA_UNNUMBERED_ENTRIES.csv` (seq 1..1562; 1562 rows, not ~1,562 approx). `seed_id` = `CU:<seq>`. Date is ISO built from the year column plus the month/day text (862 rows have no month/day, so year or year-month only). Text is whitespace-normalised and cut to 300 characters.
- Cluster file used: `jobs/census-completeness/output/CLUSTERS.csv` (1,476 clusters, pre-1900 only). Join: WPA seq N = mention `LORD:U:NNNN` (verified: the label equals the summary on all 1,158 mentions). The cluster file has 1,476 clusters, not ~1,420.
  - **1,158 rows have a cluster id**. **404 rows are 1900-1913 and have none** ("not found"). (1,158 + 404 = 1,562.)
- Census linkage:
  - Firm WPA-row to unnumbered-census-id joins: **0 rows**. The only Lord-derived unnumbered census id is `EO:UNN:LORD1944:p1:1863-03-10` (census line 14973); no WPA row has year 1863 and date March 10 (none found). The other 18 EO:UN ids are NARA codification rows (`research/stage13/CENSUS/NARA_UNNUMBERED_EDITORIAL_DATES_18.csv`) with no title or text.
  - Column `census_date_only_leads`: 7 rows share a day-precise date with one of those EO:UN ids (CU:112, 1041, 1094, 1095, 1382, 1404, 1473). **A date alone is only a lead, not a match.**
  - Column `census_ids_linked` (numbered census ids): **68 rows** sit in 11 completeness clusters that also contain WPA-numbered EO ids (e.g. EO:8, 18, 22|23, 26, 68; larger clusters list many ids). These are cluster-level, many-to-many links made by citation or by date plus shared word; not row-level identity.
  - So: **68 rows correspond (cluster-level, numbered ids) to a census id; 1,494 do not**. By unnumbered-id join: 0 correspond, 1,562 do not.

## Exceptions / open problems
- `research/progress/...` and other completeness files not used; no separate 1,420-cluster file was found beyond the 1,476-cluster `CLUSTERS.csv`.
- Group a/b overlap (22) is deliberate; distinct count is 39.
- ProQuest PDFs for 1967A, 3366 and 130C are named in `jobs/pinakes-proquest-ingest/output/INVENTORY.csv` but absent from this checkout, so the "page a person must check" is given by file name and page count only.
- Page spans of EO 5855 (PDF 372-404) and 5874 (450-493) are long; flagged for a person to confirm they are one order.
- No file in the repo was modified.
