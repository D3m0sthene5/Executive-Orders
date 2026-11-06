# Hollerith drivers

Scripts that run one claim-kit model stage for one packet through a model runner, with a schema, validation, spending caps
and a cost log. Named for Herman Hollerith's tabulators for the 1890 census. Standard library only.

| File | What it is |
|---|---|
| `driver.py` | the driver (`draft`, `review`, `after-reveal`, `kit`, `install`, `cost`, `schema`) |
| `test_driver.py` | offline tests with the dry runner (`python3 -I research/hollerith-drivers/test_driver.py`) |
| `BILLING.md` | the sourced billing facts this design rests on, and what could not be confirmed |
| `cost/COST_LOG.jsonl` | the cost log, created on first use (commit it after each batch so the next run can read the caps) |

Nothing here decides law, files a claim, writes a status or a human review. No `claude` CLI or API key exists on this PC, so
the Claude runner was tested only against a fake subprocess; **it has never made a real call.**

## What the stages do

claim-kit stages: `prepare`, `dispatch-check`, `draft` (producer), two blind reviews with planted controls, `apply`,
`batch-check`, `complete`. Model stages go through this driver; deterministic stages are passed through to `kit.py` unchanged
and logged at zero cost, so the log shows the whole flow.

- `draft PACKET --out NEWDIR` runs `kit.py dispatch-check PACKET` and refuses unless it exits 0 (BATCH.md: an old receipt is not a
  permit). It then sends READ.md and a skeleton of the blank sheet to the model **with no tools**, validates the reply, and writes
  `decisions.csv`, `clauses.csv`, `RATIONALES.json` and `DRAFT_RECEIPT.json` into the new folder. `install DRAFT PACKET` copies
  them over the packet's blank sheets (kept as `*.blank`). Then `kit apply`, `kit batch-check`.
- `review --card CARD --source-root R --allow-source-root REL --reviewer ID --scope whole_case|partial_research --out FILE`
  is one blind reviewer. A planted control is reviewed by exactly the same command (the reviewer cannot tell). Run it twice with
  two reviewer ids and, if wanted, a `--model-family` of a different family. It writes the record `completion.review_record()` reads
  (`instrument_id`, `claim_sha256`, `reviewer`, `model_family`, `independent`, `separate_context`, `review_kind`, `scope`, `verdict`;
  plus `expected_gate_errors` for a partial acceptance) and the verdict-row fields `mountweazel.py score` reads (`item_id`, `decision`,
  `locus`, `reason`, `confidence`). The model chooses only decision, locus, reason, confidence and the gate-error list; the driver
  stamps the provenance fields and takes `--scope` from the manifest, never from the model. `FILE.receipt.json` beside the record holds
  the prompt hash, the card hash and each source's path and hash.
- `after-reveal` is the same review with `verdict: upheld_after_reveal` and a coordinator-written `--reveal-note`. Blinding checks are
  skipped there by design.
