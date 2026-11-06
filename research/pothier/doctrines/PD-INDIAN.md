# PD-INDIAN: Indian reservation orders and trust-period extensions (230 members, 1905-1936)

Doctrine for the members of X1 type `indian_reservation_trust` (`research/pothier/work/PD-INDIAN/MEMBERS.csv`).
Machine form: `research/pothier/doctrines/PD-INDIAN.json` (version 3). Every lead below is a proposal for the owner;
it changes no status, codebook entry, census row or certified count (0). The status question is whether the order
as a whole was still in force on the cutoff, 2026-10-14. The doctrine applies the owner's standing decisions, the
coordinator rulings in `research/pothier/COORDINATOR_RULINGS.md` (P1 restorations, P2 amendments, P6 member text, P8
periods a statute continued), and the coordinator's adjudications for this family on the Indian Reorganization Act.

## Conclusions

The doctrine decides 93 of the 230 members (92 `no`, 1 `yes`) and leaves 137 `open`.

| Group (branch) | Members | Lead | Basis | Date rule |
|---|---:|---|---|---|
| Trust extensions whose stated period ended before 1934-06-18 (B06-TRUST-NO, B07-TRUST-NO) | 47 | no | TERM | stated expiry plus stated years (1916-1933); for six orders without an expiry year, the end a later held order fixes |
| Trust extensions for IRA sec. 13 Oklahoma tribes (B07-TRUST-NO-OKLA) | 13 | no | TERM: sec. 2 does not apply to them; no statute continued the period | stated end, 1935-1946 |
| Trust extensions issued after 1934-06-18, without a cessation clause (B07-TRUST-NO-POSTIRA) | 6 | no | TERM | stated end, 1945-1962 |
| Trust extensions whose period IRA sec. 2 continued (B07-TRUST-OPEN-IRA, -UNCERTAIN, B06-TRUST-OPEN) | 66 | open | P8: sec. 2 continued the period; IRA status and current trust record needed | none |
| Trust extensions whose period another statute reimposed (B07-TRUST-OPEN-P8) | 5 | open | P8 | none |
| 1935 extensions that cease if the reservation accepts the IRA (B07-TRUST-OPEN-CESSATION) | 4 | open | sec. 18 vote not held | none |
| Oklahoma extensions whose text shows no sec. 13 tribe (B07-TRUST-OPEN-OKLA-TRIBE-NOT-SHOWN) | 2 | open | affiliation not shown | none |
| Restorations, eliminations and a revocation (B05-P1) | 6 | no | TERM, P1 `spent_on_issue` | order date; EO 2332 by its stated opening date |
| Amendments of other reservation orders (B05-P2) | 8 | no | TERM, P2 `merged_into_parent_on_issue` | order date |
| Restorations keeping a tract or adding a direction; an entry confirmation (B05-OPEN) | 3 | open | not a single act | none |
| Orders cancelled, revoked or superseded by a later held order naming them (B02, B04-ACT-5105) | 9 | no | ACT | date of the later order |
| Temporary withdrawals with a stated end before the 1927 Act (B03) | 3 | no | TERM | order date to the stated date |
| Kalispel Reservation, EO 1904 (B01) | 1 | yes | CURRENT: 40 CFR 49.10198(b) | none |
| Standing reservation and set-apart orders (B10) | 34 | open | need a per-reservation current record | none |
| Orders of other families (B04-OUT) | 14 | open | routed to PD-ADMIN, PD-CS-RULES or PD-LAND-WITHDRAWAL | none |
| Conditional reservations, boundary definitions, unreadable approvals, withdrawals lapsing 1927-03-05 (B09) | 9 | open | condition or question unresolved | none |

`try` reports 5 contradiction flags, none of which changes a lead (section (c), last paragraph).

**Trust extensions.** An *allotment* is a parcel of reservation land assigned to an individual Indian. Under the
General Allotment Act of 1887 the United States held it *in trust* (the allottee could not sell it and it was not
taxed) for 25 years; the President could extend that *trust period*, and Mission band lands held in trust under the
1891 Mission Indian Act could be extended under the Act of March 2, 1917. Each of the 143 extension orders extends
the period on stated lands for a stated number of years, so by its own terms it ends when that period runs out.
Section 2 of the Indian Reorganization Act of June 18, 1934 (IRA) provides that "the existing periods of trust placed
upon any Indian lands and any restriction on alienation thereof are hereby extended and continued until otherwise
directed by Congress". Those words reach the trust periods existing on 1934-06-18, and an extension order's operative
content is such a period, so where an order's period was running on that date its stated end is no sound end (P8).
Three limits decide which members that reaches:

- Section 13 provides that sec. 2 "shall not apply" to the listed Oklahoma tribes. For the 13 members whose held text
  names such a tribe in Oklahoma, the period was not continued; the Act of June 15, 1935 (tied to sec. 18) does not
  reach them, and the Oklahoma Indian Welfare Act of June 26, 1936 does not by its words continue trust periods on
  existing allotments. Their own stated ends stand.
- Orders issued after 1934-06-18 fixed periods that did not exist on that date, so sec. 2 did not continue them. Six
  are decided by their own stated ends. Four others (Spokane, Klamath, Colville, Crow) provide that they "cease to be
  of force and effect" if the reservation votes at the sec. 18 election to accept the IRA; the election results are
  not held, so they stay `open`.
- Where another statute reimposed the period an order fixed (Klamath River 1942, Capitan Grande 1927, Yakima 1937,
  Pala 1936; possibly Kickapoo 1933), the order's stated end is not a sound end either, and five members stay `open`.

Where the whole stated period ran out before 1934-06-18, nothing of the order's was left for the statute to continue;
the order ended by its own terms, and any later continuation on the same land came from a separate later order (named
in the gaps where held) or from a statute named in the gaps.

**Reservation orders.** Orders that create, enlarge or set apart a reservation continue until changed. No class-wide
event ended them: the Act of June 30, 1919 stopped new executive-order reservations and the Act of March 3, 1927 made
later boundary changes a matter for Congress alone, but neither ended an existing reservation. Their status on the
cutoff depends on later statutes and current records reservation by reservation, which the project does not hold, so
they are `open` except the Kalispel Reservation, which a current regulation identifies.

**Single-act orders.** Under P1 an order whose only content restores land to the public domain, eliminates land from
a reservation or revokes another order is spent on issue. Under P2 an order whose only content amends another order
merges into the parent on issue: its text continues as part of the parent until the parent ends, and the parent's
lifecycle carries it. Restorations that keep a tract or add a further direction, and an order confirming an entry
still to be perfected, are not single acts and stay `open`.

Terms used: a *lead* is the doctrine's proposed answer (`no` ended before the cutoff, `yes` in force on it, `open`
undecided). `TERM` means the order's own terms end it; `ACT` means a later instrument whose words reach it ends it;
`CURRENT` means a statute, regulation or official current record shows it in force on the cutoff. An
*executive-order reservation* is land the President withdrew from sale and settlement and set apart for Indian use
without a treaty or statute. *Restored to the public domain* means returned to ordinary federal land open to the land
laws.

## (a) Mechanisms by which members end or persist

