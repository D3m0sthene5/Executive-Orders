# PD-NATIONAL-FOREST: national forest boundary, consolidation, transfer, name and administrative-site orders

Doctrine for the 708 members typed `national_forest_boundary` by X1 (executive orders of 1907-1936). Machine form:
`research/pothier/doctrines/PD-NATIONAL-FOREST.json`. Status question throughout: was the order, as a whole, still in
force on the cutoff, 2026-10-14? A lead is a proposal for the owner, not a status.

## Conclusions

The doctrine proposes a `no` lead for 245 of the 708 members, a `yes` lead for none, and leaves 463 `open`.

| Branch | Members | Lead | Basis | Date |
|---|---:|---|---|---|
| B01 held text is another order's | 2 | open | none | none |
| B02 revoked in full by a later member order (43 branches) | 48 | no | ACT: the revoking order's held text | revoking order's date |
| B03 own stated end date (9 branches) | 9 | no | TERM: "withdrawn until" a date | the stated date |
| B04 revocation order, spent on issue | 60 | no | TERM | order date |
| B05 amendment, correction or extension order, spent on issue | 10 | no | TERM | order date |
| B06 exclusion of land from a forest (or opening of land already excluded), spent on issue | 118 | no | TERM | order date |
| B08 administrative-site and similar Forest Service withdrawals | 142 | open | none | none |
| B09 classification, resurvey, exchange and pending-legislation withdrawals | 54 | open | none | none |
| B10 reservations for other purposes (Indian, townsite, military, water supply, railroad, school) | 79 | open | none | none |
| B11 forest creation, transfer, consolidation, addition, renaming, boundary redescription | 186 | open | none | none |
| B99 catch-all | 0 | open | none | none |

Counts are from `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-NATIONAL-FOREST.json --hints`
(708 members; decides 245; contradicted 1). By WPA hint the members are national_forest 639, military_reservation 24,
land_withdrawal 13, indian_reservation 12, other 12, blank 7, civil_service_individual 1.

The `no` leads rest on three findings. First, the family's own held texts revoke 48 other members in full, by number
and date. Second, nine pending-legislation withdrawals state their own end date. Third, under the owner's rule that an
order which only revokes, restores or amends another order is spent on issue, 188 members are revocations, amendments
or exclusions of land from a forest that were fully performed when signed. The `open` members are continuing
withdrawals and reservations, which by statute last until revoked, and orders that fix the designation of a
national forest. For those the doctrine needs either a current land record or an owner decision.

One owner decision would move 186 members. If the owner rules that a boundary, transfer, consolidation, addition or
name order is an amendment of the forest's establishing proclamation, and so spent on issue, branch B11 becomes `no`
(TERM, order date). Under the opposite reading those orders persist while the designation they made persists, and
they stay `open` until the Forest Service records below are acquired.

## (a) Mechanisms

**Terms used.** A *proclamation* establishing a national forest (before 1907, a "forest reserve") set apart public
land as a reservation; later executive orders *modified* that proclamation by excluding land, adding land, moving land
between forests or renaming the forest. *Public domain* means federal land open to disposal under the general land
laws (homestead, desert-land and similar entry). A *withdrawal* closes public land to settlement, sale or entry for a
stated purpose; a *reservation* also devotes it to that purpose. *Spent on issue* is the project's label (from the
author brief) for an order whose command was fully carried out when it was signed, so that nothing of the command
remains to be in force; its effect then counts as evidence about the order it acted on.

**M-REVOKED (later instrument, ends).** A later executive order revoked or rescinded the member in full. The project
holds the text of every revoking order used here; each names the member by number and date and revokes it without
exception. The end date is the revoking order's date. Partial revocations ("in so far as it affects", "except as to")
are not ends: held edges show EO 2242 revoked only in part by EO 7053 and EO 7448, EO 4889 only in part by EO 5048,
and EO 4421 revokes EO 1555 only in part. Those members stay on their own branches.

**M-OWN-DATE (own terms, ends).** Nine withdrawals in aid of pending legislation say the land is withdrawn "until"
March 5 of a stated year (or July 1, 1918) and that, if Congress does not act and no other direction is given, the
land "will, on [that date], become subject to disposal ... without further order". The order therefore ends on that
date. EO 2542-A's term (July 1, 1918) was extended to March 5, 1919 for described lands by EO 2896, so EO 2542-A ends
on March 5, 1919.

