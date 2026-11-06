# PD-ADMIN: administrative orders (organization, regulations, pay, fund allotments, territories, property transfers, own-terms expiry, tax return inspection, closings)

Doctrine version 3, 2026-11-06. Machine form: `research/pothier/doctrines/PD-ADMIN.json`. Members: the 801 undecided
orders whose X1 type is one of the nine administrative types (`research/pothier/work/PD-ADMIN/MEMBERS.csv`). The
doctrine applies the coordinator's common rulings P1 to P8 (`research/pothier/COORDINATOR_RULINGS.md`). Every lead
is a proposal for the owner, not a status, and the certified count stays 0.

## Conclusions

The doctrine proposes a status lead of `no` for **205 of the 801 members**: the order was no longer in force on the
cutoff, 2026-10-14. The other **596 members stay open**. It proposes no `yes` lead, because no member can be tied by
the machine to a statute, regulation or official record showing it in force on the cutoff.

`try` flags **12 decided leads** as contradicted by a held later-event edge. None of the flags changes a lead: eight
are amendments that act on the parent order of an amend-only member (P2), and four come from edges matched by number
to unrelated or separate later orders. Each flag is explained in the section "Contradiction flags" below.

| Group | Members | Basis | How the end date is fixed |
|---|---:|---|---|
| Orders that only revoke or cancel another order (B01, B01-EFF) | 16 | own terms (`TERM`), `spent_on_issue` (P1) | the order's date, or the effective date it states |
| Orders that only amend, modify or restate another order (B02, B02-TABLE) | 96 | own terms (`TERM`), `merged_into_parent_on_issue` (P2) | the order's date |
| Orders ended by a later instrument whose words reach them (B03) | 31 | later instrument (`ACT`) | the acting instrument's date, the effective date it states, or an interval |
| Spanish Treaty Claims Commission extensions (B05) | 12 | own terms (`TERM`) | the end of the stated period |
| Deferrals and continuations to a stated date (B06) | 9 | own terms (`TERM`) | the stated date, or an interval ending on it where the order allowed an earlier end |
| Alaska reserves for Natives and the Bureau of Education (B07) | 4 | statute (`ACT`), `ended_by_express_class_instrument` (P3) | 1971-12-18, the date of the Alaska Native Claims Settlement Act |
| Holidays, short days, excusals and encampment leave (B08) | 16 | own terms (`TERM`) | the last named day; for encampment leave, an interval from the last named leave day to December 31 of that year |
| Rates or percentages for a stated fiscal year or period, and one fiscal-year allotment (B09) | 20 | own terms (`TERM`) | the last day of the stated period |
| An authorization granted only until a later act, which held orders performed (B10) | 1 | own terms (`TERM`) | the date of the held orders that performed the act |

Within B03, 23 members are named and ended by a later executive order, 4 lose their only subject when a later order
abolishes it by name (P7), 2 fall in a class that a later order revokes in express words, and 2 are revoked by Public
Land Orders as the Bureau of Land Management's official table states them.

The 596 open members are described in section (d). The largest groups are:
- standing organization orders (194);
- standing regulations (97);
- territorial orders (81);
- fund allotments (55);
- standing pay rules (51);
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
- the lapse of appropriations, for fund allotments;
- whole-text replacements of a regulation that do not revoke the earlier one in terms (for example the 1949 Manual for
  Courts-Martial, EO 10020, which replaced the 1928 manual of EO 4773).

## Terms used

- **Status lead**: a proposed answer, for one order, to whether the order as a whole was still in force on 2026-10-14:
  `no`, `yes` or `open`.
- **Own terms (`TERM`)**: the order's own text supplies the end. The end may be a stated period or date, a named day, a
  fiscal year, a condition that a held instrument shows was met, or a single act performed on issue.
- **Later instrument or statute (`ACT`)**: a later executive order, Public Land Order or statute whose words reach the
  member. It either names the member or expressly describes a class that the member's own text places it in (P3).
- **Public Land Order (PLO)**: an order of the Secretary of the Interior (after 1942) that withdraws public land or
  revokes earlier withdrawals, including withdrawals made by executive order.
- **Implied displacement** does not count as an `ACT` end. Examples are an "inconsistent herewith" clause, repeal of the
  authority the order rested on, a whole-text replacement that does not revoke the earlier order in terms, and a
  statute occupying the field.
- **Spent on issue (P1)**: an order whose only command is carried out by issuing it, for example "Executive Order No. X
  is hereby revoked".
- **Merged into the parent (P2)**: an order whose only content amends another order (the parent). On issue its text
  becomes part of the parent and continues until the parent ends. The parent's lifecycle carries it.
- **Abolition of the only subject (P7)**: a later order abolishes by name the one body a member created or continued;
  the member has nothing left to govern.
- **Accrued effect**: a consequence that outlived the command, such as pay received or rights vested. It does not keep
  the order in force.
- **Candidate end**: a later event that might have ended the order but whose words do not reach it. A candidate end is
  recorded in the gaps and does not decide the lead.
