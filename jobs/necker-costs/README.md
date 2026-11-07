# Necker: dollars per worker and per claim batch

Named for Jacques Necker, whose 1781 *Compte rendu* was the first public account of the French crown's finances.

**Every dollar here is an API list-price estimate, not a bill.** Under a Claude subscription nothing is charged per
token; the figures then measure how large a piece of work was, in the one unit the project already uses to rank it
(Bentham's "API-equivalent dollars").

## Why it exists

Bentham ranks agent work by yield per API-equivalent dollar. Its price table (`jobs/bentham/measure.py`) is fixed at
Sonnet 3/15 and Opus 5/25 USD per million tokens with one cache-write rate, and the earlier proof-batch figures of
10 to 25 USD were estimates from subagent token counts that treat cache reads like full-price input. Necker prices every
message at the list price of the model that made it, with separate rates for input, output, 5-minute cache write,
1-hour cache write and cache read (`PRICES.json`, from <https://platform.claude.com/docs/en/about-claude/pricing>,
read 2026-11-06; `docs.claude.com` redirects there), then adds up per session, per worker (subagent), per model, per
day and per batch.

## Run it

```
py -I jobs/necker-costs/test_necker.py                    # 23 offline tests
bash jobs/necker-costs/refresh.sh 2026-11-06T22:40:00Z    # rebuilds output/ (the cutoff makes the run repeatable)
py -I jobs/necker-costs/necker.py transcripts PATH... --out DIR [--until ISO] [--action-ids JSON]
py -I jobs/necker-costs/necker.py telemetry AGENT_USAGE.csv --wave W [--disposition DISPOSITION.json] --out DIR
py -I jobs/necker-costs/necker.py compare WAVE=AGENT_USAGE.csv ... --out DIR
py -I jobs/necker-costs/necker.py validate PATH... [--trace TRACE.jsonl] --out DIR
```

Standard library only. `refresh.sh` reads Claude Code transcripts from `~/.claude/projects` (private; never
committed) and the committed telemetry from `origin/main` with `git show`.

## What is in `output/`

| File | Content |
|---|---|
| `BATCH_COSTS.csv` | one row per wave and batch: `batch, attempted, submitted, filed, controls_missed, usd` (the columns `bentham.py gate --batches` reads) plus production, review and other dollars, the Bentham-table dollars, the lumped dollars, cache-read tokens |
| `WORKER_COSTS.csv` | one row per worker: model, tokens by category, dollars, batch and the evidence for it |
| `telemetry/<wave>/gate_<wave>.csv` | gate-ready batch file (exact batches only; composite and correction batches left out) |
| `local/` | transcripts on this PC: `SUMMARY.json` (by model, day, attribution, reconciliation), `SESSION_COSTS.csv`, `WORKER_COSTS.csv`, `BATCH_COSTS.csv` |
| `validation/VALIDATION.json` | the price table against the CLI's own `cost-state` totals and Herschel's `cli_cost_usd` |
| `comparison/COMPARISON.{md,json}` | token count, Bentham dollars, Necker dollars and the lumped estimate for the measured waves |
| `INPUTS.json`, `BUDGET.json` | SHA-256 of every input file; bytes written (about 0.4 MiB in all) |

Rows hold session-id hashes (12 hex of SHA-256), agent ids, model ids, timestamps, token counts, dollars and batch
labels taken by fixed patterns. No prompt, message text or tool input is written; the writer refuses if any string of
24 or more characters from the transcripts' message content would appear in a file (it caught the pricing URL once,
which a session had quoted; strings of `PRICES.json` are now exempt).

## How a message is priced

* One message is counted once however many transcript records repeat it (the largest value of each counter wins;
  streaming records carry partial counts). 13,531 duplicate records collapsed in the snapshot.
* Output tokens include thinking tokens, as billed. Cache writes use `usage.cache_creation.ephemeral_5m/1h_input_tokens`;
  a total without a split would be priced at the 5-minute rate and counted as unclassified (none occurred).
