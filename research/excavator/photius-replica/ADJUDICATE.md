# Photius Lane 4 adjudication brief (Opus): ProQuest replica scans

A Sonnet reader checked each ProQuest "Replica of Original" scan against the order the project expects. You adjudicate:
every reader `fail` and `unsure`, plus a random 5% of its passes as a control. Read the page images yourself; the
reader's result is one input, not the answer. You decide nothing legal.

## Inputs

- Your packet: `ORDERS.jsonl` in the packet folder named in your instructions. One object per order with the fields
  the reader had (`instrument_id`, `expected_number`, `expected_date`, `expected_title`, `text_kind`, `pages`, `head`,
  `tail`, `marker_lines`, `machine_read`), plus `renders` (PNG paths: first, second and last page at 130 dpi),
  `reader_result` (the Sonnet reader's JSON line) and `why_adjudicated` (`reader_fail`, `reader_unsure` or
  `random_5pct_sample`).
- Read the PNGs with the Read tool. Do not open other files, run scripts or use the network.

## Rules (the same as the reader's)

- `pass`: the document is the expected order: (a) the expected number is visible (stamp, heading or closing tag) and
  nothing contradicts the expected date beyond a few days; or (b) no number is visible (common before 1907 and on
  Alien Property Custodian orders) but the date on the document is within a day of the expected date, a signature
  block is present, and the subject matches the title.
- A dateline that differs from the index by a few days while the number and subject match is a `pass`: the index date
  may be wrong; say so in `reason` and give the date on the page.
- `fail`: a different order (another number clearly shown and the expected one nowhere), a cover slate or transmittal
  with no order text, or a subject that clearly does not match.
- `unsure`: unreadable, or a conflict the pages cannot settle.
- On a `random_5pct_sample` item say whether you agree with the reader and why in one clause.

## Output

One JSON line per order in `RESULT.jsonl` in the packet folder: `instrument_id`, `verdict` (`pass`/`fail`/`unsure`),
`number_seen`, `date_seen` (ISO or ""), `signatory_seen`, `agrees_with_reader` (`yes`/`no`), `reason` (one sentence).

## When done

Reply with the packet name, counts, and each fail/unsure id with a ten-word reason. Under 30 lines.
