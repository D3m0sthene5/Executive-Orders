# PD-CS-ONE-PERSON: one-person civil-service orders

Family doctrine for 1,015 undecided orders typed by X1 as `cs_waiver_individual` (852), `personnel_designation` (128),
`patent_signing_designation` (18) and `retirement_exemption` (17). Status question: was the order, as a whole, still
in force on the project cutoff, October 14, 2026? Machine form: `research/pothier/doctrines/PD-CS-ONE-PERSON.json`
(schema `pothier-family-doctrine/v1`). Leads are proposals for the owner; they change no status and no count.

## Conclusions

The doctrine proposes a `no` lead for **90** members and leaves **925** `open`. It proposes no `yes` lead, because
nothing in force today rests on any member: no statute, regulation or current official record cited by the project
shows a member's command operating on October 14, 2026, and absence of a revocation is not evidence of force.

The 90 `no` leads rest on three kinds of basis.

1. **The life of the named person (78 members; branches B09-B13).** A one-person order permits one action for one
   named person (an appointment, reinstatement, transfer, promotion, classification or exemption) or designates one
   person. Its command is used up when the action is taken, and it cannot operate after that person dies. The
   longest verified human life is 122 years 164 days (Jeanne Calment, 1875-1997). So if the order's own text shows
   that the person was alive on some date X, the person died no later than X + 122 years 164 days; and if the text
   or a rule it cites shows the person was at least A years old on the order date D, the person was born no later
   than D minus A years and died no later than that birth bound + 122 years 164 days. The lead is `no` only when the
   bound falls before October 14, 2026 **on a fact quoted from the order or a cited rule**, never on an assumed
   adult age. The facts used are: the order is dated before May 3, 1904 (so no age is needed; 2 members); the person
   had reached a statutory retirement age, of which the lowest is 62 (5 members); the person had passed the
   65th-birthday bar of the postmaster examination order EO 3455 (15 members); the text states the person's age or an
   age limit the person exceeds (5 members); the text states that the person was employed, appointed or serving on
   or by a date before May 3, 1904 (51 members, verified one by one; quotes in Appendix A). Whether and when the
   action was taken stays unknown: these leads say the order ended within an interval, not when.
