# 6. Ordinary production receipt handoff

The optional after_completion.py command builds the exact existing NEYMAN import contract from a declared completion history and explicit final completion folders, then invokes the existing diagnosis CLI. It avoids a separate manual reconstruction of final claim hashes, publication scopes and import manifests.

No estimator is rebuilt. The existing production_receipts.py was reconstructed locally and verified byte-for-byte against main Git blob 98118e5a20bc8688b68a2542285dbf6492fa235e before integration tests. It is unchanged by this PR.

Ten focused tests passed against that real importer, covering exact claim selection, failed invocation retention, duplicate-receipt deduplication, changed pins, selected-claim mismatch, partial-vs-whole scope, unfinished-member refusal/inclusion, missing final history, and fresh output. The CLI call into diagnose.main is tested with a spy; the whole existing diagnostic report implementation was not re-executed locally. The normal NEYMAN job discovers these new tests automatically.

Usage: jobs/neyman/AFTER_COMPLETION.md. This is a diagnostic handoff, not a verified saving or a completed representative cost survey. Only supplied history is covered; missing worker/token telemetry remains unavailable. Leave unmerged.
