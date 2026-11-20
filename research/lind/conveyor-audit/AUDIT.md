# Conveyor result audit: boundaries, usage fields, 30-order replay (2026-11-13, dispatch EO-SUP-01)

No model workers were used. Everything below is recomputed by `usage_audit.py` from this session's transcript, from
the call labels in `lind_boundary_labels.csv` (my own labels: a judgment call), and from the replay receipts
`r30_LEDGER.jsonl` and `r30_MEASURES.json`. Dollars are API list price; actual cash per token is $0.

## 1. Correction: what the $6.59 / 51 calls covered

- **What it was:** clerical ($4.73, 36 calls) plus debugging or repair ($1.86, 15 calls), out of the whole Lind window
  (20:41–22:40 UTC, 93 requests, $11.75).
- **That window covers the full 30-order batch:**
  - PR merges and recording the approval;
  - setup through status review and overlay proposals;
  - reconfirmation, blind review and completion;
  - then diagnosis, the report, receipt compression and publication.
- **The error:** RESULT.md compared it with a 5-order replay that stops at overlay proposal, and called it "the
  manual route for the same stages". **That overstated the comparison** on two counts: order count and stages.

**The same window split at the replay's boundary** (Augur through overlay proposals; manual run on 30 orders):

| Segment | Requests | List $ |
|---|---:|---:|
| Before the boundary (merges, approval) | 6 | 0.68 |
| **Aligned boundary: Augur → overlay proposals** | **48** | **5.78** |
| After: reconfirmation, blind review, completion (the replay did not run these stages) | 23 | 3.01 |
| After: diagnosis, report, publication | 16 | 2.27 |

**The 48 calls inside the boundary, by label:**

| Label | Calls | $ | Conveyor removes it? |
|---|---:|---:|---|
| Stage operations | 13 | 1.64 | yes |
| Orientation (reading tools and prompts) | 11 | 1.29 | yes |
| Repair (prompt re-render, branch tracking) | 5 | 0.60 | yes |
| Git | 4 | 0.50 | mostly; someone still commits the result |
| Replies while workers ran | 6 | 0.69 | partly |
| Environment (disk cleanup) | 6 | 0.69 | no |
| Outside the conveyor (draw, freshness check) | 2 | 0.26 | no |
| Decision | 1 | 0.12 | no |

**What the conveyor can remove at this boundary:** at most 33 requests, $4.03, for a 30-order batch. That comes to
$0.13 per attempt with a coordinator re-reading about 490k tokens each time. It replaces the $6.59 figure.

## 2. The usage fields

The CLI writes one assistant record per content block. Records sharing a message id carry identical usage: 770 of
1,048 ids repeat, and none of them differ. So each request is counted once.

**Lind window, 93 requests:**

| Field | Summed tokens | List $ |
|---|---:|---:|
| Uncached input | 202 (about 2 per request) | 0.00 |
| Cache read | 48,147,999 | 9.63 |
| Cache creation (all 1-hour) | 116,182 | 0.93 |
| Output (thinking included) | 59,452 | 1.19 |

**What "518k" means:** the prompt size of one request (uncached + cache read + cache creation). It is not a sum and
not an artifact.
- Per request: mean 519k, median 517k, range 460k–576k; it grows steadily as the session lengthens.
- Other windows: post-pilot mean 610k; board work 771k.
- **Shares of the 48,264,383 prompt tokens** (cache read + cache creation + uncached input; corrected by EO-SUP-03):
  - cache read: 48,147,999, which is 99.759%, billed at $0.20 per million tokens on Opus 5.5;
  - cache creation: 116,182, which is 0.241%;
  - uncached input: 202, which is 0.0004%.
- The earlier "99.9996%" is the cache-read plus cache-creation share, that is 1 minus the uncached share. It is not
  the cache-read share.
- **Correction:** RESULT.md's "518k–769k per call" mixes per-request means from different windows. The board window
  mean is 771k (its median is 769k).

**Cash and list price:**
- `service_tier` is "standard" on every request, and there is no fallback credit.
- The session runs under a subscription, so tokens consume the weekly allowance (94% used, per the supervisor). Nothing
  is billed per token.
