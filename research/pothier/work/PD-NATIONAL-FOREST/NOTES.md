# PD-NATIONAL-FOREST working notes (2026-11-05)

## What I read

- `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`, `jobs/pothier/pothier.py`
  (condition and date-rule semantics), `research/readiness/owner_rulings/2026-11-05-empty-status-history.md`.
- `research/readiness/type-rules/TR-NATIONAL-FOREST.json` (mechanism `boundary_change_merged`, outlier list; exemplar
  EO 1260, which this doctrine decides on B08).
- `research/excavator/jacquard-2026-10-31/LOT_RULES.md` (question framing: does the order's own command still operate;
  accrued effects do not count). The Jacquard lot files have no forest lot.
- `jobs/x1-class-engine/data/EVENTS.json`: the only relevant event is X1-E5-FLPMA-1976, already classed there as
  `not_an_end_authority_repeal`, which agrees with this doctrine.
- Member records: `research/pothier/work/PD-NATIONAL-FOREST/MEMBERS.csv` and the 708 `national_forest_boundary` records
  in `jobs/pothier/output/MEMBERS.jsonl`. I read all 708 titles and the operative text of about 120 members: every B02
  revoking order, all own-date and amendment members, the questionable revocation and exclusion members, and samples from each open branch.
- Held FLPMA text: `jobs/astra-source-retention/output/pages/3949c2ad…/08af9986…/selected-pages.txt` (secs. 701-704,
  90 Stat. 2786-2792).
- Web, read only and not held: the 30 Stat. 11 PDF (pages 34-36) and 36 Stat. 847 PDF on govinfo; the 90 Stat. 2949
  PDF (sec. 9 at p. 2957); the 34 Stat. 1256 PDF (proviso at p. 1271); 16 U.S.C. 1609 at law.cornell.edu (the
  uscode.house.gov fetch failed); the Forest Service 1997 chronological record at foresthistory.org (through a
  summarizing fetch, so only sample entries were seen); search results for the FY2024 Land Areas Report.

## What I tried and rejected

- **Held later-event edges as an ending branch.** Only five members have edges. Three of the revocation edges are
  partial (EO 2242 by EOs 7053 and 7448; EO 4889 by EO 5048), and the engine cannot test an edge's qualifier. The two
  full ones (EO 3102 by EO 7078; EO 3626 by EO 5422) are covered by the explicit B02 pairs instead.
- **FLPMA sec. 702 (repeal of the homestead laws, 1976; Alaska 1986) as an outer bound for opening schedules.** I
  rejected it because it repeals the laws under which land was opened, not the orders, so it does not meet the owner
  rule.
- **NFMA sec. 9 / 16 U.S.C. 1609(a) as a CURRENT predicate for additions.** I rejected it because it protects land
  that was still in a forest in 1976 but cannot show that a given member's land or designation survived to 1976 or to
  2026.
- **Treating all boundary modifications, including additions and transfers, as amendments spent on issue.** This is
  defensible under the owner's rule and the type rule's "merged" framing. The persistence reading is also defensible,
  so I left those members open. The coordinator settled this under `research/pothier/COORDINATOR_RULINGS.md`: additions and transfers are operative acts on land whose designation persists, so they stay open (B15).
- **Consolidation-based endings** (for example EO 3317 merging the Sopris into the Holy Cross, which would end EO 1069
  under the persistence reading). I did not encode them, because they depend on the unresolved owner question and
  need forest-name matching that the held fields do not support reliably, and ruling P3 requires the later instrument's words to reach the member.
- **Coordinator lead "NFMA sec. 11".** The provision is in the 1974 Act's sec. 11(a) as redesignated, but NFMA amended
  it by its sec. 9 (90 Stat. 2957). The JSON cites sec. 9.
- **Coordinator lead "Chronologic Record 1891-2012".** I could not locate it. I used the 1997 edition (1891-1996);
  a 1985 edition is at Biodiversity Heritage Library item 252736.
- **Identity scan** for "[No. NNNN]" tags that disagree with the member number. Most hits were OCR noise. The real
  mismatches are EO 4613 (the scan is EO 4614) and EO 3537 (a postal reinstatement), both routed to B01. EO 4675's
  scan carries the tag "[No. 4676]" but its text matches EO 4675's title and date, so I kept it on B06.

## Method

Branch regular expressions were tuned against the held texts with a scratch script outside the repository
(`/tmp/pnf/scripts/build.py` generates the JSON; it is not a deliverable). The B02 pairs were found by machine from
number, date and site-name references in revoking members, then verified one by one against the revoking text. Rejected
candidates: the matches from ten texts (EOs 637, 802, 898, 970, 1069, 1257, 1354, 1934, 2223 and the EO 1555 match
inside EO 4712's neighbour text) were only mentions in neighbouring orders or navigation text; EO 4421 revokes EO 1555
and EO 3098 revokes EO 2964 only in part; and EO 1883 partly revokes EO 1324½ (Alaska medicinal springs), not EO
1324.

## Coordinator rulings applied (2026-11-05)

I applied the coordinator's message and rulings P1-P6, then re-ran `try` (708 members; decides 244; 1 contradiction,
the partial EO 5048 edge on EO 4889).

