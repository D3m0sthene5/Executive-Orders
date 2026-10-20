# ProQuest Pre-1937 Orders

**Resumption has reached the first Save on the other computer; the download destination still needs confirmation.** The owner said “go” at 2026-10-19 19:53 ET. The original EO 29 record initially displayed a login form, then opened successfully. Its matching two-page PDF rendered, and Save completed at 19:58:49 ET. The browser did not return a downloaded-file path, so that computer's folder and actual saved file remain unverified.

Repository: `D3m0sthene5/Executive-Orders`  
Handoff branch: `proquest-download-handoff-20261019`  
Next untouched order: **EO 99**

The owner should confirm Chrome saves into **Downloads / ProQuest Pre-1937 Orders** on this computer. A subsequent **ready** continues the already-authorized queue. ProQuest access is working; no new sign-in request is currently needed. See [`_resume/session_events.jsonl`](_resume/session_events.jsonl) for the resume observation and [`_resume/EO29_viewer.png`](_resume/EO29_viewer.png) for the rendered viewer. The screenshot establishes rendering, not file presence.

## Current checkpoint

| Item | Recorded state |
|---|---|
| Original HTML rows | 2,765 |
| Rows with supplied PDF links | 2,735 |
| Original-computer screenshot evidence | EO 4, 7, 12 — 3 unique orders |
| Viewer Save completed; file presence still unverified | EO 10, 13, 14, 15, 17, 23, 26, 28, 29 — 9 orders |
| Supplied record unavailable | EO 28A — library subscription response |
| Rows with no supplied links | 30 |
| Remaining untouched linked queue | 2,722 |
| PDFs confirmed stored in this repository folder | **0 — upload pending** |

The original computer is expected to hold **13 PDF files for 11 unique orders**, including two additional copies of EO 4. The new computer now has one additional completed Save request for EO29. Across both computers there are **14 expected filenames covering 12 orders**, with actual file evidence still required for the nine Save requests. These filenames and their different evidence levels are listed in [`_resume/expected_files.json`](_resume/expected_files.json). This is an expected-file manifest, not a completed upload inventory. The original-computer folder has not been exhaustively inventoried.

The authorized upload was attempted through GitHub's file chooser. Chrome reported that the ChatGPT extension's **Allow access to file URLs** setting is disabled, so no PDF transfer was completed. After that setting is enabled, finish the upload and verify the repository filenames, sizes, and blob hashes before changing the upload count. Preserve the actual PDF files and existing copies; do not replace them with placeholder files.

## Continue on another computer

Open the same ProQuest download conversation on the other computer and say **“go.”** The resuming assistant should follow [`RESUME.md`](RESUME.md), read the current audit, and continue the queue after checking the connected computer's browser and download destination.

The destination remains **Downloads / ProQuest Pre-1937 Orders** on the computer doing the downloading. Browser connection, ProQuest sign-in, and Chrome's download-folder setting belong to that computer. They are not carried in this repository. PDFs already confirmed in the repository can be restored to the new destination without downloading them again from ProQuest.

If the original PDF transfer is still pending, preserve that as outstanding work. Reconcile any accessible copies before retrying the nine uncertain Save results. A future “go” applies to this ProQuest queue; it does not restart the separately paused lifecycle-research assignment documented in older handoff notes.

## Contents

| Path | Purpose |
|---|---|
| [`RESUME.md`](RESUME.md) | Operational handoff for the resuming assistant |
| [`_resume/proquest_download_links.html`](_resume/proquest_download_links.html) | Byte-for-byte original supplied tool and all source links |
| [`_resume/checkpoint.json`](_resume/checkpoint.json) | Portable pause state, source fingerprint, and prior screenshot evidence |
| [`_resume/progress.jsonl`](_resume/progress.jsonl) | Preserved per-order action audit; append new evidence here |
| [`_resume/status.json`](_resume/status.json) | Computed progress at this checkpoint |
| [`_resume/expected_files.json`](_resume/expected_files.json) | Expected held PDF filenames, with upload explicitly pending |
| [`_resume/exceptions.json`](_resume/exceptions.json) | Missing links and the observed EO 28A response |
| [`scripts/proquest_progress.py`](scripts/proquest_progress.py) | Offline queue, audit, inventory, and reconciliation helper |
| [`scripts/proquest_browser_worker.js`](scripts/proquest_browser_worker.js) | Paused-by-default single-order browser worker; no automatic loop |
| [`tests/test_proquest_progress.py`](tests/test_proquest_progress.py) | Offline tests with temporary synthetic fixtures |

Source SHA-256: `4644b0e380356060d4098affad5bd3170ddae09ed06fef256e4fe975acf73f17`  
Source bytes: **1,005,711**

## Queue and file verification

The source tool marks rows done when a PDF or record link is clicked. Its browser-local ticks are not reliable proof that a PDF was saved, and they do not move to another computer. Use the audit and actual file evidence instead.

| Status | Evidence |
|---|---|
| `saved_requested` | The rendered viewer's Save command completed; file presence is unverified |
| `verified_screenshot` | An original-computer screenshot showed the named file |
| `verified_local_pdf` | Explicit reconciliation found a matching filename, byte size, SHA-256, and `%PDF-` signature |
| `verified_repository` | The actual uploaded repository file was confirmed at a recorded path and URL |
| `link_unavailable` | The supplied link was unavailable, or no link was supplied |
| `error_unresolved` | An attempted step needs further attention; nonterminal errors remain retryable |

The action queue excludes handled Save requests to avoid blindly saving the same order again. That exclusion does not make those files verified. `verified_repository` orders also remain excluded when the new Downloads folder is empty; restore their held PDFs from the repository. File checks do not establish archival acceptance or the historical correctness of document contents.

## Offline helper

From this folder, run:

```sh
python scripts/proquest_progress.py status
python scripts/proquest_progress.py next --limit 10
python scripts/proquest_progress.py inventory --folder "PATH_TO_DOWNLOADS/ProQuest Pre-1937 Orders"
```

Use `py` instead of `python` on Windows if needed. The helper uses only the Python standard library. Its defaults resolve from its own folder, so the working directory can differ.

`inventory` reads only the explicit folder and changes no progress. It recognizes the observed optional `PT1-` prefix and Chrome's duplicate filename suffixes. It calculates SHA-256 and size, checks `%PDF-`, and matches the filename's year and order number against the original rows. These checks do not validate every PDF page.

After reviewing actual local files, append their evidence with:

```sh
python scripts/proquest_progress.py reconcile --folder "PATH_TO_DOWNLOADS/ProQuest Pre-1937 Orders"
```

Repeated reconciliation of identical files does not duplicate audit entries. Do not run this against the assistant's scratch filesystem and interpret an empty result as proof about the user's computer.

The helper performs no network access and never starts a download. The browser worker also starts paused and has no automatic loop. On resumption, use current Browser skill documentation and record each result immediately.

## Source scope

Use the exact links supplied in the original HTML and the visible PDF controls reached through those records. Preserve every supplied row, including lettered orders and the nine rows dated later than 1936. The folder name does not narrow the owner's request for all supplied PDFs. Do not generate alternate URLs for guessed filenames or for the 30 rows with no links.

This folder records acquisition and transfer. It does not change legal-status findings, census figures, human-review counts, or `acceptable_as_original:false` pending the repository's separate source-comparison work.