- **List-price cross-check:** the CLI's own `cost-state` record prices the session at $192.78 by 01:33 UTC:

  | Model | $ |
  |---|---:|
  | Opus | 185.04 |
  | Sonnet | 5.79 |
  | Fable | 1.56 |
  | Haiku | 0.39 |

  - Pricing the same Opus token counts with `jobs/necker-costs/PRICES.json` reproduces $185.0.
  - This transcript's main thread comes to $160.90 by that time.
  - The $24.1 gap is **inferred** to be Opus subagent requests (analysts and reviewers), which the CLI's total
    includes but this main-thread transcript does not. No separate subagent usage records were checked to establish
    it.
  - Sonnet's $5.79 equals the Lind producers' measured cost.

## 3. The smallest no-paid-call comparison on equivalent inputs: all 30 Lind orders

**Setup:**
- The same 30 order ids as the pilot, the same route and wave plan, the real claim kit.
- The replay worker answers each worker session with the pilot's saved outputs.
- `--defer-adjudication` was set. The batch cap of $75 is the conveyor's minimum and was not spent.
- The run folder was deleted afterwards so it cannot enter a later prior-research scan. The reservation lock was
  restored.

**A replay-worker defect was found and fixed in the first run:**
- It kept the template's blank whole-order clause row, which Lind's producer had replaced with 5 slices.
- On EO 9447 this made kit apply fail, and the order was demoted after one repair round.
- The worker now copies Lind's clause rows exactly (`research/lind/conveyor-replay/replay_worker.py`).
- The fault was in the replay, not in the conveyor or the kit.

**Second run, 02:57:15–02:58:25 UTC:**
- **Wall-clock:** 70 s (prepare 50 s, dispatch 10 s). The first run's prepare took 166 s of 192 s total, so allow
  1–3 minutes.
- **Coordinator model calls:** 0.

| Stage | Conveyor replay (30) | Manual pilot (30) |
|---|---|---|
| Dispatch | 23 dispatchable, 7 blocked for sources | the pilot's dispatch tally |
| Status decisions filed | 8 installed (22 blank or not written by the producers) | 8 |
| Kit apply | no failures | applied |
| Status gate sent to status review | 7; EO 9739 held back (lifecycle blocked) | 8: EO 9739 was reviewed, accepted, then produced no claim (FAILURES.md) |
| Overlay proposals | 7: EO 9447, 11294, 11943, 12437, 12701, 12753, 13476 | 8, of which the same 7 became claims and went to blind review |
| Next step | **stop at producer reconfirmation** for all 7 (D-20261110-no-mechanical-reconfirmation-for-models) | reconfirmed by script, against that decision |

**Fidelity**, comparing each replay proposal bundle with the pilot's, field by field:
- **Identical in all 7:** `EVIDENCE.json`, `STATUS_DECISION.json`, `LIFECYCLE_SOURCE_DECISION.json` and the dossier's
  `status_history.fingerprint`.
- **Differences, all bindings:**
  - proposal ids;
  - reviewer names and hashes;
  - `dossier_sha256` and the working-sheet hashes;
  - `approved` (false, correctly);
  - the dossier's and proposal's top-level `fingerprint`, which are hashes of the whole bound document.
- **Correction:** RESULT.md's "evidence fingerprints identical" holds for the evidence and status-history
  fingerprints, not for the top-level dossier fingerprint.

## 4. What this establishes, and its limits

- **Established:**
  - For the same 30 orders and saved outputs, the stages Augur → overlay proposal run in 1–3 minutes, with 0
    coordinator model calls and the same evidence and status decisions.
  - The conveyor's status gate saved one status review (EO 9739) that the manual run spent.
  - It stops where the owner rule requires.
- **The manual equivalent:** 48 requests and $5.78, of which at most 33 requests and $4.03 are what the conveyor
  removes.
- **Not established:**
  - Later stages: reconfirmation, assembly, plant, blind review, completion. These are $3.01 manual, untested here;
    covered only by the conveyor's own tests.
  - Worker cost. The conveyor runs one producer session per order, where Lind ran two 15-order sessions, so worker
    tokens may differ either way. A replay cannot measure that.
  - Research quality.
  - The coordinator calls a real conveyor run still needs (launch, read results, commit; about 2–4).
  - Anything about leaner, scripted coordinators such as Papinian's.
- **Corrected break-even:**
  - Development cost: about $7.5, plus this audit.
  - Saving: at most about $3.5–4.0 per Lind-like 30-order batch at this boundary.
  - So about 2–3 such batches, not 1–2.
  - For a lean scripted coordinator, the saving and the break-even are unmeasured.

