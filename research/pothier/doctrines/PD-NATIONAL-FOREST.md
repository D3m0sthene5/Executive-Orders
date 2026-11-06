# PD-NATIONAL-FOREST: national forest boundary, consolidation, transfer, name and administrative-site orders

This is the doctrine for the 708 members that X1 typed `national_forest_boundary` (executive orders of 1907-1936). Its
machine form is `research/pothier/doctrines/PD-NATIONAL-FOREST.json`. It applies the coordinator's rulings in
`research/pothier/COORDINATOR_RULINGS.md` (P1 to P8). The status question throughout is whether the order, as a whole,
was still in force on the cutoff, 2026-10-14. A lead is a proposal for the owner, not a status.

## Conclusions

The doctrine proposes a `no` lead for 314 of the 708 members, a `yes` lead for none, and leaves 394 `open`. Of the 314
`no` leads, 111 rest on a later instrument (basis `ACT`) and 203 on the order's own terms (basis `TERM`).

| Branch | Members | Lead | Lead kind | Basis | Date |
|---|---:|---|---|---|---|
| B01 held text is another order's | 2 | open | `text_identity_failure` | none | none |
| B02-REVOKED revoked in full by a held executive order (49 branches) | 55 | no | `revoked_by_later_order` | ACT | revoking order's date |
| B02-SUPERSEDED superseded by number by a held executive order | 1 | no | `superseded_by_later_order` | ACT | superseding order's date |
| B02-PLO revoked in full by a Public Land Order per BLM's table (50 branches) | 51 | no | `revoked_by_public_land_order` | ACT | PLO signature date |
| B02-ABOLISHED the forest the order only named was abolished or merged by name (4 branches) | 4 | no | `ended_by_express_abolition_of_its_subject` | ACT | abolishing instrument's date |
| B03 own stated end date (9 branches) | 9 | no | `own_stated_end_date` | TERM | the stated date |
| B04 named amendment of a parent (7 branches) | 7 | no | `merged_into_parent_on_issue` | TERM | order date |
| B05-SCHEDULED revocation or exclusion whose own terms schedule the opening (62 branches) | 62 | no | `spent_on_issue` | TERM | last scheduled opening step |
| B05-DEFERRED restoration on a date the Secretary fixes by notice | 2 | open | `restoration_pending_secretary_notice` | none | none |
| B08-MIXED-3155 exclusion combined with an amendment | 1 | open | `mixed_exclusion_and_amendment` | none | none |
| B06-SPENT-4204, B06-SPENT-5670 single revocation or release | 2 | no | `spent_on_issue` | TERM | order date |
| B08-SPENT-EXCLUSION-LANDMARK plain exclusion with a landmark outlier word | 2 | no | `spent_on_issue` | TERM | order date |
| B09 exclusion tied to one named disposition | 4 | open | `restoration_with_retained_restriction` | none | none |
| B06 revocation with at most immediate restoration | 49 | no | `spent_on_issue` | TERM | order date |
| B07 pure amendment, correction or extension | 6 | no | `merged_into_parent_on_issue` | TERM | order date |
| B08 exclusion with immediate restoration | 66 | no | `spent_on_issue` | TERM | order date |
| B10 administrative-site and similar Forest Service withdrawals | 95 | open | `persists_until_revoked_withdrawal` | none | none |
| B11 classification, resurvey, exchange and pending-legislation withdrawals | 42 | open | `persists_until_revoked_withdrawal` | none | none |
| B12 Indian or native use or occupation (also within PD-INDIAN) | 16 | open | `other_reservation_overlap` | none | none |
| B13 military or naval purposes, post water supply (also within PD-MILITARY-RESERVATION) | 12 | open | `other_reservation_overlap` | none | none |
| B14 townsite, railroad terminal, school, springs, municipal water supply (also within PD-LAND-WITHDRAWAL) | 26 | open | `other_reservation_overlap` | none | none |
| B15 forest creation, transfer, merger, addition, renaming, boundary redescription | 194 | open | `forest_designation_persists_pending_record` | none | none |
| B99 catch-all | 0 | open | `unclassified` | none | none |

The counts come from `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-NATIONAL-FOREST.json --hints`
(708 members; decides 314; contradicted 2; 199 branches). By WPA hint the members are national_forest 639,
military_reservation 24, land_withdrawal 13, indian_reservation 12, other 12, blank 7, civil_service_individual 1.

The 314 `no` leads rest on six kinds of evidence:

- 55 members are revoked in full by a later executive order whose text the project holds and which names the member
  by number. Forty-six of the revoking orders belong to this family; the rest belong to other families (EOs 6140,
  6154 and 3679 to land withdrawals, EO 4272 to military reservations). One further member, EO 2612, is expressly
  superseded by number by EO 2789.
- 51 members are revoked in full by a Public Land Order as BLM's official Table of Public Land Orders states it. The
  table is held; the orders' own texts are not.
- 4 members did nothing but constitute or name a forest that a later instrument abolished by name, or merged by name
  into another forest (ruling P7).
- 9 pending-legislation withdrawals state their own end date.
- 181 members only revoke another order, release a reservation, or exclude land from a forest and return it to the
  general land laws. Under ruling P1 each such command is exhausted on its effective date, or on the last date its own
  opening schedule fixes.
- 13 members only amend, correct or extend another instrument. Under ruling P2 their text merged into the parent on
  issue.

The open members are of four kinds. Most are continuing withdrawals and reservations, which by statute last until
revoked, or orders that fix a national forest's designation. Six are restorations that are not complete on their own
terms, because the restoration waits on a notice by the Secretary of the Interior or is tied to one named disposition.
One does two different things. Two have a held text that belongs to another order. None of these can be decided
without a later instrument or a current record.

## (a) Mechanisms

