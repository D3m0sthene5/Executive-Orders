# Dagron, 2026-11-06: what NYU's executive-order collection could supply

Named for René Dagron, who put the dispatches of besieged Paris (1870–71) on microfilm for the pigeon post.

**The live manifest is built daily by [`jobs/dagron-collection-manifest/`](../../jobs/dagron-collection-manifest/README.md)**
in `output/nyu-film709/`. That README holds the field list, the group and priority rules, the staging command for
downloaded images and the collection's restrictions. This note records the first build: its counts, its
reconciliation with the earlier figures, and what it found about ingest routes. `SUMMARY.json` beside it is that
build's summary.

- **Built from:** main `0deba1dd46dc792784731045b4e6b7d4adcb0733`. Readiness-tracker generation `42267267276-1:df6760f2…`;
  Domesday register generated 2026-11-06T06:11:55Z.
- **Collection:**
  - NYU Bobst *Presidential executive orders*: Trans-Media microfilm, **Film 709**, 11 reels, offsite in two boxes,
    both available
    ([catalog](https://search.library.nyu.edu/discovery/fulldisplay?docid=alma990007538410107876&vid=01NYU_INST:NYU&context=L)).
  - NYU's HeinOnline *Presidential Executive Orders*: 11 volumes, 1845–1936
    ([catalog](https://search.library.nyu.edu/discovery/fulldisplay?docid=alma9998673098807871&vid=01NYU_INST:NYU&context=L)).
  - Reels: 1 EO 1–707 · 2 708–1348 · 3 1349–2125 · 4 2126–2891 · 5 2892–3579 · 6 3580–4304 · 7 4305–5075 ·
    8 5076–5760 · 9 5761–6336 · 10 6337–6925 · 11 6925A–7403.

## Result of the first build

6,010 rows: 5,954 tracked orders and 56 untracked census candidates.

| Group | Rows | Priorities |
|---|---:|---|
| 1. No accepted original witness, EO 1–7403 | 5,875 | P1 2,196 · P2 1,435 · P3 2,244 |
| 2. Original counted, no working text | 0 | All 2,027 numbered orders in range with a counted original also have its retained text |
| 3. Unnumbered or ambiguous identity | 81 | 17 unnumbered, 8 numeric-suffix, 56 untracked candidates |
| 4. EO 7404 and up, dated 1936 | 54 | Outside the reels; Hein's dates only |

Group 1 is made up of:
- 5,092 orders with the original-text step open;
- 783 orders whose step is satisfied only by a transcription (481 provisional working texts, 302 claims), which the
  tracker requires to be replaced by the original.

Priority 1 is 784 such replacements plus 1,412 orders with no image or printing of any kind. Group 1 by reel (1 to
11): 740 · 580 · 759 · 802 · 739 · 769 · 797 · 112 · 118 · 290 · 169. Reels 8 and 9 are small because most Hoover and
early Roosevelt orders already have counted GPO and OFR printings.

## Reconciliation with the earlier figures (5,305 lacking an official original, 4,954 pre-1933)

**Neither figure appears in the repository.** I searched main, the history of the tracker, the Domesday, digest,
Mabillon and Herschel reports, and the three unmerged agent branches. Measured on the same commit:

| Definition | All | Dated before 1933 |
|---|---:|---:|
| Tracker original-text step open | **5,322** | **4,926** (+45 undated) |
| `text_evidence_tier` not `original_supported` | 6,467 | 5,301 |
| Blocker `NO_OFFICIAL_SOURCE_LOCATED` | 4,787 | 4,641 |
| Domesday `best_held` ≠ `official_original_counted` (14,972 rows) | 6,027 | 5,280 |
| Mabillon frame, 2026-11-05 | 5,943 | – |
| Herschel projection, 2026-11-05 | 5,313 | – |

The earlier pair is closest to the **open original-text step**. The difference is consistent with:
- the 26 orders admitted to the census on 2026-11-06;
- Justinian's R3 re-tag;
- Mabillon and Tischendorf finds that moved orders between blockers.

How the manifest relates to the 5,322 open orders:
- **In the manifest:** 5,092 in group 1, 25 in group 3 and 12 in group 4.
- **Excluded:** 190 numbered above 7403 and dated after 1936, and 3 unnumbered orders dated after 1936.
- **Added:** the 783 transcription-dependent orders in range, because they also lack an accepted original.

**Held remotely, not retained.** For 1,902 group-1 orders a source was read and its text kept, but its bytes are not
committed: transcription pages, Civil Service Commission report scans, HathiTrust and Internet Archive printings.
For 9 more, a ProQuest link was supplied but no PDF uploaded, and 1 has a NARA image of the signed original. The
daily job lowered this to 1,839 when it began reading the Git LFS source books' hashes from their pointers.

## Found along the way

- **No ingest route exists for NYU or Hein files.**
  - Pinakes reads only ProQuest accession names, and its folders are off limits.
  - `research/stage21/original_sources/` would wrongly *count* a microfilm image: the tracker treats
    `PDF_BYTES_CAPTURED…` custody as a satisfied original.
  - The job's `record_acquisition.py` stages images in `research/acquisitions/nyu-film709/`, which only Dagron reads.
- **Hein volume = reel is an assumption.** Verify it with EO 707/708 and 1348/1349 before relying on it.
- **Restrictions already recorded:**
  - the owner's 2026-10-19 rule: no paid reproduction, no hand-scanning of microfilm, and "do not plan around the
    reel set" (Kean A-20261106-dagron-nyu asks whether to lift it for Film 709);
  - no automated bulk download from HeinOnline;
  - no bulk harvest through the owner's NYU session.
