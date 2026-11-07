# 06 - Cost, two-reviewer blind review, evaluation, human certification, legal formalisms, provenance

Research date: 2026-11-06. Prices come from vendor pages opened today unless marked otherwise. Items marked (unverified) came from search snippets, secondary blogs, or my own memory and were not confirmed on a primary page.

## 0. Bottom line

1. The cheapest large lever is the Anthropic Message Batches API at 50% off, which stacks with prompt caching. Applied to a 15 USD claim-kit batch it saves about 7.50 USD. It requires moving the producer and reviewers from agentic `claude -p` sessions to single-shot API calls with the sealed packet inlined.
2. Replacing one Opus reviewer with a different-family model (GPT-6.1-sol, Gemini 3.1 Pro) saves a further 3-5 USD per batch and also improves independence. It needs a planted-control measurement before it is trusted.
3. A Max subscription does not reduce the cost of headless work. Since 2026-06-15, `claude -p`, the Agent SDK and Claude Code GitHub Actions draw from a separate monthly credit billed at API list prices (reported by secondary sources; confirm in the help center). Use `ANTHROPIC_API_KEY` for containers.
4. Human certification will cost more than all the AI review combined. The AI savings are worth taking, but the plan for human coders is the real budget item.
5. The stated per-batch token counts do not reproduce 15 USD at today's Opus 5.5 and Sonnet 5.5 list prices (section 2). Measure the real split with `total_cost_usd` from `claude -p --output-format json` before choosing levers.

## 1. Current prices and limits

### Anthropic (platform.claude.com/docs/en/about-claude/pricing, opened 2026-11-06)

| Model | Input | Output | Cache write 5m | Cache write 1h | Cache read | Batch in / out |
|---|---|---|---|---|---|---|
| Opus 5.5 | 4 | 20 | 5 | 8 | 0.20 | 2 / 10 |
| Sonnet 5.5 | 2 | 10 | 2.50 | 4 | 0.10 | 1 / 5 |
| Haiku 5.5 (prompt <=100K) | 0.10 | 0.50 | 0.125 | 0.20 | 0.01 | 0.05 / 0.25 |
| Opus 5, 4.8-4.5 | 5 | 25 | 6.25 | 10 | 0.50 | 2.50 / 12.50 |
| Opus 4.1, 4 | 15 | 75 | 18.75 | 30 | 1.50 | - |

USD per million tokens. The page lists Opus 5.5 cache read at 0.20, which is 0.05x of input, not the 0.1x multiplier shown in the caching guide; the pricing table is the one to trust for 5.5 models. Fast mode is not available in batches. The `inference_geo: "us"` option adds 1.1x to every token category.

Batch limits (docs/en/build-with-claude/batch-processing): 100,000 requests or 256 MB per batch; most batches finish within 1 hour, all expire at 24 hours; results kept 29 days; `max_tokens: 0` pre-warming, streaming and Fast mode are unsupported. Batch and caching discounts stack, but hits are best-effort. Anthropic reports typical hit rates of 30% to 98%, and recommends the 1-hour cache TTL (write costs 2x input) and identical `cache_control` blocks in every request.

Caching details (docs/en/build-with-claude/prompt-caching): a cache entry exists only after the first response begins, so send one request first, then the rest. The cache prefix order is tools, system, messages. Minimum cacheable length is 4,096 tokens for Opus 4.5-4.7 and 1,024 for Sonnet 4.x; the page does not list Opus 5.5 or Sonnet 5.5 minimums, so check `cache_creation_input_tokens` in `usage`.

### OpenAI (developers.openai.com/api/docs/pricing, opened 2026-11-06; tier labels inferred by the fetcher)

| Model | Standard in/out/cached | Batch or Flex | Fast |
|---|---|---|---|
| gpt-6-astra | 10 / 50 / 1.00 | 5 / 25 / 0.50 | 20 / 100 |
| gpt-6.1-sol | 2 / 10 / 0.10 | 1 / 5 / 0.05 | 4 / 20 |
| gpt-6.1-terra | 1 / 5 / 0.05 | 0.50 / 2.50 / 0.025 | 2 / 10 |
| gpt-6-luna | 0.10 / 0.50 / 0.01 | 0.05 / 0.25 / 0.005 | 0.20 / 1.00 |

