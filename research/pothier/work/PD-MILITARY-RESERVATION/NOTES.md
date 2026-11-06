# PD-MILITARY-RESERVATION working notes (2026-11-05)

## What was read

Project files:

- `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`, `jobs/pothier/pothier.py` (engine:
  condition semantics, date rules, contradiction checks), `jobs/pothier/held.py`.
- `research/readiness/type-rules/TR-MILITARY-RESERVATION.json` and `TR-LAND-WITHDRAWAL.json` (ending pattern,
  outlier conditions: residual reversions, Philippines and Canal Zone, territorial lands, surplus disposal).
- `jobs/x1-class-engine/data/EVENTS.json` and `jobs/x1-class-engine/output/EVENT_SOURCES_STATE.json`: events
  X1-E3 (Canal Zone), X1-E4 (Philippines) and X1-E5 (FLPMA) and the held texts they point to.
- `research/excavator/jacquard-2026-10-31/LOT_RULES.md` (lots L5 Canal Zone and L6 Philippines; the reasoning that
  later base use rests on a new agreement is taken from L6).
- `research/pothier/work/PD-MILITARY-RESERVATION/MEMBERS.csv` and the 316 records in `jobs/pothier/output/MEMBERS.jsonl`.
- Member texts read in full or in their operative part: EO 219, 220, 468, 483, 512, 515, 636, 645, 666, 683, 770,
  777, 796, 803, 807, 969, 1011, 1070, 1080, 1084, 1129, 1136, 1154, 1169, 1282, 1389, 1397, 1423, 1507, 1526, 1613,
  1697, 1920, 1948, 1962, 2136, 2143, 2187, 2377, 2405, 2517, 2521, 2563, 2622, 2624, 2704, 2772, 2825, 2869, 2879,
  2944, 2978, 3067, 3078, 3171, 3293, 3300, 3313-A, 3364, 3402, 3418, 3497, 3514, 3848, 3952, 4026, 4047, 4062, 4128,
  4131, 4272, 4282, 4393, 4661, 4684, 4689, 4697, 4760, 5044, 5119, 5254, 5405, 5637, 7049, 7127, plus the closing
  part of every member on branch B11 (55 texts) to look for provisos.
- Non-member texts: EO 4421 (`jobs/wikisource-texts/output/texts/EO_4421.txt`; revokes EO 1920 except a school
  reservation, so not used as a full end), EO 7320 and EO 9293 (`jobs/app-executive-orders/output/texts/`).
- Held statutes: Philippine Independence Act (secs. 5, 10), Proclamation 2695, Panama Canal Act of 1979 (secs. 3,
  1111, 1503-1504, 3304), FLPMA (secs. 701, 704 and the repeal table) at the paths in the doctrine JSON.

Web (read, not held):

- https://www.govinfo.gov/link/statute/61/1174 (Treaty of General Relations: signed July 4, 1946; ratifications
  exchanged and in force October 22, 1946; article I) and https://chanrobles.com/rpustreatyofgeneralrelations.htm
  (article I wording).
- https://www.law.cornell.edu/uscode/text/22/1392 (joint resolution of June 29, 1944, sec. 2, 58 Stat. 626).
- https://treaties.un.org/doc/Publication/UNTS/Volume%201280/volume-1280-I-21086-English.pdf (Panama Canal Treaty:
  in force October 1, 1979; art. I(1) terminates and supersedes the 1903 Convention; art. XI plenary jurisdiction;
  art. II termination at noon December 31, 1999; art. IV military rights by separate agreement).
- https://www.govinfo.gov/content/pkg/STATUTE-23/pdf/STATUTE-23-Pg103.pdf (Act of July 5, 1884, sec. 1).
- https://www.govinfo.gov/content/pkg/STATUTE-73/pdf/STATUTE-73-Pg4.pdf (Hawaii Admission Act sec. 5(c), 5(e)).
- https://www.law.cornell.edu/uscode/text/43/155 (Engle Act, Pub. L. 85-337, 72 Stat. 27).

