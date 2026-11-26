# Tiro: the wave coordinator's clerk

Tiro is named after Marcus Tullius Tiro, Cicero's secretary, who kept and ordered his papers. It replaces the ad-hoc
scripts the Baldus and Baldus-2 waves ran on 2026-11-25 (`prep.sh`, `prep_loop.sh`, `render_producer.py`,
`review_prep.py`, `finish_pair.py`, `reapply.sh`, `remap_reviews.py`, `remap_finish.sh`, `reuse_finish.sh`,
`current.sh`, `gzip_receipts.py`, `cost.py` and the route prompts). Tiro runs claim-kit commands and file
bookkeeping. It makes no legal judgment: producers and blind reviewers decide every claim, and the control-scoring
rule in `finish` was fixed in advance.

The old scripts hardcoded the wave folder, the date, the wave name and the packet folder `packet`. Copying them to a
second wave folder and editing those constants by hand caused mistakes. Tiro reads every one of those values from
the wave's plan, `research/excavator/claude-<wave>/WAVE.json`:

| Value | Source | Baldus example |
|---|---|---|
| wave name and date | `"wave"` (`NAME-YYYY-MM-DD`) | `baldus`, `2026-11-25` |
| wave folder | the folder holding WAVE.json | `research/excavator/claude-baldus-2026-11-25` |
| Bentham action | `"actions"`; `--action` is required when the plan names several | `production.claim_ready.yes.fr` |
| adjudicator | `claude-coordinator-<wave>` | `claude-coordinator-baldus-2026-11-25` |
| reviewer name | `claude-blind-reviewer-<name>-<batch>-<arm>-<date>` | `claude-blind-reviewer-baldus-y01-A-2026-11-25` |
| packet folder | `--packet`; when a batch has one prepared packet folder Tiro uses it, and when it has several Tiro refuses until you name one | `packet-v2-held` |

Keys, review sets, prompts, logs and worker ledgers stay outside the repository under the scratch root. The default
is `/home/claude/<wave name>-scr` (for example `/home/claude/baldus-scr`); override it with `--scratch` or
`TIRO_SCRATCH`. Tiro refuses a scratch root inside the repository. The layout matches today's: `keys/BATCH.json`,
`review/BATCH/`, `prompts/`, `rev/BATCH-ARM/`, `work/BATCH/`, `logs/`, `DROPPED.txt`, `WORKERS_LAUNCH.csv`,
`WORKERS_DONE.csv` and `COSTS.log`.

Run Tiro from the repository root:

    python3 -X utf8 -I jobs/tiro-wave/tiro.py --wave baldus-2026-11-25 <subcommand> ...

## The wave, step by step

The steps below follow the order the Baldus wave ran on 2026-11-25. Steps 0 and 11 are the repository rules in
CLAUDE.md; Tiro does not run them.

**0. Plan and gates.** Write `WAVE.json` and pass `python -I jobs/augur-launch/augur.py check WAVE.json` with a
review bound to the plan's hash. Read `jobs/bentham/output/PLAN.md`. Prepare only from the full data checkout with
every jobs folder present. In a sparse checkout, packets fail with false blocks and go stale
(F-20261125-sparse-checkout-defect).

**1. Prepare each batch.**

    tiro.py --wave W prepare y01 EO:1 EO:2 ... [--agent baldus] [--action ID] [--level hard]
            [--packet packet] [--held-supplement] [--replacement-proposal]

This runs `kit.py prepare` with `LARREY_LEVEL`. When the kit refuses and its first `claim-kit:` line names member
orders, Tiro drops those orders, logs them in `SCR/DROPPED.txt`, and retries, up to 5 attempts. A refusal that names
no member is a failure. After a packet is prepared, Tiro runs `cruden.py lookups` and builds one Geddes slim view per
member (`views/EO_N.json`). With `--held-supplement`, the kit writes `<packet>-held` and the views go there, because
producers work in that packet. `--ids-from packet` re-prepares the orders of an existing packet into a new one,
which is what `reprep.sh` did. Prepare never overwrites a packet folder. Between retries it removes only the
folder its own failed attempt created; `prep_loop.sh` removed the whole batch folder.

**2. Producer prompt.**

    tiro.py --wave W render-producer y01 yes baldus [--note FILE] [--packet P] [--name y01-v2]

