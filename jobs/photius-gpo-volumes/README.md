# Photius GPO volumes: the bound slip-order series as official printings (EO 4306–9284)

Named for Photius of Constantinople, whose *Bibliotheca* catalogued and excerpted every book he could reach.

HathiTrust record 000070271 ("Executive order", U.S. Govt. Print. Off.) is the Government Printing Office's bound
series of numbered slip orders. On 2026-11-06 the owner downloaded twelve whole-volume PDFs (rights `pd`,
Google-digitized) covering EO 4306–7261, 7262–8314 and 8322–9284 in part, and 5660–5799 twice. The PDFs stay private
in `research/owner-inbox/hathi-gpo/` (git-ignored; `MANIFEST.json` and `SHA256SUMS.txt` beside them); the public
manifest is `data/VOLUMES.json`. Extracted text, page-render hashes and the per-order registrations are public.

## Method (owner's PC; the GitHub runner does not run this job)

1. `ocr_pages.py`: every page's own text layer (pypdfium2), a local Tesseract 5.5.3 read of a 300-dpi grayscale render
   and the render's SHA-256 (PNG). 9,086 pages in about ten minutes on 14 processes.
2. `segment.py`: finds every closing tag `[No. NNNN.]` in OCR and layer, keeps the longest increasing chain (OCR
   misreads drop out), assigns each order the pages from the previous tag to its own, reads the dateline before the tag
   (fuzzy, because the small-caps "THE WHITE HOUSE" OCRs as "Tue Waite House") and tests it against the identity layer
   and the volume's years, and checks for the signature block. Verdict `pass` when tag, date and signature agree;
   `check` when the date was not read, a tag gap precedes the order, or the dateline conflicts; `fail` when the number
   is not in the identity layer.
3. Page check (ruling R37): every `check` and `fail` plus a seeded 5% sample of passes go to Opus workers who read the
   page renders (`check_packets.py`, brief in `research/excavator/photius-gpo/PROMPT.md`); `apply_checks.py` folds the
   results into `output/PAGE_CHECKS.csv` and records the orders whose tag the OCR missed but a checker saw inside
   another order's span (`output/RECOVERED.csv`); `segment.py` registers those on the page the checker named.
4. `output/FRAGMENTS.jsonl` (producer schema; grade `official_printing`; `needs_page_check` false only when the
   alignment passed or the page check passed; `acceptable_as_original` false on every record) is what the tracker
   reads under `official_compilation_fragments`.

## Outputs

`ORDERS.csv` (one row per order: volume, pages, tag page, dateline, identity date, tests, verdict, render hashes, text
hash), `texts/EO_<n>.txt` (the printing's text with a provenance header), `FRAGMENTS.jsonl`, `PAGE_CHECK_QUEUE.csv`,
`PAGE_CHECKS.csv`, `RECOVERED.csv`, `pages/<htid>.jsonl.gz` (every page's text and render hash), `SUMMARY.json`,
`REPORT.md`, `STATUS.json`.

## What it is not

A located printing is a machine location of an official GPO printing, page-checked by a model, not an authentication
of the signed original and not a legal conclusion. Nothing here changes a status, the census, the codebook or the
human-certified count (0). The volumes above 7315 are registered too (they are the same series), but the owner's target
tonight was 4306–7315.
