# Whole-lifecycle claim and independent review inputs

The excavator accepts one JSON object per line in two separate files. A claim is a research assertion; a review is a second person's documented source check. The tracker counts an identity only if the claim passes [`claim_gate.py`](code/claim_gate.py), matches the reconciled status (a claim that disagrees is a *contest*, below), and a separate `independent_human` review with decision `uphold` matches the claim SHA-256. A changed claim invalidates an older review. This is a **structural and provenance gate**, not proof that the submitted legal judgment is correct.

Required claim fields (`schema: eo-lifecycle-claim/v1`):

- `instrument_id`, `whole_order_status` (`yes` or `no`), and `original_representation` with exact page/item and provenance: HTTPS URL plus SHA-256 or archival identifier, or an archival identifier plus SHA-256 of a local scan.
- `operative_clauses`: an asserted *complete* original clause inventory. Each clause has unique `scope_id`, original operative text/source, `state_at_cutoff`, and `later_events` (possibly empty). A terminated or never-activated clause needs `first_end` with exact date, actor, mechanism and source. An operative clause needs `current_predicate` with legal basis, source and `checked_through` date.
- For `no`, `whole_order_end` with exact date, actor, mechanism and source. Its date must equal the latest first-end date among the complete clause inventory. For `yes`, `whole_order_end` must be null and at least one clause must have a continuing predicate checked through the October 14, 2026 legal cutoff. Every later event requires an effective date, actor, mechanism and source.
- `savings_residuals` with state, reason and source; `later_source_search` with at least one repository, bounded query/scope and checked-on date; `unresolved_material_gaps: []`; and a substantive `research_rationale`.

The independent review object (`schema: eo-lifecycle-review/v1`) needs `instrument_id`, `claim_sha256`, `reviewer`, `reviewer_role: independent_human`, `decision: uphold`, a substantive `rationale`, `checked_source_urls` (HTTPS), optional `checked_archival_items` (archival IDs for offline scans), and `reviewed_on`. At least one checked source is required, and every source cited in the claim must appear in one of those checked lists. The reviewer must actually read the cited pages, test earlier effective cessations and savings, and resolve disputes; filling fields alone does not establish correctness. Source authenticity and claim completeness can still fail despite passing code.

Generate the claim fingerprint with `claim_gate.claim_sha(claim)` using the exact parsed claim object. The reviewer should sign off only on that frozen object. If research changes any field, obtain a new review. The HTML workbench exports `eo-lifecycle-worksheet/v1`, a separate draft format that [`validate_worksheet.py`](code/validate_worksheet.py) can check against its packet fingerprint. A worksheet never increments the tracker. The existing Stage 17 review importer remains the production path for legal claim certification; Stage 19 does not fabricate or import human decisions.


## Contests (owner ruling R5, 2026-11-06)

A claim may assert a `whole_order_status` that disagrees with the provisional ledger. `claim_gate.status_contested(claim, ledger_status)` reports it; it is not a gate error. The tracker records blocker `STATUS_CONTESTED`, keeps the order not ready, and lists the claim in `jobs/readiness-tracker/output/CONTESTED.csv` (instrument, ledger status, claimed status, claim sha256). The ledger is unchanged until an owner-merged pull request resolves the contest.

## Schema v2: `eo-lifecycle-claim/v2` (owner ruling R2, 2026-11-06)

v2 adopts the legal first-ending interval contract (`research/progress/sol-evidence-economy/LEGAL_INTERVAL_CONTRACT_PROPOSAL.md`) alongside immutable v1. **Every v1 claim stays valid and is checked exactly as before.** A new claim may use v2. A v2 claim has every v1 field, and its `first_end` objects and `whole_order_end` replace the free `date`/`mechanism` with:

- `date_kind`: `exact` (`date`), `interval` (`earliest` < `latest`, both exact, no `date`; a one-day interval must be written as `exact`), or `not_later_than` (`date` is the latest possible end). These are the codebook's `historical_evidence_dates` values a first end can take.
- `first_cause`: the codebook's `first_cause_type`, verbatim: `under_original_terms`, `later_amendment_imposed_condition`, `later_presidential`, `legislative`, `regulatory`, `judicial`, `completion_of_task`, `never_activated`, `unresolved`. The owner's shorthand maps as own_terms → `under_original_terms`, performance → `completion_of_task`, statute → `legislative`, judicial → `judicial`, executive_revocation and supersession → `later_presidential` (the mechanism says which), unresolved → `unresolved`.
- **`not_later_than` is accepted only with `first_cause: unresolved`, and `unresolved` only with `not_later_than`.** A latest possible end without affirmative evidence of the ending event is a bound, not a first end (the contract's rule, and D-20261028-evidence-decides).
- `mechanism`: one of `express_revocation`, `express_supersession`, `implied_supersession`, `amendment`, `expiration_by_own_terms`, `condition_or_event_occurred`, `task_completed`, `body_abolished`, `statutory_termination`, `authority_repealed_or_lapsed`, `judicial_invalidation`, `regulatory_action`, `never_activated`, `other`; free text goes in `mechanism_note` (required for `other`).
- `actor` and `source` as in v1.

Order level:

- `whole_order_end` is the **latest clause first end**, not the first moment the order lost all force: `exact` when every clause end is exact (its date = the latest), `interval` `[max(clause earliest), max(clause latest)]` when any clause end is an interval, and `not_later_than` (date = the latest bound) when any clause end is bounded.
- `formal_disposition` `{instrument, date, source?}` (optional): the instrument that formally disposed of the order (for example a later cleanup revocation), kept separate from `whole_order_end`. A claim with any `not_later_than` end must have one dated no earlier than each bound.
- Derived, never hand-filled (the gate rejects the field if a producer writes it): `formal_revocation_after_earlier_cessation` = the formal disposition is dated after an established whole-order end (`claim_gate.derived(claim)`; null when the end is only bounded or there is no disposition).

The tracker counts a v2 `exact` or `interval` claim like a v1 claim. A v2 claim with any `not_later_than` end records what the evidence shows but leaves the ending step open with blocker `FIRST_END_UNRESOLVED`; the order is not ready. `READINESS_BY_ORDER.csv` gains `claim_schema`, `status_contested`, `whole_end_date_kind` and `formal_revocation_after_earlier_cessation`. Estimand and reporting: `research/justinian/ESTIMAND.md`.
