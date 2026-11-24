# How many executive orders are there? A sourced census, 1789 to October 14, 2026

*The Afterlife of Executive Orders* (Danny Kind, NYU School of Law). Working paper, November 24, 2026. This paper
explains where the project's count of executive orders comes from, how far each part of it can be checked, and
what cannot be counted. It was compiled with AI research assistance from files in the project's repository; nothing
in it has been certified by a human reviewer.

## The answer in brief

The project has identified **16,400 to 16,811 executive orders** signed or specifically approved by presidents from
1789 through October 14, 2026. The count has two parts that are never added together without saying so.

- **The numbered series, EO 1 to EO 14435:** 15,003 census rows, of which 14,984 carry an executive-order number.
  Two published catalogs together cover the whole number range: the WPA's *Presidential Executive Orders, Numbered
  1-8030* (Clifford L. Lord, ed., 1944) and the Office of the Federal Register's catalog, which begins at EO 7532.
  **14,865 of the 14,983 numbered labels checked (99.2%) appear in one or both of those catalogs.** The other 118
  are accounted for individually below. (The check was run before EO 6585 was added on November 24.) For 12,470 census orders the project holds an official government printing
  of the text, such as a Federal Register page.
- **The unnumbered series:** orders issued before numbering began, or outside it, mostly land withdrawals,
  military and Indian reservations and Panama Canal orders. 1,405 to 1,816 are identified individually, each with
  its source. The range turns on one definitional choice: whether to count 411 groups of power-site withdrawals
  whose presidential origin is inferred from a federal registry rather than shown on a document.

**Nobody can say how many executive orders have ever been issued, and this paper does not offer a number.** The
familiar figures of 15,000 and 50,000 unnumbered orders trace back to unsupported guesses in Lord's 1943 preface
and a 1957 House committee print. The identified count is a floor, and it is known to be far from complete.
ProQuest's collection of unnumbered presidential documents for 1789 to 1936 (the CIS index in digital form) has
been read record by record, all 20,028 of its catalog entries. Sorted by title and checked against every census
list, it holds 3,941 documents marked signed by the President that are land orders or other orders by their titles
and that the census lacks. The document behind each one was then fetched and read, from ProQuest's text layer or,
for handwriting, from images of the pages. 2,032 are executive orders on their face (1,531 land orders and 501
other orders signed, approved or issued by the President), 70 more are land-order files whose order page is
unreadable, 1,808 are letters, appointments, personal actions, fund approvals, proclamations and similar papers, and
31 could not be read. Reading ProQuest's unsigned unnumbered records and its military orders the same way adds 80
more. **In all, ProQuest holds 2,112 executive orders that the census lacks**, which would more than double the
identified unnumbered series (section 4).

## 1. What is counted

An executive order, for this census, is a distinct written directive of the President that is identified as an
executive order by the numbered series, by a contemporary official publication, or by a historical compilation
of executive orders. The definition follows the November 12 census audit (`research/graunt-census-audit-2026-11-12/`).

- **Specific presidential approval counts.** A Secretary's recommendation that the President expressly approved,
  or a presidential instruction transmitted by a Secretary, is an executive order. A general delegation does not
  turn every later agency action into a presidential order.
- **Each directive is counted once,** across republications, aliases and multiple catalog entries.
- **Several numbered clauses can be one order.** In November 1894 Grover Cleveland approved amendments to the civil
  service rules, and the 1944 WPA list gave each amended rule its own number, EO 36 to 53. Where the printed text shows one presidential
  approval for several numbers, the census counts one order.
- **Some numbered items are not presidential orders.** EO 6 and EO 7 are Secretary of State Seward's
  certifications of the Fourteenth Amendment. They keep their numbers but are not counted as presidential
  directives.
- **Proclamations, memoranda and national security directives are separate document families** and are not
  counted unless a catalog files them as executive orders.
