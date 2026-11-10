# Maudslay conveyor

Named for Henry Maudslay. From 1803 his block-making machines at Portsmouth let a few unskilled hands do the work
of many skilled ones.

`conveyor.py` runs one claim-kit batch from reservation to filed claims. Scripts do the clerical steps, so the
coordinator model is needed only to adjudicate.

On 2026-11-09/10 an overnight Codex wave used about half the owner's weekly allowance and filed 12 claims. The
token split was:

- 54% went to Very High coordinators doing clerical steps themselves.
- 25% went to auto-review sessions triggered by sandbox escalations.
- 21% went to the workers doing the legal work.

In the same window the Papinian lane filed 63 claims for $297. Its coordinator took 17%, because small scripts did
the clerical work. The conveyor is those scripts joined into one resumable state machine.

The conveyor makes no legal judgment. It never decides an order the two review arms disagree on, never edits a
claim, and certifies nothing. Human-certified stays 0.

## Stages

Each stage writes a record to `BATCH/LEDGER.jsonl`, an append-only log. A re-run skips every stage and every
worker that is already done. A run killed mid-stage repeats only the unfinished part.

| Stage | What it does | Reused from |
|---|---|---|
| reserve | `kit.py next --agent --action --n` reserves disjoint orders, and its output is saved to `RESERVED.json` (`--ids` skips this) | Papinian `tools/reserve.py` |
| prepare | `kit.py prepare --action` builds the packet; then cruden lookups and one Geddes view per order; the prepared sheets are copied to `prepared/` | Papinian `tools/prep.sh` |
| dispatch | `kit.py dispatch-check --order ...` runs just before producers launch; it runs again on every restart that still has producers to launch | claim-kit `BATCH.md` |
| render | One producer prompt per order, built only from `prompts/producer.txt`, the route brief and that order's view. A prompt over `--prompt-cap-chars` (default 16,000) is not sent | Papinian `render_producer.py` |
| produce | Fresh worker sessions run concurrently, up to `--parallel`. Each worker writes only its own sheet folder | Cujas `launch.sh`, carnot `worker.py` |
| collect | Validates each sheet and merges it into the packet's `decisions.csv`, `clauses.csv` and `RATIONALES.json`. A missing or invalid sheet leaves the order `unresolved`, with the reason | new |
| check | `kit.py apply` into a new `applied-vN`, then `kit.py batch-check` with the actual checker. An order that fails gets `--repair-rounds` fresh producer sessions with its checker errors; if it still fails it is demoted to `unresolved` | Papinian producer prompt |
| plant | Sealed planted controls, `max(1, round(n/15))`: every end date (or later-event date, or signing date) moved back three years. A secret random salt picks the orders. The key lives in `--keys-dir`, outside the repository, and the ledger holds only its hash | Cujas `plant.py`, Papinian `review_prep.py` |
| review | Two independent blind arms (A, B). Each gets its own shuffled set and its own fresh session (or `--review-chunk` claims per session) | Papinian `review_prep.py` |
| controls | A control counts as caught only if both arms rejected its exact planted hash and named a date defect. Any miss stops the batch | Papinian `finish_pair.py` |
| reveal | A fresh session per arm reviews the genuine versions of the controls (`upheld_after_reveal`) | Papinian reveal prompt, without `--resume` |
| agree | An order files only if both arms upheld the exact version, and is blocked only if both rejected it. Anything else goes to `ADJUDICATE.json` | Papinian `finish_pair.py` both-uphold rule |
| complete | Writes the completion manifest and runs `kit.py complete`, adding `--publish` only when the conveyor got `--publish`. Output goes to the agent's own claim file | nira-sweep `make_completion.py` |
| measure | Writes `MEASURES.json`, upserts the batch line in `RUN/BATCHES.json`, and runs `bentham.py gate` | Bentham README "During a wave" |

Sheets, review sets and review outputs live inside the packet folder, under `packet/maudslay/`. claim-kit's
prior-research scan excludes only the packet itself. A claim or review file anywhere else under `research/` would
change the frozen packet and fail completion with "changed prior research".

## What goes to the coordinator

`ADJUDICATE.json` lists:

- arm disagreements and missing reviews (`blocks_completion: true`);
- workers over their item cap, and prompts over the cap (informational; those orders were not used).

The conveyor pauses with exit 3. To continue, write `BATCH/ADJUDICATION.json` and re-run:

```json
{"decisions": [{"instrument_id": "EO:N", "decision": "file", "reason": "...", "adjudicator": "..."}]}
```

The decision is `file` or `block`. A `file` decision needs the upholding arm's record. `ADJUDICATION.json` is pinned
as a completion receipt. `--defer-adjudication` instead completes at once and leaves the disagreed orders unfiled.

## Workers

Workers are set per role (`producer`, `reviewer_A`, `reviewer_B`, or one `reviewer` for both arms) in a JSON file;
see `workers.example.json`. A role's `command` is one of:

