# PD-LAND-WITHDRAWAL: public land withdrawals and reserves

This doctrine covers the 1,270 undecided orders that X1 typed as `land_withdrawal_general` (1,093),
`power_site_reserve` (73), `public_water_reserve` (57), `mineral_withdrawal` (44) and `stock_driveway` (3). Its
machine form is `research/pothier/doctrines/PD-LAND-WITHDRAWAL.json` (schema `pothier-family-doctrine/v1`,
version 2). It applies the coordinator rulings P1-P8 in `research/pothier/COORDINATOR_RULINGS.md`.

Every result below is a status lead proposed for the owner. None of it is a status, a claim or a finding, and the
certified count stays at 0.

## Conclusions

The procedure decides 489 of the 1,270 members and leaves 781 open. These are the counts from
`python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-LAND-WITHDRAWAL.json --hints` on
2026-11-06, run against the members file that carries the Shepard and later-events edges.

**485 members are `no` leads (ended before the cutoff of 2026-10-14):**

- **219 were revoked as a whole by a later instrument** (`ACT`).
  - 88 by a later executive order. The order's held text names the member and says it "is hereby revoked", or
    says that it "supersedes" the member.
  - 130 by a Public Land Order (PLO). BLM's held Table of Public Land Orders lists each as "revoking EO No." the
    member, or as revoking the public water or reservoir site reserve the member created.
  - 1 by statute: EO 5237, revoked by the King Range Act.
