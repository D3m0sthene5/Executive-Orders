# Pinakes: ProQuest PDFs wired in

Generated 2026-10-22T17:48:11Z.

**2807 PDF files** (2751 unique) in `ProQuest Pre-1937 Orders`, `research/pre-1937-sources/ProQuest Pre-1937 Orders` cover **2750 orders**, 2750 of them in the census. The owner's link list has 2765 links: 2750 now have a PDF, **15 are still missing** (`MISSING_FROM_UPLOAD.csv`); 0 PDFs are for orders not on the list.

| Text | Orders |
|---|---:|
| From the PDF's own text layer | 2297 |
| From OCR (tesseract) | 453 |
| No text yet | 0 |
| Usable quality | 2440 |
| Low quality (probably handwritten; needs a person) | 310 |

This run OCR'd 0 orders (0 of 4000 budgeted pages), carried 453 texts forward from the last run, and left 0 for the next run.

Every order has a fragment in `FRAGMENTS.jsonl` with `acceptable_as_original: false` and `needs_page_check: true`; the readiness tracker reads them as the lead class ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK. A person comparing the pages and the codebook assigning the grade is what would let one count.

## Files left alone

- `ProQuest Pre-1937 Orders/LRS-10-21-Cold-Calls-Plain.pdf` (164337 bytes, signature yes)

