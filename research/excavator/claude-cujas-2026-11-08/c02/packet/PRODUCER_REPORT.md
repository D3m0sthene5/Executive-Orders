# Cujas c02 producer report
Start 2026-11-08T17:52:14Z; end 2026-11-08T18:02:28Z.

## Method
Each working text (APP transcription) was compared word by word (normalised token diff, then read) with its Photius GPO printing; dates, numbers, titles, signature, completeness and quoted spans checked. Page check per AGENT_PROTOCOL APP rule (MIRROR_DOCUMENTS/DOCUMENTS row by sha256: heading, date, text_sha256) and also compared with the official printing. For the APP working text and the official_printing entry of each member, identity/complete/pages set true; approved true. The unregistered clause-drafts copy left false. Cited extension-order texts (EO 8328, 8368, 8369, 8615, 8710, 8345, 8392, 8414, 8747) were collated the same way and confirmed (apply had rejected 7 members until they were).

## Per order (all submitted unless stated)
All 24 submitted: EO 8801, 8899, 8905, 8907, 8949, 8967, 8995, 8996, 9009, 9030, 9037, 9043, 9077, 8032, 8041, 8046, 8048, 8058, 8060, 8073, 8074, 8075, 8094, 8096. Transcription agrees with the printing (only OCR noise, printing header stamps, spaced punctuation, broken hyphens). Notes:
- EO 8907: APP reads "47 Stat. 382, 401"; GPO reads "404" (as all siblings). Page-cite typo, not quoted by the claim; recorded in rationale; not treated as material.
- EO 8995, 8996, 9009 (and extension 8328): GPO dateline truncated at the page edge ("194"/"19"); year supplied by APP and register. EO 9030: printing typo "Februrary" (OCR/printing), same date.
- Ends rechecked against the printing text: each stated end date matches the claimed effective date (EO 8041: one year from March 1, 1939 = 1940-02-29). No savings change needed. FR notes: no "Revoked by" note on any member (EO 8905 itself revokes EO 8538, irrelevant). "Amended by" notes on 8041, 8046, 8058(See), 8060, 8070, 8094, 8096 and the See-note on 9009 are further-exemption orders (read in full), already reconciled in earlier_end_check; EO 8293 note on 8094 rejected as before (unrelated text). Claimed ends stand.
- EO 8070: BLOCKED. Cited extension EO 8351: APP text dateline "February 26, 1940." vs GPO printing "February 25, 1940." (and FR catalog 1940-02-25). Actor text cannot be confirmed; submitting with the GPO date (applied-v2) was rejected by the checker (working_text confirmation required). Gap recorded in unresolved_material_gaps. Its own text agrees with the printing and its end 1940-03-31 is unaffected.

## Batch check (applied-v3, final)
packet 25; assembled 24, blocked 1; actual checker 24/24 all_checks_passed; mechanical fail 0; actionable failures 0. v1: 18 pass / 7 rejected (extension texts unconfirmed); v2: 24 pass / 1 rejected (8070).
## Geddes
Lint flags 0; resolutions file empty (no flags). 
## Tool defects
None blocking. Note: the kit cannot cite an official printing as ACTOR_TEXT source when the APP actor text is wrong.
