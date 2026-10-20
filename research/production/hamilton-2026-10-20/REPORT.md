# Hamilton's first audit: where the agents' tokens went (2026-10-20)

Five Executive-Orders sessions were audited from their own transcripts
(`PROFILE_*.json` here; method in `jobs/hamilton-token-audit/README.md`).
Dollar figures are the sessions' `cost_usd`: API list-price value of the tokens,
not necessarily what the owner paid (records show `isUsingOverage: false`).

## The sessions

| Session | Value | Model calls | Median context | Notes |
|---|---:|---:|---:|---|
| Stage 9/11 research and upload, Oct 16-17 | $816 | not fully read | | 2.25 B cache re-reads, 36 M cache writes, 9.0 M output. Cost shares: re-reads 68%, cache writes 17%, output 13%. Transcript only 5% downloaded: auto mode blocked one copy step as possible data exfiltration, and it was not worked around. |
| X1 build and pilot | $54 | 535 | 421 k coordinator / 122 k helpers | |
| Remaining-work treemap and plans (this one) | ~$20+ | 164 | 305 k | |
| PR 31/33 merge | $5 | 83 | 168 k | |
| ProQuest survey | $2 | 45 | 104 k | |

Re-reading context dominates every session. The sum of cache reads in the X1
transcript matches the session's billed total exactly (136,866,592), which
anchors the attribution.

## Findings, largest first

1. **The coordinator costs more than the workers.** In X1 the main thread made 258 calls at a median
   context of 421 k tokens: 72% of input-side cost. The 11 helper agents that did the research made 277
   calls at 122 k: 28%. In this session the main thread was 97%. Every status check, file peek and
   message in a long-lived coordinator re-reads its whole history.
2. **Fixed setup on every call.** Each agent starts at about 69-73 k tokens (system prompt, tool and
   connector instructions, project rules), re-read on every call: 19% of X1's cost, 31% here, 34-51%
   in the short sessions.
3. **Waiting in a large context.** X1's status checks after the work was done (pull request, CI,
   notifications) cost about $4.4. One check after an hour idle rebuilt the cache, rewriting 629 k
   tokens for about $3.8. Together about 15% of X1. This session also had a rebuild worth about 12%.
4. **The model's own words.** Replies and narration stay in context and are re-read: 11% of X1, 21% of
   this session.
5. **Printing files and big command output.** `cat`, `sed`, heredoc scripts and their output: about
   15-20% of X1 together.
6. **Hand-written output.** 13% of the $816 session was output tokens (9 M), consistent with
   hand-built JSON, which claim-kit's decision-sheet assembler now replaces.

## Tools Hamilton proposes

These are estimates. Each needs a probe, and Hamilton re-audits it.

| Tool | Aimed at | What it does | Expected effect | Probe |
|---|---|---|---|---|
| **Revere** (relay rider) | 1, 3 | Phase handoff: at each phase end the coordinator writes a compact state file and a fresh session continues from it, so no coordinator grows past about 150-200 k. | X1's coordinator at a 150 k median instead of 421 k: about 40% off X1's total | Run Y1's build with phase handoffs; re-audit. |
| **Watchman** | 3 | Monitoring outside the big session: a scheduled fresh session or a GitHub Action checks the PR/CI with a script and wakes the main session only when something changed. | Removes most of the 15% spent waiting | Next pull request babysit. |
| **Spare setup** | 2 | Measure first-call context with unused connectors (Vercel, Docs) turned off and with shorter rules, then keep what lowers it. | Unknown until measured; each 10 k off the setup saves about 1.4% per call | One empty session per configuration, read its first-call context. |
| **Quiet protocol** | 4, 5 | Scripts print 20 lines or fewer; reports and long reasoning go to files; replies stay short. | 5-15% | Next agent batch; re-audit. |

Not proposed: re-engineering the output path. Claim-kit's assembler already targets finding 6;
Hamilton should re-audit the next claim swarm to confirm.

## Limits

- Item sizes are estimated as characters / 4, and transcripts understate output tokens.
- The $816 session was audited from totals only.
- Local (bridge) sessions report no costs.
- Five sessions are a small sample. The ranking is sturdier than any percentage.
