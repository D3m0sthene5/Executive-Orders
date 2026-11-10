# Respondendi standing adoption rule, version 1 (DRAFT: not in force)

This text is what the owner approves or declines. `respondendi.py` refuses to adopt anything until a recorded
owner decision cites the SHA-256 of this exact file (`python -I jobs/respondendi-adoption/respondendi.py rule-sha`).
Any edit to this file, the parameters included, changes the hash and needs a new owner decision.

## The rule

A provisional status proposed on the claim kit's status-overlay route is adopted, without a separate owner decision
for the order, when every condition below holds and is shown by files pinned by SHA-256 in the repository:

1. **Admitted.** The order was prepared inside a Bentham action named in `allowed_actions`, shown by the packet's
   `ADMISSION.json` receipt.
2. **Undecided and in the census.** The order has no provisional status in the accepted population and is in the
   census. Nothing here changes a status that has already been decided.
3. **Status reviewed.** An independent status reviewer, not the producer, accepted the producer's status decision
   (`STATUS_REVIEW.json`: decision `accept`, independence and source checks confirmed), and the reviewed status is
   one of `statuses_allowed`.
4. **Two blind arms upheld.** At least `min_blind_arms` independent reviewers in separate contexts, each different
   from the producer and the status reviewer, upheld the exact claim (the same SHA-256) as a whole case. For the
   genuine version of a planted control, both upheld it after the reveal.
5. **Controls caught.** The review set held at least `min_controls` planted controls, and at least one per
   `claims_per_control` claims, and every arm rejected every planted control.
6. **Checker passed.** The project's claim checker passed the exact claim in the completion receipt, and the kit's
   completion recorded no exception and no gate error for it.
7. **Status only, when the lifecycle is not finished.** A claim published as `partial_research` may carry its status
   alone into the accepted population when conditions 1-5 hold for it (both arms upheld it in the `partial_research`
   scope, confirming its exact open gaps), its open gaps are only of the kinds in `status_only_allowed_gate_errors`
   (clause-level gaps that do not touch the whole-order status), a NO states a dated whole-order end with its source,
   and the checker passed every step in `status_only_required_checker_steps`. The status is adopted; the claim is not
   filed canonically and the order goes on to ordinary decided-order production, which must finish its lifecycle.
8. **Pinned trail.** The completion, reviews, status review, decision, proposal and publication receipts are pinned
   by SHA-256 in the lot receipt and in the population contract entry.

## Safeguards

- **Sampled audit by another model family or a person.** Every lot draws a random audit sample, seeded by the lot
  receipt's hash. While the rule is on probation (fewer than `probation_audits` agreeing audits in a row), the
  sample is `audit_rate_probation` of the lot and at least `min_audits_probation` orders; after that,
  `audit_rate_steady` and at least `min_audits_steady`. An AI auditor must be of a different model family from the
  producer and every reviewer of that order. An audit checks the status and its dated basis against held sources.
- **Stop rule.** One audit that disagrees with an adopted status stops all adoption under this rule until the owner
  records a resume decision. The disputed order is reversed to undecided at once.
- **Audit debt.** No new lot is adopted while more than `max_pending_audits` sampled orders are unaudited, or while
  any sampled order has waited more than `max_audit_age_days` days.
- **Size limits.** At most `max_lot_orders` orders per lot and `max_orders_per_week` per seven days.
- **Reversible.** Any adoption can be reversed: the row, the contract entry and the canonical claim are removed and
  a pinned reversal record says why. A reversed order is undecided again.
- **Owner report.** `respondendi.py report` writes the adoptions, audits, disagreements, reversals and the
  audit-based upper bound on the error rate; it is regenerated with every lot and summarized in Kean.
- **Suspension.** The owner may suspend or end the rule at any time with a recorded decision that cites
  `respondendi-suspend-sha256:` followed by this file's hash.

## What this rule never does

- It never certifies anything: AI review is not human certification, and the certified count stays 0.
- It never decides a status from the absence of evidence, never changes the codebook, frozen weights, census,
  source grades or owner rulings, and never adopts an order that already has a status.
- It never adopts a proposal that fails any condition; such proposals stay isolated replacement proposals.
- It never counts a status-only adoption as a finished dossier: the order is decided, not ready.

## Parameters

```json
{
 "rule_id": "respondendi-standing-adoption/v1",
 "allowed_actions": ["status_assignment.undecided", "probe.status_assignment.undecided"],
 "statuses_allowed": ["no"],
 "min_blind_arms": 2,
 "min_controls": 1,
 "claims_per_control": 15,
 "probation_audits": 59,
 "audit_rate_probation": 0.34,
 "min_audits_probation": 2,
 "audit_rate_steady": 0.10,
 "min_audits_steady": 1,
 "max_pending_audits": 20,
 "max_audit_age_days": 14,
 "max_lot_orders": 60,
 "max_orders_per_week": 300,
 "status_only": true,
 "status_only_allowed_gate_errors": ["unresolved_material_gaps"],
 "status_only_required_checker_steps": ["original_text", "ending_or_current_basis", "savings_residuals", "counterevidence"],
 "stop_on_disagreements": 1
}
```
