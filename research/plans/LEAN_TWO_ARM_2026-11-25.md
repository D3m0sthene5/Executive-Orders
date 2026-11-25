# Lean two-arm production trial, 2026-11-25

This plan tests whether a leaner production workflow files claims at a lower list-price cost per filed claim without losing quality. It is registered with Junto as two frozen contracts (`lean_two_arm_2026-11-25_coordination` and `lean_two_arm_2026-11-25_sequential`), so only a measured result can verify a saving.

## Arms

Both arms run Bentham action `production.claim_ready.yes.fr` on 30 orders each, on one lane at stage 0, through the Maudslay conveyor's agent route on the owner's PC (no `--stateless`). The two lists are disjoint and drawn by seed from one pool.

- **Arm 0 (current).** Two blind Opus reviewers (arms A and B) review every submitted claim in parallel, Larrey runs at its current default level, and coordination is the current one.
- **Arm 1 (lean).** Four changes together:
  1. Sequential review with early exit: arm B reviews a claim only after arm A upholds it. Planted controls always go to both arms. A claim files only if both uphold, as now.
  2. The mechanical pre-review gate: the completion checker runs before any reviewer session, and a claim that fails it is not reviewed.
  3. `LARREY_LEVEL=strict`, only if branch `claude/larrey-2026-11-25` is merged and defines that level when the trial starts; otherwise arm 1 runs at the current level and the plan records that.
  4. Lean coordination: the conveyor supervises, workers write one-line reports, and the coordinator reads only failures and `MEASURES.json`.

Arm 1 bundles the two savers `lean_coordination` and `sequential_review_early_exit`. The trial cannot separate their effects. Junto allows one credited after-arm session per saving, so a verified result is recorded against one contract and the other stays unverified.

## Draw

1. Export the pool: the ids of decided-YES claim-ready orders that pass Larrey at the current level. (The export command is the one input this plan does not fix, because it depends on kit state on the PC; `kit.py next` reserves orders and so must not be used to list them.)
2. Run `python3 -I jobs/junto/lean_draw.py POOL.txt junto-lean-2026-11-25 research/excavator/claude-junto-lean-2026-11-25/draw`. It writes `arm0_ids.txt`, `arm1_ids.txt` and `DRAW.json` (seed, pool hash, list hashes) and asserts the lists are disjoint. Commit them before either arm runs.
3. The denominator for each arm stays at 30 drawn orders. An order that strict Larrey or the pre-review gate removes counts as attempted and not filed.

The frozen contracts pin the draw rule (the seed string and `lean_draw.py`), because the order lists do not exist yet. Before measuring, register superseding contracts that pin each drawn id and its hash (`register-test` with `supersedes`), since `add-test` checks the executed sample against the pins.

## Measures

For each arm, from `MEASURES.json` and `ADJUDICATE.json`: orders attempted, submitted and filed; filed rate per attempted order; planted controls planted and caught; list-price dollars in total and per filed claim (Necker prices, `jobs/necker-costs/PRICES.json`); the coordinator's share of dollars; requests and per-request prompt size with cache reads and writes (Kean F-20261113-conveyor-audit); and wall time from first reserve to publish.

## Stop rule

Any missed planted control in either arm, or an arm 1 filed rate per attempted order more than 10 percentage points below arm 0, keeps arm 0 and ends the trial. Otherwise Junto's own rule applies: arm 1 counts as saving only if its cost per filed claim is at most 0.9 times arm 0's. Thirty orders per arm is a small sample (Maudslay measured about 7 filed of 30), so a pass at stage 0 supports a stage 1 plan and nothing wider.

## Commands on the owner's PC

Run arm 0 first and arm 1 second on the same day. Substitute the review-mode names if the conveyor change names them differently; `--review-mode` comes from the sequential-review branch `claude/seqreview-2026-11-25`, which is still being built, so its values here (`parallel`, `sequential`) are assumed until that branch merges. The strict Larrey level is also pending.

