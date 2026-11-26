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

    tiro.py --wave W review-prep y01 applied-v2 [--note FILE] [--packet P] [--kind K] [--seed S] [--dry-run]

This plants max(1, round(n/15)) controls with `plants.make_controls`. Every control on 2026-11-25 was a three-year
date shift; both arms caught all of them, and the Geddes date checks (`date_before_signing`,
`end_year_conflicts_reasons`) now catch that kind mechanically, so it tests attention rather than judgment. Three kinds
copy the defects genuine claims were actually rejected for:

| Kind | What the planted copy does | Modes |
|---|---|---|
| `event_drop` | removes one recorded later event (one acting instrument, from every clause that records it) and lowers any stated count of that event type in the prose by one; prefers an instrument the prose never names and, for annual notices, neither the first nor the last | `notice`, `amendment`, `other` |
| `clause_misdescription` | YES claim: an ended clause recorded as operative, its first_end removed and a continuing predicate citing the clause's own text added. NO claim: a terminated clause recorded as never_activated, or the reverse | `ended_to_operative`, `state_swap` |
| `citation_drop` | removes one cited source of another instrument, and its quote, from every first_end, whole_order_end, current_predicate, savings_residuals or formal_disposition slot citing it; each slot falls back to the order's own text and the conclusion stays | the first slot type |
| `date_shift` | the original plant: end dates moved back three years, else later-event dates, else signing dates | `end`, `event`, `signing` |

Each of the three new kinds leaves the claim schema-valid (Stage 19 `claim_gate`), cites only sources the genuine
claim already cites (so the claim kit's source, quote and dossier-evidence checks pass wherever the genuine claim
passed), and adds no Geddes pre-review flag. `test_tiro_plants.py` checks this on fixture claims and on real
2026-11-25 claims read from git (y16 EO 13757, n02 EO 13322, y05 EO 11755); with `TIRO_KIT_CHECK=1` it also runs the
kit's `check_claim` against the real dossiers (about a minute). A plant never changes what a NO claim's end dates
are, so `whole_order_end` stays the latest clause end. Not every claim can take every kind: all-operative claims
whose sources are the order's own text, like most of y16, can take only `event_drop` or `date_shift`.

`--kind` defaults to `rotation`: the seed (`--seed`, default the batch name) picks a start in
`event_drop, clause_misdescription, citation_drop, date_shift`, successive controls take successive kinds, and a kind
no remaining claim can take is skipped. `--kind NAME` plants only that kind and refuses when no claim fits;
`--kind date_shift` draws exactly the orders the old tool drew. The key records `plant_kind`, `plant_seed`,
`plant_rotation` and, per control, `kind`, `mode`, `type`, `defect` (a one-line description of the planted defect,
which the reveal prompt shows) and `match` (the identifiers a rejection must name: the dropped instrument, the
misdescribed clause or the removed source). Tiro writes `SCR/review/BATCH/REVIEW_SET{,_A,_B}.jsonl` (A and B are
shuffled separately), `GENUINE_CONTROLS.jsonl`, the private key `SCR/keys/BATCH.json`, and the reviewer and reveal
prompts. In the packet it writes only `reviews/` and `APPLIED_FOR_REVIEW`; `--dry-run` skips those two writes. Tiro
refuses to overwrite an existing key without `--force`, because `finish` scores both arms against that key.

**6. Blind arms.** Two Opus reviewers, one per arm, each get `SCR/prompts/reviewer-BATCH-ARM.txt`. The prompt tells
them to read [`RUBRIC.md`](RUBRIC.md) first: what each verdict means, what sinks a claim and what is only a note
(wording that misstates evidence sinks; style does not), unheld sources (notes, not verdicts), the three open
conventions they record as `CONVENTION:` notes, and the tags every defect carries: `class` (date, omission,
misdescription, citation, page_label, convention, other), `locality` (LOCAL or STRUCTURAL) and `fields` (the exact
claim paths a fix would edit). To pool several
small batches into one agent per arm (Gilbreth: pooling sets of 4 or more cuts the per-claim review cost):

    tiro.py --wave W pool-prompt y14 y15 y16 --arm A --write pool4

This prints one instruction that contains each batch's reviewer prompt in full. The agent therefore opens nothing
in the scratch root beyond what a one-batch review allows. After both blind files exist, send the reveal prompts
(`reveal-BATCH-ARM.txt`, or `pool-prompt --reveal`) so that each arm reviews the genuine versions of the controls.

**7. Finish.**

    tiro.py --wave W finish y01 [--packet P] [--publish] [--replacement] [--repair-receipt FILE]

A control is caught only if both arms rejected its exact planted hash and named the planted defect: for a key entry
with `match` identifiers, one of them and one of the kind's words; otherwise one of the kind's words. Any miss stops
the batch before completion. `make_completion.py` then builds the manifest from arm A's records. `pair_rule()` in
`tiro_finish.py` blocks every submitted member that arm B did not also uphold at the same hash (`upheld`, or
`upheld_after_reveal` for a genuine control), quoting arm B's defects. Own claims take the file name that
`kit.py publication-name` chooses. `--replacement` writes `WAVEDIR/BATCH/REPLACEMENT_PROPOSAL.jsonl` instead (the
old scripts used the `REPLACEMENT=1` environment variable, which Tiro still honours). `kit.py complete` writes a new
`complete-vN` and its log goes to `COMPLETE_vN.log`.

