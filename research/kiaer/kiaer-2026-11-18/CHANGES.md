# Changes to the Relay and Kiaer code (2026-11-18)

The code that ran is `Relay-kiaer.zip` (sha256 in `SOURCE.txt`) plus the changes below. The exact diff against the
zip is `CHANGES.diff`. All were made by Claude (Fable 5.2), in four rounds, one after each Codex plan review
(`review/CODEX_REVIEW_1.json` to `_4.json`); the owner directed the third and fourth reviews. Relay's unit tests: 33
in the zip, 38 after round 1, 55 after round 2, 58 after round 3, 62 after round 4; all pass, and
`python -m kiaer selftest` exits 0. The first smoke test ran on the zip's code, the second on the round-2 code
(`SMOKE.json`). Round 3 was reviewed by the fourth review; round 4 has not been reviewed, and nothing has run on
rounds 3 and 4 but the tests and the selftest.

## Round 1 (after the first review)

| File | Change | Why |
| --- | --- | --- |
| `kiaer/run.py` | `stage0()` no longer raises the engine ceiling. A new `Probe` keeps the 6,000,000-unit ceiling until `full()` has passed its gate and recorded `full_started`. | Work left over from stage 0 could run past the stage-0 budget once stage 0 ended. |
| `kiaer/run.py` | `full()` refuses to start unless stage 0 finished at least 10 orders, no stage-0 turn was charged an estimate, and the projection fits under the cap after shrinking cells. `PROJECTION.json` gains `orders_measured`. | The owner's condition for the full run was checked by nobody in code. |
| `kiaer/run.py` | `Probe` refuses a data directory inside the repository. | Only the command line checked this. |
| `kiaer/run.py` | An audit agreement needs a non-empty ledger status and a non-empty conclusion. | Two missing values compared equal and counted as agreement (early-stopping score only; the report already required a ledger status). |
| `kiaer/run.py` | Blind producers are also denied `research/kiaer/**`. CAP-stopped plant reviews are released with the orders when the full run starts. | The probe's own stage-0 report would sit inside the repository during the full run. |
| `kiaer/prompts.py` | `reviewer(item, blind=False)`: for audit orders the reviewer is told not to open the ledger, claims, drafts or handoff notes. | The Codex CLI cannot deny reads; this is an instruction, not an enforced rule. |
| `kiaer/wave.py` | New `verify()`: `stage0` and `full` refuse to start unless the stage's plan carries an approving review bound to its hash, `DRAW.json` is the reviewed frame, no input changed since the draw, and workers, orders and unit cap are within the plan. New `plan_sha()` (same computation as `augur.py`). | Nothing tied a run to the plan that was reviewed. |
| `kiaer/wave.py` | Plan wording: `limits_enforced_by`, `writes`, a precise `stages.gate`, pre-mortem guards that describe what the code does, the smoke-test record (`SMOKE.json`), and the revising author. | The first plans stated guards more strongly than the code enforced them. |
| `kiaer/__main__.py` | Calls `wave.verify()` before `stage0` and `full`; `--run-id` must be a plain name. | As above; a run id could have pointed outside `research/kiaer/`. |
| `tests/test_kiaer_gate.py` | New: 5 tests of `wave.verify()` and `plan_sha()`. | Covers the new launch check. |

Two helper scripts sit beside the Relay folder and are not part of it: `run-kiaer.ps1` (clears the desktop
session's `CLAUDE*`/`ANTHROPIC*` variables, sets `RELAY_CLAUDE_BIN`, `RELAY_CODEX_BIN`, `RELAY_CODEX_EFFORT=medium`,
`RELAY_CLAUDE_MAX_BUDGET_USD=2`, `RELAY_CLAUDE_MAX_TOOL_TURNS=40`, and logs) and `codex-review.ps1` (the read-only
plan review call).

## Round 2 (after the second review): its seven grounds, and what was done