- Control seeding, the answer key, adjudication of whether a control was caught, and `complete` stay with people and the existing tools
  (COMPLETION.md: a person's recorded semantic adjudication). The driver never reads a key.
- Put `kit` options before the stage: `driver.py kit --repo . --cost-log LOG apply -- PACKET --write OUT`.

### Schemas (derived, not invented)

`python3 -I driver.py schema draft|review` prints them. Draft fields are the `ROW_FIELDS`/`CLAUSE_FIELDS` columns of `batch.py`
(a test compares them against the file), minus the identity columns the driver copies from the blank sheet. Enumerations are those
`assemble.py` and `research/stage19/code/claim_gate.py` branch on: clause state `operative|terminated|never_activated`, savings state
`none_after_bounded_search|continuing_independent|transferred_or_accrued`, outcome `submit|unresolved|blocked|route_owner`,
`publication_kind`, `checked_through` = 2026-10-14. After the schema check a second check repeats what `batch.apply` and the assembler
would reject (every member once, clause scopes equal to the inventory, `@rationale:` keys defined, end/date/confirmation rules), so a
bad draft is caught for the price of one retry rather than a review.

### Blinding, and what it does not prove

A reviewer run sees only the one card and the text files that card cites by `text_path`, read from explicit allow-roots and
hash-checked against `text_sha256` (as `blind_verify.py` does; real claims in `research/readiness/claims/` use exactly this form).
Mechanical guards, all refusals (exit 4): the card or any path names a key, sealed, adjudication, genuine, seed-receipt or mutation
location; the card carries a `verdict`, `reviewer`, `adjudication`, `seed` or `planted` field; the prompt contains a seeding marker
(`SEEDED`, `KEY.sealed`, `genuine_claim_sha256`, `seeded_by`, `leak_needle`, `MW-C1` and similar). There is no option to pass another
review or a key, and one card per run. The claude child runs in an empty temporary working directory with an empty config directory,
`--tools ""`, `--no-session-persistence`, no MCP and no slash commands, so it cannot read the repository or a key. This is
instructed-plus-mechanical blinding, **not proof**: BLIND_VERIFY.md says filename heuristics cannot prove it, and a marker the seeder did
not think of passes. It does not make two reviewers independent: `independent` and `separate_context` are assertions about the process
the driver controls. A real claim with a legitimate field named `reviewer` or `verdict` would be refused (fail closed).

## Spending caps and the cost log

Three caps, all read from the JSONL log **before** any model call: per run (`--max-run-usd`, default 2), per UTC day (`--max-day-usd`,
default 10) and campaign total (`--max-total-usd`, default 100). A run starts only if all three have room; each attempt is granted
the smallest remaining amount as `--max-budget-usd`; the one allowed retry is skipped if the run cap is spent. Exit 3 means refused with
no call made. A call whose cost is not reported counts as the whole budget it was granted (`cost_assumed: true`), never zero. Caps apply
to `total_cost_usd`, which Anthropic calls a client-side estimate (BILLING.md F6), so they are conservative, not a bill.

Each row: `ts, run_id, stage, packet, role, attempt, model, auth_basis, tokens{input,output,cache_creation,cache_read},
total_cost_usd, cost_counted_usd, cost_assumed, wall_seconds, outcome, prompt_sha256, errors`. `driver.py cost` summarizes it. The log
is a file: one writer at a time (use a GitHub `concurrency` group) and commit it after every batch. It holds hashes, never prompt or
output text.

## The decision the owner must make (from BILLING.md)

Logged in with a Max or Ultra subscription, `claude -p` draws on the subscription's usage limits, not on metered API billing; the "separate
monthly credit" reported in June 2026 was paused on 15 June 2026. There are two ways to authenticate on a runner, and the driver makes you
choose with `--auth`:

1. **`--auth subscription`** with `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token` (one-year token, Ultra plan). No dollars leave the
   100 USD ceiling, because nothing is metered, but the work **competes with the owner's own chat and interactive Claude Code for the same
   limits**, `--bare` is unavailable (the driver isolates with an empty working directory and config directory instead), and
   `total_cost_usd` may be a list-price estimate or absent. Before choosing it: read Anthropic's consumer terms on automated use (not
   checked), turn off extra usage and auto-reload so a limit cannot turn into silent spend, and keep the secret away from fork pull
   requests. The token is tied to the owner's account.
2. **`--auth api-key`** with `ANTHROPIC_API_KEY` (no key exists yet). Metered at list price; this is what the 100 USD ceiling governs. `--bare`
   is used. If the owner links a Console organization on the Ultra plan, a separate API credit of $200 a month applies to this usage
   (BILLING.md F2), expiring monthly; it does not exist until linked. The Message Batches API (50 percent off, 24-hour window) is **not**
   available through `claude -p`, and nothing documented says the Agent SDK can use it; a batch route would be a different driver that calls
   the Messages Batches API directly with everything in the prompt. The no-tool draft and review prompts here are already self-contained, so such
   a driver could reuse them; it is not built.

