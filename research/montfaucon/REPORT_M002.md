# m002: 50 Federal Register original-page checks, 1937–1940

**Result:** 50 distinct current `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` targets
independently reviewed after three planted controls per reader: **32 pass,
18 fail, 0 unsure**. Five initial verdict disagreements received separate
blind third-reader adjudications, all fail. The initial EO:7624 uncertainty
in both sealed reviews was resolved by each original reader's separate
supplemental examination of a contemporary GPO number-to-exact-page catalog
entry. The final check records are in `checks/m002-fr-modern-1937-1940.jsonl`.
Local `page_check.assemble` accepts all 100 m001+m002 checks with zero
rejections and derives 66 official fragments, 32 from this batch.

The source scan for every row is the public GovInfo Federal Register issue
PDF pinned by its SHA-256. For each passing row, images of every actual target
PDF page are retained with hashes; the five disputed citation rows also
retain the actual page image. This is source location and complete-order
coverage, with observed OCR errors recorded. It does not certify a clean
transcription, every tabular glyph, human review, physical location, or any
legal-status claim. The immutable source fragments and held texts were not
edited. The 193 Cujas Photius-stale IDs were excluded.

## Passing orders

EO:7543, 7544, 7573, 7585, 7624, 7718, 7729, 7764, 7775, 7776, 7818,
7832, 7848, 7853, 7915, 7916, 7923, 7926, 7968, 7970, 8043, 8107,
8193A, 8356, 8357, 8470, 8509, 8521, 8545, 8561, 8570, 8574.

EO:7624 is typeset without an order number in the Federal Register page.
The GPO *Monthly Catalog*, June 1937, printed page 797/PDF 137, expressly
identifies No. 7624, the May 29 Tongass enlargement, with the **same volume
2, issue 106, June 3, page 1119** as the complete inspected Register
printing. Its scan/image hashes and the independent reviewer supplements
are in the record. The 1944 WPA numbered list corroborates number, date and
subject, but says page 938; that conflicting WPA pinpoint is retained as a
secondary-source error and is not substituted for the Register's printed
1119. The neighboring WPA rows for 7622 and 7623 share that wrong 938
pinpoint despite their numbered printings on 1119.

Long target spans were inspected from opening through closing, including
EO:7926's 13-page land description, EO:8193A's 15-page tables, EO:8545's
13-page Selective Service rules, and EO:8561's 11-page regulations. Their
held OCR has recognition noise; page-check credit is limited to the complete
numbered source and its coverage, as described above.

## Failed held/cited spans

| Order | Actual complete PDF / printed pages | Exact failure |
|---|---|---|
| 7594 | 2 / 2 FR 740 | Cited printed 739 is wrong, although PDF 2 holds the complete order. |
| 7651 | 3 / 2 FR 1379 | Cited printed 1377 is wrong; held OCR also interleaves EO:7652 and scrambles the target's column order. |
| 7700 | 1–2 / 2 FR 2215–2216 | Printed closing is **No. 7700-A**, not claimed No. 7700. |
| 7757 | 1–6 / 2 FR 3091–3096 | Held/cited page 1 stops at Regulation I §6 “or by any”; omits the remaining regulations and closing on page 6. |
| 7856 | 1–8 / 3 FR 799–806 | Held/cited page 1 stops at paragraph 13; omits paragraphs 14–127 and closing on page 8. |
| 7868 | 1–8 / 3 FR 903–910 | Held/cited page 1 stops in the Fort Hall description; omits the other reservation descriptions and closing on page 8. |
| 7924 | 1–2 / 3 FR 1639–1640 | Held/cited page 1 stops at §2 “for”; omits the rest of §2 and closing on page 2. |
| 7953 | 1–3 / 3 FR 1995–1997 | Held/cited page 1 stops at “witness”; omits land parcels and closing on page 3. Number is only handwritten on the Register printing. |
| 7959 | 1–2 / 3 FR 2071–2072 | Held/cited page 2 begins mid-order; title, authority and earlier paragraphs are on omitted page 1. |
| 8109 | 1–5 / 4 FR 1903–1907 | Held/cited page 1 omits tract descriptions, §II restoration and closing on page 5. |
| 8318 | 2 / 5 FR 194 | Cited printed 193 is wrong, although PDF 2 holds the complete order. |
| 8332 | 3 / 5 FR 315 | Cited pages 1–2 contain neighbors and no EO:8332; target is entirely on page 3. |
| 8336 | 2 / 5 FR 594 | Cited printed 593 is wrong, although PDF 2 holds the complete order. |
| 8337 | 2–3 / 5 FR 594–595 | Cited pages 1–2 stop within the first parcel; omit the remaining parcels, §§2–6 and closing on page 3. Printed opening is 594, not cited 593. |
| 8347 | 2 / 5 FR 672 | Cited printed 671 is wrong, although PDF 2 holds the complete order. OCR corrupts land fractions. |
| 8407 | 3 / 5 FR 1691 | Cited page 2 contains proclamations; the entire target is on omitted page 3. |
| 8560 | 1–13 / 5 FR 3923–3935 | Held/cited page 1 contains authority and table of contents only; omits Volume Three paragraphs 301–393 and closing on page 13. |
| 8617 | 2–3 / 5 FR 5230–5231 | Held/cited pages 1–2 stop at item 3; omit items 4–15, definitions, §2 and closing on page 3. Printed opening is 5230, not cited 5229. |

The exact first and last words, identity/date/signature, page-by-page source
pins and observed OCR differences are in each JSONL record. For the five
printed-pincite disagreements (7594, 7651, 8318, 8336, 8347), the original
reader B PASS assertions remain visible alongside reader A's FAIL and the
independent adjudicator's final FAIL. The wrong printed pinpoint is fatal to
the exact source-fragment citation even when its PDF page range includes
the target.

## Blind controls and sealed reviews

The three m002 challenges were: wrong neighboring PDF page for EO:7544,
closing No. 7545 in place of printed 7544, and land “lots 5 and 8” in place
of printed “lots 5 and 6.” Both readers independently rejected all three
before the real 50. The blind challenges, key, separate control answers,
original reviews and EO:7624 supplements are retained under `reviews/m002/`.

| Receipt | SHA-256 |
|---|---|
| Sealed reader A 50-row review | `22b86bfc02eeda74131cbe7435e7dbb539ded1f93d61269aa62b704d030c09e8` |
| Sealed reader B 50-row review | `6bf6616a469ff4c87950f5a42ab3c1bc5025e55ca1e6197a0af11b9c8d9cc2ef` |
| Reader A control answers | `80ec4a9af49f80f13679ae152362e79ef9a51b9d9f44727e9d31cd4fbd5cd447` |
| Reader B control answers | `fb7f303cdb7921511d779cff046c5aadeae9e2bfb7f0e039fc1af535fb952811` |
| Reader A EO:7624 supplement | `00416440664086bb456a9399cbb930171cf50f8e04f41714a14fb0280ecc4820` |
| Reader B EO:7624 supplement | `82c80c1d41bbef6ae967ce3f79e702cf02d2b487e16624a72692414c0392d70c` |
