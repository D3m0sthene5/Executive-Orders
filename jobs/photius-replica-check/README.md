# Photius replica check: the ProQuest "Replica of Original" scans, read page by page

The project holds 2,750 ProQuest Congressional "Replica of Original" PDFs (Pinakes, `jobs/pinakes-proquest-ingest`),
each an image of the State Department's file copy of a numbered order, matched to its number by file name only. The
tracker filed them as leads with the blocker `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK`. This job is that page check,
done on 2026-11-06 under the owner's Photius prompt (decision D-20261106-photius-p4).

## Method (owner's PC; the GitHub runner does not run this job)

1. `extract.py`: for every order whose text step is open and whose blockers include the replica lead (2,557), a
   deterministic read of the Pinakes text (layer, OCR, or the Pinakes HTR reading for handwritten scans): numbers,
   dates, signature words, first and last words; packets of 30 for the readers.
2. `render.py`: first, second and last page of every replica PDF as 130-dpi PNGs (kept out of git).
3. Sonnet readers (brief `research/excavator/photius-replica/PROMPT.md`), one packet each, fresh context: they record
   the number, date, signature block and first and last words as seen, and a verdict `pass`, `fail` or `unsure`, looking
   at the page images whenever the text does not settle it.
4. Opus adjudicators (`ADJUDICATE.md`): every reader `fail` and `unsure`, plus a seeded 5% sample of passes as a
   control (`adjudicate_packets.py`).
5. `assemble.py`: `output/RESULTS.csv`, `output/FRAGMENTS.jsonl` (grade `archival_replica_checked` on a final pass,
   `needs_page_check` false; otherwise `archival_replica_check_failed_or_pending`, `needs_page_check` true), `SUMMARY.json`,
   `REPORT.md`, `STATUS.json`.

## What a pass means

The scan the project holds under this number is the order the project expects: the number is visible (stamp, heading
or closing tag) and nothing contradicts the date beyond a few days, or (for orders before about 1907 and for Alien
Property Custodian orders, which carry no printed number) the date, signature block and subject agree. The replica is
an image of the State Department file copy, so a checked replica credits the original-text step under ruling R37's
logic. The bytes are ProQuest's: the tracker row carries the flag `REPLICA_CHECKED_PROQUEST_BYTES`, and the witness is
to be re-pointed to NARA M1118 (public domain) or the owner's HeinOnline page facts when those arrive.
`acceptable_as_original` stays false; this is not an authentication and not a legal conclusion. Nothing here changes a
status, the census, the codebook or the human-certified count (0).

## Fails found

A handful of files hold the neighbouring order, a cover slate or a transmittal letter instead of the order (listed in
`output/REPORT.md`). Those orders keep the lead blocker and need another source.