- **Held**: the project keeps the source's text file, and the cited phrase (the **pin**) was found in it.
- **Member text (P6)**: a member's own text is cited as source S-MEMBER (`member_text`). The engine records that text's
  path, sha256 and grade on each lead.
- **Edge**: a held record that a later order acts on a member (revokes, amends, cites it), with the acting order and a
  quotation. Edges are found by matching order numbers and dates, so some point to unrelated orders.

## (a) Mechanisms

### M-SPENT: revoke-only orders (B01, P1) and amend-only orders (B02, P2)

A member qualifies only if its entire operative text does one of two things:
- B01: it revokes, rescinds or cancels another order;
- B02: it amends, modifies or restates part of another order or regulation, or substitutes a date in it.

Membership is a fixed list of 112 orders, set after reading each held text, and each listed order must also match a
revoke or amend phrase in that text. The amend phrase tolerates the OCR form "amen~ded" (EO 2686) and covers the two
orders that substitute a date without an amend verb: EO 516 extends the Spanish Treaty Claims Commission "to March 2,
1907, instead of January 1, as provided for in the Executive order of August 9, 1906" (EO 492), and EO 6512 defers the
abolition of field agencies set by EO 6433-A "to January 16, 1934". The government's own later text treats EO 6512 as
an amendment: EO 6561 of January 16, 1934 is titled an amendment "of Executive Order No. 6433-A ... and of Executive
Order No. 6512" and describes EO 6433-A "as amended by Executive Order No. 6512".

The lists exclude orders that pair a revocation or amendment with a second command:
- EO 1007 revokes an order and directs a re-transfer.
- EO 1244 rescinds an order and sets new boundaries.
- EO 1494 revokes an order and awards compensation.
- EO 767, 1937 and 4580 revoke an order and prescribe a new ration.
- EO 6157 and 6158 cancel a Veterans Regulation and substitute another.
- EO 6208 allocates funds and revokes a paragraph.
- EO 2226 and 2368 add land to a reserve, EO 4814 redescribes a transferred tract, and EO 2013 supplements an order by
  creating a board.

They also exclude orders whose only content is one named person's pay or designation (P4). EO 4698 amends the order
designating L. M. Parker custodian of the Railroad Labor Board records so that he is paid $5,000 a year; it is left
open for PD-CS-ONE-PERSON. EO 3283 is excluded because it does not amend: it suspends a provision of another order
"until the conclusion of the work of the United States Anthracite Coal Commission", an outside event (see O03X).

The lists also exclude orders whose held text is not the order itself. EO 319's text is an Interior Department
description, and EO 310, 311 and 313A are unreadable scans.

Four amend-only members restate the whole operative text of their parent: EO 330B and EO 980 (the Army punishment
limits of 1901, "amended so as to prescribe as follows"), EO 3723 ("the following amendments ... are hereby made" to
the Hot Springs hospital rules of 1892) and EO 6885 (the hospital order of August 25, 1892 "is hereby amended to read
as follows"). Replacing a whole table or text is still an amendment of the parent (P2, coordinator adjudication), so
they merge into the parent on issue. They form their own branch, B02-TABLE, because later orders cite the restated text
by the amending order's number or date: EO 1173 and EO 1333 amend "the Executive order dated Nov. 25, 1908" (EO 980),
EO 5429 amends paragraphs "provided ... by Executive Order No. 3723", and the Wikisource editors' notes to EO 2043
(September 5, 1914) say it superseded EO 980, 1173 and 1333. Those later acts are acts on the parent. If the owner
treats a whole-text restatement as a new standing regulation, these four leads become open pending the instrument that
ended the restated regulation.

Dates:
- B01 uses the order's own date, except where the order states its own effective date (P1). EO 6668 and EO 6669, signed
  April 6, 1934, cancel Veterans Regulations No. 1(d) and No. 12(a) "effective March 28, 1934"; their date is
  1934-03-28 (B01-EFF).
- B02 uses the amending order's own date (P2). Where an amending order states a different effective date (EO 552 from
  July 1, 1907; EO 3864 from September 1, 1923; EO 4473 from July 1, 1926; EO 3024B "as of the date thereof"), that
  date governs when the amended text operated inside the parent, and the gap says so.

Every B02 lead carries the P2 disclosure: "its text continues as part of the parent until the parent ends; the
parent's lifecycle carries it". The owner may instead treat an amending order as living as long as the amended text
lives. In that case the B02 leads become `open` until the parent is decided.

B02 includes EO 4459, 5471, 6352 and 7209, which X1 typed as closings. Their own text shows that they only amend the
Panama Canal employment rules or Schedule A of the Civil Service Rules. B02 does not decide the status of the parent
orders.

### M-REVOKED: a later instrument names the member and ends all of it (B03)

A member is decided here only after reading the acting instrument's held text, or, for a Public Land Order, the held
row of BLM's official table. The words must name the member, by number or by date and subject, and must end all of it.
Examples:
- EO 4044 of July 3, 1924 restores to the public domain the lands "reserved by Executive Order No. 1987, dated July 9,
  1914, for use of the Bureau of Education and the natives", describing all three reserves (Gravina, Fish Bay and Long
  Bay). EO 4055 of July 30, 1924 vacated the restoration only for tracts inside the Chugach National Forest, which
  stayed national forest land and were "released from reservation for use of the Bureau of Education". EO 1987 is
  therefore decided by EO 4044 and not by the 1971 Alaska statute.
