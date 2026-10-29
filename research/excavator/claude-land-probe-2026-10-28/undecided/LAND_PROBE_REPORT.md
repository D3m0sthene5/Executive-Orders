# Land probe: twelve land orders with no provisional status (2026-10-28)

Start: 2026-10-28T20:00:17Z. End: 2026-10-28T20:21Z (report written; worksheets finished at 20:18:04Z).
Agent: Claude (subagent). No statuses, ledgers, codebook rows or counts were changed. Certified: 0.
Per-order findings, citations and needed evidence are in `WORKSHEETS.jsonl` in this folder.

## Results

| Order | Type (as researched) | Proposed status | Basis | Held? | Confidence |
|---|---|---|---|---|---|
| EO 1237 (1910) | naval reservation, Cordova Point, Alaska | no | Rescinded by EO 4204, 1925-04-15; land restored to Chugach NF status | yes | high |
| EO 1304 (1911) | lighthouse-land restoration, Florida | no | Replaced "in lieu of" by EO 1311, 1911-03-01 (EO 1304 omitted township and state) | yes | high |
| EO 3853 (1923) | Devils Lake trust-period extension | no | Own ten-year term expired during 1933; EO 5953 (1932) extended from that expiry | yes | high |
| EO 4810 (1928) | withdrawal in aid of legislation, Wyoming | no | Revoked by EO 6679, 1934-04-16 | yes | high |
| EO 7069 (1935) | Power-Site Restoration No. 481 | no | Partial revocation of PSR 325; spent on issue 1935-06-11 | yes | high |
| EO 709 (1907) | Navajo Reservation addition | yes | New Mexico parts restored by EO 1000 (1908) and EO 1284 (1911); Arizona part continues inside the boundary defined by Act of June 14, 1934, 48 Stat. 960 | partly (statute not held) | medium |
| EO 6740 (1934) | Public Water Reserve No. 155 | yes | Wyoming tracts revoked by PLO 7330, 63 FR 28516, effective 1998-06-25; Utah tract: no revocation found | no (PLO not held) | medium |
| EO 5511 (1930) | classification withdrawal, Louisiana | yes | Standing "until revoked"; no revocation found | no | low |
| EO 5799 (1932) | McClellan Peak lookout site, Nevada | yes | Standing "until revoked"; no revocation found | no | low |
| EO 455 (1906) | nursery site in Salt Lake Forest Reserve | yes | Nursery closed about 1920, but no revocation found | no | low |
| EO 6210 (1933) | consolidation of Natural Bridge NF into George Washington NF | unknown (leans yes) | Proclamation 2165 (1936-04-21) moved a "Natural Bridge Division" to the new Jefferson NF; whether any former Natural Bridge land stayed in the GWNF is not established | no | low |
| EO 2901 (1918) | Fort Armstrong enlargement, Honolulu | unknown (leans no) | Merged into EO 5487's 1930 description; later partial disposals (EO 9861, 10309, 10597, 10603) do not identify this tract | partly | low |

Five of the twelve (1237, 1304, 3853, 4810, 7069) closed with high confidence from texts the project already holds. The project's later-events file (`jobs/later-events/output/EDGES.csv`) has no edge for any of the twelve, and the class engine's `EVENT_CANDIDATES.csv` offers only the FLPMA 1976 continuity point for all twelve. Every end found came from reading other held texts or from the web.

Each "yes" for a standing withdrawal (5511, 5799, 455, and the Utah tract of 6740) rests on the absence of a revocation in the sources searched. Those were the held corpus, the Federal Register full text from 1994 on (FederalRegister.gov API), and general web search. Public Land Orders from 1942 to 1993 and BLM land-status records were not searchable. These "yes" findings are provisional hypotheses under the presumption that a withdrawal continues until revoked (ruling 3: an end needs a reason). They are not findings of current status.

## Where the time went

**Observed.** Wall clock for the run was about 21 minutes. Shared setup took about 3 minutes: reading the rulings and seven type rules, locating texts, and checking the edge and candidate files. Building and running a reverse-citation scan over every held text took about 3 minutes (the scan itself ran 1 min 49 s). That left about 15 minutes of per-order work. Federal Register and GovInfo API calls from the shell were refused by the egress proxy, as were downloads from the UNT web archive. Those sources were reachable only through WebFetch, which summarizes the page and can lose detail in long PDFs.

