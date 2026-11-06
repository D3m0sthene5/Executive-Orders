# Photius Lane 4 worker brief: page check of ProQuest "Replica of Original" scans

You are checking whether each scanned document is the executive order the project says it is. You read; you do not
decide legal questions. Nothing you write changes a status or count.

## Inputs

- Your packet: `ORDERS.jsonl` in the packet folder named in your instructions. One JSON object per order with:
  `instrument_id`, `expected_number` (the number the State Department later assigned; orders before about 1907 often
  carry no number on the document itself, and many 1907–1925 file copies carry it only as a stamp or a bracketed
  closing tag such as `[No. 3900.]`), `expected_date`, `expected_title` (from an index; may be an abstract),
  `text_kind` (pinakes_layer = the PDF's own text; pinakes_ocr = Tesseract; pinakes_htr_backbone = a vision-model read
  of handwriting, which can invent words), `text_usable`, `pages`, `machine_read` (a regex pre-read: numbers, dates and
  signature words it saw, first and last words, and `auto_verdict`), `head` (first 1,500 characters), `tail` (last
  1,200 characters) and `marker_lines` (every line with a number, date or signature word).
- Page images, when you need them: `<RENDERS>/EO_<number><suffix>_first.png`, `_second.png` (when 3+ pages) and
  `_last.png` at 130 dpi. Use the Read tool on the PNG. Use images when `text_usable` is "no", when the text is
  garbled, or when the text does not settle number and date. If an image file is missing, say so in `reason`.
- Do not open any other file, do not run scripts, do not fetch anything from the network.

## What to record for each order

Write one JSON line per order to `RESULT.jsonl` in the packet folder, fields:

- `instrument_id`
- `number_seen`: the order number as it appears on the document ("" if none is visible; "stamp 3900" or "tag [No. 3900.]" is fine)
- `date_seen`: the dateline or signing date on the document, ISO `YYYY-MM-DD` ("" if none)
- `signatory_seen`: the signature block as read (president's name, and "The White House"/"Executive Mansion" when present; "" if none)
- `first_words`: the first eight words of the order's own text (after any file stamps, cover sheets or ProQuest furniture)
- `last_words`: the last eight words before the signature block
- `evidence`: `text`, `image`, or `text+image`
- `verdict`: `pass`, `fail` or `unsure`
- `reason`: one sentence

## Verdict rules

- `pass`: the document is the expected order. Either (a) the expected number is visible on the document (stamp, heading
  or closing tag) and nothing contradicts the expected date (same date, or same month and year with the day unreadable),
  or (b) no number is visible but the date on the document matches the expected date within one day, a signature block
  is present, and the subject matches the expected title.
- `fail`: a different number is clearly shown, or the date on the document is clearly a different year, or the subject
  clearly does not match the title, or the file is plainly another document (a cover sheet only, an unrelated letter).
- `unsure`: anything else, including unreadable scans, a missing image you needed, or a number/date conflict you cannot
  resolve. An OCR digit error ("39 00", "3900.1") is not a conflict when the rest agrees; say what you saw.

Do not guess; `unsure` is a fine answer. Do not pass an order because the machine pre-read said "strong"; read it.

## When done

Reply with: the packet name, counts of pass/fail/unsure, and the ids of every fail and unsure with their reason in
ten words each. Keep the reply under 40 lines.
