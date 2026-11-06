# PD-CUSTOMS-CONSULAR: customs, tariff and consular/foreign service orders, 1873-1936

Family doctrine for the 263 members of X1 types `tariff_customs` (173) and `consular_foreign_service` (90). Machine
form: `research/pothier/doctrines/PD-CUSTOMS-CONSULAR.json`. Leads are proposals for the owner, not statuses. The
doctrine applies the coordinator rulings P1-P8 (`research/pothier/COORDINATOR_RULINGS.md`) and the coordinator's
adjudications for this family.

## Conclusions

The doctrine decides 143 of the 263 members and leaves 120 open. The engine flags 2 contradictions with held
later-event edges (EO 610 and EO 7062); both are explained in section (c), and neither changes its lead.

- **32 `yes` leads (branch B01).** The current customs regulation, 19 CFR 101.3(b)(1), lists every port of entry and
  cites beside a port's name the presidential or Treasury orders "which affected these ports, or which created (or
  subsequently affected) additional ports". Thirty-two members are cited there by number as the order that created a
  port that exists today or fixed its limits. The regulation therefore relies on their operative effect, which is a
  current-law predicate. The held text is the April 1, 2025 CFR edition; the eCFR amendment history, read on the web
  but not held, shows no change to the section after 2023-11-16.
- **14 `no` leads resting on a later instrument whose words reach the member (ACT, branches B02-B12).**
  - EO 5011 is revoked by EO 5577 by number.
  - EO 2878, 5078, 5453, 4265, 4899 and 5284 each did one thing, create a port, and that port is abolished by name in
    EO 4572, 6282, 6635, 7236 and 7463 (ruling P7).
  - EO 4337 is revoked by EO 4709, which identifies it by date and subject.
  - The four unhealthful-post orders of 1925-1930 are canceled by EO 5644, by date, from July 1, 1931.
  - EO 4210 is superseded by EO 5435 by number.
  - The retention of an officer under EO 6066 ends with his retirement under EO 7061, which recites EO 6066.
- **97 `no` leads resting on the order's own terms (TERM, branches B13-B21).**
  - 4 orders ended when the maximum period they state ran out.
  - 4 one-person retirements took effect on a date the order states (ruling P4).
  - 38 orders only abolish ports of entry, and EO 6737 only cancels part of another presidential instrument. These
    are spent on issue under ruling P1, each dated by its stated effective date.
  - 13 orders only amend another executive order, and 37 only amend the Consular Regulations, the Instructions to
    Diplomatic Officers or the Tariff of Consular Fees. These merge into the parent on issue under ruling P2.
- **120 `open`.**

  | Open group | Members |
  |---|---|
  | Port orders the current list does not cite | 36 |
  | Internal revenue district orders | 28 |
  | Customs district orders | 13 |
  | Tariff Board orders | 9 |
  | Complete fee tariffs and standing fee directives | 7 |
  | One- or two-person orders without a stated date | 3 |
  | Standing Foreign Service rules | 11 |
  | Members of other families | 6 |
  | Held text unusable | 5 |
  | Indefinite suspensions | 2 |

Terms used here. A **port of entry** is a place where customs officers may accept entries of imported goods and
collect duties. A **customs collection district** was a larger administrative area headed by a collector of customs,
containing one or more ports. A **Treasury Decision (T.D.)** is a numbered Treasury or Customs ruling published in the
Federal Register and the Customs Bulletin. The **Tariff of Consular Fees** is the presidential schedule of fees that
consuls charge for official services. The **Consular Regulations of 1896** and the **Instructions to Diplomatic
Officers** (1897, revised 1927) were presidentially prescribed rulebooks for the consular and diplomatic services.

Two project terms describe how an order's command ends. Neither is a statutory term.
- **Spent on issue:** the order's command was fully performed on its effective date, so nothing in it continues to
  command.
- **Merged into the parent:** an amending order's text became part of the instrument it amended and lives or ends with
  that instrument.

## (a) Mechanisms by which members end or persist

