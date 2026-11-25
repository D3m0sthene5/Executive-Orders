# Bracton wave: PC lanes (instructions for the Claude Code session on the owner's PC)

You are the PC lane coordinator for wave Bracton (plan `WAVE.json` in this folder; Augur PASS, signed by the owner,
`AUGUR_RECEIPT.json`). The cloud coordinator runs lanes c01-c12 and does all review, reveal and filing. You run the
producer step for packets p01-p11 only, four at a time, and hand the packets back by branch. You make no legal judgment
yourself and file nothing.

## 1. Set up (once)

1. From `C:\Users\danie\Projects\Executive-Orders`: `git fetch origin`. If `git status --porcelain` shows no tracked
   changes, `git switch main && git merge --ff-only origin/main`, then `git switch -c claude/bracton-pc`. If there are
   tracked changes, do not touch them: create a worktree instead,
   `git worktree add C:\Users\danie\eo-wt\bracton-pc -b claude/bracton-pc origin/main`, and work there (it needs the
   full checkout, including `jobs/claim-kit/output`).
2. Scratch root: `C:\Users\danie\maudslay-scratch\bracton` (call it SCR). Create `SCR\transcripts`.
3. Record your start time and model in `SCR\LANES.csv` (header `label,agent_id,model,start_utc,end_utc,tokens,tool_uses,ms,result`).

## 2. For each packet pNN (p01 to p11)

1. Prepare (scripts, no tokens):
   `python -X utf8 research/excavator/claude-bracton-2026-11-25/tools/prep_pc.py pNN`, then
   `python -X utf8 research/excavator/claude-bracton-2026-11-25/tools/render_pc.py pNN C:/Users/danie/maudslay-scratch/bracton`.
   If prepare fails, record it in LANES.csv and go to the next packet. Do not edit the ids.
2. Launch one producer subagent with the Agent tool, `model: sonnet`, in the background, whose whole prompt is:
   `Your complete instructions are in the file C:/Users/danie/maudslay-scratch/bracton/prompts/producer-pNN.txt . Read that whole file first with the Read tool and follow it exactly; it is your task brief from the coordinator. Do not commit or change git state.`
   Keep at most four producers running at once; start the next packet when one hands back.
3. When a producer hands back: append its agent id, model, end time, tokens, tool uses and duration from the completion
   notice to LANES.csv. Copy its transcript (the subagent `.jsonl` under `%USERPROFILE%\.claude\projects\...\subagents\`
   for this session) to `SCR\transcripts\pNN-<agent id>.jsonl`. The Gilbreth probe prices these per call; they are the
   only per-call usage records the wave has, so copy every one, including producers that fail.
4. Commit only `research/excavator/claude-bracton-2026-11-25/pNN/` and `research/readiness/CLAIM_KIT_LOCK.json` with
   message `Bracton pNN: producer packet (PC lane)` and push `claude/bracton-pc`. Commit after every packet, not at the end.

## 3. Rules

- Read `jobs/bentham/output/PLAN.md` once; do not run any other Bentham action. Stop all lanes if the cloud coordinator
  pushes a file `STOP` to this folder on main, or if any producer reports "changed prior research".
- Never run review, reveal, `finish_pair`, Kean or HANDOFF edits; the cloud coordinator does those.
- Never edit another packet's folder, never re-prepare a packet that has an `applied-v1`, never force-push.
- When all eleven packets are handed back, write `SCR\DONE.txt` with the LANES.csv totals and stop.
