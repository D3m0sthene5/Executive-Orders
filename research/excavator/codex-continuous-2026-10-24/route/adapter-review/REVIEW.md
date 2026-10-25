# Independent status-adapter engineering review

**Final verdict: the repaired staged adapter passes this bounded engineering
review.** The initial staged version required three changes, detailed below;
the author repaired all three in stage without changing live files. This is an
engineering assessment of discovery and provenance binding, not legal review,
source adequacy assessment, adoption, or human certification. The reviewed
staged module hash is recorded in both JSON receipts.

The repaired version passes 23 focused tests (15 status plus eight prior
research, 0.068 reported seconds), the three additional hostile probes, and
the independent 37-case audit (6.369922 elapsed machine seconds). Final pins
are in `PROBES_FIXED_EXPLICIT_FIXTURE.json` and `REAL_COHORT_FIXED.json`.
Each faulty review manifest now reports a stale review, required reconciliation,
and adoption-version reconciliation while preserving the valid canonical
evidence record. A wrong embedded dossier makes the evidence and review stale.
No further blocking defect was found in this bounded inspection.

An intermediate repaired-version probe accidentally loaded the old live fixture
because an imported kit helper prepended its directory to `sys.path`; that
receipt is preserved as `PROBES_FIXED.json` and is not the final probe proof.
The harness now explicitly loads the requested staged fixture. The final
receipt cleanly isolates the three defects and the additional run is not
excluded from cost. The live adapter and active route remain untouched.

## Initial review and retained findings

The staged implementation passes 20 focused status/prior-research tests
(`test_status_continuity` and `test_prior_research`, 0.063 reported seconds).
An independently written bounded check also passes for all 29 adopted cohort
identities, both withheld identities, and six parent-ending holds (37 total;
6.525570 elapsed machine seconds). Exact producer and review pointers,
scope, D6 qualifications, current adoption state, the EO13975 correction and
EO10704 rejected theory reach the brief. EO9380/9593 remain needs-research;
all six holds remain held. No automatic or whole-lifecycle approval appears.
Changed or missing actual sources remain explicit reconciliation tasks.

The real-data check uses the 29 published decided dossiers plus eight
historical frozen base dossiers strictly as audit carriers. It does not claim
that those eight are current production freezes. It checks authoritative
status/review/hold file hashes before and after its read-only run. Git-base
comparison was not attempted because the checkout's gitdir is under parent
recovery; this is a before/after nonmutation proof, not an independent GitHub
head check.

Three additional temporary-record probes expose missing reconciliation guards:

1. **Wrong evidence member in the cross-family input manifest.** Replace the
   input manifest's EVIDENCE entry with a different, existing, correctly
   SHA-pinned evidence file for another instrument while leaving the asserted
   canonical evidence fingerprint intact. The adapter still binds the review
   as exact, reports all historical pins match, and emits no reconciliation
   task. The code instead loads the sibling EVIDENCE file inferred from the
   decision path. These contradictory manifest and canonical assertions must
   require reconciliation; neither may silently override the other.
2. **Wrong embedded base-dossier identity.** A resealed evidence object can
   have the intended outer and history identity but a different instrument in
   `base_dossier`. Updating the producer and review pins to that exact object
   still produces exact evidence/review binding and no identity reconciliation.
   The adapter needs the bounded actual-schema base-dossier identity/status/seal
   checks already used by the existing frozen-evidence validator, without
   imposing current-generation freshness on historical research.
3. **Missing EVIDENCE input hash.** Removing the evidence member's SHA leaves
   exact review binding, all-historical-pins-match and no reconciliation. The
   generic dependency walker skips entries without a truthy SHA. Required
   producer/evidence manifest entries must be unique and qualified; missing
   pins need explicit reconciliation.

All three probes retain `automatic_approval=false`; the defect is an erroneous
exact-binding/no-reconciliation representation. No legal approval escalation
was demonstrated. Each also currently returns
`recorded_provisional_status_for_review`, so the source/version discrepancy is
not surfaced through the adoption-state qualifier either.

`PROBES_INITIAL.json` contains the exact outputs. `probe_status_adapter.py`
reproduces them using only temporary synthetic records. `REAL_COHORT_INITIAL.json`
and `check_real_cohort.py` preserve the independent real-data assertions.
The adapter author initially reported leaving before the fixes, then delivered
the three narrow staged repairs while this review was still active. The final
results above supersede the initial changes-required verdict, and all original
receipts remain intact. No live adapter or active route file was changed during
this review.

The targeted rechecks were rerun because the binding logic changed. The parent
must integrate the exact repaired version and regenerate affected production
packets when its policy pin changes; engineering approval is not permission to
apply a changed adapter to already-frozen work silently.
Model token/cache usage, total active labor and net savings are unknown.
