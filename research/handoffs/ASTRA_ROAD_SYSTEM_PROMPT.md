# Astra: build the road system (shared infrastructure that makes all later work cheap)

**From the owner, 2026-10-17.** We are building roads, not making one more trip. Build
three pieces of shared infrastructure that every agent (Astra, Opus, Codex, Claude)
uses afterwards. Each must save measured agent tokens or wall time, run with zero
model tokens, and land as **its own pull request** with tests and a measured result.

Read first: `HANDOFF/README.md` and the newest notes, `AGENTS.md`,
`research/readiness/README.md` (standard procedure), `jobs/README.md` (runner,
`triggers.txt`, `after.txt`, `DAILY`, parallel-worker pattern), and the outputs of
`jobs/later-events`, `jobs/claim-drafts`, `jobs/claim-checker`,
`jobs/readiness-tracker`.

## Road 1: family rule engine (`jobs/family-rules/`). Highest token saving.

945 decided orders with a whole-order-end candidate trace to only 187 acting
instruments. The largest family has 335 targets, and families of 5+ cover 784
orders. Today an agent would analyse each target separately.

- **Rule files** written by agents in `research/readiness/rules/<rule_id>.json`:
  - acting instrument, mechanism, and effective date;
  - the exact operative clause, quoted with a claim-compatible source (url, sha256, page);
  - the scope (explicit target list, or "every target of acting X with an unqualified revocation edge in later-events");
  - exceptions and savings, with sources;
  - `written_by`, `checked_on`.
- **The job** applies each rule to every matching target and writes:
  - `FRAGMENTS.jsonl` (whole-order-end and later-event candidates citing the rule's source), which claim-drafts merges automatically;
  - a per-target **proof certificate**: the rule id, plus the case-specific checks passed or failed.
- **Checks the machine must run per target:**
  - the edge is unqualified (no "in part" or "insofar as");
  - no conflicting date;
  - the target is not cited in current law after the rule date (current-law output);
  - no independent clause or savings lead in clause-drafts;
  - not already ended earlier by another rule.
- **Counterexample sweep.** Search every saved text and current-law mention for the target being used or cited after the rule's date. Any hit blocks the certificate.
- **Done when:** the top 5 families have rule files (you write them, checking the sources yourself), the job produces certificates, and claim-checker passes their sources. Report agent tokens and time per family, against the per-order baseline.

## Road 2: case bundles and a daily digest (`jobs/case-bundles/`). Saves tokens on every action.

- One JSON file per order: `output/bundles/<prefix>/EO_<n>.json`, under 30 KB, deterministic, written for all 3,359 decided orders first. Each contains:
  - the identity and OFR index row, and the provisional status;
  - the readiness steps and blockers;
  - the claim draft and its open gate errors;
  - every fragment by kind, with its sources;
  - saved-text pointers (path, sha256, the first ~1,500 characters);
  - later events, current-law hits, conflicts, and Opus note pointers;
  - links to the raw files.
- Plus `INDEX.csv` (one row per order, with its bundle path).
- **The goal:** an agent reads **one file through the GitHub connector** to start an order.
- **Daily digest, `HANDOFF/DIGEST.md`.** A machine-written page under 150 lines: the tracker headline, what changed since yesterday, the top 10 unlocks, open asks from each agent's notes, and jobs that failed. Agents read it instead of long histories. Write it from a job run with a `DAILY` file, so the bot commits it.
- **Done when:** median bundle size, and agent tokens to start one order before and after, are measured on 10 orders.

## Road 3: runner speed (`.github/` and `jobs/_lib/`). Saves time.

- **Keep download caches between GitHub runs** with `actions/cache`, keyed per job, with restore keys and a size cap per job (the repo limit is 10 GB, oldest evicted first). Today every run re-downloads everything.
- **`jobs/_lib/fetch_pool.py`.** A shared parallel fetcher following the `fr-originals` `JOB_WORKERS` pattern:
  - thread or process workers;
  - a per-host concurrency limit (default 6);
  - robots.txt and per-worker spacing;
  - sha256 custody;
  - one result file per item, so runs can resume.

  Adopt it in `source-ladder` (774 Opus re-fetch files plus 90 shared sources) and in your `early-ranger-*` downloaders.
- **Optional `shards.txt`** for a job. The workflow then runs that job as N parallel runners (a matrix), uploads each runner's results as an artifact, and a final step merges them and commits once. Use it only for very large one-off jobs.
- **Done when:** a second GitHub run of source-ladder shows cache hits, and you report wall time before and after for one parallel job.

## Rules (all roads)

- Machine outputs are leads and custody. Never change a provisional status, a ledger row, the codebook, or a count. Nothing is certified.
- **Do not edit `jobs/fr-originals/`.** Claude's parallel-workers pull request is open for it; read it as the reference pattern.
- Pin every package exactly; permissive licences only (no AGPL). Tests run with no network.
- Make outputs deterministic: identical bytes on Windows and Linux, independent of hash seeds. Claude found later-events edge ids that differ between Windows and Linux; fix that if you touch it.
- **Report in `HANDOFF/notes-astra.md`:** for each road, the measured saving (tokens, minutes, MB) and anything you could not verify.
