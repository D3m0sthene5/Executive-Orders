# Lifecycle assurance: exhaustion credit repaired

The frozen pipeline allowed exhaustion records to advertise ready dossiers without an adopted status or the required gap disclosure. This branch repairs those tracker transitions and preserves legitimate exhaustion and unchanged complete claims. No canonical claims, statuses, census rows, scientific decisions or output generations changed. No PR is merged.

## Reproduced failures and controls

`replay.py` reads the retained EO12970 claim and the exact Federal Register PDF (SHA256 `9997afba89e10f60d9e2364d8d993bd5f441a9c97f4122d506a0414ff9b7e159`), both extracted text copies and the frozen source registry. It runs the actual checker CLI, then the baseline and repaired `tracker.build` against isolated copies. All claim mutations and invented exhaustion assertions remain engineering fixtures. The retained endpoint/rationale is not independently adjudicated here.

| Isolated version | Baseline ready | Repaired ready | Meaning |
|---|---|---|---|
| Unchanged retained claim | yes | yes, complete_claim | Legitimate mechanical control preserved |
| Missing savings, exhaustion, no disclosed claim gap | yes | no | Required disclosure enforced |
| Missing savings with disclosed gap and eligible route strings | yes | yes, machine_exhausted | Permitted exception preserved; no historical search established by fixture |
| Same disclosed gap, explicit WEAK ladder note | yes | no | Existing ladder exclusion enforced |
| Same disclosed gap, searched:[null] | yes | no | Malformed witness rejected |
| Status removed, provisional_status exhausted | yes | no | Exhaustion cannot substitute for adoption |
| No claim, four exhausted evidence roles | yes | no | No claim means no required gap disclosure |

Exact version hashes, checker receipts, input hashes, rows and logs are in `validation/native/RESULTS.json` and per-case directories. `review/native-independent/` contains the separate strong reviewer's fresh replay. These are seven tests of one source-backed order, not seven newly researched orders or production readiness losses. Canonical EXHAUSTED.jsonl is empty on this baseline; this change has no known existing exhaustion rows to migrate and claims no change to the published ready total.

`jobs/readiness-tracker/tracker.py` now permits the seven policy-listed research steps only, rejects non-object/blank/non-string route records and explicit disallowed ladder evidence, and requires a real nonblank claim gap disclosure before granting exhaustion credit. The exact-version source-hold and working-text routes are unchanged. `test_tracker.py` adds nine regressions, including 512 exhaustion subset cases. All 45 tracker tests and all 50 checker tests pass locally. The independent review seal records its own executions and exact hashes; separate green branches do not establish PR103/104 combined compatibility.

## Findings outside the repair

- Inventory omission and unsupported event inference can pass the tested assembler/checker/tracker chain. The separate lifecycle worker demonstrates this with synthetic held text. These checks are structural and deliberately rely on substantive source review. This finding does not establish any current production claim is wrong. See `lifecycle/`.
- A genuine source record wrongly mapped to an identity can make attribution circular. The discovery probe tests that assumption; historical source-boundary audits document similar past errors, while current known-case parser regressions exist. No current real misbinding is asserted, and a foreign EO mention in a multi-order volume is insufficient for rejection. See `discovery/`.
- A control review with an unrelated scope can count as caught at the completion gate. Its consumer fixture stubs checker/tracker; this is a local control-contract reproduction, not end-to-end filing. The scope expectation is under-specified. Exact reproduction and a focused recommendation go to Opus, without editing its completion implementation. See `transitions/` and `OWNER_HANDOFFS.md`.
- Changed-claim source holds deliberately become stale warnings; inheriting an old hold would change current policy. Current exact holds remain blocking. Tracker's ready count is mechanical and does not reconstruct all independent AI review provenance or transitive receipt generations. Publication discipline, truthful source attribution, reviewer independence and actual source examination remain trusted.
- The admitted denominator is 14,972 at this pin. Candidate discoveries remain separate. No claim that the historical EO census is complete follows from readiness coverage.

The concise code/obligation map, explicit invariants, permitted exceptions and trusted assumptions are in `MAP.md`. No Lean proof is claimed: the proposed bounded guards are clearer in the executable branch checks, exhaustive finite regression and native differential replay.

## Reproduction and costs

From repository root:

```bash
python3 -m unittest discover -s jobs/readiness-tracker -p 'test_tracker.py'
python3 -m unittest discover -s jobs/claim-checker -p 'test_*.py'
python3 research/progress/lifecycle-assurance/replay.py --out /tmp/eo-assurance-native
python3 research/progress/lifecycle-assurance/lifecycle/probe.py
python3 research/progress/lifecycle-assurance/discovery/repro.py
python3 research/progress/lifecycle-assurance/transitions/probe_exhaustion.py
python3 research/progress/lifecycle-assurance/transitions/probe_control_scope.py
python3 -I jobs/kean/kean.py check --strict
```

Sparse inputs required by the native replay are listed by `replay.py:input_paths`; hydrate the held EO12970 PDF and both exact text paths, the listed census/status/queue/custody CSVs, canonical claim file, source-hold registry and Stage19 gate code. The frozen source registry is read via `git show` at the baseline pin. Keep outputs isolated. No network source search or heavyweight corpus job was dispatched.

Delegation used three fresh-context `gpt-6-luna` workers for bounded tracing/probes and one fresh-context `gpt-6-astra` engineering challenger. The coordinator retained integration and legal/policy interpretation. Actual token counts, billed cost and complete labor occupancy are unavailable; measured partial worker intervals are retained with their limits in the worker reports. Code timing is not model labor. No savings estimate is inferred. The repair should prevent malformed/undisclosed exceptions from reaching downstream human review; avoided rework has not been measured.