**Terms used.** A *proclamation* establishing a national forest (before 1907, a "forest reserve") set apart public
land as a reservation. Later executive orders *modified* that proclamation: they excluded land, added land, moved land
between forests or renamed the forest. *Public domain* means federal land open to disposal under the general land
laws (homestead, desert-land and similar entry). A *withdrawal* closes public land to settlement, sale or entry for a
stated purpose; a *reservation* also devotes the land to that purpose. A *Public Land Order* (PLO) is the instrument by
which the Secretary of the Interior, under delegated presidential authority, has made and revoked withdrawals since
1942. *Spent on issue* is the project's label (ruling P1) for an order whose command was fully carried out on its
effective date. *Merged into the parent on issue* (ruling P2) describes an amending order whose text became part of the
order it amended and lives or ends with that parent.

**M-REVOKED (later instrument, ends).** A later executive order revoked, rescinded or expressly superseded the member in
full, naming it by number. The project holds the text of every revoking order used here, and none qualifies the
revocation by tract, section or "in part". The end date is the revoking order's date. Partial revocations ("in so far
as it affects", "except as to") are not ends; for example, EO 4421 revokes EOs 1555 and 1920 "except as to" school
reservations, EO 5743 revokes EO 5194 "in so far as it affects" listed lands, and EO 5651 revoked EO 4889 only as to
lands not reserved by an Act of 1930. EO 2789 says "This order supersedes and takes the place of order number 2612,
dated May 7, 1917, and is made for the sole purpose of correctly describing the lands intended to be withdrawn by that
order". Those words reach EO 2612 by number (ruling P3), so EO 2612 ends on 1918-01-19, while the Navajo withdrawal it
described continued under EO 2789. EO 4272 revokes EO 1147 "as that portion" of the lands it lists, and the list repeats
EO 1147's whole description with the same total, "Area about 16,420 acres", so the revocation reaches the whole order;
its scan omits one section number, which the lead discloses.

**M-REVOKED-PLO (later instrument, ends).** BLM's Table of Public Land Orders is the Bureau of Land Management's official
finding aid: for each PLO it gives the signature date, a subject line and the Federal Register citation. Where the row
reads "revoking EO No. NNNN" for the member, with no "in part" qualifier for that order, the member takes a `no` lead
dated by the PLO's signature date (ruling P3; `REVISION_BRIEF.md` point 3). Every such lead carries two gaps: the PLO
text is not held, and the effective date may be the Federal Register publication date. Each pair was checked by
script and by reading: the row names the member's number, the state named in the row appears in the member's text or
title, and where the row also gives a date, it is the member's date. Rows that do not reach the member are excluded:
"revoking in part" rows (EOs 1354, 1929, 3195, 3889, 4208, 4712, 6050 and 6441), rows about a half-numbered order
(PLO 399 names "EO No. 1432 1/2" and PLO 614 "EO 1324 1/2"), and rows about another order of the same date (PLO 1292
concerns a Utah water reserve dated April 29, 1912, not EO 1523). EO 2242 stays open although PLO 2337 (1961) reads
"revoking EO No. 2242", because later rows of the same table modify EO 2242 (PLO 2755, 1962) and revoke it in part
(PLO 3345, 1964; PLO 3848, 1965), so the table itself shows that the 1961 row was not a complete end.

**M-ABOLISHED-SUBJECT (later instrument, ends; ruling P7).** Some 1908-1909 orders did only one thing: they declared that
described land already in national forests "shall be known as" a named forest, or renamed a forest, and said they
released and reserved no land. When a later instrument abolishes that forest by name, the member's only subject is
gone. PLO 307 (1945) is "abolishing Mono National Forest", which EO 898 named. PLO 618 (1949) is "abolishing the La Sal
National Forest", the name that EO 1051 gave the La Salle. Two held executive orders merge a named forest out of
existence: EO 3317 (1920) transfers "all the lands included within the boundaries of the Sopris National Forest" to the
Holy Cross and merges them "into one National Forest, thereafter to be known as the Holy Cross National Forest"; EO 2153
(1915) does the same for the Nebo, merging it into the Manti on and after July 1, 1915. EOs 1069 (Sopris) and 827 (Nebo)
take `no` leads on that reading, which treats an express merger of all of a named forest's lands as abolition of that
forest by name; the adoption question below names it. Orders that also assigned land to a second forest are not
reached: EO 870 constituted the Holy Cross and also gave the rest of the old Holy Cross to the Leadville, and EO 801
constituted the Pocatello and gave part of the Bear River to the Cache. They stay open on B15, with PLO 263 and EO 2179
recorded as candidate ends of one of their two subjects. No held text abolishes an administrative site or other single
subject of a member by name, so P7 reaches no other member.

**M-OWN-DATE (own terms, ends).** Nine withdrawals in aid of pending legislation withdraw the land "until" March 5 of a
stated year (or July 1, 1918). Eight of them also provide that, if Congress does not act and no other direction is
given, the land "will, on [that date], become subject to disposal ... without further order", so each ends on that date.
EO 2542-A withdrew its land only "until July 1, 1918, in aid of legislation" and has no disposal clause. EO 2896 extended
that withdrawal to March 5, 1919 "in so far as it affects the hereinafter described lands" and added the disposal clause
for that date. The tracts EO 2896 does not list left the withdrawal on July 1, 1918, and the order as a whole ended on
March 5, 1919.

**M-SPENT-ON-ISSUE (own terms, ends; ruling P1).** Under the Act of June 4, 1897 the President could "modify any
Executive order" establishing a forest reserve and "reduce the area or change the boundary lines". The mechanism covers
four kinds of order: an order that excludes described land and returns it to the general land laws; an order that opens
to entry land already excluded; an order that only revokes another order or withdrawal; and an order that only releases
land from a reservation. Each does one thing. Once the land leaves the reservation or the revoked order ends, the land
is governed by the general land laws or by the instrument it falls under, not by the member. Two orders show the last
kind: EO 4204 rescinds a naval reservation on land that had stayed within the Chugach National Forest, and its words that
the land "is hereby restored to its former National Forest status" state that consequence; EO 5670 releases a lot from a
War Department reservation, and the lot then "becomes a part of the Siuslaw National Forest" by the terms of the 1907
proclamation, not by a command of the order.

