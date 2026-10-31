# Jacquard lot rules, 2026-10-31

Each lot below is a group of pre-1937 executive orders that X1 typed alike and that have no provisional status yet.
Under the owner ruling of 2026-10-31 (`research/readiness/owner_rulings/2026-10-31-jacquard-and-working-texts.md`),
a lot's provisional NO statuses may be adopted when an independent reviewer upholds every order in a random sample
of 59 (or every order, in a lot of 80 or fewer), with planted errors mixed in. These cards state, for each lot, why a
member order has no legal effect today and what disqualifies a member. They were written before any review and are
not changed during review.

## The question every review answers

On the project's legal cutoff, **October 14, 2026**, does the order's own command still operate? **NO** means it does
not. A consequence that the command produced and that outlived it (an appointment made, money paid, a sale
completed, a penalty incurred) is an accrued effect of that action, not continuing effect of the order, and does not
make the answer YES. The status is a provisional AI status hypothesis; it is not a finding about the exact date the
order ended and confers no certification.

An order is **upheld** for its lot only when all of these hold:

1. **Identity.** The text is the claimed order: its number or date (or both) in the text agree with the claimed
   number and date, or, for an unnumbered order, the text's date and subject agree with the claimed date and title.
   A text that is another order's, or that cannot be tied to the claimed order, fails.
2. **Fit.** The order's own text (not only its title) does what the lot describes, and nothing of another kind. A
   second operative clause of a different kind is an outlier.
3. **Basis.** The lot's reason for NO applies to this order on its own text.
4. **No outlier.** None of the lot's outlier conditions appears in the text.

Report `end_or_bound` as the latest date by which the command can no longer have operated (for example
"no later than 2025-06-13"), or a stated date in the order's own terms, with a few words of reason.

## L1. One-person civil-service waivers dated 1917 or earlier (type `cs_waiver_individual`, rule TR-CS-WAIVER)

**What the order does.** It authorizes one personnel action (appointment, reinstatement, transfer, retention,
promotion, or examination without regard to a civil-service rule) for one named person.

**Why NO.** The permission can be used only for the named person. Anyone the federal service could employ in 1917
or earlier was at least 14 years old, so was born no later than 1903. The longest verified human life is 122 years
and 164 days (Jeanne Calment, 1875-1997). A person born no later than December 31, 1903 died no later than about
June 13, 2026, before the cutoff. A permission whose only possible beneficiary has died cannot operate; any
appointment made under it ended with that person and is in any case an accrued effect of the appointment.
`end_or_bound`: "no later than 2026-06-13 (named person's latest possible death)", or an earlier stated date.

**Outliers (any one fails the order).** The order names more than one person, or a class of persons or positions
rather than a person; it amends a civil-service rule generally; it states or implies that the person is younger than
14; the order is dated after 1917; the order's text indicates a continuing authority beyond the one person (for
example "and any other person in like circumstances").

## L2. One-person exemptions from compulsory retirement (type `retirement_exemption`, rule TR-RETIREMENT-EXEMPTION)

**What the order does.** It exempts one named employee from compulsory retirement under the Civil Service Retirement
Act, for a period or without a stated period.

**Why NO.** The exemption can apply only to the named employee, who had reached or was about to reach compulsory
retirement age (62 at the youngest under the Act of May 22, 1920 and its amendments) when the order issued, so was
born no later than (order year minus 61). For an order of 1939 or earlier that person was born no later than 1878
and died no later than about 2001 under the 122-year, 164-day bound. A stated exemption period also ends on its own
terms. `end_or_bound`: the stated end date if earlier, else "no later than <birth bound + 122 years>".

**Outliers.** The order names more than one employee or a class; it amends the retirement rules generally; it does
anything besides exempting the named person (for example also changes pay or position); the text gives no basis to
tie it to a named individual.

## L3. Closings and mourning (type `closing_mourning`, rule TR-CLOSING-MOURNING)

**What the order does.** It closes executive departments or offices, or excuses employees, on a stated day or for a
stated period, or directs mourning, draping or half-staff display for a stated period.

**Why NO.** The command ends by its own terms at the close of the stated day or period, all before 1937.
`end_or_bound`: the last day of the stated day or period.

