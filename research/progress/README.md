# Executive Orders — research progress dashboard

**[Open the current generated dashboard](../../jobs/daily-digest/output/DASHBOARD.md)** · [Exact data and input hashes](../../jobs/daily-digest/output/DASHBOARD.json) · [Per-order readiness](../../jobs/readiness-tracker/output/READINESS_BY_ORDER.csv) · [Daily changes](../../jobs/daily-digest/output/DIGEST.md)

Updated October 28, 2026 (America/New_York). Legal cutoff: **October 14, 2026**. The working bibliography contains **14,972 identities**; the historical census is still incomplete. The generated dashboard reads the current status and claim registers, retains each producer's published generation date, and checks exact claim versions against the mechanical checker.

## Current readout

The combined checker → tracker → dashboard refresh finished **October 28 at 11:09 p.m. EDT**. It reports **395 ready for human review**, including **298 original-supported** and **97 transcription-dependent** cases: a net increase of **85** from the previous 310-ready generation. All **510 current claim lines covering 509 distinct orders** now have exact matching checker receipts. Readiness comes from this combined run; the separate batch replays are not added together. [Validation run and generation receipt](../../jobs/readiness-tracker/output/STATUS.json).

| Measure | Verified checkpoint | Source and definition |
|---|---:|---|
| Working identities | **14,972** | [Identity register](../stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv); bibliographic coverage, with the historical universe still unknown |
| Provisional present-status decisions | **3,403 / 14,972 = 22.73%** | [Current status register](DECIDED_CASE_COMPLETENESS_RECONCILED.csv); adopted AI status hypotheses |
| Provisional YES / NO / without an adopted status | **405 / 2,998 / 11,569** | Absence of an adopted status does not mean absence of research |
| Ready for human review, last published generation | **395 / 14,972 = 2.64%** | [Tracker summary](../../jobs/readiness-tracker/output/SUMMARY.json) and [generation receipt](../../jobs/readiness-tracker/output/STATUS.json); all applicable machine steps passed or were documented exhausted |
| Ready by text-evidence tier | **298 original-supported / 97 transcription-dependent** | The transcription tier retains explicit source limitations |
| Filed claim lines / distinct orders | **510 / 509** | [Current claims](../readiness/claims/); includes partial claims and one replacement/repeated line |
| Current claim lines with exact matching checker receipts | **510 / 510** | All 509 effective order claims also match; a matching receipt can still record a failed or unverified check |
| Published human-certified whole histories | **0** | [Separate human-review register](../stage19/output/PROGRESS.json); no AI or mechanical pass confers certification |
| Original replacement / quotation recheck obligations | **103 / 103** | Published tracker obligations, overlapping with other work |

The historical Stage 19 progress file remains the published human-certification record. Its old structural-claim and provisional-status totals are not used as current research counts. Readiness and filed claims are read from their current dedicated registers.

## Work added on October 28

The three merged production batches cover **106 attempted orders**, **99 source-review-upheld submissions**, and **88 filed claims**. Seven orders were blocked and eleven upheld submissions remained on mechanical hold. Their six planted controls were caught. The exact tallies and claims remain independently inspectable:

| Batch | Attempted | Source review upheld | Filed | Evidence blocks | Mechanical holds | Records |
|---|---:|---:|---:|---:|---:|---|
| b1a | 36 | 33 | 24 | 3 | 9 | [Tally](../excavator/claude-production-2026-10-28/b1a/packet/supp/complete-v1/TALLY.json) · [Claims](../readiness/claims/claude-2026-10-28-production-b1a.jsonl) |
| b1b | 35 | 34 | 33 | 1 | 1 | [Tally](../excavator/claude-production-2026-10-28/b1b/packet/supp/complete-v1/TALLY.json) · [Claims](../readiness/claims/claude-2026-10-28-production-b1b.jsonl) |
| b1c | 35 | 32 | 31 | 3 | 1 | [Tally](../excavator/claude-production-2026-10-28/b1c/packet/supp/complete-v1/TALLY.json) · [Claims](../readiness/claims/claude-2026-10-28-production-b1c.jsonl) |
| **Total** | **106** | **99** | **88** | **7** | **11** | All 88 filed instrument IDs are distinct |

The combined refresh makes **85 of the 88 newly filed claims ready**: **23/24** from b1a, **32/33** from b1b, and **30/31** from b1c. All **310 previously ready orders remain ready**. **EO 254, EO 2171, and EO 4354** await source-byte verification in the full workflow. Each passes its structural gate and six quotation checks, but its ProQuest scan is recorded only through custody metadata in the standard sparse checkout. These are source-custody holds, not substantive rejections. The [per-claim receipts](../../jobs/claim-checker/output/PER_CLAIM.json), [check details](../../jobs/claim-checker/output/CLAIM_CHECKS.csv), and [per-order tracker](../../jobs/readiness-tracker/output/READINESS_BY_ORDER.csv) retain the exact reasons.

