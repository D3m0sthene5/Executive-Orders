# PD-LAND-WITHDRAWAL working notes (2026-11-05)

Author: Claude, Pothier doctrine author subagent. No git commands were run. The four deliverables are the only
files written in the repository. Scratch scripts were kept in /tmp/lw, outside the repository:
`whole.py` builds the verified whole-revocation list, `build.py` generates the doctrine JSON, and `review.py`
prints each branch's members.

## Time and effort

File timestamps put the wall clock at about 22:15 to 23:05 EST on 2026-11-05, roughly 50 minutes. The split was
about 10 minutes reading the brief, schema, type rules and probe reports; about 10 minutes on web checks of
primary sources and BLM data services; about 20 minutes building and checking branches against member texts and
summaries; and about 10 minutes writing. The minutes are estimates; only the start and end are from timestamps.
About 75 tool calls.

## What I read

- **Project files.**
  - `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`, and `jobs/pothier/pothier.py`
    and `held.py`.
  - Type rules TR-LAND-WITHDRAWAL, TR-MINERAL-WITHDRAWAL, TR-POWER-SITE and TR-WATER-RESERVE.
  - Both LAND_PROBE_REPORT.md files under `research/excavator/claude-land-probe-2026-10-28/`.
  - `jobs/shepard-citations/README.md` and `BUILD_NOTES.md`, with the job's output EDGES.csv and PLO_TABLE.csv.
    These were generated on 2026-10-29 and include the 24 BLM PLO tables.
  - The `jobs/current-law/output/FRAGMENTS.jsonl` rows for EO 3489, 3529, 5136, 5237, 5327 and 6184.
- **Held source texts.**
  - The FLPMA slice, 90 Stat. 2785-2794.
  - EO 9146 (FR original), EO 9337 (mirror transcription) and EO 10355 (1989 codification).
  - 43 CFR 2300.0-3, 2400.0-3 and 2520.0-8.
- **Member texts.** About 60 member texts were read in full or at the operative clause. They covered resurvey
  withdrawals of 1924-1933, ex-service revocations, Power Site and Public Water Restorations, public water reserve
  establishments, withdrawals "until March 5", the revoking orders behind B06, and the empty-summary members.
  Summaries were read for all 1,270 members, scanned by category.
- **Web reading** (WebFetch or WebSearch; nothing on the web is held). The URLs are in the doctrine and in
  FETCH_PROPOSED.jsonl.
  - The govinfo Statutes at Large PDFs for 36 Stat. 847, 39 Stat. 862 and 90 Stat. 2743 (sec. 204(l) at
    pp. 2754-2755), and the govinfo U.S. Reports PDF for 236 U.S. 459.
  - 16 U.S.C. 818 through Cornell LII (uscode.house.gov returned a client error), and 16 U.S.C. 460y and 460y-7
    through Cornell and Justia.
  - 67 FR 63448.
  - BLM's OR/WA withdrawals map service and its data standard v1.1, and BLM's national MLRS "Withdrawals Case
    Land Status" service. Queries to the national service go through nlsdbpubgis.blm.gov.
  - GLO Records, which needs JavaScript; nothing was read there.

## Findings worth keeping

1. **Shepard rows do not reach the doctrine engine.** `jobs/shepard-citations/output/EDGES.csv` holds 1,692 rows
   on members of this family, including 145 BLM-table revocations not marked "in part". `jobs/pothier/members.py`
   does not load them: it reads only later-events and namier edges. So 179 whole revocations had to be put into
   the doctrine as instrument-id lists with a side table. Two changes would let a branch use `edge_date` with
   per-member dates: load Shepard rows into `later_edges`, and map a "in part" qualifier to a distinct mechanism
   such as `partial_revocation`. The coordinator should decide.
2. **The engine lacks day arithmetic.** B21's exact ends are the order date plus 154 days. An
   `order_date_plus_days` date rule would compute them; the doctrine uses a conservative interval instead.
