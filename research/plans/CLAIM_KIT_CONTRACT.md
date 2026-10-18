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


## Implementation extension: exact representations and decisions (claim-kit v1)

`CLAUSES.jsonl` contains the preferred attributed text per order; `TEXT_CLAUSES.jsonl`
retains the same schema for **every** discovered held representation. Sources and
Unicode code-point offsets address the raw UTF-8 decoded bytes, with no newline or
OCR normalization. `OWN_TERMS.jsonl` retains all representations with stable IDs
including the text hash. A deadline always has null end candidates.

`ACTING_PROVISIONS.jsonl` has one canonical row per target/actor pair. Additional
located spans/representations are preserved in `alternative_provisions` and in
`ACTING_REPRESENTATIONS.jsonl`; their stable IDs append a content hash. Direct and
parent-as-amended paths do not create duplicate canonical IDs. A missing named
provision goes in `MISSING_SOURCES.jsonl` with its pair and reason; no blank quote
can be cited. `CHAINS.jsonl` contains named canonical change leads only, while
generic references are counted separately. Signing fallback is explicitly an
assumption and has no exact effective date without wording.

Dossiers use `eo-claim-kit-dossier/v1`: `instrument_id`, provisional
`whole_order_status`, `original_source_id`, `clauses`, an ID-keyed `evidence` map,
`actor_provisions`, `actor_contexts`, `own_terms`, `chain`, `current_law_leads`,
`machine_searches` (full records with `search_id`, `entry` and coverage warnings),
`draft_gate_errors`, `conflicts`, `missing` and `fingerprint`. Each evidence value
has `source`, exact `text`, `char_start`, `char_end` and its applicable date/actor
metadata. Actor contexts over 50 KB have explicit shared overflow files which
must be read before judgment. Current-law serialized notes and absent original
text caches stay leads with an explicit evidence gap; they are not legal quotes.

`eo-claim-kit-decision/v1` sheets pin `dossier_sha256` and `agent`. They require
explicit `approved`, `original_confirmed`, `inventory_confirmed`; per clause,
`scope_id`, `clause_id`, `state`, `end_id`, `effective_date`,
`effective_date_confirmed`, `current_basis_id`, `current_legal_basis`,
`checked_through`, `later_events` (`id`, effective date and confirmation), and
`reason`; plus `savings` (`state`, `source_id`, `reason`), selected `search_ids`,
`conflict_resolutions`, `research_rationale`, `unresolved_material_gaps`.
IDs select evidence; sheets cannot supply free-form source citations or quotations.
Blank sheets select no legal state, date, savings or search. A changed dossier
invalidates its decisions. Assembly fails closed and reports every rejected sheet.
Only exact quoted sources are copied into Stage19 claims. Their `claim_kit`
metadata pins the producer and dossier; it is not reviewer or human approval.

`INDEX.json` enumerates current decided dossiers; the CLI rejects stale files absent
from the index. `STATUS_LEADS.jsonl` separately enumerates all undecided identities
without assigning a status. `FAMILIES.json` ranks remaining shared-evidence groups.
Reservations use an O_EXCL guard plus `research/readiness/CLAIM_KIT_LOCK.json`; this
serializes one shared checkout. Independent clones must exchange reservations by
committing/pulling before assigning work. No local lock claims cross-branch atomicity.
The runner cache is bounded, disposable and keyed by parser/source hashes.

If the proposed segmentation needs correction, the decision sheet may supply
`inventory_overrides`: each entry names a unique scope_id, the existing dossier's
original_source_id as source_id, absolute char_start/char_end within that source,
and a substantive reason. Corrected spans cannot overlap. They select exact slices
of the pinned original evidence; they cannot supply text or citations. The sheet's
clause decisions must match the corrected scopes and omit the old clause_id.
Assembly pins these span judgments in `claim_kit.inventory_overrides`; `check`
reconstructs and verifies every derived source against the original dossier.

Corpus JSONL files roll at 75 MB into `<STEM>.partNNNN.jsonl`; the first shard keeps
the required base filename. Read all shards listed in SUMMARY.json `jsonl_shards`.
No over-95-MB corpus output should disappear into the runner's temporary artifacts.
