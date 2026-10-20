# Llull: checks a research plan before money is spent on it

Named for Ramon Llull's *Ars Magna* (c. 1305), paper wheels that cross every term with every
other term and list the questions to ask. Design: `research/plans/LLULL_DESIGN.md`.
Standard library only; always run with `python3 -I`.

**Hard rule (as in Junto).** Llull earns trust only from measured outcomes. A base rate must be a
measured number with a source path, or `forecast` refuses it. Llull never changes the
evidence/legal codebook, claim statuses, tiers, or the certified count (0). AI statuses stay
hypotheses. It reads committed outputs and writes only under `jobs/llull/`.

```
python3 -I jobs/llull/llull.py census    --pool Y2 [--requires a,b,c] [--record] | --list
python3 -I jobs/llull/llull.py forecast  --plan-id ID --planner agent:model --quantity Q \
          (--p10 --p50 --p90 | --event TEXT --prob P) --reference-class KEY [--pool P | --census-id D-..] \
          [--unlock-p90 N] [--run-dir DIR] [--accept-flag REASON] [--deviation TEXT]
python3 -I jobs/llull/llull.py outcome   --forecast L-.. --measured N --source REPO/PATH
python3 -I jobs/llull/llull.py score                       # output/CALIBRATION.json
python3 -I jobs/llull/llull.py premortem PLAN.(json|md) [--pool P]   # at most 12 questions
python3 -I jobs/llull/llull.py rank      --actions FILE    # output/RANK.json
python3 -I jobs/llull/llull.py check
python3 -I jobs/llull/test_llull.py
```

Exit codes: 0 ok, 2 refused, 3 flagged (not registered), 4 check failed. `--ledger DIR` points at
another ledger (used by the tests).

## Parts

| Part | Command | What it does |
|---|---|---|
| BRIER | `forecast`, `outcome`, `score` | Registers an 80% interval or a probability **before** a run, resolves it from a committed file, scores Brier, normalized interval score, coverage, optimism (median log of measured/p50), and skill against the outside view, per planner `agent:model`. A planner is "unproven" until 5 resolved forecasts. |
| Domesday | `census` | Zero-agent, per-item count of orders that hold **every** required input. Strict ceiling = all gates held; leads ceiling = leads count too. Prints the product of marginals and flags `ASSUMED_INDEPENDENCE` when it is 1.5x or more above the joint count. |
| Wheel | `premortem` | Plan step x 10 failure modes (`failure_modes.json`) -> at most 12 questions, `auto_fail` first. Only a structured `.json` plan can fail mechanically (number above the census ceiling, `requires_unmeasured`, a gate that is not registered, a proxy unit). Prose plans give `needs_answer` text matches only. |
| Raiffa | `rank` | Ranks actions by (expected ready orders + EVSI) / cost, with a Beta prior from a measured base rate and an exact beta-binomial preposterior. An action with no measured cost or conversion is listed UNRANKED. A zero-agent check that measures a missing input runs first. |
| Juvenal | not built | Llull's own flag recall and precision (design section 6). Needs resolved plans first. |

## Refusals and flags (proved in `test_llull.py`)

- `forecast` refuses a `--reference-class` that is not in `ledger/base_rates.json` with a numeric
  value and a source (`new:<key>` plus `--reason` is allowed, but the interval must then be at least
  [0.1 x p50, 2 x p50], and the measured median miss ratio 0.036 is printed beside the p50).
  `check` fails on an unmeasured seeded row.
- A class with fewer than 3 studies needs the same wide interval. Most seeded classes have n = 1.
- p50 more than 2x from the measured outside view needs `--deviation`.
- p90 above the census ceiling (a count for `ready_orders_gained` / `accepted_items` / `items_reached`,
  a share for rate quantities) prints `CEILING_EXCEEDED` and exits 3 without writing. `--accept-flag`
  registers it flagged. `--unlock-p90` adds the p90 of a registered step that creates the missing input.
- Proxy units (tokens, payload, bytes, packets, certificates, agent-hours) are refused.
- `--run-dir` refuses if the directory already holds committed files; `check` verifies from git history
  that the forecast line was committed strictly before the run directory's first commit.
