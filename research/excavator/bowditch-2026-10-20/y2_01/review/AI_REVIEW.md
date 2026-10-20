# Bowditch Y2 batch 01: independent AI review

Reviewer: claude-bowditch-y2-01-reviewer (independent agent, not the producer). Reviewed: `applied-v3/CLAIMS.proposed.jsonl`.
**This is not a human certification. The human-certified whole-lifecycle count stays 0.** Upheld claims are AI hypotheses eligible for human review only.

Counts (25 orders): upheld 1, rejected 2, block_justified 22 (21 blocked + 1 unresolved), block_not_justified 0.

Upheld: EO 10999, revoked in whole by EO 11490 Sec. 3015(7), 1969-10-28.

Rejected:
- EO 13792. The claim dates every Sec. 2 review and report clause to the 2021-01-20 revocation by EO 13990. Sec. 2 is a one-time review-and-report command that was performed in 2017. Under jobs/claim-kit/BATCH.md, a later revocation does not prove first cessation of a command already performed. No held source gives the dates of the reports. The reviewer queued a FETCH_QUEUE request for them.
- EO 10192. Clause 1 and whole_order_end give the date 1951-05-31 with mechanism "amend" by EO 10236. EO 10236 never amends paragraph 3, and the cited quote stops before the sentence "shall cease to exist at the end of May 31, 1951". As a result, no cited text supports that date. A correction needs an end record that includes the cessation sentence (tooling gap) and a fresh review.

Blocks: all justified, and the FETCH_QUEUE lines fit the gaps. The reviewer added a missing request for EO 14125 (the date of the emergency board's report). Tooling blocks (no mechanism on ACTOR_TEXT, and no TERM record for single-day or Congress-bound ends) are confirmed for 8300, 9916, 11923 and 11065. These are tool blockers, not evidence blockers.
