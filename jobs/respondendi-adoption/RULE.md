# Respondendi standing adoption rule, version 2 (DRAFT: not in force)

This text is what the owner approves or declines. `respondendi.py` refuses to plan or adopt anything until a
committed Kean decision and a committed owner-ruling file under `research/readiness/owner_rulings/` both cite
`respondendi-rule-sha256:` followed by the SHA-256 of this exact file (`respondendi.py rule-sha`). Any edit to this
file, the parameters included, changes the hash and needs a new owner decision. One approval covers every lot kind
below, including kinds that are not yet active.

## The rule

A provisional status proposed on the claim kit's status-overlay route is adopted, without a separate owner decision
for the order or for its kind, when the order belongs to exactly one lot kind below, meets that kind's predicate,
and meets every common condition. Everything is shown by files pinned by SHA-256 in the repository.

### Lot kinds

Each kind has a zero-token predicate that reads only the claim and its pinned frozen evidence. A kind whose route is
not yet on main cannot be met: its predicate needs record types that only the fixed claim kit emits, so it stays
inactive, with no flag to switch, until that fix is merged. When the first qualifying claim of a kind appears, its
stratum opens on probation (see the audit plan); no owner decision per kind is needed.

| Kind | Status | Predicate (all must hold) | Prerequisite |
|---|---|---|---|
| `express_named_revocation` | NO | the end is an express, named, unqualified end by a later order or proclamation: the located ending quote names the order by number in the clause carrying an ending verb, with no qualifier or section heading between; the actor is another presidential instrument held with its hash; the end falls on or after the actor's signing date and before the cutoff; the decision's basis is an `ACT:` or `ACTOR_TEXT:` record, and no `ACT:` basis record is partial or carries a savings phrase | none (active) |
| `own_terms` | NO | the end is the order's own stated end (fixed term, sunset date, until-event), dated on or before the cutoff; the decision's basis includes a `TERM:` record of one of those kinds whose stated or computed end equals the claimed end date | none (active) |
| `spent_on_issue` | NO | the end is the order's own one-time act, complete on issue or on performance; the decision's basis includes an `OWN_TEXT:` record whose `own_text_kind` equals the claimed mechanism | F5 on main: the kit emits `OWN_TEXT:` records (D-20261028-evidence-decides; Pothier ruling P1) |
| `follows_parent` | NO | the order only amended a parent and its text ended with the parent (Pothier ruling P2; D-20261021-strike-and-insert): the claim names the parent, and the parent's ending quote passes the express check for the parent's number; the decision's basis includes a `PARENT_END:` record | F5 on main: the kit emits `PARENT_END:` records |
| `yes_current` | YES | the decision's basis includes a `CURRENT:` record and the current predicate is checked through the cutoff; the claim asserts no whole-order end; the frozen evidence holds no whole-scope ending lead; the review set includes a `later_event_removed` control | F3 on main: the kit builds `CURRENT:` records for undecided orders |
| `outer_bound` | NO | the end is an outer bound under the owner's bound rule, cited by the claim | the owner's approval of the outer-bound ask (Ulpian), recorded as a committed decision citing `respondendi-lot-open:outer_bound`, and a rule amendment naming its bound rule id |

**Text basis.** Each kind accepts an original (the frozen ORIGINAL is acceptable as an original) and, once F6 is on
main, a working text: the ORIGINAL record names its `working_text_basis` (`tracker_original_supported` or
`lachmann_confirmation`) and its grade is one the readiness tracker already credits (2026-10-21 transcription ruling;
2026-10-31 working-text ruling). The text basis is part of the stratum, so working-text adoptions are audited as
their own population.

**Status-only tier.** A claim published as `partial_research` may carry its status alone when its kind allows it, the
common conditions hold for it (both arms upheld it in the `partial_research` scope, confirming its exact open gaps),
its open gaps are only of the kinds in `status_only_allowed_gate_errors`, and the checker passed every step in
`status_only_required_checker_steps`. The status is adopted; the claim is not filed canonically and the order goes on
to decided-order production. No YES is adopted status-only.

### Common conditions

