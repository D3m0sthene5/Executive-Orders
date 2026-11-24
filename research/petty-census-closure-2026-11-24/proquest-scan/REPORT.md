# What ProQuest holds that the census lacks: a browse of the signed unnumbered collection (2026-11-24)

Coordinator: Claude (Opus), browsing ProQuest Congressional in the owner's Chrome through NYU's OpenAthens sign-in,
2026-11-24, at the owner's request. Only search results and record pages were read. No PDF was downloaded and no
bulk export was made.

## Conclusion

ProQuest's collection holds a few thousand presidential orders from 1789 to 1936 that are in no list the census
uses. Most of them are numbered series of land orders from 1909 to 1936: coal, petroleum, phosphate, potash and
public-water withdrawals and restorations. The census audit counted power-site withdrawals as date groups, but it
holds almost none of these other series.

- **Direct count.** Phrase searches within ProQuest's signed, unnumbered records for 1789 to 1936 return about 1,600
  records in those series. The audited unnumbered series matches about 41 of them by subject (`SERIES_COUNTS.csv`).
  The phrase counts overlap somewhat, and about 2% of ProQuest's records are second copies of one order, so the
  gap in these series alone is roughly 1,500 orders.
- **Sample estimate across all kinds of order.** A random sample of 29 months gives about 3,900 missing
  presidential orders of every kind, with a normal-approximation 95% interval of about 800 to 7,100
  (`estimate.py`). Counting land orders only, the estimate is about 3,000, with an interval from 0 to about 6,000.
  The interval is wide because only six months were drawn from 1907 to 1936, which is where most of the gap is.

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
