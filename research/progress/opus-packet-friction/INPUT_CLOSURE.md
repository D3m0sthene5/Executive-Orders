# Input closure: jobs/claim-kit and jobs/valla

**Coordinator note for Sol (Opus, 2026-10-29).** This is a handoff, not a change. Sol owns any `needs.txt` /
`inputs.txt` / `after.txt` / `triggers.txt` edit for these jobs; Opus will not edit them. Inventory drafted by a
Sonnet worker. Opus spot-checked R1 (`factual_events.py:13-16` executes `jobs/norton/model.py`), R4 (factual
evidence `raw_path` under the untracked `.job-cache/source-ladder/`, read by `norton/model.py:83`) and the current
`needs.txt` / `after.txt` text, and all three hold. What matters for narrowing:

1. **Context A is the runner job.** Its genuine closure is the "needed" rows below. U1–U4, U7–U9 look like
   historical blanket availability rather than reads, but `inputs.txt:1-5` says some blankets are deliberate for
   future producers. Narrow them only together with an equality check on `INDEX.json` and `SUMMARY.json`.
2. **Context B is never run by the runner** (only its unit tests are). Agents run it on full checkouts.
   `prior_research` and Valla deliberately discover over all of `research/**` and all tracked packages. A packet
   prepared or verified in a narrower checkout gets a different sealed context and fails `load_packet`. So do not
   reuse a runner-narrowed checkout for packet work.
3. **Valla job.** A tracked package missing from the checkout changes `INDEX.json` silently (it is only listed as
   unmaterialized). If Valla's checkout is narrowed, keep every tracked
   `research/{excavator,production}/**/{RATIONALES.json,decisions.csv,clauses.csv}`.
4. **R4 is a correctness gap independent of narrowing.** Two factual records depend on untracked cache PDFs, and
   their absence silently drops a factual event. It is recorded here for the owner of `norton`/`source-ladder`;
   claim-kit is not changing it in this PR.

Documentation only. No code or declaration file was changed. Machine-readable twin: `INPUT_CLOSURE.json` (every entry there has path or glob, discovery, category, needed label, readers as file:line, and the declaring file).
Checkout: branch `opus/packet-friction`, HEAD 71b06f9.

**Contexts.** A = runner `job.py`. B = agent CLI (`kit.py prepare/view/apply/batch-check/complete`, `source_supplement prepare/verify`, `valla attach`).
**Method.** Full read of the listed modules, plus an audit-hook trace of `load_corpus`, `act_overrides.load`, `population.validate_inputs`, `working_text.Index`, `enrich_current` (claim-kit A) and of `valla.build` (valla A), compared with `result_freshness.scope()`. The full `build()` was not run (it writes into `jobs/claim-kit/output`).

## How the runner treats declarations (read first)
- Freshness scope (`result_freshness.py:40-58`): roots are `jobs/<name>`, `jobs/_lib`, `.github/scripts`, the workflow, **every needs.txt line**, and `jobs/<dep>/output` per after.txt. Patterns are **triggers.txt plus inputs.txt**. So a needs.txt or triggers.txt line both materializes and fingerprints.
- `prepare()` (`:82-100`) materializes the parent directory of every skip-worktree file that a pattern matches. inputs.txt patterns therefore already pull in what they name.
- needs.txt goes through `git sparse-checkout add` (`run_jobs.py:270-274`). Cone mode: a directory line is recursive; a file line pulls only its parent's direct files (tested on a scratch repo).
- The checkout is `.github jobs HANDOFF` plus needs (`run-jobs.yml:50-57`); `jobs/` is always present. `filter: blob:none, fetch-depth: 0` keeps the full git index, which `valla` relies on.

## Mismatches

