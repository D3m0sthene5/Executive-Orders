# What `respondendi.py plan` reads (interface I5 of the Whitworth line)

A batch is adoptable under the standing rule only if its completion carries every file below. `respondendi.py check
--completion <dir>/complete-vN --admission <packet>/ADMISSION.json` reports, per order, which condition failed. This
page is the contract for the Maudslay conveyor (`jobs/maudslay-conveyor`) and for any session that drafts claims for
undecided orders (Nalimov).

## Files of one completion

| File | What Respondendi requires |
|---|---|
| `complete-vN/INPUTS.json` | `preserved_receipts` pins exactly one `COMPLETION.json`, either beside `complete-vN` (claim-kit and Papinian layout) or in the packet's `completion/` folder (Maudslay layout), and the pin equals the file's bytes |
| `COMPLETION.json` | `members[]`: `outcome` `submit`, the exact `claim_sha256`, `publication_kind` (`whole_case`, or `partial_research` for a status-only adoption), and an **`overlay_bundle`** with pins for `evidence` (`EVIDENCE.json`), `decision` (`STATUS_DECISION.json`), `review` (`STATUS_REVIEW.json`) and `proposal` (`PROMOTION_PROPOSAL.json`). `controls[]` with `planted_claim_sha256` and an `adjudication` pin. `receipts[]` pinning `BLIND_REVIEW_{A,B}.jsonl` and `AFTER_REVEAL_{A,B}.jsonl`. `producer_model_family` |
| `complete-vN/PUBLICATION.json` | `mode` `replacement_proposal`, `written` true, `independent_human_certifications` 0, and the proposal path with its hash. Undecided orders are never published as `own_claims` |
| `complete-vN/TALLY.json` | `finished_utc` no older than 14 days at planning; every control `caught`; per member `outcome` `eligible`, the same `claim_sha256`, `source_review_upheld` true, `publication_kind`, and `gate_errors` (empty for whole-case members) |
| `complete-vN/EXCEPTIONS.json` | empty |
| `complete-vN/TRACKER_CHECKER.json` | `by_instrument[iid]`: the same `claim_sha256`, `all_checks_passed`, `gate_passed`, `mechanical_result` `pass` (status-only: the listed `steps_checker_passed`) |
| `BLIND_REVIEW_{A,B}.jsonl` | One named reviewer per arm, different across arms, from the producer and from the status reviewer; per record `claim_sha256`, `instrument_id`, `model_family`, `independent` true, `separate_context` true, `scope` equal to the member's publication kind, `verdict` (`upheld` or `rejected`); every planted control `rejected` by every arm |
| `AFTER_REVEAL_{A,B}.jsonl` | `upheld_after_reveal` for each genuine control claim that is to be adopted |
| `CONTROL_ADJUDICATION_*.json` | **`control_kind`** from the rule's catalogue. A review set needs at least 2 controls (one per 15 claims), of 2 kinds, at least one status-determining (`partial_as_whole`, `transfer_as_end`, `later_event_removed`, `ending_source_swapped`, `wrong_order_text`, or an Ulpian kind). Kinds that require a control kind (`own_terms` and `yes_current`: `later_event_removed`; `ulpian_life_bound`: one Ulpian status kind) need it **planted on a claim of that lot kind** |
| `STATUS_REVIEW.json` | `decision` `accept`, `independence_confirmed` and `source_checks_confirmed` true, `decision_sha256` equal to the canonical hash of `STATUS_DECISION.json`; reviewer not the producer and not an arm |
| `PROMOTION_PROPOSAL.json` | `recommended_provisional_status` equal to the claim's status; `decision_sha256` and `review_sha256` equal to the claim's `claim_kit.status_overlay` |
| `<packet>/ADMISSION.json` | written by `kit.py prepare --action status_assignment.undecided` (or its probe); the order is listed |

Respondendi also re-runs the claim kit's `_sealed`, `_decision_errors` and `_review_errors` on the bundle, and
requires the claim-kit files to equal GitHub's main.

