# Integration report: claude/integration-20261104

Branch `claude/integration-20261104` was pushed to GitHub and has not been merged. Its head is `a19982c23102aa01a5b945fcfe1963885f123f56`. The branch starts from origin/main `600ae3018f71025b3e53dc8538b8f92e6e159b76`, and main had not moved when I fetched it again just before the push. The build used only the clone at `/tmp/claude-0/integ/repo`. I did not touch `/home/claude/executive-orders` or main.

The push changed files under `jobs/`, so GitHub started the repository's "Run jobs" workflow on this branch (run 41822603367, https://github.com/D3m0sthene5/Executive-Orders/actions/runs/41822603367). That workflow runs the jobs whose folders changed and commits their regenerated `jobs/*/output` back to the same branch. At 12:22 UTC it was still on the "Run the jobs" step and had committed nothing, so the branch head was still a19982c2. When the run finishes, the branch head will move to a runner commit that adds regenerated outputs on top of a19982c2. Those outputs are the newer generation and should be kept. "Geddes advisory lint" also ran on a19982c2 and succeeded.

To save disk space for the live production run, I deleted the local clone after pushing, at the coordinator's request. Every commit is on GitHub, so nothing was lost. The resolution helper scripts and test logs remain under `/tmp/claude-0/integ/tools/` and `/tmp/claude-0/integ/logs/final/`.

This was engineering integration only. No research conclusion, status, owner ruling, claim, count or codebook entry changed. The only lines added to the Kean registers are lines the PRs already contained.

## PRs merged

I checked each head against `gh api .../pulls/N` before merging it. None had moved since the PR map was made.

| Order | PR | Branch | Head used | Merge commit on branch |
|---|---|---|---|---|
| 1 | 131 | codex/bacon-recovery-20261103 | 1d0f329718defcc6d2d1327a5b1a7092d86d3436 | 172a53e9a |
| 2 | 132 | codex/future-production-preflight | bd066444399ebd039443ddc7e47a9fe42110b00b | 12dac91b7 |
| 3 | 133 | codex/maitland-reviewed-histories | c733e69dbd0fa1e57a1f2614a33d77bdd600f122 | c2ca66f20 |
| 4 | 135 | codex/sol-evidence-economy-20261104 (stacked on 133) | 348f45e22232261dcec71c51ca005f264dd9703b | 81fbd167f |
| 5 | 136 | sol/production-observability-20261104 (contains 134) | 47666eca92f8d2635d9bba313b874a5e970d3ab7 | 596ec9abf |
| 6 | 137 | sol/offload-decision-20261104 (stacked on 136) | 1d322b60c141655a3dcd676af80443dcd09f41f9 | a19982c23 |

PR134's head, `54db2cf5948d7c0cdd91c8f66a96349224aee6a1`, is an ancestor of PR136, which I confirmed with `git merge-base --is-ancestor`. PR134's single commit therefore entered the branch through PR136. All seven PR heads are ancestors of the final head.

## Conflicts and how I resolved them

### jobs/claim-kit/kit.py, PR132 against PR133 (merge c2ca66f20)

Both PRs inserted an early-return command handler at the same point in `main()`. PR132 added the `dispatch-check` handler. PR133 added the `history-check` handler and the shared `history-at`/`history-impact` handler. The handlers are independent, so I kept both blocks in that order. Git had already merged the parser lines cleanly: PR133's `history-at`, `history-check` and `history-impact` parsers, plus PR132's `prepare --research-only`, `dispatch-check` parser and research-only exit logic in the prepare/apply/batch-check branch. I compared the result with PR135's `integration/PR132_CLI_RESOLUTION.patch` and `PR132_RUNTIME.patch` and used them as guides only. The resolution matches their shape, and I copied no file from them.

### jobs/claim-kit/kit.py, PR135 (merge 81fbd167f)

