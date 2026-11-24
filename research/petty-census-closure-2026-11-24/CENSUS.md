# How many executive orders are there? A sourced census, 1789 to October 14, 2026

*The Afterlife of Executive Orders* (Danny Kind, NYU School of Law). Working paper, November 24, 2026. This paper
explains where the project's count of executive orders comes from, how far each part of it can be checked, and
what cannot be counted. It was compiled with AI research assistance from files in the project's repository; nothing
in it has been certified by a human reviewer.

## The answer in brief

The project has identified **16,400 to 16,811 executive orders** signed or specifically approved by presidents from
1789 through October 14, 2026. The count has two parts that are never added together without saying so.

- **The numbered series, EO 1 to EO 14435:** 15,002 census rows, of which 14,983 carry an executive-order number.
  Two published catalogs together cover the whole number range: the WPA's *Presidential Executive Orders, Numbered
  1-8030* (Clifford L. Lord, ed., 1944) and the Office of the Federal Register's catalog, which begins at EO 7532.
  **14,865 of the 14,983 numbered labels (99.2%) appear in one or both of those catalogs.** The other 118 are
  accounted for individually below. For 12,470 census orders the project holds an official government printing
  of the text, such as a Federal Register page.
- **The unnumbered series:** orders issued before numbering began, or outside it, mostly land withdrawals,
  military and Indian reservations and Panama Canal orders. 1,405 to 1,816 are identified individually, each with
  its source. The range turns on one definitional choice: whether to count 411 groups of power-site withdrawals
  whose presidential origin is inferred from a federal registry rather than shown on a document.

**Nobody can say how many executive orders have ever been issued, and this paper does not offer a number.** The
familiar figures of 15,000 and 50,000 unnumbered orders trace back to unsupported guesses in Lord's 1943 preface
and a 1957 House committee print. The identified count is a floor. A 30-document test run for this paper suggests
that the CIS microfiche index of presidential documents holds several hundred more presidential land and canal
orders that no list the project uses has captured (section 4).

## 1. What is counted

An executive order, for this census, is a distinct written directive of the President that is identified as an
executive order by the numbered series, by a contemporary official publication, or by a historical compilation
of executive orders. The definition follows the November 12 census audit (`research/graunt-census-audit-2026-11-12/`).

- **Specific presidential approval counts.** A Secretary's recommendation that the President expressly approved,
  or a presidential instruction transmitted by a Secretary, is an executive order. A general delegation does not
  turn every later agency action into a presidential order.
- **Each directive is counted once,** across republications, aliases and multiple catalog entries.
- **Several numbered clauses can be one order.** In November 1894 Grover Cleveland approved amendments to the civil
  service rules that the State Department later numbered EO 36 to 53. Where the printed text shows one presidential
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

The State Department began numbering executive orders in 1907. It numbered the earlier orders it held, starting
with an 1862 Lincoln order that established a provisional court in Louisiana. Since 1936 every numbered order has
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

- **EO 36 to 53 (except 50) and EO 92:** Cleveland's civil service orders of 1894 and 1896. The State Department
  numbered each amended rule separately, and the census counts them as seven orders (section 1).
- **EO 2539, 2703, 3493 and 3733** were admitted on November 12 after the project checked a held official page for
  each. Three of the four are entries in the GPO's *Monthly Catalog*, which names the order's number, date and
  subject but does not print its text.
- **EO 2103 and 6585, and the lettered labels 130A, 2687A, 5151A, 7010F and 8606A,** are cited by a published
  source, but the project does not yet hold an official page for any of them. A search for those pages was still running when this version was published; its results will be in
  `missing-numbered-14/`.

### What the project holds for each census order

The table covers all 15,002 census rows: the 14,983 numbered labels plus 19 unnumbered orders the census already
carried.

| What is held | Orders |
|---|---:|
| Official government printing of the text, such as a Federal Register page or a GPO volume | 12,470 |
| Scan of the archival copy, from ProQuest's replica of National Archives records | 152 |
| Later transcription only, such as the American Presidency Project or Wikisource | 2,241 |
| Official printing located, but the page cited for it failed a two-reader check | 69 |
| No text of any kind | 70 |

The 69 printings in the fifth row are recorded in the project's tracker as "found, page check pending." All 69 were
in fact checked by two independent readers in earlier rounds. 66 failed, usually because the cited page was wrong
even though the order appears on a nearby page; one was unsure and two were blocked. They need a second check with
corrected page spans (`page-check-69/`). None of the 69 is in doubt as an identity: each appears in a catalog and
its printing has been located.

