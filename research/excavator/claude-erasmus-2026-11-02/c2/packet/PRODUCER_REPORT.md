# Producer report, batch c2 (Erasmus resubmission)

Start 2026-11-02T03:51:28Z. End 2026-11-02T03:58:00Z (approximate; last command ran at 03:57:42Z).

## Outcome

EO:10010 (filed_claim_correction): submitted, proposal in `applied-v1` (status no, one clause `EO:10010#whole`, first end 1986-02-25 by Executive Order 12553, unchanged from the filed claim). Submitted 1, blocked 0.

What took the time: reading the rules and rulings, then verifying the held texts of EO 10010, EO 10015 and EO 12553 and choosing a later-event source for EO 10015; the pipeline itself ran in about 6 seconds (apply) plus the checker run.

## Brief defect (one)

`later_instrument_named_without_event_source` (EO:10015 named in the reasoning, no later_events entry): confirmed and fixed. Checked against the held Federal Register text of EO 10015 (13 FR 6601, issue of 1948-11-09, signed 1948-11-05, "effective as of October 18, 1948"): it adds six carriers to List A and renames two List B organizations; it neither revokes nor supersedes EO 10010. It is now a later event with the id of the registered EO 10015 actor text (`jobs/fr-originals/data/full_run/texts/EO_10015.txt`), effective date 1948-10-18 (the date the order itself states; the signing date 1948-11-05 is in the clause reason). The prior text's reason for omitting it (only a transcription held) was wrong: the official FR copy is registered as `ACTOR_TEXT`.

## Other changes found on recheck

- Removed the filed claim's statement that EO 10015 "has its own claim in this packet" (false for this packet) and the research-rationale line "the packet reports no prior claim or review" (a prior claim and review exist; now stated).
- Report date and standstill: the filed claim said "functionally spent after the board reported" with no dates. The held NMB report text (source-ladder queue file, grade `held_text_lead`) shows the report is dated December 17, 1948, after a stipulation to extend the time to that date; thirty days later is January 16, 1949. `held_text_lead` is not in `working_text.GRADES`, so it cannot be a cited claim source; the dates are disclosed in the clause reason and the earlier-end check as leads, not recorded as events and not claimed as an end. The report-deadline ruling (2026-10-21, option C) asks for these as later events; that is not possible without a claim-grade source or a reviewed NORTON factual event (none exists for EO 10010). Not counted as a material gap, since it does not affect the end.
- Added the fact that EO 12553's table also lists number 10015 (quoted subject matches held bytes).
- Quotations checked against held bytes: the 12553 words "any amendments thereto" and both table subjects. No quotation of EO 10010 or EO 10015 text (hyphenated OCR) is used; those are paraphrases.
- Inventory unchanged (one whole clause, chars 4933-6626; signature and Lists A and B follow and contain no command).
- `original_confirmed` true, `original_pages_confirmed` false (the FR record does not require a page check; I read only the text layer).

## Batch-check

apply: 1 assembled_proposal. batch-check: packet_members 1, claims_checked 1, strict pass 1, fail 0, actual claim-checker all checks passed 1, mechanical fail 0, unverified 0, actionable failures none.

## Geddes

Lint on `applied-v1`: 0 defect flags, 0 coverage gaps; `GEDDES_LINT.json` and an empty `GEDDES_RESOLUTIONS.json` written in `applied-v1`. No crash.

## Full-packet files opened beyond the view

I opened `PACKET.json` by script and ran one `grep -n clause` on `READ.md` (it printed a very large prior-research line); LOOKUPS.details.json was not opened. The slim view lacks: the dossier later-events chain, the `machine_searches` list with coverage notes, the `evidence` records for ACTOR_TEXT and TERM ids (needed to choose a later-event source id and the allowed held-text spans), `draft_gate_errors` and the dossier's `conflicts`/`missing`.

## Tool defects and notes

- The later-event quote for EO 10015 is the whole 5,588-character registered actor text (it includes neighbouring FR material); no bounded span id exists for the FR copy of EO 10015, only for the APP transcription. A source supplement could add the 2032-3574 span.
- The packet's `draft_gate_errors` lists `clause_0_state` and `clause_1_state` ("2 clause(s)") although the inventory has one clause.
- decisions.csv/clauses.csv were rewritten in place (originals kept in the session scratchpad only).
