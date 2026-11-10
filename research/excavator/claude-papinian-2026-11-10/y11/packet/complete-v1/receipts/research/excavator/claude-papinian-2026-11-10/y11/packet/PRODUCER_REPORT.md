# Producer report, packet y11 (producer-y11, Papinian lane)

Start 2026-11-10T04:42:11Z. End 2026-11-10T05:23:20Z (after the final batch-check of applied-v9 finished).
Final applied directory: `research/excavator/claude-papinian-2026-11-10/y11/packet/applied-v9`.

## Outcomes (7 submitted, 18 blocked, 0 unresolved)

Submitted (all YES, all pass the actual claim checker):

- EO:10834 (flag): inventory corrected by overrides to 11 scopes (the dossier omitted section 1 and ran section 3 across front matter). Code prints the whole order under 4 U.S.C. 1 note, 4 U.S.C. 5 defines the flag by it. Sections 31 (changeover 1960-07-04) and 33 (revoked EO 10798, 1959-08-21) recorded terminated; others operative.
- EO:11129 (JFK Space Center): 51 U.S.C. 20306(a)(6)(B) (2025) refers to the center described in the order.
- EO:12081 (end of Vietnam naturalization period): 8 U.S.C. 1440(a) held and in force, keyed to the date designated by Executive order; Code prints the order.
- EO:12549 (debarment and suspension): inventory corrected to 11 scopes; Code note under 31 U.S.C. 6101, Pub. L. 110-417 section 873 (committee under sections 4 and 5 of the order), 2 CFR 180.110. The dossier conflict PARTIAL_END_CANDIDATE_ON_YES_ORDER (29 "suspension" candidates) was resolved: they are agency Federal Register notices citing the order, not presidential instruments; EO 12689 and EO 13904 only recite it.
- EO:12568 (military spouse hiring, NAF): Pub. L. 104-106 section 568(d) points the order at 10 U.S.C. 1784; 10 U.S.C. 1784(a)(2) held.
- EO:12626 (National Defense Stockpile Manager): 50 U.S.C. 98 notes print the order; Stock Piling Act and 3 U.S.C. 301 held; EO 14051 operates on the section 7 function the order excludes. Statute text of former 40 U.S.C. 485(f) (now 574(d)) is not held and is disclosed.
- EO:13709 (National Security Medal): inventory corrected to 7 scopes (dossier held one sentence); Code prints EO 10431 as amended by section 1 of EO 13709; section 2 (one-time supersession of the 1953 regulations) recorded terminated by performance 2015-10-02.

Blocked (exact missing source):

- EO:10199: page-check fragment (Montfaucon) registers the FR scan as `official_printing`, acceptable_as_original false, but the packet ORIGINAL source carries no grade, so apply and the working-text policy reject every source reference; inventory also needs override to chars 1617-2228 (dossier span is EO 10198 text). Legally looks operative.
- EO:10860: the held original's OCR front matter reads "EO 1086Q" (Codification Guide), which the checker's order_exists check fails on `original_representation.quote` (applied-v8). Needs an original without that front matter or a checker fix. Legally looks operative.
- EO:11139, EO:11446, EO:11231, EO:12985: the EO 13286 amendment can only be cited from an APP or clause-drafts mirror; an official FR copy of EO 13286 is held but not registered as an acting provision, so `working_text:official_copy_available_recheck_required`. 11231 also needs the 1973 DoD terminal-date memorandum (DoD Instruction 1348.15).
- EO:13915: Federal Vacancies Reform Act (5 U.S.C. 3345 et seq.) text not held; no U.S. Code, eCFR or disposition hit.
- EO:13224, 13722, 13851, 14039: emergency-dependent; the National Emergencies Act continuation notices are not census-registered (listed exactly in each blocker).
- EO:13309: held evidence indicates not operative (section 5 ended 2005-09-30; EO 13446 section 5 restated EO 12994 in 2007); continuation orders and a restatement ruling needed.
- EO:12185: section 1-111 lost its basis when 42 U.S.C. 8373(c) was struck by Pub. L. 102-486 (1992), but the only packet record carrying that note is typed `report_deadline`, which the assembler refuses as an ending source.
- EO:11988: EO 13807 section 6 (revoked EO 13690) and EO 14148 (revoked EO 14030) have no citable acting provision in the packet.
- EO:13257: official EO 13286 acting provision and 22 U.S.C. 7103 text needed; 29 clauses unreconciled.
- EO:10865, EO:13549, EO:11223: clause-level reconciliation against many later instruments (some mirror-only) not completed; blockers name the instruments. These three are capacity blocks, not source-absence blocks.

