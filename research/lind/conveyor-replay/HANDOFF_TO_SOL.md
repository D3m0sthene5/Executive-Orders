# Handoff to Sol: measuring tokens and time with no extra bookkeeping (2026-11-13)

**Measurable today, from logs you already produce**
- **Per-session usage:** the Claude transcript JSONL holds the last `usage` per message id. Price it with
  `jobs/necker-costs/PRICES.json`; the code is in `research/excavator/claude-papinian-2026-11-10/tools/cost.py` or
  `jobs/bentham/bentham.py usage --wave NAME --phase LABEL --session-id ID`.
- **Context re-read per call:** the `cache_read_input_tokens` field in the same data. This is the largest cost in long
  sessions: 518-769k tokens per call measured here, 77-82% of the coordinator's dollars.
- **Calls by purpose:** each tool call's description. A rough clerical / decision / repair split is in
  `research/lind/conveyor-replay/RESULT.md` section 1.

**The important missing measurement**
- **The denominator:** verified historical findings (events, clause ends, documents) produced per session, recorded as
  a count at the end of each session. Without it, tokens cannot be tied to research output.

**The improvement you can exercise naturally**
- Keep the coordinating session short and spawn fresh contexts for each judgment task: about $0.06 against $0.13-0.21
  per call measured here.
- Hand clerical claim-kit steps to `jobs/maudslay-conveyor` (fixed for the undecided route today). Your swarm then
  pays for research, not for re-reading context.
- **Caution:** the conveyor stops at producer reconfirmation (owner decision
  D-20261110-no-mechanical-reconfirmation-for-models), and so should any manual route.
