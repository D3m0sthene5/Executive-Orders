# Continuous undecided route: execution and limits

The ordinary `prepare` command successfully froze EO10014's complete available
base dossier with status unset, beside its blank status decision and lifecycle
CSV sheets. It did not adopt a status or emit a claim. The existing compiler
freshness checks passed without modification or bypass.

The final route keeps one producer investigation through the status boundary:

- `next --scope undecided` can reserve undecided identities with history and
  compiler-generation pins; selection is not a source-readiness finding.
- Ordinary `dossier`, `sheet`, and `prepare` use the existing full frozen
  `status_overlay` base dossier when no decided dossier exists.
- `apply` retains a submitted undecided lifecycle sheet with outcome
  `awaiting_status_review`; it does not emit an unset-status claim.
- `overlay-propose --lifecycle-sheet PATH` carries that exact analysis into the
  independently reviewed working-status dossier. It snapshots the input as
  `LIFECYCLE_SOURCE_DECISION.json`, pins both versions in
  `LIFECYCLE_CONTINUITY.json`, and resets producer approval because the dossier
  fingerprint has changed. Producer reconfirmation and independent lifecycle
  review remain necessary. The owner-adoption gate remains separate.
- Batch packets now pin the directly used `status_overlay.py` policy code.

The resumed engineering inspection fixed two version defects: the carried
sheet previously retained `approved=true`, and batch policy pins omitted the
new direct `status_overlay.py` dependency. Wrong sheet schema, instrument, and
dossier versions are rejected. No compiler file was changed by these repairs.

## Executed proof

From repository root:

```text
python -B jobs/claim-kit/kit.py --output tmp/continuous-compiled prepare EO:10014 --agent codex-continuous-route --write research/excavator/codex-continuous-2026-10-24/route/freeze-eo10014-v1
python -B jobs/claim-kit/kit.py --output tmp/continuous-compiled view research/excavator/codex-continuous-2026-10-24/route/freeze-eo10014-v1
```

Both commands succeeded. The exact source artifact is
`freeze-eo10014-v1/undecided/EO_10014/EVIDENCE.json`; its adjacent `DOSSIER.json`
contains the full base dossier. Evidence fingerprint:
`5e6f1887977db59ed9b4a6f3d940a3d3ac941e20032ae02c4fe8c108c36e07fd`.
Dossier fingerprint:
`370d280e52cb84b9555b2e3321348a89d89c8c3cf83b5c23df8d0dae610425ca`.
Final explicit source/history/compiler revalidation also passed.

This diagnostic packet predates the final batch policy pin and cannot be
applied under the final code. A final v2 attempt was correctly refused after
the real producer reserved EO10014 as `codex-continuous-undecided`; no v2 was
written and no reservation was changed. That producer must prepare its own
fresh packet under its assigned path, using its own agent name. Subsequent
policy or prior-research changes likewise require a new packet version.

After filling one investigation's lifecycle CSVs, use the existing `apply`
command and pass its `applied/decisions/EO_10014.json` to `overlay-propose
--lifecycle-sheet`, together with the exact frozen evidence, producer status
decision and independent status review. `overlay-assemble`, `overlay-check`
and the existing required consumers/review gates still apply. No status or
lifecycle review was supplied by this engineering validation.

## Source coverage

`CASE_COMPARISON.json` preserves the exact main and isolated compiled records
for EO10014, EO10016, EO10030 and actors EO11258, EO11884, EO11485.
`CASE_COMPARISON_SUMMARY.json` gives the compact differences. Their selected
originals, target and actor clause records, own terms, primary acting
provisions, and target-specific chain events agree exactly. The isolated
generation omits 14 APP representation rows across six APP text paths and
one APP alternative acting provision for each target. Shared acting
alternatives agree exactly. The chain's global `generic_refs_excluded` count
falls from 234 to 153. These differences are preserved, not treated as legal
clearance or absent official originals.

For EO10014 the held selected original is
`jobs/fr-originals/data/full_run/texts/EO_10014.txt`, a 5,588-character FR page
including neighboring EO10015. The producer must establish the true operative
boundaries and inspect the source pages. Actor EO11258's full selected text is
held. The dossier still lacks a complete machine later-source search. The
freeze validates exact held text/spans and history pins; this is not a claim
that all required original-PDF custody, legal source adequacy, historical
search or substantive review obligations are complete.

The isolated generation has 24,858 distinct held text artifacts versus
41,564 in the published main generation, 10,674 versus 14,886 orders with
held text, and 9,399 versus 10,962 located actor pairs. It retains 3,403 decided
dossiers and 11,569 undecided status leads. Those counts describe compiler
populations, not validated executable work, production coverage or savings.
No global coverage improvement is claimed. No full rebuild was repeated.

## Validation and costs

Final focused command from `jobs/claim-kit`:

```text
python -B -m unittest test_continuous_route.ContinuousRouteTests test_status_overlay test_batch
```

All 56 tests passed in 2.123 reported seconds. The tests include full ordinary
undecided preparation, unchanged status and approval boundaries, reservation
and changed-input refusal, retained lifecycle analysis without claim emission,
wrong-version transfer, direct policy-change refusal, and the existing overlay
and batch safety suites.

Actual preparation took 4.6909 machine seconds. Its one freeze took 3.179857
seconds and read 401,673,613 compiled bytes across ten shards, selecting two
full texts and validating four text/span files. The final denied reservation
attempt took 0.213900 seconds. Earlier failed test invocation, duplicate
fixture executions, corrected run, and an uncaptured early-yield result are
retained in `VALIDATION.json`; none is deducted from cost. Exact total task
elapsed, active labor, summed agent time, tokens/cache use and dollars remain
unknown. This engineering check establishes no net acceleration.

No commit, publication, canonical claim/status change, hold change or legal
conclusion was made by this subtask. The parent coordinator owns integration
and HANDOFF updates; the research producer owns the now-reserved cases.