1. **Admitted.** The order was prepared inside a Bentham action in `allowed_actions` (packet `ADMISSION.json`).
2. **Undecided and in the census.** The order has no provisional status and is in the census.
3. **Status reviewed.** An independent status reviewer, not the producer, accepted the producer's status decision.
4. **Two blind arms upheld** the exact claim (the same SHA-256), each in a separate context and distinct from the
   producer and the status reviewer; for a genuine planted-control claim, both upheld it after the reveal.
5. **Typed controls caught.** At least `min_controls` planted controls and one per `claims_per_control` claims, of
   at least `min_control_kinds` kinds, at least one status-determining, each kind named in its adjudication record;
   every arm rejected every control; a kind's `required_control_kinds` are in the review set.
6. **Checker passed** the exact claim, with no completion exception or gate error (status-only: the listed steps).
7. **Audited before adoption** (audit plan below). Nothing reaches the status ledger before its audits.
8. **Pinned trail.** Plan, lot receipt, completion, reviews, status review, decision, proposal, publication receipts,
   audits and adjudications are pinned in the population contract entry.

## Audit plan (sequential, per stratum)

- **Stratum** = process fingerprint (producer and reviewer prompts, `UNDECIDED_CHECKLIST.md`, the kit's overlay,
  completion, assembly and batch code, this rule, the model families) + lot kind + text basis + tier. Any change to
  any of these opens a new stratum, which starts on probation.
- **Probation.** Until a stratum has enough audits for a 95% upper bound of `bound_target` on its error rate (59 with
  no confirmed error, 93 with one, 124 with two), every member of the stratum is audited before adoption. After that,
  `audit_rate_steady` of the stratum's members in each lot, at least `min_audits_steady`, drawn by a generator seeded
  with the plan's hash. A kind may set stricter values in its `overrides`.
- **Auditors.** A person, or an AI of a model family different from the producer and every reviewer of that order.
  The audit checks the status and its dated basis against held sources and records agree or disagree.
- **Adjudication.** A disagreement goes to a third reviewer (a person, or an AI of a family other than the
  auditor's and the reviewers'), who records a confirmed error or the auditor's error. Only a confirmed error counts.
  A lot with a confirmed error is audited in full before any of it is adopted; the order in error is not adopted.
- **Stop rule, per stratum.** `stop_confirmed_errors_in_59` confirmed errors within the stratum's last 59 audits, or
  an upper bound above `stop_bound` after `stop_bound_after_audits` audits, stops that stratum (other strata go on)
  until the owner records a decision citing `respondendi-resume:` and the stratum. A disagreement left unadjudicated
  for more than `max_unadjudicated_days` days blocks every adoption.

## Other safeguards

- **Size and cadence.** At most `max_lot_orders` orders a lot, `max_orders_per_week` a week and `max_lots_per_day`
  lot a day: frozen evidence of packets in flight pins the whole status ledger, so adopt after the day's batches.
- **Reversible.** The row leaves the ledger and the lot's rows; a filed claim stays (claim files are append-only) with
  an unresolved source-audit hold; a pinned reversal record says why.
- **Owner report.** `research/respondendi/REPORT.md` is regenerated after every write: lots, statuses by kind, audits,
  confirmed errors and the audit-based upper bound per stratum.
- **Suspension.** The owner may suspend or end the rule at any time with a recorded decision citing
  `respondendi-suspend-sha256:` followed by this file's hash.

## What this rule never does

- It never certifies anything: AI review is not human certification, and the certified count stays 0.
- It never decides a status from the absence of evidence: every kind needs a held, located basis record (a YES needs
  a `CURRENT:` record, never the mere absence of a revocation). It never changes the codebook, frozen weights,
  census, source grades or owner rulings, and never adopts an order that already has a status.
- It never adopts a proposal that fails any condition; such proposals stay isolated replacement proposals for a
  named owner decision.
- It never counts a status-only adoption as a finished dossier: the order is decided, not ready.

## Parameters

