# R4 bounded producer/consumer trace

Read-only tracing at current tree `88cef0253ed735b2a6e612770f25f9148641ce93` (2026-10-31). No code, canonical evidence, claims, status, adoption or counts were changed. Git metadata was local; absent blobs were read through GitHub fetch_file at that exact pin because lazy Git fetch stalled. Root owns register/handoff integration.

## Preferred retained cohort

Use `research/excavator/counterexample-first-2026-10-26/IMPORT.final.json` (SHA256 `a124e0a17681cd04297520c295f2f9d846a5ecad512986a10a154b90aa9238d1`; original cohort base `1caa42af95705e452d0e02425c7d9ceb9ed5ba7c`). Existing published diagnosis is `research/neyman/production-diagnostics/2026-10-26-counterexample-first/observed-final/DIAGNOSIS.json`.

This explicit ordinary-production history retains six members and all three completion invocations. `complete-v1/TALLY.json` has five eligible proposals and EO8915 blocked. `complete-publish-v2/TALLY.json` retains EO7975A exception “changed prior research; prepare a new version”, four eligible proposals and EO8915 blocked. `packet/continuation-7975a-v2/complete-publish-v1/TALLY.json` is the later successful exact-version retry. Final selection retains five reviewed whole-case proposals plus EO8915 without a selected claim hash; its actual blocked research attempt and independent blocked-research review remain referenced. This is the compact single cohort satisfying success, failure, retry and unfinished membership without synthesizing attempts.

Existing bounded CLI (requires materialized referenced metadata, no original PDF download):
```sh
python -B jobs/neyman/diagnose.py --repo . --manifest research/excavator/counterexample-first-2026-10-26/IMPORT.final.json --out research/neyman/production-diagnostics/r4-counterexample-replay
```

Expected retained summary: six observed orders, three unique invocations, one failed invocation, one blocked research attempt, five reviewed whole-case proposals, two ready in isolated replay. Completion machine seconds are historical invocation timing only; total research/agent hours and savings remain null. No population inference.

Minimum pinned metadata read by the existing published diagnosis:
```json
{
  "research/excavator/counterexample-first-2026-10-26/EFFORT.json": "e53ab8d3679d035cce5429e3bd6c66b71657f56197572462df73180acda89859",
  "research/excavator/counterexample-first-2026-10-26/EO_8915_ATTEMPT.v2.json": "fdb183b6f20890f2ad2832a34af0600e01e3fe28d8cd4a3943f978179435bcf1",
  "research/excavator/counterexample-first-2026-10-26/IMPORT.final.json": "a124e0a17681cd04297520c295f2f9d846a5ecad512986a10a154b90aa9238d1",
  "research/excavator/counterexample-first-2026-10-26/PUBLICATION_EFFORT.json": "7b90baf67ffa2bc538c0f53386e75df183f8f444388d534c5db20800c00a0f94",
  "research/excavator/counterexample-first-2026-10-26/SELECTION.json": "9cdf87854b055dfbf7b552ee3f259549832de154f3184ef6319444c97982ef99",
  "research/excavator/counterexample-first-2026-10-26/complete-publish-v2/CLAIMS.selected.jsonl": "915d682e4bfe81e7e244e73f125f8402b83181f4ef8a88a9e7981acd7e7ea015",
  "research/excavator/counterexample-first-2026-10-26/complete-publish-v2/TALLY.json": "340f91971c16eebaffe30345d9b02ebd58a542f1b293aac6d81c390c5fa3cb19",
  "research/excavator/counterexample-first-2026-10-26/complete-publish-v2/TRACKER_REPLAY.json": "484d3f6135c0578c9e3824d4d3e380eb383abe47d88645595b20082832b49b1f",
  "research/excavator/counterexample-first-2026-10-26/complete-v1/TALLY.json": "a2d7853931ee32b0dc77677d3f89ab6b07edbd8eaf26800b0f0cea531ea1d8cd",
  "research/excavator/counterexample-first-2026-10-26/packet/continuation-7975a-v2/complete-publish-v1/CLAIMS.selected.jsonl": "e0d7244951475404d2115b0e4ae95fc6be6028bf49b8e52a505013b06b0c2c67",
  "research/excavator/counterexample-first-2026-10-26/packet/continuation-7975a-v2/complete-publish-v1/TALLY.json": "a6dc2d8c6acf20ec46377362795963b803eca2a8f4cd572286bc2477c52435a4",
  "research/excavator/counterexample-first-2026-10-26/packet/continuation-7975a-v2/complete-publish-v1/TRACKER_REPLAY.json": "25add13475d9baad0687bf762782624ea77ffaccbc471b62a00d0e6c14510360",
  "research/excavator/counterexample-first-2026-10-26/packet/producers/EO_8915/BLOCKED_CHECKPOINT.v2.json": "680b6a4aae4053dad1761f9191e5b30dad46d37e9dfca3cff21441b94b75cc08",
  "research/excavator/counterexample-first-2026-10-26/packet/review/pair3/BLOCKED_RESEARCH_REVIEW.json": "a8277041673093535c719ca17c4d97a01fb49a6cd92edd787f9cf1cd027896ac"
}
```

