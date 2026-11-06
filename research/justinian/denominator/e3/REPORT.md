# E3 report: EO 8969 / EO 10276 dates, EO:7933a id, 18 census EO:UN ids
Worker: Sonnet 5.5. Read-only on the repository. Output only under this directory.

## (a) Wrong dates: confirmed, single root cause
* EO 8969 is wrongly dated **1946-12-11** (correct 1941-12-11). EO 10276 is wrongly dated **1961-07-31** (correct 1951-07-31).
  Its publication date is also wrong: 1961-08-02, correct 1951-08-02.
* **Root cause:** `jobs/later-events/output/CATALOG_INDEX.csv` line 1449 (EO:8969) and line 2781 (EO:10276).
  Neighbouring rows are correct: EO:8967 on line 1447 reads 1941-12-11, and EO:10271 reads 1951-07-07.
  The OFR-catalog row's own citation "16 FR 7535" is a 1951 volume, which contradicts its 1961 dates.
* **How it spreads:** `jobs/_lib/eo_identity.py` sets `OFR_CATALOG = jobs/later-events/output/CATALOG_INDEX.csv` (line 23).
  `load_dates()` reads it first (lines 224-225) and keeps the first date seen; a full date is replaced only by a full date that agrees on the year.
  I ran `load_dates()` and confirmed:
  `EO:8969 -> 1946-12-11 (date_source ofr_catalog)` and `EO:10276 -> 1961-07-31 (ofr_catalog)`.
  Every consumer of `load_dates` inherits the error. The `date_source` strings and the field names in the rows point at these consumers:
  * domesday-register `REGISTER.csv` lines 9463 and 10795
  * lachmann `RESIDUAL.csv` line 5866
  * lewis-originals `ROUTES.csv` line 5030
  * fr-originals `NOT_FOUND.csv` line 312 (both copies; EO 8969 only)
  * namier `EDGES.csv` line 374 and `NAME_LINKS.jsonl`
  * `research/mabillon/frame/FRAME.csv` line 5908 (date and year both 1946)
  * the claim-kit jsonl outputs (TEXT_REPRESENTATIONS, OWN_TERMS, STATUS_LEADS, CLAUSES, TEXT_CLAUSES, OVERLAY_INPUTS)
  * norton `QUESTION_LEADS.jsonl`
  * `research/readiness/claims/claude-2026-11-04-tribonian-c03.jsonl`
  * `jobs/_attempts/lewis-originals/.../ROUTES.csv` (a historical snapshot)
  The consumer of each file is inferred from `date_source` and field names; I did not trace every import.
* **Tables that are correct** (no fix needed):
  * stage15 census: EO:8969 year_group 1941 at line 13789, EO:10276 year_group 1951 at line 312.
  * `jobs/app-executive-orders/output/INDEX.csv`: 1941-12-11 at line 5493, 1951-07-31 at line 4164.
  * `research/stage12/QA/ADVERSARIAL_TARGETED_CHAIN_PANEL.csv` lines 5-6.
  * `research/stage12/QA/REMAINING_YEAR_MISMATCHES.md` line 12 already records these as repairs.
  * Dates such as 1953-07-31 and 1958-07-01 on other EO:10276 rows are the dates of *other* orders that cite EO 10276, so they are not errors.
* **Official support for the correct dates:**
  * EO 10276: HELD official Federal Register printing.
    `jobs/fr-originals/data/full_run/texts/EO_10276.txt` is 16 FR 7535, Vol. 16 No. 149.
    Line 392 reads "Thursday , August 2, 1951 FEDERAL REGISTER 7537".
    Lines 530-533 read "The White House, July 31, 1951, 7:01 p. m., e. d. t. [F. R. Doc. 51-8977; Filed, Aug. 1, 1951; 10:08 a. m.]".
    This is an OCR text layer, not authenticated, so check the PDF.
  * EO 8969: **no held official printing exists.**
    `jobs/fr-originals/output/NOT_FOUND.csv` line 312 records the OFR index as "not received for publication" (an OFR catalog statement).
    I grepped the fr-originals, ofr-compilations, mabillon-held-printings and hathi-gpo-orders outputs and found no EO 8969 fragment.
    The only text held is the American Presidency Project transcription (a mirror, not an official printing):
    `jobs/app-executive-orders/output/texts/executive-order-8969-exemption-joshua-g-hefty-from-compulsory-retirement-for-age.txt`.
    Its signature block (lines 3-5) reads "FRANKLIN D ROOSEVELT / The White House, / December 11, 1941."
    The text names EO 8637 of January 14, 1941, which fits a 1941 order.
    The 1941 date is also corroborated by the APP index and the Stage 12 panel (see above).
    Do not call EO 8969's 1941 date official-printing-confirmed.
