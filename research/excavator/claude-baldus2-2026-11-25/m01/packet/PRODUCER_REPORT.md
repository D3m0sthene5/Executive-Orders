# Producer report, baldus2 m01

Start UTC: 2026-11-25T19:12:14Z
End UTC: 2026-11-25T19:20:31Z

## Status
APPLY DID NOT RUN. `kit.py apply` stopped with "claim-kit: changed prior research; prepare a new version". Per the brief I stopped rather than work around it. No applied-v1, no batch-check, no Geddes lint. The packet's prior-research fingerprint no longer matches because research about these orders was added outside the packet after preparation (files newer than PREPARE.json that name the assigned orders: research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv and the complete-v1 tracker outputs under research/excavator/claude-baldus-2026-11-25/y14, y15, y16). The sheets (decisions.csv, clauses.csv) and ASSESSMENT.jsonl are filled and ready to apply to a fresh packet with the same dossier fingerprints.

## Intended outcomes (2 submit, 6 blocked)
- EO:10029 submit. One clause, ended by own no-change term 1949-04-09 (inclusive); report letter 1949-03-10 (reviewed factual event FACT:...10029, bytes read, page image checked); EO 12553 (1986-02-25) as later formal disposition.
- EO:10130 submit. One clause, ended 1950-08-05 (inclusive); report letter 1950-07-06 (reviewed factual event; letter misprints the order as 10138, the report body names EO 10130, parties and date match); EO 12553 as formal disposition.
- EO:10010, 10038, 10048, 10138, 10139, 10147 blocked. Held PDFs are present and hash-verified and give the report dates (1948-12-17, 1949-09-19, 1949-04-29, 1950-08-11 for both 10138 and 10139 as one joint report, 1950-09-13), but no evidence record in this packet carries the transmittal-letter span, no reviewed factual event exists for them, and the assembler refuses the packet's report_deadline TERM records as an end. Exact missing item for each (a SUPPLEMENT excerpt with text path and char range) is in decisions.csv unresolved_material_gaps. EO 10048 also has a wrong dossier inventory (scopes lead, 3, c, c-3 include a Civil Service Commission notice; the order is chars 617-2201 of its FR text). EO 10147's text file lacks the letter date line (image only; the cover date is in the text).

## What took the time
10010: report PDF and extension/standstill reading. 10029: factual-event routing (FACT can only be a later event; end sourced from the clause's own terms). 10038: shared deadline/extension records. 10048: inventory defect. 10130: letter order-number misprint check. 10138/10139: confirming one joint report. 10147: letter date only in image. Coordination of the route rules took most of the time.

## Files opened beyond views
research/readiness/owner_rulings/2026-11-08-haloander-decisions.md (cited by prior olney claim in the view) and research/excavator/claude-haloander-2026-11-07/tools/prompts/board_rule.txt (the board rule it names). PACKET.json loaded once via batch.load_packet for evidence spans. Report PDFs and source-ladder texts read directly.

## batch-check counts, Geddes
Not run (apply blocked). No flags.

## Tool defects
(1) apply fails closed on prior-research drift caused by other waves writing complete-v1 outputs during the wave. (2) The packet has no source-supplement excerpts (declared_excerpts 0), so the transmittal letters cannot be cited for six orders.
