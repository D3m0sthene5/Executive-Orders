# Coordination cost: measured baseline, a real fix, and a zero-cost replay on the real claim kit (2026-11-13)

**Corrected by `research/lind/conveyor-audit/AUDIT.md` (dispatch EO-SUP-01).** The $6.59 / 51-call comparison covered the whole 30-order Lind window, not the replay's stages. At the aligned boundary, the manual run used 48 requests ($5.78), of which the conveyor removes at most 33 ($4.03). A 30-order replay on the same saved inputs replaces the 5-order one.

**Labels:** [obs] observed in a named artifact or transcript; [proj] projection; [unk] unknown. List-price API dollars
are allowance; cash spent is $0.

## 1. Baseline: where the work goes

| Wave and output | Discovery and acquisition | Producers | Substantive review | Coordination | Output |
|---|---|---|---|---|---|
| Papinian undecided, 90 attempts (`research/excavator/claude-papinian-2026-11-10/telemetry/AGENT_USAGE.csv`) | [unk] runner jobs, unpriced | $18.08 [obs] | $28.16 [obs]: 2 review sets of 6 and 10 items | $9.59 allocated from a $51.02 wave session; scripts did the clerical steps | 6 adopted, ready claims |
| Lind stage 0, 30 attempts (`research/excavator/claude-lind-2026-11-12/telemetry/`) | [unk] | $5.79 [obs] | $7.12 [obs] | **$10.16 [obs], 44% of the wave** | 0 ready; 7 claims reviewed |
| Haloander probe, 30 attempts | [unk] | $12.12 for workers, with no role split [obs] | (in workers) | $43.75 allocated, including a one-time claim-kit repair | 3 ready |
| Codex overnight wave (`jobs/maudslay-conveyor/README.md`) | — | 21% | 25% (auto-review) | **54% clerical work by coordinators [obs]** | 12 claims |

- **Output classes are kept apart:** a ready claim, a reviewed claim, a corrected ending (the board cohort) and a full
  life history are not interchangeable.
- **Human effort:** owner approvals and merges, unmeasured.
- **Elapsed time:** the Lind pilot took about 35 minutes of production and review wall-clock (20:57 to 21:31 UTC).

**What the coordination was, measured from this session's transcript,** classifying every coordinator call by what it
did [obs]:

| Window | Calls | Cost | Mean prompt size per request (not a sum) | Share of cost that was re-reading context | Calls by purpose |
|---|---:|---:|---:|---:|---|
| Lind pilot (setup, routine, publication) | 93 | $11.75 | 518k tokens | 82% | clerical 40%, debugging or repair 16%, decision 9%, other 35% |
| Post-pilot diagnosis | 55 | $12.35 | 599k | 53% | decision 40% of dollars |
| Board work | 59 | $11.85 | 771k | 77% | clerical 35%, decision 22% |

**The largest demonstrated repeated work is a long-context coordinator re-reading its whole context to do clerical
steps.** Real decisions were 9-22% of calls.

Per-call cost differs sharply by context length:
- fresh worker contexts: the Lind status reviewer at $0.056 per call (31 calls, $1.74); the analysts at about $0.07;
- this long session: $0.13-0.21 per call.

## 2. The improvement, using existing machinery

`jobs/maudslay-conveyor/conveyor.py` already exists to do every clerical step as a resumable state machine:
- Augur and Bentham checks;
- reservation, prepare, lookups and views;
- prompt rendering and worker launch;
- apply, check and dispatch;
- the status-overlay stage, plant, review sets, completion and costs.

With it, the coordinator model only adjudicates. It was built from Papinian's scripts (17% coordinator share). It had
never been used for the undecided route on the real kit.

**A real defect blocked that use; it is now fixed.**
- **Cause:** the conveyor kept its blank STATUS_DECISION copies under the batch folder in `research/`. The kit's
  prior-research scan (`jobs/claim-kit/prior_research.py`, `collect`) reads every STATUS_DECISION under `research/`
  except the packet.
- **Effect:** `kit apply` refused with "changed prior research".
- **Proof:** recomputing the inventory with the batch folder excluded reproduces the frozen one exactly.
- **Fix:** keep the copy under `SCRATCH/prepared/BATCH/undecided/`, outside the repository by the conveyor's own design.
  The conveyor test was updated.
- **Tests:** 75 of 78 conveyor tests pass. The 3 failures are pre-existing and Windows-specific: Codex executable
  resolution, and a blinding scan given a `C:/` path.

**The replay worker** (`research/lind/conveyor-replay/replay_worker.py`) answers each worker session with the Lind
pilot's saved real outputs: producer sheets and status decisions, status reviews, and blind-review verdicts. The
conveyor can then run on the real kit at zero model cost.

## 3. Comparative measurement at the same boundary, with the same evidence

