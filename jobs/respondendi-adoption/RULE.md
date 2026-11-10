# Respondendi standing adoption rule, version 2 (DRAFT: not in force)

This text is what the owner approves or declines. `respondendi.py` refuses to plan or adopt anything until, **on
GitHub's main** (the local origin/main must equal it at the moment of writing), a Kean decision whose ruling is
exactly `Owner approves respondendi-rule-sha256:<sha>` and an owner-ruling file under
`research/readiness/owner_rulings/` (listed in that decision's sources) holding that exact line both name the SHA-256
of this exact file (`respondendi.py rule-sha`). A conditional or partial approval is no approval: to approve fewer
kinds, amend this file (a new hash) and approve that. Any edit to this file, the parameters included, changes
the hash and needs a new owner decision. One approval covers every lot kind below, including kinds that open later.

## The rule

A provisional status proposed on the claim kit's status-overlay route is adopted, without a separate owner decision
for the order or for its kind, when the order belongs to a lot kind below, meets that kind's predicate, and meets
every common condition. Everything is shown by files pinned by SHA-256 in the repository.

### Lot kinds

The kind is fixed by the kit-emitted records the status decision cites, never by the producer's wording. Each kind's
predicate is zero-token: it reads only the claim and its pinned frozen evidence. A kind with a `route` is active only
while the merged claim kit declares that route live: `UNDECIDED_ROUTES` in `jobs/claim-kit/status_overlay.py` on
origin/main, a constant that only the pull request making the route's gate live adds (agreed with the F3-F6 work). The
first qualifying claim of a newly active kind opens its stratum on probation; no owner decision per kind is needed.

| Kind | Status | Predicate (all must hold) | Route |
|---|---|---|---|
| `express_named_revocation` | NO | The basis cites an `ACT:` record by the claimed actor that is whole-scope and names the order directly (not through a parent); the machine verb typing is only a first filter (`act_verbs`, which keeps `transfer` and `other` because the extractor types "is hereby repealed and the functions ... transferred" as a transfer), and the decisive test is the sentence below. Its provision text (at most `max_provision_chars`) has one sentence that introduces the order as "Executive Order (No.) N" by its full printed number, carries an ending verb and no qualifier, and has no partial or relational phrase in the 80 characters before the number. No sentence naming the order carries a qualifier, and no "is amended" stands between the number and the verb. The claim's ending quote contains that provision; the end equals the record's effective date when it has one; the provision carries no exception or savings phrase. The actor was signed after the order and the end falls on or after the actor's signing and before the cutoff. A second witness agrees: a catalog note entry that begins "Revoked (or Superseded, Rescinded, Terminated) by:" the same actor, with no parenthesis or partial wording. No catalog entry acts on the order after the claimed end; the same actor acts on no part of the order; no reinstatement or continuation lead or note is held. | none (active) |
| `own_terms` | NO | The basis cites a whole-order `TERM:` record of a stated kind (`term_kinds`) whose stated end date equals the claimed end, which is the order's own, after its signing and before the cutoff, and whose text sets an expiry for this order (`term_text_pattern`) with no extension, renewal or further-order wording. No later instrument (no `ACT:` or `ACTOR_TEXT:` record, no missing later instrument, no catalog entry amending, continuing, extending, revoking or superseding it) touches the order. The review set holds a `later_event_removed` control planted on an own-terms claim. | none (active) |
| `spent_on_issue` | NO | The basis cites a whole-order `OWN_TEXT:` record by the order itself (scope whole; the kit's whole-order test found no continuing sentence; the kit's gate re-derives the record from the frozen original), of kind `spent_on_issue` or `amends_parent` (Pothier ruling P2 as the owner applied it on 2026-11-09: the amending command is spent on issue; the inserted text is a consequence in the parent), with its operative text. The end is the order's own, on its signing date. No catalog entry records a later act on the order. For an amending order whose parent's end is held (`PARENT_END:`), the claim's savings record cites that record as its source. No status-only tier. Every member is audited (the classifier's measured precision is 84%, 42 of 50, 95% about 71-93%). | `own_text` (F5) |
| `yes_current` | YES | The basis cites a `CURRENT:` record and the current predicate is checked through the cutoff; the claim asserts no end. Allow-list screens, all zero-token: every catalog note entry carries a label in `allowed_labels`; no observation, event or current-law lead carries an ending signal; the dossier lists no missing source; no `ACT:` or `ACTOR_TEXT:` record; no own-terms record of an ending kind; every search in `complete_searches` complete. The review set holds a `later_event_removed` control planted on a YES claim. Every member of every YES lot is audited, and one confirmed error stops YES. | `current` (F3) |