- EO 1244 redefines the Lincoln land district and rescinds the "Executive order of August 4, 1910, reestablishing the
  boundary lines of said Lincoln land district" (EO 1234).
- EO 4918 revokes "Executive Order No. 4703, of August 10, 1927" (control of Government Island).
- EO 6746: "This order supersedes Executive Orders Numbers 6440, 6554, and 6622".
- PLO 406 of September 11, 1947 ("revoking of EO No. 2259") and PLO 434 of January 6, 1948 ("revoking EO No. 6587 of
  Feb. 6, 1934"), as BLM's table states them. The PLO texts are not held, and the lead says so.

Partial revocations do not qualify, and no `no` lead rests on an edge that confines an act to part of an order:
- EO 7195 and 7223 revoke paragraph 4 of EO 6126 only "in so far as" it conflicts with them.
- EO 6963 amends EO 6098.
- EO 7139 rescinds one direction in EO 6514.
- EO 5207 revokes EO 2508 and 2525 only "as to the tract described".
- EO 10047 restores one pier of the land reserved by EO 2381.

Held ending edges that are not the acting order's words are not used. The supersessions of EO 181, 235 and 2043 and
the revocation of EO 306 by EO 311 appear only in Wikisource editors' headers or notes (and EO 311's held text is an
unreadable scan). The edges on EO 1, 4, 13 and 328C point to later orders on other subjects.

### M-ABOLISHED: abolition by name of the member's only subject (B03-11, B03-13, B03-15; P7)

- EO 9461 abolishes "the Executive Committee on Commercial Policy, established by the letter of November 11, 1933 ...
  and continued by Executive Order No. 6656 ... and Executive Order No. 7260". Both members only continue and define
  that committee.
- EO 6777 abolishes the Committee on National Land Problems "created by Executive Order No. 6693".
- EO 6858, sec. 9, abolishes the Board of Inquiry for the Cotton Textile Industry "created by Executive Order No.
  6840".

Each body is the member's only operative subject, so the lead is `no`, basis `ACT`, kind
`ended_by_express_abolition_of_its_subject`, dated by the abolishing order.

### M-CLASS-EO: a later order revokes an express class (B03-26; P3)

EO 3027 of January 25, 1919 provides: "All Executive Orders heretofore issued for the establishment of Defensive Sea
Areas are hereby revoked." The member test is the member's own text and date: EO 2584 establishes twenty-nine
defensive sea areas and the rules for persons and vessels in them, and EO 2597 establishes the additional area at the
mouth of the York River; both predate EO 3027. The lead is dated 1919-01-25.

### Dating B03 leads

The date is the acting instrument's date, or the effective date it states. Where the acting order fixes a later
effective date for its replacement rule and not for the revocation, the lead is the interval between the two dates:
- EO 5605 revokes EO 5014 with an effective date of July 1, 1931.
- EO 5952 was signed November 23, 1932, and its replacement ration took effect April 1, 1933. The lead for EO 4580 and
  5337 is the interval between those dates.
- EO 5376 was signed June 23, 1930; it revokes EO 1440 and fixes the new salary "beginning July 1, 1930". The lead is
  the interval from 1930-06-23 to 1930-07-01.
- EO 6776 of June 30, 1934 cancelled EO 6096 "as of the date thereof". The lead is the interval from 1933-03-31 to
  1934-06-30.
- EO 1244's date line reads "Sy5/. 2, 1910" in the held OCR, most likely September 2, 1910. The lead for EO 1234 is the
  interval between its neighbours' dates, EO 1243 (1910-08-24) and EO 1246 (1910-09-16).
- EO 6746 supersedes EO 6440 on signing (June 21, 1934). Its adjusted rates took effect from the first of the month after
  each agency's report, so EO 6440 rates may have been paid briefly afterwards; the gap says so.

### M-OWNDATE: the order's own stated period, date, day or condition (B05, B06, B08, B09, B10)

Each branch's regular expression requires the stated phrase to appear in the member's held text.
- B05, Spanish Treaty Claims Commission: the orders extend the Commission's powers "for and during six months [or two
  months] from and after the second day of March [or September], [year], and for no longer time". The Act of March 2,
  1901 (ch. 800, sec. 16, 31 Stat. 877) gave the Commission two years "and for no longer time", let the President
  extend the period by up to six months at a time, and let him dissolve it early only if it finished before the two
  years expired. Each stated end is therefore the latest end. For every member except the last (EO 1167, to May 2,
  1910), the next order in the series continues the Commission from the day the member's period ends, so each period
  ran its full length.
