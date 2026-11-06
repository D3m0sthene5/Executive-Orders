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
