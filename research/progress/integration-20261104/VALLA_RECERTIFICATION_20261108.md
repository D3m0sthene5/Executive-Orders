# Valla materialization certificate: re-certified after the schema v2 fix (2026-11-08)

This follows the procedure in `VALLA_CERTIFICATE.md` (same folder). The certificate on main
(`e9574c5f…`, reader `2651564b…`) matched commit 11fd9f42e2. Fourteen later commits on main changed
files in `VALLA_CERTIFICATE_ROOTS` (Kean F-20261109-valla-certificate-stale-on-main). Separately, Valla
had failed every run since 2026-11-06 for a reason the certificate does not cover. That was fixed first,
and the certificate was then recomputed over the fixed tree.

## The blocker: Valla refused canonical schema v2 claims

Failed attempts `jobs/_attempts/valla/42282006697-1` and `42517712260-1` stop in `active_claims`
(`valla.py:110`) with `nonproduction claim in canonical claims:
research/readiness/claims/justinian-2026-11-06-r3-retag.jsonl`. That file holds 184 claims, all
`eo-lifecycle-claim/v2`. No other canonical file has a v2 line (1,644 v1 lines in 163 other files).
`production_claim` accepted only v1.

**Judgment: the file belongs in the canonical claims; Valla's check was too strict.**

- Schema v2 is canonical by owner ruling R2 (Kean D-20261106-justinian-r2;
  `research/stage19/CLAIM_SCHEMA.md`, "Schema v2"). `claim_gate.validate_claim` accepts v1 and v2, and the
  tracker counts v2 claims (`tracker.py:749`).
