# PD-CLASS-EVENTS working notes (2026-11-05)

## What I read

- Brief and schema: `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`; owner ruling
  `research/readiness/owner_rulings/2026-11-05-empty-status-history.md`; engine `jobs/pothier/pothier.py`.
- Members: `research/pothier/work/PD-CLASS-EVENTS/MEMBERS.csv` and the matching rows of `jobs/pothier/output/MEMBERS.jsonl`
  (later edges, named-person hits, current-law fields).
- Type rules `research/readiness/type-rules/TR-NRA-CODE.json`, `TR-CANAL-ZONE.json`, `TR-PHILIPPINES.json`; X1 events in
  `jobs/x1-class-engine/data/EVENTS.json` and their held-source state in `jobs/x1-class-engine/output/EVENT_SOURCES_STATE.json`
  (all six event sources held with phrases found).
- NIRA sweep: `research/excavator/claude-nira-sweep-2026-10-29/SHARED_ANALYSIS.md`, `REPORT.md`, `SUPPLEMENT_SOURCES.json`.
- Jacquard: `research/excavator/jacquard-2026-10-31/LOT_RULES.md` (L4, L5, L6), `INDIVIDUAL_REVIEW.csv` in both waves,
  `jacquard-2026-10-31-w2/README.md`, and one L5 review record (EO 6219) in `jacquard-2026-10-31/reviews/L5/batch-04.jsonl`.
- Held sources opened and pinned: NIRA (48 Stat. 195) secs. 2(c), 3, 9, 10; S.J. Res. 113 (49 Stat. 375); Schechter
  syllabus and p. 542; Panama Canal Act of 1979 (93 Stat. 452) secs. 3, 2101, 2201, 2401, 3301-3304; Philippine
  Independence Act (48 Stat. 456) secs. 7(4), 10(a); Proclamation 2695 (60 Stat. 1352-1353); APP texts of EO 7075,
  7076, 7084, 7234, 6064, 6344, 6763, 6771, 7252, 1885; Wikisource EO 7076.
- Member texts read in full or in their operative part: about 70 (all NRA authority clauses by script, then 6173, 6199,
  6202-A, 6204, 6205-B, 6207, 6298, 6345, 6513, 6561, 6595, 6612-A, 6684-A, 6731-A, 6764, 6770, 6785, 6836, 6859, 6860,
  6920-A, 6920-B, 6988, 6993, 7192; Canal Zone 373-A, 412, 418, 595, 673, 725, 1231, 1860, 2737, 2907, 3917; Philippine
  2448, 2456, 2877, 7447).
- Web (not held): Panama Canal Treaty text, archived State Department page
  https://webarchive.library.unt.edu/eot2008/20081104004447/http://www.state.gov/p/wha/rlnks/11936.htm (arts. I, II,
  III(10), XI, XIII) and the UNTS registration PDF
  https://treaties.un.org/doc/Publication/UNTS/Volume%201280/volume-1280-I-21086-English.pdf (in force Oct. 1, 1979;
  No. 21086; art. II(2) phrase confirmed); 22 U.S.C. 3602 and notes at https://www.law.cornell.edu/uscode/text/22/3602.

## Findings that shaped the doctrine

- The 95 "NRA code approvals" here are almost all non-approvals; Jacquard L4/L4R failed 48 of them on type fit alone
  ("not a code or agreement approval"), never on the end date. EO 7076 (June 15, 1935), which none of the earlier
  work used, extends every Title I order only to April 1, 1936, and so decides these by authority rather than by type.
  EO 7084's recital ("continued by Executive Order No. 7076") confirms the reading.
- The coordinator's lead that S.J. Res. 113 "repealed the code provisions" is right; its lead that Title I "expired
  ... June 16, 1935" needs the correction already made by the NIRA sweep: section 1 moved the expiry to April 1, 1936
  before June 16 arrived.
- The Panama Canal Act of 1979 is a continuation statute, not an end: sec. 2101 continues Zone laws for transition
  law enforcement and courts, sec. 3(b) re-reads "Canal Zone" as the treaty areas, and sec. 3303(b) renames the
  unrepealed Canal Zone Code the Panama Canal Code. The end therefore rests on the Treaty (terminated noon Dec. 31,
  1999), which is not held. Jacquard's L5 card used the same outer bound.
- The Canal Zone failures in Jacquard were mostly correct outliers (outside-Zone reach, Panama Railroad, civil-service
  rules, continuing rights, truncation). A narrower branch decides only the clean Zone-only texts (3), and two
  spent-on-issue branches decide appointments (17) and pure amendments or revocations (5).
- Five Philippine-typed orders have no Philippine subject.

## Tried and rejected

- Dating NRA code-dependent commands at June 14, 1935 by a separate branch: rejected because the machine cannot tell a
  code-dependent clause from a section 4(a) or administrative clause; the April 1, 1936 interval is right for both.
- A "spent on issue" branch for every NRA amendment by title: rejected in favour of N6's interval, which does not
  depend on the order containing nothing but an amendment; N7 keeps only two amendments that cite no Title I power.
