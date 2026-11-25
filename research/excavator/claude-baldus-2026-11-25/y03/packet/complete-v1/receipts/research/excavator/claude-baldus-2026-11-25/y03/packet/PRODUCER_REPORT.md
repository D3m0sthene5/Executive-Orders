# Producer report y03 (baldus)

Start 2026-11-25T15:22:42Z. End 2026-11-25T15:40:22Z.

Final applied directory: applied-v5 (applied-v1 to v4 were earlier iterations).

## Outcomes
- EO 11046 submit: all 8 clauses operative on the held original; EO 11382, 13286, 14085 as amendments on clause 1; no end held.
- EO 11079 submit: one operative clause; EO 11382, 12608, 13286 amendments.
- EO 11231 submit: four operative clauses; the 1973-03-28 OFR-note date is a qualifying-service limit, not an end.
- EO 11030 blocked: missing official page/image check (low location confidence, no montfaucon pass, register date 1962-06-15 versus held text June 19, 1962). Needs the FR page image or PDF.
- EO 11060 blocked: frozen packet reference conflicts with the montfaucon official_printing declaration for the same sha; needs a re-frozen packet.
- EO 11085 blocked: sec 2(a) conforming amendments to EO 10717 cannot be determined because earlier EO 10717 texts are not held; dossier inventory needs a split.
- EO 11183 blocked: held bytes of EO 12012 (42 FR 54249, FR 1977-10-05) are missing. The PDF (sha d9136f1a...) is custody_record_only, so the selected-source check fails on five references. Legal reading otherwise complete (EO 14354 continues to 2027-09-30; sec 2(b)(4) ended 1977-10-03); ready sheet kept in scratch READY_EO_11183.py.
- EO 11190 blocked: text of 10 U.S.C. 10149 (successor of former 271) is not held.
- EO 11223 blocked: 21 waived statutes with 2026 status not held; 63 FR 33754 and 89 FR 4201 are not terminations; EO 12163, 12178, 13118 need itemising.

No order was found out of force on 2026-10-14.

## Time spent
- 11046: chain noise (spurious EO 12977), eight clause scopes, custody failure on USC notes.
- 11079: three amendments, HEW to HHS reading.
- 11231: noisy TERM records and the 1973 date.
- 11183: twelve clauses, seven amending orders, then EO 12012 custody failure.
- 11060: apply rejection, diagnosing the page-check conflict.
- 11030, 11085, 11190, 11223: reading held texts to find the exact missing sources.

## Batch-check (applied-v5)
Members 9; claims checked 3; strict pass 3, fail 0; actual checker 3 of 3 gate passed; blocked 6, assembled 3; SELECTED_SOURCE_CHECK ok true.

## Geddes
0 flags, 3 coverage gaps (citing_corpus_incomplete, 1401 files). No resolutions file needed.

## Full-packet files opened beyond the views
LOOKUPS.md, decisions.csv, clauses.csv, RATIONALES.json, HELD_SOURCES.json, DISPATCH_CHECK.json, ADMISSION.json, PACKET.json (via batch.load_packet, pickled to scratch). Held support texts opened: jobs/current-law/output/usc-notes, jobs/fr-originals texts, montfaucon FRAGMENTS_OFFICIAL.jsonl, peano-formulario cc text, source-ladder AR 600-8-22 text.

## Tool defects
- Frozen packet stale versus montfaucon page check (EO 11060).
- CURRENT: USC-note records are custody_record_only, so cannot be the current basis; used ORIGINAL plus bounded searches. Code is current only through 2026-10-09 (5-day gap, disclosed).
- Cruden ACT chain mislabels EO 12977 evidence for 11046, 11079, 11190, 11231; not cited.
- EO 11231 has noise TERM records.
- EO 12012 PDF is not held (custody record only).
- Page-check images and PDFs not inspected; none held.
