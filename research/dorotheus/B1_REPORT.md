# B1 report: denominator repairs (owner ruling R9)

Worker: Sonnet 5.5, branch `claude/dorotheus-b1`. Detail lists: `DENOMINATOR_DELTA.md` (ids, pages, not-admitted reasons, rerun list).

## Counts
* Census rows: **14,972 -> 14,998** (+26 admitted). Counted (included_in_bibliography=1): 14,972 -> 14,998.
* Renamed: 1 (`EO:7933a` -> `EO:7933A`). Date fields filled: 23 (18 `EO:UN`, 5 June-1932). Not admitted: 8 lettered/no-page ids + WPA-only 2103/2703/3493/3733 (see delta).
* domesday-register run locally on this worktree: REGISTER has 14,998 rows, includes all 26 (e.g. EO:5853, 5855A, 6005A), `EO:7933A`, no `EO:7933a`. No input change was needed (it reads the census).

## Files
* `research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv`: +26 rows, 7933 rename, 23 date fills (date_effective, year_group; date_source_type for the 23 filled rows). Existing columns only.
* `research/stage15/CENSUS/ADMISSIONS_2026-11-06.csv` (new, 26 rows; sha256 of file `1b0ed01b...bb5` is pinned in claim-kit's contract).
* `research/dorotheus/scripts/b1_admit.py` (new): reproducible script for the census edit and admissions file.
* `research/dorotheus/DENOMINATOR_DELTA.md`, this report.
* `jobs/later-events/CATALOG_DATE_CORRECTIONS.csv` (new: EO:8969 signing 1946->1941-12-11; EO:10276 signing 1961->1951-07-31 and publication 1961-08-02 -> 1951-08-02, each with evidence path and quote); `later_events.py` (`load_date_corrections`, `correct_record_dates`, applied in `build_index`, only while the value still equals the recorded wrong value); `test_later_events.py` (+4 tests). The catalog is a live API fetch, so there was no committed source row. Generated outputs untouched; rerun list in the delta.
* 7933a: `jobs/source-ladder/ofr_index.py`, `ladder_queue.py` (docstrings only; code was already case-tolerant), `test_fetch_ladder.py` (canonical case added, legacy lowercase kept), `jobs/clark-discovery/clark.py` (docstring), `test_clark.py`, `jobs/current-law/tests/test_eo_refs.py`. Frozen research/stage1x scripts, outputs and claims untouched; no claim file uses `EO:7933a`.
* Live 14,972 assumptions: `jobs/early-ranger-1862-1906/job.py` and `jobs/early-ranger-year-reconcile/job.py` count only rows not of class `admitted_numbered_2026_11_06` (comment cites R9); reconcile also maps `EO:7933A` back to the Stage 17 SQLite's `EO:7933a`. `jobs/claim-kit/population.py` + `population_contract.json`: the count/hash pin stays on the original 14,972 identities; new `admissions` (pinned file, 26) and `id_aliases` keys; statuses keyed by the historical `EO:7933a` are mapped to the census id. `test_review_regressions.py` expects 14,972 + 26; `test_population.py` +1 test. Other grep hits for 14972 are file-path constants or labels, not length checks (`claim-kit/build.py` `historical_baseline` label left as the historical value).

## Tests (all run in this worktree)
later-events (56+2 OK), source-ladder all files OK, clark-discovery 11 OK, domesday-register 3 OK, current-law discover 64 OK (1 skipped), claim-kit test_population 19 / test_review_regressions 11 / test_build 18 / test_assemble + test_excavate OK, `.github/scripts/test_pick_jobs.py` 23 OK (1 skipped). Other claim-kit test files all passed in a loop. The early-ranger jobs have no tests (py_compile only; not run: they need Stage 17 SQLite artifacts).

## Exceptions
* The OFR 1974 PDF is a git-LFS pointer here; `held_official_sha256` = LFS oid (sha256 of the real file), page cites come from the prepared inputs and `HOOVER_V2_ORDERS.csv`, not re-read from the PDF.
* date_effective for new/filled rows is a full ISO date while older rows hold a year; consumers parse both (domesday did).
* Admitted rows' `date_source_type` is `ofr_1974_hoover_compilation`; filled UN rows `nara_codification_1989_source_row`. Three pre-1862 UN dates sit in group `1862–1906` like three existing rows.
* E1 recovered rows: none admitted (4 with held printings already in census).
* Stale test failures seen in the sparse worktree were missing sparse paths, not code; fixed by sparse-adding dirs.
* Generated outputs (CATALOG_INDEX and its consumers, claim-kit output) are stale until the jobs re-run; claim-kit output still has `EO_7933a` dossier files.
