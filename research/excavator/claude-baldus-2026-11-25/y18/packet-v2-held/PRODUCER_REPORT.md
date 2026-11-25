# Producer report: y18 (packet-v2-held), agent baldus

Start UTC: 2026-11-25T17:11:15Z
End UTC: 2026-11-25T17:38:00Z (applied-v1, batch-check, Geddes lint and gate done)

The work was first done against y18/packet; on the coordinator's message the sheets were carried to packet-v2-held (columns and row keys checked equal; only dossier_sha256 differed and was rebased from the new blank rows). Final applied directory: research/excavator/claude-baldus-2026-11-25/y18/packet-v2-held/applied-v1.

## Outcome per order
- EO:13949 submit. Operative; no end of its own and no revoking instrument held; emergency continuation notices held (last: March 2, 2026, 91 FR 10937); eCFR checked through 2026-10-14. PARTIAL_END_CANDIDATE_ON_YES_ORDER conflict resolved in text (the flagged events are continuation notices).
- EO:13959 submit. Operative as restated by EO 14032; clause sec1-b recorded terminated 2022-06-03 (expiration of the clause as restated by EO 14032, end source ACTOR_TEXT:EO:14032); rest operative; emergency notices held through 2025-11-05.
- EO:13984 submit. 52 clauses operative. Time-limited Commerce, DOJ and DHS directives are not recorded as ended (a deadline is not an end; only the proposal step, 89 FR 5698, is held). EO 14144 sec 9 and EO 14306 sec 3 amend EO 13694, not this order. Emergency under EO 13694 continued by Notices of 2025-03-27 and 2026-03-24. Conflict resolved in text.
- EO:14014 submit. Operative; Burma emergency continued (Notice of Feb 3, 2026, 91 FR 5663); CFR 525 basis.
- EO:14024 submit. Operative; later-event source set to ACTOR_TEXT:EO:14114 (official text) instead of APP-mirror ACT records, which the checker rejected; Notice of March 24, 2026 (91 FR 15515).
- EO:14032 submit. Operative; the restated section 1(c)(i) divestment permission recorded terminated 2022-06-03 by its own terms (end source ORIGINAL:EO:14032, which carries the actor; the CLAUSES record has none).
- EO:14033 submit. Operative; Notice of June 22, 2026 (91 FR 38233); conflict resolved in text.
- EO:14039 blocked. Held evidence indicates the statutory regime the order implements (PEESA sec 7503, text of 22 U.S.C. 9526, SUPPLEMENT:HELD14039_11_9fc160f5e30e, unreviewed) terminates no later than 2024-12-20, before the cutoff. Missing source: a reviewed source that settles whether the section 7503(h) termination reaches the persons identified under section 7503(a)(1)(B) that section 1(a) blocks (with any Presidential certification under 7503(h)(1)), and a source showing whether, how and when the blocking under section 1 ended or continued. The continuation notice 91 FR 15515 (SUPPLEMENT:HELD14039_10_3465cac4124a) is now citable but continues only the IEEPA emergency. Re-checked against the supplement; the block stands. The ledger YES is not supported by held evidence; any ledger change belongs to an owner route.
- EO:14059 submit. Operative; Notice of December 10, 2025 (90 FR 57865); clause sec1-c rests on the Fentanyl Sanctions Act, whose text is not held (stated in the claim).

Totals: 8 submitted, 1 blocked.

## What took the time
- 13949: first order; building the spec/quote-check/trial tooling and the conflict-resolution wording.
- 13959: superseded-by-restatement analysis and the sec1-b end/conflict wording.
- 13984: reading the amending texts (14110, 14144, 14306) to confirm they amend 13694, not this order; 52 clause descriptions.
- 14014, 14033, 14059: clause descriptions and continuation-notice verification.
- 14024: APP-mirror ACT records rejected by the working_text check; moved to ACTOR_TEXT source; clause description rewrites.
- 14032: 30 clause descriptions; end-source actor fix for the terminated clause.
- 14039: reading PEESA text, assembling the precise blocker; re-check against the supplement.

## Batch-check (applied-v1)
Apply: 8 assembled_proposal, 1 blocked, 190 source files hash-checked. Batch-check actual checker: 8 claims checked, 5 all checks passed, 3 mechanical-unverified (EO:13949, EO:13984, EO:14033: `quote_verbatim:too_short_to_verify` on a short first clause, no failure), 0 mechanical failures, 8 gate passed. No actionable failure; no applied-v2 needed.

## Geddes
Lint: 8 claims, 147 flags (5 orders with flags), 11 coverage gaps (reported, not gated). Flags: 53 (14059), 42 (14024), 35 (14014), 1 (14032) fr_citation_mismatch, and 16 later_instrument_named_without_event_source (13959). All 147 answered `disputed` in applied-v1/GEDDES_RESOLUTIONS.json: the citation flags compare a later continuation notice's Federal Register page against the single pinned original; the 13959 flags concern EO 13974, which is an earlier amender replaced by EO 14032, not a later ending actor. `geddes.py gate` passes (147 resolved, 0 stale or invalid).

## Full-packet files opened beyond the views
LOOKUPS.md (partly), HELD_SUPPLEMENT.json and SOURCE_SUPPLEMENT.json (packet-v2 and packet-v2-held), HELD_SOURCES.json (existence check), PACKET.json (through batch.load_packet), decisions.csv, clauses.csv, RATIONALES.json (head), LOOKUPS.details.json (count query). Also read held repo texts (jobs/fr-originals, selden-fr-citers, later-events EDGES.csv, theophilus-sources usc texts, current-law output) via local scripts.

## Tool defects
- The checker error clause_N_first_end carries no explanation; it meant the end source record had no actor (CLAUSES: records lack actor_id, ORIGINAL: has it).
- ACT records sourced from APP mirrors trigger working_text recheck errors; ACTOR_TEXT ids avoid it.
- Geddes fr_citation_mismatch flags every Federal Register citation of a later notice against the pinned original.
- Old packet y18/packet fails apply after the Valla context change (as the coordinator said); not tried.