This writes `SCR/prompts/producer-y01.txt` from `prompts/producer.txt` and `prompts/route_<route>.txt`. The routes
are yes, no, undecided, correction, recovery and stale. Tiro splits the assigned members from the dispatch-blocked
ones using the newest `dispatch-vN.json` (by number) or `DISPATCH_CHECK.json`. For an `undecided/` packet it adds
the coordinator precheck. Rendered against today's packets, the output is byte-identical to today's prompts for
n02, y05 and u03.

**3. Launch producers and record them.**

    tiro.py --wave W ledger launch y01 --role producer --model sonnet
    tiro.py --wave W ledger done y01 --role producer --model sonnet --agent-id ID --start T --counts-from \
            [--transcript FILE.jsonl | --tokens N]

The producer runs `kit.py apply` and `batch-check` itself. `--counts-from` reads the outcome counts (submitted,
blocked, unresolved) from the batch's `decisions.csv`. `--transcript` adds the tokens and the list-price dollars of
an Agent-tool transcript and appends a `COSTS.log` line. `tiro.py cost LABEL ROLE FILE` prints the same line on its
own.

**4. Check that the packet is still current before review.**

    tiro.py current research/excavator/claude-baldus-2026-11-25/y01/packet [--from-index]

This runs `batch.load_packet` with source checks and writes nothing in the repository. It prints CURRENT or STALE
with the kit's reason. A PACKET.json that is tracked but not checked out (skip-worktree in a lean checkout) is
reported as NOT_ON_DISK; `--from-index` reads it from the git index into the scratch root. In a sparse checkout,
Tiro also warns that a STALE result can come from files that are not checked out. A stale packet goes to step 8.

**5. Review sets.**

    tiro.py --wave W review-prep y01 applied-v2 [--note FILE] [--packet P] [--kind date_shift] [--dry-run]

This plants max(1, round(n/15)) controls, seeded by the batch name, using `plants.make_controls`. Today's kind,
`date_shift`, moves every first_end and whole_order_end date back three years. When no claim has an end date it moves
every later_events date; when no claim has either, it moves every signing_date. Tiro writes
`SCR/review/BATCH/REVIEW_SET{,_A,_B}.jsonl` (A and B are shuffled separately), `GENUINE_CONTROLS.jsonl`, the private
key `SCR/keys/BATCH.json` (each control records its kind), and the reviewer and reveal prompts. In the packet it
writes only `reviews/` and `APPLIED_FOR_REVIEW`; `--dry-run` skips those two writes. Tiro refuses to overwrite an
existing key without `--force`, because `finish` scores both arms against that key.

**6. Blind arms.** Two Opus reviewers, one per arm, each get `SCR/prompts/reviewer-BATCH-ARM.txt`. To pool several
small batches into one agent per arm (Gilbreth: pooling sets of 4 or more cuts the per-claim review cost):

    tiro.py --wave W pool-prompt y14 y15 y16 --arm A --write pool4

This prints one instruction that contains each batch's reviewer prompt in full. The agent therefore opens nothing
in the scratch root beyond what a one-batch review allows. After both blind files exist, send the reveal prompts
(`reveal-BATCH-ARM.txt`, or `pool-prompt --reveal`) so that each arm reviews the genuine versions of the controls.

**7. Finish.**

    tiro.py --wave W finish y01 [--packet P] [--publish] [--replacement]

A control is caught only if both arms rejected its exact planted hash and named the planted defect. Any miss stops
the batch before completion. `make_completion.py` then builds the manifest from arm A's records. `pair_rule()` in
`tiro_finish.py` blocks every submitted member that arm B did not also uphold at the same hash (`upheld`, or
`upheld_after_reveal` for a genuine control), quoting arm B's defects. Own claims take the file name that
`kit.py publication-name` chooses. `--replacement` writes `WAVEDIR/BATCH/REPLACEMENT_PROPOSAL.jsonl` instead (the
old scripts used the `REPLACEMENT=1` environment variable, which Tiro still honours). `kit.py complete` writes a new
`complete-vN` and its log goes to `COMPLETE_vN.log`.

**8. Recover a stale packet** (the causes are below).

    tiro.py --wave W reapply y17 packet-v2-held applied-v8 packet-v3 --held [--rp]
    tiro.py --wave W reuse-reviews y17 packet-v2-held applied-v8 packet-v3-held applied-v1 --finish --publish

