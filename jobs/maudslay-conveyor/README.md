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

## Where things live

| Place | What is there |
|---|---|
| `BATCH/` = `RUN_DIR/BATCH` in the repository | `LEDGER.jsonl`, `CONFIG.json`, `RESERVED.json`, `prepared/` sheets, `prompts/` copies, `logs/`, `COSTS.log`, `CONTROLS.json` (after blind review), `ADJUDICATE.json`, `MEASURES.json`, and the kit's `packet/` |
| `SCRATCH/workers/LABEL/` (outside the repository) | One fresh, empty working folder per worker session: its `PROMPT.txt`, its sheet or its review set, and its output |
| `SCRATCH/out/` | Each worker's event stream (`.out`) and stderr |
| `SCRATCH/control/` (`--keys-dir`) | The sealed control key, the planted review set and per-arm sets, the genuine control claims, and the coordinator's `ADJUDICATION.json` |

`SCRATCH` is `--scratch-root`. It is required and has no default. It must be a durable folder outside the
repository and outside the system temp folder, because it holds paid worker output and the sealed key.

On resume, a finished worker whose folder or output is gone is a hard failure ("scratch lost"), never an invalid
sheet. Missing control material after planting is a clear error.

No worker runs inside the repository, so none loads its `CLAUDE.md` or `AGENTS.md`. Claude workers get the
repository with `--add-dir`; the conveyor removes `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` from their
environment. Codex workers get `-C` set to their own folder, which is also their only writable root.

Planted claims, review sets and the key never enter `research/`. The only files under `research/` that carry a
planted claim's hash are the post-reveal records the kit's completion needs:

- `packet/reviews/BLIND_REVIEW_{A,B}.jsonl` and `AFTER_REVEAL_{A,B}.jsonl`, written at completion;
- `packet/completion/` seed receipts and control adjudications;
- the kit's `complete-vN/` outputs.

That matters twice:

- claim-kit's prior-research scan excludes only the packet folder, so a claim or review file elsewhere under
  `research/` would fail completion with "changed prior research";
- a reviewer cannot find a planted claim's genuine twin or the key under `research/`.

## Stages

Each stage writes a record to `BATCH/LEDGER.jsonl`, an append-only log. A re-run skips every stage and every worker
already done.

| Stage | What it does | Reused from |
|---|---|---|
| reserve | `kit.py next --agent --action --n`. Its output is written atomically to `RESERVED.json` right after the call returns. If an earlier run may have reserved without leaving `RESERVED.json`, the conveyor refuses to call `next` again. `--ids` skips this stage | Papinian `tools/reserve.py` |
| prepare | `kit.py prepare --action`, then cruden lookups and one Geddes view per order; the prepared sheets are copied to `prepared/` | Papinian `tools/prep.sh` |
| dispatch | `kit.py dispatch-check --order ...` just before producers launch, again on every restart that still has producers to launch | claim-kit `BATCH.md` |
| render | One producer prompt per order, from `prompts/producer.txt`, the route brief and that order's view only. A prompt over `--prompt-cap-chars` (default 16,000) is not sent | Papinian `render_producer.py` |
| produce | Fresh sessions, concurrent up to `--parallel`, each in its own folder seeded with that order's prepared rows | Cujas `launch.sh`, carnot `worker.py` |
| collect | Validates each sheet and merges it into the packet's `decisions.csv`, `clauses.csv` and `RATIONALES.json`. A missing or invalid sheet leaves the order `unresolved`, with the reason | new |
| check | `kit.py apply` into a new `applied-vN`, then `kit.py batch-check` with the actual checker. A failing order gets `--repair-rounds` fresh sessions (in a new folder, with a copy of its sheet and the errors); if it still fails it is demoted to `unresolved` | Papinian producer prompt |
| plant | Sealed planted controls, `max(1, round(n/15))`: every end date (or later-event date, or signing date) moved back three years. A secret random salt picks the orders. All control material stays in `SCRATCH/control`; the ledger holds only counts and the key's hash | Cujas `plant.py`, Papinian `review_prep.py` |
| review | Two independent blind arms (A, B), each in its own folders holding only a prompt and a separately shuffled set, `--review-chunk` claims per session (default 10) | Papinian `review_prep.py` |
| controls | A control is caught only if both arms rejected its exact planted hash and a whole word or field name in their `defects` names a date (`date`, `first_end`, `whole_order_end`, `signing_date`, `effective_date`, `later_events`, `year` ...). `reasons` are not read, and "mandate" or "update" does not count. Any miss stops the batch | Papinian `finish_pair.py`, tightened |
| reveal | A fresh session per arm, in a new folder holding only the genuine control claims (`upheld_after_reveal`) | Papinian reveal prompt, without `--resume` |
| agree | An order files only if both arms upheld the exact version, and is blocked only if both rejected it. Anything else goes to `ADJUDICATE.json` | Papinian `finish_pair.py` both-uphold rule |
| complete | Writes the review records and manifest, then runs `kit.py complete`, adding `--publish` only when asked. The publication mode is `own_claims` unless `--replacement-proposal` is given (then `replacement_proposal`), and `--publication-mode` sets it explicitly, for example `own_claims` for agent `claude` correcting its own filed claims. If a `complete-vN/PUBLICATION.json` already says `written: true` (a run killed after publishing), that publication is adopted and recorded instead | nira-sweep `make_completion.py` |
| measure | Writes `MEASURES.json`, upserts the batch line in `RUN/BATCHES.json`, and runs `bentham.py gate` | Bentham README "During a wave" |

