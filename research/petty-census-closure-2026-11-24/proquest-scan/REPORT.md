# What ProQuest holds that the census lacks: a browse of the signed unnumbered collection (2026-11-24)

Coordinator: Claude (Opus), browsing ProQuest Congressional in the owner's Chrome through NYU's OpenAthens sign-in,
2026-11-24, at the owner's request and with the NYU librarian's approval that the owner reports. Search results and
record pages were read and their catalog data saved; no document scan was downloaded.

## Conclusion

ProQuest files 20,028 records dated 1789 to 1936 as unnumbered executive orders, directives and proclamations. All
of its result pages were read twice, oldest first and newest first, and all 20,028 records were saved (`PQ_UNNUMBERED_1789_1936.psv`). Sorted by
kind from their titles and matched against every census list (`classify_match.py`), they include **3,941 documents
signed by the President that are land orders or other operative orders and that the census lacks**
(`CANDIDATES_MISSING.csv`): 1,699 land orders, 893 of them in the numbered series of 1909 to 1936, and 2,242 other
orders and directives. The census holds 1,695 of the signed land and operative orders, and another 384 share a
date and a series or subject with a census entry. A 29-month random sample read before the full pass estimated
about 3,900 missing orders (95% interval 800 to 7,100), which the full reading confirms.

The documents behind all 3,941 were then fetched and read, from text or page images (`../scan-check/REPORT.md`).
2,032 are executive orders on their face, 1,531 of them land orders, and 70 more are probable land orders. Reading
the unsigned unnumbered records and the military-orders collection adds 80, for 2,112.

## The collection

The search was any word of "the OR of OR a OR order OR reserve" across Presidential Materials. It returns 112,006
records in all and 53,671 for 1789 to 1936, which matches the October 19 survey
(`research/pre-1937-sources/PROQUEST_CONGRESSIONAL.md`). Limited to "Unnumbered Executive Orders, Directives, and
Proclamations", 1789 to 1936 gives 20,028 records. Limited further to "Signed by the President", it gives 14,703:
2,455 for 1789 to 1861, 4,846 for 1862 to 1906 and 7,402 for 1907 to 1936.

## The sample

Months were drawn at random with seed 202611241 (`MONTHS.json`): 15 from 1789 to 1861, 8 from 1862 to 1906 and 6
from 1907 to 1936. August and September 1844 were read together as one date range. Every signed unnumbered record
in each sampled month was read from the results list, giving date, length, president and title
(`SAMPLE_ROWS.psv`, 270 records). Five months had no records at all.

Each record was classified from its title:

| Code | Kind | Records |
|---|---|---:|
| L | Land order: a withdrawal, restoration, reservation, modification or sale order | 76 |
| O | Other operative order or directive | 20 |
| A | Appointment, personnel or designation letter | 42 |
| P | Pardon, remission, respite or amnesty | 39 |
| T | Treaty or convention | 25 |
| F | Approval of a fund allotment or refund | 23 |
| M | Pass, permit or discharge for one person | 21 |
| C | Letter of instruction | 9 |
| B | *Official Bulletin* compilation | 9 |
| D | Second ProQuest record of the same order | 6 |

Each L and O record was compared by date and subject with the numbered census, the audited unnumbered series
(`jobs/domesday-register/data/GRAUNT_UNNUMBERED.csv`) and every row of the audit's findings, including rows it did
not count (`MATCH_REVIEW.txt`). An order was treated as held when the same act appears in any of them. That
includes a power-site withdrawal that falls inside the audit's group for its date, and the Papago reservation,
which ProQuest dates June 24, 1874 and Lord dates July 1, 1874. Of the 96 L and O records:

| Era | L and O records | Held | Missing |
|---|---:|---:|---:|
| 1789-1861 | 10 | 1 | 9 |
| 1862-1906 | 17 | 9 | 8 |
| 1907-1936 | 69 | 21 | 48 |

Examples of missing orders:
- Jackson's withdrawal for the Mount Vernon Arsenal, Alabama (March 13, 1830).
- Lincoln's order establishing the Sanitary Commission (June 9, 1861).
- Lincoln's lighthouse reserve on North Charity Island, Michigan (March 20, 1865).
- McKinley's authorization of plague regulations (May 21, 1900).
- Taft's Coal Land Restorations and Coal Land Withdrawals (December 1911), and his Alaskan Withdrawal No. 1
  (December 5, 1911). Numbered EO 1584 cites the Alaskan Withdrawal, but the census does not count it as an order
  of its own.