Implementation requires `jobs/neyman/diagnose.py`, `production_receipts.py`, `survey.py` and their ordinary Python imports. Reproduction should use current implementation hashes separately from the original historical output hashes.

## Actionable source-ready existing follow-up

The NMB institutional-series retained assignment provides a deterministic existing source-ready follow-up, and three actual unfinished stage-result attempts. It is distinct from the six-member history above; do not silently splice cohorts or call its three facts completed lifecycles.

`research/excavator/nmb-series-2026-10-25/SERIES_PLAN.v2.json` pins the exact original EO text identities and official annual narratives. Ordinary index matching misses target PEB67 for EO10029 and PEB86 for EO10130 because index dates can mean appointments after the EO date. The annual narrative route distinguishes those meanings; EO10117/PEB83 is an existing-route control. The retained pilot has three independently AI-reviewed signed-letter dates (1949-03-10, 1950-04-18, 1950-07-06), with receipt/first cessation/legal effect unresolved.

Run the existing route adapter with a fresh folder:
```sh
python -B jobs/source-ladder/record_series.py --repo . --manifest research/excavator/nmb-series-2026-10-25/SERIES_PLAN.v2.json --out research/excavator/r4-nmb-series-replay
```

Expected: three unreviewed identity leads/request proposals, zero unresolved questions, three explicit oversized case omissions, zero network requests. It writes proposals only; it does not enqueue or re-fetch completed reports. Source-ladder acquisition is separate and not needed for this replay.

Minimum data prerequisites, in addition to the plan and existing source-ladder Python modules:
```json
[
  {
    "path": "jobs/source-ladder/data/nmb-series-20261025/4367cdd6b746fbc114a28fa16a6dc4d5fd37e76d2c9bceee69bfaff68f24b56c.html",
    "sha256": "4367cdd6b746fbc114a28fa16a6dc4d5fd37e76d2c9bceee69bfaff68f24b56c"
  },
  {
    "path": "jobs/source-ladder/data/nmb-series-20261025/b5f4fb7949354d331fedb4ddcece9744eb1299ab03ac463a03feadb0830c54fe.html",
    "sha256": "b5f4fb7949354d331fedb4ddcece9744eb1299ab03ac463a03feadb0830c54fe"
  },
  {
    "path": "jobs/source-ladder/data/nmb-series-20261025/b5f4fb7949354d331fedb4ddcece9744eb1299ab03ac463a03feadb0830c54fe.txt",
    "sha256": "1a4303f59786c7026a11921b5e78dce7e675574699b662d73f7d507ce4476dcb"
  },
  {
    "path": "jobs/source-ladder/data/nmb-series-20261025/5d7e30ee758e4fcc75d5000e02161f9153ba4c32d4dc2160663a25fab634c47b.html",
    "sha256": "5d7e30ee758e4fcc75d5000e02161f9153ba4c32d4dc2160663a25fab634c47b"
  },
  {
    "path": "jobs/source-ladder/data/nmb-series-20261025/5d7e30ee758e4fcc75d5000e02161f9153ba4c32d4dc2160663a25fab634c47b.txt",
    "sha256": "90919e6f8f70a44c3f94007614c3fc7653a43822b1e029932f6b67168387562c"
  },
  {
    "path": "jobs/source-ladder/data/nmb-series-20261025/9962b33170b3718fa847076ba9866defb2e47de28d72e02a73bc1c6c9851e43c.html",
    "sha256": "9962b33170b3718fa847076ba9866defb2e47de28d72e02a73bc1c6c9851e43c"
  },
  {
    "path": "jobs/source-ladder/data/nmb-series-20261025/9962b33170b3718fa847076ba9866defb2e47de28d72e02a73bc1c6c9851e43c.txt",
    "sha256": "8bda0aee88206cff60b604a6fa5e9bb08da26e98042cf9600211d91ec58e7415"
  },
  {
    "path": "jobs/fr-originals/data/full_run/texts/EO_10029.txt",
    "sha256": "2e2f9c13ff34e88e3462a43b1ac23a00926af7e8c5e50be5277aade8b0fb785e"
  },
  {
    "path": "jobs/fr-originals/data/full_run/texts/EO_10117.txt",
    "sha256": "905c2c6589dcbd228da3071c4b549253ff97e6d435d8b0bbb5f5b4d1bb1ea693"
  },
  {
    "path": "jobs/fr-originals/data/full_run/texts/EO_10130.txt",
    "sha256": "437a6e7923060568daba379159cfa57836f013309d86f14bbeaeb71e5bc8f5f2"
  }
]
```