The date is the order's effective date. Many members set a schedule, made under the Act of September 30, 1913 or the
ex-servicemen Public Resolutions 29 (1920) and 85 (1930). Typical schedules are settlement only for 28 days from the
56th day, or ex-servicemen preference entry for 91 days beginning with the 63d day, followed in each case by
"appropriation under any applicable public land law by the general public". For these members the end is the date that
last step takes effect. Each of the 62 such members has its own branch, with the date read from its text and listed
under (c). Two schedules were later amended by held members: EO 2470 moved EO 2449's dates, and EO 3039 moved EO 3010's.
Under ruling P2 those amendments became part of EO 2449 and EO 3010, so their later dates are used. EOs 1924 and 1973
strike from an earlier exclusion order (EOs 1622 and 1818) the clause that withdrew the excluded land for
classification, and open the land on a dated schedule; their only content ends a withdrawal, so they take P1 leads at
the last scheduled step.

A revocation or restoration that takes effect only on a future event is not spent on its signing date. EOs 787 and 1125
exclude land and provide that it "shall be restored to the public domain and become subject to settlement ... on such
date and after such notice by publication as the Secretary of the Interior may prescribe", with entry thirty days later.
The Secretary's notice is not held, so both stay open (B05-DEFERRED-OPENING).

Ruling P1 keeps one exception: a restoration that keeps a reversion, retained tract, reserved right or purpose
restriction is not only a restoration. The test this doctrine applies is the order's own words. An exclusion whose words
tie the land to one named disposition is restricted, because the order's purpose is fulfilled only when that disposition
occurs and the order fixes no date for it. Four members meet the test: EO 4363 restores Malheur land "to entry only under
the provisions of the act of January 27, 1922" "to permit adjustment of an equitable claim"; EO 7033 excludes a Cibola lot
"in order to permit the Secretary of the Interior to dispose of the said land under the provisions of the act of March
1, 1907"; EO 6178 excludes Carson land "embraced in color of title application Santa Fe 063408" (a color-of-title claim
rests on long good-faith possession); and EO 2415 excludes former Hot Springs Indian Reservation land "in order to admit
of the disposition thereof by the Secretary of the Interior, under the provisions of Sections 2122 and 2123 of the
Revised Statutes". They stay open on B09. An exclusion that returns the land to the general land laws is not restricted,
even when general law gives someone a preference or the order sets a dated opening schedule. The following features
therefore do not count as retained rights, because they come from general law and lapse on their own terms:

- the State's sixty-day school-land preference under the Act of March 3, 1893;
- the coal-land conditions that some orders mention;
- the time-limited ex-servicemen preferences.

A later proclamation that re-added the same land to a forest would be a new reservation, not a revival of the
exclusion.

**M-MERGED-INTO-PARENT (own terms, ends; ruling P2).** An order whose only operative content amends, corrects or extends
another order or proclamation has no command of its own after issue. Every such lead carries the disclosure "its text
continues as part of the parent until the parent ends; the parent's lifecycle carries it". An extension of a withdrawal
period is an amendment of the parent, because extending is the member's only content (EOs 2896 and 3055). Seven
amending orders have their own branches, because each needs its own disclosure:

- **EO 1626 (1912-10-17)** corrected the description of Station "B" in the Secretary of the Interior's ranger-station
  withdrawal of April 1, 1907. The parent ended as to Station B on 1919-01-25, when EO 3025 revoked "Executive Order of
  October 17, 1912 (No. 1626)" and with it the corrected Station B withdrawal. The correction substituted a different
  tract, so in substance it withdrew new land in the form of a correction.
- **EO 4278 (1925-07-31)** amended EO 4246's Huachuca District boundaries. EO 5147 (1929-07-01) revoked "Executive
  Order ... (No. 4246), as amended by ... (No. 4278)"; that is the parent's end.
- **EO 2470 (1916-10-14)** only changed EO 2449's opening dates to November 14 and December 12, 1916.
- **EO 2223 (1915-07-19)** only modified EO 1228's Siletz classification withdrawal "to exclude from the operation
  thereof" lands within the Siuslaw National Forest.
- **EO 6045 (1933-02-24)** only restated the description of the Sitka Dock Site reserved by EO 3333 "to read as follows".
- **EO 2896 (1918-06-26)** only extended EO 2542-A for listed lands to March 5, 1919.
- **EO 7361 (1936-05-05)** only amended EO 4929 so that its withdrawal embraces about 37,000 more acres. In substance it
  is a new withdrawal in the form of an amendment.

EO 6208 (1933-07-21) later rescinded EO 6181 together with the section of EO 6160 it amended; under ruling P2 that is an
event in the life of the parent, EO 6160, and the lead for EO 6181 stands.