## Blinding is checked, not just asked for

Workers must emit events: Claude runs `--output-format stream-json --verbose`, and Codex runs `--json`. The conveyor
follows each event file as it is written and scans every tool call's arguments:

- Claude `tool_use` inputs;
- Codex `command`, `path`, `changes`, `arguments` and `query`.

Any worker that names one of these paths is killed:

- a path under the scratch root outside its own folder, such as another worker's folder or the other arm's folder;
- the control folder.

A reviewer is also killed for naming anything under the batch folder except:

- `packet` itself;
- `packet/PACKET.json`;
- `packet/undecided/*/EVIDENCE.json`, which `batch.load_packet` reads. Such a reviewer's arm fails, the batch stops (exit 2), and that record is never retried.

## What goes to the coordinator

`ADJUDICATE.json` lists:

- arm disagreements and missing reviews (`blocks_completion: true`);
- workers over their item cap, and prompts over the cap (informational; those orders were not used).

The conveyor pauses with exit 3. To continue, write `SCRATCH/control/ADJUDICATION.json` and re-run. The control
folder is one no worker may name or write; a file in the batch folder is ignored.

```json
{"decisions": [{"instrument_id": "EO:N", "claim_sha256": "<from ADJUDICATE.json>", "decision": "file", "reason": "...", "adjudicator": "..."}]}
```

A decision is accepted only if all of these hold:

- the file is newer than the batch's first `ADJUDICATE.json`;
- it names an item that is awaiting adjudication, with that item's exact `claim_sha256`;
- it says `file` or `block`;
- it names an adjudicator.

A `file` decision needs the upholding arm's record. The file is copied into the batch folder and pinned as a
completion receipt. `--defer-adjudication` instead completes at once and leaves the disagreed orders unfiled.

## Workers

Workers are set per role (`producer`, `reviewer_A`, `reviewer_B`, or one `reviewer` for both arms) in a JSON file;
see `workers.example.json`. A role's `command` is one of:

- `claude`: `claude -p --model M --output-format stream-json --verbose --max-turns N --max-budget-usd X --permission-mode auto --add-dir REPO`
- `codex`: `codex exec --json --skip-git-repo-check -C FOLDER -m M --config model_reasoning_effort="medium" --config model_auto_compact_token_limit=N --config tool_output_token_limit=N --config approval_policy="never" --config sandbox_mode="workspace-write" --config sandbox_workspace_write.writable_roots=["FOLDER"] --config sandbox_workspace_write.network_access=false -`
- an explicit argument list with `{placeholders}`.