```text
python -I jobs/maudslay-conveyor/conveyor.py commands --workers jobs/maudslay-conveyor/workers.example.json

python -I jobs/augur-launch/augur.py check research/excavator/claude-junto-lean-2026-11-25/arm0/WAVE.json
python -I jobs/maudslay-conveyor/conveyor.py run --run-dir research/excavator/claude-junto-lean-2026-11-25/arm0 --batch p01 \
    --agent maudslay --action production.claim_ready.yes.fr --n 30 \
    --ids research/excavator/claude-junto-lean-2026-11-25/draw/arm0_ids.txt \
    --route research/excavator/claude-papinian-2026-11-10/tools/prompts/route_yes.txt \
    --workers jobs/maudslay-conveyor/workers.example.json \
    --wave research/excavator/claude-junto-lean-2026-11-25/arm0/WAVE.json \
    --scratch-root C:/Users/danie/maudslay-scratch/claude-junto-lean-2026-11-25/arm0/p01 \
    --item-timeout 5400 --batch-usd 45 --parallel 4 --review-mode parallel --publish
python -I jobs/maudslay-conveyor/conveyor.py status research/excavator/claude-junto-lean-2026-11-25/arm0/p01

# arm 1 (PowerShell; set the variable only if the Larrey branch is merged)
$env:LARREY_LEVEL = "strict"
python -I jobs/augur-launch/augur.py check research/excavator/claude-junto-lean-2026-11-25/arm1/WAVE.json
python -I jobs/maudslay-conveyor/conveyor.py run --run-dir research/excavator/claude-junto-lean-2026-11-25/arm1 --batch p01 \
    --agent maudslay --action production.claim_ready.yes.fr --n 30 \
    --ids research/excavator/claude-junto-lean-2026-11-25/draw/arm1_ids.txt \
    --route research/excavator/claude-papinian-2026-11-10/tools/prompts/route_yes.txt \
    --workers jobs/maudslay-conveyor/workers.example.json \
    --wave research/excavator/claude-junto-lean-2026-11-25/arm1/WAVE.json \
    --scratch-root C:/Users/danie/maudslay-scratch/claude-junto-lean-2026-11-25/arm1/p01 \
    --item-timeout 5400 --batch-usd 45 --parallel 4 --review-mode sequential --publish
python -I jobs/maudslay-conveyor/conveyor.py status research/excavator/claude-junto-lean-2026-11-25/arm1/p01
```

After each arm run `python -I jobs/bentham/bentham.py gate --action production.claim_ready.yes.fr --batches <batch file the conveyor names>` and stop on STOP. Commit each arm's `p01/` folder. Then record the result with `junto.py add-test --contract lean_two_arm_2026-11-25_coordination --registration-commit COMMIT --measurement-started-at TIME --sample-manifest DRAW.json ...`, with the arm sessions, quality counts and `--complete-costs`.

## WAVE.json for Augur

Drafts are at `research/excavator/claude-junto-lean-2026-11-25/arm0/WAVE.json` and `arm1/WAVE.json`. Each is stage 0 (one lane, 30 orders, 6M units) because the agent route through the conveyor, and arm 1's review mode, have no measured configuration. `review` is empty: after the plan is final, run `augur.py sha` on each file, have a reviewer from another model family (or the owner) sign that hash into `review.plan_sha256` with verdict `approve`, and do not edit the file afterward. These drafts were not run through `augur.py check` (the tool is outside the sparse checkout used to write them).

## Expected cost

Papinian (2026-11-10) cost $296.95 at list price for 467 attempted orders, which is $0.636 per attempted order. Its log splits that into $160.20 for 38 reviewer sessions (19 pairs, $8.43 per pair, individual sessions $1.74 to $6.89) and $136.75 for producers and coordination. That gives $0.293 per attempted order outside review and, on 116 submitted plus 18 planted claims, about $1.20 per claim reviewed by a pair.

- **Arm 0.** 30 orders x $0.293 = $8.8. About 7.5 submitted (30 x 116/467) plus 1 to 2 planted controls is about 9.5 claims, x $1.20 = $11.4. Total about $20, which matches 30 x $0.64 = $19.
- **Arm 1.** Same $8.8 outside review. Arm A reviews all 9.5 claims at half the pair cost, $5.7. Arm B sees about 5 (the claims arm A upholds, roughly 55% from 63 filed of 116 submitted, plus controls), $3.2. Total about $18, so the review saving at this sample size is small and coordination savings are unmeasured here.
- **Both arms:** about $38 at Papinian's rates. A reviewer pair for a 10-claim chunk can cost $9 to $14 (Papinian y01 and y02 sets), and repairs add up to $3 per order; the worst case per arm is about $45. The owner's $60-90 band for both arms therefore holds with margin; `--batch-usd 45` per arm caps the total at $90.

The plan's expected figures are estimates from a different workflow and period, not measurements, and enter no score.
