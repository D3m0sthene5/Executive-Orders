# R4 integration contract

## Pins and ownership

Base main: `88cef0253ed735b2a6e612770f25f9148641ce93`; base Git tree `334be684f4e27a9711f610edfb620e66499a8ca4`. Branch `sol/r4-production-diagnosis`. Exact implementation/test SHA-256 values: `PINS.json`; independent final review: `ENGINEERING_REVIEW.md`.

Changes own only NEYMAN completion adapter, claim-kit `kit.py`/`completion.py`, focused tests/docs, R4 progress/handoff and R4 Kean findings/generated brief. No edits to evidence_preflight, Valla, runner/declarations, clause-drafts, Early-Ranger/census or shared `_lib`. Materialized dependency files are read-only and excluded from the PR.

Historical cohort base `1caa42af95705e452d0e02425c7d9ceb9ed5ba7c` is provenance for retained scientific receipts, not the R4 engineering source base. Exact referenced receipt pins are in the native diagnostic's `HANDOFF.json` / diagnosis `input_pins` and tracing report. Implementation changes do not retroactively re-review those historical claims.

## CLI contracts

Ordinary new batch:

```sh
python -B jobs/claim-kit/kit.py --repo . complete research/excavator/RUN/COMPLETION.json \
  --write research/excavator/RUN/complete-next \
  --diagnostic-history research/excavator/RUN/COMPLETION_COSTS.json \
  --diagnostic-base-commit EXACT_40_CHARACTER_PRODUCTION_BASE \
  --diagnostic-write research/neyman/production-diagnostics/RUN-next \
  --diagnostic-research-attempt research/excavator/RUN/UNFINISHED_ATTEMPT.json
```

The history index already records explicitly supplied prior invocations with exact path/SHA256 references; it is never discovered by filesystem search. The just-finished tally is appended by `--current` internally. The default final selection is the current completion; optional repeated `--diagnostic-final FOLDER` selects explicit historical/final folders instead. Repeat `--diagnostic-effort`, `--diagnostic-checkpoint` and `--diagnostic-question` for existing respective NEYMAN schemas. Options are repository-relative strings consumed by NEYMAN; the scientific manifest/write arguments retain their existing path rules.

Standalone adapter stays supported. New equivalents: `--current FOLDER`, `--checkpoint PATH`, `--question PATH`. A missing/nonempty-history contract is not relaxed. A first invocation without retained history can complete scientifically and use the standalone handoff later once it has an explicit pinned history. Do not infer missing earlier attempts as absent.

Exact executed native command arguments are retained in `examples/native-complete/DIAGNOSTIC.json`; `examples/HISTORY.json` names all three historical invocations and its source import. `examples/COMPLETION.json` is an explicitly unresolved/blocked R4 engineering manifest using retained control records. It contains no newly reviewed scientific submission. Preserve its missing-DESIGN execution exception; copying it into production would not make a valid scientific completion.

## Failure and dependency semantics

Scientific completion writes/publishes first and releases its lock. Only then can the optional 60-second adapter subprocess run. Success/refusal/timeout goes to `complete/DIAGNOSTIC.json` plus the CLI object. Original `TALLY.json` stays byte-stable, and scientific exceptions/exit status remain unchanged. Adapter failure never rewrites scientific receipts or canonical claims. Receipt-write failure remains visible through `receipt_error` in the CLI object.

The adapter refuses changed pins, omitted unfinished members, conflicting final selections, missing metadata and unsafe/existing output destinations. Diagnostic refusal does not assert source exhaustion. Successful diagnosis does not dispatch acquisition, review, adoption or legal judgments. Timer sums are never agent-labor estimates. Reports retain null total labor/savings and scoped partial/isolated/adopted distinctions.

No diagnostic schema/file was added to scientific dependency discovery. Focused tests verify original/independent packet context stability, plus sensitivity to genuine relevant reviews. Preserve underlying source, claim, review, checkpoint and prior-research dependencies when integrating other streams.

## Bounded source-route validation and limit

```sh
python -B jobs/source-ladder/record_series.py --repo . \
  --manifest research/excavator/nmb-series-2026-10-25/SERIES_PLAN.v2.json \
  --out research/excavator/r4-production-diagnosis/NEW-nmb-action
```

Requires the ten exact data files listed in TRACE and pinned by the retained plan. Executed output is `research/excavator/r4-production-diagnosis/nmb-action-v2/`. It is validation-only: three existing source proposals, zero network calls, no new factual/legal findings. Do not requeue reports already held. The examined native diagnoses did not support a newly productive source-ready scientific continuation. Preserve this unmet part of R4; do not call the replay a completed novel research gain.

EO8915 remains blocked for earlier-event evidence. EO8992 needs registration/integration examination outside this ownership; its actor transcription was already available. Neither a checkpoint fingerprint change nor a copied source establishes a scientific ending or clears canonical readiness.

## Checks

```sh
python -m unittest discover -s jobs/claim-kit -p 'test_completion*.py' -q
python -m unittest discover -s jobs/neyman -p 'test_*.py' -q
python3 -I jobs/kean/kean.py check --strict
```

The first two passed: 45 and 53 tests, with two preexisting metadata skips in NEYMAN. Full production/source suites need their ordinary declared source inputs. Strict Kean passed with 0 errors and 0 warnings. Root should repeat it on the integrated materialization and regenerate the brief after unioning findings.

## R1 declaration requests (no declaration edits here)

If a selectively materialized worker invokes `kit.py complete` with diagnosis options, its closure needs `jobs/neyman/after_completion.py`, `production_receipts.py`, `diagnose.py`, `survey.py` and ordinary standard-library imports in addition to the existing completion closure. Its data closure includes the explicit history, current tally, chosen final selected claims/tallies/tracker replays, every supplied attempt/effort/checkpoint/question and their recursively consumed pinned bases. Diagnostic outputs are outputs, never inputs. No universal selective certification is asserted.

A bounded NMB replay additionally needs `record_series.py`, `fetch_ladder.py`, `report_dates.py`, `request_contract.py`, their supported imports and the plan's exact ten input files. Existing source-plan/measurement interfaces remain unchanged. R1 should audit a nominated actual job/version; this document grants no runner certificate.

## Adoption steps for Root

1. Review the exact PR diff and independent engineering hashes. Apply the three implementation files together with focused tests and invocation docs.
2. Union R4-namespaced Kean entries with other sessions; regenerate `HANDOFF/KEAN.md` in the combined checkout. Retain the dedicated R4 handoff and scientific/action limitations.
3. Resolve claim-kit overlap with other sessions at the exact combined source pin. Repeat focused suites; confirm omitted diagnostic metadata still cannot affect scientific completion and derived output still does not stale independent packets.
4. Audit explicit input declarations with R1 before any selective-runner use. Exercise a real source-ready production continuation when one is supported by current evidence; keep the action objective open until then.
5. This assignment authorizes no merge, main update, status/scientific adoption or canonical readiness publication. Root owns subsequent integration decisions.