`reapply` re-prepares the same orders, taking the agent and the Bentham action from the old packet's ADMISSION.json.
It carries `decisions.csv` over with each `dossier_sha256` refreshed to the new dossier, copies `clauses.csv` and
`RATIONALES.json`, applies the sheets into `applied-v1`, and prints IDENTICAL or DIFF for each order.

`reuse-reviews` runs `batch-check` on the new applied folder and stops if it fails. It then applies owner standing
rule D-20261125-reuse-identical-reviews (rev 1): it reuses both arms' reviews only if every order's claim is
byte-identical or differs only in `claim_kit.dossier_sha256`, and only if both claim files hold the same orders. It
copies the reviews and remaps each changed row's `claim_sha256`, keeping the old hash as
`review_reused_from_claim_sha256`. It updates the key's genuine hashes and keeps the old key as `.pre-remap`. It
writes `REVIEW_REUSE.json` and `APPLIED_FOR_REVIEW` in the new packet. Any other difference is a refusal: the batch
goes back to review.

**9. Large receipts.** `tiro.py gzip-receipts .../complete-vN` stores every file over 50 MB as lossless gzip with a
`NAME.COMPRESSED.json` sha256 record, because GitHub refuses files over 100 MB.

**10. Adopt replacement proposals** under the standing rule D-20261125-auto-adopt-replacements:

    tiro.py --wave W adopt m01 [--packet P] [--write]

This wraps `jobs/claim-kit/adopt_replacement.py --standing` for the newest replacement-proposal `complete-vN`. The
default target is `research/readiness/claims/novellae-<date>-<wave>-<batch>.jsonl` and the default receipt is
`WAVEDIR/BATCH/ADOPTION_RECEIPT.json`. Without `--write`, it prints the plan and writes nothing.

**11. After each batch,** run `bentham.py gate` and stop on STOP. Commit each finished batch and drop its heavy files
before the next batch starts. When the wave ends, run `bentham.py usage` and record the results in Kean.

## Why packets went stale on 2026-11-25, and the recovery

The newest entry of `HANDOFF/notes-claude.md` (branch `claude/baldus-part6`) records three causes:

- Every packet's prior research pins each file under `research/readiness/owner_rulings/`, so one new ruling file
  invalidates every packet in flight. Where possible, record decisions in Kean without a ruling file, and write
  ruling files only between waves.
- `jobs/claim-kit/BATCH.md` is a Valla protocol pin. The owner merged PR #342 mid-wave, which invalidated every
  packet prepared before it.
- A completion's `receipts/` folder copies repository files that name many orders (`SOURCE_AUDIT_HOLDS.jsonl`,
  `MANSFIELD_AUDIT.json`). Finishing one batch can therefore invalidate other packets in flight. `prior_research.py`
  still binds `receipts/` files on purpose (`test_completion_folder_other_files_still_bind`).

The recovery that worked has four steps: re-prepare, carry the sheets over, apply, and compare. Reuse the reviews
only when the claims are byte-identical or differ only in `claim_kit.dossier_sha256`. That is step 8 above:
`reapply`, then `reuse-reviews`. Run `current` on every packet in flight after any merge, ruling or batch finish.

## Extending Tiro

- **Plant kinds** live in `plants.py`. A kind is a class with `name`, `words` (the words a rejection must use for the
  control to count as caught), `choose(claims)`, `plant(claim, mode)`, `defect(mode)` and `type(mode)`; register it in
  `plants.KINDS` and pass `review-prep --kind NAME`. `finish` judges each control by its own kind's words. Keys
  written before kinds existed have no `kind` field and are judged as `date_shift`.
- **The pair rule** is `tiro_finish.pair_rule()`, and control adjudication is `tiro_finish.adjudicate_controls()`.
  A fix-and-recheck route should extend these functions rather than add a second rule elsewhere.
- **External commands** all go through `tiro_common.run`, which the tests replace. The tests
  (`python3 -m pytest -q jobs/tiro-wave`) use small temporary fixtures and never run the real kit.
- Tiro is a coordinator tool, not a scheduled job: it has no `job.py`, so `pick_jobs` never runs it, and it imports
  nothing from `jobs/_lib` (no `triggers.txt` declarations needed).