| `ulpian_life_bound` | NO | The owner's Ulpian bound rule (D-20261110-ulpian-life-bound) is on GitHub's main at the approved hash, with its decision and ruling. The order is a `quoted_fact` member of that rule's class table (`research/ulpian/CLASS.csv` on main), still undecided, with a bound before the cutoff. The claim's whole-order end is `not_later_than` that bound with the first cause unresolved, cites the held text the class read, states the birth bound it rests on and that use of the permission is unknown. The review set holds at least one control of the Ulpian status kinds (a hidden second person or clause, or a fact about another person) planted on a claim of this kind. Every member is audited, and one confirmed error stops the kind. | the owner's Ulpian rule on main (PR #271) |

**Text basis.** Each kind accepts an original (the frozen ORIGINAL is acceptable as an original) and, while the merged
kit declares the `working_text` route live (F6), a working text: the ORIGINAL record names its `working_text_basis`
and its grade is one the readiness tracker already credits (2026-10-21 transcription ruling; 2026-10-31 working-text
ruling). The text basis is part of the stratum.

**Status-only tier.** For kinds that allow it, a claim published as `partial_research` may carry its status alone
when the common conditions hold for it in that scope, its open gaps are only of the kinds in
`status_only_allowed_gate_errors` and none concerns another instrument or the status itself, and the checker passed every step in `status_only_required_checker_steps`. The
claim is not filed canonically; the order goes on to decided-order production. No YES is adopted status-only.

### Common conditions

1. **Admitted** inside a Bentham action in `allowed_actions` (packet `ADMISSION.json`).
2. **Undecided and in the census.**
3. **The claim kit's own gates pass again** on the pinned bundle: the evidence seal, the producer decision
   (`_decision_errors`) and the independent status review (`_review_errors`); the completion is at most
   `max_completion_age_days` old.
4. **Status reviewed** by an independent reviewer, not the producer, who accepted it.
5. **Two blind arms upheld** the exact claim, each in a separate context and distinct from the producer and the status
   reviewer; for a genuine planted-control claim, both upheld it after the reveal.
6. **Typed controls caught:** at least `min_controls` and one per `claims_per_control` claims, of at least
   `min_control_kinds` kinds, one status-determining, each kind named in its adjudication record; every arm rejected
   every control; a kind's `required_control_kinds` are in the review set.
7. **Checker passed** the exact claim, with no completion exception or gate error (status-only: the listed steps).
8. **Audited before adoption** (below). **Pinned trail** in the population contract entry.

## Audit plan

- **Stratum** = process fingerprint (prompts, `UNDECIDED_CHECKLIST.md`, the kit's overlay, completion, assembly and
  batch code, this rule, the model families) + kind + text basis + tier. **Probation is per stratum:** every member
  is audited until the stratum's 95% upper bound reaches `bound_target` (59 audits with no confirmed error, 93 with
  one, 124 with two), then `audit_rate_steady` of each lot (YES: always every member), drawn by a generator seeded
  with the claims and this rule, not the lot name or date.
- **What counts:** a confirmed error always, and every reversal; an agreeing audit only when it was in its plan's
  sample and its lot was adopted. An order with a confirmed error or a reversal on record never returns under this
  rule. Every audit and adjudication pins its own evidence file in the lot's `audit-evidence/` folder, never reused,
  naming the order and its exact claim hash: for an AI, a JSON run receipt whose model id gives its family; a person
  must be one of `human_auditors`.
