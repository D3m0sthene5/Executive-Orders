# Maudslay stateless, wave 1 stage 0: run sheet (owner's PC)

Wave 1 runs Bentham's `production.claim_ready.yes.fr` action through the Maudslay conveyor's stateless mode. Stage 0
is 30 orders on 1 lane, capped at $40 list. Augur passes it (`AUGUR_RECEIPT.json`, plan sha256 in `WAVE.json`), and the
owner is the reviewer (Kean D-20261125-maudslay-wave1). The stateless calls run here because `claude -p` is logged in
only on this PC.

## 0. Precondition: the gauge says GO

1. Read `research/stateless-calls-2026-11-24/GAUGE_RESULTS.json`.
2. Continue only if its verdict is `GO_STATELESS`.
3. On `KEEP_AGENT_ROUTE`, on an incomplete run, or if the file is missing, stop and report. Do not reserve anything.

This is an operator check, not code.

## 1. Checkout

Work in a worktree of `main` at or after the commit that added this file. Run
`python -I jobs/maudslay-conveyor/test_conveyor.py`. The symlink test now passes without Developer Mode; stop on any
other failure.

## 2. Print the commands, then run the batch

```text
python -I jobs/augur-launch/augur.py check research/excavator/claude-maudslay-2026-11-25/WAVE.json
python -I jobs/maudslay-conveyor/conveyor.py commands --workers jobs/maudslay-conveyor/workers.stateless.example.json
python -I jobs/maudslay-conveyor/conveyor.py run --run-dir research/excavator/claude-maudslay-2026-11-25 --batch p01 \
    --agent maudslay --action production.claim_ready.yes.fr --n 30 --stateless \
    --route research/excavator/claude-papinian-2026-11-10/tools/prompts/route_yes.txt \
    --workers jobs/maudslay-conveyor/workers.stateless.example.json \
    --wave research/excavator/claude-maudslay-2026-11-25/WAVE.json \
    --scratch-root C:/Users/danie/maudslay-scratch/claude-maudslay-2026-11-25/p01 --batch-usd 40 --parallel 4 --publish
python -I jobs/maudslay-conveyor/conveyor.py status research/excavator/claude-maudslay-2026-11-25/p01
```

- If the conveyor stops, rerun the same `run` command; it resumes from its ledger.
- If it refuses because of the cap or Augur, stop and report the refusal text.

## 3. After the batch

1. Run `python -I jobs/bentham/bentham.py gate --action production.claim_ready.yes.fr --batches <the batch file the
   conveyor names>`. Stop on STOP.
2. Commit everything under `research/excavator/claude-maudslay-2026-11-25/p01/` and the claims the conveyor
   published, on branch `claude/maudslay-stateless-wave1`, and push.
3. Report these from `MEASURES.json` and `ADJUDICATE.json`:
   - orders attempted, submitted and filed;
   - planted controls caught;
   - list-price dollars in total and per filed claim;
   - per-request prompt size and cache reads (stage-0 measurement, Kean F-20261113-conveyor-audit).

Stage 1 (up to 3 lanes, 300 orders) needs a Kean finding with these measures and a new plan. It does not follow from
this sheet.