**M-WITHDRAWAL-PERSISTS (statute, continuity only).** Administrative-site, classification, resurvey and
pending-legislation withdrawals were made under the Pickett Act. That Act provides that "such withdrawals or
reservations shall remain in force until revoked by him or by an Act of Congress". The word "temporarily" in these
orders therefore gives no end, and orders from 1927 onward say so themselves ("This order shall continue in full force
and effect unless and until revoked by the President or by act of Congress"). FLPMA sec. 704(a) repealed the Pickett Act
and the 1891 forest-reservation authority from October 21, 1976. In the held repeal table the entry for the Act of June
25, 1910 is followed by the words "All except the second and third provisos"; the layout leaves unclear which row they
qualify, and no lead here depends on those provisos. Under ruling P3 a repeal of authority is not an end, and FLPMA sec.
701(c) kept "All withdrawals, reservations, classifications, and designations" then in effect in full force until
modified. Nothing in this mechanism shows that any member is still in force; that needs a current land record.

**M-FOREST-DESIGNATION (continuity only, lead only).** This covers the 1908 reorganization orders (EOs 801-909), the
merger and transfer orders (for example EO 2045, which merged the Zuni into the Manzano National Forest, and EO 3379,
which moved land from the Chelan to the Wenatchee), additions, and boundary redescriptions. Each is an operative act on
land whose forest designation persists, not a pure textual amendment, so ruling P2 does not reach it. Under ruling P3
such an order ends only if a later order or statute does one of two things: names the order, or expressly redescribes
the forest's whole boundary while revoking prior descriptions. Ruling P7 reaches it only when its one subject was
abolished by name, as described above.

Section 9 of the National Forest Management Act (NFMA, 1976) bars returning land still reserved as national forest to the
public domain except by Act of Congress. That is context only. It protects land that was still in a forest in 1976, but
cannot show that a given member's land or designation survived to 1976 or to 2026.

**Not used as mechanisms.** The Act of March 4, 1907 (34 Stat. 1271) bars creating or enlarging forests in Oregon,
Washington, Idaho, Montana, Colorado and Wyoming except by Act of Congress. It is a validity question for additions
there (all on B15) and fixes no end. FLPMA sec. 702's repeal of the homestead laws is a repeal of the laws under which
land was opened, not of the orders, so under ruling P3 it is not an end. Ruling P8 has no member here: no member only
delegates a statutory power, and no statute in these sources continues a member's own period. No class-wide review
program reaching these members was found.

## (b) Primary sources

| Id | Citation | Held? | Where |
|---|---|---|---|
| S-MEMBER-TEXT | The member's own order text (ruling P6) | member text | the engine records each lead's text path, sha256 and grade |
| S-ORGANIC | Act of June 4, 1897, ch. 2, 30 Stat. 11, 34-36 (16 U.S.C. 473); modification power and restoration at p. 36 | not held, read on web | https://www.govinfo.gov/content/pkg/STATUTE-30/pdf/STATUTE-30-Pg11.pdf |
| S-PICKETT | Act of June 25, 1910, ch. 421, sec. 1, 36 Stat. 847 | not held, read on web | https://www.govinfo.gov/content/pkg/STATUTE-36/pdf/STATUTE-36-Pg847.pdf |
| S-FLPMA-701C | Pub. L. 94-579, sec. 701(c), 90 Stat. 2743, 2786 | held | `jobs/astra-source-retention/output/pages/3949c2ad…/08af9986…/selected-pages.txt`, sha256 `e14185c661715326d9306d39413ea761527b18a9a9335ebcab70e298e459a786`; pin "All withdrawals, reservations, classifications, and designations" |
| S-FLPMA-704A | Pub. L. 94-579, sec. 704(a), 90 Stat. 2792 (repeals 26 Stat. 1103, 16 U.S.C. 471, and 36 Stat. 847) | held | same file; pin "26:1103 16 U.S.C. 471." |
| S-NFMA-1609 | Pub. L. 94-588, sec. 9, 90 Stat. 2949, 2957 (16 U.S.C. 1609(a)) | not held, read on web | https://www.govinfo.gov/content/pkg/STATUTE-90/pdf/STATUTE-90-Pg2949.pdf |
| S-1907-PROVISO | Act of Mar. 4, 1907, ch. 2907, 34 Stat. 1256, 1271 | not held, read on web | https://www.govinfo.gov/content/pkg/STATUTE-34/pdf/STATUTE-34-Pg1256.pdf |
| S-FS-CHRONOLOGY | USDA Forest Service, Lands Staff, *Establishment and Modification of National Forest Boundaries and National Grasslands: A Chronological Record, 1891-1996* (Nov. 1997) | not held, read on web through a summarizing fetch | https://foresthistory.org/wp-content/uploads/2017/01/Est_and_Mod_of_Nat_For_Bou_and_Nat_Gra.pdf |
| S-FS-LAR | USDA Forest Service, *Land Areas of the National Forest System*, FY2024 (as-of date unverified) | not held, not read | https://www.fs.usda.gov/land/staff/lar/LAR2024/lar2024index.html |
| S-EO-NNNN (54) | 49 revoking orders of B02-REVOKED, EO 2789 (B02-SUPERSEDED), EOs 3317 and 2153 (B02-ABOLISHED), EO 3025 (B04) and EO 2896 (B03) | held | each order's `primary_text_path`; sha256 equals the file hash and the member record's `primary_text_sha256`; pin is the operative line |
| S-BLM-NNNN (6) | BLM Table of Public Land Orders, tables 1-694, 695-2250, 2251-4975, 4976-5806, 5807-6825, 6826-7342 (official finding aid) | held | `jobs/shepard-citations/output/texts/blm/plo_<range>.txt`, sha256 as recorded in `jobs/shepard-citations/output/SOURCES.jsonl`; each source lists a row pin per PLO used |
| S-PLO-NNNN (52) | The 50 revoking PLOs of B02-PLO and PLOs 307 and 618 (B02-ABOLISHED), each with its Federal Register page | not held | `https://www.govinfo.gov/link/fr/<vol>/<page>?link-type=pdf` per PLO |

The NFMA text was checked at 90 Stat. 2957: "Notwithstanding the provisions of the Act of June 4, 1897 (30 Stat. 34;
16 U.S.C. 473), no land now or hereafter reserved or withdrawn from the public domain as national forests pursuant to
the Act of March 3, 1891 (26 Stat. 1103; 16 U.S.C. 471), or any act supplementary to and amendatory thereof, shall be
returned to the public domain except by an act of Congress." Section 9 inserted this sentence into sec. 11(a) of the
Forest and Rangeland Renewable Resources Planning Act of 1974, as that section was redesignated. Two Forest Service
chronological records were located: the 1997 edition (1891-1996) and a 1985 edition (Biodiversity Heritage Library item
252736). The Pickett Act's 1912 amendment (37 Stat. 497), which most post-1912 members cite, was not read. All unheld
sources are listed in `research/pothier/work/PD-NATIONAL-FOREST/FETCH_PROPOSED.jsonl`.