- The re-tag file applies owner ruling R3. It came in as a COUNT-CHANGING change that the owner merged
  (#174, merge f1a0cdfddc: ready 1,368 -> 1,196). Moving or re-labelling it would undo that merged count
  change and the R3 statuses. Neither may be changed here.
- The file supersedes earlier claims only by the existing later-file-wins rule. The v1 lines it
  re-tags stay in place, so Valla's `claim_versions` history keeps both versions.
- Valla reads claims generically (JSON pointers, `source` objects, rationale fields). Nothing in it
  depends on v1's free `date`/`mechanism`, so v2's `date_kind`, `first_cause` and `formal_disposition` need
  no other change.

Fix (commit bcacec8282): `CLAIM_SCHEMAS = ('eo-lifecycle-claim/v1', 'eo-lifecycle-claim/v2')`, and
`production_claim` accepts exactly those. The seeded/synthetic and `EO:` guards are unchanged.

New tests in `jobs/valla/test_valla.py::ClaimSchemaTests`:
- a v2 winner is accepted and its v1 line stays in history; a seeded v2 claim or a v3 claim is still refused;
- `CLAIM_SCHEMAS` equals the set of `SCHEMA_V*` constants in `claim_gate.py`, so a future v3 fails this test
  instead of a production run;
- every real canonical claim loads.

All three fail on the old code; all 40 Valla tests pass on the fix. A full local `job.py` build over the
checkout exits 0 with 1,530 active claims (the last published run, 2026-10-31, had 1,445).

## Audit of the commits since 11fd9f42e2 that touched the certificate scope

`git log 11fd9f42e2..HEAD -- <VALLA_CERTIFICATE_ROOTS>`:

| Commit | Files in scope | Effect on Valla |
|---|---|---|
| 4c0e6ee970 writer queue | run-jobs.yml | Concurrency group and checkout ref for writers. Runs `run_jobs.sh` with `GITHUB_SHA` = actual checkout. Valla's inputs are unchanged. |
| 70dfd46330 paid web search | `_lib/eo_websearch.py` (+test) | Valla imports no `_lib` module. No effect. |
| fd403d5b60 Niebuhr leads | `_lib/eo_identity.py` | Not imported by Valla. No effect. |
| d9c1e618f5 Arsenale stations | run-jobs.yml | Jobs run in parallel stations. Each station has the same sparse checkout as before (`/*`, `!/*/`, `/.github/**`, `/HANDOFF/**`, `/jobs/**`, `!/jobs/*/output/**`), then the same `materialize_job_inputs.py` step. The plan, bundle, collect and verdict steps call `arsenale.py`, and the run step checks HEAD = the planned input commit. |
| eefe30ad1e merge | — | Clean merge (no in-scope file differs from both parents). |
| 450e3140ce freshness scopes | `result_freshness.py` | Adds `library_closure`, `runner_scripts` and `referenced_roots`. `scope()` skips all three for `valla` (whole `jobs/_lib`, whole `.github/scripts`, `needs.txt` roots), as it did before. `literal_prefixes` and `select` are rewritten into equivalent forms (ancestor-set lookup in place of `under()` scans). The `daily-digest` pattern change does not touch Valla. `valla_references`, `valla_direct_reads`, `valla_linked_inputs`, `tree`, `working` and `capture` are byte-identical in the AST. |
| f61b47f3c6 generation id | run_jobs.py | Adds `JOB_GENERATION_ID` to the job environment and STATUS.json. Valla does not read it. |
| b4eb36815e merge | — | Clean merge. |
| dc8853d44e Pergamon store | `_lib/byte_budget.py`, `_lib/pergamon_store.py` (+tests) | New modules, not imported by Valla. They do enter the fallback-reader digest (whole `jobs/_lib`). |
| 9053141094 attempt receipts | run_jobs.py | `trim_attempt` moves large files out of a failed attempt after the run. Inputs are unchanged. |
| f50600dbbd runner secrets | run-jobs.yml | Passes two secrets in the environment. Valla reads neither. |
| 5b2c4a9c71 Pergamon tests | `_lib/test_pergamon_store.py` | Test only. |
| 5a3aa05f3d merge | — | Clean merge. |
| d77882a349 Riquet segments | run-jobs.yml | `continuation`/`deferred` plan inputs. The planner checkout keeps credentials for non-diagnostic runs. The execute checkout is unchanged. |
| bcacec8282 (this fix) | `jobs/valla/valla.py`, `test_valla.py` | Schema set only. No new file, path field, glob or pointer is read. |

`materialize_job_inputs.py` and `run_jobs.sh` did not change.

**Read closure check.** `result_freshness.py` from 11fd9f42e2 and from HEAD were each run on HEAD's data
(scratch script; the one git call that breaks the Windows command-line limit, `valla_linked_inputs`, was
replaced in both copies by a recorder, and its argument was identical in both). Both routes give the same
result. Certified route: same `scope('valla')` and the same 779 selected files (717 roots, 713 referenced
files, `dynamic_complete` true). Uncertified fallback route: same scope and the same 194,229 files.
Valla's read closure is unchanged.

## Certificates

Set in `.github/scripts/materialization_certificates.json`:

- `valla` = `valla_signature('HEAD')` = `6c931c2c9fc7377606e4ff1b13b214f4a2e16f6f263736654291277bbe0ef18b`
- `valla_fallback_reader` = `digest(tree('HEAD', valla_reader_scope()))` =
  `7daf3916a2b68bd740f3b17b101ecd72259f14d54addd15949b3d5123acc9677`

Neither digest covers the certificate file, this document or the Kean register, so both hold at this PR's
head. `valla_certified()` and `certified_valla_scope('valla_fallback_reader', …)` return true on the
committed tree.

## Left open

- **PR #243 (Ariadne, `claude/ariadne-lean-tree`) was still open when this was written.** It changes
  `result_freshness.py`, `run_jobs.py` and `run-jobs.yml` and adds `.github/scripts/ariadne.py`. Merging
  either PR changes the signature again. Whichever merges second must recompute both certificates (and
  audit `ariadne.py` and #243's freshness changes) on the merged tree.
- `run-jobs.yml` now calls `arsenale.py`, `pick_jobs.py`, `commit_results.sh` and
  `output_branch_check.py`, all outside `VALLA_CERTIFICATE_ROOTS`. They plan, bundle and publish rather
  than read Valla's inputs, so this audit leaves the roots unchanged. A change to how a station chooses
  its checkout would still bypass the certificate, and that boundary is the owner's to set.

## Addendum (2026-11-09): recomputed after merging main into the PR

The first certificate above (`6c931c2c…`/`7daf3916…`) was proved in production before main was merged.
Run-jobs run 42564703293 on the PR head c156ee1b0b took the certified narrow route
(`implementation_certified` true, 779 inputs, 717 roots, 713 referenced files). Valla **succeeded** with
1,530 active claims, its first success since 2026-11-06.

Main then gained two in-scope changes. Merge 31f74e676c brought them in:

| Commits on main | File | Effect on Valla |
|---|---|---|
| 1383cf4929 Rattle Watch audit; d5ae9fb838, a8458bac06 Quo Warranto | `.github/scripts/run_jobs.py` | Stall detection by the job's own I/O; stops processes left holding a finished job's output; adds the `rattle_watch` and `job_verdict` fields to STATUS. A job with `jobs/<name>/AUDIT_READS` runs under `read_audit.py`; Valla has none, so it runs as `python job.py` as before. No input change. |
| 18a26013e3, 7a71bb2c4e fetch_pool robots wildcards | `jobs/_lib/fetch_pool.py` (+test) | Not imported by Valla. It enters only the reader digest. |

`result_freshness.py`, `materialize_job_inputs.py`, `run_jobs.sh`, `run-jobs.yml` and `jobs/valla` did not
change on main. On the merged tree, `scope('valla')` selects 781 files. The two files added since
run 42564703293's 779 inputs are `.github/scripts/read_audit.py` and its test. They come in through the whole
`.github/scripts` freshness root that `scope()` keeps for Valla; Valla's own reads are unchanged.

Certificates at the merged head:

- `valla` = `00d6fd73b71d4ed1cee996eb000acb6222c6dc7ad79ea6d90fc9c5541576c18f`
- `valla_fallback_reader` = `372c6ce6b221a3b2617c7823749b153267da6f62feb2dd99e98ab33c5dc796b5`

PR #243 was still open at this merge, so the merge-order note above still applies.