For the 70 orders with no text held, a search for any printing or transcription was still running when this
version was published; its results will be in `nothing-held-70/`. Twenty-three of the 70 are entries whose identity
the project could not confirm, many of them half-numbered labels dated only by year.

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

By era, 137 date from 1789 to 1861, 1,109 from 1862 to 1906, 565 from 1907 to 1936 and 6 from after 1936. The
conservative figure of 1,405 leaves out 411 of the power-site groups, because the registry shows a withdrawal but
not a document that shows the President acted.

These lists are not independent of one another. Lord compiled his 1943 list largely from Richardson and from the
land-office and military-reservation records, so agreement between Lord and those sources is weak corroboration.
For that reason the project no longer reports the capture-recapture estimate (about 4,100 to 5,100) that an earlier
job computed from them: the method assumes independent lists.

## 4. A test of what the lists miss: 30 CIS documents

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
interval for 22 of 30). The 1,633 CIS documents that fall on dates where the project already knows of an order may
add more, because two orders can share a date. These figures are an estimate from 30 records, and the presidential
status of each rests on ProQuest's "signed by the President" flag. Before any of them is added to the count, a person
should read each scan.

The test also showed that CIS can settle questions the audit left open. The audit carried Lord's entries for Fort
Larned and Fort Zarah (January 3, 1868) at zero count, because it could not tell whether they were one document or
two. CIS files them as a single eight-page document signed by President Johnson.

**A finding for the project's main question.** 14 of the 30 CIS records carry cross-references such as "revoked by
1963-03-2933, Feb. 11, 1963" or "partially revoked by 1939-EO-8295." CIS therefore records later revocations and
modifications of unnumbered land orders, which is where the project's lifecycle research has the least evidence.

## 5. Why there is no total

The identified count is a floor, for three reasons. Unnumbered orders were filed in many departments and never
gathered into one series. The surviving compilations copy from one another, so their overlap says little about what
none of them saw. The sample in section 4 shows that a large compilation the project has not yet absorbed holds
hundreds of orders the other lists miss.

The published totals do not fill the gap. Lord's 1943 preface mentions Harold Ickes's figure of 15,000 and others'
figure of 50,000 without deriving either. The 1957 House Committee on Government Operations print estimated that
unnumbered orders "exceed 15,000," with no inventory behind the estimate, and the 1974 Senate special committee
report repeats it. The American Presidency Project's per-president totals sum to about 16,238 through EO 14435. That
table combines numbered and Lord's unnumbered counts and is not an independently checked list. No study the project
has found derives a total of all orders ever issued (`research/graunt-census-audit-2026-11-12/cis-kaufman/README.md`).

## 6. What remains

| Task | What it would settle | Who |
|---|---|---|
| Read the scans of the 22 CIS candidates, then a larger CIS sample | Whether CIS's signed-by-the-President flag is reliable, and how many of the 875 (and of the 1,633 on shared dates) to add | A person with NYU ProQuest access; the scans open in ProQuest's own viewer |
| Recheck the 69 failed page citations with corrected spans | Official text credit for 69 orders | Machine page check with two readers, once the source job records the corrected spans |
| Official pages for the 7 cited-but-unheld numbered labels | Whether the numbered series is complete | Search running (`missing-numbered-14/`) |
| Resolve the 214 date conflicts | Correct dates for the affected orders | Machine first pass, then human review |
| Rule on the definitional choices in section 1, especially the 411 power-site groups | The width of the identified range | Owner, ideally with a scholar of the presidency |

## Files

Everything is under `research/petty-census-closure-2026-11-24/`:

- `crosswalk/`: the cross-check script, `NUMBERED_CROSSWALK.csv` (one row per numbered label), the sources and their
  hashes, the exceptions, the absent numbers, the date conflicts, and the summary.
- `cis-pilot/`: the 30-document sample and the record-level results with ProQuest permalinks.
- `missing-numbered-14/`: the search for official pages for the numbered labels the census still lacks.
- `nothing-held-70/`: the search for texts of the 70 numbered orders with nothing held.
- `page-check-69/`: why the 69 page checks are not pending, the worklist, and a ready fetch job for a corrected
  recheck.

The census audit this paper builds on is `research/graunt-census-audit-2026-11-12/`, and the census file is
`research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv`.