**M1. Own terms of a trust extension (ends).** Each order extends "the trust period on the allotments" (or on band
lands) of a named tribe, band or reservation, or of named allottees, usually "which trust period expires during the
calendar year" Y, "for a period of" N years, often "from the date of expiration". The extended period ends in year
Y + N. The doctrine reads Y and N from the order text (the WPA 1944 summary where the scan is illegible) and states
the end as an interval covering that year; where the order does not say the N years run from expiry, the interval
starts at the order date plus N, so both readings fall inside it. Orders that name a date (EO 2856, 2866, 3348, 4816,
5474, 6341) get that date plus N. Six orders state no expiry year, but a later held order for the same allotments or
class fixes the end: EO 2109 by EO 4382 ("from March 8, 1926"), EO 2066 by EO 4464 (expiring 1926 or 1927), EO 2317 by
EO 4384 (1926), EO 2374 by EO 4407 (1926), EO 2376 by EO 4408 (1926) and EO 2966 by EO 5023 (1929, a weaker match).
M1 alone decides a member only where M2 to M4 and M10 do not reach its period. The per-member parameters are in the
appendix.

**M2. IRA sec. 2 (makes running periods open).** Act of June 18, 1934, ch. 576, sec. 2, 48 Stat. 984 (now 25 U.S.C.
5102), quoted above. For an order issued before 1934-06-18 whose period was running on that date, on a reservation not
excluded by sec. 13, the period it fixed was continued by statute where the IRA applied. Section 18 makes the Act
inapplicable to a reservation whose adult Indians voted against it; for such a reservation the Act of June 15, 1935,
sec. 3 (49 Stat. 378) extended to December 31, 1936 periods not already extended past that date, and the order's own
end may then stand. The election results are not held, so these members are `open`.

**M3. Later blanket orders (decide nothing alone).** EO 7464 (September 30, 1936, 1 FR 1507; a member) extended trusts
expiring December 31, 1936 or during 1937 "in each case for a further period of 25 years"; annual general orders to EO
10191 (1950) and Interior orders to 1988 followed (25 CFR chapter I, Appendix). Each is a new instrument running from
the expiry of the period it extends.

**M9. IRA sec. 13 (Oklahoma tribes).** "Sections 2, 4, 7, 16, 17, and 18 of this Act shall not apply" to the listed
tribes (Cheyenne, Arapaho, Apache, Comanche, Kiowa, Caddo, Delaware, Wichita, Osage, Kaw, Otoe, Tonkawa, Pawnee,
Ponca, Shawnee, Ottawa, Quapaw, Seneca, Wyandotte, Iowa, Sac and Fox, Kickapoo, Pottawatomi, Cherokee, Chickasaw,
Choctaw, Creek, Seminole) and members of affiliated tribes in Oklahoma (48 Stat. 986-987). The Oklahoma Indian
Welfare Act (49 Stat. 1967) authorizes acquisition of land in trust and tribal organization but does not extend,
continue or reimpose trust periods on existing allotments. The 25 CFR appendix lists Oklahoma statutes only for Kaw,
Quapaw and Mexican Kickapoo lands. So for an order whose text names a listed tribe in Oklahoma, the order's stated end
stands (EO 3363, 4281, 4384, 4398, 4435, 4557, 4587, 4588, 4898, 5306, 5539, 5728, 5955). EO 4470 (Modoc) and EO 4816
(Oakland Reservation) name no listed tribe, and whether their allottees were affiliated is not shown, so they are
`open`.

**M10. Statutes that reimposed an order's period (P8, makes the member open).**
- Act of December 24, 1942, ch. 814, 56 Stat. 1081 (25 U.S.C. 348a): the Klamath River trust "which expired July 31,
  1919" is "reimposed and extended for a period of twenty-five years from July 31, 1919": EO 2943's period.
- Act of February 8, 1927, ch. 78, 44 Stat. 1061 (held, Kappler IV p. 931): the Capitan Grande trust "which trust
  expired March 9, 1924, is hereby reimposed from said date and extended for a period of ten years": EO 3048's period.
- Act of May 27, 1937, ch. 270, 50 Stat. 210: Yakima trusts whose period "expired December 17, 1928, or at any other
  time prior to the approval of this Act", without fee patent, "reimposed and extended to July 9, 1942": reaches the
  period EO 3630 fixed (expired 1932); EO 7036's period had not expired in 1937 and is not reached.
- Act of February 11, 1936, ch. 44, 49 Stat. 1106: the Pala trust "which trust expired January 5, 1935" is reimposed;
  EO 6940 (January 7, 1935) addressed that period.
- Act of February 17, 1933, ch. 97, sec. 2, 47 Stat. 820: restrictions on Kickapoo (Oklahoma) lands still held by the
  Indians reimposed for ten years from approval, while EO 4029's period was running; whether that continues the
  order's period or imposes a new one is unsettled, so EO 4029 is `open`. EO 3047's period had ended in 1924, before
  the Act, and stays `no`.
- Act of April 11, 1940, ch. 80, 54 Stat. 106 (Crow) reimposes periods expired before its approval; it reaches EO 5301,
  already open under M2, and not EO 7001, whose period had not expired.

For the Act of June 15, 1935, sec. 3: its words reach a trust period on an excluded reservation that "has not ...
been extended to a date subsequent to December 31, 1936". A period that had ended before 1934 was no longer the
order's period on that land (the land's period, if any, was a later order's), so the Act does not reach the 47
pre-1934 members.

**M4. Own terms of a temporary withdrawal (ends).** EO 3307 withdraws lands "until March 5, 1921, in aid of proposed
legislation"; EO 3637 withdraws the Zia Pueblo lands "until March 5, 1924"; EO 4041 withdraws lands "until March 5,
1925, for the use and benefit of the Indians of the Walker River Reservation". Each says that if legislation is not
enacted the lands become subject to disposal on that date without further order. The withdrawal ended no later than
the stated date. Later withdrawals of the same lands (the order of May 3, 1921 for the EO 3307 lands, Kappler IV p.
1048; EO 4177 of March 18, 1925 for the EO 4041 lands) are new orders.

**M5. Later instrument naming the member (ends).** Nine members were cancelled, revoked or superseded by a later
instrument naming them by number or date: EO 302-A by EO 324-A (May 1905), EO 1267 by EO 1296 (February 1-2, 1911), EO
1632 by EO 1649 (1912-11-26), EO 1655 by EO 2524 (1917-02-01), EO 1228 by EO 2332 (1916-02-29), EO 1529 by EO 5843
(1932-04-28), EO 3351 by EO 3637 (1922-02-16), EO 6131 by EO 6147 (1933-05-26), and EO 5105 by Public Land Order 5866
(1981-05-15, 46 FR 27652), which BLM's table lists as "revoking EO No. 5105" (the PLO text is not held).

**M6. Restorations, eliminations and revocations (P1, ends on issue).** EO 628, 1090, 1172 and 1284 restore
reservation lands to the public domain, EO 3759 eliminates a 13.5-acre tract from the Navajo reservation, and EO 2332
revokes EO 1228 and opens the lands to entry "on and after April 1, 1916". EO 1284 restores "all lands not allotted to
Indians or otherwise reserved", words that only define the class restored. EO 1000, by contrast, restores the New
Mexico Navajo addition "except" 110 named unapproved allotments that stay reserved awaiting a later act, and EO 1483
restores lands to their earlier status for an exchange and directs that remaining lands be opened afterwards; under
P1 these two are not only restorations and stay `open`.