- `claude`: `claude -p --model M --output-format json --max-turns N --max-budget-usd X --permission-mode auto --add-dir REPO`
- `codex`: `codex exec --json --ephemeral --skip-git-repo-check -C BATCH -m M -c model_reasoning_effort="medium" -c model_auto_compact_token_limit=N -c tool_output_token_limit=N -c approval_policy="never" -c sandbox_mode="workspace-write" -c sandbox_workspace_write.writable_roots=["BATCH","GITDIR"...] -c sandbox_workspace_write.network_access=false -`
- an explicit argument list with `{placeholders}`.

The prompt goes on stdin. The Codex sandbox lets a worker write in the batch folder and the repository's git
directories, so normal steps need no escalation, and `approval_policy="never"` means a refused command fails
instead of starting an auto-review. Every call is a fresh session. `validate_worker_command` refuses `resume`,
`--resume`, `--continue`, `--last`, `--fork-session`, Claude's `-c`/`-r` and sandbox bypasses. It also refuses
`rollout_token_budget`, which the installed Codex build does not have.

Claude commands must carry `--max-turns` and `--max-budget-usd`. Codex commands must carry `--ephemeral`, the
compaction limit and the tool-output limit. Run `conveyor.py commands --workers FILE` to print the exact commands
without running anything.

Tokens and dollars come from each worker's own JSON: `claude -p` reports `usage` and `total_cost_usd`, and `codex
exec --json` reports `turn.completed` usage. Codex reports no dollars, so give `prices_usd_per_mtok` or the gate is
skipped rather than run on a guessed cost. Each worker also gets the carnot cost line in `BATCH/COSTS.log`, for
`bentham.py usage --reported-costs`.

## Stop rules (checked in the loop)

- **Item cap.** The cap is `--item-usd` (passed to Claude as `--max-budget-usd`) and `--item-tokens`, or a role's own
  `item_usd` / `item_tokens`, plus `--item-timeout`. A worker whose streamed usage passes the token cap is killed.
  A worker that ends over its cap has its sheet held, not used.
- **Batch budget.** `--batch-usd` and `--batch-tokens` are checked before every launch, counting running workers at
  their cap. When the next launch would pass the budget, no more workers start (exit 2). A re-run with a larger
  budget continues.
- **A missed planted control** stops the batch before reveal and completion. The batch line records
  `controls_missed`, so Bentham's gate stops the wave.
- **Zero submittable** orders after the producers, or after the mechanical checks, stops the batch.

Exit codes:

| Code | Meaning |
|---|---|
| 0 | done |
| 1 | failed (a tool or configuration error) |
| 2 | stopped by a stop rule |
| 3 | paused for adjudication |
| 4 | done, but the Bentham gate says STOP |

Batch settings are saved in `BATCH/CONFIG.json`. On a re-run, only budgets, concurrency, timeouts and the
publish/defer switches may change. Run one conveyor process per batch at a time; there is no cross-process lock.

## A 1-batch probe

Read `jobs/bentham/output/PLAN.md` first. Then:

```text
python -I jobs/maudslay-conveyor/conveyor.py commands --workers jobs/maudslay-conveyor/workers.example.json
python -I jobs/maudslay-conveyor/conveyor.py run --run-dir research/excavator/claude-maudslay-2026-11-11 --batch p01 \
    --agent maudslay --action production.claim_ready.yes.fr --n 20 \
    --route research/excavator/claude-papinian-2026-11-10/tools/prompts/route_yes.txt \
    --workers jobs/maudslay-conveyor/workers.example.json \
    --item-usd 3 --item-timeout 5400 --batch-usd 60 --parallel 4 --publish
python -I jobs/maudslay-conveyor/conveyor.py status research/excavator/claude-maudslay-2026-11-11/p01
```

After the batch:

- read `MEASURES.json` and `ADJUDICATE.json`;
- check the gate verdict in the ledger;
- when the wave ends, run `bentham.py usage --wave NAME --phase LABEL`.

## Tests

```text
python -I jobs/maudslay-conveyor/test_conveyor.py
```

The tests run the real state machine with fake workers (`fakes/fake_worker.py` writes a canned sheet or review),
so no model and no network are used. Two setups:

- **A fake kit.** `fakes/fake_kit.py` and `fakes/fake_tool.py` cover resume after a kill, the prompt cap, fresh
  sessions and budget flags, a missed control, the budget stop, the item-token kill, zero submittable, arm
  disagreement, repair and demotion, and invalid sheets.
- **The committed claim kit.** `RealKitFixtureTests` runs the kit on its own integration corpus
  (`jobs/claim-kit/test_build.py` `BuildIntegrationTests`, with `test_dispatch.py`'s raw-source retention). It uses
  the real `next`, `prepare`, `dispatch-check`, Geddes views, `apply`, `batch-check` with the actual checker, and
  `complete --publish`. Only the tracker replay is stubbed (`fakes/kit_shim.py`), as the kit's own completion tests
  stub it.

The kit test needs a checkout that holds the kit's imports (`jobs/norton`, `jobs/clause-drafts`,
`jobs/status-history`, `jobs/later-events`, `research/stage19/code`, ...). It skips in a sparse checkout unless
`MAUDSLAY_KIT_HOME` points at one.
