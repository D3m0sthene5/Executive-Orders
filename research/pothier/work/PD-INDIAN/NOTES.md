# PD-INDIAN working notes (2026-11-05)

## Read

- Brief and schema: `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`; owner ruling
  `research/readiness/owner_rulings/2026-11-05-empty-status-history.md`; type rule
  `research/readiness/type-rules/TR-INDIAN-RESERVATION.json`; `jobs/indian-reservations-1912/README.md`;
  `research/pothier/work/WORKSTREAMS.json`; engine `jobs/pothier/pothier.py` (conditions, date rules, contradictions).
- All 230 member records in `jobs/pothier/output/MEMBERS.jsonl` and the operative sentence of every member's
  primary text (scripts printed the "It is hereby ordered" span of each; fuller text for about 40).
- Kappler vol. IV pages (`jobs/numbered-early-orders/output/books/KAPPLER_IV_pages.jsonl.gz`): 1919 Act heading
  (image 204) and sec. 27 (image 235); 1927 Act ch. 299 secs. 1-5 (images 610-611); every "revoked / canceled /
  supersedes" passage in the executive-order section (images 640-740); the Utah re-withdrawals of the EO 3307 lands
  (images 722-723). Kappler vol. III printed page 193 (image 201) for the 1906 Act.
- Revoking orders: EO 324-A, 1296, 1649, 2524, 2332, 3637, 5843 (`jobs/ofr-compilations/output/texts/EO_5843.txt`),
  6147. Current-law scan: `jobs/current-law/output/MENTIONS.csv`, `ORDERS_CURRENT_LAW.csv`, `FRAGMENTS.jsonl`
  (members named: EO 1904, 2943, 4642, 5768, 5953, 6498).
- Web, not held: govinfo STATUTE-24-Pg388 (GAA sec. 5), STATUTE-48-Pg984 (IRA secs. 1, 2, 13, 18), STATUTE-49-Pg378
  (Act of June 15, 1935, secs. 1-4), STATUTE-100-Pg61 (White Earth Act sec. 3(i)); law.cornell.edu for 25 U.S.C.
  5102, 25 U.S.C. 398d, 40 CFR 49.10198 and the 25 CFR ch. I appendix; customsmobile.com copy of the appendix
  (by-state rows, Arizona to Nevada); justia.com for Sioux Tribe v. United States, 316 U.S. 317; govinfo link page
  for 25 U.S.C. 348a and a counselstack copy of 25 U.S.C. 348 notes (general orders EO 9272 to 10191).
- `held.py` searches found no registry entry for the IRA, the GAA, the 1935 Act, or the 1919 and 1927 Acts by
  citation; the Kappler books were found by file search.

## Tried and rejected

- `order_year_plus_years` for trust ends: wrong by a year when the order was issued the year before the expiry year
  (e.g. EO 2494, 1916, for trusts expiring 1917). Replaced by per-member intervals (expiry year plus period), one
  branch per interval.
- Pure regex branches for expiry year and period: the archival scans garble numerals ("to years", "19lo", "192s"),
  so the parameters were read per member (text first, WPA summary as fallback; a script compared both and found no
  disagreement where both were legible, apart from the day in EO 3348) and each branch lists its members; every
  trust branch also requires a trust-extension text or summary feature.
- `no` TERM for EO 4177 and 4297 (withdrawals until 1927-03-05): kept `open` because the end fell two days after the
  1927 Act's bar on boundary changes and no held source construes it.
- Treating IRA sec. 2 as an end of the extension orders on 1934-06-18: rejected under the owner rule that a
  continuation clause is not an end and a general rule ends an order only if it extinguishes it.
- Treating the 25 CFR ch. I appendix, the White Earth Act note and the Kenai note as current predicates: rejected;
  the first two describe past extensions and the third names a different instrument.
- A Walapai revocation (Kappler IV p. 1011, 18 July 1918) looked as if it reached EO 1368; it revokes EO 1540, so
  EO 1368 stays open.
- uscode.house.gov and ecfr.gov refused the fetches; Cornell LII copies were used for reading only.
- The first copy of `PD-INDIAN.md` disappeared from `research/pothier/doctrines/` a few minutes after writing (the
  directory was being populated by other authors at the time); it was rewritten from the same drafts.

## Generation

The JSON was produced by a scratch script outside the repository (per-member trust parameters, then grouping); the
per-member table is the appendix of the doctrine .md. Final `try`: 230 members, 172 decided (171 no, 1 yes), 58 open,
5 contradiction flags (current-law mentions on EO 2943, 4642, 5768, 5953, 6498), 72 branches.

## Effort

About three hours of agent time: an hour reading members and Kappler, an hour on the statutes and the IRA question
on the web, an hour generating, testing and writing.

## Coordinator revision (2026-11-05, later)

Revised under `research/pothier/COORDINATOR_RULINGS.md` and the coordinator's PD-INDIAN decisions: trust extensions
whose stated period was or may have been running on 1934-06-18 are `open` (IRA sec. 2 continued the period; 98
members), those ending earlier stay TERM `no` with later held extensions named (45, including EO 2109, now dated
1926-03-08 from EO 4382); the 1965 bound was dropped; restorations split into P1 `spent_on_issue` (6) and amendments
into P2 `merged_into_parent_on_issue` (8); EO 1000, 1483 (retained tract or further direction) and EO 3020 (entry to
be perfected) moved to `open`; out-of-family leads name their family; member text cited as `member_text` (P6). The
rebuilt MEMBERS.jsonl (22:58) added later edges; the six engine flags are explained in branch gaps (EO 1228 and 1256
edges quote other orders of the same date). New `try`: 230 members, 71 decided (70 no, 1 yes), 159 open, 6 flags, 54
branches.

