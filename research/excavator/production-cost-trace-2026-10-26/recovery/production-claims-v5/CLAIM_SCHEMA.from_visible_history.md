# Reconstructed schema description from visible history

This describes the existing Stage19 `eo-lifecycle-claim/v1` format. It is not a recovered byte-exact copy of the repository schema file and makes no methodology change. Root should use the actual restored repository code/schema for validation.

Required claim fields: `schema`, `instrument_id`, `whole_order_status` (yes/no), `original_representation`, nonempty complete `operative_clauses`, `whole_order_end` for NO, `savings_residuals`, nonempty `later_source_search`, `unresolved_material_gaps: []`, and substantive `research_rationale`.

Every clause has a unique `scope_id`, exact `original_operative_text`, `original_source`, `state_at_cutoff`, `first_end` or `current_predicate` as appropriate, and `later_events` list. Terminated/never-activated clauses need exact `first_end.date`, `actor`, `mechanism`, and source. An operative clause needs legal basis, source and `checked_through: 2026-10-14`. Each later event needs `effective_date`, `actor`, `mechanism`, source. A NO whole end equals the latest clause first-end date.

A source uses HTTPS URL plus SHA256 and page/item (or supported archival provenance). These manual proposals additionally pin exact local raw/text paths, textSHA256, absolute Unicode `char_start`/`char_end`, and verbatim `quote`. Supplemental `earlier_candidate_ends`, before/after text, `effective_date_source`, and `producer_qualifications` preserve explicit research qualifications; they do not create fake dossier IDs or independent/human approval.

The historical `eo-lifecycle-review/v1` certification schema is reserved to independent humans; this producer did not write such reviews. Structural/source gates do not establish legal correctness or human certification.
