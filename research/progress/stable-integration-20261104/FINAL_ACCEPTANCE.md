# Final combined acceptance

This branch incorporates PR147 and its stacked PR148, preserving original PR139/140/144 ancestry. It is the final combined candidate for main; earlier heads retain their actual failures rather than being relabeled green.

## Corrections retained

- Review-ready filed dossiers must retain their exact machine confirmation pins through fresh witness reassessment. The native before-case reproduces ready→notready after a rebuild; the fixed case stays ready with byte-identical confirmation while changed evidence reopens it. No old approval is copied.
- Windows fixtures now derive source hashes, quotes and character spans from saved bytes.54 tests pass with normal and forced CRLF writes. Runtime source checks remain strict.
- The previous Valla run passed unit, isolation, pilot and lifecycle checks, then failed with EXDEV because historical custody replays relocate PDFs from checkout to the host /tmp. Job TMPDIR now uses runner.temp. Before expensive replay, a native temporary binary must rename checkout→temp→checkout with unchanged bytes. Different devices, unexpected fallback and rename failure refuse early. Historical replay scripts and gates are unchanged.

Independent source pins and before/pass logs: FILED_SCOPE_FIX.json, FILED_SCOPE_WINDOWS_FIX.json, FILED_SCOPE_REVIEW.json, HOSTED_FILESYSTEM_FIX.json, FINAL_PORTABILITY_REVIEW.json. Full final-head hosted checks remain the acceptance gate. No new legal conclusion, scientific adoption, human certification, net readiness gain or measured project-wide saving is asserted.

## Landing

Merge this complete candidate against current main only after its actual hosted checks pass. Its ancestry includes all completed work; earlier integration PRs are incorporated, not separate deployment steps. PR141 and PR146 remain active research drafts and must retain their source/research holds; update their branches by ordinary merges with the final current main, preserving the experimental additions. Publish successful canonical generations through existing runner/reporting freshness guards and record actual publication receipts before ending.
