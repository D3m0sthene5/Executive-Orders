# F11490 outcome (Lambertini per instrument)

Pool: 20 orders superseded by EO 11490 of 1969-10-28 (34 FR 17567, sec. 3015). Ending text cited from the official FR text (FR-1969-10-30.pdf, PDF pages 63-95), never the APP transcription. Every claim is an AI hypothesis. None is certified, and the certified whole-lifecycle count stays 0.

| Batch | Attempted | Effective upheld | Rejected | Blocked | Plant caught |
|---|---|---|---|---|---|
| p (probe) | 8 | 6 | 2 | 0 | yes |
| s1 | 6 | 2 | 0 | 4 | yes |
| s2 | 6 | 6 | 0 | 0 | yes |
| **Total** | **20** | **14** | **2** | **4** | **3/3** |

- Probe gate (at least 5 of 8 upheld, at most 1 savings state overturned, plant caught): **passed** at 6/8 = 0.75. No savings state was overturned in any batch.
- 14 claims were filed in `research/readiness/claims/claude-f11490-{p,s1,s2}-2026-10-20.jsonl`. All pass kit.py check and the claim-checker; checker output was reverted and its cache deleted.
- Every upheld order ends on 1969-10-28, the signing date. 1969-10-30 is only the FR printing date, and that was the defect in all three plants.

## Rejected (D6 or gap defects)
- EO 10998: an OFR "See" note to FR Doc. 62-9459 (27 FR 9418) is not held (FETCH_QUEUE line 573), but the claim records no gap.
- EO 11003: D6 is incomplete. The Department of Transportation Act (Pub. L. 89-670) moved the FAA functions before 1969 and the statute is not held. The held EO 11382 is not discussed.

## Blocked (not decided)
- EO 11004: the HUD Act (Pub. L. 89-174) is not held (FETCH_QUEUE line 575).
- EO 11005 and EO 11088: the DOT Act (Pub. L. 89-670) is not held (FETCH_QUEUE line 576).
- EO 11090: the only end evidence is the APP transcription. Using it would raise the pending transcription-as-copy ruling.

The pending owner rulings (report-deadline, transcription-as-copy, EO 14052 strike-and-reinsert) were not decided. No item was struck and reinserted.

Source tallies: `p/TALLY.json`, `s1/TALLY.json`, `s2/TALLY.json`. Machine summary: `OUTCOME.json`.
