# Stage 15 sample estimate: operative force on 2026-10-14

**Provisional, AI-reviewed, uncertified, n=120.** Dorotheus, 2026-11-06 (owner rulings R1, R16). Human-certified whole-lifecycle dossiers: 0.

Design: the 120-order Stage 15 stratified population sample (`research/stage15/STATISTICS/STRATIFIED_POPULATION_SAMPLE_120_BLIND.csv`), 12 strata (era x source class), design weights summing to the 14,972-order census. Method and code: `research/dorotheus/estimate.py`; full output `SAMPLE_ESTIMATE.json`; per-order outcomes `research/excavator/dorotheus-sample-2026-11-06/DISPOSITION.csv`.

## Headline

- **Operative force, responses only (missing at random within stratum): 0.0% (95% interval 0.0% to 17.6%; 19 respondents).** Every one of the 19 responding orders had no operative clause on the cutoff.
- Producers' assessment of every order they were assigned, filed or not, "unknown" treated as missing (not reviewed): 5.3% (95% interval 1.2% to 14.2%; 69 respondents).
- Sensitivity, all nonresponse NO: 0.0% (95% interval 0.0% to 3.0%; 120 respondents). All nonresponse YES (worst case): 79.7% (95% interval 70.1% to 87.4%; 120 respondents).
- **Formal validity (unrevoked on the books), responses only: 0.0% (95% interval 0.0% to 26.5%; 12 respondents)**; all nonresponse revoked: 0.0% (95% interval 0.0% to 3.0%; 120 respondents).

**Read this before quoting a number.** Only 19 of 120 orders (16%) produced a filed, reviewed claim: the 12 already-ready orders and 7 newly filed undecided orders. Nonresponse is not random: 38 orders were dispatch-blocked (no held original, custody-only sources, or another owner's open claim) and 63 were blocked by a producer, 28 of them only because the claim kit's undecided route refuses a held transcription as the working text even though the 2026-10-21 ruling allows it. The 1862-1906 and unknown-date strata have no respondent at all, so their weight is carried by borrowed stratum means (see `SAMPLE_ESTIMATE.json` notes). The MAR interval therefore understates the uncertainty; the producer-assessment figure (69 orders, 3 assessed YES) is the most informative reading, and the bounds above bracket it.

## Estimator

Stratified mean, p = sum_h (N_h/N) p_h, with p_h the respondents' mean in stratum h. Variance sum_h (N_h/N)^2 (1 - r_h/N_h) s_h^2 / r_h (finite-population corrected; certainty strata contribute 0; a stratum with fewer than 2 respondents is collapsed with the largest stratum of its era). Intervals: Korn-Graubard (Clopper-Pearson on the effective sample size p(1-p)/V with degrees of freedom respondents minus strata). With every response 0 the variance estimate is 0, so the interval uses the respondents as the effective sample size (a conservative choice: no design effect below 1 is claimed).

## Response by stratum

| Stratum | n | Filed | Ready (existing) | Blocked | Dispatch-blocked |
|---|---:|---:|---:|---:|---:|
| 1862–1906 | documented_unnumbered | 1 | 0 | 0 | 0 | 1 |
| 1862–1906 | validated_historical_index | 11 | 0 | 0 | 11 | 0 |
| 1862–1906 | validated_numbered | 2 | 0 | 0 | 2 | 0 |
| 1907–1936 | validated_historical_index | 36 | 0 | 5 | 20 | 11 |
| 1907–1936 | validated_numbered | 10 | 1 | 0 | 3 | 6 |
| 1937–1989 | validated_historical_index | 1 | 0 | 0 | 0 | 1 |
| 1937–1989 | validated_numbered | 31 | 4 | 7 | 18 | 2 |
| 1990–2026 | validated_numbered | 18 | 2 | 0 | 3 | 13 |
| Unknown date | documented_unnumbered | 2 | 0 | 0 | 0 | 2 |
| Unknown date | validated_historical_index | 5 | 0 | 0 | 4 | 1 |
| Unknown date | validated_historical_reprint | 1 | 0 | 0 | 1 | 0 |
| Unknown date | validated_numbered | 2 | 0 | 0 | 1 | 1 |

## Goal 3: the cleanup question

- First cause among the 19 NO responses: later_presidential 11, legislative 5, under_original_terms 3.
- `formal_revocation_after_earlier_cessation = true` among NO responses: **1** of 19 (11 no, 7 unknown). In the sample's respondents, a formal revocation that came after the order had already ceased is rare; the 184 claims re-tagged under R3 (#174) are where this question concentrates.

## Reviewer catch rate and the defect bound

Two blind Sonnet reviewers per batch, a third where a plant was missed (3 batches). Plants: 30 (date shifts of end, event and signing dates; Mountweazel D3, D4, D5, D6, D7, D8; D1, D2 and D9 have no base in the pool). **Caught 25 of 30 (83%; 95% interval 65% to 94%)**, 22 of 30 strictly (`PLANTS.csv`). Misses: 2 of 3 Mountweazel D6 (a later event removed), 1 of 3 D3 (end quote cut before the verb), 2 of 3 signing-date shifts. With 0 genuine rejections among the 14 upheld claims, the 95% upper bound on their defect rate is 23% before correcting for misses, 28% at the point catch rate and 36% at its lower bound (the Mountweazel production conversion).

## Cost

About $67 API-equivalent for producers and reviewers plus $15 for the wave coordinator session (`telemetry/`). Context per attempted order about 1.38M tokens, far above the 150k target: packets of up to 6 orders with full dossier views still load the shared evidence per producer.