**7a. Fix and re-check a one-arm LOCAL rejection** (owner rule, 2026-11-25). When a reviewer rejects a claim for a
specific local defect, the producer may fix only that defect and the rejecting reviewer re-checks only that point,
with the other reviewer's uphold carried over if nothing else in the claim changed. A claim whose fix touches anything
beyond the flagged point still needs both reviewers again. Planted controls are never repairable, and a claim both
arms rejected is not repairable under this rule. Run it after both blind files and the reveal files exist, before
`finish`:

    tiro.py --wave W repair-prep y01 [--packet P] [--tags FILE]
    tiro.py --wave W repair-check y01 applied-v3 [--packet P] [--no-batch-check] [--dry-run]
    tiro.py --wave W finish y01 --repair-receipt research/.../y01/packet/REPAIR_RECEIPT.json

`repair-prep` reads the blind and after-reveal reviews of the `APPLIED_FOR_REVIEW` claims and lists every genuine
claim one arm rejected and the other upheld whose defects are all LOCAL, of a repairable class and name exact
`fields`. It writes `SCR/repair/BATCH/REPAIR_PLAN.json` (every order's status) and the producer prompt
`SCR/prompts/repair-producer-BATCH.txt`, which names each claim, quotes each defect as the reviewer wrote it, and
lists the fields the fix may change. It writes nothing in the packet. Reviews written before the rubric carry no
tags, so every such defect is `untagged` and not repairable; `--tags FILE` (`{"EO:N": [{"class", "locality",
"fields"} per defect, in order]}`) supplies tags for untagged defects only, and the plan records the file's sha256 on
each tag it used.

The producer fixes the named fields through the sheets and writes a new `applied-vN`. `repair-check` runs
`batch-check` on it, then diffs every claim against the reviewed version. It refuses outright when an order outside
the plan changed, the two files hold different orders, or the reviewed claims or the key changed since
`repair-prep`. For each planned claim it accepts the fix only if every changed path lies inside the clause or
top-level field the defect's `fields` name (the anchor) and is a field the class allows:

| Class | A fix may change, inside the anchor |
|---|---|
| `page_label` | `page_or_item`, `evidence_id`, `char_start`, `char_end`, `location_confidence`, `location_verified`, `requires_page_check` (never the quote, the text file or the URL) |
| `date` | `date`, `effective_date`, `earliest`, `latest`, `date_kind`, `checked_through`, and the prose fields |
| `misdescription` | `state_at_cutoff`, `mechanism`, `mechanism_note`, `first_cause`, `actor`, anything under `first_end` or `current_predicate`, and the prose fields |
| `omission` | anything under `later_events`, the prose fields, and the derived `fr_fulltext_captures` disclosure |
| `citation` | anything under a `source` (never an `original_source`), the prose fields, and the derived `fr_fulltext_captures` disclosure |
| `convention`, `other` | nothing: not repairable under this rule |

The prose fields are `research_rationale`, `judgment_reason`, `legal_basis`, `reason` and `mechanism_note`. A claim
with any change outside that map is refused and listed as needing both reviewers again; its new version has no
review, so `finish` blocks it. For each accepted claim `repair-check` copies the upholding arm's record to
`reviews/REPAIR_CARRIED_<arm>.jsonl` with the new `claim_sha256` (keeping the old one as
`review_carried_from_claim_sha256`, as `reuse-reviews` does), writes the re-check set and the prompt
`SCR/prompts/recheck-BATCH-ARM.txt` for the rejecting arm (the defect, each changed path before and after, and the
output `reviews/RECHECK_<arm>.jsonl`), and writes `REPAIR_RECEIPT.json` in the packet. `--dry-run` writes the receipt
and the carried file under `SCR/repair/BATCH/` instead.

`finish --repair-receipt` re-verifies the receipt (both claim files' hashes, the same diff, the carried file's hash),
completes the receipt's repaired applied folder, and passes arm A's extra files to `make_completion.py` with its
blind file. `pair_rule()` keeps a repaired claim only if both arms have an `upheld` record of that exact new hash:
the rejecting reviewer's re-check (same reviewer name) and the other arm's carried uphold.

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

- **Plant kinds** live in `plants.py`. A kind is a class with `name`, `words` (a rejection must use one for the
  control to count as caught), `eligible(claim, ctx)` and `plant_one(claim, rng, ctx)`, which returns the planted
  copy and its `mode`, `type`, one-line `defect` and `match` identifiers. Register it in `plants.KINDS` and add it to
  `plants.ROTATION`. A new kind must keep the claim schema-valid, cite only sources the genuine claim cites and add
  no Geddes flag; add it to `NEW_KINDS` in `test_tiro_plants.py`, which checks all three. `finish` judges each control
  by its own kind. Keys written before kinds existed have no `kind` field and are judged as `date_shift`.
- **The pair rule** is `tiro_finish.pair_rule()`, and control adjudication is `tiro_finish.adjudicate_controls()`.
  The fix-and-recheck route extends `pair_rule()` (its `repairs` argument); a later route should do the same rather
  than add a second rule elsewhere. The fix-and-recheck field map is `tiro_repair.FIELD_MAP`.
- **External commands** all go through `tiro_common.run`, which the tests replace. The tests
  (`python3 -m pytest -q jobs/tiro-wave`) use small temporary fixtures and never run the real kit.
- Tiro is a coordinator tool, not a scheduled job: it has no `job.py`, so `pick_jobs` never runs it, and it imports
  nothing from `jobs/_lib` (no `triggers.txt` declarations needed).
