# Reuse and assignment-sequence challenge

Investigation context: separate OpenAI child context, inherited model identifier not exposed by the runtime. Provider token usage, cash and exclusive active labor are unavailable. This is read-only architecture/evidence analysis, not scientific review or a savings measurement. Inspected repository pin: `a3bfac64b3e1c43400a8ed8c744419eb17f6e2e6`. Connector reads used that pin for the dispatch/preflight source. Main generated summaries are attributed to their own `commit_run`, not assumed to have been regenerated at HEAD.

## Decision

Do not build a question registry or claim that repeated applications prove repeated investigation. Existing production already shares exact questions, sources, conditional reasoning and prior findings. The strongest testable sequence change is narrower: route **explicitly declared assignment prerequisites** to source preparation before launching a full-case worker. Preserve alternative research paths and distinguish prerequisite triage from dossier completion.

`jobs/claim-kit/dispatch.py` currently requires custody/text/span checks for the original and clause evidence. Actor/current-law/contrary sources remain optional research leads until selected. This is intentional: a missing current predicate does not prevent a supported NO ending, and a pointer is not a selected legal theory. `batch.preflight` already creates `operative_current_law` tasks when a current-law lead has `evidence_gap`; ordinary packets already deduplicate these into shared tasks. The defect to test is whether the **caller assigns a current-predicate-dependent full-case task despite its declared prerequisites being absent**, not whether the packet lacks a diagnostics framework.

Minimal extension: let the ordinary caller explicitly bind the source/task prerequisites of its planned assignment to the existing dispatch check. On known failure, retain the affected members and source-preparation tasks and refuse that assignment scope. Do not globally promote every optional gap into a whole-order hold. A resumed or alternative assignment can investigate another ending theory under its own explicit scope. Use existing source-ladder request validation/plans and checkpoint/resume, not another acquisition planner.

Falsifiable claim: where the requested assignment explicitly requires a missing current-predicate source, the caller can produce the same known-source-gap triage endpoint without commissioning a model to rediscover that gap. Reject the benefit if competent current practice already performs this exact check before launch; if a model still must decide applicability for every member; if viable alternate endings are suppressed; or if source/exception coordination and fallback replace the removed work with equal or greater model work. A partial triage comparison must use identical output obligations and must not be called cheaper completed dossiers.

## Existing sharing and its demonstrated population

| Existing route | What it already shares | Supported limits |
| --- | --- | --- |
| NORTON | Exact question key over entity/object/scope/interval/proposition/event, separate answer and clause-application reviews; `FACT:` evidence only after both gates | Generated `CENSUS.json` has two exact reusable questions and six clause applications, covering five unique orders. The large unbound wording census has zero proven repeated applications. |
| Shared NRA production | Independently examined conditional propositions in `SHARED_RESEARCH.md`, explicitly assigned in `PRODUCER_BRIEF.md`; per-member exceptions and earlier endings remain | Fourteen assignments reached two eligible, eight blocked and four owner routes in the historical isolated completion. This was already a shared-reasoning production run, not fourteen demonstrated duplicate statute investigations. |
| Valla | Exact reviewed components, dependency-limited context, refused-method diagnostics, current native member view | Current generated summary has 1,445 claims and 783 shared-rationale references, but zero valid components and zero examined dependencies. Those references are not an available reusable-judgment population. |
| MAITLAND | `prepare --history-bundle` and ordinary/native/slim selected historical queries; source/review/membership validation | Bounded text/effect scopes and unknown operative states remain; no whole-order legal approval. Already integrated in main. |
| Existing batch/prior research | Shared sources/rationales, explicit packet tasks, status/lifecycle cumulative analysis, exact prior producer/reviewer/rejection/checkpoint context | Reuse must reconcile current version, source and proposition scope. Slim views already expose `prior_research_for_order`; adding it again would be redundant. |

The two NORTON shared questions are NCSSR report delivery for EO12335/12397/12402 (four clause applications) and OMB-to-GSA FACA function succession for EO11769/12024 (two applications). The corresponding `sol-norton-20261020/answers.jsonl` and `reviews.jsonl` are empty (Git empty blob `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`). Thus existing question pooling has not supplied approved answers for these clusters. It does not prove workers repeatedly reinvestigated them. Their complete current scientific eligibility was not established here.

The NORTON census reports 4,163 distinct unbound exact questions, 6,411 extracted obligations and 9,922 source/route holds. None is a count of independently mergeable legal questions or an eligible offload workload. Its possible-duplicate queue also omitted 8,867 pairs under the existing bound. Those omissions require disclosure, not a whole-corpus reuse extrapolation.

## Ranked hypotheses

