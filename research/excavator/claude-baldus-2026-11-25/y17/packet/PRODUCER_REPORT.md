# Producer report, packet y17 (baldus)

Start 2026-11-25T17:05:20Z. End 2026-11-25T17:18:30Z. Stopped early under the brief's stop rule.

## Stop reason
`kit.py apply` fails at once with `claim-kit: changed Valla review context; prepare a new version` (raised at jobs/claim-kit/batch.py line 323: the Valla context recomputed from the review folders differs from the frozen `valla_context` in PACKET.json). The same error occurs with the original, unedited decisions.csv and clauses.csv, so my edits did not cause it. I did not work around it. No applied-vN, batch-check or Geddes lint was run. Counts: submitted 0, blocked 1, undecided 8.

## State of the sheets
- EO:13915: sheet filled for submit (YES). All lead, section 1 to 3 clauses operative on the order's own text plus the three bounded searches; section 4 (revocation of EO 13244) terminated by performance on 2020-04-14. Not assembled, so not checked by the claim checker. The Vacancies Reform Act text (5 U.S.C. 3345) is not held; disclosed in the legal basis.
- EO:13883: set to blocked. Missing: National Emergencies Act continuation notices for the EO 12938 emergency (none after 2012-era texts held) on which sections 2 and 5 depend; dossier inventory is only the heading line.
- The other seven rows are unchanged (`unresolved`).

## Findings for the owner of the re-prepared packet (not yet in any sheet)
- All other orders look in force on 2026-10-14 with held evidence: EO 13857 (notice 2026-02-18, FR Doc. 2026-03502; OFAC action 2026-08-07, FR Doc. 2026-17263), EO 13863 (notice 2026-07-13, FR Doc. 2026-14454), EO 13876 and EO 13902 (EO 12957 notice 2026-03-02, FR Doc. 2026-04450; EO 13902 OFAC determination 2026-10-01, FR Doc. 2026-20839), EO 13882 (notice 2026-07-21, FR Doc. 2026-15024), EO 13886 (OFAC action 2026-10-02, FR Doc. 2026-20525), EO 13894 (notice 2026-09-30, FR Doc. 2026-20322). None needs a ledger change.
- Inventory defects: EO 13857's only clause is a truncated preamble slice (inventory override needed: Section 1(a) amendment and Section 2 are missing); EO 13894's inventory omits the preamble sentence declaring the national emergency (override needed, 50+ clauses); EO 13902's own-text boundary is flagged unverified.
- EO 13894 is amended by EO 14142 (2025-01-15: strikes a preamble phrase, replaces section 1(a)(i)(B)-(F), strikes section 8(f), which ends that clause) and EO 14312 (2025-06-30: restates sections 1(a) and 2(a)). These need later events with before/after text under the strike-and-insert ruling.
- EO 13886: no catalogue record exists for the 2021-2026 EO 13224 continuation notices (held bytes exist in jobs/selden-fr-citers), and the September 2019 notice is not held; EO 13902 likewise lacks catalogue records for the 2021-2026 EO 12957 notices.
- The PARTIAL_END_CANDIDATE conflict lines on EO 13876, 13882, 13894 and 13902 are false positives (continuation notices mentioning an unrelated revocation, a regulations rule whose title contains "Suspending", State Department designation notices, and EO 14142's amendments).
- EO 14382 (2026-02-06) recites EO 13902 but does not revoke or amend EO 13876 or EO 13902.

## What took the time
All nine orders: reading texts and continuation notices (about 12 minutes); sheet writing for EO 13915 and EO 13883; the stop came at the first apply.

## Full-packet files opened beyond the views
LOOKUPS.md (whole), PACKET.json and LOOKUPS.details.json (loaded in scripts for machine searches, conflicts and citation lists), HELD_SOURCES.json, HELD_SUPPLEMENT.json (keys only).

## Tool defects
- apply fails with the Valla message above before reading any decision row.
- LOOKUPS number-citation lists are truncated at 40 for EO 13857 (42 matching files); I checked the remainder by direct search.

## ASSESSMENT.jsonl
Nine rows written (best readings; `claimed_status` blank, outcome `unresolved` except EO 13883 `blocked`). `first_cause` is `unresolved` for orders still in force because no cessation cause applies.