**M-SPENT-REVOKE, M-SPENT-AMEND (own terms, ends).** An order whose only operative content is to revoke, rescind or
abolish another order, or to amend, correct or extend a cited order or proclamation, did its whole work when signed.
A revocation that also opens the released land to entry under the general land laws, including the ex-servicemen
preference periods of Public Resolutions 29 (1920) and 85 (1930), stays on this branch. A revocation followed by a
new withdrawal or reservation does not. The doctrine dates these ends at the order date. Where an opening schedule
runs on (for example 91 days from the 63d day), its last step falls a few months later, and the lead's gap says so.

**M-SPENT-EXCLUDE (own terms, ends).** Under the Act of June 4, 1897 (30 Stat. 36) the President could "modify any
Executive order" establishing a forest reserve and "reduce the area or change the boundary lines". An order that
excludes described land and at most returns it to the general land laws performs one act. The land leaves the
reservation on the order, and from then on the general land laws govern it, not the order. This conclusion holds
under either reading of the B11 question, because an exclusion leaves no designation behind. If the same land was
later put back into a forest, that was a new reservation, not a revival of the exclusion order. The branch also
covers orders that open to entry land which an earlier proclamation or order had already excluded.

**M-WITHDRAWAL-PERSISTS (statute, continuity only).** Administrative-site, classification, resurvey and
pending-legislation withdrawals were made under the Pickett Act. That Act provides that "such withdrawals or
reservations shall remain in force until revoked by him or by an Act of Congress". The word "temporarily" in these
orders therefore gives no end. Orders from 1927 onward say the same thing themselves: "This order shall continue in
full force and effect unless and until revoked by the President or by act of Congress." FLPMA sec. 704(a) repealed
the Pickett Act and the 1891 forest-reservation authority from October 21, 1976. FLPMA sec. 701(c) kept "All
withdrawals, reservations, classifications, and designations" then in effect in full force until modified. Under the
owner's rule the repeal of the authority is not an end. Nothing in this mechanism shows that any member is still in
force: that needs a current land record (see B08).