- **Auditors:** a person, or an AI of a model family different (case-insensitively) from the producer and every
  reviewer. **Adjudication:** a third reviewer of another kind or family; only a confirmed error counts; a lot with
  a confirmed error is audited in full; the order in error is not adopted.
- **Stop rule, per kind** (kind + text basis + tier, across process changes, so a prompt change cannot escape it):
  `stop_confirmed_errors_in_59` confirmed errors in the last 59 counted audits (YES: 1), or an upper bound above
  `stop_bound` after `stop_bound_after_audits`, stops the kind until the owner records, on main,
  `Owner resumes respondendi-resume:<kind key>@<audit count>` (a count no larger than the findings that existed);
  errors after that count stop it again. A disagreement
  unadjudicated for `max_unadjudicated_days` days blocks every adoption.

## Other safeguards

- **Clock:** dates come from the system clock; the command line takes none. **Sampling:** each member is drawn
  by its own claim hash against the rate, so lot composition cannot steer the sample. **Kit code:** the claim-kit
  files whose gates are re-run must equal main's. **Size and cadence:** at most `max_lot_orders` a lot,
  `max_orders_per_week` a week, `max_lots_per_day` lot a day.
- **Reversible:** the row leaves the ledger; a filed claim stays with an unresolved source-audit hold; the reversal
  counts as a confirmed error.
- **Owner report** `research/respondendi/REPORT.md`, regenerated after every write. **Suspension** by a decision
  on main beginning `Owner suspends respondendi-suspend-sha256:<sha>`.

## What this rule never does

- It never certifies anything: AI review is not human certification, and the certified count stays 0.
- It never decides a status from the absence of evidence: a NO needs a located ending record and a YES a positive
  current-status record; the negative screens only keep claims out. It never changes the codebook, frozen weights,
  census, source grades or owner rulings, and never adopts an order that already has a status.
