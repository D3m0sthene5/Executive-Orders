# Producer report, packet o05 (Tribonian, 2026-11-04)

Start UTC 2026-11-04T05:12:22Z. End UTC 2026-11-04T06:07:58Z. Final applied directory: applied-v3.

## Outcome
All 30 orders submitted, none blocked. Whole-order status stays "no" for each (provisional, unchanged).
- 27 one-person retirement exemptions (EO 8413, 8414, 8421, 8422, 8448, 8452, 8453, 8477, 8481, 8483, 8489, 8491, 8503, 8504, 8520, 8524, 8525, 8539, 8543, 8552, 8554, 8555, 8562, 8581, 8582, 8584, 8603): one clause each, terminated on the order's own stated end date, recorded inclusive with the exclusive reading disclosed. Savings: transferred_or_accrued (service during the exempted period). Working texts are APP transcriptions (page check done against the mirror record).
- Later further-exemption orders held for 8413 (EO 8810), 8422 (EO 8804), 8483 (EO 8828), 8504 (EO 8917), 8524 (EO 8866), 8525 (EO 8827; EO 8844 amends 8827, not 8525), 8555 (EO 8805), 8584 (EO 9002) are later events, not ends.
- EO 8413: held text prints the end year as 1041; recorded as 1941-06-30 with the misprint explained (one-year term, recital, EO 8810 recital). The first v2 claim dated the end 1941 only in prose and the checker flagged date-before-signing; fixed in v3 by recording 1941-06-30 as the date.
- EO 8421, 8491, 8520, 8581: name or spelling misprints in the held text disclosed in the rationale.
- EO 8428 (partial revocation of EO 6228, effective 1940-07-01) and EO 8529 (revocation of EO 4901, effective sixtieth day after 1940-08-27, computed 1940-10-26, alternative 10-25 disclosed): command exhausted by performance on the effective date; Federal Register text layer only, no page image inspected (original_pages_confirmed false).
- EO 8536: first end EO 9894 (1947-09-23, discontinues the area, names 8536). EO 9787 (1946-10-05) recorded as a later restatement with before/after text under the strike-and-insert ruling, with the alternative reading disclosed. Savings none_after_bounded_search.

## What took the time
Each apply took about 7 to 8 minutes (source pinning); three applies were needed. Reading the 27 near-identical exemption texts and the tooling (assembler field names, end_id rules) took most of the research time. EO 8428/8529 and 8536 needed their own reading; 8428 and 8529 first failed because the end source id must be an evidence record with an actor (fixed with ORIGINAL id).

## Batch-check (applied-v3)
30 members, 30 claims checked, strict pass 30, strict fail 0. Actual checker: 30 gate-passed, 3 all-checks-passed, 27 mechanical-unverified (custody_record_only and matched_date verbatim evidence; coordinator retains the bytes), 0 mechanical fail. applied-v1 had 2 rejected (8428, 8529); applied-v2 had 1 mechanical fail (8413 date); both superseded.

## Geddes
Lint on applied-v3 (GEDDES_LINT.json): 0 defect flags, 0 coverage gaps. One earlier attempt failed with "held corpus inventory commit changed during search" and succeeded on retry. No GEDDES_RESOLUTIONS.json needed.

## Full-packet files opened beyond the views
PACKET.json (via batch.load_packet, structured evidence and own-term spans), decisions.csv and clauses.csv (blank sheets), RATIONALES.json. READ.md, LOOKUPS.md and LOOKUPS.details.json were not opened. Also read: held APP texts of the later orders, FR texts of EO 9787, 9894, 8428, 8529, 8536, MIRROR_DOCUMENTS.jsonl rows for the later actors.

## Tool defects
- The view for each order lists the later actors only as unconfirmed working_text rows; I set their confirmations true after reading the held text and matching the mirror record.
- cruden.py search output is unlabelled; a five-file hit for EO 8536 includes a neighbouring order's file (EO_9786) that prints EO 9787 on shared pages.
