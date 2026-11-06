# PD-NATIONAL-FOREST: national forest boundary, consolidation, transfer, name and administrative-site orders

This is the doctrine for the 708 members that X1 typed `national_forest_boundary` (executive orders of 1907-1936). Its
machine form is `research/pothier/doctrines/PD-NATIONAL-FOREST.json`. It applies the coordinator's rulings in
`research/pothier/COORDINATOR_RULINGS.md` (P1 to P6). The status question throughout is whether the order, as a whole,
was still in force on the cutoff, 2026-10-14. A lead is a proposal for the owner, not a status.

## Conclusions

The doctrine proposes a `no` lead for 244 of the 708 members, a `yes` lead for none, and leaves 464 `open`.

| Branch | Members | Lead | Lead kind | Basis | Date |
|---|---:|---|---|---|---|
| B01 held text is another order's | 2 | open | `text_identity_failure` | none | none |
| B02 revoked in full by a later order of this family (42 branches) | 46 | no | `revoked_by_later_order` | ACT: the revoking order's held text | revoking order's date |
| B03 own stated end date (9 branches) | 9 | no | `own_stated_end_date` | TERM | the stated date |
| B04 amendment of a named parent (EOs 1626, 4278) | 2 | no | `merged_into_parent_on_issue` | TERM | order date |
| B05 revocation or exclusion whose own terms schedule the opening of the land (60 branches) | 60 | no | `spent_on_issue` | TERM | last scheduled opening step |
| B06 revocation with at most immediate restoration | 48 | no | `spent_on_issue` | TERM | order date |
| B07 pure amendment, correction or extension | 8 | no | `merged_into_parent_on_issue` | TERM | order date |
| B08 exclusion of land with immediate restoration or relinquishment for disposal | 71 | no | `spent_on_issue` | TERM | order date |
| B09 restoration with a purpose restriction (EO 4363) | 1 | open | `restoration_with_retained_restriction` | none | none |
| B10 administrative-site and similar Forest Service withdrawals | 142 | open | `persists_until_revoked_withdrawal` | none | none |
| B11 classification, resurvey, exchange and pending-legislation withdrawals | 54 | open | `persists_until_revoked_withdrawal` | none | none |
| B12 Indian or native reservations (also within PD-INDIAN) | 27 | open | `other_reservation_overlap` | none | none |
| B13 military or naval purposes, post water supply (also within PD-MILITARY-RESERVATION) | 20 | open | `other_reservation_overlap` | none | none |
| B14 townsite, railroad terminal, school, springs (also within PD-LAND-WITHDRAWAL) | 32 | open | `other_reservation_overlap` | none | none |
| B15 forest creation, transfer, merger, addition, renaming, boundary redescription | 186 | open | `forest_designation_persists_pending_record` | none | none |
| B99 catch-all | 0 | open | `unclassified` | none | none |

The counts come from `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-NATIONAL-FOREST.json --hints`
(708 members; decides 244; contradicted 1). By WPA hint the members are national_forest 639, military_reservation 24,
land_withdrawal 13, indian_reservation 12, other 12, blank 7, civil_service_individual 1.

The 244 `no` leads rest on four kinds of evidence:

- 46 members are revoked in full by later orders of this same family. The project holds each revoking text, which
  names its target by number and date.
- 9 pending-legislation withdrawals state their own end date.
- 179 members only revoke another order, or exclude land from a forest, and do nothing more than restore the land to
  the general land laws. Under ruling P1 each such command is exhausted on its effective date. Where the order's own
  terms schedule the opening of the land, it is exhausted on the last date that schedule fixes.
- 10 members only amend, correct or extend another instrument. Under ruling P2 their text merged into the parent on
  issue.

The open members are of three kinds. Some are continuing withdrawals and reservations, which by statute last until
revoked. Some are orders that fix a national forest's designation. One is a restoration that kept a purpose
restriction. None of these can be decided without a later instrument or a current record.

## (a) Mechanisms