**M-FOREST-DESIGNATION (continuity only, lead only).** Most of the 1908 reorganization orders (EOs 801-909), the
merger and transfer orders (for example EO 2045 merging the Zuni into the Manzano National Forest, EO 3379 moving
land from the Chelan to the Wenatchee), the additions and the renamings (for example EO 1051, La Salle to La Sal)
operate on a forest's continuing designation. Many of the 1908 orders say outright that they neither release nor
reserve land ("It is not intended by this order to release any land from reservation or to reserve any land not
heretofore embraced in a National Forest"). Two readings are open:

- Under the merger reading, the order amended the establishing proclamation and is spent on issue. The type rule
  TR-NATIONAL-FOREST already frames boundary changes as "merged into the forest's current boundary".
- Under the persistence reading, the order is in force while the designation it made lasts. It ends when a later
  order by its terms abolishes or renames that forest. For example, EO 3317 (1920) added "all lands of the Sopris
  National Forest" to the Holy Cross National Forest, which on this reading ends EO 1069, the order that created the
  Sopris.

On either reading, NFMA sec. 9 (1976) bars return to the public domain, except by Act of Congress, of land still
reserved as national forest. That bar protects land that was still in a forest in 1976. It does not show that any
particular member's land or name was still in place in 1976, so it is not a current-law predicate for a `yes`.

**Not used as mechanisms.** The Act of March 4, 1907 (34 Stat. 1271) bars creating or enlarging forests in Oregon,
Washington, Idaho, Montana, Colorado and Wyoming except by Act of Congress. It is a validity question for additions in
those states (all on B11) and decides no end date. FLPMA sec. 702's repeal of the homestead laws was considered as an
outer bound for the opening schedules and rejected, because it repeals the laws under which land was opened, not the
orders. No class-wide review program reaching these members was found.

## (b) Primary sources

| Id | Citation | Held? | Where |
|---|---|---|---|
| S-ORGANIC | Act of June 4, 1897, ch. 2, 30 Stat. 11, 34-36 (16 U.S.C. 473); modification power and restoration at p. 36 | not held, read on web | https://www.govinfo.gov/content/pkg/STATUTE-30/pdf/STATUTE-30-Pg11.pdf |
| S-PICKETT | Act of June 25, 1910, ch. 421, sec. 1, 36 Stat. 847 | not held, read on web | https://www.govinfo.gov/content/pkg/STATUTE-36/pdf/STATUTE-36-Pg847.pdf |
| S-FLPMA-701C | Pub. L. 94-579, sec. 701(c), 90 Stat. 2743, 2786 | held | `jobs/astra-source-retention/output/pages/3949c2ad…/08af9986…/selected-pages.txt`, sha256 `e14185c661715326d9306d39413ea761527b18a9a9335ebcab70e298e459a786`; pin "All withdrawals, reservations, classifications, and designations" |
| S-FLPMA-704A | Pub. L. 94-579, sec. 704(a), 90 Stat. 2792 (repeals 26 Stat. 1103, 16 U.S.C. 471, and 36 Stat. 847) | held | same file; pin "26:1103 16 U.S.C. 471." |
| S-NFMA-1609 | Pub. L. 94-588, sec. 9, 90 Stat. 2949, 2957 (16 U.S.C. 1609(a)) | not held, read on web | https://www.govinfo.gov/content/pkg/STATUTE-90/pdf/STATUTE-90-Pg2949.pdf |
| S-1907-PROVISO | Act of Mar. 4, 1907, ch. 2907, 34 Stat. 1256, 1271 | not held, read on web | https://www.govinfo.gov/content/pkg/STATUTE-34/pdf/STATUTE-34-Pg1256.pdf |
| S-FS-CHRONOLOGY | USDA Forest Service, Lands Staff, *Establishment and Modification of National Forest Boundaries and National Grasslands: A Chronological Record, 1891-1996* (Nov. 1997) | not held, read on web through a summarizing fetch | https://foresthistory.org/wp-content/uploads/2017/01/Est_and_Mod_of_Nat_For_Bou_and_Nat_Gra.pdf |
| S-FS-LAR | USDA Forest Service, *Land Areas of the National Forest System*, FY2024 | not held, not read | https://www.fs.usda.gov/land/staff/lar/LAR2024/lar2024index.html |
| S-EO-NNNN (43) | The 43 revoking orders of B02 (EOs 1417 … 7078) | held | each member's `primary_text_path`; sha256 equals the member record's `primary_text_sha256`; pin is the revoking line |
| S-EO-2896 | EO 2896, June 26, 1918 (extension of EO 2542-A) | held | its `primary_text_path`; pin "be extended to March 5, 1919, in so far as it affects the hereinafter" |

The NFMA text was checked at 90 Stat. 2957: "Notwithstanding the provisions of the Act of June 4, 1897 (30 Stat. 34;
16 U.S.C. 473), no land now or hereafter reserved or withdrawn from the public domain as national forests pursuant to
the Act of March 3, 1891 (26 Stat. 1103; 16 U.S.C. 471), or any act supplementary to and amendatory thereof, shall be
returned to the public domain except by an act of Congress." It amends sec. 11(a) of the 1974 Resources Planning Act,
as redesignated. The coordinator's lead cited it as "NFMA sec. 11", but the amending section is sec. 9. The
"Chronologic Record, 1891-2012" named in the coordinator's leads could not be located. The 1997 edition (1891-1996)
and a 1985 edition (Biodiversity Heritage Library item 252736) were found instead. The Pickett Act's 1912 amendment
(37 Stat. 497), cited by most post-1912 members, was not read. All unheld sources are in `FETCH_PROPOSED.jsonl`.

The 48 B02 pairs (revoking order, its date, the member or members it revokes in full):

