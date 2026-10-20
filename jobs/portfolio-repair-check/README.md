# Bounded portfolio repair validation

This output-only job runs the concrete regression suites for Panizzi, Rastell,
Lamm, Hamilton, Mountweazel, Polya, Llull, Junto and Lambertini. Rastell and Lamm
share the existing claim-kit implementation. Synthetic test fixtures use a
cleaned-up runner/OS temporary directory outside the checkout, including when
the inherited `TMPDIR` points into the job output. This preserves the production
guards that reject synthetic data inside the repository. Durable test logs and
receipts remain under `OUTPUT_DIR`; tests do not run a paid research campaign.

It loads the seven-case repair packet through `claim-kit/batch.load_packet`,
verifies its held source hashes and original isolated dossier hashes, and
selects the current effective canonical claims for EOs 13792, 13101, 13148,
13783, 13807 and the positive control EO 13037. The actual claim checker runs
on these six copies. All six must pass every mechanical and structural gate
check; merely completing without an exception does not pass validation.
An active legal-premise audit hold remains a separate reason to withhold
readiness even when those mechanical checks pass.

`verification_sources.json` freezes the ten already cited GovInfo SHA256/URL
pairs. The selected claims must still reference exactly that set. Before
checking, matching bytes from the existing claim-checker cache are copied
and re-hashed under `OUTPUT_DIR`. Only on GitHub, unavailable bytes receive
one attempt each through the existing `claim-checker.verify_by_download`:
at most ten initial URLs, no retries, its existing HTTPS GovInfo restriction,
120-second timeout per open and at least one second between attempts. A thin
read guard tightens its response limit to 5,000,000 bytes plus one byte for
oversize detection; oversized documents fail explicitly. The declared
aggregate response read cap is 50,000,010 bytes; the timeout is not a
wall-clock deadline. No new sources are searched for or added to the research
corpus through this step. The budget becomes zero and
network access is blocked before the actual six-claim scan. Checker files
and all copied/downloaded bytes stay under this job's `OUTPUT_DIR`.

`SOURCE_VERIFICATION.json` records cache reuse, attempts, bytes returned,
actual transport errors, hash mismatches and unavailable sources. Failed
or partial reads with unknown byte counts remain explicit.
`CHECKER_ACCEPTANCE.json` lists all six outcomes and fails on missing,
unverified or failed checks, including the positive control. Raw checker
outputs remain available for diagnosis.

The five AI source audits are verified against the manifest, effective claim
hashes, review bytes and the existing tracker's active-hold loader. Each must
appear in the current tracker with its exact `OPEN_SOURCE_AUDIT` marker,
counterevidence open and readiness withheld. EO 13037's result is observed,
not hard-coded. EO 11513 remains a no-claim source-blocked control. No total
readiness count is a test expectation.

It also replays the actual Lambertini `continue` command against the saved
historical one-plant observation. The command must exit 5 as `untested` before
selecting a batch. This is an execution regression using a reconstructed
historical contract, not a new prospective experiment.

`VALIDATION.json` records source, packet, canonical claim, AI review/hold,
mechanical checker and integrated tracker stages, with consumed-file hashes.
It records no newly created claim, established legal ending or independent
human certification. These stages overlap and cannot be added together.
Python network calls in the parent and regression workers are blocked;
configured tests use existing fake transports. Local checker runs are also
offline, and fail honestly when the saved catalogs or verified bytes are
unavailable. The bounded GitHub verification phase is the only exception.
No model calls are made, and
deterministic test success is not evidence of token savings.

## Running

Use the ordinary job runner. `after.txt` puts this check after its relevant
producers when selected; the repository's consumer scheduling includes it
when those producers run. This ordering does not automatically select upstream
jobs. For GitHub validation, the readiness tracker must have succeeded and its
`RUNNER_INPUTS.json` must have a valid schema, job, self-digest, current scope,
and base commit matching its successful status. The existing runner freshness
functions compare every captured tracker input against the current working
bytes, including generated or modified files not yet committed to Git. This
check applies even when tracker and validation share an execution commit.

An older successful tracker is reusable only with identical declared inputs;
`VALIDATION.json` records `same_execution` or `reused_identical_inputs`, the two
input digests and execution commits. Its manifest and tracker CSV are pinned.
Missing or changed provenance fails with an explicit instruction to rerun the
tracker. A validator-only invocation can therefore reuse unchanged evidence
without forcing an unrelated tracker run. The runner alone owns `STATUS.json`
and `RUNNER_INPUTS.json`.

For a local validation after refreshing the tracker:

```sh
REPO_ROOT="$PWD" OUTPUT_DIR="$PWD/jobs/portfolio-repair-check/output" \
  PYTHONDONTWRITEBYTECODE=1 python3 jobs/portfolio-repair-check/job.py
```

The job never overwrites upstream outputs, source-audit records or canonical
claims. A changed claim, review, packet or input during validation fails the
check and preserves its observations for diagnosis. Saved source coverage
and unresolved legal questions remain visible in the actual checker and
tracker records, including failures.
