# Pinakes: ProQuest PDFs wired in

Generated 2026-11-25T22:50:09Z.

**4903 PDF files** (4841 unique) in `ProQuest Pre-1937 Orders`, `research/pre-1937-sources/ProQuest Pre-1937 Orders` cover **4841 orders**, 4841 of them in the census. The owner's link list has 2765 links: 2750 now have a PDF, **15 are still missing** (`MISSING_FROM_UPLOAD.csv`); 2091 PDFs are for orders not on the list.

| Text | Orders |
|---|---:|
| From the PDF's own text layer | 3984 |
| From OCR (tesseract) | 857 |
| No text yet | 0 |
| Usable quality | 4267 |
| Low quality (probably handwritten; needs a person) | 574 |

This run OCR'd 0 orders (0 of 4000 budgeted pages), carried 857 texts forward from the last run, and left 0 for the next run.

Every order has a fragment in `FRAGMENTS.jsonl` with `acceptable_as_original: false` and `needs_page_check: true`; the readiness tracker reads them as the lead class ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK. A person comparing the pages and the codebook assigning the grade is what would let one count.

## PDFs for orders not on the supplied list

EO:1, EO:1001, EO:1003, EO:1004, EO:1005, EO:1006, EO:101, EO:1010, EO:1011, EO:1012, EO:1014, EO:1015, EO:1016, EO:1017, EO:1018, EO:1019, EO:102, EO:10214, EO:1024, EO:10246, EO:1025, EO:1026, EO:1028, EO:1029, EO:103, EO:1031, EO:1033, EO:1034, EO:1035, EO:1036, EO:1037, EO:1038, EO:1039, EO:104, EO:1040, EO:1041, EO:10417, EO:1042, EO:10427, EO:1043, EO:1045, EO:1046, EO:1047, EO:1049, EO:105, EO:1050, EO:10524, EO:1053, EO:1055, EO:1057, EO:10578, EO:1058, EO:10588, EO:1059, EO:106, EO:1060, EO:1061, EO:1062, EO:1063, EO:1064 ...

