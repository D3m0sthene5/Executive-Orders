# Reviewed overlay completion bridge and checker boundary

The staged completion bridge passes 34 focused tests and selects both exact,
independently reviewed real overlay claims without modifying their bytes.
Actual checker/tracker completion remains the parent/reviewer integration step.
This is engineering validation, not a new legal review or status adoption.

The demonstrated discontinuity was that `completion.selected_claim` required
an ordinary `PACKET.json` for every claim-kit claim. EO10014's ordinary packet
contains an unset-status base dossier and has an explicitly reconciled prior
context change. EO10016's legacy individual overlay has no ordinary packet.
Both reviewed claims instead bind the experimental dossier derived by the
existing frozen status-overlay contract. The initial failed real consumer
attempts remain under each review's `complete-attempt-v1` directory.

## Smallest executable extension

The member now supplies `overlay_bundle` with exactly four whole-file refs:
`evidence` → `EVIDENCE.json`, `decision` → `STATUS_DECISION.json`, `review` →
`STATUS_REVIEW.json`, and `proposal` → `PROMOTION_PROPOSAL.json`. Each ref pins
the exact path and raw SHA-256. All four must be in one isolated bundle.
The existing outer member `review`/`after_reveal_review` still names the
independent lifecycle verdict; it cannot be supplied by the status review.

The bridge calls existing `status_overlay.check_working_claim`, which
revalidates frozen evidence, current source/history/compiler/authority,
the exact producer status decision and independent status review, the derived
experimental dossier, its exact status-overlay label, and existing strict
claim checks. Sources, authority and compiler dependencies are pinned for
the run and the overlay is checked again after the actual consumers before
filing. Ordinary decided claims retain their existing packet checks.

Only `publication.mode: replacement_proposal` can select an unadopted overlay,
including when publication is merely being prepared. `own_claims` fails even
with `--publish`. A forged owner flag or wrong target label fails the existing
overlay gate. Canonical adoption appearing during the run also stops filing;
the producer must then prepare a proper adopted version. Receipts explicitly
retain experimental status, required owner adoption, and
`canonical_filing_allowed: false`. An isolated proposal can be filed, but its
canonical `claims_published` count remains zero.

An optional old ordinary packet can be retained only as exact base-dossier
provenance: raw-file pin, packet seal, producer and decoded frozen base must
match. It is not the current experimental dossier and cannot confer approval
through its historical code/context stamp. The real v2 manifests omit this
optional member field and retain the original packet plus the independent
prior-context delta explanation among explicit receipts. No old packet is
pretended current and no substantive source check is bypassed.

The actual tracker uses authoritative statuses unchanged. Therefore an
unadopted overlay retains `NO_PROVISIONAL_STATUS` and cannot become canonically
ready from this completion. No isolated status map or new tracker was added.

## Exact staged result

Staged source: `/tmp/continuous-completion-stage/completion.py`, SHA-256
`cc5d14a336820a9c3e72563086f4faadcf16be665114cf75858ae2fb4daafc3d`.
The accompanying `test_overlay_completion.py` hash and reproducible focused
command are in `STAGED_VALIDATION.json`. The test's repository-root override
is only needed while it is outside `jobs/claim-kit`.

All 34 focused tests passed in 1.960 reported seconds. Coverage includes exact
legacy/continuous overlay consumption, missing and stale status review,
changed claim/source, different producer, malformed target/forged owner label,
dropped status label on an explicitly declared overlay,
separate exact lifecycle review, unknown target identity, canonical-publication
refusal, isolated exact-byte publication, and an authority change during the
checker. Existing completion tests also pass. Consumer test doubles are used
only in bounded fixture tests; they are not reported as actual corpus runs.

`SELECTED_REAL.json` records actual exact selection on the immediately prior
staged revision (before only the missing-label discriminator was added), control adjudication,
after-reveal review and overlay validation of:

- EO10014, claim `08d839e6073453faf9886f7c87af596ecbad373fadff43bcd6386581cc6374e5`.
- EO10016, claim `8cec62c902fd1b59063c54bfb9a9eb17a0ba7b1ddfb4598e981ea5b36a1fe4ed`.

Both have zero gate errors, strict caught controls, exact after-reveal
whole-case review and `owner_accepted: false`. This selection check took
7.485870 elapsed machine seconds; it is not the final actual checker/tracker
receipt. The parent owns copying the staged files and publishing; this
engineering subtask did not change live completion code or publish anything.

## Independent checker review

The root's narrowly typed proposal-ID exception correctly distinguished
`status-overlay:EO:10014:<20 lowercase hex>` from a second order identity, but
the first revision let malformed values fall through to ordinary citation
scanning. A missing suffix, a plain already-seen EO ID, arbitrary non-ID text,
or null produced no failure. Root repaired this by explicitly validating the
typed field before the general non-string filter.

Twelve independent probes now pass against checker SHA-256
`bf2ab277bed0e5d9e219a7b701396b5a6bc1ab6bd8b1d21cabd5408277d99dc8`.
The valid target-bound field passes. Missing/short pin, plain ID, non-ID, null,
wrong known or unknown target, trailing citation, wrong schema and misplaced
metadata all fail. A genuine unknown ending actor still fails. The exception
remains confined to the one typed metadata field and creates no legal/review
approval. Results: `CHECKER_REVIEW.json`. No further blocking checker defect
was found in this bounded review.

All failed attempts and test-assertion corrections remain costs. Total active
labor, summed task time, tokens/cache use, dollars and net savings are unknown.
