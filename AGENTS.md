# Repository-wide standing instructions for research agents

Before doing project work in any session, read `HANDOFF/README.md` and the latest relevant notes in `HANDOFF/`, beginning with the newest entries. Check the current GitHub `main` state; do not rely on an older conversational summary.

**Standing rule from the project owner (2026-10-17):** Read `HANDOFF/README.md` in the Executive-Orders repo at the start of every session, and leave your notes in `HANDOFF/notes-astra.md` before you stop. Run scripts that are too big for your container as jobs under `jobs/`.

For an Astra session specifically, update `HANDOFF/notes-astra.md` **before ending**. Claude and Codex must instead update only their respective `notes-claude.md` and `notes-codex.md` files, as `HANDOFF/README.md` directs, avoiding concurrent edits to Astra's notes. Other agents create their own `notes-<agent>.md`.

For large network scans, big corpus extraction, or commands that exceed the agent's execution environment, create a deterministic, bounded job under `jobs/<name>/`, list its data dependencies in `needs.txt`, and inspect `output/STATUS.json` after GitHub Actions finishes. Preserve failures, query parameters, exact URLs, hashes, and reproducibility metadata.

The scientific objective is **the legally defensible lifecycle of each executive order from 1789 to the October 14, 2026 cutoff**, plus historical census recovery. Distinguish catalog hits, editorial citation links, producer claims, research hypotheses, mechanically complete draft dossiers, and independently human-reviewed whole-lifecycle conclusions. Never auto-promote one tier to another, change an immutable codebook or count unverified orders. Prioritize enabling infrastructure that makes subsequent research cheaper, broader, faster and easier to audit.

Commit code, primary-source acquisition outputs and clear status reports to GitHub. Prefer separate files/branches and pull requests for parallel agents; keep handoff concise and put large data under `research/` or `jobs/`.
