# ProQuest Pre-1937 Orders

**13 actual PDF files covering 11 unique orders are committed and byte-verified in GitHub.** The final destination is `research/pre-1937-sources/ProQuest Pre-1937 Orders/` in `D3m0sthene5/Executive-Orders`. The uploaded files are preserved in [commit `22546670`](https://github.com/D3m0sthene5/Executive-Orders/commit/22546670bf669d51c38e48a399d394a277ff08dd).

Repository: `D3m0sthene5/Executive-Orders`  
Handoff branch: `proquest-download-handoff-20261019`  
Pull request: [#38](https://github.com/D3m0sthene5/Executive-Orders/pull/38)  
Current PDF awaiting transfer: **EO 99**  
Next untouched supplied record: **EO 100**

The owner's latest **“ok go”** authorizes continued acquisition through the original supplied links and the browser's normal record, sign-in and PDF controls. EO 99's institutional sign-in renewed automatically through the normal NYU Library link. Its native Chrome PDF viewer displayed six pages and the Download control was clicked. The browser returned no file path; the actual EO 99 file path is needed for the next GitHub file-chooser upload. A local Downloads folder is an optional intermediate, with no folder-confirmation prerequisite.

## Current checkpoint

| Item | Recorded state |
|---|---|
| Original HTML rows | 2,765 |
| Rows with supplied PDF links | 2,735 |
| Actual PDFs verified in the repository | **13 files / 11 unique orders** |
| Linked orders without a repository PDF | **2,724**, including unavailable EO 28A |
| Pending repository acquisition, excluding EO 28A | **2,723** |
| Browser-action queue | **2,721**, beginning EO 100 |
| Save/Download requests still unverified and absent from GitHub | EO 29 and EO 99 |
| Supplied record unavailable | EO 28A — library subscription response |
| Rows with no supplied links | 30 |

The stored orders are **4, 7, 10, 12, 13, 14, 15, 17, 23, 26 and 28**. EO 4 has three byte-identical copies, which account for the two extra files. All 13 paths match original source rows; repository bytes, sizes, Git blob hashes, SHA-256, PDF signatures and strict PDF parsing passed verification. This verifies file integrity and structure, without establishing archival acceptance or reviewing each page's contents.

Ten historical Save/Download actions remain in the audit. Eight now correspond to verified repository files; **EO 29 and EO 99 remain uncertain**, with no PDF in the uploaded commit. Their rendered viewers establish rendering only. The three earlier screenshot-confirmed orders (4, 7 and 12) are also now stored in GitHub. Preserve this action history when adding stronger file evidence.

The browser-action queue omits EO 29 and EO 99 because Save/Download was already requested. Repository acquisition still includes them: **2,721 queued actions + EO 29 + EO 99 = 2,723 pending orders**. Keep the separately unavailable EO 28A in the exception record.

## Continue on another computer

Open the same ProQuest download conversation on the other computer and say **“go.”** The owner has already done so for the current resumption. The resuming assistant should follow [`RESUME.md`](RESUME.md), read the current audit, and continue the supplied-link queue and actual PDF transfer to GitHub.

The final destination is this repository folder on `proquest-download-handoff-20261019` / PR #38. Local storage, including Downloads, may be used as an intermediate if the available transfer method needs it. Browser connection and ProQuest sign-in belong to the connected computer and are not carried in the repository.

Preserve the 13 uploaded files and avoid downloading those 11 orders again. Reconcile any accessible EO 29 or EO 99 copy before repeating a download. Use the actual EO 99 PDF path supplied by the owner for a concrete GitHub file-chooser upload; no folder setup is required. A future “go” applies to this ProQuest queue; it does not restart the separately paused lifecycle-research assignment documented in older handoff notes.

## Contents

| Path | Purpose |
|---|---|
| [`RESUME.md`](RESUME.md) | Operational handoff for the resuming assistant |
| [`_resume/proquest_download_links.html`](_resume/proquest_download_links.html) | Byte-for-byte original supplied tool and all source links |
| [`_resume/checkpoint.json`](_resume/checkpoint.json) | Portable pause state, source fingerprint, and prior screenshot evidence |
| [`_resume/progress.jsonl`](_resume/progress.jsonl) | Preserved per-order action audit; append new evidence here |
| [`_resume/status.json`](_resume/status.json) | Computed progress at this checkpoint |
| [`_resume/repository_files.json`](_resume/repository_files.json) | Pinned repository paths, sizes, hashes and PDF page counts for all 13 verified files |
| [`_resume/expected_files.json`](_resume/expected_files.json) | File manifest with per-file transfer and verification evidence |
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
| `saved_requested` | The rendered viewer's Save/Download control was clicked; file presence is unverified |
| `verified_screenshot` | An original-computer screenshot showed the named file |
| `verified_local_pdf` | Explicit reconciliation found a matching filename, byte size, SHA-256, and `%PDF-` signature |
| `verified_repository` | The actual uploaded repository file was confirmed at a recorded path and URL |
| `link_unavailable` | The supplied link was unavailable, or no link was supplied |
| `error_unresolved` | An attempted step needs further attention; nonterminal errors remain retryable |

The action queue excludes handled Save requests to avoid blindly saving the same order again. That exclusion does not make those files verified or complete their GitHub transfer. `verified_repository` orders remain excluded regardless of what is present in an optional local intermediate folder. File checks do not establish archival acceptance or the historical correctness of document contents.

## Offline helper

From this folder, run:

```sh
python scripts/proquest_progress.py status
python scripts/proquest_progress.py next --limit 10
python scripts/proquest_progress.py inventory --folder "PATH_TO_LOCAL_PDF_FOLDER"
```

Use `py` instead of `python` on Windows if needed. The helper uses only the Python standard library. Its defaults resolve from its own folder, so the working directory can differ.

`inventory` reads only the explicit folder and changes no progress. It recognizes the observed optional `PT1-` prefix and Chrome's duplicate filename suffixes. It calculates SHA-256 and size, checks `%PDF-`, and matches the filename's year and order number against the original rows. These checks do not validate every PDF page.

If local files are used as an intermediate, append their evidence after reviewing them:

```sh
python scripts/proquest_progress.py reconcile --folder "PATH_TO_LOCAL_PDF_FOLDER"
```

Repeated reconciliation of identical files does not duplicate audit entries. Do not run this against the assistant's scratch filesystem and interpret an empty result as proof about the user's computer.

The helper performs no network access and never starts a download. The browser worker also starts paused and has no automatic loop. On resumption, use current Browser skill documentation and record each result immediately.

## Source scope

Use the exact links supplied in the original HTML and the visible PDF controls reached through those records. Preserve every supplied row, including lettered orders and the nine rows dated later than 1936. The folder name does not narrow the owner's request for all supplied PDFs. Do not generate alternate URLs for guessed filenames or for the 30 rows with no links.

This folder records acquisition and transfer. It does not change legal-status findings, census figures, human-review counts, or `acceptable_as_original:false` pending the repository's separate source-comparison work.
