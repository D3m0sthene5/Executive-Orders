# 02 - Frameworks, durable engines, agent memory and task trackers

Researched 2026-11-06. "Opened" means I fetched the page; fetched pages were summarized by a small model, so quoted figures are as that summary reported them. Tools marked "not opened" were judged from search results or background knowledge and should be re-checked before anyone relies on them.

## Bottom line

The project's real coordination failures (Claude and GPT sessions colliding in git notes, duplicated work, stale inputs) are not the problem durable-workflow engines or memory products solve. Those products solve crash recovery and conversational recall. Kean (findings, asks and decisions register, append-only JSONL, generated brief, `search`, CI check) and Bentham (ranks actions by expected dossiers per dollar, with a STOP gate) already do what Beads, Taskmaster, Mem0, Zep and Letta offer for this project, and Bentham has no counterpart in any product I found. The most useful outside ideas are narrow: hash-based IDs and work leases (Beads), an MCP wrapper so GPT and Claude sessions query Kean without reading files, and (only if the 6-hour and serial-execution limits keep biting) DBOS or Restate as a resume-on-failure layer for the claim-kit LLM batches.

Gap I could not close: I did not read the project's own collision logs, so I cannot say which collisions are git-merge conflicts in markdown (fixable with append-only files and unique IDs) versus two sessions starting the same work (needs a lease). Kean IDs look like `A-20261028-3` (date plus counter); if the counter is computed from the local file, two sessions can mint the same ID. That is a hypothesis to test in `kean.py`, not something I verified.

---

## A. Durable workflow engines

Context for all of them: the project's jobs are deterministic Python on GitHub Actions, and the heavy cost is model tokens ($10-25 per batch) plus downloads. Engine fees are negligible (one source computes all four engines at under 0.5% of the model bill for a 51-step agent run). The catch is that every engine below needs a long-running worker process on a machine you provide; GitHub Actions runners are ephemeral and capped at 6 hours, so adopting any of them means renting or owning a small always-on host (or running workers inside Actions and accepting their lifetime).