**Terms used.** A *proclamation* establishing a national forest (before 1907, a "forest reserve") set apart public
land as a reservation. Later executive orders *modified* that proclamation: they excluded land, added land, moved land
between forests or renamed the forest. *Public domain* means federal land open to disposal under the general land
laws (homestead, desert-land and similar entry). A *withdrawal* closes public land to settlement, sale or entry for a
stated purpose; a *reservation* also devotes the land to that purpose. *Spent on issue* is the project's label
(ruling P1) for an order whose command was fully carried out on its effective date. *Merged into the parent on issue*
(ruling P2) describes an amending order whose text became part of the order it amended and lives or ends with that
parent.

**M-REVOKED (later instrument, ends).** A later executive order revoked or rescinded the member in full. The project
holds the text of every revoking order used here, and each names the member by number and date and revokes it without
exception. The end date is the revoking order's date. Partial revocations ("in so far as it affects", "except as to")
are not ends. Held edges show EO 2242 revoked only in part by EO 7053 and EO 7448, and EO 4889 only in part by EO
5048; EO 4421 revokes EO 1555 only in part. Those members stay on their own branches.

**M-OWN-DATE (own terms, ends).** Nine withdrawals in aid of pending legislation withdraw the land "until" March 5 of
a stated year (or July 1, 1918). Each provides that, if Congress does not act and no other direction is given, the
land "will, on [that date], become subject to disposal ... without further order", so the order ends on that date.
EO 2896 extended EO 2542-A's term (July 1, 1918) to March 5, 1919 for described lands, so EO 2542-A ends on March 5,
1919.

**M-SPENT-ON-ISSUE (own terms, ends; ruling P1).** Under the Act of June 4, 1897 (30 Stat. 36) the President could
"modify any Executive order" establishing a forest reserve and "reduce the area or change the boundary lines". The
mechanism covers three kinds of order: an order that excludes described land and returns it to the general land laws;
an order that opens to entry land already excluded; and an order that only revokes another order or withdrawal. Each
does one thing. Once the land leaves the reservation or the revoked order ends, the land is governed by the general
land laws, not by the member.

The date is the order's effective date. Many members set a schedule, made under the Act of September 30, 1913 or the
ex-servicemen Public Resolutions 29 (1920) and 85 (1930). Typical schedules are settlement only for 28 days from the
56th day, or ex-servicemen preference entry for 91 days beginning with the 63d day, followed in each case by
"appropriation under any applicable public land law by the general public". For these members the end is the date
that last step takes effect. Each of the 60 such members has its own branch, with the date read from its text and
listed under (c). Two of the schedules were later amended by held members: EO 2470 moved EO 2449's dates, and EO 3039
moved EO 3010's. Under ruling P2 those amendments became part of EO 2449 and EO 3010, so their later dates are used.

Ruling P1 keeps one exception: a restoration that keeps a reversion, retained tract, reserved right or purpose
restriction is not only a restoration. EO 4363 restores Malheur land "only under the provisions of the act of January
27, 1922" "to permit adjustment of an equitable claim", so it stays open on B09. Some features do not count as
retained rights, because they come from general law and lapse on their own terms rather than being reserved by the
order:

- the State's sixty-day school-land preference under the Act of March 3, 1893;
- the coal-land conditions that some orders mention;
- the time-limited ex-servicemen preferences.

A later proclamation that re-added the same land to a forest would be a new reservation, not a revival of the
exclusion.

**M-MERGED-INTO-PARENT (own terms, ends; ruling P2).** An order whose only operative content amends, corrects or
extends another order or proclamation has no command of its own after issue. Every such lead carries the disclosure
"its text continues as part of the parent until the parent ends; the parent's lifecycle carries it". An extension of
a withdrawal period is an amendment of the parent and stays on this branch, because extending is the member's only
content (EOs 2896 and 3055).

Two members that later orders revoked by number are pure amendments, so they take this lead dated at their own
signing:

- **EO 4278 (1925-07-31)** amended EO 4246's Huachuca District boundaries. EO 5147 (1929-07-01) revoked "Executive
  Order ... (No. 4246), as amended by ... (No. 4278)"; that is the parent's end.
- **EO 1626 (1912-10-17)** corrected the description of Station "B" in the Secretary of the Interior's ranger-station
  withdrawal of April 1, 1907. EO 3025 (1919-01-25) revoked "Executive Order of October 17, 1912 (No. 1626)"; that is
  recorded as the end of the Station B withdrawal.