* `DATE_FIXES.csv`: 64 data rows (EO 8969: 24, EO 10276: 40), plus one header row. The `official_*` columns hold the quote above.
  Locators are physical line numbers for CSV and JSONL; JSON-field rows give the field path.

## (b) EO:7933a id
* The census holds `EO:7933a` at `research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv` line 12633; `EO:7933` is on line 12632.
  The census contains 524 uppercase-suffix ids (EO:nnnnA) and exactly 1 lowercase-suffix id (this one).
* The code's canonical form is uppercase. `canon_id` and `parse_eo_id` in `eo_identity.py` uppercase every suffix.
  `jobs/clark-discovery/test_clark.py` line 242 asserts `canon_id(*parse_eo_id("EO:7933a")) == "EO:7933A"`.
  `jobs/source-ladder/ofr_index.py` lines 39 and 53 note "the universe spells 7933a in lower case".
  The OFR catalog (`CATALOG_INDEX.csv` line 408) and the APP index (`INDEX.csv` line 6533) already use `EO:7933A`.
* **Collision to handle:** Stage 12-14 treat `EO:7933A` and `EO:7933a` as the same 1938-07-14 instrument. Evidence:
  `research/stage13/CENSUS/IDENTITY_COLLISION_RISK_REGISTER.csv` line 2, `research/stage12/SCRIPTS/build_stage12.py` line 18, `RELEASE_METRICS.json`, `OVERLAY_CHANGE_LOG.jsonl`.
  The 14,972 denominator keeps only `EO:7933a`; the `EO:7933A` alias row is excluded.
  Renaming the census id to `EO:7933A` therefore also needs the alias `{'EO:7933A':'EO:7933a'}` dropped or reversed.
  This applies in `build_stage12.py` line 18, `verify_stage12.py` lines 24-25, `verify_stage14.py` lines 23-25 and `build_official_source_manifest.py` line 28.
  The 14,972 count stays unchanged.
* `ID_NORMALIZATION.csv` lists every file using lowercase `7933a`. It has 289 files and 6 file names (EO_7933a.json / .txt style), plus a `role` column.
  A change would be: `EO:7933a -> EO:7933A` and `EO_7933a -> EO_7933A`. Nothing was changed.
  Plan:
  * Fix the primary census row (line 12633) and upstream builders.
  * Regenerate the generated outputs rather than hand-editing them.
  * Update the test fixtures `test_clark.py`, `test_eo_refs.py` (lines 29, 51, 54) and `test_fetch_ladder.py`. `test_clark.py` line 151 explicitly asserts the lowercase quirk.
  * Leave `jobs/_attempts` snapshots alone.
* 11 occurrences are bare `7933a` (no prefix) in the code and tests above.

## (c) The 18 `EO:UN:executive-orders-NN:row:N` census ids
* Exactly **18** exist in the census (lines 14955-14972); the "19" in the audit is not supported.
* **Source:** the NARA 1989 codification tables (`archives.gov/federal-register/codification/executive-orders-01/02/10.html`), one row each.
  Rows are in `research/stage13/CENSUS/NARA_UNNUMBERED_EDITORIAL_DATES_18.csv` and `jobs/ofr-codification-1989/output/UNNUMBERED_ROWS.csv`.
  The second table also has the disposition and amendment text and the PDF page.
  The NARA CSV's row numbers (the census `row:N`) differ from the OFR table_row for some rows: census `row:205` corresponds to OFR table_row 204.
  Rows `row:12` and `row:71` (both Aug. 8, 1914) are flagged `ambiguous_same_date` in `UNNUMBERED_ROWS.csv`, so the disposition text cannot be assigned to one of them with certainty.
