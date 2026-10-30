# Packet friction repairs (audit H01–H07): what changed and what it measurably bought

Branch `opus/packet-friction`, from main `f9c6d806ad`. Engineering only: no claim, status, review, census or
codebook changed, and nothing canonical was published. All replays ran in isolated, read-only hardlinked trees
(`make_tree.py`, `stage_nra.py`, `install_arm.py` in this folder). Receipts are in `receipts/`.

## Result in one paragraph

On identical pinned inputs, the native path is now several times faster and stops failing on unrelated work.
The real NRA t6 completion (16 independently reviewed claims, real reviews and controls) still loses against
a concurrent publication on the old code: 506 s, 0 published, "input file set changed". With the repair it
finishes in 122 s and publishes 16 claims, byte-identical to the file production obtained only by a second,
serial run. A supplemented 24-order packet now views in 3.7 s instead of 28.6 s. `apply` takes 8.8 s instead
of 143.7 s, and `batch-check` with the actual claim-checker takes 29.3 s instead of 158.8 s. All 18 relevant
perturbations still invalidate, while 7 false invalidations disappear (4 in the supplemented batch, 3 in the
undecided batch).

## Evidence of the problems before repair

- **H03 in production.** NRA completions `t1/complete-v2` (896 s) and `t6/complete-v1` (803 s) failed with
  "input file set changed" because another batch published disjoint claims mid-run, and both had to be re-run
  serially. Replayed exactly: in the reconstructed pre-publication tree (commit `1d112ff`, claim files taken
  from the run's own `INPUTS.json`, every pin matched), injecting `claude-2026-10-29-nira-t5.jsonl` mid-run
  reproduces the failure (`receipts/t6_base_inject.json`).
- **H01 in production.** The NRA report attributes about a quarter of the baseline batch's time, roughly 1.5M
  tokens, to stale-packet re-preparation after in-flight packets were committed. Every saved NRA packet now
  fails `load_packet` on main. One cause is a pure global counter: the tracked-package count went from 68 to
  91 (`package_scan.tracked_packages_loaded`).
- **H04.** The baseline t6 completion made 48 `load_packet` calls (16 members × 3, counting the supplement's
  internal decodes). They took 309 s of 506 s and read 9.08 GB.
- **New finding, the largest single cost.** `assemble.check_claim` calls `working_text.policy(claim, repo)`
  without an index, so every checked claim rebuilt the full fragment index (about 8 s). This happened in
  `apply`, `batch-check` and completion alike, so `apply` on 13 submitted claims spent about 120 s here. The
  audit had not identified it; it showed up as the remaining bottleneck after the first repairs.
- **H07 / current main.** On main, undecided preparation is blocked: compiled claim-kit outputs carry an older
  `build.py`/`excavate.py` fingerprint (`old_compiled_outputs:code_fingerprint`). For that reason the replays
  pin `1d112ff`, where outputs and code agree. The runner rebuilt claim-kit outputs on this branch
  automatically (see "Costs").

## Repairs (all within `jobs/valla`, `jobs/claim-kit`)

| Issue | Repair | Safety retained |
|---|---|---|
| H01 Valla context | `attach(repo, ids, exclude)` depends only on requested IDs. The packet's own folder is excluded, and so is its supplement parent when the agent is the same. Global package counters are removed from the packet context. | Relevant packages (any `@rationale` row for a member), canonical claims, attestations and method reviews for members, protocol pins, the premise library and `valla.py` still change the context. Unmaterialized tracked packages stay listed. |
| H02 ceiling | The global 100-package raise is replaced by per-query bounds: ≤100 relevant packages and ≤256 MB of sheet bytes scanned. The full index (Valla job) is bounded at 2000 packages. | Scanning is still bounded. The Valla job now succeeds on this branch with 91+ tracked packages (run 40946575823). |
| H03 disjoint completions | The start snapshot is kept. New canonical claim files are tolerated only if no line names a selected instrument, and they are receipted. A short O_EXCL lock (in the Git common directory, so it cannot be committed) spans the final recheck and the exclusive write. | Modified or deleted pre-existing files, same-instrument publications, unparseable additions, a target appearing mid-run, and every other pin and pattern still fail. A lock is removed only if its holder is a dead process on the same host. |
| H04 per-member reload | `Inputs.packet` verifies each packet once per (folder, PACKET sha256), then deep-copies member dossiers. Every packet is fully re-verified under the lock before writing. | This is stricter than before: the old code never re-verified a packet before publishing. |
| H05 fragment index | New `fragment_cache.py`: the index is reused in-process and persisted by content key (path, size and sha256 of every provider file, re-globbed each call). On a hit, every text-path existence and resolution is re-checked. An entry is stored only if it equals a genuine build. `policy_index()` lends the verified index to `working_text.policy` during apply, batch-check and complete. | `working_text.py` and `assemble.py` are byte-identical, because they are in the compiler fingerprint and changing them would force a corpus rebuild. Additions, deletions and same-size edits are tested. |
| H06 prior research | One directory walk with pruning. A one-pass regex is exactly equivalent to the old per-ID substring test (0 disagreements over 8,428 files × 4 ID sets). Completion-folder `TRACKER_CLAIMS.jsonl` union copies no longer bind. | Every other location still binds, including `CLAIMS.selected`, `CLAIMS.publishable` and receipts. Removing only the union-copy locations, the old and new outputs are equal on 3 real ID sets. Owner rulings stay universal pins. |
| H07 undecided | `prepare_evidence_many` / `validate_evidence_many` load and verify shards and authority tables once per batch. | Evidence is byte-identical to single-order freezing, and all reject conditions are kept (only which error comes first can differ). |

## Measurements on identical pinned inputs

Same machine. Both arms at commit `1d112ff`, with the NRA folder staged as untracked research as it was in
production. The base arm is that commit's code; the fix arm is the branch diff applied to it.

| Native step | Base | Repaired |
|---|---|---|
| prepare, 24 NRA orders | 18.9 s / 1.00 GB read | 2.9 s / 0.58 GB |
| source-supplement prepare (24) | 47.3 s / 2.25 GB | 18.9 s / 2.15 GB (cold cache) |
| view, supplemented packet | 28.6 s / 1.24 GB | 3.7 s / 1.10 GB |
| prepare, 4 undecided orders | 41.0 s / 3.16 GB | 8.7 s / 1.09 GB |
| view, undecided packet | 11.6 s / 1.02 GB | 2.0 s / 0.59 GB |
| apply, real t5 producer sheets (13 submitted) | 143.7 s / 4.46 GB | 8.8 s / 4.31 GB |
| batch-check with actual claim-checker | 158.8 s / 4.82 GB | 29.3 s / 4.67 GB |
| complete, real t6 manifest, no concurrent publication | 520.4 s, 16 published | n/a (see next row) |
| complete, real t6 manifest, t5 published mid-run | 506.2 s, 0 published (H03) | 122.2 s, 16 published |
| packet loads during that completion | 48 (309 s) | 6 (41 s, incl. the pre-publication recheck) |

Bytes read are `/proc/self/io` rchar for the whole process. The repaired figures still re-hash the full
provider inventory on every index use; that is deliberate, because the cache trusts content hashes, never
mtimes.

**Equivalence.** Repaired `apply` produced the same 13 claims as production's `t5/applied-v1`, with identical
outcomes and errors for all 24 members. The only field that differs is `claim_kit.dossier_sha256`, which moves
to the new packet's fingerprint, exactly remapped. The published t6 bytes match production's
`claude-2026-10-29-nira-t6.jsonl`.

**Safety matrix** (`mill.py`; one change at a time, reverted before the next; each verdict is the native
`kit.py view` result):

- **Unrelated changes that must leave packets valid.**
  - A tracked unrelated package; the packet's own sheets committed; 12 more packages beyond 100.
    Base invalidates all three in both batches; repaired keeps both batches valid.
  - An unrelated completion receipt folder. Base invalidates the supplemented batch; repaired keeps it valid.
  - An unrelated canonical claim file and an unrelated fragment provider. Both arms keep the packet valid.
- **Relevant changes that must invalidate.** These invalidate in both arms:
  - a relevant package
  - a new canonical claim for a member
  - a competing claim version
  - a review record
  - a held source byte edit
  - a new owner ruling
  - a protocol edit
  - a correction to a bound prior-research file
  - removal of a bound prior-research file
  - edited supplement declarations
  - a member's supplement source newly registered as a working text, which forces the cache rebuild
- **Neutral control.** An attestation for a member with no active claim is valid in both arms; Valla consults
  attestations only for active claims. The unit tests cover the active-claim case.
- **Completion controls.**
  - A competing publication of the same instruments mid-run is refused with 0 written and nothing overwritten
    (`receipts/t6_completionfix_sameid.json`).
  - A held-source change after selection, modified or deleted claim files, a held lock, and a target that
    appears mid-run are covered by unit tests.

## H13 replay (held later orders)

Regenerated isolated packets for EO 6254 and EO 6438 still contain no evidence record for EO 6730 or EO 6620-B.
Their chains are empty because those orders cite the code by name, not by number (`receipts/h13_replay.json`).
Declaring the two held American Presidency Project excerpts through the existing source-supplement interface
gives the following result:

- The packet contains `SUPPLEMENT:EO6730` and `SUPPLEMENT:EO6620B`.
- Their grade is `mirror_transcription`, with `acceptable_as_original: false` substituted from the registry,
  not chosen by the declarer.
- Both resolve through the assembler's ordinary reference route with no errors.

No missing consumption exists in claim-kit. The omission is a declaration the batch never made. Supplying it
is research work for the next NRA batch, together with the clause-level reading. The NRA auxiliary-command
rule was not touched.

## Tests

- **Local.** `jobs/claim-kit` passes 472 tests (1 opt-in skipped), up from 421. `jobs/valla` passes 36, up
  from 25.
- **New regression tests.** They cover:
  - Valla scoping, own-folder exclusion, relevant add/edit/delete, and the bounds
  - completion: snapshot reuse, recheck, disjoint and same-ID concurrent files, the lock (held, dead holder,
    Git common dir, conflicting target)
  - fragment-cache staleness, including a same-size edit and text-file appearance
  - prior-research equivalence and union-copy handling
  - many-ID versus single-ID undecided evidence
  - the scoped policy index, which equals a fresh index and never replaces an explicit one
- **Branch CI.** Results are recorded in the PR.

## Costs

| Context | Model | Tokens | Tool calls | Wall |
|---|---|---|---|---|
| Valla scope worker | Sonnet (`model=sonnet`) | 108,668 | 16 | 202 s |
| Completion worker | Sonnet | 127,611 | 23 | 264 s |
| Fragment index + undecided worker (redirected once: it had edited `working_text.py`, a compiler-fingerprint file) | Sonnet | 185,539 | 53 | 941 s |
| Prior-research worker | Sonnet | 107,702 | 16 | 359 s |
| Independent engineering review (fresh context, read-only) | Opus | 186,337 | 33 | 536 s |
| Coordinator: design, integration, replay harness, review fixes, the policy-index repair, this report | Opus | not exposed in this session | — | about 3.5 h |

Worker token counts are the harness totals. Cache-read versus write splits and cash cost are unavailable. The
review found no blocking defect. Its seven should-fix and minor items are fixed in `c26393eb78`: the lock
location, the agent-checked parent, Windows separators, the conflicting-target exception, receipt wording and
the duplicate hash. The note about union copies flipping mid-run is retained as a safe-direction false
invalidation.

**Unplanned compute.** Pushing claim-kit code made the runner run the `valla` and `claim-kit` jobs on this
branch (runs 40946575823 and the next push), which is a branch rebuild of claim-kit outputs. It was not started
deliberately, and the result commits are kept, not rewritten. It also means the branch's compiled outputs now
match current compiler code. Replay compute was about 2 CPU-hours locally.

## Limits and what remains

- **Re-versioning.** Every packet prepared before this change must be prepared again once, because `batch.py`,
  `valla.py`, `prior_research.py` and `source_supplement.py` are pinned code. Claims assembled from re-prepared
  packets differ only in `claim_kit.dossier_sha256`, but exact-version review still requires reviewers to
  re-attest them. Nothing here copies an attestation.
- **Cold cache.** A cold-cache process pays about 5 s extra once, to verify the stored entry against a genuine
  build. CI containers start cold.
- **Main is blocked for undecided preparation.** On current main this preparation fails until the claim-kit
  job runs with current compiler code. That job belongs to the runner, not to this branch.
- **Lock scope.** The lock serializes completions within one checkout and its linked worktrees, because it lives
  in the shared Git common directory. Separate clones are not serialized. When their publications meet in Git:
  - **Same filename:** an add/add conflict.
  - **Different filenames:** a silent clean merge in which the later filename wins. Phase 2 adds
    `kit.py publication-audit` to report that case at merge time; wiring it into CI is Sol's call.
- **Same-packet split.** Completing one packet's members in two separate completions makes the second see its
  packet-mates' new claims and refuse ("changed prior research"). Complete a packet in one run; use separate
  packets for parallel work.
- **Not done.**
  - H08–H12 belong to Sol.
  - The NRA auxiliary-command rule (H14) is not adjudicated.

## Phase 2: native full-code validation (2026-10-29, after the owner's follow-up)

- **Evidence gap closed.** Batch r1 (`research/excavator/opus-native-rehearsal-2026-10-29/REPORT.md`) ran the
  whole native path with the full repaired code in an isolated tree:
  - fresh prepare and supplements (including the held EO 6730 / 6620-B excerpts for H13);
  - a Sonnet producer and a blind Opus reviewer with a planted control, which was caught;
  - `apply`, `batch-check` and `complete`.

  Result: 5 claims eligible and published into the isolated tree, 2 blocks retained with reviewer-checked
  reasons, and no canonical write. An adoption dry run on the branch checkout reproduces the same publishable
  bytes.
- **Same inputs, both code arms.** The machine path from prepare through batch-check took 214.0 s on the
  baseline and 53.5 s repaired, with identical claims and outcomes. Completion took 60.8 s. The slowest
  remaining step is `cruden.py lookups` (113.6 s), NRA research tooling outside this assignment.
- **Model work** (harness totals; not comparable to NRA weighted totals):
  - producer: Sonnet, 111,493 tokens, 207 s;
  - reviewer: Opus, 130,996 tokens for the blind pass plus 54,881 for the reveal;
  - one-time selection screen: Sonnet, 123,374 tokens;
  - coordinator usage is not exposed.

  No token saving is claimed.
- **Retries and false invalidations.**
  - One refused completion, caused by the coordinator placing the blind review set outside the packet. It
    cost 27 s of machine time. The rule is now documented in `jobs/claim-kit/COMPLETION.md`.
  - The first t5/t6 concurrency run was contaminated by debris from earlier replays. The base
    `prior_research` bound a completion union copy (the H06 defect, which the branch fixes), and 13 members
    each re-verified the failed packet (347 s). Completion now verifies a failed packet once.
  - The clean rerun reproduced production's disjoint race with both batches published byte-identically.
- **New code.**
  - Failed packet verification is recorded once per completion.
  - `kit.py publication-audit --base <ref>` covers the separate-clone boundary.
  - 475 claim-kit tests.
- **Cache.** 16 real-tree perturbation states, including same-size edits with mtime restored and text-file
  existence flips, all equal a fresh index (`receipts/phase2/CACHE_CHECK.json`).
- **Input closure for Sol.** `INPUT_CLOSURE.md` / `.json`. Sol owns any declaration change.
- **CI.**
  - At 78eecc1, Road (Linux and Windows), Kean, the runner and the Valla bounded pilot all passed.
  - Automatic runner rebuilds on this branch:
    - 40946575823: 12.3 min.
    - 40949028950: 6.8 min.
    - 40952123524: 7.0 min, rejected as stale because a later push changed `research/**` inputs; this is the
      runner's freshness guard, not a failure.
    - 40952915668: 4.0 min, Kean.
  - Bot-authored result commits leave the PR head's workflows in `action_required` until a maintainer
    approves them.

## Combining with Sol's runner PR

- **Kean.** Both branches append to `jobs/kean/register/findings.jsonl` (this branch uses F-20261029-7001).
  Integrate by keeping both lines and regenerating `HANDOFF/KEAN.md`.
- **Narrowed checkout.** If Sol narrows what the runner materializes, the claim-kit and valla jobs still need
  `research/**` (prior research, packages, claims), `jobs/*/output/FRAGMENTS*.jsonl` and the referenced text
  files.
- **Cache location.** `fragment_cache` writes outside the repository (`~/.cache/eo-claim-kit`, or
  `CLAIM_KIT_CACHE_DIR`). A runner may point that at an Actions cache, but nothing requires it.
- **Lock and git.** `completion` resolves `git rev-parse --git-common-dir`. A sparse or shallow checkout is fine.
- **Freshness tests.** Re-run the freshness and runner tests together with `jobs/claim-kit` and `jobs/valla`
  after merging both.

## Reproduce

1. Make the isolated trees with `make_tree.py <dir> 1d112ff…`; stage NRA as in `stage_nra.py`.
2. Install an arm with `install_arm.py <tree> fix`.
3. Run `mill.py <tree> <label> out.json`, `native_path.py <tree> <supp packet> out.json --actual-checker`, and
   `replay_complete.py <tree> <manifest> <dest> --inject research/readiness/claims/claude-2026-10-29-nira-t5.jsonl --publish --out out.json`.

Helpers: `make_tree.py`, `stage_nra.py`, `replay_complete.py`, `stages.py` (per-stage timing of one packet load), `receipts/controls.sh`.