Existing `research/excavator/nmb-series-2026-10-25/verify_pilot.py` also exercises NORTON and claim-kit's factual-event bridge but needs the complete existing NORTON registry/review and retained original-report/page dependencies. Its wider dependencies should not be confused with the ten data inputs needed by record_series alone. `NATIVE_CONSUMER_CHECK.json` records three events as `other_event`, `legal_effect: unresolved`, zero legal claims, no corpus rebuild. Published attempts are `EO_10029_ATTEMPT.json`, `EO_10117_ATTEMPT.json`, `EO_10130_ATTEMPT.json` and bind `NATIVE_CONSUMER_CHECK.json`; their outcomes are `stage_result`, not completed histories.

## Blocked counterexamples

EO8915's actual blocker is the missing earlier Interior notice/land-status return occurrence before PLO1070 (1955-02-11), for Willamette Meridian T18N R27E sections20/22, 1280acres Washington. The selected unfinished member and checkpoint preserve it. A later named revocation is not evidence that this earlier notice condition occurred. The current importer honestly emits requires_scoped_assessment because no selected claim is bound to that checkpoint; open steps alone do not establish a causal bottleneck.

PR60 provides the stronger existing diagnosis of an exact selected partial: `research/neyman/production-diagnostics/2026-10-25-pr60/IMPORT.json`, selected EO10030 claim `b809bdd293634e57a546cb30073099049b3aca530f0e3315f86dcc21af51f6a7`. `b03/packet-v1/SOURCE_BLOCKED_CHECKPOINT.v1.json` SHA256 `07b340203be21e8164825f1ac153f319bed4bff0423eb58cd63615bf9166b974` binds the exact partial and `QUESTION_10030.json` asks which earliest qualifying activation/duty episode triggered paragraph1 and when it ended. Actual missing prerequisites: 1951 call-up/release orders for715th Truck Company, 1961/1962 activation/release orders for113th Wing, and DCNG OPORD2(Joint) of1967-10-15 / Circular350-57(AirCircular9) of1967-10-07 with duty classifications. Both source requests retain empty URL lists and actual no_route outcomes. Existing general history and1968 duty evidence do not supply those dates/classifications. Re-running source-ladder unchanged cannot resolve them and cannot establish exhaustion.

Existing lifecycle checkpoint/resume compares recomputed dossier content, validated requests, route SHA256 and substantive source results; unchanged work defers, changed substantive evidence/route reopens. Native CLI is `jobs/claim-kit/lifecycle_obligations.py resume --dossier ... --requests ... --routes-sha256 ... --checkpoint ... --source-results ... --out <new>`. Do not manufacture updated pins or infer permission/approval from resume eligibility.

## Cost and worker disclosure

## Follow-up correction: NMB replay is validation, not new production progress

