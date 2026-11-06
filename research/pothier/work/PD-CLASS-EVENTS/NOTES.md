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
