# PD-REFUGE-LIGHTHOUSE: bird and wildlife refuges and lighthouse reservations, 1905-1936

Doctrine for the 243 orders that the class engine typed `bird_refuge` (169) or `lighthouse_reservation` (74).
Machine form: `research/pothier/doctrines/PD-REFUGE-LIGHTHOUSE.json` (schema `pothier-family-doctrine/v1`).
Every lead below is a proposal for the owner, not a status.

## Conclusions

The doctrine decides 87 of the 243 members and leaves 156 open.

- **14 `yes` leads (in force on 2026-10-14), basis CURRENT.** Each rests on a statute or regulation in force on
  the cutoff that names the order or its refuge and keeps the reservation operating. EO 703 and EO 705 (Flattery
  Rocks and Quillayute Needles) are named by Pub. L. 100-226 sec. 3 and the current 16 U.S.C. 668dd note. EO 1044
  (Walrus and Otter Islands) is named by 50 CFR 216.85. EO 4254 (Jupiter Inlet lighthouse) is listed by
  43 U.S.C. 1787(b)(4) as an order under which a withdrawal exists. Ten Alaska bird-reservation orders (1037,
  1039, 1040, 1049, 1458, 1459, 1658, 5095, 5318, 5470) created refuges that ANILCA sec. 303 (1980) names as
  "existing" and folds into today's Alaska Maritime and Yukon Delta refuges, and ANILCA sec. 305 provides that the
  Executive orders for those units "shall remain in force and effect". The ten Alaska leads wait on acquisition of
  ANILCA, which is read on the web and not held.