- Wilson's Petroleum Reserves 58 and 59 (March 1918) and Public Water Reserves 74 and 75 (October 1920).
- Hoover's Potash Reserve No. 7 (June 8, 1929).

## Limits

- **Titles only.** The classification uses titles, not documents. Kinds O, C and F are judgment calls about what
  counts as an executive order, and the "land orders only" figures leave them out.
- **ProQuest's labels are not checked.** The "signed by the President" flag and the dates are ProQuest's own and
  have not been checked against the scans.
- **Some held orders may be missed.** Matching by date and subject can miss a held order whose date differs, as the
  Papago case shows, so a few "missing" orders may in fact be held.
- **Few months in the busiest era.** The 1907-1936 stratum has six months, so its estimate is unstable. The series
  counts above are direct and do not depend on the sample.
- **Four phrase counts were discarded.** The counts for "order of modification", "military reservation",
  "lighthouse" and "Indian reservation" were thrown out, because the browser's history had gone back to a narrower
  result set (1,481) before they ran.

## Next

The missing land orders belong to numbered series. Coal Land Restoration, Montana runs to No. 90, and Public Water
Reserves pass No. 126. Each series can be listed from beginning to end, as the power-site series was from the USGS
registry. Likely sources are the General Land Office annual reports, Interior's withdrawal schedules, and ProQuest's
own result lists, read the way this sample was read.

## The land-order series, listed record by record (2026-11-24, afternoon)

A second pass read every ProQuest result for the land-order series. The search was any of "coal land", "coal
reserve", "petroleum reserve", "petroleum restoration", "public water", phosphate, potash, "oil shale", "alaskan
withdrawal", "reservoir site", "stock driveway" or helium, limited to Presidential Materials. Among the unnumbered
records it returns 2,185. Read oldest first, the run reached 1,900 records, past the end of 1936. The 1,465 records
dated before 1937 are in `PQ_LAND_SERIES_PRE1937.psv`. Each row gives the CIS accession number, the date
(YYYYMMDD), the signed flag (S or N), the match class and a compact title.

The compact titles use these codes:

| Code | Series |
|---|---|
| CLR, CLW | Coal Land Restoration, Coal Land Withdrawal |
| PR, PRR | Petroleum Reserve, Petroleum Restoration |
| PWR, PWRR | Public Water Reserve, Public Water Restoration |
| PHR, PHRR | Phosphate Reserve, Phosphate Restoration |
| POTR, POTRR | Potash Reserve, Potash Restoration |
| RSR, RSRR | Reservoir Site Reserve, Reservoir Site Restoration |
| MOD | Order of modification |
| INT | Interpretation |

The match classes are:

| Class | Meaning |
|---|---|
| M | Matched to a census entry by date, series word and number or state |
| G | Inside an audited power-site date group |
| D | The date carries another census entry, but no subject match |
| U | Nothing in the census on that date |

The census is matched against the audited unnumbered series, the audit's findings and the domesday register. The
matching ran in the browser, from the repository's public files on GitHub.

| | Signed | Not signed |
|---|---:|---:|
| Matched (M or G) | 69 | 3 |
| Not in the census (D or U) | 1,159 | 234 |

Spot checks of the D class found different orders sharing a date, not missed matches. Some orders appear twice:
ProQuest often files the same order in record group 33 and again in group 46. Counting date and title together,
the signed orders the census lacks come to **about 1,110 distinct orders**. Of the 202 "Interpretation" records,
195 are marked not signed by the President. They are probably departmental interpretations of Public Water
Reserve No. 107, and they are not counted as presidential orders.

## The whole unnumbered collection, record by record (2026-11-24, evening)

The final pass read the collection itself rather than a sample or a set of series. The search was the same, any
word of "the OR of OR a OR order OR reserve" in Presidential Materials, dated 1789 to 1936 and limited to
"Unnumbered Executive Orders, Directives, and Proclamations", sorted oldest first at 100 records a page. A script in
the browser saved each page's records: CIS accession number, date, ProQuest's signed flag, administration and the
first 150 characters of the title. The 201 pages gave 19,983 rows and 19,918 distinct accession numbers. ProQuest
reorders records that share a date between page loads, so 111 of the 20,028 were never on a page when it was read.
A second reading, newest first, captured all 20,028; the 111 are maps, attachments and second copies, and none is a
new candidate.

