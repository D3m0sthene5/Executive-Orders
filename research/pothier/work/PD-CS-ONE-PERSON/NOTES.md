# PD-CS-ONE-PERSON: working notes (2026-11-05)

## What I read

- Brief and schema: `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`, `jobs/pothier/pothier.py`.
- Members: `research/pothier/work/PD-CS-ONE-PERSON/MEMBERS.csv`; full records in `jobs/pothier/output/MEMBERS.jsonl`.
  I read every member's WPA summary, the operative text of about 150 members in full, and machine-extracted snippets
  around years, ages, wars and retirement wording for all 1,015.
- Prior work reused: `research/readiness/type-rules/TR-CS-WAIVER.json`, `TR-RETIREMENT-EXEMPTION.json`; reviews
  `research/production/x1-2026-10-19/TR-CS-WAIVER_REVIEW_R5/R6/R7.json`; report
  `research/excavator/claude-cs-waiver-research-2026-10-28/REPORT.md`; Jacquard `LOT_RULES.md` (L1, L2),
  `jacquard-2026-10-31/INDIVIDUAL_REVIEW.csv`, `jacquard-2026-10-31-w2/INDIVIDUAL_REVIEW.csv`, `COORDINATOR_HOLDS.json`,
  `README.md` and the per-item reviews in `jacquard-2026-10-31*/reviews/*/batch-*.jsonl`; `jobs/namier/README.md` and
  the members' `name_later_hits`.
- Held primary texts opened and pinned: EO 209 (`jobs/wikisource-texts/output/texts/EO_209.txt`), EO 3455
  (`jobs/wikisource-texts/output/texts/EO_3455.txt`), EO 3461 (`jobs/csc-annual-reports/output/texts/EO_3461.txt`, stops
  at item 27), EO 6179-A and EO 5371 (APP transcriptions), EO 5872, 5896, 5912, 5921, 5946, 5954, 5988, 6142 (OFR and
  APP texts), the CSC FY1922 report pages (`jobs/numbered-early-orders/output/books/CSR_1922_pages.jsonl.gz`, printed
  p. 99, Retirement Act sec. 1) and FY1915 pages (printed pp. 7-8, "published in full in the appendix").
