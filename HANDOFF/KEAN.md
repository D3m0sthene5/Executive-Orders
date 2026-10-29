# Kean brief: read this first

Generated from `jobs/kean/register/` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand. Named for
Thomas Kean, chair of the 9/11 Commission, which found that agencies held the pieces but did not share them.

- **Start:** read this page and only the newest entry of each `HANDOFF/notes-*.md`. Before proposing any tool,
  pilot or speed-up, run `python3 -I jobs/kean/kean.py search <words>`.
- **Stop:** record results (`add-finding`), questions for the owner (`add-ask`; cite the id in your notes) and
  owner decisions you received (`add-decision`, `wire`). Routine progress stays in your notes. See `jobs/kean/README.md`.

## Waiting for the owner (10)

- **A-20261018-1** (2026-10-18, Claude): Send the drafted archival reference and scan requests (National Archives letters-received series and others)? *Pre-1862 orders have no other route to an original; none of the drafted requests has been sent.*
- **A-20261019-1** (2026-10-19, Claude): Approve, trial or reject risk-tiered review (a lighter independent review for low-risk cases)? *X1's model projected it would cut the post-series remainder from 11,256 to 10,027 agent-hours; that figure is an assumption, never measured.*
- **A-20261021-1** (2026-10-21, Claude): Admit the June 1932 run EO 5853-5879 to the census? *22 of those numbers are census gaps although the American Presidency Project gives their dates and titles; they stay outside every count until admitted.*
- **A-20261021-2** (2026-10-21, Claude): Remove LRS-10-21-Cold-Calls-Plain.pdf (class notes) from the public repository's ProQuest folder? *It was uploaded with the scans by mistake and is publicly visible.*
- **A-20261021-3** (2026-10-21, Owner ruling): Decide sampled review of machine-written claims for rule classes (the 'Jacquard' idea)? *The status-adoption ruling left it undecided; it would change how much independent review rule-class claims need.*
- **A-20261022-1** (2026-10-22, Claude): Add search keys as GitHub repository secrets: BRAVE_SEARCH_KEY, SERPAPI_KEY (paid) and NARA_API_KEY? *Lewis and Clark search the web with them. Bing's API was retired on 2025-08-11 and Google's Custom Search API is closed to new customers (ends 2027-01-01), so those two keys from the original request cannot be used.*
- **A-20261028-1** (2026-10-28, Claude): Does your 2026-10-28 permission to merge every pull request stand for future pull requests? *Agents currently leave merges to you; standing permission would let finished work land without waiting.*
- **A-20261028-2** (2026-10-28, Claude): Make the Kean check a required status check for main (GitHub Settings > Branches)? *Without it a failing Kean check is visible but does not stop a merge.*
- **A-20261028-3** (2026-10-28, Claude): Add to ChatGPT's custom instructions: 'For the Executive-Orders project, first read HANDOFF/KEAN.md in D3m0sthene5/Executive-Orders and record results there before ending'? *Kean reaches only sessions that open the repository; this line brings ChatGPT chats that do not.*
- **A-20261028-4** (2026-10-28, Claude): For orders with no provisional status, may a separate-context Claude reviewer with planted controls adopt the status when it also reviews the order's full lifecycle claim, or must status adoption keep waiting for a diff… *About 200 simple spent orders (retirement exemptions, closings, own-terms orders, allotments) and about 2,980 land orders have no status, so no claim can be filed for them through Claude's route; their reviewed research can only be held as…*

## Standing owner requirements

- **Evidence decides; agents work out legal distinctions themselves** (D-20261028-evidence-decides): Record what the evidence establishes, with the best supported date or interval, and separate an exhausted command from surviving consequences. A claim of 'happened within this interval' needs evidence that it happened; otherwise the order stays open on that question. A later general rule ends a command only if something shows it extinguished that command. Disclosure keeps a gap visible but never fills it. Do not ask the owner to choose method answers to unlock rows: apply these distinctions to the supported cases and report the exceptions.

