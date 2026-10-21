# R12553NB probe outcome (2026-10-20)

AI review hypotheses only. The certified whole-lifecycle count stays 0. No codebook or status changed.

- Pool R12553NBP: 10 orders that EO 12553 (1986-02-25, 51 FR 7237) revoked, none of them emergency boards.
- ACT: 10 attempts, 9 located, 1 blocked (EO 11284: the DOPMA earlier-end lead is not held, fetch requested). The independent Opus reviewer upheld 8 and rejected 1, for 0.8 upheld per attempt. The rejection was the planted EO 11327 copy. The genuine EO 11327 record was not reviewed, so it is not ingested.
- D6 earlier-end test: for 6 of the 8 upheld orders, EO 12553 is only an upper bound. Those orders are EO 10601 sec. 3, 11493, 12186, 12244, 12269 and 12351.
- Ingest: the 8 records are in `research/readiness/act_overrides/rastell-r12553nb-2026-10-20.jsonl`, with the review ledger in `review/`. `act_overrides.verify` accepted all 8.
- Claims: 6 claims were upheld (EO 8427, 11493, 12040, 12244, 12269, 12351) and are in `research/readiness/claims/claude-r12553nb-01-2026-10-20.jsonl`. The claim checker passed all 6. EO 10601 and EO 12186 are blocked (unlocated sec. 3 events, and a pending method question).
- Scale gate (at least 7 ACT upheld and at least 5 enabled): passed, with 8 and 6.
- Plants: 1 planted, 1 caught.
- Pending owner rulings (report-deadline, transcription-as-copy): none decided, and no item was blocked on them.