The members revoked by held executive orders, listed by the revoking order (revoking order, its date, the member or
members it revokes in full):

| Revoker | Date | Revokes | Revoker | Date | Revokes |
|---|---|---|---|---|---|
| 1417 | 1911-10-02 | 1337 | 3933 | 1923-11-23 | 1454 |
| 1895 | 1914-02-17 | 1378 | 3991 | 1924-04-17 | 1869 |
| 1934 | 1914-05-09 | 1849 | 4053 | 1924-07-23 | 3295 |
| 2048 | 1914-09-15 | 1957 | 4133 | 1925-01-26 | 1646 |
| 2096 | 1914-11-23 | 1453 | 4208 | 1925-04-20 | 1367 |
| 2127 | 1915-01-25 | 1536 | 4272 | 1925-07-21 | 1147 |
| 2146 | 1915-03-10 | 1336 | 4533 | 1926-10-29 | 1431 |
| 2266 | 1915-10-30 | 1511 | 4534 | 1926-10-29 | 3022 |
| 2267 | 1915-10-30 | 1308 | 4598 | 1927-02-26 | 2008 |
| 2349 | 1916-03-27 | 1647 | 4676 | 1927-06-29 | 4195 |
| 2485 | 1916-11-05 | 1589 | 4776 | 1927-12-02 | 4081, 4193, 4197, 4200 |
| 2487 | 1916-11-05 | 1355 | 4852 | 1928-04-06 | 4199, 4248 |
| 2490 | 1916-11-21 | 1552 | 4877 | 1928-05-04 | 4114 |
| 2674 | 1917-07-30 | 1369 | 4884 | 1928-05-17 | 4115 |
| 2787 | 1918-01-18 | 1324 | 4910 | 1928-06-12 | 1868 |
| 2789 | 1918-01-19 | 2612 (supersedes) | 4916 | 1928-06-23 | 4196 |
| 2887 | 1918-06-17 | 2530 | 4946 | 1928-08-11 | 4198 |
| 2945 | 1918-08-23 | 2168 | 4976 | 1928-10-10 | 4194 |
| 3190 | 1919-12-02 | 1634 | 5002 | 1928-11-24 | 1551 |
| 3191 | 1919-12-02 | 1375 | 5147 | 1929-07-01 | 4246 |
| 3194 | 1919-12-04 | 1401 | 5422 | 1930-08-07 | 3626 |
| 3486 | 1921-06-10 | 3309 | 6140 | 1933-05-22 | 2586, 2848 |
| 3679 | 1922-05-24 | 3043 | 6154 | 1933-06-05 | 3832, 3896 |
| 3728 | 1922-08-28 | 3186 | 6197 | 1933-07-06 | 2713 |
| 3740 | 1922-09-28 | 2148 | 7078 | 1935-06-17 | 3102 |

Every pair was checked by reading the revoking text. The number and the site, lands or forest it describes agree with
the target in every case. The cited date agrees too, with two exceptions, and in both the identification stands on the
number and the lands. EO 2485 cites EO 1589 as "of August 21, 1912", but EO 1589 is signed August 24, 1912. EO 3740 cites
EO 2148 as "of March 1, 1915", but EO 2148's scan reads "z8 March, 1915". Both lead gaps record the mismatch. Several
dates were checked against the scans:

- EO 3194 and EO 3740 lack a full date in the member record, so their dates come from the signature lines.
- EO 4133's scan reads "January 26, 1926". The State Department certified the copy on February 4, 1925, and the number
  belongs to January 1925, so 1925-01-26 is used.
- EO 4916's scan reads "June 28, 1928" against the member date 1928-06-23. The member date is used, and the five-day
  conflict is flagged in that lead's gaps.

The members revoked by Public Land Orders, per the held BLM table (member, PLO, signature date, Federal Register page):

| EO | PLO | Signed | FR | EO | PLO | Signed | FR |
|---|---|---|---|---|---|---|---|
| 1326 | 1953 | 1959-08-21 | 24 FR 6978 | 3263 | 351 | 1947-02-17 | 12 FR 1393 |
| 1357 | 4623 | 1969-04-14 | 34 FR 6689 | 3305 | 6660 | 1987-11-10 | 52 FR 44893 |
| 1432 | 1246 | 1955-11-03 | 20 FR 8423 | 3373 | 5016 | 1971-02-10 | 36 FR 2784 |
| 1441 | 428 | 1947-12-01 | 12 FR 8243 | 3405 | 420 | 1947-10-21 | 12 FR 6975 |
| 1452, 2522 | 415 | 1947-10-10 | 12 FR 6926 | 3465 | 2167 | 1960-07-22 | 25 FR 7152 |
| 1500 | 6734 | 1989-07-12 | 54 FR 30215 | 3661 | 1289 | 1956-04-24 | 21 FR 2790 |
| 1503 | 1294 | 1956-04-24 | 21 FR 2818 | 3783 | 1407 | 1957-04-05 | 22 FR 2506 |
| 1537 | 864 | 1952-09-11 | 17 FR 8364 | 3948 | 6410 | 1983-07-11 | 48 FR 32828 |
| 1560 | 1287 | 1956-04-19 | 21 FR 2658 | 3999 | 421 | 1947-10-21 | 12 FR 6976 |
| 1568 | 5902 | 1981-05-18 | 46 FR 28417 | 4247 | 982 | 1954-07-15 | 19 FR 4499 |
| 1572 | 1047 | 1954-12-30 | 19 FR 155 | 4294 | 4219 | 1967-04-24 | 32 FR 6646 |
| 1585 | 1103 | 1955-03-23 | 20 FR 1890 | 4397 | 2611 | 1962-02-12 | 27 FR 1492 |
| 1597 | 3771 | 1965-08-10 | 30 FR 10192 | 4415 | 6716 | 1989-03-29 | 54 FR 13524 |
| 1673 | 1280 | 1956-04-02 | 21 FR 2245 | 4491 | 3115 | 1963-06-28 | 28 FR 6876 |
| 1677 | 2885 | 1963-01-18 | 28 FR 695 | 4700 | 1690 | 1958-07-22 | 23 FR 5672 |
| 1742 | 1267 | 1956-02-27 | 21 FR 1383 | 4889 | 1466 | 1957-08-07 | 22 FR 6511 |
| 1747 | 3539 | 1965-02-11 | 30 FR 2214 | 4953 | 2511 | 1961-09-25 | 26 FR 9228 |
| 1793 | 2865 | 1963-01-24 | 28 FR 640 | 4963 | 6571 | 1984-09-17 | 49 FR 37760 |
| 1799 | 1669 | 1958-06-27 | 23 FR 5087 | 5278 | 1132 | 1955-04-15 | 20 FR 2666 |
| 1830 | 1131 | 1955-04-15 | 20 FR 2665 | 5799 | 3808 | 1965-08-31 | 30 FR 11354 |
| 1934 | 427 | 1947-12-01 | 12 FR 8242 | 5936 | 3266 | 1963-10-29 | 28 FR 11733 |
| 1956 | 3542 | 1965-02-11 | 30 FR 2215 | 6544 | 7289 | 1997-09-26 | 62 FR 52766 |
| 2106 | 1097 | 1955-03-15 | 20 FR 1662 | 6704 | 5079 | 1971-06-18 | 36 FR 11733 |
| 2495 | 376 | 1947-06-05 | 12 FR 3863 | 6844 | 5480 | 1975-02-04 | 40 FR 6342 |
| 3242 | 1372 | 1956-12-07 | 21 FR 9947 | 7386 | 1947 | 1959-08-18 | 24 FR 6844 |

