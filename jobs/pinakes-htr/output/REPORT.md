# Pinakes HTR: new readings of the scans below the quality screen

Generated 2026-10-22T06:16:21Z on the owner's PC. Nothing was sent off the machine.

**310 orders** (555 pages) whose Pinakes text failed the screen were read again: by two vision-language models (Qwen3-VL-8B, the backbone, and Chandra OCR 2, the cross-check; `vlm.py`) and by tesseract at 300 dpi (`htr.py`; 89 orders now pass the word-shape screen, mostly typed pages).

## Why these models

Bake-off on three sample pages (EO 12 and EO 14, clean 1874 clerk's hands; EO 23, a faded 1884 page), scored against a reading made for choosing a model (not evidence): character error rate on the two clean pages, share of the faded page's readable part recovered.

| Reader | EO 12 | EO 14 | EO 23 recovered |
|---|---:|---:|---:|
| Qwen3-VL-8B (4-bit) | 3.5% | 0.6% | 87% |
| Chandra OCR 2 | 6.0% | 0.2% | 87% |
| Qwen3-VL-4B | 5.3% | 0.5% | 78% |
| Qwen2.5-VL-3B | 2.5% | 1.4% | 73% |
| CHURRO 3B | 10.3% | 1.1% | 82% |
| TrOCR large handwritten | 87.6% | 51.3% | 18% |
| tesseract 300 dpi | 86.4% | 69.5% | 21% |

On the faded page every model invented words where the ink fails, each different ones; Chandra also invented a signature and a date on EO 12. That is why two models read every page and only words both read count as confirmed.

## What these texts are

Machine hypotheses for searching and routing. They are not source texts, they do not replace the Pinakes texts, the readiness tracker does not read them, and they do not move the certified count (`acceptable_as_source_text: false`, `needs_page_check: true`, `counts_toward_certification: false`).

## Next

A person checks the ten orders in `SAMPLE_FOR_PAGE_CHECK.csv` against their PDFs (blank columns for page kind and words wrong per reading), then works down `COMPARE.csv` from the least-confirmed order.

## Where the readings agree

310 orders have two or more readings. Of 111052 words in the backbone reading (Qwen3-VL-8B), 88029 (0.793) were also read by the cross-check model (Chandra OCR 2) and 23023 were not; 13103 words appear only in the cross-check (possible omissions by the backbone). The backbone marked 139 words [illegible]. Share confirmed per order, quartiles: 0.805 / 0.93 / 0.981; 191 orders are 90% or more confirmed, 23 under half. Median word-sequence similarity: vlm vs qwen3 vs vlm vs chandra 0.9015, vlm vs qwen3 vs tess300 0.728, vlm vs chandra vs tess300 0.6765000000000001.

`texts/EO_<n>.compare.txt` marks every word the cross-check did not also read ⟦like this⟧; `COMPARE.csv` lists the orders least confirmed first, as the queue for a person's page check. Agreement is not proof: two models can share a guess, and every reading stays a machine hypothesis.