Root correctly rejected the NMB route replay as the proposed productive follow-up: it repeats already completed routing. Keep it only as an existing deterministic reproduction example. No new source or real held conclusion is advanced by that replay.

The bounded EO8992/EO6964 inspection establishes a precise existing consumer limitation, rather than a source-ready scientific rescue. At the frozen production assignment, `packet/producers/EO_8992/MEMBER_CONTEXT.json` already holds `ACTOR_TEXT:EO:6964`, the full relevant APP transcription. Its source is raw-page SHA256 `232db8bc27d459d028be2361888d2f1dc1100e1c786620de2eb6ba6aa88f2a69`, via `jobs/clause-drafts/output/texts/cd-job-app-executive-orders-6964-232db8bc27.txt` (text SHA256 `8a4f1f0ebcc1c76827acc0785f7379ceb9795f0f4beabf1c5080106632f9eb77`). The current APP producer `jobs/app-executive-orders/output/SOURCES.jsonl` records that same raw SHA256, `grade: mirror_transcription`, `acceptable_as_original: false`, and `text_sha256: b5cfe2b37730ac7ed306c84d074ce009d78432d69a279793690273c00e1a2bd1` at `texts/executive-order-6964-withdrawal-for-classification-all-public-land-certain-states.live.txt`. Its notes expressly say raw HTML was hashed but not committed. The historical dossier prepended the title; the current producer text does not. These are separate exact representations, not evidence that the source newly appeared after the held assignment.

`jobs/readiness-tracker/tracker.py` checks shared authorities against only (a) Stage20 `source_already_retrieved`, (b) acquired statute pairs, or (c) source-ladder `wanted_id` strings. The APP registry has no `wanted_id`. Thus `SHARED_SOURCE_NOT_RETRIEVED:EO::6964` can persist despite actual producer access to that transcription. This is a registration/consumer coverage exception. It is not proof of a substantive evidence gap, a newly acquired source, or missing producer source examination. The existing EO8992 handoff says its manual proposal had no asserted source gap; the later retained completion includes source review. These historical statements do not themselves authenticate the APP transcription.

No existing native checkpoint/resume CLI solves this specific shared-source registration: there is no retained EO8992 source-blocked checkpoint, and resume emits reopen/defer only, never tracker receipts. A source supplement would add source context already present and would not close the tracker shared-authority gate. The generic `measure.py --receipts jobs/app-executive-orders/output/SOURCES.jsonl` cannot bind that APP row to `EO::6964`, because that row has no such native authority key. Manually adding `wanted_id` and calling it a native acquisition would manufacture the very consumer evidence that needs review.

The exact existing bounded acquisition interface is `REPO_ROOT=. OUTPUT_DIR=<fresh> JOB_ONLY=EO::6964 JOB_MAX_REQUESTS=8 python -B jobs/source-ladder/job.py`. It is an acquisition attempt, not an offline reuse command or a guaranteed rescue. Current `research/stage14/QUEUES/INDEXED_CACHED_EO_SOURCE_HINTS.csv` has no 6964 hint, so the held APP locator is not automatically routed through that shared-source request. A fingerprinted plan constrains membership and request budget; it cannot inject a missing URL, rename an APP source record, or turn missing cached raw bytes into a verified download. Do not run this merely to repeat a known source or claim progress from a retry. A real productive continuation first needs an authorized native registration path for existing APP authority evidence or a genuinely new source-ladder acquisition with a documented actual route. This worker does not add code/registry, alter queue/canonical metadata, fabricate a source receipt, or assert that requirement is already satisfied.

Accordingly, this bounded trace does not establish a source-ready unfinished scientific case that an existing CLI can honestly advance immediately. It does establish one concrete actionable integration exception to scope before production dispatch, and two genuinely source-blocked counterexamples that must stay unfinished. Root owns any implementation/selection beyond this read-only tracing assignment.

One bounded read-only OpenAI-family worker inherited the parent model. An exact deployed model identifier, actual token totals, billing, complete active labor and a prospectively recorded assignment timer are unavailable to this worker. Tool timings are partial execution observations only. No savings or scientific adoption is inferred. No background job or acquisition was launched. No shared files were edited.

