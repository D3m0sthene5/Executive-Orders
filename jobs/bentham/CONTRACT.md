# Bentham build contract (shared by the four builders and the coordinator)

Bentham decides where agent tokens go. It joins what the project already measures (Hamilton: tokens per agent;
Neyman and wave dispositions: yield; Polya and the readiness tracker: how many orders an action unblocks;
Llull: base-rate discipline and ranking) into one score per candidate action:

    value  = expected dossiers now + fecundity (dossiers the action makes possible later, discounted)
    score  = value / expected cost (API-equivalent dollars, from measured tokens)

Named for Jeremy Bentham's felicific calculus (1789), which weighs certainty, propinquity (nearness in time) and
fecundity (the further goods an act makes likely) against cost.

## Rules for every builder

- Python 3.12 standard library only. Run with `python3 -I`. No network. Read committed files only.
- Repository root is the parent of `jobs/`; resolve it as `Path(__file__).resolve().parents[2]` unless `REPO_ROOT`
  is set. Write only the files your brief names. Do not commit, do not touch other folders.
- Every number you output carries `source` (a repository path) and, where Llull's `check` will read it, an
  `evidence` list of `{"quote": ..., "source": ...}` whose quote appears verbatim in that file.
- Never change a status, codebook grade, census entry, claim, or the certified count (0).
- Each module ships with `test_<module>.py` (unittest, offline, small fixtures built in a temp dir).
- Plain-English docstrings: say what a number means and what it does not mean.

## Shared data shapes

`MEASURED.json` (written by measure.py):

```json
{"rates": [<Llull base_rates row>, ...],
 "costs": {"<key>": {"usd": float, "tokens": {"fresh_input": n, "cache_read": n, "cache_write": n, "output": n},
                     "per": "attempted_order|submitted_claim|filed_dossier", "source": "path", "basis": "text"}},
 "price_table": {"<model family>": {"input": usd_per_mtok, "output": ..., "cache_read": ..., "cache_write": ...},
                 "source": "assumption: Anthropic API list prices; plan allowances are not published"},
 "waves": [{"wave": "tribonian-2026-11-04", "attempted": n, "filed": n, "source": "path"}]}
```

Llull base_rates row (copy the shape of `jobs/llull/ledger/base_rates.json` rows): `key, value, num, den, unit
("share"), source, evidence, population, pool, n_studies, note`.

Rate keys: `filed_per_attempt.<status>.<era>` with status `yes|no`, era `fr` (EO number >= 7532, in the Federal
Register index era) or `prefr`; plus `filed_per_attempt.all` and `filed_per_attempt.correction`.
Cost keys: `production.per_attempt`, `review.per_submitted`, `coordination.per_attempt`, `wave.per_attempt`
(production + review x measured submit share + coordination).

`CANDIDATES.json` (written by candidates.py): `{"generated_from": {...input paths and sha256...}, "actions": [...]}`.
Each action: `id, kind ("production"|"recovery"|"acquisition"|"zero_agent"), description, orders (count),
order_ids_path (optional), rate_key, cost_key, cost_override_usd (for zero-agent or machine jobs: 0),
unlocks: [{"orders": n, "rate_key": key, "delay_days": d, "basis": "path or text"}], prerequisites: [text],
evidence: [{"quote","source"}]`.

`GATE` (gate.py): pure functions plus a CLI, see its brief.

`USAGE` (sessions.py): sanitized per-agent rows in the column layout of
`research/excavator/claude-tribonian-2026-11-04/telemetry/AGENT_USAGE.csv`.