The prompt goes on stdin. Every call is a fresh session. Only the `claude` and `codex` families are accepted for
now; `generic` is refused. The family is inferred from the program name, and a program named `claude` or `codex`
must be declared as that family.

`validate_worker_command` refuses, in any template:

- `-c`, `-r`, `--continue`, `--resume`, `resume`, `--last` and `--fork-session` (Codex settings use `--config`);
- sandbox and permission bypasses;
- `rollout_token_budget`, which the installed Codex build does not have.

Claude commands must carry `--max-turns`, `--max-budget-usd` and `stream-json`. Codex commands must carry
`--skip-git-repo-check`, the compaction limit, the tool-output limit and `approval_policy="never"`. They must not
carry `--ephemeral`, because the session's rollout file is how the token cap is read mid-run.

Every role needs an item dollar cap. A Codex role is refused unless it also has an item token cap and
`prices_usd_per_mtok`, and its spend always counts at least its item dollar cap toward `--batch-usd`. Run
`conveyor.py commands --workers FILE` to print the exact commands without running anything.

Tokens and dollars come from the workers' own events:

- **Claude:** the `result` event's `usage` and `total_cost_usd`; while it runs, the last usage per assistant message.
- **Codex:** `codex exec --json` reports usage only at `turn.completed`, after the spend. So while a Codex
  worker runs, the conveyor also follows its session's rollout file,
  `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*-<thread>.jsonl`. The thread id comes from the first `thread.started`
  event. Each model call appends a `token_count` event with the cumulative `info.total_token_usage`, the format
  carnot `meter.read_rollout` reads. The worker tree is killed when that total crosses the item token cap. A
  worker killed mid-turn is priced from the rollout total.

Each worker also gets the carnot cost line in `BATCH/COSTS.log`, for `bentham.py usage --reported-costs`.

## Crash safety

- A worker writes its events straight to `SCRATCH/out/LABEL.out`. Its PID and launch time are recorded in a
  `launched` ledger record.
- On every start the conveyor reaps workers a dead run left behind:
  - one still alive is killed (`taskkill /T` on Windows, its process group elsewhere; Windows also checks the
    creation time against PID reuse);
  - one that finished, with a complete event file, is adopted, not relaunched;
  - any other is recorded as orphaned and relaunched as a new attempt.
- An unfinished or orphaned worker counts at its item cap in the budget.
- On a batch failure or stop, every running worker tree is killed.
- A torn last ledger line never swallows the next record.
- A folder an orphan still holds gives a clear failure, not a traceback.

## Stop rules (checked in the loop)

- **Item cap.** The cap is `--item-usd` (passed to Claude as `--max-budget-usd`), `--item-tokens` and
  `--item-timeout`, or a role's own `item_usd` / `item_tokens` / `item_timeout`. A worker whose streamed usage passes
  the token cap is killed. A worker that ends over its cap has its sheet held, not used.
- **Minimum budget.** `--batch-usd` is required. The conveyor prints the batch's minimum and refuses anything
  below it. The minimum is every producer and every repair round at the producer cap, plus every reviewer session
  (blind chunks and one reveal per arm) at that arm's cap.
- **Batch budget.** `--batch-usd` and `--batch-tokens` are checked before every launch, counting running workers at
  their cap. When the next launch would pass the budget, no more workers start. This is a resumable pause, not an
  outcome: exit 6, run state `budget_paused`, no Bentham line and no gate. A re-run with a larger budget continues.
- **A missed planted control** stops the batch before reveal and completion.
- **Zero submittable** orders, after the producers or after the mechanical checks, stops the batch.

Every finished batch, and every quality stop (zero submittable, a missed control), upserts the batch line `{batch, attempted, submitted, filed, controls_missed, usd}` in
`RUN/BATCHES.json` and runs the gate on it. Process stops are not reported to Bentham, because they say nothing
about the action's yield: a failed dispatch check, a reviewer that did not finish, broken blinding.

Exit codes:

| Code | Meaning |
|---|---|
| 0 | done, gate CONTINUE or PILOT |
| 1 | failed (a tool or configuration error) |
| 2 | stopped by a stop rule |
| 3 | paused for adjudication |
| 4 | done, but the Bentham gate says STOP |
| 5 | done, but the gate gave no verdict (refused or unranked) |
| 6 | paused at the batch budget (resumable) |

