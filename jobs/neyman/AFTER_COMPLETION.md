# Ordinary completion to NEYMAN

After a bounded ordinary production run, use the existing completion-history index and name the final completion folders:

```sh
python jobs/neyman/after_completion.py --repo . \
  --history research/excavator/RUN/COMPLETION_COSTS.json \
  --final research/excavator/RUN/complete-final \
  --base-commit PRODUCTION_BASE_COMMIT_SHA \
  --write research/neyman/production-diagnostics/RUN
```

Replace RUN and the exact 40-character base SHA with the production run's recorded values. Repeat `--final` for multiple final batches. The history index must include the failed and superseded completion invocations supplied for this cohort, with exact path/SHA-256 references; no filesystem search guesses that absent receipts never existed. The bridge imports only the supplied history and labels that limitation.

For unfinished members, supply their existing `neyman.research-attempt/1` records with repeated `--research-attempt PATH`. The bridge refuses to silently drop a member appearing in completion history without a final reviewed selection or explicit research-attempt receipt. Actual effort records can be supplied with `--effort PATH`; none are invented from machine timers.

The command creates pinned SELECTION.json and IMPORT.json, validates them through unchanged production_receipts.import_production, and calls unchanged diagnose.main for DIAGNOSIS.json, OBSERVATIONS.jsonl and REPORT.md. Failures, partial results, absent status adoption and isolated readiness retain the importer's existing distinctions. Exact duplicate receipts count once. Unknown labor, tokens and savings stay unknown. No population estimate, Junto credit, source fetch, model dispatch or canonical write occurs.

All output is in a fresh research/neyman/production-diagnostics subdirectory. No default frame/pilot scheduling is changed. `jobs/neyman/job.py` already discovers test_*.py and therefore includes test_after_completion.py.
## Explicit invocation from ordinary completion

`kit.py complete` can now invoke this same adapter after it releases the publication lock and saves scientific receipts:

```sh
python jobs/claim-kit/kit.py --repo . complete research/excavator/RUN/COMPLETION.json \
  --write research/excavator/RUN/complete-next \
  --diagnostic-history research/excavator/RUN/COMPLETION_COSTS.json \
  --diagnostic-base-commit PRODUCTION_BASE_COMMIT_SHA \
  --diagnostic-write research/neyman/production-diagnostics/RUN-next \
  --diagnostic-research-attempt research/excavator/RUN/UNFINISHED_ATTEMPT.json
```

The history remains an explicit, pinned, nonempty index of retained invocations. The adapter appends the just-written `TALLY.json` to a derived `COMPLETION_HISTORY.json`; it never rewrites the supplied history or scans for missing attempts. The default final selection is this completion. Repeat `--diagnostic-final FOLDER` to explicitly select other final folders instead (for a retry or an isolated historical replay). Every observed unfinished member still needs an explicit research-attempt record. Duplicate receipts retain their existing deduplication behavior.

Optional repeated `--diagnostic-effort`, `--diagnostic-checkpoint` and `--diagnostic-question` pass existing NEYMAN record types to its unchanged importer/diagnosis. These fields add context, never legal conclusions. The adapter's standalone equivalents are `--current`, `--checkpoint` and `--question`.

`complete/DIAGNOSTIC.json` and the CLI's `diagnostic` object record success or refusal separately. `TALLY.json`, scientific exceptions, scientific eligibility and the CLI's scientific exit code do not change because of diagnostic errors. Missing required diagnostic options, invalid pins, omitted members, existing/unsafe output destinations and the 60-second diagnostic timeout are visible refusals. If receipt writing fails, the CLI object includes `receipt_error`. No diagnostic options preserves the ordinary completion behavior. No diagnostic or source action runs automatically unless explicitly requested.

Keep diagnostic output in its fresh NEYMAN directory. Current prior-research discovery ignores these derived formats while preserving the underlying claims, exact reviews and checkpoints. Focused regressions verify that writing the diagnosis does not change frozen packet context, and a genuinely relevant new review still does. Do not copy a derived report into a new purported scientific review or selected-version manifest.