- **The count measures issuance, not survival.** Whether an order still has legal effect is the project's main
  research question. It is answered order by order elsewhere and does not change this count.

These choices move the total by only a few dozen orders, apart from the power-site groups. They are the census's
main points of legal judgment, and a reader may reasonably want to revisit them.

## 2. The numbered series

### Where the numbers come from

The State Department began numbering executive orders in 1907. It numbered the earlier orders it held as well. In the WPA list, EO 1 is Lincoln's
October 20, 1862 order establishing a provisional court in Louisiana. The American Presidency Project gives EO 1 a
different date (February 14, 1862) and subject, and that disagreement is one of the date conflicts listed below. Since 1936 every numbered order has
been printed in the Federal Register. The project checked the census against every listing it holds. The script
that does this, `crosswalk/crosswalk.py`, reruns in about a second and produces the same output each time.

| Listing | What it covers | Census labels it names |
|---|---|---:|
| WPA numbered list (Lord, 1944) | EO 1 to 8030 | 8,431 |
| Office of the Federal Register catalog | EO 7532 to 14435 | 6,937 |
| Both | EO 7532 to 8030 | 503 |
| **Either** | **the whole range** | **14,865 of 14,983** |

The WPA list and the Federal Register catalog were compiled separately, decades apart. Where they overlap, from
EO 7532 to 8030, they can be compared. Outside the overlap each number rests on one catalog, together with the
order's own printed text where the project holds it. The American Presidency Project's online index names most
numbers too. It is compiled from Lord and the Federal Register, so it is not counted as independent support.

Of the 118 numbered labels that neither catalog names, 84 date from 1907 to 1936, 18 from 1862 to 1906, 2 from
after 1936, and 14 have no settled date. For 65 of them the project holds an official printing of the text itself,
and 28 appear in the ProQuest list the owner supplied. Most of the rest are lettered or half-numbered entries
("EO 106½") that the WPA list prints inside another entry. `crosswalk/EXCEPTIONS.csv` gives each one with a reason.

The cross-check also compares dates. Across 23,208 comparisons between two listings, 132 disagree by more than a
day. Across 31,921 comparisons against the census date, 82 do. The conflicts are listed in
`crosswalk/DATE_CONFLICTS.csv`. None of them has yet been resolved.

### Gaps in the numbering

Twenty-four whole numbers between 1 and 14435 were missing from the census before November 12. None turned out to be
an unused number.

- **EO 36 to 53 (except 50) and EO 92:** Cleveland's civil service orders of 1894 and 1896. The 1944 WPA list gave a
  number to each amended rule within a single presidential approval, and the census counts them as seven orders
  (section 1). All seven are printed in the Civil Service Commission's *Eighteenth Annual Report* (1902), pages
  246 to 249 and 279 to 280. That report prints the rules, not the numbers, which exist only in the WPA list.
- **EO 2539, 2703, 3493 and 3733** were admitted on November 12 after the project checked a held government page
  for each. For EO 2703, 3493 and 3733 that page is an entry in the GPO's *Monthly Catalog*, which names the order's
  number, date and subject but does not print its text. For EO 2539 it is the printed text in the *Alaska Railroad
  Record*.
- **EO 6585** is printed in the GPO's bound volume of 1934 slip orders, and the project holds that page. It was
  admitted on November 24 (`research/stage15/CENSUS/ADMISSIONS_2026-11-24.csv`).
- **EO 7010F** was in the census under a misread suffix, "EO 7010P" (see below), and was renamed on November 24.
  The project holds its printing in the GPO's 1935 slip-order volume.
- **EO 2103** is listed in the December 1914 *Monthly Catalog* (No. 240, page 321), which gives its number and date
  but no text. **EO 5151A** is printed in the Office of the Federal Register's 1974 compilation of Hoover's
  proclamations and orders, and **EO 2687A** in *Foreign Relations of the United States*, 1917. The project does not
  yet hold copies of those pages.