**The replay** (receipts `r5_LEDGER.jsonl` and `r5_MEASURES.json`) ran 5 Lind orders through the conveyor on the real
kit: EO 12753, 9739, 4475, 12437 and 11294.
- **Wall-clock:** 37 seconds, from 01:23:30 to 01:24:07 UTC.
- **Coordinator model calls:** 0.
- **What it did:**
  - passed Augur;
  - reserved, prepared and built lookups and views;
  - rendered 4 prompts;
  - its dispatch check blocked EO 4475, as in the pilot;
  - installed 4 status decisions and applied the packet;
  - its status gate left out EO 9739 (lifecycle blocked), as in the pilot;
  - the status review accepted 3;
  - it took the reviews and built 3 overlay proposals;
  - it **stopped at producer reconfirmation**, as owner decision D-20261110-no-mechanical-reconfirmation-for-models
    requires;
  - it ran Bentham's gate.
- **Fidelity:**
  - the evidence, status decisions and status-history fingerprints are identical to the manual pilot's for all 3 orders
    (the top-level dossier fingerprint hashes the bindings and differs);
  - the lifecycle sheets differ only in `approved` (left false, correctly) and `dossier_sha256` (the working dossier
    binds to the review sheet).
- **The manual route for the same stages** (corrected; AUDIT.md section 1): Augur → overlay proposals for 30 orders took
  48 requests ($5.78), of which at most 33 ($4.03) are conveyor-removable. The earlier 51 calls ($6.59) spanned the whole
  batch, including later stages and publication.
- **Not measured here:** the later stages (reconfirmation, assembly, plant, blind review, completion). They are covered by
  the conveyor's own tests on a fake kit and a real-kit fixture, not by this replay.

**A finding about my own pilot.** The manual Lind coordination reconfirmed the model producers' lifecycle approvals by
script. Owner decision D-20261110-no-mechanical-reconfirmation-for-models declines exactly that. EO 12753's claim, now
"eligible", was assembled after such a reconfirmation. It needs a producer reconfirmation, or an owner decision, before
adoption. The conveyor caught this by design; manual coordination did not.

## 4. What this establishes, and what it does not

- **Establishes:**
  - the clerical stages of an undecided batch, through overlay proposal, run on the real kit with real saved outputs in
    seconds, with no coordinator model calls;
  - the conveyor enforces owner rules that manual coordination broke;
  - the defect that prevented its use on this route is fixed.
- **Does not establish:**
  - a measured end-to-end saving in a paid batch;
  - unchanged research quality (the replay reuses the pilot's content);
  - the cost of the producer-reconfirmation session the rule requires, or of the remaining stages;
  - causality: the comparison is retrospective.
- **Smaller input is not lower end-to-end cost by itself.** Workers still pay for their own context. The expected saving
  is the coordinator's removable calls at the replay's boundary, at most $4.03 of $5.78 [obs; AUDIT.md], plus running
  the remaining decisions in a fresh context. That second part is a projection: about $0.06 against $0.13-0.21 per call.
- **Evidence omitted from a compact packet:** the conveyor does not change what workers see. Packets, views and
  sources are the kit's.

## 5. Where it applies

- **The unit is a claim-kit batch, not an order.** It applies to every production or review batch on the decided and
  undecided routes. That is where coordination was 17-78% of wave cost [obs].
- **It does not apply to:**
  - discovery and acquisition (Sol's campaign; the runner jobs);
  - producer and reviewer reading, which is the substantive work;
  - human certification;
  - one-off research outside the kit.
- **Unresolved:** waves that need judgment mid-batch (adjudicating splits). The conveyor pauses or defers them, and a
  fresh coordinator decides.

**Break-even** [proj; assumptions stated]:
- **Development cost here:** about $7.5 of this session, plus the earlier analysis.
- **Saving per 30-order batch:**
  - if the conveyor removes the removable calls of a long-context coordinator (Lind-like), at most about $3.5-4.0 at
    the tested boundary, so break-even in about 2-3 batches (corrected from $5-7 and 1-2);
  - if the coordinator was already lean and scripted (Papinian-like, about $3 per 30 attempts), about $1-2, so about 4-8
    batches.
- **Not counted:** maintenance, conveyor changes, and the reconfirmation step.

## 6. The remaining production test that would establish a net saving

- **Batch:** one real paid batch run through the conveyor with the Papinian configuration and a fresh-context
  coordinator, on a random draw from the undecided pool.
- **Comparison:** against Lind's manual measurement: coordinator $0.34 per attempt and 44% share.
- **Prerequisites:**
  - the owner either decides on producer reconfirmation, or the conveyor gains a small producer-reconfirmation session
    (a fresh producer re-approves the working sheet, about $0.2-0.5 per order);
  - a signed Augur plan.
- **Budget:** cap $25.
- **Decision rule:**
  - adopt the conveyor as the default route if coordinator dollars are at most $0.12 per attempt (at most 15% of the
    batch) and controls and blinding pass;
  - if coordination exceeds $0.20 per attempt, diagnose before further use;
  - in between counts as inconclusive. Run one more batch only on a new approval.

## 7. Cost of this investigation

- **Coordinator, this assignment:** about $7.5 through the replay (36 calls at about 870k tokens of context each),
  measured from the transcript.
- **Script runs:** seconds to minutes; no model calls.
- **Production or review:** none.
