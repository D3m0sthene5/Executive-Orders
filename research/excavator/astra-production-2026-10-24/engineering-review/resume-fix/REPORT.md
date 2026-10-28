# Independent narrow review: receipt `time_utc`

Approved `lifecycle_obligations.py` SHA256
`61448e4f640b76312df4d47f9f5c000468d1ce7e24d0c5df1115a273e13bf5ab`
and regression-test SHA256
`a9bb04c6edbb6d729974c99303ac67c8102763d7c9b411db5da0d6ace2d3a05a`.
No blocking finding remains. This review covers only the receipt-normalization
change and its real EO4314 regression, not completion glue or substantive research.

The change adds `time_utc` to the existing retry-telemetry exclusions in
`material_source_results`. It leaves source content hashes, status, substantive
failures, dossier content, requests, routes and prior-research context in the
fingerprint. No existing receipt or checkpoint is rewritten.

The independent replay passed 16 checks plus the eight-test lifecycle unit suite:

- The exact old engine reproduces the preserved real timestamp-only failure.
- Reconstruction under the new normalization exactly matches the separately
  versioned `NORMALIZED_CHECKPOINT.json`.
- Unchanged failure and a change only to its `time_utc` defer.
- Adding the real current source receipt reopens; independent changes to the
  original receipt's status, error and SHA256 also reopen.
- Old unnormalized checkpoints are not silently migrated: they reopen until an
  explicitly reconstructed checkpoint is used. The authored migration note
  states this limitation accurately.
- Historical `review/v1` bytes, original attempts, timestamps and result paths
  remain unchanged. All three authored normalized replay results match exactly.

`REVIEW.json` pins the reviewed files and preserved inputs, records every check
and replay, and includes timestamps. `replay_review.py` is the independent
reproduction; `UNIT_TESTS.log` retains the test output. The recorded execution
interval is 0.081738163 monotonic seconds. Actual/cached model tokens, cash and
aggregate agent effort are unknown and remain null. No source/legal conclusion,
readiness gain, or human certification is made.