**Read but not declared**
| # | Job / ctx | Item | Evidence |
|---|---|---|---|
| R1 | claim-kit A,B | `jobs/norton/model.py` | executed at import `factual_events.py:13-16`; pinned `batch.py:33-34`, `completion.py:624`. claim-checker and readiness-tracker declare it; claim-kit does not (after.txt `norton` = output only). |
| R2 | claim-kit A | tests import `jobs/valla/{valla.py,premises.json}`, `jobs/claim-checker/{checker.py,sources.py,data/opus_manifest_index.csv.gz}`, `jobs/readiness-tracker/{tracker.py,test_tracker.py}` | `job.py:9` runs the suite; `test_batch.py:35-55`, `test_factual_events.py:210-239`. Present (jobs/), but not fingerprinted or triggering. |
| R3 | claim-kit A,B | `jobs/source-ladder/{embedded_cites,fetch_ladder,ladder_queue,report_dates}.py`; `jobs/norton/{job,norton,test_norton}.py` | hashed through norton `INPUTS.json` (`inputs.py:380-389`). |
| R4 | claim-kit A,B | `.job-cache/source-ladder/ladder/blobs/**.pdf` | factual evidence `raw_path` (2 records) read at `norton/model.py:83`. Untracked cache; invisible to `git ls-files`-based capture and prepare. Absence silently drops the factual event. |
| R5 | claim-kit | anchors `releases/`, `progress/`, and `jobs/X/**` outside output/data | `inputs.py:86`, `current_evidence.py:22`. None used by today's 142,532 text paths; other pointer fields unverified. |
| R6 | claim-kit B | `jobs/status-history/history.py`, `jobs/valla/valla.py` as code | `status_overlay.py:66-71`, `batch.py:299-304`. |
| R7 | claim-kit B | all `research/**/*.json{,l}`, `owner_rulings/*.md`, arbitrary pinned dependency paths | `prior_research.py:82-125, 332-401, 485-493`; used by `prepare` and by `load_packet` (so also `view/apply/batch-check/complete`). Any missing file changes the sealed context and fails `changed prior research` (`batch.py:277`). |
| R8 | valla A,B | review_ref, reviewed_claim_ref, dependency-key targets outside the declared set | `valla.py:308-318, 333, 361-364, 399, 402`. Today all inside the declared set. |
| R9 | claim-kit | `jobs/claim-kit/output/SUMMARY.json` (self) | `inputs.py:587` omits the claim-kit exclusion that `:499` has. Absent in the runner, excluded from the fingerprint, no `machine_searches` key. Harmless. |

**Declared but not read (A)**
| # | Declaration | Evidence |
|---|---|---|
| U1 | claim-kit needs:8 `research/production` (677 files, 42 MB) | No A reader. Only `batch.py:161`, `completion.py:633`, `prior_research` (B). |
| U2 | claim-kit needs:6-7 `research/excavator` (11,577 files, 70 MB); :6 is inside :7 | A reads 6 population pins, 20 ledger files, 1 norton-pinned OCR text. inputs.txt:10-11,15-19 already name them. |
| U3 | claim-kit needs:3 `research/readiness` (645 files, 67 MB) | Unread: `rules/`, `type-rules/`, `method_reviews/`, `component_attestations/`, `EXHAUSTED.jsonl`, `FETCH_QUEUE.jsonl`, `SOURCE_AUDIT_HOLDS.jsonl`, `CLAIM_KIT_LOCK.json`, `README.md`. |
| U4 | claim-kit needs:1,2,4 | one file read from each (CENSUS 1/6, progress 1/154, stage19/code 1/5). |
| U5 | claim-kit inputs:6-7 blankets | ~35,000 of 85,247 files in the fingerprint are untouched by the trace plus norton pins (largest: case-bundles/output 6,813; early-orders-hunt/output 4,124). Deliberate for future producers (`inputs.txt:1-5`). |
| U6 | claim-kit after:3 `valla` | ordering only; only the generic SUMMARY.json glob touches valla output. |
| U7 | valla inputs:9 `jobs/claim-drafts/AGENT_GUIDE.md` | `AGENT_GUIDE` occurs in no .py of valla or claim-kit. `valla.py:16-18` lists the real protocol files. |
| U8 | valla needs:1,2,3,6,7,8; triggers:9 | reads: 3 readiness subdirs; 2 stage19 files; 1 LEGAL file; 2-3 research/valla files; 3 file names per tracked package (91). |
| U9 | valla inputs:13 `jobs/fr-originals/data/**` | 5 files read (6,667 in scope). |