**M6A. Amendments (P2, merge into the parent on issue).** EO 743 and 744 amend EO 711 and 709 so that their land
descriptions read anew; EO 1406 amends EO 537 "to read as follows"; EO 1322 and 1349 amend the Pima and Maricopa
orders of 1879 and 1883 to admit other Indians; EO 2030, 1598 and 1621 amend the 1876 Gila River order and EO 1538 to
eliminate tracts (EO 1621 also revoking part of EO 1598). Amending is each order's only content. Disclosure: its text
continues as part of the parent until the parent ends; the parent's lifecycle carries it.

**M7. The 1919 and 1927 Acts (lead only).** Section 27 of the Act of June 30, 1919 (41 Stat. 3, 34) provides that
"hereafter no public lands of the United States shall be withdrawn by Executive Order, proclamation, or otherwise, for
or as an Indian reservation except by act of Congress". Section 4 of the Act of March 3, 1927 (44 Stat. 1347; 25
U.S.C. 398d) provides that "changes in the boundaries of reservations created by Executive order, proclamation, or
otherwise for the use and occupation of Indians shall not be made except by Act of Congress" (with a proviso, struck
in 1976, for temporary withdrawals by the Secretary of the Interior). Neither ends an existing order. In Sioux Tribe v.
United States, 316 U.S. 317, 331 (1942), the Court held that the Indians' interest under the 1875-1876 Sioux orders
"was subject to termination at the will of either the executive or Congress"; that the executive could change such
reservations only until the 1927 Act is the doctrine's inference from that Act, not the Court's holding.

**M8. Current regulation naming the reservation (persists).** 40 CFR 49.10198(b), in force on 2026-10-14, designates
"the original Kalispel Reservation, as established by Executive Order No. 1904, signed by President Woodrow Wilson on
March 23, 1914" a Class I air-quality area. The regulation treats the reservation the order created as existing.

No member depends on the life of a named person, and no review program or class-wide event ends any member.

## (b) Primary sources

"Held" means the text is in the repository and the cited phrase (`pin` in the JSON) was found in it. Kappler vol.
III and IV are held as gzip JSON lines (one page per line; read with `zcat ... | grep`); the image number is given.

| Id | Source | Establishes | Held? |
|---|---|---|---|
| S-MEMBER | The member's own order text (`"member_text": true`, P6) | Its stated period, date, condition or single act | Yes, per member |
| S-GAA | Act of Feb. 8, 1887, ch. 119, sec. 5, 24 Stat. 388, 389 | 25-year trust; "the President of the United States may in any case in his discretion extend the period" | No: https://www.govinfo.gov/content/pkg/STATUTE-24/pdf/STATUTE-24-Pg388.pdf |
| S-1906 | Act of June 21, 1906, ch. 3504, 34 Stat. 325, 326 | President may continue restrictions before the trust period expires | Yes: Kappler III gz (image 201, printed p. 193), sha256 64716cbc...15523ed |
| S-1917 | Act of Mar. 2, 1917, ch. 146, 39 Stat. 969, 976 | President may extend the trust on Mission band lands (authority of EO 2684, 2795, 3048, 3302, 3446, 6940, 7009, 7464) | Yes: Kappler IV gz (image 124, printed p. 114) |
| S-1889 | Act of Mar. 2, 1889, sec. 11, 25 Stat. 888, 892 | Authority cited by EO 2374 | No: govinfo STATUTE-25-Pg888 |
| S-IRA | Act of June 18, 1934, ch. 576, secs. 2, 13, 18, 48 Stat. 984, 986-988 | Sec. 2 continues existing trust periods; sec. 13 excepts listed Oklahoma tribes; sec. 18 elections | No: https://www.govinfo.gov/content/pkg/STATUTE-48/pdf/STATUTE-48-Pg984.pdf |
| S-5102 | 25 U.S.C. 5102 | Current text of IRA sec. 2 | No (read on law.cornell.edu) |
| S-1935 | Act of June 15, 1935, ch. 260, sec. 3, 49 Stat. 378 | Excluded reservations: unextended periods extended to Dec. 31, 1936 | No: govinfo STATUTE-49-Pg378 |
| S-OIWA | Act of June 26, 1936, 49 Stat. 1967 (Oklahoma Indian Welfare Act) | No continuation of trust periods on existing allotments | No: govinfo STATUTE-49-Pg1967 |
| S-KLAMATHRIVER | Act of Dec. 24, 1942, ch. 814, 56 Stat. 1081 (25 U.S.C. 348a) | Klamath River trust expired July 31, 1919 reimposed 25 years | No (read via govinfo) |
| S-CAPITAN | Act of Feb. 8, 1927, ch. 78, 44 Stat. 1061 | Capitan Grande trust expired March 9, 1924 reimposed ten years | Yes: Kappler IV gz (image 605, printed p. 931) |
| S-YAKIMA1937 | Act of May 27, 1937, ch. 270, 50 Stat. 210 | Yakima periods expired before 1937 reimposed to July 9, 1942 | No: govinfo STATUTE-50-Pg210 |
| S-PALA1936 | Act of Feb. 11, 1936, ch. 44, 49 Stat. 1106 | Pala trust expired Jan. 5, 1935 reimposed | No: govinfo STATUTE-49-Pg1106 |
| S-CROW1940 | Act of Apr. 11, 1940, ch. 80, 54 Stat. 106 | Crow periods expired before 1940 reimposed to May 23, 1940 | No: govinfo STATUTE-54-Pg106 |
| S-KICKAPOO1933 | Act of Feb. 17, 1933, ch. 97, 47 Stat. 819, 820 | Kickapoo (Oklahoma) restrictions reimposed ten years | No: govinfo STATUTE-47-Pg819, Pg820 |
| S-EO7464 | EO 7464, Sept. 30, 1936, 1 FR 1507 | Later blanket extension | Yes (member text) |
| S-EO4382, S-EO4464, S-EO4384, S-EO4407, S-EO4408, S-EO5023 | Later extension orders (members) | Fix the ends of EO 2109, 2066, 2317, 2374, 2376, 2966 | Yes: member text paths and sha256 in the JSON |
| S-CFRAPP | 25 CFR ch. I, Appendix | Official list of extension orders and Acts by reservation | No (search excerpts only): ecfr.gov |
| S-1919 | Act of June 30, 1919, ch. 4, sec. 27, 41 Stat. 3, 34 | No new executive-order reservations; p. 34 supported by the opinion at Kappler IV p. 1062 citing "41 Stat. 3-34" | Yes: Kappler IV gz (image 235, printed p. 225), sha256 dc2c1f28...708cf63 |
| S-1927 | Act of Mar. 3, 1927, ch. 299, sec. 4, 44 Stat. 1347 (25 U.S.C. 398d) | Boundary changes only by Act of Congress | Yes: Kappler IV gz (image 610, printed p. 936) |
| S-398d | 25 U.S.C. 398d as amended by Pub. L. 94-579, sec. 704(a), 90 Stat. 2792 | Current law; proviso struck 1976 | No (read on law.cornell.edu) |
| S-SIOUX | Sioux Tribe v. United States, 316 U.S. 317, 331 (1942) | Interest under the 1875-1876 orders terminable at will | No: tile.loc.gov usrep316317 |
| S-KALISPEL | 40 CFR 49.10198(b) (84 FR 34313, 2019) | Kalispel Reservation "as established by Executive Order No. 1904" | Held row: `jobs/current-law/output/MENTIONS.csv` row ecfr:0522410f48fe carries the paragraph text (GovInfo eCFR bulk XML, confirmed at the cutoff), sha256 0af2d6b2...755aeb74 |
| S-WHITEEARTH | Pub. L. 99-264, sec. 3(i), 100 Stat. 61, 62 (1986) (25 U.S.C. 331 note) | EO 4642, 5768, 5953 "deemed to have extended" past trust periods | No: govinfo STATUTE-100-Pg61 |
| S-KENAI | 43 U.S.C. 1784 note | Names a different "Executive Order 2943" (Kenai, Alaska) | Held row in MENTIONS.csv |
| S-PLO5866 | PLO 5866, May 15, 1981, 46 FR 27652 | Revokes EO 5105 by number (BLM table, held as a later edge) | No: PLO text to acquire |
| S-EO324A, S-EO1296, S-EO1649, S-EO2524, S-EO2332, S-EO3637, S-EO5843, S-EO6147 | The later orders that end B02 members | Each names the member | Yes: paths and sha256 in the JSON |