- **EO 130A** (the WPA list prints it with no date) and **EO 8606A** (found only in the American Presidency Project)
  have no official printing that the search could find.

Details and the searches behind them are in `missing-numbered-14/`.

### What the project holds for each census order

The table covers the 15,002 census rows as they stood before November 24: the 14,983 numbered labels plus 19
unnumbered orders the census already carried. The admission of EO 6585 and the renaming of EO 7010F move one order
each from the last row to the first.

| What is held | Orders |
|---|---:|
| Official government printing of the text, such as a Federal Register page or a GPO volume | 12,470 |
| Scan of the archival copy, from ProQuest's replica of National Archives records | 152 |
| Later transcription only, such as the American Presidency Project or Wikisource | 2,241 |
| Official printing located, but the cited page has a final negative result from a two-reader check | 69 |
| No text of any kind | 70 |

The 69 printings in the fourth row are recorded in the project's tracker as "found, page check pending." All 69 were
in fact checked by two independent readers in earlier rounds: 66 failed, one was unsure and two were blocked. Most
failures name a wrong cited page for an order printed nearby, or a held text that omits part of the order; a few
are identity mismatches, such as an order printed as EO 7700-A cited under EO 7700. The readers' notes give the
actual pages for 57 of the 69, so a second check with corrected page spans is possible (`page-check-69/`).

A search of the 70 orders with no text held (`nothing-held-70/`) found official printings for three: EO 2406 and
EO 2859-A in the State Department's *Foreign Relations of the United States*, and EO 2539 in the *Alaska Railroad
Record*. It found secondary transcriptions for 18 more, mostly Wikisource pages for half-numbered orders of the
Roosevelt, Taft and Wilson years. Of the rest, 33 are known only from a catalog line and 12 from a date. Four
look like errors in the census itself:

- **EO 7010P was EO 7010F.** The WPA list's sequence reads A, B, C, D, E, P, G, H, and the "P" entry describes
  the same Miami electrical-contracting agreement as the American Presidency Project's EO 7010-F and the GPO slip
  printing the project holds, which closes "[No. 7010-F.]" The census row was renamed on November 24.
- **One unnumbered entry duplicates another,** with the same date (August 8, 1914) and the same later amending
  order (EO 8507).
- **The March 10, 1863 Lincoln item** is a proclamation that Wikisource labels EO 1-A.
- **EO 4361½** has the same date as EO 4361 and no title in any index.

The search also found that the text the project held for EO 4224 was in fact EO 4224½ (re-filed on November 24), and that six "A" orders on
radio frequencies (such as EO 9132-A and 10369-A) were confidential and never published, so no official text of
them is expected to exist.

## 3. The unnumbered series

Before 1907, and for land orders well after that, presidents signed many orders that never received a number. The
census audit counted 1,817 individually sourced additions and then removed one duplicate:

| Source | Orders counted |
|---|---:|
| Lord, *List and Index of Presidential Executive Orders, Unnumbered Series* (WPA, 1943) | 908 |
| Power-site withdrawals, grouped by date, from the U.S. Geological Survey's power-site registry | 475 |
| Richardson, *Messages and Papers of the Presidents* | 306 |
| Theodore Roosevelt Center digital library | 105 |
| Numbered-series cross-references and Federal Register or archival sources | 23 |

Of the 1,817 additions before the duplicate was removed, 137 date from 1789 to 1861, 1,109 from 1862 to 1906, 565
from 1907 to 1936 and 6 from after 1936. The
conservative figure of 1,405 leaves out 411 of the power-site groups, because the registry shows a withdrawal but
not a document that shows the President acted.

These lists are not independent of one another. Lord compiled his 1943 list largely from Richardson and from the
land-office and military-reservation records, so agreement between Lord and those sources is weak corroboration.
For that reason the project no longer reports the capture-recapture estimate (about 4,100 to 5,100) that an earlier
job computed from them: the method assumes independent lists.

