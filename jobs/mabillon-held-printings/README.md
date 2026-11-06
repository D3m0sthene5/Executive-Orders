# Mabillon held printings: official printings the project already holds, proved by text

Named for Jean Mabillon (1632-1707), founder of diplomatics, the science of authenticating original documents.

`jobs/hathi-gpo-orders` saved government-printed pages for 1,531 orders numbered 5076-8027: the Government
Printing Office's bound *Executive Orders* volumes (Wikimedia Commons DjVu scans, local OCR), the 1974 GPO
compilation *Proclamations and Executive Orders: Herbert Hoover* (Internet Archive), and govinfo scans of 1936
Federal Register issues. The readiness tracker files that job as a compiled transcription, a lead only, so 551 of
the orders in Mabillon's frame (`research/mabillon/frame/FRAME.csv`, orders with NO_OFFICIAL_SOURCE_LOCATED) show
no official source although their official printing is held. This job proves, offline and without tokens, which
saved passages are the order, so the owner can decide whether to count them under the rule Tischendorf already uses.

**Volume route.** `hathi-gpo-orders` OCRed whole Commons volumes (5800-8027; page dumps committed under its
`output/books/`) but saved passages only for its 1,712 target orders, which had no text at all. For every other order
in a volume's range, this job finds the order's own closing number tag or heading in the page text, takes the marker
page and its neighbour, and judges it by the same rules and controls (route `commons_gpo_volume`).

## Rule

A passage is a **strong** machine location when all of Tischendorf's checks pass (imported unchanged from
`jobs/tischendorf-originals`: own number as a heading or closing tag, text fingerprint score >= 0.5 against an
independent transcription with >= 8 rare shingles, government-printed source, controls passed) **and** two checks
added here, each forced by this job's planted controls:

1. **Own segment.** The saved passages are whole printed pages and often carry the next order. Only the text between
   the previous document's closing number tag and the order's own is scored. Without it, 11 of 4,382 negatives
   matched, and on inspection all 11 were real: the next order is printed on the same page.
2. **Neighbour margin.** Orders issued as families (codes of fair competition, veterans regulations, land
   withdrawals for resurvey) share rare wording. The claimed order's text must beat the text of every order numbered
   within 3 of it by at least 0.15. Without it, 49 of 4,382 neighbour negatives were accepted; with it, 0.

The independent witness is the American Presidency Project's transcription. It labels each order independently of
these scans; it is not a second official printing.

## Planted controls (every run)

- Positives: orders whose official original already counts and that also have a passage here; the passage must
  also agree with the counted official text (else its label is uncertain and it is not used).
- Negatives, three per passage: the passage under a wrong number (+7), and the passage under its own number paired
  with the transcriptions of the orders one and two places away in the same volume. The neighbour's text under its
  own number is counted apart, as a true neighbour printed on the same page.

A single accepted negative turns every strong verdict in the run into a lead. On 2026-11-06, with the volume route:
86 of 88 positives confirmed, 0 of 6,834 negatives accepted (2,452 of them on volume-route passages; 95% upper bound
on the false-accept rate 0.04%). Result: 1,771 strong (762 frame orders, 1,009 orders whose transcription must be
replaced), 244 leads.

## Outputs (`output/`)

`FRAGMENTS.jsonl` (producer schema the tracker reads; `grade: machine_read_government_printed_copy`,
`acceptable_as_original: false`, `needs_page_check` false only for strong), `SOURCES.jsonl`, `FINDS.csv` (every
passage: verdict, score, marker), `texts/`, `SUMMARY.json`, `REPORT.md`.

## What it does not do

No network, no status, identity, census, codebook or count change. The tracker does not read this job until the
owner registers it in `jobs/readiness-tracker/tracker.py` (`official_compilation_fragments`), which changes the
ready-for-human-review count. A strong find is a machine location, not an authentication; certified stays 0.
