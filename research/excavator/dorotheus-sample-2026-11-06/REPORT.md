# Dorotheus wave, 2026-11-06: whole-lifecycle claims for the Stage 15 population sample and a YES probe

The wave researched, reviewed and filed whole-lifecycle claims for two sets of orders. The first is the 120 orders of the Stage 15 stratified population sample (`SAMPLE.csv`). The second is a 30-order random probe of provisional-YES Federal Register orders (`../dorotheus-yesprobe-2026-11-06/DRAW.json`, seed 20261106). Every order has one row in `DISPOSITION.csv`, with an outcome and, separately, the producer's best reading of operative force and formal validity on 2026-10-14. That reading is an assessment row for the parent's sensitivity analysis, never a claim.

Nothing here certifies anything. The human-certified count stays **0**. No status, ledger, census or codebook entry changed, and the claim-kit lock file is back to its starting bytes.

Named for Dorotheus of Berytus, the law professor who helped compile Justinian's Digest from the scattered writings of earlier jurists.

## Result

| Wave / group | Orders | Filed | Blocked | Nonresponse (dispatch / owner) | Ready, existing claim |
|---|---:|---:|---:|---:|---:|
| Sample, ready | 12 | – | – | – | 12 |
| Sample, decided not ready | 16 | 0 | 13 | 3 | – |
| Sample, undecided | 92 | 7 * | 50 | 35 | – |
| **Sample total** | **120** | **7** | **63** | **38** | **12** |
| YES probe | 30 | 7 | 18 | 4 | 1 |

No order was `rejected_review` as its final outcome, and none was `nonresponse_producer`. A claim that a reviewer rejected never became a final outcome on its own, because every reviewer rejection fell on a planted version.

\* **The 7 undecided claims are filed as isolated status-overlay proposals, not as canonical readiness claims.** The claim kit refuses canonical filing of a claim whose status the owner has not adopted. Completion requires `publication.mode = replacement_proposal` outside `research/readiness` for every status-overlay member (`completion.py` `working_overlay`). They are therefore in `overlay-proposals/dorotheus-2026-11-06-sample-undecided.jsonl`. Each carries the producer's own reviewed status (all seven are NO), with owner acceptance false. Because no decided-route sample order passed, `research/readiness/claims/dorotheus-2026-11-06-sample.jsonl` was **not created**. The parent may want to treat the seven proposals as filed for the estimate and route them to the owner for status adoption.

### Filed claims

YES probe, canonical, in `research/readiness/claims/dorotheus-2026-11-06-yesprobe.jsonl` (`kit.py complete --publish`, 0 exceptions):

| Order | Status | Claim sha256 (prefix) |
|---|---|---|
| EO 10057 | yes | 6dcc836a2ecb1014 |
| EO 10104 | yes | fb03ad49c7b8ab5d |
| EO 10153 | yes | 5ab37b8caae61285 |
| EO 11219 | yes | 9ac98f2a6a7cef28 |
| EO 11600 | yes | e470f9dfd22a9651 |
| EO 11961 | yes | a29927c91ac185e5 |
| EO 12046 | yes | e40e9bdcdf597c53 |

Sample undecided, isolated proposals. Each order's first end is a later presidential revocation or supersession whose text is held:

| Order | First end, as filed |
|---|---|
| EO 5700 | EO 11408, signed 1968-04-25 |
| EO 7628 | EO 7719, signed 1937-10-08 |
| EO 10901 | EO 11652, effective 1972-06-01 |
| EO 10994 | EO 11480, 1969-09-09 |
| EO 11218 | EO 11278, 1966-05-04 |
| EO 13348 | EO 13710, 2015-11-12 |
| EO 13362 | EO 13442, 2007-08-13 |

EO 13362 was filed in a corrected version. Its first version listed the bare heading "Sec. 2. Exceptions." as a clause, which the checker could not verify. Both arms re-reviewed the corrected version (sha 242bebb5…).

### Readings for the estimate (assessment rows, not claims)

Design-weighted by `SAMPLE.csv` `design_weight` (total 14,972):

| Group | No force | Unknown | Yes |
|---|---:|---:|---:|
| Ready | 2,124 | – | – |
| Decided not ready | 1,492 | 344 | – |
| Undecided | 4,770 | 5,882 | 361 |
| **All** | **8,385 (56.0%)** | **6,226 (41.6%)** | **361 (2.4%)** |

