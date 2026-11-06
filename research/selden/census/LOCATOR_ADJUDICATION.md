# Selden locator: measured error rates (2026-11-06)

The locator (`jobs/selden-common/selden_common.py`) finds the sentence of a later instrument that prints a target
order's number and reads the relation word near it, reusing `jobs/shepard-citations/cites.py`. It was measured on
held official texts already in the project (`jobs/fr-originals`, OCR of the printed Federal Register), offline,
with `research/selden/tools/locator_eval.py`, and its false locations were adjudicated by hand by the coordinator.

## Recall against an independent key

Key: 5,574 pairs in which the Office of the Federal Register's editorial notes (`jobs/later-events`, evidence types
`ofr_note_on_target` and `ofr_note_on_acting`) say a later order revoked, superseded or amended a census order, and
the later order's own official text is held. The locator must find a sentence citing the target in the later order's
own text (neighbouring documents on the same pages cut away with `own_span`).

| Locator version | Located | Recall | Relation class agrees with OFR | False locations among near-miss and wrong-pair negatives |
|---|---:|---:|---:|---:|
| 1 (cites.py number forms only) | 976 of 1,500 sampled pairs | 65% | not measured | 0 of 5,953 |
| 2 (adds OCR-split leads, printed lists, OFR revocation tables, own-span cutting) | 4,310 of 5,574 | 77% | 2,949 of 4,310 (68%) | 0 of 21,940 |

A miss is mostly an OCR-damaged number, a citation by date or title, or a table the OCR breaks apart. The negatives
are numbers the text does not print anywhere (the target less its last digit, with a digit appended, plus one, and
another pair's target), so they test number reading, not reading a printed number in the wrong role. That second
error is measured by hand below.

## Hand adjudication of located citations

Samples drawn at random (fixed seeds) from fr-originals texts and census numbers printed in them; each line was
read and judged by the coordinator. Files: `/home/claude/selden-scratch/fallback_sample*.txt`,
`acting_sample*.txt` (scratch, not committed; the seeds reproduce them).

| Sample | What was judged | Correct | Errors found and fixed |
|---|---|---:|---|
| 40 list/table citations, first version of the fallback | does the line cite that order | about 3 of 40 | years and page numbers read as order numbers: the fallback was replaced by a list grammar that admits only numbers, "No."/"Nos.", separators, dates and short parentheticals |
| 40 list/table citations, list grammar | same | 33 of 40 | OCR-split numbers ("1 2552"), suffixed orders read as plain ("6980-C" for 6980), page-number columns in a codification guide: fixed (split numbers skipped, suffix required to match, bare-number columns only under an OFR "No. Subject" table) |
| 40 list/table citations, after those fixes | same | 38 of 40 | a year after a date ("2011 Amendments"): fixed; a neighbouring order's closing tag ("[EXECUTIVE ORDER 9346]"): now flagged `heading_or_closing_tag` and never treated as acting |
| 30 sentences classed as acting on the order (version 2 with own-span cutting) | does the sentence print an act on that order | 28 of 30 | both errors came from texts whose own heading was not found, so a neighbouring document's act was read: `selden-fr-acting` now writes such sentences as `cross_reference` with flag `instrument_heading_not_found_neighbouring_text_possible` |

Measured error of the acting classification after the fixes: 2 of 30 (7%; 95% upper bound about 21%) on OCR page
texts, both of a class now downgraded. Full-text Federal Register documents of 1994 on (`selden-fr-citers`) are
single documents, so the neighbouring-text error does not arise there.

A located sentence is a lead to what the instrument says. Whether it ended or changed the order, in whole, and when,
is the claim's legal reading and is checked by blind review.
