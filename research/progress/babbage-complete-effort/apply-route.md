# Ordinary apply/check route: retained evidence and limits

Inspected main `a3bfac64b3e1c43400a8ed8c744419eb17f6e2e6`, PR140 head
`0049d79d24694ef39581aa7a974111ffba9b1c83`, and exact retained Tribonian state
`2bc32c6d4ea87abf969c406dd4049dc3dddcc3c7`. No code, packet, review, branch
or scientific output was changed. Worker is an inherited OpenAI Codex context;
exact serving model, token usage, cash and complete active labor are unavailable.
This is engineering/process analysis, not independent legal review.

## What the long-interval claim actually supports

The exact warning is in
`research/excavator/claude-tribonian-2026-11-04/tools/prompts/producer.txt`:
apply and batch-check can take 10–30 minutes on the busy machine. This is an
assignment instruction, not a measured run.

The a01 producer reports four slow applies of up to 25 minutes, attributed to
load. Its five successful retained apply summaries instead record:

| Retained attempt | Apply wall seconds |
|---|---:|
| a01 applied-v1 |63.0797|
| a01 applied-v2 |117.2805|
| a01 applied-v3 |102.4144|
| a01 applied-v5 |90.3549|
| a01 applied-v6 |78.2345|

a01 applied-v4 is described as empty/abandoned; its SUMMARY.json returns404.
Thus a potentially expensive unsuccessful interval lacks its exact duration
and process record. The report's attribution to load is not an instrumented
causal diagnosis. No 10–30 minute apply is reproduced by these records.

Other actual apply summaries: o01/v3 309.9942 s for 27 proposals / 30 members;
o25/v1 241.1901 s for zero proposals / 30 blocked members; a03/v3 100.5547 s for 12
proposals / 33 members; c02/v3 19.2573 s for 28 proposals / 34 members; c03/v2 47.2741 s
for 30 proposals / 34 members. All identify batch code SHA256
`9f628cb4b55eb0f2219d0e7410ccb44d4c8381100de7163f64fbca5cae143b3d`.
Different inputs, timestamps and concurrent load prevent a matched speed claim.

a03 completion-v1 is a genuine failure:135.0397 s complete wall, checker92.2942 s
with return code -9. Completion-v2 took167.9890 s, checker50.8014 s, return code 0.
The coordinator report attributes the first failure to OOM and dmesg; the
retained RUN.json establishes the kill and timing, not independently its cause.
These are completion invocations, not producer apply timings.

PR140's ~11 second ordinary checker used two already-filed claims and a sparse
source context. Its archived root sheets assembled zero proposals. It did not
reproduce the submitted-row apply route or a historical completion. Preserve
the 6.2% memory result without treating it as a long-round explanation.

## Exact ordinary process sequence

The retained producer prompt invokes these from repository root:

```sh
python3 jobs/claim-kit/kit.py apply PACKET --write PACKET/applied-v1
python3 jobs/claim-kit/kit.py batch-check PACKET PACKET/applied-v1
```

`batch.apply` first loads and validates the entire frozen packet, then validates
runtime pins, reads sheets and runs assembly under fragment_cache.policy_index.
load_packet checks held source hashes, working-text confirmations, supplements,
any undecided overlays/factual intervals/history context, Valla and prior
research. Identical inputs and changes retain meaningful refusals. Zero
submitted decisions still incur packet/context validation: o25's241 s is not an
actual-checker cost.

`batch.check` loads/validates the packet again and runs strict assembly checks.
For nonempty claims it launches:

```sh
python -B jobs/claim-checker/checker.py --claims PACKET/applied-vN/CLAIMS.proposed.jsonl
```

Environment: REPO_ROOT=repo, OUTPUT_DIR=applied-vN/actual-checker,
JOB_CACHE_DIR=PACKET/.validation-cache, JOB_LIMIT empty,
CLAIM_CHECKER_VERIFY_DOWNLOADS=0 and PYTHONIOENCODING=utf-8.
Logs are applied-vN/CHECKER.log; native outputs are actual-checker/.
The zero-claim branch ALREADY SKIPS this subprocess. No new zero-claim
checker skipper is justified.

The `kit.py batch-check` caller then invokes `geddes_advisory` automatically,
in-process, after native checking. Geddes errors are retained and advisory
unless strict is explicitly requested. This stage is part of the complete
producer check obligation; timing only the checker subprocess omits it.

Completion separately pins actual SourceIndex dependencies (build_index), then
spawns a fresh actual checker, merges exact results for tracker replay, and
rechecks inputs before publication. Separate pinning and checking have distinct
correctness purposes; their repeated index construction is observable code
behavior but not proven avoidable under the existing contract.

Tribonian `tools/fin.sh` acquires an external `flock` before running
`tools/finish.py`, which builds COMPLETION.json and executes:

```sh
python3 jobs/claim-kit/kit.py complete PACKET/completion/COMPLETION.json --write PACKET/complete-vN --publish
```

That is historical command reconstruction only; this session did not execute
publication. External queue wait precedes complete's internal timer. No exact
queue duration is retained in the inspected receipts.

## A real avoidable task, with an observed failure

The producer prompt additionally asks for manual Geddes lint after batch-check,
while acknowledging batch-check may already have written it. o13's producer
report records a manual lint and automatic batch-check lint writing the same
file concurrently, producing duplicate trailing content in v1. v2 used
batch-check alone and corrected the issue. This is demonstrated duplicated
mechanical work, an extra model-managed command and a failed artifact version.

A narrow improvement is to teach the ordinary producer assignment to consume
batch-check's returned Geddes result and existing lint file; rerun manually
only if the automatic result explicitly failed or following a supported
changed-input resolution. This is small, and current competent practice
already avoids it. Do not present it as the session's consequential saving.

A combined apply/check wrapper alone has no fair task-displacement claim:
competent current practice can chain both commands in one shell invocation
without a model turn between them. Automated wait alone is also already
suggested by the retained prompt. We did not count current polling commands or
prove that models waste many calls waiting; transcripts are private and no
supported sanitized command trace was found in this bounded investigation.

## Smallest observation that would change the runtime decision

Run an actual submitted-row apply followed by ordinary batch-check on the same
fully materialized pinned packet, using existing timing wrappers, and capture
wall/user/system/peakRSS for the outer commands and checker subprocess.
Capture automatic Geddes duration and the explicit concurrency/load setting.
Preserve failed attempts and queue time separately. A short phase trace around
load_packet, provider inventory, prior_research/Valla, strict assembly and
native checking would locate the expensive process without another telemetry
framework. An isolated checker is insufficient.

A prospective comparison must show a disappearing model task or failed
attempt through an identical endpoint. CPU or wall savings alone are not
model-token savings. Retained provider totals cannot price discarded polls.

## Reproduction and boundaries

`retained-route-observations.json` preserves the inspected timing records.
Every referenced state record was fetched at exact 2bc32c6, including the three
a03 records initially read from the live branch (exact content equality
subsequently checked). Reports/commands are at the main pin stated above.
Kean search `python3 -I jobs/kean/kean.py search apply check slow polling process`
found no matches in the available checkout and explicitly warned 1,307 tracked
reports were not checked out; it was not represented as exhaustive history.
The parent coordinator owns consolidated Kean registration.

No whole-corpus runtime, total model savings, new legal finding or quality
equivalence is established by this route audit.