- `outcome` needs a repository-relative existing source file, one outcome per forecast, and warns
  `ceiling_violated` when the measurement exceeds the census cap (a gate missed a route).

## Seeds

- `ledger/postmortems.json`: the 23-plan pass-1 mining (history, **not registered**, so it feeds base
  rates but not calibration).
- `ledger/base_rates.json`: 19 rows copied only from measured values in the postmortems, each with
  `source`, `postmortem_id` and `evidence` (verbatim quotes that `check` finds in the cited files, whitespace
  ignored; the 0.036 fallback is instead recomputed from `postmortems.json`). Examples: Y2 upheld 3/50 = 0.06, Y1 accepted 15/50, X1 eligible 52/8,014,
  Opus refetch 17/472, HathiTrust 0/1,712, median measured/forecast over 9 unfavourable misses = 0.036.
- `failure_modes.json`: the 10 modes with past miss counts (8, 5, 3, 2, 2, 2, 1, 1, 0, 0 over 12 misses).
  Derived from the same 23 plans, so a score on them is in-sample; only future plans earn trust.
- `ledger/censuses.jsonl`: the three shipped pools. D-1 to D-3 (gates rev 1, commit 46f91fdac) are superseded by
  D-4 to D-6 (gates rev 2, commit 15b4b4d85); `test_llull.py` re-runs the latest rev on inputs taken with `git show`
  at the recorded commit, so later data commits do not break it.
- `examples/`: a structured plan for `premortem` and a candidate-actions file for `rank`.

## Census pools (gates rev 2, commit 15b4b4d85)

| Pool | Definition | Required inputs | Pool | Strict | Leads |
|---|---|---|---|---|---|
| Y1 | numeric EO >= 7532, no provisional status, not ready | `original_text_held`, `status_evidence_held` | 4,274 | 3,952 | 3,952 |
| Y2 | EO >= 7532, status yes/no, text held, not ready, no claim | `status_present`, `original_text_held`, `ending_or_current_held` | 2,060 | 38 (1.8%) | 363 (17.6%) |
| X1 | not numeric EO >= 7532 (pre-1937 and unnumbered) | `status_present`, `original_text_held` | 8,032 | 32 (0.4%) | 32 |

Y1 reproduces the funnel plan's 4,274 and 3,952; X1 reproduces the postmortem's "32 by EO<7532 today"
(the pilot's 52 of 8,014 counted by signing date at an earlier commit). Y2's pool was 2,063 at 46f91fdac
(the scratch `y2_predictor.py` count) and is 2,060 at 15b4b4d85.

**Gates rev 2 (adversarial review, 2026-10-20).** Rev 1 counted any whole-scope ACT verb (transfer, other) and
any TERM end date, including a single section's (`#sec4-b`), as an ending instrument: 67 strict. Rev 2 counts
only revoke/supersede/terminate/abolish ACTs with an effective date and whole-scope TERMs: 38 strict. 10 items per
pool were checked by hand against the raw files.

**The strict count is not a ceiling for rates.** Bowditch Y2 drew its 50 orders at random from this pool and
upheld 3 (6%), above the strict share (3.2% in rev 1, 1.8% in rev 2). None of the 3 upheld orders passed the gate
in either rev (one partial revocation without a date, one whole TERM with a stated but not computed end, one
amended), and 0 of the 50 pass it in rev 2. So the gate misses routes; `outcome` logs `ceiling_violated` in that
case. The strict share is a gate-held share, useful for the order of magnitude, and caps a share only when the
attempts are an unselected draw from the pool. `hit_rate` is not capped at all (it is conditional on the
finder's own selection). Widening the gate to catch these three would be fitting the test cases, so it is not done.
Either way the Y2 target of 50% upheld was far above both counts. No repository source holds a
CURRENT predicate yet, so `current_predicate_held` yields leads only (325 YES orders), never "held".
Also registered: `claim_draft_present`, `no_evidence_conflict`, `only_judgment_left` (claim-drafts).

## Not built yet

The `host_allows` network gate, the Juvenal score (`selfscore`), a Murphy decomposition below 10
binaries, and per-step `requires` evaluation inside `premortem` (it checks only that the gate exists).