**M1: Citation in the current list of ports (persists).** 19 CFR 101.3(b) states that many ports were created by the
President's message of March 3, 1913 under the Act of August 24, 1912, and that later orders creating or affecting
ports "are cited following the name of the ports". A member cited there is an order on which the regulation relies for
a port that exists today. The lead is that the order is in force at least in the provision the regulation cites.
Some cited members (for example EO 4156, 4572 and 4780) also abolished other ports, and those abolition clauses were
single acts already performed. Later Treasury Decisions cited beside the same port may have redrawn part of the
limits. The predicate is dated by the CFR edition (April 1, 2025), and the eCFR versioner shows no amendment after
2023-11-16.

**M2: A later executive order whose words reach the member (ends, rulings P3 and P7).** The later order must name the
member by number, or identify it by date and subject. Alternatively, it must abolish by name the one port that was
the member's only operative content; that case gets lead kind `ended_by_express_abolition_of_its_subject`. The date
of the end is the later order's stated effective date:
- immediately for EO 5577 and EO 5435;
- a fixed date for EO 5644 (July 1, 1931) and EO 7061 (December 31, 1935);
- the thirtieth day after signing for EO 4572 (February 26, 1927), EO 4709 (September 18, 1927), EO 6282 (October 13,
  1933), EO 6635 (April 6, 1934), EO 7236 (December 27, 1935) and EO 7463 (October 29, 1936).

A port later re-created under the same name rests on the new order, not on the member. For example, EO 4572 abolished
Bar Harbor and created a new, differently bounded port of that name, and 19 CFR 101.3 today cites EO 4572, not EO
2878.

