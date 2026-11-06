# PD-CS-ONE-PERSON: one-person civil-service orders

Family doctrine for 1,015 undecided orders typed by X1 as `cs_waiver_individual` (852), `personnel_designation` (128),
`patent_signing_designation` (18) and `retirement_exemption` (17). Status question: was the order, as a whole, still
in force on the project cutoff, October 14, 2026? Machine form: `research/pothier/doctrines/PD-CS-ONE-PERSON.json`
(schema `pothier-family-doctrine/v1`, version 2). Leads are proposals for the owner; they change no status and no count.

## Conclusions

The doctrine proposes a `no` lead for **141** members and leaves **874** `open`. It proposes no `yes` lead, because
nothing in force today rests on any member: no statute, regulation or current official record cited by the project
shows a member's command operating on October 14, 2026, and absence of a revocation is not evidence of force.

The 141 `no` leads rest on three kinds of basis.

1. **The life of the named person (99 members; branches B09-B13).** A one-person order permits one action for one
   named person (an appointment, reinstatement, transfer, promotion, classification or exemption) or designates one
   person. Its command is used up when the action is taken, and it cannot operate after that person dies. The
   longest verified human life is 122 years 164 days (Jeanne Calment, 1875-1997). So if the order's own text shows
   that the person was alive on some date X, the person died no later than X + 122 years 164 days; and if the text
   or a rule it cites shows the person was at least A years old on the order date D, the person was born no later
   than D minus A years and died no later than that birth bound + 122 years 164 days. The lead is `no` only when the
   bound falls before October 14, 2026 **on a fact quoted from the order or a cited rule**, never on an assumed
   adult age. The facts used are: the order is dated before May 3, 1904, so no age is needed (6 members: 2 whose
   held text is the order, 4 whose held text is the Civil Service Commission's account of it or a damaged scan); the
   persons had reached a statutory retirement age, of which the lowest is 62 (5 members); the candidate was past the
   65th-birthday bar of the postmaster examination order (16 members); the text states the person's age or an age
   limit the person exceeds (5 members); the text states that the person was employed, appointed or serving on or by
   a date before May 3, 1904 (67 members, each read; quotes in Appendix A). Whether and when the action was taken
   stays unknown: these leads say the order ended within an interval, not when.
2. **Own terms (31 members; B03-B03e, B05-B08c).** Designations and permissions for a stated period (two or four
   years, ten days, one year from July 1, 1926, five years from March 31, 1922, or to July 31, 1935) end on their own
   terms (9). Two orders only revoke other orders and were spent on issue (coordinator ruling P1: EO 6179-A and
   EO 3523). Twenty orders only amend another order, a proclamation or a Civil Service Rule and merged into their
   parents on issue (ruling P2: their text continues as part of the parent until the parent ends; the parent's
   lifecycle carries it).
3. **A later instrument whose words reach the member (11 members; B01-B02b, B01b-B01i).** EO 5371 revokes EO 5332 by
   number; EO 6179-A revokes the appointments EO 4528 and EO 5058 authorized, naming each by date, person and
   department; EO 1074, EO 3075 and the order of July 27, 1921 revoke EO 1010, EO 2917 and EO 1692 by date and exact
   subject; EO 5197-A, 5638, 5855 and 7251 supersede the radio frequency orders EO 4846-A, 5197-A, 5638 and 6472 by
   number; and Public Land Order (PLO) 369 revokes EO 2247 by number, as the Bureau of Land Management's official
   table of Public Land Orders states it.

The 874 open members are open for stated reasons. 548 are orders for a named person (a few for two to nine named
persons) whose text fixes no age as a number and no presence before May 3, 1904 (B99). 74 are designations of named
officers without a stated term (B23). 73 have a held text that is not the member's own order or lacks its command
(B20; 70 of them are Commission-report slices that carry a neighbouring order of the same date). 65 are class orders,
general authorities and rule instruments typed as one-person waivers (B22), and 5 more are special rules of 1900-1903
(B04), all for PD-CS-RULES. 44 are outside the family (B21). 25 are orders for a stated number of specified persons
without a bound for every person (B27). 21 may concern minors (messengers, boys, girls, apprentices; B26). 16 are
land-patent signer designations (B24) and 3 are retirement class orders (B25).

The engine flags **2 contradictions**, both explained in section (c): neither changes its lead.

**What this doctrine does with the earlier work.** It reuses TR-CS-WAIVER and TR-RETIREMENT-EXEMPTION (reviewed
research patterns), the cs-waiver research report of 2026-10-28 (four outcomes; Civil Service Commission reports do
not record use; no general rewrite ends a waiver; latest-possible-death bound only on a quoted age fact) and the
Jacquard reviews. Of the 58 orders of this family that the Jacquard coordinator held back, 14 get a `no` lead on a
dated fact or an amending text of their own (EO 325, 957, 1953, 1961, 1983, 2009, 2083, 2140, 2151, 2165, 2197, 2244,
2389, 2447); the other 44 stay open. Of the 241 family members listed in the two Jacquard individual-review files,
35 get a `no` lead and 206 stay open, most because they are class orders, lists without a bound for every person,
rule instruments, or texts of a different order. The Jacquard L1 card's premise that "anyone the federal service
could employ in 1917 or earlier was at least 14 years old" is not used anywhere in this doctrine: no held source
states it, and the owner's evidence rule requires one.

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

- *Date before May 3, 1904 (minimum age 0).* Any person named was alive on the order date. An order dated on or
  before May 2, 1904 gives a bound on or before October 13, 2026.
- *Retirement age (minimum age 61).* The 1932-1933 exemptions under section 204 of the Act of June 30, 1932 name
  persons "who have reached" (or "during the current month" reach) "the retirement age prescribed for automatic
  separation". The Civil Service Retirement Act of May 22, 1920 sets 70, 65 for mechanics, carriers and post-office
  clerks, and 62 for railway postal clerks; the Act of May 29, 1930 keeps 62 as the lowest. 61 allows for "during
  the current month". The result holds for any minimum age of 29 or more (the latest member is dated January 5,
  1933), so the exact statutory figure cannot change it.