- **P1 (`spent_on_issue`).** Revocations (B06) and exclusions (B08) are dated at the effective date. The 60 members
  whose own terms schedule the opening have one branch each (B05), dated at the last scheduled step. I read every
  schedule clause and computed the day counts by hand; amended schedules are EO 2449 via EO 2470 and EO 3010 via
  EO 3039. EO 4363's purpose-restricted restoration moved to open (B09).
- **P2 (`merged_into_parent_on_issue`).** This covers the pure amendments and extensions (B07, 8 members) and EOs 4278
  and 1626 (B04), each dated at its own signing, with the parent's end recorded in the gaps. EOs 2004 and 2069 amend
  a proclamation to revoke a withdrawal and restore the land, so they are on P1 (B05), not P2.
- **Other rulings.** B15 (186) stays open and states what would decide it. The other-reservation members are split into
  B12-B14 with the overlapping family named. The member text is cited as S-MEMBER-TEXT (P6).
- **Date notes.** The order dates of EOs 2055, 3738, 3739 and 4966 were read from their signature lines. EO 3191's
  printed opening dates precede its signing, so its order date is used.

## Effort

About three hours of wall time for the first version and about one more hour to apply the coordinator rulings, with a large token spend: many full-text reads and about 25 iterations
of `pothier.py try`. Model: Claude Opus 5.5.

## Revision after blind review (2026-11-06, reviser taking over from the author)

### What I read

- `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`, `research/pothier/COORDINATOR_RULINGS.md`
  (P1-P8), `research/pothier/work/REVISION_BRIEF.md`, the doctrine `.md` and `.json`, this file, and both reviews
  (`/home/claude/pothier-review/PD-NATIONAL-FOREST-A/REVIEW.json`, `-B/REVIEW.json`).
- `jobs/pothier/pothier.py` (contradiction kinds, ENDING/LIVING mechanism sets, date rules).
- The current `jobs/pothier/output/MEMBERS.jsonl` later edges for all 708 members, and every row of
  `jobs/shepard-citations/output/PLO_TABLE.csv` that names a member (EO ids in that file are separated by "|").
- Held texts read for the decisions below: EOs 787, 1125, 1147, 4272, 1367, 4208, 1378, 1895, 1849, 1934, 2586, 2848,
  6140, 3832, 3896, 6154, 3043, 3679, 1555, 4421, 2612, 2789, 2470, 4938, 1924, 1973, 3155, 7033, 6178, 4363, 2415,
  2542-A, 2896, 2027, 2004, 3798, 5409, 4204, 4737, 5670, 7059, 6045, 2223, 3041, 3793, 3915, 7144, 7179, 2276, 4055,
  898, 1051, 1069, 3317, 870, 801, 827, 2153, 908, 3641, 3716, 6181, 1357, and the B10/B12/B13/B14 match contexts for
  every member on those branches.
- The held FLPMA pages (sha256 re-verified) for the sec. 704(a) repeal-table layout.

### Planted errors (ignored)

The real file already had the correct values: S-ORGANIC cites 30 Stat. 11, 34-36; B02-REVOKED-BY-2146 is dated
1915-03-10; S-FLPMA-701C cites 90 Stat. 2786; B02-REVOKED-BY-2485 is dated 1916-11-05. Findings A-R1, A-R2, B-R2 and B-R3
were therefore not acted on; the script asserts these four values.

### What changed and why

- **Held whole-order revocations (A-R3, A-R4, B-R1; revision brief point 3).** Added B02 branches for the six orders
  the reviewers named (EO 1378 by EO 1895; EO 1849 by EO 1934; EOs 2586 and 2848 by EO 6140; EOs 3832 and 3896 by EO 6154)
  and for three more of the same kind found in the edges: EO 1367 by EO 4208 ("the Executive Order Number 1367 dated May
  31, 1911, is hereby revoked"), EO 3043 by EO 3679 (whole townsite reservation revoked) and EO 1147 by EO 4272 (the land
  list repeats EO 1147's whole description and its total "Area about 16,420 acres"; the scan drops "17" from one section
  list, disclosed as a gap). EO 2612 is expressly superseded "and takes the place of" by number by EO 2789: decided `no`
  ACT (kind `superseded_by_later_order`).