## Owner decisions not yet carried out by the tools (1)

- **D-20261021-transcriptions** (partly wired): A labeled transcription (APP, Richardson, CSC reports, HathiTrust, Wikisource, or the owner's ProQuest scans) may satisfy the text step provisionally; originals remain the goal and nothing becomes acceptable_as_original. A claim-kit grade-inference bug labeled 1,824 of 3,403 dossiers' transcriptions 'derivative_lead', which the working-text gate rejects; fixed in jobs/claim-kit/inputs.py, effective after claim-kit regenerates.
- Not yet checked against the tools: D-20261021-eo-10449, D-20261021-report-deadline, D-20261021-strike-and-insert, D-20261021-unnamed-instruments, D-20261021-until-dates.

<!-- kean:drift -->
<!-- /kean:drift -->
## Newest results (10 of 47; `search` finds the rest)

- 2026-10-29 F-20261029-1 **worked**: Refresh the original rocket dashboard with current published data Lesson: Preserve the original artifact and frozen weights; readiness and modeled progress never imply human certification.
- 2026-10-28 F-20261028-9 **worked**: Audit the spent-order probe effort denominator for the current dashboard Lesson: Use 5.90 recorded worker-minutes per filed claim for this probe. Keep coordinator time unmeasured and the 88-minute comparison modeled; no project-wide net saving follows.
- 2026-10-28 F-20261028-8 **worked**: Fixes found by the probe: claim-kit uses the producer-registered working-text grade; APP page check defined;… Lesson: APP pages harvested live (DOCUMENTS.jsonl) cannot be re-proven once the site changes; prefer mirror captures or government printed copies for claims, and let Cotton run on every claims change.
- 2026-10-28 F-20261028-7 **worked**: Spent-order probe: 20 pre-1937 own-terms orders (retirement exemptions, closing days, eight-hour suspensions)… Lesson: For simple own-terms orders the effort model overstates per-order work by roughly an order of magnitude. These types hold about 380 model hours; the large blocks (land, unclassified, standing, CS wai…
- 2026-10-28 F-20261028-6 **worked**: Research and rewrite of TR-CS-WAIVER (1,530 one-person civil-service waivers) under the owner's evidence ruli… Lesson: Four outcomes: exhausted on a date; within (order date, R]; not in force with use unknown as an interval to the reason date; open. Most waivers will stay open on use unless the Official Register is f…
- 2026-10-28 F-20261028-5 **no record**: Diagnose main's failed daily runs of 2026-10-26 and 2026-10-27. Lesson: Read the run page on GitHub for the failing job; the Rattle Watch now prints per-job progress so the next failure names itself in the log.
- 2026-10-28 F-20261028-4 **partly worked**: 20-order probe on spent pre-1937 orders with statuses (12 retirement exemptions, 5 eight-hour suspensions, 3… Lesson: Most blocks were tool defects, now fixed: claim-kit keeps named transcription grades and the shared date lookup reads the WPA numbered list. Re-prepare after Pinakes and claim-kit regenerate; supplem…
- 2026-10-28 F-20261028-3 **analysis**: Diagnosis of slow and opaque GitHub runs; Rattle Watch added to the runner. Lesson: Watch the per-minute Rattle Watch lines in the run log; a silent idle job is stopped after 20 minutes, and web searches run in full only on their daily schedule or when their own inputs change.
- 2026-10-28 F-20261028-2 **analysis**: Diagnosis of why the agent-hour estimate stalled. Lesson: Ask the owner for decisions and act on rulings before building speed-up tools.
- 2026-10-28 F-20261028-10 **worked**: Refresh the dashboard against the combined October 28 production claims Lesson: Use published generations and exact receipts; filed claims and isolated replay gains never establish readiness.

Register: 11 owner decisions, 0 answered questions, 47 results; 16 older reports not yet summarized (`jobs/kean/register/legacy_reports.txt`).