Or neither: keep using subagents. The owner decides; the driver and its caps are the same in every case. Suggested order, if the owner agrees:
option 1 for the measured pilot only if the terms check out, else option 2 with `--max-total-usd 5`.

## Running it on GitHub's runner

Not wired up (no workflow file was added: this stream writes only under `research/hollerith-drivers/`). A job would, in order:

```yaml
concurrency: { group: hollerith, cancel-in-progress: false }      # one writer of the cost log
steps:
  - uses: actions/checkout@v6                                      # sparse paths: the packet, the cited text files, jobs/claim-kit, this folder
  - run: curl -fsSL https://claude.ai/install.sh | bash -s 2.1.89  # pin a version the campaign has tested; native installer, no Node needed
  - run: echo "$HOME/.local/bin" >> "$GITHUB_PATH"
  - run: DISABLE_AUTOUPDATER=1 claude --version
  - run: python3 -I research/hollerith-drivers/test_driver.py
  - run: python3 -I research/hollerith-drivers/driver.py draft PACKET --auth api-key --max-day-usd 5 --out PACKET/draft-v1
    env: { ANTHROPIC_API_KEY: "${{ secrets.ANTHROPIC_API_KEY }}" }          # or CLAUDE_CODE_OAUTH_TOKEN with --auth subscription
  - run: git add research/hollerith-drivers/cost && git commit ... && git push                  # the cost log, always, even on failure
```

The secret is a repository secret named `ANTHROPIC_API_KEY` (option 2) or `CLAUDE_CODE_OAUTH_TOKEN` (option 1); the driver reads it only from
the environment and never writes it. The version number above is the example from the setup page, not a tested pin. Follow `jobs/README.md`
and the byte rules in WORKER_RULES.md for the commit step; the repository is near its size cap.

## Measured-cost plan (nothing has been spent)

1. Rehearse the flow end to end with `--runner dry` at zero cost (the tests do this).
2. Run **one** batch first: one prepared packet of at most 6 orders (the 2026-10-18 pilot packet's READ.md is 263,944 bytes, roughly 66,000
   tokens at four characters a token, which is an estimate, not a count). One draft call, then two blind reviews per submitted claim plus the
   planted controls, then `kit apply` and `batch-check`. Use `--max-run-usd 2 --max-day-usd 5` for the pilot. Per CLAUDE.md read
   `jobs/bentham/output/PLAN.md` first and run `bentham.py gate` after the batch.
3. Compare with the same packet done by subagents, from the existing telemetry: `jobs/geddes/telemetry.py` with an `agent_id,batch,role,track`
   roster and `geddes.py cost` (BATCH.md), counting cache reads, cache writes and output separately. The comparison that matters is cost and
   wall time **per filed, reviewed claim**, including failed, blocked and corrected work, not tokens per call.
4. Read the cost log: tokens by type, `cost_assumed` rows (zero is the goal), retries, and under option 1 whether `total_cost_usd` was reported at all.
5. Only then decide whether to scale, and whether a direct Messages-Batches driver is worth building (it would halve token prices but cannot loop on tools).

For scale only: at the listed Opus 5.5 prices ($4 per million input, $20 per million output, cache reads at 0.05 times input), a 66,000-token
packet read once costs about $0.26 of input before output and caching; that single figure is arithmetic on an estimated token count, not a measurement.

## Limits

- The Claude runner has never run for real: flags and the JSON result shape are from the docs read on 2026-11-06 (BILLING.md), not from a live call.
  `--tools ""`, `--max-turns 4` and `--json-schema` interact in ways to confirm on the first real call; the driver also parses a JSON `result`
  string if `structured_output` is absent.
- The draft is a single no-tool call over READ.md, so it cannot run `kit view --source` for overflow text; the prompt tells the model to block
  rather than guess. The legal quality of drafts is unmeasured: this stream measures plumbing and cost only.
- READ.md over 900,000 characters and review sources over 300,000 characters are refused rather than truncated.
- No `.github` workflow, no `jobs/` folder, no pull request.
