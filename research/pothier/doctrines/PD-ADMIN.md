# PD-ADMIN: administrative orders (organization, regulations, pay, fund allotments, territories, property transfers, own-terms expiry, tax return inspection, closings)

Doctrine version 1, 2026-11-05. Machine form: `research/pothier/doctrines/PD-ADMIN.json`. Members: the 801 undecided
orders whose X1 type is one of the nine administrative types (`research/pothier/work/PD-ADMIN/MEMBERS.csv`).
Every lead below is a proposal for the owner; none is a status, and the certified count stays 0.

## Conclusions

The doctrine proposes a status lead of `no` (the order was no longer in force on the cutoff, 2026-10-14) for **206 of
the 801 members** and leaves **595 open**. It proposes no `yes` lead: no member could be tied by the machine to a
statute, regulation or official record showing it in force on the cutoff. No decided lead contradicts any held
later-event edge (`try` reports 0 contradictions).

The 206 `no` leads rest on five mechanisms, each tied to the order's own text or to a held instrument:

| Group | Members | Basis | How the end date is fixed |
|---|---:|---|---|
| Orders that only revoke or cancel another order (B01) | 16 | own terms (`TERM`) | the order's date |
| Orders that only amend or modify another order (B02) | 75 | own terms (`TERM`) | the order's date |
| Orders revoked, superseded or abolished as a whole by a later order whose held text names them (B03) | 23 | later instrument (`ACT`) | the revoking order's date, or the effective date it states |
| Tax-return inspection orders (B04) | 27 | statute (`ACT`): Tax Reform Act of 1976 | ended within the interval from the order's date to 1977-01-01 |
| Spanish Treaty Claims Commission extensions (B05) | 13 | own terms (`TERM`) | the end of the stated period |
| Deferrals and continuations to a stated date (B06) | 10 | own terms (`TERM`) | the stated date, or the interval up to it where the order allowed an earlier end |
| Alaska reserves for Natives and the Bureau of Education (B07) | 6 | statute (`ACT`): ANCSA sec. 19(a) | ended within the interval from the order's date to 1971-12-18 |
| Holidays, short days and encampment leave on named days (B08) | 15 | own terms (`TERM`) | the last named day; for encampment leave, the interval to the end of that year |
| Rates or percentages fixed for a stated fiscal year or period; two short-period authorizations (B09) | 21 | own terms (`TERM`) | the last day of the stated period |

The 595 open members fall into nine groups (section (d)). The largest are standing organization orders (201),
standing regulations (113), territorial orders (83), fund allotments (55), standing pay rules (54) and property
transfers (37). For each, the obstacle is a specific missing source, named in the branch's gaps and, where a single
source would decide many members, in `research/pothier/work/PD-ADMIN/FETCH_PROPOSED.jsonl`.

Three of the coordinator's starting leads were checked and not adopted as class rules. Alaska and Hawaii statehood,
Philippine independence and the Puerto Rico Constitution do not, by their terms, name or end any member held here
(no Philippine member is in this family; the territorial members are land reserves, acting-judge designations and
administrative arrangements). The general pay statutes were not read in a form showing that their terms displace
presidential pay orders, so they decide nothing. Fund allotments were not decided by the lapse of appropriations,
because the period of availability depends on each appropriation item, which the project does not hold.

## Terms used

- **Status lead**: a proposed answer, for one order, to the question whether the order as a whole was still in force
  on 2026-10-14: `no`, `yes` or `open`.
- **Own terms (`TERM`)**: the order's own text supplies the end: a stated period or date, a named day, a fiscal year,
  or a single act that is complete when the order issues.
- **Later instrument or statute (`ACT`)**: a later executive order or statute that, by its own words, revokes the
  order, abolishes what it created, or forbids what it commands.
