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