The earlier **20-order spent-order probe filed 15 claims** and retained four evidence blocks plus one mechanical hold. Its [completion tally](../excavator/claude-spent-probe-2026-10-28/packet-v6/supp/complete-v1/TALLY.json) records two of two controls caught. Those filings precede the three batches above.

The separate [blinded status-review packet](../excavator/claude-status-proposals-2026-10-28/batch-1/) contains **143 review rows, including planted controls**. Merging the packet did not adopt those statuses. The current 3,403-row status register adds the previously adopted **15 Bowditch and 29 Sinclair** rows to the older 3,359-row inventory. Status adoption remains governed by the [October 21 ruling](../readiness/owner_rulings/2026-10-21-status-proposal-adoption.md).

## Source recovery

| Measure | Published result | Source |
|---|---:|---|
| ProQuest PDF files / distinct census orders with PDFs | **2,807 / 2,750** | [Pinakes summary](../../jobs/pinakes-proquest-ingest/output/SUMMARY.json) |
| Usable ProQuest machine texts | **2,440** | Same summary; text availability is separate from a page check |
| Low-quality, probably handwritten texts | **310** | Same summary; these still need a usable reading |
| Supplied ProQuest links without a matching PDF | **15** | Same summary |
| Published web-source capture hashes / failed captures | **526 / 2** | [Cotton summary](../../jobs/cotton-capture-custody/output/SUMMARY.json); source-copy counts, not completed orders |

Under the [October 21 working-text ruling](../readiness/owner_rulings/2026-10-21-transcription-as-text.md), an explicitly reviewed and disclosed transcription can support provisional research while original replacement and quotation rechecking remain obligations. The source's original-authentication grade is unchanged.

## Measured effort

The spent-order probe records **79.40 producer minutes + 9.05 reviewer minutes = 88.45 worker-minutes**, including the recorded reruns and corrections. With **15 filed claims**, that is **5.90 recorded worker-minutes per filed claim**. Dividing by the sixteen source-review-upheld submissions gives 5.53 minutes per upheld submission. These denominators measure different outcomes. See the [session telemetry](../excavator/claude-spent-probe-2026-10-28/packet-v6/supp/completion/PRODUCER_TELEMETRY.json) and [completion tally](../excavator/claude-spent-probe-2026-10-28/packet-v6/supp/complete-v1/TALLY.json).

Coordinator time and tokens were not measured. The deterministic completion run's 910.64 machine seconds are recorded separately. The earlier 88-minute-per-order comparison is a model assumption, and this probe covers simple own-terms orders. A project-wide net labor saving or a new completion forecast has not been established by these observations.

The [remaining-work snapshot](remaining-work/SNAPSHOT.md), [effort model](remaining-work/EFFORT.json), and [model notes](remaining-work/EFFORT_NOTES.md) preserve earlier planning assumptions. Their dates, inputs, and denominators differ; these historical planning records are not silently revised by the dashboard.

## How to interpret and refresh the counts

1. **Status decisions** answer the provisional present-effect question within the working bibliography.
2. **Filed claims** contain research, including partial histories and replacements. Filing alone does not make an order ready.
3. **Ready for human review** is the readiness tracker's result after its applicable gates and exact claim-checker receipts.
4. **Human certification** requires a separately recorded review of the whole lifecycle and its sources.

The existing daily-digest job generates the current dashboard from those records. It detects new files and changed claims, shows missing exact receipts, and preserves producer timestamps. A combined refresh runs **claim-checker → readiness-tracker → daily-digest**. A failed or older producer generation remains labeled; new filings are never added arithmetically to its ready count.

The [scientific gates](SCIENTIFIC_STATUS_2026-10-17.md) require a supported operative footprint, a first-ending explanation or continuing legal predicate, surviving consequences, counterevidence, and review. The [October 28 evidence ruling](../readiness/owner_rulings/2026-10-28-evidence-not-convenience.md) distinguishes a demonstrated event within an interval from an event whose occurrence remains unknown.

## Historical releases

The [Stage 17 dashboard](../stage17/reports/DASHBOARD_STAGE17.html), Stage 12–17 releases, and [October 17 progress snapshot](https://github.com/D3m0sthene5/Executive-Orders/blob/e1b9300dd3430f3a7b8c57695bbedb68ab94e88e/research/progress/README.md) retain their historical figures. They document earlier work and are not the current operational readout. [PROGRESS.md](../../PROGRESS.md) preserves the release history; [MIGRATION_STATUS.md](../../MIGRATION_STATUS.md) provides archive recovery instructions.