Batch settings are saved in `BATCH/CONFIG.json`. On a re-run, only budgets, concurrency, timeouts and the
publish/defer switches may change. The workers file is pinned by hash in the ledger at the first run and refused if
it changes, so earlier review records keep the right model family.

`BATCH/RUN.lock` is created with `O_EXCL`: a second process on the same batch refuses. A stale lock is cleared only
when its recorded process is dead.

## Augur, before anything else

`run` requires `--wave WAVE.json`. Before reserving anything, the conveyor imports `jobs/augur-launch/augur.py` and
runs its own `check(plan)`. It refuses unless:

- the verdict is PASS;
- one of the plan's actions has this batch's `--action` and at least this batch's order count.

Each check's receipt is recorded in the ledger (`augur:N`).

## A 1-batch probe

Read `jobs/bentham/output/PLAN.md` first, and write a `WAVE.json` that Augur passes (`augur.py check`), reviewed by
another model family.

With `workers.example.json` (producer cap $3, reviewer caps $12) and review chunks of 10, a 30-order batch can
commit up to:

| Workers | Caps | Total |
|---|---|---:|
| 30 producers | $3 each | $90 |
| 30 repairs (one round) | $3 each | $90 |
| 8 reviewer sessions: 3 blind chunks and 1 reveal per arm | $12 each | $96 |
| | | $276 |

The conveyor prints this minimum and refuses less, so use `--batch-usd 280`:

```text
python -I jobs/maudslay-conveyor/conveyor.py commands --workers jobs/maudslay-conveyor/workers.example.json
python -I jobs/maudslay-conveyor/conveyor.py run --run-dir research/excavator/claude-maudslay-2026-11-11 --batch p01 \
    --agent maudslay --action production.claim_ready.yes.fr --n 30 \
    --route research/excavator/claude-papinian-2026-11-10/tools/prompts/route_yes.txt \
    --workers jobs/maudslay-conveyor/workers.example.json \
    --wave research/excavator/claude-maudslay-2026-11-11/WAVE.json \
    --scratch-root C:/Users/danie/maudslay-scratch/claude-maudslay-2026-11-11/p01 \
    --item-timeout 5400 --batch-usd 280 --parallel 4 --publish
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

The tests run the real state machine with fake workers (`fakes/fake_worker.py` writes a canned sheet or review and
emits stream-json or codex events), so no model and no network are used. Two setups:

- **A fake kit.** `fakes/fake_kit.py` and `fakes/fake_tool.py` cover:
  - isolation and blinding: worker folders, control material, the event scan;
  - resume: after a kill, orphan kill, adoption, `next` never called twice, a kill after publish, a torn ledger line;
  - a failure killing live workers;
  - the prompt cap, command refusals, and Codex caps, prices and the mid-turn rollout kill;
  - the batch lock, durable scratch, the workers pin, the minimum budget and the budget pause;
  - the Augur gate, through its real `check()` on a stub plan;
  - stop rules and gate exits;
  - the control rule;
  - adjudication, repair and invalid sheets.
- **The committed claim kit.** `RealKitFixtureTests` runs the kit on its own integration corpus
  (`jobs/claim-kit/test_build.py` `BuildIntegrationTests`, with `test_dispatch.py`'s raw-source retention). It uses
  the real `next`, `prepare`, `dispatch-check`, Geddes views, `apply`, `batch-check` with the actual checker, and
  `complete --publish`. Only the tracker replay is stubbed (`fakes/kit_shim.py`), as the kit's own completion tests
  stub it.

The kit test needs a checkout that holds the kit's imports (`jobs/norton`, `jobs/clause-drafts`,
`jobs/status-history`, `jobs/later-events`, `research/stage19/code`, ...). It skips in a sparse checkout unless
`MAUDSLAY_KIT_HOME` points at one.

Not verified here: `claude` and `codex` are not installed on the build machine, so neither template has been run
against the real CLIs.
