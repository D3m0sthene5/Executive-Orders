# Producer report, batch g01 (agent claude)

Start UTC: 2026-10-31T22:12:31Z. End UTC: 2026-11-01T03:39:24Z (wall time includes a pause while the usage limit was reset; active work is much shorter).

Final applied directory: research/excavator/claude-apollo-2026-10-31/g01/packet/supp/applied-v3 (the working packet is packet/supp, built by the source-supplement route from SOURCE_DECLARATIONS.json in this folder; applied-v1 and applied-v2 are earlier attempts, v2 tried the transcription route for EO 8168 and was rejected).

Outcome: 4 submitted (EO 7577, 8129, 8163, 8168), 20 blocked. No order was changed from its provisional status of no.

## Outcome per order and why

Submitted:
- EO 7577: terminated 1940-04-18 by express revocation in Executive Order 8396 (held FR text; amending order, command performed on issue; savings none after bounded search).
- EO 8168: terminated 1941-08-16 by paragraph 1 of Executive Order 8854 (held FR text). Savings continuing_independent, because paragraph 2 re-reserves the lands and an adjoining tract as a new command. Open mechanical item: see the checker defect below.
- EO 8129 and EO 8163: terminated 1958-08-05 (signature date) by Public Land Order 1704 (23 FR 6110, held issue text added as a bounded supplement with its PDF). Reorganization Plan II of 1939 (effective July 1, 1939 by Public Resolution 20) is recorded as a later event and a disclosed unnamed earlier candidate, not an end. The catalog date of August 4 is contradicted by the signature line.

Blocked (the ending instrument the disposition note names is not held as text, so no date, actor, mechanism or quote can be supported):
- EO 7532 (PLO 801), 7555 (PLO 6144), 7601 (PLO 5887), 7678 (PLO 343), 7705 (PLO 6316), 7951 (PLO 3277), 8004 (PLO 1149), 8085 (PLO 5690), 8116 (PLO 2292), 8124 (PLO 6117), 8160 (PLO 1211), 8325 (PLO 690), 8468 (PLO 157), 8508 (PLO 1603), 8575 (PLO 907), 8577 (PLO 5461): public land order text not held anywhere in the repository. EO 8184 (for 7532) and EO 9526 (for 8325, 8508, 8577) are held amendments and are later events, not ends.
- EO 7941: PLO 1152 (signed May 23, 1955) is recited in the held text of EO 10614 and expressly revokes the order, but the only citable record would carry EO 10614 as actor, and the issue PDF is not held, so a supplement is impossible.
- EO 8518: PLO 1068 (signed Feb 9, 1955; 20 FR 972) is held as extracted text but has no packet evidence record and no local PDF (sha 470c4ff2...), so a supplement is impossible.
- EO 8173: PLO 1660 (23 FR 4621) text is not held, only a codification-guide line; Proclamation 2416 is not held.
- EO 8331: the held PLO 936 text is truncated (no date or signature); the partial revocation by PLO 584 is not held.

## What took the time (one line per order)

- 7577: reading EO 7577 and EO 8396, confirming the span and the OCR-tolerant number search.
- 8168: choosing among the FR text, the transcription and the clause-draft copy; the checker rejects the transcription route because an official copy is held, and rejects the FR quote because of an OCR artifact.
- 8129, 8163: building the supplement (PDF sha match through the GPO list, character spans), the date question (Aug 4 versus Aug 5) and Reorganization Plan II.
- 7941, 8518: finding that the ending PLO is held only as recital or extracted text without a usable packet route.
- 7532, 7555, 7601, 7678, 7705, 7951, 8004, 8085, 8116, 8124, 8160, 8468, 8575: repo-wide search by order and PLO number to confirm the PLO text is not held.
- 8173, 8331, 8325, 8508, 8577: reading partial or amending sources (EO 9526, PLO 936 fragment, PLO 1660 guide line) to confirm they do not end the order.

## Batch-check counts (applied-v3)

24 members; 20 blocked, 4 assembled; strict claim pass 4 of 4; actual claim checker: gate passed 4 of 4, all checks passed 3 of 4, mechanical failures 1 (EO 8168), unverified 0; independent human certifications 0.

The one mechanical failure is order_exists:not_in_universe on the end-source quote of EO 8168. The quote is the whole machine-extracted FR page for EO 8854, which carries a footnote mark run into the number (Executive Order No. 81681). The held bytes are quoted exactly; the checker reads 81681 as another order. The transcription alternative is refused by the assembler (working_text:official_copy_available_recheck_required, applied-v2). I left the claim submitted with the true source rather than block a sound legal reading; a reviewer should treat the finding as an extraction artifact, or a narrower held span of the FR text should replace the whole-page record.

## Tool defects

- The ACTOR_TEXT record for an FR original can only be the whole page, so neighbouring orders and OCR noise enter the quote and trip the order-exists check (EO 8854).
- The source-supplement route needs a locally held PDF with a matching sha; extracted text held without the PDF (PLO 1068, EO 10614 page) cannot be used, although the GPO-matched sha list shows custody is established.
- kit.py scripts fail under python3 -I (assemble module not found).
- The ACT record for EO 7577 spans page furniture and has no signature line; the EO 8129 supplement span contains a page-break line.
- Several PLO excerpts have OCR-split words.