The `prepare` parser line conflicted. PR135 adds `--history-bundle`, and HEAD carried PR132's `--research-only`. I wrote a single `prepare` parser with every option: `--agent`, `--write`, `--replacement-proposal`, `--history-bundle` (append) and `--research-only`. I kept PR132's `dispatch-check` parser, which is the exact line in the guide patch. The rest of PR135's kit.py changes merged without conflict: the `blind-verify` subcommand, `factual-at`, `views` and passing `history_bundles=` to `batch.prepare`. Several things now hold together:

- `batch.prepare` collects history bundles (PR133/135) and then runs PR132's custody check. That check writes `DISPATCH_CHECK.json` and `metrics['dispatch_check']`.
- `batch.validate_runtime` (PR132) is still used by `apply`.
- `dispatch.py`, `test_dispatch.py` and `jobs/claim-checker/checker.py` are byte-identical to PR132. That keeps the `check_source(..., allow_download=)` keyword and the PR132 lines of the runtime patch.
- PR133's Valla refusal context in `batch.render` and `batch.view` merged cleanly.

### Kean append-only registers

The conflicts were in `findings.jsonl` (merges for 132, 133 and 136) and `asks.jsonl` (merge for 135). I resolved each with `/tmp/claude-0/integ/tools/union_jsonl.py`. The script keeps HEAD's lines in order, then appends the incoming side's new lines, byte for byte and without duplicates. It also asserts that no base line is lost and reports any repeated (id, rev) pair; there were none. Kean's `current()` keeps the highest `rev` and the order of first appearance, so appending is the order the tool expects. Git's auto-merge of `decisions.jsonl` and of the PR137 findings line also produced plain unions. After every merge I ran a line-by-line check that each side's register lines are present. `HANDOFF/KEAN.md` was regenerated with `python3 -I jobs/kean/kean.py brief` after each merge, and `kean.py check --strict` reported 0 errors and 0 warnings each time. The final registers hold 19 asks lines, 141 findings lines and 37 decisions lines. Each line is byte-identical to some PR or to main.

### HANDOFF/notes-codex.md (every merge after 131)

I resolved this with `/tmp/claude-0/integ/tools/union_notes.py`. The script takes the union of `## ` entries from the two sides of each conflict hunk, sorts them by date with the newest first (the order is stable within a date), and leaves the text outside the hunk unchanged. No entry was dropped. The final top of the file lists, in order, the PR132, PR135, PR133, PR137, PR136, PR136-recovery, PR134 and PR131 entries, then the older entries from main.

### AGENTS.md and research/progress/control-center/README.md

Git merged both without conflict. I confirmed that every line any PR adds is present in the final file, and no instruction from any side was dropped. The README contains PR133's MAITLAND paragraph together with PR134/136's hosted URL, Production-flow line, source and refresh text, and "Dated observability snapshots" section.

### Generated outputs

`jobs/kean/output/*` is PR131's 2026-11-03 run, the newest generation in any of the PRs. No other PR changed generated `jobs/*/output` files, so nothing was merged by hand.

### .github/workflows/geddes.yml

The only workflow change is PR135's one-line addition of `/research/stage19/code/claim_gate.py` to the sparse lint checkout, as its INTEGRATION.md says.

## Check for semantic duplicates

`/tmp/claude-0/integ/tools/dupcheck.py` uses Python's syntax-tree parser (`ast`) to search jobs/claim-kit, jobs/valla, jobs/geddes, jobs/norton and jobs/claim-checker. It found no duplicated top-level function or class, no duplicated method, no subparser registered twice, and no option repeated within one parser. The only command name compared twice is `prepare` in kit.py, and that is intended: one comparison chooses the call and the other attaches `research_only`. The combined `kit.py --help` lists 28 subcommands, each once. `prepare --help` shows `--history-bundle` and `--research-only` together.

## Tests on the final combined tree (a19982c2)

I ran the suites one after another with `CLAIM_CHECKER_VERIFY_DOWNLOADS=0`, the setting the workflows use. The machine has Python 3.13.18 and Node 22. Logs are in `/tmp/claude-0/integ/logs/final/`.