| # | Ground | Change | Where |
| --- | --- | --- | --- |
| 1 | `--token-cap 0` passed the check and the engine read zero as no cap. | A cap must be a positive number: the command line, `wave.verify`, `Probe` and the engine (constructor and `set_cap`) each refuse zero or less. | `kiaer/__main__.py`, `kiaer/wave.py`, `kiaer/run.py`, `bridge/engine.py` |
| 2 | Saved run state was not checked against the reviewed plan; a wrong command could resume work under the wrong ceiling or with three workers before the gate. | `Probe` no longer resumes anything when it opens. `stage0` and `full` first run `_check_state`: the state must carry the draw's frame hash and the hash of the plan it started under; every order on file must be within the stage's drawn allowance; every database job must be named in the state. `stage0` refuses a full run and more than one worker. `full` refuses an unfinished stage 0 and passes its gate before resuming anything. State is saved after each job is created. | `kiaer/run.py`, `kiaer/__main__.py` |
| 3 | Reservation race with more than one worker. | A job is not claimed while a worker still holds its previous turn, and a worker releases only its own reservation. | `bridge/engine.py` |
| 4 | A failed, timed-out or crashed turn was charged an estimate or nothing while work continued. | Each attempt is written to the database before its provider starts; one found open after a crash is charged and flagged. A turn without measured usage stops the run: no further turn starts and nothing is retried until the operator records a figure for it, never below the charge (`python -m kiaer reconcile`). | `bridge/engine.py`, `kiaer/run.py`, `kiaer/__main__.py` |
| 5 | A step could deliver extra artifacts and scoring read the latest of each name. | A step records only the one artifact it owns (others are discarded and logged; two copies fail the step). Scoring reads each artifact only from its owning step. | `bridge/engine.py`, `kiaer/common.py`, `kiaer/run.py`, `kiaer/report.py` |
| 6 | The 2-dollar ceiling, 40 tool turns, 900-second timeout and medium effort were overridable defaults; the reservation used the largest turn only after three turns. | The limits travel in each step's options, ahead of the environment variables. A timeout above 900 seconds is refused. The reservation is the largest measured turn (at least 150,000 units) from the first turn, failed turns included. | `bridge/claude.py`, `bridge/codex.py`, `bridge/engine.py`, `kiaer/run.py` |
| 7 | Provenance wording claimed more than the code does. | The plans now say: only the 12 finding-aid inputs are hashed; slices are built at launch from the checkout; results record cited sources only; reviewer feedback can carry the ledger status into the repair turn, whose result enters no audit rate. | `kiaer/wave.py` |

New tests: `tests/test_kiaer_round3.py` (17 tests, one or more per ground). The diff of this round alone is
`review/CHANGES_round3.diff`.

Side effect to know: after any interruption that cuts a turn off (Ctrl+C, a kill, a timeout), rerunning the same
command now prints `STOPPED` until that turn is reconciled. This is deliberate (ground 4).

## Round 3 (after the third review): its three grounds, and what was done

Made after the third rejection so the kit was ready for whichever decision the owner took. The fourth review found the first and third met and the second incomplete (round 4).

| Ground | Change | Where |
| --- | --- | --- |
| `reconcile --units nan` passed validation, stored an empty charge and marked the turn reconciled, so admission resumed with the turn uncounted. | A reconciliation figure must be finite, positive and not below the charge already made; a refusal leaves the charge and the flag as they were. The command prints `REFUSED` instead of a traceback. | `bridge/engine.py`, `kiaer/__main__.py` |
| Empty or partial usage counted as measured: a Codex event with `usage: {}` was charged zero, and a turn reporting only some token counts was charged for those alone. | A turn is measured only if all four token counts came back as finite, non-negative numbers that are not all zero; otherwise it is charged the estimate, flagged and stops the run. A Codex usage event must carry input, cached input and output counts, with cached input no larger than input. | `bridge/engine.py`, `bridge/codex.py` |
| Four plan statements were stronger than the code. | The plans now say: a wave targets about 12% planted reviews and can yield none; a failed job is retried at most once, and not after a ceiling; an unmeasured turn is charged the estimate as it stands when recorded, which can exceed its reservation; and the lesson answer lists the guards that have tests and the ones that do not. | `kiaer/wave.py` |

New tests: three more in `tests/test_kiaer_round3.py` (non-finite figures in the engine and through the command,
Codex empty and incomplete usage events, partial usage stopping admission).