The undecided "yes" weight is a single assessed order. In the YES probe, 24 of 30 orders read as yes and 6 as unknown. These readings are producer judgments. Most of the undecided ones rest on a held transcription and one number search, not on a reviewed claim.

## Why orders blocked

Causes are grouped by fixed keyword rules in `tools/causes.py`. The full lists are in `CAUSES.json`, and the exact missing source per order is in `DISPOSITION.csv` `blocker`. The rules are coarse: first match wins.

**Sample (102 not filed and not ready):**

1. **Source held only as a custody record, or not held at all: 38.** These are almost all dispatch blocks: the original or the clause text is a hash with no bytes. The cases are Wikimedia Commons GPO bound-volume djvu files (EO 6071–6479), APP pages, govinfo FR PDFs for 1995–2025 orders, and three 1862–1936 orders with no attributed text. Retaining the hashed bytes would make them dispatchable.
2. **No acceptable original: 28.** This is the largest research block, and it is a tool rule, not an evidentiary finding. `status_overlay._decision_errors` requires `acceptable_as_original` for any status proposal. The 2026-10-21 transcription-as-text ruling is therefore not applied on the undecided route. Of the first 42 pre-1937 undecided members checked, only 4 had an acceptable original. Every other one holds only a Wikisource/APP transcription or a ProQuest replica scan, so no status proposal can be made, however clear the text. See tool defect 1.
3. **Ending statute or ending instrument text not held: 15.** Examples: the First War Powers Act Title I, S.J. Res. 113, Public Land Order 5658, refuge revocations and the Isthmian Canal Commission's ending statute.
4. **Performance or occurrence not shown: 11.** These are one-person waivers with no evidence the appointment was made (EO 309, 342, 719), report or termination dates (EO 9939, 12644), and completion of a task (EO 10534, 10438, 9762). Under the 2026-10-28 ruling these stay open, because known-within-an-interval differs from unknown-whether.
5. **Smaller groups.** Current-law source not held: 2. Later instrument held only as a mirror: 2. The checker's index has no signing date: 2 (EO 5857 and 5866, both upheld by both reviewers). Existing incomplete claim of another owner: 1 (EO 11299). Text defect: 1 (EO 12935, wrong pages). Other: 1 (EO 12496, the effective date of the EO 12578 supersession per pay system).

**YES probe (22 not filed and not ready):**

- **Later instrument held only as a mirror, or not registered: 7.** Examples: EO 13286, 13709 and 12692 are held only as APP or Common Crawl mirrors. The National Emergencies Act continuation notices (EO 12294, 13551) are held but not registered.
- **Custody record only: 5.**
- **One-time commands with no performance source: 4.**
- **Ending statute or public land order not held: 2.** EO 7993 needs PLO 2711; EO 12163 needs Pub. L. 105-277 §1422.
- **Singles:**
  - Current law: 1 (EO 10111).
  - Text defect: 1 (EO 12445).
  - Owner-routed: 1 (EO 13540).
  - Control missed: 1 (EO 14131). Every arm upheld it after reveal, but batch y05's control was missed by two of three arms, so the batch does not file.

## Review and planted controls

Every batch with a submission had two separate-context Sonnet blind reviewers (arms A and B) and two plants:

1. **A date-shift control on one of the batch's own claims.** It follows the ice core rule: every first-end and whole-order-end date moves back three years. If the claim had no end, every later-event date moved instead. If it had neither, every `signing_date` moved. Completion's kit controls use this plant.
2. **One Mountweazel plant**, from `mountweazel.py seed --track C --n 2 --share 0.5`, plus one real filed claim. The defect codes rotated through D3–D8. D1, D2 and D9 have no base in the pool (D1 0, D2 1, D9 0), so they were not used.

A batch with any missed plant went to a fresh third arm (C). A claim filed only if every arm that saw it upheld it, including the after-reveal review of genuine control versions.

Review batches:

- **YES-probe packets y01, y02, y03 and y05.** y04 had no submissions.
- **The 10 undecided claims, pooled into two batches (ux1, ux2) of five.** This replaced six one-claim reviews and is a deliberate deviation. Before their lifecycle review, the 10 undecided status decisions were checked by two separate Sonnet status reviewers (S1, S2). Both accepted all 10.

**Catch rate** (`PLANTS.csv`, 12 plants, 30 arm observations):