3. **BLM data sources.**
   - BLM's OR/WA withdrawals layer is an official current record that names the creating order. It has the fields
     ORD_TYPE "EO" and ORD_NUM (order number), with CASE_DISP 5 meaning Authorized. It listed EO 5907, 6019 and
     6618, and also unnumbered "PW Res NNN" and "Pwr S Res NNN" cases. PWR 107 appears there under ORD_TYPE "PO",
     number 7358.
   - The national MLRS layer has a disposition and land-status field for every withdrawal case, but in the
     samples read DOC_NR was empty. Matching would have to use case names and the MLRS case abstracts.
   - The values were read through a summarizing web fetch and must be re-read from a retained export before the
     yes leads can be relied on.
4. **The resurvey withdrawals change wording around 1928.** Withdrawals of 1923-1927 end by their own terms when
   the plat of resurvey is filed. From about 1928 they say "unless and until revoked by the President, or by an act
   of Congress". The plat filing dates in GLO Records would decide 145 members.
5. **X1 typing errors.**
   - Thirty-four members are not land orders (B01): Indian trust-period extensions (2326, 2505, 3204, 3365),
     Saturday half-holidays, employee leave, Navy and Marine strength, and others.
   - EO 3504 (Pablo bird refuge) is typed as a power site.
   - The WPA summary for EO 6116 runs into EO 6117's.

## What I tried and rejected

- **A branch on `later_edges`.** Rejected because it cannot tell partial from whole revocations, and most held
  edges are partial.
- **Treating FLPMA sec. 702 as the end of ex-service openings that run from plat filing (B22).** Sec. 702 repealed
  the preference resolutions in 1976. Rejected because that is a repeal of the authority for the command, which
  D-20261028 says is not an end. B22 stays open.
- **Treating "modified to permit" a continuing use as spent.** The cases were an aviation field, an airport lease
  and withdrawals for air navigation. Rejected after EO 7219, which had been "modified to permit construction of
  an airport", was later revoked by PLO 2080. BLM's revocation shows such orders had continuing effect, so they
  now fall to B33 and B24, which are open.
- **Accepting Shepard text-number "revocation" rows as they stand.** Rejected. Partial revocations hidden by OCR
  ("revoked as. to"), "of the [lands], is hereby revoked", "following-described" lists, deferred effect (EO 6287)
  and neighbour-page bleed (EO 3474 attributed to EO 4613) all appeared. The stricter tests in the doctrine's
  part (c) replaced them. EO 2593, 2984, 4103, 4345, 4482, 4980, 5202 and 6287 were dropped, and EO 4097 and
  5118 were dropped because their PLO headings name no State.
- **Reading EO 3895's edge from EO 4607 as a revocation.** Rejected as a false date match: the edge points at an
  unnumbered order of August 23, 1923.
- **A current-law yes for EO 5327 (43 U.S.C. 852, 43 CFR 2621.0-3) and EO 6184 (30 U.S.C. 529).** Rejected.
  These provisions refer to lands withdrawn by the orders (state selection; opening to mining under a helium
  reservation), but they do not show the withdrawal in force in 2026. Both stay on B33, open.
- **Trying to read the King Range establishment notice and the GLO survey plats.** The establishment notice's FR
  citation was not found, and the GLO plat search needs a browser.

## Memory used

None of the user's memory bore on this task beyond the stated style preferences, which shaped the prose.

## 2026-11-05, version 2 (coordinator rulings P1-P6 and decisions 1-7)

Rebuilt against the rebuilt MEMBERS.jsonl, which now carries the Shepard edges in `later_edges` with "in part"
rows as `partial_*`. Counts from `try`: 548 decided (542 `no`, 6 `yes`), 722 open, 62 contradiction flags, each
explained in the doctrine's part (c).

- **Revocation branches.** B05-B09 use `edge_date` where the earliest held whole-order edge is the verified
  instrument (198 members). The other 24 use fixed dates or intervals (B05, B07, B08, B09).
