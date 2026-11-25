# Producer report: u04 (undecided route), agent baldus

Start 2026-11-25T15:51:07Z. End 2026-11-25T16:13:14Z. Final applied directory: `applied-v1` (no later version needed).

## Outcomes (10 assigned members)

Submitted (2, both `awaiting_status_review`, status decision filled):
- EO:9941: status no. Express supersession by Executive Order 10897 section 2 (signed 1960-12-02), whose section 3 makes the order effective as of 1960-10-16; first end recorded as 1960-10-16 with the signing date disclosed.
- EO:8187: status no. One self-executing amendment (paragraph 6 added to Subdivision VI of Schedule A, FBI positions for 1939-07-01 to 1940-06-30), spent on issue 1939-06-29; the explicit empty-note flag is resolved in the decision.

Blocked (8):
- EO:11563: status no is filed (Executive Order 12553 revokes it by number, signed 1986-02-25), lifecycle blocked: 12553 is a cleanup order, so it is the formal disposition and not by default the first end; no held source shows an earlier end. Needed: statute text on expiry of induction authority or a later regulation removing section 1631.7. The dossier's amendment leads (Executive Orders 11586, 11606) amend other sections and do not name Executive Order 11563.
- EO:8305: status no is filed (Public Land Order 1491, signed 1957-09-09, express revocation), lifecycle blocked: Public Land Orders 1491, 679 and 743 are held only as govinfo page extracts with grade `government_printed_federal_register_issue`, rejected by the assembler (`working_text_exact_grade_and_false_flag_required`). Needed: an accepted-grade copy or a federalregister.gov capture.
- EO:13170: no status filed. A full 30-clause yes claim assembled and passed the kit gate, but the actual checker reported `source_held:custody_record_only` and `quote_verbatim:not_found` for the current-law source (U.S. Code note to 15 U.S.C. 644). Needed: held bytes of that current-law text through 2026-10-14. Nothing held ends the order.
- EO:13563: no status filed. All nine CURRENT records are U.S. Code extracts recorded by hash only; texts of MEMORANDUM:2013-05-17 and MEMORANDUM:2021-01-20 are not held. The dossier's chain lead that Executive Order 13777 "revokes section 6" is a mislabel (13777 section 2 only lists it for Regulatory Reform Officers to oversee); Executive Order 14094 reaffirms the order.
- EO:12241: no status filed. Original needs a page-image check (OCR only held); the 193-clause inventory is cut from neighbouring pages (the order is two sections); no CURRENT record; Executive Order 12657 supersedes it only to the extent inconsistent.
- EO:12993: no status filed. The OFR note "Superseded by: EO 13811" is not supported by the held text of Executive Order 13811, which never names it; no ending record and no CURRENT record.
- EO:9617: no status filed. No whole-order ending record or OWN_TEXT lead; the two CURRENT records are U.S. Code source credits; sections 1(d), 4(b), 6 not shown ended; inventory mislabelled (1(a) missing).
- EO:5685: no status filed. Whether and when the plat of resurvey was officially filed (trigger of the 91-day opening) is not shown by any held source; the revocation of Executive Order 5234 was performed on issue 1931-08-12.

Dispatch-blocked (10, rows left as prepared, assessment rows from views only): EO:10495, 13370, 1367, 2421, 2530, 3437, 4181, 4427, 4503, 4864.

## Time

- 9941: reading the superseding order, the effective-date question (1960-10-16 vs signing), the later revocation of 10897 by 12292.
- 8187: own-text route (spent on issue); found later re-amending orders 8441 and 8534 by wording search.
- 8305: tracing Executive Order 9526's sunset paragraph, Public Land Orders 679, 743, 1491; then the source-grade block.
- 11563: finding the 12553 table line; checking 11586 and 11606 (neither names 11563).
- 13170, 13563: building and test-assembling a 30-clause yes claim, then the custody block; reading 13777 and 14094.
- 12241, 12993, 9617: reading, then inventory/page-check/ending-record blocks.

## Checks

- `kit.py apply`: 20 members; outcomes unresolved 10, blocked 8, awaiting_status_review 2; wall 6.5 s.
- `kit.py batch-check`: claims_checked 0 (undecided members are never assembled by apply), strict pass 0, fail 0, actionable failures none; actual claim checker had no claims to run.
- Because apply does not assemble undecided members, I validated the two submitted sheets and all status decisions myself in scratch (`/home/claude/baldus-scr/work/u04/validate.py`): `status_overlay._decision_errors` returned [] for 9941, 8187, 11563 and 8305; `assemble.assemble` and `check_claim` returned no errors for 9941 and 8187 with an experimental status dossier; `batch.actual_check_offline` (actual claim checker, no downloads) passed both claims (all checks passed 2 of 2).
- Geddes lint on applied-v1: 0 defect flags, 0 coverage gaps (0 claims, since no claim is assembled at apply for undecided members); no GEDDES_RESOLUTIONS needed.
- Assessment rows: `ASSESSMENT.jsonl`, 20 rows (10 assigned, 10 dispatch-blocked).

## Files opened beyond the views

LOOKUPS.md (head only); DOSSIER.json and EVIDENCE.json of my own undecided folders (history observations, evidence records); the blank STATUS_DECISION.json files; decisions.csv, clauses.csv, RATIONALES.json. Repository sources read: jobs/fr-originals texts for Executive Orders 8441, 9526, 9672, 10897, 11586, 11606, 12292, 12553, 12657, 13777, 13811, 14094; jobs/selden-fr-acting texts FR_15_7366, FR_16_8366, FR_22_7311, FR_25_8146, FR_46_28416; jobs/selden-fr-citers fr-E9-6920; jobs/current-law usc-notes extract for 13170; cruden `literal` and `number` runs written under the scratch folder. No other packet folder was opened.

## Tool defects and observations

- `kit.py apply` does not assemble undecided members, so `batch-check` cannot exercise their claims; assembly errors (for example a rejected source grade, which I found for 8305) appear only when a sheet is assembled with a status.
- The dossier's `later_events_chain` mislabels some mentions as changes: Executive Order 13777 "revoke section 6" (13563) and Executive Orders 11586 and 11606 "parent_as_amended" (11563) do not change those orders.
- The OFR note on Executive Order 12993 ("Superseded by: EO 13811") is contradicted by the held text of 13811.
- A `CLAUSES:` evidence id cannot serve as `end_id` for a self-executing clause (assembly error `clause_0_first_end`); an OWN_TEXT lead is needed.
- The dossier for 12241 treats about 104,000 characters of neighbouring Federal Register pages as the order text.
