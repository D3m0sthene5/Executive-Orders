# Rubric: is this ProQuest land order already in the census?

Each input line is one JSON object:

- `acc`: ProQuest's CIS accession number; `date`: ProQuest's date; `title`: ProQuest's title.
- `text`: the document's own words from optical character recognition (OCR). OCR has errors; long documents are cut at "[...]".
- `census_entries_same_date`: every entry in the project's census that carries the same date, as "source:id | subject". The
  same order can appear several times under different sources (reconciled, lord, graunt, findings, numbered).

Decide whether the order in this ProQuest document is one of the census entries listed, or a different order.

## Fields to return

- `same_as`: the "source:id" of the census entry that is the same order, or "" if none of them is.
  An entry is the same order when it describes the same lands or the same action: the same reserve, withdrawal or
  restoration number, the same named place, island, reservoir, river or township, or the same reservation. A number in
  the census subject that differs from the number in the document (for example Coal Land Restoration Wyoming No. 29 vs
  No. 27) means a different order. Sharing only a state, a date or a generic word like "withdrawal" does not make it the
  same.
- `verdict`: one of
  - `same`: one listed census entry is this order;
  - `different`: the document contains an order and none of the listed entries is that order;
  - `no_order`: the document shows only correspondence, a recommendation or a draft, and no order text;
  - `unclear`: the text is too garbled, or the entries too vague, to decide.
- `order_id`: the order's own number or name as the document gives it (for example "Public Water Reserve No. 69,
  California No. 2"), or "".
- `evidence`: up to 15 words copied from the text that identify the order.
- `note`: up to 20 words explaining the choice.

Return exactly one JSON line per input, in the input's order, with keys `acc`, `verdict`, `same_as`, `order_id`,
`evidence`, `note`. Do not skip any input and add no commentary.
