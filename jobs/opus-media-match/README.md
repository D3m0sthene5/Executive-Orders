# Opus media match: which Opus PDFs and page images belong to which order

The Opus Stage 11 release comes with a companion zip of 496 PDFs and page images
(`releases/opus_stage11_complete/OPUS_STAGE11_EVIDENCE_ORIGINALS.zip`). Until now
nobody could say which order each file belongs to, because the earlier check
(`research/stage20/output/MEDIA_BATCH_ASSOCIATION_AUDIT.csv`) only looked at folder
names. So the readiness tracker marks all 844 accepted Opus orders as blocked by
`OPUS_MEDIA_NOT_MATCHED_TO_ORDER`.

This job reads **what is printed on each file** and compares it with what each
Opus case says about itself. It costs no model tokens and makes no web requests.

## What it does, step by step

1. Opens the companion zip and reads each file straight out of it (nothing is
   unpacked to disk). It checks each file's SHA-256 fingerprint against the Stage 20
   list (`OPUS_ORIGINAL_MEDIA_MEMBER_MAP.csv`).
2. Gets the text of each file: the PDF's own text layer first (with the `pypdf`
   library). Scans and page images have no text layer; those need OCR (text
   recognition). OCR runs only when the `tesseract` program is installed. On GitHub
   the job installs it. On the PC it is not installed, so the job skips OCR and
   counts how many files still need it.
3. Reads the Opus case records inside the main release zip
   (`OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip`): each order's evidence
   quotes, the files and fingerprints its records mention, and the Federal Register
   and Statutes at Large pages it cites.
