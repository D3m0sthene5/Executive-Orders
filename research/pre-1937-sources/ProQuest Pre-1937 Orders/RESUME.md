# Resume this ProQuest queue

**13 actual PDF files covering 11 unique orders are committed and byte-verified** in `research/pre-1937-sources/ProQuest Pre-1937 Orders/`, repository `D3m0sthene5/Executive-Orders`, branch `proquest-download-handoff-20261019` / PR #38. The upload is preserved in [commit `22546670`](https://github.com/D3m0sthene5/Executive-Orders/commit/22546670bf669d51c38e48a399d394a277ff08dd).

The owner's latest **“ok go”** authorizes continuation through the original source links and the browser's normal flow. EO 99's institutional sign-in renewed automatically through Institution -> New York University (NYU) Library. Its six-page PDF rendered in Chrome's native embedded viewer and Download was clicked. No file path was returned. The actual path of PT1-1897-EO-99.pdf is needed for the next concrete GitHub file-chooser upload. Local Downloads is an optional intermediate; do not request folder confirmation as a prerequisite.

Of 2,735 supplied links, **2,724 orders lack a repository PDF**. This includes unavailable EO 28A, leaving **2,723 pending orders**. The browser-action queue contains **2,721** entries, beginning EO 100. The additional pending orders are EO 29 and EO 99, whose Save/Download requests remain unverified and whose PDFs are absent from the upload. Keep the separate October 18 lifecycle-research task paused.

## 1. Load the preserved state

Read `README.md`, `_resume/checkpoint.json`, and the current `_resume/progress.jsonl`. Verify the original HTML's SHA-256 against the checkpoint. The complete queue comes from that HTML's `const ROWS=` JSON; do not reconstruct URLs from order numbers or search another site.

Use `scripts/proquest_progress.py status` and `next --limit 10` to select exact original rows. The current untouched browser-action queue has 2,721 rows beginning EO 100. Reconcile and transfer EO 29 and EO 99 separately. Actual repository completion is controlled by verified_repository evidence, not by the action queue. Current audit output controls if later work has advanced the queue.

Read `HANDOFF/README.md` and the newest agent notes before repository writes. Prepend progress to this session model's designated notes file; preserve the previous history and other agents' work. Continue on the handoff branch while its pull request is open, or on the merged state if it has since landed. Check the current branch head before committing updates.

## 2. Preserve verified PDFs and transfer EO 29 and EO 99

The repository holds orders **4, 7, 10, 12, 13, 14, 15, 17, 23, 26 and 28**. Three identical EO 4 copies account for the 13 paths covering 11 orders. Retrieved bytes, file sizes, Git blob hashes, SHA-256, PDF signatures and strict PDF parsing all passed. Preserve the actual files and their duplicate copies; count unique orders separately.

Ten historical viewer Save/Download events are retained. Eight are now supported by verified repository files. EO 29 remains absent from the upload: its matching two-page viewer rendered and Save completed at 2026-10-19 19:58:49 ET, but no saved-file bytes were confirmed. EO 99 also rendered, with six pages, and its native Download control was clicked at 2026-10-20T02:01:23.668Z. Check accessible copies before repeating either download, then transfer the actual PDFs to GitHub. The current concrete need is the actual EO 99 file path on the connected computer; GitHub remains the final destination.

Use the GitHub connector for repository text, metadata, branches, and commits. If transferring PDFs held on the user's computer, the connected local browser's documented file chooser is one route. Scratch files do not exist on that computer. Inspect current UI state and the GitHub destination before acting; do not reuse old tab IDs or assume an upload succeeded.

For each further upload, verify GitHub's actual PDF names, byte sizes and blob hashes; obtain SHA-256 and PDF-signature evidence when bytes are available. Update the manifest, checkpoint, README counts and audit from those observations. Use `verified_repository` events only for confirmed files. Continue the pending queue under the owner's existing authorization while preserving earlier action evidence.

## 3. Use the connected browser and GitHub destination