- *Postmaster examination age bar (minimum age 64).* EO 3455 (May 10, 1921) says "No person who has passed his
  sixty-fifth birthday ... shall be given the examination". Its only other limit is residence. The amendment of July
  27, 1921 changed only the residence date and kept the bar (S11), and EO 4538 (November 5, 1926) restated the order
  with the same bar and no other age limit (S12). An order waiving "that part of the Executive order of May 10, 1921,
  which pertains to the age limit", or waiving "the maximum age limit for entrance to the open competitive
  examination for postmaster" before June 22, 1928, therefore shows the candidate was past 65. The result holds for
  any maximum age of 24 or more (the latest member, EO 4807, is dated February 13, 1928). EO 4919 of June 22, 1928 is
  said to have raised the bar to the 68th birthday; it is not held, so later waivers (EO 5821, 1932) stay open.
  EO 4011, whose WPA summary says "without regard to age requirements", actually waives "the residence requirement"
  and is excluded (B20). EO 3855 waives "the age limit" for a postmaster examination at Stanwood, Iowa without
  saying which limit or citing the order of May 10, 1921, and EO 3455 covers only first-, second- and third-class
  offices; it stays open (B99).
- *Stated age or exceeded age limit.* The order says the person "is 58 years of age", is "52 years old", is "beyond
  the age limit of 45", exceeds "the maximum age limit of fifty years", or is barred by the rule that no person "who
  is over thirty-five years of age" may be certified. The minimum age is that figure. Statements that a person is
  "above the age limit" without the figure (EO 3148, 3512, 3942, 4437, 7109) do not fix an age.
- *Dated earlier presence.* The order says the person was appointed, employed or serving on or since a date before
  May 3, 1904, or for a stated number of years ending on a stated date. Being alive on that date needs no age at all.
  Each of the 67 members was read; the quote, the identity of the person (the quote names, or is the operative
  sentence about, the person in the member's WPA summary or the order's own heading) and the arithmetic are in
  Appendix A. A stated period qualified by "approximately" is shortened by five years (EO 3467). Statements about a
  husband, father or brother were rejected (for example EO 2946, 3926, 4770, 5056), as were "about" or
  "approximately" periods that could fall after 1903 (EO 3144, 5701), texts belonging to a neighbouring order (all
  of B20), and orders naming other persons without a bound (EO 1587).

**M2. EO 209 and the 1896 rules (not applied).** EO 209, effective April 15, 1903, promulgates new Civil Service
Rules "in lieu of those promulgated May 6, 1896, and the amendments thereof". It does not plainly reach special rules:
EO 250 had to revoke a 1902 special rule in 1904, so special rules outlived EO 209. The five special rules it might
reach (EO 130, 141, 142, 143, 203: rules for a class, a position or a list) are rule instruments, not one-person
orders, and no named person's death can end them. They stay `open` for PD-CS-RULES (B04), whose branch B07 holds the
same question open.

**M3. Express revocation or supersession (ends).** Under coordinator ruling P3 a later instrument ends a member only
if its words reach it, by number or by an express description that the member's own text, date or authority fits.

- EO 5371 (June 19, 1930): "Executive Order No. 5332, April 22, 1930, temporarily changing the order of precedence
  of the Assistant Secretaries of War is revoked." Date: 1930-06-19.
- EO 6179-A (June 16, 1933) revokes ten "appointments made by the President ... without regard to the requirements
  of the civil-service rules". Item (9) is "The appointment on October 23, 1926, of Mrs. Susan T. Waite as Clerk in
  the Bureau of Labor Statistics"; EO 4528, dated October 23, 1926, is the waiver for Susan T. Waite's reinstatement
  to a clerkship in that Bureau. Item (8) is "The appointment on February 26, 1929, of Mrs. Julia Behake to a
  classified position in the Department of Labor"; EO 5058, dated February 26, 1929, authorizes the appointment of
  Mrs. Julia Behneke to a position in the Department of Labor. In each case date, person and department agree (the
  name differs by a transcription letter in the second), and EO 6179-A's WPA summary lists both order numbers. Date:
  interval (order date, 1933-06-16], since use is unknown. The other eight orders the WPA summary lists are not
  members of the census.
- EO 1074 (May 21, 1909) revokes the "Executive Order issued under date of January 19, 1909, appointing the Council
  of Fine Arts"; EO 1010 is that order. Date: 1909-05-21.
- EO 3075 (April 16, 1919) revokes "The Executive Order of July 18, 1918, providing for the reinstatement of
  government employees who left the classified civil service to enter the military or naval service during the War
  with Germany"; EO 2917 is that order (a class order). Date: 1919-04-16.
- The order of July 27, 1921 (EO 3523 by its WPA summary) revokes the "Executive order of January 27, 1913, placing
  the position of female clerk to be designated by the President to sign land patents, $1,200, in the competitive
  classified service"; EO 1692 is that order. Date: 1921-07-27.
- EO 5197-A, EO 5638, EO 5855 and EO 7251 each say "This Executive order supersedes Executive Order No. ..." for
  EO 4846-A (and its amendment EO 4902), EO 5197-A, EO 5638 and EO 6472. Dates: 1929-09-30, 1931-06-08, 1932-06-06,
  1935-12-19.
- BLM's table of Public Land Orders gives PLO 369 (May 15, 1947, 12 FR 2038) as "revoking EO Nos. 2247, 2658, and
  3923; withdrawing lands for Agriculture experimental station". The member EO 2247 is the Alaska order reserving
  land "for the use of the Department of Agriculture for an agricultural experiment station"; the person in its
  record (Edith Gilbert Leadly) belongs to EO 2247-1/2, which the WPA summary runs into it. Date: 1947-05-15. The
  PLO's own text is not held.

**M4. Own terms (ends).** EO 1313 and 1753 designate Martin A. Knapp to exercise the chairman's powers "for a period
of two years" (ending 1913-03-04 and 1915-03-22); EO 7281 and 7426 designate the Federal Reserve chairman and vice
chairman "to serve as such for a term of four years" (ending 1940-02-03 and 1940-08-06); EO 4300 and 4639 designate
acting Farm Loan Commissioners "for a period of ten days from the date hereof" (1925-09-21; no later than
1927-05-06); EO 6725 appoints Science Advisory Board members whose "term of office ... shall terminate on July 31,
1935"; EO 4452 orders John G. Foster's "retention on active duty for a period of one year from July 1, 1926"
(1927-07-01); EO 3940 makes two named persons eligible to reenter the classified service "for a period of five years
from March 31, 1922" (1927-03-31).

Two orders only revoke and were spent on issue (ruling P1): EO 6179-A (June 16, 1933), whose consequences belong to
the orders it revokes, and EO 3523 (July 27, 1921), whose text revoking EO 1692 is held under EO 3521's file name;
the text held under EO 3523's own number is that day's amendment of EO 3455, which would merge on issue under P2, so
either reading gives the same lead and date.

