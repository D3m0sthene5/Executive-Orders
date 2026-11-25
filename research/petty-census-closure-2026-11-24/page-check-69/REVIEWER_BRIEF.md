# Montfaucon batch m011: blind reviewer brief

You are one of two independent readers. You do not know the other reader's answers, any earlier result for these orders, or any answer key. Do not look for them. Work only from the files named in your assignment.

## Order of work

1. Do the three control cases in `controls_reader_<a|b>.jsonl` first, alone, before any real order. For each, open the image, find the printed sentence that matches the excerpt, and compare the excerpt to the printed words one sentence at a time, including every number, date, section label and order number. A page can contain several orders; confirm that the order heading and the closing you are reading belong to the claimed order. Answer `pass` or `fail`, with the exact printed words that decided it. Do not write anything about the real orders until all three controls are answered.
2. Then review the real orders in your assignment, a small block at a time.

## What you are given for each real order

A claimed order number, the source PDF URL, the cited PDF page range, the held OCR text file, and rendered page images (the cited pages plus one neighbor before and after). The cited printing is a Federal Register daily issue (or the 1911 Isthmian Canal Commission compilation for EO:273 and EO:274).

## What to decide

Open every cited page image and read it. Then answer these as separate findings, each true or false:

- `identity_confirmed`: the printed heading, number and date on the image name the claimed order. For the 1911 compilation, which prints no order numbers, confirm date and subject against the held text and say so in `evidence`.
- `complete_start_and_closing`: the cited pages contain the order from its opening heading through its signature, dateline and closing (filing line or closing tag). Pages that stop mid-section, or an order that continues onto a page outside the cited range, make this false.
- `cited_pages_confirmed`: every cited page is needed and none belongs to a different document; no intervening page is missing.
- `image_source_and_page_confirmed`: each image shows the page its label and URL claim (check the running head or printed page number against `page_or_item`).
- `wording_compared`: you compared the held OCR text with the image, sentence by sentence.

## Verdict rules

- `pass` only when all five findings are true and `substantive_differences` is an empty list. Mechanical OCR noise (split letters, stray punctuation, a dropped hyphen, a wrong glyph in a word where the meaning is unchanged) is not a substantive difference; list it in `ocr_corrections`. A changed digit in a number, date, section label, rate, amount or order number is substantive and blocks a pass, even if it looks like OCR noise; read the image to decide which is right.
- `fail` when the cited pages show another document, omit the opening or closing, stop before the end of the order, include a different order that the held text treats as part of this one, or when the held text differs from the print in substance. Name the exact printed page where the order actually is, if you saw it.
- `unsure` when the order is identified and its span is right, but long tables, numeric annexes or dense amendments cannot be fully certified from the images. Say which part.
- `blocked` when a needed image is missing or unreadable. Do not guess from the OCR alone.

Look at the images, not only the OCR. Do not infer anything from a URL string or a page label. If you cannot see a thing, record `not visible` for that field and treat the finding as false.

## Fields to record per order (schema montfaucon-page-check/v1, one object per order)

`instrument_id`, `context_id` (your own distinct context name), `reviewer`, `verdict`, `number_seen`, `date_seen`, `signature_seen`, `first_words` (first printed words of the order), `last_words` (last printed words, including the closing tag or filing line), `evidence` (what you saw, with printed page numbers), `review_scope` (which images you read), `identity_confirmed`, `complete_start_and_closing`, `cited_pages_confirmed`, `image_source_and_page_confirmed`, `wording_compared`, `substantive_differences` (list of strings; empty only for a pass), `ocr_corrections` (list), `target_sha256` (copy from the assignment row).

Write one JSON object per line to your reviews file. State disagreements with the held text plainly; do not soften a failure to be agreeable.