* Opus 5.5 and Sonnet 5.5 cache reads list at 0.05x base input (0.20 and 0.10 USD per MTok); Fable 5.1 at 0.025x. Opus
  5.5 fast mode doubles every rate; Haiku 5.5 has a long-prompt tier (over 100,000 prompt tokens, per request).
* An unknown model is reported as unpriced, never as free.

### Check against the CLI's own cost

Claude Code writes `cost-state` records (its running dollar total per model). On this PC 22 sessions have one.

* Using the transcript's own cache-write split, Necker reproduces the CLI total to four decimals in 13 of 21
  session-model rows: every Fable 5.1 row and every Opus 5.5 row whose output tokens are complete. The prices are right.
* In the other rows the transcript holds less output than the CLI counted: some transcripts record output tokens at the
  start of streaming only (5,198 of 11,239 messages never record a stop reason). Priced as recorded, the 20 sessions
  that have a CLI total come to 87.4% of it (792.60 of 907.06 USD). `usd_repaired` adds output estimated from the
  characters the model wrote (0.586 output tokens per character, measured on messages with a final count) and reaches
  95.7% (867.97 of 907.06). Treat `usd` as a lower bound and `usd_repaired` as an estimate. The committed telemetry from
  cloud waves was built from transcripts the same way, so its output component can be low too.
* Herschel's `cli_cost_usd` (43 workers, 62.81 USD): the 31 Sonnet workers match Necker within 1.2% (CLI 15.94, Necker
  16.12). The 12 Opus workers cost the CLI 46.87 USD, which is 1.93 times the standard Opus 5.5 list price (24.33) and 0.96
  times the same tokens at the fast-mode price (48.67). **Open question for the owner: were the Herschel Opus workers run
  with fast mode?** If the tribonian Opus rows also were, they (210.03 USD) double.

## Results (snapshot cutoff 2026-11-06T22:40Z)

### Transcripts on this PC (368 files, 22 sessions, 321 workers or coordinators with messages)

| Model | Messages | Priced USD | Output tokens | Cache read tokens | Cache write 5m / 1h tokens |
|---|---:|---:|---:|---:|---:|
| claude-opus-5-5 | 9,218 | 749.03 | 4.71M | 2,049.4M | 33.5M / 9.7M |
| claude-fable-5-1 | 377 | 194.32 | 0.82M | 146.1M | 0 / 5.8M |
| claude-sonnet-5-5 | 1,636 | 65.21 | 1.97M | 173.1M | 11.3M / 0 |
| claude-haiku-5-5 | 8 | 0.01 | 0.001M | 0.4M | 0.08M / 0 |
| **Total** | 11,239 | **1,008.58** (repaired 1,083.95) | | | |

Per-day figures are in `output/local/SUMMARY.json` (`by_day`). Cache reads are 46.0% of the priced dollars (463.73 USD).
Priced as full-price input they would read 10,413.79 USD, 10.3 times the priced figure.

### Batch attribution

Only transcripts of workers (subagents) can be attributed; a coordinator's cost is not split across batches. Evidence
counted: the Workflow task label in `agent-*.meta.json` being exactly `produce:<id>`, `review:<id>` or
`Lane <n> <kind> <code>`, or a Bash command running `bentham.py gate --action <known id>`. A packet path or an action
id named in a worker's first message is recorded as `weak_label` and is **not** counted (1.93 USD).

| | USD | Share of all | Share of worker cost |
|---|---:|---:|---:|
| Attributed | 248.55 | 24.6% | 47.6% |
| Unattributed workers | 273.43 | 27.1% | 52.4% |
| Coordinators (22 main transcripts) | 486.60 | 48.2% | |

Attributed, by evidence: Lane work-item labels 135.08, `produce:` 63.19, `review:` 50.28, `gate --action` 0. **No
transcript on this PC contains a Bentham gate call, so none of the Bentham action ids is attributable.** The claim waves
Bentham measured (tribonian, icecore, theophilus) ran in cloud sessions whose transcripts are not here; their token
counts were committed as `AGENT_USAGE.csv`, which Necker reprices per batch (`telemetry` command).

