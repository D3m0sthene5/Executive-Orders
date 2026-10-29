# 1. Cotton fixture isolation and custody/check ordering

Base: main 73d99f666573ee10f5b1ff2ada60f7d9331c3952. Owner requested implementation as unmerged PRs in priority order.

The existing six-test suite was reproduced locally from exact Git blobs cotton.py 95dc3c8bf36c10baecf74a4012b558e9769bf7fc and test_cotton.py 52dfbfde52a121cf11b12f7af89c2a189ccfe8f7. With JOB_PRIOR_OUTPUT_DIR=/tmp/irrelevant-cotton, the committed-copy reuse test failed (0 published versus 1 expected), matching the retained runner failure.

The change clears the inherited variable inside each synthetic test fixture and restores the complete prior environment after the test. The explicit runner-prior-output test still supplies its own path. cotton.py, network routes, byte matching and production carry-forward are unchanged. A new negative test rejects corrupt prior bytes when retrieval fails.

Local validation: all seven tests passed with JOB_PRIOR_OUTPUT_DIR unset and again with an unrelated inherited value (14 successful test executions). No network was used. claim-checker/after.txt now orders Cotton before the checker when both are selected. This edge does not request an unconditional Cotton run and does not change any scientific gate.

Reproduce:

```sh
python -I jobs/cotton-capture-custody/test_cotton.py
JOB_PRIOR_OUTPUT_DIR=/tmp/unrelated python -I jobs/cotton-capture-custody/test_cotton.py
```

Operational sequence: Cotton, claim-checker, readiness-tracker. Missing/replaced live web versions still fail exact-byte custody. No new readiness or savings is asserted by the patch. No merge authorized.
