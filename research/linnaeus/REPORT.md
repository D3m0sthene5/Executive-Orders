# Linnaeus, 2026-11-10: the undecided orders with no lead, by type, and one bulk source per type

Track 4 of the Respondendi follow-up (owner-approved): classify the undecided orders that have no ending or current-law
lead by type, find one bulk status source per type, run it against the whole type. Plus the owner-approved Tier A
idea #6 (double-entry reconciliation), added mid-session. Named for Carl Linnaeus, whose *Systema Naturae* (1735)
sorted every living thing by kind. Nothing here adopted a status, changed a count or certified anything; a source's
silence about an order is never evidence about it. Human-certified: 0.

**In one paragraph.** The 4,174 no-lead orders are not one acquisition problem. 1,096 already have a Pothier family
status lead that no claim-kit code reads, and 260 have a held ending lead (BLM PLO tables, the 1989 OFR table, OFR
notes) that `STATUS_LEADS` does not carry: about a third is routing. Of the 2,818 unsourced, 665 are one-person
civil-service waivers (Ulpian's track). Every candidate disposition table was measured: NARA's HTML tables add
nothing beyond the FR API notes already held, the Lord 1944 list carries no later dispositions, BLM's withdrawal
database has no order-number field, and FS-612 names 7 orders by number in a later row. The one source that reaches
every family by explicit number is full text: the 1936-1993 Federal Register and the Statutes at Large, searched
through govinfo. That is `jobs/cruden-fr-concordance`: of 2,110 targets it gives 256 a hash-pinned citation, 111 a
date-confirmed one and 21 a sentence published as acting (about 80% right by the coordinator's reading). A hostile reviewer (two
passes) found three blockers in Cruden's first version; all were fixed before anything was published as acting.

## 1. The no-lead set, measured on main

Definition (Respondendi's S5, `research/excavator/claude-respondendi-2026-11-10/DESIGNS.json`): undecided in the
readiness tracker, and the claim kit's `STATUS_LEADS.jsonl` record has no `lead_actor_ids`, no `own_terms` and no
`current_law_leads`. Recomputed by `jobs/linnaeus-types` (run
[42854906849](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42854906849), `output/STATUS.json`
succeeded): **4,174 of 10,691 undecided orders**, exactly Respondendi's figure.

| Stratum | Orders | Meaning |
|---|---:|---|
| `pothier_decided_lead` | 1,096 | A Pothier doctrine proposes a status (861 own-terms NO, 213 named-act NO, 22 current-record YES); no claim-kit code reads Pothier leads |
| `held_ending_lead_unrouted` | 260 | A held finding aid names the order with an ending word (Shepard PLO-table or later-events ending edge, 1989-table `ended_by_1989` row, Selden ending class) but `STATUS_LEADS` does not carry it |
| `unsourced` | 2,818 | No held finding aid names it with an ending word; 388 of these are named without one (amendments, cross references, in-force or merged 1989 rows) |

By era: 1862-1906 310; 1907-1936 3,113; 1937-1945 516; 1946-1989 150; 1990-2026 29; undated 56. Overlap with the M1118
pre-1937 original-text gap (film-only rows of `research/photius/RESIDUAL.csv`): **1,037**, plus 109 whose ProQuest
replica check failed or was not read.

## 2. By type

Full table: `jobs/linnaeus-types/output/TYPE_TABLE.md`; one row per order: `NO_LEAD_TYPES.csv`. Families come from
X1's type rules (`jobs/x1-class-engine`), the X1 taxonomy on APP titles, Linnaeus title patterns, Pothier doctrines and
the title's form. A spot check of 15 random rows found 2 doubtful families (EO 6066, a one-person Foreign Service
retention filed as customs/consular; EO 5627, a class of employees filed as one-person); types are routing hints.

| Family | No-lead | Pothier decided | Held, unrouted | Unsourced | M1118 film gap | Matched bulk source |
|---|---:|---:|---:|---:|---:|---|
| CS_ONE_PERSON | 802 | 86 | 51 | 665 | 345 | Official Register (Ulpian, Track 3) |
| LAND_WITHDRAWAL | 632 | 195 | 32 | 405 | 66 | FR 1936-1993 number search (PLOs, restorations) |
| CS_RULES | 421 | 273 | 14 | 134 | 269 | FR number search (CSC rules, 5 CFR) |
| NATIONAL_FOREST | 406 | 148 | 11 | 247 | 32 | FR number search (FS-612 measured, not built) |
| ORGANIZATION | 241 | 30 | 18 | 193 | 15 | FR number search |
| WAR_EMERGENCY | 215 | 23 | 10 | 182 | 34 | FR number search (the 1921 joint resolution names no order) |
| CUSTOMS_CONSULAR | 210 | 75 | 18 | 117 | 24 | FR number search |
| REGULATIONS | 209 | 55 | 34 | 120 | 36 | FR number search |
| MILITARY_RESERVATION | 205 | 89 | 9 | 107 | 77 | FR number search |
| UNKNOWN | 180 | 0 | 26 | 154 | 31 | type first; FR number search |
| SPENT_ONE_TIME | 135 | 18 | 4 | 113 | 26 | the order's own text (Respondendi F5) |
| REFUGE_LIGHTHOUSE | 123 | 49 | 5 | 69 | 28 | FR number search |
| DESIGNATION | 120 | 5 | 7 | 108 | 15 | FR number search |
| TERRITORIAL | 91 | 7 | 10 | 74 | 15 | FR number search |
| INDIAN_LAND | 57 | 19 | 1 | 37 | 13 | FR number search |
| CANAL_ZONE | 50 | 4 | 6 | 40 | 9 | FR number search |
| AMENDING_OR_REVOKING | 41 | 0 | 4 | 37 | 0 | own text and the parent's status (Pothier P2) |
| NRA_CODE | 36 | 20 | 0 | 16 | 2 | FR number search (Schechter names no order) |
| **Total** | **4,174** | **1,096** | **260** | **2,818** | **1,037** | |

## 3. Candidate bulk sources, measured

Measurements and the hashes of what was read: `research/linnaeus/SOURCE_MEASURES.json`.

| Source | Access | Reaches | Verdict |
|---|---|---|---|
| NARA FR EO disposition tables, 1937 on | archives.gov HTML; 66 pages read, about 19 year or president pages now 404 or moved | 694 no-lead orders are EO 7532 or later: 665 have an entry, 110 a later note, 31 an ending note, **0** ending notes missing from the FR API catalog | No job reads the HTML, but `later-events` reads the same OFR notes from the federalregister.gov API. Nothing to add; not built. (A first parse said 6; the reviewer showed entries headed "Executive Order No. N" inherited the previous entry's notes.) |
| OFR Codification 1945-1989 table | held (`ofr-codification-1989`) | 173 no-lead orders have an `ended_by_1989` row | Held, read by claim-drafts and Shepard, not by `STATUS_LEADS`: routing |
| Lord 1944 WPA numbered list | held (`x1-class-engine/data`) | 3,337 have an entry | **No later dispositions**: 0 "revoked by"; entries summarize the order's own command. Used for typing and now for pre-1937 dates |
| BLM Tables of Public Land Orders | held (`shepard-citations`) | PLO-table ending edges on no-lead orders | Routing (claim-kit `build.py` drops non-census actors, Respondendi F4) |
| BLM MLRS withdrawal cases | public ArcGIS, no key | national service: 7,819 authorized or interim, 483 pending, 41,325 historic cases, **no order-number field**; OR/WA layer: 3 distinct EO numbers | Fails the explicit-number test; not built |
| Forest Service FS-612, 1891-2012 | govinfo GOVPUB-A13-PURL-gpo107042 | 236 named by their own number; **7** by number in a later row | Same-forest chains do not name the order (D-20261021-unnamed-instruments); the later rows are PLOs the FR search reaches; not built |
| FWS Annual Report of Lands | fws.gov | units, not orders | needs a reviewed crosswalk |
| U.S. Code and CFR notes | held (`current-law`) | 0 by definition | already searched |
| NEA notices | FR | 46 no-lead orders dated 1976 on; 0 emergency orders | reaches none |
| Official Register | HathiTrust, Internet Archive | 665 unsourced waivers | Ulpian |
| Agency annual reports | CSC reports held | waivers | print and count waivers, never record use (F-20261028-6) |
| **FR 1936-1993 full text, by number** | govinfo search (repo secret; 36,000 an hour), content PDFs public, GPO PREMIS hashes | 2,110 Cruden targets | **built** (section 5) |
| **Statutes at Large, by number** | govinfo `collection:STATUTE` | same targets | **built**, second collection of Cruden |

Two plumbing defects found on the way (Kean F-20261110-frdoc-actors-dropped): `selden-fr-citers` writes 4,070 acting
fragments whose actor is `FRDOC:<number>`, which `jobs/claim-kit/inputs.py` `NON_EO_ACTOR` does not accept, so none
becomes a claim-kit pair.

## 4. Ranked type-source pairs

Every source here costs no model tokens; the cost is runner time and, for routing, a reviewed kit change. Bentham
counts no unlock for an undecided order until it has a status, so its dossiers-per-dollar measure does not separate
these; the ranking is by orders that gain an explicit-number lead, measured.

| Rank | Pair | Orders reached | Measured | Cost | Built |
|---:|---|---:|---|---|---|
| 1 | Route held leads into the claim kit (Pothier statuses; held PLO-table, 1989-table and OFR ending edges; FRDOC actors) | 1,356 no-lead (+4,070 FRDOC fragments elsewhere) | held now | reviewed claim-kit PR | proposed as a separate session |
| 2 | All non-waiver families x FR 1936-1993 number search | 2,110 | 256 located, 111 date-confirmed, 21 acting | about 1.5 runner hours, 22 GB | yes (Cruden) |
| 3 | Same x Statutes at Large | 2,110 | 3 located, 2 acting | minutes | yes (Cruden) |
| 4 | National forests x FS-612 | 7 | measured | one PDF | no |
| 5 | Post-1937 x NARA HTML | 0 | measured | 90 pages | no |
| 6 | Land x BLM MLRS | 2 (already YES leads) | measured | free API | no |
| 7 | One-person waivers x Official Register | 665 | Ulpian | Ulpian | Track 3 |

Bentham: `acquire.cruden_fr_statute_concordance` (`jobs/bentham/candidates.py`) is a free acquisition whose lift on
`status_assignment.undecided` (2,110 orders) is listed, not counted, until a measured rate exists.

## 5. Cruden: runs and measured yield

| Run | Locator | Result |
|---|---|---|
| 42852122881 | 1 | cancelled after the hostile review (blockers) |
| 42856013837 | 2 | succeeded; **controls failed** (dated recall 14/30), so every fragment was written as a pointer. Misses traced to the scan's column interleave splitting dates, and to WPA-only dates missing |
| 42867104942 | 3 | succeeded, controls passed (22/30 dated, 17/30 published acting); 42 targets with a dated acting sentence. A precision read of all 27 acting targets: 16 fully right, 2 right relation but wrong actor (a Statutes margin tag), 9 wrong (customs-table amendments, the order cited as authority, the order as actor) |
| 42881031186 | 4 | read 792 issues, controls passed; failed only on job.py's own nothing-done check (fixed) |
| [42887085843](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42887085843) | 4 | **succeeded, controls passed**: 22/30 dated, 19/30 published acting, 0 of 396 near-miss negatives and 0 of 12 identity negatives located; 3,072 targets x 2 collections queried; 841 issues or pages read (22.6 GB), 5 failed |

Measured yield (final run; `jobs/cruden-fr-concordance/output/SUMMARY.json`):

| Target list | Targets | FR search hits | Located citation (pinned bytes) | Printed date confirms identity | Dated sentence published as acting |
|---|---:|---:|---:|---:|---:|
| Linnaeus unsourced, non-waiver | 2,110 | about 414 | **256 (12.1%)** | **111 (5.3%)** | **21 (1.0%)** |
| Nalimov decided, no later instrument, below EO 7532 | 962 | about 100 | 31 (3.2%) | 6 | 2 |

Acting sentences by family (Linnaeus): land withdrawal 6, national forest 6, refuge or lighthouse 2, military 2, one
each in regulations, customs, organization, territorial, unknown. Statutes at Large add 2 (EO 3528's revocation by
statute among them in locate-3; the Statutes collection reaches few pre-1937 orders: 31 of 3,072 had hits). By the
coordinator's reading of the 21, about 17 print a relation that acts on the order (EO 3149's printed relation word
is wrong; EO 5264, 8738 and 9521 are column-interleave misreads). Precision is therefore about 80%, and every
fragment is a lead a producer reads, never an end.

Refused (kept in `LOCATED.csv`, never published): 131 in the order's own printing, 42 with a disagreeing printed
date, 39 whose bytes are neither committed nor a GPO PREMIS match (the 80 MB extract cap filled), 3 split or longer
numbers. Cost: zero model tokens; about 1 to 1.5 runner hours and 22 GB of govinfo downloads per full run; 4,280
searches against govinfo's 36,000-an-hour limit.

**Verdict.** Full-text number search is the one bulk route that reaches every family by explicit number, but on
pre-1937 orders it reaches few: about 1 in 8 gets a pinned pointer to a later printed page, 1 in 20 a date-confirmed
one, 1 in 100 a sentence a machine may call acting. The scan's three-column interleave, not the index, is the limit.
The larger lever stays routing (rank 1, 1,356 orders already held).

## 6. Pacioli: double-entry reconciliation (Tier A #6)

`jobs/pacioli-double-entry` (run [42860052386](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42860052386),
`STATUS.json` succeeded). Three compilers keep independent tables of later events: OFR (online notes, which NARA's
HTML tables print, the 1989 table and eCFR, one family), OLRC (U.S. Code note status lines) and BLM (PLO tables). The
Lord 1944 list has no dispositions. A pair agreed by two families (same relation class, same whole/part scope, no
disagreeing date) is published with every table entry pinned (job, record id, locator, sha256, quote) and the acting
instrument's held text (path, sha256). Format for Nalimov: `jobs/pacioli-double-entry/README.md`.

| Measure (on main) | Orders | Undecided | Decided, not ready |
|---|---:|---:|---:|
| Agreed later event (any) | 966 | 546 | 252 |
| Agreed whole ending | 629 | 367 | 118 |
| Agreed whole ending, actor's text held | 604 | 362 | 113 |
| On the disagreement list (67 pairs: class 30, scope 34, date 32) | 59 | 41 | 14 |

Agreed pairs: OFR+OLRC 1,644, BLM+OFR 8. Only 4 of the 367 undecided agreed-ending orders are in the no-lead set: the
reconciliation helps orders that already have leads skip the finding step (Nalimov, Respondendi's lot); it does not
reach Track 4's set. OLRC may have read OFR's tables, so OFR+OLRC agreement is two finding aids agreeing, not proof;
the claim still quotes the actor's own text.

## 7. Hostile review

Fresh-context Fable 5.2 reviewer, read-only, briefed with the code and rules, not the author's conclusions. Pass 1
(174,299 tokens, 23 tool calls, 349 s) found three blockers: an order's own FR printing published as its own ending;
the acting instrument inferred from proximity; other numbered series (governors, Canal Zone, states) passing when
the issuer was printed before the number. And nine majors: split and suffixed numbers, unread date forms, true
citations refused for subject words, exception sentences published as endings, vacuous controls, custody gaps,
Linnaeus's "ending lead" counting non-ending 1989 rows, an overstated README, and the NARA miscount. Pass 2 (total
226,102 tokens) confirmed the blockers closed except a residual proximity actor (damaged filing lines, agency
headers), and found new over-refusals (list members, later dates, title lines, ordinary qualifiers). All were fixed
in `cruden-locate-3` and `-4` with a regression test each (17 tests); the controls now gate on both dated location (0.6) and
published acting recall (0.4) plus 12 fixed identity negatives. Silence: no zero-hit, refused or failed search writes a
fragment in any version (checked by the reviewer and by `test_silence_is_never_a_fragment`).

## 8. Costs

Coordinator: Claude Opus 5.5 (this session). Worker: one Fable 5.2 reviewer, 226,102 tokens over two passes. Jobs:
zero model tokens; GitHub Actions runs listed above; govinfo search with the repo's key.

## 9. Nalimov's acquisition lists, measured (requested 2026-11-10)

- **Official copies of 180 acting orders (219 express-revocation pairs):** 170 of the 180 are already credited
  `original_supported` by the tracker and 133 have their Federal Register text committed under
  `jobs/fr-originals/output/texts/`; only 10 lack an official copy (6 missing, 4 transcription-only). This is a routing
  gap (held actor texts not reaching the frozen dossier, Respondendi F4), not an acquisition. 55 of the 219 pairs are
  also double-entry agreed in Pacioli.
- **1,483 decided orders with no held later instrument:** Pacioli agrees on 10 (8 whole endings; 2 more disagree).
  Cruden searched the 962 below EO 7532 (`EXTRA_TARGETS.csv`): 31 get a located citation, 6 a date-confirmed one, 2 a
  sentence published as acting.