- A general "named body terminated" branch keyed on the words "National Industrial Recovery Board": rejected because
  EO 6860 mentions the Board's chairman incidentally; explicit member lists used instead (N2, N3, N5).
- Using the empty `date_candidate` of held revocation edges: the engine would give no date, so R1-R3 name the members
  and take the acting orders' dates from their held texts.
- Using the 1979 Act alone (Oct. 1, 1979) as the Canal Zone end: rejected; see above.
- Deciding EO 7192 (FTC delegation, Sept. 1935) by the Title's expiry alone: left open, since the owner rule says an
  authority's lapse is not by itself an end and EO 7076 does not reach post-June 14, 1935 orders.
- Treating fund allotments as spent on issue: left to PD-ADMIN's fund-allotment rule for consistency.

## Time and effort

About two and a half hours of agent time: roughly 40 shell and file reads, 4 web lookups, 5 doctrine iterations with
`pothier.py try`. No git commands run.

## Coordinator rulings applied (2026-11-05, version 2)

Applied `research/pothier/COORDINATOR_RULINGS.md` P1-P6 at the coordinator's request: N6 recast as `ended_by_express_class_instrument` quoting EO 7076; named-person orders (Canal Zone C1, NRA O1b, Canal Zone pay O2b) routed `open` to PD-CS-ONE-PERSON, whose members selector does not reach them; C2 split into C2a `spent_on_issue` and C2b `merged_into_parent_on_issue` with the P2 disclosure (N7 likewise); N2/N3 narrowed to the orders the terminating instrument names (EO 6859, EO 6632), so EO 6993 and EO 6637/7025 fall to O1 or N6/O1b; P1 quotes sec. 10(a) and Proclamation 2695; other-family members (fund allotments, civil-service rule orders, Alien Property Custodian and general orders) stay open with the family named; member text added as source S0 (P6). Result: 67 no, 118 open, 0 contradicted. About 30 more minutes.

## Blind reviews A and B applied (2026-11-05, version 3)

Read `/home/claude/pothier-review/PD-CLASS-EVENTS-A/REVIEW.json` and `-B/REVIEW.json`. Planted errors ignored after
checking the real file (it has 49 Stat. 375, the N6 bound 1936-04-01, 48 Stat. 456, the P1 bound 1946-07-04): A-R1,
A-R2, B-R1, B-R2. Changes, each checked against the held text:

- P8: EO 7192 decided `no` (N5b, `ended_with_delegated_statutory_power`, 1936-04-01). P7: EO 6993 joins EO 6859 (N2,
  1935-06-15); EO 6632 and EO 6771 (N3, fixed 1934-07-01); EO 7075 (N5) now quotes EO 7252 sec. 2, which names it
  ("as constituted by Executive Order No. 7075"), adds the Advisory Council, discloses the abridged held text.
- Held express ends added (R4-R8): EO 6237 (EO 6575, 1934-01-24), EO 3985 (EO 4006, 1924-05-07), EO 2867 (EO 2907,
  1918-07-09; its held scan is complete), EO 370 (EO 393, 1906-01-12; held in the 1911 compilation OCR and Wikisource),
  EO 2692 (EO 3027 class revocation, 1919-01-25). None rests on a `partial_` edge. Scanned the new Shepard edges for
  others: EO 418 (EO 474 "All orders in conflict herewith are revoked"; Wikisource editorial note only), EO 273/289
  (Wikisource note "Supersedes" on EO 394; the 1911 text of EO 394 has no revoking words), EO 1761/2118 ("Amends
  (supersedes?)" note on EO 3255), EO 3917 (EO 6072 re-transfers by reference) are implied or editorial and stay
  disclosed only (P3); EO 1897 has only a `partial_revocation` (PLO 1416).
- N6 exclusion anchored to the authority clause plus allocation and corporation clauses; only EO 6551 enters N6.
  Rejected A-R11 in part: EO 6651 stays open, not because of "export-import banks" but because it has a second
  operative clause allocating Title II funds (sec. 220, Fourth Deficiency Act), stated in the .md.
- EO 6637 moved to O1a (fund allotment, PD-ADMIN). EO 6836 and EO 595 moved to PD-CS-ONE-PERSON routing (P4), A-R17.
- EO 7076 (N4) treated as an amending order under P2 (A-R15), dated 1935-06-15 with the disclosure.
- EO 6858 given its own open branch O1c disclosing EO 7084's July 1, 1935 limit (A-R12, B-R14).
- M3 (June 14, 1935 code repeal) is now a disclosed candidate only (B-R11). C3 basis rests on P5 and Treaty art.
  II(2); the 1979 Act is described as continuing, not ending, Zone rules (B-R9); EO 2907's war-emergency predicate and
  sec. 3302(a) disclosed (B-R15); the sec. 3(b) quotation completed (A-R20). M12 quotes the reservation exceptions and
  sec. 7's opening words (B-R16). C1 discloses the stated special-judge ends (A-R18; EO 4370's text and summary carry
  no "until" date, so it is not listed). Parent labels fixed (A-R19, B-R13). "Truncated" labels replaced with each
  member's real reason: every O2 text is complete (B-R12).
- Result: 72 `no`, 113 `open`, 0 contradictions. About 40 more minutes.
