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