### Kinds

`classify_match.py` sorts each record by its title. Rules are tried in order and the first match decides. A letter
("To Edwin M. Stanton: [appoints ...]") takes the kind of its bracketed summary. Records filed twice, once in record
group 33 and again in 46, or once with and once without a supporting map, are marked second copies when their date
and title, or their date, series, numbers and states, agree.

| Code | Kind | Signed first copies |
|---|---|---:|
| L | Land order: withdrawal, reservation, restoration, modification or land-office order | 3,411 |
| O | Other operative order, rule, regulation or directive | 2,609 |
| N | NRA code of fair competition, or its amendment | 1,315 |
| T | Treaty, convention, agreement or protocol | 1,203 |
| E | Exception to the arms-export prohibition for one shipment | 925 |
| P | Pardon, commutation, remission, respite or amnesty | 907 |
| C | Letter of instruction | 806 |
| A | Appointment, designation, promotion or assignment | 777 |
| M | Pass, permit, discharge, dismissal, sentence or other action on one person | 583 |
| S | Public land-sale proclamation, postponement or land-office notice | 405 |
| F | Approval of a fund allotment, transfer or payment | 404 |
| V | Commission for one private armed vessel, 1798 to 1814 | 327 |
| R | Request to the Reconstruction Finance Corporation | 265 |
| B | *Official Bulletin* compilation, 1917 to 1919 | 219 |
| Q | Proclamation (extra session, thanksgiving and the like) | 36 |
| I | Interpretation of a land order | 6 |
| X | Map or correspondence filed with another record | 1 |

Unsigned records add 1,138 attachments, 339 interpretations (almost all of Public Water Reserve No. 107 and of
power-site withdrawals) and 1,244 requests to the Reconstruction Finance Corporation, among others.

Checked against the 215 records of the 29-month sample that could be found again by date and title, the rules and
the hand coding agree for 202 on whether a record is a land or operative order (L or O) or something else.

### Matching

Each L or O first copy is compared with the census: the reconciled inventory and every row of the Graunt audit's
findings (`research/graunt-census-audit-2026-11-12/`), the audited unnumbered series
(`jobs/domesday-register/data/GRAUNT_UNNUMBERED.csv`), Lord's unnumbered list
(`jobs/domesday-register/output/UNNUMBERED.csv`) and the numbered register (`jobs/domesday-register/output/REGISTER.csv`).

| Class | Rule |
|---|---|
| M | Land series (coal, petroleum, phosphate, potash, public water, power site, reservoir, Alaskan withdrawal): same series and number, and the same state where both name one, within seven days. Anything else: at least two distinctive subject words shared on the same date, or three within seven days |
| G | Not matched, but a census entry of the same land series, or a land entry sharing one distinctive word, has the same date |
| D | Not matched; the date carries other census entries |
| U | Nothing in the census on that date |

The land-series pass covered 1,456 of these records. Here 173 of them are interpretations and 86 are second copies.
For the other 1,197, the classes agree with that pass's series-and-number matching for 1,153; of the 44 that differ,
36 moved into G. In a random draw of 40 signed D and U records, none
had a census entry within 45 days that describes the same act.

| Era | Signed L and O | M | G | D | U |
|---|---:|---:|---:|---:|---:|
| 1789-1861 | 743 | 55 | 13 | 29 | 646 |
| 1862-1906 | 2,254 | 670 | 116 | 300 | 1,168 |
| 1907-1936 | 3,023 | 970 | 255 | 1,220 | 578 |

`CANDIDATES_MISSING.csv` lists every D and U first copy, signed or not: 3,941 signed and 1,472 unsigned. Its columns
are the accession number, date, signed flag, administration, kind, whether the census has other entries on that
date, and the title. `PQ_UNNUMBERED_CLASSIFIED.psv` gives every record with its kind, the accession of the record it
copies, its match class and the census identifier it matched.

### Limits

- The kinds rest on titles cut at 150 characters. The line between an operative order (O) and a letter of
  instruction (C), an appointment (A) or a personal action (M) is a judgment, and some O records are minor.
- ProQuest's dates and signed flags have not been checked against the scans.
- A held order dated more than a week away from ProQuest's date will show as missing, and an unrelated census entry
  that shares two distinctive words on the same date will hide a missing one.
- The 384 G records are left out of the missing count, though some are separate orders.
