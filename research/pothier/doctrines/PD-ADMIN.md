# PD-ADMIN: administrative orders (organization, regulations, pay, fund allotments, territories, property transfers, own-terms expiry, tax return inspection, closings)

Doctrine version 2, 2026-11-05. Machine form: `research/pothier/doctrines/PD-ADMIN.json`. Members: the 801 undecided
orders whose X1 type is one of the nine administrative types (`research/pothier/work/PD-ADMIN/MEMBERS.csv`). The
doctrine applies the coordinator's common rulings P1 to P6 (`research/pothier/COORDINATOR_RULINGS.md`). Every lead
is a proposal for the owner, not a status, and the certified count stays 0.

## Conclusions

The doctrine proposes a status lead of `no` for **179 of the 801 members**: the order was no longer in force on the
cutoff, 2026-10-14. The other **622 members stay open**. It proposes no `yes` lead, because no member can be tied by
the machine to a statute, regulation or official record showing it in force on the cutoff. No decided lead
contradicts a held later-event edge (`try` reports 0 contradictions).

| Group | Members | Basis | How the end date is fixed |
|---|---:|---|---|
| Orders that only revoke or cancel another order (B01) | 16 | own terms (`TERM`), `spent_on_issue` (P1) | the order's date |
| Orders that only amend or modify another order (B02) | 75 | own terms (`TERM`), `merged_into_parent_on_issue` (P2) | the order's date |
| Orders revoked, superseded or abolished by a later order that names them (B03) | 23 | later instrument (`ACT`) | the revoking order's date, or the effective date it states |
| Spanish Treaty Claims Commission extensions (B05) | 13 | own terms (`TERM`) | the end of the stated period |
| Deferrals and continuations to a stated date (B06) | 10 | own terms (`TERM`) | the stated date, or an interval ending on it where the order allowed an earlier end |
| Alaska reserves for Natives and the Bureau of Education (B07) | 6 | statute (`ACT`), `ended_by_express_class_instrument` (P3) | 1971-12-18, the date of the Alaska Native Claims Settlement Act |
| Holidays, short days and encampment leave (B08) | 15 | own terms (`TERM`) | the last named day; for encampment leave, an interval from the last named leave day to December 31 of that year |
| Rates or percentages for a stated fiscal year or period, and two short-period authorizations (B09) | 21 | own terms (`TERM`) | the last day of the stated period |

The 622 open members are described in section (d). The largest groups are:
- standing organization orders (201);
- standing regulations (113);
- territorial orders (83);
- fund allotments (55);
- standing pay rules (54);
- property transfers (37);
- the 28 tax-return inspection orders.

For each group, the branch gaps name the missing source or the missing end in the order's own terms.
`research/pothier/work/PD-ADMIN/FETCH_PROPOSED.jsonl` lists the sources that would decide several members at once.

The tax-return inspection orders are open because no order states its own end and no held instrument names the
orders. The Tax Reform Act of 1976 rewrote 26 U.S.C. 6103 from January 1, 1977. The new section forbids disclosure of
returns except as Title 26 authorizes and leaves no inspection upon order of the President. It does not name these
orders or describe them as a class. Under the owner's unnamed-instruments ruling (D-20261021-unnamed-instruments,
option C; P3), each lead therefore records 1977-01-01 only as a disclosed earlier candidate end.

Several possible class rules do not decide any member, because no held instrument names the members or expressly
describes a class containing them (P3):
- statehood for Alaska and Hawaii;
- Philippine independence (no Philippine member is in this family);
- the Puerto Rico Constitution;
- general pay statutes;
- the lapse of appropriations, for fund allotments.

## Terms used

- **Status lead**: a proposed answer, for one order, to whether the order as a whole was still in force on 2026-10-14:
  `no`, `yes` or `open`.
- **Own terms (`TERM`)**: the order's own text supplies the end. The end may be a stated period or date, a named day, a
  fiscal year, or a single act performed on issue.
- **Later instrument or statute (`ACT`)**: a later executive order or statute whose words reach the member. It either
  names the member or expressly describes a class that the member's own text places it in (P3).
- **Implied displacement** does not count as an `ACT` end. Examples are an "inconsistent herewith" clause, repeal of the
  authority the order rested on, and a statute occupying the field.
- **Spent on issue (P1)**: an order whose only command is carried out by issuing it, for example "Executive Order No. X
  is hereby revoked".