- Web (read, not held): Guinness "oldest person" page (122 years 164 days, Calment); govinfo 41 Stat. 614 (1920 Act,
  ages 70/65/62 confirmed), 46 Stat. 468 (1930 Act, 62 confirmed), 47 Stat. 382 (start page of the Act of June 30,
  1932; sec. 204's page not reached). Wikisource "Executive_Order_3461" does not exist (url_not_found).

## What I tried and rejected

- **A general minimum age of 14 (the Jacquard L1 premise).** No held or web source states it; the CSC could change age
  limits by regulation and a waiver could set them aside. Not used. Consequence: 585 post-1904 waivers stay open.
- **Position titles, "Mrs.", "widow of", professional or military rank as age facts.** Rejected under TR-CS-WAIVER
  (R6 wording); the family includes a messenger boy (EO 2661) and girl messenger (EO 3556A).
- **Namier name matches as age or use evidence.** Most non-adjacent hits are unauthenticated same-name matches (e.g.
  EO 4122 Kellogg in EO 5872's exemption list; EO 4658 Marchand in EO 5873). Identity is an inference, so no branch
  uses them. The one hit that cites the order by number (EO 7472 on EO 7140) shows Mrs. Hampton was appointed before
  1936-10-15, but EO 7140 as modified still carries a status permission for her, so EO 7140 stays open.
- **EO 3461 general clause for 1917-1921 war-work waivers.** A reading, not a fact the machine can apply; the held list
  is truncated and all its seen items are class orders. Not used (mechanism M6, lead_only).
- **Civil War / Spanish War service as an age fact without a date.** Logically sound (both wars ended before 1903),
  but I did not pin a primary source for the end dates, so EO 3201, 401, 4481 stay open. EO 1863 (Cullen) is decided on
  his 1883 appointment instead; EO 5285 and 5128 on dated 1898 service.
- **EO 154, 174, 185 under EO 209.** Their texts do not say "special rule"; only the WPA summary does. Left open.
- **Free-text regex for dated presence.** Too dangerous (husbands' and fathers' service, neighbouring orders in CSC
  slices). Replaced by a closed list verified by reading (B13, 51 members; B11, 5 members). Rejected on reading:
  EO 1587 (Milson, Leach undated), 1912/3433/3511/4431 (text of another order), 2102, 2788, 2946, 3926, 4770, 5056
  (facts about a husband or father), 3144 and 5701 ("about"/"approximately" periods that could fall after 1903),
  6058 kept (her own maiden-name service from 1899).
- **Death bound for pre-1904 orders whose text is only the Commission's narrative (EO 221, 223, 234) or unreadable
  (EO 251).** Kept open for want of the command's words, though the bound itself would hold.
- **Implied supersession of patent-signer and acting designations by later designations.** No held text says the
  earlier designation ended; open.

## Checks

- `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-CS-ONE-PERSON.json --hints`: 1,015 members;
  decides 98; contradicted 0. Branch counts are in the doctrine .md.
- Each B13/B11 quote was re-found by regex in the member's held text (whitespace collapsed); bounds recomputed with
  calendar arithmetic (subtract years, add 122 years, add 164 days). Latest bounds: B13 2026-03-11 (EO 2165, appointed
  September 28, 1903), B12 2026-01-09 (EO 226), B11 2008-11-27, B10 1985-08-08, B09 1994-06-18.
- B10's pattern excludes EO 4011, whose WPA summary says "age" but whose text waives the residence requirement.

## Memory

Nothing from the user's memory store bore on this task.

## Time and effort

About 3 hours of agent work in one session: roughly 1 hour reading prior work and sources, 1.5 hours reading member
texts and verifying the 56 per-member facts, 0.5 hour building, testing and writing. No paid fetches.

## Coordinator rulings applied (2026-11-05)

Applied `research/pothier/COORDINATOR_RULINGS.md` and the coordinator's message: EO 6179-A `spent_on_issue` (P1), EO 6142 and
EO 7472 `merged_into_parent_on_issue` (P2), S10 as `member_text` (P6); EO 209 no longer ends any member (special rules
outlived it, EO 250 of 1904), so the eight pre-1903 rule instruments are `open` for PD-CS-RULES (B04); B11/B13 lead kind
`hand_checked_dated_fact`, anchored by the exact Appendix A sentences; B99 states three evidence routes; re-typed members
name their family. Searched held CSC reports for age limits (Rule V sec. 5; FY1918 p. 111 postal limits) and the web for a
digitized Manual of Examinations (HathiTrust 000522353 is the Philippine manual, not it); no exact URL, so no fetch line.
New `try`: 1,015 members; 90 `no`; 925 `open`; 0 contradicted.

## Revision after blind review (2026-11-06, reviser taking over from the author)

### What I read

- `research/pothier/work/REVISION_BRIEF.md`, `COORDINATOR_RULINGS.md` (P1-P8), the author brief and schema; both
  reviews `/home/claude/pothier-review/PD-CS-ONE-PERSON-A/REVIEW.json` and `-B/REVIEW.json`; the coordinator's
  assignment message (planted errors in the reviewed copies: Retirement Act at "41 Stat. 641", B06 end 1925-09-30,
  Retirement Act dated "1922", EO 5371 revocation dated 1930-06-29; none is in the real file, which already had 41 Stat.
  614, 1925-09-21, May 22, 1920 and 1930-06-19, so those findings needed no change).
- Held texts opened for this revision: EO 5058, 4528, 6179-A (all ten items); EO 1074, 1010, 3075, 2917; the
  swapped CSC slices `jobs/csc-annual-reports/output/texts/EO_3521.txt` (revocation of the Jan. 27, 1913 order) and
  `EO_3523.txt` (amendment of EO 3455); EO 1692; EO 4538; EO 5197-A, 5638, 5855, 7251, 4846-A, 4902, 6472; EO 6777,
  7065; EO 6980C, 7759; EO 2247 and the PLO 369 row of `jobs/shepard-citations/output/PLO_TABLE.csv`; the texts of all
  16 members the coordinator named for B13, of EO 221, 223, 234, 251, 4050, 3855, 4807, 5821, 4452, 3940; every B22
  member whose only B22 trigger was the empty named-persons field (78); every B26 member; the B23 summaries; the 18
  amending orders now on B03d and the rejected amendment candidates (EO 1582, 2170, 3398, 5545, 7228, 7384, 7479,
  7488, 7139, 3804, 1360, 564); the FY1922 Commission report page image 100 (Rule V "6. The commission may ... change
  by regulation the existing age limits").
- Web: two searches (Stanwood, Iowa postmaster Sisler; Albert S. Roberts, The Dalles), neither decisive; not cited.

### What I changed and why

- **EO 5058 (both reviewers; coordinator adjudication):** new B02b, `no`, ACT, interval (1929-02-26, 1933-06-16]
  via EO 6179-A item (8), the same date-person-department match B02 uses. Checked the other eight orders EO 6179-A's
  WPA summary lists (5069, 5204, 5620, 5893, 6028, 6061, 6063, 6067): none is a census member.
- **Held express revocations and supersessions (brief step 3, ruling P3):** surveyed every ending edge on the 1,015
  members. Decided by held whole-order instruments: EO 1010 (EO 1074), EO 2917 (EO 3075), EO 1692 (order of July 27,
  1921; this also settles reviewer A's R12 about EO 3523 and EO 1692), EO 4846-A, 5197-A, 5638, 6472 (superseded by
  number), EO 2247 (PLO 369 per BLM table, gap: PLO text not held). Rejected edges as not reaching the member: EO 2
  (footnote numerals), EO 2680 and EO 3638 and EO 4118 (same-date different orders), EO 6101 and 6106A (EO 6147
  supplements them), EO 6980C (EO 7759 only mentions it), EO 6777 (EO 7065 abolishes two of its three bodies; P7 not
  met). No lead rests on a `partial_` edge.
- **Ruling P1/P2 applied throughout:** B03d (18 pure amendments, read in full, anchored per member) and B03e
  (EO 3523, only revokes EO 1692; either of the swapped texts gives the same `no` on 1921-07-27). EO 123, 158 and 164
  moved from B04 to B03d (pure amendments of numbered 1896 rules, as PD-CS-RULES B13 treats such orders); B04 keeps
  the five special rules.
- **B13 (coordinator list; reviewer A R4, R5):** added EO 2151, 2159, 2197, 3096, 3677, 3959, 4304, 4379, 4794,
  4871, 5286, 5150, 3695, 4016, 4039, 4509 after reading each text; each quote concerns the WPA-summary person (EO
  2159's WPA summary is empty; its scan names Campbell and is numbered 2159). Appendix A rows added; latest bound
  unchanged (2026-03-11, EO 2165).
- **B12b (coordinator; reviewer A R11):** EO 221, 223, 234, 251 decided on the pre-May 3, 1904 bound. Each is an order
  for named persons only (EO 223 names ten men appointed April-July 1903). Gap: the command's words are not held, and
  EO 251's date is the census date.
- **B22 (both reviewers):** removed the stand-alone empty named-persons trigger; added class openers for summaries
  that the empty field alone had caught (former employees, engineers detailed, filling of a position, commercial
  attaches, provisions of law, salary rule, time served, plate printers, assistant inspectors, Federal employees, a
  director authorized, "[Extension of 28 specified and other"). Lists of specified persons go to a new open branch
  B27 inside this family. One-person orders now fall to B08b/B08c (EO 4452, 3940, own terms), B10 (EO 4807), B13, B26
  or B99. EO 3855 goes to B99 (see rejections).
- **B10 (reviewer B R5, R6):** added the explicit "maximum age limit for entrance to the open competitive examination
  for postmaster" form before June 22, 1928 (EO 4807); cited the July 27, 1921 amendment (S11, held under EO 3523's
  file name) and EO 4538 (S12). Latest bound now 1986-07-27.
- **B21 (reviewer A R6):** made the summary terms tolerate OCR-joined words; EO 1027, 4176, 4612, 6131A, 6136, 6238
  (and EO 6980C, 7027, same defect) moved from B23 to B21. Checked that EO 911 ("steam vesselsin") stays on B23.
- **B20 (reviewer A R7; coordinator):** added EO 2190, 3458, 3459, 1978, 1979, 1787, 1828, 1841, 2240, 2391 and, from
  two scans comparing the person at the start of each WPA summary with the start of the held text, 57 more (listed
  in the JSON), including the Wikisource disambiguation page held for EO 335. Not added: OCR spelling variants (Harn/
  Ham, Fagan/Pagan, Osler/Osier, Moyer/Meyer and similar), EO 2583 (the list includes the person), EO 3887 (the
  slice contains Braddock's order second; B24 open anyway).
- **B26 (reviewer B R10):** anchored to the WPA summary, the title or the operative sentence; EO 400, 2180, 4799 and
  5145 (children mentioned, or "desirable as messengers") left B26 for B99.
- **EO 3467 (both reviewers):** the reading of "approximately 25 years" is now stated: shortened to at least 20
  years, giving 1894-02-20 (bound 2016-08-02); the unadjusted reading 1889-02-20 gives 2011-08-03.
- **Thresholds (both reviewers):** B09 holds for any minimum age of 29 or more. B10 holds for 24 or more, not 23:
  the reviewers' 23 was right for the reviewed membership (latest EO 4595, 1927-02-25), but EO 4807 (1928-02-13) is
  now the latest B10 member and needs 24.
- **Rule V numbering (reviewer B R9):** sec. 5, numbered sec. 6 in the FY1922 printing (verified at page image 100).
- **EO 3461 list length (reviewer A R13):** "lists 45 orders" removed; the held copy shows 27 items.
- **Anchors (reviewer A R10):** kept one shared pattern per checked branch, as the coordinator allowed; verified on
  2026-11-06 that each of the 94 listed members matches exactly one quote and each quote exactly one member.

### Findings rejected or not adopted, with the reason

- **EO 3855 into B10 (reviewer B R4/R5; coordinator: "if their texts carry the age bar").** The text says only that
  the papers "may be rated ... waiving the age limit"; it does not cite the order of May 10, 1921, does not say the
  limit was a maximum, and does not state the office's class. EO 3455 and EO 4538 cover only first-, second- and
  third-class offices, and the age limits of other postmaster examinations are not held. Its text does not carry the
  65th-birthday bar, so it stays open on B99. EO 4807's text does carry it ("maximum age limit"), so it was added.
- **EO 4050 into B11 (reviewer A R4, offered "if the annuity reading is accepted").** The text says Crocker "was
  granted an annuity as a mechanic retirable at 65, which action ... was based on misleading information, his proper
  retirement age being 70". It does not say the annuity was granted for age rather than disability, which the 1920
  Act also allowed, and it does not state his age. Not adopted; open on B99.
- **Per-member anchoring (reviewer A R10).** Not adopted as separate branches; the shared pattern is kept with the
  verified one-to-one match, as the coordinator allowed.

### Checks

- `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-CS-ONE-PERSON.json --hints`: 1,015 members;
  141 `no`, 874 `open`; 2 contradiction flags (EO 123: OCR number matches on EO 12362/12345; EO 6683: EO 6788 amends
  the parent paragraph as EO 6683 left it). Both explained in the .md.
- Bounds recomputed with calendar arithmetic for all new rows (script kept outside the repository).

### Memory

Nothing from the user's memory store bore on this task.

### Time and effort

About 2.5 hours of agent work: 0.5 hour reading briefs and reviews, 1.5 hours reading member and source texts and
building the branches, 0.5 hour writing and checking. Two web searches; no paid fetches.
