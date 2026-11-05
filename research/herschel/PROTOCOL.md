# Herschel deep sample: coordinator protocol (2026-11-05)

Herschel measures what ALL remaining work costs. `census.py` built the free census (`frame/CELLS.csv`: every open
order-step in the project, about 88,000 cells; `frame/ORDERS.csv`: features of all 14,972 orders) and drew a
probability sample (`frame/SAMPLE.csv`, weights = orders each sampled order stands for). Four coordinators (H1-H4,
`frame/ASSIGNMENTS.json`) each take a share of the deep sample. The goal is **measurement**: the cost in tokens and
wall time of every step each sampled order still needs, and how often each step succeeds or blocks. Filing claims is a
welcome by-product, never the objective, so never skip or swap an order because it is hard.

## What each coordinator does

1. Read only what you need: CLAUDE.md, AGENTS.md, `jobs/claim-kit/AGENT_PROTOCOL.md`, `BATCH.md`, `COMPLETION.md`, and the
   reusable tools and prompts in `research/excavator/claude-theophilus-2026-11-05/tools/` (and
   `research/excavator/claude-icecore-2026-11-05/tools/`). Their COORDINATOR_LOG.txt files show what went wrong today.
   Coordination was more than half of today's cost: be brief, reuse, and do not re-derive what those logs settle.
2. For each assigned order, read its open steps in `frame/ORDERS.csv` (`open_steps`) and its blockers in
   `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv`. Take it through every open step, in this order, as far as the
   project's rules allow:
   - **provisional_status** (orders with no status): the claim kit's undecided route (status unset, experimental
     overlay; `kit.py overlay-prepare` and the review sheet). The result is a reviewed status proposal. Never adopt a
     status: owner acceptance is separate.
   - **original_text**: locate and grade the official copy using what the jobs already hold (fr-originals,
     tischendorf-originals on branch `claude/tischendorf-tracker`, pinakes ProQuest scans, ofr/hathi compilations, lewis
     routes). Where none is held or reachable, record the block and the acquisition it needs; do not fetch at scale.
   - **clause_inventory, ending_or_current_basis, savings_residuals, counterevidence**: the ordinary claim-kit route
     (`prepare` → `dispatch-check` → producer → `apply` → `batch-check`).
   - **review**: two fresh blind Opus reviewers per claim or proposal, with planted controls (`plant.py`); keys only in
     your scratch directory. A claim files only if both uphold it and the checker passes.
   - **replace_original** (orders whose text rests on a transcription): if an official printing is held, record the
     swap and the quotation recheck as a step.
   A step that cannot proceed because a source is missing is an outcome, not a failure: record
   `blocked:<what acquisition would unblock it>` and move the order on to any later step that does not depend on it.
3. **Workers.** Each worker is one fresh session doing ONE step for a batch of at most 8 orders (same stratum where
   possible): Sonnet for production steps, Opus for review. Name workers `<H>-w<NN>`. One step per worker is what makes
   per-step cost measurable; never mix steps in one worker.
4. **Concurrency test.** Run at most your assigned `concurrency` workers at once (H1 4, H2 8, H3 8, H4 16), and try to
   keep that many busy. Record every usage-limit, rate-limit or overload message a worker or you hit.
5. **Budget.** Your cap is **$120 API-equivalent** for everything you and your workers spend, priced as
   `jobs/bentham/measure.py` prices tokens. After each batch, measure with
   `python3 -I jobs/bentham/sessions.py --since <your start ISO time> ...` and stop starting new work when the next batch
   would cross the cap. Orders not reached are recorded as `not_reached`, which is unmeasured, not failed.
6. **Gate.** After each review batch append `{batch, attempted, submitted, filed, controls_missed, usd}` to your
   `BATCHES.json` and run `jobs/bentham/gate.py` (`--prior-rate 0.3 --cost-per-attempt 2 --next-best 0.5 --window 2`).
   A planted-control miss stops your production. An economic STOP does not stop a survey: record it and continue.

## What each coordinator writes (all under `research/herschel/<H>/`)

- `TRACE.jsonl`: one line per worker: `{"worker","step","model","stratum","orders":[...],"started_utc","ended_utc",
  "concurrent_workers_at_start","limit_events","outcomes":{"EO:n":"done|blocked:<acquisition>|failed:<reason>|
  upheld|rejected:<defect>|not_reached"}}`.
- `ORDER_OUTCOMES.csv`: one row per assigned order and step: `instrument_id, stratum, step, outcome, worker`.
- `BATCHES.json`, gate outputs, `telemetry/` (sessions.py output, with a phase map that labels each worker by its
  step), and `COORDINATOR_LOG.txt` (decisions, problems, timings).
- Claims that file go to `research/readiness/claims/claude-2026-11-05-herschel-<H>-<batch>.jsonl`; status proposals
  stay in your folder as proposals.

## Rules that are not optional

- Never change a provisional status, the codebook, the census or the certified count (0).
- Four coordinators share this checkout and branch (`claude/herschel-survey`). Commit only your own paths
  (`git add <paths>`, never `-A`), `git pull --rebase origin claude/herschel-survey` before each
  `git push origin claude/herschel-survey`, and never delete another process's git lock. Never push to main.
- Disk is limited (about 12 GB free). Keep prepared packets in `research/herschel/<H>/packets/` (already excluded from
  git) and delete them at the end, after committing the small evidence files.
- Do not touch jobs code, other coordinators' folders, or `CLAIM_KIT_LOCK.json` beyond reservations the kit makes.
