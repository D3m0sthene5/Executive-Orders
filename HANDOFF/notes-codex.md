# Codex's handoff notes

Newest entry first. See `README.md` in this folder for the format.

<!-- Codex: add your first entry here. -->

## 2026-10-18: HathiTrust GPO acquisition stopped at anonymous access gate

- **Done:** Branch `codex/hathi-gpo-orders-20261018`, from main `224fd70cb6982f764d7f95f99102d1f1ab7d3fce`. Only `jobs/hathi-gpo-orders/` and this note changed. Pinned all 1,712 all-no census targets numbered 5076–7531 and listed ten logical GPO/Hoover volumes, including the intermediate number ranges. Inventory ranges are candidates, not verified contents.
- **Stop:** The unchanged early-orders-hunt module's shared FetchPool refused the first viewer with `blocked_by_robots_txt`; only the robots request was made by the pool. Browser inspection also met an access challenge. No volume was downloaded, no order extraction was attempted, and no login, retry, alternate route, or page-by-page reconstruction was used. The full Hathi extraction adapter was not built after this stop.
- **Validation:** Offline `finish_report.py` confirms the target count/range union and protected input hashes. Unchanged claim-kit `load_corpus` recognizes zero new texts because zero were saved; this does not validate a future OCR adapter. `jobs/claim-kit/output/` remains untouched. All 1,712 targets are recorded as not attempted in the failure list; the first-two-volumes recovery gate was not reached.
- **Running:** Nothing.
- **Next:** No automatic continuation. Read the access restrictions and receipts in `jobs/hathi-gpo-orders/README.md` and `output/STATUS.json` before any later source plan. No per-order token or savings comparison was performed.
- **Asks:** None.
- **Do not:** Bypass robots or download limits, log in for this assignment, change another producer, or treat an access stop as missing source evidence or a legal-status finding.