Twenty orders only amend another instrument (ruling P2; `merged_into_parent_on_issue`; each carries the disclosure
"its text continues as part of the parent until the parent ends; the parent's lifecycle carries it"). EO 6142 amends
EO 5872 "so as to terminate the exemption of the said Pickens Neagle on May 31, 1933"; EO 7472 modifies EO 7140; and
a checked list (B03d) of 18 orders was read in full: amendments of the Civil Service Rules (EO 60, Indian Rule IV,
1895; EO 123, 158, 164, Rules IX and X of the 1896 rules; EO 2121, 2758, 4142, 6043, 7137, numbered rules of the
1903 rules), of other executive orders (EO 7304 of EO 6141; EO 2284 of EO 2263, adding four names; EO 2389 of the
Ferguson order of December 29, 1915; EO 7223 of EO 7195, "to read as follows"; EO 4902 of EO 4846-A; EO 6683 and
EO 6788 of paragraph (3) of EO 6474; EO 4192 of the Retirement Act exclusion of September 24, 1920), and of a
proclamation (EO 3992 of Proclamation 1684). Orders that amend and also add a provision of their own (for example
EO 3398, which also says the incumbent does not acquire status; EO 5545, which also lets occupants be classified;
EO 7228, which also classifies positions; EO 1582, which also authorizes fourteen named appointments; EO 7384, which
also appoints the persons it adds) are not on this list.

**M5. General rewrites of the Civil Service Rules (no end; recorded so that nothing relies on them).** EO 7916
(1938), EO 8743 (1941), EO 9830 (1947) and EO 10577 (1954) revoke only listed orders and schedules and list no
one-person waiver; the Act of March 27, 1922 and EO 9830 section 1.1(b) recognize status granted by executive order.
Under the evidence rule a later general rule ends an order only if something shows it extinguished that order, so
none of these is an end (finding of the 2026-10-28 research report, adopted here without change).

**M6. EO 3461 (May 16, 1921) (not applied).** It revokes "all Executive orders and amendments to the civil service
rules authorizing appointments, promotions, or removals without full compliance with the civil service laws and
rules, because of war emergencies existing at the time" and then lists orders by number. The held copy stops at
item 27, so the length of the list is not verified; all listed items seen are class orders, and whether a
one-person waiver resting on war work falls under the general clause is a reading the machine cannot apply safely.
No branch uses it.

**M7. Abolition by name of a body the member created (not applied).** EO 7065 (effective at the close of business
on June 15, 1935) abolishes "The National Resources Board and the advisory committee established by Executive Order
No. 6777". EO 6777 also established a technical committee, which EO 7065 does not name, and abolished two other
bodies. Ruling P7 ends a member only when the abolished subject is its only operative content, so EO 6777 stays open
(B21) with June 15, 1935 recorded as a candidate end.

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
| S11 | Order of July 27, 1921 amending EO 3455 (EO 3521 by its WPA summary), CSC 38th Annual Report (FY1921), printed p. 123 | yes, filed under EO 3523's number (the two texts are swapped) | `jobs/csc-annual-reports/output/texts/EO_3523.txt`, sha256 dc1bb823791f9461fd312e394200a5a76446a28b76ca6b03d99c9a76e29002e2 | "No person who has passed his sixty-fifth birthday, or who has not actually resided within the delivery of such office for two years next preceding the date of examination" | B10: the bar survives the July 1921 amendment |
| S12 | EO 4538 (Nov. 5, 1926), Presidential postmasterships | yes | `jobs/app-executive-orders/output/texts/executive-order-4538-presidential-postmasterships.txt`, sha256 2f83ff37bab84412b7c23d57d2d133ae5c54ee44d17688187994933b8f3a7f60 | same phrase as S11 | B10: the bar in force for EO 4595 and EO 4807 |
| S13 | EO 1074 (May 21, 1909) | yes | `jobs/wikisource-texts/output/texts/EO_1074.txt`, sha256 e09f563b157cd9f53c4c5236fb9ffae203868abfca7aca46a46fcef4ebb2d725 | "Executive Order issued under date of January 19, 1909, appointing the Council of Fine Arts, and requiring plans to be submitted to such Council, etc., is hereby revoked" | M3 for EO 1010 |
| S14 | EO 3075 (Apr. 16, 1919) | yes | `jobs/wikisource-texts/output/texts/EO_3075.txt`, sha256 637a86afcc8a642877cad0df838bdd4ee3c8cb68503f810cb6badf61c7f927c8 | "The Executive Order of July 18, 1918, providing for the reinstatement of government employees who left the classified civil service to enter the military or naval service during the War with Germany" | M3 for EO 2917 |
| S15 | Order of July 27, 1921 revoking the order of Jan. 27, 1913 (EO 3523 by its WPA summary), CSC FY1921 report p. 123 | yes, filed under EO 3521's number | `jobs/csc-annual-reports/output/texts/EO_3521.txt`, sha256 825a5f5467c11ef700d45f4b83ba8e278996fcfd17c3e24a388a6790c13c0719 | "placing the position of female clerk to be designated by the President to sign land patents" | M3 for EO 1692; P1 for EO 3523 |
| S16 | EO 5197-A (Sept. 30, 1929) | yes | `jobs/app-executive-orders/output/texts/executive-order-5197-assignment-frequencies-government-radio-stations.txt`, sha256 0a6bfcfde0c89cc4fb1c582e9d77c79b94ebc866e05a0ad4338d141aa68106fb | "This Executive Order supersedes Executive Orders No. 4846-A, March 30, 1928" | M3 for EO 4846-A |
| S17 | EO 5638 (June 8, 1931) | yes | `jobs/app-executive-orders/output/texts/executive-order-5638-assignment-frequencies-government-radio-stations.txt`, sha256 5c35f2adad2d69c91ca09a6bf77c918b284dc7fbbc5c8791d44d7ee0cdd804ca | "This Executive order supersedes Executive Order No. 5197-A, September 30, 1929." | M3 for EO 5197-A |
| S18 | EO 5855 (June 6, 1932) | yes | `jobs/app-executive-orders/output/texts/executive-order-5855-assignment-frequencies-government-radio-stations.txt`, sha256 168ec2c7cebedb85302575a1e8e9db2d3b75ef0000ad1e09163a7572224e510a | "This Executive order supersedes Executive Order No. 5638, June 8, 1931." | M3 for EO 5638 |
| S19 | EO 7251 (Dec. 19, 1935) | yes | `jobs/app-executive-orders/output/texts/executive-order-7251-assignment-frequencies-government-radio-stations.txt`, sha256 6dc3e7ce79a6895d64bc095280be0969b7d8c616ad2354e7939096ede4397250 | "This Executive Order supersedes Executive Order No. 6472 of December 2, 1933." | M3 for EO 6472 |
| S20 | BLM, Table of Public Land Orders 1-694, entry for PLO 369 | yes (parsed table) | `jobs/shepard-citations/output/PLO_TABLE.csv`, sha256 1317b2b261b1ee30c0305a90ea76e142b0d155d89bb6cdb7bc506b4f1632640c; BLM PDF https://www.blm.gov/sites/blm.gov/files/uploads/programs_lands-and-realty_land-tenure_withdrawals_public-land-orders_1-694.pdf | "revoking EO Nos. 2247, 2658, and 3923" | M3 for EO 2247 (finding aid, not the PLO's text) |
| S21 | PLO 369 (May 15, 1947), 12 FR 2038 | no (Federal Register issue date unverified) | https://www.govinfo.gov/app/collection/fr/1947 | (to acquire) | text of the revocation of EO 2247 |
| S22 | EO 7065 (May 22, 1935, effective June 15, 1935) | yes | `jobs/app-executive-orders/output/texts/executive-order-7065-creating-the-national-resources-committee.txt`, sha256 705eaaf04b1630ae454ff8f43efa23c66d82de421680f9d5b7f5aa778562f864 | "The National Resources Board and the advisory committee established by Executive Order No. 6777, dated June 30, 1934, are hereby abolished" | M7 (no member ended) |

