# Executive-Orders Claude Code instructions

**Kean, first and last (owner, 2026-10-28):** at the start of every session read `HANDOFF/KEAN.md`, a short brief of open questions for the owner, owner decisions the tools do not yet carry out, and the newest results; then read only the newest entry of each `HANDOFF/notes-*.md`, not the whole files. Before proposing a tool, pilot, test or speed-up, run `python3 -I jobs/kean/kean.py search <words>`. Before stopping, record each result, each question for the owner and each owner decision with `jobs/kean/kean.py` (see `jobs/kean/README.md`), cite ask ids in your notes, and commit the register with the regenerated brief. A result that stays only in a chat is lost to every other session.

At the beginning of every session read `HANDOFF/KEAN.md`, `HANDOFF/README.md`, the newest entry of each agent's notes (including `HANDOFF/notes-astra.md`), plus `AGENTS.md`. GitHub is the coordination and evidence base; use it instead of asking the owner to transfer chat transcripts.

Before leaving, write the latest concise work summary and actionable requests to `HANDOFF/notes-claude.md` only. Do not edit Astra/Codex notes. For scripts too large for the current execution environment, commit a bounded job under `jobs/<name>/` with `needs.txt`; use GitHub Actions and verify its `output/STATUS.json`.

Preserve the immutable evidence/legal codebook, distinguish historical document discovery from identity authentication, and separate AI status hypotheses from source-backed full-lifecycle dossiers and independent human certification. Never inflate the 0 certified whole-lifecycle count by bulk machine review.

## Owner preference: names

Danny likes names drawn from history, not only American history: the Founders and the Federalist Papers, Supreme Court cases and justices, and niche references from any era or country. Choose by how well the name fits the tool's job first, then by how niche it is; nationality does not matter. Use them for new tools, jobs, branches you choose, and projects, while keeping file and folder names descriptive enough to find.
