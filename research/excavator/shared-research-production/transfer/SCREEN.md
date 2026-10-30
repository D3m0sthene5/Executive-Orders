# Transfer prerequisite screen

**Correction to v1:** v1 is rejected for an incorrect EO 12379 full source hash and for wording that could imply its whole family was reserved. The corrected source hash, native SourceIndex copy roster, all 23 target source hashes, reservation roster, and unreserved claim-file entries are recorded in `SCREEN.json`. The source PDF itself is not present in the checkout, so its hash can be verified against consistent source records but not recomputed from raw PDF bytes here.

Screened from the checkout at `f9c6d806ad059dcad7875ab3708715f20ea386df` on 2026-10-30. This is a bounded read of committed Polya, X1, family-rule, tracker, source-custody, native SourceIndex, and prior-review outputs; no acquisition or production run was performed. Counts below describe the pinned outputs, not a regenerated run on this checkout.

## Family-rule blockers

`jobs/family-rules/output/SUMMARY.json` reports 748 target certificates across 25 rules, 51,201 saved texts scanned, and **0 bounded-check passes**. The blocker counts are overlapping target flags; they must not be summed.

| Blocker | Targets flagged |
|---|---:|
| Original-source custody unverified | 748 |
| Target independent clauses not reviewed | 748 |
| Independent clause or savings lead | 744 |
| Later or undated saved-text use | 708 |
| Current-law use lead | 316 |
| Qualified or conflicting scope | 17 |
| Earlier or undated ending | 75 |
| Date conflict or unknown | 72 |
| Rule effective date unproven | 34 |
| Rule savings unreviewed | 23 |
| Target original text missing | 23 |
| Target outside rule scope | 67 |
| No matching ending edge | 6 |

The family-rules run is successful but old: `STATUS.json` pins it to `d66f404065c96e57a243d0e5a1d53bd8e2103070`, started 2026-10-24 03:04:46Z and finished 03:05:48Z (62 seconds). Its sweep manifest is `40409cc7…cf8f`. Polya and X1 also read older snapshots: their output `STATUS.json` files pin to `adcf881ef7eb897e6bec8a8bd7717f4eb3629039`, with Polya taking 20 seconds (07:16:23–07:16:43Z) and X1 32 seconds (07:15:51–07:16:23Z) on 2026-10-29. These are existing workflow timings, not a measured transfer or readiness gain.

Polya's older comparison has 14,972 orders, 395 ready, and 14,577 not ready; its F4 legal-family frame reaches 3,482 distinct not-ready orders (23.9%), but this is reach, not yield. X1's `TYPES.csv` and cluster sheets are class/cluster leads, not family-rule proofs. Neither metric supplies the missing custody, target review, or legal prerequisites.

## Non-NRA example screened: EO 12379 revocation family

EO 12379 is a useful diagnostic example because its rule explicitly scopes 23 targets and the 1982 Federal Register issue is indexed as an official source. It is **not a new source-ready or unreserved family assignment**.

- The actor source record is `jobs/fr-originals/data/full_run/SOURCES.jsonl` (EO:12379, SHA-256 `5432431cc09039ad5672f86f17e1fb6dddf44075581197caa24cd70f1448da4a`, official GovInfo issue PDF, 91,189,374 bytes; 47 FR 36099, PDF pp. 9–10). That exact hash appears in the full-run and current fr-originals output records, plus later-events, source-ladder, family-rule-sources, and Astra source-retention records. A lookup of that hash in the native SourceIndex (`jobs/claim-checker/sources.py`) finds 9 copy records, all `record_only` and zero with raw bytes retained. The registered PDF cache path does not exist here. Thus local index evidence supports a source-record trail, not repository-held PDF bytes; `original_custody_verified: false` remains correct. Saved text exists at `jobs/fr-originals/output/texts/EO_12379.txt`, `jobs/family-rule-sources/output/texts/queue_EO_12379_EO_12379_0b10726a10.txt`, and source-ladder copies; the family-rule text's actual SHA-256 is `ace4c68f1a5d2e44012894279ab3f38a0c8a08841bebe361d6eb39ae09b2d9bd`.
- The 23 scoped target originals have 23 source rows in `jobs/fr-originals/output/SOURCES.jsonl`; their individual PDF SHA-256 values are listed in `SCREEN.json`. Native SourceIndex lookup finds 123 target-PDF copy records in aggregate, all record-only with zero raw bytes retained. This is a bounded lookup by the exact actor and target source hashes, not a conclusion that their source records or derivative texts do not exist.
- All 23 scoped target dossiers exist, are marked `original_supported` in the tracker, and have provisional NO status. Five are marked ready for human review and 18 are not. This does not override the family-proof requirement: the rule's `target_scope_reviewed` list is empty. Every one of the 32 EO:12379 fragment rows is blocked on original-source custody, target independent-clause review, independent-clause/savings leads, and later/undated saved-text use; 9 rows additionally carry an out-of-scope lead. Several dates/current-law leads also remain.
- Prior work is substantial and overlaps an existing assignment. `research/readiness/reviews/astra-2026-10-18/BATCH1_RESERVATION.json` lists 10 of these 23 targets under actor EO:12379: EO:11022, EO:11256, EO:11782, EO:11829, EO:12075, EO:12095, EO:12159, EO:12182, EO:12262, EO:12285. The remaining 13 are not listed in that reservation, so the whole family is not described as reserved. Three of those 13 (EO:12083, EO:12089, EO:12194) have entries in `research/readiness/claims/*.jsonl`; the other 10 do not. For EO:11829 specifically, the tracker has 4/6 steps done and leaves ending/current basis and savings/residuals open; its prior independent review is not family-wide clause review or a completed lifecycle claim.
- Repeated-action issue: the family output also contains EO:12202 as a later EO:12399 revocation target. `research/readiness/rules/EO_12399.json` explicitly notes that EO:12379 had already revoked EO:12202 on 1982-08-17, so the later repetition does not establish first cessation. This is a live duplicate-event distinction, not a reason to reuse a blanket family ending.

**Disposition:** no member of this screened family satisfies the requested joint held-original-bytes prerequisite in the current native SourceIndex: all 9 actor-source copies and all 123 target-source copies are metadata/text records, with zero raw bytes retained. This is why no source-ready cohort is nominated here; it is not because all members are reserved. Ten targets are listed in the existing reservation, and 13 are not; current claim, tracker, and reservation state must be rechecked before selecting from those 13. A future assignment would first need retrievable actor and target original bytes with page verification; target-by-target independent clause and savings review; resolution of earlier/duplicate/later-event and current-law leads; and exact current dossier/status/reservation checks.

## Run and limits

Actual model: **OpenAI gpt-6-luna**. Read-only screen conducted on 2026-10-30 UTC. I did not start a prospective task clock at first contact, so exact active time for this screen is unavailable; token and dollar telemetry are unavailable. The workflow timing above is the only measured duration available. No code, canonical science, claims, reservations, or Git state was changed.