Where earlier rows revoked part of the same order (EOs 1747 and 6544) the full revocation is the end. Where a row names
the order by number without its date, or names no state (PLO 6716 for EO 4415), the lead says that identification rests
on the number and the state. PLO 1466's and PLO 1690's rows list a correction page as well; the original Federal Register
pages (22 FR 6511, 23 FR 5672) are cited.

## (c) Decision procedure

Branches are tried in order, and the first whose conditions all hold decides. "Text" means the member's primary held
text, with whitespace collapsed and limited to the first 12,000 characters. The regular expressions are written to
survive this family's scan OCR, where for example "eliminating" appears as "elimi- nating" or "byv eliminat- ing".

1. **B01-TEXT-NOT-ORDER (open).** The text mentions none of the following words: forest, ranger, withdrawal,
   reservation, public land, exclusion, townsite, meridian, acres, township. This catches EO 3537, whose held text is a
   postal reinstatement. EO 4613 is routed here by id because its held scan is EO 4614 (naval petroleum reserves). Gap:
   a correct text of the order.
2. **B02-REVOKED-BY-NNNN and B02-SUPERSEDED-BY-2789 (no, ACT, fixed date).** The member is one of the 56 targets in the
   first table under (b), and the basis is the held revoking order. Gap: the revoking text's grade (archival scan or
   mirror transcription, not an authenticated original), plus any date mismatch noted under (b).
3. **B02-PLO-NNNN (no, ACT, fixed date).** The member is one of the 51 targets in the second table under (b). Gaps: the
   PLO text is not held, the effective date may be the Federal Register date, and identification notes where the row
   gives no date or state.
4. **B02-ABOLISHED-NNNN (no, ACT, fixed date).** EOs 898 (1945-12-18), 1051 (1949-11-28), 1069 (1920-08-07) and 827
   (1915-07-01), as described under (a). Gaps: the PLO texts are not held (EOs 898 and 1051); a Wikisource note says the
   Mono division took effect July 1, 1945, which is unverified; the merger reading of ruling P7 (EOs 1069 and 827).
5. **B03-OWN-DATE-NNNN (no, TERM, fixed date).** These members end on the date their withdrawal clause states:
   - 1917-03-05: EOs 2443 and 2445.
   - 1919-03-05: EO 2542-A (as extended by EO 2896) and EOs 2887, 2930, 2937 and 2939.
   - 1921-03-05: EO 3269.
   - 1925-03-05: EO 4028.

   Each branch also requires the text to contain "withdrawn … until March 5" or "until July 1". Gap: only the held
   corpus was searched for extensions, and an extension outside it would move the end later.
6. **B04-MERGED-NNNN (no, TERM, order date, `merged_into_parent_on_issue`).** EOs 1626, 4278, 2470, 2223, 6045, 2896 and
   7361, the named amendments described under (a). Each gap records the parent's end or open status. EO 2896's gap
   records that its scan is signed "28 June, 1918" against the member date 1918-06-26.