2. **Own terms (10 members; B03, B03b, B03c, B05-B08).** Designations for two or four years, for ten days, or
   with a stated end date end on their own terms (7). EO 6179-A only revokes other orders and was spent on issue
   (coordinator ruling P1); EO 6142 and EO 7472 only amend other orders and merged into their parents on issue
   (ruling P2: their text continues as part of the parent until the parent ends; the parent's lifecycle carries it).
3. **A later instrument that names the member (2 members; B01, B02).** EO 5371 revokes EO 5332 by number;
   EO 6179-A revokes the October 23, 1926 appointment of Susan T. Waite that EO 4528 authorized.

The 925 open members are open for stated reasons, not by default: 585 one-person waivers dated after May 2, 1904 whose
text fixes no minimum age and no earlier dated presence (B99); 28 possible minors (messengers, boys, girls,
apprentices; B26); 82 designations of named officers without a stated term (B23); 17 land-patent signers (B24);
145 class orders, lists and general authorities typed as one-person waivers (B22) and 8 pre-1903 rule amendments and
special rules (B04), all for PD-CS-RULES; 46 orders outside the family (B21); 3 retirement class orders (B25); and 11 members whose held text is another order's, lacks the command, is
unreadable or names a second person with no bound (B20).

**What this doctrine does with the earlier work.** It reuses TR-CS-WAIVER and TR-RETIREMENT-EXEMPTION (reviewed
research patterns), the cs-waiver research report of 2026-10-28 (four outcomes; Civil Service Commission reports do
not record use; no general rewrite ends a waiver; latest-possible-death bound only on a quoted age fact) and the
Jacquard reviews. Of the 58 orders the Jacquard coordinator held back, 11 now get a `no` lead on a dated fact in
their own text (seven "cut-off text" holds: EO 325, 1953, 1961, 1983, 2083, 2165, 2244; four messenger holds: EO 957,
2009, 2140, 2447, each showing the person in service in 1877-1893 or with thirty years' army service by 1908). The
other 47 holds stay open. Of the 183 Jacquard failures in this family, 8 get a `no` lead (two waivers, six
retirement orders) and 175 stay open, most because they are class orders, multi-person orders without a bound for
every person, rule amendments, or texts of a different order. The Jacquard L1 card's premise that "anyone the federal service could
employ in 1917 or earlier was at least 14 years old" is not used anywhere in this doctrine: no held source states
it, and the owner's evidence rule requires one.

## (a) Mechanisms by which members end or persist

**M1. Life of the named person (ends).** A permission or designation whose only object is a named person cannot
operate after that person's death, and it is exhausted earlier if used. The death is not known, so the doctrine uses
its latest possible date. The date rule is the interval (order date, bound], where bound = X + 122 years 164 days
and X is either the latest date at which a quoted fact shows the person alive, or the order date minus the minimum
age the quoted fact fixes (subtract whole years, then add 122 years, then 164 days). A position or professional
title, "Mrs.", "widow of", or a later order naming someone with the same name does not fix an age (the family
contains a "messenger boy", EO 2661, and a "girl messenger", EO 3556A). When an order names several persons, every
one of them needs a bound and the order ends at the latest of them (EO 1587 fails this: only one of its three
persons has a dated fact). The bound rests on the empirical record of the longest verified life; that is the only
assumption, and it is the one the owner already accepted for the Jacquard lots.

The minimum-age facts the machine applies, and why each is safe:

- *Date before May 3, 1904 (a_min = 0).* Any person named was alive on the order date. An order dated on or before
  May 2, 1904 gives a bound on or before October 13, 2026.
- *Retirement age (a_min = 61).* The 1932-1933 exemptions under section 204 of the Act of June 30, 1932 name persons
  "who have reached" (or "during the current month" reach) "the retirement age prescribed for automatic
  separation". The Civil Service Retirement Act of May 22, 1920 sets 70, 65 for mechanics, carriers and post-office
  clerks, and 62 for railway postal clerks; the Act of May 29, 1930 keeps 62 as the lowest. 61 allows for "during
  the current month". The result holds for any minimum age of 34 or more, so the exact statutory figure cannot flip
  it.
- *Postmaster examination age bar (a_min = 64).* EO 3455 (May 10, 1921) says "No person who has passed his
  sixty-fifth birthday ... shall be given the examination". It has no other age limit, so an order waiving "that part
  of the Executive order of May 10, 1921, which pertains to the age limit" for a named candidate shows the candidate
  was past 65. EO 4011, whose WPA summary says "without regard to age requirements", actually waives "the residence
  requirement" and is excluded by the branch pattern (it is routed to B20).
- *Stated age or exceeded age limit.* The order says the person "is 58 years of age", is "52 years old", is "beyond
  the age limit of 45", exceeds "the maximum age limit of fifty years", or is barred by the rule that no person "who
  is over thirty-five years of age" may be certified. a_min is that age.
- *Dated earlier presence.* The order says the person was appointed, employed or serving on or since a date before
  May 3, 1904, or for a stated number of years ending on a stated date. Being alive on that date needs no age at all.
  Each of the 51 members was read; the quote, the identity of the person (the quote names the person in the
  member's WPA summary) and the arithmetic are in Appendix A. Statements about a husband, father or brother were
  rejected (for example EO 2946, 3926, 4770, 5056), as were "about" or "approximately" periods that could fall after
  1903 (EO 3144, 5701), texts belonging to a neighbouring order (EO 1912, 3433, 3511, 4431), and orders naming other
  persons without a bound (EO 1587).

**M2. EO 209 and the 1896 rules (not applied).** EO 209, effective April 15, 1903, promulgates new Civil Service
Rules "in lieu of those promulgated May 6, 1896, and the amendments thereof". It does not plainly reach special rules:
EO 250 had to revoke a 1902 special rule in 1904, so special rules outlived EO 209. The eight members it might reach
(EO 123, 158, 164, which amend numbered rules, and EO 130, 141, 142, 143, 203, special rules for a class, a position
or a list) are rule instruments, not one-person orders, and no named person's death can end them. They stay `open`
for PD-CS-RULES (B04).

**M3. Express revocation (ends).** EO 5371 (June 19, 1930): "Executive Order No. 5332, April 22, 1930, temporarily
changing the order of precedence of the Assistant Secretaries of War is revoked." Date: 1930-06-19. EO 6179-A (June
16, 1933) revokes ten "appointments made by the President ... without regard to the requirements of the
civil-service rules", including "The appointment on October 23, 1926, of Mrs. Susan T. Waite as Clerk in the Bureau
of Labor Statistics"; EO 4528, dated October 23, 1926, is the waiver for Susan T. Waite's reinstatement to a
clerkship in that Bureau. Date: interval (1926-10-23, 1933-06-16], since use is unknown. None of the other nine
appointments EO 6179-A revokes is a member of this family.

**M4. Own terms (ends).** EO 1313 and 1753 designate Martin A. Knapp to exercise the chairman's powers "for a period
of two years" (ending 1913-03-04 and 1915-03-22); EO 7281 and 7426 designate the Federal Reserve chairman and vice
chairman "to serve as such for a term of four years" (ending 1940-02-03 and 1940-08-06); EO 4300 and 4639 designate
acting Farm Loan Commissioners "for a period of ten days from the date hereof" (1925-09-21; no later than
1927-05-06); EO 6725 appoints Science Advisory Board members whose "term of office ... shall terminate on July 31,
1935". EO 6179-A's only content revokes other orders' appointments, so its command was exhausted on June 16, 1933
(ruling P1, `spent_on_issue`). EO 6142's only content amends EO 5872 "so as to terminate the exemption of the said
Pickens Neagle on May 31, 1933", and EO 7472's only content modifies EO 7140; under ruling P2 each merged into its
parent on its own date (`merged_into_parent_on_issue`): its text continues as part of the parent until the parent
ends, and the parent's lifecycle carries it.

**M5. General rewrites of the Civil Service Rules (no end; recorded so that nothing relies on them).** EO 7916
(1938), EO 8743 (1941), EO 9830 (1947) and EO 10577 (1954) revoke only listed orders and schedules and list no
one-person waiver; the Act of March 27, 1922 and EO 9830 section 1.1(b) recognize status granted by executive order.
Under the evidence rule a later general rule ends an order only if something shows it extinguished that order, so
none of these is an end (finding of the 2026-10-28 research report, adopted here without change).

**M6. EO 3461 (May 16, 1921) (not applied).** It revokes "all Executive orders and amendments to the civil service
rules authorizing appointments, promotions, or removals without full compliance with the civil service laws and
rules, because of war emergencies existing at the time" and lists 45 orders. The held copy stops at item 27, all
listed items seen are class orders, and whether a one-person waiver resting on war work falls under the general
clause is a reading the machine cannot apply safely. No branch uses it.

**Persistence.** Nothing in the family persists by its own terms past 2026. Accrued effects (an appointment made,
competitive status acquired, an annuity earned) survive as consequences of the action, not as the order's command,
and do not make a lead `yes`.

## (b) Primary sources

| Id | Source | Held? | Path and sha256, or URL to acquire | Pin (phrase found in the held text) | Establishes |
|---|---|---|---|---|---|
| S1 | Guinness World Records, "Oldest person (ever)": Jeanne Louise Calment, born 21 February 1875, died 4 August 1997, 122 years 164 days | no (read on the web 2026-11-05) | https://guinnessworldrecords.com/world-records/oldest-person ; also https://www.grg-supercentenarians.org/jeanne-calment/ | "122 years 164 days" | the longest verified life, used by every M1 bound |
| S2 | EO 209 (March 20, 1903), Civil Service Rules (cited for M2, which ends no member) | yes | `jobs/wikisource-texts/output/texts/EO_209.txt`, sha256 131c53601214343ec8d9a0cee75e4fe45e128a227c056fb811fec91dc170322a | "the President promulgates the following rules in lieu of those promulgated May 6, 1896, and the amendments thereof"; "Approved, to take effect on and after April 15, 1903." | M2 (not an end here) |
| S3 | EO 3455 (May 10, 1921), postmaster examinations | yes | `jobs/wikisource-texts/output/texts/EO_3455.txt`, sha256 46478a4f450cc35d03cc3416b1fe30f9c209d9eb24e6a75113be0e52378f072d | "No person who has passed his sixty-fifth birthday" | B10 minimum age |
| S4 | EO 6179-A (June 16, 1933) | yes | `jobs/app-executive-orders/output/texts/executive-order-6179-revocation-appointment-classified-positions-the-department-labor.txt`, sha256 a57c96a33ec6f168a59c0b4c993696feae4a8101bd68598cfb33e16d3bd61f21 | "The appointment on October 23, 1926, of Mrs. Susan T. Waite as Clerk in the Bureau of Labor Statistics, Department of Labor." | M3 for EO 4528 |
| S5 | EO 5371 (June 19, 1930) | yes | `jobs/app-executive-orders/output/texts/executive-order-5371-order-precedence-the-assistant-secretaries-war.txt`, sha256 e7cd754745d3b97a301b78367c0044bb115d4102909c6cbc0c899f3023d2a832 | "Executive Order No. 5332, April 22, 1930, temporarily changing the order of precedence of the Assistant Secretaries of War is revoked." | M3 for EO 5332 |
| S6 | Civil Service Retirement Act, Act of May 22, 1920, ch. 195, sec. 1, 41 Stat. 614 | yes, as printed in the CSC 39th Annual Report (FY1922), printed p. 99; the Statutes at Large page itself is to be acquired | `jobs/numbered-early-orders/output/books/CSR_1922_pages.jsonl.gz` (page image 150), sha256 2106b2c5749ee44e9ccea4ade12daa7224877d9915e88f5dbcea250958a7dab4; acquire https://www.govinfo.gov/content/pkg/STATUTE-41/pdf/STATUTE-41-Pg614.pdf | "railway postal clerks at sixty-two years of age" | lowest retirement age 62 |
| S7 | Act of May 29, 1930, ch. 349, sec. 1, 46 Stat. 468 | no (read on govinfo) | https://www.govinfo.gov/content/pkg/STATUTE-46/pdf/STATUTE-46-Pg468.pdf | "shall be eligible at sixty-two years of age" | 62 remains the lowest age in 1932-33 |
| S8 | Act of June 30, 1932, ch. 314, Part II, sec. 204, 47 Stat. 382 (page of sec. 204 unverified) | no; its words are quoted in the held member texts | https://www.govinfo.gov/content/pkg/STATUTE-47/pdf/STATUTE-47-Pg382.pdf | (member texts) "section 204 of Part II of the act" | authority for the 1932-33 exemptions |
| S9 | CSC 32nd Annual Report (FY1915), printed pp. 7-8 | yes | `jobs/numbered-early-orders/output/books/CSR_1915_pages.jsonl.gz` (page image 14), sha256 94cee92a0855d216af345776ed26e77031aa26e666c100e15630a66c2d54fbec | "published in full in the appendix" | the Commission's report slices print the whole order, so a slice without a signature line is not by that fact incomplete |
| S10 | Each member's own held text (source kind `member_text`, ruling P6) | member text | the engine records path, sha256 and grade on each lead | quotes in Appendix A and in M4 | stated periods, dated facts, stated ages |

Sources read for the mechanisms that are not ends (M5, M6) are those of the 2026-10-28 research report
(`research/excavator/claude-cs-waiver-research-2026-10-28/REPORT.md`: EO 7916, 8743, 9830, 10577 in the repository;
EO 3461 held only to item 27 at `jobs/csc-annual-reports/output/texts/EO_3461.txt`, sha256 636711b09cca359afcd8bfb3160718611ece8bf958c0570bdfc9590b466c560d).

## (c) Decision procedure

Branches are tried in order; the first whose conditions all hold decides. Counts are from
`python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-CS-ONE-PERSON.json --hints` on 2026-11-05
(1,015 members; 90 decided; 0 contradicted by held later edges or later name matches). Every `no` lead also carries
the engine's automatic gaps: S1 (and S7, S8 where used) not yet held, and the order text's grade when it is a
transcription or an unauthenticated scan.

| Branch | Members | Lead | Basis and date rule | Conditions (plain words) |
|---|---:|---|---|---|
| B01 | 1 | no, ACT | EO 5371 revokes EO 5332; fixed 1930-06-19 | member is EO 5332 and has the held revocation edge |
| B02 | 1 | no, ACT | EO 6179-A revokes the Waite appointment; interval (1926-10-23, 1933-06-16] | member is EO 4528 and its text names Waite |
| B03 | 1 | no, TERM (`merged_into_parent_on_issue`) | only amends EO 5872; order date 1933-05-23 | member is EO 6142 and the amending sentence is in its text |
| B03b | 1 | no, TERM (`spent_on_issue`) | only revokes other orders' appointments; order date 1933-06-16 | member is EO 6179-A and its revoking sentence is in its text |
| B03c | 1 | no, TERM (`merged_into_parent_on_issue`) | only modifies EO 7140; order date 1936-10-15 | member is EO 7472 and its modifying sentence is in its text |
| B04 | 8 | open (`retype_PD-CS-RULES`) | rule amendment or special rule, not a one-person order | dated 1896-05-06 to 1903-03-19 and held text says "Special Rule" or amends a numbered rule: EO 123, 130, 141, 142, 143, 158, 164, 203 |
| B05 | 4 | no, TERM | designation for a stated number of years; order date plus the period | designation whose text designates a person "for a period of" or "for a term of" N years, not an order establishing a body: EO 1313, 1753, 7281, 7426 |
| B06 | 1 | no, TERM | ten days; fixed 1925-09-21 | EO 4300 |
| B07 | 1 | no, TERM | at most ten days; interval to 1927-05-06 | EO 4639 |
| B08 | 1 | no, TERM | stated end; fixed 1935-07-31 | EO 6725 |
| B09 | 5 | no, TERM (life) | named persons at retirement age; a_min 61; interval (order date, 1994-06-18] | text: persons who "have reached" or "reach the retirement age prescribed for automatic separation": EO 5896, 5921, 5946, 5954, 5988 |
| B10 | 15 | no, TERM (life) | candidate past 65 under EO 3455; a_min 64; interval (order date, 1985-08-08] | text waives the part of the order of May 10, 1921 "which pertains to the (maximum) age limit" (or says the candidate is "over 65 years of age"): EO 3602, 3717, 3730, 3735, 3776, 3780, 3784, 3790, 3792, 3822, 3823, 3835, 3840, 3850, 4595 |
| B11 | 5 | no, TERM (`hand_checked_dated_fact`) | stated age; interval (order date, 2008-11-27] | checked list, anchored by the exact age phrase of Appendix A in the text: EO 3378, 3499, 3856, 4118, 5084 |
| B12 | 2 | no, TERM (life) | dated before 1904-05-03, a_min 0; interval (order date, 2026-01-09] | waiver or designation with named persons, an operative "may be reinstated/appointed..." or "designate the following named persons", no class or list language, not a narrative-only text: EO 162, 226 |
| B13 | 51 | no, TERM (`hand_checked_dated_fact`) | dated presence before 1904-05-03; interval (order date, 2026-03-11] | checked list, anchored by the exact dated-fact sentence of Appendix A in the text |
| B20 | 11 | open | identity or command not in held text | EO 221, 223, 234 (Commission narrative only), 251 (unreadable scan), 1912, 3433, 3511, 4431, 3523 (text of another order), 4011 (summary misdescribes it), 1587 (two of three persons unbounded) |
| B24 | 17 | open | land-patent signers | type `patent_signing_designation` |
| B21 | 46 | open (`retype_other_family`) | outside the family: PD-LAND-WITHDRAWAL or PD-NATIONAL-FOREST (land, districts), PD-ADMIN (bodies, boats, radio, bonds, property, patrols), PD-CS-RULES (Retirement Act class exclusions), PD-WAR-EMERGENCY (relief, CCC) | designations or retirement orders whose WPA summary is about land districts, boats, radio, bonds, bodies established, class exclusions, property; waivers naming no person about land |
| B22 | 145 | open (`retype_PD-CS-RULES`) | class orders, lists, general authorities, rule amendments after 1903 (PD-WAR-EMERGENCY for 1917-1921 war authorities) | waiver typed, and summary opens with a class or an official "authorized", or no person named, or the text speaks of "all/any/such persons", "in like circumstances", "on a list" |
| B23 | 82 | open | designations without a stated term | remaining `personnel_designation` |
| B25 | 3 | open (`retype_PD-CS-RULES`) | retirement class orders | remaining `retirement_exemption` |
| B26 | 28 | open | possible minor | "messenger", "boy", "girl" or "apprentice" in title, summary or text |
| B99 | 585 | open | one-person waiver, no age fact | catch-all |

Evidence gaps on every life-of-person branch: use of the permission is unknown (the NARA St. Louis service record
card, or the Official Register of July 1 in odd years to 1921, would show it); the bound rests on S1, which is held
only on the web until acquired. On B13 several texts are Commission report prints without a signature line (S9 says
the reports print the orders in full), and the verified list is closed: any member whose held text or identity
changes must be re-read. On B09 the orders name several persons; each reached retirement age, so the bound covers
all of them.

## (d) Members the procedure cannot decide

925 members stay open.

- **585 one-person waivers dated after May 2, 1904 with no age fact (B99).** The permission certainly ended when
  used or at the person's death, but the held text shows neither date and gives no quoted fact bounding the death
  before October 14, 2026. Most are 1910s-1930s appointments of widows, temporary employees and named specialists.
  For an order dated D, the bound falls before the cutoff only with a minimum age greater than the time from May 3,
  1904 to D (more than 14 years for an order of May 1918, more than 18 for May 1922, more than 33 for May 1937). Any
  one of three kinds of evidence would decide a member:
  1. the civil-service rule, Commission regulation or statute fixing the minimum age for entrance to the position's
     examination, in force on the order date, where the order leaves that examination in place (an order that
     waives the examination or "the civil-service rules" generally sets the age limit aside with it) and the person
     is not a preference claimant. Rule V, sec. 5 of the rules, printed in the held Commission reports (FY1914
     p. 76, FY1915 p. 69, FY1918 p. 51, FY1922 p. 49), lets the Commission "change by regulation the existing age limits
     for entrance to the examinations" and exempts preference claimants; the reports print some limits (for example
     FY1918 p. 111, a postal examination barring a person "under 18 years of age or over 50 years of age"). The source
     that would make this route machine-applicable is the Commission's published age limits per examination (its
     Manual of Examinations and the annual reports' examination tables); I could not identify an exact URL for a
     digitized Manual, so it is not in FETCH_PROPOSED;
  2. an Official Register entry (all employees, July 1 of odd years to 1921) or another record dating the person's
     presence before May 3, 1904;
  3. the NARA St. Louis service record card (birth, action and separation dates; about $20 each).
- **28 possible minors (B26).** Messenger boys and girls and apprentices may have been children; the coordinator's
  Jacquard holds of this kind stay open except the four whose text dates earlier service.
- **82 designations without a stated term (B23)**, mostly Rev. Stat. sec. 179 designations of a named solicitor,
  assistant secretary or general "to act as Secretary during the absence of the Secretary". They lasted while the
  absence lasted or until superseded and ended at the latest with the designee's tenure or death, but no held field
  gives the designee's age or separation. Their dates are public (biographical directories, agency histories) and
  could be acquired per person.
- **17 land-patent signers (B24).** Personal designations of General Land Office clerks; later designations of
  another "regular" clerk suggest supersession, but no held text says so. Acquire the clerk's separation date or the
  statute governing the patent-signing secretary (Rev. Stat. sec. 450 and its successors).
- **145 class orders (B22), 8 pre-1903 rule amendments and special rules (B04), 46 orders of other kinds (B21), 3
  retirement class orders (B25).** These are X1 misclassifications, each lead naming the family that should decide it: the death of a named person cannot end an authority over a class, a list, a position or
  future persons. They need the doctrine for their true kind (PD-CS-RULES, PD-WAR-EMERGENCY, PD-ADMIN, land
  families). Several have plain own-terms or revocation leads a future doctrine can use (for example EO 5062, an
  airspace closure from March 2 to March 6, 1929; EO 6777, whose Board EO 7065 abolished; EO 715 and 983 were already
  shown revoked by EO 9830 in the 2026-10-28 report).
- **11 identity or text failures (B20).** Need the order's own text (Commission report page, archival scan).

## Points for the coordinator

1. **Re-typing.** 202 members in B04, B21, B22 and B25 are not one-person orders; each lead names the family that
   should decide it.
2. **Checked lists (B11, B13).** These branches decide members named by instrument id after reading; each is anchored
   by a text pattern made of the exact quoted sentences in Appendix A, so a changed or replaced text fails the anchor
   and falls through to `open`. Lead kind `hand_checked_dated_fact`.
3. **B02** rests on EO 6179-A naming the appointment by date, person and position rather than by order number; all
   three agree with EO 4528.

## Appendix A. Per-member facts for B11 and B13 (checked by reading on 2026-11-05)

"Born no later than" is the quoted date (for a period of N years ending on a date, that date minus N years; for a
year without a day, December 31 of that year) or, for an age, the order date minus the age. "Latest possible death"
adds 122 years 164 days. Every quote names, or is the operative sentence about, the person in the member's WPA
summary. EO 2951 has only a year in the member record; its held text is dated September 4, 1918.

| Member | Order date | Fact (quote from the held text, whitespace collapsed) | Reading | Born no later than | Latest possible death |
|---|---|---|---|---|---|
| EO:3378 | 1920-12-26 | "he being 52 years Oid" | aged at least 52 on the order date | 1868-12-26 | 1991-06-08 |
| EO:3499 | 1921-06-16 | "no person shall be certified as eligible for appointment as a secretary in the diplomatic service who is over thirty-five years of age" | aged at least 35 on the order date | 1886-06-16 | 2008-11-27 |
| EO:3856 | 1923-05-28 | "Mr. Williams is 58 years of age" | aged at least 58 on the order date | 1865-05-28 | 1987-11-08 |
| EO:4118 | 1924-12-23 | "is now beyond the age limit of 45 for admission to exam-ination" | aged at least 45 on the order date | 1879-12-23 | 2002-06-05 |
| EO:5084 | 1929-03-28 | "The maximum age limit of fifty years for admission to the general clerical examination" | aged at least 50 on the order date | 1879-03-28 | 2001-09-08 |
| EO:325 | 1905-05-18 | "Mr. Howard was appointed to one of these positions on June 1, 1900" | alive on 1900-06-01 | 1900-06-01 | 2022-11-12 |
| EO:957 | 1908-10-23 | "Conrad Henzman, a retired first sergeant, with thirty years' experience in the army" | alive on 1878-10-23 | 1878-10-23 | 2001-04-05 |
| EO:1863 | 1913-12-01 | "Mr. Cullen served as a soldier in the Union Army during the Civil War and was honorably discharged. He had nearly 19 years of service as an enlisted man and general service clerk with the Army prior to his appointment as a clerk in the War Department under the civil-service rules in 1883" | alive on 1883-12-31 | 1883-12-31 | 2006-06-13 |
| EO:1953 | 1914-06-03 | "Mr. Bonaud was an inspector in the Customs Service at New Orleans from August 17, 1893" | alive on 1893-08-17 | 1893-08-17 | 2016-01-28 |
| EO:1961 | 1914-06-09 | "Lynch, after an excellent record of 19 years in the assistant custodian and janitor service of the Treasury Department, was dropped" | alive on 1895-06-09 | 1895-06-09 | 2017-11-20 |
| EO:1983 | 1914-07-06 | "Mrs. Oliphant was temporarily employed as a sewer in the Government Printing Office at various times during the years 1901, 1902, and 1903" | alive on 1901-12-31 | 1901-12-31 | 2024-06-12 |
| EO:2009 | 1914-08-03 | "long and faithful service of Richard Green as personal messenger to all Secretaries of the Treasury since 1877" | alive on 1877-12-31 | 1877-12-31 | 2000-06-12 |
| EO:2083 | 1914-11-11 | "Mr. Whitted was appointed as a la’ orer at $660 per annum on May 9, 1901" | alive on 1901-05-09 | 1901-05-09 | 2023-10-20 |
| EO:2140 | 1915-02-27 | "Mr. O’Neill has been employed in the Pension Office since June 15, 1893" | alive on 1893-06-15 | 1893-06-15 | 2015-11-26 |
| EO:2165 | 1915-04-13 | "Mrs. Ramsay was appointed a gold worker in the Government Printing Office, September 28, 1903" | alive on 1903-09-28 | 1903-09-28 | 2026-03-11 |
| EO:2244 | 1915-09-08 | "Mr. Potter was appointed a substitute carrier in the Jersey City, N. J., post office on September 15, 1896" | alive on 1896-09-15 | 1896-09-15 | 2019-02-26 |
| EO:2447 | 1916-08-31 | "Mr. Braxton served as messenger in the office of the commissioner of railroads from 1892 to 1899" | alive on 1892-12-31 | 1892-12-31 | 2015-06-13 |
| EO:2853 | 1918-04-30 | "Ernest L. Harris, of Illinois, who entered the Consular Service of the Government in 1898" | alive on 1898-12-31 | 1898-12-31 | 2021-06-13 |
| EO:2936 | 1918-08-14 | "Tenney is a graduate of Dartmouth College and he has lived in China for thirty-two years" | alive on 1886-08-14 | 1886-08-14 | 2009-01-25 |
| EO:2951 | 1918 | "Mr. MacDonald entered the insular civil service in January, 1902" | alive on 1902-01-31 | 1902-01-31 | 2024-07-13 |
| EO:3114 | 1919-07-16 | "Brough’s experience of 29 years in the manufacture of ammunition" | alive on 1890-07-16 | 1890-07-16 | 2012-12-27 |
| EO:3175 | 1919-11-22 | "R. Stone Jackson may be appointed as clerk in the Federal Board for Vocational Education, on the basis of his more than 25 years’ experience" | alive on 1894-11-22 | 1894-11-22 | 2017-05-05 |
| EO:3343 | 1920-10-20 | "long and faithful service of James J. Haney as assistant messenger and chief messenger in the Department of Justice since 1876" | alive on 1876-12-31 | 1876-12-31 | 1999-06-13 |
| EO:3432 | 1921-04-14 | "Mr. Mitchell was regularly employed in the Coast and Geodetic Survey from August 22, 1898" | alive on 1898-08-22 | 1898-08-22 | 2021-02-02 |
| EO:3460 | 1921-05-16 | "Mr. Owen was appointed a letter carrier on May 12, 1890" | alive on 1890-05-12 | 1890-05-12 | 2012-10-23 |
| EO:3467 | 1921-05-20 | "Wells had served for approximately 25 years in the navy yard, New York, and was discharged on February 20, 1914" | alive on 1894-02-20 | 1894-02-20 | 2016-08-02 |
| EO:3479 | 1921-06-07 | "Mr. Kimberlin served as rural carrier at McCordsville, Ind., from August 1, 1902" | alive on 1902-08-01 | 1902-08-01 | 2025-01-12 |
| EO:3490 | 1921-06-13 | "Mr. Morgan was appointed a letter carrier in the New York, N. Y., post office in 1873" | alive on 1873-12-31 | 1873-12-31 | 1996-06-12 |
| EO:3516 | 1921-07-18 | "Mr. Hall was first appointed in the postal service in 1888" | alive on 1888-12-31 | 1888-12-31 | 2011-06-13 |
| EO:3533 | 1921-08-11 | "Mrs. Latta before her marriage served in the Post Office Department from March 1, 1899" | alive on 1899-03-01 | 1899-03-01 | 2021-08-12 |
| EO:3548 | 1921 | "Mr. Artemus A. Rowe, formerly a post-office inspector, who entered the Postal Service in May, 1890" | alive on 1890-05-31 | 1890-05-31 | 2012-11-11 |
| EO:3587 | 1921-12-12 | "Mr. Bryant was appointed as a clerk in the Le Roy, N. Y., post office May 1, 1900" | alive on 1900-05-01 | 1900-05-01 | 2022-10-12 |
| EO:3606 | 1922-01-05 | "Mr. Hamlet was appointed originally on October 3, 1882, in the Interior Department" | alive on 1882-10-03 | 1882-10-03 | 2005-03-16 |
| EO:3713 | 1922-07-31 | "Vallone’s services were discontinued on January 31, 1916, under charges without sufficient evidence, after a service of more than 22 years" | alive on 1894-01-31 | 1894-01-31 | 2016-07-13 |
| EO:3937 | 1923-12-19 | "Mr. Frank E. McMillin, who served as railway mail clerk, post-office inspector, assistant postmaster at Boston, Mass., and chief post-office inspector from September 5, 1890" | alive on 1890-09-05 | 1890-09-05 | 2013-02-16 |
| EO:4122 | 1925-01-10 | "Mr. Kellogg has been in the classified service since 1895" | alive on 1895-12-31 | 1895-12-31 | 2018-06-13 |
| EO:4357 | 1925-12-15 | "Mrs. Margaret C. Gates, a Spanish war emergency clerk, who served more than seven years in the Post Office Department and was classified as a per- manent clerk by the act of April 28, 1902" | alive on 1902-04-28 | 1902-04-28 | 2024-10-09 |
| EO:4367 | 1926-01-19 | "Miss Hall has served satisfactorily as postmaster at Medical Lake for 33 years" | alive on 1893-01-19 | 1893-01-19 | 2015-07-02 |
| EO:4376 | 1926-02-01 | "Stanton resigned without prejudice as quarterman and master boat builder in the navy yard at Puget Sound, Wash., after 27 years of service, on May 14, 1919" | alive on 1892-05-14 | 1892-05-14 | 2014-10-25 |
| EO:4480 | 1926-07-17 | "Mrs. Byrd served in the Bureau of Engraving and Printing from January 5, 1882" | alive on 1882-01-05 | 1882-01-05 | 2004-06-17 |
| EO:4541 | 1926-11-13 | "served in the Bureau of Engraving and Printing as a classified employee from November 9, 1901" | alive on 1901-11-09 | 1901-11-09 | 2024-04-21 |
| EO:4563 | 1927-01-12 | "was a classified employee in the post offices at Savannah and Denver from August 26, 1902" | alive on 1902-08-26 | 1902-08-26 | 2025-02-06 |
| EO:4742 | 1927-10-12 | "Mr. FitzSimons resigned without prejudice from the position of assistant engineer on August 31, 1920, after almost continuous service which began in 1902" | alive on 1902-12-31 | 1902-12-31 | 2025-06-13 |
| EO:4743 | 1927-10-14 | "Mr. Griffin was originally employed under the Naval Establishment, on July 3, 1893" | alive on 1893-07-03 | 1893-07-03 | 2015-12-14 |
| EO:4769 | 1927-11-26 | "service of Mrs. Capron with the Red Cross and as a welfare worker at home and abroad, both in peace and in war, from the relief work in Cuba in 1899" | alive on 1899-12-31 | 1899-12-31 | 2022-06-13 |
| EO:4793 | 1928-01-13 | "Mr. Baine was continuously employed in the com- petitive classified service as an Inspector under the Post Office Department from July 1, 1902" | alive on 1902-07-01 | 1902-07-01 | 2024-12-12 |
| EO:4906 | 1928-06-06 | "Mrs. McLaughlin was employed in the Government Printing office from January 11, 1892" | alive on 1892-01-11 | 1892-01-11 | 2014-06-24 |
| EO:5020 | 1929-01-02 | "Mr. Brown served in the Government Printing Office in various positions for more than forty-one years, being dropped on account of reduction of force, March 27, 1923" | alive on 1882-03-27 | 1882-03-27 | 2004-09-07 |
| EO:5061 | 1929-02-27 | "Mr. Marsh was a classified employee from 1893 to 1914" | alive on 1893-12-31 | 1893-12-31 | 2016-06-12 |
| EO:5075 | 1929-03-04 | "Mrs. Stuart was in the competitive classified service from July 1, 1902" | alive on 1902-07-01 | 1902-07-01 | 2024-12-12 |
| EO:5128 | 1929-05-27 | "Mr. White, a veteran of the Spanish and World Wars, was a civilian employee of the United States military government in Cuba from 1898 to 1901" | alive on 1898-12-31 | 1898-12-31 | 2021-06-13 |
| EO:5135 | 1929-06-12 | "Mr. Liscombe rendered very satisfactory service in the Office of the Supervising Architect from 1902 to 1919" | alive on 1902-12-31 | 1902-12-31 | 2025-06-13 |
| EO:5269 | 1930-02-01 | "Jose T. Casanovas, employed in the Quartermaster Corps of the Army in Porto Rico since 1898" | alive on 1898-12-31 | 1898-12-31 | 2021-06-13 |
| EO:5285 | 1930-02-25 | "loyal and efficient service for the United States Government in the Philippines since August 13, 1898" | alive on 1898-08-13 | 1898-08-13 | 2021-01-24 |
| EO:5501 | 1930-12-02 | "Mrs. Eva MacFate, who served in the Bureau of Engraving and Printing, under the name of Eva C. Small, by appointment from the skilled-laborer register, from September 16, 1896" | alive on 1896-09-16 | 1896-09-16 | 2019-02-27 |
| EO:6058 | 1933-03-01 | "Barber served in the Treasury Department under her maiden name from December 5, 1899" | alive on 1899-12-05 | 1899-12-05 | 2022-05-18 |

Bounds for the pattern branches (computed the same way): B09 (a_min 61) EO 5896 1994-01-09, EO 5921 1994-02-26,
EO 5946 1994-04-29, EO 5954 1994-05-09, EO 5988 1994-06-18. B10 (a_min 64) from EO 3602 1980-06-10 to EO 4595
1985-08-08. B12 (a_min 0) EO 162 2024-07-06, EO 226 2026-01-09.
