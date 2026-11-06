# PD-REFUGE-LIGHTHOUSE: bird and wildlife refuges and lighthouse reservations, 1905-1936

Doctrine for the 243 orders that the class engine typed `bird_refuge` (169) or `lighthouse_reservation` (74).
Machine form: `research/pothier/doctrines/PD-REFUGE-LIGHTHOUSE.json` (schema `pothier-family-doctrine/v1`, version 2).
Every lead below is a proposal for the owner, not a status.

## Conclusions

The doctrine decides 87 of the 243 members and leaves 156 open.

- **14 `yes` leads (in force on 2026-10-14), basis CURRENT.** Each rests on a statute or regulation in force on
  the cutoff that names the order or its refuge and keeps the reservation operating. EO 703 and EO 705 (Flattery
  Rocks and Quillayute Needles) are named by Pub. L. 100-226 sec. 3, for refuge lands within Olympic National Park,
  and by the current 16 U.S.C. 668dd note. EO 1044 (Walrus and Otter Islands) is named by 50 CFR 216.85. EO 4254
  (Jupiter Inlet lighthouse) is listed by 43 U.S.C. 1787(b)(4) as an order under which a withdrawal exists. Ten
  Alaska bird-reservation orders (1037, 1039, 1040, 1049, 1458, 1459, 1658, 5095, 5318, 5470) created or enlarged
  reservations that the Alaska National Interest Lands Conservation Act (ANILCA, 1980) sec. 303 names as existing
  refuges and folds into today's Alaska Maritime and Yukon Delta refuges; ANILCA sec. 305 provides that the
  Executive orders for those refuges "shall remain in force and effect". The ten Alaska leads wait on acquisition of
  ANILCA, which is read on the web and not held.
