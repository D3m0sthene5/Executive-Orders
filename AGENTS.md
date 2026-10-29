# Repository-wide standing instructions for research agents

**Kean, first and last (owner, 2026-10-28):** at the start of every session read `HANDOFF/KEAN.md`, a short brief of open questions for the owner, owner decisions the tools do not yet carry out, and the newest results; then read only the newest entry of each `HANDOFF/notes-*.md`, not the whole files. Before proposing a tool, pilot, test or speed-up, run `python3 -I jobs/kean/kean.py search <words>`. Before stopping, record each result, each question for the owner and each owner decision with `jobs/kean/kean.py` (see `jobs/kean/README.md`), cite ask ids in your notes, and commit the register with the regenerated brief. A result that stays only in a chat is lost to every other session.

**Coordinate by model tier (owner, 2026-10-29):** unless a task is small, the strongest available model coordinates and keeps legal judgment, control adjudication and integration; it delegates bounded, disjoint tasks with exact inputs and deliverables to cheaper models, and deterministic work to scripts or jobs. Skip delegation when briefing and checking a worker would cost about as much as the task. Review, blinding and different-family rules are unchanged; record each worker's model, tokens and time. Full rule: [`research/readiness/owner_rulings/2026-10-29-tiered-delegation.md`](research/readiness/owner_rulings/2026-10-29-tiered-delegation.md).

Before doing project work in any session, read `HANDOFF/README.md` and the latest relevant notes in `HANDOFF/`, beginning with the newest entries. Check the current GitHub `main` state; do not rely on an older conversational summary.

**Standing rule from the project owner (2026-10-17):** Read `HANDOFF/README.md` in the Executive-Orders repo at the start of every session, and leave your notes in `HANDOFF/notes-astra.md` before you stop. Run scripts that are too big for your container as jobs under `jobs/`.

For an Astra session specifically, update `HANDOFF/notes-astra.md` **before ending**. Claude and Codex must instead update only their respective `notes-claude.md` and `notes-codex.md` files, as `HANDOFF/README.md` directs, avoiding concurrent edits to Astra's notes. Other agents create their own `notes-<agent>.md`.

**Standard research procedure (owner, 2026-10-17):** work orders through the readiness pipeline in [`research/readiness/README.md`](research/readiness/README.md): pick work from the top of `jobs/readiness-tracker/output/SHARED_UNLOCKS.csv`; request sources through `research/readiness/FETCH_QUEUE.jsonl` instead of fetching by hand; start each order from its draft in `jobs/claim-drafts/output/`; commit claims to `research/readiness/claims/<agent>-<date>.jsonl`; and report tokens and time per order in your HANDOFF note. The working progress measure is orders ready for human review in `jobs/readiness-tracker/output/TRACKER.md`.

For large network scans, big corpus extraction, or commands that exceed the agent's execution environment, create a deterministic, bounded job under `jobs/<name>/`, list its data dependencies in `needs.txt`, and inspect `output/STATUS.json` after GitHub Actions finishes. Preserve failures, query parameters, exact URLs, hashes, and reproducibility metadata.

The scientific objective is **the legally defensible lifecycle of each executive order from 1789 to the October 14, 2026 cutoff**, plus historical census recovery. Distinguish catalog hits, editorial citation links, producer claims, research hypotheses, mechanically complete draft dossiers, and independently human-reviewed whole-lifecycle conclusions. Never auto-promote one tier to another, change an immutable codebook or count unverified orders. Prioritize enabling infrastructure that makes subsequent research cheaper, broader, faster and easier to audit.

Commit code, primary-source acquisition outputs and clear status reports to GitHub. Prefer separate files/branches and pull requests for parallel agents; keep handoff concise and put large data under `research/` or `jobs/`.


For the model-neutral claim-kit dossier/decision workflow, follow [`jobs/claim-kit/AGENT_PROTOCOL.md`](jobs/claim-kit/AGENT_PROTOCOL.md).

**Ordinary production (owner, 2026-10-24):** use `kit.py prepare` / `view` /
`apply` / `batch-check`, then `kit.py complete` for reviewed batch selection,
gates, receipts, tally and authorized filing. Do not assign a model solely to
copy, format, count, file successful receipts or repeatedly poll a run. A fresh
research context and a separate independent reviewer exchange exact pinned
artifacts; send the coordinator paths, versions, outcomes and actionable
exceptions, not a restatement of every case. Supply applicable rules, qualified
prior findings/rejections, complete source access and remaining questions.
Where available use fresh contexts (`fork_turns="none"`); disclose the actual
model families and obey any different-family requirement. Keep substantive
control adjudication and after-reveal review with reviewers. A missing or
conflicting version is an exception, never inferred approval. Source-blocked
work uses the existing checkpoint/resume fingerprints and can publish reviewed
research steps without pretending to be a complete claim. See
[`jobs/claim-kit/BATCH.md`](jobs/claim-kit/BATCH.md) for the completion contract.

**Continuous status/lifecycle assignments (owner, 2026-10-24):** ordinary selection
and preparation include undecided orders with a full frozen dossier and status
unset. Carry qualified prior status research, corrections, rejected theories and
bounded search coverage into the lifecycle assignment. Keep one producer analysis
and, where independence rules permit, one independent source examination across
both output scopes, with distinct exact status and lifecycle verdicts. Status
review never substitutes for whole-case review or owner adoption. Use fresh
contexts between bounded assignments, retain blocked checkpoints, and count all
review, source, correction and integration costs; no efficiency saving is inferred
from routing or recovered records alone.