7. **B05-SCHEDULED-NNNN (no, TERM, fixed date, `spent_on_issue`).** The member is a revocation or exclusion order. Most
   meet the B06 or B08 conditions. Four are matched another way: EOs 2004 and 2069 amend a proclamation "to revoke such
   withdrawal" and restore the land, and EOs 1924 and 1973 contain "modified by striking therefrom". Its own terms fix
   the opening. The date is the day the land became subject to general disposition, counted as calendar days from the
   order date or read as a stated date:

   | End date | Members (order date + days, or stated dates) |
   |---|---|
   | 1914-06-08 | 1899, 1900, 1908 (settlement May 9 to June 7, 1914, then general) |
   | 1914-05-28 | 1924 (entry and selection for 20 days from May 8, 1914, then general) |
   | order date + 84 | 1928, 1946, 1973, 1986, 2004, 2027, 2028, 2055 (dated 1914-09-28), 2069, 2086 |
   | order date + 91 | 2176, 2212, 2276, 2302, 2305, 2338, 2365, 2367, 2492, 2507 |
   | order date + 63 | 2542 |
   | stated dates | 2449 → 1916-12-12 (as amended by EO 2470); 2739 → 1918-01-21; 2925 → 1918-10-02; 2945 → 1918-09-30; 2989 → 1919-01-22; 3009 → 1919-01-22; 3010 → 1919-05-07 (as amended by EO 3039) |
   | order date | 3191 (its printed opening dates, November 19 and 26, 1919, precede its signing on December 2, 1919) |
   | order date + 126 | 3262, 3331, 3413, 3435, 3444, 3485, 3487, 3569, 3584 (63 days from the 63d day) |
   | order date + 133 | 3486 (63 days from the 63d day, then 7 days for any entryman) |
   | order date + 154 | 3738, 3739 (dated 1922-09-26), 3740, 3872, 3955, 4088, 4264, 4533, 4534, 4566, 4750, 4966 (dated 1928-09-22), 4984, 5002, 5422, 5619, 6197 (91 days from the 63d day) |
   | order date + 119 | 3933, 4053 (91 days from the 28th day) |

   Gap: the Land Office's day-counting convention may shift a date by one day. Two signature lines conflict with the
   member dates, and the leads say so. EO 2004 is signed "28 July, 1914" against 1914-07-29, which would put its end on
   1914-10-20 rather than 1914-10-21. EO 2027 is signed "21 A ugust, 1914" against 1914-08-24, which would put its end on
   1914-11-13 rather than 1914-11-16; its scan also begins with an unrelated Canal Zone order.
8. **B05-DEFERRED-OPENING (open).** EOs 787 and 1125, whose restoration waits on the Secretary of the Interior's notice.
   What would decide it: that notice, after which the end is thirty days later.
9. **B08-MIXED-3155 (open).** EO 3155 amends Proclamation 1500 (1918) "so as to add to the areas listed therein, which
   may be selected by the State of Montana" further lands, and also excludes land from the Flathead National Forest. With
   two different operative acts neither P1 nor P2 applies. What would decide it: the lifecycle of Proclamation 1500 and
   the State's selections under it.
10. **B06-SPENT-4204, B06-SPENT-5670 and B08-SPENT-EXCLUSION-LANDMARK (no, TERM, order date, `spent_on_issue`).** EOs
    4204 and 5670 as described under (a); EOs 3798 and 5409 are plain exclusions of cannery and home-site land from the
    Tongass, restored "to entry under the applicable public land laws", which the outlier list missed only because their
    boundary descriptions name an "Indian graveyard" and the "Hyder town-site elimination".
11. **B09-RESTRICTED-RESTORATION (open).** An exclusion whose text ties the land to one named disposition: "to permit
    adjustment", "restored to entry only under the provisions of the act", "in order to permit the Secretary of the
    Interior to dispose", "in order to admit of the disposition", or "color of title application". Members: EOs 2415,
    4363, 6178, 7033. Gap: the land-office record of the named disposition.
12. **B06-SPENT-REVOKE (no, TERM, order date, `spent_on_issue`).** The text contains an operative "is/are/be [hereby]
    revoked / rescinded / vacated / abolished". OCR splits such as "here by" are accepted, and negated forms such as
    "should not now be revoked" and "shall be vacated" do not count. After the revocation the text must not re-reserve
    or rewithdraw the land, add it to or declare it part of a forest, or reserve it for a townsite or pending
    legislation. A statement that the land already lies within a forest is allowed (EOs 4663, 4665, 4675, 4837, 4938).
13. **B07-MERGED-AMEND (no, TERM, order date, `merged_into_parent_on_issue`).** The text amends, corrects, extends, or
    "modified so that" or "modified by striking" a cited order or proclamation, and does nothing else: no withdrawal,
    exclusion or boundary modification of its own, no new opening command, and no Indian, townsite, transfer, military,
    enlargement, "shall be known" or "remain part of" language. Members: EOs 1955, 3039, 3055, 6181, 7118, 7412.
14. **B08-SPENT-EXCLUSION (no, TERM, order date, `spent_on_issue`).** The text excludes or eliminates described land from
    a forest, or opens to entry land that an earlier proclamation or order excluded. None of the following outlier
    signals appears:
    - a townsite, Indian or native, military, naval or War Department purpose;
    - a transfer, "made a part of", "constituted … portion", an addition of land or an enlargement;
    - a new withdrawal, "for classification", pending legislation, or a reservation "for" or "as";
    - a railroad terminal or reserve, a power site, reservoir or water supply, an exchange, or a school reservation;
    - "shall be known", a merger or interchange, or "remain part of";
    - a named disposition or purpose restriction (those reach B09 first).

    Boilerplate does not count as an outlier: "lands were withdrawn for forestry purposes", "withdrawn for coal
    classification", and the state school-land preference are allowed.
15. **B10-ADMIN-SITE (open).** The title, summary or text refers to a ranger station, administrative or dock site,
    lookout station, boathouse, right of way, road material or Forest Service use. The 1908 boilerplate "not embraced in
    withdrawals for administrative sites for use in the management of the Forest" does not count, and neither does a
    place name such as "Lookout ... Creeks". The text excludes no land and reserves nothing for a townsite or a military
    purpose; a site lying within a townsite stays here (EOs 1384, 3333, 6189). No held order or BLM table row revokes the
    withdrawal in full. What would decide it: a revoking public land order not in the table's subject lines, the BLM
    land-status record (Mineral and Land Records System), or a current record showing the withdrawal still open.
16. **B11-PENDING-WITHDRAWAL (open).** Withdrawals for classification, resurvey or exchange, or in aid of legislation,
    with no stated end. Additions phrased "included in and made a part of" go to B15 instead, and EO 3041, which reserves
    excluded land for townsite purposes, goes to B14. What would decide it: the later Act, proclamation or revocation for
    the land.