If the owner prefers to treat an amending order as living as long as the amended text lives, these ten leads become
`open` pending their parents.

**M-WITHDRAWAL-PERSISTS (statute, continuity only).** Administrative-site, classification, resurvey and
pending-legislation withdrawals were made under the Pickett Act. That Act provides that "such withdrawals or
reservations shall remain in force until revoked by him or by an Act of Congress". The word "temporarily" in these
orders therefore gives no end, and orders from 1927 onward say so themselves ("This order shall continue in full force
and effect unless and until revoked by the President or by act of Congress"). FLPMA sec. 704(a) repealed the Pickett
Act and the 1891 forest-reservation authority from October 21, 1976. Under ruling P3 a repeal of authority is not an
end, and FLPMA sec. 701(c) kept "All withdrawals, reservations, classifications, and designations" then in effect in
full force until modified. Nothing in this mechanism shows that any member is still in force; that needs a current
land record.

**M-FOREST-DESIGNATION (continuity only, lead only).** This covers the 1908 reorganization orders (EOs 801-909), the
merger and transfer orders (for example EO 2045, which merged the Zuni into the Manzano National Forest, and EO 3379,
which moved land from the Chelan to the Wenatchee), additions, renamings (for example EO 1051, La Salle to La Sal)
and boundary redescriptions. Each is an operative act on land whose forest designation persists, not a pure textual
amendment, so ruling P2 does not reach it. Under ruling P3 such an order ends only if a later order or statute does
one of two things: names the order, or expressly redescribes the forest's whole boundary while revoking prior
descriptions.

A merger shows how the test works. EO 3317 (1920) added "all lands of the Sopris National Forest" to the Holy Cross
National Forest. Whether its words reach EO 1069, the order that created the Sopris, has to be tested against EO
3317's text once the later instruments for each forest have been collected.

Section 9 of the National Forest Management Act (NFMA, 1976) bars returning land still reserved as national forest to
the public domain except by Act of Congress. That is context only. It protects land that was still in a forest in
1976, but cannot show that a given member's land or designation survived to 1976 or to 2026.

**Not used as mechanisms.** The Act of March 4, 1907 (34 Stat. 1271) bars creating or enlarging forests in Oregon,
Washington, Idaho, Montana, Colorado and Wyoming except by Act of Congress. It is a validity question for additions
there (all on B15) and fixes no end. FLPMA sec. 702's repeal of the homestead laws is a repeal of the laws under which
land was opened, not of the orders, so under ruling P3 it is not an end. No class-wide review program reaching these
members was found.

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
| S-FS-LAR | USDA Forest Service, *Land Areas of the National Forest System*, FY2024 | not held, not read | https://www.fs.usda.gov/land/staff/lar/LAR2024/lar2024index.html |
| S-EO-NNNN (43) | The 42 revoking orders of B02, plus EO 3025 (cited on B04) | held | each member's `primary_text_path`; sha256 equals the member record's `primary_text_sha256`; pin is the revoking line |
| S-EO-2896 | EO 2896, June 26, 1918 (extension of EO 2542-A) | held | its `primary_text_path`; pin "be extended to March 5, 1919, in so far as it affects the hereinafter" |

The NFMA text was checked at 90 Stat. 2957: "Notwithstanding the provisions of the Act of June 4, 1897 (30 Stat. 34;
16 U.S.C. 473), no land now or hereafter reserved or withdrawn from the public domain as national forests pursuant to
the Act of March 3, 1891 (26 Stat. 1103; 16 U.S.C. 471), or any act supplementary to and amendatory thereof, shall be
returned to the public domain except by an act of Congress." Section 9 inserted this sentence into sec. 11(a) of the
Forest and Rangeland Renewable Resources Planning Act of 1974, as that section was redesignated. Two Forest Service
chronological records were located: the 1997 edition (1891-1996) and a 1985 edition (Biodiversity Heritage Library
item 252736). The Pickett Act's 1912 amendment (37 Stat. 497), which most post-1912 members cite, was not read. All
unheld sources are listed in `research/pothier/work/PD-NATIONAL-FOREST/FETCH_PROPOSED.jsonl`.