- **73 `no` leads (ended before the cutoff).**
  - 12 were revoked or superseded in full by a later executive order whose text the project holds (basis ACT,
    the later order's date).
  - 35 were revoked in full by a Public Land Order (PLO) of the Secretary of the Interior between 1947 and 1982,
    as recorded in the Bureau of Land Management's official Table of Public Land Orders, which the project holds
    (basis ACT, PLO signature date). The PLO texts themselves are not held, so every one of these leads carries
    that gap until the Federal Register pages are acquired.
  - 26 ended by their own terms (basis TERM): 21 orders whose only operative content revokes, restores or reduces
    another reservation and are spent on issue (coordinator ruling P1); 2 orders whose only operative content
    amends another order without adding land and merge into that order on issue (ruling P2); EO 3658, which
    withdrew Isle Royale islands "until March 5, 1923"; and EO 4490 and EO 5000, which revoked reservations and
    gave ex-servicemen a 91-day homestead preference that ran out within five months.
- **156 `open` leads.** 80 refuge reservations (B73, B74), 51 lighthouse reservations and transfers (B75) and
  16 temporary withdrawals (B72) have no held full revocation and no held current record naming the order. For
  refuges, the National Wildlife Refuge System statute makes persistence turn on one fact the project does not
  hold: whether the order's lands were in the Refuge System on or after January 1, 1975. For lighthouse
  reservations, the end, where there is one, is a station-by-station PLO or deed. Seven members are other kinds
  of order and should go to other families (B70); two, the Blackbeard Island chain, need a legible copy of EO
  3957 (B71).

Final `try` counts (`python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-REFUGE-LIGHTHOUSE.json --hints`):
243 members; decides 87; contradicted 5. By branch: B01 2, B02 1, B03 1, B04 10 (`yes` 14); B10-B20 12, B30-B59 35,
B60 1, B61 1, B62 1, B63 21, B64 2 (`no` 73); B70 7, B71 2, B72 16, B73 20, B74 60, B75 51, B99 0 (`open` 156).

The five flags come from held later-event edges, and none changes a lead. Two are events of another order: EO 3964 and
EO 5747 modify the parent Big Lake Reservation (EO 2230) that they cite with spent EO 2872, and EO 7341 enlarges
the refuge of EO 5945, which superseded EO 4975. Two are date collisions: PLO 1300 (1956) modifies a Utah water
reserve of April 4, 1922, not EO 3658, and PLO 7391 (1999) revokes an Oregon power-site order of November 14,
1917, not EO 2755. One is partial: PLO 1724 (1958) revokes EO 431 only "in part". Each is disclosed in the
gaps of its branch.

## (a) How members end or persist

Terms used below. A *reservation* or *withdrawal* sets public land aside from settlement and sale for a stated
use. A *Public Land Order* (PLO) is the order by which, since 1942, the Secretary of the Interior makes, modifies
and revokes withdrawals under delegated presidential authority. A *finding aid* is a table that lists and
summarises documents without reproducing them. *Spent on issue* is the owner's standard term for an order whose
only command was carried out when it was signed.

**M1. Spent on issue, or merged into the parent (own terms; ends; date = order date).** Under coordinator ruling
P1, an order whose only operative content revokes another order, restores land or reduces a reservation is
executed on signature (`spent_on_issue`); its consequence belongs to the other order's lifecycle. A restoration
that keeps a reversion, a retained tract, a reserved right or a purpose restriction is not only a restoration and
stays open. Under ruling P2, an order whose only operative content amends another order merges into that order on
issue (`merged_into_parent_on_issue`): its text continues as part of the parent until the parent ends, and the
parent's lifecycle carries it. Two members are of this kind: EO 5458 redescribes the EO 4410 lighthouse tract by
official survey, and EO 5457 amends restoration order EO 5243 so that it revokes a 1901 withdrawal and excludes
reserved lighthouse and naval lands from the restoration. An order that enlarges a reservation, even when worded as an amendment ("is hereby enlarged so as to
include"), is an operative act on land outside P2 and stays open: Congress itself treated EO 4254, an amendment that added two
lots to the 1854 Jupiter Inlet reservation, as an order under which a withdrawal still exists (43 U.S.C.
1787(b)(4)). Orders that both revoke one reservation and create another (EO 682, 5748, 6086, 7476, 7484)
are standing reservations, not spent.

**M2. Own stated period (ends; date = stated date or end of stated period).** EO 3658 withdrew Isle Royale islands
"until March 5, 1923". EO 4490 and EO 5000 opened revoked lands to ex-service homestead entry "for a period of 91
days, beginning with the 63rd day" after the order; after that the lands passed to the general public land laws,
which needs no continuing command. The 91-day periods ended by 1927-01-03 and 1929-04-25.

**M3. Revocation or supersession by a later executive order (ends; date = later order's date).** Eleven later
orders, all held, revoke or supersede twelve members in full, citing them by number or date: EO 3469, 3470, 3642,
4490, 4832, 5515, 5748, 5945, 7485, 7537 and 7983. Where the later order re-reserves the same area (5748, 5945,
7983), the member ends and the area continues under the new order.

**M4. Revocation by Public Land Order (ends; date = PLO signature date).** The BLM tables of Public Land Orders
(held in `jobs/shepard-citations/output/texts/blm/`) are the agency's official record of each order's number,
signature date and subject. They record 30 PLOs, 1947-1982, whose subject headings say they revoke 35 members in
full, usually by number ("revoking EO No. 1664"). Many re-withdraw the same land for a refuge
(for example PLO 1511 enlarging Malheur NWR, PLO 6287 adding to Oregon Islands NWR) or reserve a light station
anew (PLO 1352, 1733, 1765); the member still ends. The table gives the signature date; the Federal Register
publication, which may be the effective date, follows by days. Partial revocations ("revoking in part") do not
end an order: where the table shows only a partial revocation, the member stays open (for example EO 1039 by PLO
484, EO 2446 by PLO 2291, EO 4257 by six PLOs, EO 4254 by PLO 7202). Every PLO lead records that the PLO text is
not held and that the revocation's scope, whole order rather than part, is as the table states.

**M5. Refuge System persistence (statute; persists; from 1975 to the cutoff).** 16 U.S.C. 668dd(a)(6), added in
1976 by Pub. L. 94-223 (90 Stat. 199) and renumbered in 1997, provides that each area included in the National
Wildlife Refuge System on January 1, 1975 or later, whether designated "by law, Executive order, or secretarial
order" or "included by public land withdrawal", "shall continue to be a part of the System until otherwise
specified by Act of Congress". 43 U.S.C. 1714(j) (FLPMA sec. 204(j), 1976) bars the Secretary from revoking "any
withdrawal which added lands to the National Wildlife Refuge System prior to October 21, 1976". Before 1976 the
1966 Act let the Secretary revoke refuge withdrawals, which is why so many PLO revocations fall in 1947-1975. The
statute turns a refuge order's persistence into one factual question: was its area in the System on or after
1975-01-01, and has Congress since removed it?

**M6. Current-law predicates naming the order or its refuge (statute or regulation; persists).** Pub. L. 100-226
sec. 3 (1987) directs that the Flattery Rocks and Quillayute Needles refuges "established ... by Executive orders
dated October 23, 1907, as amended" be administered as refuges. 50 CFR 216.85 states that EO 1044 set aside
Walrus and Otter Islands as bird reservations and bars landing on them. 43 U.S.C. 1787(b)(4) makes the 2008
Jupiter Inlet withdrawal "subject to ... any existing withdrawals under the Executive orders" it lists, including
EO 4254. ANILCA sec. 303 (1980) incorporates "the existing" Chamisso, Bering Sea, Pribilof (Walrus and Otter
Islands), Aleutian Islands, Bogoslof, Forrester Island, Hazy Islands, Saint Lazaria and Tuxedni National Wildlife
Refuges into the Alaska Maritime NWR and the existing Nunivak refuge into the Yukon Delta NWR. Sec. 305 reads: "All
proclamations, Executive orders, public land orders, and other administrative actions in effect on the day before
the date of the enactment of this Act with respect to units of the National Wildlife Refuge System in the State
shall remain in force and effect except to the extent that they are inconsistent with this Act or the Alaska Native
Claims Settlement Act and, in any such case, the provisions of such Acts shall prevail. All land within the
boundaries described or depicted in any such action shall, if the unit of the National Wildlife Refuge System
concerned is incorporated within any refuge established or redesignated by or described in section 302 or 303, be
included within such refuge." Sec. 305 thus reaches, as a described class, the Executive orders for the refuge
units that sec. 303 names. With M5, each of these sources shows the order's reservation operating on the cutoff.

**M7. Continuities (never ends).** Reorganization Plan No. II of 1939 moved the Bureau of Biological Survey to
the Department of the Interior (sec. 4(f)) and the Bureau of Lighthouses to the Coast Guard (sec. 2(a)),
effective July 1, 1939. Proclamation 2416 (July 25, 1940) renamed the "Reservations" and "Refuges" as "National
Wildlife Refuges"; for Alaska it lists old and new names for the Aleutian Islands, Bering Sea, Bogoslof,
Chamisso Island, Forrester Island, Hazy Islands, Nunivak Island, Saint Lazaria and Tuxedni Reservations. FLPMA (1976) repealed the implied and Pickett Act withdrawal authority prospectively (sec.
704(a)) and saved existing withdrawals (sec. 701). A transfer of a lighthouse reservation's jurisdiction (EO 6896
to the Navy, EO 5419 to the War Department) changes its holder, not its existence.

**M8. Disposal and review programs (lead only).** Surplus-property disposal (Federal Property and Administrative
Services Act of 1949) and the National Historic Lighthouse Preservation Act of 2000 convey light stations one by
one by deed, and FLPMA sec. 204(l) required review of withdrawals in eleven western States. None ends a member by
its own terms; each ends one only through a PLO or deed that names it.

**M9. Acquired refuge lands (lead only).** The 1934-1936 orders reserve lands "acquired or to be acquired" under
the Migratory Bird Conservation Act (45 Stat. 1222). The United States holds those lands by title; 16 U.S.C.
668dd(a)(5) lets acquired refuge lands be disposed of only with Migratory Bird Conservation Commission approval.
This favours persistence but is not a predicate that names the order.

The coordinator's leads, checked: the 1939 plan and the 1940 proclamation are continuities as stated; the 1966 Act
does restrict disposal (668dd(a)(5)) and, since 1976, keeps System areas until Congress acts (668dd(a)(6)); the
1997 Improvement Act (Pub. L. 105-57) renumbered these paragraphs and adds no class-wide end. The FWS Annual Report
of Lands exists as a current official record (FY2024 data tables), but it lists refuge units and acreage, not
executive orders, so it supplies a predicate only through a reviewed order-to-refuge crosswalk. The National
Historic Lighthouse Preservation Act is Pub. L. 106-355, 114 Stat. 1385.

## (b) Primary sources

Held sources were opened and the pin phrase found after collapsing whitespace; sha256 values are in the JSON.

| Id | Source | Held | Path or URL |
|---|---|---|---|
| S01, S02 | 16 U.S.C. 668dd (2024 ed.), incl. (a)(5), (a)(6), 1976 amendment note, and the "National Wildlife Refuges" note listing EO 703 and EO 705 | yes | `jobs/source-ladder/output/texts/USC_16_U.S.C._668dd_a_6_cd9a4906a8.txt` |
| S03 | 43 U.S.C. 1714(j), (l) (2024 ed.); FLPMA sec. 204, 90 Stat. 2751 | yes | `jobs/source-ladder/output/texts/USC_43_U.S.C._1714_j_._7ba3070691.txt` |
| S04 | Proclamation 2416, July 25, 1940, 54 Stat. 2717 (Alaska old and new names pinned) | yes | `jobs/astra-source-retention/output/pages/15e01816.../fab36cf0....txt` |
| S05 | Reorganization Plan No. II of 1939, secs. 2(a), 4(f), 4 F.R. 2731 (53 Stat. 1431, page not checked in a held copy) | yes | `jobs/astra-source-retention/output/pages/5437e663.../c1ca82e0....txt` |
| S06 | Pub. L. 100-226 sec. 3, 101 Stat. 1550 (1987) | no | https://www.govinfo.gov/content/pkg/STATUTE-101/pdf/STATUTE-101-Pg1550.pdf |
| S07 | 50 CFR 216.85 (eCFR, 2026-10-14), excerpt | yes | `jobs/current-law/output/MENTIONS.csv` |
| S08 | 43 U.S.C. 1787(b)(4)(B)(ii), listing EO 4254 | yes | `jobs/current-law/output/MENTIONS.csv` |
| S09 | 43 U.S.C. 1787(b)(4)(A), "any existing withdrawals under the Executive orders" | no | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title43-section1787&num=0&edition=prelim |
| S10 | ANILCA, Pub. L. 96-487, sec. 303(1), 94 Stat. 2389; sec. 303(7), 94 Stat. 2392 | no | https://www.govinfo.gov/content/pkg/STATUTE-94/pdf/STATUTE-94-Pg2371.pdf |
| S11 | ANILCA sec. 305, 94 Stat. 2394-2395 (page from the NPS electronic version) | no | same |
| S20-S30 | EO 4832, 3470, 3469, 3642, 4490, 5515, 5748, 5945, 7485, 7537, 7983 (revoking orders) | yes | ProQuest and APP texts named in the JSON |
| SM | The member's own order text (kind `member_text`; path, sha256 and grade recorded on each lead) | member | per lead |
| S32 | EO 3957 (restores the Blackbeard Island reservation) | yes | `jobs/pinakes-proquest-ingest/output/texts/EO_3957.txt` |
| S-BLM-* | BLM Tables of Public Land Orders 1-694 through 6826-7342 (finding aids) | yes | `jobs/shepard-citations/output/texts/blm/plo_*.txt` |
| S-PLO-* | 30 PLOs, each at its Federal Register page | no | `https://www.govinfo.gov/link/fr/<vol>/<page>?link-type=pdf` |
| S40 | FLPMA secs. 701, 704(a), 90 Stat. 2743 (section pages not verified) | no | https://www.govinfo.gov/content/pkg/STATUTE-90/pdf/STATUTE-90-Pg2743.pdf |
| S41 | National Historic Lighthouse Preservation Act, Pub. L. 106-355, 114 Stat. 1385 | no | https://www.govinfo.gov/content/pkg/STATUTE-114/pdf/STATUTE-114-Pg1385.pdf |
| S42 | Federal Property and Administrative Services Act of 1949, 63 Stat. 377 | no | https://www.govinfo.gov/content/pkg/STATUTE-63/pdf/STATUTE-63-Pg377.pdf |
| S43 | Migratory Bird Conservation Act, 45 Stat. 1222 (1929) | no | https://www.govinfo.gov/content/pkg/STATUTE-45/pdf/STATUTE-45-Pg1222.pdf |
| S44 | FWS Annual Report of Lands, data tables as of 2024-09-30 (Table 3) | no | https://www.fws.gov/sites/default/files/documents/2025-05/2024_annual_report_of_lands_data_tables.pdf |

Held: 25 sources plus the member's own text; to acquire: 39 (all in `research/pothier/work/PD-REFUGE-LIGHTHOUSE/FETCH_PROPOSED.jsonl`, with
four further requests).

## (c) Decision procedure

Branches are tried in order; the first whose conditions hold decides. Members are named by `instrument_id` where
the deciding instrument is specific to them, with a text check where the order's own words can confirm the match.

- **B01 `yes` (CURRENT), EO 703, 705.** Pub. L. 100-226 sec. 3 and the 668dd note name the orders' refuges and
  their 1907 orders; 668dd(a)(6) continues them. Gaps: the 1987 Act is read on the web; no FWS record naming the
  order is held.
- **B02 `yes` (CURRENT), EO 1044.** 50 CFR 216.85 names the order and enforces its reservation; ANILCA secs. 303
  and 305 add a statutory basis. Gap: only the eCFR excerpt is held.
- **B03 `yes` (CURRENT), EO 4254.** 43 U.S.C. 1787(b)(4) lists the order among those under which existing
  withdrawals stand; PLO 7202 (1996) revoked it only in part. Gaps: subsec. (b)(4)(A) and PLO 7202 not held.
- **B04 `yes` (CURRENT), ten Alaska orders.** Sec. 305 keeps in force the Executive orders for the Alaska refuge
  units that sec. 303 incorporates; 668dd(a)(6) keeps the areas until Congress acts. The member maps to its sec.
  303 refuge through its own words and a held instrument: eight orders name their reservation ("This reservation
  to be known as Bering Sea Reservation"), EO 5318 and 5470 add lands to the "Aleutian Islands Reservation" and the
  "Nunivak Island Reservation", and Proclamation 2416 (held) renamed each of those reservations as the National
  Wildlife Refuge whose name sec. 303 uses. EO 5095 gives no reservation name; its link to the Nunivak Island
  Reservation rests on the island name alone, and the basis and gaps say so. Gaps: ANILCA is not held, so these
  leads wait on its acquisition; that each order was still in effect on December 1, 1980 is inferred from sec.
  303's naming the refuge as existing; partial ANCSA conveyances or PLOs (EO 1039 by PLO 484; EO 5095 by PLO 1177)
  leave the orders in force as amended.
- **B10-B20 `no` (ACT), 12 members, fixed date of the later order.** EO 763 and 1057 (EO 4832, 1928-03-17); 961
  (EO 3470, 1921-05-20); 2438 (EO 3469, 1921-05-20); 1041 (EO 3642, 1922-02-27); 1763 (EO 4490, 1926-08-03); 5349
  (EO 5515, 1930-12-15); 4626 (EO 5748, 1931-11-12); 4975 (superseded by EO 5945, 1932-11-03); 2124 (EO 7485,
  1936-11-06); 5097 (superseded by EO 7537, 1937-01-14); 369-A (EO 7983, 1938-10-04). Gap: the held texts are
  machine-read copies.
- **B30-B59 `no` (ACT), 35 members, fixed PLO signature date.** 6086 (PLO 378, 1947); 942 (446, 1948); 6065 (501,
  1948); 2759 (521, 1948); 409 and 3502 (650, 1950); 5522 (732, 1951); 675 (892, 1953); 5122 (912, 1953); 6912
  (954, 1954); 1292 (1352, 1956); 4501 (1423, 1957); 929, 5891 and 6152 (1511, 1957); 3671 (1561, 1957); 1775
  (1584, 1958); 5562 (1636, 1958); 2638 (1733, 1958); 3079 (1765, 1958); 6761 (2196, 1960); 4391 (2306, 1961); 6673
  (2358, 1961); 7476 (2494, 1961); 936 (2933, 1963); 4387 (2960, 1963); 4328 (3463, 1964); 5903 and 6697 (4371,
  1968); 1664 (4466, 1968); 718 (4597, 1969); 5727 (4911, 1970); 1959 (5515, 1975); 4364 and 5702 (6287, 1982).
  Gaps: PLO texts not held, and each revocation's whole-order scope is as the BLM table states; the BLM row for PLO 892 cites "EO of Aug. 8, 1907" (Louisiana) by date only, and for
  PLO 650 "EOs of Feb. 10, 1906", so those two matches rest on date and place; effective date may be the
  Federal Register date.
- **B60 `no` (TERM), EO 3658, 1923-03-05.** Own stated end date. Gap: an extension, if any, is not held.
- **B61, B62 `no` (TERM), EO 4490 and EO 5000.** Revocation executed on signature; 91-day preference ran out by
  1927-01-04 and 1929-04-26 (interval from order date).
- **B63 `no` (TERM, `spent_on_issue`), 21 members, order date.** Pure revocations, restorations and reductions
  with no reversion, retained tract, reserved right or purpose restriction: EO 1304, 1311, 1464, 2200, 2872, 3187,
  3422, 3469, 3470, 347-A, 3540, 3642, 4076, 4832, 4904, 5515, 5750, 6891, 701, 7485, 793. A text check requires a
  revoking or reducing word in the member's own text.
- **B64 `no` (TERM, `merged_into_parent_on_issue`), EO 5457 and 5458, order date.** Amendment is the only
  operative content and no land is added. Disclosure on each lead: its text continues as part of the parent until
  the parent ends; the parent's lifecycle carries it. If the owner treats an amending order as living as long as
  the amended text lives, these two become open pending the parent.
- **B70 `open`, 7 members of other families.** Their own texts show other kinds of order; they stay open here
  with the family that should decide them: EO 1485 (Indian-reservation restoration, PD-INDIAN), EO 2012 (relief of
  Americans abroad, 1914, PD-WAR-EMERGENCY), EO 3036 (civil service schedule, PD-CS-RULES), EO 2670 (Virgin Islands
  lighthouse administration, PD-ADMIN), EO 6724 and 7345 (fund and acquisition authorizations, PD-ADMIN), EO 3237
  (Canal Zone naval radio site, PD-CLASS-EVENTS canal_zone).
- **B71 `open`, EO 1993 and 2203.** EO 2203 vacated the 1914 Blackbeard Island reservation and added a standing
  bar on hunting permits; EO 3957 (1924) restored the reservation, but the verb it applies to EO 2203 is illegible
  in the held copy.
- **B72 `open`, 16 temporary withdrawals.** Withdrawals "pending" legislation, classification or selection, or
  "temporarily withdrawn", end only when revoked; none is revoked in full in a held source (EO 1814, 2047 and
  2599 were revoked only in part; EO 2177 expressly left 1814 and 2047 standing; EO 5971 declared that the EO 4939
  withdrawal "remains in full force and effect").
- **B73 `open`, 20 refuge orders on acquired lands; B74 `open`, 60 other refuge orders.** Persistence depends on
  the 1975 System membership of the order's area (M5); no held record links these orders to current refuge units.
- **B75 `open`, 51 lighthouse reservations and transfers.** No held full revocation or deed.
- **B99 `open`, catch-all.** Reached by no member.

## (d) Members not decided

156 members stay open. 80 refuge reservations (B73, B74) could be decided `yes` by one acquisition: the FWS land
records (the Annual Report of Lands as of 1975 and as of the cutoff, or each refuge's establishing-document file)
matched to the orders by a reviewed crosswalk, applying 668dd(a)(6); some will instead turn out to have been
revoked by PLOs that cite them by date, which the number-based BLM search here may miss. 51 lighthouse
reservations and 16 temporary withdrawals need a PLO or deed naming each order; the held BLM tables were searched
by order number and by full date, so remaining revocations would cite the order by an older date form, by
reserve name, or not appear in BLM's summaries. Seven are other families' orders, and two need a legible EO 3957.

## Choices that remain the owner's

1. Under ruling P2, EO 5457 and 5458 merge into their parents on issue. If the owner treats an amending order as
   living as long as the amended text lives, they become open pending the parent.
2. The ten Alaska `yes` leads rest on ANILCA, which is not yet held; they should be confirmed when it is acquired,
   and EO 5095's link to its refuge rests on a name match.
3. The 35 PLO leads rest on BLM's official tables; acquiring the Federal Register pages would confirm each
   revocation's terms, scope and effective date.
