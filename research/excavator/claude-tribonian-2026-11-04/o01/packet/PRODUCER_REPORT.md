# Producer report, Tribonian o01 (claude)

Start UTC 2026-11-04T04:48:12Z (first session); resumed on the re-prepared packet at 05:17:07Z. End UTC 2026-11-04T06:06:16Z.
Final applied directory: research/excavator/claude-tribonian-2026-11-04/o01/packet/applied-v3 (applied-v1 and applied-v2 are retained earlier versions).

## Counts
Submitted 27, blocked 3 (30 members). batch-check on applied-v3: claims_checked 27, strict_claim_pass 27, strict_claim_fail 0; actual checker: all checks passed 5, mechanical pass with unverified 22, mechanical fail 0, gate passed 27. The unverified items are source_held custody_record_only (coordinator retains the bytes) and one date_valid/verbatim_evidence_text item on the working-text confirmation record; I did not work around either.
History: applied-v1 rejected 3 (7738 and 8007: end_id pointed at a clause id instead of the original; 7845: unresolved conflict FULL_AND_PARTIAL_EVIDENCE_CONFLICT). applied-v2 assembled 28 but the actual checker failed EO 7831 (order_exists:not_in_universe on the fused footnote numerals in the registered OCR text of EO 8704), so 7831 was moved to blocked in applied-v3.

## Outcome per order
Submitted, terminated by own terms (fixed "ending" date, inclusive, exclusive reading disclosed): 7912 (1939-09-30), 7914 (1939-07-31), 7929 (1939-07-31), 7930 (1939-07-31), 7931 (1939-11-30), 7932 (1939-09-30), 7935 (1939-07-31), 7945 (1939-08-31; later event EO 8231), 7949 (1939-08-31), 7950 (1939-09-30), 7954 (1939-09-30), 7958 (1939-09-30; later events EO 8252, EO 8543), 7973 (1939-09-30), 7974 (1939-10-31), 7978 (1939-09-30; later event EO 8217), 7982 (1939-09-30), 7988 (1939-10-31), 7989 (1939-10-31), 7991 (1939-11-30), 7995 (1940-01-31; later event EO 8326), 7996 (1939-11-30), 8002 (1939-07-31, six months). Extensions are later events, not ends. Held text is the APP transcription with the standing note.
Submitted, own-terms window: 7738 (1938-01-15), 8007 (1939-01-15), Federal Register originals.
Submitted, express discontinuance: 7747, ended 1947-09-23 by EO 9894; EO 8536 and EO 9787 are later events (amendment and restatement).
Submitted, corrected inventory: 7980 (clause restricted to the 7980 text; the dossier clause sat on EO 7981's text), ended 1938-12-31 by own terms. 7845 (inventory corrected to 40 clauses including the enacting paragraph and page-break splits): regulatory clauses ended 1940-03-02 by EO 8384 supersession (signing 1940-03-29 disclosed; retroactive 1936-07-01 date for 8384 sections 6 and 9 disclosed); sections 20 to 22 ended by performance on issuance or publication; EO 7879 (section 6) and EO 8226 (section 15) are later events.
Blocked: 7554 and 7689 (no held instrument ends EO 7180 as amended or the Puerto Rico Reconstruction Administration's authority; searches of held texts returned nothing). 7831 (supersession by EO 8704 on 1941-03-04 is established from the clean held APP text, but the only registered, citable EO 8704 evidence is OCR text that the actual checker rejects; needs a source supplement adding the 8704 sentence).

## What took the time (one line each)
Retirement family (22): pattern fixed once; time in extension-order texts, page checks and identity notes (7931 Marion/Marlon, 7973 Joseph/Alfred).
7738, 8007: end_id correction only. 7747: tracing 8536/9787/9894. 7831: checker rejection of OCR numerals, blocked. 7845: inventory correction, conflict resolution, performance-versus-supersession call. 7980: finding the mislocated clause. 7554, 7689: searching for any PRRA-ending source.
Tool runs: apply about 2 to 5 minutes, batch-check about 5 to 10 minutes, Geddes 1 to 3 minutes each.

## Geddes (applied-v3)
defect_flags 1, coverage_gaps 3. Resolutions in applied-v3/GEDDES_RESOLUTIONS.json: EO 7845 unaddressed_citing_instrument EO 7880 disputed (the held FR file for 7880 prints 7879 on the same page; 7880 itself amends EO 7846); EO 7980 coverage gaps (order_heading_unresolved) disputed as a limitation of the registered text, handled by the corrected inventory span.

## Full-packet files opened beyond the views
PACKET.json (via batch.load_packet, for evidence ids, TERM spans, actor contexts, conflicts), decisions.csv, clauses.csv, LOOKUPS.md (summary lines). No READ.md, no LOOKUPS.details.json.

## Tool defects and notes
- batch.load_packet takes Path arguments, not strings.
- The dossier chain for 7831 lists EO 8109 (a neighbouring order on the same FR page) and for 7845 lists EO 7880 (same-page overlap with 7879); both are machine noise and were not cited.
- A coordinator-notified checker bug on matched_date was fixed before my final batch-check; no workaround used.
- Scratch and generator at /tmp/claude-0/tribonian-work/o01/ (producer_build.py, logs, .orig sheet backups). The sheets in the packet were written by that generator.
