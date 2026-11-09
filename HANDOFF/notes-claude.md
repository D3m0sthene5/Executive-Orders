## 2026-11-09 ET (Claude, Gutenberg wave: seven tool items and three waste patterns, PR #242)

- **Done (PR #242, stacks on #239):**
  - Bentham prices from `jobs/necker-costs/PRICES.json`; the old table ran 1.3x-1.9x high (Tribonian $673 -> $346); `bentham.py usage --reported-costs` cross-checks each session within max(1 cent, 1%).
  - Quo Warranto read audit (`AUDIT_READS`, report mode): claim-drafts had 8,367 undeclared reads and claim-checker 1; both now declared. Lachmann's FRAGMENTS reads declared.
  - Lachmann skipped-witness switch (`jobs/claim-kit/WORKING_TEXT_SWITCHES.json`, default void); recommendation `flag` restores 126 orders with a recheck flag.
  - Davy daily chain health (verdict in STATUS and the Kean brief); per-job `AS_OF_READOUT` for daily-digest and Davy.
  - Kean structured `measures` read by Bentham and Junto; Tsiolkovsky channel-weighted credit; Carnot coordinator kit with ready two-arm Junto tests.
- **Running:** child session `session_014fYW9tDCreZgtp1XP1tTpj` works the #185 Mabillon/Lachmann rule in its own PR.
- **Next:** after one clean report run on main, set the five `AUDIT_READS` files to enforce. Narrowing the wide globs soundly needs versioning by record kind or STATUS result (freshness change). Run the next wave with `jobs/carnot-coordinator/PROTOCOL.md` as the after arm of lean_coordination.
- **Asks:** @Owner: A-20261109-skipped-witness (set the switch to flag?).

## 2026-11-08 ET (Claude, Ariadne and Ockham: lean tree for CI and agents)

- **Done (branch `claude/ariadne-lean-tree`, PR to main):**
  - **Ariadne, shadow mode** (`.github/scripts/ariadne.py`). Traces each run-jobs job with strace on Linux and writes `oversized/runner-freshness/ariadne/<job>.json` (90-day download, never committed). Each record holds the job's closure, its required directories and its silent misses.
  - **Ockham, for agents.** Root `.ignore` for ripgrep tools; `.claude/settings.json` hook `ockham_lean_tree.py` refuses whole-tree listings; Lean-tree rule added to AGENTS.md and CLAUDE.md.
- **Why:** the materialize step costs 206-246s per station, even for a 7s job, because 103 of 106 jobs restore all of jobs/**. Main tracks 194,167 files, ~97% bulk. Kean: F-20261108-ariadne-checkout-cost, -ockham-agent-search, -ariadne-python-hooks.
- **Review:** an independent Sonnet reviewer (general-purpose subagent, 142,447 tokens, 5.8 min, same model family) found:
  - sudo jobs would fail under a non-root tracer;
  - detached git gc would keep strace alive;
  - no trace size cap;
  - parse time counted in STATUS timings;
  - hook bypasses.
  All are fixed and tested: sudo jobs are untraced, traced jobs get gc.auto=0, the trace streams through gzip with a cap, and the record is written after STATUS.json. Tests: test_ariadne 19, test_ockham_hook 6, test_rattle_watch 10.
- **Next:**
  - Read the first hosted records: closure size vs materialized, the overhead from `job_seconds` vs `last_untraced_success_seconds`, and any silent misses.
  - Then build the narrowing change: restore only a stable closure for an unchanged `narrow_signature`, with the trace as referee.
- **Valla certificate:** already stale on main before this PR. Both certificates match 11fd9f42e2, and 14 later in-scope commits changed the signature, so Valla runs on the fallback. The PR adds `ariadne.py` to `VALLA_CERTIFICATE_ROOTS` but does not re-certify; that needs an audit of those commits (F-20261109-valla-certificate-stale-on-main).
- **Merged with main's Quo Warranto and Rattle Watch changes (2026-11-09):**
  - Ariadne wraps the Quo Warranto command, so both run on `AUDIT_READS` jobs. Quo Warranto enforces declared reads for 5 Python jobs with an audit hook; Ariadne measures every job at syscall level for narrowing.
  - The runner now waits on `ariadne.py supervise`, not strace. A child shim records the job's own exit code, and leftovers are detached after 5s, so Rattle Watch's leftover cleanup behaves as it does untraced.
  - PR #245 also recomputes the Valla certificates; whichever PR merges second must recompute them.
- **Asks:** @Owner A-20261108-lean-main (pack or move bulk outputs out of main's tree; needed only to reach GitHub-API connectors).

## 2026-11-08 ET (Claude, Haloander follow-up: owner said yes to all four asks)

- **Done:**
  - Recorded the four decisions: `research/readiness/owner_rulings/2026-11-08-haloander-decisions.md`; Kean D-20261108-haloander-adopt, -board-rule, -undecided-measure, -photius-recheck. All four asks are answered.
  - Adopted the NO statuses of EO 12082, 7814 and 10733: ledger append, pinned `accepted_additions` entry, canonical `research/readiness/claims/claude-2026-11-08-haloander-ux.jsonl`. The actual checker passes all three. Population is now 4,301 decided.
  - Bentham now measures `filed_per_attempt.undecided` from a wave's `undecided_measure` (3/30). The undecided stratum ranks (#11, over budget), and the perpetual probe is gone.
- **Running:** claim-drafts and then claim-kit must rebuild for 4,301. Run each alone (`requeue_depth=1`); claim-kit reads committed drafts.
- **Next (owner-approved, not yet run):**
  - The remaining Photius-stale page check, by the h01 route.
  - A board pilot under D-20261108-board-rule on the 79 held reports.
  - Both need a new budget.
- **Asks:** @Owner: none.

## 2026-11-08 ET (Claude, Cujas wave: Photius-stale recheck c01-c03)

- **Done:** 68 of 75 Photius-stale orders were rechecked against their GPO printings and filed (`claude-2026-11-08-cujas-c0{1,2,3}.jsonl`, PR #224). All 6 controls were caught by both arms. Ready should reach about 1,091 after the tracker reruns.
  - Report: `research/excavator/claude-cujas-2026-11-08/REPORT.md`.
  - Kean: F-20261108-cujas-photius-recheck, -cujas-c02-c03, -board-fetch-not-run, -cujas-usage.
- **Cost:** about $39 of the $45 cap. The coordinator stopped at about 18:30Z.
- **Running:** a source-ladder run on main, dispatched for the 58 board-report requests. Verify its STATUS.json.
- **Next:**
  - 92 stale orders remain. Use `tools/carry.py`, which needs Tribonian sheets from `origin/claude/tribonian-state`, and the one-chain script pattern in COORDINATOR_LOG.
  - Prepare fresh after claim-kit rebuilds.
  - Add a `recovery.photius_stale` action to Bentham.
- **Asks:** @Owner: none.
## 2026-11-07 17:00 ET (Claude, Haloander: Bentham wave bentham-2026-11-07, $75 budget)

- **Done:** 25 lifecycle claims filed (`research/readiness/claims/claude-2026-11-07-haloander-h01.jsonl`, PR #222, count-changing). Tracker replay: ready 992 -> 1017.
  - Rank 8 recovery: 27 Photius-stale confirmations plus EO 12323, re-checked against the GPO printings, not re-frozen by script. 3 blocked: EO 8907, 12323, 8538.
  - Rank 7 probe (30 undecided): 0 canonical; 3 isolated overlay proposals (EO 12082, 7814, 10733) await adoption.
  - Rank 9: no paid work. 58 board-report fetches enqueued (FETCH_QUEUE 1120 -> 1178).
  - claim-kit unblocked on main: PR #219 (undeclared pinned input) and PR #221 (R9 alias in claim-drafts and claim-kit). It published at 938c1515a after three freshness refusals.
  - Report: `research/excavator/claude-haloander-2026-11-07/REPORT.md`.
- **Cost:** $61.78 API-equivalent measured (`telemetry/`): coordinator $44.45, 4 Sonnet producers $7.49, 5 Opus reviewers $9.84. Gate: h01 PILOT (28<30 attempts). The probe cannot be gated (unranked).
- **Controls:** 3 planted controls, all caught by both independent arms. No status, census or codebook change; certified 0.
- **Next:** the other ~166 Photius-193 orders are the cheapest ready gain (same h01 route; about $0.20/order in workers). After A-20261107-board-rule, a board pilot on the 79 held reports.
- **Asks:** @Owner: A-20261107-haloander-adopt, A-20261107-board-rule, A-20261107-undecided-measure, A-20261107-photius-193-recheck (existing).
- **Cautions:**
  - In a partial checkout (blob:limit), files over 1 MB are skip-worktree and the kit, Bentham and Kean read them as absent without error. Materialize with one batched `git checkout --pathspec-from-file`. Never let `jobs/_attempts` into the tree (8 GB).
  - Run claim-drafts before claim-kit, each alone with `requeue_depth=1`.
  - Completion receipts over 100 MB must be gzipped before pushing.

## 2026-11-07 02:00 ET (Claude as the Encyclopédie coordinator: adopting the Peiresc tool survey)

- **Done (all merged):**
  - Repository growth stopped at its two main sources:
    - Ptolemy is paused (`PAUSED`), measured at 0 bytes per run.
    - Failed-run receipts are trimmed ([PR #188](https://github.com/D3m0sthene5/Executive-Orders/pull/188)); they were
      about 740 MB on 2026-11-06.
  - Pergamon byte store ([PR #204](https://github.com/D3m0sthene5/Executive-Orders/pull/204)): GitHub Release assets
    now, R2 by config. 3,691 Ptolemy and Selden raw files (3.18 GB) migrated, each re-downloaded and hash-matched
    (`research/encyclopedie-campaign/storage/MIGRATION.md`).
  - Kean leases on branch `kean-leases`; `kit.py dispatch-check` honours them
    ([PR #189](https://github.com/D3m0sthene5/Executive-Orders/pull/189)).
  - New zero-token jobs:
    - Repetita, the LSA 1997-2026 ([#211](https://github.com/D3m0sthene5/Executive-Orders/pull/211));
    - Duodecim, U.S. Code Table IV 2009-2025 ([#214](https://github.com/D3m0sthene5/Executive-Orders/pull/214));
    - Youngstown, a CourtListener bulk citator ([#217](https://github.com/D3m0sthene5/Executive-Orders/pull/217)).
  - Research merged:
    - prior art, Thrower and Lowande-Poznansky, independently checked (#200, #202);
    - thesis measure (#201);
    - cross-family reviewer pilot (#205);
    - OCR pilot (#203);
    - Necker costs (#191) and Hollerith drivers and billing (#190);
    - free-source survey (#196);
    - certifier page (#195);
    - Zenodo design (#192);
    - Observable trial (#193).
  - Dashboard: every tab refreshed, plus a Trajectory tab
    ([#210](https://github.com/D3m0sthene5/Executive-Orders/pull/210)).
  - Report: `research/encyclopedie-campaign/REPORT.md`. Log: `LOG.md`.
- **Results to know:**
  - **Thesis measure:** 59 orders formally revoked after an evidenced earlier end, 34 of them verified on both sides
    (F-20261107-thesis-measure). In 59% of claimed revoked orders the revocation itself was the end.
  - **Cross-family review:** Codex caught 8 of 8 planted controls, Claude 17 of 22 (F-20261107-septuagint-xfamily).
  - **Pricing:** Bentham's price table is about 2x high (F-20261106-encyclopedie-necker).
  - **Size limit:** GitHub's 10 GB is a recommended limit; 9,776,627 KB on 2026-11-07.
- **Cautions for every session:**
  - Point release tags at `pergamon-store-root`, never at a commit with workflows. Path filters do not apply to tag
    pushes (F-20261107-pergamon-tag-triggers).
  - A job importing `jobs/_lib` must list it, and what it imports, in `triggers.txt`, or main's road tests go red.
  - Before merging a branch that ran jobs, bring it up to main and restore other jobs' outputs from main.
  - `fetch_pool` ignores robots.txt wildcards (F-20261107-robots-wildcards).
- **Asks:** @Owner: A-20261106-1, A-20261106-2, A-20261107-ocr-reference-rule, A-20261107-loc-hein, A-20261107-cap-mirror, A-20261107-tracker-thesis-fix, A-20261107-lowande-email, A-20261107-mountweazel-plants-leak, A-20261107-fetchpool-wildcards, A-20261107-courtlistener-robots, A-20261107-claimkit-court-fragments.
  - A-20261106-1 has a provisional answer recorded.
  - The rewrite plan for A-20261106-2 is `research/encyclopedie-campaign/storage/HISTORY_REWRITE_PLAN.md`.
- **Running:** nothing from this campaign. The new jobs' first runs on main regenerate their outputs. Youngstown
  re-streams 56 GB, about 2 hours.

## 2026-11-07 06:05 UTC (Claude as Hansard, progress refresh unstuck; ready 1,185 -> 992 explained)

- **Done:** [PR #212](https://github.com/D3m0sthene5/Executive-Orders/pull/212) (refreshes one at a time, latest wins)
  and [PR #216](https://github.com/D3m0sthene5/Executive-Orders/pull/216) (data-drifted reporting readouts publish as
  of their input commit, then catch up; refresh workflow only). Cancelled 13 overlapping refreshes. First generation
  since 2026-11-06 22:18: f6e5180880 at 05:23 UTC. Kean F-20261107-hansard-refresh-serialized.
- **Measured (f6e5180880 vs 6d4b5f6357):** Photius's evidence gains reproduced (NO_OFFICIAL_SOURCE_LOCATED 4,787 ->
  1,751; replica page checks 2,557 -> 10; compiled-only 2,762 -> 2,269; text step done 3,268 -> 3,516). Ready 1,185 ->
  992: all 193 lost are transcription-dependent EO 8032-9208 whose Lachmann confirmations gained Photius's GPO
  printing as a skipped witness, so their filed claims' frozen confirmations went stale. Kean
  F-20261107-ready-drop-193-photius-witness; owner question A-20261107-photius-193-recheck (page-check them against
  the new official printing rather than re-freeze).
- **Tsiolkovsky:** W 6,631 -> 6,781 h of 18,191 (37.3%); +207 h original text, -57 h on the three claim steps.
  Dashboard datasets refreshed (https://claude.ai/artifact/BZJxATqRtwrtBbuBy2UZpc). The 7-hour backlog landed in one
  generation, so per-campaign credit for it is split evenly and understates Photius.
- **Needs the owner (permission rules):** dropping two stashes in the session checkout and deleting 9 branches fully
  contained in main were refused by the session's safety check; commands are in the chat.

## 2026-11-07 (Claude, were Photius and Encyclopedie worth their cost)

- Priced Photius's 289 agents at Necker list prices: about $641 API-equivalent (opus $438, sonnet $104, an
  unlabelled family $99 priced as opus, so an upper bound), plan usage, $0 metered. About $0.21 per order that
  gained an official witness (NO_OFFICIAL_SOURCE_LOCATED 4,787 -> 1,751); ready unchanged at 1,185.
- Encyclopedie: $1,008.58 API-equivalent, $0 metered; infrastructure (repository growth stopped, reviewer-family
  gap, Bentham prices about 2x high), no order evidence.
- Kean F-20261107-photius-encyclopedie-worth. Photius's W gain still waits on a published tracker generation
  (none since 2026-11-06 22:18 UTC); the refresh-overlap decision is still the owner's (see the 2026-11-06 entries).

## 2026-11-06 23:30 ET (Claude as Photius, closing the originals hole for EO 1-7315)

- **Done (PRs, in merge order):**
  - [PR #187](https://github.com/D3m0sthene5/Executive-Orders/pull/187) merged, COUNT-CHANGING. Lane 1: twelve
    GPO bound volumes (HathiTrust, Google-digitized; PDFs private in `research/owner-inbox/hathi-gpo/`, hashes and
    text public). 3,679 orders located, 3,201 in 4306-7315; 554 Opus page checks (551 pass, 2 fail, 1 unsure).
    Kean F-20261106-photius-pr187-count-change.
  - [PR #194](https://github.com/D3m0sthene5/Executive-Orders/pull/194) merged, COUNT-CHANGING. Lane 4: 2,557
    ProQuest replicas read (Sonnet), fails/unsures and a 5% sample adjudicated on the images (Opus): 2,544 pass,
    8 fail, 5 unsure. Passes credit the text step as `archival_replica_checked` (P4, flag
    `REPLICA_CHECKED_PROQUEST_BYTES`); bytes stay ProQuest's. Kean F-20261106-photius-pr194-count-change.
  - [PR #197](https://github.com/D3m0sthene5/Executive-Orders/pull/197), COUNT-CHANGING, Lane 3: 28 free
    Internet Archive printings; 471 pages checked, 117 pass (Panama Canal 81, DOJ 18, NAL 14, Kappler 2, TWEA 2).
    Fuel Administration packets f011-f022 not run (P7). Kean F-20261106-photius-pr197-count-change.
  - [PR #198](https://github.com/D3m0sthene5/Executive-Orders/pull/198), COUNT-CHANGING, Lane 2: 37 CSC reports
    rescanned, 145 pages checked under R37: 6 pass, 129 fail (68 full text without a signature block), 10 unsure.
    Kean F-20261106-photius-pr198-count-change.
  - [PR #199](https://github.com/D3m0sthene5/Executive-Orders/pull/199), lanes 5 and 7: `HANDOFF/OWNER_TASKS.md`,
    Mabillon correction under R39 (`none` 1,535 -> 30), residual files, bentham usage, this note.
  - Rulings R37-R41 and delegated decisions P1-P7 are Kean decisions marked owner-delegated, reversible.
- **Tracker, before -> after all four lanes (local LF worktree on the same inputs; the GitHub run follows):**
  ready 1,185 -> 1,185; decided text step done 3,268 -> 3,516; NO_OFFICIAL_SOURCE_LOCATED 4,787 -> 1,751;
  ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK 2,557 -> 10; ONLY_COMPILED_TRANSCRIPTION_FOUND 2,762 -> 2,269;
  ORIGINAL_FOUND_NEEDS_PAGE_CHECK 535 -> 594 (leads); replacement obligations 1,146 -> 867. Certified count 0 -> 0.
- **Official witness by era (Mabillon frame, best route; before -> after).** Counted printing or checked replica:
  1862-1906: 0 -> 104 (4 printings, 100 checked replicas); 1907-1936: 0 -> 3,420 (1,578 printings, 1,842 checked
  replicas; 671 machine-located held printings before, unregistered); 1937-1989: 0 -> 112. Unchecked ProQuest
  replica 2,558 -> 11. `none` 1,535 -> 30; `microfilm_pending` (M1118) 0 -> 1,241.
- **Residual hole (`research/photius/RESIDUAL.md`):** 2,370 numbered orders with no text-step witness:
  1862-1906: 485; 1907-1925: 1,852; 1926-1936: 28; undated: 5. 86 HeinOnline volume blocks hold them
  (`HEIN_BLOCKS.csv`); the by-hand rules are in `HEIN_OWNER.md`. Public-domain closure waits for M1118.
- **Owner's list:** `HANDOFF/OWNER_TASKS.md` (NARA M1118 email and roll order, HathiTrust login downloads,
  HeinOnline checklist, drop folders under the git-ignored `research/owner-inbox/`).
- **Workers:** 150-plus Agent-tool workers (Opus for page checks and adjudication, Sonnet for replica reads), each
  in `research/photius/WORKERS.csv`; sanitized totals in `research/bentham/usage/photius/`. The twelve-worker
  limit was exceeded once (up to 16 concurrent) early in the wave; recorded here, not hidden. `claude -p` was
  not logged in, so workers ran through the Agent tool (P1).
- **Lane 6 (Kean F-20261106-photius-lane6):** the `Run jobs` dispatch (run 42311160709) recomputed the tracker on the
  runner with the same counts as the local run (ready 1,185; NO_OFFICIAL_SOURCE_LOCATED 1,751; needs-page-check 594;
  replica-needs-page-check cleared). Publish refused the whole station because claim-kit failed ("Draft summary
  population stale": claim-drafts ran before the tracker in the same station) and case-bundles failed (EO:11246 over
  its startup budget). Re-queued runs are on main; the tracker output on main is still the 22:18 generation until one
  passes. Run `readiness-tracker` alone first after a count-changing merge.
- **Found in passing:** main's Road system offline tests fail on their own:
  `jobs/peano-formulario/needs.txt` does not list `jobs/_lib/eo_identity.py` (Kean
  F-20261106-road-tests-red-on-main-peano). One line for the Formulario owner; Photius did not touch it (P6).
  "Halley" and "finish line iv" exist nowhere in the repository or the Kean register; not re-run.
- **Next:** the owner's three items above; when M1118 images arrive in `research/owner-inbox/m1118/`, hash, split
  and register them as `microfilm_witness`; index-date corrections for EO 28A, 2071, 2254, 2437, 2679, 2814,
  3069, 4923 (pages disagree with the index by days to a month); run packets f011-f022 only if a Fuel
  Administration order ever matters.
- **Do not:** touch heinonline.org or access.heinonline.com from any script, worker, fetcher or browser
  automation; move anything from `research/owner-inbox/` into the public repository; describe a checked replica
  or a Hein-dependent closure as public-domain custody; count a machine-located printing as authentication of the
  signed original or as a change to the certified count (0).

## 2026-11-06 17:20 ET (Claude, cleanup audit and Tsiolkovsky trajectory)

- **Counts audited:** at all 40 tracker generations on main, the ready count and census size match that
  generation's tracker summary.
- **Ready drop explained, 1,208 -> 1,185 (Kean F-20261106-ready-drop-26-mabillon-hash):**
  - +3 from Selden.
  - -26 from a Mabillon bug. `text_sha256` hashed the passage, not the file written (header + passage), so
    Lachmann now records a skipped witness, and 26 Tribonian claims fail `prior_confirmation_stale`.
  - The fix, [PR #185](https://github.com/D3m0sthene5/Executive-Orders/pull/185), is a DRAFT and COUNT-CHANGING.
    The broken hash also hides valid official printings from `official_copy_available_recheck_required`, so up to
    295 of the 1,185 ready (transcription-dependent) orders may need rechecking. Measure on the branch before
    merging.
- **Red refresh runs:** most are the freshness guard refusing results from overlapping, uncoordinated refresh
  runs, then re-queuing them. Publication itself is current. The overlap is deliberate (`test_writer_queue.py`
  forbids a concurrency group on `execute`). Serializing it is an owner decision.
- **Merged:** [PR #184](https://github.com/D3m0sthene5/Executive-Orders/pull/184), Formulario. Its first runner
  build proved 22,727 lemmas. Brave works on the runner, so A-20261106-formulario-brave is withdrawn.
- **New:** `jobs/tsiolkovsky-trajectory/` and the Tsiolkovsky Trajectory dashboard
  (https://claude.ai/artifact/BZJxATqRtwrtBbuBy2UZpc). Verified work held: 4,108 -> 6,631 of 18,191 work-hours
  (36.5%); every change is credited by input channel. Kean F-20261106-tsiolkovsky.
- **Still blocked:** deleting the 215 merged branches (the list with tips is in
  `research/dorotheus/cleanup/BRANCHES_TO_DELETE.txt`).

## 2026-11-06 16:30 ET (Claude, Formulario: a checked lemma library of lifecycle facts and the documents that prove them)

- **Done:** new job `jobs/peano-formulario/`, named for Peano's *Formulario mathematico*, the ancestor of Lean's
  mathlib.
  - **The library.** Lifecycle facts become small named lemmas with proof terms. The kernel marks a lemma
    `proved` only when its exact words are found in retained bytes, or in a re-fetchable official copy whose hash
    is recorded; the words must sit in the right record and name the other instrument. Everything else is `sorry`,
    with a reason.
  - **Local build:** 23,899 lemmas, 22,728 proved; 3,097 orders have a proved end lemma.
    - 22,697 of the proved lemmas are later-events edges. The seven Federal Register API pages behind about 15,900
      disposition notes are now retained, so those notes are checkable offline.
    - 31 of 41 axioms are proved, and all are general theorems: war and emergency terminations, Philippine
      independence, reorganization plans, FLPMA, Youngstown, Schechter and others.
  - **Size:** 27 MB retained (files up to 3 MB); lemma shards 3.4 MB.
  - **Use:** `formulario.py exact EO:N --goal end` answers the "what closes this?" question;
    `formulario.py supplement <id>` prints a claim-kit source-excerpt entry. Its `SOURCES.jsonl` makes every
    retained document checkable by claim-checker with no code change.
  - **Axiom sweep:** 8 sonnet researchers and 1 opus critic; 857,679 subagent tokens; 610 s; 127 tool uses.
    - 59 candidates proposed; the critic dropped 18 and recoded or annotated 13.
    - 15 missing instruments kept as open goals in `catalog/WANTED.jsonl`.
    - 27 bulk sources catalogued.
  - Kean F-20261106-formulario.
- **Asks:** Kean A-20261106-formulario-brave. `BRAVE_SEARCH_KEY` works, but `jobs/_lib/fetch_pool.py` refuses
  Brave's API host under robots.txt. The free engines were throttled or robots-blocked, so the search tactic
  proved none of the 10 `sorry` axioms.
- **Not done:**
  - Adapters for the Selden, current-law, Theophilus and Shepard edges.
  - `bentham.py usage` failed on the workflow transcripts ("malformed supported transcript export"), so this
    wave's usage is recorded here and in Kean only.
- **Do not:** read a `proved` lemma as a legal finding. Whether a class lemma reaches a particular order is
  legal judgment; `exact` lists class lemmas only as candidates.

## 2026-11-06 15:00 ET (Claude, Dagron: daily acquisition manifests for outside collections; NYU Film 709 first)

- **Done:** new job `jobs/dagron-collection-manifest/`. It runs daily, and after the tracker, Domesday and Lewis.
  - One spec per collection: `collections/nyu-film709.json` (11 reels, EO 1-7403; HeinOnline 1845-1936).
  - Output per collection: a gzipped JSONL and CSV manifest, plus a summary, a report and a sample.
  - First build at main `0deba1dd4`: 6,010 rows, as follows.
    - Group 1: 5,875 orders in range with no accepted original witness (P1 2,196, P2 1,435, P3 2,244).
    - Group 2: 0 (original counted but no working text).
    - Group 3: 81 unnumbered, ambiguous or untracked candidates.
    - Group 4: 54 orders numbered above 7403 and dated 1936.
  - `record_acquisition.py` stages downloaded images, with provenance, in `research/acquisitions/<collection>/`.
    Only Dagron reads that folder, to mark orders as staged.
  - The first build's report and reconciliation are in `research/dagron/README.md`. The earlier 5,305/4,954
    figures are not in the repository; the closest current measure is the open original-text step, 5,322
    (4,926 dated pre-1933).
  - Kean: F-20261106-dagron-nyu-manifest, F-20261106-dagron-job.
- **Asks:** Kean A-20261106-dagron-nyu. The 2026-10-19 owner rule ("do not plan around the reel set") must be lifted
  before anyone requests or scans the reels. Hein retrieval stays item by item.
- **Do not:** put a microfilm or Hein image into `research/stage21/original_sources/`. The tracker would count it as
  an original. Stage it with the helper instead.

## 2026-11-06 13:10 ET (Claude, cleanup at the owner's request: every open PR merged, branches sorted)

- **Merged:** [PR #167](https://github.com/D3m0sthene5/Executive-Orders/pull/167) (Selden; +8 claims, ready up by at most 8 once checked; Kean F-20261106-merge-167-selden) and [PR #162](https://github.com/D3m0sthene5/Executive-Orders/pull/162) (Pothier family doctrines; leads and asks only, no claim or status change; Kean F-20261106-merge-162-pothier). Each branch first merged main; Kean lines were united and main's outputs restored for jobs that already exist on main. New jobs (selden-*, pothier) kept their branch-run outputs, which the output-branch check flags; main's own runs regenerate them. No open PRs remain.
- **Notes conflict:** the Pothier 01:30 entry is now in time order between Justinian (05:10) and Gratian (00:45).
- **Stale run cancelled:** 39316948571 (csc-annual-reports, queued since Oct 19).
- **Post-merge chain:** "Refresh published progress" started by itself on main (runs 42265936367, 42267267276); it measures the Selden +8.
- **Branches: 215 of 219 are merged or add nothing over main, but deletion was NOT done.** The session's permission check refused the bulk remote delete; the owner can run it. The list with tip SHAs (for restore) is in `research/dorotheus/cleanup/BRANCHES_TO_DELETE.txt`. Kept on purpose: `claude/justinian-denominator` (DENOMINATOR_DELTA.md cites its `e3/DATE_FIXES.csv`), and three closed-unmerged PRs by other agents with unique content: `astra/unfinished-docket-source-trial` (#146), `codex/machiavelli-modern-undecided-20261105` (#151), `sol/babbage-complete-effort` (#141).
- Certified: 0. No codebook, census or ProQuest path touched.

## 2026-11-06 07:10 ET (Claude, Dorotheus: Justinian repairs merged, protected stratum worked)

- **Done (all merged by Dorotheus under the owner's delegation):**
  - Justinian PRs #171, #179, #168, #169, #172, #175, #177, #178, #170, #173.
  - COUNT-CHANGING #180 (B1): census 14,972 -> 14,998.
  - COUNT-CHANGING #174 (C3): ready 1,368 -> 1,196.
  - #181 (B2): catalogued_unnumbered class and two denominators.
  - COUNT-CHANGING #182 (C/D): ready 1,196 -> 1,208; provisional statuses 4,291 -> 4,298.
  - #176 closed as superseded by #180/#181.
  - Freeze posted 09:50 UTC and lifted 11:05 UTC, after one chain published at `dd216474b`: 1,368 ready, generation `42204685627-1:8ee77553...`, the same id in the tracker's SUMMARY and STATUS. That is the first authoritative post-repair figure.
  - Each count-changing merge's before/after is in Kean: F-20261106-dorotheus-merge-180, -174, -182.
- **Sample estimate** (`research/dorotheus/SAMPLE_ESTIMATE.md`; provisional, AI-reviewed, uncertified, n=120):
  - Response: only 19 of 120 orders responded (12 ready, 7 filed).
  - Operative force on 2026-10-14, responses only (MAR): **0.0%, Korn-Graubard 95% 0.0-17.6%**.
  - Producers' assessment of 69 orders: 5.3% (1.2-14.2%).
  - Bounds: all nonresponse NO gives 0.0%; all nonresponse YES gives 79.7%.
  - Formal validity (unrevoked) among responses: 0% (0-26.5%, 12 respondents).
  - formal_revocation_after_earlier_cessation is true for 1 of 19 NO responses.
  - Reviewer plants caught: 25/30.
  - YES probe: 7/30, now Bentham's rate for yes.fr.
- **Owner-delegated decisions** (Kean D-20261106-dorotheus-r7 to -r18, each "owner-delegated, reversible" where the prompt did not decide it):
  - R14: the Bacon run is closed as unrecoverable; there was no bundle to adopt.
  - R9: 4 Niebuhr orders with no held official page were not admitted.
  - R9: EO:7933a is read through an alias map, because the ledger is hash-pinned.
  - Asks closed: A-20261103-1, A-20261104-1, A-20261105-niebuhr-admit, A-20261106-mabillon-register and A-20261106-justinian-{freeze, r3-scope, e1e3, e4, astra, dedup}. No ask is open.
- **Running:** dispatch of claim-drafts, claim-kit, claim-checker, readiness-tracker, domesday-register, daily-digest and bentham with requeue_depth 1, so main publishes the post-merge figures (expected 1,208 ready of 14,998 orders and 4,298 statuses).
- **Next:**
  - Let the claim-kit undecided route accept a held transcription as working text (2026-10-21 ruling), then re-run the 28 undecided sample orders blocked only by that. They are the `blocked` rows of `research/excavator/dorotheus-sample-2026-11-06/DISPOSITION.csv` whose blocker names the original requirement.
  - Request bytes from Ptolemy for the 38 dispatch-blocked orders (custody_record_only).
  - Re-run `research/dorotheus/estimate.py`.
  - Cut producer context: 1.38M tokens per attempted order against a 150k target; try one order per producer with a pre-cut view.
  - E1 (a hosted readiness-tracker diagnostic with narrowed materialization and a byte-for-byte comparison) and E2 (freshness refusals in the first three post-freeze runs) were not reached.
  - DASHBOARD.md shows the tracker generation time and input commit but not the generation id itself.
- **Do not:**
  - Edit `research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv` keys for EO:7933a; it is hash-pinned, so add aliases instead.
  - Re-tag the 192 named revocations of in-force orders (R8).
  - Treat the sample estimate as more than a 19-response reading.

## 2026-11-06 06:10 ET (Claude, Selden: texts of the later instruments that act on an order)

- **Done:** branch `claude/selden-acting-instruments`, PR [#167](https://github.com/D3m0sthene5/Executive-Orders/pull/167). It is COUNT-CHANGING, so it waits for the owner; do not merge it during the freeze.
  - Census in `research/selden/census/`: 16,322 leads, 2,401 named instruments not held.
  - Three zero-token jobs, verified on Actions: `selden-fr-citers` (FR full text from 1994, 13,138 orders), `selden-fr-acting` (1936-93 FR pages, 803 issues matching GPO's PREMIS) and `selden-statutes` (2,179 Statutes at Large).
  - The locator is measured: 77% recall, and 0 of 21,940 planted negatives located.
- **Result:**
  - 818 of 1,015 unheld non-order instruments are now held.
  - Proof: 8 of 30 random decided orders filed after two-arm blind review, 3 of them decided by Selden texts. All 5 planted controls were caught.
  - Most remaining blocks need a current-source grade, a fact date or an owner ruling, not a text (`research/selden/REPORT.md`, F-20261106-1).
- **Next:**
  - Fix EO 8116 (Proclamation 2416 is held) and refile.
  - Mabillon: take `research/selden/ACTING_EO_TEXTS_NEEDED.csv`.
  - Gratian: add `selden-fr-acting` to `later-events/after.txt` after the merge.
- **Asks:** @Owner: A-20261106-1 (statute ending a body without naming the order); merge #167 or decide.
- **Do not:**
  - Re-run `selden-fr-acting` for a cosmetic change. It downloads about 20 GB; `gpo_premis_result` is a known misleading field, so use `gpo_premis_match`.
  - Put retries of one order into overlapping proof batches.

## 2026-11-06 05:10 ET (Claude, Justinian: repair wave A-F)

- **Done:**
  - Merge on green (no count change): [#168](https://github.com/D3m0sthene5/Executive-Orders/pull/168) A2 freshness scopes; [#169](https://github.com/D3m0sthene5/Executive-Orders/pull/169) A3 generation id; [#170](https://github.com/D3m0sthene5/Executive-Orders/pull/170) A4 branch-output check; [#171](https://github.com/D3m0sthene5/Executive-Orders/pull/171) B1/B2 NEWEST.md and the 16 KB brief; [#172](https://github.com/D3m0sthene5/Executive-Orders/pull/172) B4 daily rule; [#175](https://github.com/D3m0sthene5/Executive-Orders/pull/175) C4 estimand; [#177](https://github.com/D3m0sthene5/Executive-Orders/pull/177) B5/F1/F4; [#178](https://github.com/D3m0sthene5/Executive-Orders/pull/178) B6 Bentham; this PR (Kean records, usage, notes; stacked on #171).
  - For the owner or the coordinator to merge: [#173](https://github.com/D3m0sthene5/Executive-Orders/pull/173) C1/C2, schema v2 and contests. Count-neutral, proven by a like-for-like tracker run: 1,384 ready, 0 rows changed.
  - Draft, COUNT-CHANGING: [#174](https://github.com/D3m0sthene5/Executive-Orders/pull/174) C3 re-tag. 184 claims; ready 1,384 -> 1,208.
  - Draft, prepared only: [#176](https://github.com/D3m0sthene5/Executive-Orders/pull/176) E1-E4 denominator lists.
  - All open; nothing merged by me.
- **Results:**
  - A1: nothing was queued on main; Arsenale (#166) had already cleared the queue.
  - A2: claim-checker's stale set falls 76%, but the two discarded runs mostly saw real input changes, so the prompt's "would have published" check is false.
  - A3: 1,331 -> 1,309 came from 22 working-text policy failures. The two commit ids in the prompt do not exist.
  - #164 was merged at 08:45 UTC, before I reached F2. I left a comment on it.
  - Workers: 5 Sonnet runs ($3.55 in total); usage in `research/justinian/WORKERS.csv`. Session usage: `research/bentham/usage/justinian/` (Opus coordinator about $48, Sonnet about $6, API-equivalent).
- **Running:** nothing dispatched. The pushes to #168, #169 and #170 start their branch runs.
- **Not reached, with reasons:**
  - B3 (narrow materialization): needs hosted diagnostic runs to prove byte-identical outputs.
  - D1 and D2 (the protected sample and the YES probe): a two-stage claim-kit wave of about 150 orders needs its own session. The sample today has 12 orders ready, 16 decided but not ready, and 92 undecided.
  - E4 identity class and two denominators: an owner ruling first.
  - A5: the owner is absent, so the freeze ask is recorded.
- **Next:**
  - Merge #168-#172, #175, #177, #178 on green.
  - Owner decides #173, then #174.
  - Run D1 as one named wave before any other production (R4), then the 30-order undecided probe that Bentham now ranks #7.
  - Trace the tracker, claim-kit and Bentham as claim-checker was traced, and give each a `references.txt`.
- **Asks:**
  - @Owner: A-20261106-justinian-freeze, A-20261106-justinian-r3-scope, A-20261106-justinian-e1e3, A-20261106-justinian-e4, A-20261106-justinian-astra, A-20261106-justinian-dedup. Still open: A-20261106-mabillon-register.
  - @Coordinator: merge #173 only after the owner reads its contest and v2 rules. #174 is stacked on #173.
- **Do not:**
  - Re-tag the 192 cleanup-actor claims in `research/justinian/c3/NOT_RETAGGED.csv` without the owner's answer to A-20261106-justinian-r3-scope.
  - Merge any `jobs/*/output` that a branch run produced; #170 enforces this.

## 2026-11-06 01:30 ET: Pothier, family doctrines for the 5,918 undecided orders with no dated history (night wave)

- **Done:** eleven source-grounded family doctrines (`research/pothier/doctrines/`), coordinator rulings P1-P8 (`research/pothier/COORDINATOR_RULINGS.md`), and the zero-token job `jobs/pothier` (member table, doctrine engine, tests, bounded class-wide source fetch). Report: `research/pothier/REPORT.md`. PR #162 changes no status, codebook, census or count.
- **Result:** doctrines cover 5,834 members and decide 2,139 status leads (2,088 `no`, 51 `yes`); 3,695 stay `open` with stated reasons. Two blind Opus reviews per doctrine caught 44 of 44 planted errors; a blind 30-member pilot per doctrine caught 22 of 22 controls and found 1 wrong status in 129 decided leads (fixed; 95% upper bound 4.2%) and 10 of 201 open leads decidable. About 15M Opus subagent tokens, 4 h. Kean F-20261106-pothier plus one finding per family. Certified 0.
- **Next:** after #162 merges, the runner fetches the 128 class-wide sources (`fetch.py`); mark them held in the doctrines and rerun. Selden takes the 237 per-order acting instruments in `research/pothier/FOR_SELDEN.csv` (mostly Public Land Order texts). Biggest unlocks: BLM MLRS withdrawal cases, the Forest Service chronology, plat filing dates. After the owner answers, propose Jacquard-style sampled adoption of each family's `no` leads.
- **Asks:** @Owner: A-20261106-pothier (adopt each family doctrine, yes/no per family; are amending orders spent on issue or alive with their text, 601 leads; may `no` leads rest on BLM's PLO tables, about 400 leads; listed in REPORT.md). @Coordinator: research/pothier/QUESTIONS.md Q4-Q5 (the Kean brief is at 8,181 of 8,192 bytes).
- **Do not:** treat a lead as a status or write it into a status field.

## 2026-11-06 00:45 ET (Claude, Gratian: wiring tonight's products into the tracker and the claim kit)

- **Done:** branch `claude/gratian-wiring` (not pushed; see Asks). `48da66f7`: `source_supplement.py` now adds held excerpts to undecided dossiers by sealing a new copy of their frozen status-overlay evidence; status gates are unchanged, and `batch.py`'s codec pin changes. `fd403d5b`: new job `gratian-niebuhr-leads` types Niebuhr's results as date leads that `eo_identity.load_dates` reads last; 56 numbered orders gain a routable date for Lewis. `ed397bda`: later-events `job.py` adds `selden-fr-acting` texts without touching the kit-pinned `later_events.py`. `c32a59a2`: `research/gratian/` holds CONCORDANCE, IMPACT (tracker ablation on `b561d57a`) and the NEXT_DOSSIER queue. Kean F-20261106-gratian-wiring and F-20261106-gratian-ablation.
- **Result:** no product moves an order to ready (1,323 in every variant), because ready also needs a checked claim. With #164, Mabillon adds 58 orders to the claim-ready group and reopens 17 provisional texts. Lachmann adds 161 text steps. Ptolemy should make EO 10926 ready at the next claim-checker run. No `tracker.py` change and no COUNT-CHANGING PR from this lane.
- **Next:** push the bundle and open the wiring PR; once Selden's jobs merge, add `selden-fr-acting` to `later-events/after.txt`; add `mabillon-held-printings` to `text_jobs.py` once its SOURCES carry `text_path` (QUESTIONS Q6).
- **Asks:** @Owner: A-20261106-gratian-push. @Coordinator: `research/gratian/QUESTIONS.md` Q2 (put the 17 reopened texts in #164's description) and Q5 (re-prepare packets after merge).
- **Do not:** prepare claim-kit packets from `main` and apply them on this branch, or the reverse; the batch codec pin differs.

## 2026-11-06 00:45 ET: Mabillon, bulk sources of official originals (night wave)

- **Done:** `research/mabillon/REPORT.md` and `COVERAGE.md` (frame of 5,943 orders with NO_OFFICIAL_SOURCE_LOCATED; it reproduces Herschel's 5,313 and 1,234). There are three new zero-token jobs with tests and verified runs on the branch:
  - `mabillon-held-printings` (DAILY, offline): 1,771 official printings `hathi-gpo-orders` already held (saved passages plus its committed Commons GPO page dumps), proved by text: 762 frame orders, 1,009 replacing transcriptions, 393 of Selden's acting orders. Controls: 86 of 88 positives, 0 of 6,834 negatives accepted.
  - `mabillon-nara`: NARA's keyless S3 catalog export shows RG 11 signed originals are not online (27 imaged items). The owner chose ProQuest and no paid reproductions (D-20261105-proquest-not-nara).
  - `mabillon-scan-inventory`: no public numbered GPO volume below EO 5800.
  - Kean: F-20261106-mabillon-nara, -held, -volumes, -neighbours.
- **PRs:** #163 (no count change). #164 is COUNT-CHANGING: it registers held printings with the tracker; merge after #163. A-20261106-mabillon-register.
- **Next:** 1,535 frame orders have no route to an official image. Their route is ProQuest downloads by phrase search (1,520 are not on the owner's link list), each needing a page check. 120 frame orders lie in GPO volume ranges without a located passage (OCR damage, or volume 8032-9003 not yet downloaded).
- **Asks:** @Owner: none new in this note; the open Kean ask is A-20261106-mabillon-register, relayed through PR #164. @Claude (coordinator): port the segment and neighbour-margin rules into Tischendorf (`jobs/mabillon-held-printings/README.md`).
- **Do not:** register `mabillon-nara` or `mabillon-scan-inventory` with the tracker; they are metadata only.

## 2026-11-05 (Claude, PR cleanup and salvage of frozen runs)

- **Merged** PRs 154 (Tischendorf plus tracker registration), 155 (current-law sources), 156 (Theophilus and ice-core claims) and 157 (Herschel), after resolving conflicts: runner outputs from main (rebuilt on the next run), Kean register united by exact line, two duplicate finding ids renamed (`F-20261105-tischendorf-1`, `-2`), missing `triggers.txt` library declarations added for `theophilus-sources` and `tischendorf-originals`.
- **Salvaged** the frozen ChatGPT draft runs, PRs 141 (Sol), 146 (Astra) and 151 (Codex), in PR 158: research folders kept in place; retained sources, 176 fetch-queue rows, page-reviewed job data and code patches archived inertly under `research/salvage/frozen-drafts-2026-11-05/` (README has promotion steps). The three PRs are closed; branches remain. Their ChatGPT chats would not load in the owner's Chrome. Kean F-20261105-pr-cleanup-salvage.
- **Next:** promote the salvaged retained sources through `astra-source-retention` `retained_path` imports (top Herschel blocker); then the Herschel fixes (overlay write rule, machine later-source searches). Owner asks A-20261105-1 and A-20261105-2 stay open.

## 2026-11-05 (Claude, Herschel: measured cost of all remaining work)

- **Survey:** census of all 96,598 open order-steps plus two independent samples (153 + 85 orders), each run end to end by six Opus coordinators (H1-H6) and 195 workers with blind planted-control review. About $350 API-equivalent, 90 min. Report: `research/herschel/REPORT.md`; numbers: `research/herschel/ATLAS/`. Kean F-20261105-herschel-survey.
- **Result:** attempting every open step on current holdings would cost $21,200 (80%: $18,900-23,600; the rounds agree at $20,500 and $22,300) and carry about 760 orders through every step. Most steps block on missing sources within minutes. Fully successful orders cost $3.92 each (n=15). Human certification is the largest cost: about 50 min per dossier (Opus estimate, n=6), about 12,400 h overall.
- **Blockers to fix before any wave (zero or few tokens):** retain bytes of hash-only sources (2,867 orders touched; `astra-source-retention`); the claim-kit overlay write rule (545 orders, sole blocker); machine later-source searches for undecided dossiers (738 sole); a pre-1937 disposition source for the 5,918 undecided orders without a dated history (candidate: WPA Historical Records Survey list of EOs 1-8030, 1944, unchecked).
- **Filed:** 7 claims (`research/readiness/claims/claude-2026-11-05-herschel-*.jsonl`); status proposals stay proposals in `research/herschel/H*/`. 0 planted-control misses. Certified 0.
- **Limits:** no API limits; one 8 GB session caps at about 18 workers (OOM kills before the shared guard). More parallelism needs more machines.
- **@Owner:** A-20261105-1 (may the kit start an undecided order with an explicit empty history?), A-20261105-2 (weekly usage % after the run, for `bentham.py calibrate`). PRs #154, #155, #156 and the Herschel PR await merge. A-20261103-1 and A-20261104-1 remain open.

## 2026-11-05 (Claude, Theophilus wave: Bentham ranks 8 and 11)

- **Filed 41 reviewed claims** (`research/readiness/claims/claude-2026-11-05-theophilus-{r01,r02,r03}.jsonl`) from the 48 custody-stranded 2026-11-04 claims, plus 1 owner-reviewable replacement proposal (EO 12743, `research/excavator/claude-theophilus-2026-11-05/p01/REPLACEMENT_PROPOSAL.jsonl`). Each filing passed the actual checker and two fresh Opus blind arms; 4 of 4 controls caught by both arms. Certified 0. Kean F-20261105-theophilus.
- **Method:** the actual checker ran offline on the 48 exact reviewed lines (from `claude/tribonian-state`) before any model: 32 clean, 12 hidden `too_short_to_verify` quotes, 4 OCR or text-registration failures. The clean 32 were reapplied unchanged (dossier fingerprints equal) and reviewed fresh; the other 16 went to a Sonnet correction producer.
- **Not filed:** EO 13900, 13965 (both arms: "section 5(d)" not in the held texts); EO 14012 (sec. 6 revocation exhausted on issuance); EO 8341, 8613, 8639 (OCR order-number tokens in the only ending source); EO 10570 and (rank 11) EO 10494 (the recheck text is not registered for the FR hash, a checker or fr-originals fix); EO 9789 (EO 9818 OCR garbles; audit still open).
- **Rank 11:** 2 of 43 were closable from held bytes. The other 41 are recorded in `BLOCKED_RANK11.json` with first steps. Next: one bounded retention run over the 15 hash-only ladder finds in `RETENTION_CANDIDATES.json` (statutes, reorganization plans, PEB reports), then a correction batch for those orders.
- **Gate:** CONTINUE, then PILOT. $73.46 API-equivalent (`sessions.py`; coordination $40.16). Workers ran as headless `claude -p` sessions (`tools/launch.sh`).
- **@Owner:** adopt or reject the EO 12743 replacement proposal (its canonical filename would be shadowed by `claude-lambertini-iv01-2026-10-20.jsonl`). A-20261103-1 and A-20261104-1 remain open.
- **Error:** disk cleanup deleted r02 `complete-v1`'s bulky receipts. TALLY, EXCEPTIONS, PUBLICATION and the log survive, and the claims file's hash matches.

## 2026-11-05 (Claude, ice core probe of the remaining claim-ready orders)

- **Sampled:** 30 orders by decade from each remaining claim-ready stratum (886 NO, 359 YES), one batch each, no substitutions; Sonnet producers, two independent blind Opus reviewers with planted controls, filed only when both upheld. Report: `research/excavator/claude-icecore-2026-11-05/REPORT.md`; Kean F-20261105-icecore.
- **Filed 12** (`research/readiness/claims/claude-2026-11-05-icecore-{no,yes}.jsonl`): NO 1 of 30, YES 11 of 30. Controls 2 of 2 caught by both arms. Certified 0.
- **NO stratum is mostly unworkable as drafted:** 25 of 26 assigned orders lack a held ending source (unrevoked land withdrawals, First War Powers Act and IRC return-inspection expiry texts, report-dated boards). Tribonian's 47.6% came from orders it had already drawn off the top of the stratum.
- **YES works on the `original_plus_bounded_search` route.** Blocks: NEA continuation notices (EO 12957, 13553, 13611), later orders held only as mirrors (EO 13286, 11051, 11610), PLO 326, current 33 CFR Part 6. Three upheld claims (EO 12019, 12293, 12748) failed completion on custody-only later-event sources; seven sampled originals are custody-only (listed in the report).
- **Bentham:** `measure.py` now pools waves that opt in (`pool_into_rates`) and takes a stratum's rate from a sample of the remaining orders (`sample_of_remaining`, at least 30 attempts). NO falls to 5.2 dossiers per $100 (rank 13) and YES enters at 56.7 (rank 10). Gate STOP. Cost $59.25 API-equivalent, from `sessions.py`.
- **Next:** do not run the NO wave; retain the custody-only bytes named in the report (10 sampled orders); acquire the NEA notices (Theophilus sources job) and register official FR texts for mirror-only later orders; screen producer-added later-event sources for custody before review.
- **@Owner:** EO 9717, 9555 and 13472 have incomplete Astra claims and need an owner route or a replacement proposal. A-20261103-1 and A-20261104-1 remain open.

## 2026-11-05 (Claude, Gessner cards: one card per executive order)

- **Built** `jobs/gessner-cards/`: joins `readiness-tracker/output/READINESS_BY_ORDER.csv` with `domesday-register/output/REGISTER.csv` into `output/CARDS.html`, a self-contained page with one card per order (number, date, president, title, provisional status, segmented step bar, ready flag; detail panel with blockers in plain English, best document held, transcription-replacement obligation), pipeline counts, and a per-president mosaic. Runs `DAILY` and after both inputs (`after.txt`); tests first. Owner's copy: https://claude.ai/artifact/3dFdZuMP4Yg5cTVbe9VYhS (private until shared). Kean F-20261105-1.
- **Totals match the tracker run of 2026-11-05 12:04 UTC exactly:** 1,331 ready of 14,972; 4,291 with status; 43 one step from ready; 0 certified. No count is changed or re-measured.
- **Register data-quality leads:** the register names no president for 5,045 orders; the page derives 4,933 from dates (marked as derived). The date rule disagrees with the register on 2 of 9,889 checkable rows: EO 8969 (1946-12-11, credited to Franklin D. Roosevelt) and EO 10276 (1961-07-31, credited to Harry S. Truman). Not corrected here.
- **Next:** the owner's artifact copy is static; republishing it from `output/CARDS.html` after a tracker run refreshes it. Branch `claude/gessner-cards`.

## 2026-11-04 (Claude, Tribonian wave, PR 131-137 integration, Lind trial)

- **Filed 547 reviewed lifecycle claims** (`research/readiness/claims/claude-2026-11-04-tribonian-*.jsonl`): 492 new dossiers and 53 corrections from the drained wave, plus 2 from dispatch-checked o27. All 53 planted controls were caught; certified count 0. Report and per-batch disposition: `research/excavator/claude-tribonian-2026-11-04/REPORT.md`, `evidence/DISPOSITION.json`. Packets and reviews are on branch `claude/tribonian-state`.
- **Integrated:** PRs 131-137 and Tribonian merged through PR #138 (`claude/integration-20261104`). Fixes: Valla materialization certificate re-established after an audit (`research/progress/integration-20261104/VALLA_CERTIFICATE.md`); x1-class-engine manifest bound; neyman-pilot declaration reverted. PR134 entered through PR136.
- **Lind trial (negative):** mechanical receipts supplied to blind reviewers saved nothing measurable over 85 claims (53.7M vs 52.4M cache read). The second independent reviewer caught 7 extra defects. Receipts are not a default. Kean F-20261104-1.
- **Dispatch-checked production (negative):** o26 and o27 cleared 60/60 orders, yet only 9 were submitted and 2 filed. Kean F-20261104-5.
- **Blocked, with first step:** 47 reviewed claims stranded as custody_record_only need a new packet once the bytes are held (REPORT.md section "Still blocked"; Kean F-20261104-2). EO 10156 needs a better witness. o28-o30 have fresh packets with `dispatch-v2.json`.
- **Next:** acquire the National Emergencies Act continuation notices and register the official FR texts of later orders (EO 13286 first); tighten the pre-assignment screen for YES orders without held current-law sources and for producer-cited hash-only sources; add `.job-cache/` and `jobs/_attempts/` handling to the runner's fallback capture (Kean F-20261104-4).
- **@Owner:** A-20261103-1 (Bacon session files) and A-20261104-1 (legal first-ending contract adoption) remain open and are yours. The hosted dashboard is not redeployed; its tracker data refreshes from main.

## 2026-11-02 (Claude, Erasmus resubmission and Geddes wiring)

- **Filed 52 claims** (`research/readiness/claims/claude-2026-11-02-erasmus-*.jsonl`): 32 of the 40 Apollo rejects
  recovered, plus corrections superseding 20 filed Apollo claims (all 18 Geddes flags plus EO 6684C and 6321). Every
  claim passed the checker, a blind Opus review with a planted control (10 of 10 caught) and `kit.py complete`.
  Certified count 0. Report: `research/excavator/claude-erasmus-2026-11-02/REPORT.md`; Kean F-20261101-1.
- **Geddes:** `kit.py batch-check` now runs it and writes `GEDDES_LINT.json`; `--geddes-strict` plus
  `geddes.py gate` block review until each flag is answered; new consistency and citing checks (Apollo recall
  20/40 to 35/40); `telemetry.py` and `cost --compare`; slim view extended with the gaps producers reported.
  `source_supplement.py` now carries replacement routing so filed NRA claims can be corrected. Tests: Geddes 89,
  claim-kit batch and supplement pass.
- **Measured:** fixed per-agent cost dominates (a one-order producer read 5.2M cached tokens); the slim view did
  not lower cost per order on resubmissions, which add work per order. Telemetry in `TELEMETRY.csv`.
- **Still flagged on filed claims:** EO 11547, 11646, 12060 (false "no hit" U.S. Code searches) and EO 11303
  (exhaustion wording; correction rejected). Kean A-20261101-geddes-models (Codex) is moot now that Claude ran the
  retries; the owner may close it.
- **@Owner:** none new; A-20261031-1 still open.
- **Next:** correct the four flagged filed claims in one larger batch; give packets evidence ids for held later
  orders and accept graded board-report texts, which together block 7 orders.

## 2026-11-01: Geddes source repair and exact warning audit

- **Done:** Repaired full-order/recital boundaries, native inventory overrides, source-specific verbatim quotations, reasoning suffix/FR bindings, event actor/scope, and literal-name corpus identity/cache guards. Existing PR122 branch; canonical claims/statuses/codebook/human reviews unchanged, certified 0.
- **Evidence:** `research/excavator/claude-geddes-2026-11-01/REPORT.md` and `repair/`. Local exact recall 20/40 (was 9); 18/254 filed claims flagged (was 55). Independent audit supports all 18: 16 wording discrepancies + 2 missing event-record inconsistencies; 0 false/indeterminate in the examined set. Original total-warning metric remains 18>5; do not conflate it with audited false positives.
- **Validation:** 42 unit tests and 29 independent probes pass. Four filed order-body abstentions plus rejected EO12891 remain disclosed. All 1,346 Apollo text pins verified; local name corpus sparse (1,074/39,770). Hosted benchmark41355823118 passes:39,770/39,770 text members verified, no missing/changed files, exact same flags; raw native artifact/hash index retained. Hosted unit tests/Kean pass.
- **Costs:** Two configured gpt-6-sol workers and gpt-6-astra reviewer; prospective clocks in repair/TELEMETRY.json, token/active-time measurements unavailable. No measured model saving or new filing is claimed. Kean F-20261101-geddes-repair/native.
- **Next:** Review PR122; preserve immutable source/claim versions and truthful coverage. Track B scientific roles remain unrun under existing A-20261101-geddes-models.
- **Asks:** @Owner: none for this programming repair.
- **Do not:** suppress actual quote discrepancies to meet a warning-count target, change already-filed claims, or turn diagnostic warnings into scientific judgments.

## 2026-11-01: Geddes draft and exact Apollo retry inventory; execution incomplete

- **Done:** `jobs/geddes/` advisory lint/order view/cost, unit-test workflow and explicit pre-handback step; frozen claim-kit contract unchanged. Base `claude/apollo-moon` at `40eb4b5` because PR121 was open. Exact 40 retry versions in `research/excavator/claude-geddes-2026-11-01/inventory/`, grouped NRA 6/general 20/general 14.
- **Accuracy:** 9/40 exact review defects caught; 15 rejected versions with any flag; 55/254 filed comparator flags. Both targets fail. Read REPORT.md/DEFECT_CORRELATION.json; do not call 15 recall or infer clean claims. Corpus/name/prose and recital/inventory-boundary gaps remain.
- **Measurement:** Actual g03 bundle 8,842,721 bytes versus 24 views 634,144 bytes. Cache tokens/net savings unknown. Four Apollo cost groups reproduced. Two gpt-6-luna workers and gpt-6-astra engineering reviewer; tokens/active labor unavailable; reviewer 1,099.014s prospective wall includes waits. Telemetry availability and failed development passes retained.
- **Validation:** 14 unit tests, 20 independent/targeted probes, 18 acceptance checks pass at code 3472f558; scientific quality thresholds do not. Kean brief 7,795 bytes at registration; strict check passes. Findings F-20261101-geddes-lint/retries/cost.
- **Blocked/Next:** No fresh packet, Sonnet producer, Opus scientific reviewer, new controls or publication. 0 new claims; certified 0. Make required runtime available and repair lint precision, validate complete prepare context, then fresh prepare/review/complete sequentially under lock; commit only after packets finish. Never reuse committed Apollo packets for apply.
- **Asks:** Execution-route decision for the owner is registered as `A-20261101-geddes-models` (required models or explicit substitution).
- **Do not:** count retrospective flags as independent review; auto-reject on lint; change canonical claims/statuses/codebook/human reviews or certified count. EO6471A/7016 remain under A-20261031-1; six custody/OCR drops remain excluded.

# Claude's handoff notes

Newest entry first. See `README.md` in this folder for the format.

## 2026-11-01 (Claude, Apollo claim swarm)

- **Filed 254 lifecycle claims** (`research/readiness/claims/claude-2026-10-31-apollo-*.jsonl`) from 444 orders in
  19 claim-kit batches: 127 NRA (shared S.J. Res. 113 analysis) and 127 general post-1937. Each passed the actual
  checker, a blind separate-context Opus review with planted controls (20 of 20 caught) and `kit.py complete`.
  40 claims rejected in review, 6 dropped at completion (custody or OCR-quote mismatch), 144 orders blocked by
  producers with named gaps. Certified count 0. Report: `research/excavator/claude-apollo-2026-10-31/REPORT.md`;
  Kean F-20261031-2.
- **Telemetry:** per-agent tokens and active time in `TELEMETRY.csv` (19 Sonnet producers, 19 Opus reviewers);
  extractor `tools/moon_telemetry.py` works on any subagent transcript set.
- **@Owner:** A-20261031-1 (keep or withdraw EO 6471A and 7016 after a disclosed blinding slip).
- **Next:** a deterministic pre-review lint for template carry-over, suffix-dropped EO numbers and FR page or issue
  dates (about 15 of the 40 rejections); resubmit the 40 rejected claims with the reviewers' defects fixed; claims
  for the 888 newly statused orders once claim-kit outputs are regenerated on main.

## 2026-10-31, later (Claude, Jacquard wave 2 and Lachmann route d)

- **Jacquard wave 2** (PR #119): full review of every remaining waiver, NRA and Canal Zone lot member; 714 more
  statuses appended (register 3,403 to 4,291 with wave 1 on merge). Two over-strict wave-1 controls voided after two
  independent reviewers and the coordinator agreed (EO 370, EO 3031); 59 upheld orders held (cut-off texts, messenger
  appointments). 325 orders listed for individual review. Kean F-20261031-jacquard-wave2.
- **Lachmann route (d)** (PR #120): APP page heading plus date and title agreement confirms 910 more working texts
  (1,674 total); fresh audit 59/59. Kean F-20261031-lachmann-route-d.
- **Combined simulation:** statuses 4,291; provisional text steps 1,674; ready unchanged at 498 until claims run.
- **Usage this round:** about 6.6M Sonnet tokens (60 reviewers, 4 auditors, 2 builders); coordinator Opus 5.5.
- **Next:** claim production for the 888 new statuses whose text is now provisional or original (the ready count
  moves only through claims); a Wikisource page rule (456 orders); individual review of the 325 listed orders.

## 2026-10-31 (Claude, Jacquard and Lachmann: status adoption and working-text confirmation)

- **Owner rulings recorded** (`research/readiness/owner_rulings/2026-10-31-jacquard-and-working-texts.md`; Kean
  D-20261031-jacquard, D-20261031-claude-reviewers, D-20261031-working-text-step; answers A-20261021-3 and
  A-20261028-4): sampled class adoption with a zero-miss 59-order test; separate-context Claude reviewers may decide;
  a confirmed standalone working text closes the text step provisionally, counted separately.
- **Jacquard** (`jobs/jacquard`, branch `claude/jacquard-loom`): six lots, 325 blinded items, 25/25 planted errors
  caught, no lot passed. 174 individually upheld NO statuses appended to the register in this branch (owner merge
  adopts; 3,403 to 3,577). 126 failures in `research/excavator/jacquard-2026-10-31/INDIVIDUAL_REVIEW.csv`.
  Lesson: X1 types are heterogeneous; define lots by text features. Kean F-20261031-jacquard-wave1.
- **Lachmann** (`jobs/lachmann`, tracker change, Lewis keeps routing originals; branch `claude/lachmann-collation`):
  764 of 7,534 working texts confirmed after three audits (final round 59/59, planted 5/5). After merge the tracker
  marks those text steps `provisional` and adds their replacement and recheck obligations. Kean F-20261031-lachmann.
- **Usage:** builders Sonnet 5.5 (138k, 156k, 188k tokens); 20 Jacquard reviewers about 2.03M; 12 Lachmann auditors
  about 1.03M; coordinator Opus 5.5. Certified count 0.
- **Next:** per-order review of the remaining L4 (80) and L5 (164) members or a text-feature lot for L1 (799
  members, 81% uphold rate in the sample); a Lachmann bridge for APP/Wikisource texts without a printed number.
  Both PRs touch disjoint files from Codex PR #117. Merge order does not matter; the tracker sweep regenerates.

## 2026-10-31 (Claude, Minard: the Workflow tab on the remaining-work dashboard)

- **Built** a fifth dashboard tab, Workflow (`#workflow`): 79 named jobs, past campaigns, the agent review
  procedure and the human gates, placed in eight stages from discovery to human review, with loop arcs (review
  rejects, fetch requests, tracker blockers and audit holds), a cross-stage support band, hover cards, pinned
  detail records with dated results and repository links, search and status filters. Data in
  `research/progress/remaining-work/workflow/` (builder `build_workflow_nodes.py`, tests, provenance); page source
  in `research/progress/remaining-work/dashboard/index.html`. Branch `claude/minard-workflow-map`; not merged.
- **Rules kept:** catalog stats read live from the tools dataset (all 43 rows mapped, never summed); the ready count
  is the tracker's (498); certified 0 is shown as a separate gate; every past campaign is historical.
- **Namesakes:** NORTON is Margaret Cross Norton (recovered from Astra's 2026-10-20 naming reply); Lamm is marked
  inferred (Richard Lamm, Colorado's 1976 sunset law); descriptive names show no namesake.
- **Review round (same day):** Codex's review of `945fa7ec07` asked for four corrections, all made: exact catalog-row
  labels on shared rows, no timeless certified-zero text, 15 shorthand source paths fixed in provenance (all 302
  paths now resolve at the pin), and the Sinclair cross-family figures separated from the lean review. Close and
  Escape now return to the pinned box. Interaction test 111 of 111.
- **Discrepancies found and left in node caveats** (Lewis 2,376 vs 2,491 agent checks, 15 audit-hold records on 10
  orders, Junto's empty test ledger, Llull 65 vs 90 forecasts, Olney and Justinian with no completion record):
  see `research/progress/remaining-work/workflow/README.md`.

## 2026-10-30 UTC: PR104 control-scope repair; frozen pin superseded to b1890d7

- **Done:** `completion.controls()` now binds a planted-control review to the seeded task. Its scope must be
  `whole_case` or `partial_research` and, for a submitted member, equal the manifest `publication_kind`. This
  answers the lifecycle-assurance reproduction (PR106 `f750886a`). It adds 2 regressions and 479 tests pass. The
  rehearsal r1 dry run is unchanged. Kean F-20261030-7001.
- **Pin:** claim-kit/Valla source for Sol's combined testing is now `b1890d7` (superseding `8adc939`; announced
  on PR104).
- **Asks:** @Owner: none new (A-20261029-1 stands). @Sol: use `b1890d7` for combined testing.
- **Do not:** treat a reviewer's self-declared scope as the control's task.

## 2026-10-29 ET (later): PR104 native full-code rehearsal, concurrency/clone checks, handoff to Sol

- **Done:** Rehearsal r1 (`research/excavator/opus-native-rehearsal-2026-10-29/`) ran on fresh packets and
  supplements with the full repaired code, then producer (Sonnet), blind reviewer (Opus) with a caught plant, and
  native apply/batch-check/complete in an isolated tree. 5 claims completed; EO 6254 (6730 supersede vs amend
  undecided) and EO 6438 (Wayback-only custody) stay blocked. The adoption dry run on the branch reproduces the
  publishable bytes. No canonical write. Kean F-20261029-7002.
- **Measured:** same inputs, machine path 214.0 s base vs 53.5 s repaired; complete 60.8 s. Production's t5/t6
  race now publishes both byte-identically; a same-instrument race publishes once. Cache matched a fresh index in
  16 real perturbation states.
- **New code:** a failed packet verification is run once; `kit.py publication-audit` covers separate clones,
  which Git merges silently; a breaker guards stale-lock removal. The independent Opus review's findings are
  fixed. 477 tests.
- **Next:** combined testing is Sol's (`research/progress/opus-packet-friction/SOL_HANDOFF.md`, frozen pin on
  PR104); filing r1 is an adoption decision; run claim-kit on main (its compiled outputs are stale); declare 6730 /
  6620-B for future NRA batches.
- **Asks:** @Owner: A-20261029-1 (PR104 is the proposed repair; merging is yours); whether planted-control
  adjudication may stay with the reviewer (flagged in the rehearsal report, not a Kean ask). @Sol: own any
  `needs.txt`/`inputs.txt` change from `INPUT_CLOSURE.md`; consider wiring `kit.py publication-audit --base main`
  into PR CI.
- **Do not:** commit planted review sets or control keys; place copies of a batch's claims under `research/`
  outside its packet; split one packet across two completions.

## 2026-10-29 ET: packet-friction repairs H01-H07 (branch opus/packet-friction, PR unmerged)

- **Done:** Valla packet context scoped to requested IDs (own packet and same-agent supplement parent excluded;
  per-query bounds replace the 100-package raise); completion verifies each packet once, rechecks before writing,
  tolerates disjoint concurrent claim files under a short lock in the Git common dir; one-pass prior-research
  discovery (completion `TRACKER_CLAIMS.jsonl` union copies no longer bind); content-keyed fragment index reused
  across checked claims (`fragment_cache.py`; `assemble.py`/`working_text.py` unchanged, no compiler rebuild);
  batch-level undecided freezing. Report and receipts: `research/progress/opus-packet-friction/`. Kean F-20261029-7001.
- **Measured (same inputs, commit 1d112ff):** real t6 completion with a mid-run publication 506 s/0 filed -> 122 s/16
  filed (bytes identical to production); view 28.6 -> 3.7 s; apply 143.7 -> 8.8 s; batch-check 158.8 -> 29.3 s;
  7 false invalidations gone, 18 relevant perturbations still invalidate.
- **Next:** after merge, re-prepare in-flight packets once (pinned code changed) and re-attest re-versioned claims;
  for NRA, declare held EO 6730 (for 6254) and EO 6620-B (for 6438) through `source_supplement.py` (replay shows the
  route works; no code gap); run claim-kit on main (main's compiled outputs are stale for build.py/excavate.py, which
  blocks undecided preparation).
- **Asks:** @Owner: A-20261029-1 (this branch is the proposed Valla repair; merging is yours). @Sol: when combining,
  keep both Kean findings and regenerate the brief; claim-kit/valla jobs still need `research/**` and FRAGMENTS inputs.
- **Do not:** run two completions in one checkout without this branch; commit packets in flight on main until merged.

## 2026-10-29 ET: NIRA code-approval orders through ordinary production with one shared, reviewed analysis

- **Done:** Branch `claude/schechter-nira-sweep`. Shared analysis `research/excavator/claude-nira-sweep-2026-10-29/SHARED_ANALYSIS.md`
  (first end June 14, 1935 by S.J. Res. 113 sec. 2; Schechter recorded as a validity finding; denials exhausted on
  their date), independently reviewed (planted proposition caught). Seven batches (b0 baseline, t1-t6): 132 orders,
  91 claims upheld and filed in `research/readiness/claims/claude-*-2026-10-29-nira*.jsonl`, 41 blocked with causes;
  10 of 10 valid controls caught. Isolated tracker replays add to 486 ready once the canonical checker and tracker
  regenerate (published 395). X1 event reader repaired (8 of 8 event sources held; run 40882610996).
- **Measured:** matched 6-order pair 7.01M vs 3.26M weighted tokens (producer+reviewer); treatment batches 0.24M per
  filed claim vs 1.75M baseline; coordinator 13.0M, mostly one-time. Details and limits: `REPORT.md`, `COSTS.json`
  (from `costs.py`). Kean finding recorded; ask A-20261029-1.
- **Next:** (1) a shared rule for conditions, stays, committees and report directions attached to approvals (about 20
  blocked orders; producers treated them inconsistently), reviewed, then a reopen batch; (2) re-prepare packets with
  held later-order excerpts for EO 6242-C/D, 6254, 6438; (3) Cotton capture for EO 6414, 6457, 6467; (4) next
  batches from `COHORTS.json` pool (208 statused orders not yet attempted) with `PRODUCER_PROMPT.md` /
  `REVIEWER_PROMPT.md`; (5) cache claim-kit's fragment index (`view` spends 89% of 22 s rebuilding it) in its own PR.
- **Resume:** `python3 jobs/claim-kit/kit.py prepare <24 ids> --agent claude --write <batch>/packet`, then
  `make_declarations.py`, `source_supplement.py ... --write <batch>/packet/supp`, `cruden.py lookups`; launch a producer
  with PRODUCER_PROMPT.md; plant controls with keys outside reviewer paths; reviewer with REVIEWER_PROMPT.md;
  `make_completion.py` then `kit.py complete ... --publish`, one completion at a time.
- **Asks:** @Owner: A-20261029-1 (Valla packet-context fix). @Codex/Sol: run the different-family review in
  `review-shared/PROPOSITIONS_v2_SOL.md`.
- **Do not:** commit a packet folder while any batch is in flight; run two completions at once.

## 2026-10-28 22:30 ET: Namier batch produced and reviewed; custody of APP page bytes is the next blocker

- **Done:** Runner regenerated namier → claim-drafts → claim-kit on the branch (run 40770547716; known_pairs 18,068,
  printed_reference_only_pairs 1,074). Prepared nine serial retirement exemptions (three Namier chains) in
  `research/excavator/namier-serial-exemptions-2026-10-28/`: every extension order was already in the packet, no
  search needed. 7 claims assembled and gate-passed; blind review in a separate Claude context upheld 7/7 genuine,
  caught the planted control (strict); EO 6615 upheld after reveal. `kit.py complete`: 0 eligible, all 7
  `rejected_mechanical` on `source_held: custody_record_only` only (Kean F-20261028-14). Two members blocked by a
  clause-drafts date-line defect that hits 76 APP pages (F-20261028-13; list in that folder). New job
  `jobs/cassiodorus/` keeps the APP page bytes from the recorded captures so the checker can re-hash them; wired
  before claim-checker, claim-kit and claim-drafts; it cannot fetch from the agents' container (archives refused).
- **Running:** the push runs cassiodorus on the branch; check `jobs/cassiodorus/output/SUMMARY.json` (`kept`,
  `hash_mismatch`, `no_capture_record`) and the claim-checker rerun.
- **Next:** rerun `kit.py complete research/excavator/namier-serial-exemptions-2026-10-28/COMPLETION.json --write
  .../complete-v2` once Cassiodorus has kept the 13 pages; if eligible, `--publish` to the manifest's own-agent
  file. Then apply the tolerant DATE_LINE (patch and test drafted; changes the claim-kit compiler hash, so do it
  between batches) and re-prepare EO 6773/6577. Then the remaining 46 X1 retirement exemptions with later hits.
- **Asks:** `@Owner`: none.
- **Do not:** publish from `complete-v1` (nothing eligible); edit `packet/review/BLIND_REVIEW.jsonl` (sealed).


## 2026-10-28 18:05 ET: Namier (name-based discovery for one-person orders) and the dropped-citation fix in claim-kit

- **Done:** New job `jobs/namier/` (Kean F-20261028-11): parses the person each one-person order names and searches
  every held text once; 2,231 subjects (1,695 X1 waivers/retirement exemptions + 536 title-detected, mostly 1937-50s),
  243 with an unflagged later hit, 483 leads. Wired into claim-drafts (declared search `namier:held_texts_person_name`
  with per-order `SEARCH_COVERAGE.csv`; matches as `names_same_person` later-event proposals, never an ending) and
  claim-kit (matched orders are known actors; dossier line `names the same person (name-match lead, read before use)`).
  Second fix (F-20261028-12): claim-kit dropped 1,157 citation pairs where a held text cites the target by number without
  a change verb (serial exemptions, extensions, recitals); they are now known actors, reported as `cited by number, no
  change provision located: EO:X`. Local rebuild: known_pairs 16,626 → 17,763; EO:6088's dossier now holds EO 6998 and
  EO 7597. Tests: namier 8, claim-drafts 69, claim-kit 412 pass. After/trigger files order namier before claim-drafts
  and claim-kit; AGENT_PROTOCOL.md documents the two new lines.
- **Running:** the push runs namier, claim-drafts and claim-kit on the branch; check their `output/STATUS.json`, then
  `SUMMARY.json` counts `printed_reference_only_pairs` and `known_pairs`.
- **Next:** re-prepare the 2026-10-28 probe (12 retirement exemptions) and a serial waiver batch from the regenerated
  dossiers; a producer should find the extension orders in the packet without searching. Namier's remaining gaps: 296
  subjects with no parsable name (OCR-split surnames, class orders mistyped as one-person), common-name noise, and
  nothing outside the held texts (no Official Register, no CSC report listing use).
- **Asks:** `@Owner`: none.
- **Do not:** edit `research/readiness/type-rules/*` to point at Namier without an independent re-review; the rules'
  search step is unchanged in wording and now supplied by the dossier's machine search.


## 2026-10-28 ET (afternoon): spent-order probe filed 15 claims; waiver rule rewritten; Cotton

- **Done:** PRs #69-#73 merged.
  - **Spent-order probe:** 20 own-terms orders; 15 claims published in
    `research/readiness/claims/claude-2026-10-28-spent-probe.jsonl`. Ready for human review: 285 -> 300. The blind
    review caught both planted controls. Record: `research/excavator/claude-spent-probe-2026-10-28/` (final packet
    `packet-v6/supp`, completion `complete-v1`).
  - **Held:** EO 7208, because its APP page was harvested live and has since changed, so custody cannot be shown;
    its claim should be redone on the government printed copy (Commons DjVu 7082-7261) or a mirror capture.
    Blocked: EO 2842, 2855, 2947, 2999 (no work-completion record; 1921 resolution text not held).
  - **Fixes:** claim-kit takes the producer-registered working-text grade; the APP page check is defined in
    AGENT_PROTOCOL.md; supplement excerpts are graded; claim-checker re-fetches archived captures and Commons
    files; new job **Cotton** (`jobs/cotton-capture-custody`) commits the exact bytes of cited web sources.
  - **TR-CS-WAIVER** rewritten under the owner's evidence ruling (research in
    `research/excavator/claude-cs-waiver-research-2026-10-28/`) and approved after three independent review rounds.
- **Measured:** about 79 producer-minutes and 9 reviewer-minutes for all 20 orders, including four re-runs caused
  by now-fixed defects. That is about 5.5 agent-minutes per finished order, against the effort model's 88 minutes
  per order for these types. Coordinator time was not measured. The result covers only simple own-terms types
  (about 380 model hours); Kean F-20261028-7.
- **Lesson:** keep every review and completion file inside the final packet folder; completion refuses a packet
  whose prior research changed.
- **Next:** scale the probe method to the other 230 retirement, closing and own-terms orders; probe one large
  block (land withdrawals or the CS waivers with an Official Register fetch job); redo EO 7208.
- **Owner questions:** none new. Open asks are in `HANDOFF/KEAN.md`.

## 2026-10-28 ET: merged PRs #56 and #58-#66; Kean shared register built

- **Done:** With the owner's express permission (`research/readiness/owner_rulings/2026-10-28-merge-permission.md`),
  merged #56 and #58-#66 into main as `fef1c0d`. #57 and #54 stay open: #57's Junto candidate reuses the id
  `C-20261024-2` that main already gives a different candidate; #54 conflicts with main across ~5,300 files.
  Built **Kean** (`jobs/kean/`, brief at `HANDOFF/KEAN.md`, check in `.github/workflows/kean.yml`): one register of
  owner decisions, owner questions and results, seeded with all 9 owner rulings, 9 open owner questions and 31 results,
  and wired into AGENTS.md, CLAUDE.md, copilot instructions and HANDOFF/README.md. Start-up now reads the brief plus the
  newest entry of each notes file instead of all notes.
- **Runner:** added the Rattle Watch to `.github/scripts/run_jobs.py` (per-minute heartbeat; stops a job silent and
  idle for 20 minutes; web-search jobs run only downstream of a push get 12 requests). Cause of slow runs: one owner-ruling
  file selected 14 jobs including Clark's web search (Kean F-20261028-3).
- **Finding:** the owner ruled on 2026-10-21 that his ProQuest scans count as provisional working text, but the tracker's
  top unlock and the Pinakes README still call the grade an open codebook decision; no claim has used a scan. No
  handwriting OCR comparison exists on record; only tesseract was used (Kean F-20261022-1, F-20261028-1).
- **Next:** remove the stale ProQuest wording (Kean drift list); have the agent lines build claims on the ProQuest and
  transcription texts; test AI page reading on 20 of the 310 handwritten scans.
- **Asks:** `@Owner`: A-20261018-1, A-20261019-1, A-20261021-1, A-20261021-2, A-20261021-3, A-20261022-1,
  A-20261028-1, A-20261028-2, A-20261028-3 (all in `HANDOFF/KEAN.md`).
- **Do not:** hand-edit `HANDOFF/KEAN.md`; run `python3 -I jobs/kean/kean.py brief`.

## 2026-10-22 ET: Mansfield, judgment-only claims for modern NO orders (branch `claude/mansfield-1`)

- **Done:** 30 "only judgment left" NO orders attempted in 3 seeded batches (seed 20261022); **14 claims filed**
  (`research/readiness/claims/claude-mansfield-b0{1,2,3}-2026-10-22.jsonl`), all passing the gate and the checker;
  0 genuine rejections; 16 blocks, all judged justified; plants 4 of 5 caught (one D6 omission missed). Upheld per
  attempt 0.30 blind, 0.47 with after-reveal re-reviews, against a 0.45 forecast (Llull L-20261022-1, O-20261022-1)
  and the 0.5 gate, so the run stopped; the YES stratum was not attempted. Report:
  `research/excavator/mansfield-2026-10-22/REPORT.md`; cost about $55 estimated (`COST.md`). 8 fetch lines enqueued.
- **Why the pool did not convert:** 6 blocks where the ending text is held but the claim-kit dossier has no evidence
  span for it (needs act_overrides or a kit fix: EO 10915, 11927, 12975, 9333, 12607, 8072); 4 unheld emergency-board
  report dates (10319, 12370, 12414, 12393); 3 unheld Public Land Orders (8173, 8505, 8915); 1 unheld statute (12810);
  2 open method questions (11877, 12921).
- **Next:** wire held acting texts into dossiers (the single largest block class); fetch the PLOs and board reports;
  owner rulings on "parent revoked as amended" for amending orders (10915, 11927, 11877) and on a parent's unnamed
  sunset (12921). Expected tracker change: up to 14 more ready (AI-upheld tier), 0 certified.
- **Asks:** `@Owner`: 1. the two method questions above; 2. whether the 5 after-reveal-upheld lines (10926, 13032,
  10972, 10312, 5825) may stay filed; they were re-reviewed in full by the same independent reviewer after the plant
  key was opened, which Y2LEAD did not do. `@Codex`: dossier evidence spans for acting provisions the scanner already
  located but did not slice (EO 11976 for 11927, EO 13137 for 12975, EO 9830 for 9333, EO 12220 for 10915).
- **Do not:** promote any of these claims; re-attempt the 16 blocked orders before their sources land.


## 2026-10-21 ET (evening): tool map updated for the rulings and for Lewis and Clark

- **Done (branch `claude/great-ptolemy-9r6zah`, merged with main cd5dba93):** `build_toolmap.py` now applies the
  Oct 21 rulings (owner-ruling lane is empty; transcription-only orders sit in "ruled, not wired" until the tracker
  rule changes; Pullman packets are agent work) and reads Lewis's ROUTES.csv, which gives every transcription-only
  order a route. New lane "owner action": 2,655 text steps are the owner's own ProQuest retrievals. No-route fell
  from 3,457 to 803. `TOOLS.csv` adds Lewis, Clark and the Domesday register. Dashboard refreshed on all tabs.
- **Asks:** `@Claude` / `@Codex`: one tracker rule so a labeled transcription satisfies `original_text` provisionally
  (ruling 6), with a separate count of ready orders that rest on transcriptions; then rerun the tracker.
- **Do not:** promote a transcription to `acceptable_as_original`.

## 2026-10-21 ET: owner rulings 2-8 recorded (`research/readiness/owner_rulings/`)

- **Ruled by the owner today:** (1) report deadlines never end a board order, record both dates; (2) struck-and-inserted
  clauses continue, amended, with before/after text; (3) unnamed instruments are disclosed candidates, not ends;
  (4) EO 10449 treated like the other boards; (5) adopt the 15 Bowditch NO proposals by pull request, lean-review the
  41 Sinclair ones first; (6) transcriptions may satisfy the text step provisionally, labeled, originals still the
  goal; (7) "until" dates inclusive, alternative noted; (8) no ProQuest request, the owner is retrieving scans himself.
- **Unblocked:** Pullman's 97 packets, Blackstone's 4 orders, the 15 unnamed-instrument orders, the Lamm "until" six,
  and the 4,644 transcription-only orders for text-step purposes.
- **Rework owed:** 43 "ends on amendment" clauses in 26 orders (ruling 2); 6 claims get a disclosure flag (ruling 3).
- **Next:** adoption pull request for the 15; lean review of the 41; re-run the day review with the rulings applied.
- **Do not:** promote a transcription to `acceptable_as_original`; harvest ProQuest; change the codebook.

## 2026-10-21 ET: owner ruling on report deadlines (question 1 of the brief)

- **Ruled (owner, option C with both dates):** `research/readiness/owner_rulings/2026-10-21-report-deadline.md`.
  Report-deadline orders end on express revocation (EO 12553 for most); the report date is a `later_event` with a
  disclosed "functionally spent on <date>" note. Pullman's 97 packets can run. EO 10449 still needs a word from the owner.
- **Next:** questions 2 (strike-and-insert) and 3 (unnamed instruments) are being put to the owner now.

## 2026-10-21 ET: figures refreshed on main 09310ada; tool map added to the dashboard

- **Done (branch `claude/great-ptolemy-9r6zah`, restarted from main):** reran `build_remaining_work.py` and
  `build_effort.py`: 278 ready, 86,103 open steps, about 15,700 agent-hours (was 16,178). New
  `build_toolmap.py` and hand-kept `TOOLS.csv` put every open step in a lane (machine queued 509, machine output
  not counted 723, agent claim 13,480, owner ruling 8,357, earlier step first 50,379, no route 3,457) with the tools
  serving each. Dashboard tab "Tool map": https://claude.ai/artifact/531KGTebdrgdeUitKhp8du#toolmap.
- **Reading:** the gap is not missing tools. 8,357 open steps wait on owner rulings (transcription-as-copy,
  report deadline), 13,480 on agent claim lines that already work, and 3,457 old texts have no free route.
- **Do not:** treat lane counts as yields; they are reach, in the Polya sense.
## 2026-10-21 ET (~17:10Z): Lewis and Clark go online; Domesday register

- **Done (same branch, PR #49):**
  - `jobs/_lib/eo_websearch.py`: open-ended web search shared by Lewis and Clark. Engine registry (built-ins plus owner-extensible `search_engines.json`): general web engines, keyed engines (Google CSE, Bing, Brave, SerpAPI, NARA; the workflow now passes those secrets when added), LOC, Internet Archive, Google Books, HathiTrust catalog, FR API, Wikisource/Wikipedia search, APP, govinfo. Escalating query strategies per order; hits followed and read for number, date and operative wording; every page read harvested for order numbers; state carried forward from the last committed output so no target is ever dropped. FetchPool underneath (robots.txt obeyed, throttled, hashed into SOURCES.jsonl); blocked or keyless engines reported by name in ENGINES.json.
  - Lewis `online.py`: hunts every order in scope, manual-lead routes first, 100 targets / 1,500 requests per run by default (`JOB_MAX_TARGETS`, `JOB_MAX_REQUESTS`).
  - Clark `online.py`: hunts number gaps, plausible cited-unknowns and number-only orders; reads the list pages in `list_pages.txt` (Wikipedia, Wikisource, APP, OFR tables; owner-extensible) and reports every order number the census lacks (`WEB_LISTED_ORDERS.csv`).
  - `jobs/domesday-register`: `REGISTER.csv`, one row per census order with date, title, president, every source held by class, readiness, ProQuest state, Lewis/Clark results; `CANDIDATES_NOT_IN_REGISTER.csv` for numbers named anywhere that the census lacks. Runs after Lewis, Clark and the tracker.
- **Running:** the branch's first online run will show in `ENGINES.json` which engines answer from GitHub's runners and which robots.txt blocks; expect several blocked.
- **Asks:** `@Owner`: add search keys as repository secrets to switch on the big engines (`GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX`, `BING_SEARCH_KEY`, `BRAVE_SEARCH_KEY`, `SERPAPI_KEY`, `NARA_API_KEY`); the jobs pick them up on the next run with no code change.

## 2026-10-21 ET (~16:45Z): Lewis and Clark, two source-discovery jobs

- **Done (branch `corps-of-discovery-lewis-clark`, PR to follow):** two paired jobs plus a shared helper, all offline, standard library (pypdf optional), tests run first.
  - `jobs/lewis-originals` (**Lewis**): for every order the tracker leaves `ONLY_COMPILED_TRANSCRIPTION_FOUND` (4,644), the route to an official original and where it stands: a verified ProQuest PDF in the repo (bytes, SHA-256, pages, text-layer quality), a ProQuest link awaiting upload, a Federal Register fetch request for the source-ladder (266, contract-validated, in `PROPOSED_FETCH_REQUESTS.jsonl`; never enqueued by the job), a GPO/Hoover volume range to re-check (1,704), or a ProQuest phrase search (1,941). `FRAGMENTS.jsonl` for ProQuest files carries `acceptable_as_original: false`, `needs_page_check: true`; the tracker does not read it.
  - `jobs/clark-discovery` (**Clark**): orders the project cannot identify. 46 number gaps in the 14,972 census, 22 of them one June 1932 run (EO 5853-5879) that the APP index knows with dates and titles; 26 plausible cited-but-unknown ids from 27,017 texts and 5,063 OFR notes (EO 27-A, the 1894 run 36-53, EO 92, several lettered orders), with OCR artifacts ranked separately; 3,432 census orders known by number only (2,655 on the ProQuest list); 414 dated unnumbered references matching nothing. `HANDOFF_TO_LEWIS.jsonl` feeds Lewis.
  - `jobs/_lib/eo_identity.py`: id parsing (lettered, ½, `-1` duplicates), the date/title oracle (OFR catalog, APP index, fragments, WPA list, ProQuest list), and the citation regex.
- **Running:** nothing until the branch lands; both jobs are `DAILY` and trigger on `research/pre-1937-sources/*` and the census.
- **Next:** when the ProQuest PDFs are uploaded, Lewis inventories them on the next run (2,738 orders move from `awaiting_acquisition` to `file_verified_pages_unchecked`) and Clark reads the usable text layers.
- **Asks:** `@Owner`: 1. Should the June 1932 run (EO 5853-5879) go to census intake? Clark's `NUMBER_GAPS.csv` has the APP evidence. 2. Decide whether ProQuest replica scans may count as the original after a page check; if yes, the tracker needs one rule (`J` class + test), which I have not written. 3. Enqueue Lewis's 266 FR proposals if you agree: `python jobs/source-ladder/request_contract.py enqueue --input jobs/lewis-originals/output/PROPOSED_FETCH_REQUESTS.jsonl --queue research/readiness/FETCH_QUEUE.jsonl`.
- **Do not:** hand-edit `jobs/lewis-originals/output/` or `jobs/clark-discovery/output/`; the jobs rewrite them.

## 2026-10-20 ET (Revere phase, ~21:45Z): late update

- **Ready 256** at 21:42Z, certified 0; newer claims not yet counted.
- **Since the ~18:00Z entry:**
  - Lambertini IV probe 2: passed, 5 claims. LAMB4X has no ruling-independent orders left.
  - R9830: probe 6 claims, scale 8 claims (26 ACT records).
  - R12553NB: probe 6 claims, scale 9 claims (32 ACT records).
  - VIAPAR: probe failed (4 of 8 blocked on strike-and-insert); 3 claims in all, including EO 11908 from the mend.
  - PAGECHK3: 1 claim.
  - Fixes: claim-kit act_overrides now matches lettered numbers (EO 7975A ingests). Source-ladder re-walks PDFs that are missing their named pages, so EO 11490 pp. 63-95 should land on the next run and unlock pool F11490 (20 orders).
  - Planted controls: every plant caught today. One automated "instruction poisoning" flag on the R12553NB s5 planter was a false positive; I checked it, and the edit was scratch-only.
- **Owner brief:** `research/production/owner-rulings-2026-10-20/BRIEF.md` covers three method rulings (report deadline, strike-and-insert, unnamed-instrument ends). AGENT_PROTOCOL step 3 already says "A report deadline is never an end", which equals option C: 97 orders.
- **Next:**
  1. F11490 once its pages land: `research/production/day-review-2026-10-20/next-lines/F11490_ids.txt`, Lambertini with a probe gate.
  2. After any owner ruling, run the matching staged packets: Pullman (`research/excavator/pullman-2026-10-20/`) or Blackstone.
  3. Almost every remaining line now waits on an owner ruling.
- **Llull note:** O-58 counts the Lambertini IV probe-1 claims as 0, but its 4 upheld claims were filed anyway. Outcomes are append-only.

## 2026-10-20 ET (Revere phase, ~18:00Z): coordinator after handoff

- **Done (pushed `e3c9f0d87`+merge):**
  - Lambertini III coda: 11 of 12 claims upheld (2/2 plants caught), all pass the checker. Files: `claims/claude-lambertini-{b02,rr4}-2026-10-20.jsonl`. EO 14052 is held back: EO 14082 sec. 4(c) strikes and re-adds subsection (xii), which needs a human ruling. Llull outcomes O-46..48.
  - Re-sourced to the held official FR texts: EO 10324, 10467, 12977 (i04, i08). 21 of 21 claims pass the checker, 1/1 plant caught. EO 10169 and 10390 are recorded as blocked (`instruments/REMNANTS.md`).
  - Sinclair mend II/III: 9 NO proposals written (EO 11209, 13555, 9294, 9762, 10704, 12573, 13975, 12604, 11796), 2/2 plants caught. Owner adoption batch is now **56** (Bowditch 15, Sinclair 41).
  - Tycho: 32 PEB report dates landed. **0** orders can close without the owner's report-deadline ruling; **47** depend on it. Re-rank: `research/production/day-review-2026-10-20/RERANK-evening.md`.
  - Ready for human review was 230 at 16:45Z, before these claims were counted. Certified: 0.
- **Running:** Lambertini IV (16 orders, probe gate in code). EO 9830 probe (10 ACT records, then claims; scale only if at least 4 of 10 enable claims).
- **Process lessons:**
  - (a) Overlay proposals must be frozen and proposed with no push in between. Every Run jobs run regenerates claim-kit output, which gives `stale_compiled_generation`.
  - (b) `python3 -I jobs/claim-kit/kit.py` fails on imports; run it without `-I`.
  - (c) Workflow scripts must handle a null agent result. A session-limit hit at 14:30Z killed agents mid-run; resume from the journal works.
  - (d) The PR for this branch is #40.
- **Next:**
  1. Read the Lambertini IV and R9830 results, then scale whichever passes.
  2. After the next ladder run, check the 43 remaining Lamm III PEB lines.
  3. Pre-stage the EO 12553 emergency-board packets so they can run as soon as the ruling lands.
- **Asks:** `@Owner`:
  1. Report-deadline ruling (47 orders now, about 89 in all).
  2. Adopt the 56 NO proposals?
  3. EO 14052 strike-and-reinsert reading (does a delete-and-insert end the clause?).
  4. The transcription-as-copy and Lamm readings are still pending.

## 2026-10-20 ET: Merged PRs #38, #40, #42-#45 into main; Domesday tool audit

- **Done (owner consent to merge everything):** integrated on `claude/dazzling-gates-4xkkzo`, then into main.
  Merge order: #40 junto, #43 Valla, #44 portfolio repair, #45 NORTON (supersedes the closed #41), #42 NEYMAN, #38 ProQuest.
  `astra/apollo-audit-20261020-1407utc` (no PR) was already contained in #44's notes.
  Generated `jobs/*/output` conflicts were resolved by taking the newer side, then regenerated by the runner.
- **Conflict decisions:** both Valla and repair holds on EOs 13792/13101/13148/13783/13807 kept (one finding, two reviews).
  Junto keeps the repair's stricter missing-quality rule, which NEYMAN had also fixed independently, plus NEYMAN's
  embedded `test_contract` check. A new `origin_kind()` stops string origins from crashing `check`.
  corpus-excavator `measure.py` takes both `--closures` and `--baseline-receipts`.
- **ID renumbering** (parallel branches reused ids):
  - Junto: NORTON C-14/R-4 → C-15/R-5; NEYMAN C-14..16/R-4 → C-16..18/R-6.
  - Llull: repair outcomes O-44..46 → O-49..51; NORTON L-56/O-44 → L-65/O-52.
  - Rows carry `renumbered_from`; Llull now proves a renumbered forecast against its original registration
    (L-65 verifies as preregistered at 4d456ec).
  - `jobs/neyman-pilot/output/junto-ledger/` is that pilot's isolated copy and keeps the old ids.
- **Fixes found by tests:** NEYMAN's Junto test was updated to the merged evidence rule. Mountweazel had a
  blinding leak: claim-kit's provenance block appeared on some real claims only, so it is now stripped from packets.
  All local suites pass except claim-kit's 35 status-overlay tests, which only need the runner's rebuild
  ("run claim-kit build once").
- **Audit:** `research/plans/DOMESDAY_TOOL_AUDIT_2026-10-20.md`. All 225 ready orders came from claim batches.
  The meta-tools (Junto, Llull, Polya, NEYMAN, NORTON, Hamilton, Valla, Mountweazel) have $0 verified savings.
  Recommendation: build no new tools; run claim batches on ~890 judgment-only drafts, drain source-ladder online,
  and wire unused acquisitions (csc-annual-reports branch, hathi, wikisource and others) into the tracker.
- **Asks:** `@Astra` / `@Codex` / `@Sol`: allocate ledger ids per agent (e.g. `C-sol-…`) so parallel branches cannot
  collide; register NEYMAN's three candidates as `contracts.jsonl` contracts and stop using embedded `test_contract`.
  `@Owner`: the report-deadline and transcription-as-copy rulings unlock the most orders.
- **Do not:** reuse the old ids above; reopen #41.

## 2026-10-20 ET (evening): handoff to a fresh coordinator

- **Since the afternoon entry:**
  - Lambertini III: 52 of 82 upheld, 49 pass the checker.
  - Y2LEAD probe: 7 of 50 upheld; the gate failed and the line stops.
  - Lamm III: 2 claims, plus 84 PEB report-date fetch lines.
  - Near-ready fix-ups: 4 claims.
  - Sinclair re-freeze: the owner adoption batch is now 47 NO proposals (Bowditch 15, Sinclair 32).
- **Expected:** ready count rises from 176 by about 60 once the tracker runs on these claims.
- **Next for the new coordinator** (follow `research/plans/CONTINUOUS_PROTOCOL.md`):
  1. Lambertini III batch 02 (8 claims, never reviewed) and re-review of EO 14055, 13986, 13123 and 5624.
  2. Sinclair EO 11209, 13555 and 9294 producer fix.
  3. When the PEB report dates land (84 queued), report-relative claims, after the owner's report-deadline ruling.
  4. Re-run the day review (Llull rank).
- **Lines stopped:** Craigellachie, Y2LEAD, and the Lamm sunsets are exhausted.

## 2026-10-20 ET (afternoon): continuous run, ready 135 -> 176

- **Done:**
  - Claims from Lambertini (per ending instrument), Rastell (EO 12553), Lamm (sunsets) and Bowditch Y2 made 41 of 45 claimed orders ready.
  - claim-kit now ingests reviewed, hash-checked agent-located ACT records (`jobs/claim-kit/act_overrides.py`; 163 records).
  - source-ladder gained Panizzi I/II routes, including report dates via NMB, WCPD and Public Papers.
  - Mountweazel planted controls: plants now live in scratch copies only.
  - Sinclair Y1 sweep: 35 NO upheld of 150, proposals only.
  - Day review: `research/production/day-review-2026-10-20/REPORT.md`, with ranked next workflows and cost per ready order (Lambertini about $1.55, Lamm about $4.40).
- **Protocol** for workflows: a shared PROTOCOL in the coordinator's scratchpad, summarised here.
  - Preregister Llull forecasts (ledger-only commit, no push).
  - Use an independent Opus reviewer with held sources and a D6 step.
  - Producers write to scratch; the planter plants in a scratch review copy; only the tally writes into `research/`.
  - Never retry an auto-mode denial.
- **Push discipline:** never push while a Run jobs run is in progress on the branch. A push makes that run's "Commit results" fail, which lost two claim-checker runs today. Batch commits and push once.
- **Process defects found:**
  - Sinclair's script ran every batch even though the probe gate failed (4 of 5). Gates must be enforced in the workflow script.
  - Sinclair batches 01-05 are stale-generation and need a re-freeze.
- **Next (day-review ranking):**
  1. Lamm III sunsets and the PEB report-date queue (running).
  2. Lambertini III (running).
  3. Near-ready fix-ups (about 7 orders).
  4. Y2LEAD probe of 50, excluding EO 12553 targets.
  5. EO 12553 emergency-board claims (89 orders, about 52 ready) after the owner's report-deadline ruling and PEB dates.
  6. Report-relative claims as dates land.
- **Asks:**
  - `@Owner`, ranked by orders unblocked:
    1. Report-deadline ruling: about 52 ready soon, the most of any ruling.
    2. Transcription-as-copy: Lamm retirement exemptions.
    3. Y1 batch adoption: 15 rechecked, plus 35 Sinclair and 6 current.
    4. ProQuest/NYU request.
    5. Lamm "further exempt" and "until" readings (EO 8554, 8392, 8828, 8058, 7300, 6933).
  - `@Astra`: Lambertini P1 claims EO 10249, 10897 and 12262 overlap your BATCH1_RESERVATION; please reconcile.

## 2026-10-20 ET: thinking tools (Llull, Polya, Mountweazel), Craigellachie, Panizzi; continuous run paused at cost cap

- **Done:** `jobs/llull/` checks plans before they run: Brier forecast ledger, prerequisite census, premortem
  wheel, rank, selfscore. Postmortem of 23 past plans: 12 of 15 scored plans missed, median delivered/forecast
  0.036, 10 of 12 misses mechanically predictable. `jobs/polya/` measures alternative units of work: owner
  rulings reach 89% of not-ready orders; no frame reaches savings_residuals or counterevidence.
  `jobs/mountweazel/` calibrates reviewers with planted defects. MW-C2 caught 9/10 (Opus, packet only),
  8/10 (Opus with sources) and 6/10 (Sonnet); all missed one D6 (removed later event). Use Opus with
  sources plus a D6 step. Bowditch Y1's 0/15 certifies nothing.
  Craigellachie: 23 last-step orders, 0 upheld, all blocked on unheld sources (27 FETCH lines).
  Panizzi: `jobs/source-ladder` now routes citations embedded in prose, plus Public Law and Reorganization
  Plan routes, queue-first (50 items per run); expect about 37 real documents per run.
- **Running:** the source-ladder Actions run from commit b5aeb93d0. Check `jobs/source-ladder/output/STATUS.json`,
  then retry Craigellachie and Bowditch-Y2 orders whose sources arrived (Llull rank #2: Y2LEAD batches).
- **Next (continuous queue, 3 workflows at a time):**
  1. Retry claims after fetches land.
  2. ACT-provision producer probe (reach 1,213).
  3. A unit for savings_residuals and counterevidence.
  4. Own-term family probes.
  5. Mountweazel check fix for D8 false positives.
  6. Routes for 36 unservable lines (report dates, land records).
- **Cost:** session $87.5 of token value; paused at the owner's $100/day cap.
- **Asks:** `@Owner`:
  1. Raise the cap to continue?
  2. Batch adoption of reviewed statuses (reach 11,613)? Re-review Y1 with Opus plus sources first.
  3. Send the ProQuest/NYU request?
  4. Is a compiled transcription an acceptable copy (codebook reading)?
  5. 138 ready and 0 certified: should human review start?

## 2026-10-20 ET: Panizzi, source-ladder now resolves citations buried in prose and works the queue first

- **Done:** `jobs/source-ladder/embedded_cites.py` (+ `ladder_queue.py`, `fetch_ladder.py`, `plan.py`, `job.py`, README,
  `test_panizzi_resolvers.py`; 77 tests pass, and the tests of the jobs that import the ladder pass). Prose-only FETCH_QUEUE
  lines are split into one item per embedded Stat./Pub. L./FR/U.S.C./CFR/Reorganization Plan cite. New routes: Public Law
  by Congress and number (govinfo statute link service, checked back to 52 Stat.), and Reorganization Plan through the
  Title 5 Appendix heading, then the plan's own Stat./FR page. Default plan: queue-first, 50 items, 300 requests, 800 MB.
- **Review fixes (same day):** a Public Law or plan is no longer dropped because of an unrelated Stat. cite (only a cite in a
  volume of that Congress drops it); `5USC3345etseq` gives section 3345; a prose line with a link falls back only to the
  official copy of the SAME document as its link; no Wayback copy of the Title 5 Appendix, and a U.S. Code compilation is
  rejected as a plan's source; the eCFR renderer-API route was removed (robots.txt disallows it); a govinfo PREMIS/MODS
  metadata file is logged but never accepted as the document; no-route items are recorded before the plan.
- **Preview (container, not committed):** the default plan worked 50 queue items: 44 found, 6 retry_later, 108 requests,
  389 MB, 654 s. Of the 44, 5 are NARA finding-aid pages given by the requester and 1 was PREMIS metadata (now rejected).
- **Running:** pushing a non-`output/` change under `jobs/source-ladder/` (or to `research/readiness/`) starts the Actions job.
  Check `jobs/source-ladder/output/STATUS.json`, then `SUMMARY.json` (`found`, `embedded_cite_items`, `bytes_downloaded`).
- **Not fixed:** 52 queue lines still have no route (report dates, land records, agency orders, pay calendars and others);
  files over the shared 100 MB per-file pool bound (27 FR 2983 and 45 FR 44245 issues, 95 Stat. 357 granule).
- **Do not:** treat a found statute or CFR page as authentication, or a current CFR/Code edition as the text in force at the
  order's date (5 CFR 6 is served as the 2026 edition, which does not answer the 1953 question).

## 2026-10-20 ET: Bowditch, the Y2 claim-factory probe failed its gate and Y1 passed

- **Done:** random probe of the funnel plan (`research/excavator/bowditch-2026-10-20/REPORT.md`). **Y2** covered 50
  orders drawn from the 2,022 modern orders with a status and text but no claim. **3 upheld (6%, test needs
  ≥50%)** and 2 of 5 rejected (40%, test allows ≤11%), so it was **not scaled**. Claims are in
  `research/readiness/claims/claude-bowditch-y2-0{1,2}-2026-10-20.jsonl`; all pass the checker. Expect 0-3 new
  ready orders after the Actions tracker run.
  **Y1** covered 50 of the 4,271 no-status modern orders. 15 NO proposals were accepted, with 0 of 15
  reviewer disagreements (limit ≤11%) and about 1.5 agent-min per accepted status (limit 5): **passes**.
  The reviewer came from the same model family, and nothing was adopted.
- **Finding:** Y2 is blocked by missing inputs, not by agent effort. Most orders have no held TERM/ACT ending
  instrument or CURRENT predicate. The probe added 53 FETCH_QUEUE requests. Next: an unblocker that fetches
  ending instruments and current-law predicates in bulk (a job, not agents), then probe Y2 again.
- **Cost:** about $21 of token value for 10 agents (session total $31.67 including Junto).
- **Asks:** `@Owner`: (1) adopt the 15 Y1 NO proposals via batch PR (idea 2 in the funnel plan)? (2) rule on EO
  12080 (spent amending order), 12086 (ledger NO possibly contradicted), 14125 Sec. 4, 9704.

## 2026-10-20 ET: Junto, a scored ledger of token-saving finders

- **Done (branch `claude/junto-1727`):** design `research/plans/JUNTO_DESIGN.md`; `jobs/junto/` (append-only ledger,
  `junto.py run|score|allocate|propose|add-test|check`, 19 stdlib tests); three finders: Hamilton (fitted),
  Clausewitz (friction) and Gallatin (wasted work); five more catalogued but not built. First run:
  `research/production/junto-2026-10-20/REPORT.md`. It produced 13 candidates, **all unverified; every finder
  scores 0 verified $**. Score = verified $ saved / ($ spent + $2 prior). Only `add-test`, with measured before
  and after values, can verify a saving.
- **Next tests:** Watchman (about $1 marginal), Revere (about $3 marginal, on a planned Y1 phase; fix X1's
  phase count first), idle-cache avoidance (about $2).
- **Build cost:** $10.18 of token value and 49 M cache reads in about 50 min, against an estimate of $12-25.
  Hamilton on the coordinator thread: narration 27%, fixed setup 26%, system/user messages 17%.
- **Gap:** session 017gGL is only about 9% read (page 52 copy was blocked by auto mode, and not worked around).
- **Asks:** `@Astra` / `@Codex`: log any saver you try with `junto.py add-test`; never enter estimates as savings.

## 2026-10-20 ET: Hamilton, a token audit of agent sessions

- **Done:** `jobs/hamilton-token-audit/` (offline profiler of `list_events` transcripts) and its first audit,
  `research/production/hamilton-2026-10-20/REPORT.md`. Findings: in X1 the coordinator thread was 72% of
  input-side cost (median context 421 k) against 28% for the 11 helpers doing the research. Fixed setup is about
  70 k tokens per call. Waiting (status checks, a cache rebuild after an idle hour) was about 15%.
- **Proposed tools (probe before build):** Revere (phase handoff to fresh sessions), Watchman (monitoring outside
  big sessions), a setup trim measured by first-call context, and a quiet protocol.
- **Asks:** `@Astra` / `@Codex`: keep coordinators short-lived; start a fresh session per phase with a state file.
- **Do not:** commit raw transcripts. Auto mode blocked one copy of the Oct 16-17 session's transcript as possible
  exfiltration; it was not worked around.

## 2026-10-20 ET: refreshed remaining-work figures; gated funnel for the next excavators

- **Done (branch `claude/great-ptolemy-9r6zah`, restarted from main f57cffe8):** reran `build_remaining_work.py` and
  `build_effort.py` (code untouched; X1 owns it): 135 ready, 86,572 open steps, 16,178 agent-hours (was 17,144;
  APP and CSC transcriptions moved about 3,200 old orders to cheaper text and clause tiers). Dashboard updated:
  https://claude.ai/artifact/531KGTebdrgdeUitKhp8du. New plan `research/plans/EXCAVATOR_FUNNEL_2026-10-20.md`,
  sized only by orders that pass their prerequisites.
- **Finding:** 4,274 modern (1937+) orders have no provisional status, yet 4,273 already have status-history or OFR
  catalog records and 3,952 have their Federal Register text. They are the cheapest pool; both my series plan and X1
  skipped them. 2,150 more modern orders have status and text and wait on claim work.
- **Next:** probes before builds. Y1 modern status sweep (50 orders through `status_overlay`, then a draft
  batch-adoption pull request to `DECIDED_CASE_COMPLETENESS_RECONCILED.csv`, not merged); Y2 claim factory on 50 random
  modern status-plus-text orders, plus the own-terms mechanism.
- **Asks:** `@Owner`: yes/no on batch adoption pull requests; whether to send the NYU ProQuest access request.
  `@Astra` / `@Codex`: whoever picks up Y1 or Y2, record minutes and tokens per order from harness telemetry.
- **Do not:** quote hours saved for Y1-Y3 before their probes run; merge status rows without the owner.

## 2026-10-19 14:10 ET: owner declined paid or manual microfilm acquisition

- **Decision (owner):** no paid reproduction (Harvard Film S 1130 quote estimated at roughly $1.5k-4k) and no
  hand-scanning of microfilm. X3 must rely on free sources: HathiTrust via the owner's NYU login (public-domain PDFs,
  optional, owner's choice), existing jobs, and the negative-search automaton. Do not plan around the reel set.
- **Asks:** `@Astra` / `@Codex` / X1 session: do not request paid copies or manual scanning from the owner.

## 2026-10-19: gap orders routed to public sources; csc-annual-reports job started (branch `csc-annual-reports`)

- **Done:** ProQuest Congressional (owner's NYU login) surveyed: Presidential Materials 1789-1936 hold
  53,671 records, 9,503 tagged Numbered Executive Orders, each with a PDF scan ("Replica of Original").
  Details in `research/pre-1937-sources/PROQUEST_CONGRESSIONAL.md`. The 3,593 `PRIORITY.txt` ids minus 30
  in HathiTrust public volumes = 3,563 (`PROQUEST_RESIDUE.txt`). Routed each by the full WPA/Lord list
  (`wpa-lists` branch): `GAP_ROUTES.md/.csv`. Results: 840 cite a Civil Service Commission annual report;
  about 90 are candidates in other compilations; 2,635 have no known printing (NARA RG 11 or ProQuest only).
- **Running:** `jobs/csc-annual-reports/` fetches the CSC annual reports from the GovInfo Serial Set
  (public PDFs) and cuts each WPA-cited order from its date line. An offline trial on FY 1917 located 67 of
  68 orders. Check `output/SUMMARY.json` (orders_located, by confidence) and `CITATION_RESULTS.csv` for
  misses. Outputs are `compiled_transcription_lead` fragments with `acceptable_as_original: false`.
- **Next:** extract the Panama Canal 1922 and Kappler IV candidates (archive.org texts are free);
  HathiTrust vol. 2 of the Indian reservations orders needs a person in a browser (Cloudflare).
- **Asks:** `@Owner`: `ACCESS_REQUESTS.md` has drafts for NYU (bulk ProQuest access) and NARA (API key), not
  sent. `@Astra` / `@Codex`: the CSC fragments are report printings, not originals; grade them as leads.
- **Do not:** run a bulk ProQuest harvest through the owner's NYU session without NYU's written approval;
  treat WPA dates as verified signing dates.
## 2026-10-19 13:15 ET: X1 lifecycle class engine built, piloted on all 52 eligible old orders, recalibrated

- **Done (branch `claude/x1-class-engine`, PR to main):** `jobs/x1-class-engine/` (zero-token job): type
  classifier for all 8,014 pre-1937 orders (`TYPES.csv`; 198 unknown), 22 type rules in
  `research/readiness/type-rules/` (`eo-type-rule/v1`, three rounds of independent AI review, frozen hashes),
  5-event extinction register (`data/EVENTS.json`; 8 primary sources queued, none held yet), look-alike clusterer
  (656 texts, 132 clusters, 187 clean clones), 128 batch sheets. Report: `research/production/x1-2026-10-19/REPORT.md`.
- **Measured:** classifier on a fresh blind holdout of 80: exact type 90% (CI 82-95%), class 95%. Pilot: all 52
  pre-1937 orders that have both a provisional status and a held text (the canonical path's ceiling), in two batches;
  6 submitted, 5 upheld by an independent AI reviewer, 1 rejected (17%, above the 11% target); 46 blocked, all
  blocks confirmed. 25.4 agent-minutes in all: 0.49 min per order screened, 5.1 min and 153k tokens per accepted
  claim (harness telemetry, `AGENT_TELEMETRY.jsonl`). Claims: `research/readiness/claims/claude-2026-10-19-x1-pilot.jsonl`
  (EO 5614, 5707, 5881, 5981, 5982); actual claim-checker passes all 5 on every step, and the tracker on the branch now counts them ready for human review (130 → 135). PR #36.
- **Recalibrated** (`MEASURED.json`, `excavator_scenarios.py` now reads X1 types and measured values): X1 saves about
  463 h (assumed 4,134 incl. the unapproved review change); about 16,681 h left after X1; series without risk-tiered
  review about 11,256 h. Bug found and documented: census-gap rows were counted as "other", not land.
- **Finding:** typing is not the bottleneck for old orders; originals, end instruments and provisional statuses are.
- **Asks:** `@Owner`: (1) risk-tiered review stays off (flag `X1_RISK_TIERED_REVIEW`, default off) until you decide;
  (2) a route to CSC annual reports / Official Register would date the 1,490 one-person waivers. `@Codex` / `@Sol`
  (claim-kit): an own-terms end mechanism (EO 5763, 5930 blocked only by this) and locating the EO 7968 and EO 5707
  provisions in dossiers (6 rows). `@Astra`: EO 5874 is recited by EO 5881 but is not in the identity universe;
  check as a census gap. Anyone: the 5,297 `status_first` rows need a provisional-status path before X1 sheets help.
- **Do not:** treat X1 types, rules, events or clones as findings; enable risk-tiered review without the owner;
  reuse the round-1/2 rule files (superseded; only hashes in `TYPE_RULES_REVIEW.json` are frozen).

## 2026-10-19 13:30 ET: excavator series plan to cut the remaining agent-hours

- **Done (branch `claude/great-ptolemy-9r6zah`):** `research/plans/EXCAVATOR_SERIES_2026-10-19.md`, a funnel of ten
  ideas and a selected series of five excavators (X1 lifecycle class engine, X2 Public Land Order ledger, X3
  reel-to-text acquisition with a negative-search automaton, X4 living-law counter-search, X5 census gap admission
  line). `research/progress/remaining-work/excavator_scenarios.py` scores each idea alone and the series without
  double counting: 17,144 to about 9,100 agent-hours (47% less). Coverage sets come from committed data; hit rates and
  new minutes are assumptions in the script. `build_effort.py` now exposes `assign()`; outputs unchanged.
- **Finding:** 83% of the hours are pre-1937 orders; 7,065 h are pre-1937 orders of unknown type, so a type classifier
  is the first build.
- **Asks:** `@Owner`: (1) a route to a full-text source for EO 1-7403 (microfilm Film S 1130 at Harvard Lamont, or
  HeinOnline via a law library); (2) yes/no on risk-tiered review (20% independent-AI audit for rows matching a
  reviewed exemplar). `@Astra` / `@Codex`: pick up X1 step 1 (type classifier) or X2 (PLO harvester) as jobs; pilot
  50 orders and record minutes per step and tier.
- **Do not:** treat the scenario savings as measured, or let any excavator fill judgment fields or admit orders.

## 2026-10-19 12:30 ET: remaining work weighted by AI effort (second treemap tab)

- **Done (branch `claude/great-ptolemy-9r6zah`):** `research/progress/remaining-work/build_effort.py` gives every
  open step (same 86,607 as the count view) an AI agent-minute weight from `EFFORT_MODEL.csv`, by tier: what the
  jobs already hold for that order (clause-drafts, status-history, later-events, family-rules certificates,
  fr-originals, numbered-early-orders, claim-drafts `only_judgment_left` and `estimated_effort`). Method and the
  basis of each weight: `EFFORT_NOTES.md`. Outputs `EFFORT_LONG.csv`, `EFFORT_BY_TIER.csv`, `EFFORT.json`. Shown as
  the "AI effort" tab of https://claude.ai/artifact/531KGTebdrgdeUitKhp8du#effort. `build_remaining_work.py`
  now exposes `attribute()`; its outputs are unchanged.
- **Result:** about 17,144 agent-hours (range 8.6k-34k), about 63 min per APP order. Ending/current basis 5,625 h,
  original text 3,025 h, savings 2,612 h, counterevidence 2,297 h, clauses 1,889 h, first yes/no 1,337 h, admit
  328 h, sources/images 18 h. Pre-1937 orders about 90-108 min each, modern about 25 min. FDR, Wilson and Coolidge
  together 47%.
- **Calibration:** only CI1+EB2+SR2+CE2 (25 min) are calibrated, from Codex's batch pilot (about 26 agent-min per
  upheld modern dossier, `research/excavator/2026-10-18/batch-pilot/COST_COMPARISON.json`); OT1 uses Astra's
  measured source-read time; all other weights are assumptions.
- **Asks:** `@Astra` / `@Codex`: when the instrumented 40-80 order pilot runs, record agent-minutes per step and
  tier so `EFFORT_MODEL.csv` can be replaced with measured values; the build reruns in seconds.
- **Do not:** quote the agent-hour total as a measurement or a schedule.

## 2026-10-19 11:45 ET: remaining-work treemap against the APP count

- **Done (branch `claude/great-ptolemy-9r6zah` from main `a6d61007`):** `research/progress/remaining-work/build_remaining_work.py`
  (offline, reads committed outputs only) writes `REMAINING_WORK.json`, `REMAINING_WORK_BY_PRESIDENT.csv` and
  `REMAINING_WORK_LONG.csv`. Unit: one open readiness-tracker step for one order. Orders APP counts but the project
  does not hold (per president, APP count minus project orders, when positive) each add one "admit" step plus the six
  core steps. Owner's treemap dashboard: https://claude.ai/artifact/531KGTebdrgdeUitKhp8du (private until shared).
- **Measured:** APP counts 16,239 orders; the project holds 14,972; 1,314 APP-counted orders are not yet held (net
  1,267; Coolidge has 44 more in the project than APP counts, 18 NARA unnumbered rows sit outside any president's APP
  count by date). 86,607 open steps vs 13,503 done (13.5%). 130 ready for human review. Open steps by kind: ending or
  current basis 16,152; savings 16,120; clause inventory 16,108; counterevidence 13,816; first yes/no 12,927;
  original text 9,414; admit 1,314; shared sources + Opus media 756.
- **Attribution of orders to presidents:** APP index 9,918; exact WPA/NARA/Lord date 3,122; numbered neighbours
  agreeing on both sides 1,772; year only 158; nearest neighbour 2. Boundary years can still be off by a few orders.
- **Next:** rerun the script after each readiness-tracker run; it is cheap (seconds).
- **Asks:** `@Owner`: share the dashboard from its Share menu if others should see it.
- **Do not:** read the per-president gap as a census finding; APP's pre-1945 counts are editorial (Ragsdale/Lord).

## 2026-10-18 20:15 ET: app-executive-orders, live lane finished; capture audit 205/205 agree; PRIORITY rebuilt (3,593)

- **Done (branch `app-executive-orders`, one commit):** the live lane completed at 23:58 UTC (`output/STATE.json`
  remaining 0, complete true, 0 failures; 792 live pages, 10,270 archive captures, 10,998 texts). Harvester and the
  resume loop have exited; **no APP crawler is running.** `output/MIRROR_AUDIT_SUMMARY.md`: every 50th
  archive-covered path in path order (206), fetched live at 10 s between 23:05 and 23:58 UTC; **205 of 205 compared
  texts agree byte-for-byte** (Common Crawl 194/194 across capture years 2024-2026, Wayback 11/11 across 2022-2026);
  no disagreements to list; page hashes differ on all 205 (chrome, expected). The 206th sample path (EO 5382) had
  been fetched live before the archive reached it; its recorded hashes agree too. `data/PRIORITY.txt` rebuilt:
  **3,593 numbered census orders have no saved text of any kind** (was 6,070). **3,585 of them APP does not list at
  all** (3,529 below EO 5000, 56 at EO 5000+, e.g. EO 5000-5018, 6447-6466). The other 8 are listed but APP's page
  is "[Not Published.]" (EO 8302, 9132A, 9427A, 9451A, 9457, 10026A, ...). So the APP lane is exhausted: nothing
  left to fetch from APP.
- **Fix in `build_priority.py`:** claim-kit's discovery globs `FRAGMENTS*.jsonl`, so the archive lane's
  `MIRROR_FRAGMENTS.jsonl` (9,387 records) was invisible and the plain rebuild gave 5,652, leaving 2,059 orders with
  saved archive text on the list. The builder now also counts this job's own fragments (hash-verified): +2,090 held.
- **Caveat:** 183 ids absent from the 16:36 list reappear now (e.g. EO 28, 29, 219, 860, 1136); they are `open` in
  the readiness tracker and in no job's FRAGMENTS/SOURCES, so I could not see what held them earlier. Cause not found.
- **Next:** second index pass with a different sort for the 38 duplicate listing rows; owner's decision on the
  Common Crawl captures (19:15 entry) still open.
- **Asks:** `@Astra` / `@Codex` (whoever maintains claim-kit): decide whether `jobs/claim-kit/inputs.py` discovery
  should match `*FRAGMENTS*.jsonl` so the 2,090 archive texts reach the readiness pipeline, or whether the archive
  lane should write `FRAGMENTS_MIRROR.jsonl` instead; I changed neither. Also: `load_corpus` emits 1,310
  `text_sha256 mismatch; skipped` warnings for FRAGMENTS records in family-rules (582), ofr-compilations (500),
  isthmian-canal-1911 (105), richardson-volumes (68) and indian-reservations-1912 (55) that point at
  `jobs/clause-drafts/output/texts/cd-job-fr-originals-*.txt`; the files match their git blobs, so the recorded hashes
  are stale (clause-drafts regenerated texts after those jobs ran). 728 orders lose their held text in claim-kit
  until those jobs rerun. `@Owner`: the archive lane's stance question (19:15 entry) still needs your call.
- **Do not:** hand-edit `jobs/app-executive-orders/output/`; count APP or capture texts as originals.

## 2026-10-18 19:15 ET: app-executive-orders, archive lane: 30 h crawl collapsed to a 67-page residue

- **Done (branch `app-executive-orders`, commits `5d97ee47`, `78e7d795` + outputs):** `jobs/app-executive-orders/app_mirror.py`,
  an archive lane that reads public web-archive captures of the same APP pages instead of asking APP: WARC byte ranges
  from Common Crawl (`data.commoncrawl.org`, crawls 2024-10 to 2026-04) and original bytes from the Wayback Machine
  (`web.archive.org/web/<ts>id_/`). It never sends a request to APP, so it runs four workers. Result: **10,270 pages in
  about 55 minutes** (9,861 Common Crawl, 409 Wayback), `output/MIRROR_DOCUMENTS/SOURCES/FRAGMENTS.jsonl` (9,387
  claim-kit fragments for numbered orders), `texts/` now holds 10,727 order texts. 47 captures hold no text
  (APP's own "[Not Published.]" pages, recorded in `MIRROR_FAILURES.jsonl`); 66 index pages have no capture anywhere.
- **Live lane:** `app_harvest.py documents` now skips every archive-covered path except an `--audit-every 50`
  sample (about 205 pages) that it fetches live and compares in `MIRROR_AUDIT.jsonl` (text and page hash agreement
  plus capture date), so the captures carry a measured staleness rate. The residue it still owes APP is **67 pages**
  (44 priority orders), about 11 minutes at 10 s. APP answered HTTP 504 twice tonight (21:53 and 22:26 UTC) and the
  harvester stops on 5xx by design; a resume loop on the owner's PC (`%LOCALAPPDATA%\Temp\live_resume_loop.ps1`,
  log `~/.cache/app-documents-2.log`) reruns the documents phase after a ten-minute pause, at most six rounds, never
  retrying the failed request immediately.
- **Caveats for readers of the captures:** a capture is the APP page as of its capture date (2018-12-09 to
  2026-10-16; each record names archive, crawl and `captured_utc`), route `archive/<archive>/american-presidency-project`,
  grade `mirror_transcription`, `acceptable_as_original=false`. APP's robots.txt now disallows CCBot outright, so the
  2026 crawls hold nothing and the captures predate that rule; the owner should judge whether reading those public
  datasets fits the project's stance toward APP. Nothing here changes census, ledger, codebook or certified counts.
- **Next:** read `MIRROR_AUDIT.jsonl` once the audit sample is in and report the disagreement rate; rebuild
  `data/PRIORITY.txt` against the new texts; second index pass with a different sort for the 38 duplicate rows.
- **Asks:** `@Owner`: decide on the Common Crawl captures (above); approve committing crawl progress as it lands.
  `@Astra` / `@Codex`: `MIRROR_FRAGMENTS.jsonl` is discovery material only, same as `FRAGMENTS.jsonl`.
- **Do not:** run a second APP crawler while the resume loop is alive; hand-edit `jobs/app-executive-orders/output/`.
## 2026-10-18 17:15 ET: numbered-early-orders, printed texts for 184 of the 3,324 undecided orders 1-5075

- **Done (branch `numbered-early-orders` from main `224fd70c`, PR to main):** `jobs/numbered-early-orders/`
  matches the 3,324 census all-no numbered orders below 5076 (`data/TARGETS.csv`, with the WPA 1944 date and
  summary from `wpa-lists` commit `121ca07e`) against printed books, by number or by exact date plus
  summary words. It imports early-orders-hunt unchanged and declares hits in wikisource-texts' shape
  (`government_printed_copy`, `acceptable_as_original=false`, book URL, image, page, line span, hashes).
- **Measured (local run):** 184 orders, 197 texts. 41 came from books already held (MR 1916 37, MR 1910 2,
  Richardson IX 2, IR 1912 1). 143 came from new books: Civil Service Commission reports for FY 1914, 1915,
  1918 and 1922 (95), Kappler IV (26), Official U.S. Bulletin (17), Panama Canal 1921 (6). Kappler III gave
  0. 3,140 orders still have no text. claim-kit's loader recognized all 197 texts with no warnings.
- **Blocked:** the Archive holds only four 1908-29 CSC reports. The full run is on HathiTrust behind a
  Cloudflare bot challenge, not fetched. The Archive's 1975 Indian-reservation reprint is a lending copy.
- **Known false positive:** EO 860 matched on a citation inside a later order. Every hit must be read
  against the scan.
- **Running:** the job's first GitHub run on this branch. Check `output/STATUS.json` and `SUMMARY.json`.
- **Asks:** `@Owner`: a sanctioned route to the remaining CSC annual reports (1909-13, 1916-17, 1919-21,
  1923-29) would reach most of the remaining 695 civil-service waivers.
- **Do not:** count these texts as originals or as decided orders.

## 2026-10-18 16:45 ET: app-executive-orders, American Presidency Project index, statistics and texts

- **Done (branch `app-executive-orders` from main `224fd70c`):** `jobs/app-executive-orders/app_harvest.py`
  (phases `statistics`, `index`, `documents`; offline tests in `test_app_harvest.py`). The full APP
  "Executive Orders" category index is committed: 10,840 documents (1791-01-22 to 2026-10-16), 9,949 distinct
  numbered EOs, 890 unnumbered (`output/INDEX.csv/.jsonl`). The APP statistics table (65 rows, by president
  and term, last updated 2026-10-16) is committed with its methodology, notes and sources (`output/STATISTICS.*`).
- **Priority:** `build_priority.py` → `data/PRIORITY.txt`: 6,070 numbered census orders with no saved text
  (claim-kit loaded texts ∪ readiness-tracker `step_original_text=done`). 2,661 of them are on APP, mostly
  EO 5000-8999 (Hoover/FDR); the documents phase fetches those first (about 7.5 h), then the rest.
- **Running (owner's PC, detached):** `documents` phase, one request per 10 s (APP robots.txt Crawl-delay: 10;
  APP blocks AI-training crawlers by name and reports stability problems, so do not parallelise requests or move
  this to a runner while it runs). Log `~/.cache/app-documents.log`; progress `output/STATE.json`. Rerunning
  resumes. Output per order: text, APP footnote (Federal Register note or APP editorial note, e.g. EO 1071's
  Richardson misidentification), citation/node, categories, raw-page SHA-256; FRAGMENTS.jsonl in claim-kit shape.
- **Caveat:** the listing produced 38 duplicate rows across pages (sort ties shifting during pagination), so a
  few documents may be missing from the index; a second index pass with a different sort would check it.
- **Asks:** `@Astra` / `@Codex`: APP texts are `secondary_compilation_transcription`,
  `acceptable_as_original=false`; use them for discovery and clause reading, not custody. `@Owner`: commit
  crawl progress now and then (`git add jobs/app-executive-orders/output && git commit`).
- **Do not:** count APP texts as originals or decided orders, or run a second APP crawler concurrently.

## 2026-10-18 14:30 ET: census-completeness, a measured answer to "have we looked everywhere?"

- **Done (branch `census-completeness`, stacked on `early-orders-hunt`; local only, nothing pushed):**
  - `jobs/census-completeness/`: treats every list of pre-1900 orders the project holds as a capture of one population
    (Lord 1943; Richardson VI/VII/IX documents from `richardson-volumes`; the 1912 Indian-reservation acts; dated
    "Executive order" mentions read from the MR and GLO books `early-orders-hunt` fetched; the WPA numbered list is
    kept only to set numbered orders aside), matches mentions conservatively (same day and a shared distinctive word,
    or a citation link the earlier job made; a date alone never matches), and estimates the undiscovered remainder
    per era with the Mt maximum-likelihood estimate (Darroch) and its asymptotic interval, Chapman two-list estimates
    against Lord, and Chao1 as a check. Three matching scenarios bracket the result (strict, blind-only, every
    same-date pair as one order). Assumptions and the direction of each bias are written into the outputs. 12 tests,
    including recovery of a synthetic hidden population of 400.
  - `data/SOURCE_UNIVERSE.csv`: a 40-row series-level map of where orders could be (NARA record groups 11, 45, 56,
    59, 75, 94, 107, 48/49; LOC presidential papers; Founders Online; the printed compilations; newspapers) with
    each series' search status in this project. Only 8 rows are `searched_to_end`.
  - `research/plans/SCAN_REQUESTS_2026-10-18.md`: three draft reference/scan-request emails (NARA Archives I for
    RG 107 letters received 1789-1861; NARA for GLO/BIA reservation files; LOC Manuscript Division for the
    1841-1861 presidents' outgoing letters) plus a reproduction-order template. Drafts only; nothing sent.
  - Measured (local, books from the hunt's first six fetches): 1,394 distinct unnumbered orders 1789-1899 observed.
    1801-1861: 213 observed, Mt total 316 (269-362), undiscovered 43-103 depending on matching. 1862-1899: 1,174
    observed, Mt total 1,729 (1,634-1,825), undiscovered 295-555. Lord lists 31% of president-signed documents in
    Richardson VI and 51% in Richardson IX. All lower bounds: Lord cites these books, so the lists are positively
    dependent, and orders that reached no printed compilation are invisible to every list.
- **Running:** nothing. `early-orders-hunt`'s first GitHub run (PR #25) was in progress at the time of writing;
  this job reads its `output/books/`.
- **Next:** push after PR #25 lands (the branch stacks on it); a person settles the 260 pre-1862 ambiguous pairs;
  adjudicate the 72 president-signed Richardson VI documents Lord does not list against the codebook; draw the
  random audit months and send the three emails; add Kappler and the Civil Service Commission reports to the hunt
  registry (338 and many Lord citations respectively, none fetched).
- **Asks:**
  - `@Owner`: review the three draft emails and the audit-month sampling before anything is sent; approve pushing
    `census-completeness` once PR #25 is merged.
  - `@Astra`: the Mt/Chapman/Chao1 choice and the dependence argument in `complete.py` would benefit from your
    adversarial read; the estimators are population-level by construction.
- **Do not:** quote any undiscovered count without its bracket and the dependence caveat; treat an unmatched book
  mention as a missing order (AMBIGUOUS_MATCHES.csv exists for that); admit anything from these outputs.

## 2026-10-18 13:00 ET: early-orders-hunt, a zero-token job that goes and gets the printed texts of 1789-1899 orders

- **Done (branch `early-orders-hunt`, from main `43f415dd`; local only, nothing pushed):**
  - `jobs/early-orders-hunt/`: reads Lord's 1943 unnumbered list (the `wpa-lists` parse, or a committed pre-1900
    subset of it with hashes in `data/PROVENANCE.json`), the 1,023 Stage 14 scan date markers and the six Stage 18
    candidates; parses every printed-source citation (Richardson vol/appendix/page, `YEAR MR page`, `YEAR GLO page`,
    Statutes at Large, Annals, American State Papers, Kappler, Sparks, documents, newspapers); fetches each cited
    book once from the Internet Archive (`data/BOOKS.json`: Richardson GPO vols I-X, the four War Department
    reservation books 1898-1916, fifteen GLO annual reports), checks the Archive's sha1 and the edition (the Bureau
    of National Literature Richardson reprints are repaginated and are refused), maps printed pages from running
    heads, and cuts the passage carrying the lead's date or subject into `texts/` with image, page, line span and
    hashes. Pre-1862 leads with a day date and no book text get bounded loc.gov collection searches (Chronicling
    America, the president's papers), responses saved by hash. Richardson VI/VII/IX are read from
    `jobs/richardson-volumes/data/`, not downloaded again. 20 offline tests (a fake Archive serves a synthetic book).
  - Measured locally (6 books, 327 s, 120 MB, 26 requests): 1,994 leads (320 pre-1862); 6,744 citations
    (4,775 GLO, 1,050 MR, 436 Richardson); 2,261 citations resolved to a page, 1,594 with date and subject on it;
    **texts cut for 950 leads, 125 pre-1862**; heads agreed with the page map on 93-100% of readable pages.
    Spot-read: Washington Barracks (MR 1916 p. 52, "announced by Executive order dated July 25, 1798"), the 1838
    Pensacola live-oak reserve, the 1827 Bois Blanc fuel reserve all cut correctly. A second run confirmed the
    alternate-copy fallback: the first `GLO_1893` copy was an 84-page extract (0 texts); the full copy gives 273.
  - Telemetry: zero model tokens in the job; this session's agent time about 2.5 h including the survey.
- **Running:** nothing on GitHub yet. Outputs are in the session scratchpad only.
- **Next:** push the branch and run the job once on GitHub (`HUNT_MAX_BOOKS` default 12; the cache carries fetched
  books to the next run, so three runs cover the registry); then have a person read 10-15 pre-1862 slices against
  the scan images; then put `RICH_X` (appendix) and `RICH_VIII` page files into `richardson-volumes` with one
  PROVENANCE entry each, so its parser splits them into orders. `GLO_1886`, `GLO_1897` and `GLO_1901` still need an
  Archive identifier (candidates listed in `books/<key>.json`).
- **Asks:**
  - `@Owner`: approve pushing `early-orders-hunt` and running it on GitHub.
  - `@Astra`: the `wpa-lists` branch is still unmerged; the job falls back to a committed subset of its output.
    When it merges, nothing changes except the source line in `SUMMARY.json`.
- **Do not:** treat a `texts/*.txt` slice as the original or as an identity: it is OCR of a printed compilation and
  a lead for `original_text`; signer, capacity and inclusion stay with the reviewer. Never write a search with
  no results into `EXHAUSTED.jsonl`.

## 2026-10-18 02:00 ET: printed volumes wired in; 176 claims from the 1989 Codification / FR revocation families; ready 1 -> 130

- **Done (branch `wire-new-sources`, local only, nothing pushed):**
  - Wiring (commits `33028c03`..`150c0457`): merged `ofr-compilations`, `indian-reservations-1912`,
    `isthmian-canal-1911`, `ofr-codification-1989` and `richardson-volumes`. The tracker counts official
    compilations like fr-originals (only finds not flagged `needs_page_check`); Richardson is a lead only
    (new blocker `ONLY_COMPILED_TRANSCRIPTION_FOUND`, 68 orders, 2 decided). claim-checker holds the committed
    volumes and their per-order texts; claim-drafts reads the printed-volume jobs. No order lost a step.
  - Claims: `research/readiness/claims/claude-2026-10-18-codif-b0.jsonl` .. `-b7.jsonl`, 176 decided orders
    (all provisional `no`), copied byte for byte from the reviewer-accepted files. 197 drafted, 21 rejected
    by the reviewers (10.7%): per batch 0/28, 2/23, 2/25, 0/24, 4/26, 12/24, 1/23, 0/24. 132 are complete
    claims (full gate pass); 44 are partial (ending, and sometimes savings/clauses, left open in
    `unresolved_material_gaps`, e.g. where only a deadline or a temporary body's term bounds the end).
  - Method: 59 families, each one revoking or superseding order (actor) taken from the 1989 Codification
    disposition tables and the Federal Register job (largest: EO 11708, 12534, 11408, 11342, 11230, 11811,
    11812, 12110, 9687). For each family the acting order and every target were read in the held official
    FR/OCR text; `first_end.date` is the effective date stated or implied in the acting instrument; the
    order's own terms (expiry, temporary bodies, conditions), earlier partial amendments and statutes were
    checked before taking the revocation as the end; partial amendments are not whole-order ends; deadlines
    never fix an actual end date; quotations are word for word from the held text. No statuses, ledger rows,
    codebook or counts changed; no `independent_human` reviews written.
  - Excluded: every order already in `research/readiness/claims/`, every Astra-owned order and family
    (EO 12076 and EO 12399 were in planned families and were left out), all targets of EO 12553.
  - claim-checker (local, downloads off), the 176 new claims: mechanical pass 176/176, 0 fail, 0 unverified;
    full gate 132; steps passed: original_text 176, clause_inventory 171, ending_or_current_basis 132,
    savings_residuals 159, counterevidence 166. Every quotation exact (3,164 across all 218 claims).
  - Tracker (local run with this run's checker output) vs main's committed `SUMMARY.json`, decided orders
    (3,359): ready_for_human_review 1 -> 130 (129 of the new claims + EO 13306); original_text 2,281 -> 2,312;
    clause_inventory 7 -> 177; ending_or_current_basis 2 -> 133; savings_residuals 7 -> 160;
    counterevidence 2,461 -> 2,470. With downloads off, six of Astra's claims (EO 14134-14139) show
    `CLAIM_CHECK_FAILED` locally (their govinfo PDFs are record-only here; GitHub re-downloads and verifies
    them). Taking GitHub's committed result for those six (same claim hash) gives 178 / 134 / 166 and no
    step lost anywhere; expect those numbers on GitHub.
  - Of the 47 new claims not ready: 44 are partial (`CLAIM_INCOMPLETE`; EO 11811 and EO 9407 are also
    quarantined); the complete claims for EO 11708 and EO 11812 are blocked by
    `QUARANTINED_RELATIONSHIP_CONFLICT`, and EO 9789 by `OPUS_MEDIA_REFETCH_NEEDED`.
  - Telemetry: token and wall-time per order were not measured in this integration step.
  - Run order (`390fa519`): `ofr-codification-1989` no longer lists `readiness-tracker` in `after.txt`; with
    `claim-drafts` now after the codification job, that made a cycle the runner broke silently (tracker before
    `claim-drafts`). Simulated order: codification, claim-drafts, readiness-tracker, case-bundles, daily-digest.
  - Known gap (not fixed): claim-checker now holds the Richardson volumes, and neither the gate nor the checker
    tests that `original_representation` is an official original, so a hand-written claim citing Richardson
    could pass `original_text`. None of the 176 claims does; worth a checker rule before anyone relies on it.
- **Running:** nothing. Local outputs only, in the session scratchpad `final_run/` (not committed).
- **Next:** push `wire-new-sources` and open one PR once the owner approves; let GitHub rerun claim-checker,
  claim-drafts and the tracker. Then the 44 partial claims (find the actual end of temporary bodies and
  deadline-bounded clauses) and the next Codification families.
- **Asks:**
  - `@Owner`: review and approve pushing `wire-new-sources` (wiring + 176 claims) as one PR.
  - `@Astra`: before claiming an order in a family whose actor is EO 11708, 12534, 11811, 11812, 12110 or
    9687, check `claude-2026-10-18-codif-b*.jsonl`; those targets are claimed here.
- **Do not:** edit the `claude-2026-10-18-codif-b*.jsonl` lines (a changed claim waits for a new check);
  treat a passed claim as a human review.

## 2026-10-17 20:45 ET: custody unblocked, machine later-source search, Opus re-fetch list

- **Done (branch `unblock-claims`, one PR):**
  - `jobs/official-fixity/`: GPO's published SHA-256 for every govinfo file: 3,384 byte-identical, 0 mismatches.
  - claim-checker counts a source as held when GPO publishes those exact bytes, or when a record-only govinfo PDF is re-downloaded and matches. Before this, **every** cited source showed `custody_record_only` on GitHub, so no claim step could ever pass; 116 of the 211 references in Astra's first claims are now GPO-verified.
  - The tracker counts `counterevidence` from the machines' complete bounded searches (OFR catalog, 7,619 saved texts, full U.S. Code and eCFR) when nothing contrary was found: **0 → 2,461 decided orders**.
  - The pdfplumber recheck: 155 upgrades.
  - The opus-media-match re-fetch list, which never reached main.
- **Asks:**
  - `@Astra`: copy `jobs/readiness-tracker/output/MACHINE_LATER_SEARCH.jsonl` (claim-shaped `later_source_search`) into claims instead of writing searches by hand.
  - `@Astra`: cite `jobs/official-fixity/output/MATCHED_BY_SHA256.json` before setting a rule's `original_custody_verified`, and add `official-fixity` to `jobs/family-rules/after.txt`.
  - `@Astra`: consider batch review sheets in the production swarm: one compact table of 50-100 same-type orders (for example single-paragraph orders, where the clause inventory is one clause), approved row by row and converted to claims by a job.
  - `@Astra`: the 172 orders with `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` are judgment work for P3/P1.
- **Do not:** treat the machine search step as a legal conclusion; it records what was searched and that nothing contrary turned up.

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
