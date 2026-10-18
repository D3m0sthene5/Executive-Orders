# claim-kit data contract (v1, 2026-10-18)

These are the formats of the excavator outputs that dossiers and the assembler read. Real example records are in
`claim_kit_contract/fixtures/*.example.jsonl`, built from held texts; every quote in them is an exact slice.

## Common rules

- One JSON object per line.
- Ids look like `EO:1234` or `EO:1234A`, upper case, with no `½`/`-1` rewriting beyond the census form.
- **Every quoted `text` must equal `open(text_path).read()[char_start:char_end]`** of the file named in the record's
  source. That is how the assembler proves quotes without re-reading PDFs.
- A `source` object is `{url, sha256 (of the downloaded original), page_or_item, text_path (repo path), text_sha256}`,
  copied from the producing job (`fr-originals`, `ofr-compilations`, `isthmian-canal-1911`,
  `indian-reservations-1912`; Richardson is a lead only, never an original).
- Every record carries `confidence` (`high`/`medium`/`low`) and `notes`. Every output is a lead. Nothing here is a legal conclusion.

## CLAUSES.jsonl

One line per order.
- Top level: `{instrument_id, source, clauses: [...], method, confidence, notes}`.
- Each clause: `{scope_id (unique, "EO:n#..."), kind (whole | section | subsection | item | amendment_instruction | schedule), label, text, char_start, char_end, pdf_page}`.
- Recitals ("Whereas", "By virtue of the authority…" lead-ins) and signature or filing blocks are excluded, unless the order is a single sentence, which becomes `#whole`.

## ACTING_PROVISIONS.jsonl

One line per (target, acting order) pair:
- `target_id`, `actor_id`, `actor_source`, `provision_label`, `provision_text`, `char_start`, `char_end`;
- `verb`: revoke | supersede | amend | transfer | abolish | terminate | other;
- `scope`: whole | partial | whole_via_parent | generic;
- `names_target` (bool), `reaches_target_via`;
- `signing_date`, `filing_date`;
- `effective_wording`: a list of `{text, char_start, char_end}`;
- `effective_class`: on_signing | stated_date | relative | agency_variable | unknown;
- `effective_date`: exact, only when the wording determines it; otherwise null;
- `exceptions_text`, `savings_phrases` (exact texts), `confidence`, `notes`.

## OWN_TERMS.jsonl

One line per finding:
- `instrument_id`, `scope_id`;
- `kind`: fixed_term | sunset_date | until_event | temporary_body | report_deadline | condition | emergency_duration;
- `text`, `char_start`, `char_end`;
- `start_date`, `stated_end_date`, `computed_end_candidate` (only when a term and a start are both stated);
- `source`, `note`.

A `report_deadline` never yields an end candidate.

## CHAINS.jsonl

One line per target:
- top level: `{target_id, events: [...], generic_refs_excluded, notes}`;
- each event: `{actor_id, signing_date, verb, how_named (direct | parent_as_amended), sections_touched, provision_text, char_start, char_end, source}`, in signing-date order.

## Dossier and decision sheet

These are internal to claim-kit, but must allow:
- every source pointer in a decision sheet to be a record id from the files above (`CLAUSES:EO:n#scope`, `ACT:EO:target>EO:actor`, `TERM:...`, `CHAIN:...#k`), so the assembler can copy sources and quotes mechanically;
- each dossier to list what it could not find.
