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

## Revision after blind review (2026-11-06, reviser session)

Reviser: Claude (Pothier doctrine reviser), taking over from the author. No git commands run. Files written: the
doctrine .json and .md, this NOTES.md (appended) and FETCH_PROPOSED.jsonl. Scratch scripts in `/tmp/rl2/` (outside
the repository); the pre-revision JSON and FETCH file were copied there before editing. Effort: about two hours of
agent time.

Read: AUTHOR_BRIEF, DOCTRINE_SCHEMA, COORDINATOR_RULINGS (P1-P8), REVISION_BRIEF, the doctrine files, both reviews
(`/home/claude/pothier-review/PD-REFUGE-LIGHTHOUSE-A/REVIEW.json`, `-B/REVIEW.json`), the held texts of EO 375A,
5750, 1304, 1311, 3671, 1464, 2200, 2872, 347A, 701, 5095, 5318, 5470, 4364, 5702, 779, 4490, 5000, 5971 and the
other B63/B64 members, the held 16 U.S.C. 668dd text ((a)(5), (a)(6), 1976 note), the BLM tables 7343-7898, and all
later edges on members in `jobs/pothier/output/MEMBERS.jsonl`. Web (not held): Pub. L. 100-226
(https://usc-cdn.house.gov/statutes/pl/100/226.pdf), ANILCA NPS print
(https://www.nps.gov/subjects/wilderness/upload/ANILCA_508.pdf), Proclamation 2112 (presidency.ucsb.edu), the FWS
copies of 48 FR 7890 (Alaska Maritime and Yukon Delta), PLO 7693 (https://regulations.justia.com/regulations/fedreg/2008/03/25/E8-5995.html).

Planted errors in the reviewed copies, ignored as instructed: A-R1 (EO 4832 date), A-R2 (Proclamation 2416 page),
B-R1 (EO 3642 date), B-R3 (Reorganization Plan page). The real file already had 1928-03-17, 54 Stat. 2717,
1922-02-27 and 53 Stat. 1431.

Changes and reasons:

- EO 375A (A-R3, B-R2; coordinator): new B21, `no`, ACT, 1931-11-23; held EO 5750 (official OFR compilation text)
  revokes the order of Nov. 27, 1905 by its exact tract. Looking for others of the same kind, I scanned every held
  text corpus (`jobs/*/output/texts`) for each open member's full written date near a revoking word. Only one more
  was found: PLO 7693 (2008) in the held BLM table 7679-7715, "Revocation of Withdrawal Established by Executive
  Order Dated February 4, 1909 for the Pigeon Point Lighthouse Reservation"; the PLO text on the web names EO 1020
  by number and revokes it in its entirety as to EO 1020's exact lots. New B59 `no`, ACT, 2008-03-14. The author had
  searched only the six BLM tables up to PLO 7342; the later tables (1998-2020) were searched now by number and
  date and add only partial revocations (Jupiter Inlet PLO 7765, Sanak PLO 7486, Ediz Hook PLO 7583, Channel
  Islands PLO 7723), disclosed in gaps. Other date hits were collisions (Huron Islands order of Oct. 10, 1905 in
  EO 7795 is not EO 357B or 357C; PLO 541's Alaska order of Nov. 27, 1905 is not EO 375A).
- EO 4364, EO 5702 (A-R4, B-R7; coordinator): moved from the PLO 6287 branch to new open B69 with the 43 U.S.C.
  1714(j) conflict stated. Branch id B59 now holds PLO 7693 (EO 1020).
- EO 779 (A-R5; coordinator): no held copy of Proclamation 2112 exists (searched held.py, "Fort Jefferson",
  "Tortugas", "Executive Order No. 779"); new open B68 with the acquisition and the revoking phrase as read on the
  web (confirmed at presidency.ucsb.edu). Statutes at Large page left unverified (A's "49 Stat. 3430" not checked).
- M5 and B73/B74 (B-R7; coordinator): the (a)(6) exceptions for acquired lands, exchanges and cooperative
  agreements are quoted from the held text and their bearing on B73 is stated. A-R14: the causal clause about the
  1966 Act is replaced by what the held 1976 amendment note shows (the struck sentence preserving the Secretary's
  authority to revoke).
- B61, B62 (A-R11, B-R4): fixed dates 1927-01-03 and 1929-04-25 (last day of each 91-day period, computed from the
  order dates: day 63 is 1926-10-05 and 1929-01-25). M2, (c) and the JSON agree.
- ANILCA (A-R8, B-R5): sec. 305 cited at 94 Stat. 2395 and quoted with all three sentences; sec. 303(1)(A) quoted as
  "shall consist of eleven existing refuges" and 303(7)(A) as "shall consist of the existing ... Nunivak National
  Wildlife Refuge", checked against the NPS print.
- EO 5095 (A-R7, B-R8; coordinator): the mapping now rests on its title ("for Establishment of Nunivak Island
  Reservation") and EO 5470's "added to and made part of the Nunivak Island Reservation"; a gap discloses its
  non-refuge purposes.
- Pub. L. 100-226 (A-R9, B-R9): the "which are within the boundaries of Olympic National Park" limit is quoted in
  M6, B01 and S06, with a gap for refuge lands outside the park. Text checked at usc-cdn.house.gov.
- B04 count (A-R6, B-R10): seven orders name their reservation; eight created one and two (5318, 5470) enlarged one.
- EO 1304/1311 (B-R12; coordinator): EO 1304 moved to new B22, `no`, ACT, interval 1911-02-18 to 1911-03-01,
  because EO 1311 replaces it by number "in lieu of" it; EO 1311 stays spent on issue. No other member is replaced
  "in lieu of" (searched all member texts).
- EO 1464, 2872 (A-R13; coordinator): moved to B64 (P2) with the disclosure. Of the same kind I also moved EO 2200,
  which reduces the Klamath Lake Reservation by fixing "the new boundary thereof, established by this Order", a
  rewrite of the parent's boundary term. The other B63 members only revoke, restore or eliminate land.
- B63 condition (A-R12; coordinator): now `text_regex` on the member's own text only, with "ganeel" for the OCR of
  EO 347A's "cancelled"; all 17 members match.
- EO 2012 routing (B-R11; coordinator): PD-WAR-EMERGENCY in both files; 2670, 6724, 7345 to PD-ADMIN; the text says
  these stay open here until retyped.
- EO 3658 (A-R10, B-R6; coordinator): EO 7836 (held) disclosed as a second date collision with Public Water Reserve
  No. 82.
- FWS Federal Register refuge-description notice (B-R8; coordinator): found as 48 FR 7890 (Feb. 24, 1983),
  "National Wildlife Refuges in Alaska; Description of Boundaries". Its Alaska Maritime part names EO 1037, 1039,
  1040, 1044, 1049, 1458, 1459, 1658, 1733 and 5318; its Yukon Delta part names no order. Added as S45 and to
  FETCH_PROPOSED with the govinfo link and both FWS URLs. It is a 1983 record, so it is cited as the record naming
  the orders, not as a 2026 predicate.
- Other edge disclosures: EO 923 restoration edge (EO 10383 concerns a Hawaii Governor's order No. 923); EO 701
  partial edge (Power Site Reserve No. 701); EO 6065 edges from EO 8821 (a "shall not rescind or revoke" clause).

Findings rejected: none outright. A-R5 asked for a `no` lead on EO 779 from the web-read proclamation; I kept it
`open` because the brief allows a `no` only on a held source or a held official table, and the coordinator ruled
the same. A-R4 offered keeping B59 `no` with a gap; I took the coordinator's ruling (`open`). B-R7 called the PLO
6287 lead "sound because the BLM row shows the same lands re-withdrawn"; the row shows a withdrawal "for addition
to" the refuge, which does not by itself show the revocation was lawful under 1714(j), so the lead is open.

Final `try`: 243 members; decides 87 (yes 14, no 73); open 156; contradicted 5 (EO 2755, 2872, 3658, 431, 4975),
each explained in the .md and in its branch's gaps.