## 5. Compatibility with the recovered Sol engineering (EO-SUP-02; judged from the supervisor's description)

- **Not checked:** I did not inspect the exact bytes. Recovery commit `e3a22977b5f3` is not fetchable here ("not our
  ref"); only its base `0c3b3d24b5b9` is. The supervisor runs the combined exact-tree checks.
- **Root's exact-tree test** (reported by the supervisor in EO-SUP-03, not rerun by me): on current main `5ace518`,
  the acting-text, custody and build tests pass; the conveyor is 75/78, with the same 3 platform failures reproduced
  on unchanged main. Root's receipt carries the compatibility limits. No further replay was run.
- **No textual overlap:**
  - Since the merge base `dd448487b`, this branch changes code only in `jobs/maudslay-conveyor/conveyor.py` (the blank
    STATUS_DECISION copy path) and its test.
  - The recovery changes `jobs/claim-checker/{references.txt, sources.py}`, `jobs/claim-kit/build.py` (`_LIST_END`)
    and their tests.
  - From the merge base to the recovery's base, only claim-checker output files changed.
- **Repository-file custody** (`jobs/*/data/**/SOURCES.jsonl`, `custody == 'repo_file'`, paths confined to their
  pack): no interaction.
  - The blank copy goes under `--scratch-root`, which `conveyor.py` (around line 864) refuses if it is inside the
    repository.
  - So the copy can land neither in a data pack nor in `research/`.
  - The kit's prior-research scan reads `research/` only; data packs under `jobs/` are not STATUS_DECISION sources.
- **Explicit EO-list matcher:** an indirect interaction. `build.py` decides which listed EO numbers a held document is
  read as citing, so `kit prepare` can produce different dossiers and fingerprints for orders whose sources have such
  lists. One of Lind's 30, EO 9481, is in the regression's EO 9474–9483 family.
  - The conveyor does not pin `build.py`, and my fix is independent of it.
  - But this replay's identical-output result is for the pre-recovery tree. On the combined tree, rerun the 30-order
    replay; it takes minutes and no model calls.
  - Differences are expected only where the new matcher changes a dossier. EO 9481's producer left its status
    decision blank, so it is not among the 7 proposals.
- **Conveyor check on this branch:** `python3 -I jobs/maudslay-conveyor/test_conveyor.py` ran 78 tests. 75 pass; the 3
  failures are the known Windows-specific ones:
  - two Codex-executable tests;
  - `IsolationTests` given a `C:/` path.

## 6. Pinned accounting result

| Measure | Requests | List $ | Mean prompt per request | Source |
|---|---:|---:|---:|---|
| Lind window, whole batch (20:41–22:40 UTC 2026-11-12) | 93 | 11.75 | 519k | `usage_audit.py` |
| — aligned boundary, Augur → overlay proposals | 48 | 5.78 | about 490k | `lind_boundary_labels.csv` |
| — of which conveyor-removable | ≤33 | ≤4.03 | | the same labels |
| Conveyor replay, 30 orders, same boundary | 0 | 0 | — | `r30_LEDGER.jsonl`, `r30_MEASURES.json` |
| Efficiency assignment before this audit (5-order replay and fix) | 36 | about 7.5 | about 870k | the earlier transcript measure |
| This audit (EO-SUP-01 and -02), from 02:49 UTC 2026-11-13, measured at writing | 37 | 3.10 | 160k | `usage_audit.py` |

**Notes on the table:**
- **Cash:** $0 per token; usage counts against the subscription allowance.
- **Cost-state reconciliation:** the CLI's cost-state reproduces with `jobs/necker-costs/PRICES.json`.
- **This audit's figure** grows by about $0.1 per further request. Recompute it with:
  `python3 -I research/lind/conveyor-audit/usage_audit.py TRANSCRIPT 2026-11-13T02:49 2026-11-14T00:00`.
- **Its low prompt size** comes from a condensed context, not a different method. Per request it cost $0.08, against
  $0.12 in the Lind window, which is consistent with the fresh-context projection. This is one sample only.

**Checks:**
- `python3 -I jobs/maudslay-conveyor/test_conveyor.py`: 75 of 78 pass; the 3 known Windows failures.
- `python3 -I jobs/kean/kean.py check --strict`: 0 errors, 0 warnings.
- `py_compile` of `usage_audit.py` and `replay_worker.py`.
