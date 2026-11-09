# Tsiolkovsky: the project's trajectory

Named for Konstantin Tsiolkovsky, whose rocket equation (1903) reduced a rocket's progress to one number, its
delta-v. The Apollo rocket dashboard placed the project on Apollo 11's timeline by its fraction of weighted work.
This job gives that position a history, a velocity and an acceleration, and credits each change to whatever
landed just before it.

## The metric: verified work held, in work-hours

For every tracker generation (every version of `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv` on main's
first-parent history), sum over every census order and every step the tracker applies to it:

> step weight (the rocket's measured agent-minutes per step, `MISSION_WEIGHTS.csv`) × credit for the step's state.

Credits:
- **Done steps** earn 1.
- **Open steps** earn partial credit from the tracker's own blocker codes:
  - an official original found but not page-checked: 0.5;
  - an archival replica held: 0.4;
  - an official URL known but not downloaded: 0.3;
  - only a compiled transcription: 0.2;
  - a claim filed but not yet checked: 0.8;
  - a claim check failed, or an open source audit: 0.5;
  - an incomplete claim: 0.4.
- **Provisional text steps** earn 0.6.
- **Census admission** is a step, weighted at 15 minutes, so census growth adds work.
- **Human certification** is never credited.

A low and a high variant (partial credits halved, or raised by half and capped at 0.95) give a sensitivity band.

**Derived figures:**
- **Share:** W over the full weight of every step of every order in the largest census seen.
- **Mission clock:** the share times 109:24:15, the time of Armstrong's first step, as on the rocket dashboard.
- **Velocity and acceleration:** taken on the end-of-day series.

It beats the ready count because:
- the ready count moves only when all six steps close with matching checker receipts;
- acquisition, leads and claims register in W as they land;
- a stricter rule shows as a small loss of credited work, not as hundreds of "lost" dossiers.

## Order and correctness

- **Order:** readings follow main's first-parent history, which is the order things landed on main.
- **Landing time:** a commit's own timestamp can predate the merge that landed it, so the landing time is the
  running maximum.
- **Verification:** each reading's ready count and census size are taken from the table itself. On 2026-11-06
  they matched that generation's tracker `SUMMARY.json` at all 40 generations.

## What pushed what

Each change between two readings is split by step and credited to the events on main between the two
generation commits:
- **Pull-request merges and direct commits** are named by the campaign name in the branch or title (the `KNOWN`
  list), else by the branch label.
- **Runner result commits** are credited per producing job.
- **Instruments are never credited:** the tracker, digest, cards, Kean, Bentham, Domesday, Dagron and this job.

Each change is credited only to events that touched that step's kind of input:
- census → `research/stage15/CENSUS/`;
- provisional status → status ledger and adoption rows;
- claim steps → `research/readiness/claims/`;
- text and sources → job outputs and source folders;
- the rules (tracker, checker and claim-kit code, owner rulings) → any step.

**Channel weights (Gutenberg, 2026-11-09; the default; `TSIOLKOVSKY_CREDIT=even` restores the earlier rule):**
- A step's change goes only to events that changed that step's own tracker inputs (`STEP_INPUTS`: producer
  FRAGMENTS and texts and Lachmann's output for the text steps; claims, factual records and Lachmann confirmations
  for the claim steps), split by the lines each changed there (`git diff --numstat` against the first parent).
- A runner result passes its share to the merged campaign behind it: one that changed the job's code in the same
  interval (`channel_via_code`), else one that changed the job's declared inputs there (`channel_via_inputs`).
- When a rule (tracker, checker, claim-kit code, owner ruling) also changed in the interval, the row's rule ends in
  `+rules_changed`: lines of code and lines of evidence are not comparable, so the split is disclosed, not guessed.
- Validated on the 2026-11-07 backlog generation (6d4b5f6357 -> f6e5180880): Photius lane GPO gets 176.6 of the 207.2
  original-text hours (the even split gave the Photius lanes about 13), and the 44.7-hour claim-step loss from the
  stale Lachmann confirmations goes to the same lane through Lachmann's inputs instead of to unrelated merges.
  Lines changed are a proxy for evidence delivered, not proof of cause.

**Fallbacks:**
- No eligible event: the rules events, then everything that landed together.
- Only a re-check or a bare re-run: the most recent qualifying events, recorded as `deferred`.
- Otherwise the claim checker, as verification.

The first reading is the launch pad: work held before the repository existed. This is attribution by landing
order, not proof of cause; `CREDITS.csv` records the rule used for every row.

## Outputs (`output/`)

| File | What |
|---|---|
| `GENERATION_POINTS.csv` | One row per reading: landing time, commit, W with its band, share, clock and phase, ready count, census size, claims, statuses |
| `TRAJECTORY.csv` | End-of-day series: W by step, ready count, velocity, 3-day velocity, acceleration, clock, phase |
| `CREDITS.csv` | Each credited change: reading, credited to, agent, step, hours, rule |
| `EVENTS.csv` | Every merge, commit and producing job run between readings, with its input channels |
| `CAMPAIGNS.csv` | Net, gained and lost work-hours by campaign, machine and the launch pad, with hours by step |
| `INTERVALS.jsonl` | Per interval: change by step, credit, events |
| `MISSION.csv` | Apollo 11 milestones on the work-hours scale |
| `GENERATIONS.jsonl`, `SUMMARY.json` | Per-generation measurements (the carry-forward cache) and the headline |

The **Trajectory tab** of the project dashboard (https://claude.ai/artifact/531KGTebdrgdeUitKhp8du#trajectory) draws these files. The standalone Tsiolkovsky Trajectory page (https://claude.ai/artifact/BZJxATqRtwrtBbuBy2UZpc) was retired on 2026-11-08 at the owner's request: there is one dashboard, and Tsiolkovsky is its tab. Do not refresh the standalone page.
Its data files are attached copies, so refreshing it means uploading the new CSVs.

It runs daily and after the tracker, in zero model tokens. Readings already measured are carried forward from
`JOB_PRIOR_OUTPUT_DIR`, so a daily run reads only new tracker versions.