- **Spent on issue**: an order whose only command is performed by its issuance (for example, "Executive Order No. X
  is hereby revoked") has nothing further to do once signed. What it did is evidence about the other order. The
  author brief states this as an owner rule for orders that only revoke, restore or amend another order.
- **Accrued effect**: a consequence that outlived the command (pay already received, a transfer completed). It does not
  keep the order in force.
- **Held**: the project keeps the source's text file in the repository, and the cited phrase (the **pin**) was found
  in it.

## (a) Mechanisms

**M-SPENT: revoke-only and amend-only orders are spent on issue (B01, B02).** A member qualifies only if its entire
operative text revokes, rescinds, cancels, amends, modifies or restates another order or regulation. Membership in
these two branches is a fixed list of 91 orders, each read in its held text. The list excludes orders that pair a
revocation with a second command. Examples of excluded orders are EO 1007 (revokes an order and directs a
re-transfer), EO 1244 (revokes and sets new boundaries), EO 1494 (revokes and awards compensation), EO 767, 1937 and
4580 (revoke and prescribe a new ration), EO 6157 and 6158 (cancel one Veterans Regulation and substitute another),
and EO 6208 (allocates funds and revokes a paragraph). It also excludes orders whose held text is not the order: EO
319 is an Interior Department description, and EO 310, 311 and 313A are unreadable scans. The date is the order's own
date, even where the amendment reaches back, as in EO 3024B ("as of the date thereof") or EO 4698. Whether the amended
or revoked order is itself still in force is a separate question and is not decided here.

**M-REVOKED: a later order revokes, supersedes or abolishes the member as a whole (B03).** The doctrine decides a
member here only after reading the acting order's held text and finding that it names the member and ends all of it,
or abolishes the body the member created or continued. The acting orders are listed in section (b). Partial
revocations do not qualify. Examples: EO 7195 and 7223 revoke paragraph 4 of EO 6126 only "in so far as it is in
conflict"; EO 6963 amends EO 6098; EO 7139 rescinds one direction in EO 6514; EO 5207 revokes EO 2508 and 2525 only "as
to the tract described". Some held edges attach to the wrong order: the edges on EO 1, EO 4 and EO 13 point to later
orders about other subjects. Edges of these kinds were not used. The date is the acting order's date, or the
effective date it states: July 1, 1931 for EO 5605, and the interval from November 23, 1932 to April 1, 1933 for EO
5952. For EO 6096 the interval runs from 1933-03-31 to 1934-06-30, because EO 6776 of June 30, 1934 cancelled it "as
of the date thereof".

**M-TAX76: the 1976 rewrite of 26 U.S.C. 6103 (B04).** Every member opens tax returns to inspection by the order's
own force. Some grants are to a committee or official; others are general orders under Treasury rules approved by the
President. The orders rest on the Tariff Act of 1913 or the Revenue Acts, which allowed inspection "only upon the
order of the President" (quoted in EO 1999). Section 1202 of the Tax Reform Act of 1976 replaced section 6103
entirely, effective January 1, 1977. The new section makes returns and return information confidential and forbids
every federal officer and employee to disclose them "except as authorized by this title". The only presidential
provision of the new section is subsection (g), which allows disclosure to the President and persons he names on
written request; nothing in it authorizes inspection by others upon order of the President. From January 1, 1977, an
inspection order therefore could not operate. That is a statutory prohibition of what the orders command, not merely
the repeal of their authority. Most members ended much earlier, with the committee, investigation or Congress they
name. The project does not hold those dates, so the lead states only the interval from the order's date to 1977-01-01.
EO 5079 is excluded and left open (O03T): it opens the Commissioner's refund decisions to inspection, not returns.

**M-OWNDATE: own stated period, date or day (B05, B06, B08, B09).** These members state their own end, and each
branch's regular expression requires that the stated phrase appear in the member's held text.
- B05: the Spanish Treaty Claims Commission orders extend the Commission's powers "for and during six months [or two
  months] from and after the second day of March [or September], [year], and for no longer time".
- B06: the deferral orders defer an effective date "until" a day, or continue a body until a day.
- B08: the holiday and short-day orders name the day.
- B09: the allowance orders fix rates "for the fiscal year ending June 30, [year]" or for a stated period. The Economy
  Act index orders fix the pay-reduction percentage "during the period from ... to ..., inclusive".

Where the order lets something end it earlier, the lead gives the interval from the order's date to the stated day.
Those provisos are found in EO 6244, 6731 and 6927 ("Provided, That ... may be made operative ... between ...") and in
EO 6245 ("unless otherwise directed hereafter").

Some of these orders were amended before their stated day passed, and the lead then uses the amended date. EO 492
stated January 1, 1907, and EO 516 (October 6, 1906) substituted March 2, 1907. EO 7074 continued the first National
Labor Relations Board until July 1, 1935. EO 7090 changed that date to August 1, 1935, and EO 7121 changed it to
September 1, 1935; both amendments are held and recorded as amendment edges on EO 7074. A later extension issued as a
separate order is a different case: EO 1120's extension from September 2, 1909 does not change EO 1022's own end of
September 2, 1909.