4. For every file and order, it looks for these separate clues ("signals"):
   - **eo_number_in_text**: the order's number is printed on the page, as
     "Executive Order No. 9054", "E.O. 9054", "Exec. Order 9054", "EXECUTIVE ORDER
     9054" as a heading, or "[No. 7504]" under "THE WHITE HOUSE" in the 1930s
     Federal Register.
   - **quote_in_text**: a quote from the order's own Opus evidence appears on the
     page, word for word ("verbatim") or nearly so ("near", which allows for scan
     errors). Stock wording is not counted (see below).
   - **citation_in_text**: the page's running head shows a Federal Register or
     Statutes at Large page the order's records cite (for example "FEDERAL
     REGISTER, Wednesday, May 29, 1946 5835", or "[55 Stat." over page 838).
   - **opus_record_link**: the order's own Opus records mention this exact file,
     its fingerprint, or the source record it was cut from. This comes from Opus's
     own record-keeping, not from the page.
   - **cites_same_document** (weak, never counts as tying the file to the order):
     the order's records cite the same *whole* upstream document, for example a
     whole Federal Register issue, but this file is only a page excerpt of it. Citing
     the issue says nothing about these particular pages. (If a cited FR or Statutes
     page is printed in the excerpt's running heads, the link counts as a normal
     `opus_record_link` again.)
   - **filename_match**: the file name (such as `fr_1946-05-29.p19-20.pdf`,
     `stat_55_838.pdf`, `..._eo11425_...`) agrees with a date, page or number the
     order's records cite. This also comes from Opus, not from the page.
5. Grades every file/order pair. A file can belong to several orders: one statute
   page can be a source for dozens of orders. The job never forces one order per file.

   > **Read "unique_supported" as "content-supported", not "one order per file".**
   > The grade is about one file/order *pair*. In the full run one statute page
   > (55 Stat. 838) is `unique_supported` for 47 orders, and most `unique_supported`
   > pairs are `cited_source` (a statute or later document the order cites), not the
   > order's own printing.

   - **unique_supported**: at least two kinds of signal, at least one of them read
     from the page itself, and at least one that points at this particular order
     (its number, its quote, or its own records). A long word-for-word quote
     (100+ letters after stock phrases are removed) found in at most 2 files is
     also enough by itself. It does not count if the quote is the order's own
     wording found in a document that never names the order, such as the statute
     the order copies.
   - **ambiguous**: some signal, but not enough. Examples: only the file name and
     a citation, both of which only say "this is the statute the order cites"; or
     only Opus's own records with no readable page to confirm them.
   - **unmatched**: no signal for any order (the file row has no order).
6. Each pair is also given a **role**. `order_text_candidate` means the page
   prints the order itself: its number as a heading or signature-block number,
   plus a quote from its own text or a matching file name. `cited_source` covers
   everything else (statutes, later orders, notices).

Order numbers with a suffix letter are kept apart: "EXECUTIVE ORDER 9616A" is a
heading of EO:9616A only, never of EO:9616 (the same for 6711/6711A, 9934/9934A).

Stock wording is guarded against in three ways. A quote found word for word in
more than 6 different files is dropped as boilerplate. Common phrases such as "by
virtue of the authority vested in me" do not count toward a quote's length. A quote
on a page that prints *other* orders' headings, and never names this order, is not
counted (for example "shall remain in force until revoked by the President or by
act of Congress", which appears in many land orders).

## Outputs (in `output/`)

| File | What it is |
|---|---|
| `MATCHES.csv` | One row per file/order pair: `member_path, sha256, instrument_id, in_accepted_844, grade, role, signal_families, signals, page_refs, content_verified, directory_hint, text_method, notes`. Files with no match get one row with `grade=unmatched` and an empty `instrument_id`. `page_refs` are pages of the archived file (1 = first page). `signals` lists every clue with its page, for example `quote_in_text:verbatim:A:E01:len150@p10`. |
| `OPUS_CASE_MEDIA_STATUS.csv` | **One row per Stage 11 order** (all 1,155; the 844 accepted ones first). `media_status` (`unique_supported`, `ambiguous_only` or `no_member_signal`); `all_cited_media_resolved` (`yes` only when the order has a `unique_supported` file, no ambiguous candidates left, and no cited PDF/image missing from the companion); counts of matching files, split into `order_text_candidate_members` and `unique_supported_cited_source_members`; what its records cite: `media_files_cited_in_case_records` (local PDF/image files), `media_urls_cited_in_case_records` (PDF/image URLs, including PDFs Opus kept only as a `.txt` conversion), and what is missing: `cited_media_not_packaged` + `cited_media_urls_not_packaged` (Opus downloaded them, the release left them out as too large), `cited_media_urls_not_in_companion` (no bytes in the companion for this order), `cited_media_kept_only_as_text`, `cited_media_only_excerpt_kept_for_other_order`; `media_gap` (`none_cited`, `originals_not_in_companion`, `cited_files_not_packaged`, or empty); examples; a plain `note`. |
| `MEMBERS.csv` | One row per file: kind (pdf, png, jpg, an HTML page saved under a .pdf name, empty), SHA-256 check, how its text was obtained, pages without text, whether it needs OCR, the source URL Opus fetched it from (from the Opus `.meta.json`), and the order numbers and FR dates found on it. |
| `FRAGMENTS.jsonl` | Shared claim-fragment format, kind `original_representation`, **only** for `unique_supported` pairs whose role is `order_text_candidate`. The source reference is `{"archival_id": "opus_stage11_evidence_originals:<path in zip>", "local_file_sha256": <sha256 of the file's bytes>, "sha256": same, "page_or_item": <pages>, "upstream_url": ..., "upstream_sha256": ...}`. This is the offline form the Stage 19 claim gate accepts. `status` is always `candidate_unverified`. |
| `REFETCH_LIST.jsonl` | Originals the Opus records cite that the companion does not hold, one line per URL: `url`, `instrument_ids` (and `accepted_844_ids`), `reasons` (`left_out_of_release_too_large`, `original_not_kept_by_opus`), `expected_sha256` / `expected_bytes` from the Opus `.meta.json` of the download (the sha256 of the bytes Opus received, not of a text extract; null when Opus recorded none), and `opus_path`. The source-ladder job re-fetches these automatically and checks each copy against `expected_sha256`. |
| `SOURCES.jsonl` | Shared source-record format, one per file: SHA-256 and size of the archived bytes (also as `local_file_sha256`), `archival_id`, content type, route, extracted text path, the release zip's own SHA-256, and `upstream_url`, `upstream_sha256` and `upstream_retrieved_utc` (when Opus fetched it) from the Opus `.meta.json`. `url` is filled **only** when the file's bytes are exactly what that URL served (`sha256_is_of_url_bytes: true`). For the 222 page excerpts (`false`) `url` is null, because re-fetching the URL gives a different, larger file. The 21 HTML access-denied pages saved under `.pdf` names and the 2 empty files have `usable_as_document: false`, a `defect` (`access_denied_or_error_html` / `empty_file`), `url: null`, no orders, and notes starting "NOT the document". `retrieved_utc` is when this job read the file from the release zip. |
| `text/<sha256>.txt` | The extracted text of each file, pages separated by a form-feed character. About 9 MB in total. |
| `SUMMARY.json` | All counts: files read, SHA-256 checks, OCR needs, pairs by grade, and for the 844 accepted orders how many have a `unique_supported` file and why the rest do not. |

## What the readiness tracker should read instead (the tracker is not changed here)

Today the tracker counts an Opus order as matched when a row of
`MEDIA_BATCH_ASSOCIATION_AUDIT.csv` has `association_grade` other than
`no_case_specific_evidence` and lists the order in `example_case_ids`. That never
happens (all 496 rows are `no_case_specific_evidence`). It should read instead:

    jobs/opus-media-match/output/OPUS_CASE_MEDIA_STATUS.csv
    key: instrument_id
    strict:  opus_media step done  <=>  all_cited_media_resolved == "yes"
    looser:  opus_media step done  <=>  media_status == "unique_supported"
             (then also show ambiguous_members and media_gap next to "done")

The looser rule marks an order done when *any* one file is content-supported, even
if that file is only a statute the order cites and other cited media are still
ambiguous or missing. Which rule to use is the owner's choice; this job does not
decide it. Suggested blockers for the rest, using `media_gap`:

- `media_status == "ambiguous_only"`: blocker `OPUS_MEDIA_MATCH_AMBIGUOUS`. A
  person checks the candidates in `MATCHES.csv`; many of them are page images that
  OCR on GitHub may settle.
- `media_gap == "none_cited"` (and `media_status == "no_member_signal"`): the
  order's Opus records cite no PDF or image at all, **neither as a file nor as a
  URL** (only HTML, XML, JSON or text sources). Only this case is a candidate for
  "not applicable" for this matching step, or for `research/readiness/EXHAUSTED.jsonl`;
  the owner decides. It does not mean that no official printed copy exists.
- `media_gap == "originals_not_in_companion"`: the records cite PDF/image URLs
  whose bytes are not in the companion for this order (Opus kept only a `.txt`
  extract, or nothing, or only an excerpt kept for another order). Blocker such as
  `OPUS_MEDIA_ORIGINAL_NOT_KEPT`: re-fetch from the URL (`example_media_urls_missing`).
  **Not** "not applicable".
- `media_gap == "cited_files_not_packaged"`: Opus downloaded the cited PDFs, but the
  release left them out as too large (see `evidence/UNPACKAGED_LARGE_ORIGINALS.jsonl`
  in the release zip). Re-fetch from the URL in their `.meta.json`. **Not** "not
  applicable".

Full-run numbers for the 844 accepted orders without OCR: 357 `unique_supported`
(79 of them `all_cited_media_resolved`), 73 `ambiguous_only`, 414
`no_member_signal`. Of those 414: 205 `none_cited`, 10 `originals_not_in_companion`,
199 `cited_files_not_packaged`.

To take the page-level link itself (for example as the original-text source), use
the `unique_supported` rows of `MATCHES.csv` with `role == order_text_candidate`,
or `FRAGMENTS.jsonl`.

### For the merge job (job 8)

- Take `FRAGMENTS.jsonl` as is (kind `original_representation`, produced_by
  `opus-media-match`).
- For a claim-safe source reference to one of these files, use **`archival_id` +
  `local_file_sha256`** (the offline form the Stage 19 claim gate accepts), as the
  fragments already do. Do **not** build `{url, sha256}` from `upstream_url` and
  `sha256`: for excerpts the URL serves different bytes. `url` + `sha256` together
  are only valid where `url` is not null.
- Skip records with `usable_as_document == false`; they record failed captures
  whose URL still has to be fetched.

## How to run

**On GitHub:** commit a change to this folder, or start **Run jobs** by hand with
the job name `opus-media-match`. `job.sh` installs `tesseract-ocr` and
`poppler-utils` for OCR and then runs `job.py`. `job.py` fetches the two release
zips from Git LFS (about 566 MB) and runs the tests, then the match. The run should
take roughly 15 to 60 minutes, mostly OCR of about 180 pages. The results come back
in `output/` (about 12 MB).

**On the PC** (from the repo folder):

    python -m pip install --user pypdf==6.20.1
    $env:REPO_ROOT = "."
    $env:OUTPUT_DIR = "C:\Users\danie\AppData\Local\Temp\eo-jobs\opus-media-match\out"
    python jobs\opus-media-match\job.py

(In Git Bash: `REPO_ROOT=. OUTPUT_DIR=... python jobs/opus-media-match/job.py`.)
A full run takes about one minute without OCR. If `tesseract` and `pdftoppm` are
on PATH, OCR runs on the PC too.

Optional settings:

- `JOB_LIMIT=40` reads only 40 files, spread evenly through the zip, for a quick test.
  It must be 1 or more; leave it unset to read every file (0 or a negative number is
  refused).
- `JOB_CACHE_DIR=<folder>` sets where extracted and OCR text is cached. The default
  is `<OUTPUT_DIR>/../opus-media-match-cache`. When `OUTPUT_DIR` is this folder's
  `output/`, that is `jobs/opus-media-match/opus-media-match-cache/`, which the
  folder's `.gitignore` keeps out of git. A rerun reuses the cache and only OCRs pages
  it has not done before.
- `JOB_OCR=0` turns OCR off. `JOB_OCR_MAX_PAGES=2000` caps OCR pages per run. If
  OCR fails on a page (tool error or time-out), only that page is skipped; the count
  is in `SUMMARY.json` (`text.ocr_failures_this_run`, with examples) and the page is
  tried again on the next run.

All text outputs are UTF-8 with LF line ends on every computer, so a PC run and a
GitHub run of the same input give the same files.

The unit tests (`python -m unittest test_media_match` in this folder) use small
made-up files and no network. `job.py` runs them first and stops if any fails.

Inputs: `releases/opus_stage11_complete/` (both zips) and `research/stage20/output/`
(`OPUS_ORIGINAL_MEDIA_MEMBER_MAP.csv`, `OPUS_ORIGINAL_MEDIA_INTEGRITY.json`,
`OPUS_FULL_844.jsonl`, `OPUS_NOTE_LEADS.jsonl`), listed in `needs.txt`.

## What this does NOT establish

- **Not a legal finding.** A `unique_supported` match says only that the file's
  content and at least one more independent clue tie it to the order. It does not
  show that the file is authentic or the official printing. It does not show that
  the order text is complete, or anything about when or how the order ended or
  whether it still has effect. It changes no provisional status, ledger or count.
- An `order_text_candidate` is a candidate for the original text. A person must
  read the page and confirm it is this order, complete, and officially printed.
- Matching is limited to the 1,155 orders in the Stage 11 records. A file may
  also be relevant to orders outside that set; this job does not look for them.
- Old scans have imperfect text layers. A quote can be missed, which leaves a pair
  `ambiguous` or `unmatched`, not wrong. Without OCR, page images can only be
  matched through Opus's own records and file names, so they stay `ambiguous`.
- `opus_record_link` and `filename_match` repeat Opus's own record-keeping. They
  never make a pair `unique_supported` without a signal read from the page.
- OCR has not yet been run with the real `tesseract`/`pdftoppm` (they are not on the
  PC; only a stand-in is tested). Before relying on OCR numbers, do one GitHub run
  with a small `JOB_LIMIT` and check that `SUMMARY.json` shows `text.pages_ocr_done`
  above 0 and few `ocr_failures_this_run`.
- Whether a cited URL "is in the companion" is decided from the Opus `.meta.json`
  records and file names: a companion file counts for an order when it is the whole
  document the URL served, or a copy or excerpt kept in that order's own folders.
  Whether an excerpt holds the *right pages* is only known from the page signals.
