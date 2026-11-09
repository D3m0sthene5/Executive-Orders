# Carnot: the wave-coordinator protocol

Named for Lazare Carnot, the "organizer of victory" (1793-1795), who ran fourteen armies from a desk in Paris by
dispatch and never commanded one in the field. Include this file in every wave prompt
(`Read jobs/carnot-coordinator/PROTOCOL.md and follow it`). It turns Junto's three measured waste patterns into
rules and tools. **No saving is claimed**: each rule has a two-arm Junto test ready in
`jobs/junto/output/OPEN_TESTS.md`, and only `junto.py add-test` with measured arms can verify one.

Measured cost at stake in past waves (Rumford, `jobs/junto/output/EVIDENCE.json`): `lean_coordination` about
$620-666 (main sessions above half of a wave's cost), `revere_phase_handoff` $230 (coordinator calls carrying more
than 300k tokens each), `idle_cache_avoidance` $137 (1-hour caches held through idle waits).

## 1. Lean coordination: the coordinator decides; workers do

- The coordinator keeps legal judgment, control adjudication and integration (owner rule 2026-10-29). Everything
  bounded goes to a fresh headless worker with exact inputs and deliverables:
  `python3 -I jobs/carnot-coordinator/worker.py LABEL MODEL PROMPT_FILE --log RUN/COSTS.log --out RUN/`.
  The worker gets its own context; the coordinator reads only its result file, not its transcript.
- Deterministic work goes to scripts or jobs, never to a model (copying, counting, formatting, filing receipts).
- Do not read large files into the coordinator to "check" them. Ask a script for the number you need.
- Keep turns short: one decision per turn, then act. Do not narrate plans you will not carry out.
- **Failure modes and guards.**
  - A worker that fails silently: `worker.py` exits non-zero and logs `failed` when `claude -p` returns an error
    or no `session_id`; the coordinator must check the exit code.
  - Delegation that costs more than it saves (briefing plus checking about equal to the task): do it yourself,
    and say so in the notes. The test below measures that, not this file.
  - A worker labelled as the coordinator in usage tables: every worker's cost line is in `COSTS.log`; pass it to
    `bentham.py usage --reported-costs RUN/COSTS.log`, which labels those sessions `worker` and cross-checks the
    computed cost against the reported one.

## 2. Waiting: end the turn; never poll

- Wait on a GitHub run with one background watcher, then end the turn:
  `python3 -I jobs/carnot-coordinator/await_run.py --run RUN_ID` as a background command. It prints one line when
  the run reaches any terminal state (or times out) and exits. You are re-invoked then. Do not check in between.
- **Wait longer than about 55 minutes?** The prompt cache (1 hour) will lapse anyway, so holding the session buys
  nothing. Write a handoff packet (section 3), stop, and continue in a fresh session (or one woken by a
  scheduled task) from the packet.
- **Failure modes and guards.**
  - Rate limits: `await_run.py` polls at most every `--interval` seconds (default 300, minimum 60) and backs off
    on HTTP 403/429; anonymous GitHub API calls allow 60 per hour.
  - A run that never ends: `--max-hours` (default 6) exits with `timeout`, never silently.
  - A wrong run id: exits `not_found` at once.
  - A re-run attempt: the watcher reports the latest attempt's state.
  - Network errors: retried; after 10 in a row it exits `error` with the reason.

## 3. Phase handoff: a fresh session per phase

- At each phase boundary (batch filed, PR opened, run dispatched), and whenever the per-call context passes the
  threshold, write the packet a fresh session needs:
  `python3 -I jobs/carnot-coordinator/handoff.py write --phase NAME --next "what to do next" [--note ...]`.
  It records branch, HEAD, uncommitted files, open runs you name, recent commits, the newest notes entry and
  the size of your context, in `HANDOFF/packets/<date>-<phase>.md` (small; built from git and files, never from
  transcript text).
- Check your context any time: `python3 -I jobs/carnot-coordinator/handoff.py context`. It reads this session's
  newest transcript record and warns above 300,000 tokens per call (the threshold Rumford measures against).
- **Failure modes and guards.**
  - A packet that omits uncommitted work: it lists every modified and untracked file, and `--require-clean`
    refuses to write while the tree is dirty.
  - A stale packet: it records HEAD and the time; the fresh session must check `git rev-parse HEAD` matches.
  - A packet that leaks transcript text: it is built only from git, the notes file and arguments you pass.
  - Context unknown (transcript not found): it says `unknown`, never 0, and does not suppress the warning.
  - Handing off in the middle of a step: the packet's `--next` must name a resumable step; a half-written file
    shows in the uncommitted list.

## 4. Record

- When the wave ends: `bentham.py usage --wave NAME --phase LABEL --reported-costs RUN/COSTS.log`, then
  `kean.py add-measures` (or `add-finding --measures`) with the wave's dollars by role and orders, so Bentham and
  Junto read numbers, not prose.
- If you ran a Carnot arm of a Junto test, say which arm in the notes and record it with `junto.py add-test` only
  when both arms are measured.