For the veterans' encampment orders (EO 2237, 2423, 2669, 2882, 2890, 3112), the leave covers stated days plus "as
many more days ... as are necessary for the journey ... and return". The text therefore fixes no exact last day. The
lead gives the interval from the order's date to December 31 of that year. That upper bound is an inference (a rail
journey within the United States took days, not months), and the lead says so.

**M-ANCSA: Alaska Native reserves (B07).** Section 19(a) of the Alaska Native Claims Settlement Act of December 18,
1971 provides that "the various reserves set aside by legislation or by Executive or Secretarial Order for Native use
or for administration of Native affairs" are "hereby revoked subject to any valid existing rights of non-Natives".
The Annette Island Reserve is excepted. The six members reserve land "for the use of the Bureau of Education and the
natives of Alaska of indigenous race" (EO 1896, 1987, 2508, 2525 and 2757) or "for the natives of Alaska residing at
the village of Klukwan" (EO 3673). Each is a reserve for Native use or for the administration of Native affairs. The
lead is the interval from the order's date to 1971-12-18, because some reserves ended earlier in whole or part (for
example, EO 5207 of 1929 revoked part of the Norton Bay reserve). The statute was read only on the web, so these
leads carry the gap "source not yet held".

**Mechanisms considered and not adopted.**
- *Class events for territories*: Alaska statehood (1959), Hawaii statehood (1959), Philippine independence (1946) and
  the Puerto Rico Constitution (1952). None was found to reach a member by its terms. The Alaska land, timber and
  fisheries reserves are land withdrawals, which statehood did not revoke. The Puerto Rico acting-judge designations
  end with the absence each covers.
- *General pay statutes*: the Classification Acts of 1923 and 1949, the Pay Readjustment Act of 1942 and the Career
  Compensation Act of 1949. None is held, and the doctrine does not rely on a general "inconsistent laws repealed"
  clause.