Sources: 23 held (counting S-MEMBER, the later extension orders and the two current-law rows) and 16 to acquire
(`FETCH_PROPOSED.jsonl`). Leads resting on unheld sources carry the engine's automatic "source not held" gap.

## (c) Decision procedure

Branches are tried in order; the first whose conditions all hold decides. Branches that name instruments do so
because the date, the ending instrument or the single act was read from that member's text; each also checks a text,
summary or edge feature.

1. **B01-KALISPEL** (EO 1904): `yes`, CURRENT.
2. **B02-ACT-*** (8 branches): `no`, ACT, dated by the later order (fixed date, or an interval for EO 302-A, May 1905,
   and EO 1267, February 1-2, 1911).
3. **B03-TERM-3307, -3637, -4041**: `no`, TERM, interval from the order date to the stated date.
4. **B04-ACT-5105** (EO 5105; held revocation edge after 1981): `no`, ACT, dated by the edge (1981-05-15).
5. **B04-OUT-*** (WPA summary names a land district, the Civil Service Rules, an Emergency Conservation Work fund or
   the Reclamation Service; 14 members): `open`, each lead naming the family that decides it (PD-ADMIN, PD-CS-RULES,
   PD-LAND-WITHDRAWAL). EO 6131 is decided earlier by B02.
6. **B05-P1-SPENT** (EO 628, 1090, 1172, 1284, 3759) and **B05-P1-SPENT-2332**: `no`, TERM, `spent_on_issue`.
7. **B05-P2-MERGED** (EO 743, 744, 1322, 1349, 1406, 1598, 1621, 2030): `no`, TERM, `merged_into_parent_on_issue`, with
   the P2 disclosure.
8. **B05-OPEN-RESTORATION-WITH-RESERVATION** (EO 1000, 1483) and **B05-OPEN-ENTRY-CONFIRMATION** (EO 3020, which lets
   an entry "be perfected by the entryman upon due compliance with the law"): `open`.
9. **B06-TRUST-NO-2109, -2066, -2317, -2374, -2376, -2966, -3047**: `no`, TERM; the end comes from the later held order
   (or, for EO 3047, its own stated end, with the 1933 Kickapoo Act disclosed).
10. **B07-TRUST-NO-YYYY-nn** (19 branches, 40 members): `no`, TERM, interval = stated expiry plus stated period, every
    interval ending before 1934-06-18. Each branch names, per member, the later held extension orders for the same
    tribe and records the check of the Acts listed in the 25 CFR appendix and of the 1935 Act.
11. **B07-TRUST-NO-OKLA-YYYY-nn** (9 branches, 13 members; text or summary in Oklahoma, member listed): `no`, TERM,
    kind `trust_extension_term_expired_sec13_oklahoma`, stated end (1935-1946).
12. **B07-TRUST-NO-POSTIRA-*** (EO 6926, 6968, 7009, 7036, 7206, 7464): `no`, TERM, kind
    `trust_extension_after_ira_term_expired`, stated end (1945-1962).
13. **B07-TRUST-OPEN-CESSATION** (EO 6939, 6961, 6962, 7001; text "cease to be of force and effect"): `open`. Each ends
    on a vote accepting the IRA or else at its stated end; either ends it before the cutoff unless a statute continued
    its period, but the doctrine decides only when the vote is held.
14. **B07-TRUST-OPEN-P8-2943, -3048, -3630, -6940, -4029**: `open`, kind `trust_period_continued_by_statute_p8`.
15. **B06-TRUST-OPEN-WHITE-EARTH** (EO 4642, 5768, 5953) and **B06-TRUST-OPEN-6498**: `open`. Their periods were running
    on 1934-06-18 and they cover IRA reservations, some with sec. 13 Oklahoma reservations too. The White Earth Act
    "deemed" the first three "to have extended trust periods" in the past, and the 25 CFR appendix lists EO 6498; both
    describe past extensions and are not current predicates.
16. **B07-TRUST-OPEN-IRA** (58 members whose whole stated end falls on or after 1934-06-18, outside sec. 13) and
    **B07-TRUST-OPEN-UNCERTAIN** (EO 3722, 3995, 4024, whose end interval straddles 1934-06-18, and EO 1916, whose end no
    held source fixes): `open`, kind `trust_period_running_on_1934_06_18_continued_by_statute`.
17. **B07-TRUST-OPEN-OKLA-TRIBE-NOT-SHOWN** (EO 4470, 4816): `open`.
18. **B09-OPEN-TEMP-1927** (EO 4177, 4297), **B09-OPEN-CONDITION** (EO 1271, 1518, 1603), **B09-OPEN-BOUNDARY-DEFINITION**
    (EO 2273, 4628), **B09-OPEN-NO-ORDER-TEXT** (EO 342-B, 343-A): `open`. EO 4177 and 4297 withdraw lands for the
    Indians of an existing reservation "until March 5, 1927", two days after the 1927 Act; no held source decides
    whether such a lapse was a barred boundary change.
19. **B10-OPEN-STANDING-RESERVATION** (34 members): `open`, kind
    `persists_standing_reservation_needs_current_predicate`.
20. **B99-CATCHALL**: `open` (0 members).

