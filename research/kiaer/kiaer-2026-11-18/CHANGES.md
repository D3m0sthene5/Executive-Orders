# Changes to the Relay and Kiaer code (2026-11-18)

The code that ran is `Relay-kiaer.zip` (sha256 in `SOURCE.txt`) plus the changes below. The exact diff is
`CHANGES.diff`. All were made by Claude (Fable 5.2) after Codex's first plan review rejected both plans
(`review/CODEX_REVIEW_1.json`). After them, Relay's 38 unit tests pass (33 before, 5 new) and
`python -m kiaer selftest` exits 0. No change was made before the smoke test, and none to `bridge/`.

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

## Not fixed: what the second review still rejects

Codex's second review (`review/CODEX_REVIEW_2.json`) rejected both plans again. The owner's rule for this probe is
to stop after a second rejection, so none of these is fixed:

1. `--token-cap 0` passes `verify()` and the engine treats a zero cap as no cap.
2. Saved run state (`STATE.json`, the job database) is not checked against the reviewed plan. `stage0` on a data
   folder holding an interrupted full run would resume that work under the full cap, and `full` on an unfinished
   stage 0 would resume it with three workers before reaching the gate.
3. A reservation race in `bridge/engine.py` with more than one worker: a finished step queues the job's next step
   before the worker releases its own reservation, so another worker can claim the next step and then lose its
   reservation. Spend could pass the cap by more than the plan discloses. It cannot happen with one worker.
4. A failed, timed-out or crashed turn is charged an estimate or nothing, and work continues and retries.
5. A step may deliver extra artifacts, and scoring reads the latest artifact of each name: a producer could
   supply its own `review.json`, or a repair turn could replace `result.json`.
6. The 2-dollar ceiling, the 40 tool turns, the 900-second timeout and Codex's medium effort are defaults that
   environment variables or flags can change; the reservation uses the largest turn only after three measured turns.
7. Provenance wording: only the 12 finding-aid inputs are hashed, not the held texts; slices are built at launch,
   not at draw time; results record cited sources, not every file and URL read.
