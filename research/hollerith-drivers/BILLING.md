# Billing facts for scripted Claude Code (Hollerith, Part A)

Read on 2026-11-06 by the Hollerith stream (worktree `enc-drivers`). Every fact below was taken from an Anthropic page opened
in this session, not from memory and not from a secondary report. The `code.claude.com` and `platform.claude.com` pages came
back as their own markdown. The two `support.claude.com` articles came back through the fetch tool's summarizer, so their
wording is the tool's rendering of the page; the facts match across both articles and the search snippets, but no sentence
here is a verified verbatim quotation (the quoted phrases are as returned by that tool).

## The answer

**Logged in with a Max or Ultra subscription, `claude -p` and the Agent SDK draw on the subscription's usage limits. They are
not billed as metered API usage, and there is no separate programmatic credit that replaces the limits.** The secondary
reports that programmatic use moved to a separate monthly credit at API rates on 15 June 2026 are **refuted as stated**: the
official help article says that change was paused on 15 June 2026.

Anthropic did add something on 7 October 2026, and the secondary reports probably conflate it with the paused change: Max
($100/month) and Ultra ($200/month) plans include monthly **API credits** that are spent only when `claude -p` or the Agent SDK
is run with an **API key from a linked Console organization**. They are not extra capacity for a subscription login.

How sure: high (about 90 percent) for the headline, because two official support articles agree and the Claude Code
authentication and GitHub Actions pages say the same thing independently. The residual doubt is (a) the summarizer step on the
support pages, and (b) "paused" is a status that Anthropic can change again; re-read the article before the first paid or
subscription run.

## Facts, with sources

### F1. Subscription login: scripted use draws on subscription limits

- Source: https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan (read 2026-11-06)
- Update 15 June 2026: "the previously announced changes to Claude Agent SDK usage were paused. For now, Claude Agent SDK,
  `claude -p`, and third-party app usage still draw from subscription limits."
- Update 7 October 2026: Max, Ultra and Team plans now include monthly API credits; for plan sign-in, "Nothing changes for your plan."
  Agent SDK and `claude -p` still draw from subscription limits when signed in with the plan.
- The page shows "Updated over a week ago" and no explicit date of its own; the dated entries are the two above.

### F2. The monthly API credits (7 October 2026): what they cover and do not

- Source: https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-ultra-and-team-plans (read 2026-11-06)
- Amounts: Max $100, Ultra $200 per month; Team $20 per Standard seat and $100 per Premium seat, pooled, capped at $500. Free, Pro
  and Enterprise are not eligible. Plan must be active seven days. No payment method needed on the Claude Platform.
- Claimed by the subscriber at Settings > Billing > "Link organization" (one Console organization per plan, one plan per
  organization, cannot be changed without support). Everyone with an API key in that organization shares the balance.
- Covers: Messages API and **Message Batches API**, Console Playground, Managed Agents, Claude Agent SDK, and `claude -p` when run
  yourself with an API key from the linked Console organization.
