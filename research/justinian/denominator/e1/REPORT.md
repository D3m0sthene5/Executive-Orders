# E1 report: WPA numbered list vs census (computed 2026-11-06 on current files)

## Inputs actually used
- WPA parse: `jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv` (8,437 rows, 7,955 distinct integers, max 8030).
- Census: `research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv` (14,972 ids; 14,389 distinct base integers). Base = number with letter/`-N` suffix and `½` dropped.
- **Parser and raw OCR are not under jobs/x1-class-engine.** `SOURCE_PROVENANCE.json` points to the unmerged `wpa-lists` branch (commit 121ca07e, not in this clone). The exact blobs are archived at
  `research/progress/branch-recovery-2026-10-29/legacy/wpa-lists/jobs/wpa-lists/` : `wpa.py` (parser), `data/numbered_pages.jsonl` (695 pypdf OCR pages; sha256 7130c7ce… matches PROVENANCE.json).
  I imported that `wpa.py` read-only and confirmed `parse_numbered(pages)` reproduces the committed CSV exactly (8,437 rows, same ids, same text).
- "WPA page" below = the jsonl/CSV `page` index (scan page), not the printed folio (printed folio = scan page - 17 early in the book).

## (1) Cross-tab, integers 1..8030 (`WPA_CENSUS_CROSSTAB.csv`; per-integer file `WPA_CENSUS_PER_INTEGER.csv`)
| | in census | not in census |
|---|---|---|
| in WPA parse | 7,951 | 4 (2103, 2703, 3493, 3733) |
| not in WPA parse | 33 | 42 |

- Absent from WPA parse: **75** integers (not ~46).
- Absent from census (base number): **46** integers (42 + 4). Census also has bases above 8030 (8031..14435), irrelevant here.
- **The audit's "46" is the census-missing count, mislabelled as WPA-missing.** The 46 equal exactly the set in `jobs/clark-discovery/output/NUMBER_GAPS.csv` (all 46 present there; checked in the crosstab file).
- Page clusters in the audit are real but describe the WPA-parse misses: 22/23 (EO 36-53), 274/275 (3050-3054), 435/436 (5003-5005), 502/503 (5853-5879). Not all are "OCR page breaks" (see below).

