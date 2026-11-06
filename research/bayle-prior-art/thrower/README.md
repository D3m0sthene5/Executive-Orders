# Bayle / Thrower: the AJPS executive-order longevity data against the project's register

Prior-art stream "Bayle" of the Encyclopedie campaign. This folder compares Sharece Thrower's replication data for
her study of executive-order revocation with what the project holds. Everything here is a **lead**, never a fact
and never a status change. The certified whole-lifecycle count is untouched.

## Sources

**Dataset** (CC0; Harvard Dataverse terms: "made available under a Creative Commons CC0 license"):
Thrower, Sharece, 2016, "Replication Data for: To Revoke or Not Revoke? The Political Determinants of Executive Order
Longevity", https://doi.org/10.7910/DVN/LZGQOH, Harvard Dataverse, V1 (API reports version 1.1, released 2018-12-11),
UNF:6:HoWUG8bvlsiqOgxKJ59NUg== [fileUNF]. ZIP 8,080,973 bytes, SHA-256
`c641a12e2dbf8e827999cbb531dabbe7fcc402f20488c93da4847a95eda3f9a2`; the hash of every unpacked file is in `MANIFEST.json`.

**Article** (a separate work, not the dataset): Sharece Thrower, "To Revoke or Not Revoke? The Political Determinants of
Executive Order Longevity," *American Journal of Political Science* 61, no. 3 (2017): 642-656,
https://doi.org/10.1111/ajps.12294. The deposit's README says her sources were the National Archives disposition
tables and the American Presidency Project.

**Project side** (read with `git show origin/main:<path>`, commit `57b814115b176d99ef7220ab279dc03edc61281b`, recorded
with blob ids and hashes in `PROJECT_INPUTS.json`): `jobs/domesday-register` (REGISTER.csv),
`jobs/later-events` (EDGES.csv, CATALOG_INDEX.csv), `jobs/ofr-codification-1989` (DISPOSITION_1989.csv),
`jobs/readiness-tracker` (READINESS_BY_ORDER.csv), `jobs/status-history` (events shards), `jobs/peano-formulario`
(lemma shards). `census-completeness` and `census-candidates` cover pre-1937 orders and were not needed.

## What is here

| File | What |
| --- | --- |
| `thrower_orders.csv` | 6,158 rows (one per order, 1937-2013), the deposit's 40 columns unchanged plus `instrument_id` (7677-A -> EO:7677A), `base_number`, `suffix`, and `revokedbyeo12553` (from the main .dta; see below). 693,508 bytes. |
| `MANIFEST.json` | hashes of the source files, `thrower_orders.csv` and every result file; the project commit; a deposit self-check |
| `COVERAGE_*.csv/json` | deliverable 2 |
| `DISAGREEMENTS.csv`, `CROSSCHECK_SUMMARY.json`, `ORDER_FACTS.csv`, `AGREEMENT_BY_DECADE.csv`, `EXPECTED_AFTER_WINDOW.csv` | deliverable 3 |
| `SAMPLE15_draw.csv`, `SAMPLE15_hand_checked.csv` | the seeded draw and my reading of each case |
| `INHERITED_*` | deliverable 4 |
| `STRATA_*` | deliverable 5 |
| `scripts/` | `run_all.sh ARCHIVE WORKTREE REF CACHE` rebuilds everything; each script takes the archive path as an argument; `test_thrower_lib.py` runs first |

All numbers below come from those scripts.

## 1. The table

`eo_original_list.csv` has 6,158 data rows (the brief said 6,157; 6,158 is the count), 40 columns. Flags: revoked 1,580,
superseded 471, partrevoked 118 (partial revocations are all inside `revoked`: 117 of 118 have revoked=1), substantive_amended 455,
ceremonial 100. Two oddities of the deposit: (a) the codebook and the main .dta call a flag `revokedbyeo12553`
(372 orders, almost all revoke_year 1986) but the CSV's `revokedbyotherthaneo` (140 orders) is a different flag; they never
overlap, so I added the .dta's flag as the last column; (b) `temporaryandemergencyfunctions` is blank for all 499
orders of 1945-1948. The order-year .dta reproduces the CSV's `revoked` in all 6,158 orders.

## 2. Coverage

