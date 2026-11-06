# Dagron: order-level acquisition manifests for outside collections

Named for René Dagron, who put the dispatches of besieged Paris (1870–71) on microfilm for the pigeon post.

Given a collection described in `collections/<id>.json` (its numbered units, such as reels or volumes, and its date
range), Dagron lists every tracked order that the collection could supply missing evidence for. For each order it
gives:
- what the project already holds, by kind of witness and with retained paths;
- what is held only remotely;
- the likely unit;
- an acquisition priority;
- identity and coverage doubts;
- whether an image is already staged.

A browser agent can work from the list without redoing the inventory. It runs daily, and after the readiness
tracker, the Domesday register and Lewis, so the list never goes stale.

**What it is not.** It changes no status, readiness count, census row, codebook text or other job's output, and it
decides nothing about identity or custody. The tracker's committed output is the only authority on whether an
order's original-text step is satisfied. Collection ranges are routing leads, not proof that an order survives in
the collection.

## Collections

| Spec | Collection | Units |
|---|---|---|
| `nyu-film709` | NYU Bobst *Presidential executive orders* (Trans-Media microfilm, **Film 709**, 11 reels, EO 1–7403) and NYU's HeinOnline *Presidential Executive Orders* (11 volumes, 1845–1936) | reels; Hein volume assumed equal to the reel (unverified) |

To add a collection, copy `nyu-film709.json` and edit:
- `units` (first and last designations; a suffixed bound such as `6925A` is honoured);
- `date_coverage`, `catalog_records` and `staging_dir`;
- `restrictions`.

The next run builds its manifest.

## Outputs (`output/<collection>/`)

| File | What |
|---|---|
| `MANIFEST.jsonl.gz` | One row per order or candidate, with nested evidence records. The manifest. |
| `MANIFEST.csv.gz` | The same rows flattened for spreadsheets. |
| `SUMMARY.json` | Counts by group, priority and unit; missing-evidence categories; remote-only kinds; tracker measures. |
| `REPORT.md` | The counts as tables, plus the collection's recorded restrictions. |
| `SAMPLE.jsonl` | One row per distinct situation (13 at most). |

## Groups (each order appears once)

1. **`1_missing_accepted_original_witness`.** Numbered inside the units' range (letter and fraction variants
   included), and the tracker's `text_evidence_tier` is not `original_supported`. Either the original-text step is
   open, or it is satisfied only by a transcription that the tracker requires to be replaced.
2. **`2_missing_accepted_working_text_only`.** A counted original witness exists, but no retained text of it.
3. **`3_unnumbered_or_ambiguous_identity`.** Unnumbered orders within the dates; numeric-suffix second orders
   (`EO 8-1`); id aliases; and **untracked** census candidates (`instrument_id` empty, `proposed_id_not_in_census`
   set). Numbered coverage does not establish their inclusion.
4. **`4_edge_numbered_after_last_unit_within_dates`.** Numbered above the last unit but dated within the
   collection's range.

## Fields

- **Identity:** `instrument_id`, `eo_designation` (letters and fractions kept), `signature_date` + `date_source`,
  `title`, `president`, `census_class`.
- **Routing:** `likely_unit`, `likely_secondary_unit_unverified`, `coverage_uncertainty`.
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
- **Tracker state:** `tracker.*` (step, tier, original-text blockers, provisional status, claim; context only).
- **Held evidence, keeping the distinctions** (`held.*`). Each record carries its job, fragment file, grade,
  `page_or_item`, URL, source SHA-256, `source_bytes_retained_path`, `text_path`, `needs_page_check` and
  `acceptable_as_original`.
  - `signed_original_replica_scans`: ProQuest *Replica of Original*. A lead until a page check and a codebook grade.
  - `official_printed_copies`: Federal Register, GPO and OFR compilations, the Isthmian Canal and Indian-reservations
    compilations, Tischendorf, Mabillon held printings, Opus media, and printings named by census admissions.
    Counted only when not flagged for a page check.
  - `uncounted_printings_or_reprints`: HathiTrust GPO volumes, `numbered-early-orders` printed copies, and Civil
    Service Commission reprints. Leads, never the original.
  - `transcriptions`: the American Presidency Project, Wikisource and Richardson.
  - `index_entries`: census class, WPA/Lord citations, NARA descriptions. Index entries, not texts.
