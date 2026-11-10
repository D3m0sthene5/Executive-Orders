# Pacioli: double-entry reconciliation of later events across independent official tables

Named for Luca Pacioli, whose *Summa* (1494) set out double-entry bookkeeping: every amount entered in two books, so
a disagreement shows an error. Zero model tokens, offline: every input is a committed job output. Owner-approved
Tier A idea #6 (2026-11-10), built in the Linnaeus session.

**Compilers (families).** A pair is agreed only when two *different* compilers record it:

| Family | Compiler | Tables read (job output) |
|---|---|---|
| OFR | Office of the Federal Register | online disposition notes (`later-events` EDGES, `ofr_note_*`; NARA's HTML tables print the same notes), the 1989 Codification table (`ofr-codification-1989` FRAGMENTS), eCFR notes (`current-law`) |
| OLRC | Office of the Law Revision Counsel | U.S. Code note status lines (`current-law` EVENT_CANDIDATES, `system=usc`) |
| BLM | Bureau of Land Management | Tables of Public Land Orders (`shepard-citations` EDGES, `shepard_blm_plo_table`) |

Two OFR tables agreeing is one entry, not two (`jobs/claim-drafts/drafts.py` `JOB_SOURCE_FAMILY`). The Lord 1944 WPA
list is not read: it carries no later dispositions (`research/linnaeus/SOURCE_MEASURES.json`). An order's or
actor's own text is not a table and is never counted as an entry. OLRC compiles its notes from the instruments
themselves, but it may have read OFR's tables; treat OFR+OLRC agreement as two finding aids agreeing, not as proof.

**Matching.** Both the order (`target_id`) and the acting instrument (`acting_id`: `EO:N`, `PLO:N`, `PROC:N`) are
census or numbered ids taken from each table's own number; unnumbered or unresolved instruments are skipped. Relation
class: `ending` (revocation, supersession, termination, abolition, rescission, vacation, nullification, replacement,
restoration) or `modifying` (amendment, modification, extension, correction, suspension, continuation).

- **AGREED**: two or more families record the pair with a common relation class, a common whole-or-part scope, and,
  when at least two families give a date, a common date.
- **DISAGREED**: two or more families record the pair but the class, the scope or the dates differ
  (`relation_class_differs`, `whole_vs_part_differs`, `date_differs`). For an agent to read.
- A pair one family records is in neither list. **A table's silence is never evidence.**

**What a record is not.** Agreement is discovery evidence that lets a producer skip the finding step. It is not a
claim, status, original text or certification. A claim still quotes the acting instrument's own held text
(`actor_text`), never a table entry. Human-certified: 0.

## Record format (`AGREED.jsonl`, for Nalimov)

One JSON object per line, keys sorted:

```
{
  "schema": "pacioli-reconciliation/v1",
  "target_id": "EO:10014",              # the order, by explicit number
  "acting_id": "EO:11258",              # the acting instrument, by explicit number
  "families": ["OFR", "OLRC"],          # at least two
  "relation_class": "ending",           # ending | modifying
  "scope": "whole",                     # whole | part (every family agrees)
  "agreed_date": "1965-11-17",          # common date candidate, "" if fewer than two families date it
  "target_provisional_status": "",      # tracker value at run time ("" = undecided)
  "target_ready_for_human_review": "no",
  "actor_text": {                       # null when the project holds no text of the acting instrument
    "path": "jobs/fr-originals/output/texts/EO_11258.txt",
    "sha256": "<sha256 of the committed bytes>",
    "grade": "original_supported"       # PLO actors: the selden-fr-acting page extract, plus text_path
  },
  "entries": [                          # every table entry behind the agreement
    {"family": "OFR", "compiler": "...", "job": "later-events", "record_id": "LE-...",
     "relation": "supersession", "relation_class": "ending", "scope": "whole", "date_candidate": "...",
     "locator": "OFR API record executive_order_number=10014; ...", "source_sha256": "...",
     "source_url": "...", "quote": "Superseded by: EO 11258, November 7, 1965"}
  ],
  "notice": "..."
}
```

`DISAGREED.jsonl` has the same identity fields and `entries`, plus `disagreement` (list of reasons) and `by_family`
(each family's classes, scopes and dates). `SUMMARY.json` gives the counts for undecided and decided-not-ready orders.

Tests: `python -I jobs/pacioli-double-entry/test_pacioli.py`.