- **PLO table rows.** Added 50 per-PLO branches (51 members) where the held BLM table row reads "revoking EO No. NNNN"
  with no "in part" for that order, including EO 4889 by PLO 1466 (1957-08-07, 22 FR 6511). The script checks, for each
  pair, that the row's eo_ids contain the member, that the row has no "in part" qualifier for that member, that the
  pin appears in the held table text (sha256 re-verified against SOURCES.jsonl), and that the row's state appears in the
  member's text or title. Sources follow the PD-REFUGE-LIGHTHOUSE pattern (S-BLM-<table> held with row pins; S-PLO-NNNN
  not held, govinfo FR link). Rejected as ends: rows "revoking in part" (EOs 1354, 1929, 3195, 3889, 4208, 4712, 6050,
  6441), PLO 399 ("EO No. 1432 1/2"), PLO 614 ("EO 1324 1/2"), PLO 1292 (a Utah water reserve of EO 1523's date), and
  PLO 2337 for EO 2242 (see "Findings not adopted as proposed").
- **Ruling P7.** I applied P7 to members whose only operative content was constituting or naming a forest later
  abolished by name: EO 898 (Mono; PLO 307, 1945-12-18) and EO 1051 (La Sal; PLO 618, 1949-11-28). The rows match
  "abolishing ... National Forest". I also treated an express merger of all of a named forest's lands into another named
  forest as abolition by name: EO 1069 (Sopris; EO 3317, 1920-08-07) and EO 827 (Nebo; EO 2153, effective 1915-07-01).
  EOs 870 and 801 also assign land to a second forest, and EO 908 renames 55 forests, so they stay open; their
  candidate ends are disclosed in the B15 gaps. The coordinator should confirm the merger reading.
- **EOs 787 and 1125 (A-R5, B-R4; coordinator).** Moved to B05-DEFERRED-OPENING (open). The restoration waits on the
  Secretary's notice. The false gap sentence was removed from B08.
- **EO 2470 (A-R10, B-R5; coordinator).** Now B04-MERGED-2470 (P2, own date 1916-10-14). I applied the same treatment
  to EO 2223 (modifies EO 1228 "to exclude from the operation thereof") and EO 6045 (restates EO 3333's description "to
  read as follows"). EOs 2896 and 7361 moved from B07 to their own P2 branches so that they could carry their
  disclosures: EO 2896's signature conflict, and EO 7361 adding land (B-R13).
- **EOs 4938, 1924, 1973 (A-R7, B-R8; coordinator).** I fixed the B06 regex to accept "here by", which sends EO 4938 to
  B06. EOs 1924 and 1973 got B05 schedule branches: 1914-05-28 (20 days from and including May 8) and 1914-09-24 (28 days
  from and including the 56th day after 1914-07-02).
- **EO 3155 (A-R10, B-R6; coordinator).** Moved to B08-MIXED-3155 (open), because it has two operative acts.
- **Purpose-restricted restorations (A-R12, B-R9; coordinator).** The B09 test is now the order's own words tying the
  land to one named disposition. EOs 7033 and 6178 moved from B08 to B09 (open), and EO 2415 (disposal under R.S.
  2122-2123) moved there from B12. A scan of every decided member for "in order to permit", "color of title", "only under
  the provisions", "to permit adjustment" and similar words found no others. The "only under the provisions of the
  homestead laws" hits are dated settlement windows in general opening schedules, so they are not restrictions.
- **Regex leaks (A-R8, A-R9, B-R7; coordinator).**
  - B10 now excludes the 1908 boilerplate. Because of OCR "wit hdrawals" the regex tolerates spaces inside the word.
    EOs 860 and 881 now go to B15.
  - "lookout" now needs "station/site/tower/point" or "fire lookout", which sends EO 5646 to B15.
  - B10's townsite exclusion now applies only to townsite reservations, so the Forest Service dock and administrative
    sites inside townsites (EOs 1384, 3333, 6189) join B10.
  - B12 ignores "Indian Meridian/Creek/Grave/Gulch/Peak/trail/graveyard". EO 1147 goes to B02 (EO 4272). The boundary-only
    transfers (EOs 5758, 6333, 6334, 6882, 6889, 7087) and EO 7059 are excluded by id and go to B15.
  - B13 excludes the municipal water supplies (EOs 1887, 1911, 3793), which go to B14, and EO 4737, which goes to B15.
  - B14 excludes the railroad-boundary transfers (EOs 4757, 6806), which go to B15, and takes EO 3041 (a townsite
    reservation) from B11.
- **Further P1 leads found while fixing the leaks.**
  - EOs 3798 and 5409 are plain exclusions with full restoration; the outlier list missed them only because of a
    boundary landmark. They are now on B08-SPENT-EXCLUSION-LANDMARK.
  - EO 4204 rescinds a naval overlay on land that had stayed forest land.
  - EO 5670 releases a War Department lot, which joins the forest by the 1907 proclamation's terms.
- **Signature-date conflicts (B-R10, B-R11; coordinator).**
  - EO 2027: the signature reads "21 A ugust, 1914", which would put the end at 1914-11-13 instead of 1914-11-16.
  - EO 2004: the signature reads "28 July, 1914", which would put the end at 1914-10-20 instead of 1914-10-21.
  - EO 2896: the signature reads "28 June, 1918" against the member date 1918-06-26.

  Each conflict is now a lead gap. Member dates are kept, as for EO 4916. A scan of signature lines on all decided
  members found no other real conflict that moves a lead date: EO 1324's conflict and the OCR misreadings in EOs 1536,
  2148, 2787, 4196, 4199, 4200, 4534 and 5619 do not.
- **EO 2542-A (A-R6, B-R11; coordinator).** The basis is rewritten: the order itself withdrew until July 1, 1918 and has
  no disposal clause; EO 2896 extended only the listed lands and added the clause. M-OWN-DATE now says that 8 of the 9
  orders carry the clause.
- **EO 1626 (B-R13; coordinator).** Kept on P2 (own date). The basis now cites EO 3025 (1919-01-25) as the parent's end
  as to Station B. The gaps record two points: under the ACT alternative the date would be 1919-01-25, and the
  correction substituted a different tract.
- **Other.** B02 gaps added for the date mismatches EO 2485→1589 and EO 3740→2148 (A-R11, B-R12). S-EO-3194's citation
  and title now carry the number (A-R13). The "16 U.S.C. 471 note" codification was dropped and the LAR as-of date
  marked unverified (A-R13). The B06 description now matches its regex (B-R14). The FLPMA 704(a) layout note was added
  to the .md.

### Findings not adopted as proposed

- **A-R11 (EO 2242, PLO 2337).** The reviewer asked only for disclosure. I did not make the PLO 2337 row an end, because
  later rows of the same held table modify EO 2242 (PLO 2755, 1962) and revoke it in part (PLOs 3345, 1964, and 3848,
  1965). An order revoked in full in 1961 could not later be revoked in part, so the table itself shows the 1961 row was
  not a complete end. EO 2242 stays open on B14, with this disclosed.
- **A-R12's proposed test** ("only" plus a named Act is restricted; release for disposal under a general Act is not).
  I used the coordinator's direction to treat EOs 7033, 6178 and 4363 consistently. The test adopted is that a named
  disposition stated as the exclusion's purpose is a restriction whether or not the word "only" appears. EO 7033
  excludes land for disposal under one named Act and does not return it to the general land laws, so it is open.
- **B-R13 (EO 1626 as ACT, 1919-01-25).** Not adopted as the lead, because the coordinator ruled P2 with EO 3025 cited as
  the parent's end. The ACT reading is recorded in the gap.
- **A-R7's alternative (EOs 1924, 1973 as `merged_into_parent`).** These orders amend in form, but their only content
  ends a withdrawal and opens the land. As the coordinator directed, they take P1 (`spent_on_issue`) at the last
  scheduled step, consistent with EOs 2004 and 2069.

### Contradictions after revision (engine: 2)

- **EO 1523, edge SH-702748a1639e.** A Wikisource note says that EO 2764 "Amends" EO 1523. EO 2764 in fact further
  modifies the Harney boundary "as modified by" EO 1523's date. EO 1523's single exclusion was spent in 1912, so the lead
  stands.
- **EO 5194, edge SH-3eb5635efb76.** The edge is labelled `revocation`, but its quote is EO 5743's "Partial Revocation
  ... in so far as it affects". It is not an end, so the open lead stands.

I also checked the non-flagged edges that postdate a `no` lead's end. None changes a lead:

- the EO 1324 edge is PLO 614 ("EO 1324 1/2");
- the EO 1899 edge is a Federal Register contents line about the unnumbered order of June 13, 1899;
- the EO 1928 edge is PLO 518, about Public Water Reserve No. 114;
- the EO 3641 edge is EO 3716, which cites EO 3641 as the earlier boundary;
- the EO 6181 edge is EO 6208, which rescinds the parent's section (P2).

### Result

`try`: 708 members; decides 314 (`no` 314, `yes` 0); open 394; contradicted 2; 199 branches. 111 `no` leads rest on
ACT and 203 on TERM. 52 PLO texts were added to FETCH_PROPOSED.jsonl. The JSON was produced by a script outside the
repository (`/tmp/pnfrev.x8PH/revise.py`, applied to the pre-revision file), not edited by hand.

### Effort

About two and a half hours of wall time, with moderate token use: one full pass over both reviews, about 70 member
texts read, and about 8 `try` iterations. Model: Claude Opus 5.5.