- **208 had a single command that was exhausted on issue** (`TERM`, dated the order's own date).
  - 192 only revoke or restore land that another order withdrew (ruling P1, kind `spent_on_issue`).
  - 5 only authorize one completed act: a patent, a conveyance, a state selection or an exchange (also
    `spent_on_issue`).
  - 11 only amend another order, and their text merged into it (ruling P2, kind `merged_into_parent_on_issue`).
- **58 ended on their own terms** (`TERM`).
  - 32 opened restored land to ex-service men (veterans given first claim on reopened land) for 91 days, starting
    on a day the order itself fixed. Each ends on the order date plus 154 days, or plus 119 days for EO 3758.
  - 24 withdrew land "until March 5, 19xx" in aid of a pending bill.
  - EO 3192 ends on day 70, the date of its last opening.
  - EO 465 withdrew land for ninety days.

**4 members are `yes` leads (in force on the cutoff),** each resting on an official current record (`CURRENT`)
that the project does not yet retain.

- EO 3489 is carried in 43 CFR 2566. Only an extracted fragment of that section is held.
- EO 5907, 6019 and 6618 are listed as Authorized public water reserve cases in BLM's Oregon/Washington withdrawals
  layer, which was read on the web.

**781 members are open:**

- 411 are standing withdrawals. No held record shows them revoked as a whole, or in force on the cutoff.
- 221 depend on a future event whose date is not held, mostly the official filing of a plat of resurvey (a
  township's approved survey map).
- 71 belong to other families' doctrines.
- 28 are permits for a continuing use.
- 27 are land-district orders.
- 10 are restorations that keep a right.
- 13 have no usable text or fit no branch.

The engine flags 51 leads as contradicted by held evidence. Part (c) explains every flag. None of them changes a
lead.

## Terms used

- **Withdrawal / reservation.** An order that closes described public land to settlement, sale, entry or mining
  claims ("withdraws" it), usually for a stated public purpose ("reserves" it).
- **Restoration / revocation.** An order that ends a withdrawal, in whole or for described tracts. A partial
  revocation ("in so far as it affects", "only as to", "as to said township", "with other lands") leaves the rest
  of the order standing.
- **Pickett Act.** The Act of June 25, 1910, which let the President make temporary withdrawals.
- **Implied authority.** The power to withdraw land without a statute, upheld in *Midwest Oil* (1915).
- **Public Land Order (PLO).** A withdrawal, modification or revocation order signed by the Secretary of the
  Interior under the President's delegation, published in the Federal Register.
- **Public water reserve.** A spring or water hole withdrawn and kept open to public use under sec. 10 of the
  Stock-Raising Homestead Act.
- **Power site reserve.** Land withdrawn because it may be needed for water power.
- **Plat of resurvey.** The official map of a township's resurvey. Its filing in the land office ended some
  withdrawals and set the effective date of some revocations and openings.
- **Spent on issue** (coordinator term). An order whose only command takes full effect on its own date, leaving it
  nothing to command afterwards.
- **Merged into the parent** (coordinator term). An amending order whose text becomes part of the order it
  amends. Its text continues as part of the parent until the parent ends.
- **MLRS / LR2000.** BLM's Mineral & Land Records System and its legacy predecessor, the official database of land
  cases.
- **Edge.** A held link from a later instrument to a member, with its relation (revocation, amendment) and date.
  - Acts confined to part of an order (tracts, sections, "in part", "in so far as") carry the mechanism
    `partial_<mechanism>`.
  - No `no` lead rests on a `partial_` edge.

## (a) How members end or persist

**M1. Own terms: a stated date or period** (ends).
- **Withdrawals "until March 5, 19xx".** Twenty-four withdrawals in aid of a bill say the land is withdrawn "until
  March 5, 19xx". They add that if the bill is not enacted "and no other direction is given", the land "will, on
  March 5, 19xx, become subject to disposal ... without further order". If the bill was enacted, the statute
  disposed of the land. Either way the order ended on the stated date, unless a later instrument gave other
  direction.
  - On 2026-11-06 every member of this kind was checked against the Shepard edges, the later-events edges and
    BLM's PLO table headings. No held later instrument acts on any of them.
  - EO 2220 has the same form but was revoked again by PLO 384 in 1947, so it is decided separately.
- **EO 465.** It ran "for the period of ninety days from the date hereof".
- **EO 3192.** It restored land and fixed its openings by days counted from its own date. The last opening falls
  on the seventieth day.

**M2. Spent on issue** (ends; ruling P1).
- **What counts.** An order whose only operative content revokes or restores land withdrawn by another order
  takes effect on its own date. So does an order whose only command permits one act that is completed once done,
  such as a patent, a conveyance, a state selection or an exchange. Its effect belongs to the lifecycle of the
  order it acted on.
- **What does not count.** Ruling P1 excludes restorations that keep a right or a purpose: an overflow right, a
  right-of-way reserved to the United States, a patent condition, or "for aeronautical purposes, and for no other
  purpose". It also excludes orders that withdraw or reserve other land in the same instrument.
- **Deferred effect.** A revocation whose own text takes effect only on a future event is not spent on its signing
  date. An example is "This order shall become effective upon the date of the official filing of the plats of
  resurvey". Such a revocation stays open unless the date of the event is held (REVISION_BRIEF point 6).

**M3. Ex-service preference with a fixed start** (ends). Many revocations of 1922-1934 opened the released land
"only to entry under the homestead or desert land laws by qualified ex-service men ... for a period of 91 days
beginning with the 63rd day from and after the date hereof, and thereafter to appropriation ... by the general
public".
- The 91 days run from day 63 to day 153 after the order.
- The general opening on day 154 is the order's last command.
- EO 3758 counts from the 28th day, so its last command falls on day 119.

**M4. Later revoking instrument** (ends).
- **Who revokes.** Before 1942 a later executive order revoked these orders. From 1942 on, a Public Land Order did
  so, under the President's delegation to the Secretary in EO 9146 (1942), EO 9337 (1943) and EO 10355 (1952).
- **What counts.** Only a revocation of the whole order counts.
- **Its date.** The date is the revoking instrument's effective date, where the instrument states one. Otherwise it
  is the signing date, which for a PLO is the signature date in BLM's table.

**M5. Statute** (ends). The Pickett Act provides for revocation "by an Act of Congress". Pub. L. 91-476, sec. 8
(84 Stat. 1067, 1070) revoked EO 5237 with effect from the date the Secretary established the King Range National
Conservation Area.

**M6. Standing until revoked; FLPMA continuity** (continuity only).
- **The rule.** Pickett Act withdrawals and implied-authority withdrawals stay in force until revoked.
- **FLPMA.** The Federal Land Policy and Management Act of 1976 (FLPMA) changed this on 1976-10-21 in two ways.
  - Sec. 701(c) kept every withdrawal then in effect "in full force and effect until modified".
  - Sec. 704(a) repealed the authority to make new withdrawals. That repeal is not an end of existing withdrawals
    (ruling P3).
- **The lead.** A member with no own term and no verified whole revocation stays open. Absence of a found
  revocation is not evidence that the order is in force.

**M7. FLPMA sec. 204(l) review** (lead only). FLPMA directed a review of withdrawals in eleven western States. Its
recommendations produced many of the PLO revocations counted under M4, but the review itself ends nothing.

**M8. Future-event dates** (lead only). No held source gives the date for any of these:
- resurvey withdrawals of 1923-1927 that last "until ... the approved plat thereof is officially filed";
- revocations whose effect waits for the plat filing or for the Secretary's notice;
- ex-service openings that begin with the plat filing.

**M9. Current official record** (persists). A regulation or a BLM land-status record shows the order or its
operative effect in force.

**M10. Statutes governing reserve types** (lead only).
- **Power-site reserves.** Federal Power Act sec. 24 governs them.
- **Water reserves and stock driveways.** Sec. 10 of the Stock-Raising Homestead Act governs them.
- **Reservations for Indian use and occupation.** Since the Act of Mar. 3, 1927, ch. 299, sec. 4, 44 Stat. 1347
  (25 U.S.C. 398d), their boundaries can be changed only by Act of Congress. FLPMA sec. 704(a) repealed only that
  section's proviso (held FLPMA p. 2792).
- **Effect.** None of these statutes ends a reserve.

**M11. Merged into the parent** (ends as a command; ruling P2). Under the strike-and-insert ruling
(D-20261021-strike-and-insert), an order whose only operative content amends another order merges into the parent
on issue.
- Every such lead carries the disclosure "its text continues as part of the parent until the parent ends; the
  parent's lifecycle carries it".
- If the owner treats an amending order as living as long as the amended text lives, these 11 leads become open
  pending the parent. EO 3529 and 5136 would then become `yes` with EO 3489.

FLPMA sec. 702 repealed the ex-service preference resolutions and the homestead laws in 1976. That repeal removes
the authority for the openings under M3 and M8, and under ruling P3 it is not an end.

## (b) Primary sources

**Held.** The text is in the repository, and the pin was found in it.

| Id | Source | Path (sha256) | Pin |
|---|---|---|---|
| S0 | The member's own order text (`member_text`, ruling P6) | recorded per lead | — |
| S3, S4, S19 | FLPMA, Pub. L. 94-579, secs. 701(c), 702, 704(a), 90 Stat. 2743, 2786-2792 | `jobs/astra-source-retention/output/pages/3949c2ad.../08af9986.../selected-pages.txt` (e14185c6...) | "(c) All withdrawals, reservations, classifications, and designations"; "the implied authority of the President to make withdrawals and"; "Feb. 14,1920 76 41:434" |
| S6 | EO 9146, Apr. 24, 1942, 7 FR 3067 | `jobs/fr-originals/output/texts/EO_9146.txt` (729a941b...) | "I hereby authorize the Secretary of the Interior to sign all orders withdrawing or reserving public lands" |
| S7 | EO 9337, Apr. 24, 1943, 8 FR 5516 (mirror transcription) | `jobs/app-executive-orders/output/texts/executive-order-9337-...txt` (8006154b...) | "to modify or revoke withdrawals or reservations of such lands" |
| S8 | EO 10355, May 26, 1952, 17 FR 4831 (1989 codification) | `jobs/ofr-codification-1989/output/texts/EO_10355.txt` (ea88e35c...) | "shall be designated as public land orders" |
| S9 | BLM Table of Public Land Orders 1-7898, parsed | `jobs/shepard-citations/output/PLO_TABLE.csv` (1317b2b2...); raw text layers in `jobs/shepard-citations/output/texts/blm/` | per member, e.g. "revoking EO No. 1082" |
| S10 | Shepard reverse-citation index | `jobs/shepard-citations/output/EDGES.csv` (922449f4...) | leads, re-checked as described in (c) |
| S11 | Later-events edges | `jobs/later-events/output/EDGES.csv` (0ee5b121...) | leads, re-checked |
| S12 | Pub. L. 91-476, sec. 8, 84 Stat. 1067, 1070 (16 U.S.C. 460y-7), fragment from the OLRC release point 119-121 | `jobs/current-law/output/FRAGMENTS.jsonl` (38258ad1...) | "that Executive order is hereby revoked effective as of the date the Secretary establishes the area" |
| S14 | 43 CFR 2566.0-3 and 2566.0-7, fragment of the GovInfo eCFR bulk XML (the section is not yet retained) | same file | "Sections 2566.1 and 2566.2 are amended by E.O. 3529" |
| S20 | 43 CFR 2300.0-3 (eCFR 2026-11-04) | `jobs/theophilus-sources/output/texts/cfr-t43-2300.0-3.txt` (33342f1e...) | "shall remain in full force and effect until modified under the provisions of the Act or other applicable law" |

The revoking executive orders' held texts (path and sha256) and the PLO table rows, with the PLO's own Federal
Register page, are given per member in the JSON's `verified_whole_revocations` table and in the appendix. Where
BLM's table also lists a correction, the appendix gives the PLO's own page and the correction page.

**Read on the web, not held, to acquire.** Every lead that rests on one of these sources carries the gap
automatically.

| Id | Source | URL |
|---|---|---|
| S1 | Pickett Act, 36 Stat. 847 ("shall remain in force until revoked by him or by an Act of Congress") | https://www.govinfo.gov/content/pkg/STATUTE-36/pdf/STATUTE-36-Pg847.pdf |
| S2 | United States v. Midwest Oil Co., 236 U.S. 459 (1915) | https://www.govinfo.gov/content/pkg/USREPORTS-236/pdf/USREPORTS-236-459.pdf |
| S5 | FLPMA sec. 204(l), 90 Stat. 2754-2755 | https://www.govinfo.gov/content/pkg/STATUTE-90/pdf/STATUTE-90-Pg2743.pdf |
| S13 | BLM notice, King Range NCA, 67 FR 63448 (Oct. 11, 2002) | https://www.govinfo.gov/content/pkg/FR-2002-10-11/pdf/02-25924.pdf |
| S15 | BLM Oregon/Washington withdrawals layer (MLRS/LR2000 cases) | https://gis.blm.gov/orarcgis/rest/services/Land_Status/BLM_OR_Withdrawals/MapServer/1 |
| S16 | BLM Withdrawals Spatial Data Standard v1.1 (2018) | https://gis.blm.gov/ORDownload/DataStandards/Withdrawals_Spatial_Data_Standard_v1.1.pdf |
| S17 | Federal Power Act sec. 24, 16 U.S.C. 818 | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title16-section818&num=0&edition=prelim |
| S18 | Stock-Raising Homestead Act sec. 10, 39 Stat. 862, 865 | https://www.govinfo.gov/content/pkg/STATUTE-39/pdf/STATUTE-39-Pg862.pdf |

Some related orders are not members of this family:
- The Taylor Grazing Act withdrawals, EO 6910 and EO 6964.
- Public Water Reserve No. 107 (April 17, 1926), an unnumbered order. EO 5106, which excluded Alaska from it, is a
  member and is spent on issue.

## (c) Decision procedure

Branches are tried in the order the JSON lists them, and the first match decides. "Summary" means the WPA 1944
summary; "text" means the member's held text.

| Branch | Members | Lead | Rule | Basis and date | Gaps |
|---|---|---|---|---|---|
| B01_* | 42 | open | Another family's subject: INDIAN 5 (trust periods, liquor treaty), PERSON 12 (one act for one named person, P4: EO 975, 1135, 2501, 2551, 2712, 3178, 4015, 6170 and four others), WAR 9, CUSTOMS 1, CS 2, ADMIN 13. EO 3077 (a Wrangell townsite lot reserved for the Treasury) is excluded, because its WAR match comes from a neighbouring summary | Decide under PD-INDIAN, PD-CS-ONE-PERSON, PD-WAR-EMERGENCY, PD-CUSTOMS-CONSULAR, PD-CS-RULES or PD-ADMIN | — |
| B02 | 1 | yes | EO 3489 | CURRENT: 43 CFR 2566.0-3 and 2566.0-7 carry its townsite regulations. Held only as a fragment; the section is not yet retained | Retained copy of both sections dated on or after 2026-10-14, with sha256 |
| B03 | 3 | yes | EO 5907, 6019, 6618 | CURRENT: BLM's OR/WA withdrawals layer lists ORD_TYPE EO, ORD_NUM equal to the order, case type 231104, disposition 5 (Authorized). Read on the web 2026-11-05; not yet retained | Retained, dated JSON export of the layer query, with sha256. Covers the Oregon tracts only |
| B04 | 1 | no | EO 5237 | ACT: Pub. L. 91-476 sec. 8, 84 Stat. 1067, 1070. Interval 1970-10-21 to 2002-10-11 | Establishment notice not held |
| B05_* | 3 | no | EO 1713, 5384, 2220: two candidate instruments each | ACT: interval up to the later instrument (1981-01-15, 1967-04-06, 1947-07-25) | PLO texts |
| B06 | 196 | no | On the verified list, and the member holds a whole-order edge (no `partial_` mechanism) | ACT: `edge_date`, where the earliest whole-order edge is the verified instrument | PLO texts not held |
| B07_* | 15 | no | Verified, but the held edge has no date, carries only a signing date, or is a misattribution from a neighbouring page | ACT: fixed date from the revoking text. EO 1291: 1925-09-25. EO 2060: 1916-09-20. EO 4764: 1928-09-26. EO 4901: 1940-10-26 (EO 8529 effective on its 60th day). EO 3474: 1927-03-17. EO 4105: 1936-06-15 | — |
| B08_* | 4 | no | Verified PLO revocation, plus an earlier held edge that is partial or expressly does not revoke (EO 2538: EO 3863 "Eliminating certain lands from"; EO 3264: EO 9026 "shall not rescind or revoke"; EO 4559 and 5258: eliminations) | ACT: PLO signature date | PLO text |
| B10_* | 24 | no | Text: withdrawn "until (or on) March 5, YYYY", with no revoking clause, or one of the listed OCR cases (EO 1878, 3651) | TERM: fixed March 5 of that year | Checked: no held later instrument acts on any member. A later order "giving other direction" that is not held would postpone the end |
| B11 | 1 | no | EO 465, ninety days | TERM: `order_date_plus_days` 90 | — |
| B24_REGS | 2 | no | EO 3529, 5136: only amend EO 3489's townsite regulations | TERM: order date; `merged_into_parent_on_issue` with the P2 disclosure. The parent's current predicate is 43 CFR 2566.0-3 | Parent's status (B02) |
| B24 | 9 | no | Listed members whose only content amends another order or its terms (EO 1205, 2354, 2579, 2641, 2823A, 2982, 6016, 7038, 7047) | TERM: order date; `merged_into_parent_on_issue` with the P2 disclosure | Parent's status |
| B19 | 10 | open | Restoration that keeps a right or purpose | Ruling P1 limit | Whether the retained right still operates |
| B19D | 50 | open | Text defers the order's effect to the official filing of the plat of resurvey or to a date to be fixed | Not spent on its signing date (REVISION_BRIEF point 6) | Plat filing dates |
| B21_3192 | 1 | no | EO 3192, openings on days 63 and 70 | TERM: `order_date_plus_days` 70 | — |
| B20 | 192 | no | Summary shows only a revocation or restoration (revoked, restored, diminished, eliminated, Restoration No.). Excludes any new reservation, retained right, deferred effect, ex-service opening or amendment beyond "to restore/eliminate", and EO 4867, 324B, 5931 and 576, which withdraw or reserve other land or make a standing rule | TERM: order date; `spent_on_issue` | The effect belongs to the parent |
| B21_63, B21_28 | 31, 1 | no | Ex-service opening whose 91 days begin on the 63rd (28th) day after the order, or one of the listed OCR cases (EO 4092, 4735, 4855, 4936) | TERM: `order_date_plus_days` 154 (119) | — |
| B22 | 116 | open | Ex-service opening that starts with the plat filing or a date the Secretary is to fix (EO 6171 listed) | Revocation spent; opening awaits a date. FLPMA sec. 702 is not an end (P3) | Plat filing dates |
| B23 | 5 | no | Listed members (EO 2442, 3913, 6053, 6110, 7105) authorizing one completed conveyance, selection or exchange | TERM: order date; `spent_on_issue` (P1) | — |
| B25 | 28 | open | Permission for a continuing use: a Federal Power Commission licence, right-of-way, pipeline crossing, transmission line, lease or construction permit for a party or project | Own reasoning under D-20261028-evidence-decides: such a permit operates while the use lasts, so it is not exhausted on issue | Licence or right-of-way status, and the parent's status |
| B29 | 32 | open | Listed members revoked as a whole by a later order "effective upon the date of the official filing of the plats of resurvey" (EO 6774 by EO 8241 included) | Not shown to have taken effect | Plat filing dates |
| B30 | 23 | open | Text: resurvey withdrawal lasting "until ... the approved plat ... is officially filed". EO 3867 falls here (EO 4653 revoked it only as to two townships) | Own term not shown to have occurred | Plat filing dates |
| B01_INDIAN_RES | 29 | open | Reservation for Indian use, occupancy, schools or agencies, other than irrigation-project sites | Belongs to PD-INDIAN. 25 U.S.C. 398d requires an Act of Congress to change reservations for Indian use and occupation | Decide under PD-INDIAN |
| B34 | 27 | open | Land-district or land-office order | No held instrument ends it | The consolidation or abolition order |
| B31 | 26 | open | Public water reserve or stock driveway | Standing (M6, M10) | MLRS case or PLO |
| B32 | 3 | open | Power or reservoir site | Standing | MLRS case or PLO |
| B33 | 12 | open | Mineral withdrawal; also EO 576, which keeps coal-withdrawn lands inside forest reserves | Standing | MLRS case, PLO or statute |
| B26 | 12 | open | Amendment or enlargement that withdraws, adds or releases lands of its own (EO 1584 restates and withdraws an area; EO 6734 adds lots; EO 324B reserves land in lieu) | Standing | MLRS case or PLO |
| B35 | 358 | open | Any other withdrawal of named lands | Standing (M6) | MLRS case or PLO |
| B99 | 13 | open | No usable summary or text, a transfer of land between departments, or another subject no branch covers | — | Read the text |

**How the verified list was built.** The `verified_whole_revocations` side table (218 members) re-checks every
Shepard and later-events revocation lead against its source. A lead was admitted only if it passed one of the
following tests.

- **Executive order, cited by number.** Every one of these must hold:
  - The revoking order's held text names the member by number, or lists it in "Executive Orders Nos. ...".
  - Where the member's date is printed, it matches.
  - The text says "is hereby revoked" (OCR spacing allowed), or "This order supersedes Executive Order No. ...".
  - Nothing before or after limits it. Disqualifying phrases are "so much of", "in so far", "only as to", "as to",
    "in part", "with respect to", "with other lands", "of the [named lands]" and "the following-described".
  - Its effect is not deferred to a plat filing. A stated later effective date is used as the end date (EO 4901).
  - For ProQuest page scans, which can run into the neighbouring order, the revoking order's WPA summary must
    also name the member.
- **Executive order, cited by date only.** The revoking order's WPA summary names the member as "E. O. [N]" and
  says "revoked", with no partial words.
- **BLM PLO table.** Every one of these must hold:
  - The heading clause names the member. It may give the order as "EO No.", "EO" or "Executive Order No.", or it
    may name the public water or reservoir site reserve that the member's own summary says it created.
  - The clause says "revoking" or "Revocation of", and is cut at "and revoking in part" or "Amended/Corrected by".
  - A date printed after the number matches the member's date.
  - The heading's State is one of the member's States.

**The 51 contradiction flags.**

**12 `acted_on_after_lead_end`.** None of these later "amendment" or "modification" edges revives a command of
the member.
- **Reserve-number attribution (8 flags).** EO 5106, 5360, 5372, 5379, 5467, 5590 and 6856 are restorations that
  name a power-site, public-water, reservoir-site or petroleum reserve. Shepard resolves later instruments acting
  on that reserve to the earliest member that names its number (flag `reserve_creator_inferred`). Those
  instruments really act on the reserve, which is the parent order. EO 3474 (B07) is in the same position: EO 5904
  acts on Naval Petroleum Reserve No. 3, not on EO 3474, which EO 4614 revoked in 1927.
- **EO 3189.** The edge from EO 3248 cites EO 3189 only as an earlier amender of the parent, EO 2593 ("as modified
  by").
- **EO 4678.** EO 5592 recites EO 4678 as a past partial revocation.
- **EO 4105 (B07).** The edge from EO 8813 (1941) is a match by date to a partial revocation of a different order
  of November 22, 1924. EO 7387 superseded EO 4105 on 1936-06-15.
- **EO 4044.** EO 4055 (1924-07-30) amended EO 4044 "so as to vacate the restoration ... for the described tracts
  of land within the Chugach National Forest". That narrowed what EO 4044 restored. Under P2 the amendment merged
  into EO 4044, and EO 4044's own command, the restoration of the other tracts, was spent on 1924-07-03.

**3 `no_lead_but_current_law_predicate_lead`.**
- **EO 5237.** 16 U.S.C. 460y-8 still describes lands "withdrawn by Executive Order 5237" in the King Range area's
  boundary. That is a boundary reference in the statute that revoked the order.
- **EO 3529 and EO 5136.** 43 CFR 2566.0-3 names them as having amended the regulations of EO 3489. Under P2 their
  text lives in the parent, and that CFR section is the parent's current predicate (B02).

**36 `persistence_lead_but_held_ending_edge`.** Each is an open standing withdrawal carrying a held whole-order
"revocation" edge that failed verification.
- **Partial in substance (18).** The revoking text or its WPA summary confines the act ("as to said township",
  "with other lands", "in so far as", "eliminated from the operation of"). Shepard's own window did not catch the
  limit, so these edges keep the plain mechanism `revocation`. They show the order alive at that date and leave
  the rest standing. Members: EO 343C, 3737, 4554, 4608, 4624, 4652, 4726, 4843, 4882, 4921, 4997, 5098, 5109,
  5140, 5323, 5408, 5836 and 6076.
- **Revoke "the following-described lands" (8).** Whether the listed lands are all of the order's lands was not
  checked. Comparing land descriptions would decide these.
  - EO 2593 (by EO 4279), 2984 (EO 4419), 4289 (EO 7375), 4980 (EO 6666), 5202 (EO 6642) and 5805 (EO 6563).
  - EO 2665 (EO 6760). This revocation is also deferred to the plat filing.
  - EO 3450 (EO 3542, a Wikisource note citing only "Executive Order of May 3, 1921", a date that EO 3450 shares
    with EO 3451).
- **Revoke "the withdrawal made by EO N of [named tracts]" (2).** These may be partial: EO 4103 (EO 4674) and
  4345 (EO 4855).
- **PLO headings that fail a check (3).** The PLO texts would decide all three.
  - EO 3297 (PLO 1562): the heading is dated July 21, 1920, but the member is dated June 30, 1920.
  - EO 4097 (PLO 6147) and 5118 (PLO 5824): the heading names no State.
- **Citation by date only, not confirmed by number (3).** EO 1683 (EO 3081, which prints "(No. 1683)"), 328B
  (EO 1746) and 1967A (EO 2297 and 7325, which are partial eliminations).
- **OCR-damaged revoking verb (1).** EO 2459 (EO 2710, "hereb c, revoked").
- **Multi-State reserve (1).** EO 5327, the oil-shale withdrawal. EO 5552 eliminated Utah lands, and PLO 6866
  revoked it "as amended by PLO 4522" in Wyoming only. Its other lands are not shown revoked.

## (d) What the procedure cannot decide

The 781 open members fall into these groups.

**411 standing withdrawals**: B26 (12), B31 (26), B32 (3), B33 (12) and B35 (358). These sources would decide
most of them:
- BLM's national MLRS layer "Withdrawals Case Land Status"
  (`nlsdbpubgis.blm.gov/arcgis/rest/services/Land_Tenure/Withdrawals_Case_Land_Status/MapServer/0`). It gives the
  case serial, name, disposition and land status.
- BLM's State withdrawal layers. The Oregon/Washington layer, with ORD_TYPE "EO" and ORD_NUM, is the model.
- The MLRS case abstracts.
- A GovInfo Federal Register search for 1936-1994 (`api.govinfo.gov/search`) for "Executive Order No. NNNN" and
  for reserve numbers.

**221 that depend on a future event**: B19D (50), B22 (116), B29 (32) and B30 (22 resurvey withdrawals, plus
EO 3867). The dates of the official filings are in BLM's General Land Office Records survey plats by township
(glorecords.blm.gov, which needs a browser). A held filing date would turn most of these into `no` leads.

**71 that belong to other families**: B01_* (42) and B01_INDIAN_RES (29).

**The rest**:
- 28 continuing-use permits (B25), which live with the licence or right-of-way.
- 27 land-district orders (B34). The instrument that consolidated or abolished each district is not held.
- 10 restorations that keep a right (B19).
- 13 members on B99.

**Acquisitions for decided leads that rest on unheld records**, all listed in `FETCH_PROPOSED.jsonl`:
- B05-B08: the texts of 124 PLOs, by their own Federal Register pages, plus the correction pages where BLM lists
  one.
- B03: the BLM Oregon/Washington layer export.
- B04: the King Range establishment notice.
- B02: the retained 43 CFR 2566 sections.

## Appendix: verified whole revocations (members on B05-B08)

| Member | Branch | Revoking instrument | Date | Where the revocation is printed |
|---|---|---|---|---|
| EO 760 | B06 | EO 773 | 1908-03-23 | jobs/wikisource-texts/output/texts/EO_773.txt |
| EO 771 | B06 | PLO 359 | 1947-03-14 | BLM PLO table; 12 FR 1944 |
| EO 773 | B06 | PLO 470 | 1948-04-21 | BLM PLO table; 13 FR 2294 |
| EO 782 | B06 | PLO 7379 | 1999-03-12 | BLM PLO table; 64 FR 14261 |
| EO 808 | B06 | PLO 6214 | 1982-03-11 | BLM PLO table; 47 FR 11668 |
| EO 965 | B06 | PLO 1116 | 1955-04-08 | BLM PLO table; 20 FR 2464 |
| EO 1082 | B06 | PLO 6748 | 1989-09-13 | BLM PLO table; 54 FR 38525 |
| EO 1133 | B06 | PLO 1296 | 1956-04-27 | BLM PLO table; 21 FR 2946 (correction 21 FR 3148) |
| EO 1229 | B06 | PLO 1224 | 1955-09-14 | BLM PLO table; 20 FR 7076 |
| EO 1232 | B06 | PLO 2685 | 1962-05-24 | BLM PLO table; 27 FR 5097 |
| EO 1291 | B07_1291 | EO 4313 | 1925 | jobs/pinakes-proquest-ingest/output/texts/EO_4313.txt |
| EO 1297 | B06 | PLO 1469 | 1957-08-19 | BLM PLO table; 22 FR 6876 |
| EO 1513 | B06 | PLO 363 | 1947-04-09 | BLM PLO table; 12 FR 2478 |
| EO 1540 | B06 | EO 1798 | 1913-07-18 | jobs/app-executive-orders/output/texts/executive-order-1798-revocation-executive-order-no-1540.txt |
| EO 1713 | B05_1713 | PLO 1156 | 1955-05-27 | BLM PLO table; 20 FR 3877 |
| EO 1713 | B05_1713 | PLO 5815 | 1981-01-15 | BLM PLO table; 46 FR 6945 |
| EO 1856 | B06 | EO 1939 | 1914-05-15 | jobs/pinakes-proquest-ingest/output/texts/EO_1939.txt |
| EO 2060 | B07_2060 | EO 2457 | 1916 | jobs/pinakes-proquest-ingest/output/texts/EO_2457.txt |
| EO 2220 | B05_2220 | PLO 384 | 1947-07-25 | BLM PLO table; 12 FR 5259 |
| EO 2245B | B06 | PLO 1225 | 1955-09-21 | BLM PLO table; 20 FR 7189 |
| EO 2347 | B06 | PLO 3572 | 1965-03-26 | BLM PLO table; 30 FR 4254 |
| EO 2472 | B06 | EO 2671 | 1917-07-23 | jobs/wikisource-texts/output/texts/EO_2671.txt |
| EO 2538 | B08_2538 | PLO 1093 | 1955-03-15 | BLM PLO table; 20 FR 1659 |
| EO 2553 | B06 | PLO 5564 | 1975-12-16 | BLM PLO table; 40 FR 58857 |
| EO 2658 | B06 | PLO 369 | 1947-05-15 | BLM PLO table; 12 FR 2038 |
| EO 2727 | B06 | PLO 3023 | 1963-04-08 | BLM PLO table; 28 FR 3661 |
| EO 2854 | B06 | PLO 551 | 1949-02-04 | BLM PLO table; 14 FR 695 |
| EO 2909 | B06 | PLO 5510 | 1975-06-25 | BLM PLO table; 40 FR 27939 |
| EO 2963 | B06 | PLO 1024 | 1954-10-26 | BLM PLO table; 19 FR 7114 |
| EO 2981 | B06 | PLO 870 | 1952-10-24 | BLM PLO table; 17 FR 9776 |
| EO 3105 | B06 | EO 4092 | 1924-10-24 | jobs/pinakes-proquest-ingest/output/texts/EO_4092.txt |
| EO 3264 | B08_3264 | PLO 1727 | 1958-09-04 | BLM PLO table; 23 FR 7004 |
| EO 3308 | B06 | PLO 425 | 1947-11-12 | BLM PLO table; 12 FR 7843 |
| EO 3314 | B06 | PLO 451 | 1948-03-01 | BLM PLO table; 13 FR 1264 |
| EO 3346 | B06 | EO 5971 | 1932-12-14 | jobs/ofr-compilations/output/texts/EO_5971.txt |
| EO 3410 | B06 | PLO 7129 | 1995-03-21 | BLM PLO table; 60 FR 16584 |
| EO 3473 | B06 | PLO 792 | 1952-01-19 | BLM PLO table; 17 FR 771 |
| EO 3474 | B07_3474 | EO 4614 | 1927-03-17 | jobs/pinakes-proquest-ingest/output/texts/EO_4614.txt |
| EO 3480 | B06 | PLO 1803 | 1959-02-20 | BLM PLO table; 24 FR 1464 |
| EO 3617 | B06 | PLO 1667 | 1958-06-24 | BLM PLO table; 23 FR 4811 |
| EO 3655 | B06 | PLO 6175 | 1982-02-25 | BLM PLO table; 47 FR 9839 |
| EO 3743 | B06 | PLO 1107 | 1955-03-29 | BLM PLO table; 20 FR 2083 |
| EO 3747 | B06 | PLO 1209 | 1955-08-23 | BLM PLO table; 20 FR 6339 |
| EO 3814 | B06 | PLO 502 | 1948-07-27 | BLM PLO table; 13 FR 4481 |
| EO 3815 | B06 | EO 5162 | 1929-07-24 | jobs/app-executive-orders/output/texts/executive-order-5162-restoring-certain-reserved-lands-withdrawn-for-airplane-landing-field.txt |
| EO 3819 | B06 | PLO 1594 | 1958-02-28 | BLM PLO table; 23 FR 1600 |
| EO 3858 | B06 | EO 4665 | 1927-06-10 | jobs/pinakes-proquest-ingest/output/texts/EO_4665.txt |
| EO 3882 | B06 | EO 4734 | 1927-10-01 | jobs/pinakes-proquest-ingest/output/texts/EO_4734.txt |
| EO 3918 | B06 | EO 5446 | 1930-09-18 | jobs/app-executive-orders/output/texts/executive-order-5446-revocation-withdrawal-public-lands-for-resurvey.txt |
| EO 3954 | B06 | EO 4707 | 1927-08-13 | jobs/pinakes-proquest-ingest/output/texts/EO_4707.txt |
| EO 3967 | B06 | EO 4897 | 1928-05-28 | jobs/pinakes-proquest-ingest/output/texts/EO_4897.txt |
| EO 3982 | B06 | EO 4015 | 1924-05-31 | jobs/pinakes-proquest-ingest/output/texts/EO_4015.txt |
| EO 4000 | B06 | EO 4746 | 1927-10-21 | jobs/pinakes-proquest-ingest/output/texts/EO_4746.txt |
| EO 4014 | B06 | PLO 485 | 1948-06-09 | BLM PLO table; 13 FR 3341 |
| EO 4060 | B06 | PLO 6214 | 1982-03-11 | BLM PLO table; 47 FR 11668 |
| EO 4082 | B06 | PLO 6287 | 1982-06-16 | BLM PLO table; 47 FR 27292 |
| EO 4096 | B06 | PLO 5846 | 1981-01-15 | BLM PLO table; 46 FR 7346 |
| EO 4105 | B07_4105 | EO 7387 | 1936-06-15 | jobs/app-executive-orders/output/texts/executive-order-7387-reservation-naval-station-balboa-canal-zone.txt |
| EO 4106 | B06 | PLO 1174 | 1955-06-24 | BLM PLO table; 20 FR 4686 |
| EO 4127 | B06 | PLO 444 | 1948-01-30 | BLM PLO table; 13 FR 615 |
| EO 4144 | B06 | PLO 2966 | 1963-03-18 | BLM PLO table; 28 FR 2908 |
| EO 4170 | B06 | PLO 6226 | 1982-03-12 | BLM PLO table; 47 FR 11675 |
| EO 4181 | B06 | PLO 5894 | 1981-05-18 | BLM PLO table; 46 FR 28416 |
| EO 4202 | B06 | PLO 5941 | 1981-05-18 | BLM PLO table; 46 FR 28855 |
| EO 4212 | B06 | EO 4895 | 1928-05-26 | jobs/pinakes-proquest-ingest/output/texts/EO_4895.txt |
| EO 4213 | B06 | EO 4669 | 1927-06-18 | jobs/pinakes-proquest-ingest/output/texts/EO_4669.txt |
| EO 4222 | B07_4222 | EO 5181 | 1929-08-29 | jobs/app-executive-orders/output/texts/executive-order-5181-restoring-certain-reserved-lands-pending-resurvey-and-opening-such.txt |
| EO 4229 | B06 | EO 4670 | 1927-06-18 | jobs/pinakes-proquest-ingest/output/texts/EO_4670.txt |
| EO 4231 | B06 | PLO 6325 | 1982-08-30 | BLM PLO table; 47 FR 39494 |
| EO 4253 | B06 | EO 4861 | 1928-04-23 | jobs/pinakes-proquest-ingest/output/texts/EO_4861.txt |
| EO 4261 | B06 | PLO 1363 | 1956-11-14 | BLM PLO table; 21 FR 8992 |
| EO 4267 | B06 | EO 4675 | 1927-06-29 | jobs/pinakes-proquest-ingest/output/texts/EO_4675.txt |
| EO 4270 | B06 | PLO 996 | 1954-08-20 | BLM PLO table; 19 FR 5444 |
| EO 4287 | B06 | PLO 6319 | 1982-08-30 | BLM PLO table; 47 FR 39492 |
| EO 4309 | B06 | EO 4643 | 1927-05-05 | jobs/pinakes-proquest-ingest/output/texts/EO_4643.txt |
| EO 4322 | B06 | EO 5420 | 1930-08-05 | jobs/app-executive-orders/output/texts/executive-order-5420-revocation-withdrawal-public-lands-for-resurvey.txt |
| EO 4323 | B06 | EO 4837 | 1928-03-21 | jobs/pinakes-proquest-ingest/output/texts/EO_4837.txt |
| EO 4326 | B06 | EO 4673 | 1927-06-22 | jobs/pinakes-proquest-ingest/output/texts/EO_4673.txt |
| EO 4327 | B06 | EO 4875 | 1928-05-03 | jobs/pinakes-proquest-ingest/output/texts/EO_4875.txt |
| EO 4339 | B06 | PLO 136 | 1943-06-09 | BLM PLO table; 8 FR 8761 |
| EO 4346 | B06 | EO 4838 | 1928-03-21 | jobs/pinakes-proquest-ingest/output/texts/EO_4838.txt |
| EO 4371 | B06 | PLO 2508 | 1961-09-25 | BLM PLO table; 26 FR 9227 |
| EO 4404 | B06 | EO 4469 | 1926-06-30 | jobs/pinakes-proquest-ingest/output/texts/EO_4469.txt |
| EO 4412 | B06 | EO 4663 | 1927-06-08 | jobs/pinakes-proquest-ingest/output/texts/EO_4663.txt |
| EO 4424 | B06 | EO 4656 | 1927-05-26 | jobs/pinakes-proquest-ingest/output/texts/EO_4656.txt |
| EO 4425 | B06 | EO 5675 | 1931-08-07 | jobs/ofr-compilations/output/texts/EO_5675.txt |
| EO 4426 | B06 | EO 5810 | 1932-02-27 | jobs/ofr-compilations/output/texts/EO_5810.txt |
| EO 4456 | B06 | PLO 6050 | 1981-10-20 | BLM PLO table; 46 FR 53169 |
| EO 4468 | B06 | EO 5944 | 1932-11-01 | jobs/ofr-compilations/output/texts/EO_5944.txt |
| EO 4478 | B06 | EO 5524 | 1931-01-05 | jobs/app-executive-orders/output/texts/executive-order-5524-revocation-withdrawal-public-land-pending-resurvey-colorado.txt |
| EO 4506 | B07_4506 | EO 5177 | 1929-08-23 | jobs/app-executive-orders/output/texts/executive-order-5177-restoring-certain-reserved-lands-pending-resurvey-and-opening-such.txt |
| EO 4559 | B08_4559 | PLO 6495 | 1983-12-18 | BLM PLO table; 48 FR 56754 |
| EO 4570 | B06 | PLO 927 | 1953-11-18 | BLM PLO table; 18 FR 7494 |
| EO 4586 | B06 | EO 4936 | 1928-07-16 | jobs/pinakes-proquest-ingest/output/texts/EO_4936.txt |
| EO 4592 | B06 | PLO 2193 | 1960-08-24 | BLM PLO table; 25 FR 8257 |
| EO 4638 | B06 | EO 5485 | 1930-11-14 | jobs/app-executive-orders/output/texts/executive-order-5485-revocation-withdrawal-public-lands-for-resurvey.txt |
| EO 4641 | B06 | PLO 1543 | 1957-11-01 | BLM PLO table; 22 FR 8983 |
| EO 4654 | B06 | PLO 5907 | 1981-05-18 | BLM PLO table; 46 FR 28418 |
| EO 4657 | B06 | EO 5674 | 1931-08-07 | jobs/ofr-compilations/output/texts/EO_5674.txt |
| EO 4695 | B06 | EO 5440 | 1930-09-05 | jobs/app-executive-orders/output/texts/executive-order-5440-revocation-withdrawal-public-lands-for-resurvey.txt |
| EO 4719 | B06 | PLO 3602 | 1965-04-05 | BLM PLO table; 30 FR 4679 |
| EO 4725 | B06 | EO 5413 | 1930-07-29 | jobs/app-executive-orders/output/texts/executive-order-5413-revocation-withdrawal-public-lands-for-resurvey.txt |
| EO 4745 | B06 | EO 5678 | 1931-08-10 | jobs/ofr-compilations/output/texts/EO_5678.txt |
| EO 4763 | B07_4763 | EO 5178 | 1929-08-28 | jobs/app-executive-orders/output/texts/executive-order-5178-restoring-certain-reserved-lands-pending-resurvey-and-opening-such.txt |
| EO 4764 | B07_4764 | EO 4968 | 1928 | jobs/pinakes-proquest-ingest/output/texts/EO_4968.txt |
| EO 4766 | B07_4766 | EO 5179 | 1929-08-28 | jobs/app-executive-orders/output/texts/executive-order-5179-restoring-certain-reserved-lands-pending-resurvey-and-opening-such.txt |
| EO 4774 | B06 | PLO 6287 | 1982-06-16 | BLM PLO table; 47 FR 27292 |
| EO 4810 | B06 | EO 6679 | 1934-04-16 | jobs/app-executive-orders/output/texts/executive-order-6679-revocation-executive-order-no-4810-february-14-1928-withdrawing.txt |
| EO 4812 | B06 | PLO 367 | 1947-05-15 | BLM PLO table; 12 FR 3303 |
| EO 4827 | B06 | EO 5823 | 1932-03-21 | jobs/ofr-compilations/output/texts/EO_5823.txt |
| EO 4846 | B06 | PLO 506 | 1948-07-29 | BLM PLO table; 13 FR 4572 |
| EO 4848 | B06 | PLO 5650 | 1978-10-18 | BLM PLO table; 43 FR 49794 |
| EO 4885 | B06 | PLO 937 | 1954-02-08 | BLM PLO table; 19 FR 820 |
| EO 4900 | B06 | EO 5819 | 1932-03-12 | jobs/ofr-compilations/output/texts/EO_5819.txt |
| EO 4901 | B07_4901 | EO 8529 | 1940-10-26 | jobs/fr-originals/output/texts/EO_8529.txt (EO 8529 signed 1940-08-27, effective on its sixtieth day) |
| EO 4941 | B06 | PLO 6056 | 1981-10-20 | BLM PLO table; 46 FR 53168 |
| EO 4942 | B06 | EO 5735 | 1931-10-20 | jobs/ofr-compilations/output/texts/EO_5735.txt |
| EO 4957 | B06 | EO 5688 | 1931-08-18 | jobs/ofr-compilations/output/texts/EO_5688.txt |
| EO 4958 | B06 | EO 5877 | 1932-07-06 | jobs/ofr-compilations/output/texts/EO_5877.txt |
| EO 4960 | B06 | EO 5995 | 1933-01-13 | jobs/ofr-compilations/output/texts/EO_5995.txt |
| EO 4964 | B06 | EO 5587 | 1931-03-30 | jobs/ofr-compilations/output/texts/EO_5587.txt |
| EO 5005 | B06 | PLO 472 | 1948-04-27 | BLM PLO table; 13 FR 2429 |
| EO 5029 | B06 | EO 5421 | 1930-08-05 | jobs/app-executive-orders/output/texts/executive-order-5421-revocation-withdrawal-public-lands-for-resurvey.txt |
| EO 5030 | B06 | EO 5895 | 1932-07-26 | jobs/ofr-compilations/output/texts/EO_5895.txt |
| EO 5031 | B06 | EO 5509 | 1930-12-10 | jobs/app-executive-orders/output/texts/executive-order-5509-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5033 | B06 | PLO 5650 | 1978-10-18 | BLM PLO table; 43 FR 49794 |
| EO 5085 | B06 | EO 5933 | 1932-10-10 | jobs/ofr-compilations/output/texts/EO_5933.txt |
| EO 5091 | B06 | EO 5785 | 1932-01-29 | jobs/ofr-compilations/output/texts/EO_5785.txt |
| EO 5115 | B06 | EO 5699 | 1931-08-31 | jobs/ofr-compilations/output/texts/EO_5699.txt |
| EO 5116 | B06 | EO 5820 | 1932-03-16 | jobs/ofr-compilations/output/texts/EO_5820.txt |
| EO 5120 | B06 | PLO 2612 | 1962-02-14 | BLM PLO table; 27 FR 1620 |
| EO 5121 | B06 | EO 6171 | 1933-06-15 | jobs/app-executive-orders/output/texts/executive-order-6171-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5160 | B06 | PLO 583 | 1949-04-11 | BLM PLO table; 14 FR 1848 |
| EO 5166 | B06 | EO 6138 | 1933-05-22 | jobs/app-executive-orders/output/texts/executive-order-6138-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5176 | B06 | PLO 951 | 1954-04-02 | BLM PLO table; 19 FR 2051 |
| EO 5190 | B06 | PLO 6463 | 1983-09-14 | BLM PLO table; 48 FR 43175 |
| EO 5201 | B06 | PLO 464 | 1948-04-14 | BLM PLO table; 13 FR 2168 |
| EO 5203 | B06 | PLO 6461 | 1983-09-14 | BLM PLO table; 48 FR 43175 |
| EO 5218 | B06 | PLO 91 | 1943-02-18 | BLM PLO table; 8 FR 2614 |
| EO 5234 | B06 | EO 5685 | 1931-08-12 | jobs/ofr-compilations/output/texts/EO_5685.txt |
| EO 5258 | B08_5258 | PLO 775 | 1951-12-19 | BLM PLO table; 16 FR 13095 |
| EO 5261 | B06 | EO 6151 | 1933-06-01 | jobs/app-executive-orders/output/texts/executive-order-6151-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5277 | B06 | PLO 5507 | 1975-06-23 | BLM PLO table; 40 FR 27659 |
| EO 5300 | B06 | EO 5979 | 1932-12-19 | jobs/ofr-compilations/output/texts/EO_5979.txt |
| EO 5304 | B06 | EO 6008 | 1933-01-30 | jobs/ofr-compilations/output/texts/EO_6008.txt |
| EO 5309 | B06 | EO 5845 | 1932-04-28 | jobs/ofr-compilations/output/texts/EO_5845.txt |
| EO 5315 | B07_5315 | EO 6490 | 1933-12-12 | jobs/app-executive-orders/output/texts/executive-order-6490-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5339 | B06 | PLO 5976 | 1981-06-30 | BLM PLO table; 46 FR 35504 (correction 46 FR 38079) |
| EO 5342 | B06 | EO 6177 | 1933-06-16 | jobs/app-executive-orders/output/texts/executive-order-6177-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5352 | B06 | PLO 3602 | 1965-04-05 | BLM PLO table; 30 FR 4679 |
| EO 5361 | B06 | PLO 3944 | 1966-03-07 | BLM PLO table; 31 FR 4282 |
| EO 5364 | B06 | PLO 2448 | 1961-07-26 | BLM PLO table; 26 FR 6852 |
| EO 5370 | B06 | PLO 997 | 1954-08-24 | BLM PLO table; 19 FR 5519 |
| EO 5384 | B05_5384 | PLO 3944 | 1966-03-07 | BLM PLO table; 31 FR 4282 |
| EO 5384 | B05_5384 | PLO 4188 | 1967-04-06 | BLM PLO table; 32 FR 5837 |
| EO 5395 | B06 | EO 6163 | 1933-06-08 | jobs/app-executive-orders/output/texts/executive-order-6163-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5397 | B06 | PLO 2166 | 1960-07-21 | BLM PLO table; 25 FR 7104 |
| EO 5424 | B06 | PLO 505 | 1948-07-27 | BLM PLO table; 13 FR 4481 |
| EO 5438 | B06 | PLO 6037 | 1981-10-01 | BLM PLO table; 46 FR 49868 |
| EO 5451 | B06 | PLO 5947 | 1981-05-28 | BLM PLO table; 46 FR 29938 |
| EO 5452 | B06 | EO 5939 | 1932-10-25 | jobs/ofr-compilations/output/texts/EO_5939.txt |
| EO 5481 | B06 | PLO 5507 | 1975-06-23 | BLM PLO table; 40 FR 27659 |
| EO 5482 | B06 | PLO 744 | 1951-08-16 | BLM PLO table; 16 FR 8366 |
| EO 5483 | B07_5483 | EO 6280 | 1933-09-13 | jobs/app-executive-orders/output/texts/executive-order-6280-revocation-withdrawal-public-lands-pending-resurvey-new-mexico.txt |
| EO 5484 | B06 | EO 5932 | 1932-10-10 | jobs/ofr-compilations/output/texts/EO_5932.txt |
| EO 5500 | B06 | PLO 1497 | 1957-09-09 | BLM PLO table; 22 FR 7363 |
| EO 5542 | B06 | EO 5978 | 1932-12-19 | jobs/ofr-compilations/output/texts/EO_5978.txt |
| EO 5547 | B06 | EO 6149 | 1933-05-31 | jobs/app-executive-orders/output/texts/executive-order-6149-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5548 | B06 | EO 6183 | 1933-06-26 | jobs/app-executive-orders/output/texts/executive-order-6183-revocation-withdrawal-public-lands-pending-resurvey.live.txt |
| EO 5550 | B06 | PLO 5356 | 1973-07-23 | BLM PLO table; 38 FR 20081 |
| EO 5551 | B06 | EO 6150 | 1933-05-31 | jobs/app-executive-orders/output/texts/executive-order-6150-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5555 | B06 | EO 6193 | 1933-07-03 | jobs/app-executive-orders/output/texts/executive-order-6193-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5558 | B06 | EO 6155 | 1933-06-05 | jobs/app-executive-orders/output/texts/executive-order-6155-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5571 | B06 | EO 6137 | 1933-05-22 | jobs/app-executive-orders/output/texts/executive-order-6137-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5581 | B06 | PLO 6336 | 1982-09-01 | BLM PLO table; 47 FR 39826 |
| EO 5585 | B06 | PLO 536 | 1948-12-10 | BLM PLO table; 13 FR 7866 |
| EO 5600 | B06 | PLO 5219 | 1972-07-01 | BLM PLO table; 37 FR 13096 |
| EO 5652 | B07_5652 | EO 6613 | 1934-02-24 | jobs/app-executive-orders/output/texts/executive-order-6613-revocation-executive-order-june-18-1931-withdrawing-public-lands.txt |
| EO 5656 | B06 | EO 6195 | 1933-07-03 | jobs/app-executive-orders/output/texts/executive-order-6195-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5667 | B06 | EO 6194 | 1933-07-03 | jobs/app-executive-orders/output/texts/executive-order-6194-revocation-withdrawal-public-lands-pending-resurvey.txt |
| EO 5683 | B06 | PLO 6193 | 1982-03-02 | BLM PLO table; 47 FR 10214 |
| EO 5694 | B06 | PLO 6463 | 1983-09-14 | BLM PLO table; 48 FR 43175 |
| EO 5732 | B06 | PLO 7840 | 2015-08-26 | BLM PLO table; 80 FR 54801 |
| EO 5754 | B06 | PLO 2869 | 1963-01-18 | BLM PLO table; 28 FR 641 |
| EO 5794 | B06 | PLO 2024 | 1959-12-08 | BLM PLO table; 24 FR 10108 |
| EO 5803 | B06 | PLO 625 | 1949-12-16 | BLM PLO table; 14 FR 7647 |
| EO 5813 | B06 | PLO 2010 | 1959-10-15 | BLM PLO table; 24 FR 8498 |
| EO 5829 | B07_5829 | EO 6572 | 1934-01-24 | jobs/app-executive-orders/output/texts/executive-order-6572-revocation-executive-order-march-30-1932-withdrawing-public-lands-new.txt |
| EO 5838 | B06 | PLO 6463 | 1983-09-14 | BLM PLO table; 48 FR 43175 |
| EO 5846 | B06 | PLO 6444 | 1983-07-18 | BLM PLO table; 48 FR 33717 |
| EO 5900 | B06 | PLO 2661 | 1962-04-23 | BLM PLO table; 27 FR 4096 |
| EO 6002 | B06 | PLO 5658 | 1979-03-05 | BLM PLO table; 44 FR 14559 |
| EO 6012 | B06 | PLO 1728 | 1958-09-05 | BLM PLO table; 23 FR 7041 |
| EO 6040 | B06 | PLO 5871 | 1981-05-15 | BLM PLO table; 46 FR 28413 |
| EO 6116 | B06 | PLO 6013 | 1981-09-23 | BLM PLO table; 46 FR 48671 |
| EO 6118 | B06 | PLO 282 | 1945-05-31 | BLM PLO table; 10 FR 6848 |
| EO 6132 | B06 | PLO 2323 | 1961-04-05 | BLM PLO table; 26 FR 3151 |
| EO 6205 | B06 | PLO 6286 | 1982-06-16 | BLM PLO table; 47 FR 27291 |
| EO 6331 | B06 | PLO 1226 | 1955-09-23 | BLM PLO table; 20 FR 7256 |
| EO 6541 | B06 | PLO 2536 | 1961-11-06 | BLM PLO table; 26 FR 10638 |
| EO 6546 | B06 | PLO 6989 | 1993-07-06 | BLM PLO table; 58 FR 38083 (correction 58 FR 48545) |
| EO 6583 | B06 | PLO 6459 | 1983-08-16 | BLM PLO table; 48 FR 40724 |
| EO 6616 | B06 | PLO 2822 | 1962-11-29 | BLM PLO table; 27 FR 12058 |
| EO 6681 | B06 | PLO 2531 | 1961-10-31 | BLM PLO table; 26 FR 10480 |
| EO 6696 | B06 | PLO 6320 | 1982-08-30 | BLM PLO table; 47 FR 39492 |
| EO 6714 | B06 | PLO 2012 | 1959-10-19 | BLM PLO table; 24 FR 8650 |
| EO 6721 | B06 | PLO 6137 | 1982-02-05 | BLM PLO table; 47 FR 6852 |
| EO 6762 | B06 | PLO 6333 | 1982-09-10 | BLM PLO table; 47 FR 39824 (correction 47 FR 46505) |
| EO 6798 | B06 | PLO 5939 | 1981-05-18 | BLM PLO table; 46 FR 28854 |
| EO 6819 | B06 | PLO 6043 | 1981-10-01 | BLM PLO table; 46 FR 50541 |
| EO 6833 | B06 | PLO 364 | 1947-04-09 | BLM PLO table; 12 FR 2478 |
| EO 6883 | B06 | PLO 2005 | 1959-10-06 | BLM PLO table; 24 FR 8260 |
| EO 6890 | B06 | PLO 1791 | 1959-02-17 | BLM PLO table; 24 FR 1345 |
| EO 6946 | B06 | PLO 1615 | 1958-04-15 | BLM PLO table; 23 FR 2602 |
| EO 6973 | B06 | PLO 3390 | 1964-05-11 | BLM PLO table; 29 FR 6384 |
| EO 7112 | B06 | PLO 5854 | 1981-01-19 | BLM PLO table; 46 FR 8520 |
| EO 7219 | B06 | PLO 2080 | 1960-04-15 | BLM PLO table; 25 FR 3475 |
| EO 7309 | B06 | PLO 798 | 1952-01-25 | BLM PLO table; 17 FR 926 |
| EO 7357 | B07_7357 | EO 7382 | 1936-06-04 | jobs/app-executive-orders/output/texts/executive-order-7382-revocation-executive-order-no-7357-may-4-1936-and-partial-revocation.txt |
| EO 7471 | B06 | PLO 6109 | 1982-01-28 | BLM PLO table; 47 FR 5419 |