| Revoker | Date | Revokes | Revoker | Date | Revokes |
|---|---|---|---|---|---|
| 1417 | 1911-10-02 | 1337 | 3740 | 1922-09-28 | 2148 |
| 2048 | 1914-09-15 | 1957 | 3933 | 1923-11-23 | 1454 |
| 2096 | 1914-11-23 | 1453 | 3991 | 1924-04-17 | 1869 |
| 2127 | 1915-01-25 | 1536 | 4053 | 1924-07-23 | 3295 |
| 2146 | 1915-03-10 | 1336 | 4133 | 1925-01-26 | 1646 |
| 2266 | 1915-10-30 | 1511 | 4533 | 1926-10-29 | 1431 |
| 2267 | 1915-10-30 | 1308 | 4534 | 1926-10-29 | 3022 |
| 2349 | 1916-03-27 | 1647 | 4598 | 1927-02-26 | 2008 |
| 2485 | 1916-11-05 | 1589 | 4676 | 1927-06-29 | 4195 |
| 2487 | 1916-11-05 | 1355 | 4776 | 1927-12-02 | 4081, 4193, 4197, 4200 |
| 2490 | 1916-11-21 | 1552 | 4852 | 1928-04-06 | 4199, 4248 |
| 2674 | 1917-07-30 | 1369 | 4877 | 1928-05-04 | 4114 |
| 2787 | 1918-01-18 | 1324 | 4884 | 1928-05-17 | 4115 |
| 2887 | 1918-06-17 | 2530 | 4910 | 1928-06-12 | 1868 |
| 2945 | 1918-08-23 | 2168 | 4916 | 1928-06-23 | 4196 |
| 3025 | 1919-01-25 | 1626 | 4946 | 1928-08-11 | 4198 |
| 3190 | 1919-12-02 | 1634 | 4976 | 1928-10-10 | 4194 |
| 3191 | 1919-12-02 | 1375 | 5002 | 1928-11-24 | 1551 |
| 3194 | 1919-12-04 | 1401 | 5147 | 1929-07-01 | 4246, 4278 |
| 3486 | 1921-06-10 | 3309 | 5422 | 1930-08-07 | 3626 |
| 3728 | 1922-08-28 | 3186 | 6197 | 1933-07-06 | 2713 |
| | | | 7078 | 1935-06-17 | 3102 |

Every pair was checked by reading the revoking text: the number and date it cites, and the site, lands or forest it
describes, agree with the target member. Some dates need comment. EO 3194 and EO 3740 lack a full date in the member
record, so their dates come from the signature lines. EO 4133's scan reads "January 26, 1926", but the State
Department certified the copy on February 4, 1925, and the number belongs to January 1925, so 1925-01-26 is used. EO
4916's scan reads "June 28, 1928" against the member date 1928-06-23; the member date is used, and the five-day
conflict is flagged in the lead's gaps. EO 4278 only amended EO 4246, and EO 5147 revoked EO 4246 "as amended by"
EO 4278. EO 4278 could instead be treated as spent on its own date (1925-07-31); either way it ended by 1929-07-01.

## (c) Decision procedure

Branches are tried in order; the first whose conditions all hold decides. "Text" means the member's primary held text
(whitespace collapsed, first 12,000 characters). The regular expressions are written to survive the scan OCR in this
family, where for example "eliminating" appears as "elimi- nating" or "byv eliminat- ing".

1. **B01-TEXT-NOT-ORDER (open).** The text mentions none of forest, ranger, withdrawal, reservation, public land,
   exclusion, townsite, meridian, acres or township. This catches EO 3537, whose held text is a postal reinstatement.
   EO 4613 is also routed here by id, because its held scan is EO 4614 (naval petroleum reserves). Gap: a correct
   text of the order.
2. **B02-REVOKED-BY-NNNN (no, ACT, fixed date).** The member is one of the 48 targets above. The basis is the held
   revoking order. Gap: the revoking text is an archival scan or mirror transcription, not an authenticated original.
3. **B03-OWN-DATE-NNNN (no, TERM, fixed date).** EOs 2443 and 2445 end 1917-03-05; EO 2542-A ends 1919-03-05 (as
   extended by EO 2896); EOs 2887, 2930, 2937 and 2939 end 1919-03-05; EO 3269 ends 1921-03-05; EO 4028 ends
   1925-03-05. Each branch also requires the text to contain "withdrawn … until March 5" or "until July 1". Gap: only
   the held corpus was searched for extensions. An extension outside it would move the end later, and an earlier
   revocation would move it earlier.
4. **B04-SPENT-REVOKE (no, TERM, order date).** The text contains an operative "is/are/be [hereby] revoked / rescinded
   / vacated / abolished". Negated forms ("should not now be revoked", "shall be vacated") do not count. After the
   revocation, the text must not rewithdraw, reserve, add to or continue the land in a forest, or create a townsite or
   pending-legislation withdrawal; and it contains no new "withdrawn from settlement" or "hereby reserved" command.
   Gap: an opening schedule may end a few months after the order date.
5. **B05-SPENT-AMEND (no, TERM, order date).** The text amends, corrects, "modified so that", "modified by striking"
   or extends a cited order or proclamation. It makes no new withdrawal, no exclusion of its own and no boundary
   modification. It contains no Indian, townsite, transfer, military, enlargement or "shall be known" language, and
   does not keep land as "part of" a forest. Members: EOs 1955, 2004, 2069, 2896, 3039, 3055, 6181, 7118, 7361, 7412.
