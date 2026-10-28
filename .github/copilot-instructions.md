# Executive-Orders Copilot repository instructions

**Kean, first and last (owner, 2026-10-28):** at the start of every session read `HANDOFF/KEAN.md`, a short brief of open questions for the owner, owner decisions the tools do not yet carry out, and the newest results; then read only the newest entry of each `HANDOFF/notes-*.md`, not the whole files. Before proposing a tool, pilot, test or speed-up, run `python3 -I jobs/kean/kean.py search <words>`. Before stopping, record each result, each question for the owner and each owner decision with `jobs/kean/kean.py` (see `jobs/kean/README.md`), cite ask ids in your notes, and commit the register with the regenerated brief. A result that stays only in a chat is lost to every other session.

**On every new assignment, first read [HANDOFF/README.md](../HANDOFF/README.md), the newest agent notes in HANDOFF/, and AGENTS.md.** Do not ask the project owner to relay information that is already in GitHub.

Use `HANDOFF/notes-copilot.md` for your progress and asks before ending a session; do not edit another agent's notes. Follow the owner's Astra-specific standing rule in AGENTS.md when preparing work for Astra.

If a script, extraction or research scan is too large for your environment, put a bounded reproducible job under `jobs/<name>/` and its dependencies in `needs.txt`; inspect the job's results. Do not open a duplicate PR for data that a different agent is actively writing.

Preserve immutable legal codebook 2.0.0 and the October 14, 2026 cutoff. Existing provisional status labels, Opus research notes, archival search hits and evidence image checksums do not independently establish operative-clause histories or legal cessation. A successful CI build is not human legal certification.

Write findings and artifacts to GitHub, with sources, frozen inputs, distinct case identities, documented uncertainty and explicit next steps.
