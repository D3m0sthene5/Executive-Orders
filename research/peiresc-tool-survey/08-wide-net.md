# 08 - Wide net: swarm experience reports, similar projects, source-review tools

Researched 2026-11-06. "Opened" means I fetched the page; search snippets alone are marked. The proxy blocked direct curl to federalregister.gov, so API field claims there are unverified.

## Part 1. Experience reports on large agent swarms (measured vs anecdote)

**Anthropic, "How we built our multi-agent research system"** ([opened](https://www.anthropic.com/engineering/multi-agent-research-system))
- What: Lead Opus plus Sonnet subagents for web research. Free to read.
- Measured (Anthropic's own eval, ~20 queries, LLM judge): multi-agent beat single-agent Opus by 90.2%. Token usage alone explained ~80% of variance on BrowseComp. Agents use ~4x chat tokens; multi-agent ~15x. Parallelism cut wall time up to 90%. An agent-rewritten tool description cut later task time 40%.
- Anecdote: the example queries, user reports of "days saved".
- Failure modes listed: 50 subagents for simple queries, endless searching for sources that do not exist, vague delegation causing duplicate work, preference for SEO farms over authoritative sources, error compounding, lead-agent tweaks changing subagent behavior unpredictably.
- Fit: Directly applicable to claim-kit design. Copy: explicit delegation briefs (objective, output format, source guidance, boundaries), effort-scaling rules per task, external memory/filesystem for plans, resume-from-checkpoint. The 15x token multiplier is the number to budget against.
- Verdict: ADOPT NOW as design checklist (zero cost).

**Anthropic, "Building a C compiler with a team of parallel Claudes"** ([opened](https://anthropic.com/engineering/building-c-compiler))
- Measured: ~2,000 sessions, 16 agents, two weeks, ~2B input and 140M output tokens, just under $20,000, ~100k-line Rust compiler.
- What worked: the verifier. The author says the quality of the test harness was the most important factor. Task claiming via lock files in git; CI that blocks regressions; logs written to files with greppable error tags; a known-good oracle (GCC) to split a bug that stalled all agents.
- Failures: all agents hit the same bug so more agents did not help; new features broke old ones; frequent merge conflicts.
- Skeptic coverage: [The Register](https://www.theregister.com/2026/02/09/claude_opus_46_compiler/) notes the cost ignores training-data provenance; the author concedes quality limits.
- Fit: Strong analogue for this project's "checkers first" standard. The lesson that an oracle lets agents work disjoint slices maps to using OFR disposition tables and statute-effect lists as oracles for sampling. Task-lock-via-git is what the Kean register approximates.
- Verdict: ADOPT NOW as pattern (reading only).

**Cursor, "Scaling long-running autonomous coding"** ([opened](https://cursor.com/blog/scaling-agents))
- Anecdote with big numbers (hundreds of agents, ~1M-line browser in about a week, trillions of tokens), no controlled baseline, no cost per result. Several outputs "still need careful review". See also [Simon Willison's note](https://simonwillison.net/2026/Jan/19/scaling-long-running-autonomous-coding/) (snippet only).
- Useful and specific: locks became the bottleneck (20 agents at the throughput of 2-3); optimistic concurrency avoided that but flat agents dodged hard tasks and churned; planner / worker / judge-per-cycle with fresh starts worked best; an integrator role was dropped because it bottlenecked.
- Fit: Matches this project's collisions. Suggests replacing peer-to-peer markdown handoffs with one planner that writes disjoint task specs, workers that never coordinate with each other, and a judge deciding per cycle whether to continue. The current Opus-coordinates / Sonnet-workers rule already follows this.
- Verdict: ADOPT NOW as pattern; do not trust the scale claims.

**Cognition, "Don't Build Multi-Agents" (June 2025) and "Multi-Agents: What's Actually Working"** ([first](https://cognition.com/blog/dont-build-multi-agents), [second](https://cognition.com/blog/multi-agents-working), both opened)
- Principles: share full traces, not summaries; every action carries implicit decisions that conflict across parallel writers. 2026 update: advisor/reviewer agents with one writer work; clean-context review catches ~2 bugs per PR (58% severe) but that is Cognition's own measurement on its own PRs; cross-model "smart friend" (Claude plus GPT) helped on hard sub-tasks; arbitrary agent networks are "mostly a distraction"; weak-primary plus strong-friend failed.
- Fit: Supports the existing two-blind-reviewers design (clean context) and mixed Claude/GPT. It argues against many parallel writers touching shared state, which is the repo's merge-freeze problem. Writers should own disjoint files (per-order or per-batch outputs), never shared ledgers.
- Verdict: ADOPT NOW as design constraint.

**Berkeley MAST, "Why Do Multi-Agent LLM Systems Fail?"** ([opened](https://arxiv.org/html/2503.13657v2))
- Measured: 200+ traces from 7 open frameworks, kappa 0.88 between human annotators. Failure shares: specification issues 41.8% (step repetition 17%, ignoring task requirements 11%, not recognizing completion 10%), inter-agent misalignment 36.9% (reasoning-action mismatch 14%, proceeding on wrong assumptions 11.7%), verification failures 21.3%. Prompt fixes gave +9.4% to +15.6% success on one framework and did not close the gap.
- Caveat: frameworks tested are older chat-style systems, not current Claude Code sessions.
- Fit: A checklist for auditing this project's own traces. Failure-attribution against these categories is cheap with a script.
- Verdict: WATCH/use as taxonomy.

**ArcticSwarm, long-horizon multi-agent research** ([opened](https://arxiv.org/pdf/2609.01870))
- Measured on BrowseComp-Plus (830 questions, Qwen 3.5-27B): 82.6% vs 70.6% baseline swarm; majority voting over 40 single-agent runs saturates at 63.5%. Key findings: premature consensus (agents reading peers' partial findings anchor early), correlated search (independent replicas share paths, so voting cannot fix a shared mistake), review at commitment boundaries helps (86.4% accuracy with two verification sources vs 35.3% with none), upstream tool faults caused ~91% of subagent failures.
- Fit: Directly supports blind dual review and a separate "gather" phase that cannot see peers. It also warns that two reviewers from the same model family can share errors, which supports the different-family rule. Review raises token cost; the paper does not optimize it.
- Verdict: TRY as source of design ideas (publication is recent and single-group; not independently replicated).

**METR / Epoch MirrorCode** ([Epoch, opened](https://epoch.ai/mirrorcode); [METR post, opened](https://metr.org/blog/2026-04-10-mirrorcode-preliminary-results), thin)
- Measured: Opus 4.7 reimplemented a ~16k-line Go program in 14 hours for $251; one run lasted 19 days; one large run cost $2,600; leaderboard budgets 10B tokens per attempt. Contamination cannot be ruled out. Near-perfect, not perfect (2,000 of 2,001 tests).
- Fit: Calibrates what a single long-horizon agent costs when the verifier is a held-out end-to-end test. Argues for long single-agent runs against a strong checker over many short swarms.
- Verdict: WATCH (useful for budget sizing only).

**Gas Town / Beads discourse** ([Maggie Appleton critique, opened](https://maggieappleton.com/gastown); [Beads repo, opened](https://github.com/steveyegge/beads))
- Anecdote only. No benchmarks. Cost figures ($2-5k/month) are the critic's assumption. Reported problems: agents forget to check work, merge-agent rewrites work, difficult onboarding, parallelism topping out around five workers, creator does not review code. Ideas worth keeping: persistent task identity with disposable sessions; work queues; merge queue.
- Beads: ~28k stars, MIT, Dolt-backed dependency-graph tracker with `bd ready`/`--claim`, writes AGENTS.md integration for Claude Code and Codex. Embedded mode is single-writer; multi-writer needs a dolt server; upgrades across clones need a coordinated sequence.
- Fit: Beads is a plausible replacement for markdown handoff notes plus Kean for task claiming and dependency ordering across Claude and Codex. Cost: several hours to pilot, a new database to keep consistent in a repo that already struggles with churn. Note the repo already has the Kean register, which does part of the job; the coordination researcher likely covers this in depth.
- Verdict: Gas Town SKIP. Beads TRY on one branch with a small task graph, only if Kean's search/claim proves too weak.

**HN thread on parallel Claude Code agents in tmux with markdown specs** ([alt-hn mirror, opened](https://alt-hn.vercel.app/item/47218318))
- Anecdotes: 2-3 agents beat 6-8 because of merge conflicts; context drift fixed with a shared ground-truth file; Max plan limits hit in under an hour; deny-list bypasses (`unlink` instead of `rm`). Nothing measured.
- Fit: Corroborates this project's collision and cost experience. No new tool.
- Verdict: Evidence only.

**Other blog claims I opened and discount**: a DEV Community piece on swarm cost/failure ([opened](https://dev.to/tomtokita/the-truth-about-agent-swarming-what-the-gurus-wont-tell-you-about-cost-failure-and-security-1775)): its failure-rate numbers (64% hierarchical, 68% self-organized) are secondhand, conditions not stated; its cost model is the author's, and the author runs a consultancy.

### Practices ranked by evidence
- Measured: token budget explains most research quality variance (Anthropic, BrowseComp); independent review at commitment points raises accuracy (ArcticSwarm); correlated replicas do not fix errors (ArcticSwarm); specification and verification failures dominate (MAST); verifier quality dominates long runs (C compiler, but n=1).
- Anecdote: flat swarms churn; locks bottleneck; single-writer is safer; 2-5 parallel workers is the practical cap; persistent identity beats persistent sessions.
- Not found: any report of a swarm doing legal-history or document-status classification at scale with human certification. The closest are the annotation papers below.

## Part 2. Similar projects and reusable work

**Thrower (2017) and Lowande and Poznansky, "Executive Action that Lasts"** ([opened](https://www.cambridge.org/core/product/AABF3ACB297FA8B252507582A9B4B68E/core-reader); [supplement, opened](https://static.cambridge.org/content/id/urn:cambridge.org:id:article:S0143814X23000442/resource/name/S0143814X23000442sup001.pdf))
- The closest prior art. Codes about 6,500 executive orders (1937 to Jan 2021) for whether they were formally revoked. Sources: NARA's Executive Orders Disposition Tables through 2017, Federal Register after. They found 20 missing revocations and 65 orders credited to the wrong revoking president in Thrower's data, and state that the Disposition Tables are unofficial and have been revised. About 74% of non-ceremonial actions were never revoked. They explicitly note formal revocation is an imperfect measure of whether an order is still operative, which is this project's thesis. Immutability was coded with string matching plus hand coding (kappa 0.76), about 63% without a human reading them.
- Fit: A baseline to compare against and a source of known error counts (use as a free control set: the 20 added revocations and 65 misattributions are known corrections). I could not locate the replication archive from the pages I opened; the article's data availability statement (past the part I could read) or Thrower's AJPS Dataverse deposit should hold it.
- Verdict: ADOPT NOW as comparison dataset and citation; obtain replication files.

**NARA Executive Orders Disposition Tables** ([opened](https://www.archives.gov/federal-register/executive-orders))
- Cover Jan 8, 1937 to Jan 19, 2017; updates discontinued Jan 20, 2017. Web pages with a search feature; I could not confirm a machine-readable form. Does not cover pre-1937 orders or 2017 onward, which is the exact gap this project fills. These are the only systematic "status" source and are known to be unofficial.
- Verdict: ADOPT NOW (already presumably used; treat as hypothesis, not truth).

**NARA EO CSV dataset** ([opened](https://www.archives.gov/open/dataset-executiveorders.html)): CSVs for Clinton, Bush, Obama only; no field list or status info stated. Low value. SKIP.

**CRS, Executive Orders: Issuance, Modification, and Revocation (RS20846)** ([list of versions via everycrsreport](https://www.everycrsreport.com/reports/RS20846.html), snippet only): authoritative explanation of why no formal revocation is required for an order to lapse. Cite; not a tool.

**UK legislation.gov.uk effects data** ([changes page, opened](https://www.legislation.gov.uk/changes); [effects data model, opened](https://legislation.github.io/data-documentation/model/effects.html); [API docs, opened](https://legislation.github.io/data-documentation/api/overview.html))
- What it is: an editorial team records each "effect" (a provision of one law that inserts, repeals, substitutes, modifies or applies another), usually within two weeks of publication. Each effect has: type, affecting provisions, affected provisions, savings, in-force dates, commencement authority, extent, and "applied / requires-applied" status flags. XML (CLML) plus Atom feeds, SPARQL endpoint, 3,000 requests per 5 minutes per IP, user agent required, free crawling encouraged. Coverage: primary legislation from 2002 onward is in the lists; earlier changes are baked into the text.
- Lessons for this project: (1) separate "the effect exists" from "the effect has been applied/accounted for" as explicit flags; (2) record commencement authority and in-force date separately from the amending text; (3) record savings clauses; (4) note that effects carry no machine-readable amending instructions, i.e. the UK also relies on editors reading text; (5) pre-2002 effects are not tabulated, which shows even the leading system gave up on full history. The Law Commission's "spent or obsolete" categories ([opened](https://cdn.websitebuilder.service.justice.gov.uk/uploads/sites/54/2024/11/statue_law_repeals_background_notes.pdf)) are a ready-made taxonomy for why an order died without formal revocation: body dissolved, one-off obligation fulfilled, commencement/transitional provision spent, superseded by later law, power unused. The note says obsolescence is usually gradual, not a single moment, which matters for the "when did it cease" field.
- Reusable code: none for the US. Only the documentation repo is open; no client library is named. Verdict: ADOPT NOW as a schema model (an afternoon of design); SKIP as software.

**EUR-Lex consolidation** ([methodology PDF, opened](https://eur-lex.europa.eu/content/intro/collection/Methodology-on-Consolidation.pdf))
- Defines the start-date rule for each consolidated version (application date if the amending act sets one, otherwise entry into force; special rules per act type; second-level corrections take the date of the corrected act). The page says nothing about automation. Useful as a precedent for a documented "effective date of the effect" rule when the order text is silent. Verdict: WATCH (read once for the date-rule model).

**Open Laws Foundation** ([announcement, opened](https://www.bespacific.com/?p=125674))
- Young open-source project proposing stable identifiers, temporal validity, Akoma Ntoso output and a "semantic diff" classifying kinds of amendment, with per-jurisdiction adapters and a conformance suite. Unincorporated, no version, adoption unknown. Verdict: WATCH. Akoma Ntoso is overkill for orders.

**Temporal-aware legal RAG (NeurIPS 2026 workshop poster)** ([opened](https://neurips.cc/virtual/2026/173733))
- Brazilian regulator resolutions (693 docs, 162 questions): an LLM extracts validity-changing events, a deterministic admission gate filters them, events are applied to a versioned repository and an "active view" is built. Answer correctness 79.0% vs 70.4%. No code stated, tiny own evaluation set. Verdict: WATCH. The pattern (LLM proposes event, deterministic gate admits) is what the claim kit already does.

**Double Triangle Annotation** ([arXiv 2605.25781, opened](https://arxiv.org/pdf/2605.25781))
- Two independent multimodal LLMs annotate historical directories; agreement auto-accepts; disagreement goes to a human jury; two such systems then compare with a domain expert resolving the remainder. On 13,595 fields over 85% auto-accepted, humans touched ~12-14% in layer 1; residual errors were visually ambiguous text where all readers failed alike. Single page controlled test only; reviewer overlap noted; no source code released, benchmark released.
- Fit: The nearest published design to this project's two-blind-reviewer plus human certification. Key transferable points: show the human the two conflicting outputs rather than one suggestion (reduces anchoring); error independence between models is the assumption that breaks on degraded scans, which is exactly the 1930s-1990s OCR problem.
- Verdict: TRY the human-jury step design for the certification stage; WATCH the paper.

**LLM annotation of case law vs humans** ([Schepers et al., summary opened](https://www.rug.nl/library/open-access/blog/open-access-publication-in-the-spotlight-the-price-of-automated-case-law-annotation-comparing-th?lang=en)): GPT-4o reached human-level on basic annotation, weak recall on citation extraction, outputs varied across repeated prompts. The blog gives no numbers; the paper (AI and Law 2025) does. Relevant caution: citation and cross-reference extraction is where models are weakest, and that is the core of "which later instrument ended this order". Verdict: evidence for treating the "finding the ending instrument" step as the high-risk step.

**Prior art on tracking current EOs (low value)**: law-firm trackers (Gibson Dunn, Akin, Husch, Foley Hoag, BillTrack50) and Apify scrapers of White House pages ([example](https://apify.com/v0iddo/us-executive-orders-tracker)) cover 2025 onward as news, not status. `executiveordermonitor` on PyPI and `andharris/eo` on GitHub are small API wrappers (snippet only). Nothing found that determines status for historical orders. I found no "dead letter" or obsolete-law empirical study for US executive orders besides Thrower and Lowande/Poznansky. State code clean-up work (for example Hawaii legislative committee reports in my search) is legislative housekeeping, not datasets.

## Part 3. Systematic-review and source-tracking tools

- **ASReview LAB** ([UU page, opened](https://www.uu.nl/en/research/ai-labs/disc-ai-lab/projects/software-tools-and-infrastructure/asreview-lab)): open-source active-learning screener, v2.0 released May 2025 per the page, multi-reviewer, optional heavier models via the Dory extension. Free. Fit: it ranks documents for human screening so the human sees likely-relevant ones first. This project's problem is not screening a corpus for relevance; it is deciding status per known order. A narrow use: prioritizing which of the ~15,000 orders to send for human certification first, or finding candidate "ending instruments" among Federal Register documents. Hours to pilot, low payoff. Verdict: WATCH.
- **Zotero with API/MCP** (snippets only: [zotero-api-mcp](https://pypi.org/project/zotero-api-mcp/), [MCP guide](https://mcp.directory/blog/zotero-mcp-complete-guide-2026)): tracks bibliographic items and attachments, has a local API. Does not hash-verify bytes or store byte spans, which the project's standard requires, and the repo already holds hashed source texts. A forum thread reports a Zotero 8 local-API issue. Verdict: SKIP.
- **Covidence, Rayyan**: commercial screening/extraction tools for medical systematic reviews (PRISMA workflows); none fits byte-span evidence. SKIP.
- **UK AISI Inspect** ([snippets only](https://pypi.org/project/inspect-ai/)): open-source evaluation framework (many 0.3.x releases) for running LLM and agent evals with scorers. Fit: a harness for the planted-false-control tests, to run reviewers against known-wrong claims and report catch rates per model. The repo already has this logic in Python; adopting Inspect would add logging and model-grading plumbing but also a dependency and learning time. Not verified here beyond package listings. Verdict: WATCH.

## Part 4. Things one person plus agents could use that others may miss

1. **Use Thrower and Lowande/Poznansky's known corrections as free planted controls** (20 missed revocations, 65 misattributed revokers, 1 false revocation). They are published, independent of this project's pipeline, and test exactly the "cleanup versus real status" question. Cost: a few hours to extract and match order numbers.
2. **Adopt the UK effect schema fields** (applied/requires-applied, commencement authority, savings, in-force date, extent) as a checklist for the claim CSV. The UK distinguishes "this effect exists" from "this effect has been applied to the text"; the project's "formal revocation of an already-dead order" is the same concept.
3. **Use the Law Commission's "spent or obsolete" categories** as the controlled vocabulary for the "why ended" field.
4. **Oracle sampling.** The compiler post's key move was an independent oracle so agents could work on disjoint pieces. For orders, the disposition tables (1937-2017) are an imperfect oracle: batch disagreements between claim-kit results and the tables first, since those are where either the tables or the pipeline is wrong, and where human review pays most.
5. **Gate by commitment point, not by volume.** ArcticSwarm and Anthropic both show review pays off at commitment boundaries. A cheap deterministic pre-filter (exact-span and hash checks) before the Opus reviewers avoids paying 10-25 USD per batch to review claims that fail mechanical checks. This is already partly in place; confirm it runs before, not after, the reviewers.
6. **Reviewer family diversity.** The correlated-search result says same-family replicas share errors. Using a GPT-family reviewer for one of the two blind reviews is the best-supported change, though the evidence is on search tasks, not legal review.

## Considered and rejected
- Gas Town (chaotic, no measured results, cost estimates unreliable).
- Zotero, Covidence, Rayyan (do not match byte-span evidence or the non-medical problem).
- Law-firm EO trackers and Apify scrapers (current-news only, no historical status).
- Open Laws Foundation / Akoma Ntoso (early-stage, heavy for this data).
- NARA EO CSV (3 presidents, no status field documented).
- Epoch/METR MirrorCode (budget calibration only).

## Ranked top 5 for this scope
1. **Lowande and Poznansky / Thrower datasets**: prior art, baseline, and free independent controls. Get the replication files first.
2. **Cursor planner/worker/judge pattern plus Cognition's single-writer rule**: redesign coordination so workers own disjoint outputs and one planner assigns work, reducing merge freezes and duplicated work.
3. **Anthropic multi-agent research post**: delegation-brief template, effort-scaling rules, and the 15x token figure for budgeting.
4. **legislation.gov.uk effects model plus Law Commission obsolescence categories**: schema and vocabulary for status and reason fields.
5. **Double Triangle Annotation design**: show humans the two conflicting reviewer outputs at certification; note its independence assumption fails on degraded scans.

## Open items for the main session
- Federal Register API field list (`executive_order_notes` etc.) could not be verified from here (proxy 403 on direct curl; the docs page returned no schema). Check from a GitHub Actions job.
- Replication archive location for Lowande/Poznansky was not visible in the part of the article I could read.
- I did not find Reddit or Lobsters threads with usable content; coverage of forum experience is mostly HN (one mirrored thread), blogs and vendor posts. Weight the "anecdote" labels accordingly.
