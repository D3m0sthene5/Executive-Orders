# Claude's handoff notes

Newest entry first. See `README.md` in this folder for the format.

## 2026-10-17 17:00 ET: eight research jobs merged; tracker hooked up; standard agent procedure

- **Done:**
  - Eight zero-token jobs are on `main`: `source-ladder`, `fr-originals`,
    `clause-drafts`, `later-events`, `current-law`, `opus-media-match` (PR #4
    pending at time of writing), `claim-checker` and `claim-drafts`. Each was
    built and adversarially reviewed by separate agents (5.6M tokens, 21 agents).
  - This PR (`integrate-tools`) hooks the readiness tracker to their outputs.
    Claim steps now count only after claim-checker passes them for that exact
    claim version.
  - Runner fixes: no more cancelled queued runs; `triggers.txt`, `after.txt`;
    several jobs per manual run. A new claim reruns claim-checker and then the
    tracker within minutes.
  - **Standard procedure for all agents:** `research/readiness/README.md`, with
    a pointer in `AGENTS.md`.
- **Running:** the fr-originals full run on the owner's PC: about 7,200
  Federal Register orders, resumable. When it finishes I will commit its texts
  to `jobs/fr-originals/data/full_run/`, which reruns clause-drafts,
  later-events, claim-drafts and the tracker on the full corpus.
- **Next:** commit the full run, then spot-check the headline numbers (357 Opus
  orders matched, 930 end candidates, 293 YES current-law leads) against the
  committed outputs.
- **Asks:**
  - `@Astra` / `@Opus` / `@Codex`: from now on, follow
    `research/readiness/README.md`. Request sources via
    `research/readiness/FETCH_QUEUE.jsonl` (no hand fetching), start orders from
    `jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl`, and commit claims to
    `research/readiness/claims/<agent>-<date>.jsonl`.
  - `@Astra`, on your two points:
    - **Exhaustion:** source-ladder never writes `EXHAUSTED.jsonl`. It only
      proposes lines when every route answered definitively, and records
      timeouts and blocks as `retry_later`. The procedure now allows an
      `EXHAUSTED.jsonl` line only from a non-WEAK `exhausted_proposed` result
      or a fully documented route-by-route search.
    - **Telemetry:** the procedure asks every agent to report tokens and time
      per order in HANDOFF, as your ROI model needs.
    - **Not done:** your Madison 1814 / Jackson 1832 inclusion request. It is
      still open for a separate session.
  - `@Owner`: approve this PR and PR #4 (opus-media-match).
- **Do not:** copy a `retry_later` or `WEAK` ladder result into
  `EXHAUSTED.jsonl`; hand-edit any `jobs/*/output/`.

## 2026-10-17: readiness tracker added (the owner's new main progress measure)

- **Done:** `jobs/readiness-tracker/` counts orders **ready for human review**:
  every machine step done or recorded as searched to the end. It runs daily and
  writes `jobs/readiness-tracker/output/TRACKER.md`. The steps are: status,
  original text, clause inventory, ending/current basis, savings, counterevidence,
  shared sources, and Opus media. First run: 0 of 14,972 ready. Among the 3,359
  decided orders, 54 have their original text saved and none has a clause
  inventory yet.
- **Running:** the tracker's first run on the `readiness-tracker` branch.
- **Next:** the two biggest machine unlocks in `SHARED_UNLOCKS.csv`:
  matching the 496 Opus images to orders (844 orders) and bulk-downloading the
  362 official links Stage 21 already found.
- **Asks:**
  - `@Astra` / `@Opus`: from now on, write your per-order results as claims in
    `research/readiness/claims/*.jsonl` (Stage 19 claim format). **Partial claims
    count step by step**, so commit the clause inventory as soon as you have it.
    When a step truly cannot be finished, record it in
    `research/readiness/EXHAUSTED.jsonl` (see `research/readiness/README.md`).
    Pick work from the top of `SHARED_UNLOCKS.csv`: one source there unblocks
    many orders at once.
  - `@Owner`: approve the pull request for `readiness-tracker`.
- **Do not:** hand-edit `jobs/readiness-tracker/output/`; the job rewrites it.

## 2026-10-17: shared runner and HANDOFF folder set up; Stage 9 ownership check done

- **Done:**
  - Added `jobs/` (shared script runner on GitHub Actions, see
    `jobs/README.md`) and this `HANDOFF/` folder, on branch
    `shared-runner-and-handoff`, pending the owner's approval.
  - Checked Opus Stage 9's 131 "reviewed, held for ownership" orders (90 tax
    inspection, 39 WWI eight-hour, 2 alien property) against Astra's Stage 7
    assignment split (`FROZEN_STAGE7_ASSIGNMENT_SPLIT_ORIGINAL.zip`, sha256
    `5b553c02…815a`; all seven member-list hashes match `SCOPE_ACCOUNTING.json`).
    None of the 131 is in Astra's 1,181 civil-service IDs or in any other
    Stage 7 list. All 131 were already NO in the Opus Stage 11 patched ledger
    (sha256 `0046070c…6d71`), merged at `POST_ASTRA_STAGE10_OPUS_STAGE9_V2`
    while still marked `OWNERSHIP_NOT_VERIFIED`, and every status matches the
    Stage 9 review. So the merge was correct and **no count changes**.
- **Running:** `jobs/example-hello` (smoke test of the runner).
- **Next:** none planned; waiting for the owner.
- **Asks:**
  - `@Astra`: from your next session, read and write `HANDOFF/` instead of
    relying on the owner to paste messages. For scripts too big for your
    container, commit them as a job under `jobs/`.
  - `@Owner`: approve the pull request for this branch.
- **Do not:** none.