**Outliers.** No day or period is stated, or the period is open-ended ("until further orders"); the order sets a
recurring or standing closure (for example every Saturday afternoon, a new standing holiday); it does anything
besides closing or mourning (for example pay rules beyond the closure itself).

## L4. NRA code approvals (type `nra_code_approval`, rule TR-NRA-CODE)

**What the order does.** It approves a code of fair competition, an amendment to one, or an agreement, under Title I
of the National Industrial Recovery Act of June 16, 1933 (48 Stat. 195), usually with conditions.

**Why NO.** In A.L.A. Schechter Poultry Corp. v. United States, 295 U.S. 495 (May 27, 1935; held by the project with
its verification phrases found), the Supreme Court held the code-making delegation of Title I unconstitutional and a
code approved under it void. Title I by its own section 2(c) expired June 16, 1935, and the joint resolution of
June 14, 1935 (49 Stat. 375) continued the agency without code-making or enforcement. A code approval's command
therefore had no operative force after June 16, 1935 at the latest. `end_or_bound`: "no later than 1935-06-16".

**Outliers.** The order is an administrative order on NRA boards, staff or procedure rather than a code or agreement
approval; it rests on section 9(c) (petroleum; held invalid in Panama Refining Co. v. Ryan, January 7, 1935, an
earlier end that still yields NO but must be flagged); it is the President's Reemployment Agreement or another
section 4(a) agreement with its own terms; it rests on a statute other than NIRA Title I (for example Title II public
works, the Agricultural Adjustment Act, or the 1935 Bituminous Coal Act); the code later received statutory life.

## L5. Canal Zone orders (type `canal_zone`, high-confidence typing, rule TR-CANAL-ZONE)

**What the order does.** It governs the Canal Zone or the Panama Canal's operation: Zone government, laws,
regulations, courts, police, fees, tolls, lands, or employees' conditions of service there.

**Why NO.** The Canal Zone ceased to exist on October 1, 1979, when the Panama Canal Treaty of 1977 entered into force
and the Panama Canal Act of 1979 (93 Stat. 452; held by the project with its phrases found) took effect; transitional
U.S. jurisdiction over courts and police ended about March 31, 1982; and every remaining U.S. operating function
ended when the Treaty terminated at noon on December 31, 1999 and the canal passed to Panama. An order whose
operative content applies only within the Zone or to the U.S. operation of the canal has no object after that date.
Functions the Panama Canal Commission continued after 1979 are savings that ended no later than December 31, 1999.
`end_or_bound`: "no later than 1999-12-31", or an earlier date the text supports (own terms; 1979-10-01 for Zone
government; 1982-03-31 for courts and police).

**Outliers.** A one-person appointment (spent on issue: flag it, it belongs elsewhere); the order's content reaches
outside the Zone and the canal (for example general U.S. civil-service, pay or retirement rules that also mention
the Zone, or Panama Railroad corporate matters resting on corporate statutes); it creates or protects a continuing
individual right that a later statute preserved (for example annuities); the Zone mention is incidental.

## L6. Philippine orders (type `philippines`, rule TR-PHILIPPINES)

**What the order does.** It concerns the government or administration of the Philippine Islands under U.S.
sovereignty, or reserves land there.

**Why NO.** The United States recognized Philippine independence on July 4, 1946 (Proclamation 2695, under the
Tydings-McDuffie Act of 1934, 48 Stat. 456; Treaty of Manila, 61 Stat. 1174; the project's copies of these sources
are still pending fetch). An order resting on U.S. sovereignty over the Islands had no object after that date; later
U.S. use of bases rested on the 1947 Military Bases Agreement, a new basis. Orders on the Governor General and insular
administration ended earlier, at the Commonwealth's inauguration on November 15, 1935. `end_or_bound`: "no later
than 1946-07-04", or 1935-11-15 where the text concerns the Governor General's administration.

**Outliers.** The Philippine mention is incidental (for example a civil-service schedule covering many places); the
order concerns property the United States kept after 1946 under later agreements (embassy, cemeteries, veterans'
facilities); its content reaches beyond the Islands.