Sources read for the mechanisms that are not ends (M5, M6) are those of the 2026-10-28 research report
(`research/excavator/claude-cs-waiver-research-2026-10-28/REPORT.md`: EO 7916, 8743, 9830, 10577 in the repository;
EO 3461 held only to item 27 at `jobs/csc-annual-reports/output/texts/EO_3461.txt`, sha256 636711b09cca359afcd8bfb3160718611ece8bf958c0570bdfc9590b466c560d).
Held: S2-S6 (S6 as printed in the Commission's report), S9, S11-S20, S22. To acquire: S1, S7, S8, S21 (and the
Statutes at Large page of S6). S10 is each member's own text.

## (c) Decision procedure

Branches are tried in order; the first whose conditions all hold decides. Counts are from
`python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-CS-ONE-PERSON.json --hints` on 2026-11-06
(1,015 members; 141 decided; 2 flagged by the contradiction check, explained below the table). Every `no` lead also
carries the engine's automatic gaps: unheld sources (S1, and S7, S8, S21 where used), and the order text's grade when
it is a transcription or an unauthenticated scan.

| Branch | Members | Lead | Basis and date rule | Conditions (plain words) |
|---|---:|---|---|---|
| B01 | 1 | no, ACT | EO 5371 revokes EO 5332; fixed 1930-06-19 | member is EO 5332 and has the held revocation edge |
| B02 | 1 | no, ACT | EO 6179-A item (9) revokes the Waite appointment; interval (1926-10-23, 1933-06-16] | member is EO 4528 and its text names Waite |
| B02b | 1 | no, ACT | EO 6179-A item (8) revokes the Behneke appointment; interval (1929-02-26, 1933-06-16] | member is EO 5058 and its operative sentence is in its text |
| B01b | 1 | no, ACT | EO 1074 revokes EO 1010; fixed 1909-05-21 | member is EO 1010 and its text creates the Council of the Fine Arts |
| B01c | 1 | no, ACT | EO 3075 revokes EO 2917; fixed 1919-04-16 | member is EO 2917 and its operative sentence is in its text |
| B01d | 1 | no, ACT | the order of July 27, 1921 revokes EO 1692; fixed 1921-07-27 | member is EO 1692 and its text places the patent-signing clerk's position in the classified service |
| B01e-h | 4 | no, ACT (`expressly_superseded`) | superseded by number: EO 4846-A 1929-09-30, EO 5197-A 1931-06-08, EO 5638 1932-06-06, EO 6472 1935-12-19 | member is the named order and has a held supersession edge |
| B01i | 1 | no, ACT | PLO 369 revokes EO 2247 (BLM table); fixed 1947-05-15 | member is EO 2247, has the held revocation edge and its text reserves the experiment-station land |
| B03 | 1 | no, TERM (`merged_into_parent_on_issue`) | only amends EO 5872; order date 1933-05-23 | member is EO 6142 and the amending sentence is in its text |
| B03b | 1 | no, TERM (`spent_on_issue`) | only revokes other orders' appointments; order date 1933-06-16 | member is EO 6179-A and its revoking sentence is in its text |
| B03c | 1 | no, TERM (`merged_into_parent_on_issue`) | only modifies EO 7140; order date 1936-10-15 | member is EO 7472 and its modifying sentence is in its text |
| B03d | 18 | no, TERM (`merged_into_parent_on_issue`) | only amends another order, a proclamation or a Civil Service Rule; order date | checked list (M4), each anchored by its own amending clause |
| B03e | 1 | no, TERM (`spent_on_issue`) | only revokes EO 1692; order date 1921-07-27 | member is EO 3523 and its WPA summary describes the revocation |
| B04 | 5 | open (`retype_PD-CS-RULES`) | special rules of 1900-1903, not one-person orders | dated 1896-05-06 to 1903-03-19 and held text says "Special Rule" or amends a numbered rule (after B03d has taken the pure amendments): EO 130, 141, 142, 143, 203 |
| B05 | 4 | no, TERM | designation for a stated number of years; order date plus the period | text designates a person "for a period of" or "for a term of" N years, not an order establishing a body: EO 1313, 1753, 7281, 7426 |
| B06 | 1 | no, TERM | ten days; fixed 1925-09-21 | EO 4300 |
| B07 | 1 | no, TERM | at most ten days; interval to 1927-05-06 | EO 4639 |
| B08 | 1 | no, TERM | stated end; fixed 1935-07-31 | EO 6725 |
| B08b | 1 | no, TERM | one year from July 1, 1926; fixed 1927-07-01 | EO 4452 and its retention sentence |
| B08c | 1 | no, TERM | five years from March 31, 1922; fixed 1927-03-31 | EO 3940 and its eligibility sentence |
| B09 | 5 | no, TERM (life) | named persons at retirement age; minimum age 61; interval (order date, 1994-06-18] | text: persons who "have reached" or "reach the retirement age prescribed for automatic separation": EO 5896, 5921, 5946, 5954, 5988 |
| B10 | 16 | no, TERM (life) | candidate past 65 under the postmaster examination order; minimum age 64; interval (order date, 1986-07-27] | text waives the part of the order of May 10, 1921 "which pertains to the (maximum) age limit" (or says the candidate is "over 65 years of age"), or, before June 22, 1928, waives "the maximum age limit for entrance to the open competitive examination for postmaster": EO 3602, 3717, 3730, 3735, 3776, 3780, 3784, 3790, 3792, 3822, 3823, 3835, 3840, 3850, 4595, 4807 |
| B11 | 5 | no, TERM (`hand_checked_dated_fact`) | stated age; interval (order date, 2008-11-27] | checked list, anchored by the exact age phrase of Appendix A: EO 3378, 3499, 3856, 4118, 5084 |
| B12 | 2 | no, TERM (life) | dated before 1904-05-03, minimum age 0; interval (order date, 2026-01-09] | waiver or designation with named persons, an operative "may be reinstated/appointed..." or "designate the following named persons", no class or list language: EO 162, 226 |
| B12b | 4 | no, TERM (life) | dated before 1904-05-03, minimum age 0; interval (order date, 2026-07-22] | checked list of orders for named persons held as the Commission's narrative or a damaged scan, each anchored by its own sentence: EO 221, 223, 234, 251 |
| B13 | 67 | no, TERM (`hand_checked_dated_fact`) | dated presence before 1904-05-03; interval (order date, 2026-03-11] | checked list, anchored by the exact dated-fact sentence of Appendix A |
| B20 | 73 | open | identity or command not in held text | listed members: neighbour-order texts (EO 1912, 3433, 3511, 4431 and 66 further Commission-report slices such as EO 2190, 3458, 3459, 1978, 1979), a Wikisource disambiguation page (EO 335), a misdescribed summary (EO 4011), an unbounded second person (EO 1587) |
| B24 | 16 | open | land-patent signers | type `patent_signing_designation` |
| B21 | 44 | open (`retype_other_family`) | outside the family: PD-LAND-WITHDRAWAL or PD-NATIONAL-FOREST (land, districts), PD-ADMIN (bodies, boats, radio, bonds, property, patrols), PD-CS-RULES (Retirement Act class exclusions), PD-WAR-EMERGENCY (relief, CCC) | designations or retirement orders whose WPA summary is about land or revenue districts, boats, radio, bonds, bodies established or abolished, naval surgeons, emergency conservation work, regulations, class exclusions, property (tolerating words the OCR ran together); waivers naming no person about land |
| B22 | 65 | open (`retype_PD-CS-RULES`) | class orders, general authorities, rule instruments (PD-WAR-EMERGENCY for 1917-1921 war authorities) | waiver typed, and the WPA summary opens with a class, a rule, a schedule, a position or an official authorized to act, or the text speaks of "all/any/such persons", "in like circumstances", "on a list"; an empty named-persons field alone does not qualify |
| B27 | 25 | open (`named_persons_list_unbounded`) | lists of specified persons without a bound for every person | waiver typed, and the WPA summary opens with a number of persons or employees, or speaks of "the N persons named", or the text of "the following-named persons" |
| B23 | 74 | open | designations without a stated term | remaining `personnel_designation` |
| B25 | 3 | open (`retype_PD-CS-RULES`) | retirement class orders | remaining `retirement_exemption` |
| B26 | 21 | open | possible minor | WPA summary or title describes the appointee as a messenger, boy, girl or apprentice, or the operative sentence appoints, promotes or transfers the person to or from a messenger or apprentice position; mentions of the person's children do not count |
| B99 | 548 | open | one-person waiver, no age fact as a number, no dated presence before 1904 | catch-all |