Final `try` counts (`python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-INDIAN.json --hints`): 230
members; decides 93 (92 no, 1 yes); 137 open; 80 branches; 5 contradiction flags. By branch group: B01 1 yes; B02 8 no;
B03 3 no; B04-ACT 1 no; B04-OUT 14 open; B05-P1 6 no; B05-P2 8 no; B05-OPEN 3 open; B06-TRUST-NO 7 no; B07-TRUST-NO 40
no; B07-TRUST-NO-OKLA 13 no; B07-TRUST-NO-POSTIRA 6 no; B07-TRUST-OPEN-CESSATION 4, -P8 5, B06-TRUST-OPEN 4,
B07-TRUST-OPEN-IRA 58, -UNCERTAIN 4, -OKLA-TRIBE-NOT-SHOWN 2 open; B09 9 open; B10 34 open; B99 0.

The 5 flags, none of which changes a lead:
- EO 1228 (B02, `no`): held edges from 1931-1983 (EO 5639, 5713, 5733, 6996, PLO 6455) quote "Executive order of July
  13, 1910, effecting Coal Withdrawal Wyoming No. 1", a different order of the same date.
- EO 1256 (B10, `open`): its revocation edges (EO 5816, 1932) quote "Executive order of October 20, 1910, creating
  Power-Site Reserve No. 155" in Montana, a different order of the same date, not the Salt River addition.
- EO 1284 (B05-P1, `no`): edges from EO 1359 (1911) and EO 1482 and 1483 (1912) are later acts on the restored land,
  part of the land's history; they do not revive a spent command.
- EO 1598 and EO 744 (B05-P2, `no`): EO 1621 revoking part of EO 1598 (1912), and EO 1000 and 1284 restoring lands EO
  744 described, act on the parent orders as amended; under P2 they are events of the parent.

## (d) Members the procedure cannot decide (137), and why

- **77 trust extensions.** 66 had periods IRA sec. 2 continued: each needs the reservation's IRA status (the sec. 18
  election results, not held) and a current record of the trust lands (25 U.S.C. 5102; BIA land title records; no
  later Act ending the trust, such as a termination act). Five had periods another statute reimposed (P8): each needs
  the statutory period's end and later history. Four cease on an IRA acceptance vote not held. Two are Oklahoma
  orders whose allottees' sec. 13 affiliation is not shown.
- **34 standing reservation orders** (B10): per-reservation later statutes and a current predicate. The `current_law`
  field found one only for EO 1904. Held later events: PLO 5470 (1975), listed by BLM as "amending EO of July 22,
  1915" in California, probably EO 2225 (PLO text needed to confirm).
- **14 orders of other families** (B04-OUT), named in their leads.
- **3 not-only single acts** (B05-OPEN), **2 withdrawals lapsing 1927-03-05**, **3 conditional reservations**, **2
  boundary definitions**, **2 approvals without readable text**: reasons as in (c).

Other points for reviewers: EO 3348's scan gives the expiry as December 28, 1920 (the WPA summary has December 18);
EO 5474 extends the same Santee homesteads from December 28, 1930, so the end is fixed at 1930-12-28. EO 5768 is dated
December 30, 1931 in its held text and "December 10, 1931" in the White Earth Act. EO 3363 extends the Ponca
(Oklahoma) period that EO 3327 had extended by one year, so its 25 years run from 1921. EO 1916 carries a held edge
quoting "1916 (revoked by PLO 1593)" from a table row whose subject the quote does not show; it does not change the
`open` lead.

## Appendix: trust-extension members, parameters read and stated ends

The "stated end" column is the end the order's own terms give. For `open` members it is not a TERM end, because IRA
sec. 2, another statute or an unheld vote may decide it.

