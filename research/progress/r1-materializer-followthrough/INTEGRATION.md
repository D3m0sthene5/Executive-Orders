# R1 integration contract

PR112, branch `sol/r1-materializer-followthrough`; leave unmerged for Root.
Base: `88cef0253ed735b2a6e612770f25f9148641ce93`.
Published engineering/proof source: `9fc12f9e37780ae5831fce6d698139920bf51589`.
Valla certificate digest:
`07fef593187848774aef7e91420a9df75fc2586717a0bebddc58c05c33f7de77`.
Final review pins are in `review/REVIEW.md`; exact individual hashes and machine
receipt hashes will be retained in `SOURCE_PINS.json` and `VALIDATION.json`.

## Interfaces and ownership

R1 changes only existing materialization/freshness code, runner tests, Valla's
declarations, one engineering-certificate file and a read-only proof workflow.
It does not edit Valla, claim-kit, job implementations or `jobs/_lib`.
The new certificate covers **runner job.py → Valla full build**. It does not
certify agent CLIs, the Valla pilot, claim-kit, checker or tracker.

`scope('valla')` adds exact `referenced_files`, `dynamic_complete` and
`implementation_certified` fields to its existing roots/patterns/exclude contract.
Freshness manifest schema remains1; other jobs' scope schema and behavior remain
unchanged. Direct file reads are captured even if ignored; absent targets remain
selectors, and current live membership is rechecked after execution. Existing
same-run producer generation reconciliation and transactional prior-output
preservation remain in place. No scientific gate is bypassed.

The full materializer fallback is retained for unrecognized or changed versions.
For Valla this includes the whole repository, since new code can read outside the
old root families. Unresolved dynamic metadata, parent traversals and symlinks
also use full availability; unresolved scope blocks publication. An ignored
source's presence in a worktree does not establish retained custody or make the
remote branch freshness check pass.

R2's current integration contract asks Root to extend preflight packet pins for
excavate/segment; its helper imports are already covered by existing claim-kit
declarations and remain uncertified here. R3's optional workbench/source inputs
remain explicit and uncertified. R4's optional `kit.py complete` diagnostic route
needs `jobs/neyman/{after_completion,production_receipts,diagnose,survey}.py` and
its explicit history/current/final/attempt/effort/checkpoint/question inputs plus
recursively consumed pins. That agent CLI route is outside this Valla runner
certificate. R4's NMB replay additionally needs its exact ten plan inputs and
source-ladder helper closure. No universal job declaration can substitute for
those invocation-specific selections; claim-kit remains on fallback. Publishing
claim-kit declaration edits alone would dispatch its compiler, outside this
bounded repair's no-broad-rebuild authorization. Root should nominate and audit
that actual selection during integration rather than grant it Valla's result.
No inferred certificate is granted to another session's job. Root owns the final
combined engineering test and any additional declaration requests.

## Certificate regeneration after integration

1. Combine source changes in an isolated branch. Preserve other sessions' source,
   research and exact reviews. Commit the source/declaration tree first.
2. Run the focused fixture and original freshness/materializer suites below.
3. Inspect `result_freshness.VALLA_CERTIFICATE_ROOTS`: the entire Valla job
   excluding output, `_lib`, materializer, freshness, runner.py/sh and run-jobs
   workflow are all bound. New imports or entrypoint behavior require a new read
   audit before granting the digest. Do not regenerate solely to silence fallback.
4. Compute `result_freshness.valla_signature()` from the **committed** combined
   source and replace only the `valla` value in the existing certificate JSON.
   Commit that file. `valla_certified()` must return true in a clean checkout,
   and `fallback_jobs(['valla'])` must be empty on supported current metadata.
5. Re-run the native same-pin comparison and obtain independent exact-byte
   engineering review. If any closure member changes afterward, re-establish
   the certificate and affected verification. Notes/output-only commits do not
   change the implementation closure.

Example calculation, from repository root:

```sh
python -c 'import sys; sys.path.insert(0,".github/scripts"); import result_freshness as f; print(f.valla_signature()); print(f.valla_certified())'
```

## Tests and production comparison

```sh
python -m unittest discover -s .github/scripts -p 'test_valla_materialization.py' -v
python -m unittest discover -s .github/scripts -p 'test_materialize_job_inputs.py' -v
python -m unittest discover -s .github/scripts -p 'test_result_freshness.py' -v
python -m unittest discover -s jobs/valla -p 'test_*.py' -v
python .github/scripts/test_roads.py
```

The focused suite is also wired into the ordinary Linux/Windows road entrypoint.
It exercises valid native method and historical component review branches,
exact INDEX/SUMMARY equality, changed/added/deleted/missing/ignored inputs,
late provider discovery, package sheets, current-run output generations,
certificate changes, symlinks and actual failed-run prior-output preservation.

`run_production_comparison.py <receipt-dir>` requires an ordinary checkout able
to acquire the baseline's complete retained broad inputs. It prewarms that
availability once, then uses the same source pin, absolute worktree path, prior
outputs, fully warmed local Git objects and empty job caches for both arms.
The arms run the actual transactional Valla runner and freshness guard; there is
no publisher, scientific write or corpus rebuild. Exact INDEX, SUMMARY,
RUNNER_INPUTS, relevant input map and prior generation equality are required.
No locally available projection can substitute for this result.

Startup includes the common relevant-input verification; metadata subprocess
work is reported separately. The old broad arm does no selective-materializer
audit merely to fill a receipt. Native execution, full materialized worktree,
construction/acquisition and total verification time are separate. Both measured
arms have no remote and require already-local objects, so their remote transfer
is0 by construction. Construction's host network delta is sent+received bytes
across host interfaces, not exact Git pack bytes or avoidable network transfer.
Initial Actions bootstrap and remote CI overhead are separately visible in run
steps. A cold selective network saving remains unmeasured.

The dedicated R1 workflow is read-only, bounded to30minutes and the R1 branch.
Review its final source pin and receipt before treating the production proof as
complete. It is a reproducibility harness around the existing runner.
