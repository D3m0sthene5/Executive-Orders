# Research brief: tools that could speed up "The Afterlife of Executive Orders"

Today is 2026-11-06. Your training data is older than the tools you are asked about, so use WebSearch and WebFetch
heavily. Search forums too: Hacker News (news.ycombinator.com, hn.algolia.com), Reddit (r/ClaudeAI, r/LocalLLaMA,
r/ChatGPTCoding, r/LawSchool, r/datasets, r/LegalTech), GitHub issues and discussions, Lobsters, X/Twitter threads
quoted in articles, Substack and blog posts, vendor docs and pricing pages, and academic or industry reports. Prefer
pages you actually opened over search snippets. Leave no stone unturned within your scope, and include tools
released in 2025-2026 that you have never heard of.

## The project

A law student (Danny, NYU Law 1L) runs an empirical legal-history project. It aims to determine, for every US
executive order (about 15,000+ orders since 1789, numbered and unnumbered), whether it still has legal effect or
has ceased, when, and why, and how often a formal revocation only cleaned up an order that was already dead. The
goal is a reproducible dataset, a published analysis and a law-review article. The standard is modelled on
Lean-style machine-checked mathematics: every claim must cite exact byte spans of held, hash-verified source
texts, pass automated checkers, and pass two independent blind AI reviewers with planted false controls. Final
certification is by independent humans; the certified count is still 0.

How it runs today:
- One GitHub repository (about 9 GB on GitHub, 8.4 GB .git, 93 job folders). Data is JSONL, CSV and text files
  committed to git, including downloaded source texts and PDFs.
- Deterministic Python "jobs" run on GitHub Actions (free hosted runners). Jobs on one branch run one after another;
  a freshness guard throws away a run if its inputs changed while it ran. Jobs download from govinfo.gov (Federal
  Register, Statutes at Large, CFR), federalregister.gov API, HathiTrust, Internet Archive, the American Presidency
  Project and similar, with robots.txt respected and per-host rate limits. Large jobs download 20+ GB per run.
- AI work is done by many separate agent sessions: Claude Code (Opus 5.5 coordinating, Sonnet 5.5 workers) and
  OpenAI's GPT-6 "Astra"/Codex. They coordinate only through markdown handoff notes committed to the repo, a
  register of findings and owner questions ("Kean"), pull requests and a coordinator file. Sessions often collide:
  merge conflicts, merge freezes on main, stale-input refusals, duplicated work, and long waits.
- A "claim kit" pipeline: prepare a sealed packet of evidence per batch of ~8 orders; a cheaper model drafts
  structured claims (CSV of decisions and clauses); two Opus reviewers check them blind; a claim files only if both
  uphold its exact hash. Each batch costs roughly 10-25 USD of model tokens and 30-60 minutes.
- Scanned historical documents (Federal Register 1936-1993 daily issues, Statutes at Large, Congressional Serial
  Set, microfilm of EO 1-7403) are read through OCR layers of varying quality. Original-page custody is a major
  blocker for many orders.
- A public HTML site (dannykind.wiki/eo/...) shows per-order progress cards built from the repo.
- Known pain points: slow downloads; GitHub Actions serial execution and 6-hour job limits; repo bloat; agent
  sessions that cannot authenticate the `claude -p` CLI in some containers; token cost of reviews; coordination
  between Claude and GPT sessions; OCR quality on 1930s-1990s scans; finding when a later statute, order or
  proclamation ended an order; finding current legal status sources (current CFR, U.S. Code notes).

## What to return

Write your findings to the markdown file named in your task, then reply with a summary of at most 150 words.
For each tool or source, one block:

- **Name** (link to the page you opened) — what it is, in one or two plain sentences.
- Cost (price and plan, with the date of the pricing page) and maturity (release date, stars, users, company).
- Evidence from users: what forums and reports say, good and bad, with links. Mark hype versus measured results.
- Fit: which specific bottleneck above it addresses, and what adopting it would take (hours, money, migration).
- Verdict: ADOPT NOW, TRY (small pilot), WATCH, or SKIP, with one sentence why.

Be skeptical and specific. Say when something is vaporware, abandoned, closed beta, or overhyped. Do not pad: a
tool that does not fit gets one line under "Considered and rejected". End with a ranked top 5 for your scope.
Do not modify anything in /home/claude/Executive-Orders. Do not sign up for anything or enter any credentials.
