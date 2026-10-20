# Rastell: ACT provision records (2026-10-20)

**Pool.** 700 decided not-ready orders: 1,088 (target, actor) pairs over 325 actors. EO 12553 accounts for 333 of the orders. The RASTELL pool and its census are described in the brief.

**Forecast vs outcome (Llull outcomes recorded; the source file OUTCOME.json is uncommitted, so the outcomes would be flagged not_preregistered if committed together with the forecast, as happened to L-1 and L-2)**
- L-20261020-15, records upheld per attempt: forecast p10 0.04, p50 0.45, p90 1.0. Measured 0.826 (57 of 69), recorded as O-20261020-5. This is above p50 and inside the interval.
- L-20261020-16, claims enabled among the 40 probe orders: forecast p10 0, p50 6, p90 14. Measured 2 (EO 5737 and EO 5848), recorded as O-20261020-6. This is below p50 and inside the interval.
- Both come from independent AI review. They are hypotheses, not human certification.

| Batch | Attempts | Upheld | Refuted | Not located (confirmed) | Rate | Claims enabled |
|---|---|---|---|---|---|---|
| 01 | 26 | 21 | 1 | 4 | 0.81 | 2 |
| 02 | 43 | 36 | 2 | 5 | 0.84 | 0 |

The gate failed on plant detection only. The rate (0.826 against 0.45) and the per-batch floor (0.30) both pass. I found no `review/PLANT.json` anywhere, and neither reviewer could see it. Batch_01 refuted `ACT:EO:11371>EO:12148` as a likely plant (D6 ignored). Batch_02 refuted two WRONG_TARGET records, `ACT:EO:12271>EO:12336` and `ACT:EO:12271>EO:12399`. Whether the plants were caught is not verified, so batch_03 onward did not run.

**Blockers**
- Plant check: the coordinator must confirm each batch's plant against the plant record. A missed plant voids that batch's upheld count.
- No ingestion path exists for ACT records in claim-kit. They stay research leads and move no tracker number.
- EO 12553 emergency boards depend on the owner's ruling on report deadlines (Polya row 9).
- EO 7968: the held OCR needs a page check.

**Claim-checker.** Not run, because no claims were made.

**FETCH lines.** One appended to `research/readiness/FETCH_QUEUE.jsonl`: EO:7968, 3 FR 2185 (1938-09-08), step ending_or_current_basis, to settle the two claims-enabled records. A source request for the EO 11771 lapse in 1979 is a candidate next step but was not queued.

**Expected new ready orders.** 0 now. At most 2 (EO 5737 and EO 5848) after a 7968 page check and a kit change to ingest ACT records.

**Git status.** My changes are `research/excavator/rastell-2026-10-20/` (untracked), one line in `FETCH_QUEUE.jsonl`, and `jobs/llull/ledger/outcomes.jsonl`. The other untracked paths (lambertini, lamm, `LAMBERTINI_DESIGN.md`) belong to other workflows. Nothing is committed, and I made no claims.

SUMMARY: Rastell probe upheld 57 of 69 records (0.826, above the 0.45 p50), but the gate failed because plant detection is unconfirmed (no PLANT.json); batch_03 onward did not run. Claims enabled: 2 of 40 (p50 was 6). Llull outcomes O-5 and O-6 are recorded. One FETCH line (EO 7968) was added. No claims were made and certified stays 0. Nothing is committed.

**Coordinator note:** no plants were ever inserted (the brief assigned that to a "coordinator" role no workflow agent held), so gate condition 3 failed on process, not on review quality. The 3 refuted records are real defects.

