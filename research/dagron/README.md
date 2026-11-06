# Dagron: what NYU's executive-order collection could supply, order by order

Named for René Dagron, who put the dispatches of besieged Paris (1870–71) on microfilm for the pigeon post.

This folder is a **handoff for a browser agent with NYU Libraries access**. It lists every tracked order whose
missing evidence the NYU collection could supply, with what the project already holds for it and where. It is
read-only with respect to production: no status, readiness count, census row, codebook text or job output was
changed, and nothing here is wired into any job.

- **Built from:** commit `0deba1dd46dc792784731045b4e6b7d4adcb0733` (main, 2026-11-06). Readiness-tracker generation
  `42267267276-1:df6760f2…`; Domesday register generated 2026-11-06T06:11:55Z.
- **Regenerate:** `python3 -I research/dagron/build_manifest.py <COMMIT> research/dagron`. It reads every input from
  that commit with `git show`, so no checkout is needed and the output is exact for the commit.

## The collection (routing leads, not proof of inclusion)

| | Physical microfilm | Online scans |
|---|---|---|
| What | *Presidential executive orders*, Trans-Media, 11 reels of 35 mm film, call no. **Film 709**, offsite in 2 boxes (both available) | HeinOnline *Presidential Executive Orders*, 11 digitized volumes, 1845–1936 |
| Catalog | [alma990007538410107876](https://search.library.nyu.edu/discovery/fulldisplay?docid=alma990007538410107876&vid=01NYU_INST:NYU&context=L) | [alma9998673098807871](https://search.library.nyu.edu/discovery/fulldisplay?docid=alma9998673098807871&vid=01NYU_INST:NYU&context=L) |

Reels: 1 EO 1–707 · 2 708–1348 · 3 1349–2125 · 4 2126–2891 · 5 2892–3579 · 6 3580–4304 · 7 4305–5075 ·
8 5076–5760 · 9 5761–6336 · 10 6337–6925 · 11 6925A–7403.

`likely_hein_volume_unverified` assumes Hein volume *n* = reel *n*, because both are 11 units. **Verify it first.**
Open EO 708 in Hein (a browser agent already opened its image) and record the volume and image number. Then open
EO 707, EO 1348 and EO 1349, and confirm the volume boundaries before relying on the column.

## Files

| File | What |
|---|---|
| `NYU_FILM709_MANIFEST.jsonl` | **The manifest**: 6,010 rows, one per order or candidate, with nested evidence records (22 MB). |
| `NYU_FILM709_MANIFEST.csv` | The same rows flattened, one line each, for spreadsheet use (8 MB). |
| `SUMMARY.json` | Every count below, plus the reconciliation figures. |
| `SAMPLE.jsonl`, `SAMPLE.csv` | 11 representative rows. |
| `build_manifest.py` | The deterministic builder. |
| `record_acquisition.py` | Records a downloaded file with provenance in a staging folder (see Ingest). |

## Groups (each order appears once)

1. **`1_missing_accepted_original_witness` (5,875 orders).** Numbered EO 1–7403, letter and fraction variants
   included, where the tracker's `text_evidence_tier` is not `original_supported`. That covers:
   - 5,092 orders whose original-text step is open;
   - 783 orders whose step is satisfied only by a transcription (481 provisional working texts and 302 claims that
     depend on transcriptions); for these the tracker requires the original copy as a replacement.
2. **`2_missing_accepted_working_text_only`: 0 orders.** All 2,027 numbered orders in EO 1–7403 that have a counted
   original witness also have a retained text of that witness. The flag `missing_accepted_working_text` is still
   carried on every row: 5,092 of group 1 lack an accepted working text, besides lacking the original.
3. **`3_unnumbered_or_ambiguous_identity` (81 rows).** Kept apart: numbered coverage does not establish inclusion.
   - 17 unnumbered census orders dated in 1845–1936. Most are NARA 1989-codification rows; one comes from the Lord
     1944 list. Several predate EO 1.
   - 8 numeric-suffix orders (`EO:8-1`, `9-2`, `23-1`, `27-1`, `28-1`, `30-1`, `64-1`, `106-1`), which are second
     orders recorded under one number.
   - 56 **untracked** census candidates (`instrument_id` empty, `proposed_id_not_in_census` set). An index or
     citation names them but the census does not hold them; for these an image supports census intake, not readiness.
4. **`4_edge_numbered_after_reel_11_within_hein_dates` (54 orders).** EO 7404 onward, dated 1936, with missing
   evidence. They are outside the cataloged reels, and only Hein's stated end year suggests coverage. Check Hein only.

## Columns that matter

- **Identity:** `instrument_id` (canonical id), `eo_designation` (exact designation, letters and fractions kept),
  `number`, `suffix`, `signature_date` + `date_source`, `title`, `president`, `census_class`.
- **Routing:** `likely_reel`, `likely_hein_volume_unverified`, `coverage_uncertainty` (reel-boundary notes, e.g.
  6925 vs 6925A, variants of a reel's last number, unnumbered or pre-1862 items).
- **Missing evidence (`missing.*`):**
  - `missing_accepted_original_witness`
  - `missing_accepted_working_text`
  - `original_copy_replacement_required`
  - `no_image_of_any_kind_retained`
  - `has_signed_original_replica_scan`, with `replica_scan_text_usable`
  - `has_official_printed_copy_lead`
  - `has_uncounted_printing_or_reprint`
  - `has_transcription_only`
  - `no_witness_of_any_kind`
- **Tracker state:** `tracker.*` holds the tracker's step, tier, original-text blockers, provisional status and
  claim presence (context only).
- **Held evidence, by distinction** (`held.*`; every record carries its producing job, fragment file, grade,
  `page_or_item`, URL, source SHA-256, **`source_bytes_retained_path`**, **`text_path`**, `needs_page_check` and
  `acceptable_as_original`):
  - `signed_original_replica_scans`: ProQuest "Replica of Original" scans of the signed original. Lead only until
    a page check and a codebook grade.
  - `official_printed_copies`: Federal Register, GPO and OFR compilations, Isthmian Canal and Indian-reservations
    compilations, Tischendorf and Mabillon finds, and Opus media. Counted only when the job did not flag
    `needs_page_check`; on these rows none is counted.
  - `uncounted_printings_or_reprints`: HathiTrust GPO volumes, government printed copies from `numbered-early-orders`
    and Civil Service Commission report reprints. The tracker reads these as leads, never as the original.
  - `transcriptions`: the American Presidency Project, Wikisource and Richardson.
  - `index_entries`: the census bibliographic class, WPA/Lord list citations and NARA catalog descriptions. These
    are index entries, not texts.
- **Remote and routes:** `remote_evidence_not_retained_locally` and `other_acquisition_routes_known` (see below).
- **Priority:** `acquisition_priority` + `priority_reason`; `identity_uncertainty`.

## Priority (1 = acquire first)

| Priority | Rule | Orders |
|---:|---|---:|
| 1 | Group 1 and either (a) the working text is a transcription the tracker requires to be replaced by the original (784; an image closes the obligation), or (b) **no image or printing of any kind is held** (1,412) | 2,196 |
| 2 | Group 1, no usable image of the signed original. Either the ProQuest replica text is unusable (308, likely handwritten), or only an official-printing lead or reprint is held (1,127) | 1,435 |
| 3 | Group 1, a ProQuest replica with usable text is held, pending a page check. A NYU image corroborates it. | 2,244 |
| 4 | Group 3: confirm identity and inclusion before attaching anything | 81 |
| 5 | Group 4: outside the reels; Hein only | 54 |

`priority_reason` also notes when an order already has a provisional status or a claim, since an image there
moves it nearest to review.

## Counts by likely reel (all groups)

| Reel | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | none |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Group 1 | 740 | 580 | 759 | 802 | 739 | 769 | 797 | 112 | 118 | 290 | 169 | – |
| Group 3 | 28 | 1 | 1 | 3 | 1 | 1 | 0 | 3 | 24 | 1 | 1 | 17 |
| Group 4 | – | – | – | – | – | – | – | – | – | – | – | 54 |

Reels 8–9 are small because the Hoover and early Roosevelt orders mostly have counted GPO and OFR printings
already. Group 3's 24 on reel 9 are untracked candidates around EO 5853–5879.

## Missing-evidence categories in group 1 (overlapping)

- No accepted working text: 5,092.
- Transcription to be replaced by the original: 784.
- No image of any kind retained: 2,859.
- A signed-original replica scan is held: 2,746; its text is usable for 2,437.
- Only a transcription is held: 1,569.
- An official-printing lead is flagged for a page check: 583.
- An uncounted printing or reprint is held: 978.
- No witness of any kind: 48.
- Dated before 1933: 5,277; undated: 44.

## Reconciliation with the earlier figures (5,305 lacking an official original, 4,954 pre-1933)

**Neither figure appears in the repository.** I searched main, the history of the tracker, Domesday, digest, Mabillon
and Herschel reports, and the three unmerged agent branches. Treat them as unverified. Measured today, on the same
commit, under each definition the project uses:

| Definition | All orders | Dated before 1933 |
|---|---:|---:|
| Tracker original-text step open (no witness, not even provisional) | **5,322** | **4,926** (+45 undated) |
| `text_evidence_tier` not `original_supported` (adds transcription-dependent) | 6,467 | 5,301 |
| Blocker `NO_OFFICIAL_SOURCE_LOCATED` | 4,787 | 4,641 |
| Domesday `best_held` ≠ `official_original_counted` (14,972-row register) | 6,027 | 5,280 |
| Mabillon frame, 2026-11-05 (`NO_OFFICIAL_SOURCE_LOCATED` that day) | 5,943 | – |
| Herschel projection from 110 sampled orders (2026-11-05) | 5,313 | – |

The earlier pair is closest to **the original-text step open** (5,305 → 5,322, +17; 4,954 → 4,926 dated plus 45
undated). The difference is consistent with:
- the 26 orders admitted to the census on 2026-11-06;
- Justinian's R3 re-tag;
- Mabillon and Tischendorf finds that moved orders between blockers.

How the manifest relates to the 5,322 open orders:
- **In the manifest:** 5,092 in group 1, 25 in group 3 (unnumbered or numeric-suffix) and 12 in group 4.
- **Excluded:** 190 numbered above 7403 and dated after 1936, which the collection does not cover; and 3 unnumbered
  orders dated after 1936.
- **Added beyond the open set:** 783 transcription-dependent orders in range (481 provisional, 302 claim-dependent),
  because they too lack an accepted original. They are flagged `original_copy_replacement_required`.

**Evidence held remotely but not retained locally.** For 1,902 group-1 orders, a source was read (URL and SHA-256
recorded, and its extracted text is in the repository) but the source's bytes are not committed:
- 1,021 transcription pages;
- 798 Civil Service Commission report scans;
- 652 official printings, mostly HathiTrust and Internet Archive volumes;
- 112 uncounted GPO printings;
- 9 with a ProQuest link supplied but no PDF uploaded;
- 1 NARA digitized image of a signed original.

These are listed per order in `remote_evidence_not_retained_locally`. `other_acquisition_routes_known` adds Lewis's
routes: 2,451 orders need a ProQuest phrase search, and 290 have a GPO, OFR or Federal Register lead. Neither field
proves a copy exists.

## What to record for each image (distinctions to keep)

The image may show a **signed original**, an **official printed copy** (slip, pamphlet, Federal Register or GPO
print), a **typescript or file copy**, a **transcription**, or only an **index or register entry**. Record which one
you see, not which one you expect. Record the number exactly as shown (letters, hyphens, fractions), the date, the
first words, and whether a signature is visible. If the expected position holds a different order or nothing,
record `different_order_at_position` or `not_at_expected_position`; that is a finding, too. Do not attach an image
to a group-3 row without noting the identity evidence.

## Ingest (what exists, and what to use)

- **There is no existing ingest command for NYU or HeinOnline files.**
- The only PDF ingest job is `jobs/pinakes-proquest-ingest/`. It reads only ProQuest accession file names
  (`[PT1-]<year>-EO-<n>.pdf`) from `ProQuest Pre-1937 Orders/`. Standing instructions forbid touching that folder,
  `research/pre-1937-sources/ProQuest*` and that job. Naming a Hein file like a ProQuest accession would misattribute it.
- **Do not** add files to `research/stage21/original_sources/` either. The tracker counts any
  `PDF_BYTES_CAPTURED…` custody row there as a satisfied original, which would promote a microfilm image to a
  counted original.
- Use the staging route on this branch, or a branch made from it:

```bash
python3 -I research/dagron/record_acquisition.py DOWNLOADED.pdf --id EO:708 --collection hein --hein-volume 2 --hein-image 14 --url "<viewer URL>" --witness-kind official_printed_copy --observed-number 708 --observed-date 1907-11-02 --signature-visible no --retrieved-by "<agent and model>"
```

```bash
python3 -I research/dagron/record_acquisition.py --check
```

Each call:
- copies the file to `research/dagron/acquired/<collection>/<id>__<sha12>.<ext>`;
- appends a record to `research/dagron/acquired/PROVENANCE.jsonl` with: collection and catalog record, URL, volume,
  image, reel and frame, SHA-256, bytes, type, UTC time, who retrieved it, observed witness kind, number, date and
  title, and whether a signature is visible;
- grades the record `nyu_collection_image_pending_codebook`, with `acceptable_as_original: false` and
  `needs_page_check: true`;
- refuses an id not in the manifest, a duplicate SHA-256, and a non-image file (an access-denied page saved as
  `.pdf`).

Nothing in production reads `research/dagron/`. The jobs read `jobs/*/output/SOURCES.jsonl`, `jobs/*/data/**` and
`jobs/*/output/FRAGMENTS*.jsonl`. Wiring the staged images in is a separate step for the owner to approve: a job
modeled on Pinakes, with page checks before any image counts. If the browser agent has no shell, it can deliver the
files plus one line per file with the fields above, and a repository session runs the command.

## Source-use restrictions already recorded

- **Microfilm:** "no paid reproduction … and no hand-scanning of microfilm … Do not plan around the reel set"
  (owner, `HANDOFF/notes-claude.md`, 2026-10-19). This manifest routes by reel at the owner's request. Requesting,
  scanning or paying for Film 709 reels still needs the owner's explicit go-ahead.
- **HeinOnline:** do not "scrape or bulk-download HeinOnline through an automated job" (Astra's standing *Do not*;
  `HANDOFF/astra-history-through-20261029.md`). Retrieve item by item, at a human pace, within NYU's licence terms
  for HeinOnline, and stop if the platform warns about systematic downloading.
- **NYU-authenticated databases:** do not run a bulk harvest through the owner's NYU session without NYU's written
  approval (`HANDOFF/notes-claude.md`, 2026-10-19). The owner decided not to send the NYU bulk-access request
  (`research/readiness/owner_rulings/2026-10-21-proquest-request.md`).
- **Grading:** scans added to the repository are graded under the 2026-10-21 transcription-as-text ruling until
  compared with an original. A replica or microfilm scan never counts as the original without a page check and a
  codebook grade. The human-certified count stays 0.
