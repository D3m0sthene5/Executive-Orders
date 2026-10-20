# Resume this ProQuest queue

## Latest resume observation

The owner said **go** at 2026-10-19 19:53 ET. The new computer's Chrome browser connected. The exact supplied EO 29 record initially displayed a sign-in form, then became accessible. Its matching two-page PDF rendered and Save completed at 19:58:49 ET. The browser's download event timed out; this does not prove the Save failed. Preserve the saved_requested audit event and inspect actual file evidence before repeating Save.

**The final destination for the actual PDFs is `research/pre-1937-sources/ProQuest Pre-1937 Orders/` in `D3m0sthene5/Executive-Orders`, on branch `proquest-download-handoff-20261019` / PR #38. Zero actual PDFs have been committed so far.** A local Downloads folder is an optional intermediate. Do not require the owner to confirm or configure it before continuing. The owner's “go” already authorizes continuation at **EO 99**, with **2,722** untouched linked rows, and transfer of the actual PDFs to GitHub. ProQuest access is already working.

There are no running background downloads. The earlier PDF upload remains pending. A future resume in this conversation concerns only this ProQuest task; keep the separate October 18 lifecycle-research task paused.

## Actual PDF transfer still pending

The owner clarified that the PDFs must go to GitHub. The latest attempt could display EO 29 but did not return its file bytes: the browser asset exporter does not support PDFs, and the documented embedded-file download timed out after 45 seconds. Do not request Downloads configuration again. Use a supported file transfer or the repository upload page to acquire the actual bytes. **2,734 supplied linked orders still need repository PDFs**, with EO 28A recorded separately as unavailable. The smaller 2,722 figure is only the untouched browser-action queue; the 12 orders with Save or screenshot evidence still need GitHub transfer.

## 1. Load the preserved state

Read `README.md`, `_resume/checkpoint.json`, and the current `_resume/progress.jsonl`. Verify the original HTML's SHA-256 against the checkpoint. The complete queue comes from that HTML's `const ROWS=` JSON; do not reconstruct URLs from order numbers or search another site.

Use `scripts/proquest_progress.py status` and `next --limit 10` to select exact original rows. After the new-computer EO 29 Save request, EO 99 is first and 2,722 untouched linked rows remain. Current audit output controls if later work has advanced the queue.

Read `HANDOFF/README.md` and the newest agent notes before repository writes. Prepend progress to this session model's designated notes file; preserve the previous history and other agents' work. Continue on the handoff branch while its pull request is open, or on the merged state if it has since landed. Check the current branch head before committing updates.

## 2. Finish transferring the PDFs already held

At this checkpoint, **zero PDFs have been confirmed in the repository destination**. The expected 14 filenames covering 12 unique orders are in `_resume/expected_files.json`. Five filenames were visible in the original screenshot: three EO 4 copies, EO 7, and EO 12. Nine further filenames derive from matching rendered viewers whose Save commands completed, including EO 29 on the new computer.

The authorized GitHub upload stopped at `fileChooser.setFiles` because Chrome requires **Allow access to file URLs** for the ChatGPT extension. This observed setting requirement applies to retrying that local-file chooser route. Use an available supported transfer route to place the actual PDF bytes in GitHub. The original upload page was opened at the handoff branch's `research/pre-1937-sources/ProQuest Pre-1937 Orders` folder.

Use the GitHub connector for repository text, metadata, branches, and commits. If transferring PDFs held on the user's computer, the connected local browser's documented file chooser is one route. Scratch files do not exist on that computer. Inspect current UI state and the GitHub destination before acting; do not reuse old tab IDs or assume an upload succeeded.

After uploading, verify GitHub's actual PDF names, byte sizes, and blob hashes; obtain SHA-256 and PDF-signature evidence when file bytes are available. Update the manifest, checkpoint, README counts, and audit from those observations. Use `verified_repository` events only for confirmed uploaded files. Preserve duplicate copies in the requested folder; count unique orders separately.

If the original folder is inaccessible from the second computer, retain this transfer as unfinished. Reconcile any accessible copies and preserve the nine uncertain Save results rather than calling them completed uploads. Continue the untouched queue and PDF transfer under the owner's existing “go” authorization; pending transfer does not alter the original source links or erase prior evidence.

## 3. Use the connected browser and GitHub destination

The requested final destination is the GitHub folder named above. Local storage can serve as an intermediate when needed by the available transfer method. Resolve an actual local path only for a concrete operation that uses local files; do not reuse another computer's username or tab IDs.

Use the Browser plugin's `control-browser` skill and its current documented API. Select the newly connected computer's browser. Continue the exact supplied record links and their visible PDF controls. A local Downloads-folder confirmation is not a prerequisite.

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
