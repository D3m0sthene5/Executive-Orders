# Hostile review of the Ulpian outer-bound rule (arm: Fable)

Reviewer: Claude Fable 5.2, separate context, 2026-11-10. Reviewed: `jobs/ulpian-outer-bound/RULE.md`, `ulpian.py`,
`research/ulpian/OUTER_BOUND.md`, `CLASS.csv`, `MEASURE.json`, the cited rulings and rule texts. I changed nothing
but this file. Tests: 17 pass when run directly.

**Held texts read: 48 order texts** (all 30 floor rows dated before 1918-05-03, in full; 18 tier-1 rows, first
1,300 characters, which is the whole order for 15 of them), plus excerpts of 6 Jacquard L1 orders and of EO 284,
94, 128, 209, 2661 and 3556A. The 25 post-1936 rows have no held text; I read 5 of their index titles only.

**Overall: do not put RULE.md v1 to the owner.** Tier 2 as drafted asks the owner for exactly what the pinned
ruling refused, on a source that does not govern the orders; the class definition in the hash-locked text does not
describe the rows the tool puts in the class; and two thirds of tier 1 fails the rule's own tests.

## Verdicts

| | Question | Verdict |
|---|---|---|
| A | Surviving consequences | **should-fix** (holds for permissions; wording wrong for status orders; rests on an unreviewed assessment) |
| B | Floor against the evidence ruling | **fatal** for tier 2 as drafted |
| C | Second clauses and rule amendments | **must-fix** (exclusion is the right policy; detection is not sufficient) |
| D | Predicate failure modes | **must-fix** (tier 1 bypasses the predicate: 65 of 99 rows fail the rule's own tests; 9 of 30 floor rows have a defect) |
| E | Arithmetic and lifespan source | **should-fix** (one-day shortfall in year-plus-day arithmetic; source not held; bucket bounds) |
| F | Jacquard L1 statuses | **must-fix** (the "42 rest only on the premise" count is a date test, not a reading) |
| G | Other regrets; alternatives | **must-fix** (replace the flat floor with a per-order required age shown by quoted facts) |

## A. Surviving consequences (should-fix)

For a true permission ("may be appointed") the treatment holds, and it is the owner's own (ruling of 2026-10-28,
point 1: separate the exhausted command from the surviving appointment). A survivor annuity, back pay or a
competitive status relied on later flows from the appointment and the retirement statutes, not from the order.
Three defects:

1. **The sentence is wrong for status orders in the class.** A retirement exemption, a "classification" (EO 5269,
   5285) and a retention do not authorize a separate act; the order itself is the continuing operative thing until
   separation or death. "Any appointment or status it produced is an accrued effect of the action, not of the order"
   misdescribes them. Death still ends them, so the status is unaffected, but the locked wording is false for
   those types.
2. **Ratifying orders are not permissions.** EO 223 "approves" appointments already made; EO 776 "confirm[s]" an
   earlier order. They were spent on issue. "Use unknown" is the wrong disclosure for them.
3. **The premise is unreviewed.** TR-CS-WAIVER `exceptions_savings` carries `"reviewed": false`. The rule builds
   on it without saying so.