**M3: Spent on issue (ends on the order's own terms, ruling P1).** An order whose only operative content abolishes or
discontinues named ports, or cancels part of another instrument, does one thing on its effective date. The
coordinator applied P1 to port abolitions for this family. The consequence belongs to the port's or the other
instrument's history: the port's absence, or the cancelled text's end. A later re-designation of the same place is a
new act. For example, EO 7495 re-designated Orange, Texas after EO 7067 had abolished it.

Each abolition is dated by the effective date its text states:
- on issue where no later date is stated (6 orders);
- thirty days after the order's date (23 orders);
- a named day for 9 orders, for example January 1, 1916 for EO 2274 and September 1, 1925 for EO 4292.

An order that does more than revoke is not spent. EO 5577 revokes EO 5011 but also includes Oakland and four other
places within San Francisco's port limits, a continuing provision, so it stays open with the port orders. An
indefinite suspension (EO 4299 of EO 4284; EO 5317 of EO 5291) has a standing effect while it lasts, and both
suspensions stay open.

**M4: Merged into the parent on issue (ends on the order's own terms, ruling P2).** Under the owner's strike-and-insert
ruling, an amended clause continues, amended, until the parent ends. An order whose only operative content amends or
adds to another presidential instrument has no command of its own after issue. That instrument may be an executive
order, the Tariff of Consular Fees, the Consular Regulations of 1896 or the Instructions to Diplomatic Officers. Every
such lead discloses: "its text continues as part of the parent (the regulations or order amended) until the parent
ends; the parent's lifecycle carries it". The date is the order date.

An order with a standing command of its own beyond the amended text is excluded. EO 2022 waives fees "until further
notice" and lets the Secretary of State end the waiver, so it stays open.

The parent's later history is held at least in part. EO 5642, effective July 1, 1931, cancels and replaces the
following parts of the Consular Regulations:
- Article I, "The Consular Branch of the Foreign Service";
- Article II, "Retirement of Foreign Service Officers";
- sections 465-473 (leave of absence);
- Article XXV, "Compensation of Consular Officers".

It also cancels the parts of the Instructions covering the same subjects. That reaches the text inserted by at least
EO 5127, EO 5126 and parts of EO 3354, EO 3902 and EO 1926. The list is not exhaustive, and it changes no lead.

**M5: One-person Foreign Service orders (ruling P4, following PD-CS-ONE-PERSON).** Under the one-person doctrine, an
order ends on its own terms when its text states the end date. Without a stated date, a `no` lead needs a quoted fact
bounding the person's life. Retirements whose own text fixes the date they take effect (EO 4477-A, 6564-A, 6994,
7061) end on that date.

Three members stay open. EO 4279-A and EO 4285 are disability retirements with no stated date. EO 7358 is a
two-person reinstatement effective on Senate confirmation, and the confirmation dates are not held.

**M6: Stated maximum period (ends on its own terms).**
- EO 4043 retains an officer "for a period of one year from July 1, 1924".
- EO 5247 and EO 5519 retain officers "not in excess of five years" from a stated day.
- EO 3535 authorizes extending passports issued before June 4, 1920 so that they are valid "not to exceed two years
  from the date of issuance", so no extension could run past June 3, 1922.

The lead records the interval from the order date to the last day the period allows.

**M7: Candidate events disclosed and not applied (ruling P3).** None of these candidates names the members it might
reach, so none is applied:
- T.D. 95-77 (60 FR 50008, effective September 30, 1995) eliminated customs districts and regions only "for the most
  part". It kept them "as geographical descriptions for limited purposes".
- The complete fee tariffs of EO 496 (effective November 1, 1906) and EO 7968 (September 3, 1938) are disclosed
  earlier candidate ends for the earlier tariffs. Each says that no fee is collected for a service it does not cover,
  but neither names them. EO 7968's supersession list names 22 other orders, none of them a member.
- EO 10718 (1957) delegated fee-setting to the Secretary of State and provides that it "shall not operate to amend,
  supersede, or terminate any rates or tariffs of fees" then in force.
- Reorganization Plan No. 1 of 1952 abolished the offices of collector of internal revenue. It has not been read.

A repeal or delegation of the authority under which an order was made is not an end of the order. Ruling P8 decides
no member here. Its nearest candidate, EO 6778, is a delegation under the National Industrial Recovery Act, which
belongs to another family.

## (b) Primary sources

Every `no` lead rests on held sources. The 32 `yes` leads rest on the held S1 and on S2, which was read on the web
and is not held; the engine records that gap on each `yes` lead. The JSON records each held source's path, sha256 and
pin, and each pin was checked against the whitespace-collapsed held text. S0 is the member's own text (ruling P6),
and the engine records its path, sha256 and grade on each lead.

| Id | Source | Held |
|---|---|---|
| S0 | Member's own order text | recorded per lead |
| S1 | 19 CFR 101.3, CFR 2025 ed., Title 19 vol. 1, pp. 634-642 | held: `jobs/source-ladder/output/texts/queue_EO_8238_19_CFR_101.3_...2ada2b03ae.txt` (sha256 ad857e9d...) |
| S2 | eCFR versioner for 19 CFR 101.3 | not held; https://www.ecfr.gov/api/versioner/v1/versions/title-19.json?section=101.3 |
| S3 | EO 5577 (Mar. 13, 1931), OFR 1974 Hoover vol. II p. 802 | held: `jobs/ofr-compilations/output/texts/EO_5577.txt` |
| S4 | EO 4572 (Jan. 27, 1927) | held: `jobs/pinakes-proquest-ingest/output/texts/EO_4572.txt` |
| S5 | EO 6282 (Sept. 13, 1933) | held: `jobs/app-executive-orders/output/texts/executive-order-6282-...txt` |
| S6 | EO 6635 (Mar. 7, 1934) | held: `jobs/app-executive-orders/output/texts/executive-order-6635-...txt` |
| S7 | EO 7236 (Nov. 27, 1935) | held: `jobs/app-executive-orders/output/texts/executive-order-7236-...txt` |
| S8 | EO 7463 (Sept. 29, 1936), 1 FR 1737 (Oct. 1, 1936) | held (APP transcription): `jobs/app-executive-orders/output/texts/executive-order-7463-...txt` |
| S9 | EO 4709 (Aug. 19, 1927) | held: `jobs/pinakes-proquest-ingest/output/texts/EO_4709.txt` |
| S10 | EO 5644 (June 8, 1931), OFR 1974 Hoover vol. II pp. 932-934 | held: `jobs/ofr-compilations/output/texts/EO_5644.txt` |
| S11 | EO 5435 (Sept. 2, 1930) | held: `jobs/app-executive-orders/output/texts/executive-order-5435-...txt` |
| S12 | EO 5642 (June 8, 1931), OFR 1974 Hoover vol. II pp. 902-929 | held: `jobs/ofr-compilations/output/texts/EO_5642.txt` |
| S13 | EO 7061 (June 5, 1935) | held: `jobs/app-executive-orders/output/texts/executive-order-7061-...txt` |
| S14 | Pothier author brief (spent-on-issue rule) | held: `research/pothier/work/AUTHOR_BRIEF.md` |
| S15 | Owner ruling, strike-and-insert, 2026-10-21 | held: `research/readiness/owner_rulings/2026-10-21-strike-and-insert.md` |
| S16 | PD-CS-ONE-PERSON doctrine (the rule P4 applies) | held: `research/pothier/doctrines/PD-CS-ONE-PERSON.md` |
| S17 | EO 7968 (Sept. 3, 1938), 3 FR 2185 | held: `jobs/fr-originals/data/full_run/texts/EO_7968.txt` |
| S18 | EO 10718 (June 27, 1957), 22 FR 4632 | held: `jobs/fr-originals/output/texts/EO_10718.txt` |
| S19 | T.D. 95-77, 60 FR 50008 (Sept. 27, 1995) | not held; https://www.govinfo.gov/content/pkg/FR-1995-09-27/pdf/95-23728.pdf |
| S20 | Act of Aug. 1, 1914, ch. 223, 38 Stat. 609, 623 (19 U.S.C. 2) | not held; https://www.govinfo.gov/content/pkg/STATUTE-38/pdf/STATUTE-38-Pg609.pdf |
| S21 | Act of May 24, 1924, 43 Stat. 140, sec. 18; Act of Feb. 23, 1931, 46 Stat. 1207, sec. 26 | not held; https://www.govinfo.gov/content/pkg/STATUTE-43/pdf/STATUTE-43-Pg140.pdf |
| S22 | Reorganization Plan No. 1 of 1952, 66 Stat. 823 | not held; https://www.govinfo.gov/content/pkg/STATUTE-66/pdf/STATUTE-66-Pg823.pdf |
| S23 | Pothier coordinator rulings P1-P8 | held: `research/pothier/COORDINATOR_RULINGS.md` (sha256 9624df16...) |

S20 and S21 are the statutes the members cite as their authority; they are context and decide no member. The
acquisitions are listed in `research/pothier/work/PD-CUSTOMS-CONSULAR/FETCH_PROPOSED.jsonl`.

## (c) Decision procedure

The machine tries the branches in order, and the first branch that matches decides. Branches B01-B21, O0 and
O3-O8 select members by instrument number from lists built by reading each text. B18-B21 also require an operative
word (abolish/discontinue; cancel; amend) in the held text. O1 and O2 select by subject words.

| Branch | Members | Lead (kind) | Basis and date | Gaps |
|---|---|---|---|---|
| B01 cited in 19 CFR 101.3 | 32 | yes (persists_cited_in_current_cfr_port_list) | CURRENT: S1, S2; no date | CFR edition is April 2025 (S2 not held); a citation does not prove every clause survives; for EO 5770 and EO 6284 the CFR's date differs by a few days from the member date |
| B02 EO 5011 | 1 | no (ended_revoked_by_later_order) | ACT: EO 5577 revokes it by number; 1931-03-13 | none |
| B03 EO 2878 | 1 | no (ended_by_express_abolition_of_its_subject) | ACT, P7: EO 4572 abolishes Bar Harbor; 1927-02-26 | no order re-creating Bar Harbor in 1918-1927 is held |
| B04 EO 5078 | 1 | no (same) | ACT, P7: EO 6282 abolishes Lincoln; 1933-10-13 | none |
| B05 EO 5453 | 1 | no (same) | ACT, P7: EO 6635 abolishes Wichita; 1934-04-06 | none |
| B06 EO 4265, 4899 | 2 | no (same) | ACT, P7: EO 7236 abolishes Little Rock and Charlotte; 1935-12-27 | none |
| B07 EO 5284 | 1 | no (same) | ACT, P7: EO 7463 abolishes Fort Pierce; 1936-10-29 | none |
| B08 EO 4337 | 1 | no (ended_revoked_by_later_order) | ACT: EO 4709 revokes the order of Nov. 10, 1925; 1927-09-18 | OCR text |
| B09 EO 4187, 4744, 4772, 5324 | 4 | no (ended_canceled_by_later_order) | ACT: EO 5644 cancels the orders of those dates; 1931-07-01 | identified by date |
| B10 EO 4210 | 1 | no (ended_superseded_by_later_order) | ACT: EO 5435 supersedes it by number; 1930-09-02 | none |
| B12 EO 6066 | 1 | no (ended_by_later_order_retirement) | ACT: EO 7061 recites it and retires the officer; 1935-12-31 | none |
| B13-B15 EO 4043, 5247, 5519 | 3 | no (ended_own_terms_period) | TERM: stated maximum retention; to 1925-07-01, 1935-02-22, 1936-02-24 | none |
| B16 EO 3535 | 1 | no (ended_own_terms_period) | TERM: two years from issue; to 1922-06-03 | OCR text |
| B17a-d EO 4477-A, 6564-A, 6994, 7061 | 4 | no (term_expired_stated_date) | TERM, P4: retirement on the stated date | none |
| B18a-k pure port abolitions | 38 | no (spent_on_issue) | TERM, P1: stated effective date (on issue 6; +30 days 23; named day 9) | an unheld suspension before effect would leave the abolition unperformed; EO 4400's scan shows signing on March 28, not March 23 |
| B19 EO 6737 | 1 | no (spent_on_issue) | TERM, P1: cancels part of the Instructions; order date | none |
| B20 amends an executive order | 13 | no (merged_into_parent_on_issue) | TERM, P2; order date | parent-lifecycle disclosure; EO 7062 flag (below) |
| B21 amends Consular Regulations, Instructions or fee tariff | 37 | no (merged_into_parent_on_issue) | TERM, P2; order date | parent-lifecycle disclosure; EO 610 flag (below); number-collision edges not used |
| O3 customs district orders | 13 | open | T.D. 95-77 kept districts; EO 4284 suspended by EO 4299 | a rule abolishing districts outright |
| O4 Tariff Board orders | 9 | open | lapse of funding is not an end | 1912 appropriations; 1916 Tariff Commission title |
| O5 complete tariffs, fee directives | 7 | open | P3; EO 496 and EO 7968 disclosed as candidate ends; EO 2022 waiver "until further notice" | an instrument naming them |
| O6p one- or two-person orders without stated date | 3 | open | P4 | effective or confirmation dates |
| O6 standing Foreign Service rules | 11 | open | no instrument names them | Foreign Service Acts of 1946 and 1980 |
| O7a subject of PD-ADMIN | 4 | open | other family | no doctrine decides them unless reassigned |
| O7b subject of PD-WAR-EMERGENCY | 2 | open | other family | no doctrine decides them unless reassigned |
| O8 unusable text | 5 | open | illegible, wrong document, or a departmental description | the order's own text |
| O0 indefinite suspensions | 2 | open | standing effect; not P1 | the suspended order's end |
| O1 other port orders | 36 | open | not cited in 101.3; absence is not an end | the T.D. or order that last fixed or abolished each port |
| O2 internal revenue districts | 28 | open | no held class-wide end | Reorganization Plan No. 1 of 1952; later Treasury orders |
| Z catch-all | 0 | open | | |

Final counts from `python3 -I jobs/pothier/pothier.py try ...`: 263 members; decides 143 (32 `yes`, 111 `no`); 120
`open`; contradicted 2. None of the 32 `yes` members has a held ending edge.

The two contradiction flags are both of kind `acted_on_after_lead_end`. Neither changes its lead.
- **EO 7062 (B20)** has edges SH-3647e071d203, SH-117996891a66 and SH-99fb1b72ba35. They record that EO 10000 (1948,
  under section 853 of the Foreign Service Act of 1946) and EO 10904 (1961) add places to the unhealthful-post list
  "established by Executive Order No. 5644 ... and by Executive Order No. 7062". EO 7062 only added places to EO
  5644's list. Under ruling P2 these later acts are events of the parent list. That list (EO 5644) stays open in O6,
  and the edges are evidence that the list kept operating.
- **EO 610 (B21)** has edge SH-bdbb6b2087da. It records that EO 2022 (1914) "amends ... Executive Order 610", that is,
  it rewrites paragraphs 159-160 of the Consular Regulations and the Instructions, which EO 610 had amended. Under P2
  that is a later event of the parent regulations.

Several held edges on decided members are number collisions with different orders. None is used, and no `no` lead
rests on a `partial_` edge.

| Member | Edge | What the edge actually concerns |
|---|---|---|
| EO 1161 | PLO 5757 | revokes a Nevada land order of February 17, 1903 |
| EO 1926 | PLO 1178 | a partial revocation of a land order |
| EO 2462 | EO 9804 | a partial revocation of an order of September 29, 1916 on the Employees' Compensation Act for Alaskan employees |
| EO 422 | EO 9951 | a Hawaii order of July 23, 1930 |

## (d) Members the procedure cannot decide (120)

- **Port orders not cited in the current list (O1, 36).** Many of these ports still exist (Sitka, Tulsa, Oklahoma
  City, Winston-Salem, Morehead City), but 19 CFR 101.3 cites a later Treasury Decision for their limits. Others were
  abolished or merged by orders outside this family. Deciding them needs the T.D. or order that last fixed or ended
  each port. Two members in O1 have a specific complication:
  - EO 5291 was suspended by EO 5317 before it took effect, and EO 6283 later abolished the same ports without naming
    it.
  - EO 5577 revokes EO 5011 but also redraws San Francisco's port limits. Those limits now rest on CBP Dec. 06-23,
    which does not name EO 5577.
- **Internal revenue collection districts (O2, 28).** These orders were made under R.S. 3141-3142, and several
  designate a named collector. Reorganization Plan No. 1 of 1952 and the later Treasury district orders have not been
  read.
- **Customs collection districts (O3, 13).** T.D. 95-77 kept the districts as geographical descriptions. EO 4284,
  which abolished District No. 33, was suspended indefinitely by EO 4299, and no later act on it is held. EO 4709
  revokes EO 4337, but it also places Coos County in District No. 2, a standing assignment.
- **Tariff Board (O4, 9).** The Board lapsed for want of appropriations, which is not an end of the orders.
- **Complete fee tariffs and fee directives (O5, 7).** EO 100, EO 496, EO 132, EO 2022, EO 2730, EO 3685-A and EO
  4472. No instrument names them, and the later complete tariffs are disclosed candidate ends only. EO 2022's fee
  waiver runs "until further notice" under a power given to the Secretary of State to end it. EO 2730 runs "during the
  continuance of the war and until further orders".
- **One- or two-person orders without a stated date (O6p, 3).** EO 4279-A and EO 4285 (disability retirements with no
  stated effective date) and EO 7358 (two officers reinstated effective on Senate confirmation).
- **Standing Foreign Service regulations (O6, 11).** EO 469, 368, 829, 240, 2357A, 4696, 5400, 5644, 2139, 2341 and
  5435. EO 5644's list is shown still operating in 1948 and 1961 by EO 10000 and EO 10904.
- **Subjects of other families (O7a, O7b, 6).** No other doctrine decides these unless the coordinator reassigns
  them, because the families select members by X1 type.
  - PD-ADMIN subjects: EO 6778 (Federal Alcohol Control Administration acting officers, a delegation under the
    National Industrial Recovery Act); EO 5966 (border patrols to the Coast Guard, subject to disapproval under section
    407 of the act of June 30, 1932); EO 2620 (Virgin Islands customs); EO 4353 (Dominican customs receivership).
  - PD-WAR-EMERGENCY subjects: EO 1960 and EO 2017 (1914 arms-export and neutrality enforcement).
- **Unusable text (O8, 5).** The scans of EO 10, 12 and 14 are illegible. The held text of EO 99 is a covering letter
  about the fee tariff, and the held text of EO 538 is the State Department's description of the change rather than
  the order.
- **Indefinite suspensions (O0, 2).** EO 4299 and EO 5317.

## Data issues

Three held later-event edges on undecided or excluded members are false matches. None is used here, and each should
be corrected at its source.
- **EO 10.** The supersession edge from EO 10082 quotes "Executive Order No. 10,0041", which refers to EO 10004.
- **EO 12.** The revocation edge from EO 12900 quotes "Executive Order No. 12729 is revoked".
- **EO 2462.** The edge from EO 9804 concerns a different order dated September 29, 1916. The member is the September
  28, 1916 amendment of Consular Regulations paragraph 692, so the number may be duplicated in the census.

The WPA summary of EO 7463 gives "1 Fed. Reg. 1502"; the order is printed at 1 FR 1737.
