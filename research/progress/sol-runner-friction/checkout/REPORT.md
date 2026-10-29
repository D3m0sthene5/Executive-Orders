# Runner checkout repair and bounded rollout

Baseline: `f9c6d806ad059dcad7875ab3708715f20ea386df`, after audit PR102 and the subsequent documentation/Kean commits.

The workflow initially checks out job code/data with direct output generations excluded. It chooses jobs before restoring `.job-cache`, so an empty selection does no cache restore. The materializer then supplies declared roots, fnmatch-selected inputs, predecessors, and each selected job's complete previous output/custody. Literal roots use compact subtree rules. Size accounting uses files after materialization; no `ls-tree -l` or object-existence probe fetches blobs for measurement.

Independent review rejected universal selective rollout. `family-rule-tail` executes source-ladder code whose siblings were absent from the first minimal bootstrap. Source-ladder assumes FR index data is present. Claim-checker scans provider `SOURCES.jsonl`/capture records absent from its declarations; claim-drafts enumerates arbitrary provider outputs. All job code/data is therefore preserved initially. Only engineering-reviewed exact versions of `example-hello` and `early-ranger-transcriptions` use selective output materialization. An unaudited job, a mixed selection containing one, or any change in an audited job's nonoutput files/shared library triggers `/jobs/**` compatibility materialization. Every reason is in `compatibility_fallback_jobs`; fallback output bytes are included in the receipt. This keeps broader deployment safe while incomplete declarations are repaired.

The two embedded fingerprints bind each audited job's nonoutput tree and all `jobs/_lib` files, using tracked modes/object IDs. Own output changes do not expire the certificate. A code/declaration/library change expires it automatically. These are engineering read-closure certificates, with no scientific approval meaning.

## Final isolated fixture

`python3 research/progress/sol-runner-friction/checkout/run_fixture.py` builds isolated local clones, copies the final actual runner/helper, and reads the actual workflow sparse rules. It explicitly certificates a synthetic consumer at its own pinned fixture version. This is separate from the two production signatures. It checks every required SHA-256, runs an induced failure, then invokes the actual helper for an unaudited job and verifies broad outputs return.

| Case | Files | Materialized bytes | Local elapsed |
|---|---:|---:|---:|
| Original cone checkout | 37 | 2,311,073 | 0.0126 s |
| Output-excluding bootstrap | 32 | 213,758 | 0.0100 s |
| Final narrow checkout, excluding receipt | 36 | 213,921 | 0.0644 s including helper |

All 32 selected file hashes match. The unrelated 2 MiB output is absent in narrow mode. The induced failure retains its candidate attempt and the prior successful output/status. Unknown-job fallback restores that same omitted output. These local clones share available Git objects: remote transfer bytes and production startup time are unmeasured. Local selective expansion is slower in this fixture despite reducing bytes; no 180-second production reduction is claimed.

`test_materialize_job_inputs.py` also verifies actual repository tree closure for the two job shapes, mixed selection includes `fr-pages/SOURCES.jsonl` and APP mirror captures, and version changes trigger fallback. The materializer does not execute unselected jobs.

## H09

Full history remains. New-branch selection requires a merge base, sweeps inspect first-parent time history, publication checks resolve captured base commits, and reconciliation rebases against branch history. A smaller verified ancestry closure was not established. PR101's explicit frozen comparison fetch remains untouched.

The final fixture also verifies `implicit_root_file_preserved=true`: standard `/*` then `!/*/` bootstrap rules retain the root files that cone mode included implicitly. Later positive subtree rules restore the named folders. LFS smudge remains disabled.