## What was tried and rejected

- **Naval petroleum and oil-shale reserves.** No member's title, summary or text mentions petroleum or oil shale, so
  the Naval Petroleum Reserves Production Act and the Elk Hills and Teapot Dome sales were not researched.
- **Treating every transfer as spent on issue.** Rejected for transfers to another department for its continuing use
  (Treasury, Veterans' Bureau, Agriculture, Navy, Justice, Alaska Road Commission): the receiving department holds the
  land under the order until a later change, so those stay open. Transfers to the Interior Department for disposal
  under the 1884 Act, and restorations to the public domain or to a territorial or Philippine government, are treated
  as spent, because they end the reservation over the named lands.
- **Treating diminutions as spent.** Rejected when the text redefines the remaining reservation ("so that the
  reservation will include all public lands, and those only, within ..."; "the reservation as thus modified includes
  ..."), because the surviving reservation then rests on the diminishing order's description.
- **Using Wikisource "Revoked by" notes as ends.** Rejected: they are a mirror's editorial notes. Where the revoking
  order's own text is held, the pair became a C-branch; EO 1920's note proved partial on reading EO 4421.
- **A generic held-edge branch.** All ending edges on members (EO 2275, 2385, 3202, 3386, 3428, 4047, 4393, 5174,
  7407) are covered by specific C-branches with dates; the edges carry no date candidate except EO 7407's, so a
  generic `edge_date` branch would have produced unresolved dates.
- **EO 2879 (New Mexico artillery range).** EO 3078 and EO 3402 together relinquish most of its townships, but the OCR
  of EO 3402 garbles two township numbers, so a full relinquishment could not be confirmed; left open.
- **EO 4635, EO 4760, EO 3949, EO 2377, EO 1920.** Only partly ended by the later orders read; left on their own
  branches.
- **Philippine upper bound at the 1991-1992 base closures.** Rejected as the date rule because the Treaty of General
  Relations and the 1947 Military Bases Agreement replaced the reserving orders as the basis of U.S. use; noted in the
  B20 gaps as the owner's alternative, which does not change the `no` lead.
- **Place screens on the order text.** Rejected after test runs: EO 4282 (Fort Snelling) matched "Philippine" through
  a statute title in its text, and EO 7288 (Mayaguez) matched "Balboa" through a neighbouring order in its scan. The
  place screens now read only the WPA summary and the title.
- **A URL for EO 4131 at the American Presidency Project.** EO 4131 is not in the APP index, so no fetch was proposed
  for it rather than a guessed URL.

## Checks run

- `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-MILITARY-RESERVATION.json --hints` after each
  revision; final: 316 members, 159 decided, 0 contradicted.
- A script re-read every held source file named in the JSON, recomputed its sha256 and confirmed the pin phrase is in
  the file (all 29 held sources with pins passed).
- Date arithmetic for EO 5254: the 63rd day after December 31, 1929 is March 4, 1930; a 91-day period beginning that
  day ends June 2, 1930.
- Statutes at Large pages were read from the running heads of the held texts (48 Stat. 459 and 463; 90 Stat. 2786
  and 2792; 93 Stat. 455, 488 and 500).

## Time and effort

About three hours of agent time: one hour reading members and type rules, one hour on sources (held and web), one
hour building and testing branches (eight `try` iterations). The generator script used to write the JSON lived in
`/tmp` and is not part of the deliverable.

## Version 2 under the coordinator rulings (2026-11-05)

Applied `research/pothier/COORDINATOR_RULINGS.md`: B21 bound moved to 1999-12-31 (P5; the held Panama Canal Act has no
words ending the reservations earlier); B20 split into B20 (`no`, interval to 1947-03-26, for places not retained) and
B20r (`open`, 16 members at places listed in Annexes A and B of the 1947 Military Bases Agreement, read on the web at
the UNTS vol. 43 copy) after re-reading TM secs. 5 and 10(a)-(b), 22 U.S.C. 1392 (58 Stat. 626), Treaty art. I and the
agreement; B10 split into B10 (revocations, `spent_on_issue`, P1) and B10m (amendments, `merged_into_parent_on_issue`
with the P2 disclosure); B11 kind `spent_on_issue`; S-ORDER is now `member_text` (P6); B01 split into B01a-c naming
PD-ADMIN, PD-CS-RULES and PD-WAR-EMERGENCY. New counts: 143 `no`, 0 `yes`, 173 `open`. About 45 minutes.

## Version 3: revision after blind reviews A and B (2026-11-06, reviser)

Read: `work/AUTHOR_BRIEF.md`, `DOCTRINE_SCHEMA.md`, `COORDINATOR_RULINGS.md` (P1-P8), `work/REVISION_BRIEF.md`, the
v2 doctrine (.md, .json), this file, and `/home/claude/pothier-review/PD-MILITARY-RESERVATION-A/REVIEW.json` and
`-B/REVIEW.json`. The JSON is now generated by a script kept outside the repository (`/tmp/mr/gen.py`) from the v2
JSON; the .md was rewritten to stand alone.

Planted errors in the reviewed copies, ignored after checking that the real file is right: A R1 ("23 Stat. 130"; the
file has 23 Stat. 103), A R2 (B09 1930-04-01; the file has 1930-06-02), B R1 ("60 Stat. 1325"; the file has 1352),
B R2 (C22 1942-01-02; the file has 1943-01-02).

### What changed and why

- **B20 bound and the 1947 agreement (A R3, B R6, B R7, B R8; coordinator adjudication).** Read art. XXI and Note V
  in the 61 Stat. print (mirror at https://dheller.org/Timeline-files/US-Statutes/v61/treaties/Agreement-Philippines-1947.pdf,
  running heads 61 Stat. 4019-4036, T.I.A.S. 1775; art. XXI on 4028-4029, Note V on 4033) and in the UNTS vol. 43
  copy (art. XXI pp. 294-296, Notes V-VI pp. 309-310). Quoted art. XXI(1)-(2) and Note V in full in the JSON and .md.
  New branch B20p (open) for the Port of Manila reservation: EO 348-A, 1298, 2838, 3344, 3500, 5736 (adjudicated)
  and EO 4787 (its part II reserves Blocks 9 and 10 of plan of reclamation No. 1, Manila Harbor, the same reclaimed
  port land; A had asked for a check). EO 964 (Malate Barracks) is not port land and stays on B20. New branch B20n
  (open) for naval reservations outside the bases, which section 10(b) and Note V hold over; it has no member
  (every Philippine naval member is on B20r). For the remaining Army members on B20 the doctrine does not claim art.
  XXI(1) fails to reach them (whether an installation stood on a member's land in 1947 is not in the fields held);
  it bounds them instead, as ruling P5 allows ("an upper bound that the last such instrument fixes"): interval to
  1952-03-26. Reading: "such extension ... shall in no case exceed a period of three years" grammatically limits the
  extension, so two years plus at most three, counted from entry into force on 1947-03-26. Both reviewers read three
  years as the whole period (1950-03-26); that narrower reading and the Manila-city two-year limit (1949-03-26) are
  disclosed in the date-rule basis. The flat "July 4, 1946 for Army reservations" and "retained only the listed
  bases" are gone. S-JR1944 added to B20's sources (B R17). S-MBA1947 now cites 61 Stat. 4019 and arts. I, XXI,
  XXIX; S-PCT cites art. I (B R8).
- **Proclamation 2694 (B R9).** Verified by number, title, date and authority on the Truman Library copy
  (https://www.trumanlibrary.gov/library/proclamations/2694/designating-properties-suitable-diplomatic-and-consular-establishments);
  its closing part is on the held 60 Stat. 1352 page; opening page not verified. It designates diplomatic and
  consular properties and continues no military reservation; the B20 gap now says so.
- **Held whole-order revocations (A R5, B R4, B R5; REVISION_BRIEF point 3).** Every row was read in the held BLM
  tables (`jobs/shepard-citations/output/texts/blm/`), with its FR citation taken from the line after the row. New
  branches P01-P21: the 14 B33 members (EO 1238, 1262, 1315, 1450, 2131, 2233, 2295, 2353, 3684, 439, 4682, 4962,
  5251, 6851), the Alaska members EO 1248, 1557, 1920, 241, 2533, 4762, and two more found by scanning every BLM row
  for every family member number: EO 4449 and EO 5219, revoked "entirely" by PLO 1712 (their edges in MEMBERS did not
  carry that PLO). EO 241 and EO 439 are named by date only ("EO of Dec. 9, 1903"; "EOs of Apr. 12, 1906 ...
  entirely"); a date scan found no other family member of those dates, and the rows' states match (Alaska;
  Mississippi). P22: EO 3574 (B11 before) is revoked "entirely" by PLO 1712; its lead is the interval from its own
  date (P1) to the PLO. EO 1450 removed from the "may still stand" examples. C26 (EO 330-A by EO 432), C27 (EO 1237
  rescinded by EO 4204, held text read), C29 (EO 4671: EO 4814's held recital says EO 4716 "was issued, superseding
  said Executive Order No. 4671"; EO 4716's own held text is a "Corrected Copy" without the word, disclosed).
- **Others of the same kind.** Scanning family relinquishment texts for recited member dates and numbers found:
  EO 3056 (1919, held, not a member) transferring the Cotabato reservation (EO 1197, amended by EO 1338) and Torrey
  Barracks (amended by EO 483, EO 1364) to the Philippine government (C28; the Wikisource "revoked by EO 3056" notes
  pointed there); EO 1617 abolishing all of Camp Jossman "as ... modified by Executive Order dated November 22, 1909"
  (EO 1139, C31); EO 3464 placing under Interior exactly the 150 acres EO 1579 had retained (EO 1579, B12 before,
  C32); and EO 1096 superseding EO 1084 "as to hours of labor on Saturday" (C30, before B01a). EO 1628 (Fort Pikit,
  Fort Reina Regente) also appears in EO 3056, but the OCR gives its order's year as 1913 against EO 1628's 1912, so
  it stays on B20 with a disclosure. EO 2167, EO 4052, EO 5493 act on parts only.
- **Screen fixes.** EO 1397 out of B11: "shall be held in reservation" added to the retained-interest screen (B12,
  open). The bare phrase "held in reservation" was tried first and wrongly caught EO 1617 ("will no longer be held in
  reservation"), so the screen requires "shall be". EO 3402 and EO 5157 to a new id branch B11x (P1); the regex route
  was not used because a "reserved ... by E. O." exception would also have to be checked against every B20/B33
  summary. EO 5174 and EO 456 to a new id branch B10p (P2, dated 1929-08-21 and 1906-06-08); C07 deleted, C16 now
  EO 372-B only.
- **Year-only dates (B R13).** The generator adds a twin of every decided order-date or interval branch for each
  year-only member it receives (`B11-y1911` and so on), with the interval YYYY-01-01 to YYYY-12-31, or the class
  interval starting YYYY-01-01. Eight members.
- **Smaller items.** M3 "Version 1" wording (A R12); Limbones Island described as held on B20r by choice (A R11);
  S-PCA "establishes" narrowed to sec. 3(b)(1) as a rule of construction, sec. 1504(a)(1) added to the B21 gap
  (A R10); 1951 repeal of the 1884 Act added as a continuity note, source S-1951 (A R14); Engle pin changed to the
  phrase common to statute and Code with a note (B R15); C03 gap for the EO 5155 recital (A R8); B11 gap for EO 341-A
  / EO 477, EO 3080 / EO 5132 and EO 3418 / EO 4131 (A R13); B33 gap for the EO 2281 false edge and B20 gap for the
  EO 985 false edge (A R7, B R3).

### Findings not adopted, with reasons

- **A R6, second half (end EO 2879 on 1921-02-11).** EO 2879 reserved T. 20 S., R. 9 W.; T. 21 S., Rs. 8, 9, 10 W.;
  T. 22 S., Rs. 8, 10 W. EO 3078 relinquished T. 21 S., Rs. 8 and 9 W. EO 3402's only held text (ProQuest OCR) reads
  "T. 208., R.9 W,; T. 208. R, 10 W": the same "208." for both townships, so the OCR cannot show the second is
  T. 21 S. rather than T. 20 S. (which EO 2879 did not reserve). Left open; a clean copy of EO 3402 is in
  FETCH_PROPOSED.
- **B R14, second half (end EO 1437 by EO 3086).** EO 3086 transfers Regan Barracks "subject to such reimbursement
  and reservations as may be prescribed by the Secretary of War", a continuing clause; under the same test that keeps
  B12 open, the transfer is not a clean end. EO 1437 stays on the B20 interval, which covers 1919, with the proviso
  disclosed.
- **B R16 (route EO 1920 out of family).** Superseded: PLO 984 revokes EO 1920 as a whole, an end that holds in any
  family; the lead says EO 1920 is a Bureau of Education reservation, not a military one.
- **B R7 as a general rule.** Adopted for naval reservations (B20n). Not extended to Army reservations: Note V
  reserves the "adjustment of any rights and titles" to real property in the bases and in naval reservations outside
  them, a title question; it does not reserve possession or control of Army reservations outside the bases.
- **Both reviewers' 1950-03-26 reading of art. XXI(1).** Kept as the disclosed narrower bound; the lead uses the
  wider 1952-03-26 (reason above). The choice does not change any lead from `no`.

### Contradictions after revision

`try` reports 5: EO 2281 (false edge from EO 5590, a Montana petroleum reserve order of the same date), EO 2978
(EO 5155 recital misdescribing the EO 3067 tract), EO 3080 (EO 5132 restores another parcel), EO 3418 (EO 4131
recital confirming the transfer), EO 341-A (EO 477 redefines the 1869 Fort Bayard reservation). Each is explained in
its branch gaps and in the .md. EO 985's false edge (EO 10069, 1949) no longer flags because the B20 bound is now
1952-03-26; it is still disclosed. EO 3574's later edges (EO 4449, 4546, 5219) fall inside its new interval.

### For the coordinator

- PLO 1712 (1958) revokes EO 3574 "entirely" and EO 7049 "in part", although both only placed Alaska lands under
  Interior under the 1884 Act. BLM evidently treated such transfers as continuing withdrawals until disposal. Under
  P1 they are spent on issue and the B11 leads stand; if the owner reads them as lasting withdrawals, Alaska
  relinquishments on B11 need upper bounds.
- The art. XXI(1) reading (three years for the extension versus three years in all) sets the B20 bound at 1952-03-26
  or 1950-03-26.
- WebFetch of law.justia.com for the 1951 repeal needed an approval that was not answered; the S-1951 citation rests
  on the U.S. Code repeal note as shown in search results (openjurist, Justia, getpocketlaw titles: "Repealed. Oct. 31,
  1951, ch. 654, §1(114), 65 Stat. 706"); its opening page (701) is unverified.

### Checks run

`python3 -I jobs/pothier/pothier.py try ... --hints` after each change; final 316 members, 164 `no`, 0 `yes`, 152
`open`, 5 contradicted. A script re-read every held source (41), recomputed sha256 and found every pin and BLM row
pin. A script confirmed no `no` lead carries a bare-year date.

Time: about three hours (one reading reviews and sources, one on the Philippine agreement and the PLO tables, one
building, testing and writing).
