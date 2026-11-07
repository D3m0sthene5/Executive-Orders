# Photius Lane 2 page-check brief (Opus): Civil Service Commission annual reports

The annual reports of the U.S. Civil Service Commission (House Documents in the Congressional Serial Set, scanned by
GovInfo) print the executive orders that amended the civil-service rules or excepted positions and persons. For each
item you check whether the cited report page carries the expected order in full, as an official printing (R37: the
page must show the order's dateline or number and its signature block). You decide nothing legal.

## Inputs

- Your packet: `ORDERS.jsonl` in the packet folder named in your instructions. One object per item:
  `kind` (`located` = found earlier from the WPA citation; `rescan` = a date-line match found tonight for an order
  with no printed citation), `instrument_id`, `expected_number`, `expected_date`, `expected_title` (an index title,
  may be an abstract), `wpa_citation`, `prior_confidence`, `report`, `pdf_page`, `page_text` (the GovInfo OCR of the
  page), `next_page_text`, `render` and `render_next` (PNG paths of the page and the next one).
- Read the PNGs with the Read tool when the OCR text does not settle the question, and always for `rescan` items and for
  `located` items with prior confidence medium or low. Do not open other files, run scripts or use the network.

## What to record

One JSON line per item in `RESULT.jsonl` in the packet folder:

- `instrument_id`
- `found`: `full_text` (the order's text with its signature block), `full_text_no_signature` (the order's operative text
  is printed in full, with a date heading, but the report omits the signature block, as the 1912-1929 reports do),
  `abstract_only`, `not_on_page`, or `unsure`
- `date_on_page`: the order's dateline as printed, ISO `YYYY-MM-DD` ("" if none)
- `signature_on_page`: the signature block as printed (e.g. "THEODORE ROOSEVELT. The White House, March 2, 1909") or ""
- `first_words`: the first eight words of the order's text on the page
- `last_words`: the last eight words before the signature block
- `result`: `pass` (full text, dateline or number, and signature block all present and consistent with the expected
  date), `fail` (the page carries another order or only an abstract or summary line), `unsure`
- `note`: one sentence; for `rescan` items say whether the subject matches `expected_title`

## Rules

- Many reports print the order under a heading such as "EXECUTIVE ORDER." or inline after a date line; both are fine.
- An abstract ("By Executive order of March 2, 1909, the following positions were excepted...") is `abstract_only`
  and `fail`: the project treats a summary as a lead, not a printing.
- Full text without a signature block is `full_text_no_signature` and `fail` under R37 (the ruling requires the
  signature block); it stays a dated, located lead. Record the date and first/last words anyway.
- A dateline that differs from `expected_date` by a day or two with the subject matching is still a pass; say so.
- Orders sharing a date on one page: pass only the one whose subject matches `expected_title`; otherwise `unsure`.
- Do not pass on the OCR text when the render shows otherwise.

## When done

Reply with the packet name, counts of pass/fail/unsure, each fail or unsure id with a ten-word reason. Under 40 lines.
