# PD-REFUGE-LIGHTHOUSE: working notes

Author: Claude (Pothier doctrine author), 2026-11-05. No git commands run. Files written: the four deliverables only.
Scratch scripts lived in `/tmp/rl/` (outside the repository).

## Time and effort

Ended about 2026-11-05 22:50 (UTC-5). The start time was not recorded; the run took roughly two to two and a half
hours of agent time. About a third went to reading member texts, a third to finding later revoking instruments
in held corpora, and the rest to statutes on the web, building the JSON and writing.

## What I read

- Brief and schema: `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`, the engine
  `jobs/pothier/pothier.py` and `jobs/pothier/held.py`.
- Type rules: `research/readiness/type-rules/TR-BIRD-REFUGE.json`, `TR-LIGHTHOUSE.json`, `TR-LAND-WITHDRAWAL.json`.
- Prior work: `research/excavator/claude-land-probe-2026-10-28/undecided/LAND_PROBE_REPORT.md` (EO 1304 replaced by
  EO 1311); Kean search for "lighthouse" and "refuge"; `jobs/x1-class-engine/data/EVENTS.json` (nothing family-specific).
- Member texts: the operative 500 characters of all 243 primary texts, and full texts of about 40 (1037-1049,
  1458, 1459, 1642, 1658, 2047, 2203, 3237, 3377, 3658, 3957, 4084, 4386, 4939, 5040, 5095, 5318, 5419, 5470,
  5630, 682, 6896, 701, 703, 705, 7292 and the revoking orders).
- Held statutes: 16 U.S.C. 668dd 2024 edition (`jobs/source-ladder/output/texts/USC_16_U.S.C._668dd_a_6_cd9a4906a8.txt`,
  13 pages, including the "National Wildlife Refuges" note), 43 U.S.C. 1714 (`..._1714_j_._7ba3070691.txt`),
  Proclamation 2416 (astra derivative, 7 of 8 pages), the Federal Register of July 1, 1939 with Reorganization
  Plan No. II (astra derivative).
- Current-law job: `jobs/current-law/output/MENTIONS.csv` and `FRAGMENTS.jsonl` rows for EO 703, 705, 1044, 4254,
  7116.
- Later-event sources: `jobs/shepard-citations/output/EDGES.csv` (163 edges on members) and the BLM Tables of
  Public Land Orders in `jobs/shepard-citations/output/texts/blm/`; Wikisource notes in members' Wikisource texts.
- Web (not held): uscode.house.gov 16 U.S.C. 668dd and 43 U.S.C. 1787; Pub. L. 100-226
  (https://usc-cdn.house.gov/statutes/pl/100/226.pdf); ANILCA, NPS electronic version
  (https://www.nps.gov/locations/alaska/upload/ANILCA-Electronic-Version.PDF) for secs. 303 and 305; Pub. L.
  106-355 (https://www.govinfo.gov/content/pkg/PLAW-106publ355/html/PLAW-106publ355.htm); FWS Annual Report of
  Lands 2002, 2014 and FY2024 data tables.

## What I tried

- Reverse-citation scan of the held text corpora (17 job folders) for later orders citing a member's number near
  a revoking word, and a second scan by full written date. Found the 11 held revoking orders (including EO 7983
  revoking EO 369-A by date) and EO 2177's and EO 5971's express savings of EO 1814, 2047 and 4939.
- Searched the BLM PLO tables by member number and by full date; 30 PLOs revoke 35 members in full. Checked each
  row by hand and discarded date collisions (power-site, reservoir, phosphate and Alaska orders that share a date
  with a member: for example PLO 6769 "EO of Aug. 9, 1916; Powersite Reserve No. 539" is not EO 2438, and PLO 7391
  "EO dated November 14, 1917 ... Power Site Reserve No. 658" is not EO 2755; both are misresolved as revocations
  of members in `jobs/shepard-citations/output/EDGES.csv`).

## What I rejected

- The FWS Annual Report of Lands as a machine predicate: it lists refuge units and acreage (including "Reserved
  from Public Domain"), never executive orders. The 2002 and 2014 reports and the FY2024 tables were checked.
- Proclamation 2416 as a current predicate: it renames reservations in 1940 and says nothing about later years.
- Treating every amending order as spent: 43 U.S.C. 1787 treats EO 4254, an amendment adding land, as an order
  under which a withdrawal exists, so enlargements stay open.
- `yes` for refuges known to exist today by name only (Pelican Island, Hawaiian Islands, Malheur, Three Arch
  Rocks and others): no held or current source names the order, and EO 929, the 1908 Malheur order, was in fact
  revoked by PLO 1511 in 1957 while the refuge continued under later orders.
- Wikisource notes as ending sources (EO 779 "revoked by Proclamation 2112"): editorial notes, kept as leads.
- The coordinator's citation "114 Stat. 2412" for the National Historic Lighthouse Preservation Act: the Act is
  Pub. L. 106-355, 114 Stat. 1385.
- EO 6896 as an end of EO 1066 and 2750: it transfers San Miguel and Prince Islands to the Navy with lighthouse
  sites reserved; a transfer continues the reservation.
- EO 3957 as an end of EO 2203: the verb is illegible in the only held copy.

## Things the coordinator should know

- `jobs/pothier/output/MEMBERS.jsonl` `later_edges` does not carry the shepard-citations edges (BLM PLO table,
  held-text citations); the doctrine names those members explicitly. Folding those edges in would let future
  doctrines use `edge_date`.
- The held 16 U.S.C. 668dd note prints the Yukon Delta entry as "Pub. L. 96–498"; the Act is Pub. L. 96-487.
- `S-BLM-*` sources carry an extra `row_pins` key listing the row text for each PLO used.
- 2026-11-05, after coordinator rulings (`research/pothier/COORDINATOR_RULINGS.md`, P1, P2, P6): split the spent branch into B63 `spent_on_issue` (21) and B64 `merged_into_parent_on_issue` (EO 5457, 5458) with the P2 disclosure; replaced the EO 3658 own-text source with a `member_text` source (SM) used by B60-B64 and B70; added ANILCA sec. 305's full text to the source, the B04 basis and the .md, with Proclamation 2416's Alaska old and new names pinned and EO 5095's name-only match disclosed; PLO-lead gaps now state that the PLO text is not held and that whole-order scope is as the BLM table states; B70 names the family for each member; the lighthouse act is cited as Pub. L. 106-355, 114 Stat. 1385 throughout. `try`: 243 members, decides 87 (yes 14, no 73), open 156, contradicted 0.
- 2026-11-05 23:00: `jobs/pothier/output/MEMBERS.jsonl` was rebuilt with the shepard-citations edges; `try` now shows 5 contradiction flags (EO 2755, 2872, 3658, 431, 4975). Each was read: two are events of another order, two are date collisions (PLO 1300, PLO 7391), one is a partial revocation (PLO 1724); all are disclosed in branch gaps and no lead changes. Final `try`: 243 members, decides 87 (yes 14, no 73), open 156, contradicted 5.