- It never adopts a proposal that fails any condition; such proposals stay for a named owner decision.
- It never counts a status-only adoption as a finished dossier.

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
   "act_verbs": ["revoke", "supersede", "terminate", "transfer", "other"],
   "ending_verbs": ["revoked", "revoke", "revoking", "superseded", "supersedes", "supersede", "rescinded", "repealed", "terminated"],
   "pre_qualifiers": ["section", "sec ", "secs ", "paragraph", "subsection", "so much of", "that part of", "part of", "parts ", "provisions of", "provision of", "established by", "created by", "issued under", "pursuant to", "as amended by", "which revoked", "revoking", "revoked by", "clause", "schedule ", "sentence of"],
   "qualifiers": ["in part", "so far as", "insofar as", "in so far as", "except", "to the extent", "as of the dates", "partial", "with respect to", "as to ", "as it applies", "as it affects", "in its application", "relating to", "other than", "provided", "subject to", "effective upon", "shall be", "until", "for the period", " not ", "neither", "without revoking", "nothing in", "reinstat", "suspend"],
   "max_provision_chars": 3000,
   "text_bases": ["original", "working"],
   "status_only": true
  },
  "own_terms": {
   "status": "no",
   "term_kinds": ["fixed_term", "sunset_date"],
   "term_text_pattern": "this order[^.;]{0,120}\\b(expire|terminate|remain in (effect|force) until|continue in (effect|force) until|in (effect|force) until|effective until)",
   "extension_words": ["unless", "extend", "renew", "further order", "otherwise directed", "such later date", "or until"],
   "required_control_kinds": ["later_event_removed"],
   "text_bases": ["original", "working"],
   "status_only": true
  },
  "spent_on_issue": {
   "status": "no",
   "route": "own_text",
   "own_text_kinds": ["spent_on_issue", "amends_parent"],
   "text_bases": ["original", "working"],
   "status_only": false,
   "prerequisite": "F5 merged: UNDECIDED_ROUTES on main includes own_text (claim kit emits OWN_TEXT records)",
   "overrides": {"audit_rate_steady": 1.0, "min_audits_steady": 1}
  },
  "yes_current": {
   "status": "yes",
   "route": "current",
   "ending_signals": ["revoked", "revocation", "superseded", "terminated", "rescinded", "repealed", "expired", "abolished", "no longer", "ceased", "obsolete", "omitted", "eliminated", "executed", "suspended", "nullified", "ended_by", "spent"],
   "allowed_labels": ["amends", "revokes", "supersedes", "see", "see also", "amended"],
   "ending_term_kinds": ["fixed_term", "sunset_date", "until_event", "emergency_duration", "temporary_body"],
   "complete_searches": ["current-law:usc", "current-law:ecfr", "later-events:ofr_catalog"],
   "required_control_kinds": ["later_event_removed"],
   "text_bases": ["original", "working"],
   "status_only": false,
   "prerequisite": "F3 merged: UNDECIDED_ROUTES on main includes current (claim kit builds CURRENT records for undecided orders)",
   "overrides": {"stop_confirmed_errors_in_59": 1, "audit_rate_steady": 1.0, "min_audits_steady": 1}
  },
  "ulpian_life_bound": {
   "status": "no",
   "mechanisms": ["life_of_named_person"],
   "owner_rule": {"path": "jobs/ulpian-outer-bound/RULE.md", "sha256": "57a95ba0c11e7207c27de317d7f522c24d05b9aedda91eea261ea2f9c0f64699",
                  "token": "ulpian-rule-sha256:", "decision": "D-20261110-ulpian-life-bound", "class": "research/ulpian/CLASS.csv"},
   "required_control_any": ["second_person_hidden", "second_clause_hidden", "fact_about_another_person"],
   "text_bases": ["original", "working"],
   "status_only": false,
   "prerequisite": "PR #271 merged: the Ulpian rule, its owner decision and class table on main",
   "overrides": {"stop_confirmed_errors_in_59": 1, "audit_rate_steady": 1.0, "min_audits_steady": 1}
  }
 },
 "text_bases": {
  "working": {
   "route": "working_text",
   "grades": ["archival_replica_checked", "machine_read_government_printed_copy", "official_printing", "government_printed_copy"],
   "working_text_basis": ["tracker_original_supported", "lachmann_confirmation"],
   "prerequisite": "F6 merged: UNDECIDED_ROUTES on main includes working_text"
  }
 },
 "min_blind_arms": 2,
 "min_controls": 2,
 "claims_per_control": 15,
 "control_kinds": ["date_shift", "partial_as_whole", "transfer_as_end", "later_event_removed", "ending_source_swapped", "wrong_order_text",
                   "second_person_hidden", "second_clause_hidden", "class_clause_hidden", "fact_about_another_person"],
 "status_control_kinds": ["partial_as_whole", "transfer_as_end", "later_event_removed", "ending_source_swapped", "wrong_order_text",
                          "second_person_hidden", "second_clause_hidden", "class_clause_hidden", "fact_about_another_person"],
 "min_control_kinds": 2,
 "bound_target": 0.05,
 "audit_rate_steady": 0.20,
 "min_audits_steady": 2,
 "stop_confirmed_errors_in_59": 2,
 "stop_bound": 0.10,
 "stop_bound_after_audits": 30,
 "max_unadjudicated_days": 7,
 "max_plan_age_days": 14,
 "max_completion_age_days": 14,
 "max_lot_orders": 60,
 "max_orders_per_week": 300,
 "max_lots_per_day": 1,
 "status_only_allowed_gate_errors": ["unresolved_material_gaps"],
 "status_only_forbidden_gap_pattern": "(executive order|\\be ?o ?\\d|\\beo:|proclamation|\\bproc\\b|reinstat|revok|supersed|in force|status)",
 "human_auditors": ["owner"],
 "status_only_required_checker_steps": ["original_text", "ending_or_current_basis", "savings_residuals", "counterevidence"]
}
```