## 4. What the lists miss: the CIS index and ProQuest's collection

The most complete compilation of presidential documents ever made is the *CIS Index to Presidential Executive Orders
and Proclamations* (Congressional Information Service, 1987). It is published on microfiche and now as ProQuest
Congressional's collection of executive orders and presidential proclamations. Kaufman and Rogowski's public
replication data (2024) lists its documents by accession number. Among them are 2,520 pre-1937 documents in CIS's
executive-order groups for public lands, the Panama Canal and Interior orders. **875 of these fall on dates on which
the project knows of no order of any kind.**

To learn what those 875 are, this paper drew a random sample of 30. The sample was stratified by CIS record group,
with seed 20261124 (`cis-pilot/PILOT_SAMPLE_30.csv`). Each record was opened in ProQuest Congressional through NYU's
subscription. The record's catalog data was read: title, date, whether ProQuest marks it signed by the President,
administration, length, source record group and cross-references. The document scans themselves could not be
opened in the browser used for the test, so **the classification below rests on ProQuest's catalog data, not on
reading the documents.** Each record was then searched for in the census, the audited unnumbered list and the
audit's findings, by date and by subject.

| Result | Documents |
|---|---:|
| Signed by the President, and found in no project list by date or subject | 22 |
| Signed by the President, and matching an entry the audit found but did not count, because it could not tell whether the entry was a separate document | 3 |
| The same order as one already numbered in the census (Reservoir Site Reserve No. 17 = EO 4456A) | 1 |
| Orders of the Secretary of War, not the President | 2 |
| Marked not signed by the President; issuer not determined | 2 |

The 22 new candidates run from an 1830 Jackson withdrawal of Florida lands for naval timber to a 1929 Hoover public
water reserve. Most are numbered land withdrawals and restorations, such as "Public Water Reserve No. 76" and "Coal
Land Restoration, Montana No. 33."

**What this implies.** If the sample is representative, about 73% of the 875 date-unmatched CIS documents are
presidential orders the project has not counted: about 640, with a 95% interval of roughly 470 to 770 (Clopper-Pearson
interval for 22 of 30, which treats the stratified sample as a simple random one).
The other 1,645 CIS documents in these groups fall on dates where the project already knows of an order (1,633
share a date with an unnumbered order, 12 with a numbered one). They may add more, because two orders can share a
date. These figures are an estimate from 30 records, and the presidential
status of each rests on ProQuest's "signed by the President" flag. Before any of them is added to the count, a person
should read each scan.

The test also showed that CIS can settle questions the audit left open. The audit carried Lord's entries for Fort
Larned and Fort Zarah (January 3, 1868) at zero count, because it could not tell whether they were one document or
two. CIS files them as a single eight-page document signed by President Johnson.

**A finding for the project's main question.** 14 of the 30 CIS records carry cross-references such as "revoked by
1963-03-2933, Feb. 11, 1963" or "partially revoked by 1939-EO-8295." CIS therefore records later revocations and
modifications of unnumbered land orders, which is where the project's lifecycle research has the least evidence.

### What ProQuest's own collection holds

ProQuest Congressional files 20,028 records dated 1789 to 1936 as "Unnumbered Executive Orders, Directives, and
Proclamations." On November 24, 2026 every page of that result list was read through NYU's subscription, oldest
first, and each record's CIS accession number, date, signed-by-the-President flag, administration and title was
saved (`proquest-scan/PQ_UNNUMBERED_1789_1936.psv`). Records that share a date can change order between page loads,
so a first reading captured 19,918 distinct records; a second reading, newest first, captured all 20,028, and the 111
added are maps, attachments and second copies.