- Thrower's numbers run 7532-13655 with **no gaps**: 6,124 plain numbers and 34 lettered orders (7677-A ... 11359-A).
- The register holds 6,160 rows in that number range. **Thrower orders missing from the register: 0** after upper-casing the suffix
  (raw match: 1, because the register spells 7933-A as `EO:7933a`, a case defect copied from the OFR catalog label `7933-a`).
- **Register rows missing from Thrower: 2.** `EO:7700A` has the same date and nearly the same title as EO 7700 (an APP-index
  re-listing, probable duplicate in the register). `EO:10369A` has no date, title, text or OFR entry: probable phantom identity.
  Both are register-side leads (`COVERAGE_register_not_in_thrower.csv`).
- Thrower's universe equals the OFR catalog's: the catalog has exactly 6,158 rows in this range and the two sets are identical. No
  numbering gap and no non-EO item explains anything, because Thrower took the OFR list as given.
- **Year coding**: Thrower's `year` differs from the register date year for 106 orders. 104 are orders signed in January by an
  outgoing president and coded to the previous year (an apparent term-year convention: 26 in 1981, 17 in 1977, 14 in 1961, 12 in 2001 ...).
  The other 2 are OFR catalog date typos (EO 8969 dated 1946, EO 10276 dated 1961) where Thrower's year is right; the project
  already has them in `jobs/later-events/CATALOG_DATE_CORRECTIONS.csv`, but the register still shows the uncorrected dates.

## 3. Revocation cross-check