- Does **not** cover: interactive Claude Code, extra usage, and **runs started by the Claude Code GitHub Action** (they "count as Claude
  Code usage, even with `-p`"), IDE extension or desktop app runs.
- Unused credits expire at the end of each billing cycle, no rollover. They do not change the plan's usage limits. When they run out
  and the organization holds no purchased credits or auto-reload, API requests stop; "Usage is never charged to your Claude plan."
- Consequence for this campaign: the API credit (Ultra: $200/month) is a **separate pool from the campaign's 100 USD paid-API
  ceiling**, but only if the owner links a Console organization and creates a key. No API key exists yet, so none of it is available.

### F3. Plan limits are shared with chat and interactive use

- Source: https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan (read 2026-11-06)
- Claude on the web, desktop and mobile and Claude Code share one subscription and one set of usage limits. Pro and Max have a
  five-hour and a weekly limit; Ultra has a weekly limit (verified Ultra accounts no five-hour limit); Max and Ultra have a separate
  weekly limit for Fable.
- If `ANTHROPIC_API_KEY` is set, Claude Code uses it instead of the subscription and the usage is billed as API usage.
- The page says Claude Code may offer to continue with API credits at standard API rates when limits are hit, which can be
  declined, and that auto-reload in a Console account may add credits automatically. **Not confirmed:** what a headless `-p` run does
  at the limit. Treat "extra usage" and "auto-reload" as possible silent spend and turn them off before a subscription-authenticated run.
- The page says nothing about scripted, CI or automated use being restricted or permitted.

### F4. How `claude -p` authenticates without a browser

- Source: https://code.claude.com/docs/en/authentication (read 2026-11-06)
- Precedence (first present wins): cloud-provider variables; `ANTHROPIC_AUTH_TOKEN`; `ANTHROPIC_API_KEY` ("In non-interactive mode
  (`-p`), the key is always used when present"); `apiKeyHelper`; `CLAUDE_CODE_OAUTH_TOKEN`; Anthropic profile/federation; then
  subscription login. **An `ANTHROPIC_API_KEY` in the environment therefore silently switches a subscription user to metered billing.**
- `claude setup-token` opens the browser flow on a machine that has one and prints a **one-year** OAuth token; it is not saved. Set it as
  `CLAUDE_CODE_OAUTH_TOKEN` on the container. It "authenticates with your Claude subscription and requires a Pro, Max, Ultra, Team, or
  Enterprise plan"; it can only make model requests (no Remote Control, no claude.ai connectors).
- The token is tied to the subscription of the person who ran `setup-token` (GitHub Actions page: https://code.claude.com/docs/en/github-actions).
- Workload identity federation (GitHub OIDC to a Console service account) avoids a stored secret but is API-key billing, not subscription.
- Both `CLAUDE_CODE_OAUTH_TOKEN` and `ANTHROPIC_API_KEY` are named as supported repository secrets for the Claude Code GitHub Action.

### F5. What `--bare` does

- Source: https://code.claude.com/docs/en/headless (read 2026-11-06) and https://code.claude.com/docs/en/cli-reference
- `--bare` skips auto-discovery of hooks, skills, custom commands, subagents, plugins, MCP servers, auto memory and CLAUDE.md, so a
  scripted call behaves the same on every machine. Only Bash, file read and file edit tools remain; no system reminders, no background
  tasks. Context comes only from flags such as `--append-system-prompt`, `--settings`, `--mcp-config`.
- **Bare mode never reads OAuth credentials, the keychain, or `CLAUDE_CODE_OAUTH_TOKEN`.** It authenticates with `ANTHROPIC_API_KEY`
  or an `apiKeyHelper` (or Bedrock/Vertex/Foundry credentials). So `--bare` and a subscription token cannot be combined.
- Docs: `--bare` "is the recommended mode for scripted and SDK calls, and will become the default for `-p` in a future release."
  A run without `--bare` in a project folder also runs that project's hooks and MCP servers without a trust prompt, so an unattended
  non-bare run should use an empty working directory.

### F6. `--output-format json` and `total_cost_usd`

- Sources: https://code.claude.com/docs/en/headless and https://code.claude.com/docs/en/agent-sdk/cost-tracking (read 2026-11-06)
- The JSON result carries `result`, `session_id`, `usage` (input, output, cache_creation_input, cache_read_input tokens), `total_cost_usd`
  and a per-model breakdown (`modelUsage`). `--json-schema` adds a validated `structured_output` field; a run without valid structured
  output has no such field.
- `total_cost_usd` is a **client-side estimate** computed from a price table bundled in the client, "not authoritative billing data" and
  can differ from the bill. `usage` excludes subagents; `total_cost_usd` and `modelUsage` include them. On an error result `usage`
  may under-report; `total_cost_usd` is the figure to account from. Resumed sessions report the whole session's total.
- Under a subscription: https://code.claude.com/docs/en/costs says the session cost figure in `/usage` "isn't relevant for billing
  purposes" for Pro, Max and Ultra subscribers, whose usage is included in the plan. **Not confirmed on any page:** whether a
  subscription-authenticated `-p` run populates `total_cost_usd` at all. If it does, it is a list-price estimate of tokens, not a charge.
  The driver therefore records the field when present, logs the authentication basis beside it, and enforces its caps on the estimate
  (conservative) rather than treating a missing value as zero.
- `--max-budget-usd` stops a `-p` run once the client-side estimate reaches the amount (print mode only; spend can pass the cap).

### F7. Message Batches API: discount and limits

- Sources: https://platform.claude.com/docs/en/build-with-claude/batch-processing and https://platform.claude.com/docs/en/about-claude/pricing (read 2026-11-06)
- 50 percent of standard price on input and output tokens. A batch holds at most 100,000 requests or 256 MB. Most batches finish within an hour; a batch
  expires if not done in 24 hours; results are kept 29 days; no streaming. Prompt-caching discounts stack with the batch discount; the 1-hour cache
  duration is recommended for batches with shared context. Fast mode is not available in batches.
- Prices per million tokens (standard, then batch), as listed on the pricing page: Opus 5.5 input $4 / output $20 (batch $2 / $10);
  Sonnet 5.5 $2 / $10 (batch $1 / $5); Haiku 5.5 $0.10 / $0.50 for prompts up to 100,000 tokens (batch $0.05 / $0.25; $0.50 / $2.50 above that).
  Cache read on Opus 5.5 and Sonnet 5.5 is 0.05 times the input price; 5-minute cache write 1.25 times, 1-hour write 2 times.
- Rate limits for batches are separate and are in the rate-limits page (not read; see "Not confirmed").
- Batches need an API key (Messages API). Under F2 they are payable from the monthly API credits.

### F8. Can Claude Code or the Agent SDK use the Batches API?

- **No evidence that they can.** Nothing in the headless, CLI-reference, cost-tracking or pricing pages offers a batch mode for `claude -p` or the SDK.
  The pricing page states of Managed Agents that the Batch discount does not apply ("Sessions are stateful and interactive. There is no batch mode."),
  and Claude Code runs are stateful multi-turn agent loops of the same kind. A search of the official domains for a `claude -p` batch flag found none.
  Absence from these pages is not proof; the working assumption is: **a batch run means calling the Messages Batches API directly with an API key, one
  request per stage and no tool loop**, i.e. the model must be given everything in the prompt.

### F9. Installing Claude Code on GitHub's runner

- Source: https://code.claude.com/docs/en/setup (read 2026-11-06)
- Native installer on Linux: `curl -fsSL https://claude.ai/install.sh | bash` (also `| bash -s stable` or a pinned version such as `-s 2.1.89`). The npm package
  `@anthropic-ai/claude-code` installs the same native binary; the docs say it needs Node.js 22 or later (the installed binary does not itself invoke Node).
  A runner has `curl`; no sudo is needed for the native installer. Native installs auto-update; set `DISABLE_AUTOUPDATER=1` to hold a version.
- GitHub Action `anthropics/claude-code-action@v1` is the supported wrapper (`anthropic_api_key` or `claude_code_oauth_token` inputs); this campaign's driver
  calls the CLI directly so it can validate and cap, so the action is not needed.

## Not confirmed (say so plainly)

1. Whether `claude -p` under a subscription login returns a non-null `total_cost_usd` (F6). Run one measured call and look.
2. What a headless run does when the subscription limit is reached and "extra usage" or auto-reload is on (F3). Turn both off.
3. Whether Anthropic's Consumer Terms or Usage Policy restrict automated or high-volume use of a subscription token in CI. The Claude Code docs
   openly document `setup-token` for CI and a subscription-token GitHub Action, and the headless and support pages state no restriction, but I did not open
   the legal terms. The owner should read them before putting the Ultra token in a GitHub secret.
4. How much work an Ultra weekly limit buys in tokens, and whether campaign runs would compete with the owner's interactive sessions for it. Anthropic
   publishes no token figure on the pages read; only measurement answers it, and F3 says the pool is shared with chat and interactive Claude Code.
5. Whether the support-article status "paused" (15 June 2026) will change again.
6. The Batches rate-limit tiers (page not opened) and which model names an API key under the linked credit can use.
7. Whether the secondary sources' "$20 / $100 / $200 monthly credit" figures describe the paused June scheme or the 7 October API credits: the
   amounts for Max and Ultra match the 7 October API credits ($100 and $200); Pro $20 does not (Pro is not eligible). I treat them as describing a scheme that is not in force.
