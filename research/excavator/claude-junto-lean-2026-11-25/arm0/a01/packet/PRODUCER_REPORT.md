# Producer report: junto-arm0 a01

Start 2026-11-25T08:55Z (scratch folder creation), end 2026-11-25T09:21Z.

## Outcomes (final applied dir: applied-v5)
- Submitted (4): EO:10717, EO:11139, EO:11965, EO:12432.
- Blocked (3):
  - EO:11155: 29 FR 6909 is held only as a mirror transcription; the working-text gate rejects every clause. Missing: an exact official text or page-image record of 29 FR 6909.
  - EO:12170: claim assembled but its current predicate (eCFR node), savings source and 1981 later events came out custody_record_only/unverified. The 2025-11-05 continuation notice (90 FR 50735, jobs/selden-fr-citers/output/texts/fr-2025-19829.txt) is a federalregister.gov full text and fails the working-text check. Missing: an official page text of 90 FR 50735.
  - EO:12185: authority statute text (42 U.S.C. 8373, 8302(a)(25)), repeal history (for example Pub. L. 100-42) and performance evidence for sections 1-103 and 1-105 not held; operative force unknown.
- Unresolved, not submitted (3): EO:11858, EO:11990, EO:12146. These were not blocked by missing evidence: clause-by-clause predicates were not completed in this run (11858: EO 13456 restatement; 11990: 18 clauses; 12146: 41 clauses). All three appear in force and amended only.

## What took the time
- 10717: terminated-clause end sources (EO 12014; sec 9 own terms).
- 11139: single later event, quick.
- 11155: 12 clauses; rejected by working-text gate, unfixed.
- 11858: restatement by EO 13456 and amendment chain.
- 11965: CURRENT record was custody-only; switched to clause ids.
- 11990: 18 clauses, unfinished.
- 12146: 41 clauses, unfinished.
- 12170: later-event and NEA source grades.
- 12185: statute not held.
- 12432: inventory overrides and two added clauses.

## Batch-check (applied-v5)
4 claims checked, 4 gate passed, 4 mechanical pass, 0 fail, 0 unverified. Counts: 4 assembled, 3 blocked, 3 unresolved.

## Geddes
0 defect flags; 8 coverage gaps (citing_corpus_incomplete, advisory). Recorded in applied-v5/GEDDES_RESOLUTIONS.json.

## Coordinator note
After the missing jobs were restored, fr-2026-13939 and fr-2025-19829 were read; neither changed an outcome (the NEA notice is FRDOC grade; the HUD proposed rule is context only).

## Full-packet files opened beyond views
jobs/fr-originals texts (EO_N.txt), jobs/later-events/output/CATALOG_INDEX.csv, jobs/theophilus-sources/output/texts, jobs/selden-fr-citers/output/texts/fr-2026-13939.txt and fr-2025-19829.txt.

## Tool defects
Apply refuses writes outside the packet; FR originals of 11155 flagged as derivative hash; later-event 12278/12279 ACTOR_TEXT grade mismatch.

## Second pass, 2026-11-25 (final applied dir: applied-v8; applied-v5 is unchanged)
Pass ended 2026-11-25T09:37Z.

Outcomes: EO:11858, EO:11990 and EO:12146 are now submitted, so 7 are submitted (10717, 11139, 11858, 11965, 11990, 12146, 12432) and 3 remain blocked (11155, 12170, 12185) for the reasons above. The four earlier claims were not changed.
- EO:11858: 23 clauses. EO 13456 restated the whole order, so clauses with a counterpart in the restated text continue (sec 1 establishment, 1(a)(5), 1(a)(6), sec 2 and 2(a),(b),(d),(e), sec 4, sec 6); clauses without one ended 2008-01-23 (1(a)(1)-(4), 1(b)(1)-(4), 1(c), 2(c), 2(f), 5); sec 3 ended by its one-year term on 1976-05-07 and was formally removed in 2008. The dossier conflict PARTIAL_END_CANDIDATE_ON_YES_ORDER (Treasury guidance notice, 73 FR 74567) was resolved as not an ending event. The dossier chain lists EO 12977 for this order and EO 12146, but its held text does not mention either; the quoted provisions are EO 13286 text, so 12977 was not treated as an amendment (chain defect).
- EO:11990: 18 clauses all operative; EO 12608 sec 28 changed sec 6 only; sec 8's October 1, 1977 date is a deadline and cut-off, not an end. The 2026 HUD proposed rule (fr-2026-13939) is cited as context for current force.
- EO:12146: 39 clauses; the 15 initial-roster clauses (1-102 and its items) are treated as ended by the two-year initial term on 1981-07-18, the other 24 are operative. This is a judgment: EO 13286 sec 53 edited the roster in 2003. If a reviewer reads the roster as a continuing list, those 15 clauses become operative and the order status is unchanged.
What took the time: 11858 clause-by-clause comparison with the 13456 restatement and the conflict; 11990 18 short clauses; 12146 the roster judgment and the 12608 and 13286 amendment locations.
Batch-check (applied-v8): 7 claims checked, 7 gate passed, 5 mechanical pass, 2 pass with unverified (EO:11858 and EO:12146: quote_verbatim too_short_to_verify on short clause quotes such as one-line member items), 0 fail.
Geddes: 0 defect flags; coverage gaps are advisory (GEDDES_RESOLUTIONS.json in applied-v8).
Extra files opened: jobs/fr-originals EO_13456, 12188, 12608, 13286, 13603, 12977; jobs/status-history/output/histories/EO_11858.json; jobs/selden-fr-citers fr-E8-28791 and fr-2026-13939; PACKET.json for the conflict code.
Tool defects: views omit dossier conflicts (found only in PACKET.json); the dossier chain misattributes the EO 13286 provisions to EO 12977.