## Revision after blind review (2026-11-06)

Read `/home/claude/pothier-review/PD-INDIAN-A/REVIEW.json` and `-B/REVIEW.json`. Planted errors ignored as instructed
(A-R1 44 Stat. 1374, A-R2 1912-11-16, B-R1 34 Stat. 352, B-R2 1932-08-28); the real file already has 44 Stat. 1347,
1912-11-26, 34 Stat. 325, 326 and 1932-04-28. Changes, each checked against the source:

- IRA sec. 13 (A-R5, B-R3; coordinator adjudication 1): 13 members whose held text names a listed tribe in Oklahoma
  are TERM `no` on their stated ends. The Oklahoma Indian Welfare Act (govinfo STATUTE-49-Pg1967, read) does not
  extend, continue or reimpose trust periods on existing allotments. EO 4470 (Modoc) and EO 4816 (Oakland) name no
  listed tribe, so they stay `open` on the affiliation question (reviewer B listed EO 4470 as sec. 13 "to be
  confirmed"; not accepted without evidence of affiliation).
- Orders after 1934-06-18 (A-R6, B-R4; adjudication 2): EO 6926, 6968, 7009, 7036, 7206, 7464 TERM `no` on their own
  ends; EO 6939, 6961, 6962, 7001 `open` on the held "cease to be of force and effect" clause (vote not held);
  EO 6940 `open` under P8 (Pala Act of Feb. 11, 1936, ch. 44, 49 Stat. 1106, reimposes the trust "which trust expired
  January 5, 1935").
- P8 statutes (A-R3, A-R4, A-R9, A-R10; adjudication 3): EO 2943 (56 Stat. 1081), EO 3048 (44 Stat. 1061, held,
  Kappler IV p. 931) and EO 3630 (Yakima Act, 50 Stat. 210, words reach periods expired "at any other time prior to"
  1937) moved to `open`. Checked the rest of the 25 CFR appendix list on customsmobile.com: Acts only for Capitan
  Grande, Pala, Crow (54 Stat. 106, ch. 80, Apr. 11, 1940: reaches EO 5301, already open), Mexican Kickapoo (Act of
  Feb. 17, 1933, ch. 97, 47 Stat. 819-820: EO 4029 moved to `open`; EO 3047 kept `no` because its period had ended in
  1924, before the Act), Kaw, Quapaw (no members), Klamath River and Yakima. EO 3304 and 7036 are not reached (named in
  gaps). The 1935 Act sec. 3 (A-R10): its words reach periods on excluded reservations not yet extended past 1936; a
  member's period that had ended before 1934 was no longer the order's period, so not reached (stated in M10 and gaps).
- Ends fixed from later held orders (A-R7, B-R5; adjudication 4): EO 2066 (EO 4464), 2317 (EO 4384), 2374 (EO 4407),
  2376 (EO 4408), 2966 (EO 5023, weaker match disclosed) are TERM `no`. EO 3994 and 5383 moved to the certain group
  (A-R8). **Rejected in part, B-R5 on EO 1916:** EO 3994 (1924) extends the same Lake Traverse allotments "for a further
  period of fifteen years" but states no expiry date, so it shows only that EO 1916's period was running on
  1924-04-19; no held source fixes its end, and it stays `open` (uncertain).
- Minor: EO 2778 interval starts 1918-12-31 (A-R12); EO 4157, 5474, 6341, 4382 and 3348 end dates corrected from their
  texts (B-R6; EO 3348 fixed at 1930-12-28 from the scan and EO 5474). A-R12 on EO 6926 and 7206 rejected: both say
  the ten years run "from the date(s) on which such trust(s) would otherwise expire", so the interval rightly starts
  on January 1 of the end year. B03 wording and interval date rule (A-R11, B-R7); EO 4177 named as the new order for
  the EO 4041 lands. M8 kind `later_instrument` and the held MENTIONS row noted (B-R8, A-R14). EO 1284 versus EO 1000
  distinction stated (B-R9). Sioux Tribe wording (B-R10). 41 Stat. 3, 34 pinpoint supported by the Interior opinion
  at Kappler IV p. 1062, image 736, citing "41 Stat. 3-34" (B-R11, verified). Act of March 2, 1917 (Kappler IV p.
  114, image 124, held) and Act of March 2, 1889 added as authorities (A-R13). PLO 5470 identification marked
  "probably EO 2225" (A-R15).
- REVISION_BRIEF item 3: EO 5105 decided `no` ACT by PLO 5866 (BLM table edge SH-47485f7636e7, "revoking EO No. 5105",
  1981-05-15; PLO text not held). No `no` rests on a partial edge. EO 6208's held text rescinds only paragraph (5) of
  EO 6160 (noted in the B04-OUT-ECW gap). EO 1916's PLO 1593 edge does not name the order by number: not used.
- New `try`: 230 members; decides 93 (92 no, 1 yes); 137 open; 80 branches; 5 contradiction flags (EO 1228, 1256,
  1284, 1598, 744), each explained in the .md (c).