6. **B06-SPENT-EXCLUSION (no, TERM, order date).** The text excludes or eliminates described land from a forest, or
   opens to entry land that an earlier proclamation or order excluded. It contains none of the outlier signals: a
   townsite, Indian or native, military, naval or War Department purpose; a transfer, "made a part of", "constituted
   … portion" or addition of land; an enlargement; a new withdrawal or "for classification"; pending legislation; a
   reservation "for" or "as"; a railroad terminal or reserve; a power site, reservoir or water supply; an exchange; a
   school reservation; "shall be known"; a merger or interchange; or "remain part of". Boilerplate is not an outlier:
   "lands were withdrawn for forestry purposes", "withdrawn for coal classification", "while the lands were reserved
   for forestry purposes or pending classification", and the state school-land preference are all allowed. Gaps: the
   opening schedule's last step falls after the order date; S-ORGANIC is not yet held.
7. **B08-ADMIN-SITE (open).** The title, summary or text refers to a ranger station, administrative site, lookout,
   dock or boathouse site, right of way, road material or Forest Service use. The text excludes no land and names no
   townsite or military purpose. No held order revokes the withdrawal. Gap: a search of public land orders (Federal
   Register, 1942 on) and of the BLM land-status record (Mineral and Land Records System) for a revocation, or a
   current record showing the withdrawal still open.
8. **B09-PENDING-WITHDRAWAL (open).** Withdrawals for classification, resurvey or exchange, or in aid of legislation,
   with no stated end. Additions phrased "included in and made a part of" go to B11 instead. Gap: the later Act,
   proclamation or revocation for the land.
9. **B10-OTHER-RESERVATION (open).** The order refers to a water supply, Indian or native use, a townsite, a military
   or naval purpose, a railroad, a school, or hot or medicinal springs. Gap: the later instruments for that land.
   Some of these members may also fall under the Indian, military-reservation or land-withdrawal family doctrines.
10. **B11-FOREST-DESIGNATION (open).** Every other text that names a national forest. These are creations from
    portions of other forests, transfers, mergers, additions, renamings, boundary redescriptions, and mixed orders
    that both add and exclude land. Gaps: the owner decision described in (a). Under the persistence reading the
    Forest Service chronological record (S-FS-CHRONOLOGY) is needed for later consolidations or renamings, and the
    current Land Areas Report (S-FS-LAR) for whether the forest or name existed on 2026-10-14.
11. **B99-CATCH-ALL (open).** Nothing reached it.

The engine reports one contradiction. EO 4889 (B09, lead kind `persists_until_revoked_withdrawal`) carries a held
revocation edge from EO 5048. That edge revokes EO 4889 only "in so far as it affects" one lot, so it is not an end,
and the open lead stands.

## (d) Members not decided

There are 463 open members.

- **B11, 186 members.** These turn on the owner's choice between the merger reading and the persistence reading.
  Under the persistence reading they also need, for each member, the forest it names and that forest's later history,
  which the project does not hold as a field. The Forest Service chronological record supplies the history by EO
  number, but it omits administrative sites and minor transfers.
- **B08, 142 members.** Continuing Pickett Act withdrawals with no held revocation. A `yes` needs a current BLM or
  Forest Service land record; a `no` needs a revoking executive order or public land order. Neither is held.
- **B10, 79 members.** Continuing reservations for other agencies or purposes, needing later instruments for the same
  land. Some exclusion orders landed here only because their boundary descriptions mention an "Indian graveyard",
  "Indian settlement" or "Alaska Railroad" (for example EOs 3798, 3915, 7144, 7179). A reader could move them to B06
  after reading them, but the doctrine keeps them open rather than guess.
- **B09, 54 members.** Classification, resurvey and legislation withdrawals with no stated end, needing the later
  instrument.
- **B01, 2 members.** The held text is another order's (EOs 3537 and 4613).

Other members stay open because OCR has destroyed their operative sentence. EO 3443's exclusion clause, for example,
reads "efrhrmdfeb xldn therefrom". Better texts would move them to B06. EO 2027's held scan begins with an unrelated
Canal Zone order before the forest order. The forest text is present, but a reader should confirm the text's identity.