- **Verification pass.** The pass behind the side table was widened, which took the verified list to 220
  members. The wider tests cover:
  - OCR spacing in "is hereby , revoked";
  - "This order supersedes ...";
  - members inside "Executive Orders Nos. ..." lists;
  - PLO headings in the forms "EO N", "Executive Order No. N" and "revoking Public Water Reserve No. N", when the
    member created that reserve;
  - date citations confirmed by the revoking order's WPA summary.
- **Deferred revocations.** Whole revocations that take effect only on a plat filing became a new open branch
  (B29, 31 members).
- **Ex-service openings.** B21 uses `order_date_plus_days` (154 days, or 119 for EO 3758).
- **Spent and merged orders.**
  - B20 is `spent_on_issue`. Restorations that keep a right or purpose moved to B19, which is open.
  - B24 is `merged_into_parent_on_issue` for 10 listed amend-only members, with the P2 disclosure. Amendments that
    add land are on B26, which is open.
  - B23 is limited to 10 single completed acts. Licences, rights-of-way and other continuing-use permits are on
    B25, which is open.
  - EO 2491 was moved out of B20, because its text also withdraws additional land.
  - EO 4044 is ended on 1924-07-30, when EO 4055 vacated its restoration.
- **Other.** B01 is split by family (P4: named persons go to PD-CS-ONE-PERSON). Source S0 is `member_text` (P6).
  The B02 and B03 bases name their records as not yet retained, and their gaps give the exact acquisitions.
- **Fetch list.** FETCH_PROPOSED.jsonl now has 140 lines, including 124 PLOs. Roughly 45 more minutes.

## 2026-11-06: changes after the two blind reviews (REVISION_BRIEF.md)

I ignored the planted errors as instructed. Those were 84 Stat. 1007; the B05_5384 bound of 1977-04-06; 90 Stat.
2768; and the B05_1713 bound of 1981-07-15. My file has 84 Stat. 1067, 1070; 1967-04-06; 90 Stat. 2786; and
1981-01-15. Every other finding was checked against the held texts.

After the changes, `try` decides 489 (485 `no`, 4 `yes`), leaves 781 open, and reports 51 contradiction flags.
The doctrine's part (c) explains each flag.

### Accepted and fixed

- **Revocations deferred to a plat filing** (A R1, B R1; coordinator adjudication 1). A new branch, B19D, keeps
  open every revocation or restoration whose own text defers its effect. The wording is "effective upon the date
  of the official filing ..." or "... shall become effective upon ... such date". There are 50 such members,
  including EO 7486, which needed a pattern that tolerates OCR.
- **EO 3867** (A R2, B R3). EO 4653 revoked it "only as to" two townships. "Only as to" now fails verification, so
  EO 3867 falls to B30 (open).
- **EO 6774** (B R2). The revoking order is EO 8241, held in `jobs/fr-originals/output/texts/EO_8240.txt`. Its
  effect is deferred to the plat filing, so EO 6774 is on B29 (open).
- **EO 4901** (B R9). EO 8529 takes effect on its sixtieth day, so the end date is fixed at 1940-10-26. The held FR
  text is now cited.
- **EO 4044** (B R6; adjudication 3). EO 4055 vacated the restoration only for the Chugach tracts. The lead is now
  P1 `spent_on_issue` on 1924-07-03. The EO 4055 edge remains as a disclosed flag.
- **EO 3529 and 5136** (A R10, B R7; adjudication 4). They are now on B24_REGS under P2, merged into EO 3489. The
  basis notes 43 CFR 2566.0-3 as the parent's current predicate. B02 keeps only EO 3489.
- **EO 4867, 324B, 5931 and 576 leave B20** (A R5, A R6, B R8; adjudication 5). EO 4867 and 5931 fall to B35,
  EO 324B to B26, and EO 576 to B33. All are open.
- **EO 2641** (A R7, B R10). It is now on B24, which uses its member list without a text condition.
- **EO 1584 and 6734** (B R11, in part). They moved to B26 (open), because each also withdraws or adds land of its
  own.
