# PD-ADMIN working notes (2026-11-05)

## What I read

- Brief and schema: `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`; owner ruling
  `research/readiness/owner_rulings/2026-11-05-empty-status-history.md`; engine `jobs/pothier/pothier.py` (date rules
  have no regex extraction of an "until" date, so per-member fixed dates are separate branches keyed on instrument id
  plus a text regex that requires the stated date phrase).
- Type rules: `research/readiness/type-rules/TR-FUND-ALLOTMENT.json`, `TR-PROPERTY-TRANSFER.json`,
  `TR-OWN-TERMS-EXPIRY.json`, `TR-TAX-RETURN-INSPECTION.json`, `TR-CLOSING-MOURNING.json`.
- Jacquard: `research/excavator/jacquard-2026-10-31/LOT_RULES.md` (L3 closings) and its `INDIVIDUAL_REVIEW.csv` (29 L3
  failures: undated Labor Day orders, funeral-day orders, misclassified Civil Service amendments, unreadable scans);
  the w2 `INDIVIDUAL_REVIEW.csv` has no closing rows.
- Member texts: all 801 summaries; held texts in full or in their operative part for all closings, own-terms, tax,
  the territory reserves, single-day pay orders, fiscal-year allowance orders, and about 120 revoke/amend candidates;
  the acting orders for every held ending edge (EO 5376, 5207, 6005-A, 6612, 6562, 5952, 5605, 6913, 6776, 8714, 6550,
  9461, 6724, 6777, 6858, 7005, 7044) and the in-family revoking orders (EO 1706, 3583, 4158, 3261, 4021).
- Held statute: Tax Reform Act of 1976, `jobs/source-ladder/output/texts/queue_EO_10906_..._64c0b4c21d.txt`, lines
  8640-9916 (sec. 1202; 6103(a) at 90 Stat. 1667, 6103(g) at 1672, sec. 1202(i) at 1688, located by the page headers).
- Web: Cornell LII 43 U.S.C. 1618 (ANCSA sec. 19(a), source credit 85 Stat. 710); uscode.house.gov 31 U.S.C. 1502
  (derivation 63 Stat. 407, 68 Stat. 831); usc-cdn.house.gov Pub. L. 85-56 (truncated before titles XXII-XXIII; table
  of contents shows sec. 2307 "Outstanding rules, regulations, and orders"); a search for Rev. Stat. 3690 text (no
  primary result); a search for the 73d Congress second-session date (secondary only). uscode.house.gov failed for
  43 U.S.C. 1618 and 31 U.S.C. 1301.
- Kean was not run (the shell search of held sources with `jobs/pothier/held.py` covered the statutes needed).

## Tried and rejected

- Statehood, Philippine independence and Puerto Rico Constitution as class events: no member found that these reach
  by their terms (no Philippine member here; Alaska reserves are land withdrawals; PR orders are acting-judge
  designations).
- Fund-allotment lapse rule: rejected because availability depends on each appropriation item; act titles such as
  "Fourth Deficiency Act, fiscal year 1933" name a fiscal year but the funds ran longer. Only EO 2968A, whose own
  text limits use to "said fiscal year", is decided.
- Property transfers spent on issue: rejected to stay consistent with TR-PROPERTY-TRANSFER (end = delivery record).
- Land-office discontinuances as single acts: left open; the receiving district's extent continues to rest on them.
- Veterans' Benefits Act of 1957 as a repeal of the Veterans Regulations: not usable until sec. 2307 is read.
- Committee-life ends for tax inspection grants: each committee's resolution would be needed; the 1976 rewrite gives
  a sound outer bound instead.
- Held-edge revocations taken as given: EO 2525 (EO 5207 revokes only "as to the tract described"), EO 6126 (partial,
  "in so far as ... in conflict"), EO 6098 (amendment), EO 6514 (partial rescission), EO 1, 4, 13 (edges point to
  unrelated orders) were not used.
- EO 6221: event-relative date and the further deferral by EO 6624; left open.
- Encampment leave: the year-end bound is an inference and labelled so in the lead.

## Things noticed for other workstreams

- EO 3878, 4075, 4571 (typed fund_allotment) are Indian trust-period extensions (PD-INDIAN).
- EO 3885 (typed closing_mourning) is a military land withdrawal on Oahu; EO 1183's held text is EO 1182½.
- EO 5471, 6352, 7209 (typed closing_mourning) amend Schedule A of the Civil Service Rules; decided here as amend-only.
- EO 267's WPA summary says "until Feb. 2, 1904" for an order of July 30, 1904; the text is illegible.

## Version 2 (same day, under COORDINATOR_RULINGS.md P1-P6)

