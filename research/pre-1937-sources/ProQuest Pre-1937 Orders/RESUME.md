# Resume this ProQuest queue

The owner paused downloading to move the folder and working state to the Executive-Orders repository. **Do not start new ProQuest navigation until the owner says “go.”** Opening this file or the repository is not itself a resume command.

In this conversation, “go” means continue the ProQuest PDF download task. It does not reactivate the separately paused October 18 lifecycle-research assignment in older Astra notes.

## 1. Load the preserved state

Read `README.md`, `_resume/checkpoint.json`, and the current `_resume/progress.jsonl`. Verify the original HTML's SHA-256 against the checkpoint. The complete queue comes from that HTML's `const ROWS=` JSON; do not reconstruct URLs from order numbers or search another site.

Use `scripts/proquest_progress.py status` and `next --limit 10` to select exact original rows. At this handoff, EO 29 is first and 2,723 untouched linked rows remain. Current audit output controls if later work has advanced the queue.

Read `HANDOFF/README.md` and the newest agent notes before repository writes. Prepend progress to this session model's designated notes file; preserve the previous history and other agents' work. Continue on the handoff branch while its pull request is open, or on the merged state if it has since landed. Check the current branch head before committing updates.

## 2. Finish transferring the PDFs already held

At this checkpoint, **zero PDFs have been confirmed in the new repository folder**. The expected 13 filenames covering 11 unique orders are in `_resume/expected_files.json`. Five filenames were visible in the original screenshot: three EO 4 copies, EO 7, and EO 12. Eight further filenames derive from matching rendered viewers whose Save commands completed.

The authorized GitHub upload stopped at `fileChooser.setFiles` because Chrome requires **Allow access to file URLs** for the ChatGPT extension. This is an observed browser setting requirement. Enable it on the computer holding the files before retrying the documented file chooser. The original upload page was opened at the handoff branch's `research/pre-1937-sources/ProQuest Pre-1937 Orders` folder.

Use the GitHub connector for repository text, metadata, branches, and commits. Use the connected local browser's documented file chooser for actual PDFs that are on the user's computer. Scratch files do not exist on that computer. Inspect current UI state and the actual destination before acting; do not reuse old tab IDs or assume an upload succeeded.

After uploading, verify GitHub's actual PDF names, byte sizes, and blob hashes; obtain SHA-256 and PDF-signature evidence when file bytes are available. Update the manifest, checkpoint, README counts, and audit from those observations. Use `verified_repository` events only for confirmed uploaded files. Preserve duplicate copies in the requested folder; count unique orders separately.

If the original folder is inaccessible from the second computer, retain this transfer as unfinished. Reconcile any copied or restored files first, and preserve the uncertain eight Save results rather than calling them completed uploads. The untouched queue can continue after “go”; pending transfer does not alter the original source links or erase prior evidence.

## 3. Establish the new computer's destination and browser

The requested destination is the actual folder named **ProQuest Pre-1937 Orders** inside that computer's Downloads folder. Resolve its real path; do not reuse the original machine's username or tab IDs. Restore repository-confirmed PDFs there if they are missing locally, then inventory and reconcile any accessible files.

Use the Browser plugin's `control-browser` skill and its current documented API. Select the newly connected computer's browser. Confirm Chrome's download destination is the requested folder and that Save will not open a per-file prompt. The original owner had already set those preferences on the first computer; they must be checked again on the second.

ProQuest sign-in and any library session remain local to the browser. If an observed sign-in wall blocks the requested record, ask the owner to sign in there and continue when ready. Do not copy authentication data or assume that a repository checkout restores sign-in.

## 4. Use the working download sequence

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
