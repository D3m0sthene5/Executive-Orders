# Producer report, packet n02 (route: no, provisional NO)

Start UTC: 2026-11-25T15:52:44Z. End UTC: 2026-11-25T16:11:23Z.
Final applied directory: research/excavator/claude-baldus-2026-11-25/n02/packet/applied-v2 (applied-v1 is retained; both claims in it were rejected by apply for a placeholder word, a working-text source note and an unresolved conflict).
Submitted 2 (EO:13322, EO:11434); blocked 13. No order was found in force on 2026-10-14.

## Outcome per order

| Order | Outcome | Why / exact missing source |
|---|---|---|
| EO:13322 | submit (no) | Superseded by EO 13332 sec. 8 (signed 2004-03-03, no later effective wording). Schedule-effective dates of EO 13332 disclosed as an alternative reading. Sec. 5(b) and sec. 8 recorded as ending with the order. |
| EO:11434 | submit (no) | Inventory corrected (Sec. 1 restored, Sec. 4 merged). Secs. 1, 3, 5 end 1981-02-15 (EO 12292 sec. 10(i), "effective as of February 15,1981"). Secs. 2, 4 end 1982-05-21 (EO 12363 sec. 3 revokes EO 11264). Whole-order end 1982-05-21; EO 12553 (1986-02-25) is the formal disposition; EO 12107 amendment and EO 12292 sec. 10(h) partial revocation listed as later events. |
| EO:9053 | blocked | Text of Public Land Order 678 (15 FR 7299) not held; FR_15_9161.txt is a different page. Bound: revoked by PLO 678, 1950-10-24, per OFR note. |
| EO:12339 | blocked | Date of the Housing Commission's final report (EO 12310 sec. 4(b) own-terms end) not held. Bound: EO 12399 sec. 4(g) revocation effective 1982-12-31. |
| EO:10279 | blocked | Source for the end of the Senate Special Committee (S. Res. 202) or exhaustion of the inspection authority. |
| EO:12563 | blocked | Report-submission date of the emergency board not held (no eumenes-nmb entry; NMB PDFs are custody_record_only). |
| EO:12714 | blocked | Same as EO:12563. |
| EO:9821 | blocked | Statute or order abolishing the National Housing Agency and its Administrator; Reorganization Plan No. 3 of 1947 (held) does not expressly abolish it. |
| EO:11364 | blocked | Source for withdrawal of federal troops and release of the Michigan Guard in 1967 (CMH study excerpt held covers PDF pages 1-40 only). |
| EO:9661 | blocked | ODT order ending possession and text of the Act of June 29, 1946 (60 Stat. 341), not held. |
| EO:13901 | blocked | EO 13970 sec. 8 supersedes "as of the effective dates specified in section 7"; only Schedule 8 has a stated date (2021-01-01); the other schedules depend on pay-period start dates not in citable packet evidence. |
| EO:11285 | blocked | Pub. L. 93-17 (Interest Equalization Tax Extension Act of 1973) text not held; dossier inventory runs into unrelated Federal Register text after Sec. 6. |
| EO:9153A | blocked | Texts of PLO 284 (1945) and PLO 1087 (1955) not citable; inventory faulty (lead segment spans contents pages; Tracts 2-3, EO 8789 revocation and confidentiality command omitted). Bound: PLO 2437 (1961-07-18) revoked the order in its entirety. |
| EO:11669 | blocked | Held source for the date of J. Edgar Hoover's interment. |
| EO:10200 | blocked | Corrected inventory needed (Sec. 7 missing; Sec. 2(c)(5) and 6(b) runs contain unrelated text) and clause-by-clause reading of ten held later orders; bound: superseded by EO 10480 sec. 607 on 1953-08-14. |

## What took the time (one line each)
- EO:13322: confirming the end date against EO 13332 sec. 7 and 8 and the prior accepted pay-order claims; the working-text rule removed an OPM-notice source note.
- EO:11434: inventory correction, tracing four later instruments (EO 12292, 12363, 12553, 12107) and the Board provisions of EO 11264; the mirror-text evidence for EO 12363 had to be replaced by the FR text.
- EO:9053, 9153A: tracing PLO citations; only PLO 827 and 2437 are held as texts.
- EO:12339: reading EO 12310 and 12399 to separate the Commission's own-terms end from the cleanup revocation.
- EO:10200: reading EO 10281, 10433 and 10480 to see that a corrected inventory and per-clause mapping were needed.
- EO:9821, 9661, 11285: searching the held statute texts; none holds the ending text.
- EO:12563, 12714, 11364, 11669, 10279: one search each of the held corpus for the ending fact; none found.
- EO:13901: working out why the exact first end cannot be dated from packet evidence.

## batch-check (applied-v2)
packet_members 15; claims_checked 2; strict_claim_pass 2; strict_claim_fail 0; actual claim checker: 2 of 2 passed all checks; actionable_failures none; blocked 13.

## Geddes
Lint on applied-v2: 0 defect flags, 3 coverage gaps (citing_corpus_incomplete on both claims, unclassified_instrument_mention EO:13291 for EO:13322#sec8). No resolutions needed; GEDDES_RESOLUTIONS.json is written with an empty list. The EO 13291 mention is explained in the claim (EO 13291 amended EO 13282, which EO 13322 supersedes).

## Files opened beyond the per-order views
LOOKUPS.md (prebuilt, read in full); READ.md only by bounded sed/grep (the EO:9053 section, and an evidence-index scan of every member for ACT/ACTOR ids and spans); PACKET.json only through batch.load_packet in scripts (evidence texts, conflicts); HELD_SUPPLEMENT.json (alias list, to see whether it supplied citable evidence; it does not); decisions.csv and clauses.csv; DISPATCH_CHECK.json (head only). Repository sources opened: held order and statute texts named in the reports above, jobs/status-history/output events and histories for the OFR notes, jobs/current-law/output/MENTIONS.csv, and prior claims under research/readiness/claims for the pay-order treatment.

## Tool defects and notes
- The assembler's placeholder check matches the plain word "placeholder" in prose; the first apply rejected EO:13322 for it.
- An ACT evidence record built on an APP mirror text (EO 12363) forces the working-text route and then fails with official_copy_available_recheck_required because the FR text is held; the ACTOR_TEXT record of the FR text avoids this but quotes the whole order.
- kit.py apply refuses a write path outside the packet, so trial runs could not go to scratch.
- LOOKUPS and the dossier flag "cited by number: EO:1126" for EO:11434, a mis-parse of the heading "Executive Order No. 1126If".