Applied the coordinator's message: B04 tax orders made `open` (1976 rewrite of sec. 6103 kept as a disclosed earlier
candidate end, P3; no member's own text states an end period, checked against TR-TAX-RETURN-INSPECTION); B07 ANCSA
leads re-based on the quoted class words with kind `ended_by_express_class_instrument`, fixed 1971-12-18; B01 kind
`spent_on_issue`, B02 kind `merged_into_parent_on_issue` with the P2 disclosure; encampment leave intervals now run
from the last named leave day to December 31 with the inference stated; misfiled members split into O01 sub-branches
naming their family; member texts cited as `member_text` (P6). New counts: 179 decided (`no`), 622 open, 0
contradicted. The version 1 generator in the shared `/tmp/pd/` was overwritten by another session; version 2 was
produced by editing the JSON with `/tmp/pd-admin/revise.py`.

## Effort

About three hours of agent time: roughly one hour reading member texts, one hour on sources and the web, one hour
building and testing the doctrine (generator kept outside the repository at `/tmp/pd/gen.py`; the JSON in the
repository is its output).

## Version 3 (2026-11-06, reviser after blind reviews A and B)

Read: `work/AUTHOR_BRIEF.md`, `DOCTRINE_SCHEMA.md`, `COORDINATOR_RULINGS.md` (P1-P8), `work/REVISION_BRIEF.md`, the v2
doctrine, these notes, `/home/claude/pothier-review/PD-ADMIN-A/REVIEW.json` and `-B/REVIEW.json`, the engine
(`jobs/pothier/pothier.py`: contradiction test flags living edges dated after a `no` lead's end). The JSON was edited by
`revise3.py` and `patch2.py` in a private `mktemp` directory (`/tmp/pdadmin-rev.*`), from a copy of v2 kept there.
Web: govinfo STATUTE-31-Pg877 (Spanish Treaty Claims Act: chapter 800, March 2, 1901, sec. 16 terms) and the OLRC copy
of Pub. L. 85-56 (title XXII begins 71 Stat. 157, title XXIII 71 Stat. 172; sec. 2307's page not reached).

### Planted errors ignored
A-R1 (EO 5605 effective "1931-01-07"), A-R2 (ANCSA "85 Stat. 701"), B-R1 (EO 6913 "1934-04-12"), B-R2 (ANCSA "Pub. L.
92-302"). The real file has 1931-07-01, 1934-12-04 and Pub. L. 92-203, 85 Stat. 688, 710; confirmed.

### Findings accepted and what changed
- EO 1987 (A-R3; coordinator): moved from B07 to new B03-22, `no`, ACT, 1924-07-03. Held EO 4044 restores all three
  reserves naming EO 1987; held EO 4055 vacated the restoration only for Chugach National Forest tracts and calls them
  released from the Bureau of Education reserve. B07 is now 4.
- Contradictions (A-R4, B-R4): the .md now states the count and explains every flag (12 after the changes below).
- EO 2686 (A-R5, B-R9; coordinator): B02 regex tolerates "amen~ded". EO 3283 removed from B02 to new open O03X
  (suspension until the Anthracite Coal Commission finished; event not dated). B02 list size now matches the text.
- EO 516 and EO 2525 (A-R6; coordinator): both amend-only, moved to B02 (P2). EO 492 keeps its end as amended by EO
  516; EO 2508 keeps the ANCSA end, which reaches EO 2525's text through it.
- EO 457 (A-R7, B-R5; coordinator): no interval is supported by the text (three months from an undated hiring; the
  appropriation named is not a period limit on the employment). Moved to O03X, open.
- Committee grants (A-R9, B-R14; coordinator): EO 3595 and EO 6603A now have their own B04 gap (no resolution named).
  I did not apply P4 to EO 3595: its content is a grant of access to a committee through its chairman, not one of the
  one-person acts P4 lists.
- EO 973 (A-R10, B-R17; coordinator): decided in new B08-973, 1908-11-25, reading disclosed (Wednesday + November +
  order date 1908-11-17; WPA summary agrees).
- (b) table (A-R8): rebuilt. Besides EO 6612 and 6776, EO 5376, 5605 (O07), 6562 (O08), 6913 (O06) and 1244 (O09) are
  also family members; the table now separates 15 outside acting orders from 14 member acting orders.
- Spanish Treaty Claims Act (B-R3; coordinator): chapter 800, verified on govinfo (web, not held). Each B05 basis now
  says the stated end is the latest end and why the period ran its length (the next order continues from its last
  day; sec. 16's early dissolution speaks only of the original two years). EO 1167 gap: no record of earlier
  dissolution.
- EO 330B and EO 980 (B-R6): kept as amend-only under P2 per the coordinator's adjudication; moved with EO 3723 and EO
  6885 (the other whole-text restatements) to new B02-TABLE, whose gaps disclose EO 1173/1333/5429 citing the restated
  text and the Wikisource note that EO 2043 superseded EO 980, plus the owner's alternative.
- P7 (B-R7; coordinator): B03-11, 13, 15 now `ended_by_express_abolition_of_its_subject`, mechanism M-ABOLISHED.
- EO 4698 (B-R8; coordinator): removed from B02 to new O01-PERSON (open, PD-CS-ONE-PERSON, P4). Same-kind check: the
  other B02 members carry no named-person content except the Commerce acting-secretary designation chain (EO 2186,
  2686, 3749), which the coordinator placed in B02 by its ruling on EO 2686.
- EO 6927 (B-R10): "none held" removed; the gap names the four held edges and why they are separate later delays.
- EO 292 and 749 (B-R11; coordinator): the v2 gap ("as in every legible member" starting March 2) was false. Now
  B05-292 (1905-09-02) and B05-749 (1908-09-02), fixed, with the reading disclosed; EO 674 ends 1908-03-02, EO 921
  starts 1908-09-02, and the WPA summaries agree.
- EO 1440 (B-R12; coordinator): interval 1930-06-23 to 1930-07-01, as B03-05.
- EO 6668 and 6669 (B-R13; coordinator): new B01-EFF, fixed 1934-03-28 (P1 stated effective date).
- EO 1 (B-R15; coordinator): kept in O01-CIVILWAR with an accurate description. I did not move it to O01-TEXT: the
  held text and member date agree (War Department EO No. 1 on political prisoners, 1862-02-14); the mismatch is with
  the WPA summary (Louisiana provisional court), and the gap asks which order the number denotes.
- Amend-only orders left open (B-R16): read EO 574, 3311, 3369, 4102 and the other 47 open members whose title or text
  says amended or modified. Added 18 to B02 (EO 552, 574, 3311, 3369, 3864, 4102, 4111, 4473, 5429, 7226, 7319, 7333,
  7347, 7371, 7433, 7446) and B02-TABLE (EO 3723, 6885). Not added: EO 3604A (prescribes an affidavit rule without
  amending words), 2226 and 2368 (add land), 4814 (redescribes a tract), 2013 (creates a board), 7003 (its amendment
  ends with a transfer of employees whose place in the amended text I did not confirm), 2802 and 3004 (modify a land
  withdrawal for named entries), 2362A (complete passport rules), 1096 (a superseding order), 7056 (designates a person).
- Pub. L. 85-56 pages (B-R18; coordinator): now 71 Stat. 83, title XXII from 157, title XXIII from 172, sec. 2307 page
  unverified (OLRC copy read on the web was truncated before title XXIII's text).

### Found in the new edge data (REVISION_BRIEF step 3)
Checked every held ending edge (revocation, supersession, rescission, abolition, termination, restoration) on every
member. New `no` leads, each on the acting instrument's own words: EO 1234 (EO 1244 rescinds the "Executive order of
August 4, 1910" by date and subject; interval because EO 1244's date line is OCR-damaged), EO 4703 (EO 4918), EO 6440
(EO 6746 "supersedes Executive Orders Numbers 6440, 6554, and 6622"), EO 2584 and 2597 (EO 3027's express class, "All
Executive Orders heretofore issued for the establishment of Defensive Sea Areas"), EO 2259 and EO 6587 (PLO 406, PLO
434 per the held BLM table; PLO texts not held, gap stated). Also EO 7321 (new B10): its authorization ran "pending the
promulgation of uniform regulations", and held EO 7409/7410 of 1936-07-09 promulgated them; the temporary regulations'
partial survival is disclosed as a surviving consequence.
Edges not used: EO 181, 235, 2043 (Wikisource editors' headers only; the orders' bodies have no supersession words);
EO 4773 (EO 10020 prescribes a new manual with a savings proviso, no revocation in terms: P3 candidate end); EO 306 (EO
311 is an unreadable scan; the revocation is in a Wikisource note); EO 328C (EO 4272 revokes EO 1147 in part;
misattributed); EO 2381 (EO 10047 restores one pier); EO 6514 (partial rescission); EO 7194 (a chairman replacement);
EO 6766 (EO 6898 recites the allocation); edges on EO 1, 4, 13 (unrelated orders).
EO 6512 moved from B06 to B02: EO 6561 of the deadline day amends "Executive Order No. 6512" and calls EO 6433-A "as
amended by Executive Order No. 6512"; as an own-terms deferral its end would have been carried past 1934-01-16 by that
amendment, while under P2 it merged into EO 6433-A on issue (as EO 516 does into EO 492).

### Result
`try`: 801 members; 205 decided (all `no`), 596 open; 12 contradiction flags, all explained in the .md (8 are P2
amendments acting on the parent: EO 330B, 980, 552, 6512, 6576, 7117, 7119, 7125; 4 are number-matched or separate
later orders: EO 1440, 6840, 6927, 921). FETCH_PROPOSED: STCC and Pub. L. 85-56 citations corrected, ANCSA note to 4
members, PLO 406, PLO 434 and a legible EO 1244 added.

Effort: about two hours of agent time (reviews and adjudications 30 min, member and acting texts 50 min, script and
runs 20 min, .md and notes 30 min).
