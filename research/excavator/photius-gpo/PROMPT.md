# Photius Lane 1 page-check brief (Opus): GPO bound slip-order volumes

The project located executive orders in the Government Printing Office's bound volumes of numbered slip orders
(HathiTrust record 000070271) by their closing tags "[No. NNNN.]". A machine aligned each located span to an order
number and tested its dateline against the identity layer. You check the alignment by reading the page images. You
decide nothing legal; you say what is on the page.

## Inputs

- Your packet: `ORDERS.jsonl` in the packet folder named in your instructions. One object per order:
  `instrument_id`, `expected_number`, `identity_date` (from the project's index; may be empty or a year only),
  `expected_title`, `htid`, `pdf_pages` (1-based pages of the span), `renders` (PNG paths of the first pages of the
  span, at most five), `machine_dateline`, `date_test`, `alignment_verdict` (pass/check/fail), `alignment_reasons`,
  `why_queued` (alignment_failed or random_5pct_sample), `gap_before` (order numbers the machine found no tag for just
  before this one; the span may contain them), `text_head`, `text_tail` (OCR of the span).
- Read the PNGs with the Read tool. Do not open other files, run scripts or use the network.

## What to record

One JSON line per order in `RESULT.jsonl` in the packet folder:

- `instrument_id`
- `number_on_page`: the closing tag or heading number as printed (e.g. "[No. 4316.]"), "" if not visible in the renders
- `dateline_on_page`: the printed signing date, ISO `YYYY-MM-DD`, "" if not visible
- `signatory_on_page`: the printed signature block (name and "The White House" when present), "" if not visible
- `first_words`: the first eight words of the order's text (after the "EXECUTIVE ORDER" heading and any title)
- `result`: `pass`, `fail` or `unsure`
- `note`: one sentence
- `other_orders_in_span`: a list, possibly empty, of objects `{"number": "4315", "pdf_page": 48, "dateline": "1925-09-29"}`
  for every other order whose heading or closing tag you see inside the rendered pages (this is how the project
  recovers numbers whose tag the OCR missed; `gap_before` tells you which numbers to look for)

## Rules

- `pass`: the rendered pages show this order's own closing tag or heading number, and the dateline (when visible) is
  consistent with `identity_date` (same date; or the same year when the index has only a year; or the index is empty).
  A dateline that differs from the index by a day or a few days while the number matches is still a pass: say so in
  `note` (the index may be wrong; the printed date is evidence).
- `fail`: the pages show a different order (tag number differs and the expected number is nowhere in the span), or the
  span is not an executive order at all.
- `unsure`: the renders do not show the tag page (the span was longer than five pages), the print is unreadable, or you
  cannot settle it.
- Read every order's pages. Do not pass on the machine's verdict alone.

## When done

Reply with the packet name, counts of pass/fail/unsure, each fail or unsure id with a ten-word reason, and any
`other_orders_in_span` numbers found. Under 40 lines.