**Estimates.** The per-order minutes in the worksheets are estimates; no timing system was used. They allocate the per-order time by the order of tool calls and are scaled to the observed wall clock.

| Step | Minutes (sum over 12) | Share |
|---|---|---|
| Finding later instruments | 6.7 | 46% |
| Getting instrument texts | 3.3 | 23% |
| Text and clauses | 1.8 | 12% |
| Savings and contrary evidence | 1.4 | 10% |
| Writing | 1.4 | 10% |

| Type | Orders | Minutes (estimate) | Note |
|---|---|---|---|
| National forest (6210, 5511, 5799) | 3 | 5.6 | Two ended without a decision; boundaries are defined by diagrams, and no per-forest chain is held |
| Military (1237, 2901) | 2 | 2.7 | 1237 took under a minute; 2901 needed a chain of 13 Fort Armstrong orders and still has no end |
| Indian (709, 3853) | 2 | 2.1 | The held 1912 GPO compilation and Wikisource notes gave the chain; only the 1934 statute came from the web |
| General withdrawal (4810, 455) | 2 | 2.0 | 4810 took half a minute; 455 used 1.5 minutes on searches that found nothing |
| Water reserve (6740) | 1 | 1.3 | Closed in part by one PLO found by web search |
| Lighthouse (1304) | 1 | 0.5 | Held replacement order |
| Power site (7069) | 1 | 0.4 | A restoration, so spent on issue |

The pattern is the observation that matters most. Orders whose end is recorded in another held text closed in about 0.5 minutes each. Standing withdrawals with no recorded end cost about three times as much, because the searches came back empty, and they still ended at low confidence. Multi-instrument reservations whose lands are described by metes and bounds or by diagram (2901, 6210) cost the most and remained undecided.

## Instruments and sources that recur

- **Later executive orders that revoke, restore or supersede.** Pre-1942 ends are almost always another executive order: EO 4204, 1311, 6679, 1000, 1284, 1995, 5487, 9861, 10309, 10597 and 10603. They cite the earlier order by number ("Executive Order No. 4810"), by date ("Executive order of December 12, 1912"), or by reserve number ("Power-Site Reserve No. 325", "Public Water Reserve No. 155"). The phrases "revoked", "rescinded", "restored to", "in lieu of" and "revoking in part" mark the act.
- **Public Land Orders (1942 on).** Post-war ends of withdrawals and water reserves, such as PLO 7330 in 1998, cite orders by date and reserve number, not by EO number. One PLO typically revokes parts of dozens of orders.
- **Confirming or defining statutes.** The Act of June 14, 1934 (48 Stat. 960) for Navajo lands, FLPMA s.701 as a continuity point, the Hawaiian Organic Act s.91 for Fort Armstrong, and the Indian Reorganization Act s.2 for trust periods.
- **Proclamations** for forest boundaries, such as Proclamation 2165 creating the Jefferson NF, with boundaries often drawn only on attached diagrams.
- **Compilations the project already holds:** the 1912 GPO "Executive Orders Relating to Indian Reservations", the Wikisource "Amended by" notes, the ProQuest replica scans, the Hathi GPO volumes and the APP transcriptions.
- **Land-status records** (BLM MLRS, master title plats) and the Forest Service boundary-history tables. These were needed for every open "yes" or "unknown" and are held for none.

## Missing sources that would unblock the most orders

1. **BLM land status by legal description** (MLRS case records or master title plats). These would decide the four standing withdrawals (5511, 5799, 455, and the Utah tract of 6740) and test every "yes" that now rests on not finding a revocation. Across about 3,000 land orders this is likely the largest single unblocker, because most withdrawals are small Pickett Act tracts (an estimate from this sample, not a measurement).
2. **An index of Public Land Orders 1942-1993**, giving number, date, FR citation, the orders and reserve numbers revoked, and the lands. Candidate sources are the BLM PLO tables on blm.gov and the digitized Federal Register 1936-1994 on GovInfo. This index would serve the same four orders and every water reserve, power site and lookout withdrawal.
3. **The Forest Service table "Establishment and Modification of National Forest Boundaries and Names"** (FS-612), or an equivalent chain of proclamations for each forest. This would decide EO 6210 and most national-forest boundary and renaming orders.
4. **Held copies of recurring statutes and PLOs:** 48 Stat. 960 and 63 FR 28516-28521 (PLO 7330). Fetching each once and adding it to the holdings removes the "held: false" flag from EO 709 and EO 6740 and from any other order that cites them.
5. **Hawaii disposal records:** Army and GSA deeds and Admission Act s.5(e) conveyances. These are needed for EO 2901 and the rest of the Fort Armstrong and Kakaako group.

