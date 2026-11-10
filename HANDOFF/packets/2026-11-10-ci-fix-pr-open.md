# Handoff packet: ci-fix-pr-open

Written 2026-11-10T04:13:35Z by `jobs/carnot-coordinator/handoff.py`. Built from git and its arguments only.

## Where things stand

- Branch `codex/mommsen-2-production`, HEAD `c240fbd246388d792d2291943d16c23ae9f79beb`. Check `git rev-parse HEAD` matches before continuing; if not, read the commits since.
- Upstream: ## codex/mommsen-2-production...origin/codex/mommsen-2-production
- Uncommitted files (242): `HANDOFF/packets/2026-11-10-pr-open-rebased.md` (??), `HANDOFF/packets/2026-11-10-pr-open.md` (??), `research/excavator/mommsen2-2026-11-10/b01/packet/DISPATCH_CHECK.json` (??), `research/excavator/mommsen2-2026-11-10/b01/packet/PACKET.json` (??), `research/excavator/mommsen2-2026-11-10/b01/packet/PREPARE.json` (??), `research/excavator/mommsen2-2026-11-10/b01/packet/RATIONALES.json` (??), `research/excavator/mommsen2-2026-11-10/b01/packet/READ.md` (??), `research/excavator/mommsen2-2026-11-10/b01/packet/clauses.csv` (??), `research/excavator/mommsen2-2026-11-10/b01/packet/decisions.csv` (??), `research/excavator/mommsen2-2026-11-10/b01/packet/dispatch-v2.json` (??), `research/excavator/mommsen2-2026-11-10/b01/packet/dispatch-v3.json` (??), `research/excavator/mommsen2-2026-11-10/b02/COMPLETION.json` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a1/page45.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a1/page528.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a1/page529.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a1/page532.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a1/page72.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a2/ofr-244.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a2/ofr-332.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a2/ofr-357.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a2/ofr-366.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a2/ofr-527.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a3/page-219.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a3/page-220.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a3/page-498.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a3/page-499.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a3/page-528.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a3/page-533.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a3/page-536.png` (??), `research/excavator/mommsen2-2026-11-10/b02/agents/a3/page-537.png` (??), `research/excavator/mommsen2-2026-11-10/b02/complete-v2/CLAIMS.publishable.jsonl` (??), `research/excavator/mommsen2-2026-11-10/b02/complete-v2/CLAIMS.selected.jsonl` (??), `research/excavator/mommsen2-2026-11-10/b02/complete-v2/EXCEPTIONS.json` (??), `research/excavator/mommsen2-2026-11-10/b02/complete-v2/INPUTS.json` (??), `research/excavator/mommsen2-2026-11-10/b02/complete-v2/PACKETS.json` (??), `research/excavator/mommsen2-2026-11-10/b02/complete-v2/PUBLICATION.json` (??), `research/excavator/mommsen2-2026-11-10/b02/complete-v2/TALLY.json` (??), `research/excavator/mommsen2-2026-11-10/b02/complete-v2/receipts/research/excavator/2026-10-18/review/INDEPENDENT_AI_REVIEW.json` (??), `research/excavator/mommsen2-2026-11-10/b02/complete-v2/receipts/research/excavator/mommsen2-2026-11-10/b02/COMPLETION.json` (??), `research/excavator/mommsen2-2026-11-10/b02/complete-v2/receipts/research/excavator/mommsen2-2026-11-10/b02/packet/applied-v2/SUMMARY.json` (??) ...
- Newest notes entry: 2026-11-09 ET (Claude, why Mission has been pending since 2026-11-06)
- Context of the handing-off session: 400732 tokens per call (hand_off).

## Recent commits

- c240fbd246 Retain Kean source evidence for Mommsen II
- 99bbe0e215 File two reviewed early-order lifecycle claims
- ff0e3073cf Results of job(s): claim-checker readiness-tracker gessner-cards daily-digest
- 387bacee09 Results of job(s):
- d2163878a3 Results of job(s): claim-checker readiness-tracker gessner-cards daily-digest
- f3c693ff6e Merge pull request #247 from D3m0sthene5/claude/froissart-journal
- 84b78f2e2d Merge pull request #249 from D3m0sthene5/claude/mission-checker-scope
- 8777d36ea2 Restore main's Kean outputs (the runner rebuilds them after merge)

## Notes from the coordinator

- MOMMSEN-II not finished. PR 252 has two locally filed claims EO 5595 and EO 5989, 2/2 controls caught, local ready 659 to 661; Kean source fix c240fbd246 pushed. PR 253 separate test-only sparse CI fix, local daily-digest 25/25 and Kean strict passed; watcher pr253-watch.log running. Neither PR merged.

## Next

PR 253 sparse CI test fix is open; use background watcher result, merge only if green and applicable. Then fetch and merge main into MOMMSEN-II claim PR 252, regenerate Kean brief, run local checker/tracker as needed, wait for green PR head, and merge under owner grant. Then continue b01 acquisition and b03 production; do not delete worker packet files.
