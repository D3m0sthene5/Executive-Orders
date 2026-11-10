# Respondendi standing adoption rule, version 1 (DRAFT: not in force)

This text is what the owner approves or declines. `respondendi.py` refuses to plan or adopt anything until a
committed Kean decision and a committed owner-ruling file under `research/readiness/owner_rulings/` both cite
`respondendi-rule-sha256:` followed by the SHA-256 of this exact file (`respondendi.py rule-sha`). Any edit to this
file, the parameters included, changes the hash and needs a new owner decision.

## The rule

A provisional status proposed on the claim kit's status-overlay route is adopted, without a separate owner decision
for the order, when every condition below holds and is shown by files pinned by SHA-256 in the repository.

**Scope: one lot, defined in advance (the "Hexapla" lot, `lot` below).** The order's whole-order end is an express,
named, unqualified end by a later executive order or proclamation: the ending mechanism is one in `lot.mechanisms`,
the actor is another presidential instrument held as text with its hash, the end falls on or after the actor's
signing date and before the cutoff, and the located ending quote names the order by number within the clause that
carries an ending verb, with no qualifier (in part, so far as, except, to the extent, as of the dates ...). Every
other kind of end (own terms, completion of a task, amendment-only orders, a statute or general rule, a working text,
any YES) stays on a named owner decision until its own lot has its own rule.

1. **Admitted.** The order was prepared inside a Bentham action in `allowed_actions`, shown by the packet's
   `ADMISSION.json` receipt.
2. **Undecided and in the census.** The order has no provisional status in the accepted population and is in the
   census. Nothing here changes a status that has already been decided.
3. **Status reviewed.** An independent status reviewer, not the producer, accepted the producer's status decision,
   and the status is one of `statuses_allowed`.
4. **Two blind arms upheld.** At least `min_blind_arms` independent reviewers in separate contexts, each different
   from the producer and the status reviewer, upheld the exact claim (the same SHA-256). For the genuine version of
   a planted control, both upheld it after the reveal.
5. **Typed controls caught.** The review set held at least `min_controls` planted controls and one per
   `claims_per_control` claims, of at least `min_control_kinds` kinds from `control_kinds`, at least one of them a
   status-determining kind (`status_control_kinds`: a partial end presented as whole, a transfer presented as an end,
   a later event or savings clause removed, a swapped ending source, a wrong order's text). Every arm rejected every
   control. Each control's adjudication record names its kind.
6. **Checker passed.** The project's claim checker passed the exact claim in the completion receipt, and the kit's
   completion recorded no exception and no gate error for it.
7. **Status only, when the lifecycle is not finished.** A claim published as `partial_research` may carry its status
   alone when conditions 1-5 hold for it (both arms upheld it in the `partial_research` scope, confirming its exact
   open gaps), its open gaps are only of the kinds in `status_only_allowed_gate_errors`, and the checker passed every
   step in `status_only_required_checker_steps`. The status is adopted; the claim is not filed canonically and the
   order goes on to decided-order production, which must finish its lifecycle.
8. **Audited before adoption.** See the audit plan. Nothing is written to the status ledger until the lot's audits
   are recorded.
9. **Pinned trail.** The plan, the lot receipt, the completion, reviews, status review, decision, proposal,
   publication receipts, audits and adjudications are pinned by SHA-256 in the population contract entry.

## Audit plan (sequential, per process stratum)

- **Stratum.** Each lot belongs to a process stratum: a fingerprint of the producer and reviewer prompts, this
  checklist (`UNDECIDED_CHECKLIST.md`), the kit's overlay, completion, assembly and batch code, the lot and the model
  families. Any change opens a new stratum.
- **Probation.** Until a stratum has enough audits for a 95% upper bound of `bound_target` on its error rate (59 with
  no confirmed error, 93 with one, 124 with two), every member of every lot is audited before adoption. After that,
  `audit_rate_steady` of each lot and at least `min_audits_steady`, drawn by a generator seeded with the plan's hash.
- **Auditors.** A person, or an AI of a model family different from the producer and every reviewer of that order.
  The audit checks the status and its dated basis against held sources and records agree or disagree.
- **Adjudication.** A disagreement goes to a third reviewer (a person, or an AI of a family other than the
  auditor's and the reviewers'), who records a confirmed error or the auditor's error. Only a confirmed error counts.
  A lot with a confirmed error is audited in full before any of it is adopted; the order in error is not adopted.
- **Stop rule.** `stop_confirmed_errors_in_59` confirmed errors within a stratum's last 59 audits, or an upper bound
  above `stop_bound` after `stop_bound_after_audits` audits, stops the stratum until the owner records a decision
  citing `respondendi-resume:` and the stratum. A disagreement left unadjudicated for more than
  `max_unadjudicated_days` days blocks every adoption.

## Other safeguards

- **Size and cadence.** At most `max_lot_orders` orders a lot, `max_orders_per_week` a week and `max_lots_per_day`
  lot a day: frozen evidence of packets in flight pins the whole status ledger, so adopt after the day's batches.
- **Reversible.** Any adoption can be reversed: the row leaves the ledger and the lot's rows, a filed claim stays (claim
  files are append-only) with an unresolved source-audit hold, and a pinned reversal record says why.
- **Owner report.** `research/respondendi/REPORT.md` is regenerated after every write: lots, statuses,
  audits, confirmed errors and the audit-based upper bound per stratum. Kean summarizes it per wave.
- **Suspension.** The owner may suspend or end the rule at any time with a recorded decision citing
  `respondendi-suspend-sha256:` followed by this file's hash.

## What this rule never does

- It never certifies anything: AI review is not human certification, and the certified count stays 0.
- It never decides a status from the absence of evidence, never changes the codebook, frozen weights, census,
  source grades or owner rulings, and never adopts an order that already has a status.
- It never adopts a proposal that fails any condition; such proposals stay isolated replacement proposals for a
  named owner decision.
- It never counts a status-only adoption as a finished dossier: the order is decided, not ready.

## Parameters

```json
{
 "rule_id": "respondendi-standing-adoption/v1",
 "allowed_actions": ["status_assignment.undecided", "probe.status_assignment.undecided"],
 "statuses_allowed": ["no"],
 "lot": {
  "id": "express-named-revocation",
  "mechanisms": ["express_revocation", "express_supersession", "express_repeal", "express_termination", "body_abolished"],
  "actor_prefixes": ["EO:", "PROC:"],
  "ending_verbs": ["revoked", "revoke", "superseded", "supersedes", "supersede", "rescinded", "repealed", "terminated", "abolished"],
  "qualifiers": ["in part", "so far as", "insofar as", "in so far as", "except", "to the extent", "as of the dates", "partial", "with respect to"],
  "cutoff": "2026-10-14"
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
 "status_only": true,
 "status_only_allowed_gate_errors": ["unresolved_material_gaps"],
 "status_only_required_checker_steps": ["original_text", "ending_or_current_basis", "savings_residuals", "counterevidence"]
}
```
