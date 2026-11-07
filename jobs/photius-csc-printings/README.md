# Photius CSC printings: Civil Service Commission annual reports as official printings (R37)

`jobs/csc-annual-reports` located 803 orders in the Commission's annual reports (Serial Set House Documents on
GovInfo) from the WPA/Lord citations and filed them as leads. Under ruling R37 (2026-11-06) a full-text printing in an
official government publication is an official printing witness once a page check confirms the dateline or number and
the signature block. This job runs that check and rescans the reports by date for orders the WPA list cites nowhere.

## Method (owner's PC; the GitHub runner does not run this job)

1. The 37 report PDFs (4.9 GB) are re-fetched from GovInfo into a private cache and verified against the hashes the
   csc-annual-reports job recorded; every page's text layer is cached.
2. `scan.py` step A: for the 803 located orders, the cited page's dates and signature words are re-read; a seeded 10%
   sample of the high-confidence locations and every medium and low one go to Opus page checks (brief
   `research/excavator/photius-csc/PROMPT.md`). Step B: every date line in all 37 reports is matched to frame orders
   with no WPA printed citation; a hit with a signature block nearby or a subject overlap goes to the same check.
3. `assemble.py`: a page counts only when the check found the full text with its signature block. The sampled
   high-confidence batch is judged per report: a report whose sampled pages all pass promotes its unsampled
   high-confidence locations; one with a sampled failure promotes nothing unsampled.

## What the pages showed

The reports for fiscal 1912-1929 print the orders under a date heading, in full, but without the signature block and
often with the Commission's own comment. Under R37 those are `full_text_no_signature`: dated, located leads, not
official printings. The 1895-1909 reports print the order with "Approved <date>. <President>", which passes.

`output/FRAGMENTS.jsonl` carries grade `official_printing` (needs_page_check false) where the check passed and
`csc_report_lead` (needs_page_check true) where it did not; `acceptable_as_original` is false throughout. Nothing here
changes a status, the census, the codebook or the human-certified count (0).
