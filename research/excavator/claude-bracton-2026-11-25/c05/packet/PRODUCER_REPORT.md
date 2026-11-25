# Producer report, c05 (route: correction)

Start 2026-11-25T09:09:34Z. End: see the timestamp at the foot of this file.

## Outcomes

No claim was submitted. Seven assigned orders are blocked; the two dispatch-blocked orders (EO 10971, EO 10975) keep their prepared `unresolved` rows.

All six orders with a held report (EO 11006, 11008, 11011, 11015, 11027, 11040) share one cause. Each filed claim ends the order at EO 12553 (1986-02-25) as a not-later-than bound, with first cause unresolved. The rule in the Haloander owner ruling (A-20261107-board-rule, `research/readiness/owner_rulings/2026-11-08-haloander-decisions.md`) ends the board command on the transmittal-letter date of the held report and the standstill 30 days later. I fetched each report PDF from the Pergamon store (jobs/eumenes-nmb-reports/output/SOURCES.jsonl locators; every hash matched) and read the transmittal letter on the page image. Letter dates: EO 11006 1962-05-01 (PEB 144), EO 11008 1962-05-03 (PEB 145), EO 11011 1962-05-01 (PEB 146), EO 11015 1962-06-14 (PEB 147), EO 11027 1962-08-30 (PEB 148), EO 11040 1963-03-04 (PEB 150; settlement report). Each cover date agrees with its letter.

The claim cannot cite these dates. `end_id` must be a packet evidence id, and the only report-text evidence ids in the packet are spans over other passages (none holds the cover or letter date; for EO 11040 the existing cover span stops just before the date). Creating a new span needs `source_supplement.py prepare`, which my brief forbids. Exact missing source per order, as a supplement declaration over the held text (character offsets are into the Unicode text; text sha256 values are in decisions.csv gap text and /home/claude/bracton-scr/work/c05/offsets.json):
- EO 11006: queue_EO_11006_..._3570471334.txt, cover 729-1214, letter from 1265.
- EO 11008: queue_EO_11008_..._f7f48320f7.txt, cover 700-1261, letter from 1286 (letter OCR is clean: "MAY 3, 1962.").
- EO 11011: PEB-146 text, cover 998-1502, letter from 1560.
- EO 11015: PEB-147 text, cover 725-1201, letter from 1252; the packet also lacks the ACT provision for EO 12553 ("target provision not located"), though the held EO 12553 table lists 11015.
- EO 11027: PEB-148 text, cover 700-1233, letter from 1284.
- EO 11040: PEB-150 text, cover 737-1197, letter from 1246.
The OCR of the letter date line is damaged in 11006, 11011, 11015, 11027 and 11040 (for example "May 1, 136~"), so a quote must use the clean cover date line, with the letter date recorded as a page-image reading. The supplement declaration needs a `local_path` to held bytes; the PDFs are in the Pergamon store, not the repository, so the coordinator must confirm the supplement route accepts a Pergamon-held file.

EO 11033: no report is held. source-ladder's fetch of NMB PEB-149-Report.pdf (33,438 bytes, sha256 3f50b19def1ed723a77e7b41e83d114d3c2133513741d87af3a159c77e959d30) was rejected as not an emergency board report. The NMB index (created 6/20/1962, closed 8/11/1962) is an index entry, not a report date.

Formal disposition for all nine orders: EO 12553 of 1986-02-25 (each number appears in the held EO 12553 revocation table).

## What took the time
- EO 11006, 11011, 11015, 11027, 11040: reading the damaged OCR, then rendering and reading the letter page image.
- EO 11008: clean OCR; nothing beyond the evidence-id check.
- EO 11033: searching for any held report; none.
- Orientation: finding the board rule (its prompt file, board_rule.txt, is no longer in the checkout) and the Pergamon store.

## Checks
apply: 7 blocked, 2 unresolved. batch-check: 0 claims checked, 0 failures, 0 actionable failures. Geddes: 0 flags, 0 coverage gaps (applied-v1/GEDDES_LINT.json); no resolutions file needed.

## Files opened beyond the views
None of PACKET.json, READ.md or LOOKUPS.details.json. I loaded PACKET.json once through batch.load_packet in a script to list evidence spans. Outside the packet I read: jobs/eumenes-nmb-reports (README, SOURCES.jsonl), research/lind/board-candidates-2026-11-13 (RESULT.md, CANDIDATES.csv/json, NMB inventory html), jobs/source-ladder/output (SOURCES.jsonl, ATTEMPTS.jsonl, report texts), jobs/fr-originals text of EO 12553, and one old claim line (tribonian-f01, EO 10286) as a format example.

## Tool defects and notes
- The coordinator brief says NMB report PDFs are custody_record_only. Since 2026-11-10 they are in the Pergamon store and the checker has an adapter, so the bytes are held; the block here comes from the missing evidence span, not custody.
- Lind's flag "no_thirty_day_sentence_in_claim_text" for EO 11027 is spurious: the sentence is present, split by a line-end hyphen in "re-port".
- The EO 11040 report cover reads "Executive Order 11041" while its letter reads "Executive Order No. 11040"; EO 11040 (Belt Railway Company of Chicago, 1962-08-06) is the order created that day. A reviewer should see this.
- I did not read the filed claims' reviews; the blocks do not depend on them.
End 2026-11-25T09:15:27Z

## Recheck after the coordinator note (jobs now on disk)
No block rested on an absent file. jobs/astra-source-retention/output/pdf holds 251 PDFs, none with the hashes of the PEB 143-150 reports or the rejected PEB-149 file. The selden-fr-citers hits for 11015 and 11033 are FR document numbers, not citations of these orders. Blocks and applied-v1 unchanged.
