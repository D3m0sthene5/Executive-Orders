# Photius Lane 3 page-check brief (Opus): free official printings on the Internet Archive

Each item is a page of a government publication (Department of Justice, State Department, Panama Canal Press, Fuel
Administration, the Official U.S. Bulletin, Kappler's Indian Affairs, Public Health Reports, GPO slips) that a machine
flagged as possibly printing an executive order in full. You check whether the page carries the expected order as an
official printing under R37: the order's text with its dateline or number and its signature block. You decide nothing
legal.

## Inputs

- Your packet: `ORDERS.jsonl` in the packet folder named in your instructions. One object per item: `source`,
  `source_title`, `page_index` (0-based leaf), `instrument_id`, `expected_date`, `expected_title`, `numbers_on_page`,
  `dates_on_page`, `by` (`number` = the order's number is printed; `date` = matched only by date), `page_text` (the
  Internet Archive OCR of the page), `next_page_text`, `prev_page_tail`, `page_image_url`.
- The OCR text is the text layer; R37 lets a page check rest on it. Do not fetch the image or anything else from the
  network; do not open other files or run scripts.

## What to record

One JSON line per item in `RESULT.jsonl` in the packet folder:

- `instrument_id`, `source`, `page_index`
- `found`: `full_text` (order text with signature block), `full_text_no_signature`, `abstract_only`, `citation_only`
  (the page merely refers to the order), `not_on_page`, `unsure`
- `date_on_page`: the order's dateline as printed, ISO `YYYY-MM-DD` ("" if none)
- `number_on_page`: the order number as printed ("" if none)
- `signature_on_page`: the signature block as printed ("" if none)
- `first_words`, `last_words`: eight words each, of the order's text (not the publication's commentary)
- `subject_matches_title`: `yes`, `no`, `unclear`
- `result`: `pass` (full text, dateline or number, signature block, subject consistent with `expected_title` or, when
  the title is an abstract, not contradicting it), `fail`, `unsure`
- `note`: one sentence

## Rules

- A page that matches only by date may carry a different order of the same date: pass only when the subject fits the
  expected title. Several orders share dates in 1917-1918; `unsure` is fine.
- Many pages are tables of contents, indexes or rulings that quote an order: `citation_only`, `fail`.
- A compilation that prints the order with a dateline and "WOODROW WILSON" (or another president) but no "The White
  House" line still has a signature block.
- Do not pass on the machine's flags alone; read the text.

## When done

Reply with the packet name, counts of pass/fail/unsure, each pass id with source and page in ten words, and each
unsure id with a ten-word reason. Under 40 lines.