- B06, deferrals: the orders defer an effective date "until" a day, or continue a body until a day.
- B08, holidays, short days and excusals: the orders name the day.
- B09, allowances: the orders fix rates "for the fiscal year ending June 30, [year]" or for a stated period. The Economy
  Act index orders fix the pay-reduction percentage "during the period from ... to ..., inclusive".
- B10: EO 7321 of March 21, 1936 authorizes department heads to issue temporary leave regulations "pending the
  promulgation of uniform regulations as provided for by the said acts". EO 7409 and EO 7410 of July 9, 1936
  promulgated the uniform annual and sick leave regulations under those acts and ratified the temporary regulations
  issued "under authority of Executive Order No. 7321". The authorization's condition was met on July 9, 1936. The
  temporary regulations were revoked only "insofar as they are inconsistent" with the uniform ones; whatever of them
  survived is their own lifecycle, a surviving consequence and not the order.

Some orders let something end them before the stated day. The lead for those is an interval from the order's date to
the stated day. This applies to EO 6244, 6731 and 6927 ("Provided, That ... may be made operative ... between ...")
and to EO 6245 ("unless otherwise directed hereafter").

An amendment that names the member and changes its date before that date passes is followed, because the amendment
merges into the member (P2):
- EO 516 (October 6, 1906) replaced EO 492's limit of January 1, 1907 with March 2, 1907.
- EO 7090 and EO 7121 moved EO 7074's end (the first National Labor Relations Board) to August 1, 1935, then to
  September 1, 1935.

A later order that makes a separate further extension does not change an earlier order's own end. EO 1120 extends the
Commission from September 2, 1909, but EO 1022 still ends on September 2, 1909. EO 7077, 7261, 7390 and 7526 each
delay the remaining transfers under section 4 of EO 6166 again, citing EO 6927 only as an order under which transfers
were made; EO 6927 still ends on June 30, 1935.

Where OCR damages a date that the order's own date and series fix, the doctrine reads the date and discloses the
reading. The same standard applies to four members:
- EO 625 reads "1G08", taken as 1908 given the order's 1907 date.
- EO 292 (January 31, 1905) reads "the second day of' Maarcb., nineteen' in tred. n fv"; the period starts March 2,
  1905, the next March 2 after the order, and ends 1905-09-02.
- EO 749 (February 5, 1908) reads "the second dayr of March, 1 903"; a start in 1903 would precede the order by five
  years, and EO 674's period ended on March 2, 1908, so the period starts March 2, 1908 and ends 1908-09-02.
- EO 973 (November 17, 1908) excuses employees to attend the Sheridan statue unveiling "on \X'ecnesdav, November 2,5,
  10,"; November 25, 1908 was a Wednesday, and the day is 1908-11-25.
Every legible Commission member that states a period "from and after" a day starts it on the first March 2 or
September 2 after its own date, and the WPA 1944
summaries independently give "until Sept. 2, 1905", "until Sept. 2, 1908" and "Nov. 25, 1908" for EO 292, 749 and 973.

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
- EO 1896, 2508 and 2757 reserve land "for the use of the Bureau of Education and the natives of Alaska of indigenous
  race".
- EO 3673 sets the boundaries of "the reservation for the natives of Alaska residing at the village of Klukwan".

Each is therefore a reserve set aside by Executive order for Native use or for administration of Native affairs. The
date is the Act's date, 1971-12-18.

Three qualifications apply:
- EO 2525 restated EO 2508 "to read as follows"; it is amend-only and merged into EO 2508 (B02), so the 1971 end
  reaches its text through EO 2508.
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
- **Whole-text replacements without words of revocation.** The passport rules of 1903 and 1907 (EO 235, 654), the Army
  punishment limits of 1916 (EO 2498) and the 1949 Manual for Courts-Martial (EO 10020) replaced earlier regulations of
  this family, but their texts do not revoke the earlier orders in terms; under P3 they are disclosed candidate ends.

## (b) Primary sources

