# Daily operational digest

The DAILY marker uses the shared runner's daily 09:17 UTC schedule. Output is
`DIGEST.md` plus a daily snapshot of job summaries. The runner publishes only this
named digest to `HANDOFF/DIGEST.md`, bounded to 149 lines. That explicit exception
to the usual output-only publication rule is requested by the owner.

It includes tracker headlines, scalar changes from the last committed snapshot
before today's New York date, top unlocks, newest handoff asks, and failed jobs.
The first run states that no prior comparison exists. It makes no model calls.

The status section describes published output generations. Transactional failures
retain earlier successful outputs, so a healthy output status does not establish
that the latest attempt succeeded. The digest points to `jobs/_attempts/` and the
workflow status for those receipts. NEYMAN and its pilot precede the digest when
selected, so their new summaries are available before publication.

## Current research dashboard

The same job also writes [`output/DASHBOARD.md`](output/DASHBOARD.md) and
[`output/DASHBOARD.json`](output/DASHBOARD.json). These are the moving dashboard;
the dated Stage 12–17 HTML releases and PR48 planning snapshot remain historical.

The dashboard reads the working-identity and provisional-status registers, filed
claim JSONL, published checker receipts and tracker outputs. It reports claim
lines separately from distinct orders, compares exact canonical claim hashes
against every checker receipt, and flags unmatched new or changed claims. Matching
receipts may contain failures: receipt coverage never creates readiness. The
ready count always comes from the published tracker and retains its generation
date. Human certification comes only from the separate published Stage19 record.

Original-supported and transcription-dependent readiness are shown separately.
Pinakes PDF/text counts and Cotton retained web copies describe source acquisition,
not completed legal research. Source SHA-256 hashes, producer generation receipts
and the dashboard's input commit are recorded in JSON. A source missing from the
checkout is reported as unavailable, never as zero progress.

`python -m unittest -v test_dashboard` runs before the existing digest generation.
The tests cover stale receipts, replacement/duplicate claim counts, unavailable
inputs and separation of human certification from AI checks. `needs.txt` declares
the extra small research input folders; `after.txt` keeps checker/tracker and source
acquisition ahead of this display job when they are selected in the same run.

No model calls, legal classifications, source fetching, readiness assignment or
effort-model recalibration occur in this renderer. The existing 149-line HANDOFF
digest limit and daily snapshot comparison retain their behavior.