The 46 B02 targets, listed by the order that revokes them (revoking order, its date, the member or members it revokes
in full):

| Revoker | Date | Revokes | Revoker | Date | Revokes |
|---|---|---|---|---|---|
| 1417 | 1911-10-02 | 1337 | 3933 | 1923-11-23 | 1454 |
| 2048 | 1914-09-15 | 1957 | 3991 | 1924-04-17 | 1869 |
| 2096 | 1914-11-23 | 1453 | 4053 | 1924-07-23 | 3295 |
| 2127 | 1915-01-25 | 1536 | 4133 | 1925-01-26 | 1646 |
| 2146 | 1915-03-10 | 1336 | 4533 | 1926-10-29 | 1431 |
| 2266 | 1915-10-30 | 1511 | 4534 | 1926-10-29 | 3022 |
| 2267 | 1915-10-30 | 1308 | 4598 | 1927-02-26 | 2008 |
| 2349 | 1916-03-27 | 1647 | 4676 | 1927-06-29 | 4195 |
| 2485 | 1916-11-05 | 1589 | 4776 | 1927-12-02 | 4081, 4193, 4197, 4200 |
| 2487 | 1916-11-05 | 1355 | 4852 | 1928-04-06 | 4199, 4248 |
| 2490 | 1916-11-21 | 1552 | 4877 | 1928-05-04 | 4114 |
| 2674 | 1917-07-30 | 1369 | 4884 | 1928-05-17 | 4115 |
| 2787 | 1918-01-18 | 1324 | 4910 | 1928-06-12 | 1868 |
| 2887 | 1918-06-17 | 2530 | 4916 | 1928-06-23 | 4196 |
| 2945 | 1918-08-23 | 2168 | 4946 | 1928-08-11 | 4198 |
| 3190 | 1919-12-02 | 1634 | 4976 | 1928-10-10 | 4194 |
| 3191 | 1919-12-02 | 1375 | 5002 | 1928-11-24 | 1551 |
| 3194 | 1919-12-04 | 1401 | 5147 | 1929-07-01 | 4246 |
| 3486 | 1921-06-10 | 3309 | 5422 | 1930-08-07 | 3626 |
| 3728 | 1922-08-28 | 3186 | 6197 | 1933-07-06 | 2713 |
| 3740 | 1922-09-28 | 2148 | 7078 | 1935-06-17 | 3102 |

Every pair was checked by reading the revoking text: the number and date it cites, and the site, lands or forest it
describes, agree with the target. Several dates were checked against the scans:

- EO 3194 and EO 3740 lack a full date in the member record, so their dates come from the signature lines.
- EO 4133's scan reads "January 26, 1926". The State Department certified the copy on February 4, 1925, and the
  number belongs to January 1925, so 1925-01-26 is used.
- EO 4916's scan reads "June 28, 1928" against the member date 1928-06-23. The member date is used, and the five-day
  conflict is flagged in that lead's gaps.

## (c) Decision procedure

Branches are tried in order, and the first whose conditions all hold decides. "Text" means the member's primary held
text, with whitespace collapsed and limited to the first 12,000 characters. The regular expressions are written to
survive this family's scan OCR, where for example "eliminating" appears as "elimi- nating" or "byv eliminat- ing".

1. **B01-TEXT-NOT-ORDER (open).** The text mentions none of the following words: forest, ranger, withdrawal,
   reservation, public land, exclusion, townsite, meridian, acres, township. This catches EO 3537, whose held text is
   a postal reinstatement. EO 4613 is routed here by id because its held scan is EO 4614 (naval petroleum reserves).
   Gap: a correct text of the order.
2. **B02-REVOKED-BY-NNNN (no, ACT, fixed date).** The member is one of the 46 targets above, and the basis is the held
   revoking order. Gap: the revoking text is an archival scan or mirror transcription, not an authenticated original.