Risks the third review noted without making them grounds: a blind producer can still see public project pages in
web-search result snippets (only fetches of the project's sites are denied); creating a job and saving the state
file are not one atomic step, so a crash between them leaves a job the next start refuses; the projection is a
forecast.

## Round 4 (after the fourth review): its one ground, and what was done

Made after the fourth rejection. Not reviewed.

| Ground | Change | Where |
| --- | --- | --- |
| The Codex adapter checked a usage event only if its usage field was an object. A completion event with usage missing, null, a list or a string, or an older-format event with an empty usage object behind a fallback, was skipped, so earlier valid counts stood and the turn counted as measured. | Every accounting event in a turn's stream (each `turn.completed`, and any `token_count` that carries a usage field) must have a complete, valid usage object. One that does not makes the whole turn unmeasured, even after valid events: it is charged the estimate, flagged, and stops the run. An event that carries no accounting field at all is still ignored. | `bridge/codex.py` |

New tests: four more in `tests/test_kiaer_round3.py`, including a mixed stream driven through the adapter and the
engine (estimate charged, next turn blocked until reconciled) and a clean stream that stays measured. The four real
Codex event streams on file (the plan reviews) each hold one `turn.completed` with full usage and still read as
measured. Plans: one more lesson answer and the wording of `unmeasured_turns`.

## Owner round (after the owner took the reviewer's role)

On 2026-11-18 the owner took the reviewer's role for both plans (Kean D-20261118-kiaer-owner-directed-wave),
directed that no further Codex review be run, and that any later defect be fixed with a test and logged here. The
changes below were not reviewed by a second model. Tests after this round are counted at the end of this section.

### Smoke-test cost check (no tokens spent)

Units by step and token class, from the two smoke runs' turn records (EO 9703, the same order twice):

| Run | Step | Cache read (x0.1) | Uncached input (x1) | Cache write (x1) | Output (x4) | Units |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | producer (Claude) | 65,546 | 8 | 29,255 | 7,065 | 64,078 |
| 1 | review (Codex) | 135,424 | 44,587 | 0 | 1,368 | 63,601 |
| 1 | repair (Claude) | 17,378 | 4 | 11,487 | 6,701 | 40,033 |
| 2 | producer (Claude) | 115,679 | 12 | 33,639 | 8,711 | 80,063 |
| 2 | review (Codex) | 93,696 | 42,392 | 0 | 1,596 | 58,146 |
| 2 | repair (Claude) | 17,928 | 4 | 13,354 | 8,393 | 48,723 |

What the units are made of: for Claude turns, output (44 to 69% of the turn) and cache writes (27 to 46%); for
Codex reviews, uncached input (70 to 73%).

Findings:

- **Repair ran both times, for the review's substance.** The reviewer marked three propositions unverifiable
  (it could not retrieve the eCFR versioner URL the producer cited) and, in run 2, listed evidence the producer had
  missed. The repair turns narrowed claims, corrected a stop code the reviewer marked wrong and added three
  propositions from the missed evidence. Not a format or parse problem; left as it is. Note for reading the
  results: Codex could not reach the dated eCFR API in either run, so orders that cite eCFR will usually draw an
  "unverifiable" and a repair turn.
- **Nothing defeats caching between turns.** Each prompt puts its fixed text (rules, task, output shape) first and
  the order's slice last; within a turn 65,000 to 135,000 tokens were served from cache. The cache writes are the
  files and pages a turn reads, written once.
- **No re-fetching of slice material was found.** The producer opened the held Federal Register texts the slice
  names and fetched two public pages the slice does not hold (the eCFR part and the National Archives disposition
  table).
- **Nothing was removed.** No cost in these two runs was plainly waste.
- **One accounting fact, disclosed and not changed:** units count each CLI's main model. Claude Code also runs a
  small side model for web-fetch summaries: 75,265 raw tokens in run 1 and 89,307 in run 2, which is 1.0% and 1.6%
  of Claude's dollar cost. Counting those tokens at the main model's weights would have added 107,000 to 126,000
  units per order and changed the meaning of every figure the cap and the stop conditions were set against, so the
  meter is unchanged. The side-model tokens and Claude's reported dollars are now totalled in the report, and the
  plans say so (`limits.unit_definition`).

### Changes

| Change | Why | Where |
| --- | --- | --- |
| The Claude adapter keeps, per turn, the tool calls the CLI refused (`permission_denials`). The report lists them for blind-audit orders, with any denied path a blind result cites. | The owner's stop condition "a blind-audit producer read a denied ledger file" had nothing to be checked against. A refused call is a blocked attempt, not a read. | `bridge/claude.py`, `kiaer/report.py` |
| When no usage can be read from a Codex turn, the adapter keeps the stream's event types and accounting lines in the turn record. | The owner's rule for an estimated turn is to inspect its raw event stream; it was not kept. | `bridge/codex.py` |
| The report totals Claude's side-model raw tokens and reported dollars, counts planted-review turns in raw tokens and estimated turns, and counts turns by outcome. | The side model is outside the units; planted reviews were missing from two totals. | `kiaer/report.py` |
| Plan wording: the owner as reviewer of record, the owner's four stop conditions, the unit definition. | The plans the owner signs must say what will happen. | `kiaer/wave.py` |

Helper scripts beside the Relay folder (not part of it): `bind_owner_review.py` (writes the owner's review into
both plans, bound to `augur.py sha`, and refuses a plan outside the owner's bounds), `record_owner_launch.py`,
`smoke_costs.py`, `progress.py`, `log_owner_round.py`.

New tests: `tests/test_kiaer_owner_round.py`.

### What ran on this code

Stage 0 (29 orders, 1 worker) and the full run (51 more orders in two waves, 3 workers) ran on 2026-11-18 on the
code above, with no code change between or after them: 66 unit tests pass and the selftest exits 0. All
221 turns reported complete usage; none was charged an estimate, none failed and
no order was retried. The full run's gate passed as written (it shrank the cells to fit), so the gate was not
changed. The run stopped at the shrunk cell caps with 1,917,991 of the 10,000,000 units
unspent: the caps were sized at the 80th-percentile cost and are not grown back when orders come in cheaper.
That was left as it is.

Scripts that are not part of the kit and sit beside it: `owner_tables.py` (writes `OWNER_TABLES.json` from the
report's own files) and `record_final.py` (this record).