- **Named-person orders** (A R12; adjudication 6). B01_PERSON now lists EO 975, 1135, 2501, 2551, 2712, 3178,
  4015 and 6170 and routes them to PD-CS-ONE-PERSON. B23 keeps five conveyance, selection or exchange orders.
- **The cited "coordinator ruling 4" did not exist** (A R11, B R15; adjudication 7).
  - B23 now rests on P1.
  - B25 rests on this doctrine's own reasoning under D-20261028-evidence-decides.
- **B10 check** (B R16; adjudication 8). On 2026-11-06 I checked all 24 members of the B10 "until March 5, 19xx"
  branch for a later act on them. The sources were the members' Shepard and later-events edges, and BLM PLO table
  rows whose eo_refs or subject contain the number.
  - No member has a later instrument acting on it.
  - EO 3895's only edge is a misattributed date citation, now marked partial.
  - The PLO-table hits all turned out to be PLO numbers or dates, not EO references.

  B10 stays TERM, with the check recorded in its gaps.
- **Misrouted members** (A R14, B R17).
  - OCR damage had misrouted EO 4092, 4735, 4855 and 4936; they are now listed on B21_63. EO 1878 and EO 3651 are
    now listed on B10.
  - EO 3077 is excluded from B01 and falls to B35.
  - EO 413 reaches B34, now placed before B26.
  - EO 6171 is listed on B22.
  - EO 3192 is dated day 70 on its own branch, B21_3192 (B R21).
- **Indian reservations** (A R16). A new branch, B01_INDIAN_RES (29 members), routes reservations for Indian use,
  occupancy, schools or agencies to PD-INDIAN. Its basis cites 25 U.S.C. 398d (44 Stat. 1347). Irrigation-project
  sites and the Episcopal mission site stay on B35, because they are ordinary withdrawals.
- **Doubled-escape regex** (A R17, B R18). "modified,?\s?and" is now written with a single escape.
- **Year-only dates on B07** (A R18). They are now fixed from the held texts:
  - EO 1291: 1925-09-25.
  - EO 2060: 1916-09-20.
  - EO 4764: 1928-09-26.
- **B08** (A R13). The earlier edges are partial or non-revoking. EO 9026 says it "shall not rescind or revoke".
  B08 is now dated by the PLO, and the earlier edges are disclosed.
- **B05** (B R20). M1 and S0 were dropped from B05_1713 and B05_5384.
- **PLO correction pages** (B R14). PLO 1296, 5976, 6333 and 6989 now cite their own pages: 21 FR 2946, 46 FR 35504,
  47 FR 39824 and 58 FR 38083. The correction pages follow. The appendix and FETCH_PROPOSED.jsonl both changed.
- **Held paths** (A R20, B R19). The appendix now cites held paths: EO 8529 for EO 4901, and EO 5877 for EO 4958.
- **Counts and contradiction disclosure** (A R8, A R9, B R12, B R13). These were restated from the run.
  - The 14 members that now carry only `partial_` edges are no longer flagged.
  - B99 now describes what it holds (A R19).

### Rejected, with reasons

- **EO 6016 and EO 7038 stay on B24, merged under P2** (B R11, in part). Each order's only content is a general
  amendment of EO 5327's terms. EO 6016 authorizes oil and gas permits and leases "for any of said lands"; EO 7038
  does the same for sodium. Neither is a licence or permit granted to a named party or project. That matches
  EO 2354 (timber use under the Alaska townsite withdrawals) and EO 7047 (settlement on EO 6957 lands), which the
  reviewers did not question. B25 is reserved for permissions granted to a party or project.
- **EO 4266 and EO 4949 stay open** (A R14, in part). Each also reserves land of its own, so neither is only a
  revocation with an opening:
  - EO 4266 adds lands to an experiment station.
  - EO 4949 reserves part of the excluded land for railroad use.

### Other

- P7 and P8 decide no member here. No held instrument abolishes by name the subject of a member, such as a land
  district. The Indian trust-period orders that P8's converse would reach are routed to PD-INDIAN (B01_INDIAN).
- About 60 more minutes.