17. **B12-OVERLAP-INDIAN, B13-OVERLAP-MILITARY, B14-OVERLAP-LAND (open).** The text refers to one of these purposes:
    - Indian or Alaska native use or occupation (B12, also within PD-INDIAN): a reservation for their use, a restoration
      to an Indian reservation, a withdrawal pending allotment, or an exclusion of land they occupy (EOs 3915, 7144,
      7179). "Indian Meridian" and the place names Indian Creek, Indian Grave and the old Indian trail do not count, and
      transfers that name an Indian reservation only as a boundary go to B15 (EOs 5758, 6333, 6334, 6882, 6889, 7059,
      7087);
    - a military or naval purpose, a post's water supply, or a forest district carved from military land subject to War
      Department use (B13, also within PD-MILITARY-RESERVATION);
    - a townsite, railroad terminal, school, hot or medicinal springs, or a municipal water supply (B14, also within
      PD-LAND-WITHDRAWAL; the San Francisco rights of way EOs 1887 and 1911 and the Yakima watershed EO 3793 are here).
      Transfers that name a railroad only as a boundary go to B15 (EOs 4757, 6806).

    The gap names the overlapping family.
18. **B15-FOREST-DESIGNATION (open).** Every other text that names a national forest: creations from portions of other
    forests, transfers, mergers, additions, renamings not reached by P7, boundary redescriptions, and mixed orders that
    both add and exclude land. EO 4737, which keeps Cape Fanshaw land in the Tongass with its own "continue in full force"
    clause, and EO 4055, which keeps Chugach land "part of said national forest ... until otherwise ordered", are here.
    What would decide it:
    - the Forest Service chronological record, mapping each order to its forest's later consolidation, renaming or
      redescription;
    - the text of each later instrument, tested for words that name the member or expressly redescribe the forest's
      whole boundary while revoking prior descriptions;
    - for a persistence lead, the current Land Areas Report.
19. **B99-CATCH-ALL (open).** No member reaches it.

**Contradictions.** The engine reports 2 contradictions. Neither changes its lead.

- **EO 1523 (B08, `no`, 1912-04-29), edge SH-702748a1639e** (kind `acted_on_after_lead_end`). The edge is a Wikisource
  note that EO 2764 (1917-11-26) "Amends Executive Order 1523". EO 2764's own words modify "the boundaries of the Harney
  National Forest, as modified by Executive order of April 29, 1912" by a further exclusion. It acts on the forest's
  boundary, which EO 1523 had last changed. EO 1523's own command, a single exclusion, was exhausted in 1912, and nothing
  in EO 2764 continues or revives it. The member's other later edge, PLO 1292 (1956), revokes in part a Utah water-reserve
  order of the same date, not EO 1523.
- **EO 5194 (B11, open, `persists_until_revoked_withdrawal`), edge SH-3eb5635efb76** (kind
  `persistence_lead_but_held_ending_edge`). The edge is labelled `revocation`, but its own quote is EO 5743's "Partial
  Revocation", which revokes EO 5194 "in so far as it affects the following described lands". The two other edges from
  the same order are correctly marked `partial_revocation`. A partial revocation is not an end, so the open lead stands.

Several held edges on other members are not flagged by the engine but were checked. None changes a lead:

- The PLO 614 edge on EO 1324 concerns "EO 1324 1/2".
- The PLO 1140 edge on EO 1899 is a Federal Register contents line about the unnumbered order of June 13, 1899.
- The PLO 518 edge on EO 1928 is a contents line about the order creating Public Water Reserve No. 114.
- The EO 3716 edge on EO 3641 cites EO 3641 only as the forest's earlier boundary.
- The EO 6208 edge on EO 6181 is a rescission of the parent section, which ruling P2 assigns to the parent.
- The EO 2223 edge on EO 860 concerns EO 1228.
- The EO 4421 edge on EO 1555 is a partial revocation.
- The PLO 2337 edge on EO 2242 is contradicted by later rows of the same table, as described under (a).

## (d) Members not decided

There are 394 open members.

- **B15, 194 members.** Each is an operative designation that ends only by an instrument whose words reach it. The needed
  instruments are listed by EO number in the Forest Service chronological record, which is not held. The record omits
  administrative sites and minor transfers.
- **B10, 95 members.** Continuing Pickett Act withdrawals with no held full revocation. A `yes` lead needs a current BLM
  or Forest Service land record, and a `no` lead needs a revoking executive order or public land order that the held
  table does not name. EO 1354, for example, is revoked only in part by PLO 1506 (1957).
- **B12-B14, 54 members.** Continuing reservations for other agencies or purposes, needing later instruments for the
  same land. They are kept open here, with the overlapping family named. EO 2242 is among them because the BLM table
  gives conflicting rows for it.
- **B11, 42 members.** Classification, resurvey and legislation withdrawals with no stated end, needing the later
  instrument.
- **B09, 4 members; B05-DEFERRED, 2 members; B08-MIXED-3155, 1 member.** Restorations tied to a named disposition,
  restorations waiting on the Secretary's notice, and one order with two operative acts.
- **B01, 2 members.** The held text is another order's (EOs 3537 and 4613).

Some other members stay open because OCR has destroyed their operative sentence. EO 3443's exclusion clause, for
example, reads "efrhrmdfeb xldn therefrom"; better texts would move such members to B08.

**Questions for the owner's adoption.** First, ruling P2: if the owner prefers to treat an amending order as living as
long as the amended text lives, the 13 P2 leads become `open` pending their parents. EOs 1626 (a correction that
substituted a different tract) and 7361 (an amendment that adds about 37,000 acres) are amendments in form that withdrew
new land in substance. Second, ruling P7: the leads for EOs 1069 and 827 read an express merger of all of a named
forest's lands into another named forest as abolition of the first forest by name. Third, the 51 PLO leads rest on BLM's
finding aid, not on the PLO texts. If the owner will not accept a table row as the basis for an end, those members return
to their open branches (B10, B11, B13, B14) with the PLO named as the candidate end.
