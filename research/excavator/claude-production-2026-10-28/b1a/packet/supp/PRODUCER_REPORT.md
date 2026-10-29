# Producer report: batch b1a (claude, 2026-10-28)

Producer work only. There is no independent review or human certification, the certified count stays 0, and nothing was committed.

- **Start:** 2026-10-28T19:58:10Z. **End:** 2026-10-28T20:32:03Z.
- **Result:** 33 orders submitted, 3 blocked, 0 unresolved, out of 36.
- **Final packet:** `research/excavator/claude-production-2026-10-28/b1a/packet/supp`. It is the prepared packet plus the source supplement declared in `../SUPPLEMENT_DECLARATIONS.json`, which adds 19 held later-order excerpts.
- **Final applied directory:** `packet/supp/applied-v1`. `CLAIMS.proposed.jsonl` has sha256 `1bb16728…7399`.

## Batch-check result (exit 1)

- **Gates.** All 33 claims pass the Stage 19 gate and the strict claim check (33 of 33). The actual claim-checker reports 33 claims with the gate passed.
- **Custody.** Every claim carries the expected `source_held:custody_record_only` items. The raw APP captures and the ProQuest PDF are not committed, and network verification is off.
- **Mechanical failures (4 claims).** EO 6577, 6773, 7291 and 7315 fail `quote_verbatim:not_found`, caused by the checker defect described below. Each quote matches the registered text it cites; I checked this against the held files.
- **Unreadable sources (2 claims).** EO 7477, and EO 6865's later event EO 7477, are unverified with `source_text_not_available` because of the same defect.
- **Fixability.** These failures cannot be fixed inside the packet without citing the unregistered clause-drafts copy, which the production route forbids, or without cutting the dated signature line out of the evidence. I did neither.

## Defects in the tools