Each record was sorted by kind from its title and checked against every census layer: the numbered register, the
audited unnumbered series, Lord's unnumbered list, and every row of the audit's findings and reconciled inventory,
including rows the audit did not count (`proquest-scan/classify_match.py`). A land order in a numbered series
matches a census entry of the same series, number and state dated within a week. Any other record matches a census
entry that shares at least two distinctive subject words on the same date, or three within a week. On the 215
records of an earlier hand-coded sample of months, the title rules and the hand coding agree for 202 on whether a
record is a land order or an operative order. In a random draw of 40 unmatched records, none had a census entry
within 45 days that describes the same act.

Among the first copies signed by the President, 3,411 are land orders and 2,609 are other operative orders, rules or
directives. Of these 6,020, the census holds 1,695. Another 384 land orders share their date and their series or
subject with a census entry, so they may be parts of an order the census counts once; they are not counted as
missing. **The other 3,941 are missing from the census:**

| Era | Land orders in numbered series | Other land orders | Other orders and directives | Total |
|---|---:|---:|---:|---:|
| 1789-1861 | 0 | 110 | 565 | 675 |
| 1862-1906 | 0 | 322 | 1,146 | 1,468 |
| 1907-1936 | 893 | 374 | 531 | 1,798 |
| **All** | **893** | **806** | **2,242** | **3,941** |

The list is `proquest-scan/CANDIDATES_MISSING.csv`, which also gives the 1,472 unsigned records that match nothing.
An earlier estimate from 29 months drawn at random put the missing records at about 3,900, with a 95% interval of
800 to 7,100, and the full reading agrees.

**What the documents show.** Every one of the 3,941 documents was fetched from ProQuest (two have no PDF) and read
(`scan-check/REPORT.md`, `scan-check/FULL_READING_3941.csv`). 2,687 were read from ProQuest's text layer: 838 land
orders by their order language, the rest by Claude Haiku readers under a fixed rubric. The 1,252 handwritten or
illegible ones were read from page images by Claude Haiku readers, after a decoder written for the job turned
ProQuest's fax-format scans into page images inside the browser. The readers agree with Claude's own scan readings
for 36 of 40 documents. In all, 1,531 are land orders and 501 are other operative orders, 70 are probable land
orders, 29 are unreadable, and 1,808 are not executive orders: 451 actions on one person, 366 letters of
instruction, 247 other letters, 172 fund approvals, 171 orders a Secretary signed "by command of the President," 132
appointments, 70 proclamations, 32 pardons, 17 treaties and 150 others. **The census therefore lacks 2,032
executive orders among these records, about 1,530 of them land orders.** The same reading of ProQuest's 1,472
unsigned unnumbered records and of 654 general orders in its military-orders collection finds 80 more presidential
orders, for **2,112 in all** (about 2,180 with the probable land files). ProQuest's "signed by the President" flag marks a recorded presidential act, not always a signature.
Genuine missing orders include Van Buren's transfer of $500,000 to the Mint (July 20, 1838), Lincoln's order making
Arkansas one revenue collection district (March 1, 1865), McKinley's Philippine government orders of 1899 to 1901,
Taft's Coal Land Restoration, Washington No. 6 (October 8, 1912), and Harding's order vacating Alaskan Withdrawal
No. 1 (May 19, 1921).

The rest of the collection is presidential paperwork that most definitions of an executive order leave out. The
signed first copies include 1,203 treaties and conventions, 1,315 NRA codes of fair competition and amendments, 925
exceptions to the arms-export embargo, almost all from 1912 to 1917, 907 pardons and remissions, 777 appointments,
806 letters of instruction, 583 passes, discharges and other actions on one person, 404 fund approvals, 405 land-sale
proclamations and notices, 327 privateer commissions of 1798 to 1814 and 219 *Official Bulletin* compilations. A broad definition
could count some of them; that is a ruling for the owner (section 6).

Three limits apply. The readers' judgments could be wrong for a few hundred documents in either direction, and
only the first and last page of each handwritten document was read. The definition used leaves out letters of
instruction, orders a Secretary signed by command, appointments and fund approvals, which would add several hundred
more. A held order whose census date differs by more than a week from ProQuest's, as with the Papago reservation
(ProQuest June 24, 1874; Lord July 1, 1874), will appear as missing.

