# Independent narrow review: retention output cap

Approved runner SHA256
`75f5f250cdbf0a3eff077d6f6431e50df1c0d26d4650e160432d433565783795`.
No blocking finding remains. `REVIEW.json` records exact hashes for the runner,
tests, unchanged freshness engine, retention opt-in, and documentation.

The default remains **95 MiB / 99,614,720 bytes**. Only
`astra-source-retention/MAX_OUTPUT_FILE_BYTES` opts into **104,857,599 bytes**,
strictly below 100 MiB. The decimal positive-integer validator rejects an
unsafe ceiling before the previous output is moved or the producer executes.
Freshness capture precedes validation and covers the cap file, runner/job code,
and declared source inputs. The existing oversized-file destination, status
listing and transactional failure handling remain in use.

The independent actual-size replay used the already held 104,612,053-byte
PL 97-35 PDF, SHA256
`aacf815d01c9c3d797d7c516d9ccddd1f723dc1a44e47f8899ba742d988e2127`,
inside temporary test repositories. It confirmed:

- Opted-in output retains the PDF byte-for-byte and retains a file exactly at
  104,857,599 bytes. A 104,857,600-byte file moves to the existing oversized
  artifact location and is listed in status.
- A default-cap job still moves the same PDF and both larger boundary fixtures
  out of output; the relocated PDF remains byte-identical.
- Cap/source changes alter the exact captured input versions. The captured
  manifest includes the cap, runner/job source, and the actual held input file.
- An invalid cap never starts the producer, preserves every prior-output byte,
  retains failure receipts and blocks dependent publication.

All **24 independent checks** passed, including the **four focused tests**.
Execution took 2.102353185 monotonic seconds. Logs, status receipts, the captured
manifest, exact input hashes and reproducible probe code are beside this report.
The held PDF and reviewed code were rehashed unchanged at completion. Temporary
repositories were removed; no project Git or HANDOFF mutation occurred.

No network request, upload, new storage mechanism or remote retention run was
performed by this review. The ordinary remote job must still fetch/retain and
publish its own successful receipts. Unknown actual/cached model tokens, cost
and aggregate agent effort remain null. This approval concerns file retention
and runner behavior only, not historical or legal conclusions.
