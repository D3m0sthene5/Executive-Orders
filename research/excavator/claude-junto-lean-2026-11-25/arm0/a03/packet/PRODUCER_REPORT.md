# Producer report: junto-arm0 a03

Start 2026-11-25T08:55:13Z; end 2026-11-25T09:11:00Z. Final applied directory: applied-v1.

## Outcomes
- EO:13613 submit (YES). Sixteen-clause inventory checked against the held Federal Register text. Section 3 (revocation of EO 13242 and the 2002 memorandum) is terminated by performance on 2012-05-21 with the held original as source; the other fifteen clauses are operative on the original-plus-bounded-search basis (no own-terms end, empty later-event chain, three searches read). A bounded corpus search for amending or revoking language naming 13613 found none.
- EO:13660, 13661, 13849, 13851, 14038, 14078 blocked. Each is emergency-dependent. The continuation notices are registered in the dossiers only as ACTOR_TEXT:FRDOC records at jobs/selden-fr-citers/output/texts/fr-*.txt, which is tracked in git but not materialized in this working tree. A pilot assembly of a full EO 13660 claim failed every notice with text_unavailable_or_unsafe. The same bytes are held under jobs/theophilus-sources/output/texts/ (sha256 of fr-2026-03501.txt equal to the registered text_sha256), but that path is not registered. Extra gaps: 13849 inventory covers only the preamble (sections 1 to 11 missing) and no EO 13694 notice chain is held; 13851 needs EO 14088 amendments recorded clause by clause; 14038 lacks 2007 to 2021 notices; 14078 conflict (2023-05-30 "supersession") is an OFAC general-license rule, a false lead; 13661 has two duplicate-labelled clauses.
- EO:14306 blocked: dated directives inserted into EO 14144 have no held performance or present-force source; the 2026-03-24 "revocation" conflict is a continuation notice; the notice is at the unmaterialized path.
- EO:7680 blocked: Proclamation 2578 (1943) superseded it in part per the OFR catalog and is not held; EO 9021 modified it; no current land-status source is held.
- EO:9873 blocked: EO 12608 (52 FR 34617) amended paragraph 2 (Bureau of the Budget to Office of Management and Budget; 1989 codification note) but is not an evidence record in the dossier, so it cannot be listed as a later event; the 36 U.S.C. 2111 note reproduces the order without stating present force and the statute text is not held.
No order was found out of force on 2026-10-14, so no ledger-change report is needed.

## What took the time
13613 clause inventory and the sec. 3 end source (an end source needs an actor, so the clause record was unusable and the original record was used). 13660 pilot (full claim drafted, then discarded when the notice path failure appeared). 13849 inventory check. 7680 and 9873 later-event leads. 14078 and 14306 conflict leads. Other orders: blocks.

## Batch-check
1 claim checked; strict pass 1, fail 0; actual checker all checks passed 1; outcomes: 1 assembled, 9 blocked. Geddes: 0 flags, 1 coverage gap (citing corpus incomplete: 14,475 tracked files not materialized); resolutions file is empty.

## Files opened beyond views
Views plus: PACKET.json (loaded once by script, no check_sources), LOOKUPS.md, jobs/current-law notes and the 22 U.S.C. 9522 extract, jobs/fr-originals EO_12608 and EO_9021 texts, jobs/ofr-codification-1989 EO_9873, jobs/status-history observations for 14078 and 14306, jobs/later-events CATALOG_INDEX and EDGES.

## Tool defects
- jobs/selden-fr-citers is not materialized, making registered FRDOC notice sources uncitable while dispatch-check and source verification report no unavailable sources.
- Outcome field first_cause has no value for orders still operative; "unresolved" was used.

## Second pass (after checkout fix): start 2026-11-25T09:15:12Z, end 2026-11-25T09:19:31Z; final applied directory applied-v2
jobs/selden-fr-citers is now on disk. I rebuilt the full EO 13660 claim (23 clauses, 12 notices plus 5 reciting orders) and assembled it. Every notice citation failed the checker (276 errors: working_text_exact_grade_and_false_flag_required and working_text_fragment_identity_or_grade_mismatch). The notices are registered as fr_document_full_text captures with acceptable_as_original false, a grade the working-text policy does not accept, and they are not exact official printings. So EO 13660, 13661, 13849, 13851, 14038, 14078 and 14306 stay blocked, with the gap text and ASSESSMENT blockers changed from "path missing" to "grade not citable; needed: official printing of each notice or an accepted grade". EO 7680 and 9873 blocks did not rest on missing files and are unchanged; EO 13613 is unchanged (same claim). Batch-check on applied-v2: 1 claim, pass 1, fail 0, actual checker all passed 1, Geddes 0 flags, resolutions empty. The "path not materialized" defect in the first-pass report is superseded by this finding.