- **Merged into the parent (P2)**: an order whose only content amends another order (the parent). On issue its text
  becomes part of the parent and continues until the parent ends. The parent's lifecycle carries it.
- **Accrued effect**: a consequence that outlived the command, such as pay received or rights vested. It does not keep
  the order in force.
- **Candidate end**: a later event that might have ended the order but whose words do not reach it. A candidate end is
  recorded in the gaps and does not decide the lead.
- **Held**: the project keeps the source's text file, and the cited phrase (the **pin**) was found in it.
- **Member text (P6)**: a member's own text is cited as source S-MEMBER (`member_text`). The engine records that text's
  path, sha256 and grade on each lead.

## (a) Mechanisms

### M-SPENT: revoke-only orders (B01, P1) and amend-only orders (B02, P2)

A member qualifies only if its entire operative text does one of two things:
- B01: it revokes, rescinds or cancels another order;
- B02: it amends, modifies or restates another order or regulation.

Membership is a fixed list of 91 orders. I read each held text, and each listed order must also match a revoke or amend
verb in that text.

The lists exclude orders that pair a revocation with a second command:
- EO 1007 revokes an order and directs a re-transfer.
- EO 1244 revokes an order and sets new boundaries.
- EO 1494 revokes an order and awards compensation.
- EO 767, 1937 and 4580 revoke an order and prescribe a new ration.
- EO 6157 and 6158 cancel a Veterans Regulation and substitute another.
- EO 6208 allocates funds and revokes a paragraph.

The lists also exclude orders whose held text is not the order itself. EO 319's text is an Interior Department
description, and EO 310, 311 and 313A are unreadable scans.

The date is the order's own date, even where the order reaches back in time:
- EO 3024B amends "as of the date thereof", and EO 4698 is also retroactive.
- EO 6668 and 6669 cancel regulations "effective March 28, 1934". Their own date is April 6, 1934, and the command was
  carried out on issue.

Every B02 lead carries the P2 disclosure: "its text continues as part of the parent until the parent ends; the
parent's lifecycle carries it". The owner may instead treat an amending order as living as long as the amended text
lives. In that case the B02 leads become `open` until the parent is decided.

B02 includes EO 4459, 5471, 6352 and 7209, which X1 typed as closings. Their own text shows that they only amend the
Panama Canal employment rules or Schedule A of the Civil Service Rules, and they are decided on that text. B02 does not
decide the status of the parent orders.

### M-REVOKED: a later order names the member and ends all of it (B03)

A member is decided here only after reading the acting order's held text. That text must name the member, by number or
by date and subject. It must also either end all of the member or abolish the body the member created or continued.
Examples:
- EO 9461 abolishes "the Executive Committee on Commercial Policy, established by the letter of November 11, 1933 ...
  and continued by Executive Order No. 6656 ... and Executive Order No. 7260".
- EO 6777 abolishes the committee "created by Executive Order No. 6693".
- EO 6858, sec. 9, abolishes the board "created by Executive Order No. 6840".

Partial revocations do not qualify:
- EO 7195 and 7223 revoke paragraph 4 of EO 6126 only "in so far as" it conflicts with them.
- EO 6963 amends EO 6098.
- EO 7139 rescinds one direction in EO 6514.
- EO 5207 revokes EO 2508 and 2525 only "as to the tract described".

The held edges on EO 1, 4 and 13 point to later orders on other subjects and are not used.

The date is the acting order's date, or the effective date it states:
- EO 5605 revokes EO 5014 with an effective date of July 1, 1931.
- EO 5952 was signed November 23, 1932, and its replacement ration took effect April 1, 1933. The lead for EO 4580 and
  5337 is the interval between those dates.
- EO 6776 of June 30, 1934 cancelled EO 6096 "as of the date thereof". The lead is the interval from 1933-03-31 to
  1934-06-30.

### M-OWNDATE: the order's own stated period, date or day (B05, B06, B08, B09)

Each branch's regular expression requires the stated phrase to appear in the member's held text.
- B05, Spanish Treaty Claims Commission: the orders extend the Commission's powers "for and during six months [or two
  months] from and after the second day of March [or September], [year], and for no longer time".
- B06, deferrals: the orders defer an effective date "until" a day, or continue a body until a day.
- B08, holidays and short days: the orders name the day.
- B09, allowances: the orders fix rates "for the fiscal year ending June 30, [year]" or for a stated period. The Economy
  Act index orders fix the pay-reduction percentage "during the period from ... to ..., inclusive".