Evidence gaps on every life-of-person branch: use of the permission is unknown (the NARA St. Louis service record
card, or the Official Register of July 1 in odd years to 1921, would show it); the bound rests on S1, which is held
only on the web until acquired. On B13 several texts are Commission report prints without a signature line (S9 says
the reports print the orders in full), and the verified list is closed: any member whose held text or identity
changes must be re-read. EO 2159 has no date in the member record (its held scan is dated April 6, 1915 and numbered
2159), so its lead interval has an empty lower end; EO 4304 and 4509 carry only a year. On B09 the orders name
several persons; each reached retirement age, so the bound covers all of them. On B12b the command's own words are
not held: EO 221, 223 and 234 are held as the Commission's account of the order, and EO 251's scan is readable only
at "Matthew D. MeCarthy maybe transferre[d]"; EO 251's date is the census date, and its bound (2026-07-22) falls
before the cutoff only if the order was signed on or before May 2, 1904. On B10, EO 4807 does not state the class of
The Dalles post office; EO 4538 governs first-, second- and third-class offices, and the lead holds for any maximum
age of 24 or more.

**Checked lists and their anchors (B03d, B11, B12b, B13).** These branches decide members named by instrument id
after reading. Each branch's text condition is one pattern made of the exact quoted sentences of its members, so a
member passes only if its held text contains one of them. On 2026-11-06 each of the 94 listed members matched exactly
one quote, and each quote matched exactly one member, its own; a replaced or shortened text that loses its sentence
falls through to a later branch. The shared pattern would let a member pass on a neighbour's sentence only if that
sentence came to appear in its text; the per-member check is re-run whenever a held text changes.

**Contradiction check: 2 flags, neither changes its lead.**

- EO 123 (B03d, `no` on 1900-01-15) carries four held "amendment" edges from EO 12585 (1987) and EO 12692 (1989).
  Their quotes cite "Executive Order No. 123G2" and "Executive Order No. 123 45", OCR forms of EO 12362 and EO 12345;
  they do not act on EO 123.
- EO 6683 (B03d, `no` on 1934-04-19) carries two held "amendment" edges from EO 6788 (June 30, 1934), which amends
  "Paragraph (3) of Executive Order No. 6474 ... as amended ... by Executive Order No. 6683". That is an amendment of
  the parent paragraph as EO 6683 left it, which is what ruling P2 expects: EO 6683's text lives in EO 6474 and the
  parent's lifecycle carries it.

The engine does not flag ending edges on `no` or open leads. The held ending edges on members that are not used are
these, and none reaches its member: EO 2 (EO 10859 and EO 6527 match only a footnote numeral "2"); EO 2680 (PLO 1542
revokes a power-site order of the same date, August 13, 1917); EO 3638 (EO 4020 revokes the Alaska Peninsula
fisheries order of the same date, February 17, 1922); EO 4118 (EO 4801 on Canal Zone bicycles, a date match);
EO 6101 and EO 6106A (EO 6147 supplements them and revokes EO 6131); EO 6980C (EO 7759 mentions it and revokes
EO 7024-B and EO 7129-A); EO 6777 (M7). Partial revocations (`partial_revocation`) on EO 293, 944, 1781, 1913, 2729,
3148 and 4091 are land orders of the same date or number in BLM's tables; no lead rests on a partial edge.

