# Owner decision, 2026-11-09: Lachmann skipped-witness switch set to "flag"

Asked in A-20261109-skipped-witness (Gutenberg wave, PR #242). The owner answered "yes" in the Gutenberg session on
2026-11-09.

**Decision.** `jobs/claim-kit/WORKING_TEXT_SWITCHES.json` `skipped_witness_addition` is `flag`. A frozen Lachmann
working-text confirmation no longer goes stale when the only difference is skipped witnesses that Lachmann added for
a known reason (`grade_not_in_working_text_policy`, `text_hash_mismatch`) and never compared. Each such witness raises
`working_text:skipped_witness_added_recheck:<grade>:<why>`, shown in the tracker's `working_text_recheck_flags`
column. Every other difference still makes the confirmation stale.

**Measured before the decision** (all 1,530 claims on 2026-11-09): 126 orders were blocked only by
`working_text:prior_confirmation_stale`, every difference being added skipped witnesses; under `flag` exactly these
126 lose that error and gain recheck flags. Kean F-20261109-gutenberg-skipped-witness.

**Unchanged.** No claim is re-frozen or edited. D-20261108-photius-recheck still applies: the flagged orders' h01 page
check against the official printing remains owed, and the flag lists the orders it covers. No status, census,
codebook entry or certified count (0) changes. This is a provisional working-text rule, never authentication.