| Plant kind | Arm-level, lenient (rejected the planted hash) | Arm-level, strict | Plant-level, missed by no arm |
|---|---:|---:|---:|
| Date-shift | 13/15 | 13/15 | 5/6 |
| Mountweazel | 12/15 | 9/15 (Mountweazel's own scorer) | 4/6 |
| **All** | **25/30 (83%)** | **22/30 (73%)** | – |

Misses by arm: A 3, B 1, C 1.

- **Third arms** ran for y01 (A missed D3), y02 (A and B missed D6, a removed later event) and y05 (A missed the signing-date shift).
- **y05's control was missed by A and C**, caught only by B. The batch did not file, and the Bentham gate returns STOP for the action on that basis.
- **The signing-date plant is the weakest test.** Reviewers check quotes, ends and events, not the `signing_date` metadata, so 2 of 3 arms missed it. A YES claim with no ends and no later events needs a better plant type.

Every reviewer rejection of a claim this wave produced fell on a planted version. No genuine version was rejected. The six real filed claims that Mountweazel mixed in as items were each reviewed by two or three arms, and none was rejected, so there were 0 false alarms.

## Cost and context

Workers were 45 Sonnet sessions, including 2 killed: producers, assessment supplements, overlay reconfirmations, a correction, status reviewers, blind and after-reveal reviewers. They ran at most 8 at a time (`tools/scheduler.py`).

| Measure | Value |
|---|---|
| CLI-reported API-equivalent cost of workers (`COORDINATOR_LOG.txt`) | $61.19, plus about $0.38 for two killed y05 reviewers |
| Transcript-priced, at Bentham list prices (`telemetry/SUMMARY.json`) | production $47.66, review $19.78; **$67.44 producers and reviewers** |
| Coordination (Opus, transcript-priced) | about $29 |
| Budget | $400; never approached |
| Cumulative context per attempted order (input, cache read and cache write over all turns; production and review; 95 orders a producer attempted) | **about 1.38M** (sample 0.90M, YES probe 2.74M; median 0.90M) |
| Production only | about 1.0M per attempted order |

**The 150,000-token target was not met.** The slim views kept each prompt small: about 107k context per producer call. The cumulative figure is driven by turn count, and a YES order with a long inventory needed 50–76 turns. Resuming a worker after its cache expired cost $1–2 even for 2–5 turns; the six overlay reconfirmations cost $8.5 in all.

Pre-1937 undecided packets cost $0.2–0.9 each and took 1–5 minutes, because they blocked mechanically. The ten supplements that deepened their assessment rows added about $5.

The `telemetry/` "unlabeled" phase holds three sessions outside this wave, including the parent session; they are excluded from every figure above.

Per-order `context_tokens` and `turns` in `DISPOSITION.csv` split each packet's worker totals equally over its members. Review-batch and status-review totals are split over that batch's orders.

## Tool defects and process notes

1. **The undecided route ignores the transcription ruling.** `status_overlay._decision_errors` requires `acceptable_as_original`. Under the 2026-10-21 ruling, a transcription is a usable working text for claims, but no transcription-only undecided order can get a status proposal. This blocked 28 sampled orders whose text was held. The rule needs an owner decision or a code change; nothing here changed it.
2. **Completion cannot file one manifest across several packets.** `complete` writes `CLAIMS.selected.jsonl` outside every packet but one. `prior_research` then sees new research about the other packets' orders and fails with "packet dependencies changed during completion". A dry-run completion left in `research/` also permanently changes those packets' context; I moved mine to scratch. The fix used here: a fresh **publication packet** (`../dorotheus-yesprobe-2026-11-06/publication/packet`) prepared for exactly the seven YES orders to file. Its dossiers are byte-identical to the producing packets' (checked), and completion runs inside it. Without this, the "one claim file per wave" requirement cannot be met.
3. **Mountweazel `seed --n 1` seeds the whole pool.** `n_real = 0` never stops the real-item loop, so one run produced 1,416 items. Use `--n 2`. Batch ids must match `MW-C\d+`.
4. **Claude CLI argument parsing.** `--add-dir` is variadic and swallows a trailing prompt argument, so the prompt must come on stdin (`tools/launch.sh`).
5. **The checker's signing-date index has no date for EO 5857 or 5866 (1932).** Both claims were upheld by both arms but end `pass_with_unverified: date_after_signing:no_signing_date_known`.
6. **The dispatch check covers only mandatory sources.** EO 10513's ending source (EO 13245, 66 FR 66268) is custody-only, and that surfaced only at completion. This repeats the ice core finding.
7. **Second attempts.** Only two orders had an effort block rather than a missing-source block: EO 12046 and 12163, where the inventory was "unverified". Attempt 2 filed EO 12046 and blocked EO 12163 on Pub. L. 105-277 §1422.
8. **Early undecided assessments were thin.** The first ten undecided producers (u001–u107) blocked transcription-only orders within about a minute, with view-only assessment rows. Each was resumed once to read the held text and run one number search per order before its rows were final.
9. **y05 reviewers relaunched.** The first two y05 reviewers launched seconds before their review set was rebuilt with a control (EO 14131 had no date to shift). They were killed, their cost logged, and the batch re-reviewed by fresh arms.

## Rules followed, and where I chose the conservative route

- Everything written stays in the allowed places: under `research/excavator/dorotheus-sample-2026-11-06/` and `research/excavator/dorotheus-yesprobe-2026-11-06/`, the one canonical claim file `research/readiness/claims/dorotheus-2026-11-06-yesprobe.jsonl`, and scratch under `/tmp/claude-0/dorotheus-wave/`.
- Reservations went through `kit.reservations`/`kit.py release`; the lock file is unchanged. Nothing under the ProQuest folders or `jobs/pinakes-proquest-ingest/` was modified; it was read only as working texts.
- **Bentham gate**, run after the wave on the YES batches (`../dorotheus-yesprobe-2026-11-06/BATCHES.json`): **STOP**, because "planted control missed in batch y05". The posterior yield is 0.244 (80% interval 0.149–0.348). This wave was a fixed, owner-directed measurement sample, so it was run to completion rather than gated per batch; no further dispatch was pending when the gate ran.
- **Kean and HANDOFF were not updated**, because they are outside this wave's write scope. Results the parent may want to record as Kean findings:
  - (a) tool defect 1, the largest lever for undecided orders;
  - (b) the publication-packet workaround in tool defect 2;
  - (c) the YES-probe yield of 7/30, against the ice core's 11/30;
  - (d) the weak signing-date plant.

## Files

- `DISPOSITION.csv` (150 rows), `PLANTS.csv`, `CAUSES.json` and `COORDINATOR_LOG.txt`: every worker with model, cost, turns, start and end, plus checkpoints.
- `telemetry/`: `AGENT_USAGE.csv` and `SUMMARY.json` from `jobs/bentham/sessions.py`.
- `overlay-proposals/dorotheus-2026-11-06-sample-undecided.jsonl`: the 7 isolated undecided proposals.
- `completion-undecided/`: the overlay completion manifest. `complete-v3` published; `v1`/`v2` are dry runs.
- `<packet>/packet/` for `d01`–`d03` and `u001`–`u402`: frozen packet, views, decisions, `ASSESSMENT.jsonl`, `PRODUCER_REPORT.md`, `applied-v*`, and `undecided/EO_N/` with the status decision and review. `overlay/EO_N/proposal-v1/` holds the bundle and working claim.
- `ux1/` and `ux2/`: pooled undecided review sets, reviews and completion receipts.
- `tools/`: `plan.py`, `prepare.sh`, `render_producer.py`, `launch.sh`, `resume.sh`, `scheduler.py`, `enqueue.sh`, `review_prep.py`, `arm_c.py`, `reveal_msg.sh`, `complete_wave.py`, `finish.py` (per-packet variant, superseded by `complete_wave.py`), `disposition.py`, `causes.py`, `batches.json` and `prompts/`.
- The private control keys, review sets, Mountweazel keys and scores stay in `/tmp/claude-0/dorotheus-wave/` and were never written into the repository.

**Commit guidance for the parent.** The two wave folders hold 827 MB, mostly bulk the evidence does not need:

- Each `complete-v*/TRACKER_CLAIMS.jsonl` (about 95 MB) is a union copy of all canonical claims; `prior_research` ignores it by design.
- Each packet's `LOOKUPS.details.json` is about 8 MB, 183 MB in all.
- `complete-v*/tracker-*` and `checker/` add 44 MB.

Leaving these out keeps every pinned input of the published claims. That covers `PACKET.json`, the decisions, the reviews, the completion manifests and the overlay bundles. The publication packet `../dorotheus-yesprobe-2026-11-06/publication/packet/PACKET.json` is pinned by the filed YES claims' completion manifest, so keep it.

