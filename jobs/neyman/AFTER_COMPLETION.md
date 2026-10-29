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