1. **Declared prerequisite routing before full-case assignment.** Uses existing preflight/dispatch/shared tasks. Removes a known-gap rediscovery assignment only where scope explicitly requires the missing source. Best bounded experiment if retained actual workers were launched into that gap. Measure caller, source-preparation, exception and resumed-work costs through a shared triage endpoint.
2. **Targeted current Valla lookup from slim consumers.** Geddes `_view_one` exposes prior research and reviewed histories but omits Valla context. Existing native `batch.view` revalidates that context. PR137 already documented this omission and rejected blanket embedding of a historical member projection exceeding 51 KB. Test a compact routing notice only on genuinely flagged cases; count additional lookup and reviewer reading. No currently valid component-reuse population established.
3. **New broad question compiler/registry.** Reject absent evidence of duplicate investigations outside already-shared production. NORTON already implements the proposed unit with the correct answer/application separation. Its missing approved answers and source holds are evidence/research prerequisites, not a registry absence.

Adding mechanical receipts to every reviewer prompt is outside these hypotheses; Lind's negative result remains controlling unless the actual task displacement mechanism changes.

## Exact inspected artifacts

| Path | Git blob or source attribution |
| --- | --- |
| `jobs/claim-kit/dispatch.py` | `b0772a70eece7034862064ba8492b8b2fd9d67e3` at a3bfac64 |
| `jobs/claim-kit/evidence_preflight.py` | `a7443b9b5722cfbccfe02bbf0d5846ff8106bd34` at a3bfac64 |
| `jobs/claim-kit/batch.py` | `cbdbf2dc1de1dd95ee35b1f0fd7a0efe26775443` |
| `jobs/claim-kit/history_context.py` | `f4d0c8bc592e3d918b55234a5888ec63cfe20dce` |
| `jobs/claim-kit/AGENT_PROTOCOL.md` | `6850712fd2de16e491c02d4fc8b1f76dc32bb5a2` |
| `jobs/claim-kit/BATCH.md` | `7e36f71a2d6e3b5786f46b521554369a4a6e6dae` |
| `jobs/norton/README.md` | `e03ab4a5edfa13d20fec25aa2a454e3796e7a60e` |
| `jobs/norton/output/CENSUS.json` | `26db565a6059bee6179abb6b7b2d4b7f779442d7`; STATUS commit_run `2c85459cf38b08dc1eea6d7c84a74268fa45c28e`, run 41886953010 |
| `jobs/valla/README.md` | `34ef674803c8b8a12aa4d39379ee341188436543` |
| `jobs/valla/output/SUMMARY.json` | `ff49ed18faef5d54824b3953f24b79dd32385126`; same generated run as NORTON |
| `research/excavator/shared-research-production/SHARED_RESEARCH.md` | `e86e582e5f4fa02f4eff91135812aeeb4aa3dd3d` |
| `research/excavator/shared-research-production/PRODUCER_BRIEF.md` | `8a31c2485f33a4eb996c3503b2a488c8176601eb` |
| `research/progress/offload-decision-20261104/DECISION.md` | `55264763a0fb9ea359113efa100848952b44ce3c` |
| `research/progress/offload-decision-20261104/NEXT_TEST.md` | `93839ceaed4343eeb90f5c8e9742f036125d7dba` |

Kean query run in the shared new checkout: `python3 -I jobs/kean/kean.py search current-law prerequisite preflight source-plan dispatch`; no matching earlier work was found under that compound query, with 1,307 tracked reports/notes unmaterialized and therefore excluded. This query is not evidence that no relevant prior work exists; the directly read older reports above establish extensive overlap. The coordinator records the integrated finding and final source pins.

## Implemented consumer and validation handoff

The narrow implementation is `dispatch.check(..., require_task_kinds=['operative_current_law'])`
and ordinary `kit.py dispatch-check PACKET --require-task-kind operative_current_law`.
It changes no `prepare` default or scientific gate. Full current packet/source/runtime
validation remains before assignment classification; custody checks still run.
The exact internal `_assignment_prerequisites(preflight, ids, require_task_kinds)`
slice returns per-member blockers and grouped task diagnostics. Historical replay
of that slice has a prerequisite-routing endpoint only, never current dispatch
approval. Literal key equality is explicitly denied source-identity/legal-answer
authority, and empty `{}` keys are grouped separately per member.

All 17 focused dispatch tests passed in 23.844 seconds, including six new cases:
explicit versus default scope, mixed member selection, unidentified task keys,
unknown/duplicate/malformed kind refusal, concurrent source/stale-packet refusal,
and incomplete task payload refusal. `validation/dispatch-tests.log` retains
the output. Python compilation passed. Earlier attempts could not reach test logic
because the sparse checkout lacked `jobs/norton/model.py`, then
`jobs/later-events/later_events.py`; materializing unchanged dependencies resolved
those environment failures without code or gate relaxation. These checks establish
engineering behavior only. The coordinator owns the real assignment comparison,
independent review, integrated Kean finding and final recommendation.
