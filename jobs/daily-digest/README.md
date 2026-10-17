# Daily operational digest

The DAILY marker uses the shared runner's daily 09:17 UTC schedule. Output is
`DIGEST.md` plus a daily snapshot of job summaries. The runner publishes only this
named digest to `HANDOFF/DIGEST.md`, bounded to 149 lines. That explicit exception
to the usual output-only publication rule is requested by the owner.

It includes tracker headlines, scalar changes from the last committed snapshot
before today's New York date, top unlocks, newest handoff asks, and failed jobs.
The first run states that no prior comparison exists. It makes no model calls.