```json
{
 "rule_id": "respondendi-standing-adoption/v2",
 "allowed_actions": ["status_assignment.undecided", "probe.status_assignment.undecided"],
 "statuses_allowed": ["no", "yes"],
 "cutoff": "2026-10-14",
 "kinds": {
  "express_named_revocation": {
   "status": "no",
   "mechanisms": ["express_revocation", "express_supersession", "express_repeal", "express_termination", "body_abolished"],
   "basis_prefixes": ["ACT:", "ACTOR_TEXT:"],
   "actor_prefixes": ["EO:", "PROC:"],
   "ending_verbs": ["revoked", "revoke", "superseded", "supersedes", "supersede", "rescinded", "repealed", "terminated", "abolished"],
   "qualifiers": ["in part", "so far as", "insofar as", "in so far as", "except", "to the extent", "as of the dates", "partial", "with respect to"],
   "text_bases": ["original", "working"],
   "status_only": true
  },
  "own_terms": {
   "status": "no",
   "mechanisms": ["expiration_by_own_terms", "fixed_term", "sunset_date", "until_event"],
   "basis_prefixes": ["TERM:"],
   "term_kinds": ["fixed_term", "sunset_date", "until_event"],
   "text_bases": ["original", "working"],
   "status_only": true
  },
  "spent_on_issue": {
   "status": "no",
   "mechanisms": ["spent_on_issue", "task_completed"],
   "basis_prefixes": ["OWN_TEXT:"],
   "text_bases": ["original", "working"],
   "status_only": true,
   "prerequisite": "F5 on main (claim kit emits OWN_TEXT records)"
  },
  "follows_parent": {
   "status": "no",
   "mechanisms": ["follows_parent"],
   "basis_prefixes": ["PARENT_END:"],
   "actor_prefixes": ["EO:", "PROC:"],
   "ending_verbs": ["revoked", "revoke", "superseded", "supersedes", "supersede", "rescinded", "repealed", "terminated", "abolished"],
   "qualifiers": ["in part", "so far as", "insofar as", "in so far as", "except", "to the extent", "as of the dates", "partial", "with respect to"],
   "text_bases": ["original", "working"],
   "status_only": true,
   "prerequisite": "F5 on main (claim kit emits PARENT_END records)"
  },
  "yes_current": {
   "status": "yes",
   "basis_prefixes": ["CURRENT:"],
   "ending_verbs": ["revoke", "supersede", "terminate", "abolish"],
   "required_control_kinds": ["later_event_removed"],
   "text_bases": ["original", "working"],
   "status_only": false,
   "prerequisite": "F3 on main (claim kit builds CURRENT records for undecided orders)",
   "overrides": {"stop_confirmed_errors_in_59": 1}
  },
  "outer_bound": {
   "status": "no",
   "mechanisms": ["outer_bound"],
   "basis_prefixes": [],
   "owner_token": "respondendi-lot-open:outer_bound",
   "bound_rule_id": null,
   "text_bases": ["original", "working"],
   "status_only": false,
   "prerequisite": "owner approval of the outer-bound ask (Ulpian) and a rule amendment naming its bound rule id"
  }
 },
 "text_bases": {
  "working": {
   "grades": ["archival_replica_checked", "machine_read_government_printed_copy", "official_printing", "government_printed_copy"],
   "working_text_basis": ["tracker_original_supported", "lachmann_confirmation"],
   "prerequisite": "F6 on main (overlay route accepts tracker-credited working texts)"
  }
 },
 "min_blind_arms": 2,
 "min_controls": 2,
 "claims_per_control": 15,
 "control_kinds": ["date_shift", "partial_as_whole", "transfer_as_end", "later_event_removed", "ending_source_swapped", "wrong_order_text"],
 "status_control_kinds": ["partial_as_whole", "transfer_as_end", "later_event_removed", "ending_source_swapped", "wrong_order_text"],
 "min_control_kinds": 2,
 "bound_target": 0.05,
 "audit_rate_steady": 0.20,
 "min_audits_steady": 2,
 "stop_confirmed_errors_in_59": 2,
 "stop_bound": 0.10,
 "stop_bound_after_audits": 30,
 "max_unadjudicated_days": 7,
 "max_plan_age_days": 14,
 "max_lot_orders": 60,
 "max_orders_per_week": 300,
 "max_lots_per_day": 1,
 "status_only_allowed_gate_errors": ["unresolved_material_gaps"],
 "status_only_required_checker_steps": ["original_text", "ending_or_current_basis", "savings_residuals", "counterevidence"]
}
```
