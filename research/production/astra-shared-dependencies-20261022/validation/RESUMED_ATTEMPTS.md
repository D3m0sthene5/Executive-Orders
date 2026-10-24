# Retained execution issues

- The first local freshness suite had9 errors because this bounded checkout omitted jobs/claim-kit/inputs.txt. The29-test log is retained as freshness-tests.log. Materializing that existing fixture input and rerunning only the affected suite is recorded separately in freshness-complete-inputs.log. No production code change was needed.
- After source batch3 successfully retained all30 exact versions, its local git-add collided with the fixture materialization's index.lock. No source acquisition or extraction was repeated; staging was retried after the materialization finished. GitHub inputs were not concurrently modified, and no publication was lost.
- Generated source extraction retains trailing spaces from the PDF. A broad diff whitespace check reported those source bytes; they were not normalized or rewritten. Runtime code is checked separately.

- The coordinator repeated the tracker suite before materializing research/stage19/code in the sparse checkout:36 setup errors (no assertions executed). Its full failure log is retained. After restoring the existing fixture directory, all36 tests passed in0.251s without a production change. One unsupported git sparse-checkout option was rejected before materialization; the supported command then succeeded.

- An early local reconciliation was attempted while the output-only bot commit was still being restored locally, so it read the prior272-ready generation and rejected the expected five-case delta. No consumer failure or claim change occurred. After restoration completed, reconciliation against pinned c30ba4b4 passed exactly53restored+5optional completions; the equality assertion was not relaxed.
