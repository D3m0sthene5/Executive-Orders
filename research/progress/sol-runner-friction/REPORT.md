# Sol runner friction repairs

The branch repairs scoped freshness enumeration, avoids initial output checkout before job selection, skips cache restore on empty selection, and adds cache-I/O attribution. Independent review restricted selective output materialization to two exact audited job versions; other jobs retain historical availability through an explicit compatibility fallback. No claim, status, census, source grade, reviewer requirement, or canonical generation is published by this work.

Baseline main is `f9c6d806ad059dcad7875ab3708715f20ea386df`. PR102's audit and the two subsequent Kean/documentation commits were inspected. The working branch is `sol/runner-friction`; the separate checkout has its own Git index. An unrelated checkout-created CRLF diff in `jobs/hathi-gpo-orders/data/TARGETS.json` is excluded. No Opus-owned code is changed.

## Measured results and limits

| Cost | Evidence | Result |
|---|---|---|
| Materialization | Isolated same-pin runner fixture | 2,310,540 to 213,388 bytes; all required hashes equal; failure preserves prior success. Local elapsed 0.0099 to 0.0618 seconds, so no startup-time saving established. |
| Freshness metadata | Five actual job scopes at pinned baseline | Exact selected entries/hashes equal for all. FR originals candidates 97,160 to 13,665; local tree time 273.8 to 25.9 ms. |
| Broad declarations | Claim-kit/digest metadata comparisons | Candidates remain 94,286/80,592; modest measured benefit. No dependency narrowing in these jobs. |
| Remote transfer | No instrumented cold remote comparison | Bytes and avoidable portion of audit's 180 seconds remain unmeasured. |
| Download cache | Two exact local payloads requested twice | Both versions: 12,288 successful payload bytes, two hits, 12,288 persistent reread/checksum bytes. Instrumentation only; no production saving. |
| Context/cost | Retained NRA COSTS.json + bounded workers | NRA coordinator 267 calls, 113,985,255 cache-read tokens; avoidable fraction unknown. Current token/cash telemetry unavailable. |

Freshness now uses conservative literal directory prefixes, then the unchanged fnmatch selection semantics. Capture scopes its baseline output tree; publication loads a union of required scopes/output baselines once per check. Working index scans remain live, detecting modified/deleted/staged/untracked inputs and stage conflicts. The existing same-run/later-producer baseline and concurrent output guards remain. Broad wildcard declarations still require broad traversal. Receipts distinguish returned metadata entries/bytes from physical disk reads or remote bytes.

## Safety correction from independent review

The first minimal-code checkout proposal was rejected: existing dynamic reads exceed manifests. The final bootstrap keeps all job code/data; only `example-hello` and `early-ranger-transcriptions` at exact audited fingerprints narrow outputs. Unknown/changed/mixed selections restore every job output and report the fallback. The fixture verifies this actual sparse operation, not just a proposed path set. This is a bounded repair, with incomplete declarations explicitly limiting production-wide benefit.

The proposed invocation-memory body reuse was discarded: a tiny synthetic gain and no production repeat frequency did not justify memory/mutation complexity. SHA-256 verification, exact URL metadata, resume, robots, offline behavior and prior-success reuse remain. Cache stats count persistent validation reads/bytes, successful payload bytes, requests, hits and cold/missing/invalid causes. Payload bytes exclude robots/redirect/error bodies. Default-branch cache restoration is deferred; mutable URL captures must not be called current content merely because bytes validate.

## H12, H15 and H16 operations

Use a fresh bounded worker per phase; pass base commit, exact file hashes, owned paths, deliverable, acceptance cases and unresolved exceptions. Return paths/hashes/outcomes rather than a corpus recap. This assignment exercised three fresh `gpt-6-luna` workers and a fresh independent `gpt-6.1-sol` engineering reviewer. Models are actual assigned identifiers; no comparative price or current token-saving estimate is available. Workers' reports retain available markers; elapsed occupancy includes waits and is not exclusive labor. Briefing, initial review rejection, correction review, failed local setup and integration all belong to this assignment's cost; they are not omitted from an asserted saving because no total saving is asserted.

Before scientific review launch, use the existing packet view/check entrypoints, verify the exact producer agent/version and artifact hashes, and copy only the frozen reviewer-accessible artifacts. Keep private control keys outside that directory and every reviewer mount; never put keys in the handoff. On mismatch, stop before launch and preserve the attempt. No scientific review rule is altered. Those launch paths are Opus-owned, so no new preflight platform is added here.

Scratch directories were separated by worker under `/workspace/scratch/97820cf3b00d/`. Wait on a retained execution session ID or Actions run ID. Never kill or poll by a matching process name. A worker nevertheless killed an unidentified test PID; its report preserves the error and uncertainty. Root stopped a looping own test through its exact unified session after bounded whitespace escaping was repaired. Root also produced unnecessarily broad startup tool/status output, and first ran road tests without an existing sparse code dependency. Those are retained limitations of this session, not evidence of token savings.

## Reproduction and validation

- `python3 .github/scripts/test_roads.py` — normal offline Linux/Windows CI entrypoint, now includes materialization regressions.
- `python3 research/progress/sol-runner-friction/checkout/run_fixture.py` — actual helper, checksum equality, induced failure and broad fallback in temporary clones.
- `python3 research/progress/sol-runner-friction/freshness/compare_metadata.py` — five pinned full/scoped tree equivalence comparisons, no corpus build.
- `python3 research/progress/sol-runner-friction/cache-ops/benchmark_fetch_pool.py` — loopback transport comparison; no public acquisition.
- `python3 -I jobs/kean/kean.py check --strict` — register/brief validation.

Final local/remote checks and exact review pins are retained in `validation/`, `REVIEW_INPUTS.json`, and `review/`. Initial review failures and corrections are preserved. No full-corpus build is dispatched. Ordinary branch PR CI is sufficient; avoid duplicate heavyweight workflow dispatches.

## Opus handoff and adoption checks

Opus should continue its separate claim-kit/Valla work. This branch changes no implementation there. Before combining, preserve both append-only Kean additions (Sol F-20261029-8001 and Opus 7001–7099), regenerate the brief, and test the combined source at one exact commit. Run road tests on both OSes, Kean strict, Opus's packet/publication regressions, PR101 reviewer-card/frozen-baseline checks, and the isolated materializer fallback/failure fixture. Recheck actual declared scopes for any proposed additional narrow-job certificate; in particular audit checker/provider capture discovery, claim-draft dynamic outputs and source-ladder wrapper inputs. Do not infer combined compatibility from two separately green branches, and do not merge either PR without the requested adoption step.