3. **B03-OWN-DATE-NNNN (no, TERM, fixed date).** These members end on the date their withdrawal clause states:
   - 1917-03-05: EOs 2443 and 2445.
   - 1919-03-05: EO 2542-A (as extended by EO 2896) and EOs 2887, 2930, 2937 and 2939.
   - 1921-03-05: EO 3269.
   - 1925-03-05: EO 4028.

   Each branch also requires the text to contain "withdrawn … until March 5" or "until July 1". Gap: only the held
   corpus was searched for extensions, and an extension outside it would move the end later.
4. **B04-MERGED-1626 and B04-MERGED-4278 (no, TERM, order date, `merged_into_parent_on_issue`).** These are the two
   pure amendments described under (a). The gap records the parent's end.
5. **B05-SCHEDULED-NNNN (no, TERM, fixed date, `spent_on_issue`).** The member is a revocation or exclusion order (it
   meets the B06 or B08 conditions, or is one of the two 1914 orders, EOs 2004 and 2069, that amend a proclamation "to
   revoke such withdrawal" and restore the land). Its own terms fix the opening. The date is the day the land became
   subject to general disposition, counted as calendar days from the order date or read as a stated date:

   | End date | Members (order date + days, or stated dates) |
   |---|---|
   | 1914-06-08 | 1899, 1900, 1908 (settlement May 9 to June 7, 1914, then general) |
   | order date + 84 | 1928, 1946, 1986, 2004, 2027, 2028, 2055 (dated 1914-09-28), 2069, 2086 |
   | order date + 91 | 2176, 2212, 2276, 2302, 2305, 2338, 2365, 2367, 2492, 2507 |
   | order date + 63 | 2542 |
   | stated dates | 2449 → 1916-12-12 (as amended by EO 2470); 2739 → 1918-01-21; 2925 → 1918-10-02; 2945 → 1918-09-30; 2989 → 1919-01-22; 3009 → 1919-01-22; 3010 → 1919-05-07 (as amended by EO 3039) |
   | order date | 3191 (its printed opening dates, November 19 and 26, 1919, precede its signing on December 2, 1919) |
   | order date + 126 | 3262, 3331, 3413, 3435, 3444, 3485, 3487, 3569, 3584 (63 days from the 63d day) |
   | order date + 133 | 3486 (63 days from the 63d day, then 7 days for any entryman) |
   | order date + 154 | 3738, 3739 (dated 1922-09-26), 3740, 3872, 3955, 4088, 4264, 4533, 4534, 4566, 4750, 4966 (dated 1928-09-22), 4984, 5002, 5422, 5619, 6197 (91 days from the 63d day) |
   | order date + 119 | 3933, 4053 (91 days from the 28th day) |

   Gap: the Land Office's day-counting convention may shift a date by one day.
6. **B06-SPENT-REVOKE (no, TERM, order date, `spent_on_issue`).** The text contains an operative "is/are/be [hereby]
   revoked / rescinded / vacated / abolished". Negated forms such as "should not now be revoked" and "shall be vacated"
   do not count. After the revocation the text must not do any of these things: rewithdraw the land, reserve it, add
   it to a forest, continue it as part of a forest, put it in a townsite, or withdraw it pending legislation. It also
   contains no new "withdrawn from settlement" or "hereby reserved" command.
7. **B07-MERGED-AMEND (no, TERM, order date, `merged_into_parent_on_issue`).** The text amends, corrects, extends, or
   "modified so that" or "modified by striking" a cited order or proclamation. It does nothing else: no withdrawal,
   exclusion or boundary modification of its own, no new opening command, and no Indian, townsite, transfer,
   military, enlargement, "shall be known" or "remain part of" language. Members: EOs 1955, 2896, 3039, 3055, 6181,
   7118, 7361, 7412.
8. **B08-SPENT-EXCLUSION (no, TERM, order date, `spent_on_issue`).** The text excludes or eliminates described land
   from a forest, or opens to entry land that an earlier proclamation or order excluded. None of the following
   outlier signals appears:
   - a townsite, Indian or native, military, naval or War Department purpose;
   - a transfer, "made a part of", "constituted … portion", an addition of land or an enlargement;
   - a new withdrawal, "for classification", pending legislation, or a reservation "for" or "as";
   - a railroad terminal or reserve, a power site, reservoir or water supply, an exchange, or a school reservation;
   - "shall be known", a merger or interchange, or "remain part of";
   - a purpose restriction.

   Boilerplate does not count as an outlier: "lands were withdrawn for forestry purposes", "withdrawn for coal
   classification", and the state school-land preference are allowed. The gap names the two orders (EOs 787 and 1125)
   that left the opening date to the Secretary of the Interior; for them the restoration took effect on the order.
9. **B09-RESTRICTED-RESTORATION (open).** An exclusion whose restoration is limited "to permit adjustment" of a claim
   (EO 4363). Gap: the land office record of the claim's adjustment.
10. **B10-ADMIN-SITE (open).** The title, summary or text refers to a ranger station, administrative site, lookout,
    dock or boathouse site, right of way, road material or Forest Service use. The text excludes no land and names no
    townsite or military purpose, and no held order revokes the withdrawal. What would decide it: a revoking order
    found in the public land orders (Federal Register, 1942 on) or the BLM land-status record (Mineral and Land
    Records System), or a current record showing the withdrawal still open.
11. **B11-PENDING-WITHDRAWAL (open).** Withdrawals for classification, resurvey or exchange, or in aid of legislation,
    with no stated end. Additions phrased "included in and made a part of" go to B15 instead. What would decide it: the
    later Act, proclamation or revocation for the land.
12. **B12-OVERLAP-INDIAN, B13-OVERLAP-MILITARY, B14-OVERLAP-LAND (open).** The text refers to one of these purposes:
    - Indian or native use (B12, also within PD-INDIAN);
    - a military or naval purpose or a post's water supply (B13, also within PD-MILITARY-RESERVATION);
    - a townsite, railroad terminal, school, or hot or medicinal springs (B14, also within PD-LAND-WITHDRAWAL).

    The gap names the overlapping family. A few exclusions sit here only because their boundary descriptions mention
    an "Indian graveyard", an "Indian settlement" or the "Alaska Railroad" (for example EOs 3798, 3915, 7144, 7179).
    They stay open rather than being guessed into B08.
13. **B15-FOREST-DESIGNATION (open).** Every other text that names a national forest: creations from portions of other
    forests, transfers, mergers, additions, renamings, boundary redescriptions, and mixed orders that both add and
    exclude land. What would decide it:
    - the Forest Service chronological record, mapping each order to its forest's later consolidation, renaming or
      redescription;
    - the text of each later instrument, tested for words that name the member or expressly redescribe the forest's
      whole boundary while revoking prior descriptions;
    - for a persistence lead, the current Land Areas Report.
14. **B99-CATCH-ALL (open).** No member reaches it.

The engine reports one contradiction. EO 4889 is on B11 (lead kind `persists_until_revoked_withdrawal`) and carries a
held revocation edge from EO 5048. That edge revokes EO 4889 only "in so far as it affects" one lot, so it is not an
end, and the open lead stands.

## (d) Members not decided

There are 464 open members.

- **B15, 186 members.** Each is an operative designation that ends only by an instrument whose words reach it. The
  needed instruments are listed by EO number in the Forest Service chronological record, which is not held. The record
  omits administrative sites and minor transfers.
- **B10, 142 members.** Continuing Pickett Act withdrawals with no held revocation. A `yes` lead needs a current BLM or
  Forest Service land record, and a `no` lead needs a revoking executive order or public land order. Neither is held.
- **B12-B14, 79 members.** Continuing reservations for other agencies or purposes, needing later instruments for the
  same land. They are kept open here, with the overlapping family named.
- **B11, 54 members.** Classification, resurvey and legislation withdrawals with no stated end, needing the later
  instrument.
- **B01, 2 members.** The held text is another order's (EOs 3537 and 4613).
- **B09, 1 member.** The restoration kept a purpose restriction (EO 4363).

Some other members stay open because OCR has destroyed their operative sentence. EO 3443's exclusion clause, for
example, reads "efrhrmdfeb xldn therefrom"; better texts would move such members to B08. EO 2027's held scan begins
with an unrelated Canal Zone order before the forest order. The forest text is present and decides the lead, but a
reader should confirm the text's identity.