| Order | Date | Expiry and period read | Stated end of the extended period | Lead | Branch |
|---|---|---|---|---|---|
| 1916 | 1914-04-16 | no expiry year stated; ten years | not fixed by a held source (after 1924-04-19) | open | B07-TRUST-OPEN-UNCERTAIN |
| 2066 | 1914-10-27 | no expiry year stated; EO 4464 extends the same class of allotments expiring during 1926 or 1927 | 1924-10-27 to 1927-12-31 | no | B06-TRUST-NO-2066 |
| 2109 | 1914-12-23 | no expiry year stated; ten years; EO 4382 extends the same period "from March 8, 1926" | 1926-03-08 (EO 4382) | no | B06-TRUST-NO-2109 |
| 2133 | 1915-02-03 | text: expire during 1915; one year | 1916-01-01 to 1916-12-31 | no | B07-TRUST-NO-1916-01 |
| 2317 | 1916-02-15 | no expiry year stated; EO 4384 (1926) re-extends the same named allotments, WPA: expiring in 1926 | 1926-02-15 to 1926-12-31 | no | B06-TRUST-NO-2317 |
| 2363 | 1916-04-20 | text: expires during 1916 and 1919; ten years from the dates of expiration | 1926-01-01 to 1929-12-31 | no | B07-TRUST-NO-1929-09 |
| 2374 | 1916-04-29 | no expiry year stated; EO 4407 extends the Ponca (Nebraska) trust expiring during 1926 for a further ten years | 1926-04-29 to 1926-12-31 | no | B06-TRUST-NO-2374 |
| 2376 | 1916-04-29 | no expiry year stated; EO 4408 re-extends the same named allotments from present date of expiration, WPA: during 1926 | 1926-04-29 to 1926-12-31 | no | B06-TRUST-NO-2376 |
| 2432 | 1916-08-01 | expiring 1916, period 10 (WPA summary) | 1926-01-01 to 1926-12-31 | no | B07-TRUST-NO-1926-08 |
| 2453 | 1916 | expiring 1916 (WPA summary), period 10 (WPA summary) | 1926-01-01 to 1926-12-31 | no | B07-TRUST-NO-1926-08 |
| 2494 | 1916-11-24 | expiring 1917 (WPA summary), period 10 | 1927-01-01 to 1927-12-31 | no | B07-TRUST-NO-1927-10 |
| 2512 | 1917-01-15 | expiring 1917, period 10 | 1927-01-01 to 1927-12-31 | no | B07-TRUST-NO-1927-10 |
| 2580 | 1917-04-04 | expiring 1917, period 10 (WPA summary) | 1927-01-01 to 1927-12-31 | no | B07-TRUST-NO-1927-10 |
| 2591 | 1917-04-11 | expiring 1917, period 10 (WPA summary) | 1927-01-01 to 1927-12-31 | no | B07-TRUST-NO-1927-10 |
| 2607 | 1917-05-04 | expiring 1917 (WPA summary), period 10 | 1927-01-01 to 1927-12-31 | no | B07-TRUST-NO-1927-10 |
| 2623 | 1917-05-19 | text: expires during 1917; one year from the date of expiration | 1918-01-01 to 1918-12-31 | no | B07-TRUST-NO-1918-02 |
| 2684 | 1917-08-16 | expiring 1917, period 10 | 1927-01-01 to 1927-12-31 | no | B07-TRUST-NO-1927-10 |
| 2747 | 1917-11-02 | expiring 1917, period 10 | 1927-01-01 to 1927-12-31 | no | B07-TRUST-NO-1927-10 |
| 2778 | 1917-12-31 | text: expire during 1918; one year (not stated to run from expiry; order dated 1917-12-31) | 1918-12-31 to 1919-12-31 | no | B07-TRUST-NO-1919-03 |
| 2795 | 1918-01-26 | expiring 1918, period 10 | 1928-01-01 to 1928-12-31 | no | B07-TRUST-NO-1928-12 |
| 2804 | 1918-02-11 | expiring 1918, period 10 | 1928-01-01 to 1928-12-31 | no | B07-TRUST-NO-1928-12 |
| 2816 | 1918-03-02 | text: would otherwise expire during this calendar year (1918); ten years | 1928-01-01 to 1928-12-31 | no | B07-TRUST-NO-1928-12 |
| 2856 | 1918-05-04 | text: expires June 12, 1918; nine years from said date | 1927-06-12 | no | B07-TRUST-NO-1927-11 |
| 2866 | 1918-05-24 | text: expires June 5, 1918; ten years from said date | 1928-06-05 | no | B07-TRUST-NO-1928-13 |
| 2927 | 1918-07-30 | expiring 1918, period 10 (WPA summary) | 1928-01-01 to 1928-12-31 | no | B07-TRUST-NO-1928-12 |
| 2943 | 1918-08-23 | text: expires during 1918; one year | 1919-01-01 to 1919-12-31 | open | B07-TRUST-OPEN-P8-2943 |
| 2965 | 1918 | expiring 1918, period 10 | 1928-01-01 to 1928-12-31 | no | B07-TRUST-NO-1928-12 |
| 2966 | 1918 | no expiry year stated; EO 5023 extends the Iowa (Kansas and Nebraska) trust expiring during 1929 (weaker match: exceptions differ) | 1928-09-23 to 1929-12-31 | no | B06-TRUST-NO-2966 |
| 3024 | 1919-01-11 | text: expire during 1919; one year | 1920-01-01 to 1920-12-31 | no | B07-TRUST-NO-1920-04 |
| 3047 | 1919-02-27 | text: expires during 1919; five years | 1924-01-01 to 1924-12-31 | no | B06-TRUST-NO-3047 |
| 3048 | 1919-02-27 | text: expires during 1919; five years | 1924-01-01 to 1924-12-31 | open | B07-TRUST-OPEN-P8-3048 |
| 3110 | 1919-07-10 | expiring 1919, period 10 | 1929-01-01 to 1929-12-31 | no | B07-TRUST-NO-1929-14 |
| 3111 | 1919-07-10 | expiring 1919 (WPA summary), period 10 | 1929-01-01 to 1929-12-31 | no | B07-TRUST-NO-1929-14 |
| 3223 | 1920-02-05 | expiring 1920, period 3 | 1923-01-01 to 1923-12-31 | no | B07-TRUST-NO-1923-06 |
| 3250 | 1920-03-24 | expiring 1920, period 10 | 1930-01-01 to 1930-12-31 | no | B07-TRUST-NO-1930-15 |
| 3301 | 1920-07-03 | text: expires during 1920; one year (OCR cut; WPA one year) | 1921-01-01 to 1921-12-31 | no | B07-TRUST-NO-1921-05 |
| 3302 | 1920-07-07 | text: expires during 1920; five years from date of expiration | 1925-01-01 to 1925-12-31 | no | B07-TRUST-NO-1925-07 |
| 3304 | 1920-07-10 | expiring 1920, period 10 | 1930-01-01 to 1930-12-31 | no | B07-TRUST-NO-1930-15 |
| 3312 | 1920-07-21 | expiring 1920, period 10 (WPA summary) | 1930-01-01 to 1930-12-31 | no | B07-TRUST-NO-1930-15 |
| 3327 | 1920 | text: 25-year period expiring during 1920 (OCR 19lo; WPA 1920), one year | 1921-01-01 to 1921-12-31 | no | B07-TRUST-NO-1921-05 |
| 3348 | 1920-11-05 | text (scan): expires December 28, 1920 (WPA summary: Dec. 18; EO 5474 gives the next expiry as December 28, 1930); ten years from said date | 1930-12-28 | no | B07-TRUST-NO-1930-16 |
| 3362 | 1920-11-30 | text: expire during 1920 and 1921; 25 years from date of expiration | 1945-01-01 to 1946-12-31 | open | B07-TRUST-OPEN-IRA |
| 3363 | 1920-12-01 | text: Ponca (Okla.) period extended one year by EO of Sept. 19, 1920 [EO 3327: expiring 1920, +1 = 1921], extended a further 25 years | 1946-01-01 to 1946-12-31 | no | B07-TRUST-NO-OKLA-1946-09 |
| 3383 | 1921-01-07 | text: expires during 1921 (OCR 192s; WPA 1921); 25 years from date of expiration | 1946-01-01 to 1946-12-31 | open | B07-TRUST-OPEN-IRA |
| 3445 | 1921-04-30 | expiring 1921 (WPA summary), period 10 | 1931-01-01 to 1931-12-31 | no | B07-TRUST-NO-1931-17 |
| 3446 | 1921-04-30 | expiring 1921, period 10 | 1931-01-01 to 1931-12-31 | no | B07-TRUST-NO-1931-17 |
| 3447 | 1921-05-02 | expiring 1921, period 10 | 1931-01-01 to 1931-12-31 | no | B07-TRUST-NO-1931-17 |
| 3586 | 1921-12-07 | expiring 1921, period 10 | 1931-01-01 to 1931-12-31 | no | B07-TRUST-NO-1931-17 |
| 3613 | 1922-01-12 | expiring 1922, period 10 | 1932-01-01 to 1932-12-31 | no | B07-TRUST-NO-1932-18 |
| 3614 | 1922-01-12 | expiring 1922, period 10 | 1932-01-01 to 1932-12-31 | no | B07-TRUST-NO-1932-18 |
| 3630 | 1922-02-03 | expiring 1922, period 10 | 1932-01-01 to 1932-12-31 | open | B07-TRUST-OPEN-P8-3630 |
| 3699 | 1922-06-27 | expiring 1922, period 10 | 1932-01-01 to 1932-12-31 | no | B07-TRUST-NO-1932-18 |
| 3722 | 1922-08-12 | text: expire during 1922, 1923 and 1924; ten years from the dates of expiration | 1932-01-01 to 1934-12-31 | open | B07-TRUST-OPEN-UNCERTAIN |
| 3805 | 1923-03-05 | expiring 1923, period 10 | 1933-01-01 to 1933-12-31 | no | B07-TRUST-NO-1933-19 |
| 3853 | 1923-05-22 | expiring 1923, period 10 | 1933-01-01 to 1933-12-31 | no | B07-TRUST-NO-1933-19 |
| 3980 | 1924-03-26 | expiring 1924, period 15 | 1939-01-01 to 1939-12-31 | open | B07-TRUST-OPEN-IRA |
| 3994 | 1924-04-19 | no expiry year stated; at least order date plus fifteen years | on or after 1939-04-19 | open | B07-TRUST-OPEN-IRA |
| 3995 | 1924-04-19 | text: expires during the calendar year 1924; ten years | 1934-01-01 to 1934-12-31 | open | B07-TRUST-OPEN-UNCERTAIN |
| 4024 | 1924-06-10 | expiring 1924, period 10 | 1934-01-01 to 1934-12-31 | open | B07-TRUST-OPEN-UNCERTAIN |
| 4029 | 1924-06-19 | expiring 1924 (WPA summary), period 10 | 1934-01-01 to 1934-12-31 | open | B07-TRUST-OPEN-P8-4029 |
| 4145 | 1925-01-28 | expiring 1925, period 10 | 1935-01-01 to 1935-12-31 | open | B07-TRUST-OPEN-IRA |
| 4154 | 1925-02-10 | expiring 1925, period 10 (WPA summary) | 1935-01-01 to 1935-12-31 | open | B07-TRUST-OPEN-IRA |
| 4157 | 1925-02-17 | text: expires during the calendar years 1925 and 1926; ten years from date of expiration | 1935-01-01 to 1936-12-31 | open | B07-TRUST-OPEN-IRA |
| 4159 | 1925-02-19 | expiring 1925, period 10 | 1935-01-01 to 1935-12-31 | open | B07-TRUST-OPEN-IRA |
| 4168 | 1925-03-11 | expiring 1925, period 10 | 1935-01-01 to 1935-12-31 | open | B07-TRUST-OPEN-IRA |
| 4233 | 1925-05-26 | expiring 1925, period 10 | 1935-01-01 to 1935-12-31 | open | B07-TRUST-OPEN-IRA |
| 4281 | 1925-08-11 | expiring 1925, period 10 | 1935-01-01 to 1935-12-31 | no | B07-TRUST-NO-OKLA-1935-01 |
| 4293 | 1925-08-25 | expiring 1925, period 10 | 1935-01-01 to 1935-12-31 | open | B07-TRUST-OPEN-IRA |
| 4298 | 1925-08-29 | expiring 1925, period 10 | 1935-01-01 to 1935-12-31 | open | B07-TRUST-OPEN-IRA |
| 4382 | 1926-02-10 | text: ten years from March 8, 1926 | 1936-03-08 | open | B07-TRUST-OPEN-IRA |
| 4384 | 1926-02-20 | expiring 1926 (WPA summary), period 10 | 1936-01-01 to 1936-12-31 | no | B07-TRUST-NO-OKLA-1936-02 |
| 4398 | 1926-03-18 | expiring 1926 (WPA summary), period 10 | 1936-01-01 to 1936-12-31 | no | B07-TRUST-NO-OKLA-1936-02 |
| 4406 | 1926-03-30 | expiring 1926, period 10 | 1936-01-01 to 1936-12-31 | open | B07-TRUST-OPEN-IRA |
| 4407 | 1926-03-30 | expiring 1926, period 10 | 1936-01-01 to 1936-12-31 | open | B07-TRUST-OPEN-IRA |
| 4408 | 1926-03-30 | expiring 1926 (WPA summary), period 10 | 1936-01-01 to 1936-12-31 | open | B07-TRUST-OPEN-IRA |
| 4417 | 1926-04-14 | expiring 1926, period 10 | 1936-01-01 to 1936-12-31 | open | B07-TRUST-OPEN-IRA |
| 4435 | 1926-04-29 | expiring 1926, period 10 | 1936-01-01 to 1936-12-31 | no | B07-TRUST-NO-OKLA-1936-02 |
| 4464 | 1926-06-28 | text/summary: expire during 1926 or 1927; ten years | 1936-01-01 to 1937-12-31 | open | B07-TRUST-OPEN-IRA |
| 4470 | 1926-07-01 | expiring 1926, period 10 | 1936-01-01 to 1936-12-31 | open | B07-TRUST-OPEN-OKLA-TRIBE-NOT-SHOWN |
| 4548 | 1926-12-04 | expiring 1927, period 10 | 1936-12-04 to 1937-12-31 | open | B07-TRUST-OPEN-IRA |
| 4557 | 1926-12-23 | expiring 1927, period 10 | 1936-12-23 to 1937-12-31 | no | B07-TRUST-NO-OKLA-1937-03 |
| 4587 | 1927-02-17 | expiring 1927 (WPA summary), period 10 | 1937-01-01 to 1937-12-31 | no | B07-TRUST-NO-OKLA-1937-04 |
| 4588 | 1927-02-17 | expiring 1927, period 10 (WPA summary) | 1937-01-01 to 1937-12-31 | no | B07-TRUST-NO-OKLA-1937-04 |
| 4600 | 1927-03-01 | expiring 1927, period 10 | 1937-01-01 to 1937-12-31 | open | B07-TRUST-OPEN-IRA |
| 4642 | 1927-05-05 | expiring 1927, period 10 | 1937-01-01 to 1937-12-31 | open | B06-TRUST-OPEN-WHITE-EARTH |
| 4687 | 1927-07-11 | expiring 1927, period 10 | 1937-01-01 to 1937-12-31 | open | B07-TRUST-OPEN-IRA |
| 4688 | 1927-07-11 | expiring 1927 (WPA summary), period 10 | 1937-01-01 to 1937-12-31 | open | B07-TRUST-OPEN-IRA |
| 4694 | 1927-07-22 | expiring 1927, period 10 | 1937-01-01 to 1937-12-31 | open | B07-TRUST-OPEN-IRA |
| 4765 | 1927-11-23 | expiring 1928, period 10 | 1938-01-01 to 1938-12-31 | open | B07-TRUST-OPEN-IRA |
| 4775 | 1927-11-30 | expiring 1928 (WPA summary), period 10 | 1938-01-01 to 1938-12-31 | open | B07-TRUST-OPEN-IRA |
| 4816 | 1928-02-25 | text: expires June 5, 1928; ten years from said date | 1938-06-05 | open | B07-TRUST-OPEN-OKLA-TRIBE-NOT-SHOWN |
| 4858 | 1928-04-16 | expiring 1928, period 10 | 1938-01-01 to 1938-12-31 | open | B07-TRUST-OPEN-IRA |
| 4898 | 1928-05-29 | expiring 1928, period 10 | 1938-01-01 to 1938-12-31 | no | B07-TRUST-NO-OKLA-1938-05 |
| 4979 | 1928-10-16 | expiring 1928, period 10 | 1938-01-01 to 1938-12-31 | open | B07-TRUST-OPEN-IRA |
| 4981 | 1928-10-20 | expiring 1928, period 10 | 1938-01-01 to 1938-12-31 | open | B07-TRUST-OPEN-IRA |
| 4994 | 1928-11-14 | expiring 1928, period 10 | 1938-01-01 to 1938-12-31 | open | B07-TRUST-OPEN-IRA |
| 5023 | 1929-01-10 | expiring 1929, period 10 | 1939-01-01 to 1939-12-31 | open | B07-TRUST-OPEN-IRA |
| 5028 | 1929-01-16 | expiring 1929, period 10 | 1939-01-01 to 1939-12-31 | open | B07-TRUST-OPEN-IRA |
| 5087 | 1929-04-01 | expiring 1929, period 10 | 1939-01-01 to 1939-12-31 | open | B07-TRUST-OPEN-IRA |
| 5148 | 1929-07-03 | expiring 1929, period 10 | 1939-01-01 to 1939-12-31 | open | B07-TRUST-OPEN-IRA |
| 5173 | 1929-08-09 | expiring 1929, period 10 | 1939-01-01 to 1939-12-31 | open | B07-TRUST-OPEN-IRA |
| 5253 | 1929-12-31 | expiring 1930, period 10 | 1939-12-31 to 1940-12-31 | open | B07-TRUST-OPEN-IRA |
| 5299 | 1930-03-10 | expiring 1930, period 10 | 1940-01-01 to 1940-12-31 | open | B07-TRUST-OPEN-IRA |
| 5301 | 1930-03-12 | expiring 1930, period 10 | 1940-01-01 to 1940-12-31 | open | B07-TRUST-OPEN-IRA |
| 5302 | 1930-03-12 | expiring 1930, period 10 | 1940-01-01 to 1940-12-31 | open | B07-TRUST-OPEN-IRA |
| 5303 | 1930-03-12 | expiring 1930, period 10 | 1940-01-01 to 1940-12-31 | open | B07-TRUST-OPEN-IRA |
| 5305 | 1930-03-18 | expiring 1930, period 10 | 1940-01-01 to 1940-12-31 | open | B07-TRUST-OPEN-IRA |
| 5306 | 1930-03-18 | expiring 1930, period 10 | 1940-01-01 to 1940-12-31 | no | B07-TRUST-NO-OKLA-1940-06 |
| 5356 | 1930-05-28 | expiring 1930, period 10 | 1940-01-01 to 1940-12-31 | open | B07-TRUST-OPEN-IRA |
| 5357 | 1930-05-29 | expiring 1930, period 10 | 1940-01-01 to 1940-12-31 | open | B07-TRUST-OPEN-IRA |
| 5383 | 1930-06-26 | no expiry year stated; at least order date plus ten years from expiry | on or after 1940-06-26 | open | B07-TRUST-OPEN-IRA |
| 5415 | 1930-08-04 | expiring 1930, period 10 | 1940-01-01 to 1940-12-31 | open | B07-TRUST-OPEN-IRA |
| 5416 | 1930-08-04 | expiring 1930, period 10 | 1940-01-01 to 1940-12-31 | open | B07-TRUST-OPEN-IRA |
| 5466 | 1930-10-22 | expiring 1930, period 10 | 1940-01-01 to 1940-12-31 | open | B07-TRUST-OPEN-IRA |
| 5474 | 1930-10-31 | text: expires December 28, 1930; ten years (not stated to run from expiry) | 1940-10-31 to 1940-12-28 | open | B07-TRUST-OPEN-IRA |
| 5516 | 1930-12-17 | expiring 1931, period 10 | 1940-12-17 to 1941-12-31 | open | B07-TRUST-OPEN-IRA |
| 5539 | 1931-01-23 | expiring 1931, period 10 | 1941-01-01 to 1941-12-31 | no | B07-TRUST-NO-OKLA-1941-07 |
| 5546 | 1931-01-31 | expiring 1931, period 10 | 1941-01-01 to 1941-12-31 | open | B07-TRUST-OPEN-IRA |
| 5556 | 1931-02-11 | expiring 1931, period 10 | 1941-01-01 to 1941-12-31 | open | B07-TRUST-OPEN-IRA |
| 5557 | 1931-02-13 | expiring 1931, period 10 | 1941-01-01 to 1941-12-31 | open | B07-TRUST-OPEN-IRA |
| 5575 | 1931-03-12 | expiring 1931, period 10 | 1941-01-01 to 1941-12-31 | open | B07-TRUST-OPEN-IRA |
| 5580 | 1931-03-16 | expiring 1931, period 10 | 1941-01-01 to 1941-12-31 | open | B07-TRUST-OPEN-IRA |
| 5626 | 1931-05-18 | expiring 1931, period 10 | 1941-01-01 to 1941-12-31 | open | B07-TRUST-OPEN-IRA |
| 5728 | 1931-09-29 | expiring 1931, period 10 | 1941-01-01 to 1941-12-31 | no | B07-TRUST-NO-OKLA-1941-07 |
| 5730 | 1931-10-08 | expiring 1931, period 10 | 1941-01-01 to 1941-12-31 | open | B07-TRUST-OPEN-IRA |
| 5734 | 1931-10-17 | expiring 1931, period 10 | 1941-01-01 to 1941-12-31 | open | B07-TRUST-OPEN-IRA |
| 5746 | 1931-11-10 | summary: expiring during 1931 and 1932; ten years | 1941-01-01 to 1942-12-31 | open | B07-TRUST-OPEN-IRA |
| 5768 | 1931-12-30 | expiring 1932, period 10 | 1942-01-01 to 1942-12-31 | open | B06-TRUST-OPEN-WHITE-EARTH |
| 5953 | 1932-11-23 | expiring 1933, period 10 | 1943-01-01 to 1943-12-31 | open | B06-TRUST-OPEN-WHITE-EARTH |
| 5955 | 1932-11-30 | expiring 1932, period 10 | 1942-01-01 to 1942-12-31 | no | B07-TRUST-NO-OKLA-1942-08 |
| 6341 | 1933-10-17 | text: expires on December 13, 1933; ten years from the date of the expiration | 1943-12-13 | open | B07-TRUST-OPEN-IRA |
| 6498 | 1933-12-15 | expiring 1934, period 10 | 1944-01-01 to 1944-12-31 | open | B06-TRUST-OPEN-6498 |
| 6926 | 1934-12-20 | expiring 1935, period 10 | 1945-01-01 to 1945-12-31 | no | B07-TRUST-NO-POSTIRA-6926 |
| 6939 | 1935-01-07 | expiring 1935, period 10 | 1945-01-01 to 1945-12-31 | open | B07-TRUST-OPEN-CESSATION |
| 6940 | 1935-01-07 | expiring 1935, period 10 | 1945-01-01 to 1945-12-31 | open | B07-TRUST-OPEN-P8-6940 |
| 6961 | 1935-02-04 | expiring 1935, period 10 | 1945-01-01 to 1945-12-31 | open | B07-TRUST-OPEN-CESSATION |
| 6962 | 1935-02-04 | expiring 1935, period 10 | 1945-01-01 to 1945-12-31 | open | B07-TRUST-OPEN-CESSATION |
| 6968 | 1935-02-09 | expiring 1935, period 10 | 1945-01-01 to 1945-12-31 | no | B07-TRUST-NO-POSTIRA-6968 |
| 7001 | 1935-04-05 | expiring 1935, period 10 | 1945-01-01 to 1945-12-31 | open | B07-TRUST-OPEN-CESSATION |
| 7009 | 1935-04-10 | expiring 1935, period 10 | 1945-01-01 to 1945-12-31 | no | B07-TRUST-NO-POSTIRA-7009 |
| 7036 | 1935-05-08 | expiring 1935, period 10 | 1945-01-01 to 1945-12-31 | no | B07-TRUST-NO-POSTIRA-7036 |
| 7206 | 1935-10-14 | expiring 1936, period 10 | 1946-01-01 to 1946-12-31 | no | B07-TRUST-NO-POSTIRA-7206 |
| 7464 | 1936-09-30 | text: expire December 31, 1936, or during 1937; 25 years from date of expiry | 1961-12-31 to 1962-12-31 | no | B07-TRUST-NO-POSTIRA-7464 |