**Ingestion (follow-up, 2026-10-20).** `jobs/claim-kit/act_overrides.py` now reads `research/readiness/act_overrides/*.jsonl`, re-slices every span from the held actor text, checks the sha256 values, and requires an independent upheld review with a D6 step. It refuses seeded, planted and example records, pairs the scanner already located, and duplicates. The 57 upheld records are in `rastell-2026-10-20.jsonl`. A local full build (scratch output, not committed) ingested 55 and refused 2: `ACT:EO:10972>EO:12220@rastell` (the scanner now holds a whole_via_parent lead for that pair) and `ACT:EO:11287>EO:12692@rastell` (names_target true but reaches_target_via set, and the number is not in the span). Result: 35 dossiers lose the ACT gap, 22 orders newly meet the Llull ending_instrument_held gate, and 18 dossiers have no missing line. The reviewer still counts only 2 claims enabled (EO 5737, EO 5848, pending the EO 7968 page check), because 15 of the 17 mechanical candidates have an earlier end found at D6. Nothing is pushed. Outcomes O-20261020-13 and O-20261020-14.

**Batch_03 (EO 12553 subline, 2026-10-20).** 20 pairs, 20 records, 20 located. A planter inserted 2 plants into the review packet (key outside the repo): a span moved to the adjacent row and an invented effective date. The independent reviewer refuted both (SPAN, EFFECTIVE), so plant catch is 2 of 2. Upheld 18 of 20 (0.90; no genuine record was refuted); 17 are claims-enabled yes. EO 10080 is upheld but not claims-enabling (its one-year window closed 1950-09-30). Gate for the subline (>=0.70 upheld and >=5 of 20 orders claims-enabled): pass. The 18 upheld clean records were appended to `research/readiness/act_overrides/rastell-2026-10-20.jsonl` (75 lines in all); the packet copy with plants was deleted and the plants never reached research/ or jobs/. A scratch build ingests 73 of 75 (same 2 refusals as before). Effects: 17 more dossiers lose the "target provision not located" line (1229 to 1212), 17 more dossiers have no missing lines (903 to 920), and 18 more orders have a whole-scope dated ending ACT (22 to 40). All 18 rest on EO 12553, whose on_signing date is a reading, so they are upper bounds, not certified ends. AI hypotheses only; certified count stays 0. No Llull forecast was registered for batch_03, so no outcome is attached.

**Rastell III (batches 04-08, EO 12553 subline, 2026-10-20).** 100 pairs, 100 records, all located. A planter put 2 plants in each scratch copy of the review packet (one span moved to the adjacent row, one invented effective date, 1986-03-03 in place of 1986-02-25). The key was kept outside the repo. The independent reviewers did not open the keys.
- Plant scoring: 10 of 10 caught (SPAN and EFFECTIVE, matching the plant types). No genuine record was refuted. Batches 03-08 together: 12 of 12 plants caught. No batch was voided.
- Upheld 18 of 20 in every batch (90 of 100 attempts; 90 of 90 genuine records upheld). Claims enabled: b04 17, b05 16, b06 16, b07 17, b08 17 (83 in all; 100 with batch_03). The orders not enabling claims have an earlier-end lead (EO 10157, 10323, 10504, 10738, 10774, 10976, 11026). EO 12553 is only an upper bound for them. All 90 rest on the on_signing reading of EO 12553 (1986-02-25), so the ends are upper bounds, not certified ends.
- The plant-bearing packet copies were deleted from scratch. The plants never reached `research/` or `jobs/`. The plant keys were scored and removed.
- The 90 upheld genuine records (the producer's unplanted records) were appended to `research/readiness/act_overrides/rastell-2026-10-20.jsonl`, now 165 lines. For each batch I wrote the reviewer ledger `batch_0N/review/REVIEW.jsonl` from the reviewer's verdicts and `UPHELD_ACT_RECORDS.jsonl` from the producer's records. For batches 07 and 08 the reviewer name was in the batch summary only, so I copied it into each ledger entry.
- Scratch claim-kit build (deleted afterwards): 163 ingested, 2 refused. The refusals are the same two as before, `ACT:EO:10972>EO:12220` and `ACT:EO:11287>EO:12692`. Located actor pairs rose from 10,404 to 10,512 (+108, so +90 from this run and +18 from batch_03).
- Llull: batches 03-08 had no registered forecast, so no outcome was recorded and no after-the-fact forecast was registered. The four Rastell forecasts (L-15, 16, 24, 25) already have outcomes.
- These are AI review hypotheses. The certified count stays 0. Nothing was committed or pushed.