Also: `working_text.RULING` and `evidence_preflight owner_rule` name owner_rulings files as strings only (`working_text.py:12`, `evidence_preflight.py:156`); they are never opened.

## Categories: claim-kit, context A (runner)
- **Code fingerprint.** `jobs/claim-kit/**` (needed, includes tests); `jobs/clause-drafts/segment.py` (needs:9; `excavate.py:121-134`, `inputs.py:25-27`); `research/stage19/code/claim_gate.py` (`assemble.py:139-144`); R1-R3.
- **Canonical records.** Census CSV and `DECIDED_CASE_COMPLETENESS_RECONCILED.csv` (one file each); seven pinned population files named in `population_contract.json` (inputs:14-20); `act_overrides/*.jsonl`; reviewer ledgers `research/**/REVIEW.jsonl` + `UPHELD_ACT_RECORDS.jsonl` named by each record's `review.source_file` (dynamic, `act_overrides.py:103-129`); `readiness/decisions/*/*.json` (absent today); `readiness/factual/*/{questions,answers,applications,evidence,reviews}.jsonl`.
- **Provider records (dynamic globs).** `jobs/*/output/FRAGMENTS*.jsonl`, `jobs/*/data/**/FRAGMENTS*.jsonl` (22 jobs), `jobs/*/{output,data}/SOURCES.jsonl` (20 jobs), `jobs/*/data/PROVENANCE.json` (9 jobs) plus pointer files under `fragments_path`-style keys (`inputs.py:445-522`).
- **Referenced texts (dynamic from records).** 142,532 `text_path` declarations, all under `jobs/*/{output,data}/**` today (`inputs.py:199-248`, `build.py:159-163`). Also norton `INPUTS.json` pins: 20,399 paths including `research/readiness/{reviews 79, claims 64, factual 15}` (`inputs.py:373-390`).
- **Other jobs' outputs.** claim-drafts (`DRAFT_CLAIMS*.jsonl`, SUMMARY, `inputs.py:533-586`, `population.py:125-148`); later-events/namier/shepard-citations/app-footnote-leads (`EDGES.csv`, `CATALOG_INDEX.csv`); status-history (FRAGMENTS, STATUS, 7,650 `histories/EO_*.json`); norton (FRAGMENTS, STATUS, INPUTS); current-law `SOURCES.jsonl` and its text/cache files; generic `SUMMARY.json` (45 files).
- **Compiled prior output of this job.** None read in A (the runner empties `output/` first, `run_jobs.py:282-285`).
- **Prior research (`research/**`).** Not read in A except the ledgers above.
- **Environment.** `.job-cache/claim-kit` segmentation cache (performance only, `build.py:308-347`); R4; `~/.cache/eo-claim-kit` touched only by unit tests.
- **Failure behaviour worth knowing.** A missing norton-pinned file is swallowed as a warning (`inputs.py:398`). In this checkout 8 pins differ (norton ran against older SOURCES/STATUS files of astra-source-retention, clark-discovery, cotton-capture-custody), so factual obligations are rejected here.

