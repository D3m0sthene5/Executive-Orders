# Photius free printings: official publications on the Internet Archive (R40)

Ruling R40 (2026-11-06) admits as routes the free Internet Archive copies of official publications that print executive
orders in full: the Department of Justice's *Emergency legislation* (1918), the State Department's *Trading with the
enemy act* compilation (1920), the Panama Canal Press *Executive orders relating to the Panama Canal, annotated* (1922),
the Fuel Administration's *General orders* (1919), the *Official U.S. Bulletin* (1917-1919), Kappler's *Indian Affairs*
vol. III (1913), Public Health Reports items, and fourteen GPO slips held by the National Agricultural Library. The
list with ranges is `data/SOURCES.json`.

## Method (owner's PC; the GitHub runner does not run this job)

1. The `_djvu.txt` and `_djvu.xml` files were fetched robots-compliantly from archive.org (metadata, SHA-1 verified).
2. `candidates.py`: one text per page from the XML; a page is a candidate when a block beginning "EXECUTIVE ORDER",
   "Order of the President," or "Executive order of the President" (index pages with more than six headings skipped)
   carries a signature block or a closing tag, and either prints an order number in the source's range or a date that
   the identity layer gives to an order in that range; one page per order per source; only orders whose text step is
   open or transcription-dependent.
3. Opus page checks on the text layer (brief `research/excavator/photius-free/PROMPT.md`): `full_text` with dateline or
   number and signature block, and a subject consistent with the index title, is a pass; citations, abstracts and
   full text without a signature block are leads.
4. `assemble.py`: `output/FRAGMENTS.jsonl` with grade `official_printing` (needs_page_check false) on a pass,
   `official_printing_lead` otherwise; `RESULTS.csv`, `SUMMARY.json`, `REPORT.md`, `STATUS.json`.

`acceptable_as_original` is false on every record; a located printing is a machine location checked by a model, not an
authentication of the signed original and not a legal conclusion. Nothing here changes a status, the census, the
codebook or the human-certified count (0).

## Run of 2026-11-06 (Photius)

631 candidate pages in 64 packets. Packets f011-f022 (the Fuel Administration *General orders*, 1919, 160 items) were
not checked: the twelve Official Bulletin packets f059-f064 and the earlier Fuel pages showed that every date-only match
in that material is a Fuel Administration order signed by H. A. Garfield that cites the August 1917 orders, not an
executive order, so the expected yield was near zero and the Opus budget went to the Panama Canal, DOJ, NAL and Kappler
packets instead (coordinator decision, reversible: the packets are still in `work/packets/` and can be run later).
Checked 471 pages: 117 pass (Panama Canal compilation 81, DOJ Emergency legislation 18, NAL slips 14, Kappler 2, State
Department TWEA 2), 346 fail (311 not on page, 35 citation only), 8 unsure. Unchecked candidates get no fragment.
