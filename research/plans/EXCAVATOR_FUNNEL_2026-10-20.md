# Next excavators: a gated funnel (2026-10-20)

Selection made before implementation, in the format of `research/stage19/FUNNEL.md`. It replaces the
ranking in `EXCAVATOR_SERIES_2026-10-19.md`, whose savings X1 measured at about 463 h against the
4,134 h assumed (`research/production/x1-2026-10-19/REPORT.md`).

## What X1 taught us, and the rule this funnel follows

My series plan was wrong mainly because it treated research steps as independent. An order cannot
reach a claim until it has:

- a provisional YES/NO;
- a held text;
- for the end, an instrument the dossier can cite.

X1's pilot found only 52 of 8,014 pre-1937 orders past those gates. My invented hit rates were also
far too high, and mass-ending events are rarely an order's first end.

**Rule for this funnel:** every idea below is sized only by orders that already pass, or that it makes
pass, its prerequisites. Counts are measured from main `f57cffe8`. Each idea gets a probe of a few
agent-hours before anything is built, and a stated test that the probe must pass.

## Where orders are stuck (measured, main f57cffe8)

| | 1937 and later | Before 1937 |
|---|---:|---:|
| Orders | 6,940 | 8,032 |
| No provisional YES/NO | **4,274** | 7,339 |
| ... of those, with a status-history observation or OFR catalog record | **4,273** | 367 |
| ... of those, with official text saved | **3,952** | 608 |
| ... of those, with only a transcription lead (APP, Richardson, CSC) | 313 | 2,012 |
| Provisional YES/NO, not yet ready | 2,536 | 688 |
| ... of those, with text saved | 2,150 | 27 |
| Ready for human review | 130 | 5 |

The pre-1937 orders without a status split by X1 class:

| Class | Orders |
|---|---:|
| Land | 2,959 |
| Spent | 1,911 |
| Standing | 1,747 |
| Swept | 484 |
| Unknown | 238 |

**Diagnosis:**

- **Cheapest pool:** the 4,274 modern orders with no status, which X1 and my earlier plan both skipped.
  They already hold the inputs a status needs: a Federal Register text and an editorial history. They
  are blocked only because Stage 11 reviewed 3,359 orders and stopped.
- **Second pool:** the 2,150 modern orders that have a status and a text. They wait on clause and end
  work, which the claim swarm has done at about 2-5 agent-minutes per accepted claim.
- **Old orders:** they need texts first. That depends on an access decision (ProQuest) and a codebook
  question (what counts as an acceptable copy), not on more excavation.

### Measured anchors

| Source | What was measured | Value |
|---|---|---|
| Claim swarm, 2026-10-18 (`EXCAVATOR_FUNNEL_2026-10-18.md`) | Accepted claims for decided-NO orders revoked by one named EO | 176 claims, about 360 agent-minutes in all, so about 2 min per accepted claim; 11% rejected |
| Codex batch pilot (`research/excavator/2026-10-18/batch-pilot/COST_COMPARISON.json`) | Hard modern dossiers | 2 upheld of 12 attempts, about 4.3 min per attempt |
| X1 pilot | Pre-1937 orders | 5.1 min per accepted claim, 0.49 min per order screened, about 10% eligible |
| Stage 11 | Accepted AI-reviewed statuses | About 24,900 tokens per accepted status, 73% accepted; no time recorded |

## C. Ten ways to turn the most orders ready per agent-hour

