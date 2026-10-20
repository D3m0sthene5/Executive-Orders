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