Per-batch dollars from transcripts (all Opus 5.5, the 2026-10-18 batch run, `produce:` plus `review:`; `usd_repaired`
in parentheses): b0 7.08 (8.56), b1 9.91 (11.63), b2 10.71 (12.78), b3 9.91 (11.69), b4 14.13 (16.43), b5 15.86 (18.47),
b6 11.78 (13.85), b7 14.95 (17.48); together 94.32 (110.89), of which producers 63.19 and reviewers 31.13. The ten
`review:<name>` labels of 2026-10-17 (claim-checker, current-law and others) are tool reviews, not claim batches; they are
in `local/BATCH_COSTS.csv` under their names. Lane work items: lane1.gpo 51.88 (43 workers), lane4.replica 48.54 (86),
lane3.free 22.67 (46), lane2.csc 8.90 (12), lane4.adjudication 3.10 (5).

### Waves Bentham already measured: token count against price

| Wave | Agents | Tokens | Cache reads, share of tokens | Bentham table USD | Necker USD | Necker / Bentham | Lumped USD | Cache reads, share of Necker USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tribonian-2026-11-04 | 78 | 1,354,974,123 | 96.2% | 815.18 | 419.36 | 0.51 | 3,720.64 | 41.8% |
| claude-icecore-2026-11-05 | 7 | 98,946,980 | 97.2% | 59.25 | 32.92 | 0.56 | 297.57 | 43.0% |
| claude-theophilus-2026-11-05 | 11 | 109,086,406 | 97.7% | 73.46 | 41.70 | 0.57 | 397.09 | 45.5% |

"Bentham table USD" applies `measure.py`'s table to every row of the CSV (including coordinator and trial arms;
Bentham's own `wave.per_attempt` total, 672.81 USD, selects fewer rows). "Lumped" prices cache reads and writes as
full-price input at the current rates. In tribonian, 96.2% of tokens are cache reads, which are 41.8% of the priced
dollars (175.29 of 419.36); output is 24.6% (103.33) and cache writes 33.5% (140.69). Bentham's table is about twice
too high because it prices Sonnet 5.5 as Sonnet 4.x and Opus 5.5 as Opus 5 (Necker / Bentham is 0.47 for production
rows, 0.57 for review, 0.52 for coordination). Scaling Bentham's unit costs by those ratios gives about 0.18 USD per
attempted production order (Bentham has 0.376), 0.23 per reviewed claim (0.399) and 0.016 for coordination, so a wave
at about 0.33 USD per attempted order (0.646) and 0.70 per filed dossier (1.37). These are derived, not recomputed by
Bentham; see `PROPOSAL.md`. The 751,000 tokens of context per attempted order that Bentham reports is a size, not a
price; at current list prices most of it costs a tenth to a twentieth of fresh input.

Per-batch tribonian dollars are in `output/telemetry/tribonian-2026-11-04/BATCH_COSTS.csv`: for example o01 13.23 USD
for 30 attempted, 27 submitted, 25 filed; a03 6.73 USD for 33 attempted, 12 filed. A gate file built from it runs
unchanged: `bentham.py gate --action production.claim_ready.no.fr --batches
output/telemetry/tribonian-2026-11-04/gate_tribonian-2026-11-04.csv` returned CONTINUE (the gate reads `attempted`,
`filed` and `controls_missed`, and reports `usd` as money spent).

## Limits

* List prices applied to recorded tokens; no discount, credit, tax, plan allowance or data-residency multiplier. If a
  worker used fast mode the transcript's `usage.speed` says so (all local messages say `standard`; the committed
  telemetry has no speed field).
* Output tokens are a lower bound where a stop reason was never recorded (see above).
* A transcript attributed to a label is assigned wholly to it; a worker that served two batches is not split. Composite
  telemetry batches (`a01+o17+o22` and others) are kept as their own rows and left out of gate files.
* Transcripts are private and sit on this PC only; re-run `refresh.sh` there. The numbers move as sessions grow, which is
  why `refresh.sh` takes a cutoff.
* Nothing here changes a status, claim, codebook grade or count. Certified: 0.
