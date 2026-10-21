# The Afterlife of Executive Orders — corrected Stage 8 integration / Stage 9 handoff

**Prepared:** 2026-10-16  
**Research cutoff:** 2026-10-14, America/New_York  
**Codebook:** 2.0.0 (unchanged)

## Exact coverage accounting

| Reconciliation | YES | NO | UNKNOWN | Determinate | Coverage of validated population |
|---|---:|---:|---:|---:|---:|
| Stage 6 verified | 191 | 1,287 | 13,495 | 1,478 | 9.871101% |
| Stage 7 verified after 3 Astra quarantines | 191 | 1,695 | 13,087 | 1,886 | 12.596006% |
| Stage 8 technical merge, includes 340 Opus NO/NO | 191 | 2,035 | 12,747 | 2,226 | **14.866760%** |

The denominator is **14,973 validated executive orders** (from **15,010 ledger records**). The project has NOT proved this is the complete historical universe, especially for early unnumbered orders. `UNKNOWN` means unresolved present substantive effect, not evidence of continuing or ceased legal effect.

Opus's self-reported 14.886796% was off by exactly three records: it projected from 1,889 Stage 7 determinate statuses, whereas the independent Stage 7 reconciliation held EO **5333, 5335 and 5347**, leaving 1,886. The corrected, cross-checked **technical merge** is 2,226. It preserves the Stage 7 verified source ledger, all original untouched rows, and protected causal/disposition fields, but it does NOT constitute independent legal rereview of 340 primary-source decisions. The Opus acceptance relies on its separate reported reviewers.

Additional Opus Stage 8 details: **368** order decisions; **340** newly determinate NO/NO (256 retirement, 84 NRA), **21** accepted UNKNOWN/UNKNOWN, **5** reviewer NO suggestions still requiring a third/confirming judgment, and **2** held NRA cases. The unresolved queue has **33 entries but 28 unique IDs** (five duplicated), despite the report's 26. The five reviewer-only cases are EO 8256, 8497, 8904, 10225 and 11619. They are **not counted**. All 340 accepted IDs were independently checked against the Stage 7 ledger, were validated UNKNOWN there, and were outside frozen V1–V5 memberships. None overwrote Astra Stage 7 decisions.

There are **3,166** Opus evidence rows: **2,807** have SHA-matching files within the source ZIP and exact literal quotes verified in those files; **359** reference external source paths and were not source-by-source reproduced here. This verifies quote fidelity for the files available and structural consistency, not interpretation of each controlling rule. Opus also flagged inherited title/date mistakes and placeholder cache retrieval times; do not silently correct originals or invent retrieval dates.

## Files and their meanings

- `STAGE8_PRELIMINARY_MERGED_LEDGER.jsonl`: 15,010 rows, incorporating the 340 accepted-reported-reviewed Opus decisions while keeping other rows byte-identical. **Preliminary technical merge, not a certified Stage 8 legal release.**
- `STAGE8_RECONCILIATION_AUDIT.json`: exact counts, input SHA-256 hashes, source checks and known limits.
- `STAGE8_TECHNICALLY_ACCEPTED_340.jsonl`: the 340 accepted IDs, families, producer shard and reported reviewer acceptance.
- `STAGE8_UNRESOLVED_28.jsonl`: each distinct Opus unresolved ID once with its actual blocker and reviewer disagreement where present.
- `STAGE9_TAX_RETURN_INSPECTION_CANDIDATES.jsonl`: **103** broad title matches, still UNKNOWN. No statutory inference has been adjudicated.
- `STAGE9_WWI_EIGHT_HOUR_CANDIDATES.jsonl`: **46** title leads, still UNKNOWN.
- `STAGE9_ALIEN_PROPERTY_CANDIDATES.jsonl`: **196** broad title leads, still UNKNOWN; do not assume the named sale occurred.
- `STAGE9_UNASSIGNED_FAMILY_LEADS.jsonl`: **49** title leads from Astra's frozen-assignment-excluded discovery set (5 emergency-board, 13 dated office closings, 17 commemoration, 14 advisory committee). The 30 GSP candidates are withheld after Astra's zero-acceptance pilot.
- `ASTRA_STAGE9_PROMPT.md`, `OPUS_STAGE9_PROMPT.md`: immediately executable role-specific instructions with independent-review, legal and provenance gates.
- `ORIGINAL_ASTRA_STAGE7_VERIFIED_CHECKPOINT.zip`, `ORIGINAL_OPUS_STAGE8_STATUS_DELTA.zip`: **byte-for-byte copies of both uploaded ZIPs** with all the evidence and review records they included.
- `CODEBOOK_2.0.0_UNCHANGED.json`, `FROZEN_MEMBERSHIPS_V1_V5.json`, etc.: extracted read-only pointers for direct use.
- `REBUILD_STAGE8.py`: standalone deterministic script that reads the two bundled original ZIPs, verifies their exact checksums, checks coverage and V1–V5 nonoverlap, and rebuilds the preliminary merged ledger. `SHA256SUMS.txt` lists every packaged member's hash.

## Assignment-boundary limitation

The exact **1,181-ID reserved Astra assignment list (P1 705, P2 476)** is in the earlier original Stage 7 split/Astra archive, *not* in either of the two new ZIPs. The next sessions must recover that original list to authorize new Opus cohorts. The 49 `STAGE9_UNASSIGNED_FAMILY_LEADS` arose from Astra's own prior exclusion scan and can be piloted as a safe fallback; other title leads must be screened against original frozen assignments before any decision is promoted. Do not approximate the scope by keyword matching.

## Rebuild and verify

Run after extracting this handoff ZIP:

```bash
python REBUILD_STAGE8.py --directory . --output REBUILT_STAGE8_PRELIMINARY_MERGED_LEDGER.jsonl
sha256sum REBUILT_STAGE8_PRELIMINARY_MERGED_LEDGER.jsonl
```

The SHA-256 of the correct Stage 8 provisional merged ledger is `80d6f1aa20e32209d9e9ec4c62f90cbdc5efdfc4c63d21e39dc1d1eeda8e5115`.

**Start Stage 9 from 2,226/14,973 (14.866760%), maintaining provisional/independent-review qualifiers. Do not add the 340 again, reclassify GSP en masse, reopen the full early historical census, or infer legal expiration merely because a record is old.**