## (d) Members the procedure cannot decide

874 members stay open.

- **548 orders for a named person with no age fact as a number and no dated presence before 1904 (B99).** The
  permission certainly ended when used or at the person's death, but the held text shows neither date and gives no
  quoted fact bounding the death before October 14, 2026. Most are 1910s-1930s appointments of widows, temporary
  employees and named specialists; a few name two to nine persons (for example EO 415, 938, 944, 1148, 4789). For an
  order dated D, the bound falls before the cutoff only with a minimum age greater than the time from May 3, 1904 to
  D (more than 14 years for an order of May 1918, more than 18 for May 1922, more than 33 for May 1937). Any one of
  three kinds of evidence would decide a member:
  1. the civil-service rule, Commission regulation or statute fixing the minimum or maximum age for entrance to the
     position's examination, in force on the order date, where the order leaves that examination in place or waives
     a stated limit (an order that waives the examination or "the civil-service rules" generally sets the age limit
     aside with it) and the person is not a preference claimant. Rule V, sec. 5 of the rules (numbered sec. 6 in the
     FY1922 printing), printed in the held Commission reports (FY1914 p. 76, FY1915 p. 69, FY1918 p. 51, FY1922
     p. 49), lets the Commission "change by regulation the existing age limits for entrance to the examinations" and
     exempts preference claimants; the reports print some limits (for example FY1918 p. 111, a postal examination
     barring a person "under 18 years of age or over 50 years of age"). The source that would make this route
     machine-applicable is the Commission's published age limits per examination (its Manual of Examinations and the
     annual reports' examination tables); no exact URL for a digitized Manual was found, so it is not in
     FETCH_PROPOSED. EO 4919 (June 22, 1928) would decide EO 5821, a 1932 waiver of the maximum age for postmaster;
  2. an Official Register entry (all employees, July 1 of odd years to 1921) or another record dating the person's
     presence before May 3, 1904;
  3. the NARA St. Louis service record card (birth, action and separation dates; about $20 each).
- **74 designations without a stated term (B23)**, mostly Rev. Stat. sec. 179 designations of a named solicitor,
  assistant secretary or general "to act as Secretary during the absence of the Secretary", and appointments to New
  Deal boards. They lasted while the absence lasted or until superseded and ended at the latest with the designee's
  tenure or death, but no held field gives the designee's age or separation. Their dates are public (biographical
  directories, agency histories) and could be acquired per person.
- **73 identity or text failures (B20).** The held text is another order's (most are Commission-report slices that
  begin at a neighbouring order of the same date; the member's own order may follow on the same page), a disambiguation
  page, a misdescribed summary or an order with an unbounded second person. They need the order's own text
  (Commission report page, archival scan). The list comes from comparing the person named at the start of each WPA
  summary with the first 1,200 characters of the held text; a swap in a member whose summary does not open with a
  name is not detected.
- **65 class orders (B22), 5 special rules (B04), 44 orders of other kinds (B21), 3 retirement class orders (B25).**
  These are X1 misclassifications, each lead naming the family that should decide it: the death of a named person
  cannot end an authority over a class, a list, a position or future persons. Several have plain own-terms or
  revocation leads a future doctrine can use (for example EO 5062, an airspace closure from March 2 to March 6, 1929;
  EO 715 and 983 were already shown revoked by EO 9830 in the 2026-10-28 report; EO 6777's Board was abolished by
  EO 7065).
- **25 lists of specified persons (B27).** Each acts for several persons, often named in the text; the order is spent
  only when every person's permission has ended, and no held fact bounds every person's death. A dated fact for every
  person, or the list's own terms, would decide it.
- **21 possible minors (B26).** Messenger boys and girls and apprentices may have been children; the coordinator's
  Jacquard holds of this kind stay open except those whose text dates earlier service (EO 957, 2009, 2140, 2447) or
  that turned out to be other kinds of order (EO 5150, a reinstatement with 1902 service).
- **16 land-patent signers (B24).** Personal designations of General Land Office clerks; later designations of
  another "regular" clerk suggest supersession, but no held text says so. Acquire the clerk's separation date or the
  statute governing the patent-signing secretary (Rev. Stat. sec. 450 and its successors; current law is 43 U.S.C.
  15). The position-classification order of this kind, EO 1692, is decided by its express revocation (B01d).

## Points for the coordinator

1. **Re-typing.** 117 members in B04, B21, B22 and B25 are not one-person orders; each lead names the family that
   should decide it. Members decided here although outside the one-person kind (EO 1010, 1692, 2247, 2917, the radio
   orders, and the B03d amendments) are decided by an express instrument or by rulings P1 and P2, the same rules
   other families apply.
2. **Checked lists (B03d, B11, B12b, B13).** Lead kinds `merged_into_parent_on_issue`, `hand_checked_dated_fact`
   and `life_of_person_bound`; the anchors are shared patterns with a verified one-to-one match (section (c)).
3. **Identification by date, person and position.** B02 and B02b rest on EO 6179-A naming each appointment by date,
   person and department rather than by order number; B01b, B01c and B01d rest on revocations naming the order by
   date and exact subject.
4. **Swapped texts.** The held texts of EO 3521 and EO 3523 (both July 27, 1921) are swapped; B01d, B03e and the B10
   source S11 read them that way, and the dates do not depend on the swap. A page check of the FY1921 report, p. 123,
   would confirm it (FETCH_PROPOSED).
5. **A possible further route for New Deal designations.** Appointments to bodies established under Title I of the
   National Industrial Recovery Act (for example the bituminous coal boards, EO 6512A, 6560A, 6560B, 6578A) may end
   with that Title under section 2(c) as PD-CLASS-EVENTS applies it (ruling P7 or P8); this doctrine does not apply
   it, because whether each board was established under Title I was not checked.

## Appendix A. Per-member facts for B11 and B13 (checked by reading on 2026-11-05 and 2026-11-06)