- *Lapse of appropriations for fund allotments*: the lapse rule is general. Its application depends on whether each
  appropriation item was annual, multi-year or "until expended", and the project holds none of those items. Many
  allotments cite emergency acts whose titles name a fiscal year (for example "Fourth Deficiency Act, fiscal year
  1933") but whose funds were available beyond that year.
- *The Veterans' Benefits Act of 1957*: it repealed earlier veterans' laws, but it also carries a section on
  "outstanding rules, regulations, and orders" (sec. 2307), which the copy read did not reach.
- *Property transfers performed by delivery*: the reviewed type rule TR-PROPERTY-TRANSFER makes the end the delivery or
  accession date, which the project does not hold.

## (b) Primary sources

| Id | Citation | Held or to acquire | Establishes |
|---|---|---|---|
| S-TRA76-A | Tax Reform Act of 1976, Pub. L. 94-455, sec. 1202(a), 90 Stat. 1520, 1667-1668 (Oct. 4, 1976); 26 U.S.C. 6103(a) | held: `jobs/source-ladder/output/texts/queue_EO_10906_Tax_Reform_Act_of_1976_Pub._L._94-455_sec._1202_90_Stat._1667_which_rewrote_sec._6103_64c0b4c21d.txt` (sha256 `38235434bbf04013146a46e5e35912661539be250b864905434e3039bd4ba956`; PDF sha256 `252063912027da27…`, https://www.govinfo.gov/content/pkg/STATUTE-90/pdf/STATUTE-90-Pg1520.pdf); pin "confidential, and except as authorized by this title" (text line 8659) | The general rule of confidentiality and the prohibition on disclosure except as Title 26 authorizes |
| S-TRA76-G | same Act, 90 Stat. 1672; 26 U.S.C. 6103(g) | same file; pin "DISCLOSURE TO PRESIDENT AND CERTAIN OTHER PERSONS" (line 8948) | The only presidential provision of the new section is disclosure to the President on written request |
| S-TRA76-I | same Act, sec. 1202(i), 90 Stat. 1688 | same file; pin "(i) EFFECTIVE DATE.—The amendments made by this section take" (line 9914, continuing "effect January 1, 1977.") | Effective date January 1, 1977 |
| S-ANCSA | Alaska Native Claims Settlement Act, Pub. L. 92-203, sec. 19(a), 85 Stat. 688, 710 (Dec. 18, 1971); 43 U.S.C. 1618(a) | to acquire: https://www.govinfo.gov/content/pkg/STATUTE-85/pdf/STATUTE-85-Pg688.pdf (read on Cornell LII, source credit Pub. L. 92-203, sec. 19, 85 Stat. 710) | Revocation of Executive-order reserves for Native use, except Annette Island |
| S-STCC-ACT | Act of March 2, 1901, ch. 804, sec. 16, 31 Stat. 877 | to acquire: https://www.govinfo.gov/content/pkg/STATUTE-31/pdf/STATUTE-31-Pg877.pdf (chapter and page as conventionally cited; unverified) | Authority for the Commission extensions; context only |
| S-EO1120 | EO 1120 (Aug. 6, 1909) | held: `jobs/app-executive-orders/output/texts/executive-order-1120-time-limit-for-completion-the-work-the-spanish-treaty-claims.txt`; pin "is hereby extended for and during six months from and after the second day of September, 1909, and for no longer time" | The series' own-terms formula |
| S-EO516 | EO 516 (Oct. 6, 1906) | held: `jobs/wikisource-texts/output/texts/EO_516.txt`; pin "is hereby extended to March 2, 1907, instead of January 1" | Amended end of EO 492 |
| S-EO7090, S-EO7121 | EO 7090 (June 29, 1935), EO 7121 (July 31, 1935) | held: APP texts `executive-order-7090-extending-the-national-labor-relations-board.txt`, `executive-order-7121-extending-the-national-labor-relations-board.txt` | EO 7074's end moved to August 1, then September 1, 1935 |
| S-EO5376 … S-EO6858 | 14 revoking orders outside the family: EO 5376 (June 23, 1930), 6005-A (Jan. 21, 1933), 6612 (Feb. 22, 1934), 6562 (Jan. 18, 1934), 5952 (Nov. 23, 1932), 5605 (Apr. 21, 1931), 6913 (Dec. 4, 1934), 6776 (June 30, 1934), 8714 (Mar. 18, 1941), 6550 (Jan. 6, 1934), 9461 (Aug. 7, 1944), 6724 (May 28, 1934), 6777 (June 30, 1934), 6858 (Sept. 26, 1934) | held: APP transcriptions in `jobs/app-executive-orders/output/texts/` and the OFR Hoover compilation text `jobs/ofr-compilations/output/texts/EO_6005A.txt`; each pin is the clause naming the member, recorded with its sha256 in the JSON | Each ends the named member(s) as a whole |
| S-EO7005, S-EO7044, S-EO1706, S-EO3583, S-EO4158, S-EO3261, S-EO4021 | 7 revoking orders inside the family | held: each member's primary text; pins in the JSON | End EO 6832, 7004, 1648, 3251, 4147, 3166 and 3752 respectively |

Every held source's path, sha256 and pin are in the JSON `sources` list. The generator checked each pin against the
held file. The member orders' own texts are the evidence for every `TERM` lead, and each lead records the text's path,
sha256 and grade. Most are mirror transcriptions or machine-read scans, and the engine adds that as a gap.

## (c) Decision procedure

Branches are tried in order. The first branch whose conditions all hold decides the member. Branch ids are those in
the JSON.

1. **B01, revoke-only (16; `no`, `TERM`, the order's date).** Condition: the member is on the verified list, and its
   text contains revoked, rescinded or cancelled. Members: EO 446, 1074, 1182, 1706, 3261, 3583, 4020, 4021, 4158,
   6575, 6612, 6668, 6669, 6776, 7005 and 7044. Gap: the text grade.
2. **B02, amend-only (75; `no`, `TERM`, the order's date).** Condition: the member is on the verified list, and its
   text contains an amend, modify or substitute verb. The list includes EO 4459, 5471, 6352 and 7209, which X1 typed
   as closings but which amend the Panama Canal employment rules or Schedule A of the Civil Service Rules. They are
   decided by their own text, not by the closing type. Gaps: the text grade; the amended order's status is not
   decided.
3. **B03-01 to B03-21, revoked by a later order (23; `no`, `ACT`).** Condition: the member is on the verified pair
   list. Each branch cites its revoking order and gives that order's date or stated effective date. Gap: the revoking
   order's text grade.
4. **B04, tax-return inspection (27; `no`, `ACT`, interval from the order's date to 1977-01-01).** Conditions: the X1
   type is `tax_return_inspection`; the text matches "open(ed) to inspection", "inspection of ... returns" or
   "INSPECTION OF INCOME"; the text is not the refund-decisions order. Gaps: the earlier actual end (the named body's
   end) is not held; section 6103(b)(1) defines "return" by reference to Title 26, so its reach to returns filed under
   pre-1939 Acts rests on the general prohibition rather than an express provision; the text grade.
5. **B05, Spanish Treaty Claims Commission (13; `no`, `TERM`).** Eleven branches fix the end date from a legible stated
   period: EO 228 (1904-03-02), 246 (1904-09-02), 407 (1906-09-02), 492 and 516 (1907-03-02), 557 (1907-09-02), 674
   (1908-03-02), 921 (1909-03-02), 1022 (1909-09-02), 1120 (1910-03-02) and 1167 (1910-05-02). B05-ZZ covers EO 292
   and 749, whose starting year is partly illegible ("Maarcb., nineteen' in tred. n fv"; "March, 1 903" in an order of
   February 5, 1908). For these two the lead is the interval from the order's date to 1910-05-02, the end of the last
   extension in the series, and the gap says the bound assumes the next March 2 after the order's date. EO 267 and 345
   are illegible and are left open (O03).
6. **B06, deferrals and continuations (10; `no`, `TERM`).**
   - Fixed dates: EO 6222 (1933-09-10), 6690 (1934-05-21), 6512 (1934-01-16) and 7100 (1935-12-01).
   - Intervals ending on the stated date, because a proviso allowed an earlier end: EO 6244 (to 1933-10-10), 6245 (to
     1933-09-30), 6731 (to 1934-10-01) and 6927 (to 1935-06-30).
   - EO 625 runs to 1908-06-30; the year reads "1G08" and is taken with the order's 1907 date.
   - EO 7074 runs to 1935-09-01, as amended.

   Gap: no amending order was searched for beyond the held edges.
7. **B07, Alaska Native reserves (6; `no`, `ACT`, interval to 1971-12-18).** Condition: the member is on the list, and
   its text reserves land for the natives. Gaps: ANCSA is not held; earlier partial revocations were not searched.
8. **B08, named days (15; `no`, `TERM`).**
   - Inauguration-day excusals: EO 1728 (1913-03-04) and 2540 (1917-03-05).
   - Four-hour days: EO 3205 (1919-12-31), 3370 (1920-12-31), 3589 (1921-12-24), 3665 (1922-04-27), 3765
     (1922-12-23), 3934 (1923-12-24) and 4110 (1924-12-24).
   - Encampment leave, with the interval running to December 31 of the stated year: EO 2237, 2423, 2669, 2882, 2890
     and 3112.
9. **B09, stated fiscal year or period (21; `no`, `TERM`).**
   - Officers' rental and subsistence allowances for a fiscal year: EO 3865, 3996, 4228, 4414, 4620, 4847, 5099, 5355,
     5583, 6213 and 6769 (each ends June 30 of the stated year).
   - Economy Act cost-of-living percentages: EO 6085, 6188, 6553, 6791 and 6936.
   - Rural carriers' equipment allowances: EO 6176, 6332 and 6675.
   - EO 2968A: an allotment "during said fiscal year", ending no later than 1919-06-30.
   - EO 457: a copyist "not to exceed three months", ending no later than 1906-09-13.
10. **O01 to O09 and O03T (595; `open`).** See section (d).
11. **O99, catch-all (0; `open`).**

Counts from `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-ADMIN.json --hints`: 801 members;
206 decided (all `no`); 0 contradicted. Branch counts: B01 16, B02 75, B03 23 (21 branches), B04 27, B05 13, B06 10,
B07 6, B08 15, B09 21; O01 29, O02 17, O03 5, O03T 1, O04 55, O05 37, O06 83, O07 54, O08 113, O09 201, O99 0. By
WPA family hint: 616 "other", 141 "emergency_war", 10 "office_closing_mourning", 8 "tariff_customs", and small
remainders.

## (d) Members the procedure cannot decide (595)

- **O01, misclassified or text mismatch (29).** The held text is another order's, the scan is unreadable, or the order
  is a different kind. Examples:
  - The text is another order's: EO 1183's text is EO 1182½ (the Alaska fox-island leases); EO 27-1 is a State
    Department notice.
  - The scan is unreadable: EO 112, 113, 13, 310, 311 and 313A.
  - The order is a different kind: EO 3878, 4075 and 4571 are Indian trust-period extensions, which belong with
    PD-INDIAN; EO 3885 is a military land withdrawal; EO 1 and EO 4 are Civil War orders, and their held edges point
    to unrelated later orders; EO 3292 and 3319 concern the Grain Corporation's capital stock.

  These members need reassignment by text, or a legible copy.
- **O02, closings and mourning without a fixed day (17).**
  - The Labor Day orders of 1907-1910 (EO 677, 926, 1122, 1243) name "the first Monday in September" without a year.
    Their annual reissue suggests each covered one year, but the text does not say so. EO 1404 and 1574 say
    "hereafter", which makes them standing rules.
  - The mourning orders tie closings to "the day of the funeral" without a date (EO 24, 27, 2516, 3466, 4274A).
  - EO 190 names "Monday" against a Wednesday parade date.
  - EO 973's day and hour are damaged by OCR.
  - EO 1541 sets a preference, and EO 3676 grants pay for a past holiday.

  The Jacquard L3 review (`research/excavator/jacquard-2026-10-31/INDIVIDUAL_REVIEW.csv`) rejected these on the same
  grounds.
- **O03, own-terms orders with no fixed end (5).**
  - EO 6221 defers to "sixty days after the convening of the second session of the 73rd Congress". Deciding it needs
    the convening date from the Congressional Record, and EO 6624 (March 1, 1934) further deferred the Board's
    abolition until a later transfer.
  - EO 7084 and 7085 were amended by EO 7089 and 7091 to run "until further order". Deciding them needs the orders
    that ended the Textile and Steel Labor Relations Boards.
  - EO 267 and 345 are illegible.
- **O03T, EO 5079 (1).** It opens the Commissioner's refund decisions to inspection. Whether the 1976 rewrite reaches
  those decisions is not settled by the held text.
- **O04, fund allotments (55).** An allotment's command ends when its funds are spent or when the appropriation lapses.
  The lapse date depends on each appropriation item. Examples are the "Temporary Government for West Indian Islands"
  items of the Naval Appropriation Acts, which fund the Virgin Islands allotments, and the availability clauses of
  the Fourth Deficiency Act of 1933 and the Emergency Relief Appropriation Act of 1935. None of these items is held.
  The Virgin Islands orders also merge the sums into the colonial treasuries.
- **O05, property transfers (37).** Under TR-PROPERTY-TRANSFER the end is the delivery date, which is not held. Several
  members also carry return-on-notice terms (EO 3785), personnel or functions (EO 2588, 2707, 2903), conditions (EO
  3573), or are misfiled (EO 3407 passports, EO 7365 the dissolution of the Second Export-Import Bank).
- **O06, territories (83).** This group comprises Alaska land, timber and fisheries reserves (land withdrawals, for
  PD-LAND-WITHDRAWAL); Puerto Rico acting-judge designations, which end with the absence covered and need the absent
  judges' service dates; Hawaii orders of 1898-1900 (EO 116 and 122 wait on the Hawaiian Organic Act, 31 Stat. 141);
  Virgin Islands administration and narcotics rules; reporting channels for Guam and Samoa; and the Cuban provisional
  government (EO 518).
- **O07, pay and allowances (54).** This group comprises standing pay rules (enlisted special pay, flying pay,
  quarters allowances, travel regulations), compensation of named persons and commissions, and emergency-agency wage
  rules. No held statute displaces them by its terms.
- **O08, regulations (113).** This group comprises Army ration and punishment regulations, passport rules, Hot Springs
  hospital rules, Veterans Regulations (other than the amend-only and revoked ones), Alien Property Custodian powers,
  and emergency-relief employment rules. The superseding instruments are not held. The Veterans' Benefits Act of 1957
  must be read for its savings section.
- **O09, organization (201).** This group comprises land-office discontinuances, removals and consolidations (65 by WPA summary), boards
  and committees, succession orders, and transfers of functions. A land-office discontinuance is a single act, but the
  receiving district's extent continues to rest on the order. Reorganization Plan No. 3 of 1946, which would show
  whether those offices were abolished, is not held.

## What the coordinator must decide

1. Whether to accept the 1976 tax rewrite as an `ACT` end for the 27 inspection orders. The statute prohibits the
   commanded conduct and leaves no presidential-order route. The residual question is its reach to returns filed under
   pre-1939 Acts.
2. Whether the four Civil Service Rules amendments that X1 typed as closings (EO 5471, 6352, 7209) and EO 4459 should
   stay decided here as amend-only, or move to PD-CS-RULES. The coordinator's instruction routed misclassified members
   to open, but these are decided by their own text under the brief's amend-only rule.
3. Whether to queue the ANCSA volume (85 Stat. 688). B07 rests on it.