Project facts: later-events edges (OFR disposition-note edges and order-text edges) and the 1989 Codification table,
restricted to events dated by 2013 (Thrower's window; later events are in `EXPECTED_AFTER_WINDOW.csv`, 82 orders). Edge
classes: unqualified revocation/rescission = whole; any qualifier = partial; a whole edge is downgraded to partial when other
evidence for the same acting order and target says partial (later-events' own rule; 165 edges). Peano lemmas and status-history events
are looked up per row as derived views (columns `peano_end_lemmas_*`, `status_history_end_events`); see section 4.

Agreement (6,158 orders):

| | both | Thrower only | project only | neither |
| --- | --- | --- | --- | --- |
| Thrower revoked vs project any revocation (whole or partial, or 1989 "revoked") | 1,578 | 2 | 174 | 4,404 |
| Thrower superseded vs project whole supersession | 469 | 2 | 85 | 5,602 |

Among the 1,578 orders both call revoked, Thrower's revoke_year equals some project revocation year in 1,568, is one year off in 3 and
two or more years off in 6 (a lone year is the usual case; she matches the latest year in 1,554 and the earliest in 1,481).
Of 60 orders with revoke_year equal to the issue year, the project has a revocation in that year for 57. EO 12553: of her 372
flagged orders the project has an EO 12553 revocation edge for 371 and the 1989 table names it for 370; the project has 12 more EO 12553 targets she did not flag.
The 140 `revokedbyotherthaneo` orders are overwhelmingly Public Land Order revocations in the project (122 PLO, 4 Proclamation, 2 Public Law, others mixed).

**`DISAGREEMENTS.csv`: 228 rows, 225 distinct orders**, columns as requested plus thrower_eonumber, thrower_year,
project_evidence, peano/status-history counts:

| kind | rows |
| --- | --- |
| project_revoked_thrower_silent | 126 |
| partial_vs_full | 24 |
| project_partial_revoked_thrower_silent | 23 |
| project_superseded_thrower_silent | 38 |
| year_differs (2+ years) | 6 |
| year_differs_by_one | 3 |
| supersede_year_differs | 2 |
| thrower_revoked_project_silent | 2 |
| thrower_revoked_project_status_in_effect | 2 |
| thrower_superseded_project_revoked | 1 |
| thrower_superseded_project_silent | 1 |

Basis of the 126 `project_revoked_thrower_silent`: 85 rest on the 1989 table alone, 37 on an OFR note (12 of those also on the
table), 4 on order text only. Of 24 `partial_vs_full` (Thrower says full, project says partial), 11 carry an "in part" qualifier,
7 a "with respect to ..." qualifier, 5 are whole in one source and partial in another, 1 names a section.
`thrower_revoked_project_status_in_effect` is only listed where Thrower's partrevoked=0; 11 more orders with partrevoked=1 have project status YES and are not disagreements.

### The 15-case hand check

Seeded draw (seed 20261106, stratified by kind; `SAMPLE15_draw.csv`), my reading of the project's evidence in
`SAMPLE15_hand_checked.csv`. Result: **Thrower is the likelier wrong side in 5 firm cases** (EO 8258 row slip to the neighbouring
order, EO 11654 inherited OFR typo "1972" for 1982, EO 8083 and EO 11603 year slips, EO 8065 partial flag) **and probably omits non-EO
instruments in 4 more** (EO 9709, 10633, 10126, 9267; the first three rest on one or two editorial records with Federal Register
citations I did not open). **The project is the wrong side in 3** (EO 12656, 12922, 12872: the text scan misread a qualifier, so the project's own "whole" or
"partial" edge is an artifact; Thrower is right). **3 are definitional or unresolved**: EO 12890 (an amending order that Thrower counts as revoked with its parent), EO 8597 (Thrower's 1946 is a
discontinuance, the project's 1992 is the formal revocation: both true), EO 8647 (needs the text of Public Law 100-696 sec. 507).
So both sides err, in different ways: Thrower in digit and row slips, in copying note typos, and in leaving out non-EO instruments; the
project in text-scan qualifier parsing. Outside the sample I noticed one more project-side gap: EO 7594's OFR note reads
"Public Land Order: 6489, October 27, 1983" (stray colon), so the project has no 1983 edge there and Thrower's 1983 is right.

## 4. Inherited errors

**Does the project derive from the same tables?** Yes, for the formal-revocation layer.
- Thrower's stated source is the National Archives disposition tables; later-events' notes are the Office of the Federal Register's
  `disposition_notes` field from the Federal Register API (the project's own README calls them OFR editorial notes). I could not
  confirm from held bytes that the archives.gov tables and the API field are generated from one database; that needs the 2014-2015 captures of the tables, not fetched here. The tests below show behaviour consistent with it.
- Lineage in the files: 23,821 of the 23,829 peano instance lemmas carry a later-events edge id (the other 8 are class lemmas from axiom files), and all 15,772 status-history events do. So peano and status-history add no independent
  revocation facts. Of 6,434 later-events revocation edges, 4,007 come from OFR notes and 2,427 from order texts; the order-text edges and the 1989 table are the only partly independent checks.
- **Fingerprint test** (3,712 Thrower orders with a 1989 table row): where OFR notes and the 1989 table both say revoked, Thrower is revoked in 1,147 of 1,163 (98.6%); where
  the notes are silent and the table says "Revoked", Thrower is revoked in **1 of 98**; where the notes say revoked and the table does not, Thrower is revoked in **172 of 192**; where neither says revoked, 0 of 2,259. She follows the notes, not the 1989 table. (The two OFR compilations themselves disagree: 174 of 1,541 "revoked" table rows have no OFR-note ending.)
- **Date test**: the one clean case is EO 11654 above; only 4 revocation edges have a note year that differs from the catalog year, so this test is thin (Thrower matches the note year in 2, the catalog year in 2).

**Flags** (`INHERITED_flags.csv`; Thrower and the OFR note agree, a held official text or the Codification differs). 46 rows; I read all of them. 
- 38 `ofr_whole_primary_text_partial`: the held official text revokes the order with a qualifier. By eye about 9 are "with respect to <country>" clauses that qualify a termination, not the revocation (parser artifacts, the whole reading is right); about 15 are savings clauses ("except that ...", "to the extent not heretofore made inapplicable") where the order is revoked whole but with saved effects (e.g. EO 11677, 11796, 11810, 11958); the rest are genuine or unclear section-level revocations (e.g. EO 10582 subsections 2(a), 2(c); EO 13585 section 1(n)). Not individually adjudicated. Thrower agrees with the OFR "whole" reading in 32 of the 38.
- 4 `ofr_partial_primary_text_whole` (EO 9330, 9366, 12088, 12258): the text edge's qualifier detection and the note disagree; unread beyond the quote.
- 4 `shared_omission_held_official_text_states_revocation`: EO 7732 and 12692 are really partial, EO 12656 is sections only; only **EO 13554** is a likely shared omission (EO 13626 sec. (d) revokes it; the OFR note is a "See" reference, Thrower has revoked=0).
- Thrower and OFR notes agree on a pre-1989 whole revocation that the 1989 table lists as codified: 0 orders (EO 12211 and EO 10000 first looked like cases but are partial revocations, consistent with "codified").

## 5. Strata: do Thrower's covariates predict hard or cheap?

Outcomes from the readiness tracker for all 6,158 orders: decided (has a provisional YES/NO) 2,499 (40.6%); ready for human review 784 (12.7%);
a claim present 1,108 (18.0%); text step done 5,908 (95.9%); first-end/current-basis unproved 1,568 (25.5%); contrary lead or quarantined conflict 149 (2.4%).
Tables: `STRATA_crosstabs.csv` (counts, rates, Wilson intervals), `STRATA_chi2.csv`, `STRATA_adjusted_logit.csv` (odds ratios holding the decade fixed; no multiplicity correction).

**What predicts:**
- **Decade** is the strongest stratifier: decided 22-58%, ready 1.6-20%; highest in the 1960s-70s (ready 18-20%), lowest from the 1990s on (ready 9.6% in the 1990s, 4.7% in the 2000s, 1.6% in the 2010s).
- **Civil-service flag** (733 orders): decided 67.8% vs 36.9%, ready 38.5% vs 9.3%; adjusted odds ratios 5.6 (decided) and 7.0 (ready). This is the project deciding whole classes (civil-service exemption orders), not intrinsic ease.
- **Revoked (Thrower)**: decided 52.4% vs 36.5%, ready 18.9% vs 10.6%; adjusted OR 1.7 and 2.4. Among decided orders the provisional status is YES (in effect) for only 1.6% of her revoked orders against 18.3% of the rest (13 of 828 vs 305 of 1,671), so her revoked flag and the project's statuses mostly agree.
- **Temporary-and-emergency-functions flag** (517 orders): decided 63% vs 38%; the end is unproved far more often (50.9% vs 22.6%; adjusted OR 3.8). Self-terminating orders are the hard ones for the first-end step.
- **Public land** (671 orders): decided 16%, ready 1.2% (adjusted OR for ready 0.13). **Foreign/defense/security (`fds`)**: ready 6.7% vs 14.7%, OR 0.58.

**What does not:** divided government, war, `nyt`, public mention, economy, committee, military operations, foreign service, procurement, civil rights, intelligence and national security show no or only marginal, unstable effects (several have fewer than 300 orders or zero ready orders; the logit marks separation). Ceremonial (100 orders) has a low ready rate (3%) but a wide interval (adjusted OR 0.29, CI 0.09-0.94). The text step is about 96% done in every stratum and does not discriminate; the contrary-lead rate is flat (2-6%) except that it rises over time (0.1% in the 1930s to 6% in the 1980s).

Caution: "decided" and "ready" reflect which orders previous waves chose to work (decision origin: legacy-inherited 1,646, Opus 807, other 46 of 2,499 decided; see `STRATA_decision_origin_by_revoked.csv`), so these are descriptions of the project's selection as much as of difficulty.

## Limits

- Project snapshot is 2026 and OFR notes contain events after Thrower's 2013 window; I excluded those, but note edits made after her 2014-15 download cannot be separated from her omissions (this may explain part of the 174 project-only revocations, though 85 rest on the 1989 table, which pre-dates her).
- My whole/partial classification uses later-events' qualifier text, which is itself imperfect (three of my 15 cases are parser artifacts). Treat partial_vs_full and year_differs rows accordingly.
- The 15 cases were read from the project's own records (OFR note text, quotes of held FR originals, the 1989 row), not from fresh page images; I opened no Federal Register page. Nothing here is a verified legal fact.
- Statistics are descriptive (Pearson chi-square, simple logit), no scipy available, own implementation with tests.
- Not done: archives.gov table capture; any check of 2014 data vintage; comparison of Thrower's topic flags with a project classification (the project has none to compare).

## Open questions for the owner

1. Treat Thrower as a same-lineage check only: her revoked flag adds almost nothing beyond the OFR notes. Her partrevoked, supersede and reject-of-authority flags are the only additional coding; worth using as a coder-disagreement signal?
2. Later-events parser: fix the qualifier detection for "section 401(3)-(4)" with an en dash, for "with respect to <country>" after a "terminate" clause, and for stray colons in notes ("Public Land Order: 6489").
3. Register: normalise `EO:7933a`, review `EO:7700A` (duplicate) and `EO:10369A` (phantom), and apply `CATALOG_DATE_CORRECTIONS.csv` to the register dates (EO 8969, 10276).
4. Should an order that only amends a later-revoked parent be recorded as ending with it (Thrower's EO 12890 reading)?
5. Check the Federal Register pages 13 FR 6080 (EO 9709), 26 FR 6233 (EO 10633), 31 FR 13422 (EO 10126).