## (2) The 75 WPA-parse misses (`RECOVERED_IDENTITIES.csv`, one row per integer)
Of 75: **48 located in the OCR text** (identity = number inferred/printed + date as printed + snippet), **27 not found** (EO 5853-5879).
Causes (the parser's `N_ENTRY` accepts only `N:` or `N-<letter>:` and a sequence guard `cur-5 <= num <= cur+60`):
| cause | n | numbers |
|---|---|---|
| multi-number / range head ("36, 37:", "40-42:", "43-46:", "47-49:", "51-53:") | 17 | 36-49, 51-53 (WPA p22-23) |
| starred head ("21 * :", "396 * : (no date)") | 2 | 21, 396 |
| odd head "92-92-3:" (printed as OCR'd; meaning ambiguous, may be 92 plus 92-1..92-3) | 1 | 92 (p27, Nov. 2) |
| two entries on one OCR line, second head mid-line | 8 | 106, 913, 1486, 2104, 2539, 3494, 4866, 6117 |
| head has no colon ("6171 June 15") | 1 | 6171 |
| plain readable head rejected by sequence guard after a misread neighbour head | 7 | 3051-3054, 5003-5005 |
| head digit misread by OCR; number INFERRED by sequence+date (printed digits differ) | 12 | 569 ("669"), 1601 ("l501"), 2093 ("2003"), 2159 ("2150"), 3050 ("3060"), 3194 ("3104"), 3536 ("3636"), 5644 ("6644"), 5658 ("5758"), 5659 ("5759"), 6585 ("6885"), 7586 ("7686") |
| not in OCR text | 27 | 5853-5879 |
- Most are NOT page-break splits; only a few heads sit at a page edge (flagged `on_page_boundary` in notes: 41, 42, 569, 1601, 2093, 3050, 3194, 5004, 5005).
- Side effects in the committed WPA parse worth knowing: the misreads created spurious rows: `EO:3060` appears twice (the first is really 3050, p275 L0), `EO:5011A`/`5011B` (p435 L29,L32) sit between 5002 and 5003 and read as OCR damage of a Dec. 3 run (true head unknown; not resolved), and rows such as EO:5758, 6885, 7686 are mislabelled neighbours. `EO:106-4` is printed `106*4`. Merged lines also mean 2103 and 3493 rows contain the next entry in their text field.
- **5853-5879 (27 integers): not recoverable from this OCR.** The scan skips printed folios 486-487: page 502 ends `[ 485 ]` (EO 5852, June 1, 1932) and page 503 ends `[ 488 ]` and starts at EO 5880 (July 9, 1932). So the gap is two missing scan pages, not a parser failure. Corroboration outside this scan: `research/niebuhr/README.md` says the project holds APP transcriptions for these and official OFR compilation text for most of them; those rows are named in `RECOVERED_IDENTITIES.csv` notes as non-official mirror rows only. I did not verify them further.
- Held official printing (SOURCES.jsonl grade `*government_printed_copy` or route `official/*`), searched across all `jobs/*/output/SOURCES.jsonl` by exact `EO:<n>`: found for only 4 of the 75: 5659 (hathi-gpo-orders), 6117 (mabillon-held-printings), 6171 (hathi-gpo-orders), 7586 (mabillon-held-printings); path and `page_or_item` are in the CSV. I did not search `jobs/fr-originals/output` separately beyond its SOURCES.jsonl (covered by the glob; 1937+ only), nor open any PDF/page to confirm. "Held" = a SOURCES.jsonl row exists; I did not check that the bytes are retained. For the other 71 the column says `none found`. The 5853-5879 rows have no official row in SOURCES.jsonl even though niebuhr says OFR text is held (probably in a job output not keyed by SOURCES.jsonl; not found by me).
- Every recovered row is a lead: for the 12 inferred rows the number is not printed in the OCR; a person should check the scan image. Dates are WPA dates (a finding aid), not signing dates.

## (3) WPA present, census absent (`WPA_ONLY_CENSUS_ABSENT.csv`)
Exactly 4, all in the WPA parse: 2103 (CSV line 2165, p195, Dec 7 1914, Alaska Townsite Withdrawal No. 5; merged with 2104), 2703 (line 2785, p244, Sept 12 1917, Grace Matthews Trescot eligible for reinstatement), 3493 (line 3631, p312, June 14 1921, California National Forest diminished; merged with 3494), 3733 (line 3879, p331, Sept 8 1922, Arthur J. Hannan). No other WPA-present/census-absent numbers exist.
- Why absent: grep of `research/stage15/CENSUS` and `research/progress` finds **no** mention of `EO:2103/2703/3493/3733`; the census lacks them simply because no source feeding it named them (no documented exclusion). They are listed as `number_only` gaps with no index evidence in `jobs/clark-discovery/output/NUMBER_GAPS.csv`, and as `number_gap` targets in `research/niebuhr/` (WPA_JOIN.json, CORROBORATION.csv: WPA agrees, "identified_no_text"). No SOURCES.jsonl row names any of them, so no held printing.
- Interesting: the neighbours 2104 and 3494 ARE in the census while 2103 and 3493 are not; in WPA those pairs share an OCR line, but the census does not derive from the WPA parse so no causal link is shown.

## (4) Is the audit statement still true?
- "about 46 integers missing from the WPA parse": FALSE as stated: 75 are missing from the WPA parse; 46 are missing from the census.
- "clustered at 22/23, 274/275, 435/436, 502/503": TRUE for locations of WPA misses, but causes differ (multi-number heads, parser sequence guard, two missing scan pages), and 33 of the 75 are in the census already.
- "2103, 2703, 3493, 3733 in WPA, not in census": TRUE, and they are the only four.

## Exceptions / open problems
- 92 (`92-92-3`) meaning unresolved; 396 date is "(no date)" as printed; 5011-A/B origin unresolved.
- Census base rule counts suffixed ids (EO:23-1, EO:106-1) as bases 23, 106; `EO:106` and `EO:21` also exist as bare ids (checked), so 21/106 are genuinely census-present.
- `WPA_CENSUS_CROSSTAB.csv` is summary + detail rows (85 lines); full per-integer table is `WPA_CENSUS_PER_INTEGER.csv`.

## Reproduce (from the output dir; python3 -I)
```
python3 -I scripts/step1.py WPA_CENSUS_PER_INTEGER.csv scripts/_missing.json   # (1) cross-tab inputs
python3 -I scripts/step2c.py scripts/_missing.json scripts/_rec.json RECOVERED_IDENTITIES.csv   # (2)
python3 -I scripts/step3.py     # (3) WPA_ONLY_CENSUS_ABSENT.csv
python3 -I scripts/step4.py     # WPA_CENSUS_CROSSTAB.csv
python3 -I scripts/step2a.py    # confirms archived wpa.py reproduces the committed CSV
```
(`step2b.py`, `ctx.py`, `gap.py` are exploration helpers; `gap.py N...` prints the raw OCR between neighbours.)