1. **The claim-checker reads the wrong copy of APP texts.** `jobs/claim-checker/sources.py` (`load_job_sources`) indexes `jobs/app-transcriptions/output/SOURCES.jsonl`. That file records each APP text as `../../app-executive-orders/output/texts/...`. `_safe_child` rejects that relative path, so the checker has no readable copy of the registered text. It then falls back to the clause-drafts copy with the same sha256.
   - The clause-drafts copies drop the date line when the transcription prints it without a comma (`June 30 1934.`, `February 14 1936.`, `March 11 1936.`). A whole-text quote of the registered file therefore fails against them (EO 6773, 7291, 7315, and EO 6773 again as EO 6577's later event).
   - EO 7477 has no clause-drafts copy, so its text is reported as unavailable.
   - Fix: let the checker resolve the parent-relative `text_path` inside the repository, or prefer the cited claim's own `text_path` once its hash matches.
2. **The registry overstates custody for four live-harvested pages.** The fragment registry grades the live-harvested APP pages for EO 7080, 7205, 7208 and 7217 as `mirror_transcription`. Their only page record is in `DOCUMENTS.jsonl`, with no archived capture.
   - I used them only as later events. Each one is flagged in its claim as unable to be re-proven once the site changes.
3. **The machine lead for EO 6773 misreads a birthday.** The own-terms lead reads the employee's seventieth birthday ("70 years of age on January 24, 1934") as a fixed term ending 1934-01-24. I rejected it and cited the lead on the operative sentence instead.
4. **A waiting command hung on itself.** The first `apply` ran past the 120-second foreground limit (224 s wall), and a `pgrep -f` wait loop I wrote then matched its own command line and never ended.
   - The fix is to run `apply` and `batch-check` in the background from the start.

## Reasoning shared across the retirement exemptions

- **Statutory basis.** Each order exempts one named employee, two in the case of EO 6338, from section 204 of the Act of June 30, 1932 "until" a stated date.
- **The end.** The end is recorded on that date, inclusive, under the owner's until-date ruling. The exclusive reading is stated as the alternative.
- **Later further-exemption orders.**
  - Each one recites the earlier grant as past ("who was exempted … by Executive Order No. …") and makes a new grant with its own date. None amends the earlier order, and nothing is struck or inserted.
  - Each is therefore recorded as a later event with its own date and quote, not as this order's end.
  - Each claim states the alternative first end, the last later order's date, and why the texts do not support it.
- **Page check.** Done for every APP text against its page record in `MIRROR_DOCUMENTS.jsonl`, or `DOCUMENTS.jsonl` for the four live pages. In each case the heading names the number, the date and subject agree with the text, and `text_sha256` equals the held file's hash.
- **Searches.** Census register titles, the WPA 1944 numbered list, and a full-text name search of all held texts. These found the later orders used here and no others.
- **Authority through 1938.** EO 7704 (1937, running to 1938-10-01) and EO 7725 (1937, running to 1938-11-01) show section 204 still in use through the latest end in the batch, 1938-01-01.

## Per order

The "time" note says what took the time for that order.

| Order | Outcome | First end, or reason blocked | Time went to |
|---|---|---|---|
| EO 2171 | submitted | Own terms, close of 1915-04-15 (Lincoln anniversary closing; the request to merchant ships is not a command). | Rendering and reading the ProQuest page image to confirm the OCR text. |
| EO 5008 | **blocked** | Page check impossible. The CSC report scan (GovInfo SERIALSET-09300…0207, PDF page 84) is not held, and GovInfo returned a proxy 403. The legal reading (own terms, 1928-12-24) is recorded for reuse. | Trying to reach the scan. |
| EO 6214 | submitted | 1934-06-30. Later events: EO 6738 and EO 7080 (live page). | Finding the two Marbut extensions, which are not in any batch. |
| EO 6338 | submitted | 1934-10-31 for both employees. Later events: EO 6862, 6873, 7208 (live page), 7475 and 7645. | Two-person scope and five later events. |
| EO 6342 | **blocked** | No stated period and no held evidence of when the Senate committee's inspection permission ended. Needed: S. Res. 78 (73rd Congress), later Senate action or the committee's final report, or a withdrawal of T.D. 4359 ¶13(a) for that committee. | Checking whether the hathi "EO 6343" T.D. 4397 text and EO 6712 were later events (they are not). |
| EO 6494 | submitted | 1935-12-31 | Routine. |
| EO 6577 | submitted (checker defect 1) | 1934-07-31. Later events: EO 6773 and EO 7217 (live page). | Finding EO 7217. |
| EO 6647 | submitted | 1936-03-31. Later event: EO 7310. | Routine. |
| EO 6702 | submitted | 1934-10-01. Later event: EO 6857, which places him at Brooklyn rather than Newark; name, title and recital show the same employee. | Identity check. |
| EO 6773 | submitted (checker defect 1) | 1935-11-01. Later event: EO 7217 (live page). | Rejecting the 1934-01-24 machine lead; diagnosing the checker failure. |
| EO 6821 | submitted | 1935-09-01 | Routine. |
| EO 6857 | submitted | 1935-02-01 | Routine. |
| EO 6862 | submitted | 1935-11-01. Later events: EO 7208 (live page), 7475 and 7645. | Hedgcock chain shared with EO 6338 and 7475. |
| EO 6865 | submitted | 1935-11-01. Later events: EO 7205 (live page) and 7477. | Finding EO 7205. |
| EO 6873 | submitted | 1935-11-01 | Routine. |
| EO 6920 | submitted | Own terms, close of 1934-12-31 (two afternoon closings). | Excluding the unrelated 6920-A/B/C. |
| EO 6984 | submitted | 1936-04-01. Later event: EO 7307. | Routine. |
| EO 7054 | submitted | 1935-09-01 | Routine. |
| EO 7099 | submitted | 1936-08-01. Later event: EO 7419. | Routine. |
| EO 7113 | submitted | 1936-08-01. It recites EO 6759; no later order is held. | Routine. |
| EO 7162 | submitted | 1936-03-01 | Routine. |
| EO 7187 | **blocked** | Hitchcock likely died before the stated date of 1936-10-01. Records found by web search give his death year as 1935, and my background knowledge, not checked against a held source, puts it at 1935-12-16. Needed: a held death or separation record, to decide whether the exemption ended at his death. | Web check of the death year. |
| EO 7248 | submitted | 1937-01-01. Later event: EO 7517. The name varies across sources (Andrd, Andre, Andrew, André). | Reconciling the name. |
| EO 7258 | submitted | 1936-04-01 | Routine. |
| EO 7291 | submitted (checker defect 1) | 1937-03-01. Later event: EO 7567. | Diagnosing the checker failure. |
| EO 7315 | submitted (checker defect 1) | 1937-04-01. Later event: EO 7586. | Diagnosing the checker failure. |
| EO 7348 | submitted | 1937-05-01 | Routine. |
| EO 7419 | submitted | 1937-08-01 | Routine. |
| EO 7431 | submitted | 1937-10-01. Later event: EO 7704. | Routine. |
| EO 7455 | submitted | 1937-10-01 | Routine. |
| EO 7468 | submitted | 1937-03-31 | Routine. |
| EO 7475 | submitted | 1937-07-01. Later event: EO 7645. | Routine; chain shared with EO 6862. |
| EO 7477 | submitted (checker defect 1: text unreadable to the checker) | 1937-05-01 | Diagnosing the missing checker copy. |
| EO 7480 | submitted | 1937-07-01 | Routine. |
| EO 7517 | submitted | 1938-01-01 | Routine. |
| EO 7518 | submitted | 1938-01-01 | Routine. |

## Open questions for review

- **Deaths before the stated date.** The general earlier-end rationale says that no held record shows a death or separation before the stated date, and that finding one reopens the claim. Only Hitchcock (EO 7187) was checked outside the corpus, so a reviewer may want a similar spot check for other employees.
- **Live-page later events.** The later events drawn from live-harvested pages (EO 7080, 7205, 7208 and 7217) do not support any claimed end. They should still be replaced if archived captures become available.