## Categories: claim-kit, context B (agent CLI)
All entries are **needed only for the listed subcommand**.
- **prepare:** `jobs/claim-kit/output/{INDEX.json,dossiers/*}` (`batch.py:423,451`); `readiness/claims/*.jsonl` (`:155`); `research/production/claim-kit-pilot-2026-10-18/FREEZE_MANIFEST.json` (`:161`); `CLAIM_KIT_LOCK.json` (`:421`); held texts (`:76`, `evidence_preflight.py:52-58`); Valla context; prior-research scan of all `research/`; for undecided ids also the compiled shards, both authority CSVs, `jobs/status-history/history.py` and `output/**`, and its OFR sources (`status_overlay.py:66-175, 417-505`).
- **view / apply / batch-check / complete:** `load_packet` repeats Valla context, prior-research scan, held-text pins, undecided-evidence validation (`batch.py:247-280`). apply/batch-check add code pins, the full `FRAGMENTS*` provider inventory (~230 MB hashed per call, `fragment_cache.py:45-86`) and `~/.cache/eo-claim-kit`, claim gate, factual registry and custody paths.
- **batch-check / complete:** subprocess `jobs/claim-checker/checker.py` (`batch.py:613-624`, `completion.py:393-405`). **complete:** also SOURCE_AUDIT_HOLDS and cited review files, manifest-cited receipts, `pin_checker_inputs` globs, tracker module, and `git rev-parse --git-common-dir` for the lock (`completion.py:509-519`).
- **source_supplement prepare/verify:** declarations file, each `local_path`+`text_path`, parent packet, FRAGMENTS inventory (`source_supplement.py:23-165`).

**Reached through claim-checker** (constants only): census, decided CSV, `stage21/sources_index/OFFICIAL_SOURCE_CASE_CROSSWALK.csv`, `stage14/QUEUES/OFFICIAL_DIRECT_DOCUMENT_FETCH_MANIFEST.csv`, `stage21/original_sources/{CASE_ORIGINAL_SOURCE_CUSTODY.csv,ACQUISITION_LOG.jsonl}`, `stage20/output/{STATUTE_FETCH_INDEX,OPUS_ORIGINAL_MEDIA_MEMBER_MAP}.csv`, `stage18/SOURCE_MANIFEST.json`, `jobs/*/output/*.csv`, `jobs/*/output/SOURCES.jsonl`, `jobs/*/data/PROVENANCE.json`, `releases/source_books`, `releases/opus_stage11_complete`, `jobs/official-fixity/output/MATCHED_BY_SHA256.json`, `jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl`, `jobs/claim-checker/data/*`. **Through readiness-tracker** (`complete` only): `P`/`J` in `tracker.py:58-110` (stage19/output, stage20/output, stage21 CSVs, EXHAUSTED, SOURCE_AUDIT_HOLDS, 20+ job outputs).

## valla
- **A (runner).** Needed: code `jobs/valla/{valla.py,premises.json}`; `readiness/claims/*.jsonl` (`valla.py:98`); `method_reviews/*.jsonl` (`:419`); `component_attestations/*.jsonl` (`:475`); five protocol pins (`:16-18`, absent file pins as null, silently); dependency/review targets named by records (today 5 FR texts, BATCH.md, METHOD.md, two research/valla JSONL files); `git ls-files` for tracked RATIONALES (`:184`); `RATIONALES.json`, `decisions.csv`, `clauses.csv` of each of 91 tracked packages (`:237-280`). No tests run. A tracked-but-unmaterialized package is only listed in `package_scan.unmaterialized_packages` (`:203-205`), so too narrow a checkout changes `INDEX.json` without failing.
- **B (`attach`, via batch).** Same code with `ids`: claims lines prefiltered by id; every tracked package's `decisions.csv`/`clauses.csv` scanned for the ids (bound 256 MB, `:210-234`); own and parent packet folders excluded. `pilot.py`/`correction` also read `research/valla/pilot-2026-10-20/SAMPLE.json`, SOURCE_AUDIT_HOLDS and a git object (`91116f87:jobs/claim-kit/batch.py`).

## Not verified
Ingest reads (REVIEW/UPHELD files) are static. Per-file reads of the 20,399 norton pins are taken from `INPUTS.json`. Checker and tracker internals beyond path constants. kit.py subcommands outside your list. Pointers in future records.