## What took the time (one line each)

10199: identity (EO 10198 text in the clause span), then the grade defect. 10834: rebuilding an 11-scope inventory from OCR with front matter in the middle. 10860: five-scope inventory, then the checker OCR failure. 10865/13549/11223: size of the later-event maps. 11129: quick. 11139/11446/11231/12985: working-text policy defect. 11988: tracing 13690/13807/14030/14148. 12081: 8 U.S.C. 1440 text. 12185: 42 U.S.C. 8373 and the report_deadline refusal. 12549: inventory and conflict resolution. 12568: Pub. L. 104-106 note. 12626: authority statutes. 13224/13722/13851/14039: NEA notice census gaps. 13257: 13286 mirror-only. 13309: 13446 restatement. 13709: seven-scope inventory. 13915: FVRA text not held.

## Batch-check counts (applied-v9)

Packet members 25; claims checked 7; strict pass 7, fail 0; actual claim checker: all checks passed 7, mechanical fail 0, unverified 0; outcomes: assembled 7, blocked 18. Earlier versions: v1 (11129 pass, 10199 rejected), v3 (11139/11446 rejected by working-text policy), v5 (12549 conflict), v8 (10860 checker failure).

## Geddes

Lint of applied-v9: 0 defect flags, 13 coverage gaps (advisory): `citing_corpus_incomplete` on all 7 claims (912 of 63,287 tracked held texts missing or changed in this worktree), and `own_order_body_unverified` / `citing_own_body_unverified` (order_heading_unresolved) on EO:12549, EO:11129 and EO:12626. No flags, so `GEDDES_RESOLUTIONS.json` holds an empty list.

## Full-packet files opened beyond the views

`LOOKUPS.md` (read in part, about 30 KB), `decisions.csv` and `clauses.csv`. `PACKET.json` was loaded once through `batch.load_packet(check_sources=False)` in a script to read dossier evidence records (ORIGINAL spans, ACT and TERM records, conflicts); `READ.md` and `LOOKUPS.details.json` were not opened. Repository sources read: held texts under `jobs/fr-originals`, `jobs/theophilus-sources/output/texts`, `jobs/later-events/output`, `jobs/current-law/output`, `jobs/app-executive-orders/output`, `jobs/montfaucon-page-check/output`, `jobs/selden-fr-citers/output/texts` (samples), `jobs/source-ladder/output/texts` (one 15 U.S.C. 714b file).

## Tool defects and notes

1. The packet ORIGINAL source for EO 10199 carries no grade although a page-check fragment registers the same scan as `official_printing` with acceptable_as_original false (assembler/working-text policy then rejects all references).
2. Working-text policy rejects an APP or clause-drafts mirror of a later order whenever any official copy of that order is held (`official_copy_available_recheck_required`), even when the packet itself registers only the mirror as the acting provision (EO 13286).
3. Evidence records typed `report_deadline` cannot serve as an end source even when the held text records a statutory repeal (EO 12185, 42 U.S.C. 8373(c)).
4. Derived inventory records (`OVERRIDE:...`) carry no `actor_id`, so a terminated clause cannot name them as its end source; ORIGINAL had to be used, and whole-original quotes carry OCR front matter into the checker (EO 10860).
5. Several dossier inventories mislabel sections (EO 12549 section 2(c) labelled section 5; EO 10860 sections 2 and 3 merged; EO 10834 section 3 spanning front matter; EO 13709 holding one sentence), so overrides were required.
6. The dossier conflict PARTIAL_END_CANDIDATE_ON_YES_ORDER for EO 12549 is a false positive from the word suspension in agency notices.
7. No git state was changed; nothing outside the packet and the scratch folder was written.