- **DBOS Transact** ([pricing page, opened](https://www.dbos.dev/pricing)) - an MIT-licensed Python/TypeScript library that checkpoints each workflow step into a Postgres database you supply, so a crashed run resumes from the last finished step.
  - Cost: library free; Pro $99/month (2 seats, 1M checkpoints, $50 per extra million), Teams $499/month, as of the 2026-11 page. A [third-party comparison](https://www.beri.net/article/temporal-vs-inngest-vs-restate-vs-dbos-durable-execution-agent-cost) says $0 engine fee without the paid Conductor console. Maturity: Pydantic AI ships a co-maintained DBOS integration ([Pydantic docs, opened](https://pydantic.dev/docs/ai/durable-execution/overview/)). Stars and user counts: not verified.
  - Evidence: only vendor pages and comparison blogs; no user reports found. The comparison notes that every step writes to your database, so very high step counts can strain a small Postgres.
  - Fit: addresses "a claim-kit batch dies halfway and the 10-25 USD of draft and review tokens is repeated" and the freshness-guard throwaway. A workflow per batch, one step per order or per reviewer call, with idempotent steps, would resume instead of restarting. Does nothing for downloads, OCR or git bloat. Adoption: about 1-2 days for a pilot (small Postgres on Neon/Supabase free tier or a $5 VPS, one worker host). It conflicts with the "sealed packet" model only if steps are not deterministic; packet hashes make the steps idempotent already.
  - Verdict: **TRY** (small pilot on one claim-kit batch). Cheapest and closest to the existing Python style; do it only if resumption of partial batches is a measured loss in Bentham's cost data.

- **Restate** ([third-party profile, opened](https://www.beri.net/tools/restate)) - a single-binary durable execution server with Python, TypeScript, Java, Go and Rust SDKs.
  - Cost: server free to self-host under BSL 1.1 (source-available, converts to Apache 2.0 after four years); Cloud Free 50k actions/month with 1-day retention, Starter $75/month. Prices came from a third-party summary, not the vendor page. Maturity: founded 2024, $20M Series A reported September 2026, "hundreds of firms."
  - Evidence: practitioners call it younger and less battle-tested than Temporal (same source). Short history retention on low tiers hurts auditability.
  - Fit: same as DBOS but with no Postgres dependency (one binary). The project needs audit trails kept in git anyway, so engine history is not a system of record.
  - Verdict: **WATCH**. DBOS is closer to this project's Python and Postgres-free-tier setup; pick Restate only if you dislike running Postgres.

- **Temporal** (opened: [Google Cloud pay-as-you-go post, 2026-08-31](https://temporal.io/blog/temporal-expands-google-cloud-partnership-with-pay-as-you-go-pricing); [LangGraph plugin post](https://temporal.io/blog/temporal-langgraph-plugin-durable-execution)) - the market-leading durable execution platform; per-action billing about $50 per million actions on Cloud, $150 free credits for new sign-ups (the page also mentions $1,000 Marketplace credits and does not reconcile them).
  - Evidence: workflow history is capped at 51,200 events or 50 MB (comparison article), so large fan-outs need continue-as-new.
  - Fit: strongest engine, heaviest to run, aimed at multi-team production services. A one-student project does not need it.
  - Verdict: **SKIP** for now; **WATCH** only if DBOS pilot hits a limit.

- **Inngest** ([self-hosting docs, opened](https://www.inngest.com/docs/self-hosting.md)) - event-driven step functions; hard cap of 1,000 steps per run and 100 concurrent steps on Pro (comparison article). Self-hosting runs on SQLite plus in-memory Redis by default and does not scale past one node without external Postgres and Redis; Inngest does not guarantee support for self-hosters. License not stated on the page I opened.
  - Verdict: **SKIP**. Built for web-app event handlers, not 15,000-order batch pipelines.

- **Hatchet** ([profile, opened](https://automationatlas.io/tools/hatchet/)) - open-source (page contradicts itself on MIT versus Apache 2.0) task queue and durable workflow engine on Postgres, with Python, TypeScript and Go SDKs, concurrency keys and rate limits built in. About 8,000 stars (September 2026), 1-10 employees, YC W24; the profile says feature parity with Temporal is still maturing. Cloud: free for the first 100k runs, then roughly $10 per million runs (July 2026 entry) or usage-based (September entry); the two entries conflict.
  - Fit: the built-in per-key rate limits are the one feature that matches "per-host rate limits for govinfo, HathiTrust, Internet Archive downloads." But those limits already exist in the project's jobs.
  - Verdict: **WATCH**.

- **Trigger.dev** - not opened. TypeScript-first background jobs; **SKIP** (language mismatch).

## B. Agent frameworks

None of these is needed to run the claim kit, which is a deterministic pipeline with two model calls per claim. The relevant question is whether a framework removes code the project must otherwise maintain.

- **Pydantic AI** ([durable-execution docs, opened](https://pydantic.dev/docs/ai/durable-execution/overview/)) - typed, vendor-neutral agent library whose outputs are validated against Python models. It supports nine durable backends (Temporal, DBOS, Prefect, Restate, AWS Lambda, Absurd, pgtask, Azure Durable Task, Airflow); only one engine per agent.
  - Fit: structured-output validation maps naturally onto "CSV of decisions and clauses," and a single abstraction over Claude and GPT would let the same drafter run on either vendor. The project already has a frozen claim-kit contract and checkers (`checker-v4`), so the gain is small unless it replaces vendor-specific glue.
  - Verdict: **WATCH**; revisit if DBOS is piloted (the two compose).

- **OpenAI Agents SDK** ([2026 feature summary, opened](https://www.developersdigest.tech/blog/openai-agents-sdk-whats-new-2026)) - sandbox agents, serializable `RunState` for pause/resume, client-side sessions and a sandbox `Memory()` that distills lessons from past runs into files. The summary calls non-OpenAI models its weakest fit, and notes minor releases have broken APIs (pin versions). `RunState.from_json()` does not authenticate snapshots.
  - Verdict: **SKIP** (Astra/Codex already supplies this on the GPT side; the project gains nothing by wrapping it).

- **Claude Managed Agents** ([docs, opened](https://platform.claude.com/docs/managed-agents); [pricing from a Substack review](https://trilogyai.substack.com/p/the-plumbing-wars-are-claude-managed)) - Anthropic-hosted agent harness in beta (header `managed-agents-2026-04-01`), sessions persist server-side, not eligible for zero data retention. Reported price $0.08 per active session-hour on top of tokens. Claude models only; multiagent orchestration and Outcomes need a separate research-preview application.
  - Fit: could host long reviews that now fail on container authentication problems, but locks the pipeline to one vendor, which breaks the "different-family reviewer" rule the project already uses (Claude drafts, GPT reviews, and so on). 
  - Verdict: **WATCH**.

- **Claude Agent SDK** - not opened (the project's Claude Code sessions are its descendants). It is the harness already in use; **no action**.

- **LangGraph** - not opened directly; Temporal's own post ([opened](https://temporal.io/blog/temporal-langgraph-plugin-durable-execution)) states that LangGraph checkpoints preserve data but not execution: a dead process must be detected and restarted by something you build, and Temporal's plugin that fixes this is Public Preview. 
  - Verdict: **SKIP**. Adds a graph abstraction over a pipeline that is already a Python DAG of jobs.

- **Considered and rejected (not opened):** CrewAI, AutoGen/AG2, DSPy, Mastra, smolagents, Google ADK. Role-play and chat-orchestration frameworks, or (DSPy) prompt optimization, which is useful only if the project begins tuning drafter prompts against a labelled set; revisit DSPy then. Mastra is TypeScript.
- **Inspect AI** (UK AISI eval framework; search only, not opened) - an evaluation harness with logs. The project's planted-control blind review is its own, stricter design; **SKIP** unless a published methodology comparison is wanted.

## C. Protocols

- **MCP** (Model Context Protocol; version negotiation `2026-07-28` appears in OpenAI SDK release notes) - the common tool interface; Claude Code and Codex CLI both act as clients (Basic Memory's page lists both).
  - Fit: the specific, cheap use is a small stdio MCP server wrapping `kean.py search`, `add-finding`, `add-ask`, and a lease call, so GPT and Claude sessions share one interface and never hand-edit the shared files. Build time: roughly half a day. It replaces reading `HANDOFF/*.md` (about 60,000 tokens a session before Kean, per Kean's README).
  - Verdict: **TRY** (build it, do not buy it).

- **A2A (Agent2Agent)** ([Linux Foundation release, 2026-04-09, opened](https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year?hs_amp=true)) - version 1.0 spec, 150+ supporting organizations, 22,000+ GitHub stars, Azure and Bedrock integration. The release names no specific production deployments and gives no usage metrics; those claims come from the foundation and its members.
  - Fit: it connects agents that run as network services. The project's agents are CLI sessions that do not accept inbound calls.
  - Verdict: **SKIP**.

## D. Cross-session and cross-vendor memory

The shared design requirement is a store both Claude and GPT can read and write, whose entries are reviewable and tied to source, since the project forbids unreviewed machine claims from entering the dataset. A [2026-04 survey](https://dev.to/sebastian_chedal/agent-memory-038-knowledge-systems-compared-2026-guide-568p) (by a consultancy, no original testing) found that no memory system natively supports human review of agent-proposed knowledge and that vendor benchmark scores (LOCOMO, LongMemEval) are vendor-reported and easy to overfit. Kean's append-only register with explicit `add-ask` and owner decisions is already that review layer.

- **Mem0** - not opened; searches show Apache 2.0 license and large star count (about 48k, secondhand). A [developer write-up](https://dev.to/mukesh_13/mem0-auto-resolves-memory-conflicts-for-you-until-it-silently-deletes-one-you-still-need-4f4m) (opened) shows its LLM conflict resolver can silently delete a still-valid memory; the evidence is one constructed example plus one anecdote, but the mechanism (LLM decides ADD/UPDATE/DELETE) is real. An LLM that deletes facts is unacceptable for a project whose evidence must be immutable.
  - Verdict: **SKIP**.

- **Zep / Graphiti** ([Graphiti repo, opened](https://github.com/getzep/graphiti); [Zep deprecation notice, opened](https://help.getzep.com/ce-deprecation-notice)) - Graphiti is an Apache-2.0 temporal knowledge graph (32.5k stars) whose facts carry validity windows and are invalidated rather than deleted. It requires you to run Neo4j, FalkorDB or Neptune and uses LLM calls for extraction. Zep Community Edition is deprecated; only Zep Cloud (free tier) and Graphiti remain. Its reference MCP server has no authentication.
  - Fit: the "valid from/until" model resembles what the project asks of each executive order (in force, ceased when, why), which makes it conceptually tempting. But the project's lifecycle claims must cite byte spans of held documents and pass checkers; an LLM-extracted graph would be a hypothesis layer, which the project's rules say must stay separate from certified claims. A plain table with start and end dates is simpler and auditable.
  - Verdict: **SKIP**.

- **Letta** (Context Repositories, [blog 2026-02-12, opened](https://www.letta.com/blog/context-repositories)) - agent memory stored as git-versioned files, with each subagent writing in an isolated git worktree and merging back. Works for Letta Code agents only; maturity and limitations not stated.
  - Fit: validates the pattern the project already uses (memory as files in git) and the worktree-per-writer idea, but requires adopting Letta's agent runtime.
  - Verdict: **WATCH** (borrow the worktree-per-writer pattern; do not adopt the runtime).

- **Cognee** - not opened; document-to-graph open-core, opaque managed pricing per the survey. **SKIP** (same objection as Graphiti).

- **Claude memory tool** ([docs, opened](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)) - an API tool in which Claude issues file commands (`view`, `create`, `str_replace`, `insert`, `delete`, `rename`) under `/memories` and your code executes them; storage is yours, and the page does not document sharing one store among agents. The SDK includes a local-filesystem implementation.
  - Fit: GPT sessions cannot use it, so it does not address Claude-GPT collisions; for Claude-only API runs it would let the drafter keep a lessons file, which the repo's notes already do. 
  - Verdict: **SKIP**.

- **ChatGPT memory and Claude.ai memory** - consumer features, not shared across vendors and not scriptable. **SKIP**. (The only cross-vendor route is a store you own, reached by MCP.)

- **Basic Memory** ([repo, opened](https://github.com/basicmachines-co/basic-memory)) - AGPL-3.0, about 3.6k stars; notes are plain Markdown on disk indexed by local SQLite, exposed over MCP to Claude Desktop, Claude Code, Codex CLI, Cursor and VS Code; ChatGPT through Custom GPT actions. Cloud $15/month (as listed). Concurrent-edit handling is not described beyond overwrite protection in `write_note`.
  - Fit: it is the closest product to "one shared markdown store with an MCP interface," but the project already has that in git, and its failure mode is the same (concurrent writers). The repo's 9 GB history makes a local index over it slow to build; an index over `HANDOFF/` and the register only would be cheap.
  - Evidence: a [single-user write-up](https://dev.to/arasovic/sharing-memory-between-three-ai-agents-claude-code-codex-and-hermes-394h) (opened) shares markdown between Claude Code, Codex and Hermes via Syncthing with conflict files surfaced for a human decision; one smoke test, anecdotal, but it shows the working rule set: no wholesale rewrites, re-read before writing, never silently merge.
  - Verdict: **WATCH**.

## E. Agent task trackers shared by Claude and GPT

- **Beads (`bd`)** ([repo, opened](https://github.com/steveyegge/beads); [Thoughtworks Radar, opened](https://www.thoughtworks.com/pt-br/radar/tools/beads)) - an MIT-licensed dependency-aware issue graph on Dolt (a version-controlled SQL database) for coding agents. About 28k stars, 1.9k forks, about 1.1k open issues. Hash-based IDs (`bd-a1b2`) avoid ID collisions; Dolt merges at cell level; sync is `bd dolt push/pull` against a git remote; named integrations include Claude Code and Codex CLI. Version 1.0 added work leases, an HTTP mode (experimental, with documented behavior gaps) and sync to Linear, Jira and GitHub Issues.
  - Evidence: Thoughtworks moved it from Assess (April 2026) to Trial (November 2026), saying many of its developers use it by default; it warns that schema upgrades are in place so clients on different versions cannot share a store (pin one version). A [DoltHub post](https://www.dolthub.com/blog/2026-04-02-restoring-beads-classic/) (opened) documents that embedded Dolt allows one writer at a time and that concurrent `bd init` hit a Dolt bug. [Maggie Appleton's review](https://maggieappleton.com/gastown) calls the surrounding Gas Town design chaotic and costly ($2,000-5,000 per month estimated) while saying Beads' git-stored-tasks idea is sound. Beads tracks coding tasks; nobody reports using it for evidence-bound research pipelines.
  - Fit: addresses "duplicated work" (leases) and ID collisions. Costs: a Dolt dependency, a second source of truth next to Kean, and Dolt data in or beside an already 8.4 GB `.git`. Kean already holds asks, decisions and findings with a CI check; Beads would add only the lease and the dependency graph.
  - Verdict: **TRY, narrowly** - first copy the two ideas into Kean (random-suffix IDs; a `lease` command that records which session holds a batch with an expiry, committed to a small file). Pilot Beads itself only if that proves insufficient.

- **Taskmaster AI (`claude-task-master`)** ([review, opened](https://www.chatforest.com/reviews/task-master-mcp-server/)) - turns a PRD into dependency-ordered tasks via an MCP server; about 27k stars; MIT with Commons Clause (not OSI open source). The review rates it 3.5/5 and lists open issues: telemetry reportedly capturing full prompts by default (#1681), status updates that do not persist and task-ID collisions (#1683, #1647), no npm release in 49 days as of April 2026.
  - Fit: it plans software tasks from a spec; the project's planning problem is ranking known work by measured yield per dollar, which Bentham does. Its local `tasks.json` would add a third collision-prone file.
  - Verdict: **SKIP**.

- **Linear with agents** ([Linear guide, opened](https://linear.app/enablement/guide/ai-agents)) - issues can be delegated to agents (the page names Cursor, Copilot, Codex, Devin, Warp, Sentry; it does not mention Claude); coding tasks return as pull requests; Beads syncs to it. Pricing not on the page.
  - Verdict: **SKIP** (adds a paid third system; GitHub Issues is free).

- **GitHub Agent HQ** ([GitHub blog 2026-02-04, opened](https://github.blog/2026-02-04-pick-your-agent-use-claude-and-codex-on-agent-hq/)) - assign one issue to Copilot, Claude, Codex or all three and compare draft pull requests; requires Copilot Pro+ or Enterprise; Claude and Codex are in public preview; each session consumes one premium request; background sessions are Copilot only.
  - Fit: a convenient way to put Claude and GPT on the same issue, but it duplicates the project's own handoff and wave process, spends a second budget, and does not touch blind review or sealed packets. Could be tried for code-only chores (workflow fixes).
  - Verdict: **WATCH**.

## F. Research-pipeline platforms (2026)

I searched for platforms for multi-step AI research pipelines (not coding agents). The results were agent-hosting products (Claude Managed Agents above, OpenAI Agents SDK sandbox) and eval harnesses (Inspect AI). I found none that offers sealed evidence packets, byte-span citation checks or independent blind review with planted false controls; that part of the project is bespoke and nothing I found replaces it.

## What the home-grown tools already cover

| Product capability | Project tool that already does it |
|---|---|
| Persistent cross-session task memory (Beads, Taskmaster) | Kean register and generated `HANDOFF/KEAN.md`, `search`, CI `check --strict` |
| Memory of results and lessons (Mem0, Letta, Claude memory tool) | Kean findings (what was tried, expected, happened, verdict, lesson) |
| Ranking what to spend tokens on | Bentham `plan` (dossiers per dollar, 60-day half-life) and `gate` (CONTINUE, PILOT, STOP); no product found offers this |
| Human approval of agent-proposed knowledge | Owner asks and decisions, `wire` to show whether tools carry them out |
| Token telemetry | Bentham `usage` |
| Tiered delegation | CLAUDE.md rule of 2026-10-29 |

Not covered by anything in the repo as far as I saw: leases on batches (to stop two sessions starting the same work) and automatic resume of a half-finished claim-kit batch.

## Ranked top 5 for this scope

1. **Copy Beads' hash-style IDs and lease idea into Kean** (in-house, hours of work, zero dependency) - targets the collision and duplicated-work pain directly.
2. **MCP wrapper around `kean.py`** (in-house, about half a day) - one interface for Claude and GPT sessions; cuts start-up reading.
3. **DBOS Transact pilot on one claim-kit batch** (TRY) - only if Bentham's data shows partial-batch reruns cost real money.
4. **Beads proper** (TRY only if item 1 proves insufficient) - Trial on the Thoughtworks Radar, but adds Dolt and a second register.
5. **Pydantic AI with DBOS** (WATCH) - vendor-neutral typed drafter; adopt only if the DBOS pilot succeeds and the drafter should run on both vendors.

Nothing in this scope merits ADOPT NOW as a product.
