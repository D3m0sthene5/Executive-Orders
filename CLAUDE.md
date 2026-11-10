# Executive-Orders Claude Code instructions

**Kean, first and last (owner, 2026-10-28):** at the start of every session read `HANDOFF/KEAN.md`, a short brief of open questions for the owner, owner decisions the tools do not yet carry out, and the newest results; then read `HANDOFF/NEWEST.md` (the newest entry of each `HANDOFF/notes-*.md`, generated; `python3 -I jobs/kean/kean.py newest` prints the current ones), not the whole notes files. Before proposing a tool, pilot, test or speed-up, run `python3 -I jobs/kean/kean.py search <words>`. Before stopping, record each result, each question for the owner and each owner decision with `jobs/kean/kean.py` (see `jobs/kean/README.md`), cite ask ids in your notes, and commit the register with the regenerated brief. A result that stays only in a chat is lost to every other session.

**Coordinate by model tier (owner, 2026-10-29):** unless a task is small, the strongest available model coordinates and keeps legal judgment, control adjudication and integration; it delegates bounded, disjoint tasks with exact inputs and deliverables to cheaper models, and deterministic work to scripts or jobs. Skip delegation when briefing and checking a worker would cost about as much as the task. Review, blinding and different-family rules are unchanged; record each worker's model, tokens and time. Full rule: [`research/readiness/owner_rulings/2026-10-29-tiered-delegation.md`](research/readiness/owner_rulings/2026-10-29-tiered-delegation.md).

**Spend tokens where Bentham says (owner, 2026-11-05):** before any agent wave, read `jobs/bentham/output/PLAN.md` (rebuilt daily from measured yields, costs and the orders each action unlocks) and run ranked actions in rank order within the owner's budget. After each batch run `python3 -I jobs/bentham/bentham.py gate --action ID --batches FILE` and stop on STOP. When the wave ends, run `bentham.py usage --wave NAME --phase LABEL` and commit the sanitized output so the next plan is measured on it. See `jobs/bentham/README.md`.

**No wave launches without Augur (proposed by Claude 2026-11-10, after the overnight Codex wave; in force when the owner merges):** write the wave as a plan (`WAVE.json`). It must pass `python -I jobs/augur-launch/augur.py check WAVE.json` before any agent spends, with:
- an outcome objective, never spend or activity;
- Bentham actions only;
- a ramp from a 1-lane, 30-order stage 0 for any configuration not yet measured;
- every matching Kean warning answered, and a pre-mortem;
- a review by another model family or the owner, bound to the plan's hash.

An unranked Bentham refusal is a stop, never advice. The claim kit refuses orders outside the named Bentham action (`jobs/claim-kit/admission.py`). The Savigny supervisor stops lanes on measured spend per verified claim, not on what agents report. See `jobs/augur-launch/README.md`.

**Lean tree (2026-11-08):** never list or search the whole ~194,000-file tree; name the folder you need. The root `.ignore` keeps Grep out of outputs and data unless you give their path, and `.claude/hooks/ockham_lean_tree.py` refuses bare `git ls-files`, `find .`, `ls -R` and root-wide `**` globs. Details in `AGENTS.md`.

At the beginning of every session read `HANDOFF/KEAN.md`, `HANDOFF/README.md`, the newest entry of each agent's notes (including `HANDOFF/notes-astra.md`), plus `AGENTS.md`. GitHub is the coordination and evidence base; use it instead of asking the owner to transfer chat transcripts.

Before leaving, write the latest concise work summary and actionable requests to `HANDOFF/notes-claude.md` only. Do not edit Astra/Codex notes. For scripts too large for the current execution environment, commit a bounded job under `jobs/<name>/` with `needs.txt`, start it with `gh workflow run run-jobs.yml --ref <branch> -f job=<name> -f only=true` (no push starts a run, Kean D-20261109-no-push-runs), and verify its `output/STATUS.json`.

Preserve the immutable evidence/legal codebook, distinguish historical document discovery from identity authentication, and separate AI status hypotheses from source-backed full-lifecycle dossiers and independent human certification. Never inflate the 0 certified whole-lifecycle count by bulk machine review.

## Owner preference: names

Danny likes names drawn from history, not only American history: the Founders and the Federalist Papers, Supreme Court cases and justices, and niche references from any era or country. Choose by how well the name fits the tool's job first, then by how niche it is; nationality does not matter. Use them for new tools, jobs, branches you choose, and projects, while keeping file and folder names descriptive enough to find.