| Suite | Result |
|---|---|
| `kean.py check --strict` | 0 errors, 0 warnings |
| jobs/kean (unittest) | 13 run, OK |
| jobs/hamilton-token-audit | 26 run, OK |
| jobs/norton | 16 run, OK |
| jobs/geddes (`-I`) | 96 run, OK |
| jobs/geddes inside a reproduction of the workflow's sparse checkout (`git archive` of geddes.yml's paths only) | 96 run, OK |
| jobs/valla | 37 run, OK |
| jobs/claim-checker | 69 run, OK |
| jobs/claim-kit | 627 run, OK, 1 skipped |
| `node --test research/progress/control-center/observability-core.test.js` (PR136/137) | 10 of 10 pass |
| `python3 research/progress/control-center/verify-flow.py` (PR136) | exit 0 |
| `kit.py publication-audit --base origin/main` | ok, no problems |
| `kit.py publication-audit --merge-commit` on each of the 6 merge commits | all exit 0 |

The claim-kit suite already includes every test file the PRs added: test_act_overrides, test_blind_verify, test_dispatch, test_factual_events, test_history_context, test_provision_history, test_provision_history_cli and test_reinstatement_handoff. The other added files, test_geddes, test_profile and test_valla, ran in their own suites. Nothing failed, so I did not need the second worktree on main to sort failures into categories. The retained failures the PRs document were Windows CRLF and backslash-path failures (PR133) and a sparse-checkout lint failure (PR135, later repaired). Linux cannot reproduce the Windows failures. The sparse-checkout lint passes both in the local reproduction and in GitHub's "Geddes advisory lint" run on this branch, which succeeded.

I did not run the following locally:
- Valla pilot workflow steps beyond the unit suites: the mountweazel and junto tests, `valla/pilot.py`, and the lifecycle and custody replays. They need frozen historical commits fetched by the workflow.
- PR136's baseline and historical rebuilds and PR137's population, span and replay scripts. They need source caches that are not tracked in Git.
- PR135's native partial replay and real bounded history packet.
- Windows CI.

## Not merged

All six PRs requested are merged. Nothing from them was left out.

## Follow-ups

1. Close PR134 as covered: its only commit, 54db2cf5, is an ancestor of PR136 and of this branch.
2. Hosted CI needs a full rerun. PRs 134, 136 and 137 used `[skip actions]` and never ran repository workflows, and the combined tree has never had a pull-request CI run. The next step is to open a draft PR from `claude/integration-20261104` to main, or dispatch the workflows, so that kean, valla-pilot (bounded-offline-pilot), claim-publication-audit, geddes (lint and benchmark), road-tests and Windows tests run on the combined head. Watch Windows in particular for the retained CRLF and backslash cases from PR133.
3. Steps from PR135's INTEGRATION.md that still apply to this tree:
   - Rerun dispatch refusal checks, `native_partial_replay.py` and a real bounded history packet.
   - Check source freshness and fingerprints.
   - Prepare new packets. Never renew old packet hashes.
   - Re-establish any runner certificate that changed code affects. kit.py, batch.py, checker.py and the Hamilton files changed, so the code pins stored in packets prepared earlier will now refuse, by design.
4. PR136's Hamilton changes may affect `needs` and runner closure. Revalidate rather than copy earlier certificates.
5. Reconcile with the Tribonian branch (cacfb8f4) and the final production checker before landing. The PR map records that Tribonian also changes HANDOFF/KEAN.md and jobs/kean/output; regenerate the brief again after that merge.
6. The legal first-ending interval contract stays a separate, unadopted proposal: ask `A-20261104-1` is open, and the withdrawn duplicate ask is kept as its own revision. The integration adopted nothing.
7. Record a Kean finding for this integration and add a HANDOFF/notes-claude.md entry in the main session if wanted. I made neither, because this task was integration only and must not touch the production checkout.