Some orders let something end them before the stated day. The lead for those is an interval from the order's date to
the stated day. This applies to EO 6244, 6731 and 6927 ("Provided, That ... may be made operative ... between ...")
and to EO 6245 ("unless otherwise directed hereafter").

An amendment that names the member and changes its date before that date passes is followed:
- EO 516 (October 6, 1906) replaced EO 492's limit of January 1, 1907 with March 2, 1907.
- EO 7090 and EO 7121 moved EO 7074's end (the first National Labor Relations Board) to August 1, 1935, then to
  September 1, 1935. Both are held, and both are recorded as amendment edges on EO 7074.

A later extension issued as a separate order does not change an earlier order's own end. EO 1120 extends the
Commission from September 2, 1909, but EO 1022 still ends on September 2, 1909.

#### Encampment leave orders (EO 2237, 2423, 2669, 2882, 2890, 3112)

These six orders grant leave to veterans "who desire to attend" a named encampment, "that they may have the
opportunity to attend". The leave covers stated days plus "as many more days ... as are necessary for the journey ...
and return". The text therefore ties the leave to that encampment but fixes no last day.

Each lead is an interval from the last named leave day to December 31 of that year. The upper bound is an inference:
a rail journey within the United States took days, not months. The lead's basis says so.

| Order | Interval |
|---|---|
| EO 2237 | 1915-10-03 to 1915-12-31 |
| EO 2423 | 1916-09-03 to 1916-12-31 |
| EO 2669 | 1917-08-27 to 1917-12-31 |
| EO 2882 | 1918-09-05 to 1918-12-31 |
| EO 2890 | 1918-08-24 to 1918-12-31 |
| EO 3112 | 1919-09-14 to 1919-12-31 |

### M-ANCSA: Alaska Native reserves (B07)

Section 19(a) of the Alaska Native Claims Settlement Act of December 18, 1971 (Pub. L. 92-203, 85 Stat. 688, 710;
43 U.S.C. 1618(a)) provides that "the various reserves set aside by legislation or by Executive or Secretarial Order
for Native use or for administration of Native affairs, including those created under the Act of May 31, 1938 ... are
hereby revoked subject to any valid existing rights of non-Natives". The section does not apply to the Annette Island
Reserve. This is an express description of a class.

The member test is each order's own text:
- EO 1896, 1987, 2508, 2525 and 2757 reserve land "for the use of the Bureau of Education and the natives of Alaska of
  indigenous race".
- EO 3673 sets the boundaries of "the reservation for the natives of Alaska residing at the village of Klukwan".

Each is therefore a reserve set aside by Executive order for Native use or for administration of Native affairs. The
date is the Act's date, 1971-12-18.

Two qualifications apply:
- Part of the Norton Bay reserve ended earlier, because EO 5207 of 1929 revoked it "as to the tract described".
- The Act was read only on the web, so the engine adds "source not yet held" to each lead.

### M-TAX76: the 1976 rewrite of section 6103 (candidate end only)

Section 1202 of the Tax Reform Act of 1976 is held. From January 1, 1977 it makes returns confidential and forbids
disclosure "except as authorized by this title". Its only presidential provision, 6103(g), allows disclosure to the
President on written request.

The section names no executive order and describes no class of orders, so it does not end the inspection orders (P3).
Each tax lead records it as a disclosed earlier candidate end.

### Mechanisms checked and not adopted

- **Statehood, independence and the Puerto Rico Constitution.** No instrument found names a member or a described class
  that contains one.
- **General pay statutes** (the Classification Acts, the Pay Readjustment Act of 1942, the Career Compensation Act of
  1949). These are not held, and an inconsistent-laws clause would be implied displacement.
- **Lapse of appropriations.** The period of availability depends on each appropriation item, and none is held.
- **Veterans' Benefits Act of 1957.** It has a section on "outstanding rules, regulations, and orders" (sec. 2307) that
  has not been read.
- **Property transfers.** Under the reviewed type rule TR-PROPERTY-TRANSFER the end is the delivery date, and none is
  held.

## (b) Primary sources