| Id | Citation | Held or to acquire | Establishes |
|---|---|---|---|
| S-MEMBER | the member's own held text (`member_text`, P6) | recorded per lead by the engine (path, sha256, grade) | The operative clause and any stated period, date or condition |
| S-ANCSA | Alaska Native Claims Settlement Act, Pub. L. 92-203, sec. 19(a), 85 Stat. 688, 710 (Dec. 18, 1971); 43 U.S.C. 1618(a) | to acquire: https://www.govinfo.gov/content/pkg/STATUTE-85/pdf/STATUTE-85-Pg688.pdf (read on Cornell LII; source credit Pub. L. 92-203, sec. 19, 85 Stat. 710) | The express class revocation quoted above |
| S-TRA76-A | Tax Reform Act of 1976, Pub. L. 94-455, sec. 1202(a), 90 Stat. 1520, 1667-1668 (Oct. 4, 1976); 26 U.S.C. 6103(a) | held: `jobs/source-ladder/output/texts/queue_EO_10906_Tax_Reform_Act_of_1976_Pub._L._94-455_sec._1202_90_Stat._1667_which_rewrote_sec._6103_64c0b4c21d.txt` (sha256 `38235434bbf04013146a46e5e35912661539be250b864905434e3039bd4ba956`; from https://www.govinfo.gov/content/pkg/STATUTE-90/pdf/STATUTE-90-Pg1520.pdf); pin "confidential, and except as authorized by this title" (text line 8659) | The candidate end for the tax orders (general rule) |
| S-TRA76-G | same Act, 90 Stat. 1672; 26 U.S.C. 6103(g) | same file; pin "DISCLOSURE TO PRESIDENT AND CERTAIN OTHER PERSONS" (line 8948) | The only presidential provision of the new section |
| S-TRA76-I | same Act, sec. 1202(i), 90 Stat. 1688 | same file; pin "(i) EFFECTIVE DATE.—The amendments made by this section take" (line 9914, continuing "effect January 1, 1977.") | The date of the candidate end |
| S-STCC-ACT | Act of March 2, 1901, ch. 800, sec. 16, 31 Stat. 877 | to acquire: https://www.govinfo.gov/content/pkg/STATUTE-31/pdf/STATUTE-31-Pg877.pdf (chapter, date, page and sec. 16 read there on the web) | Two years "and for no longer time", six-month presidential extensions, early dissolution only within the two years; context for B05 |
| S-EO1120, S-EO7090, S-EO7121 | EO 1120 (Aug. 6, 1909), EO 7090 (June 29, 1935), EO 7121 (July 31, 1935) | held: APP transcriptions in `jobs/app-executive-orders/output/texts/` (paths, sha256 and pins in the JSON) | The Commission series' own-terms formula; EO 7074's end moved to August 1, then September 1, 1935 |
| S-EO516 | EO 516 (Oct. 6, 1906) | held: `jobs/wikisource-texts/output/texts/EO_516.txt`; pin "is hereby extended to March 2, 1907, instead of January 1" | The amended end of EO 492 |
| S-EO6005A, S-EO5952, S-EO8714, S-EO6550, S-EO9461, S-EO6724, S-EO6777, S-EO6858, S-EO6746, S-EO4918, S-EO4044, S-EO4055, S-EO3027, S-EO7409, S-EO7410 | 15 acting orders outside the family: EO 6005-A (Jan. 21, 1933), 5952 (Nov. 23, 1932), 8714 (Mar. 18, 1941), 6550 (Jan. 6, 1934), 9461 (Aug. 7, 1944), 6724 (May 28, 1934), 6777 (June 30, 1934), 6858 (Sept. 26, 1934), 6746 (June 21, 1934), 4918 (June 23, 1928), 4044 (July 3, 1924), 4055 (July 30, 1924), 3027 (Jan. 25, 1919), 7409 and 7410 (July 9, 1936) | held: APP, Wikisource and ProQuest-scan texts and the OFR Hoover compilation (`jobs/ofr-compilations/output/texts/EO_6005A.txt`); each path, sha256 and pin is in the JSON | Each names and ends the member or members listed in B03, or performs the act EO 7321 waited for (B10) |
| S-EO5376, S-EO6612, S-EO6562, S-EO5605, S-EO6913, S-EO6776, S-EO1244, S-EO7005, S-EO7044, S-EO1706, S-EO3583, S-EO4158, S-EO3261, S-EO4021 | 14 acting orders that are themselves members: EO 6612, 6776, 7005, 7044, 1706, 3583, 4158, 3261 and 4021 (decided in B01), and EO 5376, 5605 (O07), 6562 (O08), 6913 (O06) and 1244 (O09), which also prescribe new rules and stay open | held: each order's held text; pins, paths and sha256 in the JSON | Each names and ends the member listed in B03 |
| S-BLM-1-694 | Bureau of Land Management, Table of Public Land Orders 1-694 (official finding aid) | held: `jobs/shepard-citations/output/texts/blm/plo_1-694.txt` (sha256 `d8a6e9b1da9f4c6a22973f7a6d8a5a88f3cee5b00c1460e14f0e6d878e9d4ec0`); rows "Alaska; revoking of EO No. 2259; withdrawing for Alaskan Road" and "Utah; revoking EO No. 6587 of Feb. 6, 1934; withdrawing public" | PLO 406 revoked EO 2259; PLO 434 revoked EO 6587 |
| S-PLO-406, S-PLO-434 | PLO 406 (Sept. 11, 1947, 12 FR 6259); PLO 434 (Jan. 6, 1948, 13 FR 199) | to acquire: https://www.govinfo.gov/link/fr/12/6259?link-type=pdf and https://www.govinfo.gov/link/fr/13/199?link-type=pdf | The revoking orders themselves |

Every held pin was checked against its held file when the JSON was generated.

## (c) Decision procedure

Branches are tried in order, and the first branch whose conditions all hold decides the member. Counts come from
`python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-ADMIN.json --hints`: 801 members, 205 decided
(all `no`), 596 open, 12 flagged as contradicted (explained below).

**B01 and B01-EFF, revoke-only (16 members; `no`, `TERM`, `spent_on_issue`).** The member must be on the verified list,
and its text must contain "revoked", "rescinded" or "cancelled". B01 (14) is dated by the order's own date: EO 446,
1074, 1182, 1706, 3261, 3583, 4020, 4021, 4158, 6575, 6612, 6776, 7005 and 7044. B01-EFF (2) is dated by the stated
effective date, 1934-03-28: EO 6668 and 6669.

**B02-TABLE and B02, amend-only (96 members; `no`, `TERM`, `merged_into_parent_on_issue`, the order's date).** The member
must be on the verified list, and its text must contain an amend, modify or substitute phrase. B02-TABLE (4) holds the
whole-text restatements EO 330B, 980, 3723 and 6885, with the disclosure described in section (a). B02 (92) holds the
rest. Every lead carries the P2 disclosure and the owner's choice described in section (a).

**B03-01 to B03-28, ended by a later instrument whose words reach the member (31 members; `no`, `ACT`).**

| Branch | Member | Acting instrument | Lead date |
|---|---|---|---|
| B03-01 | EO 1440 | EO 5376 | 1930-06-23 to 1930-07-01 |
| B03-02 | EO 3360 | EO 6005-A | 1933-01-21 |
| B03-03 | EO 3870 | EO 6612 | 1934-02-22 |
| B03-04 | EO 3962 | EO 6562 | 1934-01-18 |
| B03-05 | EO 4580, 5337 | EO 5952 | 1932-11-23 to 1933-04-01 |
| B03-06 | EO 5014 | EO 5605 | 1931-07-01 |
| B03-07 | EO 5502 | EO 6913 | 1934-12-04 |
| B03-08 | EO 6096 | EO 6776 | 1933-03-31 to 1934-06-30 |
| B03-09 | EO 6202-B | EO 8714 | 1941-03-18 |
| B03-10 | EO 6548 | EO 6550 | 1934-01-06 |
| B03-11 | EO 6656, 7260 | EO 9461 (P7) | 1944-08-07 |
| B03-12 | EO 6684 | EO 6724 | 1934-05-28 |
| B03-13 | EO 6693 | EO 6777 (P7) | 1934-06-30 |
| B03-14 | EO 6832 | EO 7005 | 1935-04-10 |
| B03-15 | EO 6840 | EO 6858, sec. 9 (P7) | 1934-09-26 |
| B03-16 | EO 7004 | EO 7044 | 1935-05-15 |
| B03-17 | EO 1648 | EO 1706 | 1913-02-20 |
| B03-18 | EO 3251 | EO 3583 | 1921-11-29 |
| B03-19 | EO 4147 | EO 4158 | 1925-02-19 |
| B03-20 | EO 3166 | EO 3261 | 1920-04-23 |
| B03-21 | EO 3752 | EO 4021 | 1924-06-07 |
| B03-22 | EO 1987 | EO 4044 (with EO 4055) | 1924-07-03 |
| B03-23 | EO 1234 | EO 1244 | 1910-08-24 to 1910-09-16 |
| B03-24 | EO 4703 | EO 4918 | 1928-06-23 |
| B03-25 | EO 6440 | EO 6746 | 1934-06-21 |
| B03-26 | EO 2584, 2597 | EO 3027 (express class, P3) | 1919-01-25 |
| B03-27 | EO 2259 | PLO 406 (BLM table) | 1947-09-11 |
| B03-28 | EO 6587 | PLO 434 (BLM table) | 1948-01-06 |

The lead kind is `ended_by_named_later_instrument`, except `ended_by_express_abolition_of_its_subject` for B03-11, 13 and
15 and `ended_by_express_class_instrument` for B03-26.

**B04, tax-return inspection (27 members; `open`).** The member's X1 type must be `tax_return_inspection`, its text
must open returns to inspection, and it must not be the refund-decisions order. I checked each text against
TR-TAX-RETURN-INSPECTION: none limits inspection to a stated period or date. The gaps record:
- the 1977-01-01 candidate end;
- for the 11 grants to a congressional committee under a resolution named in the text (EO 6241, 6712, 6742, 7039,
  7097, 7115, 7158, 7322, 7350, 7411, 7483), the resolutions that would show when each committee's authority ended,
  and the House rules or precedents that would be needed if a House resolution's authority ends with its Congress;
- for EO 3595 (two firms' returns opened to "Honorable Joseph W. Fordney, Chairman of the Ways & Means Committee", or a
  member he designates) and EO 6603A (returns opened to the House Committee on Naval Affairs), which name no
  resolution, the end of the standing committee's inquiry or of the chairman's tenure;
- for the general and State-officer orders, the need for a later order that names them or an expressly described class
  that contains them.

**B05, Spanish Treaty Claims Commission (12 members; `no`, `TERM`, fixed end dates).**

| End date | Orders |
|---|---|
| 1904-03-02 | EO 228 |
| 1904-09-02 | EO 246 |
| 1905-09-02 | EO 292 (starting year read from the order's date) |
| 1906-09-02 | EO 407 |
| 1907-03-02 | EO 492, as amended by EO 516 |
| 1907-09-02 | EO 557 |
| 1908-03-02 | EO 674 |
| 1908-09-02 | EO 749 (starting year read from the order's date) |
| 1909-03-02 | EO 921 |
| 1909-09-02 | EO 1022 |
| 1910-03-02 | EO 1120 |
| 1910-05-02 | EO 1167 |

**B06, deferrals and continuations (9 members; `no`, `TERM`).**
- Fixed dates: EO 6222 (1933-09-10), 6690 (1934-05-21) and 7100 (1935-12-01).
- Intervals ending on the stated date, because a proviso allowed an earlier end: EO 6244 (to 1933-10-10), 6245 (to
  1933-09-30), 6731 (to 1934-10-01) and 6927 (to 1935-06-30).
- EO 625 runs to 1908-06-30. The held text reads "1G08", which is taken as 1908 given the order's 1907 date.
- EO 7074 ends 1935-09-01, as amended by EO 7090 and 7121.
Only the held later-event edges were searched for an order amending a member's date before it passed.

**B07, Alaska Native reserves (4 members; `no`, `ACT`, `ended_by_express_class_instrument`, fixed 1971-12-18).** EO 1896,
2508, 2757 and 3673. The member must be on the list, and its text must reserve land for the natives. The leads note
that ANCSA is not yet held.

**B08, named days (16 members; `no`, `TERM`).**
- Inauguration-day excusals: EO 1728 (1913-03-04) and 2540 (1917-03-05).
- Four-hour days: EO 3205 (1919-12-31), 3370 (1920-12-31), 3589 (1921-12-24), 3665 (1922-04-27), 3765 (1922-12-23),
  3934 (1923-12-24) and 4110 (1924-12-24).
- Encampment leave: the six intervals in section (a).
- The Sheridan statue excusal, EO 973 (1908-11-25), with the reading disclosed.

**B09, stated fiscal year or period (20 members; `no`, `TERM`).**
- Officers' rental and subsistence allowances, each ending June 30 of the stated fiscal year: EO 3865, 3996, 4228,
  4414, 4620, 4847, 5099, 5355, 5583, 6213 and 6769.
- Economy Act pay-reduction percentages: EO 6085, 6188, 6553, 6791 and 6936.
- Rural carriers' equipment allowances: EO 6176, 6332 and 6675.
- EO 2968A, an allotment "during said fiscal year": interval to 1919-06-30.

**B10, authorization until a later act (1 member; `no`, `TERM`, fixed 1936-07-09).** EO 7321, as described in section (a).

**Open branches (596 members).** B04 (27), O01-INDIAN 4, O01-MILRES 1, O01-WAR 2, O01-ORG 3, O01-CIVILWAR 2,
O01-PERSON 1, O01-TEXT 17, O02 16, O03X 2, O03 5, O03T 1, O04 55, O05 37, O06 81, O07 51, O08 97, O09 194, and the
catch-all O99 (0).

### Contradiction flags (12)

The engine flags a `no` lead when a held edge records a later order amending, extending or otherwise acting on the
member after the lead's end date. A flag never changes a lead. The twelve flags and their dispositions:

| Member | Branch | Held edge | Why the lead stands |
|---|---|---|---|
| EO 330B | B02-TABLE | EO 980 (1908) amends EO 330B | EO 980 amends the restated punishment table, which is part of the 1901 parent (P2) |
| EO 980 | B02-TABLE | EO 1173 (1910), EO 1333 (1911) amend "the Executive order dated Nov. 25, 1908" | Same: they amend the parent's restated text (P2); the Wikisource note that EO 2043 superseded EO 980 is disclosed in the gap |
| EO 552 | B02 | EO 574 (1907) amends EO 552 "to read as follows" | EO 574 restates the amendment to the Hot Springs rules, which are the parent (P2) |
| EO 6512 | B02 | EO 6561 (Jan. 16, 1934) amends EO 6433-A "and" EO 6512 | EO 6561 defers again the abolition date in the parent, EO 6433-A (P2) |
| EO 6576 | B02 | EO 6683 (Apr. 1934), EO 6788 (June 1934) amend EO 6474 and EO 6576 | They amend the parent EO 6474 as amended (P2) |
| EO 7117, 7119 | B02 | EO 7164 (Aug. 29, 1935) recites "Regulation No. 1 as amended (Executive Orders Nos. 7046, 7117, and 7119 ...)" | EO 7164 acts on Regulation No. 1 of EO 7046, the parent (P2) |
| EO 7125 | B02 | EO 7164 (Aug. 29, 1935) recites "Regulation No. 2 as amended (Executive Orders Nos. 7060 and 7125 ...)" | EO 7164 acts on Regulation No. 2 of EO 7060, the parent (P2) |
| EO 1440 | B03-01 | EO 10666 (1956), a Hawaii land order | Matched by number; EO 10666 does not act on EO 1440 |
| EO 6840 | B03-15 | EO 6875, EO 6876 (Oct. 16, 1934), NRA code approvals | They recite the board's report after its abolition; they do not act on EO 6840 |
| EO 6927 | B06-6927 | EO 7261, 7390, 7526 (1935-1936) | Separate later delays under sec. 22 of EO 6166; they do not amend EO 6927's date |
| EO 921 | B05-921 | EO 9556 (1945), a Federal Register contents page | Matched by number; it does not act on EO 921 |

## (d) Members the procedure cannot decide (596)

### Misfiled members, with the family named (30)

- **O01-INDIAN (4).** EO 1302, 3878, 4075 and 4571 are Indian treaty provisions or trust-period extensions. They belong
  to PD-INDIAN.
- **O01-MILRES (1).** EO 3885 withdraws lands on Oahu for military purposes. It belongs to PD-MILITARY-RESERVATION.
- **O01-WAR (2).** EO 3292 and 3319 concern the Grain Corporation's capital stock. They belong to PD-WAR-EMERGENCY.
- **O01-ORG (3).** EO 4175, 6126 and 6169 are organization orders typed as fund allotments. They belong with this
  family's organization orders and are open for the same reason as O09.
- **O01-CIVILWAR (2).** EO 1 and 4 are Civil War orders, and no Pothier family covers them. EO 1's held text and member
  date are the War Department's Executive Order No. 1 relating to political prisoners (February 14, 1862), while its
  WPA 1944 summary describes the Louisiana provisional court order of 1862; which order the number denotes must be
  settled before a text is chosen. EO 4 is a Virginia order of 1865. Their held edges point to unrelated later orders.
- **O01-PERSON (1).** EO 4698's only content is one named person's pay; it follows PD-CS-ONE-PERSON (P4).
- **O01-TEXT (17).** The held text is another order's, a description of the order, or an unreadable scan. Examples are
  EO 1183 (whose held text is EO 1182 1/2), 319, 27-1, 112, 113, 13 and 3885C. A legible text of each order is needed.

### Tax-return inspection (28)

- **B04 (27).** No order states its own end; 1977-01-01 is a disclosed candidate end.
- **O03T (1).** EO 5079 opens the Commissioner's refund decisions rather than returns.

### O02, closings and mourning without a fixed day (16)

- The Labor Day orders of 1907-1910 (EO 677, 926, 1122, 1243) name "the first Monday in September" without a year.
- EO 1404 and 1574 say "hereafter", so they are standing rules.
- The mourning orders tie closings to "the day of the funeral" without giving a date.
- EO 190 names "Monday", but the parade it closes for was on a Wednesday.
- EO 1541 sets a preference, and EO 3676 grants pay for a holiday already past.

The Jacquard L3 review rejected these orders on the same grounds.

### O03X and O03, own-terms orders with no fixed end (7)

- EO 457 authorizes the hire of a copyist, "the employment to continue for such length of time as may be necessary, but
  not to exceed three months". The three months run from the hiring, which the text does not date.
- EO 3283 suspends a records transfer "until the conclusion of the work of the United States Anthracite Coal
  Commission", whose date is not held.
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
- **O06, territories (81).** This group comprises Alaska land, timber and fisheries reserves (which are land
  withdrawals), Puerto Rico acting-judge designations, Hawaii orders of 1898-1900, Virgin Islands administration
  orders, reporting channels for Guam and Samoa, and EO 518 (the Cuban provisional government). An acting-judge
  designation ends with the absence it covers, but the date of that end is not held.
- **O07, pay and allowances (51).** Standing pay rules, named-person compensation and emergency-agency wage rules.
  Orders for one named person follow PD-CS-ONE-PERSON (P4). EO 5376 and 5605, which revoke earlier members, also
  prescribe new rules and stay open.
- **O08, regulations (97).** Army ration and punishment rules, passport rules, Hot Springs hospital rules, Veterans
  Regulations, Alien Property Custodian powers and emergency-relief employment rules. No held instrument names them
  and supersedes them in words. The disclosed candidate ends include the passport rules of 1903 and 1907 for EO 181 and
  235, EO 2498 for EO 2043, and the 1949 Manual for Courts-Martial for EO 4773. The Veterans' Benefits Act of 1957
  (Pub. L. 85-56, 71 Stat. 83; title XXII begins at 71 Stat. 157 and title XXIII at 71 Stat. 172; the page of sec.
  2307 is unverified) is the source that would decide the Veterans Regulations.
- **O09, organization (194).** Land-office orders, boards and committees, succession orders and transfers of
  functions. Reorganization Plan No. 3 of 1946, which could bear on the land-office orders, is not held. EO 306's
  revocation by EO 311 rests only on a Wikisource note, and EO 311's held text is unreadable.

## What the owner is asked to choose

1. **P2 for B02 and B02-TABLE.** Either amend-only orders merge into the parent on issue, which gives the 96 `no` leads,
   or they stay open until the parent is decided. For the four whole-text restatements, a third choice is to treat
   each as a new standing regulation, open until the instrument that ended it is held.
2. **ANCSA.** Whether to acquire the Alaska Native Claims Settlement Act volume (85 Stat. 688). The four B07 leads rest
   on it.
3. **Public Land Orders.** Whether to acquire PLO 406 and PLO 434 (12 FR 6259, 13 FR 199). The leads for EO 2259 and
   EO 6587 rest on BLM's table until then.
