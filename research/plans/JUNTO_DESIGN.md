# Junto: a club that learns where to look for token savings (design, 2026-10-20)

Named for Benjamin Franklin's Junto (1727), the Philadelphia club of tradesmen that met on
Friday evenings, answered a fixed list of "standing queries" and kept only the ideas that
worked in practice. Junto does the same for agent cost: it runs **finders**, tests what they
suggest, and gives more of its budget to the finders whose suggestions held up.

Status: built in `jobs/junto/` (as-built names and commands are in its README: finders
`hamilton`, `friction`, `wasted_work`; commands `run`, `add-test`, `score`, `allocate`,
`propose`, `check`). No saving is verified yet.

## 0. Levels and the hard rule

| Level | What it is | Examples |
|---|---|---|
| **Saver** | A change that cuts tokens in real sessions. | Revere (phase handoff to a fresh session), Watchman (monitoring outside the big session), Spare setup, Quiet protocol |
| **Finder** | A script that reads audit data and proposes savers ("candidates"). | `hamilton_causes` (the first one; wraps Hamilton's profiles) |
| **Junto** | Runs finders, tests candidates, scores finders, divides the budget, proposes new finders. | `jobs/junto/junto.py` |

**Hard rule.** A saving counts only after a small before-and-after test that measured it.
Estimates, projections and "should save" never count toward any score. Everything a finder
emits has `status: "unverified"`. Why this rule exists: the excavator plan assumed X1 would save
4,134 hours; X1 measured about 463 (`research/production/x1-2026-10-19/REPORT.md`).
Hamilton's own tool table (Revere "about 40% off X1", Watchman "most of the 15%") is a set of
estimates too. Those savers enter Junto as unverified candidates.

What Junto inherits from Hamilton (`jobs/hamilton-token-audit/`,
`research/production/hamilton-2026-10-20/REPORT.md`): in X1 the coordinator was 72% of
input-side cost; each agent re-reads about 70 k tokens of fixed setup on every call; waiting in
a large context (status checks, a cache rebuild after an idle hour) was about 15%; the model's
own narration was 11-21%; printing files and command output was about 15-20%.

## 1. Layout

```
jobs/junto/
  README.md
  junto.py                 # driver: run-finder, propose-test, record-test, score, allocate, blindspot, check
  config.json              # round budget, exploration share, thresholds (section 3)
  causes.json              # cause taxonomy: Hamilton labels -> cause keys (section 4)
  finders/<name>.py        # one file per finder (section 2)
  ledger/
    finders.json           # registry (small JSON, edited by junto.py only)
    runs.jsonl             # one line per finder run, with its cost
    candidates.jsonl       # finder output plus status changes, append-only
    tests.jsonl            # test plans and results, append-only
    verified_savings.jsonl # measured savings, each tied to a test, append-only
    finder_proposals.jsonl # blind-spot proposals for new finders, append-only
  output/
    SCOREBOARD.json        # derived by `junto.py score`; never hand-edited
    STATUS.json            # last driver run: ok/failed, counts, checker result
```

If a finder needs more than the container can hold, it runs as a GitHub Actions job with
`needs.txt`, as other jobs do, and Junto reads `output/STATUS.json` before using its output.

### Ledger conventions

- JSONL files are **append-only**. A status change is a new line with the same id and a higher
  `rev`; the current state is the line with the highest `rev`. No line is ever edited or deleted,
  so parallel agents merge cleanly and every refuted claim stays on the record.
- Every line has `schema` (e.g. `"junto.candidate/1"`), `rev`, `written_at` (ISO 8601 UTC) and
  `written_by` (agent name, e.g. `"claude"`, not a person's email).
- Money is `usd` with two decimals, at API list-price value (the same basis as Hamilton's
  `cost_usd`), with a `usd_basis` field: `"get_session.cost_usd"`, `"actions_minutes"` or
  `"profile_scaled"`.
- Ids: `F-<name>`, `R-<yyyymmdd>-<n>`, `C-<yyyymmdd>-<n>`, `T-<yyyymmdd>-<n>`, `V-<yyyymmdd>-<n>`,
  `P-<yyyymmdd>-<n>`.
- `junto.py check` validates every file against the field lists below and the privacy rules
  in section 5. A commit that fails the check must not be pushed.

### `ledger/finders.json`

```json
{"schema": "junto.finders/1", "finders": [
  {"finder_id": "F-hamilton_causes", "name": "hamilton_causes",
   "script": "jobs/junto/finders/hamilton_causes.py", "version": "1",
   "added_at": "2026-10-20", "origin": "seed | proposal:P-...",
   "state": "exploring | scored | dormant | retired",
   "targets": ["coordinator_context", "fixed_setup", "idle_wait", "narration", "tool_output"],
   "notes": "one line"}]}
```

`targets` lists the cause keys (section 4) the finder is meant to cover. The blind-spot step
relies on this list.

### `ledger/runs.jsonl` (one finder run)

| Field | Meaning |
|---|---|
| `run_id`, `finder_id`, `finder_version` | |
| `started_at`, `ended_at`, `wall_seconds` | |
| `data_digest` | sha256 over the sorted input file names and sizes, so a run can be repeated. Not the contents. |
| `inputs` | `{"profiles": n, "sessions": n, "events": n}` counts only |
| `candidates_emitted` | list of `candidate_id` |
| `usd_spent`, `usd_basis` | What the run cost: the agent session that ran and read it (from `get_session` `cost_usd`, the difference between before and after), plus Actions minutes when it ran there. A pure script with no model in the loop records its Actions cost or 0.00 with `usd_basis: "local_script"`. |
| `round_id` | the Junto meeting that paid for it (section 3) |

### `ledger/candidates.jsonl` (what a finder emits)

| Field | Meaning |
|---|---|
| `candidate_id`, `rev`, `finder_id`, `run_id` | |
| `saver_key` | Short slug of the proposed saver, e.g. `revere_phase_handoff`. Used to merge duplicates: two finders proposing the same `saver_key` share one test (section 3). |
| `title` | 12 words or fewer |
| `targets` | cause keys it attacks, e.g. `["coordinator_context"]` |
| `evidence` | Aggregates only: `[{"session_id": "...", "profile": "research/production/.../PROFILE_x1.json", "cause_key": "...", "usd": 4.4, "share": 0.15, "events": 37, "model_calls": 12, "median_context_tokens": 421000}]`. No text from the transcript. |
| `estimate` | `{"usd_per_session": n, "tokens_per_session": n, "basis": "one line on how"}`. Shown for triage and **never counted**. |
| `proposed_test` | One line: which task, which arms, which measure. |
| `status` | `unverified` -> `test_proposed` -> `tested` -> `verified` or `refuted` (also `withdrawn`) |
| `status_ref` | the `test_id` (or `verified_id`) that justifies the current status |

Lifecycle:

```
unverified --(junto.py propose-test: a test plan is written)--> test_proposed
test_proposed --(both arms measured; tests.jsonl result line)--> tested
tested --(result meets section 1 test rule)--> verified   (+ a verified_savings line)
tested --(no saving, or quality fell)--> refuted
tested --(inconclusive)--> test_proposed  (one retest; a second inconclusive is refuted)
any --(finder or owner withdraws)--> withdrawn
```

Only `junto.py` moves a status, and a move to `verified` is refused unless the referenced test
line has both arms measured.

### `ledger/tests.jsonl` (a small before-and-after test)

| Field | Meaning |
|---|---|
| `test_id`, `rev`, `candidate_ids`, `saver_key` | |
| `phase` | `planned` or `measured` |
| `unit_of_work` | What one accepted result is: `accepted_claim`, `merged_pr`, `completed_phase`, `pr_babysit_to_merge`, ... |
| `before` / `after` | Each arm: `{"session_ids": [...], "usd": n, "usd_basis": "get_session.cost_usd", "tokens": {"input", "cache_read", "cache_write", "output"}, "units": n, "usd_per_unit": n, "quality": {"accepted": n, "rejected": n, "checker_pass": n}, "profile": "path to a Hamilton PROFILE json"}` |
| `matched_on` | What was held fixed: model, task class, repository commit, the rules in force |
| `test_cost_usd` | What the test cost Junto (section 3) |
| `delta_usd_per_unit` | `before.usd_per_unit - after.usd_per_unit` |
| `verdict` | `saves`, `no_saving`, `quality_fell`, `inconclusive` |
| `unpredicted_waste` | Filled by the blind-spot step (section 4) |

**Test rule.** Totals come from `get_session` (the session's own `cost_usd` and token counts),
not from Hamilton's per-cause shares, which are estimates. A test is `saves` only if
`after.usd_per_unit <= 0.9 * before.usd_per_unit` and no quality measure is worse. A smaller
gain is `inconclusive` (a single pair is noisy). The before arm may be an existing audited
session of the same task class; the after arm is a fresh run with the saver on.

### `ledger/verified_savings.jsonl`

| Field | Meaning |
|---|---|
| `verified_id`, `test_id` (required), `saver_key`, `candidate_ids` | |
| `kind` | `test_realized`: the saving inside the test itself, `delta_usd_per_unit * after.units`. `adoption_realized`: a later real session that used the saver, re-audited by Hamilton, priced against the test's `before.usd_per_unit` for the same unit of work. |
| `usd_saved`, `tokens_saved` | measured, never projected |
| `measurement` | `{"before_usd_per_unit": n, "after_usd_per_unit": n, "units": n, "session_ids": [...]}` |
| `credited_to` | `[{"finder_id": "...", "share": 0.5}]` (section 3) |

`junto.py check` rejects a line whose `test_id` is missing, whose test is not `measured` with
verdict `saves`, or whose `usd_saved` exceeds the test's measured delta times the units.
There is no field for an annual or projected saving.

### `ledger/finder_proposals.jsonl`

See section 4.

## 2. Finder interface

```
python3 -I jobs/junto/finders/<name>.py --data <dir> --out <file.jsonl> --run-id <R-id> [--profiles <dir>]
```

- `--data`: a directory **outside the repository** (e.g. the scratchpad `junto-data/`) holding
  saved `list_events` pages and `get_session` totals. The finder refuses (exit 3) if `--data`
  resolves inside the repository.
- `--profiles`: optional directory of Hamilton `PROFILE_*.json` files (committed, already redacted).
- `--out`: candidate records, one JSON object per line, in the `candidates.jsonl` fields above,
  every one with `status: "unverified"`, `rev: 0`.
- Writes `<out>.run.json` beside it: the `runs.jsonl` fields it can know (`wall_seconds`,
  `inputs`, `data_digest`, `candidates_emitted`), with `usd_spent: null`. `junto.py run-finder`
  fills in `usd_spent` from the running session's `get_session` totals before appending to
  `runs.jsonl`, so a finder cannot report its own cost as lower than it was.
- Prints at most 20 lines to stdout (Hamilton's quiet protocol): counts and the top candidates'
  `saver_key` and `estimate`. No transcript text.
- Exit codes: 0 ok; 2 bad or empty input; 3 privacy refusal (data inside repo, or a record failed
  the redaction check).
- Standard library only, runs with `-I`, deterministic for the same inputs (sorted iteration, no
  clocks in the records except `written_at`).
- Reuses `jobs/hamilton-token-audit/profile.py` (`load`, `profile`, `tool_label`) rather than
  re-parsing transcripts, so the redaction in `tool_label` applies.

Seed finder `hamilton_causes`: reads profiles, maps each cause to a key (section 4), and for
each key above 5% of a session's cost emits the saver template for that key (Revere for
`coordinator_context`, Watchman for `idle_wait`, Spare setup for `fixed_setup`, Quiet protocol for
`narration` and `tool_output`). Its first run turns Hamilton's four proposed tools into four
unverified candidates.

## 3. Scoring and allocation ("Poor Richard": a penny saved is a penny earned)

**What a finder spends.** `spent_f` = the sum of its `runs.jsonl` `usd_spent` plus its share of
`test_cost_usd` for every test of its candidates. `test_cost_usd` includes:
the after arm's full cost; any before arm run only for the test (an existing audited session
costs nothing); the cost of building the saver for the test; and the coordinator's cost of
planning and recording the test (the change in its `get_session` total). A test of a
`saver_key` proposed by several finders before the test was planned is charged, and credited,
in equal shares to those finders. A finder that emits the same `saver_key` after it has been
tested gets no share.

**What it earned.** `verified_f` = the sum of its credited `usd_saved` in `verified_savings.jsonl`.
Nothing else.

**Score.**

```
score_f = verified_f / (spent_f + S0)        S0 = $2.00 prior (config.json)
```

A finder with no verified saving scores exactly 0, however large its estimates. The prior `S0`
keeps a finder with one lucky cheap test from dominating (a $1 saving on $0.05 spent scores
0.49, not 20). Scores above 1 mean the finder paid for itself. Junto's own overhead (the
`junto.py` driver session and meetings) is also logged in `runs.jsonl` under `F-junto`, and
`SCOREBOARD.json` reports Junto's total `verified / spent`, so the meta-tool is held to the same
rule.

**Allocation per meeting.** The owner sets `round_budget_usd` in `config.json`. Each meeting:

1. **Exploration, 20%**: split equally among finders in state `exploring` (new, from a blind-spot
   proposal, or fewer than 2 resolved tests), at most 3 per meeting, oldest first. If none,
   this share goes to exploitation.
2. **Exploitation, 80%**: proportional to `score_f` among `scored` finders, with a floor of 5% of
   this pool for any finder with `score_f > 0`. If no finder has a positive score yet (now),
   the whole budget is exploration.
3. **Dormancy**: a finder with `score_f = 0` after at least 2 resolved tests and at least $10 spent
   becomes `dormant` and gets no exploitation money; it may re-enter exploration once every 5
   meetings. A finder is `retired` only by the owner.
4. Within a finder's allowance, its untested candidates are tested in order of `estimate`
   (estimates may rank work, never score it). Unspent allowance does not carry over.

`junto.py allocate` writes the plan to `output/SCOREBOARD.json` (finder, state, spent, verified,
score, allowance). The plan is advice to the coordinator; spending happens only through tests
that are logged.

## 4. Blind-spot step ("Standing Queries")

Franklin's Junto opened each meeting with standing queries, among them whether anyone had heard
of a mistake worth avoiding. After every measured test, `junto.py blindspot --test <T-id>` asks
the same of the before and after Hamilton profiles:

1. Map every Hamilton cause label to a cause key using `causes.json`, e.g.
   `fixed setup (...)` -> `fixed_setup`; `model wrote: reply or narration` -> `narration`;
   `Bash cat`, `Bash sed`, `Bash ls`, `Read` -> `tool_output`; `model wrote: Write`, `model wrote: Bash ...`
   -> `model_writes`; `status_checks_in_large_context` and `cache_rebuilds` -> `idle_wait`;
   main-agent share above 60% -> `coordinator_context`. An unmapped label maps to `unmapped:<label>`
   (the label is already redacted by `tool_label`).
2. A cause key is **waste** in this test if, in either arm, it costs at least 5% of the session
   or at least $1.00, or it rose by at least 20% from before to after (a saver that moved cost
   elsewhere).
3. It is **unpredicted** if no candidate of any finder lists it in `targets` and no registered
   finder lists it in `finders.json` `targets`.
4. Each unpredicted key is written to the test's `unpredicted_waste` and, if no open proposal
   already covers it, appended to `finder_proposals.jsonl`:

| Field | Meaning |
|---|---|
| `proposal_id`, `rev`, `test_id`, `cause_key` | |
| `evidence` | `{"session_ids": [...], "usd": n, "share": n, "arm": "before|after", "rise": n}` |
| `suggested_finder` | name and one line on what it would look for |
| `status` | `open` -> `accepted` (a finder is built and registered with `origin: proposal:P-...`, state `exploring`) or `declined` (reason) |

The cost of the blind-spot step is charged to `F-junto`, not to the finder under test.
A finder built from a proposal starts in the exploration share like any other new finder.

## 5. Privacy rules

1. **No raw transcripts in the repository.** `list_events` pages and `get_session` dumps stay in
   the scratchpad (`junto-data/`) or in Actions artifacts that are not committed. Only derived
   aggregates are committed: Hamilton profiles and the ledger.
2. **No transcript text in any ledger field.** Evidence is numbers, session ids, event and call
   counts, cause keys and committed file paths. No prompts, replies, command text, tool output or
   file bodies.
3. **Cause labels go through Hamilton's `tool_label`**, which never echoes a command that sets
   variables (`Bash (sets variables, then runs a script)`) and keeps only the program name for
   other commands. Finders must not build labels of their own from command text.
4. **No secrets, tokens, keys, passwords, cookies, signed URLs or email addresses.**
   `junto.py check` rejects any string that matches common secret patterns (`ghp_`, `github_pat_`,
   `sk-`, `xox`, `AKIA`, `Bearer `, `-----BEGIN`, `token=`, `key=`, `sig=`), contains `@` followed
   by a domain, contains `=` inside a cause label, contains a URL with a query string, or is longer
   than 200 characters in `evidence`. Unknown keys are rejected too.
5. **Paths**: only repository-relative paths of committed files. No absolute paths, home
   directories or scratchpad paths in the ledger.
6. **Isolation**: finders and the driver run with `python3 -I`, standard library only, and are
   kept in `jobs/junto/`, never inside the data directory, so a file in downloaded data cannot
   shadow a module.
7. **People**: `written_by` names an agent. The owner appears only as `owner`.
8. A redaction failure is a stop: the finder exits 3, nothing is appended, and the run is logged
   with `usd_spent` (the cost still counts) and `candidates_emitted: []`.

## 6. First meeting (proposed, not started)

1. Build `junto.py check` and the empty ledger; register `F-hamilton_causes` and `F-junto`.
2. Run `hamilton_causes` on the five committed profiles: expect four unverified candidates
   (Revere, Watchman, Spare setup, Quiet protocol). Budget is all exploration, since no finder
   has a score.
3. Cheapest test first: Spare setup (one empty session per configuration, read first-call
   context), then Watchman on the next pull-request babysit, then Revere on a Y1 phase.
4. Run the blind-spot step after each test; report `SCOREBOARD.json` in `HANDOFF/notes-claude.md`.

None of this touches the evidence codebook, claim status, or the certified whole-lifecycle count.