- **Remote and routes:**
  - `remote_evidence_not_retained_locally`: a source was read (URL and SHA-256 recorded) but its bytes are not
    committed; a ProQuest link was supplied with no PDF; a NARA digitized object exists.
  - `other_acquisition_routes_known`: Lewis's routes. Searches and leads, not located copies.
- **Staging and priority:** `staged_acquisitions`, `acquisition_priority` + `priority_reason`.

**Retained** means the bytes are committed somewhere in the tree. The checks cover:
- the files a fragment names;
- the SHA-256 records in the Wikisource, Cotton, Ptolemy and Cassiodorus source indexes and the salvage folders
  (measured on 2026-11-06 to resolve every retained source behind a pre-1937 fragment);
- the Git LFS source books in `releases/source_books/`, whose pointer gives the file's SHA-256;
- the Stage 21 custody table.

## Priority (1 = acquire first)

| | Rule |
|---:|---|
| 1 | Group 1 and either the working text is a transcription that must be replaced, or no image or printing of any kind is held |
| 2 | Group 1, no usable image of the signed original: the ProQuest replica's text is unusable, or only an official-printing lead or a reprint is held |
| 3 | Group 1 with a usable ProQuest replica pending a page check; or group 2 |
| 4 | Group 3: confirm identity and inclusion first |
| 5 | Group 4 |

`priority_reason` says which rule applied, and whether the order already has a provisional status or a claim.

## Staging downloaded images

There is no other ingest route for these files:
- `jobs/pinakes-proquest-ingest/` reads only ProQuest accession file names, and its folders are off limits.
- `research/stage21/original_sources/` must not be used: the tracker counts `PDF_BYTES_CAPTURED…` custody rows there
  as satisfied originals.

```bash
python3 -I jobs/dagron-collection-manifest/record_acquisition.py DOWNLOADED.pdf --spec nyu-film709 --id EO:708 --collection hein --hein-volume 2 --hein-image 14 --url "<viewer URL>" --witness-kind official_printed_copy --observed-number 708 --observed-date 1907-11-02 --signature-visible no --retrieved-by "<agent and model>"
```

```bash
python3 -I jobs/dagron-collection-manifest/record_acquisition.py --spec nyu-film709 --check
```

Each call:
- copies the file to `<staging_dir>/<collection>/<id>__<sha12>.<ext>`;
- appends one provenance record to `<staging_dir>/PROVENANCE.jsonl`: catalog record, URL, volume and image or reel
  and frame, SHA-256, bytes, type, UTC time, who retrieved it, and the **observed** witness kind
  (`signed_original`, `official_printed_copy`, `typescript_or_file_copy`, `transcription`,
  `index_or_register_entry`, `not_at_expected_position`, `different_order_at_position`, `unclear`), number, date and
  title, and whether a signature is visible;
- grades the record `collection_image_pending_codebook`, with `acceptable_as_original: false` and
  `needs_page_check: true`;
- refuses an id not in the manifest, a duplicate SHA-256, and a non-image file.

The next run marks the order staged (`staged_acquisitions`). Only Dagron reads the staging folder. Counting a staged
image as evidence is a separate step for the owner to approve: a job modeled on Pinakes, with page checks.

## Restrictions

Each spec carries the restrictions recorded for its collection, and `REPORT.md` repeats them. For `nyu-film709`:
- the owner's 2026-10-19 rule against microfilm reproduction and hand-scanning (Kean A-20261106-dagron-nyu);
- no automated bulk download from HeinOnline;
- no bulk harvest through the owner's NYU session;
- staged images stay unverified until a page check and a codebook grade.

## Run it

```bash
python3 -I jobs/dagron-collection-manifest/dagron.py . /tmp/dagron-out
```

The runner calls `job.py`, which runs `test_dagron.py` first. A local run takes a few seconds. It reads files from
the working tree and falls back to `git show HEAD:<path>`, so a sparse checkout works. The first manifest, its
reconciliation with earlier counts and its source notes are in `research/dagron/README.md` (2026-11-06).
