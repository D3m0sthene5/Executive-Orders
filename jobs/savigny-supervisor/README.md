# Savigny supervisor: headless Codex lanes with measured stop rules

Runs a Codex coordinator (SAVIGNY) and production lanes as headless `codex exec` turns on the owner's PC. It stops
them on measured waste. This is the supervisor of the 2026-11-09/10 overnight wave, rebuilt after that wave spent
about half the owner's weekly Codex allowance for 12 filed claims (Kean F-20261110-mommsen-unranked-pools).

```bash
python -I jobs/savigny-supervisor/supervisor.py --root C:/Users/danie/eo-wt/_savigny
```

## Where last night's tokens went (measured from the Codex rollout files)

| Spender | Input tokens | Share | What it was doing |
|---|---:|---:|---|
| Very High coordinators (lanes and Savigny) | about 490M | 54% | About 3,000 tool calls, each re-sending a context of about 190k tokens (peak 447k) |
| Auto-review sessions | about 227M | 25% | 150 reviews of sandbox escalations, each re-reading a large context |
| Medium-effort workers (the dossier work) | about 190M | 21% | Producers and reviewers |
| **Total** | **910M** | | 881M (97%) cache re-reads; 3.87M output tokens |

Papinian (Claude) filed 63 claims in the same window for $297 at API list prices. Its coordinator took 17% of that,
because scripts (`prep.sh`, `render_producer.py`, `review_prep.py`, `finish_pair.py`) did the clerical work.

## The stop rules

All of them act on measurements: `jobs/carnot-coordinator/meter.py` reads the Codex rollout files and the lanes'
claim files. None depends on what an agent reports about itself.

| Rule | Default | Why this value |
|---|---|---|
| Every turn starts a fresh session (never `exec resume`) | always | A resumed session re-sends its whole history on every call. Last night lane contexts reached 400k+. |
| `context_kill_tokens`: kill a turn whose latest call carries more context | 120,000 | Last night's average call carried about 190k. A lane at most 120k, restarted from its handoff packet, pays well under half that per call. |
| `spend_per_claim_units`: pause a lane that spends this much since its last verified claim | 3,000,000 | Measured: lane I 5.9M units per filed claim, lane II 9.1M, lane III 26.8M; lanes IV and V spent 16M each for nothing. |
| `no_claim_minutes`: pause a lane after this many running minutes without a new verified claim | 40 | Papinian filed a batch about every 25 minutes. 40 minutes is one batch plus slack, not 2 hours. |
| `reviews_per_hour`: pause a lane that causes this many auto-reviews in an hour | 6 | Each review re-reads a large context. A burst means the sandbox lacks a permission the work needs: fix the sandbox, do not pay per command. |
| `coordinator_units_per_hour`: the coordinator's own spend per hour | 1,000,000 | The coordinator runs only when there is news (a lane turn ended, a pause), never on a timer. |
| `chain_budget_units`: total for the run; at 100%, everything is killed and STOP is written | set by the owner, required | No run starts open-ended. |

The limits live in the run's plan, `WAVE.json` (`"limits"`). The supervisor runs Augur's launch check on that plan at
startup (`jobs/augur-launch/augur.py`), and refuses to start if Augur refuses, if any limit is missing, or if
`lanes.json` names more lanes than the plan approved.
Usage units = 0.1 x cached input + 1 x uncached input + 4 x output (meter.py), an explicit approximation of how a
plan meters usage. For scale, last night's run measured about 148M units.

```json
{"chain_budget_units": 40000000, "spend_per_claim_units": 3000000, "no_claim_minutes": 40,
 "context_kill_tokens": 120000, "reviews_per_hour": 6, "coordinator_units_per_hour": 1000000}
```

## What the supervisor does not prevent

- **Work outside Bentham's plan:** the claim kit refuses it (`jobs/claim-kit/admission.py`).
- **Low-yield ranked actions:** Bentham's gate handles these, and the spend rule above caps them.
- **Clerical work done by an expensive model:** lanes should drive scripts, as Papinian did. The supervisor caps
  what that costs but cannot make a lane efficient.
- **A lane padding its claim files to reset the spend rule:** the meter counts distinct orders in the lane's claim
  files without checking them. Padded claims cannot merge, because CI runs the claim checker, but they can buy a
  lane one more allowance. Compare the meter's count with merged claims at the end of each run.

## Runtime folder (`--root`)

`WAVE.json` (the plan Augur checks), `lanes.json` (`{"lanes": {"mommsen-1": "C:/Users/danie/eo-wt/mommsen-1", ...}}`), `prompts/`
(`savigny.md`, `savigny-turn.md`, `lane.md`, `lane-turn.md`), `status/`, `inbox/`, `directives/`, `logs/`,
`state.json`. To stop everything, create an empty `STOP`. `PAUSE-<agent>` pauses one agent. Keep owner grants in
the runtime folder, never in this repository.

Tests: `test_supervisor.py` runs the real scheduling loop with a fake Codex, an injected meter and a controllable
clock. `jobs/carnot-coordinator/test_meter.py` tests the meter on synthetic rollout files. Both run in road CI.