| # | Distinct concept | Lever | Orders it can reach (measured) | Principal limit | Probe before building |
|---:|---|---|---:|---|---|
| 1 | **Modern status sweep** | Proposes provisional YES/NO for modern orders from their own catalog disposition notes, status-history observations, later-events edges and current-law mentions, through claim-kit's existing reviewed `status_overlay` path. | 4,274 | A catalog note is an editorial lead; YES needs a current predicate through the cutoff. | 50 random no-status modern orders, producer plus independent review. Record minutes, tokens, agreement, and how many become claim-eligible. |
| 2 | **Batch adoption pull request** | Overlay proposals need the owner's adoption, and the authoritative file is `research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv`. A job turns each reviewed batch into one pull request that adds rows with provenance, so the owner merges once per batch. | every proposal | Changes a research ledger count, so it needs the owner's explicit OK for the mechanism. | Dry-run one batch of the probe's proposals as a draft pull request, without merging. |
| 3 | **Modern claim factory** | Runs claim-kit decision sheets and the assembler on modern orders with status and text, in context-lean batches by family. | 2,150 now, plus whatever 1 adds | Hard families block often (Codex: 5 of 6). | 50 random, not cherry-picked, modern status-plus-text orders. Measure accepted per attempt and minutes. |
| 4 | **Own-terms and provision unblockers** | Adds an own-terms end mechanism to claim-kit and locates the ending provision in dossiers. claim-kit's own-terms families hold 2,360 memberships (condition 919, report deadline 508, until-event 370, fixed term 352, sunset 146 and two smaller ones; they overlap). | up to 2,360 | Wording is a lead, not a fact, for example whether a report was ever filed. | Rerun X1's 8 blocked rows and 50 own-term family members. |
| 5 | **Old-order status from type rules** | Uses X1's 22 frozen rules and its types with held transcriptions to propose statuses for spent and swept old orders. | 2,395 (spent 1,911, swept 484) | Depends on whether a transcription can support a provisional status (codebook question). | Codebook reading first, then 50 spent orders. |
| 6 | **ProQuest access** | One owner email (`research/pre-1937-sources/ACCESS_REQUESTS.md`, drafted) asking NYU for permission to retrieve the scans in bulk. ProQuest holds 9,503 numbered pre-1937 orders, each with a scan. | 3,563 with no other text; better copies for more | NYU may refuse; the grade of the scans is a codebook question. | None; the owner decides whether to send it. |
| 7 | **Public Land Order ledger** (old X2) | Finds revocations of land orders in Public Land Orders since 1942. | 2,959 land orders without status | Pre-1942 or statutory ends are missed. | 30 land orders: what share does a PLO or later order reach? |
| 8 | **CSC appointment dating** | The `csc-annual-reports` job, already merged, cuts orders from Civil Service Commission reports; the appointment dates in them date the waivers. | 840 cite a CSC report | Report printings are leads, not originals. | Read the job's first run once `output/SUMMARY.json` exists. |
| 9 | **Gated frontier scheduler** | Ranks every order by how many prerequisites it lacks, so agents work the nearest-to-ready orders first. It also gates the effort model (X1 item 5). | all | A scheduler moves no order by itself. | None; a small offline job. |
| 10 | **Census gap admission line** | Builds admission packets for the 1,314 orders APP counts that the project lacks. | 1,314 | Admission is a human identity decision. | Defer. |

## Selected series

Build in this order. Each step starts only after its probe passes.

| Step | Combines | Why first | Passes if |
|---|---|---|---|
| Y1 Modern status sweep, with batch adoption | 1, 2, 9 | Largest pool whose inputs already exist; nothing else moves these 4,274 orders. | Reviewer disagreement ≤ 11% and median under 5 agent-minutes per accepted status. |
| Y2 Modern claim factory, with unblockers | 3, 4 | Turns Y1's statuses and the 2,150 waiting orders into ready claims with machinery that is already measured. | Accepted claims per attempt ≥ 50% on a random sample, and rejections ≤ 11%. |
| Y3 Old orders | 5, 8, then 7 | Only after the codebook answer on acceptable copies and the owner's ProQuest decision. | Set when those answers are in. |

**What this plan does not promise.** No hours-saved figure is given until the probes run. The probes
cost a few agent-hours each, and their measured yields replace every assumption here.

**Upper bound, for scale only.** If the modern pool converted at the claim swarm's rate, about 6,800
modern orders could become ready for roughly 500-1,000 agent-hours of attempts. If it converts like
Codex's hard pilot, a fraction of that. The Y1 and Y2 probes decide which.

## Owner decisions this plan needs

1. **Yes or no on the batch adoption mechanism (idea 2):** AI-reviewed statuses join the official list
   by a pull request the owner merges, one per batch.
2. **Whether to send the drafted NYU access request** for ProQuest (idea 6).
3. **The X1 session's follow-up items** still wait on the owner's yes in that session. Y1 supersedes
   its status-line item for modern orders.

## Guardrails (unchanged)

- Proposals are AI status hypotheses, never findings; the human-certified count stays 0.
- No codebook change.
- Risk-tiered review stays off unless the owner approves it.
- A WPA, APP, CSC or ProQuest copy is never `acceptable_as_original` without the codebook and a person
  deciding so.