The money screen misses "with pay", "salary from", "compensation" and "back pay"; a pay claim does survive to an
estate. I found no such case in the 48 texts (EO 2827 mentions the widow's compensation only as background).

## B. The 14-year floor (fatal for tier 2 as drafted)

1. **The source does not govern the orders.** The floor is quoted from the 1883/1884 rules (EO 284, 307) and the
   1897/1900 Rule V table (EO 94, 128). All 30 unlocked orders are dated 1907-1918, under the rules of 1903
   (EO 209), which replaced the earlier rules and carry no age table: "The Commission may, with the approval of the
   proper appointing officer, change by regulation the existing age limits for entrance to the examinations". The
   limits in force in 1907-1918 are Commission regulations, and none is held. OUTER_BOUND.md mentions this as a
   footnote ("could change limits by regulation"); it is the main point.
2. **The limit binds examinations, and these orders waive examination or the rules.** The author concedes this.
   The held rules also show the limit was never universal: EO 284 says "these limitations of age shall not apply
   to persons honorably discharged from the military or naval service"; EO 209 says persons preferred under
   R.S. 1754 "may be examined without regard to age".
3. **Some rows are outside the Civil Service Rules altogether.** EO 1892 and EO 2108: "this order waives the labor
   regulations and not the civil-service rules". EO 2827 is a "primer worker" at a torpedo station; EO 2793 and
   2835 are skilled laborers. No held rule sets any age for these.
4. **"The text would say if the person were a child" is an argument from absence**, and the screens are that
   argument in code. The type holds a "messenger boy" addressed as "Mr." (EO 2661).
5. **The ask itself breaches point 5** ("not ask [the owner] to choose a convenient historical answer to unlock
   ... rows"). Calling the floor "an owner-adopted rule ... not a fact shown by the order" concedes that it is
   disclosure standing in for evidence (point 4).

**What the author missed is that 14 is almost never needed.** The status turns on one fact: was the person born on
or before 1904-05-02? The age that fact requires on the order date is (order date minus 1904-05-02): 3.2 years for
EO 669, under 5 for the 1909 orders, 9 to 11 for 1913-1915. Only six of the 30 need more than 12 (EO 2433, 2729,
2781, 2793, 2827, 2835). TR-CS-WAIVER already requires stating "the smallest a_min at which the bound would fall
before that cutoff"; the rule ignores it and overclaims 14 for everyone. And the texts hold positive evidence
against infancy: EO 776 (a deputy collector separated "for more than one year" before October 1907), EO 2032
("electrical machinist ... from April 4, 1905": he would have been under one year old), EO 2126 (appointed
"through examination on June 26, 1905"), EO 1892 ("four little children"), EO 1064 (clerical services to a
Senator). That is evidence in the order, which point 2 allows; a flat floor from a superseded rule is not.

For the six that need 12 to 14, five are wives or widows, where TR-CS-WAIVER allows "only the lowest lawful
marriage age", and no held source fixes that at 14. Those stay open on the evidence held. EO 2835's margin is 23
days (bound 2026-09-21).

**EO 1865 needs no floor at all**: Solyom "served four and one-half years ... resigning on August 9, 1907", so he
was in service by early 1903, before 1904-05-03. Pothier B13 missed it.

## C. Second clauses and rule amendments (must-fix)

Excluding them is right. The status is for the order as a whole, so one living clause keeps it open, and a life
bound on the personal clause decides nothing. Do not split clause by clause inside this rule; an amending clause
belongs to the parent rule's lifecycle (Pothier P2). But the exclusion is only as good as detection:

- No screen for a second clause of another kind. EO 1017: "may be reinstated ... and will be suspended for sixty
  days from the date of his reinstatement" passes.
- No screen for "confirmed", "approved", "ratified" (EO 776 acts on another order and passes).
- No completeness test. EO 2063, 2793 and 2835 stop mid-sentence ("while employed as an unclassified", "in the
  discharge of his duties in that office on", "a former employee of the Govern-"). A clause that is not held
  cannot be excluded. Eighty characters is not a text.
- No conditional screen (EO 2544: "subject to such noncompetitive test of fitness as the Civil Service Commission
  may prescribe"; EO 4016, 5286: "when a vacancy shall occur"), although TR-CS-WAIVER lists conditional waivers as
  outliers.
- Tier 1 is not screened at all (D).

## D. Predicate failure modes (must-fix)

**Tier 1 bypasses the predicate.** `candidates()` marks every Pothier B09-B13 lead `in_class` before the date,
person-count, surname and screen tests run. Re-running the tool's own tests on the 99 `existing_quoted_fact` rows:
**65 fail at least one** (35 have a parsed person count other than 1: 25 with 0, 9 with 2, 1 with 4; 5 have no
exact date; the rest hit a screen). OUTER_BOUND.md says 370 orders "pass the predicate"; at most 246 were tested.
The 25 post-1936 rows have no held text, while RULE.md section 1 requires every condition "on its own held text".

**RULE.md section 1 does not describe the class.** "It names exactly one person" is false for most rows (husbands,
predecessors, officials are named). "Does not speak of ... a position" is false for nearly every row ("a
clerkship"). The age bullet excludes an order that "mentions ... an age limit without stating a figure", which is
exactly tier 1 branch B10 (EO 3602: "which pertains to the age limit"). Section 3's formula has only `a_min`; the
73 B12/B13 rows are bounded from a date the person was alive, which the rule text never states. `tag` would print
"at least quoted years old" for them.

Rows I think are wrong are listed at the end.

## E. Arithmetic and the lifespan source (should-fix)

- **One-day shortfall.** Calment lived 44,724 days. "Plus 122 years, plus 164 days" gives 44,723 days whenever the
  122-year span contains 1900 and only 29 leap days: 3,650 of the 9,131 order dates from 1880-01-01 to 1904-12-31
  at `a_min` 0. A person matching Calment's life in days outlives the stated bound by a day. No status flips (the
  short cases have bounds in 2002-2022; at the threshold the count is 44,724 or 44,725), but the published bound
  date is wrong for them. Define the term as 44,724 days, or add a day.
- Feb 29 handling and the strict `<` cutoff test are correct. Thresholds reproduce (1904-05-03, 1918-05-03).
- **Bucket bounds, not order bounds.** Every B13 row carries 2026-03-11, every B10 row 1986-07-27: Pothier's
  latest-member bound, not the order's own. Safe as an outer limit, false as "the latest possible death of {person}".
- **Source not held.** "Pothier S1 (web, to acquire)". The LongeviQuest 2023 and SSA "no survivors at 118-119"
  statements are unsourced in the repository; I could not check them. Hold a source or drop them. The Zak
  challenge only shortens the bound, as stated. Say plainly that "longest verified" is an empirical premise, not a
  legal maximum.
- **Dates.** EO 776's held text reads "April , 1908" (no day); the member date comes from elsewhere. Harmless
  there, but EO 2827 and 2835 sit 35 and 23 days inside the cutoff, so a wrong order date flips them. The lot
  should refuse a row whose held text does not show the date used.

## F. The Jacquard L1 statuses (must-fix)

"42 of 48 rest only on the premise" is not established. `jacquard_l1_check` "reads the order date only". Reading
six: EO 1918 (consul "from October 1, 1885"), EO 2648 ("as early as 1899") and EO 2235 (mother "now 74 years of
age") carry quoted facts; EO 2070 was "a messenger boy in the classified service" from 1908. The required age is
0.6 years for EO 276, at most 7 for 19 of the 42, above 12 for 5 (EO 2471, 2529, 2610, 2648, 2745). Eight hit an
Ulpian screen.

- **Floor approved:** the 34 that pass the screens stand, with claim wording restated to disclose the basis; the 8
  that hit a screen get an individual read. The owner approved the L1 card with the 14-year sentence on it, so say
  honestly that this ratifies it.
- **Floor declined:** do not withdraw 42 in bulk and do not leave them. Read each; restate those with a dated
  fact or a text that excludes the required age; return the remainder to undecided by a correction pull request.
- **Per-order required age (my recommendation):** the same reading, and most will stand on their own text.

Either way the L1 card's premise sentence must stop being cited as a source.

## G. Other regrets and the alternatives (must-fix)

- **Cost against yield.** A hash-locked owner ruling that narrows the pinned ruling buys 30 orders, of which one
  has no text, one is already tier 1, three are cut short and only six need the number 14.
- **Higher floors are worse.** 18 and 21 are contradicted by the held rules themselves (14-20 class, 16 postal)
  and unlock more rows on weaker ground.
- **"Civil-service waivers only" changes nothing**: all 246 floor rows already are.
- **Dangling references.** OUTER_BOUND.md cites `research/ulpian/REVIEW.md` and Kean ask
  A-20261110-ulpian-outer-bound; neither exists in this worktree (no `ulpian` string under HANDOFF or jobs/kean).
- **The real yield is tier 1's adoption route** (the 124), and it needs no new legal rule, but it must not ride on
  a rule text and a "passes the predicate" count that are untrue for it.

## Required fixes, ranked

1. Withdraw the flat floor. Replace with: per order, state the required age r = order date minus 1904-05-02, and
   quote the fact in the order that excludes an age below r; no fact, stay open. No owner ask is needed for that.
2. Run every tier-1 row through the same person, date, text and screen gates, or define tier 1 as Pothier's leads
   under Pothier's doctrine and stop calling it this class. Fix the 370 and 124 counts.
3. Rewrite RULE.md section 1 so it is true of its rows (beneficiary of the command, not "names"; position; age
   bullet against B10/B11), and add the alive-at-date bound to sections 2-3.
4. Add gates: text completeness, "Text not located", second clause, confirm/ratify, conditional, labor regulations.
5. Redo the Jacquard L1 measure by reading, and correct the "42" claim.
6. Term in days (44,724) or plus one day; per-order bounds; hold the lifespan source; refuse rows whose text does
   not show the date used.
7. Fix the end wording for status and ratifying orders; note that the accrued-effects assessment is unreviewed.
8. Remove or create the dangling REVIEW.md and Kean ask references.

## Rows from D that I found wrong

Floor rows (tier `floor_needed`, before 1918-05-03):

| Row | Quote | Reason |
|---|---|---|
| EO:2002 | "Text not located." | No order text held; passes on Wikisource page furniture and the title. |
| EO:1865 | "served four and one-half years ... resigning on August 9, 1907" | Already tier 1 (in service before 1904-05-03); misfiled as needing a floor. |
| EO:1017 | "and will be suspended for sixty days from the date of his reinstatement" | Second operative clause of another kind. |
| EO:776 | "is hereby, on the report of the Civil Service Commission, confirmed" | Acts on another order (October 30, 1907); ratification, not a permission; day of date illegible. |
| EO:1892 | "this order waives the labor regulations and not the civil-service rules" | Outside the Civil Service Rules; the floor's source cannot reach it. |
| EO:2108 | same sentence; "Mrs. John L. Evans" | Same; the person is named only through her husband. |
| EO:2063 | ends "while employed as an unclassified" | Truncated; a second clause cannot be excluded. |
| EO:2793 | ends "in the discharge of his duties in that office on" | Truncated. |
| EO:2835 | ends "a former employee of the Govern-" | Truncated; 23-day margin. |

Arguable: EO:2544 (conditional on a "noncompetitive test of fitness"); EO:2433 ("Mrs. Alexander Walters", named
only as a wife).

Tier-1 rows (`existing_quoted_fact`):

| Row | Quote | Reason |
|---|---|---|
| EO:162 | "I hereby designate the following named persons to serve as delegates ... to draw upon the Secretary of State for such moneys" | Reception committee for Prince Henry: several persons, a designation, money. Not this class. |
| EO:223 | "the names of 10 men whom it was desired to appoint" | Ten persons; held text is the Commission's account; approves appointments already made. |
| EO:226 | "Mrs. Annie M. West and Mrs. Sadie B. Yates may be reinstated ... respectively" | Two persons (parsed as one). |
| EO:3432 | "reinstatement of Hugh C. Mitchell ... April 14, 1921. Mrs. Martha Rich Smith may be appointed" | Slice holds two orders. |
| EO:5896 | "the following-named persons who have reached" | A list; same screen hits on EO:5921, 5946, 5954, 5988 (not read). |
| EO:3602 | "which pertains to the age limit" | Sound under Pothier B10, but excluded by RULE.md's own age bullet. |
| EO:4016, EO:5286 | "when a vacancy shall occur" | Conditional; Foreign Service reinstatement under the Act of May 24, 1924, not a civil-service rule. |

Tier-1 rows read and found to be one person, one clause: EO 325, 1863, 1983, 2009, 2083, 2151, 2197, 3460, 4794,
5128. The 25 `retirement_age_fact_title` rows could not be checked: no text is linked.

## Re-check of v2

Same reviewer, 2026-11-10, against RULE.md v2, `ulpian.py` v2 and the regenerated CLASS.csv (tier `quoted_fact`
40, tier `required_age_reading` 240). **Held texts read this round: 50** (all 40 quoted-fact rows in full; 10
tier-2 rows drawn at random, seed 7). Nothing edited but this section.

**Verdict: the lot of 40 is sound in substance. I would reject 1 row, send 3 to a page check for the order date,
and fix three sentences of RULE.md before it is hashed. OUTER_BOUND.md is still version 1 and must not go to the
owner as it stands.**

### 1. The 40 quoted-fact rows

Every one of the 40 has a single beneficiary and a single command; none carries a class, an office designation,
a money grant or a condition. In every row the quoted fact concerns the beneficiary, not a spouse or relative
(I checked the rows where a husband's service is also recited: EO 4379 "She was employed ... from July 13,
1899", EO 4541 "Mrs. Rooney, as Laura V. Walker, served ... from November 9, 1901", EO 4906, EO 6058), and
`born_by` follows from it. The thinnest margin is EO 2165 (appointed September 28, 1903; bound 2026-03-10).

Reject or hold:

| Row | Quote | Reason |
|---|---|---|
| EO:2853 | "may he re-instated as Consul General of Class five ... without regard to the Executive Order of June 27, 1906" | **Reject under section 1 as written.** Not a civil-service rule: it waives the consular-service order, and the post is a consular office, not a classified position. The fact ("entered the Consular Service ... in 1898") is good; the class is not. Either widen section 1 in terms or drop the row. |
| EO:4541 | "CALVIN COOL IDGE ... November 18, 1996"; "to the date of his death, February 7, 1928" | **Hold for a page check.** The row's date is 1926-11-13; the held text reads the 18th, and recites a death in 1928 in an order of 1926. The bound does not depend on it, but the order date and the text are not reconciled, and section 1 requires an exact date. |
| EO:3096 | "from $r,8o to 1 $89 ... 1June,'191." | **Hold for a page check.** The date line is unreadable and the service years are garbled; only "second deputy comptroller in 1885" is legible. The fact probably stands; the date is not shown by the text. |
| EO:4769 | "November 86, 1987" | Date line garbled (row says the 26th). Page check; otherwise sound ("relief work in Cuba in 1899"). |

Sound but outside the letter of section 2 (fix the text, keep the rows):

- EO 1961 ("an excellent record of 19 years"), EO 3114 ("experience of 29 years in the manufacture of
  ammunition"), EO 3175 ("more than 25 years' experience"): no "stated date" ends the period; `born_by` is the
  order date minus the years, which is right, but section 2 allows only periods "ending on a stated date". EO 3114
  and EO 4769 rest on experience and Red Cross work, not on being "appointed, employed or serving" under the
  Government.
- EO 3467: "approximately 25 years" cut to 20 is a convention, not evidence. Harmless here (bound 2016), but call
  it a convention.
- EO 5084: the "maximum age limit of fifty years" is measured at an examination closing April 5, 1929, eight days
  after the order. Immaterial (bound 2001).
- EO 4807 (B10) states no figure itself and depends on EO 3455 and 4538; section 2 says so. Fine.
- EO 3175 and EO 3606 contain no "without regard to" words at all. Still one permission for one person.

Order date shown in the held text: yes for 36; not legibly for EO 2853 ("3Q April, 1918"), 3096, 4541, 4769.

### 2. RULE.md v2 sections 1-3 and the 2026-10-28 ruling

No remaining conflict with the ruling for this lot: the event claimed within the interval (death, or earlier
exhaustion) is certain once the quoted fact holds, use is left open, and nothing is asked of the owner that
substitutes for evidence. Three inaccuracies in the text to be hashed:

1. Section 1 "without regard to a civil-service rule" excludes EO 2853 and does not describe EO 3175 or 3606.
2. Section 2 first bullet: add "or ending no later than the order date" and "experience or work" if EO 1961, 3114,
   3175 and 4769 are to stay.
3. Section 3 wording "whom its text shows alive on {born_by}" is false for the age-based rows (EO 3378, 4118, 4807,
   5084), where the text shows an age, not presence on that date. The retirement-exemption sentence and the
   `pothier_B12_a_min_0` basis describe no row in the lot (B09 and B12b are excluded; no B12 row survived).

### 3. Ten tier-2 rows (EO 2174, 2781, 3139, 3404, 4058, 4179, 4288, 4835, 5059, 6133)

All ten: one beneficiary, one command, complete text, no second clause or condition. The gates now catch every
floor-row defect I listed (EO 2002, 1017, 776, 1892, 2108, 2063, 2793, 2835, 2544). Two problems:

- **EO 1865 is still in tier 2** (required age 10). "Served four and one-half years ... resigning on August 9,
  1907" is a stated period ending on a stated date, exactly section 2. It belongs in the lot; the tool takes
  facts only from Pothier's appendix and so cannot see it. Other tier-2 rows may hide the same.
- **Tier 2 is a reading list, not a yield.** Required ages run to 30 (EO 6133, 1933, whose whole text is one
  sentence). Nothing in RULE.md says what fact excludes an age below r, so no status may be drawn from tier 2
  until that is written and reviewed. Do not report 240 as unlockable.

Over-exclusion is now heavy and safe: nine tier-1 rows I read as sound in round one (EO 325, 1863, 1983, 2083,
2151, 2197, 3460, 4794, 5128) are out on false screen hits or person-parse errors. They stay open; they are lost
yield for an individual-review pass.

### 4. Required fixes still open

- **OUTER_BOUND.md is unchanged version 1**: it still argues the 14-year floor, reports 370/124/246/30, and
  describes the predicate that no longer exists. RULE.md cites it as the research. Rewrite before any ask.
- `research/ulpian/REVIEW.md` and Kean ask A-20261110-ulpian-outer-bound still do not exist in the worktree;
  RULE.md cites both.
- The lifespan source is still not held (OUTER_BOUND.md: "Pothier S1 (web, to acquire)").
- Jacquard L1: JACQUARD_L1.csv now gives r and screen hits, which fixes the measure; the per-row reading and the
  correction of the "42 rest only on the premise" sentence (still in OUTER_BOUND.md) are not done.
- The 25 post-1936 retirement rows remain without held text (`needs_held_text`); correct, but section 1 and the
  wording still carry retirement language that no row exercises.
- Fixed: flat floor withdrawn; tier 1 gated; 44,724 days; per-order bounds; completeness, second-clause,
  ratification, conditional, labor-regulation and text-not-located gates; accrued-effects caveat in section 4.
