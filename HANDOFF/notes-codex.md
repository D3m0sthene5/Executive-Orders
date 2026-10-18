# Codex's handoff notes

Newest entry first. See `README.md` in this folder for the format.

<!-- Codex: add your first entry here. -->

## 2026-10-18: Alternate sources saved 1,531 texts for the 1,712-order gap

- **Done:** Continued `codex/hathi-gpo-orders-20261018` / PR #28 after the HathiTrust refusal. Wrote an 18-route plan before each route's downloads; saved 781 IA Hoover GPO texts, 54 GovInfo Federal Register texts, 689 Commons GPO scan OCR texts, and seven Wikisource scan-page transcriptions. Exactly 181 targets remain missing (five Hoover, 176 FDR). Only `jobs/hathi-gpo-orders/`, `research/orders-1929-1936/`, and this note changed. All acquisitions are attributed derivatives, explicitly `acceptable_as_original:false`; no order status changed.
- **Validation:** Exactly 1,712 unique RESULTS.csv rows partition into 1,531 saved and 181 missing. Unchanged claim-kit `load_corpus` recognizes all 1,531 once, with no warnings and all original flags false. Source/text hashes and raw held artifacts checked; protected inputs and shared download/extraction tools unchanged. No writes to claim-kit/output. OCR, page furniture and some adjacent context remain; page checking is required before substantive claims. Raw artifacts are protected from Git newline conversion.
- **Access:** Hathi excluded; APP's explicit OpenAI robots exclusions respected. Google Books throttling, FDR library TLS failure, GovInfo API robots HTTP 500 and NARA key/storage terms are recorded without bypass. The local wildcard/AI-group policy adapter corrects the shared robots parser's missed wildcard rule; no shared code changed. A mistakenly fetched GovInfo search SPA supplied no texts.
- **Running:** Nothing after the bounded job ends. No automatic job.py or scheduler was added.
- **Next:** HUMAN_STEPS.md gives exact short owner actions; the leading action is an APP export/permission request for up to 181 residual IDs, actual overlap unconfirmed. Incoming local-file importer is ready. The scan-page queue has navigation leads for 105 residual IDs; these are not text recoveries. Do not redownload the same government scans merely to repeat OCR.
- **Asks:** None sent. Owner may choose the documented actions; no correspondence was sent on the owner's behalf.
- **Do not:** Modify other producers/status records, bypass access controls, count derivative text as original, or treat acquisition failures as evidence absence. No per-order token/savings comparison was performed.


## 2026-10-18: HathiTrust GPO acquisition stopped at anonymous access gate

- **Done:** Branch `codex/hathi-gpo-orders-20261018`, from main `224fd70cb6982f764d7f95f99102d1f1ab7d3fce`. Only `jobs/hathi-gpo-orders/` and this note changed. Pinned all 1,712 all-no census targets numbered 5076–7531 and listed ten logical GPO/Hoover volumes, including the intermediate number ranges. Inventory ranges are candidates, not verified contents.
- **Stop:** The unchanged early-orders-hunt module's shared FetchPool refused the first viewer with `blocked_by_robots_txt`; only the robots request was made by the pool. Browser inspection also met an access challenge. No volume was downloaded, no order extraction was attempted, and no login, retry, alternate route, or page-by-page reconstruction was used. The full Hathi extraction adapter was not built after this stop.
- **Validation:** Offline `finish_report.py` confirms the target count/range union and protected input hashes. Unchanged claim-kit `load_corpus` recognizes zero new texts because zero were saved; this does not validate a future OCR adapter. `jobs/claim-kit/output/` remains untouched. All 1,712 targets are recorded as not attempted in the failure list; the first-two-volumes recovery gate was not reached.
- **Running:** Nothing.
- **Next:** No automatic continuation. Read the access restrictions and receipts in `jobs/hathi-gpo-orders/README.md` and `output/STATUS.json` before any later source plan. No per-order token or savings comparison was performed.
- **Asks:** None.
- **Do not:** Bypass robots or download limits, log in for this assignment, change another producer, or treat an access stop as missing source evidence or a legal-status finding.