## Claims each lot kind accepts

The kind comes from the decision's `basis_evidence_ids`, never from the producer's wording.

| Kind | Basis record in the frozen evidence | Whole-order end in the claim |
|---|---|---|
| `express_named_revocation` | `ACT:` by the actor, whole scope, naming the order directly | `date_kind` exact, `actor` the revoking instrument, `date` its effective date, `source.quote` containing the ACT provision |
| `own_terms` | `TERM:` of kind `fixed_term` or `sunset_date`, whole-order `scope_id`, `stated_end_date` equal to the end | `actor` the order itself, `date` the stated end |
| `spent_on_issue` (route `own_text`) | `OWN_TEXT:` with `scope` `whole`, `whole_order_test.continuing_sentences` 0, `own_text_kind` `spent_on_issue` or `amends_parent` | `actor` the order itself, `mechanism` `spent_on_issue`, `date` the signing date; for `amends_parent` with a held `PARENT_END:`, `savings_residuals[].source.evidence_id` names it |
| `yes_current` (route `current`) | `CURRENT:`; decision `current_predicate_checked_through` 2026-10-14 | none |
| `ulpian_life_bound` | (membership in the owner-approved `research/ulpian/CLASS.csv`) | `date_kind` `not_later_than`, `first_cause` `unresolved`, `mechanism` `life_of_named_person`, `date` the class bound, `source.text_path` the class's text; the claim states `born_by` and that use is unknown |

A new claim kind that fits none of these needs an amendment of `RULE.md` (a new hash and owner decision).

**Strata are per producer.** The process fingerprint includes the completion manifest's `agent`, the model families,
the named prompt or code files, `UNDECIDED_CHECKLIST.md`, the kit's overlay, completion, assembly and batch code, and
the rule. A script producer such as Nalimov (`agent` `nalimov-script`) therefore starts its own probation stratum and
never shares audit statistics with model producers. Planners should still pass the drafter's code as `--prompt`
(for Nalimov: `jobs/nalimov-tablebase/drafter.py` and `predicate.py`), so that a change to it opens a new stratum.

**Nalimov's express drafts (PR #279)** map to `express_named_revocation`:
- `STATUS_DECISION.json` basis `[ACT:<order>><actor>]`, plus `ACTOR_TEXT:<actor>` when official;
- the whole-order end is the ACT actor at the actor's date, with the ACT provision as its quote;
- `material_gaps` is empty.

Clause-level `task_completed` ends for clauses that only revoke other orders are lifecycle detail; the status kind is
fixed by the ACT basis. Nalimov vendors `named_end_in`, `_segments` and `_later_acts` with a parity test. Any change
to them here, or to RULE.md's express parameters, must be mirrored there: Respondendi re-checks every claim with its
own copy regardless.

## Gaps in the Maudslay conveyor as merged (#269, main at a1cb3f9ea9)

1. **No status-overlay route.** Members carry decided-order `packet` claim references and no `overlay_bundle`, so an
   undecided batch cannot yet produce what `plan` reads. The conveyor needs the overlay steps the Papinian and
   Haloander waves ran by hand:
   - prepare undecided members;
   - the producer fills `STATUS_DECISION.json`;
   - an independent status reviewer;
   - `overlay-propose` to a bundle;
   - completion with overlay members and `replacement_proposal` publication.
2. **Untyped controls.** `plant` moves dates only and `CONTROL_ADJUDICATION_*.json` has no `control_kind`. It needs
   typed plants of the status-determining kinds above, recorded by kind, planted on claims of each lot kind.
3. **Publication mode.** Undecided batches must publish as `replacement_proposal`.

The audits happen after `plan`, outside the conveyor. A cross-family auditor (or the owner) writes one evidence file
per order under `research/respondendi/lots/<lot>/audit-evidence/`. An AI's file is a JSON run receipt with its
`model` id, the order and its `claim_sha256`. Then `respondendi.py audit-record` and, for disagreements,
`adjudicate`.