Batch API (guide opened): 50% off, 24-hour window, up to 50,000 requests and 200 MB per file, separate rate-limit pool, outputs kept 30 days. Flex (guide opened): synchronous calls at Batch rates via `service_tier: "flex"`, beta, with 429 "Resource Unavailable" when capacity is short (not charged) and a 10-minute default SDK timeout. Flex suits a reviewer that must return in minutes without a batch file round trip.

### Google Gemini (ai.google.dev/gemini-api/docs/pricing, opened 2026-11-06)

| Model | Standard in/out | Batch and Flex in/out | Cached input |
|---|---|---|---|
| Gemini 3.1 Pro Preview (<=200k) | 2.00 / 12.00 | 1.00 / 6.00 | 0.20 (+4.50 per M tokens per hour storage) |
| Gemini 3.5 Flash | 1.50 / 9.00 | 0.75 / 4.50 | 0.15 |
| Gemini 3 Flash Preview | 0.50 / 3.00 | 0.25 / 1.50 | 0.05 |

Batch (docs opened): 50% off, 24-hour target, jobs expire at 48 hours, input files to 2 GB, structured output and `cached_content` supported, results kept 6 weeks, job creation is not idempotent. Google batch mode does not support thinking or web search (per Inspect's batch page). Implicit caching is automatic on 2.5 and newer models; minimum 4,096 tokens on 3.1 Pro.

### OpenRouter (openrouter.ai/docs/faq, opened)

No markup on inference pricing; a platform fee applies to credit purchases (the rate did not render, so unknown to me); free models limited to 50 requests per day. The page describes no batch discount. It buys routing and one API key, not savings. Skip as a cost lever.

## 2. What each lever saves on one 8-claim batch (baseline 15 USD)

Assumptions, because the brief does not give the split. (a) Producer is 10% of cost (1.50 USD) and each Opus reviewer is 45% (6.75 USD). (b) Reviewer input is mostly the sealed packet, which is identical for both reviewers and for all 8 claims in a batch. (c) Percent discounts apply multiplicatively whatever the input/output mix; only caching depends on the mix, so it carries a range.

Reconciliation problem: 0.2M Sonnet tokens plus 0.35M tokens per Opus reviewer (0.7M total) at an 85/15 input/output mix costs about 5 USD at Opus 5.5 and Sonnet 5.5 list prices. To reach 15 USD, either the token counts omit cache writes and reads that Claude Code bills, the reviewers run on a more expensive model (Opus 4.1 at 15/75 gives about 17 USD for the same tokens), or the output share is much higher. The percentages below hold in every case, but the dollar values scale with the true baseline.

| Lever | New cost | Saving | Notes |
|---|---|---|---|
| Batch API for producer and both reviewers (Anthropic) | 7.50 | 7.50 (50%) | Needs API calls with packet inlined; two sequential rounds (producer, then reviewers), typically 1 hour each, up to 24 hours. |
| Batch for reviewers only | 8.25 | 6.75 (45%) | Producer stays interactive; keeps most of the saving because reviewers dominate. |
| Prompt caching only, shared packet prefix | 11-13.5 | 1.5-4 (10-25%) | Estimate. First call writes at 1.25x (2x for 1 hour); the other 15 reviewer calls read at 0.05-0.1x. Claude Code already caches within a session, so the extra gain is cross-session and cross-reviewer sharing only. |
| Batch + caching, all Anthropic | 5.6-6.8 | 8.2-9.4 (55-62%) | Hit rate is best-effort (30-98% per Anthropic); use 1-hour TTL and send one warm-up request first. |
| Reviewer B swapped to gpt-6.1-sol, standard | 11.6 | 3.4 | Half the Opus 5.5 price. Different family. |
| Reviewer B on gpt-6.1-sol Batch or Flex | 9.9 | 5.1 | 75% below Opus 5.5 standard. |
| Reviewer B on Gemini 3.1 Pro, standard / batch | 12.0 / 10.1 | 3.0 / 4.9 | Output cheaper than sol only in batch. |
| Reviewer B on gpt-6.1-terra batch | 9.1 | 5.9 | 87.5% below Opus 5.5; quality unknown, pilot first. |
| Reviewer B on gpt-6-astra standard | 24+ | negative | 2.5x Opus 5.5 price. Do not use. |
| Combined: producer batch, reviewer A Opus batch+cache, reviewer B sol batch | about 4.5-5.8 | about 9-10 (62-70%) | Best plausible plan with two families. |
| Max 5x or Max 20x subscription | 15 | 0 | Credit of 100 or 200 USD per month at API list prices covers roughly 7 or 13 batches; no discount rate. |
| OpenRouter | 15 | 0 | No markup but no batch discount. |
| Cheap screen before Opus (Haiku 5.5 at 0.10/0.50, or deterministic checks) | varies | unmeasured | Dropping claims that fail hash or span checks before any Opus call is free; a Haiku screen cannot replace blind review. Measure the rejection rate first. |

## 3. Subscription versus API, and headless authentication

- **Subscription changes (secondary sources, 2026).** The Decoder and a dev.to analysis report that from 2026-06-15, programmatic use (Agent SDK, `claude -p`, Claude Code GitHub Actions, third-party Agent SDK apps) moves off subscription rate limits onto a monthly credit billed at full API rates: Pro 20, Max 5x 100, Max 20x 200 USD; the credit expires monthly; after it runs out, extra usage is billed at API list price and is off by default. Interactive Claude Code, chat and Cowork stay on subscription limits. Sources: https://the-decoder.com/claude-subscriptions-get-separate-budgets-for-programmatic-use-billed-at-full-api-prices/ and https://dev.to/vainamoinen/what-anthropics-200-agent-sdk-credit-means-if-you-run-claude-p-in-production-ce2. The dev.to piece says the help-center articles leave hooks, subagents, scheduled agents and remote agents unclear. The pricing page (claude.com/pricing, opened) lists "$100/month in API credits" for Max 5x and 200 for the top tier, which agrees. Confirm in the Anthropic help center before relying on it.
- **Implication.** Interactive sessions where Danny or a coordinator agent types prompts remain a flat-rate resource. Containerized headless review is metered at API prices either way, so the API's Batch and caching discounts are strictly better for the claim kit.
- **Authentication in containers (code.claude.com/docs/en/authentication, opened).** Precedence: cloud-provider variables, then `ANTHROPIC_AUTH_TOKEN`, then `ANTHROPIC_API_KEY` (always used in `-p` mode when present), then `apiKeyHelper`, then `CLAUDE_CODE_OAUTH_TOKEN`, then stored `/login` credentials. `claude setup-token` prints a one-year OAuth token tied to a Pro, Max, Team or Enterprise plan; it can make model requests only and is not read in `--bare` mode. `--bare -p` is the recommended scripted mode, ignores OAuth and keychain entirely, and needs `ANTHROPIC_API_KEY` or an `apiKeyHelper`. `--output-format json` returns `total_cost_usd` (a client-side estimate) and `--json-schema` returns validated `structured_output`. `--max-budget-usd` caps a run.
- **Known failures.** anthropics/claude-code-action issue 1281 (opened) reports `CLAUDE_CODE_OAUTH_TOKEN` from `setup-token` failing on Max accounts, including a case that began 2026-08-17 with the token regenerated three times; affected users moved to `ANTHROPIC_API_KEY`. No maintainer response is shown. Two further issue pages (anthropics policy question 27125, 401 bug 65320) were blocked by robots.txt, so I did not read them.
- **Recommendation for the "cannot authenticate `claude -p` in some containers" pain point.** Put an API key in a GitHub Actions secret, run `claude --bare -p ... --output-format json --json-schema ... --max-budget-usd N`, and log `total_cost_usd` per call. The setup-token route works for some users but has live bug reports and is not available with `--bare`.

## 4. Different-family review

- Same-family bias evidence is mixed. Measured: a model recognizes its own output (GPT-4 73.5%, Panickssery et al. 2024, arXiv:2404.13076) and self-preference correlates with recognition. Wataoka et al. (arXiv:2410.21819) found no significant self-preference for most of eight models, attributing the effect to familiarity. Chen et al. (arXiv:2504.03846) found on verifiable tasks that a judge's accuracy tracks its own task accuracy (r 0.71-0.90) and that Qwen2.5-72B preferred its own wrong MATH500 answer 86% of the time. I read these through agentpatterns.ai (https://agentpatterns.ai/verification/judge-self-preference-detection/), not the papers.
- Against assuming an ensemble helps: Kohli 2026 (arXiv:2605.29800, via the same page) found nine judges from seven families gave about 2.18 independent votes, and the best single judge matched or beat the panel in every condition. A blog (tianpan.co, 2026-06-03) argues that all-same-family ensembles agree because they share priors; its numbers are hypothetical or uncited, so treat it as opinion.
- Fit for this project. The two Opus reviewers are the same family as the Sonnet producer, so their errors can correlate with the producer's. A reviewer from a different family is a cheap test of that. The planted false controls already in the pipeline are the right instrument: measure each reviewer's miss rate on planted controls, then compare the Opus pair against Opus plus GPT-6.1-sol or Gemini 3.1 Pro. Because a claim files only if both reviewers uphold its exact hash, a weaker second reviewer lowers recall of valid claims but cannot by itself file a false one unless the first reviewer also misses it. A different-family second reviewer is therefore also a safety gain when its misses are uncorrelated with Opus's.
- Verdict: TRY (small pilot) - replace reviewer B with GPT-6.1-sol on Flex or Batch for 3 batches (24 claims plus planted controls) and compare control-catch rates and agreement with Opus. OpenAI's GPT-6 "Astra" is already used by Codex sessions in this project, so this also addresses the Claude/GPT coordination gap.

## 5. Evaluation frameworks for planted controls

- **Inspect AI** (https://inspect.aisi.org.uk/; https://github.com/UKGovernmentBEIS/inspect_ai) - open-source evaluation framework from the UK AI Security Institute and Meridian Labs; built-in providers for Anthropic, OpenAI, Google and others; model-graded and custom scorers; log viewer; built-in batch mode (`--batch`) for OpenAI, Anthropic, Google, xAI and Together, billed at about 50% (https://inspect.aisi.org.uk/models-batch.html).
  - Cost: free, MIT license. Maturity: 3.1k stars, 8,099 commits, 329 open issues (GitHub page, opened). The fetched page showed no release dates.
  - Evidence: no independent user reports gathered; the maintainers are a government institute, which lowers abandonment risk.
  - Fit: a reviewer is a scored sample; a planted control has a known target, so catch rate and false-uphold rate fall out of a custom scorer. Batch mode gives the 50% discount for free on single-turn evals. Caveat from the docs: multi-turn agentic samples are slow in batch mode. Adoption: about one day to wrap the existing reviewer prompt and the controls file.
  - Verdict: TRY (small pilot). It is the best fit for measuring both reviewers and comparing families.
- **promptfoo** (https://github.com/promptfoo/promptfoo) - YAML-driven prompt and model evaluation with assertions and red teaming. MIT, 26.5k stars. OpenAI announced its acquisition on 2026-03-09 (Bloomberg, SiliconANGLE and others in search results); the repo says it remains open source and MIT licensed. Fit: workable for assertions, but a vendor-owned tool is a mild conflict for a project that insists on different-family review. Verdict: WATCH.
- **Braintrust** (pricing page opened) - hosted evals. Starter 0 USD with 14-day retention, Pro 249 USD per month with 30 days. Retention that short conflicts with a permanent evidence trail. Verdict: SKIP.
- **LangSmith** (pricing page opened) - Developer free with 5k traces per month and 14-day base retention; Plus 39 USD per seat. Same retention problem; the stack is LangChain-centric. Verdict: SKIP.
- **OpenAI Evals** (https://github.com/openai/evals) - 19.6k stars; README now points to the OpenAI Dashboard evals product. Locks you to one vendor. Verdict: SKIP.

## 6. Human annotation and certification

Facts from pages opened:

- **Label Studio** (https://github.com/HumanSignal/label-studio) - 28.6k stars, Apache-2.0. The Community Edition has no annotator-agreement metrics, no reviewer assignment, no task overlap and no consensus matrices; reviewer assignment and task overlap arrive in Starter Cloud, and full agreement and consensus only in Enterprise (docs.humansignal.com/guide/label_studio_compare). Enterprise pricing is not published. Verdict: TRY only as a single-annotator review UI; compute agreement with your own script. Do not pay for Enterprise for a count of 0 certified.
- **Argilla** (https://github.com/argilla-io/argilla) - 5.2k stars, Apache-2.0. The README says the original authors "have moved on," no new features are planned and only fixes continue. Verdict: SKIP.
- **Prodigy** (https://prodigy.ai/buy) - 390 USD one-time personal license, 490 USD per seat in packs of 5 (the page is unclear on per-seat versus per-pack), 12 months of upgrades, self-hosted, scriptable. The page does not describe multi-annotator or review features beyond a conflict-resolution interface. Verdict: WATCH; fine for one annotator, unverified for a certification workflow.
- **Doccano** (https://github.com/doccano/doccano) - 10.8k stars, MIT; text classification and sequence labeling only. It lacks a built-in agreement metric and its release recency was not visible. Verdict: SKIP.
- **Hypothesis** (https://web.hypothes.is/) - browser annotation of web pages and online PDFs with a public API and a Python wrapper (PyPI). The page does not confirm exact text-quote anchoring. It would annotate the public rendering, not the hashed byte spans of the held source, and OCR text layers on scans will not match. Verdict: SKIP for certification; possibly useful for public comment later.
- **Recommended certification tool.** The project already has a public HTML card per order. Add a certifier page or CSV per claim showing the quoted byte span from the hash-verified file, the checker results and the two reviewer verdicts, then collect an independent human decision (uphold, reject, unclear) into a CSV. Compute Krippendorff's alpha and Cohen's kappa in about 30 lines of Python. Cost: a day of work. Verdict: ADOPT NOW in preference to buying a platform.

Recruiting and paying coders:

- **Prolific** (https://www.prolific.com/pricing, opened): platform fee usually 42.8% for corporate and 33.3% for academic or nonprofit accounts; minimum 8 USD per hour, recommended 12 USD per hour, higher for specialized work. Pay-as-you-go includes "AI Taskers and Domain Experts"; the page does not name law as a filter. Prolific itself advertises "Specialised Participant - Lawyers" jobs for AI training (search results; (unverified) for how a researcher accesses that pool). At 12 USD per hour plus fee, about 16-17 USD per hour. That pay is low for work that needs reading Federal Register scans and statutes; legal-trained coders will cost more.
- **CloudResearch Connect** (opened): the page gives no fee, pay minimum or occupation targeting. Contact sales. Skip unless Prolific fails.
- **Upwork**: a listing titled "Legal Data Annotator - Law Students and Paralegals Welcome" exists but the page would not load, and no rate was retrieved. Rates for paralegals appear in search results only. (unverified)
- **Law-school research assistants**: search found only unrelated postings (Oxford empirical legal studies RA, Berkeley, Wisconsin student hiring forms). I did not find a documented standard rate for coding work. NYU Law student RA pay and work-study eligibility should be asked of the school directly. Assumption for budgeting: 25-40 USD per hour and 10-20 minutes per claim, which gives 35-110 USD to certify one 8-claim batch, two to seven times the AI cost. (my estimate, not sourced)
- **Reliability practice.** Report Krippendorff's alpha (handles more than two coders, missing data and nominal labels) alongside raw agreement, with 0.80 conventionally read as reliable and 0.667 as the floor for tentative conclusions (Krippendorff; from memory, unverified here). Two coders on a sample of at least 10-20% of items, with disagreements adjudicated by a third, is the usual design; the certification step here should use the same structure, with the two AI reviewers entered as additional coders so human-versus-AI agreement is reported.
- **Lawma** (https://arxiv.org/abs/2407.16615, ICLR 2025): on 260 legal annotation tasks, commercial models were non-trivial but variable, and small fine-tuned open models beat them with a few hundred to a thousand labeled examples. Relevance: certified human labels are also the training or calibration set that could later replace Opus review with a cheap fine-tuned model. Verdict: WATCH as a future lever; it needs several hundred certified claims first.

## 7. Formal and Lean-like legal reasoning tools

None of these fit the project's task. Deciding whether an executive order still has effect is a document-finding and interpretation problem (which later statute, order or proclamation ended it, and why), not the execution of a rule set against facts. The Lean-like standard is already implemented as hash-verified span citations and automated checkers.

- **Catala** (https://github.com/CatalaLang/catala) - Inria research DSL for turning legislative text into executable code; 2.4k stars, Apache-2.0; the README calls the compiler unstable; used for French tax and benefit computation. Verdict: SKIP; it computes legal outcomes from facts, which is not this question.
- **Blawx** - a rules-as-code tool by Jason Morris (code at StandardLaw/blawx on GitHub per search results). The blawx.com domain redirected to an unrelated commercial site (thetreemassage.com), which I did not follow; treat the domain as lapsed. Verdict: SKIP.
- **L4** (https://github.com/smucclaw/dsl) - Singapore Management University legal DSL; 82 stars; the README says it is "primarily intended for core devs." Verdict: SKIP.
- **LegalRuleML and Akoma Ntoso** - OASIS XML standards (Akoma Ntoso 1.0 approved 2018). Akoma Ntoso is rare in US law (vaquill.ai guide). Verdict: SKIP.
- **USLM** (https://github.com/usgpo/uslm) - GPO's US Legislative Markup, schema 2.1.0 on the main branch. The Office of the Law Revision Counsel publishes the US Code as USLM XML, with release points; govinfo lists USLM for public laws and Statutes at Large only from the 108th Congress (2003) on (vaquill.ai guide; secondary, unverified against govinfo). Its dated-version addressing (`@2013-05-02`) could help the "current status sources" gap by diffing US Code release points to see when a section was repealed or omitted. It does not cover 1789-1993 orders. Verdict: WATCH; consider it only for the current-US-Code status lookups, which belong to another scope.

## 8. Provenance standards

- **W3C PROV** (https://www.w3.org/TR/prov-overview/) - the data model (PROV-DM), ontology (PROV-O) and notation (PROV-N) are W3C Recommendations dating from 2013; the Working Group considers its work complete. The model already maps cleanly: a claim is an Entity, produced by an Activity (producer run, reviewer run) using Agents (model, human) and derived from the source-text Entities identified by hash. Cost: free. Adoption effort: a few hours to emit a PROV-JSON-style record per claim next to the existing claim CSV. Verdict: TRY, as an export format only, after the CSV schema is stable.
- **RO-Crate** (https://www.researchobject.org/ro-crate/) - JSON-LD packaging of data plus metadata with schema.org terms; used by WorkflowHub, Nextflow provenance plugins and others. The page did not show the spec version or hash support. Fit: packaging the final dataset (data files, codebook, checker code, run logs) for a Zenodo or Dataverse deposit alongside the law-review article. Verdict: TRY at publication time.
- **Nanopublications** (https://nanopub.net/) - each claim becomes a signed RDF unit with assertion, provenance and publication-info graphs, a trusty URI that includes a content hash, and replacement or retraction as new versions; libraries exist for Java, Python, JavaScript and Rust. This resembles the project's hash-checked claims, but requires RDF modeling and key management for small payoff. Verdict: WATCH.
- **C2PA** (https://c2pa.org/) - Content Credentials for media such as images; the page does not claim text, JSON or dataset support. Verdict: SKIP.

## Considered and rejected

OpenRouter (no discount), Braintrust, LangSmith, OpenAI Evals, Argilla, Doccano, Hypothesis for certification, CloudResearch (no public terms), Catala, Blawx, L4, LegalRuleML, Akoma Ntoso, C2PA, GPT-6 Astra as a reviewer (2.5x Opus price).

## Ranked top 5 for this scope

1. **Anthropic Message Batches API plus 1-hour prompt caching for reviewer calls (ADOPT NOW).** Saves 55-62% on the Anthropic portion; stacks; all stated limits fit an 8-claim batch. Cost: rewrite review calls as single-shot API calls with the packet inlined and `--json-schema` style output; send one warm-up request before the rest.
2. **API key authentication with `claude --bare -p ... --output-format json --max-budget-usd` (ADOPT NOW).** Fixes the container login problem, avoids the setup-token bugs, and logs real cost per call.
3. **Different-family second reviewer (GPT-6.1-sol on Flex or Batch, or Gemini 3.1 Pro on Batch), measured with Inspect AI against planted controls (TRY).** Saves 3-5 USD per batch and tests reviewer independence with the instrument the project already has.
4. **Own certification page plus a Krippendorff's alpha script, with the AI reviewers entered as coders (ADOPT NOW).** Defers any platform purchase; Label Studio Community lacks agreement and review features.
5. **PROV export now, RO-Crate at publication (TRY).** Both are free and map onto the existing hash-and-span evidence model.