| Id | Citation | Held or to acquire | Establishes |
|---|---|---|---|
| S-MEMBER | the member's own held text (`member_text`, P6) | recorded per lead by the engine (path, sha256, grade) | The operative clause and any stated period, date or condition |
| S-ANCSA | Alaska Native Claims Settlement Act, Pub. L. 92-203, sec. 19(a), 85 Stat. 688, 710 (Dec. 18, 1971); 43 U.S.C. 1618(a) | to acquire: https://www.govinfo.gov/content/pkg/STATUTE-85/pdf/STATUTE-85-Pg688.pdf (read on Cornell LII; source credit Pub. L. 92-203, sec. 19, 85 Stat. 710) | The express class revocation quoted above |
| S-TRA76-A | Tax Reform Act of 1976, Pub. L. 94-455, sec. 1202(a), 90 Stat. 1520, 1667-1668 (Oct. 4, 1976); 26 U.S.C. 6103(a) | held: `jobs/source-ladder/output/texts/queue_EO_10906_Tax_Reform_Act_of_1976_Pub._L._94-455_sec._1202_90_Stat._1667_which_rewrote_sec._6103_64c0b4c21d.txt` (sha256 `38235434bbf04013146a46e5e35912661539be250b864905434e3039bd4ba956`; from https://www.govinfo.gov/content/pkg/STATUTE-90/pdf/STATUTE-90-Pg1520.pdf); pin "confidential, and except as authorized by this title" (text line 8659) | The candidate end for the tax orders (general rule) |
| S-TRA76-G | same Act, 90 Stat. 1672; 26 U.S.C. 6103(g) | same file; pin "DISCLOSURE TO PRESIDENT AND CERTAIN OTHER PERSONS" (line 8948) | The only presidential provision of the new section |
| S-TRA76-I | same Act, sec. 1202(i), 90 Stat. 1688 | same file; pin "(i) EFFECTIVE DATE.—The amendments made by this section take" (line 9914, continuing "effect January 1, 1977.") | The date of the candidate end |
| S-STCC-ACT | Act of March 2, 1901, ch. 804, sec. 16, 31 Stat. 877 | to acquire: https://www.govinfo.gov/content/pkg/STATUTE-31/pdf/STATUTE-31-Pg877.pdf (chapter and page as conventionally cited; not verified) | Authority for the Commission extensions; context only |
| S-EO1120 | EO 1120 (Aug. 6, 1909) | held: `jobs/app-executive-orders/output/texts/executive-order-1120-time-limit-for-completion-the-work-the-spanish-treaty-claims.txt`; pin "is hereby extended for and during six months from and after the second day of September, 1909, and for no longer time" | The series' own-terms formula |
| S-EO516 | EO 516 (Oct. 6, 1906) | held: `jobs/wikisource-texts/output/texts/EO_516.txt`; pin "is hereby extended to March 2, 1907, instead of January 1" | The amended end of EO 492 |
| S-EO7090, S-EO7121 | EO 7090 (June 29, 1935), EO 7121 (July 31, 1935) | held: `jobs/app-executive-orders/output/texts/executive-order-7090-extending-the-national-labor-relations-board.txt`, `...-7121-extending-the-national-labor-relations-board.txt` | EO 7074's end moved to August 1, 1935, then to September 1, 1935 |
| S-EO5376 … S-EO6858 | 14 revoking orders outside the family: EO 5376 (June 23, 1930), 6005-A (Jan. 21, 1933), 6612 (Feb. 22, 1934), 6562 (Jan. 18, 1934), 5952 (Nov. 23, 1932), 5605 (Apr. 21, 1931), 6913 (Dec. 4, 1934), 6776 (June 30, 1934), 8714 (Mar. 18, 1941), 6550 (Jan. 6, 1934), 9461 (Aug. 7, 1944), 6724 (May 28, 1934), 6777 (June 30, 1934), 6858 (Sept. 26, 1934) | held: APP transcriptions in `jobs/app-executive-orders/output/texts/`, and the OFR Hoover compilation text `jobs/ofr-compilations/output/texts/EO_6005A.txt`; each pin, path and sha256 is in the JSON | Each names and ends the member or members listed in B03 |
| S-EO7005, S-EO7044, S-EO1706, S-EO3583, S-EO4158, S-EO3261, S-EO4021 | 7 revoking orders inside the family | held: each member's primary text; pins in the JSON | They end EO 6832, 7004, 1648, 3251, 4147, 3166 and 3752 respectively |

Every pin was checked against its held file when the JSON was generated.

## (c) Decision procedure

Branches are tried in order, and the first branch whose conditions all hold decides the member. Counts come from
`python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-ADMIN.json --hints`: 801 members, 179 decided
(all `no`), 0 contradicted.

**B01, revoke-only (16 members; `no`, `TERM`, `spent_on_issue`, the order's date).** The member must be on the verified
list, and its text must contain "revoked", "rescinded" or "cancelled". The members are EO 446, 1074, 1182, 1706, 3261,
3583, 4020, 4021, 4158, 6575, 6612, 6668, 6669, 6776, 7005 and 7044.

**B02, amend-only (75 members; `no`, `TERM`, `merged_into_parent_on_issue`, the order's date).** The member must be on
the verified list, and its text must contain an amend, modify or substitute verb. Every lead carries the P2 disclosure
and the owner's choice described in section (a).

**B03-01 to B03-21, named and ended by a later order (23 members; `no`, `ACT`, `ended_by_named_later_instrument`).**
Each branch cites its revoking order and that order's date or stated effective date.

**B04, tax-return inspection (27 members; `open`).** The member's X1 type must be `tax_return_inspection`, its text
must open returns to inspection, and it must not be the refund-decisions order. I checked each text against
TR-TAX-RETURN-INSPECTION: none limits inspection to a stated period or date. The committee grants tie inspection to a
committee authorized by a named resolution of a named Congress, but the committee's end is not in the text. The gaps
record:
- the 1977-01-01 candidate end;
- for the 13 committee grants, the committee resolutions that would show when each committee's authority ended, and
  the House rules or precedents that would be needed if a House resolution's authority ends with its Congress;
- for the general and State-officer orders, the need for a later order that names them or an expressly described class
  that contains them.

**B05, Spanish Treaty Claims Commission (13 members; `no`, `TERM`).** Eleven members have a legible stated period, and
their end dates are fixed:

| End date | Orders |
|---|---|
| 1904-03-02 | EO 228 |
| 1904-09-02 | EO 246 |
| 1906-09-02 | EO 407 |
| 1907-03-02 | EO 492 and 516 |
| 1907-09-02 | EO 557 |
| 1908-03-02 | EO 674 |
| 1909-03-02 | EO 921 |
| 1909-09-02 | EO 1022 |
| 1910-03-02 | EO 1120 |
| 1910-05-02 | EO 1167 |

B05-ZZ covers EO 292 and 749. Their period and "no longer time" clause are legible, but the starting year is partly
illegible. The lead is an interval from the order's date to 1910-05-02, the end of the last extension in the series.
The gap notes that this bound assumes the period starts on the March 2 next after the order's date, as in every
legible member.

**B06, deferrals and continuations (10 members; `no`, `TERM`).**
- Fixed dates: EO 6222 (1933-09-10), 6690 (1934-05-21), 6512 (1934-01-16) and 7100 (1935-12-01).
- Intervals ending on the stated date, because a proviso allowed an earlier end: EO 6244 (to 1933-10-10), 6245 (to
  1933-09-30), 6731 (to 1934-10-01) and 6927 (to 1935-06-30).
- EO 625 runs to 1908-06-30. The held text reads "1G08", which is taken as 1908 given the order's 1907 date.
- EO 7074 ends 1935-09-01, as amended by EO 7090 and 7121.

**B07, Alaska Native reserves (6 members; `no`, `ACT`, `ended_by_express_class_instrument`, fixed 1971-12-18).** The
member must be on the list, and its text must reserve land for the natives. The leads note that ANCSA is not yet held.

**B08, named days (15 members; `no`, `TERM`).**
- Inauguration-day excusals: EO 1728 (1913-03-04) and 2540 (1917-03-05).
- Four-hour days: EO 3205 (1919-12-31), 3370 (1920-12-31), 3589 (1921-12-24), 3665 (1922-04-27), 3765 (1922-12-23),
  3934 (1923-12-24) and 4110 (1924-12-24).
- Encampment leave: the six intervals in section (a).

**B09, stated fiscal year or period (21 members; `no`, `TERM`).**
- Officers' rental and subsistence allowances, each ending June 30 of the stated fiscal year: EO 3865, 3996, 4228,
  4414, 4620, 4847, 5099, 5355, 5583, 6213 and 6769.
- Economy Act pay-reduction percentages: EO 6085, 6188, 6553, 6791 and 6936.
- Rural carriers' equipment allowances: EO 6176, 6332 and 6675.
- EO 2968A, an allotment "during said fiscal year": interval to 1919-06-30.
- EO 457, a copyist "not to exceed three months": interval to 1906-09-13.

**Open branches (622 members).** B04 (27), O01-INDIAN 4, O01-MILRES 1, O01-WAR 2, O01-ORG 3, O01-CIVILWAR 2, O01-TEXT
17, O02 17, O03 5, O03T 1, O04 55, O05 37, O06 83, O07 54, O08 113, O09 201, and the catch-all O99 (0).

## (d) Members the procedure cannot decide (622)

### Misfiled members, with the family named (29)

- **O01-INDIAN (4).** EO 1302, 3878, 4075 and 4571 are Indian treaty provisions or trust-period extensions. They belong
  to PD-INDIAN.
- **O01-MILRES (1).** EO 3885 withdraws lands on Oahu for military purposes. It belongs to PD-MILITARY-RESERVATION.
- **O01-WAR (2).** EO 3292 and 3319 concern the Grain Corporation's capital stock. They belong to PD-WAR-EMERGENCY.
- **O01-ORG (3).** EO 4175, 6126 and 6169 are organization orders typed as fund allotments. They belong with this
  family's organization orders and are open for the same reason as O09.
- **O01-CIVILWAR (2).** EO 1 and 4 are Civil War orders, and no Pothier family covers them. Their held edges point to
  unrelated later orders.
- **O01-TEXT (17).** The held text is another order's, a description of the order, or an unreadable scan. Examples are
  EO 1183 (whose held text is EO 1182 1/2), 319, 27-1, 112, 113, 13 and 3885C. A legible text of each order is needed.

### Tax-return inspection (28)

- **B04 (27).** No order states its own end; 1977-01-01 is a disclosed candidate end.
- **O03T (1).** EO 5079 opens the Commissioner's refund decisions rather than returns.

### O02, closings and mourning without a fixed day (17)

- The Labor Day orders of 1907-1910 (EO 677, 926, 1122, 1243) name "the first Monday in September" without a year.
- EO 1404 and 1574 say "hereafter", so they are standing rules.
- The mourning orders tie closings to "the day of the funeral" without giving a date.
- EO 190 names "Monday", but the parade it closes for was on a Wednesday.
- EO 973's day is damaged by OCR.
- EO 1541 sets a preference, and EO 3676 grants pay for a holiday already past.

The Jacquard L3 review rejected these orders on the same grounds.

### O03, own-terms orders with no fixed end (5)

- EO 6221 runs until a date counted from the convening of the second session of the 73d Congress, which the text does
  not give. EO 6624 also deferred the Board's abolition further.
- EO 7084 and 7085 were amended by EO 7089 and 7091 to run "until further order".
- EO 267 and 345 are illegible.

### Other open groups

- **O04, fund allotments (55).** The project does not hold the appropriation items whose terms set when each allotment
  stopped being available. These include the Virgin Islands items of the Naval Appropriation Acts and the
  availability clauses of the 1933-1935 emergency acts.
- **O05, property transfers (37).** No delivery records are held. Some members also carry return-on-notice, personnel
  or conditional terms.
- **O06, territories (83).** This group comprises Alaska land, timber and fisheries reserves (which are land
  withdrawals), Puerto Rico acting-judge designations, Hawaii orders of 1898-1900, Virgin Islands administration
  orders, reporting channels for Guam and Samoa, and EO 518 (the Cuban provisional government). An acting-judge
  designation ends with the absence it covers, but the date of that end is not held.
- **O07, pay and allowances (54).** Standing pay rules, named-person compensation and emergency-agency wage rules.
  Orders for one named person follow PD-CS-ONE-PERSON (P4).
- **O08, regulations (113).** Army ration and punishment rules, passport rules, Hot Springs hospital rules, Veterans
  Regulations, Alien Property Custodian powers and emergency-relief employment rules. No held instrument names them
  and supersedes them.
- **O09, organization (201).** Land-office orders (65), boards and committees, succession orders and transfers of
  functions. Reorganization Plan No. 3 of 1946, which could bear on the land-office orders, is not held.

## What the owner is asked to choose

1. **P2 for B02.** Either amend-only orders merge into the parent on issue, which gives the 75 `no` leads, or they stay
   open until the parent is decided.
2. **ANCSA.** Whether to acquire the Alaska Native Claims Settlement Act volume (85 Stat. 688). The six B07 leads rest on
   it.
