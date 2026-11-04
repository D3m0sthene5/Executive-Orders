# Capcom finalization (bounded publication adapter)

One-off execution of the existing Mission builder and exact Tribonian accounting. It does not run claim-checker, readiness-tracker, source acquisition, production models, or substantive review.

Run only after a fresh successful combined tracker generation is published. Base the finalization branch on that generation so it appears in the first-parent history. The adapter refuses a stale tracker, mismatched totals, a ready campaign member lacking an exact effective passing receipt, changed historical Mission rows, or a missing frozen model input. A blocked campaign minority remains reported without suppressing the verified majority.

Use the existing Run jobs workflow with job capcom-finalization. Local reproduction uses the standard REPO_ROOT and OUTPUT_DIR environment variables and python3 -I jobs/capcom-finalization/job.py. See ../README.md for the runner contract.

Outputs:
- RECONCILIATION.json: native claim hashes, campaign/baseline attribution, current generation receipts, input hashes, actual Mission position and measured machine interval.
- CAMPAIGN_ROWS.json: each actual current Tribonian file/line/instrument/hash and exact checker/readiness result.
- MISSION_LOG.csv: maintained build_mission_log.py output with frozen weights and denominator; historical rows verified unchanged.
- KEAN_FINDINGS.jsonl / KEAN_BRIEF.md: native Kean CLI results staged entirely under OUTPUT_DIR for append-only integration against fresh main.
- Frozen model copies and ordinary runner STATUS.json/log.txt.

The baseline is the November2 tracker retained at a3bfac64b3e1c43400a8ed8c744419eb17f6e2e6. No expected final count is hardcoded. The human-certification register is copied into the receipt as a separate scope.

Do not merge an output from an old branch over newer main generations. Integrate only this adapter's source/output, the generated Mission feed, and the reconciled register append/brief. The original research claims, reviews and source grades remain their existing records.

Independent static review and known corrected failures are retained in research/progress/tribonian-finalization-20261104/. Native execution, final output review and publication remain required.
