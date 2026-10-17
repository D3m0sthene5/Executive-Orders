# How Copilot, Claude, Codex and Astra can collaborate without copying chat transcripts

**Status (2026-10-17):** asynchronous shared-repository handoffs are already usable. Repository instructions are in `AGENTS.md`, `.github/copilot-instructions.md`, `CLAUDE.md` and `HANDOFF/README.md`. Direct automatic agent invocations are **not configured** by these files; a separate GitHub App integration, credential and workflow may be required for each service.

## Default: GitHub as evidence repository and communication channel

1. Each agent begins by reading `HANDOFF/README.md`, newest other-agent notes, the immutable legal codebook, the task's source manifest, and `main` HEAD.
2. Work moves through **GitHub issues → a separate branch/job → source-linked artifacts → PR or commit → tests and review → a note in that agent's own HANDOFF file**. Each note identifies the originating issue, exact artifacts and decisions requested from the next agent.
3. Restrict simultaneous writers to their own notes and working paths. Never silently overwrite another agent's in-progress dataset; reconcile branches explicitly. The canonical accepted scientific ledger changes only after its declared legal/review gates.
4. A heavy extraction or network harvest becomes a `jobs/<job>/` execution with input dependencies and an auditable `output/STATUS.json`. The next agent can pick it up without transferring context by hand.

## Agent roles where parallelism actually helps

- **Claude / Opus:** large-scale primary-source discovery, reading historical research shards, proposing candidate operative clause histories and explicitly recording uncertainties.
- **Astra / ChatGPT:** evidence reconciliation, adjudication design and cross-source challenges; verify that a proposed transition is genuinely first-effective and distinguish source metadata from legal authority.
- **Copilot cloud coding agent or Codex:** implement/review acquisition tools, deduplication, tests, indexes and human-review interfaces from documented issue specifications.
- **Independent human reviewers:** inspect and approve frozen cases if and when whole-lifecycle certification is required. An AI review by another model is still an AI review.

## Optional true automated agent-to-agent workflow (not yet active)

- GitHub Copilot cloud agent can work from assigned GitHub issues and produce PRs, subject to the account's Copilot entitlement and repository permissions. The repository already has the documented Copilot instructions file.
- The official Anthropic `anthropics/claude-code-action@v1` can respond to `@claude` on approved issue/PR events after the GitHub App and a secure `ANTHROPIC_API_KEY`, compatible token, or workload-identity setup are configured.
- The official `openai/codex-action` can run Codex from trusted GitHub Actions events using an `OPENAI_API_KEY` stored in repository Actions secrets. A separate connected ChatGPT session does **not** thereby become an always-on responder.
- Compose work across events with **issue labels / branch and PR states / explicit completion manifests**, rather than invoking models to chat endlessly. For security, Github Actions comments made with the default `GITHUB_TOKEN` generally do not trigger another workflow. A narrowly permitted GitHub App token or dispatch action is required for safe cross-workflow triggering.

Reference documentation:
- Copilot repository instructions: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions
- Copilot agents: https://docs.github.com/en/copilot/responsible-use/agents
- Claude Code GitHub Action: https://github.com/anthropics/claude-code-action
- Anthropic action setup: https://github.com/anthropics/claude-code-action/blob/main/docs/setup.md
- Codex Action: https://github.com/openai/codex-action
- GitHub Actions comment-trigger limitation: https://github.com/anthropics/claude-code-action/blob/main/docs/faq.md

## Should we automate everything?

The useful part is **automatic transfers of case and evidence artifacts**, not autonomous model debates. For the EO project, begin with one source-retrieval issue, one independent review issue and one PR per large batch, with a bounded attempt budget, provenance and explicit handoff note. Avoid recursive bot-to-bot loops, excessive context tokens, and machine certification of legal status. No API credentials or tokens belong in this repository.