* **The census year 'Unknown date' is stale, not a real gap.** All 18 already carry a full reference date from the NARA row.
  `jobs/early-ranger-year-reconcile/output/STAGE15_TO_STAGE17_YEAR_CHANGES.csv` already assigns Stage 17 years to them.
  The date is in the NARA source row itself; BLM/PLO tables add no dates.
* **Matching against `jobs/shepard-citations/output/PLO_TABLE.csv`** (7,866 rows; first PLO signed 1942-06-20, so no pre-1942 order can be one of them):
  * PLO dates equal the unnumbered order's date only by coincidence. `row:31` (1954-04-30) coincides with PLO:960, and `row:134` (1955-08-23) with PLO:1209 and PLO:1210. These are different instruments and are rejected, so confidence is none.
  * Seven rows are cited by date inside later PLO subjects or held FR texts.
    * **strong (1):** `row:4` (July 21, 1871). PLO:1359 (line 1359) and PLO:5585 (line 5573) say "revoking in part EO of July 21, 1871", and the shepard job already links them (EDGES lines 7611-7612). The strength is for date and identity of the cited order; there is still no EO number.
    * **weak (6):** `row:2` (PLO:2224, 2877, 5234, 7585); `row:12` and `row:71` (PLO:931); `row:65` (PLO:3102, 6487); `row:102` (PLO:7303); `row:205` (the held FR text of EO 8507 quotes "Executive Order of November 9, 1923"; shepard `UNRESOLVED.csv` lines 552/554/1720).
      These cite only the date, so identity rests on date equality.
      Same-date census orders exist for rows 65, 102 and 205, and the pair 12/71 shares a date.
      Same-date numbered EOs (leads, not matches) are EO 1881/1882/1883, EO 2605A and EO 3924; row 12/71's date also matches EO 2016/2017 (`same_date_numbered.json`).
  * **none (11):** `row:1, 3, 7, 8, 9, 10, 11, 61` of table 01, `table-02 row:107`, and `table-10 row:31` and `row:134`.
* **No EO number is established for any of the 18.** The `eo_number` column is "not found" throughout.
  Dispositions such as "Revoked by EO 9830" give the *later* order's number, not the unnumbered order's own.
* **Disposition text stays raw.** The OCR joins words ("Revokedby", "Publiclands").
* `UN_RESOLUTION.csv`: 18 rows (1 strong, 6 weak, 11 none).
  The `date` column is the NARA reference date, with the caveat above.
  The conclusion is that the census date field can be filled from the NARA reference dates, which is a date-field repair, not an identity resolution.
  Confidence in the table is about identity of the cited order, not about the date's origin.

## Exceptions / limits
* The date scan covered CSV/JSONL files found by grep for the numbers or ids (342 files) and the `load_dates` loaders. A table that spells the order differently could be missed.
* Locators for CSV rows are the physical line of the record start; JSONL rows use the line number.
* I did not open the NARA HTML pages (only `executive-orders-02.html` is held, under hathi-gpo-orders). The NARA row text is as extracted by the project's own tables.
* Nothing in the repository was modified.

## Reproduce
```
cd /home/user/Executive-Orders
O=<this directory>
grep -rIlE --include=*.csv --include=*.jsonl -E '(EO[:-]|(^|,|")0*)(8969|10276)(,|"|$)' research jobs releases > $O/scripts/files.txt
python3 -I $O/scripts/scan_dates.py < $O/scripts/files.txt > $O/scripts/scan_raw.jsonl
python3 -I $O/scripts/make_date_fixes.py $O/scripts/files.txt $O/DATE_FIXES.csv   # then add the line-2781 publication_date row by hand (see report)
python3 -I $O/scripts/check_load_dates.py
python3 -I $O/scripts/make_id_norm.py $O/ID_NORMALIZATION.csv
python3 -I $O/scripts/same_date_numbered.py $O/scripts/same_date_numbered.json
python3 -I $O/scripts/make_un_resolution.py $O/UN_RESOLUTION.csv $O/scripts/same_date_numbered.json
python3 -I $O/scripts/probe_plo.py
```