## Steps a machine job could do

- **Reverse-citation index over all held texts.** For each order, list every held text that names it by number, by date phrase, or by reserve number (PWR, PSR, RSR), with the acting phrase. A 40-line prototype ran in under 2 minutes over the whole corpus and found the ends for 1237, 1304 and 4810, plus the full Navajo and Fort Armstrong chains. None of these was in EDGES.csv, because that job parses only the OFR disposition notes from 1937 on. The prototype script is at /tmp/claude-0/-home-claude/ff3ec4d2-0950-5dc7-b1ab-b629bafe81d8/scratchpad/revcite.py (scratch only; not committed).
- **Spent-on-issue classifier.** Titles or texts containing "Restoration No.", "revoking in part", "Revocation of Executive Order No." or "in lieu of" mark orders whose whole effect is the act itself, as with 7069 and 1304. Such orders can be proposed "no" in bulk and turned into end edges for their parent orders.
- **Trust-extension table.** For each reservation and expiry year, list the extending order and its successor. This closes own-terms extensions such as 3853 mechanically.
- **Date and identity checks.** Several held texts carry errors a job could flag. OCR years are wrong for 6210 (1938), 6679 (1984) and 7069 (1936); a check of each printed date against its volume's date range would catch these. EO 5799's date in X1 (1932-02-13) differs from its texts (02-15). EO 709's APP title ("Camp McDowell") is wrong. APP lists the NRA silk order as a duplicate EO 6210 (the clause-drafts copy calls it 6210-A).
- **Type re-check.** X1 typed EO 5511 (a classification withdrawal) and EO 5799 (an administrative site outside a forest) as national-forest boundary orders. It also gave no restoration flag to 1304 and 7069. A rule-based pass on the operative verb (withdraw, restore, consolidate, extend) would correct most of these.
- **Fetching Federal Register PLOs.** The FederalRegister.gov API (1994 on) and the GovInfo search API (historical FR) answer exact-phrase queries such as "Public Water Reserve No. 155". They are blocked from this session's shell but could run as a GitHub Actions job.

## Recommendations for reusable resources

1. **Build the reverse-citation index as a committed job.** A suggested name is `shepard`, after Frank Shepard's citator (1873), which listed every later citation of a case. It should key on EO number, date phrase, reserve number and reservation name, and it should feed EDGES.csv as leads. This sample suggests it would close a large share of pre-1942 land orders without web work. That share is an estimate from 12 orders; testing it on a few hundred land orders is the next step.
2. **Build a PLO table job** from the BLM PLO tables and the FR (1994 on via the API, 1942-1993 via GovInfo FR volumes), run in Actions, recording the lands and the revoked orders and reserves for each PLO.
3. **Request land-status access.** Ask for MLRS or master-title-plat access, or a bulk export, so that "no revocation found" can become "current basis checked against the land record". Without it, every standing-withdrawal "yes" stays low confidence.
4. **Build reservation and forest chain files**, generated once and reused by every order in the chain: the Navajo additions, Fort Armstrong, each national forest's proclamations, and each power-site and water-reserve number.
5. **Fetch recurring statutes once** (48 Stat. 960, 48 Stat. 984, FLPMA s.701 and s.704) and the PLOs found here into held sources, so later worksheets can cite them as held.

## Limits of this probe

The sample is 12 orders chosen by the caller. Rates and minutes are from one run and one agent, and minutes are estimates. "No revocation found" covers only the sources named above. As the caller asked, no git commands were run. The CLAUDE.md steps for recording results in the Kean register were therefore not done, and the parent session should record them.