The requested final destination is the GitHub folder named above. Local storage can serve as an intermediate when needed by the available transfer method. Resolve an actual local path only for a concrete operation that uses local files; do not reuse another computer's username or tab IDs.

Use the Browser plugin's `control-browser` skill and its current documented API. Select the newly connected computer's browser. Continue the exact supplied record links and their visible PDF controls. A local Downloads-folder confirmation is not a prerequisite.

ProQuest sign-in and any library session remain local to the browser. Follow the normal sign-in controls reached from the supplied record using current Browser guidance. If that flow requires the owner to complete authentication, hand off that specific step and continue afterward. Do not copy authentication data or assume that a repository checkout restores sign-in.

## 4. Use the working download sequence

On the latest EO 99 record, Chrome's native embedded PDF viewer rendered the exact file, while the top PDF control did not produce a separate matching PDF.js tab. The native viewer's visible Download control was used instead. The older worker handles the separate PDF.js case; inspect the current UI and use the appropriate visible download control. Do not infer failure solely from a missing popup or event, and do not repeat downloads before checking available file evidence.

Start order attempts at least **12 seconds apart**. Process one record at a time and close only task-created viewer tabs when finished.

1. Navigate to the row's exact original `rec` URL.
2. Inspect the rendered record and the observed `embed[type="application/pdf"]` source. Confirm its entitlement matches the row's original year and order number.
3. Click the record's visible **PDF** button.
4. Find the newly opened matching PDF.js viewer using the documented tab list.
5. Wait for rendered page regions and a positive displayed page count.
6. Click the viewer's visible **Save** button once.
7. Immediately append a `saved_requested` event with the original source URL, observed viewer/PDF URL, page count, time, and precise evidence. Verify the actual file separately.

The observed EO 10 filename was `1873-EO-10.pdf`, without the guessed `PT1-` prefix. The record's actual PDF control was necessary. Do not rewrite the supplied PDF URL to guess a correction.

The original session's direct PDF navigations sometimes produced `ERR_BLOCKED_BY_CLIENT`. Download listeners and `downloadMedia` timed out even when the viewer's Save command really created files, as the later screenshot showed. Avoid repeating those exploratory routes. A missing download event alone does not justify a second Save click or a success/failure claim.

`scripts/proquest_browser_worker.js` preserves this procedure as a paused-by-default factory. Read the current Browser skill and API documentation before loading it. Supply the current browser, a current task record tab, and the original rows. It defines one-order actions; the assistant selects the next row, records every returned event, and controls continuation. The Python helper performs no browser or network operations.

## 5. Handle outcomes and checkpoint progress

EO 28A's exact supplied record returned **“Access is denied. Your Library's ProQuest Subscription needs to be updated.”** Its latest audit event is terminal `link_unavailable`; the earlier timeout event is retained as history. Do not treat it as downloaded. Preserve it as an access exception while processing other supplied links.

The 30 no-link rows are listed in `_resume/exceptions.json`; there is no permitted link to follow for those entries. Do not generate one. Preserve lettered rows and all nine rows dated later than 1936 because the owner requested all supplied PDFs.

For a new error, record the original source URL and what the browser actually showed. Distinguish unavailable records from sign-in, identity mismatches, rendering failures, and uncertain Save results. Stop a running loop when the owner pauses; do not leave a background download process active. Unrelated unavailable rows need not stop the rest of the authorized queue.

Append audit events immediately. Periodically reconcile accessible files, upload collected PDFs to the shared folder, and commit the audit and manifest so another interruption can resume. Keep file-presence evidence distinct from archival/source acceptance and legal research outcomes.

## Offline validation

```sh
python -m unittest discover -s tests -v
```

The tests use temporary synthetic fixtures and make no network requests. They cover the paused queue, exact-link validation, filenames and duplicate handling, PDF signatures and hashes, read-only inventory, idempotent reconciliation, and repository-confirmed progress when a new local folder is empty. They were executed on Linux; the conditional Windows file-locking path still needs execution on Windows.