- **73 `no` leads (ended before the cutoff).**
  - 14 were revoked, superseded or replaced in full by a later executive order whose text the project holds
    (basis ACT, the later order's date). Twelve are cited by number; EO 375-A is described by its date and tract in
    EO 5750 (1931), and EO 1304 was replaced by EO 1311, issued "in lieu of" it twelve days later.
  - 34 were revoked in full by a Public Land Order (PLO) of the Secretary of the Interior between 1947 and 2008,
    as recorded in the Bureau of Land Management's official Tables of Public Land Orders, which the project holds
    (basis ACT, PLO signature date). The PLO texts are not held, so every one of these leads carries that gap until
    the Federal Register pages are acquired.
  - 25 ended by their own terms (basis TERM): 17 orders whose only operative content revokes, restores or
    eliminates land from another reservation and are spent on issue (coordinator ruling P1); 5 orders whose only
    operative content rewrites another order's terms without adding land and merge into that order on issue
    (ruling P2); EO 3658, which withdrew Isle Royale islands "until March 5, 1923"; and EO 4490 and EO 5000, which
    revoked reservations and gave ex-servicemen a 91-day homestead preference that ended on 1927-01-03 and
    1929-04-25.
- **156 `open` leads.** 79 refuge reservations (B73, B74), 49 lighthouse reservations and transfers (B75) and
  16 temporary withdrawals (B72) have no held full revocation and no held current record naming the order. For
  refuges, the National Wildlife Refuge System statute makes persistence turn mainly on a fact the project does not
  hold: whether the order's lands were in the Refuge System on or after January 1, 1975, and, for acquired lands,
  whether they were later disposed of under the statute's exceptions. For lighthouse reservations, the end, where
  there is one, is a station-by-station PLO or deed. Two Oregon orders (EO 4364, EO 5702) are listed as revoked by a
  1982 PLO that a 1976 statute appears to forbid (B69); EO 779 is revoked by number by a 1935 proclamation that
  the project does not hold (B68); seven members are other kinds of order (B70); and two, the Blackbeard Island
  chain, need a legible copy of EO 3957 (B71).

Final `try` counts (`python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-REFUGE-LIGHTHOUSE.json --hints`):
243 members; decides 87; contradicted 5. By branch: B01 2, B02 1, B03 1, B04 10 (`yes` 14); B10-B20 12, B21 1,
B22 1, B30-B59 34, B60 1, B61 1, B62 1, B63 17, B64 5 (`no` 73); B68 1, B69 2, B70 7, B71 2, B72 16, B73 20,
B74 59, B75 49, B99 0 (`open` 156).

The five contradiction flags come from held later-event edges in `jobs/pothier/output/MEMBERS.jsonl`; none changes a
lead, and each is disclosed in the gaps of its branch.

- EO 2872 (B64): edges from EO 3964 (1924) and EO 5747 (1931) act after the lead's date. Both modify the Big Lake
  Reservation created by EO 2230 "as reduced" and cite EO 2872 for that reason. Under ruling P2, EO 2872's text
  lives on in its parent, so these are events of EO 2230's lifecycle.
- EO 4975 (B17): an edge from EO 7341 (1936) is an amendment after the lead's date. EO 7341 enlarges the Tule Lake
  refuge established by EO 5945, the order that superseded EO 4975 in 1932; it acts on EO 5945, not on EO 4975.
- EO 3658 (B60): an edge from PLO 1300 (1956) modifies "the EO of Apr. 4, 1922; creating Public Water Reserve No.
  82" in Utah, a different order that shares EO 3658's date. A second unflagged edge, from EO 7836 (1938), is the
  same collision: it revokes in part the orders creating Public Water Reserves Nos. 77, 82, 85 and 12.
- EO 2755 (B75): an edge from PLO 7391 (1999) revokes an Oregon order of November 14, 1917 that created Power Site
  Reserve No. 658, a date collision with EO 2755.
- EO 431 (B75): an edge from PLO 1724 (1958) revokes the order of March 27, 1906 only "in part", per the BLM table.
  A partial revocation does not end the order. These last two flags arise because the B75 lead kind begins with
  `persists`, which makes the engine report any held ending edge.

## (a) How members end or persist

Terms used below. A *reservation* or *withdrawal* sets public land aside from settlement and sale for a stated
use. A *Public Land Order* (PLO) is the order by which, since 1942, the Secretary of the Interior makes, modifies
and revokes withdrawals under delegated presidential authority. A *finding aid* is a table that lists and
summarises documents without reproducing them. *Spent on issue* is the owner's standard term for an order whose
only command was carried out when it was signed. *Acquired lands* are lands the United States bought or received
by gift or exchange, as distinct from public-domain lands it always owned.

**M1. Spent on issue, or merged into the parent (own terms; ends; date = order date).** Under coordinator ruling
P1, an order whose only operative content revokes another order in whole or in part, restores land, or eliminates
land from a reservation is executed on signature (`spent_on_issue`); its consequence belongs to the other order's
lifecycle. A restoration that keeps a reversion, a retained tract, a reserved right or a purpose restriction is not
only a restoration and stays open. Under ruling P2, an order whose only operative content rewrites another order's
terms merges into that order on issue (`merged_into_parent_on_issue`): its text continues as part of the parent
until the parent ends, and the parent's lifecycle carries it. Five members are of this kind: EO 5458 redescribes
the EO 4410 lighthouse tract by official survey; EO 5457 amends restoration order EO 5243 so that it revokes a 1901
withdrawal and excludes reserved lighthouse and naval lands from the restoration; EO 1464 reduces the Clear Lake
Reservation and restates its hunting prohibition "within the limits of this reservation"; EO 2200 reduces the
Klamath Lake Reservation by fixing "the new boundary thereof, established by this Order"; and EO 2872 modifies the
Big Lake boundaries and restates "The reservation thus reduced in area will embrace the following lands". An order
that enlarges a reservation, even when worded as an amendment ("is hereby enlarged so as to include"), is an
operative act on land outside P2 and stays open: Congress itself treated EO 4254, an amendment that added two lots
to the 1854 Jupiter Inlet reservation, as an order under which a withdrawal still exists (43 U.S.C. 1787(b)(4)).
Orders that both revoke one reservation and create another (EO 682, 5748, 6086, 7476, 7484) are standing
reservations, not spent.

**M2. Own stated period (ends; date = stated date or last day of the stated period).** EO 3658 withdrew Isle
Royale islands "until March 5, 1923". EO 4490 (August 3, 1926) and EO 5000 (November 23, 1928) opened revoked lands
to ex-service homestead entry "for a period of 91 days, beginning with the 63rd day from and after the date hereof";
after that the lands passed to the general public land laws, which needs no continuing command. Counting from the
order dates, the periods ran from 1926-10-05 to 1927-01-03 and from 1929-01-25 to 1929-04-25, and the leads use
those last days as fixed end dates.

**M3. Revocation, supersession or replacement by a later executive order (ends; date = later order's date).**
Thirteen later orders, all held, end fourteen members in full. Eleven cite their members by number or date: EO
3469, 3470, 3642, 4490, 4832, 5515, 5748, 5945, 7485, 7537 and 7983. EO 5750 (1931-11-23) revokes the "Executive
order of November 27, 1905, which withdrew lots 8 and 9, fractional sec. 36, township 29 south, range 10 east of
the Mount Diablo meridian, California, for lighthouse purposes", which is the whole of EO 375-A by date, tract and
purpose. EO 1311 (1911-03-01) restores the same tracts "in lieu of Executive Order No. 1304"; whether EO 1304's own
restoration took effect before it was replaced is not shown, so its lead is dated by the interval between the two
orders. Where the later order re-reserves the same area (5748, 5945, 7983), the member ends and the area continues
under the new order. Under ruling P3, a later order ends a member only when its words reach it; each of these does.

**M4. Revocation by Public Land Order (ends; date = PLO signature date).** The BLM Tables of Public Land Orders
(held in `jobs/shepard-citations/output/texts/blm/`, 1942-2020) are the agency's official record of each order's
number, signature date and subject. They record 30 PLOs, 1947-2008, whose subject headings say they revoke 34
members in full, usually by number ("revoking EO No. 1664"). Many re-withdraw the same land for a refuge (for
example PLO 1511 enlarging Malheur NWR) or reserve a light station anew (PLO 1352, 1733, 1765); the member still
ends. PLO 7693 (2008) revokes the withdrawal "Established by Executive Order Dated February 4, 1909 for the Pigeon
Point Lighthouse Reservation"; EO 1020 is the only Minnesota lighthouse order of that date, and the PLO text, read
on the web, names "Executive Order No. 1020" and revokes it "in its entirety" as to the lots EO 1020 reserved. The
table gives the signature date; the Federal Register publication, which may be the effective date, follows by days.
Partial revocations ("revoking in part") do not end an order: where the table shows only a partial revocation, the
member stays open (for example EO 1039 by PLO 484, EO 2446 by PLO 2291, EO 4257 by six PLOs, EO 4254 by PLO 7202
and PLO 7765). Every PLO lead records that the PLO text is not held and that the revocation's scope, whole order
rather than part, is as the table states. One PLO is not accepted as an end: see M5 on PLO 6287.

**M5. Refuge System persistence (statute; persists, with exceptions; from 1975 to the cutoff).** 16 U.S.C.
668dd(a)(6), added in 1976 by Pub. L. 94-223 (90 Stat. 199) and renumbered in 1997, provides that each area
included in the National Wildlife Refuge System on January 1, 1975 or later, whether designated "by law, Executive
order, or secretarial order" or "so included by public land withdrawal, donation, purchase, exchange, or pursuant
to a cooperative agreement", "shall continue to be a part of the System until otherwise specified by Act of
Congress". The same paragraph says that nothing in it precludes "(i) the transfer or disposal of acquired lands
within any such area pursuant to paragraph (5)", "(ii) the exchange of lands within any such area pursuant to
subsection (b)(3)", or "(iii) the disposal of any lands within any such area pursuant to the terms of any
cooperative agreement". Paragraph (5) allows acquired System lands to be transferred or disposed of when the
Secretary finds, "with the approval of the Migratory Bird Conservation Commission", that they are no longer needed.
These exceptions matter most for the 1934-1936 orders that reserve lands "acquired or to be acquired" (B73): their
lands could leave the System lawfully without an Act of Congress, so System membership in 1975 does not by itself
show that the order's reservation survived. Separately, 43 U.S.C. 1714(j) (FLPMA sec. 204(j), 1976) bars the
Secretary from revoking "any withdrawal which added lands to the National Wildlife Refuge System prior to October
21, 1976". Until 1976 the 1966 Act had expressly preserved the Secretary's existing authority "to modify or revoke
public land withdrawals affecting lands in the System"; the 1976 amendment struck that sentence. The PLO
revocations of refuge withdrawals in 1947-1975 therefore rest on authority the statute then preserved. PLO 6287
(1982), which the BLM table lists as revoking EO 4364 and EO 5702, falls after 1714(j) took effect; EO 5702
reserved Oregon reefs as a refuge for sea lions, and EO 4364 withdrew Oregon bird rocks pending legislation for
permanent reservation. Without the PLO text the project cannot tell whether those withdrawals had added lands to
the System or how the PLO squares with 1714(j), so both members stay open (B69).

**M6. Current-law predicates naming the order or its refuge (statute or regulation; persists).** Pub. L. 100-226
sec. 3(a) (1987) directs that "land and waters in the Quillayute Needles National Wildlife Refuge and Flattery Rocks
National Wildlife Refuge established as preserves for native birds and animals by Executive orders dated October
23, 1907, as amended, which are within the boundaries of Olympic National Park, shall be administered by the United
States Fish and Wildlife Service for refuge purposes". The direction reaches only refuge lands within the park; the
section's value here is its recognition that the 1907 orders established both refuges, which the 668dd note
confirms by listing EO 703 and EO 705. 50 CFR 216.85 states that EO 1044 set aside Walrus and Otter Islands as bird
reservations and bars landing on them. 43 U.S.C. 1787(b)(4) makes the 2008 Jupiter Inlet withdrawal "subject to ...
any existing withdrawals under the Executive orders" it lists, including EO 4254. ANILCA sec. 303(1)(A) provides
that the Alaska Maritime NWR "shall consist of eleven existing refuges", among them the Chamisso, Bering Sea,
Pribilof (Walrus and Otter Islands), Aleutian Islands, Bogoslof, Forrester Island, Hazy Islands, Saint Lazaria and
Tuxedni refuges, and sec. 303(7)(A) that the Yukon Delta NWR "shall consist of the existing Clarence Rhode National
Wildlife Range, Hazen Bay National Wildlife Refuge, and Nunivak National Wildlife Refuge" and other lands. Sec. 305
(94 Stat. 2395) reads in full: "All proclamations, Executive orders, public land orders, and other administrative
actions in effect on the day before the date of the enactment of this Act with respect to units of the National
Wildlife Refuge System in the State shall remain in force and effect except to the extent that they are
inconsistent with this Act or the Alaska Native Claims Settlement Act and, in any such case, the provisions of such
Acts shall prevail. All land within the boundaries described or depicted in any such action shall, if the unit of
the National Wildlife Refuge System concerned is incorporated within any refuge established or redesignated by or
described in section 302 or 303, be included within such refuge. All funds available on such date of enactment for
administration of any refuge shall remain available for the administration of such refuge." Sec. 305 thus reaches,
as a described class, the Executive orders for the refuge units that sec. 303 names. The Fish and Wildlife
Service's 1983 boundary notice for the Alaska refuges (48 FR 7890) describes the Alaska Maritime subunits by EO
1037, 1039, 1040, 1044, 1049, 1458, 1459, 1658, 1733 and 5318, which is an official record that those orders were
treated as in effect when ANILCA passed; its Yukon Delta part names the former Nunivak refuge but no order. The
notice is read on the web and not held. With M5, each of these sources shows the order's reservation operating on
the cutoff.

**M7. Continuities (never ends).** Reorganization Plan No. II of 1939 moved the Bureau of Biological Survey to
the Department of the Interior (sec. 4(f)) and the Bureau of Lighthouses to the Coast Guard (sec. 2(a)),
effective July 1, 1939. Proclamation 2416 (July 25, 1940) renamed the "Reservations" and "Refuges" as "National
Wildlife Refuges"; for Alaska it lists old and new names for the Aleutian Islands, Bering Sea, Bogoslof, Chamisso
Island, Forrester Island, Hazy Islands, Nunivak Island, Saint Lazaria and Tuxedni Reservations. FLPMA (1976)
repealed the implied and Pickett Act withdrawal authority prospectively (sec. 704(a)) and saved existing
withdrawals (sec. 701); under ruling P3 a repeal of the authority does not end orders already made. A transfer of
a lighthouse reservation's jurisdiction (EO 6896 to the Navy, EO 5419 to the War Department) changes its holder,
not its existence.

**M8. Disposal and review programs (lead only).** Surplus-property disposal (Federal Property and Administrative
Services Act of 1949) and the National Historic Lighthouse Preservation Act of 2000 convey light stations one by
one by deed, and FLPMA sec. 204(l) required review of withdrawals in eleven western States. None ends a member by
its own terms; each ends one only through a PLO or deed that names it.

**M9. Acquired refuge lands (lead only).** The 1934-1936 orders reserve lands "acquired or to be acquired" under
the Migratory Bird Conservation Act (45 Stat. 1222). The United States holds those lands by title, and 16 U.S.C.
668dd(a)(5) lets acquired refuge lands be disposed of only with Migratory Bird Conservation Commission approval.
This favours persistence but is not a predicate that names the order, and the (a)(6) exceptions in M5 mean such
lands can leave the System without an Act of Congress.

Coordinator rulings P4 (named persons), P5 (territories that left United States sovereignty), P7 (abolition by
name of the member's only subject) and P8 (delegations of a statutory power that ceased, and periods a statute
continued) reach no member that this doctrine decides. No refuge or lighthouse order is a one-person act; the
1939 transfer of the Bureau of Lighthouses to the Coast Guard moved an agency without abolishing any reservation;
and the members that delegate or allocate statutory funds (EO 6724, 7345) or concern the Canal Zone (EO 3237) are
routed to other families on B70.

The coordinator's leads, checked: the 1939 plan and the 1940 proclamation are continuities as stated; the 1966 Act
restricts disposal of acquired lands (668dd(a)(5)) and, since 1976, keeps System areas until Congress acts, subject
to the (a)(6) exceptions; the 1997 Improvement Act (Pub. L. 105-57) renumbered these paragraphs and adds no
class-wide end. The FWS Annual Report of Lands is a current official record (FY2024 data tables), but it lists
refuge units and acreage, not executive orders, so it supplies a predicate only through a reviewed order-to-refuge
crosswalk. The FWS Federal Register boundary notices are the better acquisition where they exist, because they
name the establishing orders; the 1983 Alaska notice is the one found. The National Historic Lighthouse
Preservation Act is Pub. L. 106-355, 114 Stat. 1385.

## (b) Primary sources

Held sources were opened and the pin phrase found after collapsing whitespace; sha256 values are in the JSON.

| Id | Source | Held | Path or URL |
|---|---|---|---|
| S01, S02 | 16 U.S.C. 668dd (2024 ed.), incl. (a)(5), (a)(6) with its exceptions, the 1976 amendment note, and the "National Wildlife Refuges" note listing EO 703 and EO 705 | yes | `jobs/source-ladder/output/texts/USC_16_U.S.C._668dd_a_6_cd9a4906a8.txt` |
| S03 | 43 U.S.C. 1714(j), (l) (2024 ed.); FLPMA sec. 204, 90 Stat. 2751 | yes | `jobs/source-ladder/output/texts/USC_43_U.S.C._1714_j_._7ba3070691.txt` |
| S04 | Proclamation 2416, July 25, 1940, 54 Stat. 2717 (Alaska old and new names pinned) | yes | `jobs/astra-source-retention/output/pages/15e01816.../fab36cf0....txt` |
| S05 | Reorganization Plan No. II of 1939, secs. 2(a), 4(f), 4 F.R. 2731 (53 Stat. 1431, page not checked in a held copy) | yes | `jobs/astra-source-retention/output/pages/5437e663.../c1ca82e0....txt` |
| S06 | Pub. L. 100-226 sec. 3(a), 101 Stat. 1550 (1987) | no | https://www.govinfo.gov/content/pkg/STATUTE-101/pdf/STATUTE-101-Pg1550.pdf |
| S07 | 50 CFR 216.85 (eCFR, 2026-10-14), excerpt | yes | `jobs/current-law/output/MENTIONS.csv` |
| S08 | 43 U.S.C. 1787(b)(4)(B)(ii), listing EO 4254 | yes | `jobs/current-law/output/MENTIONS.csv` |
| S09 | 43 U.S.C. 1787(b)(4)(A), "any existing withdrawals under the Executive orders" | no | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title43-section1787&num=0&edition=prelim |
| S10 | ANILCA, Pub. L. 96-487, sec. 303(1)(A), 94 Stat. 2389; sec. 303(7)(A), 94 Stat. 2392 | no | https://www.govinfo.gov/content/pkg/STATUTE-94/pdf/STATUTE-94-Pg2371.pdf |
| S11 | ANILCA sec. 305, 94 Stat. 2395 (page from the NPS print) | no | same |
| S45 | FWS, National Wildlife Refuges in Alaska; Description of Boundaries, 48 FR 7890 (Feb. 24, 1983) | no | https://www.govinfo.gov/link/fr/48/7890?link-type=pdf |
| S20-S30 | EO 4832, 3470, 3469, 3642, 4490, 5515, 5748, 5945, 7485, 7537, 7983 (revoking orders) | yes | ProQuest and APP texts named in the JSON |
| S31 | EO 5750, Nov. 23, 1931 (revokes EO 375-A by date and tract) | yes | `jobs/ofr-compilations/output/texts/EO_5750.txt` |
| S33 | EO 1311, Mar. 1, 1911 ("in lieu of Executive Order No. 1304") | yes | `jobs/pinakes-proquest-ingest/output/texts/EO_1311.txt` |
| S34 | EO 7836, Mar. 11, 1938 (date collision with EO 3658) | yes | `jobs/app-executive-orders/output/texts/executive-order-7836-public-water-restoration-no-80.txt` |
| SM | The member's own order text (kind `member_text`; path, sha256 and grade recorded on each lead) | member | per lead |
| S32 | EO 3957 (restores the Blackbeard Island reservation) | yes | `jobs/pinakes-proquest-ingest/output/texts/EO_3957.txt` |
| S46 | Proclamation 2112, Jan. 4, 1935 (revokes EO 779; Statutes at Large page unverified) | no | https://www.presidency.ucsb.edu/documents/proclamation-2112-fort-jefferson-national-monument-florida |
| S-BLM-* | BLM Tables of Public Land Orders 1-694 through 6826-7342, 7679-7715 and 7753-7787 (finding aids) | yes | `jobs/shepard-citations/output/texts/blm/plo_*.txt` |
| S-PLO-* | 31 PLOs (30 ending members, plus PLO 6287), each at its Federal Register page | no | `https://www.govinfo.gov/link/fr/<vol>/<page>?link-type=pdf` |
| S40 | FLPMA secs. 701, 704(a), 90 Stat. 2743 (section pages not verified) | no | https://www.govinfo.gov/content/pkg/STATUTE-90/pdf/STATUTE-90-Pg2743.pdf |
| S41 | National Historic Lighthouse Preservation Act, Pub. L. 106-355, 114 Stat. 1385 | no | https://www.govinfo.gov/content/pkg/STATUTE-114/pdf/STATUTE-114-Pg1385.pdf |
| S42 | Federal Property and Administrative Services Act of 1949, 63 Stat. 377 | no | https://www.govinfo.gov/content/pkg/STATUTE-63/pdf/STATUTE-63-Pg377.pdf |
| S43 | Migratory Bird Conservation Act, 45 Stat. 1222 (1929) | no | https://www.govinfo.gov/content/pkg/STATUTE-45/pdf/STATUTE-45-Pg1222.pdf |
| S44 | FWS Annual Report of Lands, data tables as of 2024-09-30 (Table 3) | no | https://www.fws.gov/sites/default/files/documents/2025-05/2024_annual_report_of_lands_data_tables.pdf |

Held: 30 sources plus the member's own text; to acquire: 42, all in
`research/pothier/work/PD-REFUGE-LIGHTHOUSE/FETCH_PROPOSED.jsonl`, which also carries three further requests (the
full 50 CFR 216.85, the 1975 FWS land report and PLO 7202).

## (c) Decision procedure

Branches are tried in order; the first whose conditions hold decides. Members are named by `instrument_id` where
the deciding instrument is specific to them, with a text check where the order's own words can confirm the match.

- **B01 `yes` (CURRENT), EO 703, 705.** Pub. L. 100-226 sec. 3(a) names the refuges and their 1907 orders for refuge
  lands within Olympic National Park; the 668dd note lists both orders; 668dd(a)(6) continues the areas. Gaps: the
  1987 Act is read on the web; refuge lands outside the park rest on the note and (a)(6) alone; no FWS record naming
  the order is held.
- **B02 `yes` (CURRENT), EO 1044.** 50 CFR 216.85 names the order and enforces its reservation; ANILCA secs. 303 and
  305 add a statutory basis, and the 1983 FWS notice describes the Pribilof subunit by EO 1044. Gaps: only the eCFR
  excerpt is held; the FWS notice is read on the web.
- **B03 `yes` (CURRENT), EO 4254.** 43 U.S.C. 1787(b)(4) lists the order among those under which existing
  withdrawals stand; PLO 7202 (1996) and PLO 7765 (2011) revoked Jupiter Inlet withdrawals only in part. Gaps:
  subsec. (b)(4)(A) and the PLO texts are not held.
- **B04 `yes` (CURRENT), ten Alaska orders.** Sec. 305 keeps in force the Executive orders for the Alaska refuge
  units that sec. 303 incorporates; 668dd(a)(6) keeps the areas until Congress acts. Each member maps to its sec.
  303 refuge through held text: seven orders name the reservation they create ("This reservation to be known as
  Bering Sea Reservation"); EO 5095's title reads "for Establishment of Nunivak Island Reservation"; EO 5318 and EO
  5470 add lands "to and made part of" the Aleutian Islands Reservation and the Nunivak Island Reservation; and
  Proclamation 2416 (held) renamed each of those reservations as the refuge whose name sec. 303 uses. Eight of the
  ten orders created a reservation; EO 5318 and EO 5470 enlarged one. Gaps: ANILCA is not held, so these leads wait
  on its acquisition; the 1983 FWS notice, which names EO 1037, 1039, 1040, 1049, 1458, 1459, 1658 and 5318, is read
  on the web; for EO 5095 and 5470 no record names the order, so their being in effect in 1980 is inferred from sec.
  303(7)(A)'s naming the Nunivak refuge as existing; EO 5095 also set the island apart for Agriculture Department
  reindeer, caribou and musk-ox experiments, and whether sec. 305 keeps those non-refuge purposes in force is not
  settled, so the lead is that the order is in force at least as to its refuge reservation; partial ANCSA
  conveyances or PLOs (EO 1039 by PLO 484; EO 5095 by PLO 1177) leave the orders in force as amended.
- **B10-B20 `no` (ACT), 12 members, fixed date of the later order.** EO 763 and 1057 (EO 4832, 1928-03-17); 961
  (EO 3470, 1921-05-20); 2438 (EO 3469, 1921-05-20); 1041 (EO 3642, 1922-02-27); 1763 (EO 4490, 1926-08-03); 5349
  (EO 5515, 1930-12-15); 4626 (EO 5748, 1931-11-12); 4975 (superseded by EO 5945, 1932-11-03); 2124 (EO 7485,
  1936-11-06); 5097 (superseded by EO 7537, 1937-01-14); 369-A (EO 7983, 1938-10-04). Gap: the held texts are
  machine-read copies. EO 4975 carries the EO 7341 flag explained above.
- **B21 `no` (ACT), EO 375-A, 1931-11-23.** EO 5750 revokes the order of November 27, 1905 that withdrew lots 8 and
  9, fractional sec. 36, T. 29 S., R. 10 E., Mount Diablo Meridian, for lighthouse purposes, which is the whole of
  the member. Gaps: the match rests on identical date, tract, State and purpose, not on the number; the texts are
  OCR copies; a BLM row for PLO 541 (1948) that revokes an Alaska order of the same date is a date collision.
- **B22 `no` (ACT), EO 1304, interval 1911-02-18 to 1911-03-01.** EO 1311 restores the same tracts "in lieu of
  Executive Order No. 1304". Whether EO 1304's restoration took effect on its date or was displaced before taking
  effect, it had no command left once EO 1311 issued.
- **B30-B59 `no` (ACT), 34 members, fixed PLO signature date.** 6086 (PLO 378, 1947); 942 (446, 1948); 6065 (501,
  1948); 2759 (521, 1948); 409 and 3502 (650, 1950); 5522 (732, 1951); 675 (892, 1953); 5122 (912, 1953); 6912
  (954, 1954); 1292 (1352, 1956); 4501 (1423, 1957); 929, 5891 and 6152 (1511, 1957); 3671 (1561, 1957); 1775
  (1584, 1958); 5562 (1636, 1958); 2638 (1733, 1958); 3079 (1765, 1958); 6761 (2196, 1960); 4391 (2306, 1961); 6673
  (2358, 1961); 7476 (2494, 1961); 936 (2933, 1963); 4387 (2960, 1963); 4328 (3463, 1964); 5903 and 6697 (4371,
  1968); 1664 (4466, 1968); 718 (4597, 1969); 5727 (4911, 1970); 1959 (5515, 1975); 1020 (7693, 2008). Gaps: PLO
  texts not held, and each revocation's whole-order scope is as the BLM table states; the BLM row for PLO 892 cites
  "EO of Aug. 8, 1907" (Louisiana) by date only, for PLO 650 "EOs of Feb. 10, 1906", and for PLO 7693 "Executive
  Order Dated February 4, 1909" (Minnesota, Pigeon Point), so those matches rest on date and place in the held
  table (the PLO 7693 text, read on the web, names EO 1020 by number); the effective date may be the Federal
  Register date (2008-03-25 for PLO 7693); held edges from EO 8821 (1941) on EO 6065 quote a clause that "shall not
  rescind or revoke" it.
- **B60 `no` (TERM), EO 3658, 1923-03-05.** Own stated end date. Gaps: an extension, if any, is not held; the PLO
  1300 and EO 7836 edges are date collisions with Public Water Reserve No. 82, explained above.
- **B61, B62 `no` (TERM), EO 4490 (1927-01-03) and EO 5000 (1929-04-25).** The revocation was executed on
  signature; the 91-day preference, beginning on the 63rd day after the order, ended on the fixed date given.
- **B63 `no` (TERM, `spent_on_issue`), 17 members, order date.** Pure revocations, restorations and eliminations
  of land with no reversion, retained tract, reserved right, purpose restriction or restated parent terms: EO 1311,
  3187, 3422, 3469, 3470, 347-A, 3540, 3642, 4076, 4832, 4904, 5515, 5750, 6891, 701, 7485, 793. A text check
  requires a revoking, restoring or eliminating word in the member's own text (the OCR of EO 347-A reads "Ganeele"
  for "cancelled", and the pattern allows it). Gaps: EO 3671 (1922) later reserved one tract that EO 1311 restored,
  a new reservation decided on B42; an edge on EO 701 from PLO 1705 (1958) concerns Power Site Reserve No. 701.
- **B64 `no` (TERM, `merged_into_parent_on_issue`), EO 1464, 2200, 2872, 5457 and 5458, order date.** Rewriting
  the parent's terms is the only operative content and no land is added. Disclosure on each lead: its text continues
  as part of the parent until the parent ends; the parent's lifecycle carries it (parents EO 1332, 924, 2230, 5243
  and 4410). If the owner treats an amending order as living as long as the amended text lives, these five become
  open pending the parent. EO 2872 carries the EO 3964 and EO 5747 flag explained above.
- **B68 `open`, EO 779.** Proclamation 2112 (January 4, 1935), read on the web, states "do hereby revoke the
  aforesaid Executive Order No. 779, of April 6, 1908"; no copy is held. Once a copy is held and the phrase pinned,
  the lead becomes `no`, basis ACT, 1935-01-04.
- **B69 `open`, EO 4364 and EO 5702.** The BLM table lists PLO 6287 (1982-06-16) as "withdrawing lands for addition
  to Oregon Islands National Wildlife Refuge; revoking EO Nos. 4082, 4364, 4774 and 5702", but 43 U.S.C. 1714(j)
  bars the Secretary from revoking withdrawals that added lands to the Refuge System before October 21, 1976. The
  PLO text would show whether these withdrawals had added lands to the System and whether the revocation is valid
  (for example, as a replacement by a new withdrawal for the same refuge). If valid, the lead is `no`, ACT,
  1982-06-16 or the Federal Register date; if not, the question becomes the order's own persistence under
  668dd(a)(6).
- **B70 `open`, 7 members of other families.** Their own texts show other kinds of order: EO 1485 (Indian-
  reservation restoration, PD-INDIAN), EO 2012 (relief of Americans abroad, 1914, PD-WAR-EMERGENCY), EO 3036 (civil
  service schedule, PD-CS-RULES), EO 2670 (Virgin Islands lighthouse administration, PD-ADMIN), EO 6724 and 7345
  (fund and acquisition authorizations, PD-ADMIN), EO 3237 (Canal Zone naval radio site, PD-CLASS-EVENTS
  canal_zone). The engine assigns each member to one doctrine by its class type, so these stay open here until the
  class engine retypes them; no doctrine decides them meanwhile.
- **B71 `open`, EO 1993 and 2203.** EO 2203 vacated the 1914 Blackbeard Island reservation and added a standing
  bar on hunting permits; EO 3957 (1924) restored the reservation, but the verb it applies to EO 2203 is illegible
  in the held copy.
- **B72 `open`, 16 temporary withdrawals.** Withdrawals "pending" legislation, classification or selection, or
  "temporarily withdrawn", end only when revoked; none is revoked in full in a held source (EO 1814, 2047 and
  2599 were revoked only in part; EO 2177 expressly left 1814 and 2047 standing; EO 5971 declared that the EO 4939
  withdrawal "remains in full force and effect"; PLO 7486 (2001) only partly revoked the Sanak Harbor lighthouse
  withdrawal that EO 7032 may cover).
- **B73 `open`, 20 refuge orders on acquired lands.** If the area was in the System on or after 1975-01-01,
  668dd(a)(6) keeps it there until Congress acts, but the paragraph's exceptions let acquired lands be transferred
  or disposed of (with Migratory Bird Conservation Commission approval), exchanged, or disposed of under a
  cooperative agreement without an Act of Congress. Persistence needs both a link from the order to a current
  refuge unit and evidence that its lands did not leave under those exceptions; neither is held.
- **B74 `open`, 59 other refuge orders.** Persistence depends on the 1975 System membership of the order's area (M5),
  subject to the same exceptions; no held record links these orders to current refuge units. A held restoration
  edge on EO 923 (Key West) comes from EO 10383, which concerns an order No. 923 of the Governor of Hawaii.
- **B75 `open`, 49 lighthouse reservations and transfers.** No held full revocation or deed. Later held BLM
  headings show only partial revocations that may reach some of them (PLO 7583, 2003, Ediz Hook; PLO 7723, 2008,
  lighthouse withdrawals for Channel Islands National Park, which may cover the San Miguel, Prince and Santa Barbara
  Island orders). EO 431 and EO 2755 carry the flags explained above.
- **B99 `open`, catch-all.** Reached by no member.

## (d) Members not decided

156 members stay open. 79 refuge reservations (B73, B74) could be decided `yes` by one acquisition program: the
FWS refuge-description notices in the Federal Register where they name establishing orders (as the 1983 Alaska
notice does), or the FWS land records (the Annual Report of Lands as of 1975 and as of the cutoff, or each
refuge's establishing-document file) matched to the orders by a reviewed crosswalk, applying 668dd(a)(6); for the
acquired-land orders the same records must also show that the lands did not leave the System under the (a)(6)
exceptions. Some will instead turn out to have been revoked by PLOs that cite them by date or by reserve name,
which a search by number and full date can miss. 49 lighthouse reservations and 16 temporary withdrawals need a
PLO or deed naming each order. The held BLM tables (1942-2020) and the held executive-order texts were searched by
member number and by full written date, so remaining revocations would cite the order by an older date form, by
reserve or station name, or not appear in BLM's summaries. Two Oregon orders need the PLO 6287 text, EO 779 needs a
held copy of Proclamation 2112, seven are other families' orders, and two need a legible EO 3957.

## Choices that remain the owner's

1. Under ruling P2, EO 1464, 2200, 2872, 5457 and 5458 merge into their parents on issue. If the owner treats an
   amending order as living as long as the amended text lives, they become open pending the parent.
2. The ten Alaska `yes` leads rest on ANILCA, which is not yet held, and on the 1983 FWS notice for eight of them;
   they should be confirmed when both are acquired. Whether sec. 305 keeps EO 5095's non-refuge purposes in force is
   a question of the order's scope that the lead does not settle.
3. The 34 PLO leads rest on BLM's official tables; acquiring the Federal Register pages would confirm each
   revocation's terms, scope and effective date. PLO 6287 needs the same acquisition before EO 4364 and EO 5702
   can be decided at all.