## 5. Why there is no total

The identified count is a floor, for three reasons. Unnumbered orders were filed in many departments and never
gathered into one series. The surviving compilations copy from one another, so their overlap says little about what
none of them saw. Section 4 shows that the largest compilation, which the project has not yet absorbed, holds
thousands of presidential orders the other lists miss.

The published totals do not fill the gap. Lord's 1943 preface mentions Harold Ickes's figure of 15,000 and others'
figure of 50,000 without deriving either. The 1957 House Committee on Government Operations print estimated that
unnumbered orders "exceed 15,000," with no inventory behind the estimate, and the 1974 Senate special committee
report repeats it. The American Presidency Project's per-president totals sum to about 16,238 through EO 14435. That
table combines numbered and Lord's unnumbered counts and is not an independently checked list. No study the project
has found derives a total of all orders ever issued (`research/graunt-census-audit-2026-11-12/cis-kaufman/README.md`).

## 6. What remains

| Task | What it would settle | Who |
|---|---|---|
| Have a second reader check a random sample of the 3,939 reader verdicts, and read the middle pages of handwritten documents | An independent error rate for the 2,032 | A second reader; browser reading of ProQuest's PDFs |
| Rule on which kinds of presidential document count: letters of instruction, appointments, personal actions such as passes and discharges, fund approvals, orders a Secretary signed by the President's command, NRA codes, arms-export exceptions, privateer commissions | Whether the unnumbered series grows by about 2,000 to 2,100 or by several thousand more | Owner, ideally with a scholar of the presidency |
| Recheck the 69 failed page citations with corrected spans | Official text credit for 69 orders | Machine page check with two readers, once the source job records the corrected spans |
| Fetch and hold the located pages for the Cleveland orders, EO 2103, 2687A and 5151A | Whether the numbered series is complete | Machine fetch through the project's runner, then a census admission under the owner's November 12 rule |
| Search further for EO 130A and 8606A | Whether these two labels are real orders | Archival search (ProQuest, National Archives) |
| Resolve the 214 date conflicts | Correct dates for the affected orders | Machine first pass, then human review |
| Rule on the definitional choices in section 1, especially the 411 power-site groups | The width of the identified range | Owner, ideally with a scholar of the presidency |

## Files

Everything is under `research/petty-census-closure-2026-11-24/`:

- `crosswalk/`: the cross-check script, `NUMBERED_CROSSWALK.csv` (one row per numbered label), the sources and their
  hashes, the exceptions, the absent numbers, the date conflicts, and the summary.
- `cis-pilot/`: the 30-document sample and the record-level results with ProQuest permalinks.
- `proquest-scan/`: every ProQuest unnumbered record for 1789 to 1936 as read (`PQ_UNNUMBERED_1789_1936.psv`), the
  classification and census match of each (`PQ_UNNUMBERED_CLASSIFIED.psv`, `classify_match.py`,
  `CLASSIFY_SUMMARY.json`), the list of missing orders (`CANDIDATES_MISSING.csv`), the land-series listing, the
  29-month sample with its matching review and estimate script, and the series counts.
- `scan-check/`: the reading of every missing record's document (`FULL_READING_3941.csv`), the text layers
  (`PQ_TEXT_LAYER_3941.jsonl.gz`), the page decoder (`g4_page_decoder.js`), the two reader rubrics, the 50-record
  hand reading and the report.
- `missing-numbered-14/`: the search for official pages for the numbered labels the census still lacks.
- `nothing-held-70/`: the search for texts of the 70 census orders with nothing held, 51 of them numbered.
- `page-check-69/`: why the 69 page checks are not pending, the worklist, and a ready fetch job for a corrected
  recheck.

The census audit this paper builds on is `research/graunt-census-audit-2026-11-12/`, and the census file is
`research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv`.