"Born no later than" is the quoted date (for a period of N years ending on a date, that date minus N years; for a
year without a day, December 31 of that year; for a month without a day, the last day of the month) or, for an age,
the order date minus the age. "Latest possible death" adds 122 years 164 days. Every quote names, or is the
operative sentence about, the person in the member's WPA summary or in the order's own heading. EO 2951, 3548, 4304
and 4509 have only a year in the member record and EO 2159 has no date; their held texts are dated September 4,
1918, 1921, September 18, 1925, September 15, 1926 and April 6, 1915.

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
| EO:2151 | 1915-03-23 | "appointed substitute carrier in the Oakland office on September i, 1902" | alive on 1902-09-01 (OCR 'i' for '1') | 1902-09-01 | 2025-02-12 |
| EO:2159 | (none; text 1915-04-06) | "Mr. Campbell was appointed a clerk in the Railway Mail Service on October 29, 1887" | alive on 1887-10-29 | 1887-10-29 | 2010-04-11 |
| EO:2165 | 1915-04-13 | "Mrs. Ramsay was appointed a gold worker in the Government Printing Office, September 28, 1903" | alive on 1903-09-28 | 1903-09-28 | 2026-03-11 |
| EO:2197 | 1915-05-14 | "He has been employed intermittently since Sep- ember 9, 1902" | alive on 1902-09-09 | 1902-09-09 | 2025-02-20 |
| EO:2244 | 1915-09-08 | "Mr. Potter was appointed a substitute carrier in the Jersey City, N. J., post office on September 15, 1896" | alive on 1896-09-15 | 1896-09-15 | 2019-02-26 |
| EO:2447 | 1916-08-31 | "Mr. Braxton served as messenger in the office of the commissioner of railroads from 1892 to 1899" | alive on 1892-12-31 | 1892-12-31 | 2015-06-13 |
| EO:2853 | 1918-04-30 | "Ernest L. Harris, of Illinois, who entered the Consular Service of the Government in 1898" | alive on 1898-12-31 | 1898-12-31 | 2021-06-13 |
| EO:2936 | 1918-08-14 | "Tenney is a graduate of Dartmouth College and he has lived in China for thirty-two years" | alive on 1886-08-14 | 1886-08-14 | 2009-01-25 |
| EO:2951 | 1918 | "Mr. MacDonald entered the insular civil service in January, 1902" | alive on 1902-01-31 | 1902-01-31 | 2024-07-13 |
| EO:3096 | 1919-06-12 | "second deputy comptroller in 1885" | alive by 1885-12-31 | 1885-12-31 | 2008-06-12 |
| EO:3114 | 1919-07-16 | "Brough’s experience of 29 years in the manufacture of ammunition" | alive on 1890-07-16 | 1890-07-16 | 2012-12-27 |
| EO:3175 | 1919-11-22 | "R. Stone Jackson may be appointed as clerk in the Federal Board for Vocational Education, on the basis of his more than 25 years’ experience" | alive on 1894-11-22 | 1894-11-22 | 2017-05-05 |
| EO:3343 | 1920-10-20 | "long and faithful service of James J. Haney as assistant messenger and chief messenger in the Department of Justice since 1876" | alive on 1876-12-31 | 1876-12-31 | 1999-06-13 |
| EO:3432 | 1921-04-14 | "Mr. Mitchell was regularly employed in the Coast and Geodetic Survey from August 22, 1898" | alive on 1898-08-22 | 1898-08-22 | 2021-02-02 |
| EO:3460 | 1921-05-16 | "Mr. Owen was appointed a letter carrier on May 12, 1890" | alive on 1890-05-12 | 1890-05-12 | 2012-10-23 |
| EO:3467 | 1921-05-20 | "Wells had served for approximately 25 years in the navy yard, New York, and was discharged on February 20, 1914" | served about 25 years ending 1914-02-20; read as at least 20 years (five years allowed for "approximately"); the unadjusted reading, 1889-02-20, gives 2011-08-03 | 1894-02-20 | 2016-08-02 |
| EO:3479 | 1921-06-07 | "Mr. Kimberlin served as rural carrier at McCordsville, Ind., from August 1, 1902" | alive on 1902-08-01 | 1902-08-01 | 2025-01-12 |
| EO:3490 | 1921-06-13 | "Mr. Morgan was appointed a letter carrier in the New York, N. Y., post office in 1873" | alive on 1873-12-31 | 1873-12-31 | 1996-06-12 |
| EO:3516 | 1921-07-18 | "Mr. Hall was first appointed in the postal service in 1888" | alive on 1888-12-31 | 1888-12-31 | 2011-06-13 |
| EO:3533 | 1921-08-11 | "Mrs. Latta before her marriage served in the Post Office Department from March 1, 1899" | alive on 1899-03-01 | 1899-03-01 | 2021-08-12 |
| EO:3548 | 1921 | "Mr. Artemus A. Rowe, formerly a post-office inspector, who entered the Postal Service in May, 1890" | alive on 1890-05-31 | 1890-05-31 | 2012-11-11 |
| EO:3587 | 1921-12-12 | "Mr. Bryant was appointed as a clerk in the Le Roy, N. Y., post office May 1, 1900" | alive on 1900-05-01 | 1900-05-01 | 2022-10-12 |
| EO:3606 | 1922-01-05 | "Mr. Hamlet was appointed originally on October 3, 1882, in the Interior Department" | alive on 1882-10-03 | 1882-10-03 | 2005-03-16 |
| EO:3677 | 1922-05-20 | "He was appointed in the Railway Mail Service September 27, 1889" | alive on 1889-09-27 | 1889-09-27 | 2012-03-09 |
| EO:3695 | 1922-06-20 | "Appointed Secretary of Legation at Seoul, Korea, April 24, 1901" | alive on 1901-04-24 | 1901-04-24 | 2023-10-05 |
| EO:3713 | 1922-07-31 | "Vallone’s services were discontinued on January 31, 1916, under charges without sufficient evidence, after a service of more than 22 years" | alive on 1894-01-31 | 1894-01-31 | 2016-07-13 |
| EO:3937 | 1923-12-19 | "Mr. Frank E. McMillin, who served as railway mail clerk, post-office inspector, assistant postmaster at Boston, Mass., and chief post-office inspector from September 5, 1890" | alive on 1890-09-05 | 1890-09-05 | 2013-02-16 |
| EO:3959 | 1924-02-16 | "where he had served since 1887" | alive by 1887-12-31 | 1887-12-31 | 2010-06-13 |
| EO:4016 | 1924-06-03 | "Julius G. Lay was appointed in the Consular Service on Septem- ber 1, 1893" | alive on 1893-09-01 | 1893-09-01 | 2016-02-12 |
| EO:4039 | 1924-06-27 | "Mr. Sullivan was appointed to this position by the Attorney General on July 14, 1897" | alive on 1897-07-14 | 1897-07-14 | 2019-12-25 |
| EO:4122 | 1925-01-10 | "Mr. Kellogg has been in the classified service since 1895" | alive on 1895-12-31 | 1895-12-31 | 2018-06-13 |
| EO:4304 | 1925 (text 1925-09-18) | "from May 7, 1898, to the present time" | alive on 1898-05-07 | 1898-05-07 | 2020-10-18 |
| EO:4357 | 1925-12-15 | "Mrs. Margaret C. Gates, a Spanish war emergency clerk, who served more than seven years in the Post Office Department and was classified as a per- manent clerk by the act of April 28, 1902" | alive on 1902-04-28 | 1902-04-28 | 2024-10-09 |
| EO:4367 | 1926-01-19 | "Miss Hall has served satisfactorily as postmaster at Medical Lake for 33 years" | alive on 1893-01-19 | 1893-01-19 | 2015-07-02 |
| EO:4376 | 1926-02-01 | "Stanton resigned without prejudice as quarterman and master boat builder in the navy yard at Puget Sound, Wash., after 27 years of service, on May 14, 1919" | alive on 1892-05-14 | 1892-05-14 | 2014-10-25 |
| EO:4379 | 1926-02-04 | "She was employed in the Bureau of Engraving and Printing and the office of the Treasurer of the United States from July 13, 1899" | alive on 1899-07-13 | 1899-07-13 | 2021-12-24 |
| EO:4480 | 1926-07-17 | "Mrs. Byrd served in the Bureau of Engraving and Printing from January 5, 1882" | alive on 1882-01-05 | 1882-01-05 | 2004-06-17 |
| EO:4509 | 1926 (text 1926-09-15) | "Mr. Ernest H. Hubbard served as office deputy United States marshal, Indian Territory, from July 1, 1900" | alive on 1900-07-01 | 1900-07-01 | 2022-12-12 |
| EO:4541 | 1926-11-13 | "served in the Bureau of Engraving and Printing as a classified employee from November 9, 1901" | alive on 1901-11-09 | 1901-11-09 | 2024-04-21 |
| EO:4563 | 1927-01-12 | "was a classified employee in the post offices at Savannah and Denver from August 26, 1902" | alive on 1902-08-26 | 1902-08-26 | 2025-02-06 |
| EO:4742 | 1927-10-12 | "Mr. FitzSimons resigned without prejudice from the position of assistant engineer on August 31, 1920, after almost continuous service which began in 1902" | alive on 1902-12-31 | 1902-12-31 | 2025-06-13 |
| EO:4743 | 1927-10-14 | "Mr. Griffin was originally employed under the Naval Establishment, on July 3, 1893" | alive on 1893-07-03 | 1893-07-03 | 2015-12-14 |
| EO:4769 | 1927-11-26 | "service of Mrs. Capron with the Red Cross and as a welfare worker at home and abroad, both in peace and in war, from the relief work in Cuba in 1899" | alive on 1899-12-31 | 1899-12-31 | 2022-06-13 |
| EO:4793 | 1928-01-13 | "Mr. Baine was continuously employed in the com- petitive classified service as an Inspector under the Post Office Department from July 1, 1902" | alive on 1902-07-01 | 1902-07-01 | 2024-12-12 |
| EO:4794 | 1928-01-13 | "her service extending from 1891 to 1905" | alive by 1891-12-31 | 1891-12-31 | 2014-06-13 |
| EO:4871 | 1928-05-03 | "From 1898 until 1911 Mr. Dudley was in the competitive classified service" | alive by 1898-12-31 | 1898-12-31 | 2021-06-13 |
| EO:4906 | 1928-06-06 | "Mrs. McLaughlin was employed in the Government Printing office from January 11, 1892" | alive on 1892-01-11 | 1892-01-11 | 2014-06-24 |
| EO:5020 | 1929-01-02 | "Mr. Brown served in the Government Printing Office in various positions for more than forty-one years, being dropped on account of reduction of force, March 27, 1923" | alive on 1882-03-27 | 1882-03-27 | 2004-09-07 |
| EO:5061 | 1929-02-27 | "Mr. Marsh was a classified employee from 1893 to 1914" | alive on 1893-12-31 | 1893-12-31 | 2016-06-12 |
| EO:5075 | 1929-03-04 | "Mrs. Stuart was in the competitive classified service from July 1, 1902" | alive on 1902-07-01 | 1902-07-01 | 2024-12-12 |
| EO:5128 | 1929-05-27 | "Mr. White, a veteran of the Spanish and World Wars, was a civilian employee of the United States military government in Cuba from 1898 to 1901" | alive on 1898-12-31 | 1898-12-31 | 2021-06-13 |
| EO:5135 | 1929-06-12 | "Mr. Liscombe rendered very satisfactory service in the Office of the Supervising Architect from 1902 to 1919" | alive on 1902-12-31 | 1902-12-31 | 2025-06-13 |
| EO:5150 | 1929-07-05 | "She was appointed and served thru competitive examination as printer's assistant, from June, 1902" | alive by 1902-06-30 | 1902-06-30 | 2024-12-11 |
| EO:5269 | 1930-02-01 | "Jose T. Casanovas, employed in the Quartermaster Corps of the Army in Porto Rico since 1898" | alive on 1898-12-31 | 1898-12-31 | 2021-06-13 |
| EO:5285 | 1930-02-25 | "loyal and efficient service for the United States Government in the Philippines since August 13, 1898" | alive on 1898-08-13 | 1898-08-13 | 2021-01-24 |
| EO:5286 | 1930-02-25 | "H. Percival Dodge was appointed in the Diplomatic Service on February 16, 1899" | alive on 1899-02-16 | 1899-02-16 | 2021-07-30 |
| EO:5501 | 1930-12-02 | "Mrs. Eva MacFate, who served in the Bureau of Engraving and Printing, under the name of Eva C. Small, by appointment from the skilled-laborer register, from September 16, 1896" | alive on 1896-09-16 | 1896-09-16 | 2019-02-27 |
| EO:6058 | 1933-03-01 | "Barber served in the Treasury Department under her maiden name from December 5, 1899" | alive on 1899-12-05 | 1899-12-05 | 2022-05-18 |

Bounds for the pattern branches (computed the same way): B09 (minimum age 61) EO 5896 1994-01-09, EO 5921
1994-02-26, EO 5946 1994-04-29, EO 5954 1994-05-09, EO 5988 1994-06-18. B10 (minimum age 64) from EO 3602 1980-06-10
to EO 4807 1986-07-27 (EO 4595 1985-08-08). B12 (minimum age 0) EO 162 2024-07-06, EO 226 2026-01-09. B12b (minimum
age 0) EO 221 2025-12-14, EO 223 2025-12-24, EO 234 2026-02-07, EO 251 2026-07-22.
